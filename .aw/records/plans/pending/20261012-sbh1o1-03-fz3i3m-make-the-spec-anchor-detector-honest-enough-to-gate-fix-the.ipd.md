# IPD: Make the spec-anchor detector honest enough to gate: fix the agent crash, the table-row false positive and the unattributed misses

- Date: 2026-10-12
- Kind: child
- Concern: `check.spec-anchor-stale` (shipped `info` by `mt54wr`) cannot honestly be promoted to a gate today because its census is not zero for reasons that are the DETECTOR's fault, not the tree's: it misreads one valid citation, it is blind to anchors whose block never names the spec id6 (and those blind spots hide real stale anchors), and its `--agent` output crashes whenever it has any finding at all.
- Scope: FOUR things, all on the opt-in `--source-anchors` report, none changing its severity. (1) Fix the `--agent` crash (backlog `g3ropl`): derive the branch's exit code and outcome from the registered rule severities via `artifact_core.drift_exit_code` instead of hardcoding `exit_code = 0` beside `status = "findings"`. (2) Teach the detector to accept a TABLE-ROW anchor: an offset that lands on a markdown table row is valid when that row's first cell (for example `I-07`) appears in the citing comment or docstring BLOCK, which removes the `check_engine.py` `pqsx96` `:135` false positive. (3) Report an UNATTRIBUTED spec anchor (a `spec \`:NNN\``/`spec :NNN` spelling with no resolvable spec id6 anywhere in its comment or docstring block) as a finding with validity `unattributed`, because an offset no tool can attribute is unverifiable by construction and is exactly the class backlog `1vd74h` point (5) names. (4) Retarget the three live unattributed `25kzda` anchors this exposes (two in `oc_runipd.py`, one in `agy_runipd.py`, all citing the long-moved `:129`/`:131`) onto the stable `Section 2.1` token with the quoted sentence intact, and reword the one test docstring that spells the pattern literally. EXCLUDES promoting the severity and wiring CI (Order 04 `l85xvi`), EXCLUDES any speed optimisation (Order 04 runs the detector only in CI, so no user waits on it), EXCLUDES editing any spec, and EXCLUDES the SECTION-token validity question (`mt54wr` OQ-02).
- Scope-Paths: agent_workflows/spec_citations.py, agent_workflows/cli.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_spec_citation_anchors.py
- Item-Dependencies: executed:mt54wr, executed:atpvao
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 1vd74h
- From-Spec: none
- Set: sbh1o1
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: fz3i3m
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 03 of two plans graduating backlog 1vd74h; Order 04 (l85xvi) depends on it. Fixes bug g3ropl found during authoring.

## Goal

Bring the anchor detector's real-tree census to zero by fixing the detector's own errors (a false positive, a blind spot, a crash) and the three real stale anchors the blind spot was hiding, so that Order 04's promotion to a gate rests on a census that is zero because the tree is clean rather than because the detector cannot see.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [ ] E-01 RECORD THE BASELINE before any edit. Run, and paste: `aw check specs --source-anchors` (human mode; expect the single `check_engine.py` `pqsx96` `:135` finding measured at authoring, or whatever it reports now), `aw check --source-anchors --agent` (expect the `ValueError: Invalid aw.agent/v1 record: Exit code mismatch` traceback and a nonzero exit, measured at authoring at `92a6f240d`), and the bare suite `python3 -m pytest` summary line plus the SET of failing test ids for E-06 to compare against. Also run this supplementary scan and paste its hits, since it is how authoring found the blind spot: `grep -rnE "\bspec\b( +(Section +)?[0-9]+(\.[0-9]+)*[a-z]?)? +\`?:[0-9]+\b" --include=*.py agent_workflows tools tests` (authoring found `agy_runipd.py` "refuse the flag spec \`:131\`", `oc_runipd.py` "(spec \`:131\` freezes it)", `oc_runipd.py` "the one flag spec \`:131\` explicitly freezes" with "The blanket \`:129\` reading" on the next line, plus two literal spellings in `tests/test_spec_citation_anchors.py`).
  - Depends on: none
  - Expected outcome: pasted detector output, pasted crash, pasted suite baseline, pasted grep hits.
  - Execution state: pending

