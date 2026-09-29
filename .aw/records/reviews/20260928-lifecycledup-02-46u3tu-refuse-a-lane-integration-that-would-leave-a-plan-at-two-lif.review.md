# Review findings: plan 46u3tu

- Subject-Id: 46u3tu
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3f1ea74e` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and unmodified. No production
code was modified by this review; every post-change claim below was measured by driving the shipped
functions, against real git repositories in temp directories for the integration probes and against
this repository's own tree for the placement measurements.

THE PLAN'S DIAGNOSIS IS CORRECT, ITS CENTRAL DEFECT REPRODUCES EXACTLY, AND ITS CORRECTION OF THE
BACKLOG ITEM HOLDS. Re-driven end to end at review through `oc_runipd.integrate_lane_branch` on the
add/add fixture (plan ABSENT at the merge base, lane commits it at `pending/`, main commits the same
filename at `executed/`): `merge-tree --write-tree` exits 0, the predicted tree lists BOTH
`.aw/records/plans/pending/...ipd.md` and `.aw/records/plans/executed/...ipd.md`, the call returns
`integrated=True`, `kind='integrated'`, reason `controlled non-ff merge integrated to main`, and main
afterwards holds the plan at both paths. So F-03 and F-04 are confirmed independently, the defect is
real, no existing gate sees it, and the plan is worth executing.

WHAT REVIEW FOUND IS ONE DEFECT THAT WOULD HAVE MADE THE SHIPPED ARM REFUSE EVERY INTEGRATION IN
THIS REPOSITORY, a second that would have refused an ordinary and expected lane act, and three
unreachable or wrong instructions in E-02. The approach is sound and every finding was repairable
with bounded edits to this plan alone.

**THE ARM WOULD HAVE REFUSED EVERY INTEGRATION ON BOTH HOSTS (PR-101, BLOCKER).** E-01 consumes
Order 1's PURE CORE, which by Order 1's own design carries NO enumeration and therefore no filtering:
`tl2b2r` E-01 sites the filtering in the SCANNING WRAPPER (`check_engine._iter_type_files`, which
drops `_SKIP_NAMES` = `{'README.md','INDEX.md','STATUS.md'}` and globs `*.md`) and hands the core "an
iterable of already-gathered `(path, text_or_None)` records". This plan's records come from RAW
`git ls-tree -r --name-only <tree>`. Order 1's F-07 "zero duplicated locations" was measured through
the FILTERED wrapper, so it does not describe what this caller sees. Driven at review over this
repository's real `HEAD`: FOUR identities already sit at more than one lifecycle bucket, namely
`('plans','README.md')` at six buckets, `('plans','.gitkeep')` at five, and the same pair for
`prompts`. On an `aw install`-shaped tree with every declared bucket scaffolded it is EIGHT, across
all four types. That furniture is deliberate (`engine.py` writes
`files.append((f"{dirs['plans']}/{sub}/.gitkeep", ""))` per bucket), so an arm reading ABSOLUTE
placement refuses every lane from the first commit. This is a BLOCKER because the failure mode is a
normal-path failure of the whole runner rather than a missed detection, and because the plan cited
Order 1's F-07 as though it licensed the absolute reading.

**AND THE HEAD DELTA ALONE IS STILL NOT SUFFICIENT (PR-102, HIGH).** Driven at review: with a base
carrying only `specs/draft/` and `specs/approved/`, a lane that creates `specs/reviewed/` with the
`README.md` plus `.gitkeep` that `aw install` writes makes the HEAD delta report both of those as
NEWLY INTRODUCED at a second bucket, so a delta-only arm refuses that lane. This is not exotic:
`specs/parked/` is the one declared bucket ABSENT from this tree today, so the next plan that parks a
spec produces exactly this shape. The remedy is to apply the wrapper's own exclusions to the raw list
in THIS caller, which is why a new OQ records the decision rather than leaving it implicit.

**E-02's EXPECTED OUTCOME WAS UNREACHABLE AS WRITTEN (PR-103, MEDIUM).** It required
`terminal_refusal_verdict` to return a sentence naming BOTH record paths. Driven
`inspect.signature`: that function is `(integ_kind: str, cause: str) -> str` and has exactly ONE
caller, `decide_integration_deferral`, whose own signature is
`integ_kind`/`attempts_used`/`limit`/`policy`/`cause`. Neither receives a path, a verdict object or
the grouping, so the requirement could only be met by widening two signatures shared by every refusal
kind, in a plan whose own Deferred section declares the ladder out of scope. An executor would have
hit this after writing E-01 and either widened undeclared shared surface or quietly dropped the
requirement.

**"MAP IT WHERE THE EXISTING CAUSES ARE MAPPED" POINTED AT THE WRONG DICT (PR-104, MEDIUM).**
`GATE_STATUS_TO_INTEGRATION_CAUSE` maps a GATE STATUS to a cause and holds exactly two entries; the
third existing cause, `INTEGRATION_CAUSE_GIT_CONFLICT`, is deliberately ABSENT from it because
`integrate_lane_branch`'s own arm produces it rather than a gate status (driven:
`INTEGRATION_CAUSE_GIT_CONFLICT in GATE_STATUS_TO_INTEGRATION_CAUSE.values()` is `False`). This
refusal fires BEFORE the gate runs, so it has no gate status at all, and an added entry would assert
a status that cannot occur, which is the practice the module explicitly forbids for the unreachable
four.

**TWO CAUSE-KEYED CONSUMERS WERE NEVER CHECKED (PR-105, MEDIUM).** The plan reasons about the
redaction asymmetry but never asks whether the new cause ENTERS the paths that key on a cause. Driven
against a tagged reason: the merge-conflict SEND-BACK loop predicate
(`read_integration_cause(reason)[0] == INTEGRATION_CAUSE_GIT_CONFLICT`) is `False`, and
`record_integration_refusal`'s un-redacting `record_refusal` call keys on the same equality and is
also `False`. Both outcomes are the wanted ones, so no code is owed, but they were assumed rather
than measured, and a later executor choosing to reuse `INTEGRATION_CAUSE_GIT_CONFLICT` instead of a
new constant would silently acquire a correction turn for a condition no agent edit can fix.

**THE SUITE BASELINE DRIFTED AGAIN (PR-106, LOW).** F-11 recorded `2937 passed` at authoring; bare
`python3 -m pytest` re-driven at review in this same lane reports `3153 passed, 2 skipped, 3 warnings
in 49.21s` (205 deselected). That is +216 from unrelated main traffic, and V-04 used the authored
figure as its comparison bar, which cannot distinguish an added test from a merge. Order 1's review
reached the same conclusion independently on the same number, which is corroborating rather than
coincidental.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed and none was added. Both authored open questions survive review, OQ-01's resolution strengthened
by PR-101's measurement (the delta is load-bearing, not merely kind to innocent lanes) and OQ-02's
reinforced by driven classifier output rather than reasoning. OQ-03 is new, recording the filtering
decision that PR-102 forced.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | A. Correctness / D. Anti-regression | plan E-01 ("Compare the predicted tree's placement against `HEAD`'s ... this repository currently has none (Order 1 F-07)"); `check_engine._SKIP_NAMES` = `{'INDEX.md','STATUS.md','README.md'}` and `_iter_type_files` -> `sorted(d.rglob("*.md"))`; `tl2b2r` E-01 (core takes "an iterable of already-gathered `(path, text_or_None)` records"); `engine.py` (`files.append((f"{dirs['plans']}/{sub}/.gitkeep", ""))`); driven over real `HEAD`: four multi-bucket identities, eight on a fully scaffolded tree | THE ARM WOULD REFUSE EVERY INTEGRATION IF IT READ ABSOLUTE PLACEMENT, and the plan cited Order 1's zero-duplicate measurement as though it licensed that reading. That measurement ran through the FILTERED wrapper; Order 1's pure core is filter-free by design, and this plan feeds it RAW `git ls-tree` output. Every lifecycle bucket of every type carries a tracked `README.md` and `.gitkeep` on purpose, so raw stem grouping reports four multi-bucket identities on this tree today and eight on a fresh install. A normal-path failure of the runner on both hosts, not a missed detection. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the fix is a comparison already named in the plan, promoted from optional to required, plus a pinning test; no code exists yet) | FIXED | E-01 now states the HEAD-delta comparison is a CORRECTNESS REQUIREMENT with the measurement inline, and explicitly refuses the absolute reading. Added F-12 carrying both driven figures. E-04 gains row (e) (a base with furniture in every bucket, which must still integrate) and V-01 requires pasting the raw grouping over this repository's `HEAD` beside the arm's silence on it, so "it did not refuse" is not taken on trust. OQ-01's resolution restated: the delta is load-bearing, not a courtesy. |
| PR-102 | HIGH | UNDER-SCOPE | A. Correctness / F. UX (a gate that reds on normal work gets bypassed) | driven in a throwaway repo: base carries `specs/draft/` + `specs/approved/`, lane creates `specs/reviewed/` with `README.md` + `.gitkeep`, HEAD delta reports `('specs','README.md') -> ['reviewed']` and `('specs','.gitkeep') -> ['reviewed']` as INTRODUCED; `sorted(LIFECYCLE_SUBDIRS['specs'])` vs the buckets present on disk (only `parked` absent) | THE DELTA ALONE STILL REFUSES A LEGITIMATE LANE. A lane that merely SCAFFOLDS a lifecycle bucket the base lacks introduces that bucket's furniture at a second location, so a delta-only arm refuses it. `specs/parked/` is the one declared bucket absent from this tree, so the next plan parking a spec reproduces the shape; this is expected traffic, not a corner case. A gate that reds during ordinary work is a gate that gets bypassed. | C:Low; U:Low; S:Low; F:Low; Overall:Low (apply the wrapper's existing exclusions in the caller; both symbols already exist) | FIXED | E-01 now requires FILTERING the raw enumeration before grouping (skip `check_engine._SKIP_NAMES`, require the type's `artifact_naming.TYPE_FACET` suffix) and states the core is deliberately unfiltered so the filter is this caller's obligation. It explicitly forbids pushing the filter into Order 1's core (undeclared file, already `executed`, and it would destroy the filter-free property Order 2 depends on). Added F-13, new OQ-03, E-04 row (f), and a V-04 falsification requirement that dropping the filter makes row (f) FAIL. |
| PR-103 | MEDIUM | IN-SCOPE | G. Plan executability | plan E-02 Expected outcome ("`terminal_refusal_verdict` returns a sentence naming the lifecycle condition and both paths"); driven `inspect.signature(terminal_refusal_verdict)` = `(integ_kind: str, cause: str) -> str`; its single caller `decide_integration_deferral` = `(*, integ_kind, attempts_used, limit, policy='defer', cause='unknown')` | AN EXPECTED OUTCOME THAT CANNOT BE MET. Neither the verdict function nor its only caller receives a path, a verdict object or the placement grouping, so a sentence naming both record paths is unreachable without widening two signatures shared by every refusal kind, in a plan that declares the ladder out of scope. An executor would discover this after E-01 and either breach scope or drop the requirement silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now SPLITS the obligation: the verdict names the condition CLASS (matching how the three existing sentences describe their class rather than their instance), and the two paths, buckets and statuses go in the `reason` E-01 returns, which is what reaches `item["integration_deferral"]`, the attempt record and the console. Added F-14, a Deferred row refusing the signature widening with its reason, and a corrected V-02 that explicitly does NOT require paths from the verdict. |
| PR-104 | MEDIUM | IN-SCOPE | C. Architecture and operability | plan E-02 ("map it where the existing causes are mapped"); `GATE_STATUS_TO_INTEGRATION_CAUSE` = 2 entries, both `integration_failed_*`; driven `INTEGRATION_CAUSE_GIT_CONFLICT in GATE_STATUS_TO_INTEGRATION_CAUSE.values()` is `False` | THE ONE "MAPPING" THE INSTRUCTION COULD NAME IS THE WRONG ONE. That dict maps GATE STATUSES, and the only comparable existing cause (the one this refusal most resembles, produced by `integrate_lane_branch`'s own arm) is deliberately absent from it. This refusal fires before the gate runs and has no gate status, so an entry would assert a status that cannot occur, which the module forbids for the unreachable four. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02's opening sentence no longer says to map it, states there are exactly TWO registrations (the constant and a verdict branch), and records that the old wording was measured wrong and removed so it is not restored from a stale copy. A dedicated bullet forbids the dict entry with the driven evidence. Added F-15. V-02 requires pasting the dict UNCHANGED. |
| PR-105 | MEDIUM | UNDER-SCOPE | E. Testing and verification | `runner_shared` send-back predicate (`read_integration_cause(integ_reason)[0] == INTEGRATION_CAUSE_GIT_CONFLICT` and `integ_kind == INTEGRATION_REFUSAL_CONFLICT`); `record_integration_refusal`'s `if cause == INTEGRATION_CAUSE_GIT_CONFLICT: record_refusal(...)`; driven `False` for both against a `tag_integration_cause('lifecycle-duplicate-placement', ...)` reason; driven `revalidation_was_unmeasured({})` is `False` | TWO CAUSE-KEYED CONSUMERS WERE ASSUMED RATHER THAN MEASURED. A new cause either enters the agent SEND-BACK loop (spending a correction turn on a placement no agent edit can change) or the un-redacting `record_refusal` writer, and the plan reasons about redaction without asking either question. Both are correctly `False` for a new constant, so nothing is owed, but an executor who instead REUSED `INTEGRATION_CAUSE_GIT_CONFLICT` would acquire both behaviors silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 gains a bullet requiring both predicates be driven and their `False` results pasted, plus the `revalidation_was_unmeasured` result showing a pre-gate refusal is not reclassified to the deferrable unmeasured kind. Added F-16. V-02 lists all three as required evidence. |
| PR-106 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-11 (`2937 passed, 2 skipped, 3 warnings in 45.62s`, 201 deselected); re-driven bare `python3 -m pytest` at review: `3153 passed, 2 skipped, 3 warnings in 49.21s` (205 deselected) | A LIVE COUNT USED AS A BAR, AND IT DRIFTED BY 216 TESTS BEFORE EXECUTION. V-04 required comparing the suite summary against F-11's authored figure; a plan-recorded total cannot distinguish an added test from unrelated main traffic. This is the repository's own live-artifact-count convention applied to the plan's own validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 carries both figures, is relabelled as context that provably drifts, and states the +216 is other work. V-04 now requires a baseline taken in this same lane IMMEDIATELY BEFORE the change, with added tests accounted as the difference between two runs, and forbids comparing against any number in the plan. The Required tests section carries the same instruction. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Raw `git ls-tree` output contains per-bucket `README.md`/`.gitkeep` furniture that groups as duplicated identities. Filter in this caller, filter in Order 1's core, or rely on the HEAD delta alone? | FILTER IN THIS CALLER, applying the wrapper's own exclusions (`check_engine._SKIP_NAMES` plus the type's `artifact_naming.TYPE_FACET` suffix) to the raw path list before grouping, AND keep the HEAD delta. | (a) Rely on the delta alone - TESTED AND REFUTED at review: a lane scaffolding `specs/reviewed/` with its `README.md` and `.gitkeep` makes the delta report both as newly introduced, so the arm refuses a lane whose only act was creating a directory, and `specs/parked/` is absent from this tree so the case is imminent. (b) Teach Order 1's pure core to filter - rejected: its filter-free contract is precisely what makes it callable on a tree enumeration (PR-002 of Order 1's own review), `check_engine.py` is not in this plan's `Scope-Paths`, and Order 1 will be `executed` and unamendable when this runs. (c) Read absolute placement and accept the noise - rejected: measured to refuse every integration in this repository. (d) Ask the maintainer - rejected: the repository answers it by driving two probes, and resolving from evidence is the instructed default. | Driven over real `HEAD`: four raw multi-bucket identities (`plans`/`prompts` x `README.md`/`.gitkeep`), eight on a fully scaffolded tree. Driven in a throwaway repo: the bucket-scaffolding lane's delta reports the furniture as INTRODUCED. `check_engine._SKIP_NAMES` and `_iter_type_files`'s `*.md` glob; `engine.py`'s per-bucket `.gitkeep` writes; `tl2b2r` E-01's core contract. | yes |
| D-2 | `terminal_refusal_verdict` cannot name the offending paths. Widen it (and its caller), or carry the paths elsewhere? | CARRY THE PATHS IN THE `reason` STRING E-01 RETURNS; the verdict names only the condition class. | (a) Widen `terminal_refusal_verdict` and `decide_integration_deferral` to take the grouping - rejected: both are shared by every refusal kind, the plan's own Deferred section declares the ladder out of scope, and the information is already delivered by the `reason`, which reaches `item["integration_deferral"]`, the attempt record and the console. (b) Drop the requirement that both paths be named anywhere - rejected: an operator who is told only that "a duplicate exists" must then find both copies by hand, which is the measured `5bmq5f` complaint Order 1 was told not to reproduce. (c) Add a second verdict function taking paths - rejected: two verdict producers for one refusal is the drift `tag_integration_cause` exists to prevent. | Driven `inspect.signature` on both functions; the single call site read from `decide_integration_deferral`; `record_integration_refusal` writing `item["integration_deferral"] = integ_reason`. | yes |
| D-3 | Should the new cause be added to `GATE_STATUS_TO_INTEGRATION_CAUSE`? | NO. Exactly two registrations: the constant, and a `terminal_refusal_verdict` branch. | (a) Add a dict entry to satisfy "map it where the existing causes are mapped" - rejected on measurement: that dict is keyed by GATE STATUS, this refusal fires before the gate runs and has none, and the most comparable existing cause is deliberately absent from it for the same reason. An entry would assert a gate status that cannot occur, which the module explicitly forbids. (b) Reuse `INTEGRATION_CAUSE_GIT_CONFLICT` rather than adding a constant - rejected: driven, that value routes into the agent send-back loop and the un-redacting `record_refusal` writer, neither of which is wanted for a placement no agent edit can change. | `GATE_STATUS_TO_INTEGRATION_CAUSE`'s two entries; driven `INTEGRATION_CAUSE_GIT_CONFLICT in ...values()` is `False`; the send-back and `record_refusal` predicates driven `False` for a new cause. | yes |
| D-4 | F-11's suite baseline drifted 216 tests between authoring and review. Update the digit, or change what V-04 compares against? | BOTH: record the re-driven figure as context and change V-04's bar to a baseline taken in this lane immediately before the change. | (a) Just update the number - rejected: it drifted once already and will drift again before execution, and the repository's own live-artifact-count convention says such a count belongs in prose as context rather than as a bar. (b) Drop the accounting requirement - rejected: accounting for every added test is a real obligation; only the reference point was wrong. | Re-driven `3153 passed, 2 skipped, 3 warnings in 49.21s` against the authored `2937 passed`; Order 1's F-11 reaching the same conclusion on the same number. | yes |
