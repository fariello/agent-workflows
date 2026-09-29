# IPD: Redact absolute paths at the one refusal writer so every refusal code inherits leak protection

- Date: 2026-09-29
- Kind: child
- Concern: `render_stream.record_refusal` is the ONE refusal writer and it performs no path redaction, so a refusal whose `reason`/`remedy` embeds an absolute home path prints that path verbatim in the run summary's Diagnostics block, in `aw runs`, and in that command's JSON, while its two sibling readers `integration_refusal_detail` and `review_integration_refusal_detail` both redact for exactly this surface.
- Scope: Writer-side redaction inside `render_stream.record_refusal`, a REQUIRED widening of `_ABSOLUTE_PATH_IN_TEXT` so a slash command such as `/spec-review` is not mangled into `<path>`, one existing assertion in `tests/test_cross_tree_session_refusal.py` retargeted from the raw absolute path to the redacted form, and new tests pinning the redaction and the slash-command non-mangling. NOT the reader-side redaction in the two sibling readers (left in place, measured idempotent), NOT `Refusal.from_obj` (a reader over frozen state), NOT the 37 producer call sites, and NOT the `events.jsonl` payloads or the stderr lines the producers print.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_cross_tree_session_refusal.py, tests/test_refusal_record_redaction.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: i597pz
- Blocks-Release: next
- Set: refusalleak
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 7sc8fk

## Workflow history

- 2026-09-29 draft (opencode): created.
- 2026-09-29 to-review (opencode): authored from backlog item `i597pz`. The item's fix direction (redact at the one writer) was PROTOTYPED AND MEASURED in this lane, and the measurement found the item's plan INSUFFICIENT AS STATED: the naive one-line writer-side redaction breaks three shipped tests, two of which are the shipped redactor MANGLING A SLASH COMMAND and are real operator-facing regressions rather than test churn (F-04, F-05). The plan records that correction rather than inheriting the item's direction unexamined.

## Goal

Make every refusal record path-redacted AT THE WRITER, so all 37 producer call sites and every future refusal code inherit leak protection without each author remembering it. Because the shipped redactor cannot currently tell an absolute path from a slash command, the plan also widens the pattern to require at least two path segments, which is what makes the writer-side redaction safe to apply to remedies that legitimately name `/spec-review`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the redactor safe to apply to a remedy

- [ ] E-01 Widen `_ABSOLUTE_PATH_IN_TEXT` so a single-segment root-relative token (a slash command) is NOT matched, by requiring one or more interior `/` separators (`(?:[\w.\-+@]+/)+` rather than `*`), and record in the comment that the pattern's coarseness is now bounded by this one property because it is about to run over every refusal remedy.
  - Depends on: none
  - Expected outcome: `_redact_absolute_paths("/spec-review x")`, `("/plan-review")`, `("/exec-set abc")` and `("/whatnext")` all return their input UNCHANGED; `_redact_absolute_paths` still redacts `/home/<user>/VC/agent-workflows` to `<path>` and still rewrites a path under a recognized marker to its tail (`.aw/worktrees/q`); the two sibling readers' shipped behavior on their own inputs is unchanged.
  - Execution state: pending

### Task group 2: redact at the one writer

- [ ] E-02 Redact `reason` and `remedy` through `_redact_absolute_paths` inside `record_refusal` before constructing the `Refusal`, and state in the docstring that the writer is the redaction point so every code inherits it, naming the sibling readers as the precedent.
  - Depends on: E-01
  - Expected outcome: a `record_refusal` whose `reason`/`remedy` embed an absolute home path stores the REDACTED text in `item["refusal"]`, so the Diagnostics block, `aw runs`' two refusal surfaces and its JSON all print the redacted form; `code` is NOT redacted (it is a machine token with no path in it); `Refusal.__post_init__`'s non-empty invariant still holds because redaction never empties a non-empty string.
  - Execution state: pending

### Task group 3: the one shipped assertion this changes

- [ ] E-03 Retarget the `tests/test_cross_tree_session_refusal.py` assertion that requires the RAW absolute sweep-lane path inside the recorded refusal reason, so it asserts the redacted form instead, and state in the test why the raw path must NOT be there.
  - Depends on: E-02
  - Expected outcome: `tests/test_cross_tree_session_refusal.py` passes; its `events.jsonl` assertions on `lane_tree`/`operator_tree` are UNTOUCHED and still assert the raw absolute path, because that file is gitignored durable state and not the copied summary.
  - Execution state: pending

### Task group 4: coverage

