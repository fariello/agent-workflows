# Review findings: plan tliqz6

- Subject-Id: tliqz6
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in a lane worktree at HEAD `2cfd2a1ea`. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after with zero findings. No pre-review snapshot was owed: `git status --porcelain` was
empty, so the plan was committed and unmodified. NO PRODUCTION FILE WAS MODIFIED; every measurement
was taken either by direct call against the real functions or in throwaway git repositories under the
gitignored `tmp/` path, and `git status --porcelain` is empty apart from the two planning documents
this review authored.

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND FOURTEEN OF ITS FIFTEEN FINDINGS RE-MEASURED CORRECT.
F-05, which is the plan's central justification, reproduces exactly: seeding one plan at `approved` in
a throwaway repo and staging four variants, `check_status_untooled` refuses the two UNATTRIBUTED
variants and PASSES the attributed illegal `approved -> draft`, while `validate_transition` refuses
both illegal variants and passes both legal ones. The two gates are therefore genuinely orthogonal,
the attributed illegal edit is currently unrefused by anything the repository ships, and the plan's
decision to ADD a rule rather than widen `check_status_untooled` is correct. F-01 holds (the
aggregator's `for fn in (...)` names exactly three rules and none consults the predicate). F-02, F-04,
F-06 and F-08 reproduce verbatim by direct call, including that `validate_transition('draft','executed')`
refuses on its terminal-predecessor branch with no actor. F-07 reproduces and is the strongest
argument in the plan: `approved -> executed` is `ok=True` with no actor, `ok=True` for `aw ipd finalize`,
and `ok=False` for the real driver actors (`aw oc run`, an `opencode ...` model string), which is
exactly why passing no actor is right. F-10's full design was INDEPENDENTLY REBUILT as a probe from
E-03's prescription and scored correct on all 17 edges plus the clean tree (4 must-refuse, 13
must-pass, zero mismatches). F-11's zero-refusal replay reproduces. F-12 holds, including that the
`precommit-scope-gate` is not wired in `.pre-commit-config.yaml` and that `aw check plans` runs as a
named fail-closed CI step. F-13's class is not merely live but GROWING. The metadata is correct:
backlog `4ynlcg` is `graduated`, carries no `- Blocks-Release:`, and the sibling `nvsz19` declares
`status_set.py` plus two test files, so there is no file contention.

