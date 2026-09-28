# Review findings: plan t0ovw6

- Subject-Id: t0ovw6
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2271ca6b` in a lane worktree; the plan was authored against `98e3ea9a`, which is an
ancestor eight commits back. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent` conforms after revision
with zero findings. No pre-review snapshot was owed: the plan was committed and unmodified (added by
`8b6b168b`) with `git status --short` empty at review start, and it is byte-identical to the lane
input copy. The plan carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.
Every mutation this review ran was staged IN MEMORY via pytest plugins wrapping the function object,
and `git status --short` was verified empty after each; NO tracked file was edited to obtain any
measurement below.

THE DIAGNOSIS VERIFIED IN FULL, AND THE TWO CENTRAL GAPS REPRODUCE. This plan's premise is unusual and
correct: the backlog item it graduates is FALSIFIED (the lift already landed) and what actually
survives is the loss of the lift's guards. Every load-bearing measurement holds at this HEAD. F-01 and
F-04: `runner_shared.add_output_mode_flags` exists and both host wrappers are exactly one delegating
statement after the docstring strip (AST-probed: 1, 1, and 5 for the shared body). F-03: `rg
add_output_mode_flags tests/` is EMPTY, and no `refork` or `rununify` test file exists. F-05 and F-12:
all four subparsers render the correct host's text and none renders the other's, and both hosts give
`start` -> `0`, `resume` -> `None`. F-06: giving agy the opencode `verbose_help` leaves the suite at
`3069 passed, 2 skipped`, with the mutation verified to have bitten (agy renders `"diff hunks"`). F-07:
re-forking the oc body leaves it at `3069 passed, 2 skipped`. F-08: the both-hosts asymmetry mutation
fails exactly one node at `tests/test_agy_runipd_cli.py:1681`, and `tests/test_oc_runipd_cli.py` does
not exist. F-10, F-11 and F-15 are confirmed from backlog `39jkux`'s own text. So the plan's central
claim - that this symbol has two measured, unguarded regression paths and has already regressed once
in reality - is TRUE, and the route it proposes is right.

THE DOMINANT FINDING IS THAT E-01 IS UNEXECUTABLE AS WRITTEN, AND WOULD HAVE FAILED ON A CORRECT TREE.
E-01 demands the help text be pinned "BY VALUE" against the rendered `format_help()`. `argparse`
REFLOWS help to the terminal width, so NEITHER host's full `-v` sentence NOR oc's full `--raw` string
appears verbatim in any rendered output: measured `False` for all five combinations. oc's `-v` splits
mid-sentence and oc's `--raw` orphans `"(legacy behavior)"` onto a second line. An executor writing the
literal-substring pin the item describes gets a RED test on a correct tree, and the likely next move is
to weaken the assertion until it passes, which produces exactly the decorative guard this plan exists
to replace. Classified BLOCKER because the plan's lead deliverable cannot be implemented as specified.
Two replacement routes were PROBED, not reasoned about, and both work; E-01 now permits either and
requires the executor to declare which.

THE SECOND CLUSTER IS THAT E-04 UNDER-STATES ITS OWN WORK BY A LARGE FACTOR, TWICE OVER. The item
describes correcting "the two comments" and names one oc comment specifically. Measured: the two host
runners carry FOURTEEN such citations (oc 8, agy 6), and the repository carries TWENTY-SIX across SEVEN
files. Both errors bite. The first means an executor could correct the one named comment, leave
thirteen live false citations in the declared files, and still tick E-04 - reproducing the defect class
the plan is about. The second means E-04's Expected outcome as authored ("no comment in either host
runner cites it as a live guard") was fine but read alongside F-13's "14 hits across 3 files" invited a
package-wide reading that the declared scope cannot deliver, since `runner_shared.py` alone carries six
and is deliberately out of fence. All fourteen in-scope citations are now enumerated by surrounding
symbol, and the twelve-citation residue is declared with its carrier.

THE THIRD FINDING IS A SHARED-CHECKOUT HAZARD IN THE VALIDATION METHOD, and it is sharper here than in
the usual case because the plan's own gate names the hazard and then instructs it anyway: it calls
`runner_shared.py` and both hosts "high-contention files in a shared checkout" in the same paragraph
that tells the executor to edit all three and `git checkout` them back, around full-suite runs. Three
of the four mutation proofs are reachable in memory (demonstrated at review), and exactly ONE is not:
E-03's AST test reads source on disk, so its RED proof genuinely requires a file edit. That asymmetry
is now written down, with the file-edit case scoped to a narrowed single-node run.

