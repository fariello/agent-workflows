# Review findings: plan qo9khm

- Subject-Id: qo9khm
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `947f72de` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified. No production or test file was modified by this review; every measurement
ran in throwaway `tempfile` git repos driving the real `aw ipd scaffold`/`begin`/`finalize`
subprocesses, from scripts under the gitignored `.aw/state/`, with `git status --short` empty
throughout.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS MEASUREMENT DISCIPLINE IS EXCELLENT. Every load-bearing
claim reproduced independently through the real CLI. F-02: a plan whose leaves carry
`Execution state: performed`, `Result: pass` and real `Observed evidence` but UNTICKED checkboxes
refuses with `IPD-S401 E-01: execution checkbox does not agree with state 'performed'` and
`IPD-S402 V-01: validation checkbox does not agree with result 'pass'`, and
`finalize_refusal_is_retryable` returns `False` today. F-04: reconstructing
`prefix + summary + "  {rule} {detail}"` from the real `--json` payload gives
`RECONSTRUCTION == human stdout: True`. F-03: the `--agent` record carries only
`{"location","rule"}` per diagnostic and no `summary`. F-05's load-bearing half: a genuine success
stdout begins `plans index --check: clean` and naive `json.loads` raises `JSONDecodeError`. F-11:
the worker-role path returns exit 2 with `stdout == ''` under `--json`. F-01, F-06, F-07, F-10,
F-12, F-14, F-15 and F-16 all reproduce as written.

WHAT REVIEW FOUND IS THAT THE DRAFTED CODE SET WAS UNSAFE IN THE OPPOSITE DIRECTION FROM THE PLAN'S
INTENT. The plan exists to stop prose matching from silently changing which refusals are retryable;
its own E-02 would have silently WIDENED two classes the spec forbids retrying.

**ADMITTING `C_CHECKPOINT` BY CODE WIDENS TWO NEVER-RETRY CLASSES (PR-901, BLOCKER).** E-02 listed
`ipd_lint.C_CHECKPOINT` first in the retryable code set. `IPD-S404` is a CATCH-ALL:
`ipd_lint.check_checkpoint` attaches it to the three answerable pre-transition messages AND to
`status '<x>' is incompatible with checkpoint '<cp>'`, emitted UNCONDITIONALLY at the top of the
function before the `if checkpoint == "pre-transition":` branch, so it can co-occur with the very
summary that gates Arm 1, AND to `<OQ>: unresolved blocking question at pre-execution`. Simulated
against the shipped classifier, the drafted rule flips both from `False` to `True`. Neither is
fixable by ticking a box, and the blocking-question case is answerable only by a HUMAN, so retrying
it burns a turn to be refused again. The shipped comment the plan sets out to correct already warns
that this code is "the obvious and WRONG trigger", and it is right. FIXED: the set is
`{C_EXEC_STATE, C_VALID_STATE, C_CROSS_STATE}`, and the three answerable `IPD-S404` messages stay
retryable through the PROSE fallback, which makes the composition strictly additive in exactly one
direction. V-02(b2)/(b3) now fail the item if the catch-all returns or if the answerable family
regresses.

**E-04's TWO-WAY COVERAGE PIN WOULD HAVE PUSHED THE EXECUTOR INTO PR-901 (PR-902, HIGH).** E-04
asserted every emitted pre-transition code is "in the new retryable code set or matched by the prose
allowlist". Since `C_CHECKPOINT` legitimately appears at pre-transition and is deliberately NOT in
the retryable set, that assertion goes RED for the non-answerable `IPD-S404` variants, and the
obvious way to make it green is to add the catch-all, which is precisely the unsafe change. FIXED:
the pin is now a THREE-WAY partition with an explicit KNOWN-TERMINAL set, so "considered and
deliberately terminal" is expressible.

**F-05's PER-LINE COUNT DOES NOT REPRODUCE (PR-903, LOW).** F-05 claims
`per-line JSON records found: 0` for `--json`. Measured on a genuine success stdout, SIX lines parse
individually: bare JSON strings from the pretty-printed body (`"src/f.py"`, the receipt path), none
payload-shaped. That makes a naive JSONL reader slightly WORSE than described (it finds records and
never the payload), so E-01's balanced-brace requirement is strengthened, not weakened. Also
recorded: reaching the polluted path required supplying the scope-reconciliation answers finalize
demands, since a first attempt refused with `finalize needs scope reconciliation answers`.

**BACKLOG `144b3x` IS ALREADY `graduated` (PR-904, LOW).** It reads `- Status: graduated`,
`- Graduated-To: finstruct`, graduated by run `run-20260928T235941Z-1396311` naming this plan. So
the gate's "on completion the runner sets backlog `144b3x` to `graduated`" is a no-op, and an
executor must not re-graduate it or set it `done`. F-07's parenthetical that
`grep -rn "From-Backlog: 144b3x"` is EMPTY is also now false, because this plan carries that field;
F-07's actual conclusion (no OTHER plan carries it, `ibuxe6` is a distinct open sibling) is
unaffected and reproduces.

