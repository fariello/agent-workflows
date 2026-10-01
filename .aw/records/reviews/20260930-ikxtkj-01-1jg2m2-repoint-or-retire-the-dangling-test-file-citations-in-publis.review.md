# Review findings: plan 1jg2m2

- Subject-Id: 1jg2m2
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-101 (HIGH, fixed), PR-102 (MEDIUM, fixed), PR-103 (MEDIUM, fixed), PR-104 (MEDIUM, fixed), PR-105 (LOW, fixed), PR-106 (LOW, fixed)

## Round 1

Reviewed at HEAD `f90b054f`. Structural preflight `aw ipd lint --phase author --agent` reported
`clean` (exit 0) before semantic review, and `--phase review-finalize --agent` reported `clean`
(exit 0) after all revisions. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row
check does not apply.

THE PLAN'S EVIDENCE IS UNUSUALLY STRONG AND I RE-DERIVED IT RATHER THAN ACCEPTING IT. Every
material claim verified, including the three that cut AGAINST the backlog item it graduated from:
`tests/test_flag_surface_uniformity.py` exists at 8,383 bytes (re-added by `44323024`), carries zero
matches for either `EXEMPT_SUBCOMMANDS` or `FORWARDED_SUBCOMMANDS`, and covers both flag pairs
(9 color, 12 interactive matches), so F-1 holds in full; the `test_wtiso_characterization.py`
passage genuinely opens `THESE DEFECTS ARE NO LONGER PINNED BY A TEST` and states the 2026-09-18
retirement before the name appears, so F-4's refusal to "fix" it is correct; and the two coverage
holes measure exactly as F-6 and F-7 state (zero test references for all seven
`security_hardening` checkers, and zero for `gate_changelog_versioning`, `gate_residual_risk` and
`build_report` against one file each for `gate_leak_scan` and `gate_ipd_lint`). The five deletion
attributions are exact. P16's "one narrow exception" sanctions this test shape verbatim.

