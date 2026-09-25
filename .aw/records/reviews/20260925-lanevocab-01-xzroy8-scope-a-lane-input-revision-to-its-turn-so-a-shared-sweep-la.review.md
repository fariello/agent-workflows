# Review: Scope a lane input revision to its turn so a shared sweep lane attaches the right plan

- Subject-Id: xzroy8
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4ae7cb05`, in the review sweep lane. The target plan was committed and unchanged (the
lane's rev-1 materialized copy is byte-identical to the tracked file), so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) before review; `--phase review-finalize --agent` reports `conforming` (exit 0)
after every edit below, including the E/V renumbering.

THE PLAN IS CORRECT AND ITS FIX IS THE RIGHT SHAPE, AND I DID NOT TAKE THAT ON ITS WORD. I reproduced
F-1 by driving the REAL `oc_runipd.run_opencode` against a scratch lane holding rev-3 (plan A) and rev-5
(plan B), with an item recording `lane_input_revision: 3`. The single `--file` value came back as
`.../rev-5/plan-planB.ipd.md` with bytes `# PLAN B`, while the turn's own manifest entry was
`.aw/state/lane-inputs/rev-3/plan-planA.ipd.md`. So a reviewing agent is handed another plan's file,
which is the worst available failure of a review sweep: the review it produces is confidently about the
wrong artifact. I also drove the ordering claim rather than reading it, and the chain holds exactly as
the plan describes: with `aaaaaa` at position 3 declaring a dependency on `bbbbbb` at position 5,
`dependency_depth` returns 1 and 0 and `queue_sort_key` dispatches `(bbbbbb, 5)` first, so
`revision=int(item["position"])` materializes 5 before 3 and "latest" becomes the wrong turn's.

THE MOST IMPORTANT THING I CHANGED IS PR-001: E-01, THE PLAN'S FIRST ITEM AND THE GATE ON EVERYTHING
ELSE, COULD NOT RUN WHERE THIS PLAN EXECUTES. It required probing `.aw/records/runs/*/state.json` and
said "if there are none, stop and report: the defect has moved". That tree is GITIGNORED
(`.aw/.gitignore:14`) and a lane worktree resolves it to its own nonexistent copy: measured, a bare glob
returns 0 from this lane while `runner_shared.runs_repo_root` plus `state_root` returns 265. Since every
execute item runs in a lane by default, the plan's own first item would have found zero mismatches and
instructed the executor to abandon a live defect. The package ships `runs_repo_root` for precisely this
reason and its docstring records the same measurement from lane `vddpml` (0 versus 246). I inverted the
dependency: the scratch reproduction I ran is now E-01 and authoritative, the corpus probe is E-02 and
explicitly corroboration whose absence is a pass.

PR-002 IS THE ONE THAT WOULD HAVE SHIPPED A TEST THAT CANNOT FAIL. E-02's second case was "an execute
item whose attempt has `lane_input_revision: 1` and a lane holding only rev-1 still attaches rev-1".
Measured: on a lane holding only rev-1, `revision=None` and `revision=1` both return `rev-1`. The case
is therefore identical before and after the fix and guards nothing. The guard that matters is the
opposite shape, and I measured it: with TWO revisions present and an attempt carrying NO
`lane_input_revision` key (or an empty attempts list), the attachment must still be `rev-2`. That case
fails if the executor writes `or 1` or `int(...)` around `turn_revision`, which is the single most likely
wrong implementation of E-05 and would attach position 1's plan to every non-materialized turn. E-04 now
carries it, plus a non-isolated case and a runbook case, since E-05 changes BOTH `localize_attachment`
calls and only the plan one was otherwise covered.

