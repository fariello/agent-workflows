# IPD: Resolve Python-source file:line offsets in comments and docstrings as an advisory opt-in report

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in the tree resolves a `<file>.py:<line>` offset cited in Python source. `spec_citations.stale_spec_anchors` (behind `aw check --source-anchors`) resolves offsets only into `.spec.md` files, and `artifact_refs.check_source_citations` (behind `--source-citations`) checks that a cited FILE exists but never resolves the OFFSET. Measured at authoring (F-02), 8 of the 37 resolvable comment/docstring offsets in `agent_workflows/`, `tools/` and `tests/` land past end of file, on a blank line, or on a punctuation-only line, so the defect class backlog `7jl2bf` describes recurs with no tool able to see it.
- Scope: Answer the four decisions backlog `7jl2bf` owes (OQ-01..OQ-04, each resolved from repository evidence below) and build the report they describe. (1) A new pure detector module `agent_workflows/source_offsets.py` that extracts `<file>.py:<line>[-<line>]` citations from COMMENT tokens and DOCSTRING tokens only (via `tokenize`, never from ordinary string literals, which are fixture data), resolves each named file inside the repository, and returns findings with validity `past_eof`, `blank_line` or `punct_only`, REUSING `spec_citations._resolve_offset` for the first two verdicts. (2) A new opt-in flag `aw check --source-offsets` and its `_run_check` branch, reporting a new rule `check.source-offset-stale` registered `info` in `check_engine.RULE_REGISTRY`, with the exit code and outcome derived from registered severity (so an advisory finding exits 0 with outcome `conforms`). (3) Exempt a citation whose citing line names a commit hash (a HISTORICAL citation). (4) Fixture-only behavioral tests and one `CHANGELOG.md` line. EXCLUDES fixing the live sites the report finds (Order 03 `jem77o`), EXCLUDES any change to `spec_citations.py` or to the `--source-anchors` branch (owned by pending `sbh1o1` plans `fz3i3m`/`l85xvi`), EXCLUDES citation-FORM checking (that is `IPD-C801`'s job for plans), EXCLUDES any CI step, default-path wiring or severity above `info`.
- Scope-Paths: agent_workflows/source_offsets.py, agent_workflows/cli.py, agent_workflows/check_engine.py, tests/test_source_offsets.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 7jl2bf
- Set: hostcite
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: pyuw4v
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Record: .aw/records/reviews/20261012-hostcite-02-pyuw4v-resolve-python-source-file-line-offsets-in-comments-and-docs.review.md Round 1

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 02 of two plans graduating backlog 7jl2bf; resolves the item's four owed decisions from repository evidence; Order 03 (jem77o) depends on it.

## Goal

Give the repository a mechanical, advisory, opt-in report of `<file>.py:<line>` citations in Python comments and docstrings that point past end of file or at a meaningless line, so the stale-offset class that plans `fnbtta`, `3tov52` and `rdl9lh` each fixed by hand can be found by running one command instead of by a manual sweep.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [ ] E-01 RECORD THE BASELINE before any edit. Run and paste the bare suite `python3 -m pytest` summary line plus the SET of failing test ids (E-06 compares against it). Confirm `agent_workflows/source_offsets.py` and `tests/test_source_offsets.py` do not exist and that `aw check --help` lists no `--source-offsets` flag (paste the `ls` error and a `aw check --help | grep -c source-offsets` of 0). Confirm `spec_citations._resolve_offset` still takes `(lines, headings, in_fence, offset)` and returns `(enclosing_heading, validity)` with verdicts `past_eof`/`in_fence`/`blank_line`/`valid` (paste its signature line); if pending plan `fz3i3m` has changed that contract, adapt E-02 to the new one and record the adaptation.
  - Depends on: none
  - Expected outcome: pasted suite baseline, pasted absence proofs, pasted `_resolve_offset` signature.
  - Execution state: pending

### Task group 2: Detector and rule

- [ ] E-02 WRITE THE PURE DETECTOR `agent_workflows/source_offsets.py`. Module docstring names this plan and backlog `7jl2bf` and states it is pure and cwd-independent (takes `repo_root` and paths explicitly, never imports `check_engine`), matching `spec_citations`. Provide a frozen dataclass `StaleSourceOffset(file: Path, line: int, cited: str, target: Path, offset: int, validity: str)` and `stale_source_offsets(repo_root, paths) -> List[StaleSourceOffset]`. Behavior: (a) TARGET INDEX: walk `repo_root` for `.py` files skipping `artifact_core.is_ignored_path` (with `artifact_core.get_ignored_dirs`), indexed by repo-relative POSIX path and by basename. (b) SCAN: for each `.py` file under `paths` (walk directories as `stale_spec_anchors` does), skip it outright when the citation regex `\b([A-Za-z_][\w/.]*\.py):(\d+)(?:-(\d+))?\b` does not match the raw text (a cheap prefilter, measured at authoring to halve wall time), otherwise tokenize it with `tokenize.generate_tokens` and examine only `COMMENT` tokens and DOCSTRING `STRING` tokens (a string token that is a statement by itself: the previous significant token is absent or is `NEWLINE`/`INDENT`/`DEDENT`), mapping each physical line of a multi-line docstring to its own line number. A file that fails to tokenize is skipped, never raised. (c) RESOLVE the cited name: an exact repo-relative path in the index wins; else a file of that basename in the citing file's own directory; else the basename when it is UNIQUE in the index; otherwise the citation is UNRESOLVABLE and is not reported (dangling file names are `--source-citations`' subject, not this one's). (d) VERDICT: call `spec_citations._resolve_offset(lines, [], [False] * (len(lines) + 1), offset)` for the start offset, mapping `past_eof` and `blank_line` straight through; when it returns `valid`, report `punct_only` if the target line's stripped text consists only of brackets, commas, colons or semicolons (for example a bare `)` or `),`); for a range, also report `past_eof` when the END offset exceeds the file length. (e) HISTORICAL EXEMPTION (OQ-02): skip a citation whose citing physical line contains a token of 7 to 40 lowercase hex characters carrying at least one digit and at least one letter (a commit hash). Return findings sorted by `(file, line, offset)`.
  - Depends on: E-01
  - Expected outcome: `stale_source_offsets` returns one finding per defective offset on a fixture, and none for valid, string-literal, unresolvable or hash-qualified citations.
  - Execution state: pending
- [ ] E-03 REGISTER THE RULE. Add `"check.source-offset-stale": RuleSpec("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` to `check_engine.RULE_REGISTRY` beside `check.spec-anchor-stale`, with a comment naming this plan and backlog `7jl2bf` and giving the reason it is `info` (OQ-01): it is a heuristic over prose, and spec `ipd-structure-and-linting` Section 10.2 records that "a gate that false-positives trains authors to bypass it"; invariant `""` for the same reason the `check.spec-anchor-stale` comment gives (no catalog invariant governs citation freshness).
  - Depends on: E-01
  - Expected outcome: `check_engine.rule_spec("check.source-offset-stale").severity` returns `info`.
  - Execution state: pending

### Task group 3: CLI surface

- [ ] E-04 ADD `aw check --source-offsets`. In `cli._build_parser`, beside the `--source-anchors` argument, add `--source-offsets` (`dest="source_offsets"`, `store_true`) with help text "Scan Python comments and docstrings for <file>.py:<line> citations that point past end of file, at a blank line, or at a punctuation-only line (opt-in, advisory info; never changes the exit status)." In `cli._run_check`, add an `if getattr(args, "source_offsets", False):` branch modelled on the `--source-anchors` branch (same scan roots `agent_workflows`, `tools`, `tests`), with these differences: build each `Diagnostic` with `rule="check.source-offset-stale"`, `location` `<citing file>:<line>`, a detail naming the cited text, the resolved target path, the offset and the validity, and `severity=check_engine.rule_spec("check.source-offset-stale").severity`; derive `exit_code` as 1 when any diagnostic severity is not `info`, else 0; set `status = "conforms" if exit_code == 0 else "findings"` (never the hardcoded `exit_code = 0` beside `status = "findings"` pairing that backlog `g3ropl` records as crashing the `aw.agent/v1` validator); count the `rules` evidence by severity; render human lines as `<file>:<line>: <cited> -> <validity>`. Place the new branch AFTER the `--source-anchors` branch, so the existing first-match precedence among the opt-in scan flags (`--source-citations`, then `--source-anchors`) is unchanged, and append to the help text "Not combined with --source-citations or --source-anchors; when given together the first of those runs." so the precedence is not silent. Extend `cli._build_check_continuation` with an `is_source_offsets` keyword returning `aw check --source-offsets --agent --limit <n>`. Do NOT touch the `--source-anchors` branch.
  - Depends on: E-02, E-03
  - Expected outcome: `aw check --source-offsets` and `aw check --source-offsets --agent` both exit 0 on a fixture with findings, print the findings, and emit no traceback; bare `aw check` does not run the detector.
  - Execution state: pending
- [ ] E-05 RECORD THE USER-VISIBLE CHANGE. Add one `CHANGELOG.md` line under the pending 2.0.0 section, plain prose with no em or en dashes (user-facing): "Added: `aw check --source-offsets` reports Python comment and docstring citations of the form `file.py:LINE` that point past the end of the file, at a blank line, or at a line holding only punctuation. It is opt-in and advisory, so it never changes the exit status, and a citation that names a commit hash is treated as historical and skipped."
  - Depends on: E-04
  - Expected outcome: the CHANGELOG carries the line.
  - Execution state: pending

### Task group 4: Tests

- [ ] E-06 ADD BEHAVIORAL TESTS in a new `tests/test_source_offsets.py`, over self-written `tmp_path` fixtures only and never the live tree census (P16: call the function and drive the CLI, assert on returned findings, printed output, JSON records and exit codes). Cases: (a) a comment citing `target.py:999` against a 5-line `target.py` yields one `past_eof`; (b) a docstring line citing an offset that lands on a blank line yields one `blank_line` with the docstring's physical line number; (c) a citation landing on a bare `)` yields one `punct_only`; (d) a citation landing on real code yields none; (e) the same past-EOF citation inside an ordinary string literal assignment yields none; (f) a citation naming a file that does not exist yields none; (g) a past-EOF citation whose line also carries `at 6e299712f` yields none; (h) a range `target.py:2-999` yields one `past_eof`; (i) a basename citation resolves to the sibling file in the citing directory when two same-named files exist elsewhere; (j) `cli.main(["check", "--source-offsets", "--dir", <fixture>])` returns 0 and prints the finding; (k) `aw check --source-offsets --agent --dir <fixture>` run as a subprocess (`sys.executable -m agent_workflows`, with `PYTHONPATH` at the checkout, `AW_NO_REEXEC=1`, and `HOME`/`XDG_CONFIG_HOME` in `tmp_path`, so the subprocess imports THIS checkout's package and not an installed one) exits 0, writes no traceback to stderr, and its first JSON record carries outcome `conforms` and a `check.source-offset-stale` diagnostic with severity `info`; (l) a clean fixture through the same `--agent` command exits 0 with no diagnostic. Then run the bare suite and compare with the E-01 baseline.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: every test in the new file passes; the bare suite shows no new failures relative to E-01.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `spec_citations` is the precedent for a pure, cwd-independent citation detector behind an opt-in `aw check` flag; its module docstring states "PURE AND CWD-INDEPENDENT: takes repo_root and paths explicitly, never imports check_engine."
- `spec_citations._resolve_offset` already returns the verdicts `past_eof`, `in_fence`, `blank_line` and `valid`; backlog `7jl2bf` names reuse of that mechanism ("THE ACTUAL GAP IS SUBJECT, NOT MECHANISM").
- `check_engine.rule_spec` is the single lookup for a rule's registered severity; `artifact_core.drift_exit_code` exempts only `info` from the nonzero exit; the `aw.agent/v1` validator refuses `exit 0` beside outcome `findings` (`agent_schema.POSITIVE_OUTCOMES` is `("clean", "ok", "conforms")`), which is the `g3ropl` crash pending plan `fz3i3m` fixes in the sibling branch.
- `tests/test_spec_citation_anchors.py` and `tests/test_source_citation_scan.py` set the test posture: self-written fixtures, `cli.main([... "--dir", str(tmp_path)])` or a subprocess, no live-tree counts.
- CHANGELOG entries are single `- Added:`/`- Changed:` lines under the pending 2.0.0 heading.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The gap is the SUBJECT, as the backlog says: `spec_citations.stale_spec_anchors` builds its target set from `specs._spec_files`, so only `.spec.md` offsets are resolved; `artifact_refs.check_source_citations` calls `dead_filename_citations(... verify_on_disk=True ...)`, which checks file existence and never reads an offset. | Read at authoring at HEAD `59fddefa2`. |
| F-02 | Re-measured at HEAD `59fddefa2` with a throwaway script implementing exactly E-02's rules (comments and docstrings only, the E-02 resolution order): 37 resolvable offsets, 3 unresolvable names skipped, 8 defective: 3 past EOF in `agy_runipd.py` (citing `oc_runipd.py` at 8766, 8645 and 8834 against a 5582-line file), 4 blank-line (`runner_shared.py` citing `ipd_lifecycle.py:3989` and `cli.py:8487`; `tests/test_oc_runipd.py` citing `oc_runipd.py:4823`; `tests/test_runner_shared.py` citing `agy_runipd.py:2190`), and 1 punctuation-only (`selectors.py` citing `status_set.py:132`, a bare closing brace). | Script output pasted at authoring: "resolved 37 skipped 3 8" followed by the 8 tuples. RE-MEASURED AT REVIEW, HEAD `dcdc79632`, with a script implementing E-02's rules: "resolved 37 unres 3 7"; the `tests/test_oc_runipd.py` site (comment quoting `plan_repo = Path(work_dir) if work_dir else repo`) now lands on a non-blank line and is no longer reported, the other 7 are unchanged. The population drifts with every commit, so E-02/V-02 judge against a re-derivation, not this count. The backlog's own 2026-10-02 sample (51 offsets, 12 defective) predates `fnbtta`, which fixed the `runner_shared.py` sites it counted. |
| F-03 | Restricting extraction to comments and docstrings removes the fixture false positives a naive regex finds. A whole-line regex scan of the same tree reports 11, the extra 3 being test FIXTURE DATA: `tests/test_defect_report.py` `"where": "mod.py:12"` and two `tests/test_ipd_lint.py` lint-fixture strings, whose offsets are the line-as-subject case spec Section 10.2 exempts. | Naive scan at authoring: "total 49 {'past_eof': 4, 'blank': 6, 'punct': 1}", the 3 extras listed above. |
| F-04 | No live defective citation names a commit hash, so the historical exemption (OQ-02) costs no true positive today. | A hex-token scan of the 8 citing lines at authoring returned nothing. |
| F-05 | Cost is acceptable for an opt-in flag: about 2.0s wall on this tree with the raw-text prefilter (4.7s without it), against a command nobody runs by default. | `/usr/bin/time` at authoring: "1.91 user 2.00 real" with the prefilter, "4.56 user 4.66 real" without. |
| F-06 | Folding Python offsets into `--source-anchors` would couple this advisory heuristic to pending plan `l85xvi`, which promotes `check.spec-anchor-stale` to `error` and runs `--source-anchors` as a fail-closed CI step. A separate flag and rule id keeps the two severities independent and keeps this plan off the lines `fz3i3m` rewrites. | `l85xvi` Scope: "Re-register `check.spec-anchor-stale` as `error`" and "Add ONE fail-closed step ... running `python -m agent_workflows check --source-anchors --agent`". |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Pure detector reusing `spec_citations._resolve_offset` (E-02) and the `info` rule registration (E-03).
3. Opt-in CLI flag with severity-derived exit (E-04) and the CHANGELOG line (E-05).
4. Fixture tests and suite comparison (E-06).

