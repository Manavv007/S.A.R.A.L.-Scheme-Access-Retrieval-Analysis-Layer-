---
type: incident
project: S.A.R.A.L.
status: resolved
confidence: confirmed
created: 2026-07-05
related:
  - "[[Clean-Slate-Push-HF-Spaces]]"
---

# Incident: Hugging Face Spaces Git Push Failures

## Context
A GitHub Actions CI workflow was set up to sync S.A.R.A.L. code changes automatically with the Hugging Face Spaces repository remote.

---

## Symptom
The GitHub Action build failed consistently at the Git push stage with errors:
`error: failed to push some refs to 'https://huggingface.co/spaces/...'`
`Updates were rejected because the remote contains work that you do not have locally.`

---

## Initial Belief
It was believed that the credentials (token permissions) were invalid or expired.

---

## Investigation & Root Cause
* **Investigation:** Inspected the Git log of both the GitHub main branch and the Hugging Face Spaces branch.
* **Root Cause:** Hugging Face Spaces allows users to edit README metadata via their web GUI. Additionally, the space's builder generates internal tracking files. These updates caused the remote branch to diverge, preventing standard fast-forward merges.
* **Secondary Root Cause:** The repository contained intermediate scraper data, cache directories, and local SQLite database files that exceeded Hugging Face's single-file size push limits.

---

## Resolution Attempts
1. **Git Pull before Push:** Configured the action to run `git pull --rebase` before pushing.
   * *Result:* Failed due to merge conflicts in compiled files and cache files.
2. **Clean-Slate Push Script:** Designed a script to copy clean files, create a new commit, and force-push.

---

## Final Resolution
Implemented a squashed commit force-push script inside the CI pipeline (`clean_slate_push.sh`). The script:
1. Creates a clean temp directory.
2. Copies only required repository source code.
3. Initializes a new Git repository.
4. Commits files under a single commit message.
5. Runs `git push --force` to override divergent histories on Hugging Face Spaces.

---

## Lessons Learned
Syncing repositories to secondary target hosting platforms (like Hugging Face Spaces or Streamlit) via CI works best when histories are squashed and force-pushed, bypassing file size limits and divergent branch conflicts.
