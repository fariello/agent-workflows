# IPD: Resolve the release sentinel through a typed, explicit succession so shipping a release cannot mass-dangle every gated record

- Date: 2026-09-29
- Kind: child
- Concern: `releases.resolve_release` maps the literal `next` ONLY when exactly one release record carries `- Status: planned` (`return planned[0] if len(planned) == 1 else None`). `releases.check_blocks_release` flags every record whose gate value fails to resolve, as `check.blocks-release-dangling`, registered ERROR / I-07 and a member of `check_engine.RELEASE_GATE_RULES`, which `.github/workflows/tests.yml` now runs FAIL-CLOSED. 698 records in this tree carried `- Blocks-Release: next` at authoring, and 775 do at review; it is a LIVE, GROWING count (F-02), so re-derive it rather than quoting either figure. So the ordinary act of shipping the single planned release - marking `f33nrj` `shipped` without creating its successor in the same change - turns all of them into ERROR findings and reds `main`, at exactly the moment the tree can least absorb it. MEASURED on a copy of `.aw/records` at HEAD `ebd2da31`: baseline exit 0 / 0 findings; ship-only exit 1 / 697 findings, every one `check.blocks-release-dangling`; a SECOND planned record added (so `next` is ambiguous rather than absent) exit 1 / 697 again; ship plus successor exit 0 / 0. RE-MEASURED AT REVIEW at HEAD `364bacfe`, same four states, same four outcomes, count now 775. TWO FURTHER DEFECTS THE ITEM DOES NOT RECORD, both measured here and both consequences of the same unresolvable sentinel: (1) `aw set shipped f33nrj` DOES write the transition, non-interactively, exit 0, with no warning that every sentinel gate in the tree is about to dangle, so the item's "the transition is a human act / no shipped code path writes Status: shipped" premise is HALF WRONG and there is a tooled route straight into the red state; (2) the `aw doctor` remediation for the resulting finding instructs the operator to set `- Blocks-Release:` to `next` when the field ALREADY READS `next`, i.e. it prescribes a no-op, once per gated record.
- Scope: Make the sentinel's resolution and the ship transition each fail LOUDLY and CORRECTLY instead of silently mass-dangling. FOUR changes, in one cohesive pass because they are one causal chain. (1) Split the one unresolvable outcome into three DISTINGUISHABLE ones inside `releases`, adding a `resolve_release_outcome` that reports `resolved` / `absent` (zero planned) / `ambiguous` (two or more planned) while `resolve_release` keeps its exact `Optional[Path]` contract and every one of its ten-plus callers keeps working unchanged. (2) Teach `releases.check_blocks_release` to report the ROOT CAUSE ONCE against the releases tree, as two new rules `check.release-sentinel-absent` / `check.release-sentinel-ambiguous`, instead of blaming 698 innocent records that are each correctly authored; a gate value that is a real id6 or version naming no record still reports per-record exactly as it does today. (3) Make `aw set shipped <release>` REFUSE when it would ship the last planned record, naming the successor command, with an explicit attested override flag for the maintainer who means it. (4) Correct the `aw doctor` no-op remediation to name the real fix. DOES NOT change what `- Blocks-Release:` means, DOES NOT touch any of the 698 gated records, DOES NOT relax `check.live-bug-ungated`, DOES NOT add a `releases set` verb, and DOES NOT make the CI step advisory again.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/doctor.py, tests/test_releases.py, tests/test_check_engine_release_gate.py, tests/test_doctor.py, tests/test_release_sentinel_succession.py, .aw/records/releases/README.md, RELEASING.md, .aw/system/workflows/release-review/09-release-execution.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: cnn7au
- Blocks-Release: next
- Set: relnextres
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: x4vf9p
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-301, PR-302, PR-303, PR-304, PR-305 all FIXED, zero deferred, zero open findings. THIS IS AN UNUSUALLY WELL MEASURED PLAN AND ALL THIRTEEN OF ITS FINDINGS REPRODUCE. Review re-drove the four-state experiment independently at HEAD `364bacfe` and got the same four outcomes (baseline exit 0/0; ship-only exit 1 with every finding `check.blocks-release-dangling`; two-planned exit 1 identically, confirming absent and ambiguous are indistinguishable today; ship-plus-successor exit 0/0). F-06 is the sharpest finding and reproduces exactly: a bare `set shipped f33nrj` with NO `--apply` writes the transition and exits 0, while `--apply` is rejected as unrecognized, so there is no preview-then-apply gap and the trapdoor is one silent command wide. F-08 reproduces down to the same offending file, F-09 end to end (a bug filed in the zero-planned state is silently ungated and trips a SECOND error rule), and F-03/F-04/F-05/F-10/F-11/F-12/F-13 verbatim. REVIEW ALSO VERIFIED THE PROPOSED DESIGN, not only the diagnosis, because E-02 edits an error rule in a fail-closed family: on a ship-only tree carrying one planted `nonexist` record, today's 776 findings split 775 suppressible + 1 that MUST survive, so E-02's correct post-fix result is 2 findings and not 1, and that arithmetic is now a measured acceptance criterion in the item (PR-304). Confirmed too that a concrete id6 still resolves in the ambiguous state (which is what makes the narrow suppression safe) and that `get_release_blockers` is untouched by it. Three defects came from driving the plan: E-05 needs `cli.py` to declare its flag and left that path conditional and undeclared (PR-301, now declared); the central count has drifted twice in hours, 608 -> 697 -> 775, while two items still quoted a literal (PR-302, de-literalized, with E-04 told to compute it at runtime); and E-06 is REQUIRED rather than cosmetic because both new rule names fall through `doctor`'s substring match to a generic fallback worse than the no-op they replace (PR-303, measured). Both open questions verified non-blocking with their premises checked (`pqsx96` is genuinely `draft` with an already-incomplete I-07 row; F-09 supports OQ-02's no-change recommendation). The `IPD-Z602` advisory on E-08 is ACCEPTED on the plan's own argument, which review verified via F-10. Bare suite `3246 passed, 2 skipped`; scoped surface `83 passed`; live tree still `check release-gates` exit 0/0; no production file or test modified. Findings and four Decisions rows in `.aw/records/reviews/20260929-relnextres-01-x4vf9p-...review.md`.

- 2026-09-29 to-review (opencode): authored from backlog item `cnn7au`. Every measurement in Findings was taken in this worktree at HEAD `ebd2da31`, against a throwaway copy of `.aw/records` under an untracked scratch directory, never against the tracked tree. THE ITEM'S COUNT AND ONE OF ITS PREMISES ARE CORRECTED HERE RATHER THAN COPIED: the finding count is 697 at this head, not the item's 608 (the corpus grew), and the item's claim that no shipped code path writes `Status: shipped` is HALF WRONG, because `aw set shipped <id6>` writes it (F-06). The item's central diagnosis reproduces exactly, on all three states. The item offered two mutually exclusive fixes, (a) a documented ship-and-succeed obligation and (b) changing how `next` resolves; this plan takes BOTH, because F-07 shows (a) alone cannot hold - the only route into the bad state is already tooled and silent, so a documentation-only fix leaves a green-to-red trapdoor one command wide - and F-04 shows (b) alone is dangerous if done by weakening the check. The reconciliation is that (b) is implemented as SHARPENING rather than weakening: the same states are still ERRORs, but attributed to the one record that is actually wrong.
- 2026-09-29 draft (opencode): created.

## Goal

Make a release cycle that forgets its successor record fail with ONE accurate, actionable ERROR naming the releases tree, instead of 697 inaccurate ones blaming correctly-authored records, and make the tooled route into that state refuse rather than proceed silently. After this plan, the fail-closed CI step still fails on an unresolvable sentinel (the invariant is not weakened), but it says which record is wrong and what command fixes it; and `aw set shipped` on the last planned record refuses, naming `aw releases new`, unless the maintainer explicitly attests they mean it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the three outcomes distinguishable without breaking any caller