## Deferred / out of scope (with reason)

- FIXING THE 8 LIVE DEFECTIVE CITATIONS F-02 lists. A comment sweep is a separate concern from building the report and is verified BY the report.
  - Carrier: jem77o
- PROMOTING `check.source-offset-stale` ABOVE `info`, OR RUNNING IT IN CI OR BY DEFAULT. Refused on the repository's own measured position for prose heuristics (OQ-01).
  - Carrier-Declined: spec `ipd-structure-and-linting` Section 10.2 records the advisory tier for a prose-citation heuristic as "a measured final position, not a provisional one"; a plan wanting a gate must first measure this rule's false-positive rate on post-sweep code.
- CITATION-FORM CHECKING for source (a bare offset with no symbol beside it). Resolvability is this rule's subject; form is `IPD-C801`'s, and that rule is scoped to plans.
  - Carrier-Declined: Section 10.2 governs IPD prose, not source comments; extending form rules to code is a separate policy decision nobody has asked for.
- A CUTOVER DATE (OQ-04). Not built.
  - Carrier-Declined: the rule is opt-in and advisory and Order 03 brings its census to zero, so there is no untouched corpus to shield; a per-line date gate would need `git blame` per citation.

## Scope check

- Over-scope: none. Each declared path is modified: `source_offsets.py` (E-02, new), `check_engine.py` (E-03), `cli.py` (E-04), `CHANGELOG.md` (E-05), `tests/test_source_offsets.py` (E-06, new).
- Under-scope: none known. If E-01 finds `fz3i3m` changed `_resolve_offset`'s contract, E-02 adapts to it without editing `spec_citations.py`; if adaptation proves impossible, implement the two verdicts locally and record why.

