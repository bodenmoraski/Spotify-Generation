# Daily Brief — Tuesday, 17 November 2026

<!-- episode_title: When the Metric Mistook Length for Convergence -->

_Good morning. Today: a compute rule that may just move the border, a tax argument that says revenue is the least interesting part, a paper on a measurement bug hiding in plain sight, and an idea about facts over theories. Eighteen minutes._

## The World

### 1. A compute rule that moves the border rather than closes it

The Bureau of Industry and Security [B-I-S] published a 132-page export-control rule early this week, and the most telling detail is not the rule itself but the byline: Commerce credited the Treasury and National Security Council with writing large parts of it. ChinaTalk’s Jordan Schneider argues that this is a signal that enforcement, not just drafting, has shifted. On the table are three real loopholes: license requirements for advanced chips routed through Singapore, Malaysia, Thailand, Indonesia, and Brazil; a cap on compute rented directly to Chinese firms; and a TSMC [tee-ess-em-see] backdoor closed for the second time. ChinaTalk estimates the cloud loophole alone supplies about two-fifths of China’s AI compute. But Schneider and two former Biden NSC officials point to the Northern Virginia problem: if the rule stops at the US border, a Chinese firm can simply rent from a US-based cloud provider in a Washington suburb and stay legal. The rule is an industrial-policy document as much as a security one — it decides who gets to train next-generation models and where that training physically happens.

**Why this matters:** Without internal reporting and enforcement, the rule may relocate the problem to American data centers instead of solving it.

### 2. Taxation as emancipation, not just revenue

Vanessa Williamson in n+1 makes a claim that upends the usual fiscal-policy reaction: the midterm result is not primarily a chance to raise or lower rates; it is a chance to rebuild democratic control through taxation. Her phrase is “emancipatory taxation.” The idea is that taxes are the point where the state makes its relationship to wealth legible, and where citizens can demand an accounting. The essay starts from the seating of a new Congress in January 2027, but the argument is longer: fiscal policy has been trapped in a revenue-first frame that treats taxes as a necessary evil. Williamson wants to treat them as a political technology — a way to discipline industries, expose offshore capital, and force the wealthy to appear in public records.

**Why this matters:** This is not a story about the deficit; it is a story about whether tax law becomes a tool for popular accountability, not just a funding mechanism.

### 3. The economics of an indispensable founder

Marginal Revolution’s Tyler Cowen has an uncomfortable post-mortem on the Huang era at Nvidia [en-VID-ee-ah]: a great CEO can be a governance failure. Jensen Huang [JEN-sen hwahng] famously had about sixty people reporting directly to him. Cowen argues that, whatever the daily advantages, that structure is not resilient. When Huang stepped down, no single subordinate had collected and interpreted the information from those sixty lines. The result is that a share-price decline after his resignation reflects not just the loss of a brilliant leader but the failure to build a system that could survive him. Cowen’s one-liner is that the best CEOs make themselves at least partially dispensable.

**Why this matters:** This reframes founder-led companies from heroic autocracies into fragile infrastructure — a lesson that travels far beyond chipmakers.

### 4. The ancient category error behind AI

Public Books has a piece that makes the usual AI-slavery comparison feel fresh by reverse-engineering it. Morgan Barry starts with a Roman senator’s son who could not learn the alphabet, so he used twenty-four slave boys, each named for a letter, as learning tools. The moment the boy grasped their function, they were decommissioned as obsolete hardware. The article argues that our current language — tools, agents, assistants — sits inside a longer genealogy in which intelligence is treated as a purchasable instrument, and the line between person and tool is deliberately flexed. That is not a warning about robot sentience; it is a warning about the categories we are building into product design and labor relations.

**Why this matters:** The language we use for AI now encodes a very old power move: some minds count, and some are infrastructure.

### 5. The AI consciousness argument is now about belief, not metaphysics

Transformer’s Celia Ford reports that the Catholic Church and the Associated Press now agree: AI does not think, feel, want, or understand. The AP updated its stylebook to bar human-characteristic language; Pope Leo the Fourteenth’s first encyclical says AI has no body, no joy, no relationships. But the scientific case is not closed. Recent work from academic groups and Anthropic [an-THROP-ic] suggests current language models may have something researchers call access consciousness: not feeling, but at least being able to access a thought and act on it. Ford’s argument is that the real question is not whether machines have inner life, but what we decide to believe about them, because those beliefs will structure regulation, liability, and labor.

**Why this matters:** The debate is shifting from what AI is to what it is allowed to be in law and in speech — and that is a political fight.

### 6. The pseudonym as academic survival

Literary Hub carries a sharp piece by Azra Liaqat Khan [AZ-rah lee-AH-kat kahn], a name that is itself a pseudonym. The writer is a political scientist whose memoir describes sex work, and the essay is about why she cannot publish it under her own name. Her university would remove her from high school recruitment, she writes; keynotes would dry up; her authoritative no-AI policy and meticulous teaching notes would suddenly read differently. The argument is not that she wants privacy, but that the persona of the neutral expert is built on an unmarked biography. Stigmatized labor breaks that illusion.

**Why this matters:** It exposes the hidden price of academic credibility — and why some knowledge only enters public life behind a mask.

## Paper of the Day

### Embedding Cosine Measures Text Length Before It Measures Homogenization

A quiet methodological paper on arXiv [archive] may have just pulled the rug out from a whole shelf of AI-and-culture research. The question Fengming Liu starts with is simple: when researchers say that online discourse is becoming more homogeneous after generative AI, what exactly is the cosine similarity between embedding vectors actually measuring?

