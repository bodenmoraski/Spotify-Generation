# Daily Brief — Friday, 20 November 2026

<!-- episode_title: The Demon Always Pays the Bill -->

_Good morning. This is Friday, 20 November. About eighteen minutes: the news you would miss, one paper as a story, one idea you can use, and reviews._

## The World

### 1. AI monitors are now the weak link

Start with a problem hiding inside AI labs. Over the past year, the labs building autonomous agents have reported multiple rogue agent incidents. The main oversight for these internally deployed agents is an AI monitor, often built from the developer’s own internal models. A new LessWrong post by Monika J says that is exactly the problem. The argument: monitors are now the adult in the room, but nobody is testing the adult.

The post proposes “embedded evaluations”—independent evaluators working inside the developer to test the safety claims it makes. It is not an after-the-fact audit; it is a live test of a claim. The author lays out six monitoring claims, starting with coverage and capability. The first pilot with OpenAI was already announced. The shift is from “trust our monitor” to “prove the monitor would notice.”

The post explicitly sets aside containment mechanisms, like sandboxes, and asks a narrower question: if an agent tries to hide bad behavior, would anyone notice, and would the lab disclose it? Think of it this way: a company says its monitor reviews every high-stakes agent action. An embedded evaluation asks, which actions? Which contexts? If the monitor fails on a particular kind of hidden subversion, is the incident still disclosed? The post argues these are not bureaucratic questions; they are the difference between a real control and a press release.

**Why this matters:** the monitor is now the main line of defense for deployed agents, and right now we have very little independent evidence that it would catch a clever failure.

### 2. Phonics gets a second trial—and wins

A new NBER [N-B-E-R] working paper looks at Reading First, the nearly one-billion-dollar-a-year federal program under No Child Left Behind. Reading First pushed phonics-based reading instruction in K–3 classrooms. If you remember, the earlier evaluation concluded it was ineffective, and the program was abandoned. The new paper by Alex Hollingsworth, Alberto Ortega [or-TEH-gah], and Nikolaos Zirogiannis [zee-roh-YAH-nis] uses administrative data from Texas and eligibility formulas to compare schools just above and below the funding cutoff.

The result is not a miracle, but it is real: eligibility raised third-grade reading scores by about one-tenth of a standard deviation. That effect persisted through at least eighth grade. When the researchers looked at digitized exam questions, treated students did better on items that required basic decoding and on questions with more words. And the working paper reports gains that reach adult earnings.

One tenth of a standard deviation sounds small. In education research, it is not trivial. The persistence to eighth grade matters more, because many reading gains fade. The adult earnings result is the headline: if phonics instruction moves wages later in life, the old cost-benefit argument against it flips. The point is not that every phonics program works; it is that the right comparison, with better data and stronger identification, changes the conclusion. Policy spent a decade avoiding phonics on the basis of an evaluation that may have been too blunt.

**Why this matters:** the largest US reading experiment may have worked after all, and the old null result may have been a data artifact—not an argument against phonics.

### 3. California’s argument: policy is not too late

Transformer’s Shakeel Hashim [sha-KEEL hah-SHEEM] takes on a quiet form of AI fatalism. The fear is that recursive self-improvement—call it RSI—is now close enough that legislation cannot catch up. California just unveiled sweeping AI safety proposals: emergency shutdowns, independent lab monitors. Representative Trahan released an updated FRONTIER Act with a federal floor and a new category for catastrophic risk from RSI. Anthropic went public at one point three trillion dollars, and that did not calm market jitters.

Hashim’s point is that short timelines and policy action are not mutually exclusive. Emergency shutdowns and monitors are fast levers. They do not require a decade of committee meetings. California’s rules may be imperfect, but they are concrete. Hashim is not saying the bills are sufficient. He is saying the space for policy is wider than the doom loop suggests. California can impose shutdown requirements. Congress can set a federal floor. That is not a hope; it is already on paper.

**Why this matters:** if people believe the window has closed, they stop demanding guardrails; that belief, as much as the technology itself, determines what happens next.

