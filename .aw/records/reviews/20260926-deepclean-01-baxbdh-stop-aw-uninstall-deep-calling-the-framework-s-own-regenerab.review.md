# Review findings: plan baxbdh

- Subject-Id: baxbdh
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b861bb05`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision, and `--phase review-finalize` conforms after. No pre-review
snapshot was needed: the tracked plan was committed and unmodified, and the lane-input copy is
byte-identical to it (both sha256 `d23f13c972ba9530c3d213404dfbbc7d4795b4c03d65a1de16434827ff88e7af`).

**THE DEFECT IS REAL AND THE FIX IS THE RIGHT SHAPE.** I reproduced every diagnostic claim on a real
install built with the test module's own helpers, committed with `git add -A`:

```text
AT_RISK: ['.aw/workflow-artifacts/README.md']
all_recoverable: False
README in files: True        README in other_files: True     README in records_files: False
counts[.aw/workflow-artifacts]: 1
check-ignore: 0 .aw/.gitignore:75:/workflow-artifacts/	.aw/workflow-artifacts/README.md
tpl exists: True   tpl identical to README: True   tpl tracked: True
```

The regenerability premise holds on both halves: the target carries a TRACKED template byte-identical
to the written README, and `_ARTIFACTS_README_FALLBACK` covers a template that cannot be read. The
plan's structural reading of `plan_deep_cleanup` is accurate, and its choice to put the exemption in
the CALLER rather than soften `_git_file_state` is right, since that function's docstring commits to
being loud ("anything uncertain is \"at_risk\"") and three other roots depend on it.

**THE AUTHORED FIX SILENCES A WARNING THAT IS CORRECT, AND THE STATE IT SILENCES IS ONE THE CODEBASE
ITSELF SAYS PERSISTS FOREVER.** This is the finding worth the most. The plan's test was
`rel not in _DEEP_CLEANUP_REGENERABLE and _git_file_state(...) == "at_risk"`, exempting by PATH. But
`ensure_workflow_artifacts_readme`'s own comment records why a tracked copy exists in the wild: "git's
ignore rules do NOT untrack an already-tracked path: a repo that installed before Order 02's ignore
rule landed would keep the file tracked forever." In that repo the README is tracked, so a user's
uncommitted edits to it are content git cannot restore, and a path-only exemption tells them deletion
is safe. Driven on a real install with the README `git add -f`'d, committed, then edited:

```text
3 tracked+dirty: today    ['.aw/workflow-artifacts/README.md']
3 tracked+dirty: blanket  [] <- SILENCED
3 tracked+dirty: narrowed ['.aw/workflow-artifacts/README.md'] <- PRESERVED
```

I verified the narrowed rule (exempt only while UNTRACKED) on all four states plus the existing
passing test's scenario, so it fixes the defect without weakening anything:

```text
1 committed:       today ['.aw/workflow-artifacts/README.md'] | narrowed []
2 records scratch: narrowed ['.aw/records/research/scratch.md']
4 tracked+clean:   today [] | narrowed []
+ user note:       narrowed ['.aw/workflow-artifacts/my-notes.md']
```

**THE PLAN NAMED THE WRONG SURFACE, AND THE ONE IT NAMED IS THE ONLY ONE THAT PRINTS NOTHING.** The
title and `- Concern:` said `aw uninstall --deep` warns. Driving the real CLI on a committed install:

```text
--dry-run          ! 1 of these are NOT recoverable from git (untracked/uncommitted)
--dry-run --deep   ! 1 of these are NOT recoverable from git (untracked/uncommitted)
--yes --deep       lines mentioning recoverable/permanent: (NONE)   README removed: True
interactive offer  WARNING: 1 of these are NOT recoverable from git (untracked, uncommitted, or
                   ignored). Deleting them is permanent:
                     ! .aw/workflow-artifacts/README.md
