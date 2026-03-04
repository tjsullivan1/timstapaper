# Decisions

## Decision: Remove .squad/ from main branch

**Date:** 2025-07-24  
**Author:** Holden (Lead)  
**Status:** Executed

### Context

Two commits (`fef3942`, `55fcbcd`) pushed `.squad/` runtime files directly to `main`. The guard workflow at `.github/workflows/squad-main-guard.yml` explicitly forbids `.squad/` and `.ai-team/` on protected branches (main, preview, insider).

### Decision

Remove `.squad/` files from the git index on `main` using `git rm --cached -r .squad/`. This:
- Unblocks the guard workflow on main
- Preserves all local working copies
- Does NOT add `.squad/` to `.gitignore` — these files are meant to be tracked on `dev` and feature branches
- Does NOT touch `.squad-templates/` or `.github/` — those belong on main

### Outcome

Commit `253b7af` pushed to `origin/main`. 22 files removed from tracking. Local copies and dev branch history unaffected.
