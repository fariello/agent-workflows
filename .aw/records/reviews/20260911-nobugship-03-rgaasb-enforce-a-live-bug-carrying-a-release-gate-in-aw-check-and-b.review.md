# Review: enforce a live bug carrying a release gate in aw check and backfill the existing violations, child rgaasb (Set nobugship)

- Subject-Id: rgaasb
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `45158943`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(clean, exit 0, 0 findings) before semantic review. At `--phase review-finalize` the linter now reports
exactly ONE finding, `IPD-Q501` on blocking OQ-03, which is the gate working as designed rather than a
structural defect: it refuses the plan at every checkpoint until the maintainer answers the question this
review escalated.

SELF-REVIEW DISCLOSURE: this Set was authored in the same repository by the same model family, so treat
this as a near-self-review worth less than an independent one. Its value rests entirely on what was
EXECUTED, which in this case was the plan's own most dangerous step.

SCOPE OF THE LEDGER. The invocation named this child only. The orchestrator `qmgn12` and siblings
`zqs0px` / `di08i9` were read as EVIDENCE and NOT edited. The blocker below belongs to the parent's
OQ-03 and is restated here (with a `- Finding: PR-001` link) rather than edited into the parent, because
the parent is outside this ledger and already carries the question.

THE WHOLE BACKFILL WAS EXECUTED IN A THROWAWAY COPY, AND THAT IS WHERE EVERY FINDING CAME FROM. All 22
items were driven through the shipped setter, one at a time, exactly as E-04 prescribes. Result: 21
succeeded, 1 REFUSED, and the tree ended carrying 15 NEW `check.from-backlog-gate-mismatch` ERROR
findings where it had ZERO before, 2 of them naming plans in `executed/`. The bare suite still passed
(`5971 passed, 3 skipped, 2 xfailed in 62.80s`), so this is a checker-state collision and not a code
break. That single experiment produced PR-001, PR-004, PR-005, PR-006 and PR-011.

THE PLAN'S THESIS IS CORRECT AND ITS SHAPE WAS NOT CHANGED. A checker really is what makes the rule
self-maintaining, the rule family really does already exist at `error` under `I-07`, and the plan's own
warning about invariant misfiling is real. Every E-item survived; four were rewritten, none removed.

THE SECOND FINDING IS THE ONE THAT WOULD HAVE COST THE MOST EXECUTION TIME. E-05 and V-05 named
`aw check backlog` clean as the proof of success. Driven on the fully backfilled tree, that command
reported `outcome conforms, exit 0, findings 0` WHILE 15 ERROR findings existed. The cause is structural:
`check_release_gate_consistency` is called only from the once-per-full-sweep seam in `check_types`
(`check_engine.py:1806-1811`), so `check_type('backlog')` never reaches it. Verified twice, by source
inspection and in-process (`check_types(repo,['backlog'])` returned 0 while `['all']` returned 183 on the
same tree). So the plan's success criterion was blind to the plan's own rule family, and an executor
following it would have reported success over a red tree.

E-01'S CENTRAL DESIGN INSTRUCTION IS IMPOSSIBLE, WHICH MATTERS BECAUSE E-03 WOULD HAVE PINNED IT. The
plan requires composing with `evaluate_blocking_close` and requires a test asserting that composition.
But that predicate returns `CloseVerdict(True, "ok", "unchecked transition")` for an UNGATED item:
every branch keys on `blocks_release` being PRESENT (`check_engine.py:2016`, `:2028`, `:2065`, `:2077`),
which is the exact inverse of what this rule detects. Driven on a synthetic ungated `open` bug to
confirm. Had E-03 shipped as written, the test suite would have enforced a design that cannot work.

THE PLAN GOT ONE HARD THING EXACTLY RIGHT AND REVIEW CONFIRMED IT RATHER THAN CHANGED IT. `I-07` is the
correct invariant home: read at `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135`
it is "Release-gate preservation", assurance class "Repository invariant", and its control column already
names `evaluate_blocking_close` plus the sibling rules. The one honest caveat, now written into E-02, is
that the catalog text is phrased for the CLOSE direction while this rule governs the OPEN direction.