### Task group 2: Detector honesty

- [ ] E-02 FIX THE `--agent` CRASH (backlog `g3ropl`). In `cli._run_check`'s `if getattr(args, "source_anchors", False):` branch, replace the hardcoded `exit_code = 0` and `status = "clean" if len(findings) == 0 else "findings"` with: build the diagnostics first with `severity=check_engine.rule_spec("check.spec-anchor-stale").severity` (instead of the literal `"info"`), then `exit_code = artifact_core.drift_exit_code(...)` over those severities (or the equivalent `1 if any(sev != "info") else 0`), and `status = "conforms" if exit_code == 0 else "findings"`, matching how `aw check specs` reports `CONFORMS` while carrying an `info` finding. Make the `rules` evidence count by severity rather than hardcoding `info`, and set both `Evidence.status` values from the same `exit_code` (`"clean"` when zero findings, `"conforms"` when only `info` findings, `"findings"` otherwise) so no record in the stream carries a negative status beside `exit` 0. Keep the zero-finding case reporting `clean` exactly as today. While the rule is `info` the exit stays 0, so no current behavior other than the crash changes; Order 04's one-line severity change then flips the exit with no further CLI edit.
  - Depends on: E-01
  - Expected outcome: `aw check --source-anchors --agent` emits a valid `aw.agent/v1` record with `outcome` `conforms` and `exit` 0 when the only findings are `info`, and no traceback; with zero findings it still reports `clean`/0.
  - Execution state: pending
- [ ] E-03 ACCEPT A TABLE-ROW ANCHOR. In `spec_citations`, when an offset resolves `valid` to a line whose stripped text starts with `|`, extract that row's first cell (strip pipes, backticks and whitespace, for example `I-07`) and treat the citation as valid when that token appears in the citing BLOCK: the contiguous run of `#` comment lines, or the docstring, containing the citing line (not only the citing line itself, because `check_engine.py`'s citation puts the path on one line and "I-07" on the lines either side). Track the block text in `stale_spec_anchors` alongside the existing `comment_id6`/`docstring_id6` state and pass it to `_evaluate_citation`. Do not change the heading-match rules for non-table lines.
  - Depends on: E-01
  - Expected outcome: the `check_engine.py` `pqsx96` `:135` citation produces no finding; a fixture citing a table row whose key is ABSENT from the block still produces one.
  - Execution state: pending
- [ ] E-04 REPORT AN UNATTRIBUTED SPEC ANCHOR. In `spec_citations`, when a line inside a comment or docstring block matches the bare spellings `_find_anchors_on_line` already recognises in its step 2 (backtick `:\d+` or `spec [N.N] :\d+`) but the block names NO known spec id6 (so `active_id6` is None), emit a `StaleSpecAnchor` with `id6=""`, the cited offset, empty `enclosing_heading`, and `validity="unattributed"`. Limit the backtick spelling to lines that also contain the word `spec` (case-insensitive) so a self-file citation such as `runner_shared.py`'s "the suite-baseline comment at \`:16624\`" is NOT reported. Update the human rendering and the diagnostic detail so an unattributed finding reads as such (for example `spec ? :131 -> unattributed`) instead of printing an empty id6.
  - Depends on: E-01
  - Expected outcome: the three runner-file anchors E-01 found are reported as `unattributed`; the `runner_shared.py` `:16624` self-citation is not. At review a scratch prototype of this rule over `agent_workflows`, `tools` and `tests` reported exactly `agy_runipd.py 4189 ? 131 unattributed`, `oc_runipd.py 4779 ? 131 unattributed`, `oc_runipd.py 5398 ? 131 unattributed`, plus the pre-existing `check_engine.py` `pqsx96` `:135` finding that E-03 removes. With the rule also applied to the one-line docstring branch (re-run at review), it additionally reported `tests/test_spec_citation_anchors.py 124 ? 131 unattributed`. It did not report the `tests/test_spec_citation_anchors.py` docstring only because the prototype skipped the detector's ONE-LINE docstring branch in `stale_spec_anchors` (the branch that evaluates a line opening and closing a triple quote, then `continue`s). E-04 must apply the rule on that branch too, since a one-line docstring is a docstring; it will then report that test docstring, which is why E-05 rewords it. Re-derive this set at execution; it is context, not the bar.
  - Execution state: pending