PR-003 RECORDS A CITATION TO A SYMBOL THAT DOES NOT EXIST. The conventions section asserted
"`lane_containment.lane_input_paths` already iterates `range(1, latest + 1)`". There is no
`lane_input_paths` anywhere in the package. The `range(1, latest + 1)` loop is in
`lane_containment.driver_written_lane_paths`. The substantive conclusion survives (teardown accounting
tolerates sparse out-of-order revisions and needs no change, which I verified by reading that function's
`continue` on a missing revision), but the plan's own conventions section is what an executor trusts
when it cannot find a symbol, so a wrong name there is worse than no name. This matters more than usual
here because the repository's own convention, recorded in this plan, is to cite by SYMBOL.

PR-004 WIDENS THE DOCSTRING WORK BECAUSE THE SCOPE CHECK ANSWERED THE WRONG QUESTION. The plan's scope
check said "the only product caller of `localize_attachment` is `oc_runipd.run_opencode`", which I
re-verified and is true. But the hazard is not the caller, it is the DEFAULT: five functions in
`lane_containment` take `revision: int | None = None` and all five resolve `None` to the latest on disk
(`read_lane_input_manifest`, `verify_link_independence`, `verify_lane_input_seal`,
`verify_lane_input_manifest`, `localize_attachment`). On a shared lane each verifier would silently
verify another turn's revision. They have no product caller today, so I did NOT ask for signature
changes; E-06 documents all five, which is the proportionate response to a latent hazard and is where a
future caller will read it.

PR-005 IS THE FINDING I DID NOT EXPECT TO MAKE. This plan amends acceptance criterion A12b, and A12b has
NO SHIPPED TEST. No test in `tests/` imports `lane_containment` for any R5 criterion at all. The file
that held A12, A12b (all three parts, including `test_part_iii_a_change_is_a_new_revision_not_an_edit`)
and A13 (including `test_both_attachments_are_localized`) was `tests/test_lane_input_manifest.py`, 444
lines and 21 tests, DELETED in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000
tests") along with 13 other lane test files. Had that file survived, `test_both_attachments_are_localized`
is plausibly the test that would have caught this defect. So the new test file this plan adds becomes
the ONLY shipped test of any part of R5. I deliberately did not put restoration in scope: the deletion
was an intentional suite-wide trim of 219,063 lines across 318 files, so reversing one file of it is a
decision about that trim, not about this defect. What I did require is that A12b SAY SO, because an
acceptance criterion that reads as covered while nothing enforces it is the more dangerous of the two
errors.

PR-006: OQ-01 ASKED A QUESTION THE TREE HAD ALREADY ANSWERED, AND ITS PREMISE WAS FALSE. It asked
whether `i4y84y` should be reclassified `chore` to `bug` and stated "the item stays `Work-Kind: chore` as
filed". The item on disk carries `- Work-Kind: bug` and `- Blocks-Release: next`, and its own history
line records the reclassification in the same commit (`7d42c93d`) that created this plan. This plan
already carries both fields, so the release gate is inherited and nothing was outstanding. Resolved from
evidence, not asked.

PR-007 rewrote the gate, which carried only a commit rule. It now states what a human is approving
(including that the spec is `approved` and this amends a live contract), the reproduced-at-review
evidence with the honest note that reachability is narrow (which is what makes `Priority: low`
defensible against a severe consequence), a per-path scope fence naming `runner_shared.py` and
`agy_runipd.py` as expected-unmodified, an honesty rule naming the three specifically fakeable claims,
two genuine stop conditions, and conditional runner/executor finalize ownership. I also added the
`19313eed`-anchored evidence requirement so PR-005's claim is checkable rather than asserted, and
required `python3 -c "import agent_workflows.lane_containment"` in V-06, since an unbalanced quote is the
one way a docstring-only edit breaks a module.

ON F-4, THE agy NON-AFFECTEDNESS CLAIM, which I checked because a "not affected" claim resting on a code
comment is the kind that rots: it holds on the code. `grep -n "\-\-file" agent_workflows/agy_runipd.py`
returns nothing, and `run_agy_turn` builds `[agy_bin, "-p", prompt_text, ...]`, passing its prompt inline.
The plan's evidence column cited the oc comment ABOUT agy rather than agy itself, which I replaced with
the argv construction.

