# Evidence - assess documentation 20260704-193843

Read-only inspection. No files were modified during the assessment.

## Ground truth gathered (to verify doc claims against)

- Command shims per tool: 15 (`ls .opencode/commands | wc -l`).
- Command set: advise, assess, assess-all, getting-started, incident, list-workflows,
  migrate, plan-review, release-notes, release-review, release-review-plan, scaffold,
  setup-repo, spec, verify.
- Manifest non-catalog command rows: 15 (matches).
- Assess concern lenses: 29 (`ls assess/lenses/*.md | wc -l`).
- Advise personas: 7.
- Tools: `assess/tools/scan_secrets.py`, `setup-repo/tools/setup_tools.py`,
  `verify/tools/run_checks.py`.
- Framework version: `20260704-01` (`.agents/workflows/VERSION`).
- Plans lifecycle dirs present: `.agents/plans/pending/`, `.agents/plans/done/`.

## Documents inspected

- `README.md` - full read; internal file references all resolve; core-workflows table has
  13 `/`-rows (12 core + `/advise`; `/assess` documented separately). Accurate. Mentions
  `scan_secrets.py`, versioning, `--version`.
- `ARCHITECTURE.md` - full read (lines 1-274). Stale: assess model (197-203), by-tool
  examples (259), file tree (26-35), missing workflows (no verify/advise/assess-all/spec/
  incident/release-notes/migrate/list-workflows/getting-started), no VERSION/tests mention,
  tools list missing run_checks.py.
- `CONTRIBUTING.md` - full read; doc-sync checklist step 3 covers `assess-*` only (23-24);
  step 5 requires README+ARCHITECTURE accuracy (the lapsed control). Secret-scanning
  section accurate; Self-tests section present and correct.
- `AGENTS.md` - pointer block only; accurate.
- `.agents/workflows/index.md` - "Running a workflow (by tool)" section exists at line 79
  (confirms the README/ARCHITECTURE cross-reference, D-10). Manifest and prose current.
- `GUIDING_PRINCIPLES.md` - no stale command references.

## Commands run (read-only)

- `ls`, `grep -n`, `find -name '*Zone.Identifier'`, `date -u`, `cat` on the docs above.
- No git-state-changing commands during assessment.

## Sampling / limits

- Did not exhaustively read every one of the 29 lens files or 7 persona files as prose;
  the documentation lens targets repo docs, and those were spot-checked for count/accuracy
  only. Their writing style is the `prose` lens's domain, not this one.
