# Project Brain Protocol

This repository has a persistent Project Brain located at:

`.project-brain/`

The Project Brain represents the accumulated mental model of engineers who have worked on this project over time.

It contains:

* current architecture
* historical architecture
* components and relationships
* decisions and reasoning
* incidents and root causes
* failed approaches
* experiments
* lessons learned
* important changes
* unresolved questions

The Project Brain is not ordinary documentation.

It is persistent project memory.

# Mandatory Workflow

For every non-trivial task, follow this process.

## Step 1 — Orient

Read:

`.project-brain/PROJECT-BRAIN.md`

Do not read the entire Project Brain.

Use the entry point to identify the parts of the graph relevant to the current task.

## Step 2 — Retrieve Relevant Memory

Determine:

* Which components are affected?
* Which concepts are involved?
* Have similar problems happened before?
* Were relevant architectural decisions made?
* Are there known constraints?
* Were previous approaches attempted and rejected?

Follow relevant `[[wikilinks]]`.

Read connected notes until you have enough historical and architectural context to work safely.

Prefer this traversal pattern:

Current component
→ related decisions
→ historical incidents
→ failed experiments
→ lessons learned
→ current constraints

Stop when additional notes are no longer materially relevant.

## Step 3 — Build a Context Brief

Before planning significant work, internally establish:

### Current state

How does the relevant system work today?

### Historical context

How did it arrive at this state?

### Relevant decisions

What previous decisions constrain the task?

### Past failures

Has something similar failed before?

### Lessons

What knowledge should influence the current approach?

### Unknowns

What important information is still missing?

Do not blindly follow old decisions.

If current evidence suggests an old decision is no longer valid, identify that explicitly.

## Step 4 — Inspect Current Reality

The Project Brain may be outdated.

Always verify relevant claims against:

* current source code
* current configuration
* current dependencies
* current infrastructure
* current Git state

Use this priority when conflicts occur:

1. Current verified runtime behavior
2. Current source code and configuration
3. Recent explicit developer decisions
4. Project Brain
5. Historical Git evidence
6. Assumptions

If the Project Brain conflicts with current reality, do not silently ignore the conflict.

Record the change.

## Step 5 — Plan and Work

Use both:

* current repository evidence
* relevant Project Brain context

When proposing a change, consider:

* Does this contradict an earlier decision?
* Does it reintroduce a known failure?
* Does it repeat a failed experiment?
* Which components could be affected indirectly?
* What assumptions are being made?

## Step 6 — Verify

After implementation:

* test the change
* inspect unexpected side effects
* compare intended behavior with actual behavior
* determine whether any assumptions were wrong

Do not update the Project Brain with unverified claims as confirmed facts.

## Step 7 — Decide Whether Memory Changed

After meaningful work, ask:

* Did architecture change?
* Did a component's responsibility change?
* Was an important decision made?
* Did an incident occur?
* Was a root cause discovered?
* Did an approach fail?
* Was an experiment performed?
* Was an old assumption disproved?
* Was a reusable lesson learned?
* Did the relationship between components change?

If all answers are no, do not update the Project Brain.

Avoid memory pollution.

## Step 8 — Update the Graph

When durable knowledge was created:

1. Update existing nodes when the concept already exists.
2. Create a new atomic node only when a genuinely new concept exists.
3. Add `[[wikilinks]]` to related nodes.
4. Update relationship frontmatter.
5. Update the timeline when historically significant.
6. Update `PROJECT-BRAIN.md` only when the high-level project model changed.

Never create duplicate nodes for the same concept.

## Memory Quality Rules

Never store:

* temporary debugging output
* routine code edits
* raw conversation transcripts
* speculative claims presented as facts
* information already obvious from reading one line of code
* secrets, credentials, tokens, or API keys

Prioritize:

* WHY over WHAT
* causality over chronology alone
* decisions over implementation trivia
* root causes over symptoms
* lessons over logs
* relationships over isolated notes

## Confidence

Every historical or causal claim must be classified as:

* `confirmed` — directly supported by evidence
* `inferred` — strongly suggested by available evidence
* `unknown` — unresolved

Never convert inference into fact without new evidence.

# Core Principle

The Project Brain should allow a future AI agent to benefit from experience it did not personally live through.

Before important work:

Consult the brain.

After important learning:

Improve the brain.
