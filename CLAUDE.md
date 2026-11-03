# CLAUDE.md — PrognosIQ session protocol

This file is loaded automatically at the start of every Claude Code session in
this repo. It exists so the project can continue smoothly across sessions and
across AI tools, no matter how big it gets.

## At session start (every time, no exceptions)

1. **Read `PROGRESS.md` (repo root) first.** It is the single source of truth:
   verified repo state, next task, real file/class names, rules, board, and
   gotchas. Do not trust any memory of a previous session over it — it is
   updated at the end of every session precisely so you don't have to guess.
2. **Check live state:** `git status --short --branch` and `git log --oneline -5`.
3. **Work from PROGRESS.md**, in this order of authority:
   - "FIRST ACTION" in the Git state section (if present — do it before anything)
   - "Next task" section (the current work item)
   - Rules section (always applies)
   - Board section (what Done / In progress / Backlog mean right now)
4. **If the project outgrew PROGRESS.md**, widen the sources, in order:
   `gh issue list` + `gh pr list` (GitHub issues/board), `apps/*/README.md`,
   `docs/` if it exists, then ask the user. PROGRESS.md should name these
   sources as they appear.

## At session end (every time)

1. **Update `PROGRESS.md` BEFORE stopping**: what was done this session,
   newly verified names/paths, board moves, and the concrete next step.
2. Commit the PROGRESS.md update together with (or right after) the session's
   work so the next session starts from the real state.
3. Keep the test suite green; record the verified test count in PROGRESS.md.

## Hard rules (full details in PROGRESS.md)

- **Workflow:** new branch off updated `main` → lint → code → tests green →
  commit → PR ("Closes #N") → squash-merge. Never commit straight to `main`.
- **Lint before every commit** (PROGRESS.md Rule 8):
  `~/prognosiq/.venv/bin/ruff check --fix apps/api && ~/prognosiq/.venv/bin/ruff format apps/api`
- **No bare `python`** — use `/home/dev/prognosiq/.venv/bin/python` (WSL, no
  python on PATH). Docker Desktop must be running first (Postgres container
  `prognosiq-db-1` on 127.0.0.1:5432) or tests and server fail at connect time.
- **Dev DB schema changes only via Alembic** (PROGRESS.md Rules 5–6, incl. the
  DuplicateTable desync procedure). `create_all` belongs to the test DB only.
- **Never code from memory** (Rule 1): paste verified names from PROGRESS.md,
  then adapt. SQLAlchemy `Mapped["OtherModel"]` forward references need an
  `if TYPE_CHECKING:` import or ruff reports F821 false positives.
