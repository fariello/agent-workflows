# Review: Make finalize rollback restore the recorded index entry instead of unstaging to HEAD

- Subject-Id: zbh2yt
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `513c7d12`. The target plan was committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and again at
`--phase review-finalize` after the revisions.

THIS IS A WELL-MADE PLAN AND I REPRODUCED ALL FOUR OF ITS PROBE FINDINGS EXACTLY, in a scratch git
repo rather than by reading. F-1: both arms of `if p in prior_index:` in `_rollback_precommit` step 3
are byte-identical `_git(repo_root, ["restore", "--staged", "--", p])`, so `prior_index` decides
nothing. F-2, the one that makes this a bug and not dead code: with a staged plan edit recorded as
`100644 01392d80...`, `_rollback_precommit` returned ok and the entry came back
`100644 74993650...` (HEAD's blob), with `git status` flipping from `M ` to ` M`. So a rollback whose
docstring promises to restore "the exact prior Git-index entries" silently discards a peer's staged
edit. F-3: `restore --staged` on the never-indexed destination exits 1 with
`error: pathspec '...' did not match any file(s) known to git`, ignored. F-4:
`git update-index --index-info` fed the recorded line restored the entry byte-for-byte and returned
status to `M `. The plan's reading (2) of backlog `67k1ol` is correct, and its choice of remedy is
the right one.

E-03's caller claim also checks out, which matters because the plan asserts no caller change is
needed. Both sites do exactly what it says: the resume branch sets `existing["phase"] =
PHASE_UNKNOWN_OUTCOME` plus `existing["rollback_error"] = msg` and returns `EXIT_CANNOT_RUN`, and
`_rollback_and_return` does the same on `cur`. So a new `(False, ...)` arm routes correctly with no
caller edit.

THEN I DROVE THE PROPOSED NEW RULE, AND ITS `--force-remove` ARM IS DANGEROUS IN A WAY THE PLAN
UNDERSTATES. OQ-01 raises the right question but reaches the wrong conclusion about the tests, and
the measurement inverts its reasoning. Running `git update-index --force-remove` on a path that IS in
the index staged a DELETION: status went from clean to `D  <path>` with the file still on disk. That
is a destructive index write performed on the strength of an ABSENT journal key, and it is the
opposite of the peer-safety discipline steps 1 and 2 establish (both refuse rather than overwrite
content the transaction did not write). The plan's own conventions section notes that discipline and
then proposes an arm that violates it.

F-6 IS RIGHT THAT THE FIXTURES ARE AT RISK BUT WRONG ABOUT WHY, and the difference decides the fix.
The plan says "the pending path is tracked at HEAD, so `--force-remove` would unstage-delete it". I
drove the actual fixture: `_init_git_repo` runs `git init` and NEVER COMMITS, so
`git rev-parse HEAD` fails and nothing is tracked at HEAD at all. But `make_set` STAGES the plan, so
the path IS in the index with no HEAD commit behind it. I confirmed `_git_index_entries` returns a
real entry for `.aw/records/plans/pending/20260906-rbhalf-00-orc000-synthetic.ipd.md` while the
fixture journal hard-codes `"git_index_entries": {}`, and that force-removing it produces
`D  <path>` plus `?? <path>`. So the hazard is real, it reaches cases 2 and 3 of
`test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent` (case 1 and the second
`{}` site both return at step 1 on `unknown-outcome` and never reach step 3), and the mechanism is a
journal that misdescribes the index rather than a tracked-at-HEAD path. That matters because the
correct guard follows from the mechanism: an absent or empty recording is EVIDENCE ABSENCE, not
evidence of absence, so the safe action is to write nothing.

SO I RESOLVED OQ-01 AGAINST THE FORCE-REMOVE ARM ENTIRELY, not merely behind an empty-dict guard.
OQ-01's default ("treat an EMPTY `git_index_entries` as not recorded and skip step 3 for every path")
is correct as far as it goes but is keyed on the wrong condition: a journal carrying entries for SOME
owned paths and not others is not empty, so the guard would not fire, and the missing path would
still be force-removed on absent evidence. The general rule is per-path: restore when an entry was
recorded, and do NOTHING when none was. I verified this costs no coverage, which is what makes the
decision safe rather than merely cautious. For every destination case I could construct, the old
unconditional `restore --staged` and a do-nothing arm reach the SAME end state, because step 1
already unlinked the destination and `git restore --staged` on a staged-then-deleted new path exits 0
and clears the entry, while `--force-remove` clears it too: measured, all three routes end with no
index entry and a clean or `?? `-only status. The only case where the arms differ at all is the plan
file, which is exactly the recorded-entry case the fix is about.

ON THE `subprocess.run` DETAIL, the plan is right that `_git` cannot pass stdin (it delegates to
`git_commit_helper._git`, which takes only args) and right to prefer a local call over changing that
shared signature. I strengthened it to say the local call must still be `cwd=repo_root` and must
capture stderr, because E-03's failure string needs the stderr text and a bare `subprocess.run`
without `capture_output` would give it nothing to report.

ON RIGHT-SIZING: four items was slightly too coarse in one place. E-02 carried the three-case
rewrite, the branch deletion, the comment rewrite AND the stdin mechanism; after the OQ-01 resolution
it also owes the per-path guard. I split the guard out as its own item, because it has a different
failure mode (a destructive write on absent evidence) and its own test surface (the two existing
`{}`-journal fixtures), and because it is the one part where being wrong loses a peer's staged work
rather than merely failing to restore it.

Two things I checked and found correct, recorded so a later reader does not re-derive them. F-5's
coordinator-worktree claim holds and is the reason the no-op case is the common one:
`_finalize_transaction` performs the mutations in a coordinator worktree, so the shared index is
normally untouched and step 3 should usually write nothing. And `RollbackFailureSemanticsTests` is
the right home for E-01: unlike the orchestrator-retirement fixture it calls `_commit_all(self.root,
"init")` in `setUp`, so its plan file is genuinely tracked at HEAD and a staged-edit-versus-HEAD
assertion is meaningful there. Backlog `67k1ol` is `Work-Kind: bug` carrying `- Blocks-Release: next`,
which this plan correctly inherits.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | A. Correctness / B. Peer-safety boundary | Driven at review: `git update-index --force-remove` on a path present in the index took `git status` from clean to `D  <path>` with the file still on disk. Steps 1 and 2 of `_rollback_precommit` both REFUSE rather than overwrite content the transaction did not write (`"refusing a destructive restore"` in each) | THE PROPOSED `--force-remove` ARM PERFORMS A DESTRUCTIVE INDEX WRITE ON THE STRENGTH OF AN ABSENT JOURNAL KEY, which inverts the peer-safety discipline the plan's own conventions section cites. An absent recording is EVIDENCE ABSENCE (`_git_index_entries` also returns `{}` on any `ls-files` failure, as the plan notes), not proof the path had no entry, so treating it as an instruction to stage a deletion can destroy a peer's staged work in precisely the scenario this rollback exists to protect. OQ-01's empty-dict guard is keyed on the wrong condition: a journal with entries for SOME owned paths is not empty, so the guard would not fire and the unrecorded path would still be force-removed. | C:Low; U:Low; S:Medium (a peer's staged work); F:Medium; Overall:Low (the fix REMOVES an arm, and review measured that doing so costs no coverage) | FIXED | The `--force-remove` arm is REMOVED. E-02 is now a TWO-case rule: restore when an entry was recorded, do NOTHING when none was, per path. New E-03 owns that guard with its reason. OQ-01 re-resolved from "guard the empty dict" to "never write on absent evidence, per path", with the measurement showing the removal is free: for every destination case constructed, the old `restore --staged`, `--force-remove`, and do-nothing all end with no index entry (step 1 has already unlinked the destination, and `restore --staged` on a staged-then-deleted new path exits 0 and clears the entry). Added F-7 and F-8. |
| PR-802 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest documentation | Driven at review on the real fixture: `_init_git_repo` runs `git init` with NO commit, so `git rev-parse HEAD` fails; `make_set` stages the plan, so `_git_index_entries` returns `{'...20260906-rbhalf-00-orc000-synthetic.ipd.md': '100644 30a4e612... 0\t...'}` while the fixture journal hard-codes `"git_index_entries": {}`; force-removing it yields `D  <path>` plus `?? <path>` | F-6 IDENTIFIES THE RIGHT TESTS FOR THE WRONG REASON, AND THE REASON DECIDES THE GUARD. It says "the pending path is tracked at HEAD, so `--force-remove` would unstage-delete it"; nothing is tracked at HEAD in that fixture, because it never commits. The path is in the INDEX with no HEAD behind it, and the journal misdescribes the index. Believing the tracked-at-HEAD story would suggest the fix is about HEAD state; the real mechanism (a journal whose recording disagrees with the index) is what implies the per-path do-nothing rule of PR-801. I also established WHICH cases are exposed: cases 2 and 3 of `test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent` reach step 3, while case 1 and the second `{}` journal site both return at step 1 on `unknown-outcome` and never get there. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-6 rewritten with the measured mechanism, the `git rev-parse HEAD` failure, the real recorded entry, and the precise list of which fixture cases reach step 3 and which return early. E-03 cites it as the reason the guard is per-path rather than empty-dict-keyed, and V-03 requires the two existing fixtures shown passing with the guard in place. |
| PR-803 | MEDIUM | UNDER-SCOPE | G. Plan executability (right-sizing) | Original E-02 carried: the three-case rewrite, the identical-arm deletion, the step-3 comment rewrite, and the `subprocess.run` stdin mechanism; after PR-801 it also owed the per-path evidence guard. `aw ipd lint` passed on count (4 items, 3 groups) | ONE E-ITEM CARRIED FOUR DELIVERABLES AND THE ONE PART WHERE BEING WRONG LOSES DATA. The right-sizing diagnostics answer yes on multiple axes: distinct deliverables, and independent test surfaces (the recorded-entry restore is proven by E-01's new test, while the absent-evidence guard is proven by two PRE-EXISTING fixtures with hand-built journals, which is a different kind of evidence). Bundling them means an executor who gets the restore right and the guard wrong produces a passing E-01 and a destructive regression. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Five items with a 5:5 E/V bijection: E-01 the failing regression test, E-02 the recorded-entry restore, E-03 the absent-evidence guard, E-04 the surfaced failure, E-05 the bare suite. `- Highest E allocated:` raised to 05. Cohesion rationale states it is one concern and why E-02 and E-03 are separate. |
| PR-804 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: one sentence covering approval, commit path and transition; compare pending plan `t0jyb2`'s gate | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS: no statement of what a human is approving (and what they are approving is a change to the code path that runs when a finalize has ALREADY failed, i.e. the last thing standing between a failure and a peer's staged work), no scope fence inside the two declared paths, no stop conditions, and a transition instruction with no runner/executor ownership split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming the failure-path blast radius and the removed `--force-remove` arm; a per-path scope fence stated as a DECLARATION with an explicit not-in-scope list mirroring the plan's own OUT clause; the hard-MUST honesty rule naming V-01 and V-03 as the items most exposed to faking and why; three genuine stop conditions; and the transition with conditional runner/executor ownership and no hand-rolled `git mv`. |
| PR-805 | LOW | IN-SCOPE | A. Correctness / E. Testing | `git_commit_helper._git(repo_root, args)` takes no stdin parameter; E-03's failure string requires stderr text | THE LOCAL `subprocess.run` PRESCRIPTION OMITS TWO NECESSARY ARGUMENTS FOR THE FAILURE PATH TO WORK. The plan gives `cwd=repo_root, input=..., text=True, capture_output=True` in one sketch, which is right, but E-03's requirement to report `<stderr>` depends on `capture_output=True` specifically, and a reader trimming the call (a common simplification, since the return value is only checked for nonzero) would leave the failure message with an empty stderr and no diagnostic. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states `cwd=repo_root` and `capture_output=True` as REQUIRED with the reason each is needed (the first so the call is not run against the reviewer's own checkout, the second so E-04's message has stderr to quote), and notes that `git_commit_helper._git`'s signature must stay untouched. |
| PR-806 | LOW | IN-SCOPE | E. Testing | Original E-01 asserts `(b) _git_index_entries after equals the recorded dict` and `(c) the destination path has no index entry`; measured, the failure signature is the blob id changing from the staged blob to HEAD's | E-01's ASSERTION SET IS RIGHT BUT ITS FAILURE EVIDENCE IS UNDER-SPECIFIED. V-01 asks for "the assertion diff naming the HEAD blob vs the recorded blob", which a dict-equality assertion on a two-key dict may render unhelpfully. Since this test is the sole proof the bug exists, its failure output should be unambiguous about WHICH blob replaced which. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the test to assert the plan path's entry explicitly (not only via whole-dict equality) so the failure names both blob ids, and to record `git status --porcelain` before and after, since the `M ` to ` M` flip is the operator-visible symptom. V-01 requires both in the pasted failing output. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 asks what to do when `git_index_entries` has no entry for an owned path. Guard only the empty dict (the plan's default), force-remove, or never write on absent evidence? | Never write on absent evidence, PER PATH. Remove the `--force-remove` arm entirely. | (a) Force-remove as originally written - rejected on measurement: it stages a deletion (`D  <path>`) on the strength of a missing journal key, inverting the refuse-rather-than-overwrite discipline steps 1 and 2 establish. (b) The plan's empty-dict guard - rejected as keyed on the wrong condition: a journal with entries for SOME owned paths is not empty, so a partially-recorded journal would still force-remove the unrecorded path. (c) Ask the maintainer - rejected: the repository states the discipline in the two adjacent steps' own refusal messages, and review could measure that removing the arm costs no coverage. | Driven: `--force-remove` on an indexed path yields `D  <path>`; steps 1 and 2 each carry `"refusing a destructive restore"`; and for every destination case constructed, `restore --staged`, `--force-remove` and do-nothing all end with no index entry, because step 1 already unlinked the destination | yes |
| D-2 | Does removing the `--force-remove` arm lose the old unconditional call's coverage for the destination path? | No, and it is measured rather than assumed. | (a) Keep an unconditional `restore --staged` for unrecorded paths to be safe - rejected: that is the current bug's mechanism applied to a second path, and it is what emits F-3's spurious pathspec error; it also writes when nothing needs writing, against F-5's no-op-is-normal observation. | Measured three routes on a staged-then-unlinked destination: `restore --staged` rc 0 clearing the entry, `--force-remove` rc 0 clearing the entry, and do-nothing after step 1's unlink; all three end with no index entry and a clean or `?? `-only status | yes |
| D-3 | F-6 claims the fixture's pending path is "tracked at HEAD". Is it? | No. It is in the INDEX with no HEAD commit at all; correct the finding rather than keep a claim that happens to point at the right tests. | (a) Leave F-6 as written since it identifies the right tests - rejected: the stated mechanism is false and would mislead the guard's design toward a HEAD-state question, when the real issue is a journal recording that disagrees with the index. (b) Drop F-6 - rejected: the two fixtures genuinely are the regression surface for E-03 and V-03. | Driven on the real fixture: `git rev-parse HEAD` fails after `_init_git_repo`; `make_set` stages the plan; `_git_index_entries` returns a real entry while the journal hard-codes `{}`; force-removing yields `D  <path>` + `?? <path>` | yes |
| D-4 | Which existing fixture cases actually reach step 3, and must the plan say? | Cases 2 and 3 of `test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent`; yes, the plan must name them. | (a) Say "the rollback tests" generally - rejected: two of the four `{}`-journal call sites return at step 1 on `unknown-outcome` and never reach step 3, so an executor verifying "the rollback tests pass" could satisfy V-03 without ever exercising the guard. | Read of the two `"git_index_entries": {}` sites: the first case and the second site both assert `assertFalse(ok)` with `unknown-outcome`, which returns in step 1; cases 2 and 3 assert `assertTrue(ok)` and run to completion | yes |