## Required tests / validation

- New fixture tests (E-06) asserting only on returned findings, printed output, JSON records and exit codes.
- Executed CLI probes on the real tree: `aw check --source-offsets` (expect findings, exit 0) and `aw check --source-offsets --agent` (expect a valid record with outcome `conforms`, no traceback, exit 0).
- The bare suite `python3 -m pytest`, compared with the E-01 baseline.

## Spec / documentation sync

N/A for specs: no spec governs citations inside Python source. Spec `ipd-structure-and-linting` Section 10.2 governs IPD prose and is only cited here as the severity precedent, never edited. The flag's `--help` text (E-04) and the `CHANGELOG.md` line (E-05) are the user-facing documentation.

## Open questions

### OQ-01: What severity should the widened check carry?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: `info`, opt-in, never changing the exit status. Both precedents the backlog names point the same way: `check.spec-anchor-stale` ships `info`, and spec `ipd-structure-and-linting` Section 10.2 records the advisory tier for a prose-citation heuristic as "a measured final position, not a provisional one" because "a gate that false-positives trains authors to bypass it". F-03 shows the residual false-positive class is real (fixture strings), even if comment/docstring extraction removes the measured instances. A separate rule id and flag (F-06) keeps this decision independent of `l85xvi`'s promotion of the spec-anchor rule.