- [ ] E-04 Add `tests/test_refusal_record_redaction.py` pinning the writer-side redaction end to end through `render_run_summary_table`, through `run_viewer`'s two refusal surfaces, and through the JSON record, using a synthetic absolute home path.
  - Depends on: E-02
  - Expected outcome: new tests FAIL on the pre-E-02 tree by finding the synthetic path verbatim in each rendered surface, and pass after E-02; each asserts on RENDERED OUTPUT rather than on source text.
  - Execution state: pending

- [ ] E-05 Add the slash-command non-mangling regression to the same new test file, asserting that a remedy naming `/spec-review`, `/plan-review`, `/exec-set` and `/whatnext` survives `record_refusal` verbatim, and that `record_refusal` is idempotent under re-application.
  - Depends on: E-01, E-04
  - Expected outcome: the four slash commands round-trip unchanged through `record_refusal`; applying `_redact_absolute_paths` to an already-redacted string is a no-op, so a reader that redacts again (the two sibling readers still do) cannot double-mangle.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or by a quoted content string, not by a bare line number, since an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE LEAK RULE THIS PLAN ENFORCES IS ALREADY WRITTEN, and both sibling readers cite it in their own docstrings: `integration_refusal_detail` states "the end-of-run summary is the most-copied output in the product ... and `AGENTS.md`'s leak rule forbids machine-identifying strings in a public artifact", and `review_integration_refusal_detail` says it redacts "for the same reason". This plan extends that established policy to the writer rather than inventing one.
