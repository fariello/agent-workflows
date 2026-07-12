# IPD: Mirror the workflow-pointer block into existing CLAUDE.md / GEMINI.md (reach Claude Code + Gemini)

- Date: 2026-07-12
- Concern: instruction-file reach / correctness. Research
  (`docs/research/2026-07-12-agent-instruction-file-discovery-survey.md`) established that our
  `AGENTS.md`-only pointer does NOT reach two of the most-used agents: **Claude Code never auto-reads
  `AGENTS.md`** (it reads `CLAUDE.md`) and **Gemini CLI defaults to `GEMINI.md`**, not `AGENTS.md`.
  This is NON-RECOGNITION (the tool never looks at AGENTS.md), not conditional shadowing. So a repo
  using Claude Code or Gemini never sees our workflow pointer (or, once Theme D lands, the brain-dir
  mirroring rules). Revises the provisional D59 ("generate neither").
- Scope: `agent_workflows/engine.py` (generalize the AGENTS pointer write to ALSO refresh the same
  managed block in an existing `CLAUDE.md`/`GEMINI.md`), the install summary line, tests, docs, and
  DECISIONS (revise D59; note D21). CORE ONLY: patch native files that ALREADY EXIST; never create
  them. Detection/adapters/doctor-report/Zed-first-match-shadowing/`.agents/AGENTS.md`-revisit are
  DEFERRED to a follow-on.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after the GPT-5.6 research
  survey. Maintainer chose the core (mirror into existing CLAUDE.md/GEMINI.md) + revise D59, deferring
  the doctor/adapters/shadowing machinery. Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-B (uninstall already strips the block -> generalize remove_agents_pointer), PR-C (native writes
  inherit backup+stage+no-commit via the shared helper). No BLOCKER/HIGH. Status -> reviewed.

## Project conventions discovered (Step 0, VERIFIED against source)

- Today, `update_agents_pointer` (engine.py:1007) writes the managed block to ONE resolved file via
  `resolve_agents_file` (:988, candidates `AGENTS.md` then `.agents/AGENTS.md`, :102) using
  `agents_pointer_block()` (:541). The write contract (reuse it VERBATIM): exactly-one-well-formed
  marker pair -> replace in place; malformed/partial -> append; existing-no-markers -> append;
  none -> create with a header. Backs up before first edit (unless --no-backup), stages (never
  commits), honors --dry-run, idempotent ("pointer already current").
- Research verdicts we are acting on (survey sections 3A/3B/3E + 5): (b) mirror the SMALL managed
  block into existing `CLAUDE.md`/`GEMINI.md` (NOT import all of AGENTS.md - avoids duplicated
  context and respects user-owned content); `.agents/AGENTS.md` is NOT a real project-wide location
  for any mainstream agent (dead-end fallback). We are NOT doing (c) detection/doctor/shadowing yet.
- The block is identical across files (same `AGENT-WORKFLOWS:BEGIN/END`), so a repo that loads BOTH
  files (e.g. Cursor CLI) sees one small pointer duplicated - acceptable and easy to dedupe/remove.
