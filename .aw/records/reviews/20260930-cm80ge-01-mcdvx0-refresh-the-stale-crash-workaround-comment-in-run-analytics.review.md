# Review findings: plan mcdvx0

- Subject-Id: mcdvx0
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `eeb13f6c`. The plan file was committed and unmodified
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` after revision, including the new `E-04`/`V-04` pair. The
plan is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE PLAN IS UNUSUALLY WELL MEASURED AND ITS CENTRAL JUDGEMENT IS RIGHT. I re-drove every finding
rather than trusting it, and the plan's best contribution survives scrutiny intact: it REFUSED the
replacement rationale that both of its own carrier items proposed, having measured that rationale
false. That is the difference between fixing a stale comment and replacing one confident falsehood
with another.

Reproduced independently:

- F-01. The documented crash does not occur. `render_summary(..., context=OutputContext(mode=AGENT,
  fields=['outcome']))` returns
  `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"ok","exit":0,"total":3,"emitted":2,"omitted":1,"complete":false}`.
- F-02. `_PRESERVED_FIELDS` is `['applied','cmd','complete','emitted','exit','kind','omitted','outcome','schema','total','verified']`
  and `filter_record_fields` uses it, so the comment's citation of `_MANDATORY_FIELDS` names the
  superseded constant.
- F-03. The counts survive EVERY projection (`fields=['cmd']`, `fields=['total']`, and no context all
  retain `total`/`emitted`/`omitted`), so the counts cannot be what distinguishes the two calls. Both
  carrier items proposed exactly that rationale and both are wrong.
- F-04. `'next' in _PRESERVED_FIELDS` is `False`; `fields=['cmd']` with a `next_cmd` set drops `next`
  while `fields=['next']` and the no-context call retain it. I ALSO checked the half the plan did not
  state explicitly: the production call really does pass `next_cmd=result.next_command or None`, and
  `run_analytics_query` sets `next_command` exactly `if omitted:`, so the rationale is live rather
  than hypothetical.
- F-05, F-06, F-07, F-09. All hold. `gygujf` E-04 hands this work to `cm80ge` verbatim ("the comment
  block above it is now partly stale, which is `cm80ge`'s work and not this plan's"), so the plan is
  the intended carrier. `o8vgss` carries no `- Blocks-Release:`, and its `Work-Kind` is `chore`, so
  E-02's close is legitimate; I confirmed the prescribed command succeeds under `--dry-run` and left
  the item untouched.
- `docs/cli-agent-protocol.md` is correct post-`gygujf` as the plan's third Deferred row claims: its
  `--fields` bullet names the four additionally retained fields explicitly.

TWO MEDIUMS, BOTH OF WHICH WOULD HAVE COST AN EXECUTOR REAL TROUBLE.

THE FIRST IS AN UNREACHABLE GATE (PR-001). E-03 required the bare suite at or above `3387 passed,
2 skipped` "with no new failure". The suite is NOT green here: it reports `1 failed, 3457 passed,
2 skipped`, and the failure is the local-versus-UTC history-date skew in
`test_release_exempt_setter_roundtrip_and_parity`, which is red for the part of every day when the
machine's local date and the UTC date differ (`TZ=UTC` turns it green). It is filed three times as a
release-blocking bug, belongs to another party, and cannot be affected by a comment in
`run_analytics_cli.py`. An executor holding the authored bar faces two bad options: refuse to finalize
a correct change, or "fix" a co-worker's gated test to go green, which the shared-checkout rule
forbids outright. The bar is now an unchanged named failure SET against a baseline re-derived at
execution. The stale number is withdrawn in both directions, since the pass count has also RISEN as
other lanes landed tests.

THE SECOND IS A MISSING PIN THE PLAN ARGUED ITSELF OUT OF (PR-002). The plan correctly observes that
P16 forbids asserting comment text, then generalizes to adding no test at all. That conflates the
comment's TEXT with the PROPERTY the text asserts, and the property is pure observable output: this
call keeps `next` on a bounded answer where a projected one loses it. I demonstrated rather than
argued it, driving the real call path:

```
fields=None      summary has 'next' = True   complete=False omitted=3
fields=['cmd']   summary has 'next' = True   complete=False omitted=3
same record via render_summary(..., context=OutputContext(fields=['cmd']))  ->  'next' = False
```

So an assertion passes as shipped and fails under precisely the mutation the plan's own Goal section
says it fears (a later maintainer "correcting" the call to pass `ctx`). Without it, the comment's
central claim is defended only by this one commit's diff review. E-04 adds that test with a MANDATORY
falsifier demonstration, and V-04 refuses it without one. The Deferred row and the conventions bullet
are narrowed from "no test" to "no comment-text tripwire", which is what P16 actually says.

I DID NOT widen this plan further. Three things I checked and deliberately left alone: the `next`
projection defect itself (correctly carried by `kkjrqr`, which the plan filed at authoring and which
resolves), the `render_summary` call's shape (the plan's central constraint, and F-04 gives it a live
justification), and the protocol document's "safe to pass on any command" framing (owned by `kkjrqr`
as candidate fix (c), not duplicated here).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (testing/verification); G (live-artifact criteria) | plan E-03 second check and F-08; `agent_workflows/backlog.py` (`_reattach_history`, local `datetime.date.today()`) versus `agent_workflows/status_set.py` (`apply_status_change`, UTC); `tests/test_backlog.py` (`test_release_exempt_setter_roundtrip_and_parity`) | E-03's suite bar is UNREACHABLE and would block this plan on a defect it cannot cause. The bare suite is not green at this HEAD (`1 failed, 3457 passed, 2 skipped`); the failure is the pre-existing, TIME-DEPENDENT local-versus-UTC history-date skew, filed three times as a release-blocking bug (`fnb8pl`, `lq2w86`, `2wae2x`) and owned by another party. `TZ=UTC` passes. An executor holding the authored bar would either refuse to finalize a correct comment change or be tempted to fix a co-worker's gated test, which the shared-checkout rule forbids. The authored count is stale in both directions (3387 -> 3457). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's second check rewritten: the bar is now an UNCHANGED NAMED FAILURE SET against a baseline re-derived before any edit, with the pre-existing failure named, the two forbidden shortcuts named (fixing the test; setting `TZ`), and a risen pass count explicitly allowed. F-11 added with the measurement; F-08 marked superseded; V-03, the Required-tests section, the Proposed-changes list and the gate paragraph all reconciled. |
| PR-002 | MEDIUM | UNDER-SCOPE | E (testing/verification); D (anti-regression) | plan "Required tests / validation" first paragraph, the P16 conventions bullet, and the fourth Deferred row; `tests/test_run_analytics_cli.py` (`test_run_query_overview_agent_unchanged`) | The plan's "no test is added" reasoning over-generalizes. P16 forbids asserting COMMENT TEXT, which the plan rightly refuses; but E-01's new rationale is a claim about EMITTED RECORDS, and that is exactly what P16 requires a test to assert. Measured through the real call path: `next` survives `fields=None` and `fields=['cmd']` on a bounded query, and vanishes the moment the call is given a projecting context. So the property is pinnable with a demonstrable falsifier, and the mutation it catches is precisely the overreach the plan's Goal section fears. Left unpinned, the comment's central claim is defended only by this commit's diff review. The plan also already has a test module driving this module in agent mode, so there is no new harness cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-04 (one behavioral test asserting `next` present, its value, and `complete is False` with `omitted > 0`, reading no production source) and V-04 (requiring a demonstrated falsifier via a temporary `context=ctx` mutation, then revert). Declared `tests/test_run_analytics_cli.py` in `- Scope-Paths:`; bumped `Highest E allocated` to 04. Narrowed the Deferred row and the P16 conventions bullet from "no test" to "no comment-text tripwire"; F-12 added; Scope, Scope-check, Required-tests and the gate paragraph reconciled. |
| PR-003 | LOW | IN-SCOPE | G (live-artifact criteria) | plan F-08 row | F-08 asserts a green suite baseline as a stable fact and E-03 turns it into a bar. It was true when measured and is a drifting live population, so stating it as a bar rather than as context is the defect (the same class the repository's live-artifact convention names). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 marked SUPERSEDED BY F-11, retaining the authoring measurement as history with both numbers side by side so the drift is visible rather than silently overwritten. |
| PR-004 | LOW | IN-SCOPE | G (plan executability) | plan F-07 row; `tests/test_run_analytics_cli.py` | F-07's facts hold (no test pins the comment text; nothing else repeats the stale claim) but its conclusion "no test needs to change" was read as "no test should be added", and the row omits that `tests/test_run_analytics_cli.py` exists and already drives this module in agent mode. That omission is what made PR-002's gap invisible. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 corrected: conclusion scoped to EXISTING tests, and the Evidence column now names the test module and the sibling test whose fixture shape E-04 follows. |
| PR-005 | LOW | IN-SCOPE | G (plan executability) | plan Goal, Scope, Scope check, Required tests, Deferred, and the approval gate | The two substantive corrections above touch claims restated in several places, and a correction is not complete until every sibling that quotes the superseded wording is swept. Four sites still asserted "no test is added" or the withdrawn green bar, and the gate paragraph's comment-lines-only rule would have read as forbidding E-04's test file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swept all of them: `Scope` names the new test and its P16 reasoning; `Scope check` over-scope row names the test; Required-tests rewritten around the TEXT-versus-OUTCOME distinction with four validation legs; the conventions bullet narrowed; the gate paragraph now scopes comment-lines-only to the production file and warns not to read the pre-existing red test as this plan's failure. Grepped for `3387` and for "no test is added" to confirm no stale sibling survives. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The bare suite is red at base on a bug unrelated to this plan. Require green, exclude the test, or require an unchanged failure set? | REQUIRE AN UNCHANGED NAMED FAILURE SET against a baseline re-derived at execution, naming the pre-existing failure. | (a) Require green - rejected: unreachable for part of every day through no fault of this plan, and it pressures an executor into fixing a co-worker's release-gated test, which `AGENTS.md` forbids in a shared checkout. (b) Pin `TZ=UTC` for the suite run - rejected: that hides a live release-blocking bug behind an environment variable and would make this plan's evidence misrepresent the tree's real state. (c) Drop the suite check - rejected: it is the plan's only whole-tree signal that a comment edit did not break something, and dropping it loses the very assurance E-03 exists for. | measured `1 failed, 3457 passed, 2 skipped` at HEAD `eeb13f6c` versus `TZ=UTC` green on the narrowed run; local date `2026-09-30` against UTC `2026-10-01`; `fnb8pl`/`lq2w86`/`2wae2x` all `open` with `- Blocks-Release: next`; `AGENTS.md` shared-checkout rule. | yes |
| D-2 | The plan declines all tests under P16. Accept that, or add a behavioral test for the property the comment asserts? | ADD ONE behavioral test (E-04) with a mandatory demonstrated falsifier, and narrow the P16 refusal to a comment-TEXT tripwire. | (a) Accept "no test" as authored - rejected on measurement: the rationale is an emitted-output claim, so P16 REQUIRES testing it rather than forbidding it, and leaving it unpinned means the only defense of the comment's claim is one diff review, against a mutation the plan itself names as the thing it fears. (b) Require the test to fail first - rejected: it pins SHIPPED behavior that E-01 documents and does not change, so demanding a red-first run would demand a test lie; the falsifier requirement supplies the non-vacuity proof instead. (c) Pin `_PRESERVED_FIELDS`'s contents - rejected: that is a constant census, not an outcome, and `kkjrqr` already records that this contract must be tested on emitted records. | driven output of `_emit_query_agent` under `fields=None` and `fields=['cmd']` (both retain `next`) against `render_summary(..., context=OutputContext(fields=['cmd']))` (drops it); `tests/test_run_analytics_cli.py::test_run_query_overview_agent_unchanged` as the existing fixture precedent; GUIDING_PRINCIPLES P16's text, which forbids pinning text and mandates asserting outcomes. | yes |
| D-3 | Five findings, two MEDIUM, none BLOCKER or HIGH. Does this plan go NO-GO? | NO. All five FIXED by in-place revision, so readiness is `go-pending-approval`. | (a) NO-GO on the two MEDIUMs - rejected: severity is for reporting and the Fix Bar alone decides fixing; every fix is Low Remediation Risk on all four axes (relax an unreachable bar to a delta, add one behavioral test with a falsifier, mark a finding superseded, correct a conclusion, sweep restatements) and none alters the plan's design or the production change. (b) REPLAN - rejected: the diagnosis reproduces exactly, the refusal of both carrier items' proposed rationale is the plan's strongest work and is correct, and the defects were in a validation bar and an over-broad inference, both repairable with bounded edits. (c) Escalate as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the `HIGH` threshold, and nothing is left unfixed. | the `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision including the new E/V pair; `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies; OQ-01 independently re-measured and upheld. | yes |
