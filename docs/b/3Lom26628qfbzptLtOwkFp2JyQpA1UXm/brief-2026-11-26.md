# Daily Brief — Thursday, 26 November 2026

<!-- episode_title: The Map Moves Under the Money -->

_Good morning. It is Thursday, November twenty-sixth. About eighteen minutes: five world items, one paper as a story, one idea you can apply, and four review cards. I will not pad this with slideshows or a read-later list. If something is thin, I will say so and move the minutes somewhere more useful._

## The World

### 1. Stablecoins look like transaction money, not parked crypto capital

Marginal Revolution points to a new NBER working paper using wallet-level blockchain data from 2020 through 2025. The headline is a reframe: stablecoins are not mostly speculative cash sitting on the sidelines. They are transaction money. Onchain volume exceeds Bitcoin’s despite a much smaller supply. Velocity has risen sharply. Transactions have shifted toward low-value transfers, which is what real payment money does. The paper also reattributes exchange activity using transaction timing. Once it does, activity looks spread across the Americas, Europe, and Asia, with fewer cross-regional flows than the standard method implies. Stablecoins are becoming the settlement currency of a fast-growing on-chain credit market. The growth appears to reallocate rather than destroy credit. Smart contracts are involved in about a third of Ethereum stablecoin transactions and over two thirds of volume, and one protocol shows sub-cent machine-to-machine payments. Why this matters: If stablecoins are tokenized money settling small payments and credit, the regulatory question shifts from “should we allow another speculative token?” to “whose payment rails and credit markets are being built?”

### 2. Fabricated dunks are cheap, optimized misinformation — not just selection bias

LessWrong has a short essay by Dean Valentine called “Dunks.” The argument is that social media’s most corrosive fake content is not a selection problem. It is an optimization problem. The common view is that dunks are true but unrepresentative: people pick a celebrity’s worst moment, and the core is basically correct. Valentine says that is much too optimistic. Almost nobody investigates the takes they read. A rebuttal from the person targeted rarely travels as far as the original mockery. A take can always be made stupider, or attached to a more famous or more hateable person. So for every genuinely dumb take, there is a dumber, more memetic take an influencer can pretend someone made, if they are willing to maliciously interpret, fabricate, or decontextualize. The result is a market where fabricated dunks outcompete real ones because they are cheaper and better designed for attention. Why this matters: The next time a screenshot makes you angry, ask not only “is this real?” but “who benefits if I never check?”

### 3. The open-weight AI fight is industrial policy, not just a safety argument

The Times of India carries a piece on the lobbying battle in Washington over open-access AI models. The framing is less about a Pentagon press conference and more about technology influence. Open-weight releases let other countries and companies fine-tune and deploy models without paying a license to a frontier lab. The fight in DC is about whether that openness is a safety risk, a competitiveness problem, or a geopolitical gift. The Indian outlet reads it as a contest over who gets to build the next layer of the AI stack. US firms want to hold the frontier; open models lower the entry cost for everyone else. The subtext is that if Washington treats open weights as a national security problem, it may push the open ecosystem toward non-US centers. That changes who trains the next wave of models and who sets the defaults. Why this matters: Open-weight policy is not just about safety; it is industrial policy by another name, and the rest of the world is watching which way the lobbying tips.

### 4. A Ukrainian essay reads 2026 through 1918

Literary Hub publishes an essay by Illia Ponomarenko [ill-YAH pah-noh-mah-REN-koh]. He opens in January 1918 at a railway stop called Kruty [KROO-tee], near Nizhyn [NEE-zhin]. Ukrainian cadets and students are trying to hold a line against a Red advance. It is cold, fogged, chaotic. The essay then connects that fight to 2014 and the current war. The title asks “1918 or 2014?” The argument is that Russian aggression against Ukraine is not a single event but a cycle. Each generation meets it with scarce weapons and a long memory. Ponomarenko is not offering a policy paper. He is making the present legible as recurrence. That can be dangerous if it flattens differences. But it is useful if it reminds you the current war did not begin with the last headline. Why this matters: The news cycle has no memory; a literary essay can restore a longer horizon without pretending the tactics are identical.

### 5. A Caribbean wire re-sequences the Gaza ceasefire story

A GDELT [GEE-delt] feed surfaces the Gaza ceasefire story from CBC Barbados, not from a US or Middle Eastern wire. The headline: Israel intensifies assassinations in Gaza as the US urges Netanyahu [neh-tan-YAH-hoo] to proceed with a ceasefire plan. The Caribbean framing is worth pausing on. It is not the usual “Israel defends itself” or “US pressure grows” framing. It foregrounds the assassination campaign as the active fact, with US urging as the conditional. That inverts the standard Western read, where the diplomatic process is the spine and the strikes are context. I could not verify the underlying sourcing beyond the feed, so I will not lean on this as confirmed. But as a case study in how news selection works, it is useful: the same events, re-sequenced, move the story from a negotiation to a killing campaign. Why this matters: If you only see one desk’s version, you may mistake a narrative choice for the shape of the war.

## Paper of the Day

### Guidance as Variance Matching