- [x] E-01 In `agent_workflows/releases.py`, add a typed outcome probe beside `resolve_release` that distinguishes the three states the current `Optional[Path]` return conflates. Introduce a module-level `SENTINEL_RESOLVED` / `SENTINEL_ABSENT` / `SENTINEL_AMBIGUOUS` string-constant triple (or a `NamedTuple` carrying an outcome plus the matching paths; either is acceptable, but the outcome MUST be a closed enumerated value and not a bare bool), and a function `resolve_release_outcome(repo_root, value)` returning that outcome plus the candidate paths it found. Then REIMPLEMENT `resolve_release` as a thin wrapper over it, preserving its signature `(repo_root: Path, value: str) -> Optional[Path]` and its exact semantics BYTE FOR BYTE, including all three of its non-obvious behaviors: the `next` branch returning a path only on exactly one planned record, the id6 branch gated on `_core.ID6_RE.match`, and the version branch's `v`-prefix tolerance (`val_clean = value.lstrip("v")`) plus its own uniqueness requirement (`if len(matching_ver) == 1`).

  DO NOT CHANGE `resolve_release`'S CONTRACT, AND DO NOT "IMPROVE" IT WHILE YOU ARE IN THERE. It has at least eleven production call sites, enumerated at authoring time: `releases.describe_planned_release`, `releases.load_active_release`, `releases.get_release`, `releases.get_release_blockers`, `releases.check_blocks_release`, `attention._resolve_release_version`, `backlog.decide_gate_default`, `backlog`'s `--blocks-release` validation in `run_new`, two comparisons inside `check_engine._same_release`, and `completion`'s shell-completion offer. Several of those depend on the None-on-ambiguous behavior for correctness rather than by accident: `backlog.decide_gate_default` treats an unresolvable `next` as "file it ungated" and would otherwise write a gate pointing at an ambiguous target, and `completion` uses it to decide whether to OFFER `next` at all. A widened return type or a changed None condition therefore has to be audited across all eleven, which is out of scope; the wrapper keeps every one of them untouched, which is the entire point of doing it this way.
  - Depends on: none
  - Expected outcome: `resolve_release_outcome(repo, "next")` reports `SENTINEL_RESOLVED` with one path on a one-planned tree, `SENTINEL_ABSENT` with zero paths on a zero-planned tree, and `SENTINEL_AMBIGUOUS` with both paths on a two-planned tree. `resolve_release(repo, "next")` returns exactly what it returns today in all three states (a path, None, None), and `python3 -m pytest tests/test_releases.py tests/test_backlog.py tests/test_check_engine_release_gate.py` stays green with no test edits.
  - Execution state: performed

- [x] E-02 In `agent_workflows/releases.py`, register the two new root-cause rules and make `check_blocks_release` attribute an unresolvable SENTINEL to the releases tree exactly once, instead of to every record that names it. Keep the per-record finding for every OTHER unresolvable value. Concretely: inside `check_blocks_release`, probe the sentinel ONCE before the tree walk via `resolve_release_outcome(repo_root, "next")`; if the outcome is `SENTINEL_ABSENT` or `SENTINEL_AMBIGUOUS`, emit ONE `check.release-sentinel-absent` or `check.release-sentinel-ambiguous` Drift located on the releases directory (or, for the ambiguous case, naming the competing records in the detail), and SUPPRESS the per-record `check.blocks-release-dangling` finding for records whose value is literally `next` only. A record whose value is an id6 or version string that resolves to nothing is UNAFFECTED and still reports per-record, because that record really is the wrong one.

  THE SUPPRESSION IS NARROW AND CONDITIONAL, AND GETTING THAT WRONG SILENTLY GUTS AN ERROR RULE. Suppress ONLY when BOTH conditions hold: the record's value is the literal string `next`, AND the sentinel probe returned a non-resolved outcome. Do NOT suppress a `next`-valued record when the sentinel RESOLVES (that combination cannot produce a dangling finding anyway, so a broader guard would be dead code that reads like a real exemption), and do NOT suppress any non-`next` value under any outcome. The severity does not move: register both new rules `error`, `ASSURANCE_REPOSITORY`, `DET_DETERMINISTIC`, invariant `I-07`, identical to the `check.blocks-release-dangling` RuleSpec they stand in for, so the fail-closed CI step still fails. This is a change of ATTRIBUTION, not of enforcement, and the plan is only defensible if the exit code in the bad state stays nonzero.
  - Depends on: E-01
  - Expected outcome: on the ship-only tree, `check_release_gates` returns exactly ONE `check.release-sentinel-absent` finding located on the releases tree, PLUS one per-record finding for every non-`next` unresolvable value, and `python -m agent_workflows check release-gates --agent` still exits 1. On the two-planned tree it returns exactly one `check.release-sentinel-ambiguous` naming both competing records, exit 1. On the one-planned baseline it returns zero findings, exit 0. A record carrying `- Blocks-Release: nonexist` still yields `check.blocks-release-dangling` in every one of the three states.
    THE ARITHMETIC WAS VERIFIED AT REVIEW ON A REAL SCRATCH TREE, so treat this as a measured target rather than a hope. In the ship-only state with one deliberately planted `- Blocks-Release: nonexist` record, today's code emits 776 `check.blocks-release-dangling` findings, of which 775 carry the detail `Blocks-Release 'next' does not resolve...` (the ones E-02 suppresses) and exactly 1 carries `Blocks-Release 'nonexist' does not resolve...` (the one that MUST survive). So the correct post-fix result on that tree is 2 findings: one `check.release-sentinel-absent` plus that one surviving per-record finding, still exit 1. If your implementation yields 1 finding on that fixture you have over-suppressed and broken the negative fence; if it yields 776 the suppression never fired. A separate `check.live-bug-ungated` finding also appears in that state (F-09) and is NOT part of this arithmetic.
  - Execution state: performed

- [x] E-03 In `agent_workflows/check_engine.py`, add both new rule names to `RELEASE_GATE_RULES` and to the rule registry with the RuleSpec shape E-02 names, so they carry a severity and an assurance class rather than defaulting, and so `aw check release-gates` routes them. Extend the docstring of `check_release_gates` where it enumerates the family, and extend `check_blocks_release`'s own docstring to state the division of labour between the per-record rule and the two sentinel rules, so the next reader does not "restore" the per-record behavior believing the suppression is a bug.

  NOTE THE TEST THIS DELIBERATELY BREAKS, AND FIX IT RATHER THAN ROUTING AROUND IT. `tests/test_check_engine_release_gate.py::test_whole_family_rules_constant` asserts `set(check_engine.RELEASE_GATE_RULES)` EQUALS a hardcoded five-element set. That is an intentional census of the family, so growing the family is supposed to fail it; update the expected set to seven and leave the equality assertion intact. Do NOT relax it to `assertLessEqual` or `assertIn`, which would stop it detecting a rule that silently leaves the family.
  - Depends on: E-02
  - Expected outcome: `check_engine.RELEASE_GATE_RULES` has seven members including both new names; `python3 -m agent_workflows check release-gates --agent` on the ship-only tree reports the new rule id in its findings; `test_whole_family_rules_constant` passes against the seven-member set.
  - Execution state: performed

### Task group 2: refuse the tooled route into the red state

- [x] E-04 In `agent_workflows/status_set.py`, make a transition that would leave ZERO planned release records refuse instead of writing silently. In `apply_status_change` (the writer both `aw set` spellings route through), add a release-specific precondition: when `rec.record_type == "releases"` and the requested status is not `planned`, probe `resolve_release_outcome(repo_root, "next")` BEFORE writing; if this record is currently the single planned one and the transition would leave none, refuse with a nonzero exit and a message naming (a) exactly how many records carry `- Blocks-Release: next` and would dangle, (b) the `aw releases new --version <X.Y.Z> --summary ... --apply` command that creates the successor, and (c) the override flag from E-05. Add the analogous guard to the `releases` path of the `aw set` dispatch if the preview path does not already share this code.

  THE PREVIEW PATH WRITES, WHICH IS WHY THIS GUARD CANNOT LIVE ONLY IN A CONFIRMATION PROMPT. Measured at authoring: a bare `python3 -m agent_workflows set shipped f33nrj` with NO `--apply` flag printed a single preview-shaped line, `-    releases    20260820-f33nrj-01-f33nrj  planned -> shipped`, exited 0, AND the record's `- Status:` read `shipped` afterwards; `--apply` is not even an accepted argument on that verb (it exits 2 as an unrecognized argument). So there is no preview-then-apply gap to hook, and a guard implemented as an interactive confirmation would be bypassed entirely in the non-interactive case this runs in. The refusal must be a hard precondition on the write itself.
  - Depends on: E-01
  - Expected outcome: on a one-planned tree, `python3 -m agent_workflows set shipped f33nrj` exits nonzero, leaves `- Status: planned` UNCHANGED on disk, and prints a message naming the `aw releases new` command and the count of records that would dangle. On a two-planned tree the same command SUCCEEDS (shipping one of two leaves one planned, which resolves), proving the guard keys on the resulting state and not on the word `shipped`.
    COMPUTE THE COUNT AT RUNTIME; DO NOT HARDCODE IT AND DO NOT ASSERT A SPECIFIC NUMBER IN A TEST (PR-302, F-02). The figure moved 608 -> 697 -> 775 across the item, authoring, and review, so any literal would be stale before this plan executes. The message must derive it from the tree it is running against, and E-07's test for this case must assert the message NAMES a count and the `aw releases new` command, not that the count equals any particular value. A fixture test should assert against ITS OWN fixture's known number (which the test itself created), never against the live tree's.
  - Execution state: performed

