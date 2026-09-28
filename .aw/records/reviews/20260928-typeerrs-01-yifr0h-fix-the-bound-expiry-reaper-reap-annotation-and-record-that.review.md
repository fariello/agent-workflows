# Review findings: plan yifr0h

- Subject-Id: yifr0h
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d2c7921b` in a lane worktree; the plan was authored at `258a1894`. Structural
preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0, `findings: 0`) and
`--phase review-finalize --agent` conforms after revision with zero findings. No pre-review snapshot
was owed: the plan was committed and unmodified, with `git status --short` empty at review start. The
plan carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.
`aw sanitize --agent` clean. Every mutation this review ran was reverted and verified reverted.

THE DOMINANT FINDING IS THAT THE PLAN'S MAIN DELIVERABLE HAD ALREADY SHIPPED WHEN IT WAS AUTHORED,
AND FROM A DIFFERENT BACKLOG ITEM. Plan `2o9osz` (`.aw/records/plans/executed/20260928-jt01do-01-2o9osz-...ipd.md`,
from backlog `jt01do`, now `done`) executed at commit `d0d0c9e4` and did exactly what this plan's
E-01 proposed: it replaced `reap: Callable[[Any, Path], Any] | None` with a `_ReapCallable` Protocol
and added `tests/test_reap_contract.py`. Measured at review, `python3 -m mypy
agent_workflows/lane_containment.py --ignore-missing-imports` now reports `Success: no issues found
in 1 source file`, where the plan's F-04 recorded `:1245: error: Unexpected keyword argument
"run_dir"  [call-arg]`. So E-01's entire Expected outcome is already true.

CRUCIALLY THIS WAS NOT A LATER ARRIVAL THAT NOBODY COULD HAVE SEEN. `git ls-tree -r --name-only
258a1894 -- .aw/records/plans/` shows `2o9osz`'s file already in `pending/` at this plan's own
authoring HEAD, declaring `- Scope-Paths: agent_workflows/lane_containment.py,
tests/test_reap_contract.py` and a Concern quoting the same annotation and the same
`reaper(process, run_dir=run_dir)` call. Two pending plans claimed the same production file for the
same defect from two near-duplicate backlog items, and neither cited the other. The authored evidence
pass verified the defect against the CODE, which proved it was live but could not prove it was
unclaimed. Recorded as new F-14 with the convention that would have caught it.

THE SECOND FINDING IS THAT THE AUTHORED E-04 IS ALSO ALREADY DELIVERED, and this one was settled by
running the plan's own proposed mutation rather than by finding a similar-looking test. E-04 wanted a
pin asserting that a CLEAN tree whose HEAD has moved off `attempt["starting_head"]` takes the
PRESERVE branch with `work_dir=None`. Deleting exactly that arm (`elif starting_head and
head_now.strip() != starting_head: holds_work = True`) from
`runner_shared.reconcile_item_on_interrupt` turns `tests/test_interrupt_reconcile.py` RED at
`InterruptReconcileNoWorktreeUnitTests::test_no_worktree_committed_work_preserves_work`
(`1 failed, 9 passed`), whose body commits a file, asserts `item["status"] == "interrupted"`, asserts
the receipt survives, and asserts the `work-preserved` subevent. That IS E-04's assertion. Note the
plan's own prose warned "DO NOT duplicate the six cases `tests/test_interrupt_reconcile.py` already
covers" while proposing a pin duplicating one of them, and that module in fact carries TEN tests.
Recorded as new F-13.

SO THE REVIEW'S CENTRAL QUESTION WAS WHETHER ANYTHING SURVIVES, AND SOMETHING GENUINELY DOES. This
was tested by mutation rather than assumed, because `tests/test_reap_contract.py`'s name suggests it
already covers the seam. It does not: it converts the `reap` ANNOTATION into an `inspect.Signature`
and calls `sig.bind(...)`, never invoking `bound_expiry_reaper`. Two mutations measured the gap.
FIRST, rewriting the product call to `reaper(process, run_dir)` positionally left that file GREEN at
`2 passed` while mypy reported `lane_containment.py:1261: error: Too many positional arguments for
"__call__" of "_ReapCallable"`. SECOND, replacing the default reaper with
`lambda process, *, run_dir: None` ALSO left it GREEN at `2 passed`, and nothing catches that at all.
Because this repository runs no type checker on any gate (re-verified: no `mypy`, `pyright` or
`type-check` in `.pre-commit-config.yaml` or `.github/workflows/tests.yml`), both regressions ship
today on a green bare suite. The second is the more serious: spec `c4gd2h` R5 requires ONE shared
reaper and `bound_expiry_reaper`'s docstring says a caller passing anything else "is introducing the
second reaper the spec forbids", and that is asserted in two docstrings and enforced by nothing.
`2o9osz` agrees in its own Deferred words, recording that it "adds only a CONTRACT guard ... which is
deliberately not behavioral coverage".

THE PLAN WAS THEREFORE NARROWED RATHER THAN RETIRED, recorded as OQ-03 and D-1. Retiring to
`superseded/` was the serious alternative and was rejected on two grounds. Substantively, a measured
spec-backed gap survives `2o9osz`'s execution and this plan is the filed carrier for it. Mechanically,
`g321ny` carries `- Blocks-Release: next`, and the repository's close-legitimacy rule accepts a
handoff only through an EXECUTED plan carrying `- From-Backlog: g321ny` and the same gate; this plan
is that carrier, so retiring it would strand a live release gate with no carrier. That consequence is
now stated in the gate section for whoever closes the item. The maintainer can still retire it at
approval, and the revised gate paragraph says so explicitly along with what they would then owe.

WHAT THE REVISION DID. The title, Concern, Scope, Goal and `- Scope-Paths:` were rewritten to the
surviving work. `- Scope-Paths:` SHRANK from two paths to one, `tests/test_lane_reaper_callshape.py`,
so NO production module is editable: `agent_workflows/lane_containment.py` was removed because its
Protocol and clean mypy result already shipped, and editing it now risks "correcting" `2o9osz`'s
better-reasoned code. The checklist went from four E-items to three: the two behavioral guards
(formerly E-02 and E-03, now E-01 and E-02) plus a new E-03 that records the provenance of both
shipped halves in the new file's module docstring. `- Highest E allocated:` was corrected from `04`
to `03`. The V-items were rewritten to match, each now demanding that the shipped
`tests/test_reap_contract.py` be shown GREEN under the same mutation that turns the new file RED,
which is what proves this plan adds coverage rather than duplicating `2o9osz`.

THE THIRD MATERIAL FINDING IS A SPENT BASELINE OVER A RED TREE. F-11 recorded `2935 passed, 2
skipped` at `258a1894`. Re-measured at review on a clean tree: `1 failed, 3006 passed, 2 skipped, 3
warnings in 45.43s`. The one failure is pre-existing and unrelated:
`tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` fails
at `assert not sat` (`tests/test_dependency_block_reporting.py:122`) because it hardcodes the
dependency `executed:5o1jye` and `5o1jye` has since reached `executed/`. Left as authored, the
executor of a plan whose diff is one test file would have faced a 71-test gap plus an unexplained red
and the plan's own hard-MUST honesty rule telling them to report it.

A SMALLER BUT REAL TRAP WAS THE SHIPPED PROTOCOL'S SHAPE. `_ReapCallable.__call__` is
`(self, process: Any, /, *, run_dir: Path) -> Any` with `process` POSITIONAL-ONLY, and its docstring
gives the reason ("so an injected test double may name it freely without raising a parameter name
mismatch"). E-01 proposed `(self, process: Any, *, run_dir: Path)`. An executor reading the
unrevised plan beside the shipped file would have had a standing instruction that disagrees with
better-reasoned committed code, on the exact axis (positional versus keyword binding) the plan is
about. Both the spy's shape and an explicit prohibition on "fixing" the Protocol are now stated.

BOTH SURVIVING E-ITEMS' ASSERTIONS WERE DRIVEN AT REVIEW, so they are confirmations rather than
hopes: the keyword spy was called exactly once with the expected `run_dir`, and the
`(process, run_dir, /)` spy raised `TypeError: pos_only() got some positional-only arguments passed as
keyword arguments`, which also confirms the plan's claim that the reap call sits outside
`contextlib.suppress` and the negative assertion is reachable.

WHAT REVIEW LEFT ALONE, each considered. The two toolchain deferrals (no type checker, carrier
`fcua9q`; the 103 `runner_shared.py` errors) are correct and were strengthened by noting that
`2o9osz` reached the same boundary independently, measuring 627 pyright errors. Spec `7ckptx`'s A10
bound-expiry demonstration stays with carrier `f15tne` and is now named in the Deferred section and
in the spec-sync section, so this plan's narrow call-shape tests are not mistaken for it. F-01, F-02,
F-03, F-05, F-06 and F-10 all re-verified as written and were kept, F-08 was retained as background
with its status changed from a live choice to settled history, and the four pre-existing `aw check
plans` errors (none naming this plan) were not touched.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | OVER-SCOPE | A. Correctness / G. Plan executability | `git log --oneline -S "_ReapCallable" -- agent_workflows/lane_containment.py` -> `d0d0c9e4`; `git show --stat d0d0c9e4`; `python3 -m mypy agent_workflows/lane_containment.py --ignore-missing-imports` -> `Success: no issues found in 1 source file`; `agent_workflows/lane_containment.py` `_ReapCallable` | E-01'S ENTIRE DELIVERABLE ALREADY SHIPPED, IN A DIFFERENT PLAN FROM A DIFFERENT BACKLOG ITEM. Plan `2o9osz` (backlog `jt01do`, now `done`) executed at `d0d0c9e4` and added the `_ReapCallable` Protocol and the annotation E-01 proposed; the file now type-checks clean where F-04 measured one error. An executor following the plan would either no-op E-01 or, worse, edit shipped code to match a superseded draft. Classified BLOCKER because a plan whose lead item re-does committed work will either strand the executor or damage it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (a rescoping, no code at risk once declared) | FIXED | E-01 removed. Title, Concern, Scope and Goal rewritten to the surviving work; `agent_workflows/lane_containment.py` REMOVED from `- Scope-Paths:` so no production module is editable; F-04 rewritten as the supersession record with the commit and the proof that `2o9osz` was already in `pending/` at this plan's authoring HEAD; OQ-03 records the narrow-versus-retire decision. |
| PR-002 | HIGH | OVER-SCOPE | D. Anti-regression | Mutation at review: deleting `elif starting_head and head_now.strip() != starting_head` from `runner_shared.reconcile_item_on_interrupt` -> `tests/test_interrupt_reconcile.py` `1 failed, 9 passed`, failing `InterruptReconcileNoWorktreeUnitTests::test_no_worktree_committed_work_preserves_work`; that test read in full | E-04'S PROPOSED REGRESSION PIN IS ALREADY DELIVERED, proven by running E-04's own mutation rather than by resemblance. The existing test commits a file, then asserts `interrupted`, receipt survival and the `work-preserved` subevent, which is precisely E-04's assertion. Adding a second pin would duplicate a guard while implying to the next reader that none existed. The plan also warned against duplicating "the six cases" of a module that carries ten. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 removed; `- Highest E allocated:` corrected `04` -> `03`. Added F-13 with the mutation evidence. The provenance is now recorded by the new E-03 docstring and V-03's pasted evidence instead of by a duplicate test, and a new Deferred row states this is dropped-because-done rather than deferred. |
| PR-003 | HIGH | IN-SCOPE | E. Testing and verification | `python3 -m pytest` at review on a clean tree -> `1 failed, 3006 passed, 2 skipped, 3 warnings in 45.43s`; F-11's authored `2935 passed, 2 skipped`; `tests/test_dependency_block_reporting.py:122` `assert not sat`; `5o1jye` in `.aw/records/plans/executed/` | THE AUTHORED BASELINE IS SPENT AND THE TREE IS ALREADY RED FOR AN UNRELATED REASON. 71 tests arrived since `258a1894`, and the one failure is pre-existing, caused by a test hardcoding `executed:5o1jye` after that plan reached `executed/`. The plan's honesty rule would have handed the executor of a one-test-file change a red suite and a 71-test gap to explain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 rewritten with the re-measured baseline, the exact pre-existing node id, its cause, and its clean-tree reproduction. The validation section and V-03 now set the bar as "that one node id and no other, count at or above 3006 plus your new tests", cite `verify-execution` Dimension 3's attribution rule, and ask the executor to say which case they observed if a fix has since landed. |
| PR-004 | HIGH | IN-SCOPE | D. Anti-regression / G. Plan executability | `agent_workflows/lane_containment.py` `_ReapCallable.__call__` is `(self, process: Any, /, *, run_dir: Path) -> Any`; its docstring "The first parameter `process` is positional-only (`/`) so an injected test double may name it freely"; E-01's proposed `(self, process: Any, *, run_dir: Path)` | THE SHIPPED PROTOCOL'S SHAPE DIFFERS FROM THE PLAN'S PROPOSAL ON THE EXACT AXIS THE PLAN IS ABOUT. The committed `__call__` makes `process` POSITIONAL-ONLY for a documented reason; the plan specifies it without `/`. An executor holding the unrevised plan beside the shipped file has a standing instruction to change working code back to a draft's wording, and would also write the test spy against the wrong shape. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | F-07 rewritten to record the SHIPPED shape and its documented reason instead of the superseded measurement. E-01 carries an explicit bullet naming the positional-only first parameter and forbidding any "correction" of the shipped Protocol; the gate's failure-modes paragraph repeats the prohibition as its THIRD item. |
| PR-005 | HIGH | IN-SCOPE | E. Testing / A. Correctness | Mutation 1 (positional call): `tests/test_reap_contract.py` -> `2 passed`, mypy -> `Too many positional arguments for "__call__" of "_ReapCallable"`. Mutation 2 (default reaper replaced): `tests/test_reap_contract.py` -> `2 passed`. `tests/test_reap_contract.py` read in full; spec `c4gd2h` R5 | F-09 IS NOW FALSE AS WRITTEN, AND ITS CORRECTION IS THE PLAN'S ONLY REMAINING JUSTIFICATION. The claim that `tests/` contains zero references to `bound_expiry_reaper` was true at authoring and is false now. But the shipped test is narrower than its name: it binds the ANNOTATION and never invokes the function, so both a positional-call rewrite and a swapped default reaper leave it green, and with no type checker on any gate both ship on a green suite. Without this correction the plan rests on a false premise while its real premise goes unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 rewritten with both mutation measurements, the mypy output, and `2o9osz`'s own admission that it "adds only a CONTRACT guard ... which is deliberately not behavioral coverage". Each surviving V-item now requires showing `tests/test_reap_contract.py` GREEN under the same mutation that turns the new file RED, which is the proof of non-duplication. |
| PR-006 | MEDIUM | UNDER-SCOPE | B/C. Spec conformance | Spec `c4gd2h` R5 "The cleanup routine is ONE implementation shared by all four levels"; `bound_expiry_reaper` docstring "is introducing the second reaper the spec forbids"; mutation 2 leaving `tests/test_reap_contract.py` green | THE SPEC-BACKED HALF WAS BURIED IN A BULLET AND IS THE MORE IMPORTANT OF THE TWO GUARDS. Replacing the default reaper is caught by NOTHING today, not even by a type checker, so R5 is asserted in two docstrings and enforced nowhere. The authored plan folded this into E-03 beside a signature check that the shipped test already largely performs, which risked the whole item being judged redundant and dropped. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Promoted to its own E-02 with the R5 quotation and the measurement showing it unenforced, and with the patched-attribute assertion named as the load-bearing half ("if you keep only one, keep that"). The partly-redundant signature assertion is retained with an instruction to cite `tests/test_reap_contract.py` in a comment so a later reader deletes neither believing it duplicates the other. |
| PR-007 | MEDIUM | IN-SCOPE | C. Architecture / process | `git ls-tree -r --name-only 258a1894 -- .aw/records/plans/` showing `2o9osz` in `pending/`; its `- Concern:` and `- Scope-Paths:`; backlog `jt01do` and `g321ny` summaries | THE COLLISION WAS DISCOVERABLE AT AUTHORING AND THE PLAN RECORDS NO LESSON. Two pending plans declared the same production file for the same defect from two near-duplicate backlog items, and neither cited the other. The authored evidence pass verified the defect against the CODE, which proves a defect is live but not that it is unclaimed. Without recording this, the next author repeats it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with the evidence, and a `## Project conventions` entry stating the convention: before authoring, grep `pending/` for every path you intend to declare in `- Scope-Paths:` and for the symbol you intend to change, and cite what you find. It also notes why the runner's isolation does not help here (it protects EXECUTION; the waste was at authoring). |
| PR-008 | MEDIUM | IN-SCOPE | G. Plan executability / honest documentation | Authored gate paragraph "The other is live, but the item names the wrong side ... The fix is four lines and no executable change"; authored close note "only one is fixed by this plan, the other having shipped in `87jnym`" | THE GATE TOLD THE HUMAN THEY WERE APPROVING A FIX THIS PLAN NO LONGER MAKES, and the close note understated the situation by one half. After PR-001 the plan fixes NEITHER reported error, and its entire diff is one test file. A gate paragraph is the one place a maintainer reads before signing, so a stale claim there is the highest-leverage inaccuracy in the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate paragraph rewritten to lead with "BOTH ... are ALREADY FIXED IN SHIPPED CODE", name `87jnym` and `2o9osz` (`d0d0c9e4`), state that the diff is one new test file and no production line, and frame the approval question as whether the remaining sliver is worth executing, including the RETIRE option and what retiring would owe. The failure-modes list grew from two to four. |
| PR-009 | MEDIUM | IN-SCOPE | A. Correctness (release gate) | Authored close note; backlog `g321ny` `- Blocks-Release: next`, `- Status: graduated`; the repository close-legitimacy rule requiring an EXECUTED carrier with `- From-Backlog:` and the same gate | THE CLOSE NOTE MISDESCRIBES WHY `g321ny` MAY CLOSE, which matters because the item is release-gated. It said the close is legitimate "because between them both halves are resolved and E-04 preserves the shipped half's guarantee". E-04 is gone, and the actual mechanism is the HANDOFF rule: this plan carries `- From-Backlog: g321ny` and the same `- Blocks-Release: next`, so reaching `executed/` is what preserves the gate. Stated wrongly, a closer could close on prose and drop a release blocker. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The close note rewritten to say this plan fixes NEITHER half, name the plan that fixed each, and state the handoff mechanism explicitly. It also records the consequence for the retire option: retiring this plan would leave `g321ny` with a live gate and no executed carrier, so anyone taking that route must give the item another one first. |
| PR-010 | LOW | IN-SCOPE | E. Testing | Authored validation bullet naming `tests/test_liftaudit_stop_halts_run.py` as "the one test file that exercises `runner_shutdown`"; `tests/test_reap_contract.py` (shipped since) | THE TARGETED REGRESSION SET NAMES THE WRONG COMPANION FILE. The file that actually guards this seam, `tests/test_reap_contract.py`, did not exist when the plan was authored and is the one that must stay green (and must be shown green under mutation) for this plan's non-duplication claim to hold. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `python3 -m pytest tests/test_reap_contract.py tests/test_interrupt_reconcile.py -o addopts=""`, with review-measured expectations (`2 passed` and `10 passed`) and a note explaining the substitution. |
| PR-011 | LOW | IN-SCOPE | F. Honest documentation | Authored Scope check "Under-scope: Two things are knowingly left"; carrier `f15tne`; spec `7ckptx` A10 | THE SCOPE CHECK OMITS THE LARGEST HONEST LIMIT. Spec `7ckptx`'s A10 bound-expiry demonstration is undemonstrated and belongs to carrier `f15tne`; a reader could take this plan's two call-shape tests for that coverage, which would over-credit it on a criterion of an approved spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Under-scope grew from two items to three, naming `7ckptx` A10 and `f15tne`. A Deferred row and a spec-sync paragraph both state that this plan's tests are narrow call-shape guards and NOT that demonstration, and that `7ckptx` is approved with A10 currently undemonstrated. |
| PR-012 | LOW | IN-SCOPE | E. Testing / safety | Three deliberate-failure demonstrations, mutating `lane_containment.py` twice and `runner_shared.py` once; `- Scope-Paths:` names one test file | EVERY VALIDATION MUTATION NOW TOUCHES A FILE OUTSIDE SCOPE, and after rescoping the plan should modify NO production file, so a leaked mutation is both a scope breach and a silent behavior change in a shared checkout. The authored plan flagged this for one mutation only. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Each of V-01, V-02 and V-03 now demands `git status --short` proving the mutated production file is unmodified before staging, with a STOP-and-report instruction for `runner_shared.py` as the highest-contention file. The validation section states the bar once, the Scope check explains why exercising and mutating an out-of-scope module is legitimate provided it is reverted, and the final staged set must contain no production path at all. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Both halves of `g321ny` shipped before this plan could execute. Retire it as superseded, or narrow it to what remains? | NARROW, and record the provenance of both shipped halves in the surviving test file. | (a) Retire to `superseded/` by `2o9osz` and re-file the behavioral gap - rejected on two grounds: a measured, spec-backed gap survives `2o9osz`'s execution (mutation shows its test green when the default reaper is swapped), and `g321ny` carries `- Blocks-Release: next` whose close needs an EXECUTED carrier with `- From-Backlog:` and the same gate, so retiring would strand a live release blocker. (b) Keep the plan as authored and let the executor discover the collision - rejected outright: E-01 would no-op or damage `2o9osz`'s better-reasoned positional-only Protocol. | `git ls-tree 258a1894` showing `2o9osz` already pending; mypy `Success` at review; both mutation runs leaving `tests/test_reap_contract.py` green; `2o9osz`'s own Deferred text; the repository close-legitimacy rule; backlog `g321ny` `- Blocks-Release: next` | yes |
| D-2 | Is the surviving behavioral guard real coverage, or does the shipped `tests/test_reap_contract.py` already provide it? | REAL, and require every deliberate-failure demonstration to show the shipped file GREEN under the same mutation. | (a) Trust the shipped file's name and drop the plan - rejected: measurement refutes it; the file binds an annotation and never invokes the function. (b) Assert the gap in prose without the paired green run - rejected: the non-duplication claim is exactly what a future reader will doubt, so the proof belongs in the evidence rather than in an argument. | Mutation 1: shipped file `2 passed`, mypy `Too many positional arguments for "__call__" of "_ReapCallable"`. Mutation 2: shipped file `2 passed`, no checker catches it. `tests/test_reap_contract.py` read in full. No type checker in `.pre-commit-config.yaml` or `tests.yml` | yes |
| D-3 | Should the plan add the `g321ny` item-1 regression pin it authored? | NO: drop it as already delivered, and record the provenance in a docstring instead. | (a) Add it anyway for a test that names the backlog id - rejected: it duplicates an existing guard and implies to the next reader that none existed. (b) Add it and delete the existing test - rejected outright: the existing test is broader (receipt survival and the `work-preserved` subevent) and is not this plan's to touch. | Deleting the moved-HEAD arm turns `tests/test_interrupt_reconcile.py` red at `test_no_worktree_committed_work_preserves_work` (`1 failed, 9 passed`); that test read in full; the module carries ten tests, not the six the plan assumed | yes |
| D-4 | E-03's provenance record: a docstring, or an executable assertion? | A DOCSTRING, with V-03 carrying the pasted verification. | (a) Assert `_ReapCallable` exists / that a commit is in history - rejected: the first is a structure pin of the kind the maintainer's 2026-09-26 ruling removed in bulk, and the second breaks on any history rewrite while testing git rather than the code. (b) Record it only in this IPD - rejected: the reader who needs it is someone opening the test file and asking why a plan titled for an annotation fix changes no production code. | The 2026-09-26 no-source-text-pins ruling; the claim being recorded is provenance, whose verification is pasted evidence rather than a runtime assertion | yes |
| D-5 | `intent-audit`-style four-versus-five style aside: should this plan reconcile the shipped Protocol's positional-only shape with its own proposed shape? | NEITHER: keep the SHIPPED shape, forbid editing it, and correct the plan's prose to describe it. | (a) Edit the Protocol to `(self, process, *, run_dir)` to match the plan - rejected: it would damage working code with a documented rationale to satisfy a superseded draft sentence, on the exact positional-versus-keyword axis this plan is about. (b) Leave the plan's prose as authored - rejected: an executor holding a standing instruction that contradicts committed code will eventually follow it. | `_ReapCallable.__call__` and its docstring read at review; the shipped form is `(self, process: Any, /, *, run_dir: Path) -> Any` | yes |