The findings therefore concern the plan's DURABLE ARTIFACT (the new test) and its internal ordering,
not its premise.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | Rubric D (anti-regression), E (testing), G | plan E-08 as authored ("SCOPE IT TO PUBLISHED PROSE ONLY: every file under `docs/` plus the root prose docs"); `DECISIONS.md` header ("Append-only, dated record of significant decisions"); `pyproject.toml` `markers` (`livecorpus`) | E-08's SCAN ROOT WAS AMBIGUOUS IN A WAY THAT WOULD MAKE THE NEW GUARD START RED ON 39 UNFIXABLE CITATIONS. E-08 names no root files, so an executor reading it alone would glob the repository root. Measured at review: `docs/**/*.md` plus the five enumerated root docs yields exactly 6 dangling citations and is GREEN after this plan's fixes; adding a root `*.md` glob additionally yields `CHANGELOG.md` 4 and `DECISIONS.md` 35. Both are append-only dated history, so those citations were correct when written and repointing them would falsify the record, which is the same reasoning the plan already applies to `.aw/records/` and to the wtiso passage. A red default-run test blocks integration for every concurrent lane, which is the exact cost `pyproject.toml` records for the `livecorpus` class (2026-09-19: 2h 10m, $55.02, nothing integrated) | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-08 now requires an ENUMERATED literal allowlist (`docs/**/*.md` plus exactly the five named root docs), forbids a root `*.md` glob, and excludes `CHANGELOG.md`/`DECISIONS.md` by name with the append-only reason stated; it also records that an allowlist fails safe (a missed catch, not a false failure). E-01 must scan the two history files but report them in a separate labelled out-of-scope section so the census stays honest. A new out-of-scope entry records the 39-citation class. V-08 now demands the scan-root constant be pasted and a passing run be shown WHILE those two files still contain danglers. Recorded as F-11 |
| PR-102 | MEDIUM | UNDER-SCOPE | Rubric A (correctness), F (honest documentation) | `docs/wtiso-state-taxonomy.md` `## Column vocabularies (closed enums)` opening sentence `The freeze test rejects any value outside these sets.` | A SECOND FALSE PRESENT-TENSE CLAIM ABOUT THE DELETED FREEZE TEST SITS TWELVE LINES FROM THE ONE E-04 FIXES, and the plan did not name it. No citation-scanning test can ever catch it because it names no path. Fixing only the cited half would leave the document dating the freeze test's removal in one paragraph and asserting its active enforcement in the next section | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now fixes both claims and dates the loss to `19313eed`; V-04 demands the second sentence be quoted and a grep showing no present-tense mechanical-checking claim survives in the file. Recorded as F-12, which also states the resulting LIMIT of E-08 plainly: an existence test catches a dangling path, not a false claim about a deleted test |
| PR-103 | MEDIUM | IN-SCOPE | Rubric G (plan executability), sequencing | plan E-02 and E-06 as authored ("citing the backlog item E-07 files", `- Depends on: E-01`) | AN ORDERING DEFECT MAKES TWO ITEMS UNEXECUTABLE AS WRITTEN. E-02 and E-06 must cite the backlog item E-07 creates, but both declared `Depends on: E-01` only, so a dependency-ordered executor may perform them before the item exists. The honest outcomes are both bad: a placeholder id6 (a forged reference) or an omitted pointer (the doc states a gap with no way to follow it) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both now declare `Depends on: E-01, E-07`, and each states why. The gate and the Proposed-changes list carry the order note; V-07 now requires the created id6 to be pasted because E-02 and E-06 consume it. `aw ipd lint` accepts the edges |
| PR-104 | MEDIUM | IN-SCOPE | Rubric G (open questions), GUIDING_PRINCIPLES P12 | plan OQ-02 as authored (`bug` versus `chore`/`followup`); `.aw/records/backlog/README.md` `- Work-Kind: bug \| feature \| chore \| security \| followup`; `config.release_gate_work_kinds` | OQ-02 POSED A FALSE BINARY, so the maintainer was being asked to choose between two options when the repository offers a third that fits these gaps better. The backlog enum carries a `security` work-kind the plan never mentions, and measured at review `config.release_gate_work_kinds` returns `frozenset({'bug'})`, so `security` names the risk in the type system WITHOUT auto-attaching a release gate | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 now states three positions with the measurement behind each, and E-07 requires the executor to name which of the four candidate kinds it chose and why the other three were rejected. V-07 requires that justification. The question stays OPEN and `Blocking: no`, because which risk posture to take is the maintainer's call; the review only removed the false constraint |
| PR-105 | LOW | IN-SCOPE | plan-review Step 4 (lifecycle ownership) | plan gate as authored ("move this plan to `.aw/records/plans/executed/` via the tooled transition") | THE GATE INSTRUCTED THE TERMINAL TRANSITION UNCONDITIONALLY, which is wrong under a runner-owned lifecycle: `aw oc run` / `aw agy run` perform the atomic finalize after their own checks, so an executor that also moves the file fights the runner | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now carries the conditional LIFECYCLE OWNERSHIP paragraph (runner-owned versus agent-executed), and still forbids a hand-rolled `git mv` |
| PR-106 | LOW | IN-SCOPE | plan-review Step 4 scope-fence ruling (2026-09-01) | plan gate as authored ("commit only the paths declared in `- Scope-Paths:`"), with no reconciliation route stated | THE SCOPE FENCE GAVE NO ROUTE FOR A LEGITIMATE OUT-OF-SCOPE EDIT. The 2026-09-01 ruling makes a fence a DECLARATION the runner reconciles afterwards, satisfied by a `--scope-reason` at finalize, not a reason to abandon an edit | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states the fence is a declaration and that an out-of-scope edit is made and then justified with a `--scope-reason` per path at finalize |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the 39 dangling `tests/test_*.py` citations in `CHANGELOG.md` and `DECISIONS.md` be fixed, recorded as out of scope, or left unmentioned? | RECORD them as out of scope by class, scan them in E-01 under a separate labelled heading, and exclude them from E-08's guard by name. | (a) Fix them, rejected because it falsifies dated history. (b) Leave them unmentioned, rejected because the census would then be silently incomplete and the next reader would re-discover them as a surprise, possibly writing the guard to the loose root-glob reading. (c) Scan them and fail, rejected on the measured integration cost of a red default-run test. | `DECISIONS.md`'s own header states "Append-only, dated record of significant decisions"; its entries cite tests by the names they bore at the time (the 2026-07 `tests/test_comms.py` and `tests/test_packaging.py` rows). Sibling plan `2wmwf7` (`.aw/records/plans/pending/20260929-ajomj3-01-2wmwf7-...ipd.md`) reached this conclusion independently for dangling SPEC citations in these exact two files, its E-05/E-08 RECORDING rather than fixing them. `pyproject.toml` `markers` records the measured cost of a default-run test that any agent can turn red. | yes |
| D-2 | Does the newly found second false freeze claim (`The freeze test rejects any value outside these sets.`) belong in this plan or in a separate item? | THIS PLAN, folded into E-04. | Filing it separately, rejected: it is in an already-declared scope path, twelve lines from an edit E-04 already makes, and splitting it would ship an internally contradictory document for the interval between the two plans. | `docs/wtiso-state-taxonomy.md` is already in `- Scope-Paths:`, and E-04 already rewrites the adjacent `Freeze means:` paragraph; both sentences assert enforcement by the same test `19313eed` deleted, so they are one defect with two surfaces rather than two concerns. | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Readiness `go-pending-approval`: the verdict is clean, no unfixed
BLOCKER or HIGH finding remains, and the one still-open question (OQ-02, the work-kind
classification) carries `- Blocking: no`, which per the 2026-09-10 maintainer ruling does not make a
plan `NO-GO`. Human approval is the remaining step.