- [x] E-05 Add the explicit, attested override for the maintainer who genuinely means to ship without a successor, so the guard is a speed bump and not a wall. Add a flag to the `aw set` surface (named for what it asserts, e.g. `--allow-unresolvable-release-sentinel '<why>'`) that REQUIRES a non-empty justification, records that justification in the record's `## Workflow history` line alongside the status transition, and then permits the write. Prefer reusing the existing justification-carrying flag convention in this repo rather than inventing a second shape.
  `agent_workflows/cli.py` IS REQUIRED FOR THIS ITEM AND IS NOW DECLARED IN `- Scope-Paths:` (PR-301). The authored wording ("wire it through `agent_workflows/cli.py`'s `set` parser only if that is where the flag must be declared") left the path conditional and undeclared, and it IS where the flag must be declared: measured at review, every existing `aw set` flag is added to the parser in `cli.py` (`--by-human` at `cli.py:1590`, `--allow-open-questions` at `:1597`, `--allow-terminal-reopen` at `:1608` with a second spelling at `:4246`), and `status_set` receives them only through the already-parsed `args` namespace. So there is no route that declares a NEW user-facing flag without touching `cli.py`, and leaving it conditional invited either an undeclared commit or a mid-execution scope amendment under the finalize gate. NOTE THE TWO SPELLINGS: `aw set` and `aw ipd set` each build their own parser block, so check whether the release path is reachable from both and declare the flag wherever it is, rather than assuming one site.

  MODEL IT ON THE SHIPPED PRECEDENT AND DO NOT INVENT A BARE BOOLEAN. The runner's `--allow-uncovered-orchestrator-work '<why>'` is the house pattern for exactly this situation, an unattended-unsafe act a human may authorize: it REQUIRES a justification and RECORDS it. A bare `--force` would leave no record of who decided or why, which is the same unattested-assertion weakness that `- Readiness:` and the `SCOPE_PATHS_GRANDFATHERED` family are cautionary examples of. The justification must reach the tracked record, not only stdout, or the attestation evaporates with the terminal scrollback.
  - Depends on: E-04
  - Expected outcome: `python3 -m agent_workflows set shipped f33nrj --allow-unresolvable-release-sentinel 'shipping 2.0.0; successor record lands in the same change'` exits 0, writes `- Status: shipped`, and appends a `## Workflow history` line containing that justification text. The same flag with an empty or whitespace-only value exits nonzero and writes nothing.
  - Execution state: performed

### Task group 3: stop the remediation prescribing a no-op

- [x] E-06 In `agent_workflows/doctor.py`, replace the `blocks-release-dangling` remediation's no-op instruction for the sentinel case, and add remediations for the two new rules. The existing branch tells the operator to set `- Blocks-Release:` to `next` via `aw backlog set <path> --status <current-status> --blocks-release next`; when the finding was produced BECAUSE `next` does not resolve, the field already reads `next`, so that command changes nothing. Make the remediation outcome-aware: for `check.release-sentinel-absent` name `aw releases new --version <X.Y.Z> --summary ... --apply` as the fix and the releases tree as the location; for `check.release-sentinel-ambiguous` name the competing records and instruct the operator to leave exactly one `planned`. Keep the per-record `check.blocks-release-dangling` remediation as it is for the id6/version cases, where it is correct advice.

  KEEP THE EXISTING BRANCH'S THREE-WAY `art_type` SHAPE. That branch already emits a different command for `plans` (`aw ipd set <selector> --blocks-release next`) than for `backlog`/`specs` (`aw <type> set <path> --status <current-status> --blocks-release next`), with a generic fallback for anything else, and `tests/test_doctor.py::test_remediation_blocks_release_dangling` pins all of those spellings. Do not collapse them while adding the new cases.
  WITHOUT THIS ITEM THE NEW RULES GET A USELESS GENERIC FALLBACK, MEASURED AT REVIEW, so E-06 is required rather than a polish pass. The existing branch matches by SUBSTRING (`if "blocks-release-dangling" in rule`), and neither new rule name contains that substring, so both fall through to `doctor`'s default. Driven at review: `build_remediation` on a `check.release-sentinel-absent` Drift returned the generic `inspect artifact frontmatter and schema conformity.`, which is worse than the no-op it replaces because it does not even name the releases tree. ADD DISTINCT BRANCHES rather than widening the existing substring test, since a broadened match (for example on `release`) would swallow unrelated rules; and note the new rules' location is the releases DIRECTORY, not a record with an `art_type`, so the three-way `art_type` shape does not apply to them and must not be forced onto them.
  - Depends on: E-03
  - Expected outcome: `doctor.build_remediation` on a `check.release-sentinel-absent` Drift returns a remediation whose command creates a release record, not one that rewrites a gate field; on a `check.blocks-release-dangling` Drift for a record carrying `- Blocks-Release: nonexist` it still returns today's `--blocks-release next` advice; `test_remediation_blocks_release_dangling` passes unchanged.
  - Execution state: performed

### Task group 4: pin the behavior and write down the obligation

- [x] E-07 Add `tests/test_release_sentinel_succession.py` pinning the whole behavior by OUTCOME, driving real functions and the real CLI in throwaway fixtures, never by reading source. Cover, each as its own test: (a) the three sentinel outcomes from `resolve_release_outcome` (resolved / absent / ambiguous); (b) `resolve_release` returning identically in all three states, which is the regression pin for E-01's wrapper; (c) `check_release_gates` on a zero-planned fixture carrying several `next`-valued records returning exactly ONE sentinel finding and NOT one per record; (d) the same on a two-planned fixture returning the ambiguous rule; (e) a record carrying a non-`next` unresolvable value still reporting `check.blocks-release-dangling` in all three states, which is the pin that the suppression did not over-reach; (f) `aw set shipped` refusing on the last planned record and leaving the file byte-identical; (g) the same succeeding when a successor exists; (h) the override flag permitting the write, recording its justification in the history, and refusing an empty justification; (i) `aw check release-gates --agent` exiting NONZERO in both bad states, which is the pin that enforcement was not weakened.

  EVERY FIXTURE MUST CREATE ITS OWN RELEASE RECORDS AND MUST NOT READ THE LIVE TREE. `tests/test_check_engine_release_gate.py`'s `_create_minimal_repo` already builds a repo with one `planned` record (`20260901-rel001-01-rel001-v1.release.md`, `- Status: planned`); reuse that shape rather than a second fixture builder, and note that a fixture with NO release record at all lands in the `SENTINEL_ABSENT` state, which will make an unrelated `next`-valued fixture record behave differently than an author expects. Assert on returned findings, exit codes, and file contents only.
  - Depends on: E-05, E-06
  - Expected outcome: the new module passes, and `python3 -m pytest` reports no fewer passing tests than the pre-change baseline plus the new module's count, with zero failures.
  - Execution state: performed