### OQ-02: Is a historical citation exempt?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: yes, when the citing line names a commit hash. A citation describing code "as it stood at <commit>" has no correct current offset, so a past-EOF verdict on it would be a false positive by construction. Keying on a hex token on the same line is mechanical and cheap, and F-04 shows it suppresses no live true positive. Prose such as "previously" without a hash is NOT exempt, because it gives a reader no way to locate the cited state.

### OQ-03: Should the rule report an offset the repository's policy says should not be there at all?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: the rule judges RESOLVABILITY only and reports regardless of FORM. Section 10.2 form (c) permits a trailing offset beside a symbol, and such an offset can still point past end of file; a resolvability check is the only thing that would catch it. Form is `IPD-C801`'s subject and applies to plans, so this rule neither duplicates nor contradicts it.

### OQ-04: Should a cutover date gate it?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: no. `IPD-C801`'s cutover exists because it reports by default on every `aw ipd lint` and would otherwise flood an untouched corpus. This rule is opt-in and never changes the exit status, and Order 03 (`jem77o`) sweeps the 8 live findings, so there is no legacy corpus to shield; a per-citation date gate would also need `git blame` on every hit, multiplying a cost F-05 already measures at about 2s.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted bare-suite summary line and failing-id set, the pasted absence proofs for both new files and the flag, and the pasted `_resolve_offset` signature line.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output of a one-off `python3 -c` call of `source_offsets.stale_source_offsets` on the real tree (roots `agent_workflows`, `tools`, `tests`) listing each finding as `file:line cited validity`, compared line by line against the 8 sites in F-02 (any difference explained by commits since `59fddefa2`), plus the passing output of E-06 cases (a) through (i).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output of `python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('check.source-offset-stale'))"` showing severity `info`, and the passing output of `python3 -m pytest tests/test_severity_tier_contract.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted real-tree output of `aw check --source-offsets` with its `echo $?` of 0, and the pasted first JSON record of `aw check --source-offsets --agent` showing outcome `conforms`, exit 0 and `check.source-offset-stale` diagnostics, with nothing on stderr (produced by `cli._run_check`'s new `--source-offsets` branch); plus a pasted `aw check --help` excerpt showing the flag.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the pasted `git diff CHANGELOG.md` showing the single added line, containing no em or en dash.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the pasted runner output of `python3 -m pytest tests/test_source_offsets.py` with every test passing, and the pasted bare-suite summary line with its failing-id set compared against E-01 (no new failures).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Readiness is an output of `/plan-review` (recorded in front matter). Explicit human approval is required before execution.

EXECUTION CONTRACT. OQ-01..OQ-04 are resolved from repository evidence; no question is open. Execute E-items in dependency order. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): paste ACTUAL runner output for every test claim, and a claim without pasted output satisfies no `V-*`; run the suite bare (`python3 -m pytest`).

SCOPE FENCE. Do NOT edit `agent_workflows/spec_citations.py`, the `--source-anchors` branch of `cli._run_check`, `.github/workflows/tests.yml`, any spec, or any comment the report flags (Order 03 owns those). An out-of-scope edit that proves necessary is MADE and then JUSTIFIED to `aw ipd finalize` with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.

POST-GATE LIFECYCLE. Do not move this plan to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries observed evidence. Under `aw oc run` / `aw agy run` the runner performs finalize; executed by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do not set backlog `7jl2bf` `done` here: it closes when Order 03 executes.