The answer Liu finds is uncomfortable: when the embeddings come from a mean-pooled encoder that was never trained for sentence similarity, most of the similarity signal is text length. The study looks at 6.06 million Reddit comments. An earlier analysis using uncentered DeBERTa-v3 [dee-BERT-ah vee-three] had reported that only conservative discourse broke toward homogeneity after late 2022. Liu takes those same comments and merely truncates them from ten words to one hundred fifty words. That manipulation alone raises the mean cosine by eight times the size of the reported break. Then the really damning control: replace every comment with a random comment of equal length, and the asymmetry is 81 percent reproduced. A fixed-content simulation gets 78 percent. The leading principal direction carries 99.9 percent of raw DeBERTa homogeneity. Once length is handled, the political asymmetry disappears under every encoder tested.

The same test on 575,000 Stack Exchange answers: the post-ChatGPT homogenization of technical sites is fully reproduced by a placebo, because answers grew longer. A census of 31 studies maps the risk pattern: anisotropic [an-eye-so-TROP-ik] encoders, time-series designs, and length-unequal comparisons.

Think about what this does to the lunch conversation. For two years, the respectable version of “AI is homogenizing culture” relied on a number: mean pairwise cosine similarity. This paper shows the number is so sensitive to length that a placebo can reproduce the core political finding. The reason is that mean-pooled embeddings from many encoders carry a dominant direction correlated with passage length. When you center or renormalize, the effect changes or vanishes. The so-what is simple: if a study compares texts from before and after ChatGPT, and the later texts are longer — which they often are — then the method may be doing length detection, not convergence detection. Liu does not say no homogenization is happening; the paper says the standard measurement cannot tell you whether it is.

**Why this matters:** A lot of confident claims about AI making everyone sound the same may instead be measuring that everyone is writing longer. Before citing the next AI homogenization study, ask whether they controlled for length.

## One Idea

### 1. Read more facts, fewer theories

First idea comes from LessWrong, by Arjun Panickssery. The claim is blunt: read more facts and fewer theories. Almost all the most thoughtful people he knows, or has interviewed, have memorized a lot of dates, places, names, and numbers — and they care about being able to recall them. He quotes Joe Wiesenthal [WEES-en-thal]: “Seek truth from facts. It’s the only way.”

The mechanism is not anti-intellectual. It is that theories are high-dimensional; they can be shaped to fit almost any new fact, and they give a false sense of understanding. Facts are low-dimensional constraints. A date, a place, a price, a vote count — those cannot be flexed. They break when they do not fit. Michael Crichton’s Gell-Mann amnesia is the standard example: you read an article about your own field and see the journalist gets it wrong; then you turn the page and trust the paper on another topic. The corrective is not to read no journalism; it is to carry a small stock of hard facts into every new domain so you can catch the wrongness early.

How to use it: keep a running fact log when you read. Not quotes, not takeaways. Facts. When someone offers a grand theory about politics, economics, or AI, ask one question: “What exact number or specific event would falsify this?” If they cannot answer, you are probably hearing a story, not a model. In your own research, collect anomalies before you write the synthesis. The theory should come last, after the facts have had a chance to be inconvenient.

**Why this matters:** The feeling of being well-read is not the same as being fact-armed, and one of these is much harder to persuade.

### 2. The art of presence: Tehran’s quiet disobedience

Aeon’s Parisa Khoshnami [pah-REE-sah khosh-NAH-mee] writes about something easy to miss in news photos from Iran: women in Tehran are not just defying dress codes in isolated protests; they are changing society by dressing as they choose, every day, in numbers too large to stop. Khoshnami calls it the “art of presence.” The reframe is important: this is not sad victimhood or a single brave act, but distributed civil disobedience operating at the level of daily life.

The mechanism is a slow-motion norm cascade. Each woman walking out in the “wrong” coat or uncovered hair changes what the street looks like; enough changed streets change what is normal; enough normal makes enforcement expensive and visible. This is not a riot; it is an atmosphere.

Use it as a lens. When you read about authoritarian crackdowns, look for the daily aesthetic choices that are not being counted as resistance. The numbers may be missing because the acts are too ordinary. The women of Tehran are using presence the way others use votes or strikes — and the regime’s inability to stop it is itself a fact.

**Why this matters:** Some of the most powerful resistance never looks like politics; it looks like a woman deciding what to wear on a Tuesday.

## Quick Reviews

**Assigned.** Four cards from three days ago.

**1. Fugitive imagination.** Three days ago we covered an argument about fugitivity as a source of knowledge, not just escape. _…take a second…_ in that framing, what does fugitivity produce?

Because it produces a perspective — a mobile, marginal vantage that sees the official order from the outside. Not just flight, but a different epistemology.

**2. November Bookmarks: A Single Woman in a Dust-Proof Room.** We read a bookmarks roundup. _…take a second…_ what was the main weakness we flagged in that piece?

It gave excerpts but no argument or reframing. The quotes were well-chosen, but there was no thread tying them together; it was a tasting menu, not a meal.

**3. WOKE feminist EXPOSES left-wing anti-meme (NOT CLICKBAIT).** The argument was about anti-memetic ideas. _…take a second…_ what made an idea an anti-meme?

It was true, but carrying a social cost to say aloud, so it self-censored. People who could spread it stayed quiet, and the idea died not from being false but from being costly.

**4. Open-source AI without Jensen.** We covered a reframing of Nvidia’s open-model ecosystem risk. _…take a second…_ what was the specific risk?

That open-model funding depended on Jensen Huang’s personal stance and credibility. Remove the person, and the commitment — and the money — may not survive the succession.

_End of brief._