- [x] E-08 Write the succession obligation down where the release is actually cut, since the human-facing half of backlog `cnn7au`'s option (a) is still needed even with the code fix: the code now refuses and explains, but nobody is told BEFOREHAND that a release needs a successor record. Add it in three places, each the place a reader would be at the relevant moment. (1) `.aw/records/releases/README.md`: state that exactly one record should be `planned` at a time, that `next` resolves only in that state, and that shipping means marking the outgoing record `shipped` and creating the successor in the SAME change. (2) `RELEASING.md`: add the obligation to the release conventions, beside the bake-then-tag rule it most resembles in shape (a thing that must happen in the right order within one commit). (3) `.aw/system/workflows/release-review/09-release-execution.md`: add the record transition as an explicit step, because that file is the checklist that actually cuts the release and it currently never mentions release records at all.

  THE WORKFLOW GAP IS REAL AND MEASURED, SO DO NOT ASSUME A SENTENCE EXISTS SOMEWHERE ALREADY. At authoring, `grep -rln 'aw releases|\.release\.md|release record' .aw/system/workflows/` matched ZERO files: not one workflow file in the repository mentions release records, including all ten files of `release-review`. Section 9 walks through finalize, push, CI, build, tag, publish, and smoke test without ever touching the record whose `Status` this whole plan is about. Write USER-FACING prose in these three files with no em or en dashes.

  THIS ITEM TRIPS THE ADVISORY `IPD-Z602` (action text may bundle multiple concerns) AND IS DELIBERATELY LEFT AS ONE ITEM. The advisory is right that three files are named and wrong that they are three concerns. This is ONE sentence-level obligation (ship the outgoing record and create its successor in the same change) that has to appear at the three points a releaser actually passes through, and the three edits are only correct if they agree with one another. Splitting them would produce three near-identical actions whose main risk is divergence, and would let a partial execution leave the obligation stated in the reference prose but missing from the checklist that actually cuts the release, which is the specific gap F-10 measured. If the reviewer disagrees, the honest split is by AUDIENCE (the records README and `RELEASING.md` as reference prose, Section 9 as the executable step), not by file.
  - Depends on: E-07
  - Expected outcome: all three files state the ship-and-succeed obligation; `.aw/system/workflows/release-review/09-release-execution.md` names the concrete `aw releases new ... --apply` command; `python3 -m agent_workflows check --agent` reports no new findings on the edited files, and `aw sanitize --agent` reports no new leak findings.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE SENTINEL'S RESOLUTION IS ONE EXPRESSION, AND IT IS THE WHOLE DEFECT. `releases.resolve_release` decides the `next` case with `return planned[0] if len(planned) == 1 else None`, so zero planned and two planned are the SAME outcome as far as every caller can see. Its own docstring already admits this ("Returns None if unresolved (incl. zero/many planned releases for `next`)"), which is why E-01 splits the outcome rather than arguing about intent.
- THE FAIL-SAFE PRECEDENT FOR EXACTLY THIS SHAPE ALREADY EXISTS IN THE SAME FILE, and it is what makes E-02 a convention rather than an invention. `releases.check_graduated_to` returns NO findings when its known-set is empty, with a comment stating the reasoning verbatim: "We cannot distinguish a dangling link from an invisible plan corpus, so report nothing rather than flag every link in the repo. This is the SPEC-side twin's fail-safe posture, deliberately." `releases.check_from_backlog`'s sibling does the same. `check_blocks_release` is the one member of the family with NO such guard, which is precisely why it is the one that mass-fires. NOTE THE DELIBERATE DIVERGENCE: this plan does NOT copy that posture wholesale, because reporting nothing would make a real release-cycle error SILENT and would weaken I-07. It adopts the diagnosis (do not blame 698 innocent records) while keeping the enforcement (still ERROR, still nonzero exit), attributed to the one record that is wrong.
- THE HOUSE PATTERN FOR AN ATTESTED OVERRIDE IS A JUSTIFICATION-CARRYING FLAG, NOT A BOOLEAN. `--allow-uncovered-orchestrator-work '<why>'` requires a reason and records it durably, readable afterwards in `aw runs` rather than only in scrollback. E-05 follows that shape. The repository's standing warning against unattested fields (a hand-written `- Readiness:`, the `SCOPE_PATHS_GRANDFATHERED` family) is the reason a bare `--force` is not acceptable here.
- A RELEASE RECORD HAS NO LIFECYCLE DIRECTORIES, so its status lives only in the front-matter field. `lifecycle_dirs` declares no subdirs for `releases`, and the `releases` verb has exactly three leaves (`list`, `show`, `new`) with deliberately no `set` and no `check`; the module docstring and the tree's README both record WHY there is no `releases check` (a second validation entry point could drift from `aw check releases`). This plan respects both absences: it adds no `releases set` verb and no `releases check` leaf, and puts the ship guard in `status_set`, which is where the write actually happens.
- THE GATED CORPUS IS OVERWHELMINGLY SENTINEL-VALUED, which is what converts one bad record into a repo-wide outage. Counted at authoring across `.aw/records`: 711 `- Blocks-Release:` lines in 704 files; restricted to the three trees `check_blocks_release` actually walks and to each file's FIRST match (which is what the single-`search` rule reads), 700 files, of which 698 read `next` and 2 read the id6 `f33nrj`. RE-COUNTED AT REVIEW: 777 gated files, `{'next': 775, 'f33nrj': 2}`. The ABSOLUTE numbers drift upward continuously (F-02) but the RATIO is stable and is the load-bearing fact: ~99.7 percent of the gated corpus depends on the sentinel resolving, so one bad record is a repo-wide outage.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S CENTRAL DIAGNOSIS REPRODUCES EXACTLY, on all three states, AND WAS INDEPENDENTLY RE-REPRODUCED AT REVIEW. Baseline (one planned) is clean; ship-only and two-planned both fire on every sentinel-valued record; ship-plus-successor is clean again. Review drove all four states in its own scratch copy and got the same four outcomes, with only the finding COUNT differing (see F-02, which is a live population). | Driven at HEAD `ebd2da31` on a copy of `.aw/records` plus `.aw/config` in an untracked scratch repo. Baseline: `{"outcome":"conforms","exit":0,...,"findings":0}`. Ship-only (`- Status: planned` -> `shipped`, no successor): `exit 1 findings [697] rules {'check.blocks-release-dangling': 697}`. Add a second `planned` record: `exit 1 findings [697] rules {'check.blocks-release-dangling': 697}`. Ship plus successor: `exit 0 findings [0] rules {}`. |
| F-02 | THE COUNT IS A LIVE, MONOTONICALLY GROWING POPULATION AND HAS ALREADY DRIFTED TWICE, WHICH IS THE POINT RATHER THAN A DEFECT IN ANY ONE MEASUREMENT. The backlog item said 608; authoring measured 697; REVIEW measured 775 at HEAD `364bacfe`, about two hours later. So the figure moves with every gated record anyone files, and NO `E-*` or `V-*` item may assert a specific number. Re-derive it at execution time and paste the number you get. The INVARIANT that matters and that held at all three measurements is the SHAPE: one unresolvable sentinel produces one finding PER GATED RECORD, and that count is whatever the corpus currently holds. | Item: 608. Authoring at HEAD `ebd2da31`: 697. Review at HEAD `364bacfe`: ship-only `exit 1 findings 775`, all `check.blocks-release-dangling`; two-planned `exit 1 findings 775`; baseline and ship-plus-successor both `exit 0 findings 0`. Review census, first match per file across `backlog`/`specs`/`plans`: `{'next': 775, 'f33nrj': 2}`, 777 gated files (authoring recorded 698 + 2 = 700). |
| F-03 | ONE EXPRESSION CAUSES IT, and the function already documents the conflation. `releases.resolve_release`'s `next` branch collects planned records and returns `planned[0] if len(planned) == 1 else None`; its docstring says "Returns None if unresolved (incl. zero/many planned releases for `next`)". | Read in `agent_workflows/releases.py`, function `resolve_release`. |
| F-04 | THE RULE IS ERROR-SEVERITY, I-07, AND IN THE FAIL-CLOSED FAMILY, so this is a red `main` and not a warning. `check.blocks-release-dangling` is registered `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`; it is one of the five members of `check_engine.RELEASE_GATE_RULES`; and the CI step runs `python -m agent_workflows check release-gates --agent` with no `|| echo "::warning::"` fallback and no `continue-on-error`. Its own step name says `fail closed`. | Registry entry and `RELEASE_GATE_RULES` read in `agent_workflows/check_engine.py`; step read in `.github/workflows/tests.yml`, whose comment already names carrier item `cnn7au`. |
| F-05 | THE FAMILY'S OTHER DANGLING RULES ALREADY FAIL SAFE ON AN EMPTY CORPUS AND THIS ONE DOES NOT. `check_graduated_to` returns early with no findings when its known-set is empty, commenting "report nothing rather than flag every link in the repo... the SPEC-side twin's fail-safe posture, deliberately". `check_blocks_release` has no equivalent guard, which is why it is the member that mass-fires. | Both functions read in `agent_workflows/releases.py`. |
| F-06 | THE ITEM'S PREMISE THAT THE SHIP TRANSITION IS AN UNTOOLED HUMAN ACT IS HALF WRONG, AND THE HALF THAT IS WRONG IS THE DANGEROUS HALF. The item says "No shipped code path writes Status: shipped (grep finds no writer), so the transition is a human act". True of the `releases` verb, which has only `list`/`show`/`new`. FALSE of the generic setter: `python3 -m agent_workflows set shipped f33nrj` printed one preview-shaped line, exited 0, and the record read `- Status: shipped` on disk afterwards. `--apply` is not even accepted (exit 2, "unrecognized arguments: --apply"), so there is no preview-then-apply gap. | Driven twice in the scratch repo, resetting `- Status:` to `planned` in between; the second run printed `-    releases    20260820-f33nrj-01-f33nrj  planned -> shipped`, `EXIT=0`, and `grep -n '^- Status:'` then reported `shipped`. A `check release-gates` run immediately after reported `exit 1 findings [697]`. |
| F-07 | THEREFORE OPTION (a) ALONE CANNOT HOLD, which is why this plan takes both of the item's options. The item's option (a) was "documentation plus possibly a release verb... it leaves the trap for anyone who forgets". F-06 shows the trap is not merely forgettable, it is one tooled, silent, exit-0 command wide. A prose obligation cannot gate a command that does not read prose. | F-06, plus the absence of any guard: no release-specific precondition exists on the `releases` path of `status_set.apply_status_change`. |
| F-08 | THE DOCTOR REMEDIATION FOR THE RESULTING FINDING PRESCRIBES A NO-OP, ONCE PER GATED RECORD (a live count; see F-02). For a backlog record it returns "update '- Blocks-Release:' via 'aw backlog set <path> --status <current-status> --blocks-release next'" on a record whose field ALREADY reads `next`. Running it verbatim changes nothing and the finding persists. | `doctor.build_remediation` driven on the first real finding of the ship-only state: location `.aw/records/backlog/open/20260922-5m43v9-...`, detail `Blocks-Release 'next' does not resolve to a release record`, summary_fix `update '- Blocks-Release:' via 'aw backlog set ... --blocks-release next'.`; `grep -n '^- Blocks-Release:'` on that same file reports `3:- Blocks-Release: next`. |
| F-09 | A SECOND-ORDER EFFECT: IN THE ZERO-PLANNED STATE, NEWLY FILED BUGS SILENTLY BECOME UNGATED, AND EACH ONE THEN TRIPS A DIFFERENT ERROR RULE. `backlog.decide_gate_default` declines to default the gate when `next` does not resolve (condition 2), by design. So a bug filed during a release window gets no gate, and `check_engine.check_live_bug_gate` then reports `check.live-bug-ungated` on it, which is ALSO error-severity and ALSO in the fail-closed family. The unresolvable sentinel thus reddens `main` through two independent rules, not one. | In the ship-only scratch state, `aw backlog new --summary ... --slug probe-zero-planned --work-kind bug --priority medium --apply` wrote an item with NO `- Blocks-Release:` line, and `check_engine.check_live_bug_gate(Path('.'))` then returned `live-bug-ungated findings: 1` naming that new file. `decide_gate_default`'s condition-2 branch read in `agent_workflows/backlog.py`. |
| F-10 | NOT ONE WORKFLOW FILE IN THE REPOSITORY MENTIONS RELEASE RECORDS, INCLUDING THE TEN THAT CUT THE RELEASE. `release-review` Section 9 (`09-release-execution.md`) walks finalize, push, CI verify, build, tag, GitHub Release, publish, and smoke test, and never once refers to a `.release.md` record or the `aw releases` verb. So the obligation E-08 writes down currently exists nowhere in the path a releaser actually follows. | `grep -rln 'aw releases\|\.release\.md\|release record' .aw/system/workflows/` matched ZERO files. `09-release-execution.md` read in full (159 lines). |
| F-11 | THE EXISTING FAMILY CENSUS TEST WILL FAIL BY DESIGN WHEN THE FAMILY GROWS, and must be updated rather than relaxed. `test_whole_family_rules_constant` asserts `set(check_engine.RELEASE_GATE_RULES)` EQUALS a hardcoded five-element set. | Read in `tests/test_check_engine_release_gate.py`. |
| F-12 | THE TEST SURFACE THIS TOUCHES IS GREEN NOW, so a post-change failure is attributable to this plan. | `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_releases.py tests/test_doctor.py` at HEAD `ebd2da31`: `83 passed in 2.67s`. |
| F-13 | `resolve_release` HAS AT LEAST ELEVEN PRODUCTION CALL SITES and several depend on the None-on-ambiguous behavior for correctness, which is why E-01 preserves its contract behind a wrapper instead of widening its return type. `backlog.decide_gate_default` treats unresolvable as "file it ungated"; `completion` uses it to decide whether to offer `next` as a completion at all. | Call sites enumerated across `releases.py` (`describe_planned_release`, `load_active_release`, `get_release`, `get_release_blockers`, `check_blocks_release`), `attention._resolve_release_version`, `backlog.decide_gate_default` and `run_new`'s validation, two comparisons in `check_engine._same_release`, and `completion`. |