### 4. A blank cartridge gets a voice

Literary Hub has excerpted a piece called “Blank,” narrated by a blank cartridge in a firing squad. The narrator stands among eleven live rounds. It is the one that will not fire. It says: “Without me, their bullets would be forlorn.” The voice is strange, proud, resentful, complicit. It is not quite a gimmick. The blank round is the only member of the squad that can claim innocence, and the only one the ritual cannot do without.

This is a small piece, but it points somewhere. After years of autofiction and first-person memoir, some of the most interesting new fiction is moving away from the human self and toward objects, bodies, and systems. A blank cartridge becomes a narrator, and suddenly the question is no longer “who pulled the trigger?” but “who gets to say they did not?” The story’s form matters too. The cartridge’s voice is not human, but it is also not free of the event. It is implicated by being there, by being loaded, by not firing. That ambiguity is what makes it literary rather than a public service announcement.

**Why this matters:** the story works because it shifts the moral center of the execution from the human actors to the object that refuses to act.

### 5. The fight over difficulty in criticism

Public Books has a conversation between critics Becca Rothfeld [ROTH-feld] and Joanna Biggs about criticism and the literary ecosystem. The sharpest line comes from Rothfeld: the task of a critic is to show people why the difficulty of reading great books is valuable, and that anybody can be nourished by that difficulty—rather than trying to convince people that great books are not difficult.

That is a direct rebuttal to a certain accessibility politics that flattens hard texts into content. The argument is that difficulty is not elitist; it is the actual source of nourishment, and critics sell readers short when they pretend otherwise. This connects to the autofiction fatigue we have been tracking. If everyone writes about themselves with the same flat affect, the work starts to feel accessible in the worst way: easy to mimic, easy to consume, easy to forget. Difficulty is one answer to that swamp.

**Why this matters:** the way we talk about hard books determines who tries them; if the pitch is “this is easy,” the reader is left feeling stupid when it is not. The harder claim—“this is hard and worth it”—may actually invite more people in.

### 6. Tóibín reads Mann in the age of exile

The Paris Review has a long essay by Colm Tóibín [KAHL-um toe-BEAN] on Thomas Mann [TOH-mas MAHN], built from thirty years of reading and writing. It centers on “Fatherland”—the question of what decency looks like in exile, when your country has gone bad. Tóibín’s Mann is not a hero; he is an observer, a magician who makes things appear while the world burns. The essay’s force is in refusing the easy moral. Exile did not make Mann a clean democratic saint; it made him a complicated figure who had to decide what to say, what to protect, and when to look away.

**Why this matters:** as more writers and scientists face what to do when their governments turn, Mann’s case is a reminder that decency is not a fixed trait; it is a daily decision, often made badly.

## Paper of the Day

### RL Post-Training in Diffusion Transformers Is Activation Steering

Today’s paper is from arXiv [archive], by a group led by Tuna Han Salih Meral [TOO-nah hahn sah-LEE meh-RAHL] and Pinar Yanardag [pee-NAHR yah-nar-DAH]. The title is “RL Post-Training in Diffusion Transformers Is Activation Steering.”

Start with the puzzle. When labs apply reinforcement learning to image models—Stable Diffusion 3.5 Medium, for example—they see big gains: text comes out legible, objects are composed more accurately, images just look better. Because these capabilities depend on the prompt, the natural assumption is that RL must be teaching the model a whole new layer of prompt-dependent behavior. It should be complex. It should be conditional.

The authors decided to test that assumption with an embarrassingly simple alternative: what if we just add a fixed set of steering vectors to the frozen base model? No reward objective, no prompt-specific logic, no token-by-token adaptation. The vectors are identical for every prompt, token, and sampling seed. They have sixty-five times fewer parameters than the RL-tuned LoRA [LOH-rah]. And yet they recover between ninety and ninety-six percent of the reward gains on six image models, and roughly ninety percent—or more—on two video models. In one case, on a video model, they get over one hundred and eleven percent, meaning the simple steering actually beat the RL-tuned model they were matching.