ELEVEN THINGS WERE DRIVEN RATHER THAN RECALLED: the population recomputed per item with status and
priority; the carrier set recomputed across ALL 22 items (15 carriers, not 11); the full 22-item backfill
executed through the setter; the resulting finding set enumerated with each carrier's directory;
`aw check backlog` and `aw check all` both run on the backfilled tree and compared; `check_types` called
in-process for `['backlog']` versus `['all']`; the `blocked` item's refusal reproduced and then cleared
with its gate flags; `aw ipd set --blocks-release` driven on a `pending/` carrier (works) and an
`executed/` carrier (refuses, demanding `--actor`); a same-status versus different-status `ipd set`
compared to prove the positional-status hazard; `evaluate_blocking_close` called on an ungated item; and
the release-blocker view counted before (114) and after (136).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Rubric A/D (correctness, invariants) | `check_engine.py:2204-2241`; full backfill driven at review | E-04's backfill creates 15 NEW `check.from-backlog-gate-mismatch` ERRORS (13 carriers in `pending/`, 2 in `executed/`) where there were ZERO. Proven by backfilling all 22 items through the setter in a throwaway copy. The plan's completion criteria are unreachable by any route it authorizes, and 2 carriers sit in a terminal directory where in-place edits are forbidden | C:Medium; U:Low; S:Low; F:High; Overall:High | OPEN | ESCALATED as blocking OQ-03 with `- Finding: PR-001`, carrying the corrected scale and the measured routes. Not fixable in-plan: choosing among the parent's four options trades a shipped ERROR rule against a backfill and two carriers are immutable, so it is the maintainer's decision |
| PR-002 | HIGH | IN-SCOPE | Rubric C (reuse the right mechanism) | `check_engine.py:2016`, `:2028`, `:2065`, `:2077` | E-01 mandates composing with `evaluate_blocking_close`, which cannot express an ABSENT gate: driven on an ungated bug it returns `(True,'ok','unchecked transition')`. E-03 would have pinned that impossible design with a test | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now forbids that composition, names the real reusable pieces (`find_from_backlog_artifacts`, `_backlog._iter_items`, the family parse helpers), and requires the driven non-use output; E-03's anti-fork assertion replaced by reuse assertions |
| PR-003 | HIGH | IN-SCOPE | Rubric E (validation actually validates) | `check_engine.py:1806-1811`; both commands driven | E-05/V-05 require `aw check backlog` clean, but it reported `conforms, exit 0, findings 0` on a tree with 15 of these ERRORs, because the family is wired only into the `check_types` full-sweep seam | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-05/V-05 now forbid that command as proof and require the shipped full-sweep command; E-02 must choose and PROVE the seam by running both commands on a violating tree; E-03 gains a `check_types` seam test |
| PR-004 | HIGH | IN-SCOPE | Rubric G (scope accuracy) | carrier set recomputed for all 22 items | The collision is 15 carriers, not 11, and is not confined to graduated items: `f5pttg` -> `4bc1nd` and `x6tk1u` -> `vhbvwz` are `open` items with carriers the plan never mentions | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04, the Scope check and OQ-03 all restated at 15 carriers with the two `open`-item carriers named, so a graduated-only remedy cannot silently leave mismatches |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric A (correctness of the prescribed command) | `aw backlog set blocked adgtqb --blocks-release next` -> exit 1 | The setter REFUSES the one `blocked` item: re-asserting `blocked` re-validates the typed gate, so the gate-only edit fails unless `--gate-kind`/`--gate-ref` are re-supplied | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 records the refusal, the working command shape, and the instruction to re-read the item's own gate fields; V-04 requires that row to show the flags |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric A (silent side effect) | `aw ipd set to-review <reviewed plan>` driven | The setter takes a status positionally; passing a status other than the artifact's current one transitions it and appends a history line. Reproduced on a sibling verb, and E-04 would sweep 13 carriers this way | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires each item's status be read from disk and echoed in the command, with the measured same-status-versus-different-status contrast stated; the gate repeats it as hazard three |
| PR-007 | MEDIUM | IN-SCOPE | Rubric G (unverified claim) | `.github/workflows/tests.yml:153-170` | The Scope sentence claims "registered in the rule registry so CI fails on it", but `aw check backlog` runs with an or-true suffix as ADVISORY per DECISION 18-r2ks4k-D1, so a rule reported only there fails nothing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 must state which CI step fails on the rule or say plainly that none does; V-02 makes an unqualified claim a failed validation; flipping the CI step added to Deferred with its documented precondition |
| PR-008 | MEDIUM | UNDER-SCOPE | Rubric E (honest success criterion) | `aw check all` -> 183 findings | No sweep this plan runs can be "clean": 183 pre-existing findings are present and reducing them would mean editing other parties' artifacts | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests and E-05/V-05 now demand a PER-RULE delta against a pre-edit baseline, with the measured tally quoted for reference and the live `check.from-backlog-dangling` explicitly excluded |
| PR-009 | MEDIUM | UNDER-SCOPE | Project spec-sync contract | `...pqsx96...spec.md:135` | `I-07` is verified correct but is worded for the CLOSE direction, and the plan neither noted the tension nor said who may fix it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 cites the catalog line and requires the tension be noted in the registration comment; the spec amendment is PROPOSED and added to Deferred, with the declare-first route stated if it must land here |
| PR-010 | LOW | IN-SCOPE | Evidence integrity | `git cat-file -t 2ff2b1b1` | Every authored figure is attributed to a commit absent from this repository | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The authored history line records the unverifiable anchor; the Concern carries re-measured counts at a resolvable HEAD |
| PR-011 | LOW | IN-SCOPE | Rubric E (evidence shape) | per-item `git diff` on the backfilled tree | The setter appends a status-history line per item even on a same-status call, so each diff is two insertions; V-04's "only the gate line and history changed" would read as a discrepancy mid-run | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states the expected two-insertion shape and V-04 asks for it explicitly |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the new predicate compose with `evaluate_blocking_close`, as the plan instructs? | NO. Reuse `find_from_backlog_artifacts`, `_backlog._iter_items` and the family's parse helpers instead, and record why. | Wrap it anyway (rejected: it returns "unchecked transition" for an ungated item, so the wrapper would report nothing). Widen `evaluate_blocking_close` to cover the open direction (rejected: three shipped surfaces depend on its current semantics, so widening it for one new caller risks the setter gate, the consistency rule, and the opt-in hook). | Driven call on an ungated bug returning `(True,'ok','unchecked transition')`; the four `blocks_release`-present branch guards at `check_engine.py:2016/2028/2065/2077`. | yes |
| D-2 | Is `aw check backlog` an acceptable success criterion for this plan's rule family? | NO. Require the full-sweep command plus a per-rule delta. | Keep it and additionally run `aw check all` (rejected: leaving a proof that is known-blind invites an executor to paste the easy one). Wire the family into the backlog content path so the command becomes valid (NOT decided here: it is a real option and E-02 must choose it explicitly with evidence, but it changes where four shipped rules fire and is the executor's call to record, not the reviewer's to impose). | `check_engine.py:1806-1811`; `check_types(repo,['backlog'])` -> 0 versus `['all']` -> 183 on a tree with 15 known mismatches; `aw check backlog --agent` reporting `conforms/0` on that same tree. | yes |
| D-3 | Is `I-07` the right invariant, given its close-direction wording? | YES, with the tension recorded in the registration comment and a catalog amendment PROPOSED rather than performed. | Choose another invariant (rejected: none of I-01..I-16 describes release-gate preservation, and picking a convenient id is the exact misfiling the plan warns about). Amend the catalog in this plan (rejected: `pqsx96` is not in `Scope-Paths` and a spec edit changes the contract every other plan is reviewed against; the declare-first route is stated instead). | The catalog row at `...pqsx96...spec.md:135` with its assurance class and control column; the recorded `check.setid-collision`/`I-09` misfiling in the same spec. | yes |
| D-4 | Should the 15-carrier collision be resolved here, since review measured it precisely? | NO. Escalate to the maintainer as blocking OQ-03 and let the lint gate hold the plan. | Pick option (a) (co-update the 13 pending carriers, exempt the 2 terminal) and write it in (rejected: it needs a `Scope-Paths` widening AND a narrowing of a shipped ERROR rule, and the reviewer would be authorizing both on their own authority). Narrow the new rule to `open`/`blocked` so no collision arises (rejected: it leaves 11 real bugs ungated, contradicting the Set's own concern). | `AGENTS.md`'s prohibition on editing a plan in `executed/`; the driven refusal of `aw ipd set executed ... --blocks-release`; the 15-finding result of the executed backfill; the parent's four costed options. | no |

#### Escalation of the irreversible decision (D-4)

D-4 is `Reversible: no` (it decides how a shipped ERROR rule interacts with a 37-file backfill, and two
affected artifacts are immutable), so recording it is NOT sufficient. It is escalated in the reviewed plan
as OQ-03 carrying `- Blocking: yes` and `- Finding: PR-001`, which `aw ipd lint` now refuses at every
checkpoint (`IPD-Q501`, verified at review-finalize), so execution cannot proceed until the maintainer
answers on the parent `qmgn12`.

## Round 2

Opened 2026-09-12 to record the maintainer's answer, which was given on the PARENT (`qmgn12` OQ-03)
exactly as round 1 instructed. Round 1 is left as written, per the reviews README. No plan content was
re-critiqued, no new finding was derived, and no product code was modified by this round.

THE RULING: restate `check.from-backlog-gate-mismatch` as the ONE-WAY obligation it already implements
(a LIVE carrier must not drop a gate its item carries) and SKIP a terminal carrier. Round 1's own
three corrections to the parent's framing all SURVIVE it, and were re-verified rather than trusted:
the carrier count is 15 and not 13, and the two extra carriers come from `open` items (`f5pttg` ->
`4bc1nd`, `x6tk1u` -> `vhbvwz`). Both were re-checked at round 2 and sit in `pending/`, so they are LIVE
and the ruling covers them with no special handling.

WHY THE RULING GENERALIZES TO A POPULATION THE PARENT HAD NOT MEASURED, which is the reason this round
can close the finding rather than re-open the question: the discriminator is the CARRIER's liveness, not
the ITEM's status. Round 1 had correctly warned that a remedy scoped to "the graduated 11" would leave
findings standing; the chosen remedy is not scoped that way.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness and data integrity / G. Plan executability | round 1's full-execution measurement (22 items backfilled in a throwaway copy, 15 carriers flagged, 2 terminal); both `open`-item carriers re-verified as `pending/` at round 2 | Carried forward: THIS PLAN'S BACKFILL CREATES 15 `from-backlog-gate-mismatch` ERRORS, 2 of them on plans in `executed/` that `AGENTS.md` forbids editing, so the plan could not complete by any route it authorized. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | RESOLVED BY THE PARENT'S RULING, which answers all three things round 1 asked an answer to cover: the 13 live carriers are co-updated (with `- Scope-Paths:` gaining the plans tree first, as round 1 demanded); the 2 terminal carriers are NEVER touched and stop being findings because the rule stops over-reaching, not because they are named as exceptions; and the two `open`-item carriers are treated identically, since liveness rather than item status is the discriminator. `check_engine.py` joins this plan's scope for the narrowing, which must reuse the shipped `is_retired`/`_EXECUTED_SEGMENT` predicate and must be tested to FAIL against today's code. OQ-03 additionally requires the test to pin BOTH measured directions, including the zero-finding case that is currently unreachable by construction and would otherwise be undefended against a refactor. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Round 1 refused to decide this inside the plan and sent it to the parent. Was that still right once the count turned out to be 15 rather than 13? | YES, and the larger count VINDICATED it: a plan-local remedy scoped to the graduated items would have left the two `open`-item carriers flagged. | Deciding locally once the fuller measurement was in hand (rejected: two of the four options changed a shipped ERROR rule's behavior, which is a contract trade-off the maintainer owns, and a plan-local answer would have been scoped to the population this plan happened to measure). | Round 1's own enumeration; the ruling's carrier-liveness discriminator, which covers all 15. | yes |