```

`--yes --deep` performs the cleanup without the prompt, so it emits no recoverability line at all. The
user-visible defect lives in `--dry-run` (the preview a careful user runs first) and in the
interactive offer. The fix is unaffected; the plan's own description of what a human is approving was
wrong, and a human reading only the title would have tested the one invocation that shows nothing.

**EVERY TEST WAS SLOW-MARKED, WHICH HIDES THIS FIX FROM THE RUN THIS REPO JUDGES CHANGES BY.** E-04
marked the new file `pytest.mark.slow` "like `tests/test_installer.py`". That reasoning copies a cost:
backlog `4vfkl1` and `xuc9v0` exist precisely because the slow subset accumulates regressions
invisibly, and approved plan `4petcj` is fixing that. The classification rule needs no install, which I
verified by reproducing all four states on a hand-built 5-file fixture:

```text
fixture (5 scenarios):  0.24s
one real install:       1.83s / 2.01s / 3.38s  (three runs)
```

I also verified the mechanism the split needs, since a per-class mark on a `unittest.TestCase` is the
kind of thing that silently marks nothing:

```text
(default)      2 passed
-m 'not slow'  1 passed, 1 deselected
-m slow        1 passed, 1 deselected
```

**WHAT I CONFIRMED RATHER THAN CHANGED.** `cli.py` genuinely needs no edit: all three surfaces read
`plan.at_risk` (`_uninstall_dry_run_report`, and `_offer_deep_cleanup`'s two
`[f for f in plan.at_risk if f in ...]` filters), so they become correct automatically. The
spec-sync claim is accurate: grepping `.aw/records/specs/` for `plan_deep_cleanup`, `at_risk`, and
`uninstall --deep` finds nothing, and the physical-layout spec's Section 5 only names the tree as
per-machine control state covered by `.aw/.gitignore`. `README.md` and `docs/` describe no at-risk
count. OQ-02's reading of `4vfkl1` is correct against that item's body. The `57dwkc` deferral is right
and carries a real carrier. `run_deep_cleanup` does remove the README (verified), so keeping it in
`plan.files` is load-bearing and the plan is right to insist on it. Right-sizing: now 7 E-items over
four small surfaces, well under threshold, dependency graph honest.

ONE SMALL STALENESS: HEAD `61ef21d8` was two commits behind (`b861bb05`), and the `2 failed in 8.79s`
evidence came from a two-node selection rather than the module. Re-measured over the whole file:
`2 failed, 93 passed in 220.87s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness (a fix that suppresses a true warning about unrecoverable content) | driven on a real install with the README `git add -f`'d, committed, then edited: `engine._git_file_state` -> `at_risk`; the plan's path-only test -> `[]`; a tracked-aware test -> `['.aw/workflow-artifacts/README.md']`. The state is documented as permanent by `ensure_workflow_artifacts_readme`'s own comment, "a repo that installed before Order 02's ignore rule landed would keep the file tracked forever" | **EXEMPTING BY PATH ALONE SILENCES THE ONE CASE WHERE THE WARNING IS CORRECT.** A README that is git-TRACKED (the pre-ignore-rule install shape) and holds uncommitted edits is content git cannot restore, yet `rel not in _DEEP_CLEANUP_REGENERABLE` drops it from `at_risk`, so `aw uninstall` would tell that user deletion is recoverable. The plan's own OQ-01 considered "user edited the README" but resolved it without distinguishing the tracked case. | C:Low; U:Low; S:Low; F:High; Overall:Low (the fix is one added `git_is_tracked` conjunct, verified correct on all four states) | FIXED | E-03 now exempts only when the path is NOT tracked, states the four-state truth table as its required property, and forbids the path-only spelling with the measurement. E-02's comment must carry the tracked caveat and its reason. V-03 demands a four-row pasted table and says a missing tracked-and-dirty row does not satisfy it. E-04 case (3) pins it as a negative control; the gate's stop condition forbids deleting that case. OQ-01 rewritten with the split answer. F-6 added. |
| PR-002 | MEDIUM | IN-SCOPE | E/D. testing visibility (a new test hidden from the run the contract judges by) | measured: a hand-built 5-file fixture reproduces all four classification states in 0.24s; one real install costs 1.83s to 3.38s over three runs. Per-class `pytestmark` verified: default `2 passed`, `-m 'not slow'` `1 passed, 1 deselected`, `-m slow` `1 passed, 1 deselected`. Backlog `4vfkl1` and `xuc9v0`, and approved plan `4petcj`, all exist because the slow subset hides regressions | **MARKING THE WHOLE NEW TEST FILE SLOW MAKES THIS FIX INVISIBLE TO THE BARE SUITE.** E-04 copied `tests/test_installer.py`'s module-level mark, so the only proof of the change would sit in the deselected subset that this repository has twice filed bugs about, and a later regression in the classifier would go unseen. The classification rule needs no install to test. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 is now DEFAULT-VISIBLE, builds a minimal fixture by hand, and holds the four classification cases; a new E-05 keeps the real-install integration case in a SEPARATE class with a class-scoped slow mark (the mechanism verified above). V-04 requires a BARE run showing the cases selected; V-05 requires the `-o addopts=""` run plus a bare run whose `deselected` count proves the install class was skipped. F-8 added; the Deferred section records what this plan does and does not owe `4vfkl1`. |
| PR-003 | MEDIUM | IN-SCOPE | G. plan executability (the named user-visible surface is the one that does not warn) | the real CLI driven on a committed install: `--dry-run` and `--dry-run --deep` print `! 1 of these are NOT recoverable from git (untracked/uncommitted)`; `--yes --deep` prints no such line and removes the README; the interactive `_offer_deep_cleanup` prints `WARNING: ... Deleting them is permanent:` then `! .aw/workflow-artifacts/README.md` | **THE PLAN'S TITLE AND CONCERN BLAME `aw uninstall --deep`, WHICH EMITS NO RECOVERABILITY LINE AT ALL.** Under `--deep` the cleanup runs without the prompt. The warning a user actually sees comes from `--dry-run` (the preview) and from the interactive offer. A human approving on the title, or an executor spot-checking the fix, would exercise the one invocation that shows nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Title, `- Concern:`, `## Goal`, and the approval paragraph now say `aw uninstall` and enumerate all three invocations with their measured output, explicitly noting that `--yes --deep` prints nothing. F-7 added. |
| PR-004 | MEDIUM | UNDER-SCOPE | G/F. user-visible change with no user-facing record | `CHANGELOG.md` `## 2.0.0 (pending)` carries 11 `Fixed:` entries and 7 of 47 pending plans declare `CHANGELOG.md` in `- Scope-Paths:`; `CONTRIBUTING.md` Authoring conventions names `CHANGELOG` as user-facing prose governed by the no-dash rule | **A WARNING A USER READS CHANGES, AND NOTHING RECORDS IT.** The plan's spec-sync section correctly finds no spec or doc to amend and then concludes nothing user-facing is owed, but the text a user sees during `aw uninstall` is exactly what this plan alters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 adds one `- Fixed:` line under `## 2.0.0 (pending)`, worded for a user and stating the three preserved behaviors; V-07 requires the diff plus a dash grep printing nothing. `CHANGELOG.md` added to `- Scope-Paths:`; the spec-sync section now states what it does and does not owe. |
| PR-005 | LOW | UNDER-SCOPE | D. anti-regression (a test that passes while its prose says it fails) | the docstring of `tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed`: "PRE-EXISTING FAILURE ... Either the product should exclude its own gitignored run-scratch README from the at-risk set, or this expectation should change; that is a maintainer call about `agent_workflows/`" | **THE NOW-PASSING TEST WOULD KEEP DECLARING ITSELF A KNOWN FAILURE AND ASKING FOR THE DECISION THIS PLAN MAKES.** A later reader would treat a green test as red, and the open product question as still open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 replaces that paragraph with one sentence citing the resolution (`_DEEP_CLEANUP_REGENERABLE`, plan `baxbdh`, backlog `3ypquf`), touching NO assertion; `tests/test_installer.py` added to `- Scope-Paths:` for a docstring-only edit; V-06 requires the full diff and forbids a changed assertion line; the gate's stop condition forbids changing any assertion there. F-9 added. |
| PR-006 | LOW | IN-SCOPE | correctness of stated evidence | `git rev-parse --short HEAD` -> `b861bb05`; `61ef21d8` is two commits back; `python3 -m pytest -o addopts="" -q tests/test_installer.py` -> `2 failed, 93 passed in 220.87s` | **THE DECLARED HEAD IS STALE AND THE FAILING-TEST EVIDENCE CAME FROM A TWO-NODE SELECTION.** Nothing turns on it, but the plan presents `2 failed in 8.79s` as the module's state when it was the result of naming two nodes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | HEAD corrected to `b861bb05` throughout; F-3's evidence replaced with the whole-module run and its real duration; the Findings preamble now distinguishes authoring-time from review-time measurement. |
| PR-007 | LOW | IN-SCOPE | E. testing (validation that could be satisfied by weakening a test) | the gate carried one stop condition (E-01 finding `at_risk` empty) and no protection for the negative controls; E-04's controls are the only thing standing between this fix and PR-001's regression | **NOTHING FORBADE PASSING VALIDATION BY DELETING THE CONTROL THAT PROVES THE FIX IS NARROW.** An executor hitting a red tracked-and-dirty case could satisfy every V-item by removing it or by relaxing the installer test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now carries a second GENUINE STOP CONDITION forbidding deletion or relaxation of E-04 case (3) and any assertion change in `tests/test_installer.py`, naming the consequence (the plan would pass while re-introducing the defect). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan exempts the README by PATH. Accept that, gate on content equality with the shipped template, or gate on git state? | GATE ON GIT STATE: exempt only while the path is UNTRACKED. | (a) Path only, as authored: rejected, measured to silence a true warning for a tracked-and-dirty README, which is the one state where git holds nothing recoverable. (b) Content equality against `templates/workflow-artifacts-README.md`: rejected on two counts, it is still WRONG in the tracked case (a tracked file edited away from the template is at risk, and one edited back to it is not, so content is the wrong question), and it adds a template read plus a byte comparison to a pure classifier, where the fallback path means the template may not even be readable. (c) Ask the maintainer: rejected, the repository answers it, since `ensure_workflow_artifacts_readme`'s own comment states that the tracked shape persists forever and `_git_file_state` already returns the correct verdict for it. | Driven on real installs: path-only -> `[]` for tracked+dirty; tracked-aware -> flags it; both agree on untracked, tracked+clean, and a sibling user file. `ensure_workflow_artifacts_readme` comment: "a repo that installed before Order 02's ignore rule landed would keep the file tracked forever". | yes |
| D-2 | E-04 marks the new file slow "like `tests/test_installer.py`". Keep that, or split the file? | SPLIT: default-visible classification cases on a hand-built fixture, plus one slow-marked class for the real install. | (a) Keep everything slow: rejected, it hides the fix from the bare run this repo's contract judges changes by and adds to the very problem `4vfkl1`/`xuc9v0`/`4petcj` are about. (b) Make everything default-visible including the install: rejected, an install costs 1.8s to 3.4s and the file-copy integration genuinely needs it; the existing module is slow-marked for that reason. (c) Rewrite `tests/test_installer.py` to be fast: rejected as far out of scope, and its `DeepCleanupTests` docstring records a deliberate reason for its shape. | Measured: fixture 0.24s for 5 scenarios versus 1.83/2.01/3.38s per install. Per-class `pytestmark` verified to deselect one class while siblings stay visible. | yes |
| D-3 | The plan blames `aw uninstall --deep`. Correct the wording, or leave it as shorthand? | CORRECT IT, and enumerate all three invocations with measured output. | (a) Leave it: rejected, `--yes --deep` is the single invocation that prints NO recoverability line, so the shorthand points a human and an executor at the wrong place. (b) Correct the title only: rejected, the `- Concern:` and the approval paragraph carried the same claim and are what a human actually reads before approving. | The three invocations driven against the real CLI; `--yes --deep` produced no matching line while `--dry-run` and the interactive offer each did. | yes |
| D-4 | A user-visible warning changes and the plan declares no user-facing artifact. Add a CHANGELOG line, or accept the spec-sync N/A? | ADD ONE `Fixed:` LINE. | (a) Accept N/A: rejected, the spec/doc analysis is correct but the CHANGELOG is the repository's standing home for a user-visible behavior change, and 7 of 47 pending plans declare it for exactly this reason. (b) Also write a doc section: rejected, no doc describes the at-risk count today, so a new section would be inventing a surface to maintain. | `CHANGELOG.md` `## 2.0.0 (pending)` with 11 existing `Fixed:` entries; `CONTRIBUTING.md` Authoring conventions naming CHANGELOG as user-facing prose. | yes |
| D-5 | The now-passing installer test carries a docstring declaring itself a known failure. Edit it here, or leave it to a follow-up? | EDIT THE DOCSTRING HERE, assertions untouched, and declare the path. | (a) Leave it: rejected, it would leave a green test asserting it is red and an answered product question recorded as open, in the very file this plan's own validation quotes. (b) Edit assertions too: rejected and explicitly forbidden, the plan's whole claim is that the test passes AS WRITTEN. (c) File a follow-up item: rejected, a one-paragraph prose correction in a file the plan already runs is smaller than the item that would track it. | The docstring text itself; the execution contract's rule that a plan may not leave documentation contradicting behavior it changed. | yes |

