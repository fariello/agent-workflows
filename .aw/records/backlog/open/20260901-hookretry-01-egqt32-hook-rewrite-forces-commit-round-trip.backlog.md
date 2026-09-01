- Id: egqt32
- Status: open
- Set: hookretry
- Priority: medium
- Work-Kind: bug
- Summary: A mutating pre-commit hook (whitespace/eof fixer, formatter) rewrites a staged file and rejects, and offer_commit unstages and exits 1 instead of re-staging, so routine whitespace churn costs every agent a full commit round trip plus a mandated index re-verify

## Workflow history
- 2026-09-01 created (aw backlog): A mutating pre-commit hook (whitespace/eof fixer, formatter) rewrites a staged file and rejects, and offer_commit unstages and exits 1 instead of re-staging, so routine whitespace churn costs every agent a full commit round trip plus a mandated index re-verify

OBSERVED (maintainer, 2026-09-01): "it seems that the commit hook ALWAYS removed some whitespace and
you \"by contract\" need to re-verify. That seems extremely wasteful. How do we make it so this does not
happen?"

Both halves are real: the hooks DO rewrite on most commits, and the contract DOES then charge a
re-verify. The waste is the product of the two.

CAUSE 1: FOUR HOOKS REWRITE FILES AND THEN REJECT THE COMMIT. In `.pre-commit-config.yaml`:
`trailing-whitespace` (`:15-16`), `end-of-file-fixer` (`:17-18`), `ruff --fix` (`:31-33`), `ruff-format`
(`:34-35`). Their shared `exclude` regex covers ONLY `.agents/docs/research/`,
`.aw/records/docs/research/`, and `.aw/system/`. It does NOT cover `.aw/records/plans|backlog|specs`,
which is exactly where agents write most. (The `local` hooks are read-only refusals and never rewrite:
`local-leaks` `:42-47`, `ipd-executed-transition-gate` `:55-60`, `ipd-status-untooled-gate` `:69-74`.
No hand-written hook in `.git/hooks/` rewrites anything; all mutation comes from the four above.)

CAUSE 2: `offer_commit` MAKES EXACTLY ONE ATTEMPT AND GIVES UP. `agent_workflows/git_commit_helper.py`:
the commit at `:245`, and on `rc != 0` (`:246`) it runs `git reset --quiet HEAD -- *our_staged` (`:247`)
and returns `STATUS_ERROR`. There is NO retry loop, no detection that a hook rewrote a file, and no
re-`add`. `work_cmd.run_commit:456-457` then prints `aw commit: error: git commit failed: ...` and exits
1. So a stripped trailing space forces the caller to notice, re-run, and (per contract) re-verify.

CAUSE 3: THE CONTRACT CHARGES THE RE-VERIFY UNCONDITIONALLY. `engine.py:1184-1189` (rendered into every
managed repo as `AGENTS.md:49`) says a hook failure INVALIDATES the pre-commit check and `git diff
--cached --name-only` must be re-run after EVERY failed attempt. `engine.py:1190-1194` (`AGENTS.md:51`)
then calls the tooled path "immune to this by construction", which is TRUE for index pollution and
FALSE for auto-fix rejection. An agent following the contract literally pays the full tax for a
whitespace fix.

FIX LAYER 1 (the actual defect): BOUNDED SINGLE RETRY ON A SELF-REWRITE. In `offer_commit`, before the
commit at `:245`, record a content hash per path in `our_staged`. On `rc != 0`, re-hash. If any of OUR
OWN paths changed on disk, the rejection was a REWRITE, so `git add -- <our_staged>` and retry the
commit EXACTLY ONCE, and report the rewritten paths (e.g. a `hook_fixed` tuple on `CommitOutcome`,
`:39-51`) so the fix is visible and not silent. If NOTHING of ours changed, the rejection was a genuine
refusal (gitleaks, local-leaks, the two IPD gates) and MUST fail exactly as it does today. A second
rejection after the retry also fails: one retry, never a loop.

WHY THIS IS SAFE IN A SHARED CHECKOUT. The retry re-stages ONLY `our_staged`, which is already the
intersection of the caller's explicit paths with what the helper itself staged (`:233-234`). A
co-worker's path restored into the index by pre-commit's stash/restore is therefore still
unreachable, so the property `AGENTS.md:51` actually guarantees is preserved, not weakened. Never add
`--no-verify` (the argv contract test `tests/test_git_commit_helper.py:66-70` forbids it, correctly).

