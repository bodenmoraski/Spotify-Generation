# Daily Brief — Friday, 13 November 2026

<!-- episode_title: The Goal Is Not a Ghost -->

_Good morning. About eighteen minutes: the news you would miss, one paper as a story, one idea you can use, and reviews. Let’s begin._

## The World

### 1. South Africa’s coalition math after the ANC’s worst showing

Start in South Africa. The African National Congress, the party of Nelson Mandela, in power since 1994, is now learning to govern without a majority. After its worst election result, the real contest is not nostalgia for the liberation movement. It is a scramble over coalition arithmetic.

The ANC has options, and each one changes what South Africa actually does. It can turn to the center-right Democratic Alliance, which demands fiscal discipline and policy concessions. It can turn to the populist Economic Freedom Fighters, whose economic nationalism could split the ANC internally. Or it can try a patchwork of smaller parties, which creates a government held together mainly by cabinet posts.

The local reporting spends less time on who gets which ministry and more on what the coalition means for land reform, for the state power utility Eskom [ESS-kom], and for black economic empowerment rules. The underlying fear is not that South Africa collapses. It is that a coalition engineered only to survive becomes a government unable to act, while unemployment remains above thirty percent and trust in the state keeps sliding.

**Why this matters:** South Africa is the continent’s largest industrial economy and a bellwether for whether liberation-era parties can survive the transition to coalition politics.

### 2. Independent AI auditors are already bottlenecked

Now to an AI policy story that is not about a model launch. Washington and Silicon Valley have been converging on a safety idea: independent verification organizations, or IVOs, should audit advanced AI systems. Massachusetts has a proposal that would give auditors advance access to models and the power to question AI companies.

It sounds strong. Then you hit the labor market. There are simply not enough people with the right mix of skills: enough machine learning to inspect model behavior, enough policy sense to judge risk, and enough independence to say no to a lab. Those people are being hired by the same labs they are supposed to audit, or they are still in graduate school. The people pushing for the oversight ecosystem are sounding the alarm, and the alarm is about staffing, not just authority.

This is a governance gap that will not be fixed by more legislation. It requires a training pipeline. That training takes years, and the policy proposals are moving faster than the people needed to carry them out.

**Why this matters:** An auditor shortage could quietly turn the boldest AI oversight proposals into a paper regime with no enforcement muscle.

### 3. Britain flirts with Russia backchannels

Britain’s defence minister is reportedly open to backchannel talks with Moscow. The argument sounds pragmatic: keep a line open, reduce escalation risk.

Diplomacy experts warn that it is more fraught than it looks. Russia has a long record of using backchannels to split Western allies, to test whether one country will accept negotiations on Russia’s terms, and to frame the war as a NATO project rather than an invasion. A private channel without a shared agenda can become a tool for managed ambiguity. The Kremlin hears one thing, London hears another, and Kyiv and Washington hear nothing.

The danger is not that people talk. It is that they talk in a way that gives Russia strategic patience without extracting any reciprocal gesture. That can quietly normalize the idea that Russia is a partner for stability while it continues fighting.

**Why this matters:** Backchannels are only as useful as the unity behind them, and unity is exactly what they can erode.

### 4. Southern Africa prepares for an intense El Niño

From machine-translated Portuguese coverage: SADC [SAD-see], the Southern African Development Community, is debating disaster preparation ahead of forecasts for an unusually strong El Niño [el NEEN-yoh].

The report is from a Brazilian outlet that follows regional diplomacy, and the tone is different from the usual wire summary. It is not a weather report. It is a governance question: can regional institutions preposition food, water, and health resources before the lean season hits?

Countries like Mozambique, Malawi, and Zimbabwe are still recovering from the last drought cycle. The fear is not just failed crops. It is failed supply chains and delayed regional funding. The local framing emphasizes who pays and who waits, not just rainfall projections. The conversation is happening now, before a crisis, which is itself notable.

**Why this matters:** Early warning only matters if regional plans move faster than the disaster does.

### 5. The status-seeking model of migration gets a pushback

Tyler Cowen at Marginal Revolution offers a sharp two-step against the fashionable idea that people mostly seek relative status, not absolute income.

His evidence is migration. If people really preferred being high-status in a poorer society over being ordinary in a richer one, then western professionals would save up to live like kings in poor countries. Instead, doctors from Africa come to the United States even if they have to drive a cab. Migrants to Europe from the Middle East and Africa are not the poorest; they are relatively well off at home. Workers endure harsh conditions in Gulf labor markets because the pay is still better than their alternatives.

Cowen’s point is not that status does not matter. It is that absolute income, security, and opportunity often outweigh the status loss. That cuts against arguments that treat inequality as purely a status competition.

**Why this matters:** If you overrate zero-sum status-seeking, you design policy for a phantom motivation and ignore the very real pull of absolute gains.

### 6. Political paralysis gets a new fictional grammar

Finally, a culture argument worth having. Literary Hub runs a piece linking Kaveh Akbar’s [kah-VEH AHK-bar] novel _Martyr!_ and Sally Rooney to political paralysis.

Akbar’s protagonist, Cyrus Shams, lost his mother when the US Navy shot down Iran Air Flight 655 in 1988. The state never apologized. Cyrus cannot sue, cannot organize, cannot even make the event legible to most Americans. He writes poetry and grapples with martyrdom.