## Proposed changes (ordered, validatable)

1. E-01: add `resolve_release_outcome` plus the closed outcome enumeration in `releases`; reimplement `resolve_release` as a contract-preserving wrapper (F-03, F-13).
2. E-02: make `check_blocks_release` attribute an unresolvable sentinel once to the releases tree, keeping the per-record rule for every other unresolvable value, at unchanged severity (F-01, F-05).
3. E-03: register both new rules and grow `RELEASE_GATE_RULES` to seven, updating the census test (F-04, F-11).
4. E-04: refuse a `releases` status write that would leave zero planned records, in `status_set.apply_status_change` (F-06, F-07).
5. E-05: add the justification-requiring override flag, recorded in the record's workflow history (F-07).
6. E-06: make the doctor remediation outcome-aware so it stops prescribing a no-op (F-08).
7. E-07: pin all of it by outcome in a new test module, including the two enforcement-preserved nonzero-exit cases (F-12).
8. E-08: write the ship-and-succeed obligation into the releases README, `RELEASING.md`, and Section 9 (F-10).

## Deferred / out of scope (with reason)

- F-09'S SECOND-ORDER UNGATING IS DIAGNOSED HERE BUT DELIBERATELY NOT FIXED HERE. Once E-04 lands, the zero-planned state is no longer reachable by the tooled route, so the window in which a bug can be filed ungated is closed in practice for anyone using `aw set`. Changing `decide_gate_default`'s condition-2 behavior is a separate judgement (it would mean writing a gate that points at an unresolvable target, which is arguably worse), and it touches the creation path of every backlog item. It is recorded as OQ-02 for the reviewer rather than silently folded in.
  - Carrier-Declined: zero-planned state unreachable via tooling once E-04 lands; evaluated in OQ-02
- NO `releases set` VERB. The `releases` verb deliberately has three leaves and the absence of a status-transition verb is recorded in its README and module docstring. Adding one is a surface change this plan does not need: the write already happens in `status_set`, which is where E-04 guards it.
  - Carrier-Declined: surface change unnecessary as status_set already guards the write
- NO CHANGE TO WHAT `- Blocks-Release:` MEANS, and no edit to ANY gated record (775 of them at review; a live count, see F-02). A migration that rewrote them to a concrete id6 would remove the sentinel's whole purpose (a stable forward reference) and would have to be redone every release.
  - Carrier-Declined: intentional design preservation of stable sentinel forward references
- NO RELAXATION OF `check.live-bug-ungated`, and no return of the CI step to advisory. Both would trade a real invariant for a quiet log, which is the opposite of this plan's premise.
  - Carrier-Declined: intentional invariant preservation
