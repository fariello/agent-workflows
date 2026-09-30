# Review findings: plan 8rsxy1

- Subject-Id: 8rsxy1
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-A01 (MEDIUM, fixed), PR-A02 (LOW, fixed), PR-A03 (LOW, fixed), PR-A04 (LOW, fixed), PR-A05 (LOW, fixed)

## Round 1

Reviewed at HEAD `1630f2c8` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

I REPRODUCED EVERY MEASUREMENT RATHER THAN TAKING ANY ON TRUST, including re-applying the plan's prototype
and reverting it. All of them hold. The defect: on a two-status same-basename fixture the output reads
`20260101-s-01-dupdup-same-name.backlog.md: backlog.id-duplicate: id dupdup also in
20260101-s-01-dupdup-same-name.backlog.md`, location and claimed duplicate byte-identical (F-01). The fix's
output: `.aw/records/backlog/graduated/...: backlog.id-duplicate: id dupdup also in
.aw/records/backlog/done/...`, two different paths, exactly as E-02 predicts. F-04's `aw doctor`
misattribution: driving `doctor._categorize_drift` with the basename shape returns directory
`.aw/records/backlog/done` for a duplicate that actually lives in `graduated/`, and the repo-relative shape
returns `.aw/records/backlog/graduated`. F-06's weak test: its two fixtures really are
`...-01-dupdup-a.md` / `...-02-dupdup-b.md` in one directory, asserting only the rule-id substring. F-02's
mechanism argument: `backlog.drift_location` delegating to `specs.drift_location` returns identical strings
for all four required cases, and the reused helper's records-segment truncation is the right answer.
`aw backlog check` on the live tree reports `all backlog items conform`, so F-01's claim that the defect is
latent and must be driven from a fixture is correct.

THE FIX IS RIGHT AND REVIEW CHANGED NOTHING ABOUT IT. Reusing `specs.drift_location` instead of the backlog
item's proposed `f.relative_to(repo_root)` is the correct call and the plan's reasoning for it is sound:
`relative_to` raises on any path outside the root, and the legacy `.agents/backlog` root makes that reachable
rather than theoretical. E-03's widening beyond the item's literal one-line proposal is justified by measured
findings rather than by taste, and F-07's blast-radius measurement is what makes it safe. What review found
were four errors in what the plan CLAIMS and one gap in what it requires be VERIFIED.

FIRST, AND THE ONE THAT MATTERS: E-03 CHANGES A THIRD SURFACE THE PLAN NAMES NOWHERE.
`check_engine.check_content` calls `_backlog.validate_item(p, ...)` with an ABSOLUTE `p`, so every
`backlog.*` finding on `aw check backlog` renders a BASENAME today for exactly the reason the plan documents
for `aw backlog check`. I drove it: on a fixture with an invalid `Priority`, `check_content` reports
`location= 20260101-s-01-dupdup-bad.backlog.md` before and
`location= .aw/records/backlog/open/20260101-s-01-dupdup-bad.backlog.md` after. This is an IMPROVEMENT and
needs no additional code, which is why it is a MEDIUM about evidence rather than a risk: E-03 as written
already fixes it. But the plan discusses only `aw backlog check` and `aw doctor`, so an executor completing
V-03 as written would leave a user-visible output change on a third command unrecorded. I also verified the
honest bound: `aw check backlog` on the REAL tree is byte-identical before and after, because its three live
findings (`check.name-nonconformant` twice, `check.collisions-not-checked`) come from other producers, so the
change is invisible until a `validate_item` rule actually fires.

SECOND, the rule count is wrong. F-03 says `rel` reaches "ALL TEN" rules; it reaches TWELVE distinct rule ids
across 12 `core.Drift(rel, ...)` construction sites. The plan's own parenthetical list shows how the error
arose: it collapses `gate-missing`/`gate-kind-invalid`/`gate-ref-invalid` into one entry. This changes no
decision, but F-03 is E-03's stated justification and an understated count weakens the argument it exists to
make.

