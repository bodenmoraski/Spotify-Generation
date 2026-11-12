# Daily Brief — Thursday, 12 November 2026

<!-- episode_title: Twin studies, collapsing coverage, and the trouble with ease -->

_Good morning. About eighteen minutes. Today: a statistical result that could shrink the role of the randomized trial, a breakup in South African politics, two arguments about novels, and a paper that explains why fine-tuned language models sometimes get worse even while their reward goes up. Then one idea — about the questions we ask before we ask the big question — and reviews._

## The World

### 1. The observational trial gets its digital twin

There is a new working paper from Raj Chetty [CHET-ee] and coauthors that takes aim at one of the quiet orthodoxies of policy evaluation: the idea that randomized controlled trials are the only reliable way to learn whether a program works. The paper starts from a real problem. Older observational studies often diverged from experimental benchmarks, sometimes badly. That created a kind of institutional pessimism: if you did not randomize, the story went, your estimate was probably biased.

The authors argue that this pessimism may have been an artifact of small survey datasets. They went back to the era of large administrative data. Using anonymized IRS tax records covering all American adults from 1999 to 2025, they trained a machine-learning model to predict counterfactual earnings from prior work history, demographics, and residential location. Then they tested that model against 37 randomized controlled trials of workforce training programs. The result is striking: the observational machine-learning estimates match the RCT estimates so closely that their root mean squared error is comparable to the trials themselves. Relative to the parametric estimators used in earlier work, the method reduces error by 60 percent.

**Why this matters:** If the result generalizes beyond workforce training, governments could evaluate hundreds of programs continuously from administrative data, with RCTs becoming occasional validation checks rather than the only oracle.

### 2. South Africa’s small-party shock

The Africa Report’s post-election read is not about who governs, but about who no longer needs permission to matter. The headline story is that small parties pulled off big surprises in South Africa’s recent contests. The article treats that not as a chaotic sideshow but as a structural signal. After years of service-delivery failures, rolling electricity cuts, water problems, and factional infighting inside the dominant parties, voters in key municipalities and provinces split their ballots. Regional, single-issue, and personality-based parties gained seats by campaigning on potholes, lighting, land, and local administration — not big ideology.

What makes this different is the arithmetic. The large parties still have numbers, but they now need partners that five years ago would have been ignored. Coalition agreements are being negotiated with parties whose entire mandate is a few grievances and a local base. That changes what gets traded in coalition talks. It also makes future policy more volatile, because small parties can extract visible concessions in exchange for stability, then withdraw if their local credibility is threatened.

**Why this matters:** South Africa is often read as a one-party-dominant system; this result suggests power is shifting to the margins, and the center may now be a permanent negotiation, not a command post.

### 3. Gopnik on Hemingway, a century later

Literary Hub has Adam Gopnik [GOP-nik] on The Sun Also Rises at 100, and his argument is sharper than the usual anniversary appreciation. He starts from the discomfort first-time readers now feel. The novel opens with a tang of anti-Semitism around Robert Cohn, indulges in later slights against gay men, and treats the heroine’s ordinary sexual appetite as a somewhat undignified affliction. Some contemporary readers stop there. Gopnik does not wave that away. His point is that the prejudices are not an obstacle to the book’s power; they are part of its documentary texture. The novel is about a lost generation after the First World War, with its brittle masculinity, displaced Jewishness, and sexual unease. Hemingway does not flatter his people. He records them.

That, Gopnik argues, is why the book has lasted a century and why writers keep mining it. Against the polished surfaces of Gatsby, The Sun Also Rises still offers barbed wire and thorns. It refuses to be a clean antique.

**Why this matters:** This is a useful lens for reading difficult old fiction — the thing that offends may be evidence, not error, and avoiding it can flatten history into comfort.

### 4. Brazil reframes climate as geopolitics

A piece in the Brazilian outlet Projeto Draft carries a line worth sitting with: the climate debate has stopped being an environmental discussion and has landed in geopolitics. That may sound generic in an English-language read, but the local frame matters. For Brazil, this is not primarily about saving trees. It is about leverage. The Amazon is increasingly being discussed as a strategic asset: critical minerals, water, carbon markets, food security, and the energy transition. The article argues that this opens an opportunity for Brazil to play an important global role — not as a passive host of the planet’s lungs, but as a dealmaker.

That shift changes the tone of the conversation. A country that sees itself as a steward asks for aid. A country that sees itself as a supplier of strategic stability sets terms. The piece is careful not to claim Brazil has already converted that potential into influence, but it frames the current moment as one in which the door is open. The question is whether Brazil’s political class can negotiate as a bloc, rather than as competing ministries with separate agendas.

**Why this matters:** When climate becomes geopolitics, the asking price for cooperation changes — and countries that frame their resources as leverage can set entirely different terms in trade and investment talks.