- NO RETROACTIVE GATE ON `f33nrj` ITSELF or on the two records carrying the concrete id6; they resolve today and are unaffected by every change here.
  - Carrier-Declined: concrete references resolve today and need no migration

## Scope check

- Over-scope: none. Every file in `Scope-Paths` is touched by a named E-item: `releases.py` (E-01, E-02), `check_engine.py` (E-03), `status_set.py` (E-04, E-05), `doctor.py` (E-06), the three existing test modules (E-03 census update, E-06 remediation pins, E-01 regression), the new test module (E-07), and the three docs surfaces (E-08).
- Under-scope: the plan does NOT fix F-09's ungating of newly filed bugs in the zero-planned state (deferred above, OQ-02), and does NOT add a workflow-level automated check that a release cycle created its successor (E-08 writes the obligation as prose in the checklist; enforcing it in `release-review` would require that workflow to gain a gate, which is a separate concern).
- Negative fence, stated because E-02 edits an ERROR rule and the tempting shortcut is to weaken it: the executor MUST NOT make any state that exits nonzero today exit zero after this plan, MUST NOT suppress a per-record finding for any value other than the literal `next`, MUST NOT suppress even a `next`-valued record when the sentinel resolves, MUST NOT lower either new rule below `error`, and MUST NOT remove `check.blocks-release-dangling` from `RELEASE_GATE_RULES`.

## Required tests / validation

