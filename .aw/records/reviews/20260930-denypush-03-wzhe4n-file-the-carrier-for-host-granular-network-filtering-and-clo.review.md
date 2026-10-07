# Review findings: plan wzhe4n

- Subject-Id: wzhe4n
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (HIGH, fixed), PR-1002 (MEDIUM, fixed), PR-1003 (MEDIUM, fixed), PR-1004 (MEDIUM, fixed), PR-1005 (LOW, fixed), PR-1006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff -q` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` with zero findings after revision. This plan's
own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row check does NOT apply
and the bounded repair loop was never entered.

I RAN THIS PLAN'S OWN AUDIT rather than reading it. That is the only way an audit plan can be
reviewed: its deliverable is a set of checks, and a check can only be judged by attempting it. Doing so
produced both serious findings, and they share one shape worth naming because it is the failure mode
this plan class is uniquely prone to: A CHECK TOO NARROW TO FIND ANYTHING, REPORTED HONESTLY. Neither
defect would have made anything go red; both would have produced a clean audit that proved nothing.

### PR-901: the audit's own grep decided its thoroughness

E-03(d) is the Set's ONLY defense against the overclaim the orchestrator's Cross-IPD section describes,
where "each child is individually honest while the COMBINATION is where an overclaim would appear". It
said: "grep the spec and the module docstring for any sentence asserting push denial as an available
guarantee". It named no search term. Measured on the current spec, the term decides the result:

```text
deny push-capable      2
push denial            3
no-push                7
deny_push              6
push                  28
```

An executor free to choose was therefore choosing how thorough the Set's honesty gate would be, and the
cheapest choice is the narrowest one. E-03 now fixes all five terms, requires each count stated, and
designates the bare-`push` run a completeness sweep whose purpose is to surface a sentence the other
four miss.

### PR-902: the spec's second push-denial site was delegated here and not carried

`grep -c "deny push-capable"` on spec `25kzda` returns 2. The first is 5.2's requirement bullet, which
Order 01 amends and which every plan in the Set knows about. The second is Section 6.1 limit 4,
"**No-push and hook guarantees require control of execution.**", whose body says the design "requires
the engine to own process launch, deny push-capable network/credentials, own commits, and record the
commit gateway".