### 5. Dostoevsky’s messy novel for a messy time

Public Books has a B-sides essay on Fyodor Dostoevsky’s [dos-toy-EV-skee’s] The Adolescent, and the title alone makes the case: it is among his wildest, sloppiest, least-loved works, and there has never been a better time to read it. The novel’s narrator, Arkady Dolgoruky, is the illegitimate son of a nobleman. He is obsessed with becoming a Rothschild, torn between competing father figures, and filled with ideological scripts he cannot quite inhabit. It is a book about inherited confusion, about wanting power before knowing what the power is for.

The essay argues that the usual criticism of The Adolescent — that it is formally messy, episodic, uneven — is precisely what makes it newly legible. We live in a period in which young people carry contradictory ideological scripts and uncertain inheritances, asked to build identities from fragments. A tidy novel would falsify that condition. The Adolescent does not. Its disorientation matches ours.

**Why this matters:** Sometimes a lesser-known book clicks into place when its disorder matches the moment — and The Adolescent is being reread as a map of that disorder, not a failed masterpiece.

## Paper of the Day

### Coverage collapse and the reset that saves post-training

Today’s paper is a theory paper from the arXiv [archive], by Audrey Huang and colleagues. The question is simple: why does language-model post-training sometimes stall even when the reward signal keeps improving? The answer they propose has a name — coverage collapse — and it gives people who train models a new debugging lens.

The story begins with how modern language models are tuned. After a base model is trained, labs use reinforcement learning to make it produce better answers. The workhorse algorithms are variants of REINFORCE, the basis for PPO and GRPO. The assumption has been that if the model gets reward signal, it will gradually shift its probabilities toward good responses. This paper shows that assumption is not guaranteed.

The authors find that REINFORCE can drive the probability of optimal responses to near zero, even as the measured reward improves. The model gets better on the metric, but it loses the ability to generate some of the very responses that made it useful. That is coverage collapse. It does not require noisy gradients or bad data. It happens even with exact gradients. It also persists under KL regularization to the base model — the standard fix.

Why does this matter practically? Because once coverage collapses, optimization can require exponentially many steps to recover, despite the model having had good initial coverage. A training run can look healthy according to the reward curve and still be quietly destroying response diversity.

The paper’s second contribution is a fix. The authors show that repeatedly resetting the KL reference to the most recent policy — rather than always regularizing back to the base model — mitigates coverage collapse. They formalize this intervention as Approximate Policy Mirror Descent, or APMD, a meta-algorithm that solves a sequence of KL-regularized RL subproblems. This reframing gives coverage-preserving guarantees: the sample and gradient complexity are governed by the base model’s response coverage.

**Why this matters:** If you are fine-tuning a model and the reward rises while real performance plateaus, do not just look at the learning rate. Check whether the policy has lost access to good responses it once had — and try resetting the reference rather than anchoring to the base.

## One Idea

### The impossibility of nothing, and the loop that made complexity

This section is about two mental tools, and the first comes from a new Aeon [EE-on] essay by Andrew Brenner on the oldest question: why is there something rather than nothing? Brenner offers an answer that is neither simple nor easy. The argument is not the usual religious one, and it is not the usual scientific one. It is a challenge to the question itself. Absolute nothing, the essay suggests, may not be a genuine possibility, because possibility is a feature of existing systems. We cannot step outside existence to ask whether existence as a whole could have failed. The sentence “there might have been nothing” feels meaningful, but its meaning may depend on there being someone or something to frame it.

The portable idea is this: before asking the biggest why, check whether the alternative is actually coherent, or just grammatical. In conversation, when someone asks why there is more inequality rather than less, pause. Ask what the alternative “no inequality” would actually require. Sometimes the alternative is not a possible state; it is a rhetorical construction. In your own research, the same move applies to null models. A null hypothesis that is not internally coherent is not a default. It is a hidden assumption. The attempt to imagine absence — no effect, no state, no baseline — can reveal what you were taking for granted.

The second tool comes from Quanta Magazine’s long read on how chemistry became biology. The key idea is that complexity did not arrive with a blueprint. Around 4.6 billion years ago, on a violent cooling Earth, simple molecules found loops. Some reactions produced products that made more of those reactions happen. Complexity was not added from above; it accumulated from below, through feedback. You do not need a designer to get order. You need a loop that makes the next step more likely.

These two ideas pair well. The first says some grand questions dissolve when you interrogate the alternative. The second says many grand systems build themselves when a small loop becomes self-reinforcing.

**Why this matters:** The feeling of profundity can be a trap: sometimes the deepest question is badly posed, and sometimes the deepest explanation is an ordinary loop you have not noticed.

## Quick Reviews

No reviews are due this morning — the retrieval deck is clear.

_End of brief._