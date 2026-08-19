# IPD: json output and documented exit codes on read verbs

- Date: 2026-08-18
- Kind: child
- Concern: awhelp Order 03 (spec 20260818-1525-01 goal G6; TODO items 4, 10, 13, 14, 29, 31). Goal G6 requires every verb a machine consumer touches to have a machine-readable mode (`--json`/`--agent`) and DOCUMENTED exit codes (0 ok / 1 findings / 2 cannot-run), reusing the existing `drift_exit_code` convention (artifact_core.py:262-266). Today this is uneven on the EXISTING read verbs: `context` has `--agent`, `attention` has `--format json` (attention.py:362), `project status` and `storage status` have `--json`, but the plain read verbs `list` (the repo listing) and `status` (the environment summary) have neither `--json` nor a documented exit-code contract, and the check/index-style verbs do not state their 0/1/2 meaning in help. This Order adds `--json` to the read verbs that lack it (where a machine consumer benefits), makes the check/index-style verbs return 0/1/2 uniformly via `drift_exit_code`, and DOCUMENTS the exit codes in each verb's help/description. It coordinates with Set awcmdsurf, which adds `--json` to the NEW cross-cutting verbs; this Order covers only the EXISTING read verbs.
- Scope: `agent_workflows/cli.py` (add a `--json` flag to `list` cli.py:532-539 and `status` cli.py:541-543 where sensible; add an exit-code line to the relevant read/check verbs' `_DESCRIPTIONS` / `help=`; emit JSON via `json.dumps` in the dispatch handlers for `list` cli.py:4106 and `status` cli.py:4108), reusing `agent_workflows.artifact_core.drift_exit_code` (artifact_core.py:262) for the check/index verbs, plus a new test `tests/test_json_and_exitcodes.py`. IN: `--json` on the read verbs missing it (`list`/`list-repos`, `status`) reusing `json.dumps`; a uniform 0/1/2 return for the check/index-style read verbs via `drift_exit_code`; the 0/1/2 meaning documented in each such verb's help; a test that a read verb emits valid JSON and returns the documented codes. OUT: the top-level epilog and arg-hungry examples (awhelp Order 02); the jargon rewrite (awhelp Order 01); `--json` on the NEW verbs (`check`/`find`/`index`/...), which Set awcmdsurf owns; any change to what a verb computes (only the OUTPUT FORMAT and documented EXIT contract are added).
- Status: to-review
- Set: awhelp
- Order: 3
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: oc4cph

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 4,10,13,14,29,31 (Set awhelp).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. --json + documented exit codes on read verbs, reusing artifact_core.drift_exit_code (:262); additive; no findings.

## Goal

Give the EXISTING read verbs a consistent machine-readable contract per spec goal G6: add `--json` to the
read verbs that lack it (where a machine consumer benefits), make the check/index-style read verbs return
0 (clean) / 1 (findings) / 2 (cannot-run) uniformly by reusing `drift_exit_code`, and document those exit
codes in each such verb's help. No verb changes WHAT it computes; only its output format and its
documented exit contract are added or clarified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Edit ONLY `agent_workflows/cli.py` and add ONLY `tests/test_json_and_exitcodes.py`.
Reuse `agent_workflows.artifact_core.drift_exit_code` (artifact_core.py:262) for the check/index verbs -
do NOT invent a new exit-code helper. When adding `--json`, reuse `json.dumps(...)` for the payload and
gate it behind the new `--json` flag so the human text output is unchanged when the flag is absent. Do
NOT change what any verb COMPUTES; only add an alternative output format and a documented exit contract.
Follow the survey in E-01 before adding a flag so you only add `--json` where a machine consumer actually
benefits (a bare informational verb with nothing structured to emit does not need it - record that in the
Findings if you skip one).

### Task group 1: survey and add `--json` to read verbs missing it

- [ ] E-01 In `agent_workflows/cli.py`, first SURVEY which read verbs already expose a machine-readable mode and record it in the Findings table: `context` has `--agent` (cli.py:152-156), `attention` has `--format json` (attention.py:362), `project status` and `storage status` have `--json` (cli.py:167-170, cli.py:184-187). Then ADD `--json` to the read verbs that lack it and would benefit - the repo-listing `list` verb (cli.py:532-539; note Set awcmdsurf renames it to `list-repos`, so add the flag to the existing `list` parser here) and the environment `status` summary (cli.py:541-543). Emit the structured payload with `json.dumps` in each verb's dispatch handler (`list` at cli.py:4106, `status` at cli.py:4108), gated behind the new `--json` flag so the default human output is byte-for-byte unchanged. If you determine a surveyed read verb has nothing structured worth emitting, SKIP it and note the reason in Findings rather than adding a no-op flag.
  - Depends on: none
  - Expected outcome: `aw list --json` and `aw status --json` each print valid JSON (parseable by `json.loads`) carrying the same facts as the human output; without `--json` the human output is unchanged; the Findings table records which verbs already had a machine mode and which (if any) were deliberately skipped.
  - Execution state: pending

### Task group 2: uniform 0/1/2 exit codes, documented

- [ ] E-02 In `agent_workflows/cli.py`, make the check/index-style read verbs return exit 0 (clean) / 1 (findings) / 2 (cannot-run) UNIFORMLY by reusing `drift_exit_code` (artifact_core.py:262: returns 1 if drift else 0; the caller returns 2 on a could-not-run / invocation failure), and DOCUMENT that 0/1/2 meaning in each such verb's help or `_DESCRIPTIONS` description. Cover the existing check/index read verbs (e.g. `backlog check`, `specs check`, `plans-index --check`, `research index --check`, `plan-names --check`, `attention --check`) - for each, confirm it already funnels through `drift_exit_code` (or an equivalent 0/1 return) and, where it does not, route its clean/findings return through `drift_exit_code`; and reserve exit 2 for the cannot-run/invocation-failure path. Add a single documented sentence to each verb's help text, e.g. "Exit codes: 0 = clean, 1 = findings, 2 = could-not-run." Do NOT change what the verb validates or computes; only normalize the RETURN and document it.
  - Depends on: none
  - Expected outcome: each surveyed check/index read verb returns 0 when clean, 1 when it reports findings, and 2 when it cannot run (bad invocation), all via `drift_exit_code` (or the caller's 2 path); each such verb's `--help` states the 0/1/2 meaning.
  - Execution state: pending

### Task group 3: test JSON output and exit codes

- [ ] E-03 Add `tests/test_json_and_exitcodes.py` that: (a) invokes a read verb with `--json` (e.g. `aw status --json` or `aw list --json`, or `aw storage status --json` for a verb that already had it) via the CLI entry, captures stdout, and asserts `json.loads(stdout)` succeeds and the object carries an expected key; (b) drives a check verb through its clean and findings paths and asserts the exit code is 0 on clean and 1 on findings, and asserts a deliberately bad invocation returns 2; (c) asserts the documented "Exit codes: 0 ... 1 ... 2 ..." sentence appears in that verb's `--help`. Reuse existing test fixtures/helpers for building a repo root where a check verb runs. Run the full serial suite and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: `tests/test_json_and_exitcodes.py` passes; a `--json` read verb emits valid JSON; a check verb returns the documented 0/1/2 codes and states them in `--help`; the full serial suite is green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Machine-readable modes are uneven today: `context` uses `--agent` (cli.py:152-156), `attention` uses `--format json` (attention.py:362) plus `--agent`, `project status`/`storage status` use `--json`; the plain `list` (cli.py:532-539) and `status` (cli.py:541-543) verbs have neither.
- `drift_exit_code(drift)` (artifact_core.py:262-266) is the canonical `--check` exit convention: returns 1 if any drift else 0; the docstring explicitly notes that exit 2 (could-not-run) is the CALLER's responsibility on an invocation/parse failure. This is the reuse target for the check/index verbs' uniform contract.
- `render_agent_drift` (artifact_core.py:255) is the tab-separated `--agent` drift renderer; `--agent` and `--json` are distinct output modes and both may coexist on a verb (e.g. `storage status` has both).
- The `_DESCRIPTIONS` dict (cli.py:36-323, applied by `_apply_descriptions` cli.py:326-344) is where a verb's full `--help` description lives; the exit-code documentation sentence belongs there (or in the short `help=`) for each check/index verb.
- Set awcmdsurf RENAMES `list` -> `list-repos` and adds `--json` to the NEW cross-cutting verbs; this Order intentionally touches only the EXISTING `list`/`status` parsers and the existing check/index verbs to avoid colliding with that Set's parser surgery.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | `context`/`attention`/`project status`/`storage status` already have a machine mode; `list`/`status` do not. | E-01 adds `--json` to `list` and `status`; the survey result is recorded here at execution time. |
| F2 | `drift_exit_code` is the canonical 0/1 helper; 2 is the caller's cannot-run path. | E-02 reuses it uniformly rather than inventing per-verb exit logic. |
| F3 | Set awcmdsurf renames `list`->`list-repos` and owns `--json` on the new verbs. | This Order scopes to the EXISTING verbs only; the flag added to `list` carries forward under the rename. |

## Proposed changes (ordered, validatable)

1. Survey machine modes; add `--json` (via `json.dumps`) to `list` and `status` where beneficial (E-01).
2. Normalize check/index read verbs to 0/1/2 via `drift_exit_code` and document the codes in help (E-02).
3. Add `tests/test_json_and_exitcodes.py` for valid JSON + documented exit codes; run the suite (E-03).

## Deferred / out of scope (with reason)

- `--json` on the NEW cross-cutting verbs (`check`/`find`/`index`/`search`/`rename`/`group`/`archive`): Set awcmdsurf owns those verbs and their machine modes; adding it here would collide with that Set's parser work.
- The top-level epilog / arg-hungry examples: awhelp Order 02. The jargon rewrite: awhelp Order 01.
- Any change to WHAT a verb computes or validates: out of scope; only output format and exit contract are added.

## Scope check

- Over-scope: none - only `--json` on existing read verbs, a `drift_exit_code`-based 0/1/2 normalization + documentation for existing check/index verbs, and one new test file.
- Under-scope: none - spec goal G6's machine-mode + documented-exit-code requirement is met for the EXISTING read verbs (items 4, 10, 13, 14, 29, 31), with the new-verb coverage explicitly delegated to awcmdsurf.

## Required tests / validation

`tests/test_json_and_exitcodes.py` (E-03): a `--json` read verb emits valid JSON; a check verb returns 0/1/2 per the documented contract and states it in `--help`; plus the full serial suite. Each V pins one E.

## Spec / documentation sync

Implements spec 20260818-1525-01 goal G6 (machine-readable mode + documented 0/1/2 exit codes) for the existing read verbs; the new verbs are covered by Set awcmdsurf. No AGENTS.md change. No spec status transition (the Set orchestrator advances the spec).

## Open questions

### OQ-01: name the machine flag `--json` or `--agent` on `list`/`status`?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: use `--json` on `list`/`status`, matching the existing `project status`/`storage status` verbs (which already use `--json` for structured output). `--agent` is used elsewhere for the tab-separated drift stream; `list`/`status` emit a structured object, so `--json` is the consistent choice. A verb that already has `--agent` keeps it. Resolved per E-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw status --json` (and/or `aw list --json`) output and confirm it parses with `json.loads`; paste the same verb WITHOUT `--json` to show the human output is unchanged; confirm the Findings table records the survey result.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a check verb returning 0 on a clean tree, 1 on a tree with findings, and 2 on a deliberately bad invocation (show the shell `$?` for each), plus that verb's `--help` showing the "Exit codes: 0 = clean, 1 = findings, 2 = could-not-run." sentence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `tests/test_json_and_exitcodes.py` passing and the full serial suite tail (no regressions).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` plus an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification and path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two touched
paths (`agent_workflows/cli.py` and `tests/test_json_and_exitcodes.py`) path-scoped (never `git add -A`),
and never pushes. Transition to executed only after `aw ipd lint --phase pre-transition` conforms and
every V is `pass`. Third Order of Set awhelp; coordinates with Set awcmdsurf (which adds `--json` to the
NEW verbs) but is independent of awhelp Orders 01/02. On Set completion the orchestrator advances spec
20260818-1525-01 accordingly.