THIRD, the baselines are stale, which is the third plan in this sweep to carry this. Authoring measured
`3246 passed, 2 skipped` bare and `269 passed` on the targeted set; re-measured at review on a later HEAD,
`3291 passed, 2 skipped, 3 warnings in 82.90s` and `272 passed in 39.45s`, both green with the prototype
applied. Three sites instruct a comparison against the authoring totals, and a 45-test drift would read as a
regression.

FOURTH, the gate instructs something that cannot happen: "Backlog item `8hcy97` is transitioned to
`graduated` by the runner on verification". That item is ALREADY `graduated`, carrying
`- Graduated-To: bklgdupemsg` and `- Blocks-Release: next`, so there is no transition for the runner to
perform. An executor reading that would look for a state change that does not exist.

WHAT I CHECKED AND FOUND SOUND, recorded so a later reader knows it was examined. The purity argument for
E-03 is correct: `drift_location` is pure string manipulation with no disk read and no `cwd` dependence, so
routing `validate_item`'s `rel` through it does not weaken that function's documented contract. F-07's
consumer analysis holds, and I READ all four rather than grepping: `set_records.promote_*` raises a
`ValueError` interpolating only `d.rule`/`d.detail`; `runner_shared`'s run-structure preflight builds its
message from `d.rule`/`d.detail` plus its own separately computed `rel_path`; `check_engine.check_content`
passes the Drift through unchanged; none parses the location as a basename. The existing weak test still
passes after the fix (`tests/test_backlog.py` is `37 passed` both before and after), so E-04's decision to
ADD coverage rather than rewrite it is right. I additionally probed two things the plan does not: the
CROSS-LAYOUT duplicate (same id6 and basename under both `.agents/backlog/open/` and
`.aw/records/backlog/open/`, since `_iter_items` spans `BACKLOG_ROOTS`) works correctly and names both sides,
which is now F-10 and a required E-04 case because the legacy segment is precisely where the rejected
`relative_to` mechanism would have raised; and the reused helper's BARE `.agents/` prefix truncation is safe
against four adversarial roots (a temp dir containing `.agents/`, a `.agents-scratch` component, a
`my.agents` component, and a doubled records segment), each truncating at the intended segment. The
`escape_detail` deferral is correct on its own evidence, and I verified the reasoning: a repo-relative POSIX
path contains no tab, newline or control character, so the change would be a provable no-op. No spec
amendment is owed and I confirmed the claim: Section 8.5 of
`attention-registry-and-cross-tree-status` already requires repo-relative POSIX paths, so this plan conforms
to an existing approved contract rather than changing one.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | MEDIUM | UNDER-SCOPE | E. Testing / G. Plan executability (an unrecorded output change) | `check_engine.check_content`'s backlog arm: `drift.extend(_backlog.validate_item(p, p.read_text(encoding="utf-8")))` where `p` comes from `_iter_type_files` and is ABSOLUTE. Driven on a fixture with an invalid `Priority`: BEFORE `location= 20260101-s-01-dupdup-bad.backlog.md`, AFTER `location= .aw/records/backlog/open/20260101-s-01-dupdup-bad.backlog.md`, rule `backlog.priority-invalid` both times | **E-03 changes THREE user-visible surfaces and the plan names two.** `aw check backlog` renders `validate_item` locations as basenames today for the identical reason `aw backlog check` does, so E-03 repairs it as well. This needs no extra code and is an improvement, which is why it is an evidence finding rather than a risk; but V-03 as written would be satisfied without ever looking at it, leaving an output change on a third command undocumented and undetected by the plan's own validation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-09 records the driven before/after AND the honest bound (on the REAL tree `aw check backlog` is byte-identical, because its three live findings come from other producers and are already repo-relative, so the change is invisible until a `validate_item` rule fires). E-03 now states the third surface explicitly and its Expected outcome covers it. V-03 requires the driven `check_content` before/after plus the real-tree byte-identical capture, stating that reporting only the plan's two named surfaces leaves a user-visible change unrecorded. Required-tests adds `aw check backlog` before/after. OQ-01's resolution gains this as a fourth consideration strengthening the same answer. A third silent-failure mode added to the gate |
| PR-A02 | LOW | IN-SCOPE | Evidence accuracy (an understated count in the justification for E-03) | Counted in `validate_item`: 12 `core.Drift(rel, ...)` construction sites and 12 distinct `backlog.*` rule ids (`id-invalid`, `status-invalid`, `status-dir-mismatch`, `priority-invalid`, `kind-invalid`, `set-missing`, `summary-missing`, `summary-unsafe`, `gate-missing`, `gate-kind-invalid`, `gate-ref-invalid`, `gate-unexpected`) | **F-03 says `rel` reaches "ALL TEN" rules; it reaches TWELVE.** The plan's own parenthetical shows the error: it collapses the three `gate-*` rules into a single entry. No decision changes, but F-03 is the stated justification for E-03's widening and an undercount weakens the argument it exists to carry | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 corrected to twelve, with the construction-site count and the full enumeration, and stating how the authoring count arose so a later reader does not re-collapse it. E-03's reference to "all ten" corrected |
| PR-A03 | LOW | IN-SCOPE | G. Plan executability (a stale live-artifact count as a success bar) | Re-measured at review with the prototype applied: bare `python3 -m pytest` -> `3291 passed, 2 skipped, 3 warnings in 82.90s`; the targeted set -> `272 passed in 39.45s`; against this plan's `3246 passed, 2 skipped` and `269 passed in 8.57s` | **Three sites instruct a comparison against authoring-time suite totals that have drifted by 45.** The count is a live population every merged lane moves, so an executor comparing totals reads normal growth as a regression, or reconciles it. The durable facts are that the suite is green before the change and which node ids fail | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-08 records both measurements and states the count is a live population. F-07 restated with the review re-measurement and its finding (empty blast radius) separated from its numbers. The Required-tests bullet and V-04 both now require a FRESH baseline captured at execution HEAD with a node-id comparison, and explicitly forbid comparing against any number written in the plan. A second silent-failure mode added to the gate |
| PR-A04 | LOW | IN-SCOPE | A. Correctness (an instruction for a state change that cannot happen) | `.aw/records/backlog/graduated/20260922-bklgdupemsg-01-8hcy97-backlog-check-duplicate-message-self-referential.backlog.md` carries `- Status: graduated`, `- Graduated-To: bklgdupemsg`, `- Blocks-Release: next`, `- Work-Kind: bug` | **The gate says "Backlog item `8hcy97` is transitioned to `graduated` by the runner on verification"; it is already `graduated`.** There is no transition to perform, so an executor would look for a state change that cannot happen, and a reader cannot tell whether the plan is describing a step that was missed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate corrected to state the item is already `graduated` with the verified front-matter values, so nothing is owed on that front. The "do not set it `done`" instruction is KEPT and its reason made explicit: the item's `- Blocks-Release: next` is inherited by this plan, and the close-legitimacy rule requires an EXECUTED carrier before the item may close, which is a step after this plan rather than part of it |
| PR-A05 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) + E. Testing (a fixture that cannot reach the rule) | Gate as authored: no approval summary, no scope-fence disposition for an out-of-scope edit, no finalize ownership conditional, no silent-failure modes. Separately measured: a thin fixture missing `- Work-Kind:` and a directory-matching `- Status:` produced 12 unrelated `backlog.*` findings across two files and ZERO `id-duplicate` lines | **The gate lacks required execution-contract elements**, and E-04 gives no fixture shape even though `validate_item` runs BEFORE the duplicate check, so a plausible thin fixture emits six unrelated findings per file and no duplicate finding at all. A test built that way fails for the wrong reason or asserts on an incidental substring | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with a "what a human is approving" paragraph naming all four review corrections, a make-and-then-JUSTIFY scope disposition with `--scope-reason` and no stop directive for the scope case, ONE sanctioned stop for the genuinely unsafe condition (`specs.drift_location` absent or re-signatured at execution HEAD, where improvising would re-create the duplicated-policy hazard F-02 avoids), three measured silent-failure modes, and a post-gate `AW-LIFECYCLE-ROLE-001` lifecycle paragraph forbidding a hand-rolled `git mv`. E-04 now states the required fixture fields with the measured failure mode, and adds the F-10 cross-layout case |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-A01: `aw check backlog` also changes. Does it need its own E-item, a production change, or only evidence? | EVIDENCE ONLY, folded into E-03's statement and V-03's requirements | (a) A separate E-item for the `check_engine` surface; (b) exempt `check_engine` so its locations stay basenames; (c) leave it undocumented since the fix is automatic | Read the call site: `check_engine.check_content` passes the Drift through UNCHANGED, so E-03's one-line change to `validate_item` already fixes it and a separate E-item would have no code to carry. Option (b) is actively wrong: a basename is the defect, and `aw check` is subject to the same Section 8.5 repo-relative requirement. Option (c) is what the plan did and is what PR-A01 exists for: an output change on a command the plan never mentions, with no validation item that would notice | yes |
| D-2 | PR-A03: the baselines drifted 45 tests. Update the numbers, or change the comparison? | CHANGE THE COMPARISON to failing node ids against a freshly captured baseline; keep both counts as history | (a) Update `3246` to `3291` and `269` to `272`; (b) leave them and rely on the executor noticing | Option (a) buys one lane's accuracy and rots identically, and this plan executes after further merges; the same defect has now appeared in three plans in this sweep, which is evidence the pattern rather than the number is the problem. The workflow's re-derivation convention addresses exactly this: state the property (green before the change) and re-derive at execution | yes |
| D-3 | Should E-04 also pin the CROSS-LAYOUT duplicate case, which the plan does not mention? | YES, added as a required E-04 case, with F-10 recording the measurement | (a) Leave E-04 with the two-status case only; (b) record F-10 as evidence without requiring a test | `_iter_items` iterates `BACKLOG_ROOTS = (".agents/backlog", ".aw/records/backlog")`, so a cross-layout duplicate is reachable, and the legacy `.agents/` segment is PRECISELY where F-02's rejected `relative_to` mechanism would have raised `ValueError`. So this case is the one that most directly validates the plan's central mechanism choice, and it was untested. Option (b) leaves the property true today and unguarded tomorrow, which is the same gap F-06 documents for the duplicate rule itself | yes |
| D-4 | The reused `specs.drift_location` truncates at a BARE `.agents/` prefix. Is that safe enough to depend on? | YES, verified over four adversarial roots; no change requested | (a) Ask for a stricter segment match (`/.agents/backlog/`); (b) accept it untested | The plan depends on a helper it does not own and whose truncation rule is coarser than it looks, so the claim needed establishing rather than inheriting. Probed a temp root that itself contains `.agents/`, a `.agents-scratch` sibling component, a `my.agents` component, and a doubled records segment: each truncates at the intended segment with no false early cut, because the search is for the literal `.agents/` with its leading dot. Option (a) would edit a file outside `Scope-Paths` that another tree depends on, for a hazard that does not reproduce | yes |
| D-5 | PR-A05: the gate needs a stop directive for an absent `specs.drift_location`. Does the 2026-09-01 anti-stop ruling forbid it? | NO: include it, scoped to that one condition, and keep make-and-then-JUSTIFY for the scope case | (a) Omit every stop directive; (b) add a stop for out-of-scope edits too | The ruling forbids a stop over a SCOPE question and expressly preserves one for "a prerequisite whose symbols are absent". This plan's entire mechanism is a delegation to one function it does not own, and F-02 records that the obvious local substitute is the hazard being avoided, so improvising past its absence is the failure mode. Option (b) is the wording the ruling exists to stop | yes |