Today’s paper is from the arXiv [archive], by Ali Backour [BACK-oor], Artem Lukoianov [loo-KYAH-nov], Frank Permenter [PER-men-tur], Tommi Jaakkola [YAHK-oh-lah], Justin Solomon, and Vincent Sitzmann [SITZ-mahn].

The question starts with a trick. Diffusion models are the systems behind much of the recent image, video, and audio generation. They lean on a trick called guidance, where the model’s prediction is pushed away from a weaker reference prediction. Guidance substantially improves sample quality. But nobody has had a clean explanation of what it is actually doing.

The standard story has been that guidance improves the model’s estimate of something called the posterior mean. That is the model’s training target. The authors check that story at the scales people actually use. They find it is wrong. Guidance does not improve the posterior-mean prediction. It makes the prediction worse, while the samples get better.

So why do the samples improve? The authors find that posterior-mean predictions have less variance than the real data. The model’s natural output is too smooth, too typical, too safe. Guidance restores the missing variance. They use that to build something called variance-matched guidance. It is a closed-form rule that picks the guidance scale by matching the variance of the guided predictions to the variance of the data. Without tuning, it recovers the hand-picked scales of eleven widely used models across image, video, audio, motion, and world generation. To their knowledge, no previous explanation of guidance predicted those scales. Applied per noise level, it yields a schedule without tuned hyperparameters that users prefer to hand-crafted ones on Stable Diffusion 3.5 Medium.

The interpretation is elegant. Each model makes a random error in predicting the posterior mean. Guidance rescales the difference of those errors into a sample. The result is not a more accurate guess. It is a more realistic one.

Why this matters: Most practitioners treat guidance scales like seasoning. This paper says there is a measurable reason behind the knob, and maybe a recipe. If it holds, it removes one of the most artisanal parts of generative model pipelines.

## One Idea

### Desirable difficulties, applied — and a shorter add-on about identity theft

The first idea is from The Learning Scientists, by Megan Sumeracki [soo-mer-AH-kee]. It is built around a counterintuitive claim: forgetting is part of remembering. Her context is Thanksgiving break. Students come back after a two-week gap and say “I can’t remember” or “when did we learn this?” She says she is not concerned. That forgetting is not a failure. It is the raw material for stronger retrieval.

The mechanism goes back to Hermann Ebbinghaus [HER-man EB-ing-house] in the 1880s. He mapped the forgetting curve. Forgetting is rapid at first, then slows. He also showed that spreading repetitions out works better than cramming. When you let a memory fade a little and then retrieve it, the effort of reconstructing it strengthens the memory more than fluent rereading. That is the desirable-difficulty principle. The work that feels worse in the moment is often the work that sticks.

The usable rule is that the optimal gap scales with how long you want to remember. If you need something for an exam next week, wait a day or two between reviews, not an hour. If you need it for life, wait a week, then a month, then longer. The feeling of ease is a trap. Rereading feels fluent, but it mostly tells you that you recognize the page. Retrieval feels harder, but it is the actual work of memory.

How to use it in conversation: resist the urge to supply a word or name too quickly when someone is struggling. The pause is not awkward. It is the other person’s memory doing the desirable work. How to use it in your own research: after reading a section, close the tab or the book and write the argument from memory in one sentence. Then check. You will notice what you did not actually understand. How to use it in self-improvement: once a week, take a blank page and write what you remember from the things you read. Do not scroll your highlights first. The blank page is the test.

The add-on is from Aeon, an essay by Dina Gilio-Whitaker [JEE-lee-oh WHIT-uh-ker] called “The pretendian wars.” The essay argues that falsely claiming Indigenous identity is not a frivolous mistake. It is a grave theft. The stakes are rising because identity can unlock jobs, grants, authority, and public sympathy. The conceptual mechanism is worth lifting out: identity claims function like a commons. False claims extract status without paying the membership cost. The person who can counterfeit belonging skips the burdens and still takes the benefit. Why this matters: The same logic applies to any credential or background you might be tempted to exaggerate. The easy claim devalues the real one.

## Quick Reviews

**Assigned.** First, three days ago we covered a reported rare trilateral summit in Shenzhen. _…take a second…_ What was the central claim about why it mattered?

It could reshape geopolitics by placing Putin, Xi, and Trump in the same room outside existing alliance structures; it was flagged as needing verification because the combination was unusual enough to demand harder sourcing.

Second, we covered “Science After Super Intelligence.” _…take a second…_ What was the core reframe about AI’s role in science?

It reframed AI’s role as expanding rather than ending human inquiry: superintelligence does not make science obsolete; it shifts human effort toward choosing questions, interpreting results, and deciding what matters.

Third, “New Congress, New Rare Earths Policy?” _…take a second…_ What was the core reframe about rare-earth supply chains?

Rare-earth supply chains are leverage, not just dependencies; the analysis argued the useful move is to treat them as strategic chokepoints and price in policy fragility, though the item was news-pegged and truncated.

Fourth, “How do biotech hedge funds make money?” _…take a second…_ What was the main explanation?

They make money through information networks: being embedded in clinical, regulatory, and scientific networks gives early signals that are not yet visible in public data. The science matters, but the network placement is the edge.

_End of brief._