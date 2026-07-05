# Agent Instructions

This project uses a persistent Project Brain.

Before performing any non-trivial task, read:

`PROJECT_BRAIN_PROTOCOL.md`

Then follow the protocol.

The Project Brain is available at:

`.project-brain/`

Its entry point is:

`.project-brain/PROJECT-BRAIN.md`

Do not read the entire vault by default.

Start at `PROJECT-BRAIN.md`, identify relevant concepts, and traverse only the connected notes relevant to the current task.

Before making a significant architectural or implementation decision:

1. Check relevant Project Brain history.
2. Inspect current source code.
3. Identify previous decisions, incidents, failed approaches, and lessons.
4. Make the decision using both historical context and current evidence.

After meaningful work, evaluate whether durable project knowledge was created.

If durable knowledge changed, update the Project Brain according to `PROJECT_BRAIN_PROTOCOL.md`.

Do not update the brain for routine edits or temporary debugging.

The goal is to avoid repeating mistakes and preserve project experience across agents and sessions.