THE SUBSTANTIVE FINDING IS PR-001, and it is a case of a true measurement supporting a false
conclusion. F-09 measured `validate_transition('APPROVED','draft')` returning `ok=True`, which is
real, and concluded a case-fold was mandatory. But E-03 is REQUIRED to read its statuses through
`_status_meta`, which already lowercases, so no uppercase value can reach the predicate by this code
path. The fold would have been dead code, its test could not fail, and V-03's demanded demonstration
was unsatisfiable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | Rubric E (testing); GUIDING_PRINCIPLES P16 (a test that cannot fail) | `agent_workflows/check_engine.py` `_status_meta` -> `_metadata_status` (`return m.group(1).strip().lower() if m else None`); the plan's E-03 ("normalize BOTH ... and case-fold"), E-05 case (i), V-03's third discriminating case, and F-09 | **THE MANDATED CASE-FOLD IS DEAD CODE, ITS TEST CANNOT FAIL, AND THE EVIDENCE DEMANDED FOR IT CANNOT BE PRODUCED.** F-09's predicate-level measurement is true but UNREACHABLE from this rule: E-03 must read statuses through `_status_meta`, which already lowercases, so `- Status: APPROVED` arrives as `'approved'` (measured). A probe built to E-03's exact shape refuses `APPROVED -> draft` IDENTICALLY with and without the fold, so E-05 case (i) pins nothing and V-03's demand to show it "passing without the case-fold" is unsatisfiable. F-09's corpus evidence fails independently: all 25 uppercase files are in `executed/` (a terminal source E-03 skips anyway) and every one carries a MULTI-WORD value for which `_status_meta` returns `None`, so not one of them could ever produce a status delta here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The fold is REMOVED from E-03 with the reason stated in the plan, and E-03's expected outcome now requires its absence. The ALIAS NORMALIZATION the plan bundled with it is KEPT and shown to be the genuinely load-bearing half: measured, a staged `- Status: pending` yields `unknown target status 'pending'` and falls through, hiding the real illegal `approved -> pending` edge (which normalizes to `approved -> to-review`). E-05 case (i) and V-03's third case are repointed at that pair in BOTH directions (`approved -> pending` refused, `pending -> reviewed` not refused), so the case can actually fail when the normalization is dropped. F-09 is rewritten as WITHDRAWN carrying both counter-measurements, and the Scope check's reference to it is corrected. |
| PR-002 | MEDIUM | IN-SCOPE | project rule `check.ipd-uncarried-obligation` (`error`, I-07); Rubric G | `aw check` / `check_engine.check_durable_carrier` naming this plan; the deferral row reading `- Carrier: AW_MISSING_INPUT see Open questions OQ-01; ...`; `test_check_engine_release_gate.py::test_check_commit_invariants_composition` | **TWO DEFECTS THE SHIPPED CHECKERS ALREADY FLAG AT `error` SEVERITY, PLUS A FALSE PREMISE UNDER ONE DECLARED SCOPE PATH.** (a) A deferral row's `- Carrier:` value is the literal sentinel string `AW_MISSING_INPUT see Open questions OQ-01; ...`, which `check_durable_carrier` rejects as a malformed reference ("expected a bare 6-char id6"); the row asserted a carrier that does not exist. (b) OQ-01 itself records an outstanding obligation with no carrier field, flagged by the same rule. (c) Separately, the plan asserts `test_check_commit_invariants_composition` "WILL NEED UPDATING" and declares a scope path on that basis, but measured it will NOT break: it asserts via three `assertIn` plus one `assertNotIn` over a SET with no exact-set assertion, and its fixture runs `git init` then `git add` with no commit, so the staged plan has no HEAD blob and the new rule's add-case skip emits nothing there. V-04's demand to justify "the change" was therefore unsatisfiable too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both carrier rows replaced with typed `Carrier-Declined` fields stating the real reason: what is outstanding on the F-07 class is a mutually-exclusive CHOICE between two remedies, so no backlog item can describe defined work until the maintainer answers, and the declination explicitly expires with that answer. Re-ran the shipped predicate: no finding for this plan (74 -> 73 tree-wide). For (c), F-16 records the measurement, the scope path is KEPT for an ADDITIVE strengthening (adding the new rule id to the `assertIn` set so the composition is pinned at four), and V-04's demand is replaced with an honest two-branch instruction (paste the strengthening green, or state the path was declared-but-unmodified and will be `--scope-ack`ed). |
| PR-003 | LOW | IN-SCOPE | live-artifact re-derivation convention | bare `python3 -m pytest`; `check_lifecycle_transitions` over the live tree; pending-plan census; the 400-commit replay | **EVERY LIVE COUNT IN THE FINDINGS TABLE HAS DRIFTED, ONE BY ENOUGH TO BE MISREAD AS CATASTROPHE.** Re-measured at review: pending plans 194 -> 185; born at `to-review` 65 -> 37; replay transitions examined 350 -> 98 (the `WOULD REFUSE: 0` unchanged); `check_lifecycle_transitions` findings 5 -> 9; bare suite `3512 passed, 2 skipped` -> `3809 passed, 2 skipped`. No conclusion moves, and the F-13 drift strengthens the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each figure re-recorded beside its authoring value with an explicit re-derive instruction rather than as a bar. F-15's suite note now states the number is a live population; the Required-tests bullet states why the re-derive instruction is load-bearing rather than boilerplate (a literal comparison would read a 297-test gain as damage); F-11 tells V-06 to compare its own two numbers; F-13 records the growth as corroboration. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 removes the case-fold. Should the discriminating test case it justified be deleted, or replaced? | REPLACED, with the alias-normalization pair (`approved -> pending` refused, `pending -> reviewed` not refused). | (a) Delete case (i) outright: rejected because it would leave the normalization, which IS load-bearing, pinned by nothing, and the plan would lose a case that can genuinely fail. (b) Keep the uppercase case anyway as harmless: rejected because a test that cannot fail is forbidden by GUIDING_PRINCIPLES P16 and actively misleads a later reader into believing the fold is protecting something. (c) Keep the fold as cheap insurance: rejected because dead code with a non-failing test is exactly what the repository's outcomes-not-structure rule exists to prevent. | Measured: `_status_meta('- Status: APPROVED')` -> `'approved'`, and a probe built to E-03's shape refuses `APPROVED -> draft` identically with and without the fold; while `validate_transition('approved','pending')` -> `ok=False, "unknown target status 'pending'"` (falls through) versus the normalized `approved -> to-review` -> `ok=False, "backwards transition"` (refused). So the normalization changes an outcome and the fold does not. | yes |
| D-2 | The F-07 actor-attribution class has no fileable carrier. Declare `Carrier-Declined`, or file a backlog item to satisfy the `error`-severity rule mechanically? | `Carrier-Declined` on both the deferral row and OQ-01, each stating that the outstanding thing is a CHOICE and that the declination expires when the maintainer answers. | Filing a backlog item now: rejected because the two candidate remedies (widen `_FINALIZE_ACTORS`, or have finalize record a canonical actor) are mutually exclusive with different costs, so an item would either pre-commit to one remedy on no authority or be a placeholder restating the question. Leaving the sentinel string in place: rejected outright, since it is a malformed reference the shipped checker rejects and it asserts a carrier that does not exist. | `check_durable_carrier`'s recovery text accepts `Carrier-Declined` as a first-class escape; re-running the predicate after the edit returns no finding for this plan; F-07's measurement (356 edges, the actor census) is already recorded so nothing is lost by waiting; OQ-01 names the maintainer as owner and the two options with their differing consequences. | yes |
| D-3 | The composition test does not break, yet the plan declares its file. Drop the declared path, or keep it? | KEEP it, for an additive strengthening that pins the composition at four rules. | (a) Drop the path: rejected because the composition contract would then tolerate three rules silently, and a future regression that stopped composing the new rule would pass the test it was supposed to be fenced by. (b) Keep the plan's original claim that the test "will need updating": rejected as false, measured, and it would have sent an executor looking for a break that does not exist and then demanded a justification for a change that was not necessary. | Assertion census over the test body: three `assertIn`, one `assertNotIn`, zero `assertEqual` on the rule set; its fixture's git sequence is `init`, `config`, `add` with no `commit`, so the staged plan has no HEAD blob and the add-case skip applies. `aw ipd finalize` already enforces `--scope-ack` for a declared-but-unmodified path, so keeping the declaration is safe either way. | yes |

### Deferred and open

(none)

OQ-01 remains OPEN with `Owner: maintainer` and `Blocking: no`, which this review did not disturb: it
is a genuine risk-appetite choice between two incompatible remedies, E-03 passes no actor so the rule
is correct whichever way it is answered, and a non-blocking open question is not a `NO-GO` condition
(maintainer ruling 2026-09-10, plan `qhy3i3` OQ-01). OQ-02 was already resolved from repository
evidence and the review confirmed its reasoning independently: `doctor.py` does call
`check_engine.check_status_untooled` in the same collection path with the same `try`/`except`
isolation, so declaring it is consistency with a shipped precedent rather than scope growth.