### Round 2 addendum (reviewer, after the ruling)

TWO THINGS WERE VERIFIED RATHER THAN TAKEN ON TRUST before this round's verdict flipped, because the
ruling arrived as another party's edit to a plan under review and a reviewer accepting that unchecked
would be endorsing an unread change. FIRST, the ruling's load-bearing measurement reproduces: adding
`- Blocks-Release: next` to pending plan `yeh7gc`, whose item `5ev6lh` carries no gate, produced ZERO
findings, and the structural cause is exactly as cited (`if mid and mbr` at `check_engine.py:2213-2216`
never admits an ungated item to `item_gate`). So the asymmetry is real and the reframing is not a
convenient story. SECOND, every precedent the ruling leans on exists: `is_retired` (`:482-494`),
`_EXECUTED_SEGMENT` (`:999`), and the neighbouring rule that excludes `executed/` for the identical
stated reason (`:1069-1071`).

THE RULED REMEDY WAS THEN EXECUTED END TO END, which is what licenses closing PR-001 rather than merely
recording an answer to it. In a throwaway copy: the terminal-carrier narrowing applied via `is_retired`,
all 22 items backfilled through the setter, finding set 15 -> 13 (the two `executed/` carriers gone), then
the 13 live carriers co-updated with `aw ipd set <current-status> ... --blocks-release next` -> ZERO
findings, 0 command failures, and the bare suite `5971 passed, 3 skipped, 2 xfailed in 61.04s`. So the
remedy is not only authorized, it is demonstrated to reach the Set's completion criterion 6.

