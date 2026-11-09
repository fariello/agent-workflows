# IPD: Write the finalize scope fields in the executed append

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.2c and 4.4 require finalize to write `scope_result`, `out_of_scope_paths` and `widened_paths` in the executed append. Finalize writes `- Scope-Exceeded:` today through `ipd_lifecycle._insert_scope_exceeded_metadata` (41 tracked plans carry it, `xexn45` F-05). This is part of `8q27jt` (itself part of `xexn45`), split 2026-11-09.
- Scope: In `ipd_lifecycle._finalize_transaction`, write the three scope fields in the SAME `artifact_meta.append` call as the transition to `executed`, render them in phase B as today's bullet, and delete `_insert_scope_exceeded_metadata` (`8q27jt` E-03, finalize subset). Depends on `9qhtrc` for the repository-root path rule. EXCLUDES: retirement (`8q27jt`), the `finalize` event payload (`nq1src`).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/artifact_meta.py, tests/test_writers_scope_fields.py, .aw/records/plans/pending/20261109-metastore-132-1dvb08-write-the-finalize-scope-fields-in-the-executed-append.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:9qhtrc
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 132
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1dvb08

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 8q27jt (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The finalize scope result is a logged field written with the executed transition, while the phase-B file still shows exactly today's `- Scope-Exceeded:` bullet.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/1dvb08/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/1dvb08/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: finalize scope fields

- [ ] E-01 In `ipd_lifecycle._finalize_transaction`, add to the transition to `executed` from `status_set.apply_status_change` (Order 06), in the SAME `artifact_meta.append` call, a `set` of `scope_result` (`within` when no path was out of scope or widened, `widened` when only widened paths exist, `exceeded` when any out-of-scope path was accepted), `out_of_scope_paths` and `widened_paths` (each a list of `{path, reason}` from `evidence["scope_reconciliation"]`), pinned first. Paths stay REPOSITORY-relative (OQ-03, enforced by `9qhtrc`). Rollup retirement (`retire_orchestrator`) writes none of the three fields. Add to `tests/test_writers_scope_fields.py`: through `artifact_meta.read`, `scope_result`, both lists and their reasons are present after a fixture finalize (`exceeded`, `widened`, `within` cases); a rollup retirement leaves all three absent; a separate later `set scope_result` is refused.
  - Depends on: none
  - Expected outcome: the three new finalize cases report `exceeded`, `widened` and `within` with the expected path lists; rollup leaves them absent; the out-of-append `set` is refused.
  - Execution state: pending

- [ ] E-02 Render the scope fields in phase B as today's file shows them (D-3) and delete `ipd_lifecycle._insert_scope_exceeded_metadata`: the legacy writer renders ONLY the existing `- Scope-Exceeded: <path> (<reason>); ...` bullet with today's sanitizing from `ipd_lifecycle._format_scope_exceeded_value` (sorted, `;()` removed, newlines folded, 200-character cap), and nothing for `within`/`widened`. Behaviors kept: `tests/test_scope_exceeded.py` (cases a to e, unchanged), `tests/test_finalize_refusal_findings.py`, `tests/test_finalize_sendback.py`, `tests/test_ipd_lifecycle_cli.py::test_widening_finalizes_when_each_added_path_carries_a_reason`.
  - Depends on: E-01
  - Expected outcome: the four pinned modules pass before and after with equal outcome lists; `rg -n "_insert_scope_exceeded_metadata" agent_workflows` prints nothing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -c "_insert_scope_exceeded_metadata\(" agent_workflows` = 2 (the def and one call site) | One deletion. |
| F-02 | Pinned-module test counts: `test_scope_exceeded` 7, `test_finalize_refusal_findings` 4, `test_finalize_sendback` 62, `test_ipd_lifecycle_cli` 73 | E-01 names 5 units, E-02 7. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-3 (scope fields in phase B). The logged values `within` and `widened` have no legacy bullet; the legacy file shows only `- Scope-Exceeded:` for `exceeded`, exactly as today. So in phase B the cache returns `scope_result` only from a just-written append (fixture tests) and the legacy loader reads it back from `- Scope-Exceeded:` as `exceeded`; `within` and `widened` become durable only at the cutover. This is the honest phase-B form of AC-39 (4); Order 13 re-demonstrates it on logs.

## Proposed changes (ordered, validatable)

1. Write the scope fields in the executed append (E-01).
2. Render them as today's bullet and delete the old inserter (E-02).

## Deferred / out of scope (with reason)

- The `finalize` event payload that later replaces the interim scope fields.
  - Carrier: nq1src
- The final merge-independence test, the AC-21 obligations test (which extends `tests/test_writers_obligations.py`), the raw-write audit (F-09), the documentation lines, and the full gates of the writer move.
  - Carrier: xexn45

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Adds the finalize cases to `tests/test_writers_scope_fields.py` (created by `9qhtrc`). Contributes to `4sd62s` AC-39 (4).

## Spec / documentation sync

None here; the path-root amendment is in `9qhtrc`.

## Open questions

### OQ-03: Are finalize's `out_of_scope_paths` and `widened_paths` records-root-relative?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1, decision D-2)
- Resolution or deferral rationale: No; they are repository-relative, exactly as `Scope-Paths` and `runner_shared.compute_scope_reconciliation` produce them. `xexn45` F-05 measures 35 of 64 entries as code paths (`agent_workflows/...`, `tests/...`) that have no records-root form. The 4.2 PATH HISTORY rule ("relative to the resolved records root") governs the artifact's own `path` field. `tve77h` E-03 (c) as written requires every `path`, `out_of_scope_paths` and `widened_paths` value to resolve inside the records root, and spec 4.2 says these two keys "are checked by the path rules (PATH HISTORY below)", so the approved texts and this decision disagree and 35 of 64 measured finalize paths would be refused. Resolution: `validate_new_events` applies the records-root containment rule to `path` only, and applies "relative, no `..`, not absolute, sanitizer-scanned, inside the REPOSITORY root" to `out_of_scope_paths` and `widened_paths`; the spec 4.2 sentence is amended in the same change. Recommendation strength: strong.
- Note: carried unchanged from `8q27jt` (originally `xexn45`) with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_scope_fields.py -k finalize` with these cases PASSED by name, quoting each assertion: `scope_result == "exceeded"` with its `out_of_scope_paths`, `"widened"` with its `widened_paths`, `"within"` with both lists empty, the rollup case with all three absent, and the refused out-of-append `set scope_result`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/1dvb08/E-02-before.txt` and `.aw/state/1dvb08/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: each of the five `tests/test_scope_exceeded.py` cases a to e; `tests/test_ipd_lifecycle_cli.py::test_widening_finalizes_when_each_added_path_carries_a_reason`; the per-module PASSED counts (equal before and after) of `tests/test_finalize_refusal_findings.py` and `tests/test_finalize_sendback.py`. Plus `git diff --stat tests/test_scope_exceeded.py` empty and `rg -n "_insert_scope_exceeded_metadata" agent_workflows` printing nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 1dvb08 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 1dvb08` itself.