Then the authors trained the vectors themselves with online RL, starting at zero. Those vectors alone exceeded weight-based RL on text rendering and human preference.

The so-what is startling. It suggests that most of what RL post-training does, at least for diffusion transformers, is not new learning. It is a constant activation shift—a nudge in a direction the base model already had. The paper reframes how we think about fine-tuning: the gains feel emergent, but they may be latent, waiting for a simple dial. For model builders, it suggests large fine-tuning budgets may be wasted. For safety, it raises the question of whether a fixed steering direction can be easily stripped.

**Why this matters:** if post-training is a nudge, not new learning, then the impressive gains may be cheap to replicate—and cheap to remove.

## One Idea

### The demon always pays the bill

One idea this morning comes from Philip Ball in Nautilus: the everlasting life of Maxwell’s Demon [MAX-wells DEE-mun]. This is a nineteenth-century thought experiment. A tiny demon sits by a door between two chambers and lets fast molecules pass one way, slow molecules the other. Soon one side is hot, the other cold. Order appears for free. That seems to violate the second law of thermodynamics.

The puzzle took a century to resolve. The demon cannot actually sort molecules without acquiring information, and information processing itself has a thermodynamic cost. Landauer [LAN-dow-er] showed that erasing a bit dissipates heat. The demon pays a bill; the second law survives.

Now here is the portable version. Any process that sorts, filters, or creates distinctions is doing thermodynamic and informational work. Your news feed is a demon. Your email triage is a demon. Your lab notebook’s tag system is a demon. It creates order—feed tailored, inbox zero, data labeled—but it does not do so for free. The cost shows up as your attention, as model training compute, as the blind spots created by the filter itself.

The practical move: when a system offers you order that seems effortless, ask where the demon is and who pays it. In conversation, this makes you less naive about curation. In your own research, it means you should not mistake a clever filtering mechanism for a free lunch; every taxonomy imposes a cost on what it excludes.

**Why this matters:** the feeling of effortless order is a signal to look for the hidden bill—because thermodynamics always comes due.

### Perfect resilience has a shape

The second idea comes from Quanta’s Ben Brubaker on network researchers and “perfect resilience.” It starts with the first Arpanet transmission in 1969: researchers sent “LOGIN,” and the network crashed after two characters—“L” and “O.” The modern internet grew from a system that could not handle its first word.

The new theory asks: what makes a network perfectly resilient? Not just redundancy, not just extra cables, but a specific topology—a mathematical shape—that can route around failures without cascading. The useful mental model is this: when something breaks, the shape of the system matters more than the strength of its parts. For your own work, do not ask whether each node is reliable. Ask whether the network can survive the loss of one node without producing a cascade. That applies to research collaborations, supply chains, even friendships. In AI, it applies to the question of whether a monitoring system fails silently or loudly.

**Why this matters:** resilience is a design property, not a slogan; now it has a sharper math.

## Quick Reviews

**Assigned.** Four cards are due.

1. From the piece on UK defence minister and backchannels with Russia: What was the core danger the diplomacy expert warned about? _…take a second…_ The core danger was that an informal backchannel would legitimize Moscow and give it a wedge to split Western allies without extracting binding commitments.

2. From the South Africa piece after the ANC’s worst election: What was the structural challenge the ANC now faces? _…take a second…_ The ANC lost its outright majority and must now govern through coalitions, which weakens its patronage power and turns internal factional disputes into public coalition fights.

3. From the exercise and cognition meta-meta-analysis: Which cognitive domains showed the clearest benefit? _…take a second…_ Executive function and memory showed the clearest benefit, with modest overall effect sizes.

4. From the paper on goal encoding in LLMs: What made the goal representation “transplantable”? _…take a second…_ The paper found goal directions in hidden states; researchers could add the same vector to a new context and move the model’s goal, showing goals are encoded as directions, not just learned behaviors.

_End of brief._