The orchestrator `l4vw9o` states in its Cross-IPD section that "Order 03's E-03 and V-03 now name it"
and its own V-03 fails an audit "reporting one hit". Measured: this plan mentioned Section 6.1, limit 4,
or that heading ZERO times. So the parent had already delegated the obligation here and recorded it as
discharged, while the child did not carry it. That is exactly the mechanism by which the second site
gets missed, and the consequence is concrete: the Set could amend 5.2 to say denial is MEASURED while
limit 4 continues to describe the design as requiring a control nothing provides, leaving a reader to
reconcile them. E-03 and V-03 now name limit 4, fix its required judgement ("requirement/limit,
acceptable, not an available-guarantee claim"), and record the DO-NOT-AMEND resolution with its reason.

### PR-903: the acceptance bar was unreachable

E-04's Expected outcome read "All checks pass with pasted output". Two of the five gates it prescribes
cannot pass on this repository. Measured on a clean tree before this Set runs:

```text
aw check                   exit 1, 60 findings
aw research index --check  exit 1, 96 findings
aw backlog check           exit 0
aw sanitize --agent        exit 0
```

All 96 research findings are `adopted-without-consumer` on ARCHIVED docs, and none names `uq4y6q` or
`denypush`; the 60 `aw check` findings are dominated by `check.plan-spec-link-missing` (34) and
`check.ipd-uncarried-obligation` (10) across the pending corpus. So 156 findings this Set does not own
stood between the executor and its stated bar. The two available responses were both bad: report a
blocked run over someone else's backlog, or soften the criterion and claim a pass. In the plan whose
entire purpose is to be strict, teaching an executor to soften a criterion is the worst available
outcome. E-04 and V-04 now judge those two gates by DELTA (no new finding naming any artifact this Set
touched, counts RE-DERIVED at execution because they are live populations) while holding the other two
to a genuine zero exit, where a nonzero result is a real regression.

### What I verified and deliberately left alone

Reviewing an audit means checking the checks that are RIGHT as carefully as the ones that are wrong,
because a correct check removed is a regression. These were each run and are sound:

- Carrier `sv9ce4`: `Status: open`, `Priority: low`, `Work-Kind: feature`, NO `Blocks-Release:` line,
  summary names host-granular filtering and not push denial, body cites research `uq4y6q`. So E-01's
  expected state is the actual state, and the VERIFY-not-file arrangement is the stronger one.
- `aw attention` contains `sv9ce4` (and `wcbpqf`), so V-01's behavioral proof of visibility works.
- `len(RUN_FINDING_CODES)` is 12 and `validate_finding_table()` returns
  `EvidenceValidationResult(ok=True, findings=())`, so E-03(b) is executable as written.
- 5.2's requirement bullet appears exactly once and the 5.6 packet example's `"deny_push"` exactly
  once, so V-02's byte-unchanged greps are well-founded.
- F-3's quotation of `4h7tt0` ("no sandbox is owed") is verbatim, and `oq05nc` does contain the
  "DURABLE CARRIER" phrasing F-3 attributes to it.
- `oq05nc` is already `graduated`, so OQ-02's resolution is correct and the Deferred row declining to
  close it is right.
- Both open questions were already `resolved` with sound reasoning; I verified their bases rather than
  re-deciding them, and OQ-01's "not independently useful" test for one-carrier-versus-two holds.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | E. Testing / G. Plan executability | Plan E-03(d) "grep the spec and the module docstring for any sentence asserting push denial", naming no term; measured hit counts on the current spec: `deny push-capable` 2, `push denial` 3, `no-push` 7, `deny_push` 6, bare `push` 28 | THE AUDIT'S OWN GREP DECIDED ITS THOROUGHNESS. Sub-check (d) is the Set's only defense against the combination-level overclaim the orchestrator describes, and an unnamed grep lets the executor pick the narrowest term and pass honestly. The spread is an order of magnitude, so this is not a hypothetical difference. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 fixes all five terms, requires each count stated with judgements on the first four, and designates bare `push` a completeness sweep. V-03 requires all five counts pasted and re-derived rather than copied, since the spec is amended three times in this Set. F-7 records the measurement. |
| PR-902 | HIGH | UNDER-SCOPE | D. Invariants / G. Plan executability | `grep -c "deny push-capable"` on spec `25kzda` = 2 (5.2's bullet and Section 6.1 limit 4, "**No-push and hook guarantees require control of execution.**"); orchestrator `l4vw9o` Cross-IPD: "Order 03's E-03 and V-03 now name it", and its V-03 fails an audit "reporting one hit"; measured: this plan mentioned Section 6.1, limit 4, or that heading ZERO times | THE PARENT DELEGATED THE SECOND SITE HERE AND RECORDED IT AS DISCHARGED; THE CHILD DID NOT CARRY IT. The Set could therefore amend 5.2 to say denial is MEASURED while limit 4 keeps describing the design as requiring a control nothing provides, which is the reconciliation gap the orchestrator raised the row to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now names limit 4 with its quoted body, fixes the required judgement ("requirement/limit, acceptable, not an available-guarantee claim") and records the DO-NOT-AMEND resolution and reason. V-03 requires the evidence to contain the words Section 6.1 limit 4 and fails a one-hit report. The gate's scope fence adds a negative constraint against amending it. F-8 records the measurement. |
| PR-903 | MEDIUM | IN-SCOPE | E. Testing / G. Plan executability | E-04 Expected outcome "All checks pass with pasted output"; measured on a clean tree: `aw check` exit 1 with 60 findings, `aw research index --check` exit 1 with 96 (all `adopted-without-consumer` on ARCHIVED docs, none naming `uq4y6q` or `denypush`), `aw backlog check` exit 0, `aw sanitize --agent` exit 0 | AN UNREACHABLE ACCEPTANCE BAR. 156 pre-existing findings this Set does not own sit between the executor and "all checks pass", so the honest responses are to report a blocked run over someone else's backlog or to soften the criterion and claim a pass. In the Set's strictness gate, teaching an executor to soften a criterion is the worst outcome available. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 and V-04 judge `aw check` and `aw research index --check` by DELTA (no new finding naming this Set's artifacts, counts re-derived at execution as live populations) and hold `aw backlog check` and `aw sanitize --agent` to a genuine zero exit where nonzero is a real regression. F-9 records the four measurements. |
| PR-904 | MEDIUM | IN-SCOPE | G. Plan executability | Scope check "`.aw/records/backlog/open` is written by E-01" against E-01's own first word, VERIFY, and a carrier filed at authoring time; `ipd_lifecycle` emits `declared-but-unmodified path needs a --scope-ack: <p>` | THE PLAN CONTRADICTED ITSELF ON WHETHER IT WRITES ITS OWN SCOPE PATH, and the contradiction surfaces at finalize as an unexpected `--scope-ack` demand on a clean run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The entry is deliberately KEPT (E-01's corrective branch needs it in scope) and the Scope check now states the path is expected unmodified, names the finalize demand verbatim, and gives the ordinary answer. The gate's scope fence repeats the expectation. F-10 records it. |
| PR-905 | MEDIUM | IN-SCOPE | E. Testing | Plan validation section: "`aw check` reports no new violations, including `check.from-backlog-dangling` (every plan in this Set carries `- From-Backlog: oq05nc`)" and "`aw research index --check` reports no drift"; measured: `check.from-backlog-dangling` reports ZERO rows, and the research checker reports 96 | TWO GATES CITED THAT PROVE NOTHING AS WORDED. The first names an already-clean rule, so asserting it passes is vacuous; the second states an outcome that is unachievable. Verified separately that all four Set plans DO carry `- From-Backlog: oq05nc`, so the underlying property is true and only the gate choice was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The validation section now records the zero-row measurement, redirects the assertion to the `release-gates` family (the spec carries `- Blocks-Release: next` and no plan here moves it), states the research checker's real pre-existing count, and reduces the research claim to the checkable one: that `uq4y6q` itself is clean after Order 01 sets `consumed-by: [x2dwu5]`, which resolves today. |
| PR-906 | LOW | IN-SCOPE | G. Plan executability | "Proposed changes" item 1 "File the host-granular filtering carrier"; E-01 "VERIFY, do not re-file"; Concern and Scope both say the carrier was filed at authoring time | THE ORDERED CHANGE LIST CONTRADICTED THE CHECKLIST IT SUMMARIZES, which is the section an executor skims first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 1 rewritten to VERIFY with the contradiction noted; items 3 and 4 updated to name the fixed search terms, both spec sites, and the delta judgement. |
| PR-907 | LOW | IN-SCOPE | E. Testing | `aw host capabilities opencode`: bare `grep -c REFUSED` returns 1 (the fresh-verifier note reads "a reused-identity run was REFUSED"), `grep -c 'REFUSED  '` returns 0 | AN AUDIT FALSE-POSITIVE WAITING TO HAPPEN. Sub-check (a) inspects that output for evidence nothing is gated; a bare `REFUSED` grep hits a probe note and would be reported as a gated action. In an audit whose job is accuracy, a false overclaim finding is the same defect pointed the other way. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now prescribes the two-space form with both measured counts and names the probe-note sentence that causes the bare hit. |
| PR-908 | LOW | IN-SCOPE | G. Plan executability | `aw ipd set reviewed` surfaced `check.lifecycle-transition-invalid` with `to-review -> draft`; the two 2026-09-29 history records were in oldest-first order while the section is newest-first | A LATENT HISTORY-ORDERING INVERSION, dormant until a new record made the pair the readable transition. Identical to the defect found in sibling plan `pi3bk8` this round, so it is a Set-wide authoring artifact rather than a one-off. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Records reordered newest-first; `check.lifecycle_transitions` reports zero findings for this plan afterwards. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-901: which search terms must sub-check (d) run, given the plan named none? | Fix five terms: `deny push-capable`, `push denial`, `no-push`, `deny_push`, and bare `push`, with the last as a completeness sweep. | Naming one canonical term (any single term misses sites the others catch, which is the defect); leaving it to executor judgement (that is the finding). | Measured each term's hit count on the current spec: 2, 3, 7, 6, 28. The spread is an order of magnitude, and the two known push-denial sites are both found by `deny push-capable` while `no-push` and `deny_push` reach the 4.2 retirement history and the 5.6 packet example that the narrow term does not. | yes |
| D-2 | PR-902: should this plan AMEND Section 6.1 limit 4, or record a judgement on it? | Record a judgement; DO-NOT-AMEND. | Amending limit 4 to mention the port probe. Rejected because limit 4 states the design REQUIRES these controls and that a host lacking them fails closed, which is what this Set confirms rather than changes; editing an accurate honest-limits entry to mention a partial mechanism would itself be the overclaim this plan exists to catch. | Orchestrator `l4vw9o`'s Cross-IPD section already resolved it DO-NOT-AMEND and assigned the recorded judgement to Order 03, and its V-03 demands two judged hits. I verified limit 4's text is accurate as it stands. | yes |
| D-3 | PR-903: how should a gate that exits nonzero over pre-existing findings be judged? | By DELTA: finding count plus rule breakdown before and after, requiring no new finding that names an artifact this Set touched; counts re-derived at execution. | Requiring a zero exit (unreachable, 156 findings not owned by this Set); dropping the two gates (loses the regression detection they do provide). | Measured all four gates on a clean tree: `aw check` exit 1 / 60, `aw research index --check` exit 1 / 96 with zero `uq4y6q`/`denypush` hits, `aw backlog check` exit 0, `aw sanitize --agent` exit 0. The two that pass today are held to zero precisely because a nonzero there IS attributable. | yes |
| D-4 | PR-904: remove `.aw/records/backlog/open` from `Scope-Paths` since E-01 only verifies, or keep it? | Keep it, and record that a `--scope-ack` is the expected finalize answer. | Removing it. Rejected because E-01's corrective branch (`aw backlog set` on drift, or re-filing a removed item) would then be an out-of-scope edit requiring a `--scope-reason`, which is the worse of the two finalize answers and penalizes the executor for doing E-01's job. | Verified the finalize behavior in `ipd_lifecycle`, which emits `declared-but-unmodified path needs a --scope-ack: <p>` for a declared path left untouched, and `_parse_scope_ack_flags` accepting `<path>[=<note>]`. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 was required.
OQ-01 and OQ-02 were already `resolved` by the author; I verified their bases (`oq05nc` is `graduated`;
the two carrier halves are not independently useful) rather than re-deciding them, so neither produced
a Decisions row. No finding was left `OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed
under Step 4 and none was written.

### Verification performed at review

- `diff -q` lane input against the tracked plan: identical, so no pre-review snapshot.
- `aw ipd lint --phase author --agent`: `conforming`, exit 0, zero findings (before semantic review).
- `aw ipd lint --phase review-finalize --agent`: `conforming`, exit 0, zero findings (after revision).
- Carrier `sv9ce4` front matter read in full: `open`, `low`, `feature`, no `Blocks-Release:`, summary
  names host-granular filtering, body cites `uq4y6q`.
- `aw attention`: contains `sv9ce4` and `wcbpqf`.
- Spec term counts: `deny push-capable` 2, `push denial` 3, `no-push` 7, `deny_push` 6, `push` 28;
  both `deny push-capable` sites read in context (5.2 bullet; Section 6.1 limit 4).
- `len(RUN_FINDING_CODES)` = 12; `validate_finding_table()` = `EvidenceValidationResult(ok=True, findings=())`.
- Gate exits on a clean tree: `aw check` 1 / 60 findings (rule breakdown captured), `aw research index
  --check` 1 / 96 findings with 0 naming `uq4y6q` or `denypush`, `aw backlog check` 0, `aw sanitize
  --agent` 0.
- `aw host capabilities opencode`: bare `grep -c REFUSED` = 1, `grep -c 'REFUSED  '` = 0,
  `grep -c deny_push` = 0.
- All four Set plans carry `- From-Backlog: oq05nc`; `check.from-backlog-dangling` reports 0 rows;
  `check.plan-spec-link-missing` named this plan (advisory, `info`) and is cleared by the added
  `- From-Spec: 25kzda`.
- `oq05nc` confirmed `graduated`; `x2dwu5` resolves, so Order 01's `consumed-by` will not dangle.
- `check_engine.check_lifecycle_transitions` reports zero findings for this plan after PR-908.
- `4h7tt0`'s "no sandbox is owed" and `oq05nc`'s "DURABLE CARRIER" quotations confirmed verbatim.

No production code, test, or configuration file was modified by this review. The only file changed is
the plan, plus this record.

## Round 2

Re-review after the plan returned to authoring (2026-10-06) and back to `to-review` (2026-10-07). Round 1's findings (PR-901..PR-908) all remain fixed in the plan text.


Reviewed in an isolated review lane at HEAD `112df4db1`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author` and `--phase review-finalize` are both `clean`.
`- Kind: child`.

Re-measured state. `x2dwu5` (Order 01) is executed. `pi3bk8` (Order 02, this plan's dependency) and `l4vw9o`
(Order 00) are `reviewed`. Spec `25kzda` still has 2 `deny push-capable` hits (5.2 bullet, line 1216; 6.1 limit 4,
line 1559), and both are byte-intact. No `deny`-named field exists on `HostSandboxCapabilities`.
`len(RUN_FINDING_CODES) == 12`. `aw backlog check` exits 0. `aw attention` shows `sv9ce4` as `native_status: open`,
`attention_class: ready`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | IN-SCOPE | Rubric G / A (carrier state model) | `sv9ce4` front matter `- Graduated-To: netnsfilter`; history "graduated: 2j4pd0, m0kl28, nxh5s4, rozdkp, wn956n" (2026-10-01) and then back to `open` (2026-10-06); E-01 required "still `open`" and offered "if the item was closed ... re-file it". | The carrier now has a successor Set. When `netnsfilter` re-graduates or completes, `sv9ce4` legitimately leaves `open`, and E-01 as written would have an executor RE-FILE a duplicate carrier and fork the obligation away from the Set building it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now defines "live" as `open`, `graduated` with `Graduated-To: netnsfilter`, or `done` with that Set executed, and re-files only on removal or a close with no handoff. V-01 accepts all three states. |
| PR-1002 | MEDIUM | UNDER-SCOPE | Spec sync (concurrent amender) | `wn956n` E-02: "Amend spec `25kzda` 5.2 to record that the push-denial requirement now has a PARTIAL and probed answer"; there is no edge between the Sets. | Two Sets amend the same spec section. Without a re-read, this plan's carrier sentence could contradict `netnsfilter`'s amendment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires re-reading 5.2 at execution and wording the sentence consistently with whatever is there. No edge is added, because the runner isolates and merges. |
| PR-1003 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable check) | (e) required "none reintroduces `supports_deny_push`". Measured hits: `pi3bk8` 8, `l4vw9o` 4, this plan 2, `run_evidence.py` retirement comment 1, all of them mentions. | A zero-hit reading can never pass, which pushes an executor toward editing records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (e) now judges each hit as `definition` or `mention`, plus a behavioral `dataclasses.fields(HostSandboxCapabilities)` check. E-03's "four checks" is corrected to "five". |
| PR-1004 | MEDIUM | IN-SCOPE | Evidence accuracy (stale prediction) | Required tests: "`uq4y6q` itself is clean after Order 01 sets `outcome: adopted`". Measured: `aw research index --check` reports `uq4y6q ... stale-state-to-promote` (record `status: todo`). | The predicted clean state is false now that Order 01 has executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The finding is classified as pre-existing (it predates this plan) and named as the one tolerated `uq4y6q` line in Required tests and V-04. Promotion stays out of scope, with a scope-reason route if needed. |
| PR-1005 | LOW | IN-SCOPE | Internal consistency | OQ-02: "E-01 files a NEW item"; E-01 opens with "VERIFY, do not re-file". | A stale sentence contradicted E-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 now says E-01 verifies `sv9ce4`. |
| PR-1006 | LOW | IN-SCOPE | Honest wording | `sv9ce4` body: "`unshare -Urn --map-root-user true` failed ... Operation not permitted". Research `akmzyq` Finding 0 ("THE PREMISE CORRECTION"): the same command gives `rc=0` on another host. | E-01's "honestly worded" check did not know the carrier's hardness premise had been superseded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-01 now record the `akmzyq` correction and append a note if the item is still `open`. They do not rewrite the dated history. OQ owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan depend on `netnsfilter` (`wn956n`) for the 5.2 edit? | No edge; re-read at execution. | Add `executed:wn956n`: rejected, because it would block a low-risk records plan on a five-plan security Set, and the runner already merges same-file edits. | AGENTS.md "The runners own ordering, isolation"; `wn956n` E-02. | yes |
| D-2 | What to do with the stale `uq4y6q` finding? | Classify it as pre-existing under the delta bar; promotion stays out of scope. | Add the research record to Scope-Paths and require promotion: rejected, because it widens a verification plan into curation that `aw research promote` owns. | `aw research index --check` output at review. | yes |
