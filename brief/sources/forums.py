"""LessWrong / Alignment Forum / EA Forum: karma-thresholded RSS + ForumMagnum GraphQL."""

from __future__ import annotations

from typing import Any

from brief.models import Item
from brief.sources import parse_datetime, parse_rss, strip_html

# ForumMagnum (LessWrong / EA Forum) list query. karmaThreshold is applied
# client-side as well in case the schema ignores the terms field.
POSTS_QUERY = """
query RecentPosts($limit: Int) {
  posts(input: {terms: {view: "new", limit: $limit}}) {
    results {
      _id
      title
      pageUrl
      postedAt
      htmlBody
      excerpt
      baseScore
      user { displayName }
    }
  }
}
"""


def parse_rss_feed(body: str | bytes, feed: dict[str, Any]) -> list[Item]:
    items = parse_rss(body, feed)
    threshold = int(feed.get("karma_threshold") or 0)
    if threshold <= 0:
        return items
    kept: list[Item] = []
    for item in items:
        karma = item.karma
        if karma is None:
            kept.append(item)
            continue
        if karma >= threshold:
            kept.append(item)
    return kept


def parse_graphql(body: dict[str, Any] | str, feed: dict[str, Any]) -> list[Item]:
    import json

    if isinstance(body, (str, bytes)):
        data = json.loads(body)
    else:
        data = body
    payload = data.get("data") or data
    posts = payload.get("posts") or {}
    rows = posts.get("results") or posts.get("data") or []
    if isinstance(posts, list):
        rows = posts
    threshold = int(feed.get("karma_threshold") or 0)
    items: list[Item] = []
    for row in rows:
        title = strip_html(row.get("title") or "")
        url = (row.get("pageUrl") or row.get("url") or "").strip()
        if not title or not url:
            continue
        karma = row.get("baseScore")
        try:
            karma_i = int(karma) if karma is not None else None
        except (TypeError, ValueError):
            karma_i = None
        if threshold and karma_i is not None and karma_i < threshold:
            continue
        excerpt = strip_html(row.get("excerpt") or row.get("htmlBody") or "")[:4000]
        user = row.get("user") or {}
        authors = []
        if isinstance(user, dict) and user.get("displayName"):
            authors.append(user["displayName"])
        items.append(
            Item.from_parts(
                title=title,
                url=url,
                feed=feed,
                excerpt=excerpt,
                authors=authors,
                published=parse_datetime(row.get("postedAt")),
                karma=karma_i,
            )
        )
    return items


def parse(body: Any, feed: dict[str, Any]) -> list[Item]:
    if isinstance(body, dict) or (isinstance(body, str) and body.lstrip().startswith("{")):
        return parse_graphql(body, feed)
    return parse_rss_feed(body, feed)
