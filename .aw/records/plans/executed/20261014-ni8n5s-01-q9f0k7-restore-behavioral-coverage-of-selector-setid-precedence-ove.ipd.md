# IPD: Restore behavioral coverage of selector setid precedence over filename substring

- Date: 2026-10-14
- Kind: child
- Concern: The frozen selector precedence (`setid` and `status` outrank the filename `stem` and `substring` rules) has no live behavioral guard since `tests/test_selector_zero_open.py` was deleted in `19313eed`.
- Scope: Add one new outcome-only test module that drives `selectors.resolve` on temporary fixture trees and asserts which rule wins when a token is both a Set id (or Status) and a filename fragment; repoint the stale "no live guard" code comment in `agent_workflows/selectors.py` to the new module.
- Scope-Paths: tests/test_selector_precedence_outcomes.py, agent_workflows/selectors.py, .aw/records/plans/pending/20261014-ni8n5s-01-q9f0k7-restore-behavioral-coverage-of-selector-setid-precedence-ove.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ni8n5s
- Set: ni8n5s
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: q9f0k7

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: q9f0k7 verified (set ni8n5s, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-ni8n5s-01-q9f0k7)
- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored from backlog ni8n5s; review-ready.

## Goal

Restore behavioral coverage of the selector precedence property recorded as site S-26 in plan `ev7t1w` (`RETIRE-UNGUARDED`): when a token is simultaneously a Set id and a filename fragment, `selectors.resolve` must return the `setid` match, not the `substring` match. The restored tests exercise the resolver and assert on its returned `Resolution`, never on source text or on the `_PRECEDENCE` tuple (GUIDING_PRINCIPLES P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Outcome tests

- [x] E-01 Create `tests/test_selector_precedence_outcomes.py` (`unittest.TestCase`, `tempfile.TemporaryDirectory` cleaned up in `tearDown`, no `slow`/`livecorpus` marker, following `tests/test_selector_two_dialect_readers.py`) with a temporary-repo fixture (plans tree under `.aw/records/plans/pending/`, several plans declaring `- Set: demo`, plus one colliding plan declaring `- Set: other` whose FILENAME contains `demo`) and a test asserting `selectors.resolve(root, "plans", "demo")` returns `kind == selectors.MATCH_SETID`, contains every `Set: demo` plan, and excludes the colliding file.
  - Depends on: none
  - Expected outcome: The test passes against the current resolver and would fail if `substring` were evaluated before `setid`.
  - Execution state: performed

- [x] E-02 In the same module add (a) a `status`-over-`substring` collision test (a token, e.g. `approved`, that is a declared `- Status:` value of some plans, is NOT any plan's `- Set:` value, AND is a fragment of another plan's filename resolves with `kind == selectors.MATCH_STATUS` and excludes the filename-only hit), and (b) a fall-through test: a token that is a filename fragment only (no record declares it as Set or Status) resolves with `kind == selectors.MATCH_SUBSTRING` to exactly that file, proving the setid result above came from precedence and not from substring being broken.
  - Depends on: E-01
  - Expected outcome: Three behavioral tests in the module, all asserting on `Resolution.kind` and `Resolution.paths` only; no `inspect`, `ast`, regex over source, or reference to `selectors._PRECEDENCE`.
  - Execution state: performed

- [x] E-03 Prove the setid test is falsifiable: rebind `selectors._PRECEDENCE` IN PROCESS (never edit `selectors.py` and never use a scratch copy of the module, which the test would not import) so `MATCH_SUBSTRING` precedes `MATCH_SETID`, then run the E-01 test in that same process, e.g. `python3 -c "import pytest; from agent_workflows import selectors as s; s._PRECEDENCE=(s.MATCH_PATH, s.MATCH_ID6, s.MATCH_SUBSTRING, s.MATCH_SETID, s.MATCH_STATUS, s.MATCH_STEM); raise SystemExit(pytest.main(['-o', 'addopts=', '-q', 'tests/test_selector_precedence_outcomes.py', '-k', '<setid test name>']))"`, and observe it FAIL. `resolve` reads the module global `_PRECEDENCE` at call time, so the rebind takes effect. Nothing from this probe is committed or written to disk.
  - Depends on: E-02
  - Expected outcome: Captured failing pytest output under the reordered precedence; `git diff --stat agent_workflows/selectors.py` prints nothing (E-04 not yet applied).
  - Execution state: performed

### Task group 2: Comment repoint and commit

- [x] E-04 Edit the `_PRECEDENCE IS FROZEN AS SEMANTICS` comment in `agent_workflows/selectors.py` (the paragraph reading "Formerly pinned by `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` (deleted in `19313eed`; no live guard currently asserts this)") so it names `tests/test_selector_precedence_outcomes.py` as the live behavioral guard, keeping the historical reference. Comment-only change; then run the bare suite and commit via `aw commit q9f0k7 -- tests/test_selector_precedence_outcomes.py agent_workflows/selectors.py`.
  - Depends on: E-03
  - Expected outcome: Comment updated, no code change in `selectors.py`, bare suite passes, single path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- GUIDING_PRINCIPLES P16 and AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert on outputs. The deleted `PrecedenceForcesFrontMatterReadsTests.test_precedence_places_filename_rules_last` read `selectors._PRECEDENCE` indices, a structure pin; it is deliberately NOT restored. Its `test_a_filename_query_still_reads_because_earlier_rules_must_lose_first` asserted open counts via patched `builtins.open`, an implementation-cost proxy; also not restored (out of the backlog item's stated property).
- Precedent for this exact restoration style: `tests/test_selector_two_dialect_readers.py` (module docstring cites the same deleted file and restores only outcomes on temp fixtures, no `slow`/`livecorpus` marker).
- Resolver contract: `selectors.resolve` docstring, "Precedence (first rule that yields matches wins)": path, id6, setid, status, stem, substring; constants `selectors.MATCH_SETID`, `selectors.MATCH_STATUS`, `selectors.MATCH_SUBSTRING` are the public result kinds carried on `Resolution.kind`.
- Suite runs bare: `python3 -m pytest` (AGENTS.md repo-local contract); commits through `aw commit`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The property lost is setid-over-substring precedence. | `git show 19313eed^:tests/test_selector_zero_open.py`, `PrecedenceForcesFrontMatterReadsTests.test_a_token_can_be_both_a_setid_and_a_filename_fragment` resolved `"demo"` with a colliding `...-dd0001-demo-shaped-name.ipd.md` and asserted `MATCH_SETID`. |
| F-02 | Plan `ev7t1w` classified site S-26 `RETIRE-UNGUARDED`. | `ev7t1w` disposition table row S-26: "tested setid outranking substring in selector resolution; deleted in `19313eed`". |
| F-03 | No live test asserts this today. | `rg -n "MATCH_SUBSTRING" tests/` is empty; `tests/test_selector_two_dialect_readers.py` asserts `MATCH_SETID` only on non-colliding YAML research fixtures. |
| F-04 | The source comment explicitly records the gap. | `agent_workflows/selectors.py` comment: "no live guard currently asserts this". |

## Proposed changes (ordered, validatable)

1. E-01/E-02: new module `tests/test_selector_precedence_outcomes.py` with three outcome tests.
2. E-03: one-off falsifiability probe (not committed).
3. E-04: comment repoint in `agent_workflows/selectors.py`, bare suite, commit.

## Deferred / out of scope (with reason)

- Read-cost/open-count assertions from the deleted file (E-05 of `e32j35`): a cost proxy, not the backlog item's property, and borderline P16.
  - Carrier-Declined: an implementation-cost proxy that P16 discourages; not an outstanding obligation.
- `id6`-over-`setid` and `stem`-over-`substring` orderings: not named by the backlog item; can be filed separately if wanted.
  - Carrier-Declined: backlog `ni8n5s` scopes this work to setid-over-substring (site S-26); no defect is known in the other orderings, which the maintainer can file separately if wanted.
- Any change to resolver behavior: the property is restored as-is.
  - Carrier-Declined: deliberate non-goal (coverage restoration only), not an outstanding obligation.

## Scope check

- Over-scope: none. The `selectors.py` edit is comment-only and removes a now-false statement.
- Under-scope: none. The backlog item's single property (setid precedence over filename substring) is covered by E-01, with E-02 adding the status sibling and the fall-through control that make E-01 meaningful.

## Required tests / validation

- `python3 -m pytest tests/test_selector_precedence_outcomes.py -o addopts="" -v` shows the setid-collision, status-collision and substring fall-through behaviors each passing (test count and names are pointers, not the bar).
- Falsifiability probe (E-03, in-process rebind) shows the setid test failing under reordered precedence.
- Bare `python3 -m pytest` passes.
- `aw ipd lint` on this plan conforms.

## Spec / documentation sync

N/A: no spec or user-facing doc describes this test; the only documentation touch is the in-source comment updated by E-04. No `.spec.md` is edited.

## Open questions

### OQ-01: Restore the `_PRECEDENCE` index assertion too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. It reads an internal constant (structure pin), prohibited by P16 and by the backlog item text "only behavioral outcomes may be restored, never a source-reading pin".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest tests/test_selector_precedence_outcomes.py -o addopts="" -v` showing the setid-collision test PASSED, plus the test source excerpt showing the colliding file is a `Set: other` plan whose filename contains `demo` and the assertions on `kind == selectors.MATCH_SETID` and exclusion of the colliding path.
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=3725032953
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/q9f0k7
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 3 items

tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_filename_substring_resolves_when_earlier_rules_do_not_match PASSED [ 33%]
tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_setid_outranks_filename_substring_on_collision PASSED [ 66%]
tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_status_outranks_filename_substring_on_collision PASSED [100%]

============================== 3 passed in 0.22s ===============================
```
Source excerpt from `tests/test_selector_precedence_outcomes.py`:
```python
        # Colliding plan declaring `- Set: other` whose FILENAME contains `demo`
        self.setid_collide_plan = (
            self.pend / "20260101-other-01-dd0001-demo-colliding-plan.ipd.md"
        )
        self.setid_collide_plan.write_text(
            "# Set Collision Plan\n\n- Id: dd0001\n- Status: draft\n- Set: other\n\n## Goal\nCollide setid\n",
            encoding="utf-8",
        )
...
    def test_setid_outranks_filename_substring_on_collision(self) -> None:
        """A token matching both Set ID and filename substring resolves as MATCH_SETID."""
        got = selectors.resolve(self.repo_root, "plans", "demo")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        resolved_paths = [p.resolve() for p in got.paths]
        for plan_path in self.demo_plans:
            self.assertIn(plan_path.resolve(), resolved_paths)
        self.assertNotIn(self.setid_collide_plan.resolve(), resolved_paths)
        self.assertEqual(len(resolved_paths), len(self.demo_plans))
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Same verbose pytest output showing the status-collision and substring fall-through tests PASSED, and pasted `rg -n "import inspect|from inspect|import ast|_PRECEDENCE|read_text\(.*selectors" tests/test_selector_precedence_outcomes.py` returning no matches.
  - Observed evidence:
```
Verbose test output from V-01 shows both tests passed:
tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_filename_substring_resolves_when_earlier_rules_do_not_match PASSED
tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_status_outranks_filename_substring_on_collision PASSED

Clean token check:
$ rg -n "import inspect|from inspect|import ast|_PRECEDENCE|read_text\(.*selectors" tests/test_selector_precedence_outcomes.py
(no matches, exit code 1)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output of the setid-collision test FAILING with `selectors._PRECEDENCE` monkeypatched to place `MATCH_SUBSTRING` before `MATCH_SETID` (produced by the E-03 in-process probe, with the exact command pasted), and pasted `git diff --stat agent_workflows/selectors.py` printing nothing before E-04.
  - Observed evidence:
```
Exact probe command and failing output:
$ python3 -c "import pytest; from agent_workflows import selectors as s; s._PRECEDENCE=(s.MATCH_PATH, s.MATCH_ID6, s.MATCH_SUBSTRING, s.MATCH_SETID, s.MATCH_STATUS, s.MATCH_STEM); raise SystemExit(pytest.main(['-o', 'addopts=', '-q', 'tests/test_selector_precedence_outcomes.py', '-k', 'test_setid_outranks_filename_substring_on_collision']))"
F                                                                        [100%]
=================================== FAILURES ===================================
_ SelectorPrecedenceOutcomesTests.test_setid_outranks_filename_substring_on_collision _

self = <tests.test_selector_precedence_outcomes.SelectorPrecedenceOutcomesTests testMethod=test_setid_outranks_filename_substring_on_collision>

    def test_setid_outranks_filename_substring_on_collision(self) -> None:
        """A token matching both Set ID and filename substring resolves as MATCH_SETID."""
        got = selectors.resolve(self.repo_root, "plans", "demo")
>       self.assertEqual(got.kind, selectors.MATCH_SETID)
E       AssertionError: 'substring' != 'setid'
E       - substring
E       + setid

tests/test_selector_precedence_outcomes.py:91: AssertionError
NOTE: 2 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
=========================== short test summary info ============================
FAILED tests/test_selector_precedence_outcomes.py::SelectorPrecedenceOutcomesTests::test_setid_outranks_filename_substring_on_collision
1 failed, 2 deselected in 0.15s

Pre-E-04 diff check:
$ git diff --stat agent_workflows/selectors.py
(no output, exit code 0)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git show --stat HEAD` naming `tests/test_selector_precedence_outcomes.py` and `agent_workflows/selectors.py` and no path outside Scope-Paths, pasted `git show HEAD -- agent_workflows/selectors.py` showing only comment lines changed, and the pasted summary line of a bare `python3 -m pytest` run showing all passed with zero failures.
  - Observed evidence:
```
$ git show --stat HEAD
commit 1057341350e9b24a6b80c68c4909f319efe94e47 (HEAD -> aw/lane/q9f0k7)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Fri Oct 16 03:43:13 2026 -0400

    work(q9f0k7): Restore behavioral coverage of selector setid precedence over filename substring

    AW-Run: run-20261016T041640Z-2100696
    AW-Item: q9f0k7
    AW-Runner: aw agy run

 agent_workflows/selectors.py               |   6 +-
 tests/test_selector_precedence_outcomes.py | 116 +++++++++++++++++++++++++++++
 2 files changed, 119 insertions(+), 3 deletions(-)

$ git show HEAD -- agent_workflows/selectors.py
commit 1057341350e9b24a6b80c68c4909f319efe94e47 (HEAD -> aw/lane/q9f0k7)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Fri Oct 16 03:43:13 2026 -0400

    work(q9f0k7): Restore behavioral coverage of selector setid precedence over filename substring

    AW-Run: run-20261016T041640Z-2100696
    AW-Item: q9f0k7
    AW-Runner: aw agy run

diff --git a/agent_workflows/selectors.py b/agent_workflows/selectors.py
index a7aef5f80..43e641334 100644
--- a/agent_workflows/selectors.py
+++ b/agent_workflows/selectors.py
@@ -114,9 +114,9 @@ _SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}
 # `_PRECEDENCE` IS FROZEN AS SEMANTICS, NOT AS INERTIA. A token can legitimately be BOTH a Set id
 # and a filename fragment, so the order decides which record WINS an existing query; reordering it
 # silently changes matching. Formerly pinned by
-# `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` (deleted in `19313eed`;
-# no live guard currently asserts this), which also proved the corollary that a stem or substring
-# query cannot be made read-free while the order stands.
+# `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` (deleted in `19313eed`);
+# guarded behaviorally by `tests/test_selector_precedence_outcomes.py`, which also preserves the
+# corollary that a stem or substring query cannot be made read-free while the order stands.
 #
 # THE PARSED FILENAME `id6` SLOT IS NOT A SAFE DISCRIMINATOR, a live trap independent of any
 # filter: `parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")` returns
```
Bare `python3 -m pytest` summary:
```
705 passed in 23.04s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved q9f0k7 --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin q9f0k7`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/selectors.py` that cannot be safely combined, or `selectors.resolve` no longer evaluating `setid` before `substring` (the premise of this plan).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The E-03 probe is in-process only and is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit q9f0k7 -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize q9f0k7` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
