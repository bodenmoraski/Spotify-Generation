"""JSON-lines structured logging to stdout."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


def log(**fields: Any) -> None:
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **fields}
    sys.stdout.write(json.dumps(payload, default=str) + "\n")
    sys.stdout.flush()