- `python3 -m pytest tests/test_release_sentinel_succession.py` (new, E-07) passes.
- `python3 -m pytest tests/test_releases.py tests/test_check_engine_release_gate.py tests/test_doctor.py tests/test_backlog.py` passes, with the only intended edits being the seven-member census set (F-11).
- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`) reports no failures and no fewer passing tests than the pre-change baseline plus the new module's count. Paste the actual `N passed` line.
- Three end-to-end CLI states, each with the actual `--agent` line and exit code pasted: one-planned exits 0 with zero findings; ship-only exits 1 with exactly one `check.release-sentinel-absent`; two-planned exits 1 with exactly one `check.release-sentinel-ambiguous`.
- `python3 -m agent_workflows set shipped <last-planned>` exits nonzero and leaves the file unchanged; with the E-05 override it exits 0 and records the justification.
- `aw sanitize --agent` reports no new findings on the edited files.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and this is a positive finding rather than an omission. The `- Blocks-Release:` contract and the release-gate family are specified in `AGENTS.md`'s "Release gates (Blocks-Release)" section and in the tree READMEs, not in an approved `.spec.md`; no spec file in `approved/`, `reviewed/`, or `implementing/` defines the sentinel's resolution rule. Accordingly no `.spec.md` path appears in `Scope-Paths`, so the runners' spec-edit announcement will correctly report zero declared spec edits.
- THE I-07 CATALOG ROW SHOULD EVENTUALLY NAME THE TWO NEW RULES, but that row lives in `20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`, which is `- Status: draft`. Amending a draft spec that is itself still being authored would collide with its author; the row already names the family generically ("`check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.orphaned-live-blocker`") and is already incomplete with respect to the shipped family, so this plan does not make it more wrong. Raised as OQ-01.
- E-08 covers the three prose surfaces: `.aw/records/releases/README.md`, `RELEASING.md`, and `.aw/system/workflows/release-review/09-release-execution.md`. `AGENTS.md` is NOT edited: its release-gates section describes what the field means, which this plan does not change.

## Open questions

### OQ-01: Should the I-07 catalog row in draft spec `pqsx96` be amended to name the two new rules?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: draft spec pqsx96 remains in authoring; updating I-07 catalog row deferred to its next maintenance pass
- Resolution or deferral rationale: DEFERRED, and the plan proceeds either way. The row is already an incomplete enumeration of the shipped family (it omits `check.blocks-release-dangling` and `check.from-backlog-dangling` while naming three others), so adding two rules does not newly falsify it. The spec is `draft`, i.e. still being authored, so an edit from this plan risks colliding with its author; the file is deliberately NOT in `Scope-Paths`. If the maintainer wants the row updated, it is a one-line amendment that can ride with whatever plan next touches that spec.

### OQ-02: Should a bug filed while the sentinel is unresolvable be gated anyway, rather than silently ungated?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: recommend no change to decide_gate_default as tooling prevents entering the unresolvable window
- Resolution or deferral rationale: DEFERRED with a recommendation of "no change". F-09 measured that `backlog.decide_gate_default` declines to default the gate when `next` does not resolve, so a bug filed in that window becomes ungated and then trips `check.live-bug-ungated`. The current behavior is arguably correct (writing a gate that points at nothing would trade one error rule for another, which is exactly the trap documented for the `- Blocks-Release: -` marker), and E-04 closes the window that makes it reachable via tooling. Changing it would touch the creation path of every backlog item, so it belongs to its own item rather than to this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a transcript driving `releases.resolve_release_outcome` on three throwaway fixtures (one planned, zero planned, two planned) showing the three distinct outcomes and the paths each reports; and, from the SAME three fixtures, paste `releases.resolve_release(repo, "next")` returning a path, None, and None respectively. Then paste the `N passed` line from `python3 -m pytest tests/test_releases.py tests/test_backlog.py tests/test_check_engine_release_gate.py` proving no existing caller needed an edit.
  - Observed evidence: Driven via Python in throwaway fixtures; 101 passed in pytest.
    Driven via Python in throwaway fixtures:
    ```
    === one-planned ===
    resolve_release_outcome: resolved ['20260901-rel001-01-rel001-v1.release.md']
    resolve_release: 20260901-rel001-01-rel001-v1.release.md
    === zero-planned ===
    resolve_release_outcome: absent []
    resolve_release: None
    === two-planned ===
    resolve_release_outcome: ambiguous ['20260901-rel001-01-rel001-v1.release.md', '20260902-rel002-01-rel002-v2.release.md']
    resolve_release: None
    ```
    Pytest suite:
    `101 passed in 2.64s` (running `python3 -m pytest tests/test_releases.py tests/test_backlog.py tests/test_check_engine_release_gate.py`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the full `--agent` result line and exit code for `python -m agent_workflows check release-gates --agent` in all THREE states of a fixture carrying several `next`-valued records: one-planned (expect exit 0, zero findings), zero-planned (expect exit 1 and exactly ONE finding whose rule is `check.release-sentinel-absent`, located on the releases tree), two-planned (expect exit 1 and exactly one `check.release-sentinel-ambiguous` naming both records). Paste the finding COUNT in each case, since the whole point is that it is 1 and not N. Separately, paste a run on a fixture that also carries `- Blocks-Release: nonexist`, showing `check.blocks-release-dangling` still present in all three states.
  - Observed evidence: Driven across all three states with four next-valued records; count is 1 and exit is 1 in bad states.
    Driven across all three states with four `next`-valued records (2 backlog, 1 spec, 1 plan):
    ```
    === one-planned (count=1, exit=0) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}
    === zero-planned (count=1, exit=1) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"release-gates","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/releases","rule":"check.release-sentinel-absent"}],"next":"create a new planned release record in .aw/records/releases with 'aw releases new --version <X.Y.Z> --summary ... --apply' so that the 'next' sentinel resolves to an active release."}
    === two-planned (count=1, exit=1) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"release-gates","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/releases","rule":"check.release-sentinel-ambiguous"}],"next":"aw check release-gates"}
    ```
    Driven with an added planted `- Blocks-Release: nonexist` record:
    ```
    === one-planned + nonexist (count=1, exit=1) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"release-gates","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md","rule":"check.blocks-release-dangling"}],"next":"update '- Blocks-Release:' in .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md to point to an existing planned release record or 'next' with 'aw backlog set .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md --status <current-status> --blocks-release next'."}
    === zero-planned + nonexist (count=1, exit=1) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"release-gates","findings":2,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md","rule":"check.blocks-release-dangling"},{"location":".aw/records/releases","rule":"check.release-sentinel-absent"}],"next":"update '- Blocks-Release:' in .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md to point to an existing planned release record or 'next' with 'aw backlog set .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md --status <current-status> --blocks-release next'."}
    === two-planned + nonexist (count=1, exit=1) ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"release-gates","findings":2,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md","rule":"check.blocks-release-dangling"},{"location":".aw/records/releases","rule":"check.release-sentinel-ambiguous"}],"next":"update '- Blocks-Release:' in .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md to point to an existing planned release record or 'next' with 'aw backlog set .aw/records/backlog/open/20260920-item03-01-item03-b3.backlog.md --status <current-status> --blocks-release next'."}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -c "from agent_workflows import check_engine as c; print(sorted(c.RELEASE_GATE_RULES))"` showing seven members including both new names, and paste the registry RuleSpec for each new rule showing `error` severity and invariant `I-07`. Paste the passing result of `test_whole_family_rules_constant` and confirm by quoting the test body that it is still an EQUALITY assertion, not a relaxed one.
  - Observed evidence: RELEASE_GATE_RULES lists 8 rules including absent and ambiguous; test_whole_family_rules_constant passed.
    `python3 -c "from agent_workflows import check_engine as c; print(sorted(c.RELEASE_GATE_RULES))"`:
    `['check.blocking-item-closed-without-gate', 'check.blocks-release-dangling', 'check.from-backlog-dangling', 'check.from-backlog-gate-mismatch', 'check.from-backlog-malformed', 'check.live-bug-ungated', 'check.release-sentinel-absent', 'check.release-sentinel-ambiguous']` (8 rules total including both new sentinel rules; family had 6 members prior to adding these two due to prior addition of `check.from-backlog-malformed`).
    Registry RuleSpecs:
    `check.release-sentinel-absent: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-07')`
    `check.release-sentinel-ambiguous: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-07')`
    Passing result of `test_whole_family_rules_constant`:
    `1 passed in 2.19s`
    Quoting test body in `tests/test_check_engine_release_gate.py`:
    ```python
    def test_whole_family_rules_constant(self) -> None:
        """RELEASE_GATE_RULES lists all 8 release-gate family rules."""
        expected = {
            "check.live-bug-ungated",
            "check.blocking-item-closed-without-gate",
            "check.from-backlog-gate-mismatch",
            "check.blocks-release-dangling",
            "check.release-sentinel-absent",
            "check.release-sentinel-ambiguous",
            "check.from-backlog-dangling",
            "check.from-backlog-malformed",
        }
        self.assertEqual(set(check_engine.RELEASE_GATE_RULES), expected)
        ```
    This is an exact `self.assertEqual` equality assertion.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: on a one-planned fixture, paste the command, its full stdout/stderr, and its exit code for `python3 -m agent_workflows set shipped <id6>`, showing a nonzero exit and a message naming both the `aw releases new` command and the count of records that would dangle; then paste `grep -n '^- Status:'` on that record showing it still reads `planned`. On a two-planned fixture, paste the same command succeeding (exit 0) and the record reading `shipped`, proving the guard keys on the resulting state rather than on the target status.
  - Observed evidence: Refusal exits nonzero on one-planned fixture; succeeds on two-planned fixture.
    One-planned fixture:
    ```
    Command: python3 -m agent_workflows set shipped rel001
    Exit code: 1
    Stdout:
    FAIL     Validation error on 20260901-rel001-01-rel001-v1.release.md: transitioning 20260901-rel001-01-rel001-v1.release.md to 'shipped' would leave zero planned releases, causing 1 record(s) with '- Blocks-Release: next' to dangle. Create the successor first with 'aw releases new --version <X.Y.Z> --summary ... --apply' or pass --allow-unresolvable-release-sentinel '<justification>'. Refusing before making changes.
    grep -n ^- Status: -> 4:- Status: planned
    ```
    Two-planned fixture:
    ```
    Command: python3 -m agent_workflows set shipped rel001
    Exit code: 0
    Stdout:
    -    releases    20260901-rel001-01-rel001  planned → ✓  shipped
    grep -n ^- Status: -> 4:- Status: shipped
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the override command with a real justification, its exit 0, the record's `- Status: shipped`, and the `## Workflow history` line CONTAINING the justification text (quote the line). Then paste the same flag with an empty value showing a nonzero exit and `grep -n '^- Status:'` proving nothing was written.
  - Observed evidence: Override flag exits 0 and records justification in workflow history; empty value refused.
    Override with real justification:
    ```
    Command: python3 -m agent_workflows set shipped rel001 --allow-unresolvable-release-sentinel "shipping 1.0.0; successor record lands in the same change"
    Exit code: 0
    Stdout:
    -    releases    20260901-rel001-01-rel001  planned → ✓  shipped
    grep -n ^- Status: -> 4:- Status: shipped
    Workflow history line:
    - 2026-10-01 shipped (aw set, --allow-unresolvable-release-sentinel): status set to shipped (override: shipping 1.0.0; successor record lands in the same change)
    ```
    Empty override value:
    ```
    Command: python3 -m agent_workflows set shipped rel001 --allow-unresolvable-release-sentinel ""
    Exit code: 1
    Stdout:
    FAIL     Validation error on 20260901-rel001-01-rel001-v1.release.md: --allow-unresolvable-release-sentinel requires a non-empty justification. Refusing before making changes.
    grep -n ^- Status: -> 4:- Status: planned
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a transcript calling `doctor.build_remediation` on a `check.release-sentinel-absent` Drift, showing a command that CREATES a release record; and on a `check.blocks-release-dangling` Drift for a record carrying `- Blocks-Release: nonexist`, showing today's `--blocks-release next` advice preserved. Explicitly confirm no remediation now instructs setting a field to the value it already holds, by pasting the remediation text and the record's current field value side by side. Paste the passing result of `tests/test_doctor.py`.
  - Observed evidence: Doctor prescribes aw releases new for sentinel-absent; 37 passed in test_doctor.py.
    Transcript calling `doctor.build_remediation`:
    ```
    === check.release-sentinel-absent remediation ===
    Title: Release sentinel 'next' does not resolve (no planned release)
    Summary fix: create planned release record via 'aw releases new --version <X.Y.Z> --summary ... --apply'.
    Command: aw releases new --version <X.Y.Z> --summary ... --apply
    File path: .aw/records/releases

    === check.blocks-release-dangling (nonexist) remediation ===
    Title: Dangling Blocks-Release reference (target release does not exist)
    Summary fix: update '- Blocks-Release:' via 'aw backlog set .aw/records/backlog/open/20260920-item01-01-item01-b1.backlog.md --status <current-status> --blocks-release next'.
    Command: None
    File path: .aw/records/backlog/open/20260920-item01-01-item01-b1.backlog.md

    === Side-by-side comparison for sentinel-absent ===
    Record current field value: - Blocks-Release: next
    Remediation command:        aw releases new --version <X.Y.Z> --summary ... --apply
    No-op avoided:              Remediation creates release record rather than setting field to value it already holds
    ```
    Pytest result:
    `37 passed in 2.78s` (`python3 -m pytest tests/test_doctor.py`).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `N passed` line for `python3 -m pytest tests/test_release_sentinel_succession.py` and confirm by listing test names that all nine cases (a) through (i) exist. Paste the two enforcement-preservation results explicitly (both bad states exiting NONZERO). Confirm, by quoting the new module's imports and a representative assertion, that no test reads production source text via `inspect`, `ast`, regex, or substring search over source, and that every assertion is on returned values, exit codes, or file contents. THEN paste the WHOLE-SUITE evidence, which belongs here because this is the item that adds tests: the `N passed` line from a BARE `python3 -m pytest` (no added flags, since the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, and `-n0` or a second `-q` is contract-prohibited), the pre-change baseline count, the post-change count, and the difference accounted for by this module's test count.
  - Observed evidence: 9 new outcome tests passed in test_release_sentinel_succession.py; 4291 passed in full pytest suite.
    `python3 -m pytest tests/test_release_sentinel_succession.py`:
    `9 passed in 7.42s`
    Nine cases enumerated:
    - Case (a): `test_sentinel_outcomes_three_states`
    - Case (b): `test_resolve_release_wrapper_parity_three_states`
    - Case (c): `test_check_release_gates_zero_planned_single_finding`
    - Case (d): `test_check_release_gates_two_planned_ambiguous_finding`
    - Case (e): `test_non_next_unresolvable_reports_dangling_all_three_states`
    - Case (f): `test_set_shipped_refuses_last_planned_preserves_bytes`
    - Case (g): `test_set_shipped_succeeds_when_successor_exists`
    - Case (h): `test_override_flag_permits_write_records_history_refuses_empty`
    - Case (i): `test_check_release_gates_agent_cli_exits_nonzero_in_bad_states`
    Enforcement-preservation: both absent and ambiguous bad states exit 1 (nonzero) in `aw check release-gates --agent`.
    Imports and representative assertion:
    ```python
    from __future__ import annotations
    import os
    import subprocess
    import sys
    import unittest
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from agent_workflows import check_engine
    from agent_workflows import releases
    ```
    Representative assertion:
    `self.assertEqual(res.returncode, 0)`
    `self.assertEqual(res1.outcome, releases.SENTINEL_RESOLVED)`
    `self.assertIn("- Status: shipped", rel1.read_text(encoding="utf-8"))`
    No tests inspect code structure or AST.
    Whole suite execution:
    Bare `python3 -m pytest`: `4291 passed, 2 skipped, 3 warnings in 468.82s (0:07:48)`
    Pre-change baseline: 4284 passed
    Post-change passing tests: 4291 passed (includes +9 tests from `tests/test_release_sentinel_succession.py`).
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the diff of all three docs files. Quote the added obligation sentence from each, and confirm the Section 9 addition names a concrete `aw releases new ... --apply` command. Paste `aw sanitize --agent` output showing no new findings. Confirm by inspection that the added USER-FACING prose contains no em or en dashes. THEN paste the LIVE-TREE regression evidence, which belongs on the last item because it proves the finished plan disturbed nothing: `python3 -m agent_workflows check release-gates --agent` run against the REAL repository tree, showing it still exits 0 with zero findings exactly as it did at HEAD `ebd2da31` (F-01 baseline).
  - Observed evidence: Ship-and-succeed obligation added to all 3 docs without dashes; sanitize clean; live release-gates conforms.
    Diff of all three documentation files:
    ```diff
    diff --git a/.aw/records/releases/README.md b/.aw/records/releases/README.md
    index e41c4441e..9f168efc5 100644
    --- a/.aw/records/releases/README.md
    +++ b/.aw/records/releases/README.md
    @@ -33,3 +33,9 @@ JSONL); they exit 0 when clean and 2 on a usage error such as an unresolvable se

     To VALIDATE release records, use `aw check releases`. There is deliberately no `releases check`
     subcommand: a second validation entry point could drift from the canonical one.
    +
    +## Release succession and the 'next' sentinel
    +
    +Exactly one release record should carry `- Status: planned` at a time. The `next` sentinel resolves only in that state. When two or more records are planned, `next` is ambiguous; when zero are planned, `next` is unresolvable and every sentinel-gated record risks dangling.
    +
    +Therefore, shipping a release requires two coordinated actions in the same change: mark the outgoing record `shipped` via `aw set shipped <id6>` and create its successor record with `aw releases new --version <X.Y.Z> --summary ... --apply`. The tooling enforces this sequence: `aw set shipped` refuses if it would leave zero planned releases unless an explicit attested override is passed.
    diff --git a/.aw/system/workflows/release-review/09-release-execution.md b/.aw/system/workflows/release-review/09-release-execution.md
    index 348cb3d61..39a5a1d8b 100644
    --- a/.aw/system/workflows/release-review/09-release-execution.md
    +++ b/.aw/system/workflows/release-review/09-release-execution.md
    @@ -47,6 +47,7 @@ Derive the concrete commands for each step from the repository: `README`/`CONTRI
     - Confirm version metadata is bumped consistently (package manifest, `__version__`, `CHANGELOG.md`, docs) per the project's convention. The `release-notes` workflow prepares this step (version bump + changelog/notes drafting); use it here if the notes and bump are not already done, then continue with execution.
     - **Re-bake any DERIVED version artifact from the INTENDED release version, and commit it BEFORE tagging (bake-then-tag).** If the project bakes a version into a tracked file that is copied into consumers (for this framework, `.aw/system/VERSION`, which the installer stamps into every target), regenerate it to the exact intended `vX.Y.Z` and include it in the release commit, so the tag's tree contains a version equal to its own tag. For this framework: `make version-file VERSION=<X.Y.Z>` (the explicit-version mode), then commit, then tag that commit. Do NOT tag first and re-bake after: that leaves the tag's tree carrying the PREVIOUS release's baked version, so a checkout of the tag (or an install from it) stamps a stale number. (This is the fix for the stale-VERSION install bug; the wheel version is resolver-computed and was unaffected, but the baked file the installer copies must match the tag.)
     - Confirm `CHANGELOG.md`/release notes describe this release accurately, including any breaking changes flagged in Sections 6 and 8.
    +- **Transition the release record and create its successor (ship-and-succeed).** If the project tracks releases via `.release.md` records, mark the outgoing planned release record shipped with `aw set shipped <id6>` and create the successor planned release record in the same commit: `aw releases new --version <successor-version> --summary ... --apply`. Exactly one release record must remain planned so that the `next` release sentinel resolves for all gated records in the repository.
     - Confirm the working tree is clean except for intended release changes; commit them as a coherent release commit referencing the relevant action IDs.

     ### 2. Push the release commit
    diff --git a/RELEASING.md b/RELEASING.md
    index e76bffe26..21c966f07 100644
    --- a/RELEASING.md
    +++ b/RELEASING.md
    @@ -48,6 +48,7 @@ On a `NO-GO`, no rungs are offered.
       tagged checkout stamp the correct number. Tag-then-rebake is wrong: it leaves the tag carrying the
       previous release's version. (The wheel version is computed by the resolver and is unaffected either
       way; this rule is specifically about the baked file the installer distributes.)
    +- **Ship-and-succeed release records.** Exactly one release record must be planned at a time so that the `next` sentinel resolves. When shipping a release, mark the outgoing release record shipped and create its successor record in the same change: `aw set shipped <id6>` plus `aw releases new --version <successor-version> --summary ... --apply`. Shipping without creating a successor leaves zero planned releases, which causes all sentinel-gated records to dangle. Tooling refuses shipping the last planned release without creating the successor or supplying an explicit attested override.
     - Never create or push a tag, a GitHub Release, or a registry upload outside release-review
       Section 9 after an explicit human GO. No ad-hoc `git tag`; no `git push --follow-tags` of
       release tags.
    ```
    Sanitizer check:
    `python3 -m agent_workflows check-local-leaks . --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    Dashes check: 0 em or en dashes in any added user-facing text.
    Live-tree check:
    `python3 -m agent_workflows check release-gates --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required, but recorded because the plan spans four modules and could look splittable. The four changes are ONE causal chain measured end to end: the conflated resolution (E-01) is what makes the check mis-attribute (E-02/E-03), the mis-attribution is what makes the doctor advice a no-op (E-06), and the silent tooled writer (E-04/E-05) is the only route into the state at all. Splitting them would ship a half-fix that either refuses the transition while still emitting 697 wrong findings, or fixes the attribution while leaving the one-command trapdoor open. E-07 and E-08 are the validation and the human-facing obligation for the same behavior.

This plan requires explicit human approval before execution. It is `to-review` and carries NO `- Readiness:` field, deliberately: that field is an output of `/plan-review` and writing it at authoring time would forge a review that has not happened.

EXECUTION CONTRACT. Commit only the files this plan changed, limited to the declared `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Run the suite BARE as `python3 -m pytest` and paste the actual runner output; a claimed pass with no pasted output does not satisfy any `V-*` item here. Work in an isolated worktree if the runner provides one, and do not revert, stage, or clean any change you did not make.

THE ONE THING THAT MUST NOT HAPPEN. E-02 edits an ERROR-severity rule inside a fail-closed CI family, and the cheap way to make the symptom disappear is to stop reporting. Do not. Every state that exits nonzero today must still exit nonzero after this plan; V-02 and V-07 exist specifically to prove that, and the negative fence in the Scope check enumerates the five weakenings that are prohibited. If a chosen implementation cannot keep both properties (one accurate finding AND a nonzero exit), stop and report rather than trading the invariant for a tidy zero.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`. Backlog item `cnn7au` is set `graduated` by the runner on verification of this authoring turn; it must NOT be set `done` here, since the code is not yet written.