### Task group 3: Tree sweep and tests

- [ ] E-05 RETARGET THE EXPOSED ANCHORS. Rewrite the three runner-file comments onto the stable section token, keeping each quoted claim: `agy_runipd.py` "refuse the flag spec \`:131\` freezes" becomes "refuse the flag spec `25kzda` Section 2.1 freezes"; `oc_runipd.py` "(spec \`:131\` freezes it)" becomes "(spec `25kzda` Section 2.1 freezes it)"; `oc_runipd.py` "the one flag spec \`:131\` explicitly freezes" becomes "the one flag spec `25kzda` Section 2.1 explicitly freezes" and "The blanket \`:129\` reading" becomes "The blanket Section 2.1 `--resume` reading" (the cited sentences live in Section 2.1 Command grammar: "The frozen value cannot change on resume." and "`--resume` is mutually exclusive with a new selector and with flags that would change the frozen queue or policy."). Reword the docstring in `tests/test_spec_citation_anchors.py` `test_bare_backtick_spelling_detected_in_same_comment_block` so it no longer spells a literal bare anchor (the fixture STRING it writes is data and stays). Once E-04 covers one-line docstrings it reports that docstring as `unattributed`, so the reword is required for a zero census. Comment-only edits in the runner files: no code changes.
  - Depends on: E-04
  - Expected outcome: `aw check specs --source-anchors` reports zero findings on the real tree.
  - Execution state: pending