### Deferred and open

- (none). All seven findings were FIXED in place, four of them by changing what the plan will DO (a
  git-state-conditioned exemption, a split test file with one default-visible surface, a docstring
  correction with an assertion fence, and a CHANGELOG line) rather than by rewording. No question
  required the human: OQ-02 was already correctly resolved, OQ-01 was superseded from measurement, and
  every decision above rests on a driven measurement or an existing repository rule.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECT and the
proposed RULE by driving `plan_deep_cleanup` and a local reimplementation of the narrowed predicate on
real installs; I did NOT edit `engine.py`, so that the shipped change composes with the module exactly
as I modelled it remains E-03's work and V-03's evidence. My four-state table used a README force-added
with `git add -f` to simulate a pre-ignore-rule install; I did not reconstruct such a repo from an
actual older framework version, so that shape is inferred from `ensure_workflow_artifacts_readme`'s own
comment rather than observed in the wild. I ran the full `tests/test_installer.py` once
(`2 failed, 93 passed in 220.87s`), so a flaky failure would look identical to a deterministic one
here, though the two failures matched the two the backlog already owns. I did not run the repository's
bare suite in this lane, so the plan's before/after failing-node-set comparison is still owed by V-07.
The per-class slow-mark mechanism was verified on a scratch fixture with its own `pytest.ini`, not
inside this repository's `conftest.py` with xdist and random ordering active, so E-05 must confirm the
deselection in the real invocation.