One reproduction detail worth recording because it cost me a wrong result first: the dependency token
grammar is `executed:<id6>` or a BARE `<id6>`. `parse_dependency_token("ipd:bbbbbb")` returns `None`, so a
probe written with the obvious-looking `"ipd:"` prefix yields depth 0 for both items and silently fails
to reproduce the out-of-position dispatch. That is now a conventions bullet.

E and V were renumbered to a contiguous E-01..E-10 / V-01..V-10, because `aw ipd lint` refuses suffixed
ids (`IPD-I302`, `IPD-I305`) and the three additions had been written as E-01a/E-02a/E-05a.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / G. Plan executability (a gating item that cannot run where the plan executes) | Measured in this lane: `glob(".aw/records/runs/*/state.json")` -> 0, while `runs_repo_root(Path("."))` -> the main checkout and `state_root(...)` -> 265 `state.json` files; `.aw/.gitignore:14` ignores `records/runs/`; `runner_shared.runs_repo_root`'s docstring records the same failure from lane `vddpml` (0 vs 246) | E-01 GATED THE WHOLE PLAN ON A TREE THAT IS UNREACHABLE FROM A LANE AND UNTRACKED EVERYWHERE. It probed `.aw/records/runs/*/state.json` and instructed "if there are none, stop and report: the defect has moved". Every execute item runs in a lane by default, so the executor would have found zero mismatches and abandoned a live, reproducible defect on the strength of a missing gitignored corpus. The plan's own Concern also rests the defect's existence on "measured in recorded runs", which is evidence no executor can re-derive. | C:Low; U:Low; S:Low; F:Medium (a live defect abandoned on absent local scratch); Overall:Low | FIXED | E-01 is now the deterministic scratch reproduction I ran (authoritative, tree-independent); the corpus probe is E-02, explicitly corroboration, required to resolve the root through `runs_repo_root` and to print `corpus unavailable: <path>` when absent, with absence and zero-mismatch both stated as passes. V-01/V-02 split accordingly. Concern and conventions record the resolver and the gitignore. |
| PR-002 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing (a no-regression case that cannot fail) | Measured: on a lane holding only rev-1, `localize_attachment(..., revision=None)` and `(..., revision=1)` both return `rev-1`. Measured with two revisions and no recorded revision: `attempts=[]` and `attempts=[{}]` both return `rev-2/plan-B.md` | E-02'S SECOND CASE GUARDS NOTHING AND HIDES THE ONE THAT MATTERS. "An execute item whose attempt has `lane_input_revision: 1` and a lane holding only rev-1 still attaches rev-1" is byte-identical before and after the fix, so it cannot fail. The regression this change can actually cause is the opposite: coercing a missing `lane_input_revision` (`or 1`, `int(...)`) so a non-materialized turn attaches position 1's plan. Three live call sites reach `run_opencode` with no recorded revision (`oc_runipd.audit`, which appends its attempt only AFTER launch; a `--no-isolate-worktree` turn; and the defect re-ask, which does carry the key). None was named. | C:Low; U:Low; S:Low; F:Medium-High on the tested property (a coercion bug ships with a green suite); Overall:Low (the fix is a better test, not a design change) | FIXED | E-04 replaces the inert case with three that can fail: (a) two revisions plus an absent recorded revision must still attach the LATEST, in both the empty-list and missing-key shapes; (b) a non-isolated turn attaches `fallback` unchanged; (c) the runbook attachment localizes to the same turn revision, since E-05 changes both call sites. E-05 names the three no-revision call sites and forbids defaulting to 1; V-05 requires the diff to show no coercion; a stop condition covers it. |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability (a cited symbol that does not exist) | `grep -rn "lane_input_paths" agent_workflows/ tests/` returns nothing; the `range(1, latest + 1)` loop with a `continue` on a missing revision is in `lane_containment.driver_written_lane_paths` | THE CONVENTIONS SECTION CITES A NONEXISTENT SYMBOL. It asserts "`lane_containment.lane_input_paths` already iterates `range(1, latest + 1)`". No such function exists. The conclusion it supports is correct (teardown accounting tolerates sparse, out-of-order revisions), but the conventions section is exactly what an executor trusts when a symbol is not where the plan says, and this plan's own last conventions bullet mandates citing by SYMBOL. A wrong name there teaches the executor to distrust the section or to invent a replacement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bullet is rewritten as an explicit CORRECTION naming `driver_written_lane_paths`, keeping the substantive conclusion and stating plainly that only the function name was wrong. Added bullets for `attachment_values`/`attachments_outside_lane` and for the `runs_repo_root` resolver so tests and probes reach for the right symbols. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Architecture (the hazard is the default, not the caller) | `grep -n "revision: int \| None = None" agent_workflows/lane_containment.py` -> lines 2604, 2665, 2750, 2814, 3072, i.e. `read_lane_input_manifest`, `verify_link_independence`, `verify_lane_input_seal`, `verify_lane_input_manifest`, `localize_attachment`; no product caller of the four verifiers exists outside the module | THE DOCSTRING FIX WAS SCOPED TO THE CALLER CENSUS RATHER THAN TO THE DEFAULT. E-04 covered `localize_attachment` and `read_lane_input_manifest`; the scope check justified stopping there because `run_opencode` is the only product caller. But the latent trap is the SHARED `revision=None` means latest default, which three verifier functions also carry: on a shared lane each would verify another turn's revision and report conformance about the wrong input set. A caller census is the wrong test for a hazard that bites the next caller. | C:Low; U:Low; S:Low; F:Medium (a verifier silently attesting to another turn's inputs); Overall:Low | FIXED | E-06 now documents all five readers with line numbers; F-5 records the census and that the four verifiers have no product caller today; the scope check is rewritten to say the caller question was the wrong one and why; narrowing the four signatures is recorded as Deferred with the reason (latent, not live). |
| PR-005 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing (amending a criterion nothing enforces) | `git show 19313eed --stat` lists `tests/test_lane_input_manifest.py \| 444 ----` plus 13 other lane test files, total 219,063 deletions across 318 files; the deleted file's 21 tests include `test_part_iii_a_change_is_a_new_revision_not_an_edit` and `test_both_attachments_are_localized`; `grep -rn "lane_input\|materialize_lane_inputs" tests/` returns nothing today | THE PLAN AMENDS A12b WHILE A12b HAS NO SHIPPED TEST, AND NOTHING SAYS SO. No test in `tests/` exercises any R5 criterion: the file that held A12, all three parts of A12b, and A13 was deleted in `19313eed`. `test_both_attachments_are_localized` is plausibly the test that would have caught this very defect. So the new file becomes the ONLY R5 coverage, and an amended A12b reads as a covered criterion when it is aspirational. | C:Low; U:Low; S:Low; F:Medium (a contract believed enforced); Overall:Low | FIXED | E-08 requires A12b to name `19313eed` and state which of its parts has no shipped test; V-08 requires the `git show` output anchoring the claim. Restoration is recorded as Deferred with its reason (reversing one file of a deliberate suite-wide trim is a decision about the trim, not about this defect) and a note that a separate backlog item is the right carrier, deliberately not filed by this review. |
| PR-006 | LOW | IN-SCOPE | G. Plan executability (an open question whose premise is false) | Item front matter: `- Work-Kind: bug`, `- Blocks-Release: next`; its history line "2026-09-25 graduated (aw set): ... reclassified bug: a sweep review was handed another plan's file in 4 recorded reviews"; commit `7d42c93d` message lists `i4y84y` under "Reclassified bug + Blocks-Release next on measurement"; this plan already carries both fields | OQ-01 ASKS THE MAINTAINER SOMETHING THE TREE ALREADY ANSWERED, ON A FALSE PREMISE. It asks whether `i4y84y` should be reclassified `chore` to `bug` and states "the item stays `Work-Kind: chore` as filed". The item was reclassified `bug` with `- Blocks-Release: next` in the same commit that created this plan. Asking spends a maintainer turn on a settled question and, worse, the false premise would invite someone to "fix" a classification that is already correct. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 set `- Status: resolved` with the item's own front matter, history line and commit cited, and a plain statement that the authored premise was stale and no action is needed. F-3 rewritten to record that the reclassification already happened. The gate states the gate is inherited and the item closes with `--evidence`. |
| PR-007 | LOW | UNDER-SCOPE | G. Plan executability (execution contract, baselines, fallback hazard) | Plan gate as authored: one sentence, no fence, no stop conditions, no honesty rule, unconditional finalize; V-02's evidence was a bare failing-test claim; V-06/V-07 had no pre-change baseline; measured `revision=99` -> the main-checkout fallback path, which `attachments_outside_lane` flags | THE GATE CARRIED ONLY A COMMIT RULE, THE VALIDATION HAD NO BASELINES, AND A NEW HAZARD WAS UNDOCUMENTED. No scope fence, so an out-of-scope edit could not be reconciled; no statement of what approval means for an amendment to an APPROVED spec; no stop conditions. V-02 accepted a bare failure, which cannot distinguish the defect from a broken test. V-06 had no before-count, so a pre-existing failure would read as caused by this change. And passing an explicit `revision` newly makes the out-of-lane `fallback` reachable (a revision the lane does not hold resolves to MAIN's plan path, an R5.3 violation), which nothing mentioned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with an approval paragraph (the live-contract spec amendment, the reproduced evidence, why narrow reachability makes `low` defensible against a severe consequence), a per-path scope fence naming `runner_shared.py`/`agy_runipd.py` as expected-unmodified, an honesty rule naming the three fakeable claims, two genuine stop conditions, and conditional runner/executor finalize ownership. V-03 must quote the failing assertion; V-09 requires a `<before> -> <after>` baseline; V-10 forbids `-n0`/`-qq`/`-p no:randomly`; V-06 adds an import check. F-7 records the fallback hazard and E-06 must document it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's probe returns nothing in a lane and the corpus is gitignored. Leave it as the gating item, or restructure? | Invert it: make the deterministic scratch reproduction E-01 and authoritative, demote the corpus probe to E-02 corroboration whose absence is an explicit pass. | (a) Leave E-01 as written and add a caveat - rejected: the item's own instruction is "stop and report: the defect has moved", so a caveat elsewhere loses to the imperative an executor reads at the item. (b) Delete the corpus probe entirely - rejected: the 4 recorded mismatches are the reason this was reclassified `bug`, and a reachable corpus is real evidence worth printing when present. (c) Require the executor to run outside the lane - rejected: it contradicts the lane contract and the runner isolates by default. | measured 0 from the lane vs 265 through `runs_repo_root`; `.aw/.gitignore:14`; `runs_repo_root`'s own docstring measurement from lane `vddpml`; my own scratch reproduction of F-1 | yes |
| D-2 | The plan's proposed no-regression case (single-owner lane, rev-1 only) cannot fail. Accept it, or design cases that can? | Replace it with the two-revision absent-revision cases, plus non-isolated and runbook cases, and forbid coercing a missing revision. | (a) Keep it - rejected: measured identical before and after, so it is decoration that makes the suite look protective. (b) Add only the two-revision case - rejected: E-05 changes BOTH `localize_attachment` calls and the runbook one would otherwise have no coverage at all. (c) Require the executor to test every no-revision call site end to end - rejected as over-scope: the unit-level `None` assertion pins the property, and `tests/test_defect_report.py` already drives the re-ask path. | measured `revision=None` == `revision=1` == `rev-1` on a single-revision lane; measured `attempts=[]` and `attempts=[{}]` both -> `rev-2`; the three no-revision call sites read in `oc_runipd` and `runner_shared` | yes |
| D-3 | A12b, which this plan amends, has no shipped test because `19313eed` deleted the 21-test R5 file. Restore it, amend silently, or record the hole? | Record the hole in A12b itself, naming the commit, and keep restoration out of scope. | (a) Restore `tests/test_lane_input_manifest.py` - rejected: reversing one file of a deliberate 219,063-line trim across 318 files is a decision about that trim, and bundling it turns a focused one-consumer fix into a test-policy argument. (b) Amend A12b without mentioning coverage - rejected: an amended criterion reads as enforced, and believing a contract is tested when it is not is the more dangerous error. (c) File a backlog item from this review - rejected: a review must not create the work it then cites as the carrier; the maintainer decides. | `git show 19313eed --stat`; the deleted file's test names including `test_both_attachments_are_localized`; `grep -rn "lane_input" tests/` -> nothing | yes |
| D-4 | The plan cites `lane_containment.lane_input_paths`, which does not exist. Correct it silently, or record it? | Record it as an explicit CORRECTION bullet naming `driver_written_lane_paths`, keeping the conclusion. | (a) Silently rename - rejected: the plan's own convention is to cite by symbol, and a reader who later finds the discrepancy in git history cannot tell whether the conclusion was also wrong. (b) Delete the bullet - rejected: the conclusion it carries (sparse revisions need no teardown change) is correct, load-bearing for the Deferred re-key decision, and verified. | `grep -rn "lane_input_paths"` -> nothing; the `range(1, latest + 1)` loop with `continue` in `driver_written_lane_paths` | yes |
| D-5 | Four other `revision`-defaulting readers share the hazard but have no product caller. Change signatures, document, or ignore? | Document all five in E-06; record signature narrowing as Deferred. | (a) Narrow the four signatures to a required argument - rejected: no product caller exists, so it is unobservable churn inside a plan whose whole virtue is a two-line consumer fix. (b) Document only the two the plan named - rejected: the hazard is the shared default, not the current caller, so the next caller reads whichever docstring it happens to open. (c) Add tests for the verifiers - rejected as over-scope: nothing calls them, so a test would pin behavior no product path depends on. | the five `revision: int \| None = None` signatures at lines 2604, 2665, 2750, 2814, 3072; no caller outside the module | yes |
| D-6 | OQ-01 asks the maintainer about a reclassification the tree already made. Ask anyway, or resolve? | Resolve from the tree and record that the authored premise was stale. | (a) Ask the maintainer - rejected: the repository rule is not to ask what the repository already answers, and the item, its history line and the commit message all record the reclassification. (b) Leave it open as harmless - rejected: it carries a FALSE statement ("stays `Work-Kind: chore` as filed"), which could prompt someone to change a correct classification. | item front matter `- Work-Kind: bug` / `- Blocks-Release: next`; its 2026-09-25 history line; commit `7d42c93d` | yes |
| D-7 | Passing an explicit `revision` newly makes the out-of-lane `fallback` reachable (an R5.3 violation). Fix it here, or document? | Document it in E-06 and require callers to pass only a revision they materialized; do not change the fallback. | (a) Make `localize_attachment` raise on an unheld revision - rejected: the fallback is deliberate and documented ("attaching nothing would silently drop an input the turn was designed to have"), and changing a shared containment primitive is out of proportion to a two-line consumer fix. (b) Ignore it - rejected: before this plan, `revision` was never passed, so the path was unreachable in the product; the plan makes it reachable and owes the reader that. | measured `revision=99` -> the main-checkout path, flagged by `attachments_outside_lane`; `localize_attachment`'s "FALLBACK IS DELIBERATE" paragraph; spec R5.3 | yes |