**THE SHIPPED COMMENT MISCOUNTS ITS OWN ALLOWLIST (PR-905, LOW).** The comment above
`RETRYABLE_FINALIZE_FINDING_TEXTS` says "Four strings, MEASURED from `ipd_lint`'s `pre-transition`
checkpoint" and the tuple holds THREE. The plan's F-02 correctly says three. Since E-05 rewrites
that comment block anyway, the miscount is folded into that item rather than carried separately.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. All three authored open questions survive review: OQ-01's refusal to widen the return type is
upheld on F-15/F-16 (both reproduce) and on F-04's byte-exact reconstruction; OQ-02 is upheld and
GAINS a decisive third reason from PR-901, since the prose fallback turns out to be the mechanism by
which the answerable `IPD-S404` family stays retryable while its non-answerable siblings stay
terminal; OQ-03's deferral of the stdout pollution is upheld, with its carrier `eaffgr` confirmed
present, `Work-Kind: bug` and `Blocks-Release: next` as the plan states.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | blocker | IN-SCOPE | B. Security and correctness of the retry gate | `agent_workflows/ipd_lint.py` `check_checkpoint` (unconditional `C_CHECKPOINT` emission above the `pre-transition` branch; the `pre-execution` blocking-question emission); simulation against `runner_shared.finalize_refusal_is_retryable` | E-02's drafted code set included the catch-all `C_CHECKPOINT`, which also covers `status ... is incompatible with checkpoint ...` and `unresolved blocking question at pre-execution`. Measured, admitting it flips both from terminal to retryable, widening spec `25kzda` 5.5's never-retry territory in the opposite direction from the plan's intent. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-02 narrowed to `{C_EXEC_STATE, C_VALID_STATE, C_CROSS_STATE}` with the reasoning stated; E-05 gains a sixth required point recording the exclusion; V-02(b2)/(b3) added; new F-17; the gate's failure-modes section now leads with this. |
| PR-902 | high | IN-SCOPE | E. Testing and verification | plan E-04; `ipd_lint.check_checkpoint` emitting `C_CHECKPOINT` at pre-transition | E-04's two-way "retryable code or prose" assertion goes RED for the non-answerable `IPD-S404` variants, and the obvious repair is to add the catch-all to the retryable set, i.e. the test would have pressured the executor into PR-901. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-04 rewritten as a THREE-WAY partition with an explicit KNOWN-TERMINAL set, with the reason recorded so the partition is not "simplified" back. |
| PR-903 | low | IN-SCOPE | Evidence accuracy | genuine success-path run: first line `'plans index --check: clean'`, 77 lines, 6 individually-parsing lines all `payload-shaped=False` | F-05's `per-line JSON records found: 0` does not reproduce; six lines parse (bare JSON strings), none the payload. F-05's conclusion stands and is strengthened. Reaching the path also required supplying the demanded scope answers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-05 corrected in place with the measured count and why it strengthens the balanced-brace requirement; new F-18. |
| PR-904 | low | IN-SCOPE | G. Plan executability | `.aw/records/backlog/graduated/...144b3x...` showing `Status: graduated`, `Graduated-To: finstruct`, graduation history line; `grep -rn "From-Backlog: 144b3x" .aw/records/plans/` returning this plan | The item is already `graduated`, so the gate's completion instruction is a no-op; and F-07's "grep is EMPTY" clause is stale because this plan now carries the field. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The POST-GATE paragraph now states the item is already graduated and forbids re-graduating or setting `done`; F-07's stale clause annotated; new F-19. |
| PR-905 | low | IN-SCOPE | Documentation accuracy | `len(RETRYABLE_FINALIZE_FINDING_TEXTS) == 3` against the comment's "Four strings" | The shipped comment block miscounts its own allowlist. E-05 already rewrites that block, so the correction belongs there. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Folded into E-05's required rewrite (the block is replaced wholesale, so the miscount goes with it); recorded here so the executor does not reproduce the wrong count. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The drafted code set admits the catch-all `C_CHECKPOINT`, widening two never-retry classes. Narrow the set, or keep it and add explicit message-level exclusions for the two non-answerable `IPD-S404` variants? | Narrow the set to `{C_EXEC_STATE, C_VALID_STATE, C_CROSS_STATE}` and let the existing prose fallback carry the three answerable `IPD-S404` messages. | (a) Keep `C_CHECKPOINT` plus a deny-list of non-answerable message substrings: rejected because it reintroduces prose matching in the fail-OPEN direction (a new non-answerable `S404` message would be retried by default), which is strictly worse than the prose matching the plan exists to remove. (b) Raise it as a `Blocking: yes` question: rejected because the repository answers it decisively (the shipped comment states the hazard and `check_checkpoint`'s structure confirms reachability), so it is resolvable from evidence. | `ipd_lint.check_checkpoint` emitting `C_CHECKPOINT` unconditionally above the `pre-transition` branch and again for the `pre-execution` blocking question; simulation showing `shipped=False -> drafted=True` for both non-answerable messages; the shipped comment calling the code "the obvious and WRONG trigger". | yes |
| D-2 | E-04's coverage pin conflicts with the narrowed set. Weaken the pin, or add a declared KNOWN-TERMINAL set? | Add an explicit KNOWN-TERMINAL set, making the pin a three-way partition. | (a) Restrict the pin to the codes in the retryable set: rejected because it would stop detecting a NEW pre-transition code, which is the entire purpose of the pin. (b) Drop E-04: rejected because F-10 measures a real coverage hole that the existing prose pin does not close. | `ipd_lint.check_checkpoint` legitimately emitting `C_CHECKPOINT` at pre-transition while E-02 excludes it; F-10's measurement that the shipped prose pin filters to `C_CHECKPOINT` only and so missed the `S401`/`S402` gap. | yes |
| D-3 | F-05's per-line count does not reproduce. Correct it, or treat the discrepancy as immaterial since the conclusion is unchanged? | Correct it in place and record why the real behavior is slightly worse than described. | (a) Leave it: rejected because a plan's measured digit is the thing a reviewer is invited to dispute, and a wrong one erodes trust in the rest of a table that is otherwise very strong. (b) Re-derive the whole of F-05: unnecessary, since its load-bearing half (first line `plans index --check: clean`, naive `json.loads` raising) reproduced exactly. | Genuine success-path run printing the first-line repr, the 77-line total, and a per-line enumeration of the 6 parsing lines each with `payload-shaped=False`. | yes |