ONE NEW FINDING THIS ROUND, and it is the gap between what the ruling authorized and what the plan
actually declared.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-012 | MEDIUM | UNDER-SCOPE | G. Plan executability (scope declaration) | plan `- Scope-Paths:` line 7 versus the ruling's "must gain the plans tree BEFORE any write" | The ruling authorized the plans tree and `check_engine.py` in scope, and the OQ-03 prose says so twice, but the `- Scope-Paths:` FIELD was never updated: it still listed only the checker, the test file and the backlog tree. A plan whose prose authorizes an edit its declared scope forbids sends the executor into the finalize scope gate with 13 undeclared carrier edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `.aw/records/plans/pending` added to `- Scope-Paths:` (`check_engine.py` was already declared). The Scope check section rewritten from "under-scope" to resolved, with a warning that the broad directory declaration is not licence to edit an unrelated plan and that finalize will still want a reason per carrier and a `--scope-ack` for anything declared-but-untouched. |

ALSO TIGHTENED, not as findings but as sequencing the ruling implies and the plan did not state: E-04 now
says the narrowing must land BEFORE the backfill (narrow, then backfill, then co-update), because the
reverse order produces a red exit-blocking sweep in a shared checkout; the spec-sync section now records
that this plan AMENDS a shipped rule, with the reuse requirement and the fail-against-today's-code test
obligation; and the gate's correction 5 and readiness paragraph were updated from `no-go` to
`go-pending-approval` with the measured 15/13/zero figures.

SHARED-CHECKOUT DISCLOSURE, recorded because it affected this record. Round 1 was written while this file
was uncommitted; the maintainer appended Round 2 and changed the `- Readiness:` line before noticing, and
said so in their commit message (`b3851a59`). Their Round 2 content is preserved verbatim above; this
addendum is the reviewer's own continuation of the same round. My in-flight plan revisions were swept into
that commit rather than mine, so the plan edits from round 1 are attributed there.