- ASSERT ON OBSERVABLE BEHAVIOR, never on code structure (`AGENTS.md`; GUIDING_PRINCIPLES P16). E-04 and E-05 call `record_refusal` and the renderers and assert on returned strings and rendered lines; no test reads production source text, counts call sites, or pins a docstring.
- REDACT AT ONE PLACE, WHICH IS THE ITEM'S OWN STATED SCOPE ("redact at the ONE writer so every refusal code inherits it, rather than at each call site"). The repository's F-4 defect class is precisely a reader and a writer drifting apart, and `record_refusal`'s docstring already says it exists so "the reader and the writer cannot drift apart the way F-4 measured".
- A REFUSAL MUST KEEP ITS REMEDY ACTIONABLE. `Refusal`'s docstring records the measured failure that a gate saying only "X is forbidden" gets complied with by DELETION, which is why `remedy` is required and non-empty. A redaction that mangles the command inside a remedy therefore breaks a load-bearing property, and that is exactly the regression E-01 exists to prevent (F-04).
- `render_stream` IMPORTS NO FIRST-PARTY MODULE (stdlib only), which the `Refusal` docstring states is what makes it the safe home for a type both renderers and runners see. This plan adds no import: `_redact_absolute_paths` and `re` are already in the module.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE LEAK REPRODUCES AT THIS LANE'S HEAD, so it is live.** Calling `record_refusal` with `reason` and `remedy` each embedding an absolute home path and rendering through `render_run_summary_table` prints BOTH verbatim: the Diagnostics line reads `• abc123: merge-refused (suite FAILED with exit 1 in /home/<user>/VC/agent-workflows (no summary line parsed))` and the next line reads `→ remedy: inspect the lane at /home/<user>/VC/agent-workflows/.aw/worktrees/abc123 then retry`. This confirms the item's measurement. | Probe at HEAD `7dfefc82` constructing the refusal and capturing the rendered lines containing the synthetic user token. |
| F-02 | **THE ASYMMETRY THE ITEM DESCRIBES IS EXACTLY AS RECORDED.** `record_refusal`'s body is three statements and contains no redaction call; `integration_refusal_detail` ends `return _redact_absolute_paths(detail)` and `review_integration_refusal_detail` ends `return _redact_absolute_paths(str(detail))`. So protection exists on the legacy-field read path and not on the `Refusal`-record path, which is the newer and preferred one. | Read of all three function bodies. |
| F-03 | **THERE IS A LIVE PRODUCER THAT DEMONSTRABLY FEEDS AN ABSOLUTE PATH IN, so this is not a theoretical leak.** `runner_shared`'s cross-tree session arm builds `refusal_reason` as `f"cannot carry operator session {op_session!r} bound to {op_tree!r} into isolated sweep lane {lane_tree!r}: ..."` where `op_tree = str(repo)` and `lane_tree` is the sweep lane's absolute path, and passes it straight to `record_refusal` along with a `remedy` that repeats `lane_tree`. Both reach the Diagnostics block verbatim. A second family is the suite-check reasons (`f"suite FAILED with exit {exit_code} in {repo_dir} ..."`, plus the timeout/127/passed variants), which is the exact string `integration_refusal_detail`'s docstring quotes as the reason IT redacts. | Read of the cross-tree arm and of its `record_refusal` call; read of the four `SuiteCheckResult.reason` branches; render probe from F-01 using the cross-tree wording, which printed both paths. |
| F-04 | **THE NAIVE WRITER-SIDE FIX BREAKS THREE SHIPPED TESTS, and this is the finding that shapes the plan.** Prototyping the item's direction as a one-line redaction of `reason`/`remedy` in `record_refusal` and running the BARE suite gives `3 failed, 3243 passed, 2 skipped` (baseline `3246 passed, 2 skipped`). The three are `tests/test_cross_tree_session_refusal.py::test_oc_runipd_sweep_lane_turn_refusal` and two `tests/test_spec_review_dispatch.py::TestSpecReviewDispatchE07` cases. So the item's fix as stated is incomplete, which is why this plan has E-01 and E-03 and not one item. | Prototype applied to `record_refusal` alone; BARE `python3 -m pytest` summary line captured; tree restored and re-verified green afterwards. |
| F-05 | **TWO OF THOSE THREE FAILURES ARE A REAL OPERATOR-FACING REGRESSION, NOT TEST CHURN: the shipped redactor MANGLES A SLASH COMMAND.** `_ABSOLUTE_PATH_IN_TEXT` is `(?<![\w/])/(?:[\w.\-+@]+/)*[\w.\-+@]+`, whose `*` quantifier makes the interior separators OPTIONAL, so a single-segment token beginning with `/` matches and is replaced by `<path>`. Measured: `/spec-review` becomes `<path>`, and so do `/plan-review`, `/exec-set` and `/whatnext`. The spec-review refusal arm builds `remedy = f"/spec-review {rel_target}"`, so under the naive fix its remedy became `<path> .aw/records/specs/to-review/<name>.spec.md`, destroying the command the operator is told to run. That is the deletion-by-compliance failure `Refusal`'s own docstring warns about, so the correct response is to FIX THE PATTERN (E-01) rather than to relax the tests. | The regex read from source; a probe over `/spec-review`, `/plan-review`, `/exec-set`, `/whatnext` under the shipped pattern, all four returning `<path>`; the two failing assertions' messages, each reading `'/spec-review' not found in '<path> .aw/records/specs/...'`; read of the `remedy = f"/spec-review {rel_target}"` producer. |
| F-06 | **THE WIDENED PATTERN FIXES BOTH OF THOSE AND COSTS NO REDACTION COVERAGE.** Changing `(?:[\w.\-+@]+/)*` to `(?:[\w.\-+@]+/)+` (one or more interior separators) leaves all four slash commands UNCHANGED while still redacting `/home/<user>/VC/agent-workflows` to `<path>`, `/home/<user>/VC/agent-workflows/.aw/worktrees/q` to `.aw/worktrees/q`, `/tmp/<tmpdir>/sweep_lane` to `<path>`, `/etc/passwd` to `<path>` and `/usr/bin/git` to `<path>`. Applying BOTH E-01 and E-02 and running the BARE suite gives `1 failed, 3245 passed, 2 skipped`: the two spec-review failures are GONE, leaving only the one assertion E-03 legitimately retargets. | Side-by-side probe of the shipped and widened patterns over eleven inputs with both outputs printed; BARE `python3 -m pytest` with both changes applied, summary line captured; tree restored to green afterwards. |
| F-07 | **THE ONE REMAINING FAILURE IS A TEST ASSERTING THE LEAK ITSELF, so retargeting it is correct rather than a weakening.** `test_oc_runipd_sweep_lane_turn_refusal` asserts `self.assertIn(str(sweep_lane), refusal.get("reason", ""))`, i.e. that the recorded refusal reason CONTAINS the absolute sweep-lane path. That is the precise string this plan exists to remove, so the assertion and the fix are in direct contradiction and one must change. Its neighbouring assertions on the `events.jsonl` record (`lane_tree`, `operator_tree`) are a DIFFERENT surface: `.aw/records/runs/` is gitignored (`git check-ignore` confirms, via `.aw/.gitignore:records/runs/`), so that durable state legitimately keeps full paths and E-03 leaves those assertions untouched. | The failing assertion read in context; its failure message `'/tmp/<tmpdir>/sweep_lane' not found in "... bound to '<path>' into isolated sweep lane '<path>' ..."`; `git check-ignore -v` on a path under `.aw/records/runs/`; read of the adjacent event assertions. |
| F-08 | **FOUR SEPARATE SURFACES INHERIT THE FIX, which is the argument for the writer over a per-reader patch.** A recorded `Refusal` is read out by `render_stream.render_run_summary_table`'s Diagnostics block (`{refusal.reason}` and `{refusal.remedy}`, plus the `AWAITING HUMAN DECISION` arm), by `run_viewer.format_refusal_summary`, by `run_viewer.render_step_details` (explicitly "the FULL, untruncated reason and remedy"), and by `run_viewer`'s JSON builder as `rec["refusal"] = rf.to_dict()`. Patching readers instead would mean four edits plus every future one, and `run_viewer`'s detail view documents that it elides nothing. | `rg` for `refusal.reason`/`refusal.remedy`/`rf.remedy` across `agent_workflows/`; each of the four sites read in context. |
| F-09 | **THERE ARE 37 `record_refusal` CALL SITES, so per-call-site redaction is the wrong shape.** They are distributed 34 in `runner_shared.py`, 2 in `render_stream.py` (the definition and `record_integration_refusal`'s delegation), and 1 in `oc_runipd.py`. This is the item's stated reason for fixing the writer, and it is also the CAUTION the item files rather than fixing inline: a redaction at the writer rewrites messages that were not individually examined, which is why E-04/E-05 pin the behavior and V-05 requires a before/after comparison over the real producer strings. | `rg -c 'record_refusal\('` per file. |
| F-10 | **REDACTION IS IDEMPOTENT, so the two sibling readers can keep redacting and nothing double-mangles.** Applying `_redact_absolute_paths` twice to `"suite FAILED in /home/<user>/VC/agent-workflows (x)"` and to `"lane /home/<user>/x/.aw/worktrees/q"` yields byte-identical results at both passes. This is what makes E-02 additive rather than a coordinated change: the readers are left exactly as they are, and the two paths (legacy field, `Refusal` record) converge on the same text. | Two-pass probe over both inputs with both outputs compared. |
| F-11 | **`code` MUST NOT BE REDACTED, and the reason is mechanical.** Refusal codes are machine tokens matched by identity elsewhere: `render_run_summary_table` branches on `refusal.code == GATE_ANSWER_NEEDS_HUMAN_CODE` to render the AWAITING HUMAN DECISION arm, and shipped tests assert exact codes (`"cross-tree-session-refused"`, `SPEC_REVIEW_REFUSAL_CODE`). None contains a path. Redacting `code` would risk breaking that dispatch for no leak benefit, so E-02 redacts only `reason` and `remedy`. | Read of the `GATE_ANSWER_NEEDS_HUMAN_CODE` comparison; the two shipped code-equality assertions read; inspection of the code constants for path-like content. |
| F-12 | **`Refusal.from_obj` IS DELIBERATELY NOT TOUCHED, which bounds this plan honestly.** It is the tolerant READER over durable state whose docstring says the input is "a JSON file a previous driver version wrote". A run directory frozen BEFORE this plan still carries unredacted text and will still render it, because this plan changes the writer only. Since `.aw/records/runs/` is gitignored (F-07) that text is not in a public artifact, and redacting on read would additionally defeat F-10's convergence argument by adding a second place the policy lives. | Read of `Refusal.from_obj`'s docstring and body; `git check-ignore` result from F-07. |
| F-13 | **NO OTHER PENDING PLAN DECLARES THIS FILE'S REFUSAL CODE, so the concurrent-edit risk is bounded.** Six pending plans list `agent_workflows/render_stream.py` in `- Scope-Paths:` (`entv1d`, `4taj2e`, `165lkb`, `it6tpj`, `35mjqc`, `zhqt51`). Each names a different region: box-column width measurement (`4taj2e`, `it6tpj`), the malformed-entry table row (`165lkb`), the progress denominator (`35mjqc`), a typed dependency signal (`zhqt51`), and the stranded exit code (`entv1d`). None mentions `record_refusal` or `_redact_absolute_paths`. The one pending plan that DOES mention `record_refusal` is `8eei5p`, and it does not list `render_stream.py` in its scope at all (it cites the function only as F-07 context). Per `AGENTS.md`, file overlap between plans is not a runner hazard; this is recorded so a reviewer knows the regions are disjoint. | `- Scope-Paths:` read from every pending plan naming this file; `rg` for `record_refusal`/`_redact_absolute_paths` across `.aw/records/plans/pending/`; `8eei5p`'s `- Scope-Paths:` read. |
| F-14 | **THE SUITE IS GREEN AT THIS LANE'S HEAD, giving the baseline validation compares against: `3246 passed, 2 skipped, 3 warnings` from a BARE `python3 -m pytest`.** The prototypes of F-04 and F-06 were both reverted and the tree re-verified clean (`git status --short` shows no modification to `agent_workflows/render_stream.py`). | BARE `python3 -m pytest` at HEAD `7dfefc82`, summary line captured; `git status --short` after restoring. |
| F-15 | **NO SPEC GOVERNS THIS BEHAVIOR, so no amendment is owed.** `grep` for `redact` across `.aw/records/specs/` returns hits in exactly two specs: approved `25kzda`, whose single hit is a host-capability bullet ("capture exit/output/diff evidence with redaction and provenance") about worker evidence capture and not about refusal records, and an implemented hierarchy spec. Neither names `record_refusal`, `Refusal`, or the Diagnostics block. The governing rule is `AGENTS.md`'s leak-sanitizer paragraph, which is policy prose rather than a spec contract. | `rg -l redact .aw/records/specs/*/*.spec.md` (two files); the `25kzda` hit read in context. |

## Proposed changes (ordered, validatable)

1. Widen `_ABSOLUTE_PATH_IN_TEXT` to require at least one interior separator, so a slash command is not a path (E-01).
2. Redact `reason` and `remedy` inside `record_refusal`, leaving `code` alone (E-02).
3. Retarget the one shipped assertion that requires the raw absolute path inside the recorded reason, leaving its `events.jsonl` assertions untouched (E-03).
4. Add the end-to-end redaction tests across all four reader surfaces (E-04) and the slash-command plus idempotence regressions (E-05).

## Deferred / out of scope (with reason)

- REDACTING ON READ IN `Refusal.from_obj` is rejected rather than deferred. It would put the policy in two places and defeat the convergence F-10 relies on, and its input is a gitignored run directory rather than a public artifact (F-07, F-12). A frozen pre-fix run rendering its old text is a disclosed limit of a writer-side fix, not an unowned gap.
  - Carrier-Declined: Nothing is owed. The leak this item is about is the text a NEW refusal writes into the most-copied output, and after this plan no new refusal carries an absolute path. No future work is implied.
- REDACTING THE `events.jsonl` PAYLOADS OR THE PRODUCERS' STDERR LINES is out of scope. The events file lives under the gitignored `.aw/records/runs/` and is durable diagnostic state where the full path is the useful fact (F-07); the stderr line is the operator's live console and not a copied artifact. The backlog item scopes itself to the run summary surface.
  - Carrier-Declined: Nothing is owed, because neither is a public artifact. If a future change ever COMMITS a run record, that change would owe the decision, and this plan does not create that situation.
- FIXING THE 37 PRODUCERS TO BUILD RELATIVE STRINGS IN THE FIRST PLACE is out of scope. It is the alternative the item explicitly rejects in favour of the one-writer fix, it would touch four modules, and it cannot protect a future producer. The writer-side redaction makes each producer's sloppiness harmless rather than requiring 37 authors to remember.
  - Carrier-Declined: Nothing is owed. A producer that still names an absolute path is now harmless at the surface this item is about, so no residual defect remains to carry.
- BROADENING THE REDACTOR TO OTHER IDENTIFYING CLASSES (hostnames, usernames outside a path, session ids) is out of scope. `AGENTS.md` points at `aw sanitize` as the deterministic authority for that judgement, and this plan's fence is the one asymmetry the item measured.
  - Carrier-Declined: Nothing is owed here; the sanitizer already owns that scan and reports clean on this tree.

## Scope check

- Over-scope: none. `agent_workflows/render_stream.py` carries E-01's pattern change and E-02's two redaction calls plus their comments; `tests/test_cross_tree_session_refusal.py` carries E-03's single retargeted assertion; `tests/test_refusal_record_redaction.py` is new and carries E-04 and E-05. No producer module is edited, no sibling reader is edited, `run_viewer.py` is not edited even though its three surfaces stop leaking as a consequence (F-08), and no spec is touched (F-15). No `.aw/` record changes beyond this plan.
- Under-scope: a run directory frozen BEFORE this plan still renders its unredacted refusal text, because the fix is writer-side (F-12). That is disclosed rather than omitted, and it is not a public-artifact leak because `.aw/records/runs/` is gitignored (F-07).

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against the F-14 baseline of `3246 passed, 2 skipped`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_refusal_record_redaction.py tests/test_cross_tree_session_refusal.py tests/test_spec_review_dispatch.py tests/test_run_summary_table.py -o addopts=""` for per-test counts on the files this plan writes or whose behavior it changes.
- `python3 -m pytest tests/test_oc_runipd.py tests/test_runner_shared.py tests/test_finalize_sendback.py tests/test_host_capability_wiring.py tests/test_spec_edit_ack_gate.py tests/test_zero_dispatch_outcome.py tests/test_run_selection_policy.py tests/test_carrier_finished_verification.py tests/test_orchestrator_not_approved_reason.py tests/test_dependency_block_reporting.py -o addopts=""` as the targeted regression set: every test file that constructs or reads a refusal record.
- A DELIBERATE-FAILURE DEMONSTRATION for E-04: the new tests must be shown FAILING on the pre-E-02 tree by finding the synthetic absolute path verbatim in each of the four surfaces, since a leak guard that was never red proves nothing.
- A SECOND RED DEMONSTRATION for E-01, which is the evidence an executor is most likely to skip: apply E-02 WITHOUT E-01 and paste the two `tests/test_spec_review_dispatch.py` failures whose messages show `'/spec-review' not found in '<path> ...'`. That contrast is the whole justification for E-01 and it distinguishes this plan from the one-line fix the item proposed (F-04, F-05).
- A SLASH-COMMAND SURVIVAL PROBE over at least `/spec-review`, `/plan-review`, `/exec-set`, `/whatnext` and the repository's other `/`-prefixed workflow names, asserting each survives `record_refusal` byte-identically.
- A REDACTION-COVERAGE PROBE showing the widened pattern still redacts every case the shipped one did: an absolute repository path, a path under `.aw/`, a `/tmp` path, `/etc/passwd`, `/usr/bin/git`. Paste both patterns' outputs side by side over the same inputs and state that no input lost its redaction.
- A NO-CHANGE PROBE for the two sibling readers: run `integration_refusal_detail` and `review_integration_refusal_detail` over their real recorded shapes before and after, asserting byte-identical output, plus the F-10 idempotence check.
- A REAL-PRODUCER BEFORE/AFTER COMPARISON, which is the item's filed CAUTION (F-09): take the actual `reason`/`remedy` strings from at least the cross-tree session arm, the four suite-check branches, the spec-review arm, the carrier-verification arm and `record_integration_refusal`'s two remedy variants, pass each through `record_refusal` before and after, and paste both forms. Every difference must be a path becoming `<path>` or a marker-relative tail, and nothing else. Paste the count of strings compared.
- `aw ipd lint` on this plan, reporting conforming.
- `aw sanitize --agent` before commit, since this plan's evidence quotes rendered output containing synthetic absolute paths. Use an obviously synthetic user token in every pasted probe, never the real home path.
- `aw check` to confirm no new drift, and `aw backlog check` to confirm item `i597pz` is well-formed.
- `git diff --cached --name-only` immediately before committing, which must list exactly the three paths in `- Scope-Paths:` plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be, per F-15.

`grep` for `redact` across `.aw/records/specs/` returns two specs. Approved `25kzda`'s single hit is a host-capability requirement about worker evidence capture ("capture exit/output/diff evidence with redaction and provenance"), not about refusal records or the run summary; the other is an implemented hierarchy spec. Neither mentions `record_refusal`, `Refusal`, or the Diagnostics block, so no contract this plan changes is spec-governed. The governing statement is `AGENTS.md`'s leak-sanitizer paragraph, which is policy prose this plan CONFORMS to rather than amends.

No shipped contract moves in a way a consumer can observe as a regression. `Refusal`'s field names, its `to_dict()` shape, `REFUSAL_KEY`, and `record_refusal`'s signature and return type are all unchanged; only the TEXT stored in two of the three fields changes, and it changes toward the form the two sibling readers already produced for the same surface (F-02). No CLI surface, no exit code, and no `aw.agent/v1` field is added or renamed. The one machine-readable field a tool matches on, `code`, is deliberately left byte-identical (F-11). The two in-source docstrings and the one pattern comment that describe the behavior being changed are amended by E-01 and E-02 themselves, inside a file already in scope.

## Open questions

### OQ-01: Should the fix be at the writer, at the readers, or in the producers?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS THE WRITER, from repository evidence, and it needs no maintainer ruling because the item already scopes it that way and the measurement agrees. FOUR reader surfaces consume a recorded refusal (`render_run_summary_table`'s Diagnostics block, `run_viewer.format_refusal_summary`, `run_viewer.render_step_details`, and `run_viewer`'s JSON builder), so a reader-side fix is four edits plus every future one, and `render_step_details` explicitly documents that it elides nothing (F-08). A producer-side fix is 37 call sites across three modules and cannot protect a future producer (F-09). The writer is one place, it is already the designated choke point (`record_refusal`'s docstring calls itself "THE ONE WRITER" paired with `refusal_of_item`), and because redaction is idempotent (F-10) the existing reader-side redaction in the two sibling readers can stay exactly as it is with no coordinated change.

### OQ-02: Should the shipped `_ABSOLUTE_PATH_IN_TEXT` pattern be changed, or should the slash-command remedies be reworded?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS CHANGE THE PATTERN, because the alternative damages the thing a refusal exists to carry. The shipped pattern's `*` quantifier makes interior separators optional, so `/spec-review` matches and becomes `<path>` (F-05); the spec-review arm's remedy is literally `f"/spec-review {rel_target}"`, so the naive fix printed `<path> .aw/records/specs/...` to an operator, destroying the command they are told to run. REWORDING THE REMEDIES IS REFUSED for two reasons: it would have to be done at every producer that names a slash command, now and forever, which is the per-call-site discipline OQ-01 rejects; and `Refusal`'s own docstring records the measured failure that a message which cannot say what to do next gets complied with by deletion, so mangling the command is a regression in exactly the property `remedy` is required for. A SINGLE-SEGMENT ROOT-RELATIVE TOKEN IS NOT AN ABSOLUTE PATH WORTH REDACTING in any case: `/spec-review` identifies no machine and no user, and measured, requiring one or more interior separators loses no redaction coverage at all (F-06), so the pattern becomes MORE correct rather than merely more permissive.

### OQ-03: Is retargeting the `test_cross_tree_session_refusal` assertion a legitimate fix or a weakening of a guard?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS LEGITIMATE, and stated explicitly because "the fix required me to change a test" is exactly the shape that should draw a reviewer's suspicion. The assertion is `assertIn(str(sweep_lane), refusal.get("reason", ""))`: it requires that the recorded refusal reason CONTAIN an absolute filesystem path, which is the precise string this plan exists to remove from a copied artifact. The assertion and the item's goal are in direct contradiction, so exactly one must change, and the one that encodes the defect is the assertion. WHAT THE TEST MUST STILL PROVE is unchanged and E-03 keeps it: the refusal is recorded, its `code` is `"cross-tree-session-refused"`, the operator session id still appears in the reason (it is not a path and is not redacted), and the lane is still IDENTIFIED, now in redacted form. The test's neighbouring assertions on `events.jsonl` (`lane_tree`, `operator_tree`) assert the RAW absolute path and E-03 leaves them untouched, which is what keeps the guard honest: the full path remains provably recorded in gitignored durable state, and only the copied surface is redacted (F-07).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/render_stream.py` as it stands after E-01 ONLY, showing the quantifier change and the amended comment and NO other executable change (in particular `record_refusal` must still be unmodified at this point). Paste the SLASH-COMMAND SURVIVAL PROBE from Required tests: each of `/spec-review`, `/plan-review`, `/exec-set`, `/whatnext` and every other `/`-prefixed workflow name found in the repository passed through `_redact_absolute_paths`, with input and output printed for each, all identical. Paste the REDACTION-COVERAGE PROBE side by side for the shipped and widened patterns over an absolute repository path, a path under `.aw/`, a `/tmp` path, `/etc/passwd` and `/usr/bin/git`, and state in one sentence that no input lost its redaction. Paste the NO-CHANGE PROBE for `integration_refusal_detail` and `review_integration_refusal_detail` over their real recorded shapes, byte-identical before and after. Paste a BARE `python3 -m pytest` at this point and state it against the F-14 baseline, since E-01 alone must be a no-op for the suite.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/render_stream.py` in full (both changes now present), showing the two `_redact_absolute_paths` calls inside `record_refusal`, the amended docstring, and that `code` is passed through UNREDACTED. Paste a probe reproducing F-01's leak and showing it GONE: the same synthetic-absolute-path reason and remedy recorded and rendered through `render_run_summary_table`, with the Diagnostics and remedy lines pasted, and an explicit assertion that the synthetic user token appears NOWHERE in the render. Paste the same for `run_viewer.format_refusal_summary`, `run_viewer.render_step_details` and the JSON record (F-08), with `git status --short` showing `agent_workflows/run_viewer.py` UNMODIFIED. Paste the F-10 idempotence check and the F-11 check that `refusal.code` is byte-identical before and after and that the `GATE_ANSWER_NEEDS_HUMAN_CODE` branch still renders its AWAITING HUMAN DECISION arm. THEN PASTE THE SECOND RED DEMONSTRATION required by F-05: at a tree with E-02 applied but E-01 REVERTED, the two `tests/test_spec_review_dispatch.py` failures with their messages showing `'/spec-review' not found in '<path> ...'`. Without that contrast a reader cannot tell this plan from the one-line fix the backlog item proposed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `git diff tests/test_cross_tree_session_refusal.py`, showing exactly the one retargeted assertion and NO other change; the `events.jsonl` assertions on `lane_tree` and `operator_tree` must be visibly untouched and must still require the RAW absolute path. Quote the new assertion and the comment explaining why the raw path must not be in the recorded reason. Paste `python3 -m pytest tests/test_cross_tree_session_refusal.py -o addopts=""` green with its per-test count. Confirm in one sentence that the test still proves the refusal is recorded, its code is `"cross-tree-session-refused"`, the operator session id is still present in the reason, and the lane is still identified in redacted form (OQ-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the full committed source of `tests/test_refusal_record_redaction.py` as it stands after E-04, and confirm in one sentence that every assertion is on RENDERED OUTPUT or on a returned string and that none reads production source text, counts call sites, or pins a docstring (GUIDING_PRINCIPLES P16). Paste the tests' output on the PRE-E-02 tree, which must FAIL by finding the synthetic absolute path verbatim, with the failing assertion messages shown for each of the four surfaces. Paste them green after E-02. Confirm the synthetic path used is obviously not the maintainer's real home directory.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the added slash-command and idempotence tests and their green run. Paste the REAL-PRODUCER BEFORE/AFTER COMPARISON that the item's filed CAUTION demands (F-09): the actual `reason`/`remedy` strings taken from the cross-tree session arm, all four suite-check branches, the spec-review arm, the carrier-verification arm and both of `record_integration_refusal`'s remedy variants, each passed through `record_refusal` before and after, with BOTH forms printed. State the count of strings compared, and confirm in one sentence that every single difference is a path becoming `<path>` or a marker-relative tail and that no command, branch name, commit hash, session id or sentence structure changed. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line against the F-14 baseline of `3246 passed, 2 skipped`, comparing failing NODE IDS rather than totals; paste the targeted regression set from Required tests; paste `aw ipd lint` on this plan reporting conforming; paste `aw sanitize --agent` clean; paste `aw check` and `aw backlog check` clean; and paste `git diff --cached --name-only` showing exactly the three scope paths plus this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph, because the plan is LARGER than the one-line change its backlog item describes. The item asks for redaction at the one writer. Measured, that alone breaks three shipped tests (F-04), and two of those breakages are a genuine operator-facing regression rather than test churn: the shipped redactor's pattern treats a single-segment token like `/spec-review` as an absolute path and replaces it with `<path>`, so the spec-review refusal's remedy stopped naming the command the operator must run (F-05). This plan therefore ships TWO production changes: the pattern is widened to require an interior separator (measured to lose no redaction coverage at all, F-06), and only then is the writer-side redaction applied. It also retargets ONE shipped assertion that currently requires an absolute filesystem path to be present in a recorded refusal reason, which is the exact string the plan exists to remove (F-07, OQ-03). The fence is one production file plus two test files; no producer, no sibling reader and no other module is edited, even though three `run_viewer` surfaces and its JSON stop leaking as a consequence (F-08).

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including V-02's SECOND red demonstration and V-05's real-producer before/after comparison. Use an obviously synthetic user token in every pasted probe: this plan's evidence is rendered output that would otherwise contain the maintainer's home path, and `aw sanitize --agent` must be clean before commit. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches only the second of them.

FIRST, SHIPPING E-02 WITHOUT E-01. This is the tempting order, because E-02 is the item's stated fix and E-01 looks like unrelated polish. It mangles `/spec-review` and every other slash command inside a remedy into `<path>`, which is the deletion-by-compliance failure `Refusal`'s docstring exists to warn about. The suite DOES catch this one (two `test_spec_review_dispatch.py` cases go red), and the executor must resist "fixing" those tests: they are correct and the pattern is not. V-02's second red demonstration requires reproducing that state deliberately, precisely so the reasoning is recorded rather than rediscovered.

SECOND, WIDENING THE PATTERN TOO FAR. E-01 must change ONLY the quantifier governing interior separators. Any broader relaxation (making the leading `/` optional, dropping the `(?<![\w/])` lookbehind, narrowing the character class) risks letting a real absolute path through, and the whole point of the plan is that this pattern now runs over every refusal message in the product. V-01's redaction-coverage probe over five path shapes is the check, and it must show every one still redacted.

THIRD, REDACTING `code`. It costs one extra argument and looks more thorough. `render_run_summary_table` dispatches on `refusal.code == GATE_ANSWER_NEEDS_HUMAN_CODE` to render the AWAITING HUMAN DECISION arm, and shipped tests assert exact code strings; no code contains a path, so redacting it buys nothing and risks breaking that dispatch (F-11). V-02 checks the code is byte-identical and that the decision arm still renders.

FOURTH, QUIETLY RELAXING THE `events.jsonl` ASSERTIONS while retargeting the one in the recorded reason. Those two assertions are what keep this plan honest: they prove the full absolute path is STILL recorded in gitignored durable state, so the fix redacts the copied surface without destroying diagnostic information. Weakening them would convert a redaction into a data loss and nothing would notice (F-07, OQ-03).

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. A run directory frozen BEFORE this plan still renders its unredacted refusal text, because the fix is writer-side and `Refusal.from_obj` is deliberately untouched (F-12). The executor must not write a walkthrough or commit message claiming every refusal anywhere is now redacted; the true claim is that every NEWLY RECORDED refusal is path-redacted at the one writer, so all 37 producer call sites and every future refusal code inherit the protection.

This plan inherits `- Blocks-Release: next` from backlog item `i597pz` because its `- Work-Kind:` is `bug`, and the repository policy is that every live bug gates the next release. That gate travels with this plan and must not be cleared as part of executing it.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