- [ ] E-06 ADD BEHAVIORAL TESTS to `tests/test_spec_citation_anchors.py`, over self-written fixtures only (never the live tree census): (a) a table-row anchor whose key cell appears on a neighbouring comment line produces no finding; (b) the same anchor with the key absent from the block produces one finding; (c) an unattributed `# ... spec \`:11\`` in a block naming no id6 produces one finding with validity `unattributed`; (d) a `# see the comment at \`:11\`` line with no `spec` word produces none; (e) `aw check specs --source-anchors --agent --dir <fixture>` with a stale anchor exits 0, prints no traceback, every emitted line parses as JSON, and its result record has `outcome` `conforms`, `exit` 0, and a `check.spec-anchor-stale` diagnostic (the `g3ropl` regression; on the current code this exact command exits 1 with `ValueError: Invalid aw.agent/v1 record: Exit code mismatch`, so the test is red before E-02); (f) the same command with no stale anchor reports `outcome` `clean`, `exit` 0. Drive the CLI with `subprocess` as the existing `test_cli_check_specs_source_anchors_exits_zero_with_finding` does. Then run the bare suite and compare to the E-01 baseline.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: the new tests pass; the bare suite shows no new failures relative to the E-01 baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.drift_exit_code` exempts only `info` from the nonzero exit, and the `aw.agent/v1` validator (`agent_schema.assert_valid_agent_record`) refuses `exit 0` with outcome `findings`; the other `aw check` surfaces report `conforms` with `info` findings present (measured: bare `aw check specs` prints "CONFORMS" with "info 1", exit 0).
- `check_engine.rule_spec` is the single lookup for a rule's registered severity; reading severity from it rather than a literal is what lets Order 04 promote with one registry edit.
- `mt54wr`'s `tests/test_spec_citation_anchors.py` header states the P16 posture this plan keeps: "behavioral assertions only, no code-structure pinning, no live-tree census counts".
- `atpvao` set the retargeting idiom: "spec `25kzda` Section <N.N>" with no offset and the quoted claim intact.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `aw check --source-anchors --agent` CRASHES whenever there is a finding. The branch hardcodes `exit_code = 0` and `status = "findings"`, a pair the schema validator refuses. Filed as bug `g3ropl` (`Blocks-Release: next`). | Run at `92a6f240d` on the real tree: traceback ending `ValueError: Invalid aw.agent/v1 record: Exit code mismatch: exit=0 incompatible with negative outcome 'findings'`. Reproduced on a one-spec fixture with one stale anchor: exit 1, same error; zero findings: exit 0, outcome `clean`. |
| F-02 | The census after `atpvao` is ONE finding and it is a false positive: `check_engine.py`'s comment cites the pqsx96 spec path at `:135`, which is the `| I-07 |` table row under "## 3. Invariant catalog"; the citing block says "I-07" but the heading title does not appear, so the detector reports it. | `aw check specs --source-anchors` output: "agent_workflows/check_engine.py:391: spec pqsx96 :135 -> ## 3. Invariant catalog"; line 135 of the pqsx96 spec begins "| I-07 | Release-gate preservation". |
| F-03 | The detector's blind spot hides REAL stale anchors that `atpvao` excluded as "not spec anchors". Three comments in the runner drivers cite spec `25kzda` by bare offset (`:131`, `:129`) with no id6 in their block, so the detector never attributes them. Both offsets now land in "### 1.1 Normative roles"; the cited sentence "The frozen value cannot change on resume." is in "### 2.1 Command grammar". | Supplementary grep in E-01; `atpvao` Scope EXCLUDES "the `oc_runipd.py`/`agy_runipd.py` cross-file `oc_runipd.py:NNNN` citations, which are not spec anchors" (these three are not of that form). The 25kzda spec headings read at authoring: "### 1.1 Normative roles" encloses the old offsets; "### 2.1 Command grammar" carries the sentence. |
| F-04 | The other blind spots backlog `1vd74h` lists are ALREADY GONE: `atpvao` retargeted the `RUN_POLICY_FLAGS` comment, `evaluate_unverifiable_admission` and `AggregatedItem` anchors to section tokens. | `atpvao`'s own supplementary grep re-run at authoring over `runner_shared.py`, `run_evidence.py`, `host_sandbox_profile.py` and `tests/test_host_capability_extension.py` returns no hits; `evaluate_unverifiable_admission`'s docstring now reads "(spec Section 2.1)". |
| F-05 | A bare backtick offset is not always a spec citation: `runner_shared.py` cites its OWN line ("the suite-baseline comment at \`:16624\`"). Requiring the word `spec` on the line keeps the unattributed rule from reporting it. | Supplementary grep in E-01; the line reads "see the suite-baseline comment at `:16624`". |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Crash fix with severity-derived exit (E-02).
3. Table-row acceptance (E-03) and unattributed reporting (E-04).
4. Sweep the exposed anchors (E-05), then tests and suite comparison (E-06).

## Deferred / out of scope (with reason)

- PROMOTING THE SEVERITY AND WIRING CI. That is the decision Order 04 (`l85xvi`) carries and asks the maintainer to approve; this plan is worth executing either way, because it fixes a crash and makes the report true.
  - Carrier: l85xvi
- DETECTOR SPEED (about 4.2s user CPU on the real tree, against about 1.1s for bare `aw check specs`, measured three times at authoring). Not fixed here because Order 04 keeps the detector out of every default command and runs it only as a CI step, where nobody waits on it interactively.
  - Carrier-Declined: no user-perceptible cost while the detector runs only behind an opt-in flag and in CI (AGENTS.md: inefficiency users cannot notice is not a defect); a plan that proposes making it default must measure and fix speed itself.
- SECTION-TOKEN VALIDITY (whether a cited `Section N.N` still exists). Recorded as `mt54wr` OQ-02; not needed for the offset gate.
  - Carrier-Declined: owned by `mt54wr` OQ-02, which explicitly declines a carrier until the maintainer rules that a non-resolving section token is a defect; filing one here would presuppose that ruling.

## Scope check

- Over-scope: none. Each declared path is modified: `spec_citations.py` (E-03, E-04), `cli.py` (E-02, E-04 rendering), `oc_runipd.py` and `agy_runipd.py` (E-05, comments only), `tests/test_spec_citation_anchors.py` (E-05 docstring, E-06 tests).
- Under-scope: none known. If E-01's supplementary grep finds a site authoring did not, retarget it in E-05 if it is a spec anchor in a declared path, otherwise record it and justify the extra path to finalize with `--scope-reason`.

## Required tests / validation

- New fixture tests (E-06) run bare and asserting only on returned findings, printed output, JSON records and exit codes.
- Executed CLI probes on the real tree: `aw check specs --source-anchors` (expect zero findings, exit 0) and `aw check --source-anchors --agent` (expect a valid record, no traceback, exit 0).
- The bare suite `python3 -m pytest`, compared with the E-01 baseline.

## Spec / documentation sync

N/A for specs: no spec text changes; the detector is a check, and spec `25kzda` is only cited, never edited. No user-facing documentation names `--source-anchors` beyond its `--help` string, which stays accurate (still opt-in and advisory after this plan). `CHANGELOG.md` is updated by Order 04, which makes the user-visible change.

## Open questions

### OQ-01: Should an unattributed anchor be a finding at all, rather than silently ignored?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: yes. F-03 shows the blind spot hid three genuinely stale anchors that a prior sweep (`atpvao`) explicitly reasoned past, so ignoring unattributed anchors would let a gate pass a tree carrying stale citations, which is the exact false assurance backlog `1vd74h` point (5) warns about. Reporting them is honest because the fix is always available and cheap: name the spec id6 or cite a section token. The `spec`-word restriction (F-05) keeps the rule off self-file citations.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the two detector commands (including the crash traceback), the pasted bare-suite summary line and failing-id set, and the pasted supplementary grep hits.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted result JSON record of `aw check --source-anchors --agent` on a fixture with a stale anchor, showing `"outcome":"conforms"`, `"exit":0`, a `check.spec-anchor-stale` diagnostic, and a pasted `echo $?` of 0 with no traceback on stderr (produced by `cli._run_check`'s `--source-anchors` branch); the same on a zero-finding fixture showing `"outcome":"clean"`; and the pasted passing output of E-06 tests (e) and (f).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted real-tree `aw check specs --source-anchors` output showing no `check_engine.py` `pqsx96` finding, plus the passing output of E-06 tests (a) and (b).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted detector output taken BEFORE E-05 showing the three runner-file anchors reported as unattributed and the `runner_shared.py` `:16624` line absent, plus the passing output of E-06 tests (c) and (d).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the pasted `git diff` of `oc_runipd.py` and `agy_runipd.py` showing comment-only changes, and pasted real-tree `aw check specs --source-anchors` output reporting zero findings with exit 0.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` with every test passing and tests (a) through (f) visible by name, and the pasted bare-suite summary line with its failing-id set compared against E-01 (no new failures).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Explicit human approval is required before execution. OQ-01 is resolved; none remain.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push. Paste ACTUAL runner output for every test claim and never claim a result you did not run; run the suite bare (`python3 -m pytest`).

SCOPE FENCE. Do NOT change the registered severity of `check.spec-anchor-stale`, do NOT edit `.github/workflows/tests.yml`, and do NOT edit any spec or any record under `plans/executed/`; those belong to Order 04 or to no plan. An out-of-scope edit that proves necessary is MADE and then JUSTIFIED to `aw ipd finalize` with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.

POST-GATE LIFECYCLE. Do not move this plan to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item reads `pass` with observed evidence. Under `aw oc run` / `aw agy run` the runner performs finalize; executed by hand, run `aw ipd finalize fz3i3m --actor <agent/model> --message <summary> --apply`. The runner's backlog-close step acts only on this plan's `- From-Backlog:` item (`1vd74h`), which must stay `graduated` because Order 04 `l85xvi` is a second carrier that has not executed; do not set it `done` by hand. Bug `g3ropl` is NOT this plan's `From-Backlog`, so no runner closes it: once this plan is in `executed/`, close it with `aw backlog set done g3ropl --evidence <this executed plan path>`, which is the SATISFIED path for its `Blocks-Release: next` gate. That is a separate commit on `.aw/records/backlog/`, outside this plan's Scope-Paths.