The reviewer’s argument is that this is not just one character’s grief. It is a generation of fiction that frames politics as inner weather rather than collective action. The political is felt, elegized, and internalized. That can be moving, but it can also naturalize helplessness. The essay asks whether the novel’s recursive grief is an aesthetic achievement or a symptom.

**Why this matters:** It names a real pattern in contemporary fiction: the political novel increasingly describes what politics feels like, not what it does.

## Paper of the Day

Today’s paper is called “Goal Encoding in LLMs,” by Arnab Sen Sharma, Eric Todd, David Bau, and colleagues, posted on arXiv [archive]. It asks a simple question that quickly becomes strange: when a language model carries out a multi-step task, does it have an internal representation of the goal, or is it just improvising one token at a time?

The researchers built a setting with several sub-tasks. Think of checking whether a word is a palindrome, or translating a line of code. They found something they did not entirely expect. A sparse set of attention heads encoded the next sub-goal. They could read out, in natural language, what the model was about to do: “I’m checking if a word is a palindrome.” That is already a finding. The model’s future action was there in the activations before it happened.

Then they tested whether the representation was causal. If they edited those heads, the model changed its next action. If they transplanted the goal encoding into a different environment, another programming language for example, the model pursued the same operation but executed it with a different sequence of tokens. So the goal representation is not just a label. It is plastic, in the way you would want a real goal to be: the same intention, different plan.

The puzzle came next. A transformer language model has no built-in recurrence. It has a fixed number of layers. It cannot carry a hidden state forward indefinitely. So how does it sustain a goal over many tokens? The answer they propose is almost anti-climactic, and probably more interesting because of it. The model does not need to carry a hidden state. It re-reads the task specification, compares it with the progress visible in the context, and reinstates the goal at each step. They call this a non-recurrent goal-seeking account.

That might sound like a limitation. It is not. It explains why the model can recover from detours, why a goal can stay active beyond the literal memory horizon, and why context matters so much. The goal lives in the room, not in the ghost.

**Why this matters:** If goal representations are localized and re-readable, they become more legible, and more editable, than the phrase “the model has a goal” suggests.

## One Idea

### A harder rule for helping people change

We are going to sit with the first idea, because it is counterintuitive and easy to get wrong. It comes from an essay on LessWrong by a writer named Jenn, called “How To Get A Friend To Leave An Abusive Relationship.” The title is difficult. So is the advice. But it generalizes far beyond abuse.

Here is the mechanic. People who work at women’s shelters say there is a reliable way to help someone leave, but it violates ordinary impulses. First, you make it known early that you dislike some aspects of the relationship or the abuser. You do not launch a campaign. You say it once, clearly. Then, after that, you support the person and their choices without reservation. You do not bad-mouth the abuser. You do not issue ultimatums. You make it clear you will be there no matter what.

Why does this work? Because when someone is inside a controlling relationship, any push on the abuser gets reframed, by the abuser and by the victim’s own defense mechanisms, as an attack on the victim’s judgment. If you keep pushing, the victim cuts you out. So you stop pushing. But you leave the early marker in place. Later, when the relationship becomes untenable, that marker does the work. The friend knows you saw the problem long ago, that you did not abandon them anyway, and that you will not say “I told you so.” That is the safe exit.

The general mechanism is uncomfortable: influence often increases when you stop trying to win. You plant one honest objection, then preserve the relationship. You let time and accumulated evidence do the persuasion. Suppose a colleague is stuck on a wrong claim. You can argue the point to death, or you can say once, “I think that assumption is wrong,” and then preserve the working relationship. Later, when their own data pushes back, they will hear it as discovery, not defeat. That is not passivity. It is a strategy for staying in someone’s life long enough to matter.

**Why this matters:** The feeling of ease is a trap, but so is the feeling of moral urgency. The work that feels worse in the moment, waiting, supporting, not arguing, is often the work that sticks.

### The body-brain shortcut

The second idea is shorter, but it points the same direction: the body is part of the study system. The Learning Scientists covered a meta-meta-analysis of 133 meta-analyses, which included 2,724 randomized controlled trials. The finding: exercise, even light intensity, improves general cognition, memory, and executive function across all populations.

That is not a news flash, but it is often ignored. The useful mental model is not “exercise is good for you.” It is: before you add another study hour, audit the body that will carry it. Sleep, feeding, walking. Cognitive gains are physiological.

**Why this matters:** In a high-stress, fast-paced environment, the easiest part of the system to forget is the body, and the cheapest intervention may be a walk.

## Quick Reviews

**Assigned.** Four spaced-repetition cards are due.

**South Africa elections: small parties.** What did that piece claim was the source of the small parties’ surprise gains? _…take a second…_ It mostly stayed at horse-race level: collapsing ANC turnout and local protest votes, with no new theory of realignment.

**COP31 climate security.** What was the main analytical weakness of the “fragile progress” piece? _…take a second…_ It offered generic calls to integrate climate into security planning but did not specify institutions, financing, or enforcement mechanisms.

**Experimentally validated digital twins.** What core result made ML on administrative data relevant to randomized controlled trials? _…take a second…_ ML models trained on administrative data reproduced RCT treatment-effect estimates well enough to function as policy “digital twins,” cutting the cost of evidence.

**Gopnik on _The Sun Also Rises_ at 100.** What did Gopnik argue about the novel’s dated prejudices? _…take a second…_ He argued they are not flaws to excuse; they are part of the novel’s hard, particular truth about a lost generation.

_End of brief._