No `Reversible: no` decision was made. Every decision above is a scoping or wording change inside
one pending plan plus this review record; each is undone by editing the plan, and none touches
production code, a published interface, a migration, a released artifact, or an executed record. In
particular this review modified NO production file: the five mutations it ran to establish PR-002,
PR-005 and D-3 were each reverted and verified (`git diff --stat` empty, `git status --short` clean).

No finding is left `OPEN` or `DEFERRED`, so no escalation into the plan as a `- Blocking: yes`
question is owed under `review_findings_gate.block_at` (default `HIGH`). The BLOCKER (PR-001) and all
four HIGH findings are `FIXED` in place by rescoping. OQ-01 and OQ-02 were pre-existing, `resolved`
and non-blocking; both keep their answers, with OQ-01's spent closing sentence corrected and OQ-02
marked settled-in-code. OQ-03 was added by this review to carry D-1 and is non-blocking, because the
narrowing is fully specified in this revision and the retire alternative is a call the maintainer can
still make at approval.

### Structural and consistency checks at review

- `aw ipd lint --phase author --agent` before revision: `outcome: clean`, `exit 0`, `findings: 0`.
- `aw ipd lint --phase review-finalize --agent` after revision: `outcome: clean`, `exit 0`,
  `findings: 0`. (One intermediate `IPD-I302` was hit and fixed during revision: a V-item heading must
  read `V-NN validates E-NN`, which is also what obliged the provenance record to become a real E-03
  rather than a bare validation item.)
- `aw check release-gates`: `CONFORMS`, 0 errors, so `- Blocks-Release: next` and
  `- From-Backlog: g321ny` both resolve.
- `python3 -m mypy agent_workflows/lane_containment.py --ignore-missing-imports`:
  `Success: no issues found in 1 source file` (mypy 2.3.1).
- `python3 -m mypy agent_workflows/runner_shared.py --ignore-missing-imports`:
  `Found 103 errors in 1 file`, unchanged from authoring.
- `python3 -m pytest tests/test_reap_contract.py -o addopts=""`: `2 passed`.
- `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts=""`: `10 passed`.
- Bare `python3 -m pytest` on a clean tree: `1 failed, 3006 passed, 2 skipped, 3 warnings in 45.43s`,
  the one failure pre-existing and unrelated (see PR-003).
- `aw sanitize --agent`: clean.
- Mutation hygiene: five probe mutations across `lane_containment.py` and `runner_shared.py`, all
  reverted and verified; the only files this review modified are the plan and this record.
