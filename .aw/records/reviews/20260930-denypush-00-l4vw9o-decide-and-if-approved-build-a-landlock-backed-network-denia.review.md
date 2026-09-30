# Review findings: plan l4vw9o

- Subject-Id: l4vw9o
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (MEDIUM, fixed), PR-602 (MEDIUM, fixed), PR-603 (MEDIUM, fixed), PR-604 (LOW, fixed), PR-605 (LOW, fixed)

## Round 1

Reviewed at HEAD `45e38499` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:` bullet reads
`orchestrator`, so the `IPD-S407` typed child-row check DOES apply here; the linter reports no `IPD-S407`
violation at either checkpoint, so the bounded repair loop was never entered. All four Set members lint
`conforming`.

I RE-MEASURED THE SET'S ENTIRE TECHNICAL PREMISE FROM THE KERNEL UP rather than reading research
`uq4y6q`, because every claim in the Set descends from it and a decision plan resting on an unverified
measurement is worth nothing. It holds, completely:

- This host reports Landlock ABI 4 (`landlock_create_ruleset(NULL, 0, VERSION)` returns 4; kernel
  6.8.0-142-generic), so network rules are available and Order 02's real denial test will not skip here.
- A ruleset handling `LANDLOCK_ACCESS_NET_CONNECT_TCP` with NO net rule refuses every outbound connect
  with `EPERM(13)`, which is the fail-closed default research `uq4y6q` describes.
- A ruleset allowing ONLY port 443 permits `1.1.1.1:443` AND `8.8.8.8:443` (two distinct hosts, same
  port, both allowed) while refusing `1.1.1.1:22`. That is the two-sided denial plus the PORT-GRANULAR,
  ADDRESS-BLIND property on which the Set's whole decision turns, measured rather than inherited.
- `/usr/include/linux/landlock.h` confirms `struct landlock_net_port_attr` is `{allowed_access, port}`
  with NO address field, which is the structural reason the granularity limit is not fixable by a better
  rule.

So the Set's conclusion is correct: kernel TCP denial is real and cheap, and it cannot separate a git
remote from the model API on 443. The honest split this Set ships is the right shape.

THE FIVE CODE-LEVEL COMPLETION CRITERIA ARE EACH TRUE TODAY, verified against the tree rather than
assumed: `ACTION_CLASSES` is `(ACTION_READ_ONLY,)`; `len(run_evidence.RUN_FINDING_CODES)` is 12 with no
`NO-PUSH`-shaped code; `supports_deny_push` and `CAP_DENY_PUSH` are absent from the dataclass, the module
and `__all__`; `DenyPushRemovedTests` is live in `tests/test_host_capability_extension.py` with its
assertions intact; and spec 5.2's requirement bullet "deny push-capable network routes and withhold
remote credentials" is present at its landing site. The child table matches reality: all three children
exist, their `- Id:`, `- Order:` and `- Item-Dependencies:` (`none`, `executed:x2dwu5`, `executed:pi3bk8`)
match the table exactly, and the dependency chain is a straight line. The orchestrator carries
ORCHESTRATION ONLY and I checked that properly rather than taking its word: each of its three E-items
confirms one child reached `executed`, and every Completion criterion maps onto a specific child E-item
(5.2 to child 01 E-03, the capability to child 02 E-03, the absent caps to child 02 E-07, `ACTION_CLASSES`
to child 02 E-03 and child 03 E-03c, the 12 codes to child 03 E-03b, `sv9ce4` to child 03 E-01, the sweep
to child 03 E-04). Nothing is parked on the parent, so retiring it on child completion is honest and the
runner's orchestrator coverage gate should pass it.

THE CARRIERS ARE UNUSUALLY GOOD AND I VERIFIED BOTH. `sv9ce4` is `open`, ungated, and worded as
host-granular filtering rather than push denial. `wcbpqf` is `open` and is the best decision carrier I
have reviewed: it holds all THREE maintainer decisions the Set raises (this plan's OQ-01, child 02's name
question, child 01's bullet-split question), states why each is the human's rather than an agent's,
carries the measured context, and specifies a close procedure including that a rename must be applied to
all four plans together. The note explaining that `sv9ce4` was filed AT AUTHORING TIME rather than by
Order 03 is exactly the right call, and Order 03 verifying rather than filing it is the correct inversion.

THE ONE REAL GAP: A SECOND SPEC SITE NOBODY OWNS. `grep -c "deny push-capable"` on spec `25kzda` returns
**2**. The first is 5.2's requirement bullet, which all three children know about and each is required to
leave byte-unchanged. The second is Section 6.1 limit 4, "No-push and hook guarantees require control of
execution", whose body says the design "requires the engine to own process launch, deny push-capable
network/credentials, own commits, and record the commit gateway". Measured: NO plan in this Set mentions
Section 6.1, limit 4, or that heading anywhere. The consequence is a reader-facing inconsistency the Set
could ship: an amended 5.2 saying denial is MEASURED beside an untouched limit 4 saying the design
REQUIRES a control, with nothing reconciling them. I resolved this as "do not amend, but require the
judgement" rather than adding a fourth child, because limit 4 is ALREADY ACCURATE (it says the design
requires these controls and that a host lacking them must fail closed, which is exactly what this Set
confirms), and editing an honest-limits entry to mention a port probe would be the overclaim the Set
exists to avoid. Order 03's audit grep would surface the hit, but nothing told that executor it was an
expected second hit or who owned the judgement, so an audit reporting one hit would have looked clean.

TWO CHECKS THAT WOULD HAVE PASSED WITHOUT THE SET RUNNING. V-03 required pasting `aw attention` showing
`oq05nc` "no longer `open`"; measured, `oq05nc` is ALREADY `graduated` (graduated when this Set was
authored, per its own history), so that assertion is true at HEAD and proves nothing about whether the
Set executed. Retargeted onto the two carriers, which is the property actually worth checking. And V-02's
`aw host capabilities opencode` evidence asked for the capability row without asking for the probe NOTE,
which is the entire mitigation OQ-01 rests on, nor for the negative half (no `deny_push`, no `REFUSED`),
which is where a silently acquired gate would appear.

ONE HAZARD I DEMONSTRATED ON MYSELF, now recorded in the plan because it bears directly on child 02's
probe design. Re-deriving the measurement I first set `handled_access_net` to `1 << 0` and observed every
outbound connect refused with `EPERM(13)`, including the port I had explicitly ALLOWED. Read one-sidedly
that looks like a working boundary. It was not: `1 << 0` is `LANDLOCK_ACCESS_NET_BIND_TCP` and
`CONNECT_TCP` is `1 << 1`, so the ruleset handled a right my test never exercised and the total denial
came from handling-with-no-matching-rule. This is exactly the "jail too tight" shape child 02's E-02
already enumerates as one of three distinguishable exit codes, which is a point in that plan's favour;
what the incident establishes is that the arm is load-bearing and must not be simplified away, and that
the Set's convention of naming the constant SYMBOLICALLY (every child and the research do; none carries a
numeric bit) is what kept this error out of the plans.

NO SPEC AMENDMENT IS OWED BY THIS ORCHESTRATOR and its `Scope-Paths` correctly declares only its own
file, since every spec edit belongs to a child that declares it.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Architecture (an unowned contract site) | `grep -c "deny push-capable"` on spec `25kzda` returns 2: line 1169 (5.2's requirement bullet) and line 1471 (Section 6.1 limit 4, "No-push and hook guarantees require control of execution", whose body says the design "requires the engine to ... deny push-capable network/credentials"). `grep` for `6.1`, `limit 4`, `No-push and hook` across all four Set plans returns NOTHING | **The spec asserts push denial in TWO places, the Set amends one, and no plan mentions the other.** The Set could therefore ship an amended 5.2 saying denial is MEASURED beside an untouched honest-limits entry saying the design REQUIRES a control nothing provides, leaving a reader to reconcile them. Order 03's audit grep would surface the hit, but nothing tells that executor it is an expected SECOND hit or who owns the judgement, so a one-hit audit would read as clean | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New Cross-IPD row states the measured two-hit count, quotes limit 4, records that NO child mentions it, and resolves it as DO NOT AMEND with the reason (limit 4 is already accurate; editing it to cite a port probe would be the overclaim the Set exists to avoid). Order 03's obligation is now the JUDGEMENT: V-03 requires two hits each judged and states that an audit reporting one hit does not satisfy the item. A Completion criterion records the deliberate non-amendment, and the child-table row for Order 03 names it. No fourth child added, since no edit is owed |
| PR-602 | MEDIUM | IN-SCOPE | E. Testing (a validation item that passes without the Set running) | `aw find backlog oq05nc` reports `graduated` at HEAD, before any child executes; its own history records it graduated when this Set was authored. `aw attention` shows both `sv9ce4` and `wcbpqf` present | **V-03 requires pasting `aw attention` showing `oq05nc` "no longer `open`", which is already true and therefore proves nothing about whether the Set executed.** A validation item satisfied by the pre-existing state is the vacuous-pin shape, and it sits on the orchestrator's final check where it is least likely to be questioned | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-03 retargeted onto the two CARRIERS (`sv9ce4` as residual, `wcbpqf` as decision), which is the property worth checking at Set end, and explicitly forbids asserting the `oq05nc` status as evidence, stating the measured reason it would pass vacuously |
| PR-603 | MEDIUM | IN-SCOPE | B. Security / F. UX (the mitigation is unverified by the item that verifies the capability) | The plan's own OQ-01 rests the over-read mitigation on "the name and ... the required `probe_notes` limit", and Order 03's audit checks the note; but the orchestrator's V-02, which is where the capability itself is verified, asked only for "the new capability row with its probe note" | **V-02 verifies the capability shipped without verifying the thing that makes shipping it safe.** The row is what an operator over-reads; the note is the entire mitigation. V-02 also omitted the NEGATIVE half (no `deny_push`, no `REFUSED` row), which is precisely where a capability that silently acquired a gate would surface, and `ACTION_CLASSES` alone would not show it | C:Low; U:Medium; S:Medium; F:Low; Overall:Medium | FIXED | V-02 now requires the probe note QUOTED and confirmed to state the port-granularity limit, with the reason (the row is over-read, the note is the mitigation), plus an explicit statement of the negative half: the same output contains no `deny_push` and no `REFUSED` row |
| PR-604 | LOW | IN-SCOPE | D. Anti-regression (a probe-design hazard, demonstrated) | Reviewer's own re-derivation: with `handled_access_net = 1 << 0`, ALL connects returned `EPERM(13)` including the explicitly allowed port, which reads as working enforcement. `/usr/include/linux/landlock.h`: `LANDLOCK_ACCESS_NET_BIND_TCP (1ULL << 0)`, `LANDLOCK_ACCESS_NET_CONNECT_TCP (1ULL << 1)`. Corrected to `1 << 1`: allowed 443 succeeds to two hosts, 22 refused | **A one-sided network probe can report total denial for the wrong reason and look like a working boundary.** Handling a right the test never exercises denies everything, which is indistinguishable from enforcement unless the ALLOWED side is also required to succeed. Child 02's E-02 already enumerates this as "allowed-connect-denied (jail too tight)", so the plan is right; what was missing is any record that the arm is load-bearing rather than defensive thoroughness, and that the Set's symbolic-constant convention is what kept the error out of the plans | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | New Cross-IPD row records the incident, the two constants, the corrected result, and the two consequences: Order 02's allowed-connect-must-succeed arm must not be simplified away, and no plan may state the bit numerically (every child and the research already name it symbolically, which is now recorded as load-bearing) |
| PR-605 | LOW | IN-SCOPE | G. Plan executability (the decision the Set exists to serve, unsupported by evidence at the gate) | The gate paragraph tells a reviewer to push hardest on OQ-01 but supplies no measurement there; the evidence sits in research `uq4y6q`, which the maintainer would have to open separately | **The plan asks the maintainer for its central decision without putting the decision's factual basis where the decision is made.** OQ-01 is the whole point of backlog `oq05nc` and the gate correctly identifies it as the one place tests cannot help, which makes the absence of the re-derived numbers at that point the gap | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate paragraph gains a "what review established" block with the re-derived ABI, the fail-closed default, and the address-blind result, stating plainly that the measurement favours NEITHER answer (it establishes the capability would report something true and partial) and that `wcbpqf` carries the decision durably, so declining Orders 02 and 03 loses nothing written down |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-601: spec `25kzda` Section 6.1 limit 4 also asserts push denial and no child owns it. Amend it, add a child, or require a judgement? | REQUIRE THE JUDGEMENT in Order 03's audit; amend nothing; add no child | (a) Amend limit 4 in child 01 beside the 5.2 amendment; (b) author a fourth child owning Section 6.1; (c) leave it entirely unmentioned, as authored | Read limit 4 before deciding: it says the DESIGN REQUIRES the engine to deny push-capable network and credentials and that a host lacking those controls must fail closed. That is TRUE and this Set CONFIRMS it; nothing measured here contradicts a word of it. So option (a) would edit an accurate honest-limits entry to mention a port probe, which is the overclaim the Set exists to avoid and would also breach the Set's own rule that no artifact may read as a push-denial guarantee. Option (b) spends a whole child on an edit that should not happen. Option (c) is the finding: the hit would appear in Order 03's grep with nothing marking it expected, so a one-hit audit reads as clean and the second site is missed silently. Requiring the judgement is the only option that makes the non-amendment VISIBLE and CHECKED | yes |
| D-2 | PR-602: `oq05nc` is already `graduated`. Retarget V-03's attention check, or drop it? | RETARGET onto the two carriers (`sv9ce4`, `wcbpqf`) | (a) Drop the `aw attention` evidence from V-03 entirely; (b) keep it and note that `oq05nc` is expected to be already graduated | Option (b) preserves a check that cannot fail, which is the exact vacuity this repository keeps having to remove; noting that it passes trivially does not make it evidence. Option (a) throws away the one Set-end property genuinely worth confirming: that the residual carrier and the decision carrier are both still live and visible in the attention view, which is the mechanism by which the unbuilt half survives the Set closing. That is checkable, can genuinely fail (a carrier could be closed or parked by then), and is what the Set's own "THE CARRIER OUTLIVES THE SET" invariant claims | yes |
| D-3 | PR-604: should the reviewer's own mis-set-bit incident be recorded in the plan, or just fixed in the reviewer's script? | RECORD it as a Cross-IPD row | (a) Say nothing, since the error was the reviewer's and the plans were already correct; (b) add it only to the review record, not the plan | Option (a) is tempting precisely because the plans got it right and my probe got it wrong, so there is no plan defect to report. But the incident is EVIDENCE ABOUT THE SUBJECT MATTER, not about me: it demonstrates on this Set's own mechanism that a one-sided network probe reports total denial for the wrong reason and is indistinguishable from enforcement. That converts child 02's three-exit-shape requirement from apparent thoroughness into a measured necessity, and it converts the symbolic-constant convention from a style habit into a load-bearing rule. Option (b) puts it where the executor of child 02 will not read it. A reviewer's own near-miss on the exact hazard a plan guards against is worth more in the plan than in the review record | yes |
| D-4 | Does this orchestrator carry work no child covers, which would make its runner retirement dishonest? | NO; it is pure orchestration and needs no additional child | (a) Conclude the Completion criteria and Cross-IPD validation constitute parent-only work and demand a new child to own them | I mapped every Completion criterion onto a specific child E-item before answering (5.2 to child 01 E-03; the capability to child 02 E-03; absent caps to child 02 E-07; `ACTION_CLASSES` to child 02 E-03 plus child 03 E-03c; the 12 codes to child 03 E-03b; `sv9ce4` to child 03 E-01; the sweep to child 03 E-04), and each of the parent's three E-items is a pure state-on-disk confirmation. Option (a) would be the blunt "no items on a parent" misreading `AGENTS.md` explicitly warns against: an orchestrator SHOULD carry a child checklist, and deleting it causes the lost work the checklist prevents. The one edit review added to the parent (the limit-4 judgement) was assigned to Order 03 rather than parked here, precisely to keep this answer true | yes |
