---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Hugging-Face-Spaces-Push-Failure]]"
---

# Decision: Clean-Slate Git Push for Hugging Face Spaces CI/CD

## Context & Problem
To provide a live public playground, S.A.R.A.L. is synced with Hugging Face Spaces. The initial integration used a standard GitHub Actions CI workflow to push the git repository directly to the Hugging Face remote.
This failed due to:
1. **Divergent History:** Out-of-band updates on Hugging Face (such as space restarts or metadata edits) caused git branch conflicts.
2. **File Size Constraints:** Hugging Face Spaces restricts pushes that include large intermediate cache files or local SQLite databases.

---

## Options Considered
1. **Standard Git Pull and Merge:** Pull Hugging Face changes, merge them locally, and push.
   * *Cons:* Merging divergent branches in an automated CI runner is error-prone and frequently stalls builds.
2. **Clean-Slate Force Push Script:** Script the CI runner to copy the clean workspace, initialize a fresh Git repository, commit the files as a single squashed commit, and force-push.
   * *Pros:* Bypasses git history conflicts and ignores untracked local directories.

---

## Choice Made
* **Clean-Slate Force Push Script:** Implemented a workflow that wipes the target history on HF Spaces, and force-pushes a single squashed commit containing the current state of the main branch.

---

## Trade-offs & Consequences
* **Pros:** Builds deploy reliably. Bypasses divergent history and prevents pushing large git histories or cache files.
* **Cons:** Destroys the Git commit history on the Hugging Face Space repository itself, though the master history remains preserved in the primary GitHub repository.
