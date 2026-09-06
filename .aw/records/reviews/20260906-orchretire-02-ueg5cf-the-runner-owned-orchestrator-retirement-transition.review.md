# Review: the runner-owned orchestrator retirement transition (child ueg5cf, Set orchretire)

- Subject-Id: ueg5cf
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `ae701828`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review and `--phase review-finalize` conformed after the revisions.

DISCLOSURE: I authored this plan in the same session, so this is a SELF-REVIEW, not an independent one.
It is recorded because the repository requires a review record before `to-review -> reviewed`.

THIS IS THE SET'S HIGHEST-RISK PLAN and the review was scoped accordingly. Children 01 and 03 can only
cause a false REFUSAL (an orchestrator lingers, which is today's status quo). This one deliberately OPENS
a lifecycle gate, so its failure mode is a false RETIREMENT, or worse, a route by which an ordinary plan
reaches `executed` without evidence. So beyond verifying the plan's claims I went looking specifically
for ways the opened gate could be reached by something other than an eligible orchestrator. All three
HIGH findings came out of reading `ipd_lifecycle.py` directly rather than trusting the plan's account of
it, and none of them is hypothetical.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | B. Security (default-deny, privileged bypass) | `ipd_lifecycle.py:72`, `:2223`, `:2403`; `_refuse_worker_role_verb` `:82-97` | The worker-role refusal is NOT inheritable. `worker_role_active` is called in the CLI WRAPPERS `run_begin` (`:2223`) and `run_finalize` (`:2403`), not inside `finalize()`, and has exactly those two call sites in the module. A new transition function therefore begins with NO role guard, so a managed WORKER could create lifecycle authority through the new route: precisely the `wtiso-03` E-05 invariant, and the same class of hole as the `aw set executed` bypass this plan is otherwise careful not to build on. The plan noted that bypass in its conventions and still did not guard its own new path | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06 (refuse in worker role FIRST, before any resolution/gate/mutation, reusing `_refuse_worker_role_verb`) and V-06 (evidence of the `AW-LIFECYCLE-ROLE-001` refusal with no transition, plus a sabotage). Added F-6. Watermark 05 -> 06 |
| PR-202 | HIGH | UNDER-SCOPE | A. Correctness; C. operability (concurrency, recovery) | `ipd_lifecycle.py:303`, `:130-143`, `:1632`, `:1702-1725`, `:1744-1760`, `:1869`, `:1500-1516` | E-01 said the rollup must perform "every other gate the main path performs" and then enumerated FIVE. `finalize` performs at least nine, including the EXCLUSIVE finalize lock, the two-phase transaction journal (`prepared -> mutating -> ready-to-commit -> committed -> complete`), early crash recovery that resumes or rolls back a prior interrupted transaction BEFORE the fresh precheck, the idempotent pre-commit rollback, and the actor/message refusals. E-02's drift test, built from the five-item list, would have PASSED while the rollup silently ran with no lock, no journal and no recovery, inside a live runner in a shared checkout where a child's own finalize can interleave | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now carries the full nine-gate enumeration with `path:line` for each, requires a recorded reason for any gate deliberately not shared, and adds an explicit concurrency instruction (take the same lock or state why not). V-02 requires the enumeration to include lock/journal/recovery/index-refresh. Added F-7 |
| PR-203 | HIGH | IN-SCOPE | B. Security (authorization scoped to the resource) | E-01 pre-revision; `oc_runipd.py:2450-2463`, verified by calling `action_for` | E-01 gated the route on `Kind: orchestrator` only. That makes it a function that retires ANY orchestrator it is pointed at, with only caller discipline between it and a false retirement, and `action_for` returns `orchestrate` from `reviewed` onward so the window opens before human approval. The one thing this Set must never do is assert a completion that did not happen | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires child 01's eligibility verdict IN the transition, not just in its caller, with the reason stated. V-01 adds a fifth required piece of evidence: a `Kind: orchestrator` plan whose Set is ineligible must be REFUSED. Added F-9 |
| PR-204 | MEDIUM | UNDER-SCOPE | A. Correctness; honesty | `ipd_lifecycle.py:1355-1364`, `:1170`, `:1391` | The receipt carries more than authority. `finalize_precheck` reads `base_head` FROM it (refusing a missing or `unversioned` value) and that is the baseline the ENTIRE scope delta is computed against, plus the frozen `scope_paths`. So R-6's option "the rollup does not require a receipt" silently also means "the rollup performs no scope reconciliation", a consequence neither the spec nor the plan mentioned and which would have been discovered during implementation rather than decided | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names what the receipt was carrying, requires the scope-delta consequence to be stated, and requires the rollup to ASSERT it changed nothing outside its own `owned_paths` rather than assume it. V-03 requires that assertion as evidence. Added F-8 |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` question
was required.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-201: add the role guard as a new E-item, or fold it into E-01's gate list? | New E-06 with its own V-06. | Folding it into E-01, REJECTED because E-01 is already the densest item and a security guard buried in a nine-gate enumeration gets implemented as a checkbox; it needs its own sabotage-backed validation. Leaving it to the `aw set executed` bypass item (spec Section 4), REJECTED because that item concerns an EXISTING path while this is a NEW path being created here, and shipping a new hole while a separate item fixes an old one is indefensible. | `ipd_lifecycle.py:2223`/`:2403` call sites; spec Section 4 scoping | yes |
| D-2 | PR-203 could be read as "the eligibility check belongs in the caller (child 03), so this is not ueg5cf's finding". Whose is it? | This plan's: the transition itself must require the verdict. | Leaving it to child 03's dispatch, REJECTED as defense-in-depth that costs one call: a transition function that trusts its caller is one refactor away from being called from somewhere new, and the failure it permits is a false retirement, the exact thing the Set exists to prevent. | `plan-review.md:427-432` (authorization default-deny, resource-scoped); `oc_runipd.py:2450-2463` | yes |
| D-3 | Is PR-202 a BLOCKER? | HIGH. | BLOCKER, REJECTED: it is a coverage/robustness gap in a plan that has not run, and the drift test's PURPOSE was already correct; the enumeration was incomplete. Nothing is currently broken and no data is at risk. It is material because a lockless journal-less transition in a shared checkout can corrupt a concurrent finalize, which is why it is not MEDIUM. | `plan-review.md:504-509` | yes |
| D-4 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status: reviewed`, no human sign-off). `no-go`, REJECTED (no open question, no unfixed BLOCKER/HIGH). | `plan-review.md:531-546`; `.aw/records/plans/README.md:45-51` | yes |

No `Reversible: no` decision was taken.

### Verified claims

- The E/V contradiction is exactly as described. `check_checkpoint` (`ipd_lint.py:753-784`) applies the
  `pre-transition` requirements UNCONDITIONALLY: every `E-*` must be `performed`, every `V-*` must be
  `pass` with non-empty `Observed evidence`. `grep -c orchestrator agent_workflows/ipd_lint.py` returns
  `0`, so the linter has no orchestrator concept, confirming F-2 and the plan's cited line range.
- The receipt gate is first and fails closed. `finalize_precheck` (`:1337-1345`) returns the "no begin
  receipt for <id> ... (fail-closed: no receipt = no execution authority)" refusal before any other
  check, confirming F-3.
- `finalize` consumes the receipt on success at exactly the cited line: `receipt_path_for(...).unlink()`
  at `ipd_lifecycle.py:2114`. The plan's conventions note is precise.
- The parenthesis constraint is real and documented where claimed. `driver_actor`'s docstring
  (`oc_runipd.py:799-810`) states the actor is kept parenthesis-free, and
  `_HISTORY_ATTRIB_RE` (`ipd_lint.py:179-181`) captures the actor as `\((?P<actor>[^)]*)\)`, which a
  parenthesized actor would indeed misparse. Today's `--actor "aw oc run (orchestrator rollup)"`
  (`oc_runipd.py:785`) contains parentheses, confirming F-4.
- The rollup message string has never been written to a plan, consistent with 0 `orchestrator-finalized`
  events, so E-04's claim that the wording is free stands.
- Status legality for `pre-transition` means "not already terminal"
  (`ipd_schema.checkpoint_allows_status`, `:1066-1068`), which is what E-01's "status legality" resolves
  to. Worth having pinned, since it is weaker than a reader might assume.
- The plans-index refresh is genuinely fail-loud: it re-runs `aw index plans --check` and RAISES
  "owned plans index refresh did not converge ... finalize fails closed rather than committing a stale
  index" (`:1500-1516`). E-01 calling it "fail-loud" is accurate.
- The commit is path-scoped over `owned_paths` = plan, destination, `INDEX.json`, `INDEX.md`
  (`_finalize_transaction`, `:1892-1896`).
- The 0-vs-28 measurement and the `99760832`/`801dd28a` ordering were re-verified in this Set's earlier
  reviews and hold (28 deferrals, 15 distinct orchestrators, 103 run records).

### Right-sizing and conceptual density

Now six E-items in two groups. E-01 is the densest (a new transition plus two gating conditions) but is
one deliverable with one test-surface; E-02's enumeration grew substantially but remains a single drift
test. E-06 was added as a SEPARATE item precisely to avoid burying a security guard inside E-01 (D-1).
`Scope-Paths` is three files and already covered E-06 without widening. No split recommended.

### Not verified, and stated as such

I did not implement the transition, run the suite, or exercise a rollup. Every claim above is a read of a
named `path:line` at `ae701828`, or the output of a read-only call. The plan's own V-items must produce
the runtime evidence, and V-01/V-02/V-05/V-06 are deliberately written to require sabotages rather than
passing tests, because a passing test proves nothing about a boundary it never probes.