TWO SMALLER BUT REAL CORRECTIONS. F-08's gap is WIDER than F-08 claims: an OC-only loss of the
`resume` default passes the FULL bare suite, not merely the agy test file, which is E-02's strongest
justification and also makes the mutation SCOPING in V-02 mandatory rather than a nicety (the
both-hosts form fails a pre-existing test and would let a useless E-02 look validated). And the
deferred row about stale citations in `tests/test_runner_shared.py` names two dead guards where the
comment names THREE; the third, `test_exactly_one_definition_package_wide`, is cited as living "below"
in that very file and does not exist anywhere, so a reader checking only the two named files would
conclude one guard still stood.

WHAT THIS REVIEW DID NOT CHANGE. The route is untouched: three additive tests plus a comment
correction, `tests/test_runner_shared.py` as the home (OQ-02), E-03's deliberate refusal to fingerprint
the shared body, the four deferral dispositions, and the decision to graduate the item by restoring
guards rather than closing it as already-fixed (OQ-01, which is well-argued and verified). All three
declared carriers (`pn7rw3`, `xvp5vx`, `s4jctz`) resolve to live `open` backlog items.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | BLOCKER | IN-SCOPE | E. Testing / G. Plan executability | Probe: full oc `-v` string `in format_help()` -> **False** on `start` and `resume`; full agy `-v` -> **False** on both; oc full `--raw` -> **False** on both; rendered lines `'  -v, --verbose         Increase live stream detail: -v also shows reads and'` and `'                        shows diff hunks and diagnostics. Ignored under'`; whitespace-normalized -> all five **True**; `action.help == expected` -> **True** both hosts | **E-01 IS UNEXECUTABLE AS WRITTEN AND WOULD BE RED ON A CORRECT TREE.** `argparse` reflows help text, so the "BY VALUE" pin against rendered `format_help()` cannot match any full help string. The executor's likely recovery is to weaken the assertion until it passes, producing the decorative guard this plan exists to replace. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (two working routes were demonstrated at review, so no uncertainty remains) | FIXED | E-01 rewritten with an explicit warning, the measurement, and TWO measured-working routes (whitespace-normalize the rendered text, or read `action.help` unwrapped), requiring the executor to declare which in V-01. Records which SHORT needles survive wrapping so the negatives stay simple. V-01(c) FAILS the item if a full string is asserted as a plain substring of raw `format_help()`. New F-16; OQ-03 records the decision as D-1. |
| PR-802 | HIGH | IN-SCOPE | Evidence accuracy / G. Plan executability | `rg -c "test_runner_refork_guard\|anti-re-fork"` -> `oc_runipd.py` 8, `agy_runipd.py` 6, `runner_shared.py` 6, `run_viewer.py` 1, `artifact_audit.py` 1, `tests/test_runner_shared.py` 1, `tests/fixtures/verifier_evidence_corpus.json` 1; total 26 across 7 files | **F-13 UNDERSTATES ITS OWN SUBJECT: 26 hits across SEVEN files, not "14 hits across 3 files".** Six are in `runner_shared.py`, which the plan deliberately keeps out of `- Scope-Paths:`, so E-04 closes 14 of 26 and the rest is residue. Left uncorrected, the count invites either a package-wide reading E-04 cannot satisfy within its fence, or an executor "finishing the job" into an out-of-fence file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 rewritten with the per-file breakdown and the 14-of-26 split; E-04 gained an explicit SCOPE BOUND naming the twelve out-of-scope citations and their carrier; the deferred row and Scope check's under-scope list both corrected from "the third citation" to twelve; V-04(c) requires pasting the residue count and confirming it is untouched; the gate's fence forbids the `runner_shared.py` sweep. |
| PR-803 | HIGH | IN-SCOPE | G. Plan executability | `rg -n` over both hosts with each hit classified by enclosing context: oc 8 (import-block identity note, `_read_id` noqa, re-export note, two `REFORK_TABLE` notes, "fails a test" note, `render_stream`-adjacent note, `locked_run` note above `_detect_driver_command`); agy 6 (import note, "requires of BOTH runners", `_read_id` noqa, `test_the_oc_to_agy_import_count_did_not_increase`, `REFORK_TABLE` note, `dispatch_orchestrator_item`-adjacent note) | **E-04 UNDER-STATES ITS OWN EDIT EIGHTFOLD ON THE OC SIDE.** It names "the comment above `_detect_driver_command`" plus "the module-level comments" for agy, where oc carries eight citations and agy six. An executor correcting the one named comment leaves thirteen live false citations and can still mark E-04 complete - which IS the defect class this plan exists to fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (mechanical once enumerated) | FIXED | E-04 rewritten to enumerate all fourteen by surrounding symbol (deliberately not by line offset, per the plan's own convention), and to require that each correction KEEP the reasoning while fixing the citation, explicitly refusing a fix that merely drops the filename. Expected outcome restated as all fourteen. V-04(b) requires accounting for all fourteen and saying which was not found if the count differs. New F-19. |
| PR-804 | HIGH | IN-SCOPE | E. Testing and verification | Bare `python3 -m pytest` at review on a clean tree -> `3069 passed, 2 skipped, 3 warnings in 41.44s`; authored F-09 `2935 passed, 2 skipped` at `98e3ea9a`; `git merge-base --is-ancestor 98e3ea9a HEAD` true; `tests/test_runner_shared.py -o addopts=""` -> `101 passed`; `tests/test_agy_runipd_cli.py -o addopts=""` -> `58 passed` | **THE AUTHORED BASELINE IS SPENT BY 134 TESTS**, and V-01(b) demands the delta be "accounted for entirely by added tests", which an executor could not do against a stale aggregate with no per-file figures. Unlike several sibling plans the tree IS fully green, so the bar is genuinely zero failures - worth stating, because the executor would otherwise not know whether a red is theirs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 and the Required tests preamble carry the re-measured baseline, the ancestry note, the fully-green statement, and two per-file baselines. V-01(a) and V-01(b) now cite them, and V-01(b) requires the delta stated per E-item. |
| PR-805 | HIGH | IN-SCOPE | B. Security / C. Operability (shared-checkout safety) | The plan's own gate sentence calling all three files "high-contention files in a shared checkout" beside its instruction to edit and revert them; AGENTS.md shared-checkout rule; review demos: `add_output_mode_flags` wrapper (GAP 1, agy renders `"diff hunks"`), caller-scoped wrapper (E-02, OC-only), `_add_output_mode_flags` rebinding (GAP 2 runtime), each with `git status --short` empty | **ALL THREE MUTATION PROOFS INSTRUCT EDITING TWO HOST RUNNERS AND `runner_shared.py` IN A SHARED CHECKOUT**, with `git checkout` restores around minute-long suite runs, in a plan that names that exact hazard one paragraph earlier. A restore discards a co-worker's concurrent edit to those files. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | Required tests gained a METHOD RULE mandating in-memory staging with the mechanism named per proof, and identifying the ONE genuine exception: E-03's AST proof needs a real source edit (F-18), now scoped to a narrowed single-node run with an explicit `git checkout --` and `git status --short` step. `runner_shared.py` is forbidden as an on-disk mutation target. V-01, V-02 and V-03 each require the evidence its method implies; the gate and Scope check record the transient edit as expected and in-fence. |
| PR-806 | MEDIUM | IN-SCOPE | D. Anti-regression | Caller-scoped mutation at `REV10_F08_SCOPE=oc` -> `3069 passed, 2 skipped, 3 warnings in 41.87s` (zero failures); at `both` -> `1 failed, 4 passed` on the narrowed agy file | **F-08 UNDERSTATES ITS OWN GAP, AND THE TRUE VERSION IS E-02'S BEST ARGUMENT.** "The OC host losing its `resume` default alone would pass" reads as passing one test; it passes the ENTIRE suite. One host's regression on a load-bearing asymmetry is invisible to 3069 tests. This also makes V-02's mutation scoping MANDATORY: the both-hosts form fails a pre-existing test, so it would show a RED that E-02 did not cause and let a useless E-02 look validated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-17 with both measurements; E-02 carries the corrected statement and its Expected outcome now says "an OC-only loss passes the whole suite"; V-02 requires the OC-scoped mutation and states in terms why the both-hosts form does not discharge it. |
| PR-807 | MEDIUM | IN-SCOPE | D. Anti-regression / E. Testing | Rebinding `oc_runipd._add_output_mode_flags` to a directly-registering body -> `3069 passed, 2 skipped, 3 warnings in 47.02s`; AST probe under the rebinding confirming the on-disk shape is unchanged | **E-03'S AST GUARD CANNOT SEE A RUNTIME RE-FORK, WHICH IS THE EXACT MECHANISM THIS REVIEW USED TO MEASURE F-07.** Unstated, that leaves two hazards: a reader mistaking the AST test for a runtime guarantee, and an executor discharging V-03 with a monkeypatch that leaves the test green and proves nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the bound is accepted, not closed) | FIXED | New F-18 records the asymmetry and why the bound is ACCEPTED (a real re-fork arrives as a source edit; a rebinding is a harness technique). E-03 must state it in its docstring; V-03(b) requires a REAL source edit and says a monkeypatch does not discharge the item; V-03(c) requires pasting the docstring sentence; F-07's own row now carries the method bound so its two measurements are not conflated. |
| PR-808 | MEDIUM | UNDER-SCOPE | Evidence accuracy | `rg -n "def test_exactly_one_definition" tests/` -> no match (exit 1); `rg -n "exactly_one_definition" tests/` -> only the citing comment at `tests/test_runner_shared.py:313`; `runner_shared.py:323` repeating the same citation | **THE DEFERRED ROW NAMES TWO DEAD GUARDS WHERE THE COMMENT NAMES THREE.** The `SUPERSEDED_SINCE_MOVE` block cites `test_runner_refork_guard.py`, `test_rununify_run_queue.py`, and `test_exactly_one_definition_package_wide` "below". The plan records the first two as deleted. The third does not exist either, and is cited as living in that very file, so a reader who checked only the two named files would conclude one guard still stood. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-20 with the measurement. The deferred row now states all three are dead and that whoever corrects the comment must correct three claims, not two; Scope check's under-scope list carries it. Left DEFERRED as work (correctly - its subject symbol is out of scope and it is carried by `pn7rw3`); only the plan's description of it is corrected. |
| PR-809 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | The authored gate: no declared scope fence, no out-of-scope-edit disposition, no finalize-ownership statement; workflow Step 4 execution-contract requirement | THE GATE LACKS THREE EXECUTION-CONTRACT ELEMENTS: a DECLARED fence (so the runner can reconcile afterwards), a disposition for an out-of-scope edit (the make-then-justify rule, per the 2026-09-01 ruling), and a statement of who performs the terminal transition, risking a double finalize under `aw oc run`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained a declared SCOPE FENCE naming the three files with three load-bearing negative constraints (never commit or edit `runner_shared.py`; never weaken an existing test in the harness or fingerprint the shared body; never sweep the twelve out-of-fence citations), the make-then-justify disposition citing `--scope-reason`/`--scope-ack`, a LIFECYCLE TRANSITION paragraph with conditional ownership, and a WHAT THE HUMAN IS APPROVING paragraph. |
| PR-810 | LOW | IN-SCOPE | E. Testing and verification | V-01(b) as authored ("a count increased by exactly the number of added tests") against a single stale aggregate; review per-file baselines `101 passed` and `58 passed` | THE "EXACTLY N ADDED TESTS" BAR WAS UNVERIFIABLE as written: with only a stale aggregate and no per-file figure, an executor cannot show which file the delta came from, and a silently-lost existing test would net out against added ones. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Per-file baselines measured and recorded in F-09 and Required tests; V-01(a) states the targeted count against `101 passed` and V-01(b) requires the aggregate delta stated per E-item. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's "BY VALUE" pin is red on a correct tree because argparse reflows. Which mechanism replaces it? | PERMIT EITHER of two DEMONSTRATED routes (whitespace-normalized rendered text, or unwrapped `action.help`), requiring the executor to declare which in V-01. | (a) Mandate one route - rejected: the two differ in a real trade the executor is better placed to weigh (route (a) also catches a formatter change that mangles operator-visible text; route (b) is immune to terminal width in CI), and both detect the F-06 regression, which is the property that matters. (b) Weaken the assertion to the short distinctive substrings only - REJECTED outright: the negatives alone would pass a mutation that rewrote the rest of a host's sentence while keeping its distinctive phrase, which is a guard that cannot fail for most of what it claims to cover. | Probe measuring all five full-string containments False against raw `format_help()`, all five True normalized, and `action.help == expected` for both hosts; the two rendered wrapped lines quoted | yes |
| D-2 | Three mutation proofs instruct editing high-contention tracked files in a shared checkout. Mandate in-memory staging for all, or keep file edits? | IN-MEMORY for three, with ONE explicit exception for E-03's AST proof, which genuinely requires a source edit. | (a) Keep file edits with a louder warning - rejected: the plan ALREADY warns in the same paragraph and instructs the edit anyway, so a warning demonstrably does not prevent it; the hazard is a co-worker's edit being reverted, which no instruction to the executor addresses. (b) Mandate in-memory for ALL FOUR - rejected on measurement: E-03 asserts over the AST on disk, so a rebinding leaves it green (measured `3069 passed`) and would let V-03 be discharged by evidence that proves nothing. | AGENTS.md shared-checkout rule; the plan's own high-contention sentence; three in-memory demos with `git status --short` empty; the rebinding measurement showing the AST test blind to it | yes |
| D-3 | F-08's gap is stated as one-test-file when it is whole-suite. Correct F-08 in place, or add a row? | ADD F-17 and correct E-02's and V-02's statements, keeping F-08's original text. | (a) Rewrite F-08 only - rejected: F-08's structural analysis (agy-only `assertIsNone`, `start`-only cross-host loop, missing mirror file) is correct and worth preserving verbatim; the correction is an additional measurement, not a repudiation. (b) Leave it, since the conclusion is unchanged - rejected: the understatement makes V-02's mutation SCOPING look optional when it is load-bearing, since the both-hosts form fails a pre-existing test. | The scoped mutation runs at `oc` (3069 passed) and `both` (1 failed); the test's assertion targets read in place | yes |
| D-4 | E-04's citation count is wrong and the residue spans out-of-fence files. Widen the fence, or bound the item? | BOUND the item to the two declared host files and DECLARE the twelve-citation residue with its existing carrier. | (a) Add `runner_shared.py` to `- Scope-Paths:` to fix all 26 - rejected: it is the most contended file in the repository, the plan's whole premise is that it changes NO shipped behavior, and six comment edits there would multiply the blast radius of a documentation fix for no measured benefit. (b) Leave the count wrong since the Expected outcome already said "either host runner" - rejected: F-13's "14 hits across 3 files" beside that wording invites a package-wide reading the fence cannot deliver. | `rg -c` per-file breakdown totalling 26 across 7 files; backlog `pn7rw3` resolving `open`; the plan's own gate rationale for excluding `runner_shared.py` | yes |
| D-5 | The deferred stale-citation row names two dead guards; a third is also dead. Note it, or leave the row? | NOTE IT as F-20 and sharpen the deferred row, without taking the work into scope. | (a) Take the correction into scope as a new E-item - rejected: the comment's subject symbol is `should_color`, which this plan does not touch, and `pn7rw3` already carries it. (b) Say nothing, since the row already defers the file - rejected: the row asserts a specific count of dead guards, and a reader who verified the two named files would wrongly conclude the third guard stands. | `rg "def test_exactly_one_definition" tests/` no match; the only hit being the citing comment; the parallel dead citation in `runner_shared.py` | yes |

### Deferred and open

None. Every finding is FIXED. No finding was left OPEN or DEFERRED, so no escalation to a
`- Blocking: yes` open question is owed under the repository's `HIGH` gate threshold (note PR-801 is a
BLOCKER by severity and was FIXED in place, not deferred). The plan's two pre-existing open questions
(OQ-01, OQ-02) were already `resolved` and both were re-verified at review rather than accepted;
OQ-03 was added to record decision D-1 in the plan itself. No decision above carries `Reversible: no`,
so no maintainer escalation is owed on that axis.

FINAL GATES: `aw ipd lint --phase review-finalize --agent` exit 0 `findings: 0`;
`check_engine.evaluate_durable_carrier` returns zero drifts for this plan (checked directly, because a
prose-bearing `- Carrier:` line is a known way to break that rule); `aw check` unchanged at its 5
pre-existing findings with none on this plan; `aw sanitize --agent` clean; `git status --short` showing
exactly the plan (modified) and this review record (new), with every throwaway probe removed.