- PLAN-REVIEW VERIFIED (PR-B): uninstall ALREADY strips the AGENTS block via
  `remove_agents_pointer` (engine.py:1964, called from `uninstall_repo` :1939, "leaves the user's own
  AGENTS prose intact"). So change #3 GENERALIZES `remove_agents_pointer`, not net-new behavior. The
  marker-merge write logic is currently INLINE in `update_agents_pointer` (engine.py:1026-1053), so
  "factor into a shared helper" is accurate and the right refactor.
- PLAN-REVIEW VERIFIED (PR-C): the AGENTS write contract already backs up before first edit and stages
  (never commits); the native-file writes MUST inherit the same backup+stage+no-commit behavior (the
  shared helper gives this for free). Confirm the backup path (`create_backup_path`) is used for each
  native file too, so a user's pre-existing CLAUDE.md/GEMINI.md is backed up before its first edit.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Generalize the pointer write to additional EXISTING native files.** Add a constant
   `NATIVE_AGENT_FILES = ("CLAUDE.md", "GEMINI.md")` (repo-root). After the existing
   `update_agents_pointer` handles the resolved AGENTS file, for each native file that ALREADY EXISTS
   at the repo root, refresh the SAME managed block in it using the identical marker/backup/fail-safe/
   idempotent/dry-run/stage logic (factor the marker-merge into a shared helper so AGENTS.md and the
   native files share one implementation - single source of truth). NEVER create a native file that
   does not exist (creating a CLAUDE.md/GEMINI.md in a repo that has none would inject unwanted
   context and pick a side the repo did not choose).
2. **Report each mirrored file** in the install summary (e.g. `CLAUDE.md: refreshed workflow pointer`
   / `GEMINI.md: not present (skipped)`), consistent with the existing `AGENTS.md:` status line.
3. **Uninstall symmetry.** Generalize `remove_agents_pointer` (engine.py:1963-1964) so `uninstall_repo`
   removes the managed block from the native files too (only the block, leaving user content), matching
   AGENTS.md. A native file left with ONLY the block + whitespace after removal is still left in place
   (we never created it, so we never delete the user's file - only our block).
4. **Tests** (`tests/test_installer.py` / `test_cli.py`): existing `CLAUDE.md` gets the block
   (idempotent re-run = one block; user prose preserved; malformed marker -> safe append); existing
   `GEMINI.md` likewise; ABSENT native file is NOT created; dry-run reports without writing; uninstall
   removes only the block. Reuse the temp-repo harness.
5. **Docs + DECISIONS.** Commit the research survey + its prompt under `docs/research/`. README /
   ARCHITECTURE: note that the installer also refreshes an existing `CLAUDE.md`/`GEMINI.md` so the
   workflow pointer reaches Claude Code and Gemini (which do not read `AGENTS.md`). REVISE D59 (record
   the evidence: AGENTS.md-only misses Claude Code + default Gemini via non-recognition; the decision
   is now "mirror the managed block into existing native files, never create them"; the doctor/
   adapters/shadowing/`.agents/AGENTS.md` items are a named follow-on). Add a DECISIONS entry (Dnn) for
   this change referencing the survey.

## Deferred / out of scope (named follow-on IPD)

- Detecting a tool whose native file is ABSENT and offering to CREATE a tiny adapter (opt-in).
- A canonical-import mode (`@AGENTS.md` in CLAUDE.md/GEMINI.md) for repos that want AGENTS.md as the
  single source of ALL policy (different semantics from publishing our pointer).
- Zed / first-match shadowing detection (`.rules`/`.cursorrules`/... can beat AGENTS.md).
- An `aw doctor`-style coexistence report.
- Revisiting the D21 `.agents/AGENTS.md` fallback (survey: not a mainstream project-wide location;
  preserve-and-warn rather than treat-as-equivalent). Capture as its own decision/IPD.

## Open questions (v1 leans for review)

1. Native file set: `CLAUDE.md` + `GEMINI.md` for v1 (the two confirmed non-readers). Add others
   (e.g. `AGENT.md` singular for some Gemini Code Assist surfaces) later. (Lean: just the two.)
2. Root-only, or also nested/`.claude/CLAUDE.md`/`~/.claude`? (Lean: repo-root only for v1; global/
   nested are the user's domain, not ours to edit.)
3. Should mirroring be default-on, or gated behind a flag? (Lean: default-on but ONLY for files that
   already exist - zero new files, minimal intrusion, so default-on is safe and matches the goal.)
4. Uninstall symmetry: RESOLVED (PR-B) - uninstall already strips the AGENTS block via
   `remove_agents_pointer`; generalize it to the native files. Confirmed by source, not deferred.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened against source:
- PR-B (verified, tightened): uninstall ALREADY removes the AGENTS block (`remove_agents_pointer`,
  engine.py:1963-1964); change #3 generalizes that function rather than adding new behavior. Also
  confirmed the never-delete-the-user's-file rule (we only strip our block).
- PR-C (guardrail added): the shared write helper must carry the existing backup-before-first-edit +
  stage-never-commit contract to each native file (`create_backup_path` per file), so a user's
  pre-existing CLAUDE.md/GEMINI.md is backed up before its first edit.
- Rubric G (KISS): scope is correctly held to the core (patch existing files only; never create),
  with detection/doctor/adapters/shadowing explicitly deferred - good complexity discipline.
- Rubric B/H (safety/principles): never creating native files and touch-only-our-region respects
  user-owned content (P10, "touch only its region"); no security regression.
No BLOCKER/HIGH findings; OQ1-4 leaned/resolved. This IPD does not self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ1-3 leans), execute changes 1-5, validate (suite green),
commit (never push), `git mv` to executed/. Not auto-executed.