TEST GAP THAT MUST BE CLOSED BY THIS LAYER. `tests/test_git_commit_helper.py` (328 lines, 16
`offer_commit` call sites) has NO test for a hook-rejected commit, because its fixture
`tests/support/__init__.py:92-100` does a bare `git init` and installs NO hook. Both fixtures are
needed: (a) a hook that REWRITES a staged file and exits nonzero -> assert one retry, commit succeeds,
`hook_fixed` names the path; (b) a hook that REFUSES without touching files -> assert NO retry, still
`STATUS_ERROR`, index left as found.

FIX LAYER 2 (removes most triggers at the source): NORMALIZE ON WRITE. `artifact_core.atomic_write`
(`:118-132`) is the single write path for tool-authored artifacts (used by `backlog.py:439/603`,
`specs.py`, `releases.py:847`, `prompts.py:264`, `research_cmd.py:130`, `artifact_refs.py:158`,
`artifact_rename.py:287/456`, `plans_refs.py:345`). Normalizing there (rstrip EACH line, exactly one
trailing newline) makes every artifact hook-clean at birth. Note the renderers already do a WHOLE-FILE
`.rstrip() + "\n"` (`backlog.py:337`, `plans.py:291`, `specs.py:844`, `set_records.py:83/113/134/197/397`,
`status_set.py:804`, `artifact_rename.py:457`) but NONE strips per-line, which is the case the hook
actually catches.

TRADEOFF, STATED HONESTLY: per-line rstrip destroys markdown's two-space hard line break. The
`trailing-whitespace` hook ALREADY destroys it on every non-excluded path, so this is making the writer
agree with the hook, not a new loss. Related asymmetry worth deciding at the same time: `.editorconfig`
sets `trim_trailing_whitespace = true` globally (`:8`) but EXEMPTS `*.md` (`:14-15`), while the hook does
NOT exempt markdown. Editor and hook currently disagree; pick one.

FIX LAYER 3 (contract wording): the re-verify tax should apply to raw `git commit`, not to the tooled
path once layer 1 exists. THIS ITEM DOES NOT DECIDE THAT WORDING. The maintainer ruled on 2026-09-01
that the contract should say MUST use the tooled path rather than PREFER, and that ruling is recorded on
backlog item `wjl471` (commitguard), whose open question 1 already asks whether the answer is to "make
the tooled path the path of least resistance" rather than intercepting the untooled one. See `wjl471`
for the exact replacement text.

HARD ORDERING CONSTRAINT: the reworded paragraph DESCRIBES the retry, so it MUST NOT ship before layer 1
lands, or the installed contract in every managed repo would document behavior the code does not have.
Layer 1 is therefore a prerequisite of `wjl471`'s answer, not a competitor to it.

EVIDENCE THIS CHURN IS NOT HYPOTHETICAL: `.aw/records/research/opencode/README.md:17-25` records
ruff-format silently reformatting delivered prototype files before the exclude regex existed ("The
pristine as-delivered copies were not retained"), which is WHY the regex exists;
`.aw/records/plans/executed/20260712-consolidate-reference-00-7waz4b-...:52` records end-of-file-fixer
normalizing a trailing newline; two superseded handoff prompts
(`.aw/records/prompts/superseded/20260717-1450-01-...:63`, `20260717-1950-01-...:49`) warned
"Pre-commit (ruff/ruff-format/whitespace/eof/gitleaks) may reformat and abort -> re-stage and
re-commit", i.e. the manual workaround was already being taught by hand;
`20260819-setupmarker-260819-01-i80vz1-...:94,185` added a "re-stage on hook-restore" caution after
observed stash/restore races.

RELATED: `gjadwm` (executed-transition gate false-positives on a legitimately finalized plan) is a
DIFFERENT hook problem, but its reasoning applies verbatim here: "a gate that false-positives on correct
behavior TRAINS agents to bypass it" (`:45-49`). Same for churn: a contract that taxes correct behavior
trains agents to ignore the contract. `wjl471` owns the MUST ruling and the guard design.
