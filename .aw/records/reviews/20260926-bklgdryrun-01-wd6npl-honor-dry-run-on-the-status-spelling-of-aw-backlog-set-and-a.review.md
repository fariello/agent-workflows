# Review findings: plan wd6npl

- Subject-Id: wd6npl
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1aae8813`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision. No pre-review snapshot was needed: the plan was committed and
unmodified, and the lane-input copy is byte-identical to the tracked file.

EVERY AUTHORED FINDING REPRODUCED, AND THE TWO THAT MATTER MOST I DROVE LIVE. F-1: both parsers give
`dry_run=True` and NO `apply` attribute, so `getattr(args, "apply", True)` is unconditionally True.
F-2: zero `dry_run` occurrences in either module. F-3, on a scratch repo:

```text
=== aw backlog set <path> --status open --dry-run ===
aw backlog set: 20260921-abc123-01-abc123-demo.backlog.md -> open
rc=0
sha256 before b9d360c0... after ab85c620...      <- the file was REWRITTEN
Custom-Field still present? 0                    <- an unrecognized field was DELETED
history.jsonl: -rw-r--r-- ... 139 bytes           <- the sidecar was CREATED
```

And the specs half, which is the worse of the two because it relocates a tracked record:

```text
=== aw specs set <path> --status to-review --dry-run ===
rc=0
BEFORE: .aw/records/specs/draft/20260901-sp0001-01-sp0001-demo.spec.md
AFTER:  .aw/records/specs/to-review/20260901-sp0001-01-sp0001-demo.spec.md
git status:  D .aw/records/specs/draft/...   ?? .aw/records/specs/to-review/
```

F-4 and F-5 both hold: a `--status done` refused by the release gate still created the sidecar, and a
`--graduated-to 'BAD SET'` refusal (a true `rc=2`, which I confirmed separately after a shell pipeline
initially masked it) also created it. So the plan's decision to widen from "gate before write" to "no
sidecar on any refusal" is the same defect class rather than scope creep, and the Over-scope note
saying so is correct. E-01 through E-04's insertion points are all precisely located against the real
code, which is better than most plans manage on a two-module edit.

**F-7 IS WORSE THAN THE PLAN STATES, AND THE ESCALATION IS THE MOST VALUABLE THING THIS REVIEW FOUND.**
The plan records that the positional spelling skips `check_engine.evaluate_blocking_close`. I drove both
spellings against ONE fixture item carrying `- Blocks-Release: rel001` with no handoff and no evidence.
The `--status` form refused correctly with the three legitimate fixes (exit 1). The positional form:

```text
=== aw backlog set done abc123 --yes ===
- >  backlog  20260921-abc123-01-abc123  [high]  [blocking]  open -> done
Committed 2 path(s): 8334d0487dacb4bb7015d3a52226ce314cf073b7
rc=0
```

It SELF-COMMITS. That is the part the plan does not say, and it is what removes the safety net, because
the documented backstop is staged-scoped by design: `check_engine.check_release_gate_consistency`
iterates `_staged_backlog_done_items(repo_root)` and its own comment states that "only a backlog item
whose close-to-`done` is STAGED in THIS commit is examined, so historical `done/` items closed before
this guard existed are grandfathered". A path that commits its own move leaves nothing staged, so I
measured `aw check release-gates` on the post-bypass repo reporting `CONFORMS, errors 0`. For that
spelling the gate is unenforced AND the backstop is unreachable. The grandfathering is a deliberate,
well-reasoned choice and I am not calling it wrong; the defect is that one setter never reaches the
predicate at all. This is correctly OUT of this plan's scope, and it is ALREADY FILED as backlog
`mawwlc` (`bug`/`high`/`Blocks-Release: next`), whose text credits this plan's author and already
prescribes the fix. So the plan's deferral was stale in a way worth fixing: it promised a verbal
hand-off "because the authoring brief forbids filing backlog items", when the item exists.

**THE PLAN'S OWN GATE NAMES A BACKLOG ID AS A PLAN ID.** The stop condition warns about "plan `rendrop`
/ f2kqas". `f2kqas` is the backlog item; the plan is `2yqt0a`, which declares
`agent_workflows/backlog.py` plus `tests/test_backlog.py` and carries `- Item-Dependencies:
executed:wd6npl`. An executor checking for a concurrent editor would search for a plan that does not
exist. Corrected, and I added the reassurance the plan should have carried: because `2yqt0a` depends on
this plan, the runner orders it AFTER and isolates it, so file overlap is not a live hazard.

**TWO TEST ITEMS WOULD HAVE FAILED FOR REASONS UNRELATED TO THE FIX.** E-06(a) asserts
`git status --porcelain` is empty, but `SpecStatusDirectoriesTests.setUp` git-inits and mkdirs WITHOUT
committing, so a spec written in the test body is untracked and the status is non-empty before the
command runs; the two existing relocation tests in that file do `git add -A` + `git commit` themselves,
and the new test must copy that. I also recorded why the assertion is not vacuous once fixed: the
sidecar is gitignored in this repo only through `.aw/.gitignore` (`records/history.jsonl`), which a
scratch fixture does not inherit, so a stray sidecar write genuinely shows as `??` and the empty-status
assertion detects it. Separately, V-05 told the executor to `git worktree add /tmp/opencode/base`, which
writes OUTSIDE the lane an execute turn is confined to and registers a worktree in the shared object
store that lane teardown does not own; replaced with an in-tree revert-and-restore method.

**ONE FINDING I ADDED THAT RAISES THIS PLAN'S VALUE.** The `--dry-run` write does not merely rewrite the
item, it DELETES unrecognized fields (measured: `- Custom-Field: KEEP-ME` gone, count 1 -> 0). That data
loss belongs to plan `2yqt0a`, which waits on this one, so the ignored `--dry-run` is currently the
delivery vehicle for a second, unrelated data-loss bug. I folded it into E-05 as a fixture detail (give
the item an unrecognized field so the byte-identity assertion also covers it) while explicitly keeping
the assertion as byte identity so this plan does not pre-empt `2yqt0a`'s renderer fix.

**WHAT I DID NOT CHANGE.** The explicit-gate approach over unification (OQ-01 is correctly resolved, and
its reasoning is now measurably right: unifying onto the positional path would inherit the F-7 hole),
all three Carrier-Declined deferrals, the sidecar-move design, the outcome-tests-only posture, and the
`apply` fallback (verified: `tests/test_backlog.py` has many `apply=True` call sites that would break
without it). The plan's structure, right-sizing, and E/V bijection are sound, and it is honest about the
duplicate item `19lmbe`, which I confirmed is genuinely the same defect.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE (reporting); OUT (fix) | B. security-adjacent (a bypassed gate with an unreachable backstop) | both spellings driven on one fixture: `--status` exit 1 with the three fixes, positional exit 0 + `Committed 2 path(s)`; `aw check release-gates` after the bypass -> `CONFORMS, errors 0`; `_staged_backlog_done_items` scoping in `check_engine.check_release_gate_consistency` | **F-7 UNDERSTATES ITSELF: THE POSITIONAL CLOSE ALSO SELF-COMMITS, WHICH PUTS IT BEYOND THE STAGED-SCOPED BACKSTOP.** The documented `check.blocking-item-closed-without-gate` examines only items whose close is STAGED in the current commit (deliberate grandfathering). A setter that commits its own move leaves nothing staged, so the release-gate check reports CONFORMS on a close that bypassed the gate entirely. The plan recorded the missing predicate but not that the safety net cannot fire. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low (for THIS plan: reporting only, no code change here) | FIXED | F-7 rewritten with the measurement and the backstop analysis; the gate's approval paragraph now names the adjacent hole so the approving human sees it; the fix stays out of scope and is attributed to backlog `mawwlc`. |
| PR-002 | MEDIUM | IN-SCOPE | A. correctness (a stale deferral and an obsolete hand-off route) | `.aw/records/backlog/open/20260926-gatebypass-01-mawwlc-positional-done-skips-release-gate.backlog.md` exists, `bug`/`high`/`Blocks-Release: next`, and its text credits this plan's author | **THE F-7 DEFERRAL PROMISES A VERBAL HAND-OFF FOR A DEFECT THAT IS ALREADY FILED.** It says "the authoring brief forbids filing backlog items, so it is reported to the maintainer in the authoring report for filing as its own bug". Item `mawwlc` already exists and already prescribes the fix, so the deferral would send the maintainer to re-file a duplicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The deferral now names `mawwlc` as the owner with its path and classification, and drops the obsolete authoring-report route. |
| PR-003 | MEDIUM | IN-SCOPE | A. correctness (a wrong artifact id in a stop condition) | `f2kqas` resolves only to `.aw/records/backlog/graduated/20260923-rendrop-01-f2kqas-...backlog.md`; the plan is `2yqt0a`, which declares `- Item-Dependencies: executed:wd6npl` | **THE GATE'S STOP CONDITION NAMES A BACKLOG ID AS A PLAN ID.** "plan `rendrop` / f2kqas depends on this one" points at an item, not a plan, so an executor checking for a concurrent editor searches for something that does not exist and may conclude there is no adjacent plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-10; the stop condition now names `2yqt0a`, states its declared paths and its dependency edge on this plan, and notes the runner therefore orders it after (file overlap only). |
| PR-004 | MEDIUM | UNDER-SCOPE | E. testing (an assertion that fails for an unrelated reason) | `SpecStatusDirectoriesTests.setUp` git-inits and mkdirs but never commits; the two existing relocation tests each do `git add -A` + `git commit -m initial` themselves | **E-06(a)'s EMPTY-`git status` ASSERTION CANNOT PASS ON THE FIXTURE AS DESCRIBED.** A spec written in the test body is untracked, so the status is non-empty before the command runs, and the test would fail for a reason unrelated to `--dry-run`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now states the precondition and points at the existing commit-first precedent in the same file; it also records why the assertion is non-vacuous (the sidecar is gitignored only via `.aw/.gitignore`, which a scratch fixture does not inherit, so a stray write shows as `??`) and forbids adding a fixture gitignore to force a pass. V-06 requires pasting the status. |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness; E. testing (a stronger assertion available for free) | scratch repro: `- Custom-Field: KEEP-ME` present before, `grep -c` = 0 after a `--dry-run`; `2yqt0a` front matter | **THE DRY RUN ALSO SILENTLY DELETES UNRECOGNIZED FIELDS, WHICH THE PLAN NEVER MENTIONS.** The template rebuild in `backlog._render_item` drops them, so today's ignored `--dry-run` is the delivery vehicle for a second data-loss bug owned by plan `2yqt0a` (which depends on this one). The E-05(a) fixture can cover it at zero cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-9; E-05(a)'s fixture item now carries an unrecognized field, with the assertion deliberately kept as BYTE IDENTITY so this plan does not pre-empt `2yqt0a`'s renderer fix. |
| PR-006 | LOW | IN-SCOPE | C. operability (an instruction that breaks lane containment) | V-05 as authored: `git worktree add /tmp/opencode/base <base-sha>` | **V-05 TELLS THE EXECUTOR TO WRITE OUTSIDE ITS WORKSPACE.** An execute turn runs in an isolated lane whose directory is its complete authorized workspace; adding a worktree under `/tmp` writes outside it and registers a worktree in the shared object store that lane teardown does not own. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 and V-06 now prescribe an in-tree revert-and-restore (or an in-lane checkout under `.aw/`) and explicitly forbid an out-of-lane worktree. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-7 reports a gate the positional setter skips. Accept the report, or probe how far the hole goes? | PROBE, and it goes further: the setter self-commits, so the staged-scoped backstop never sees the close and `aw check release-gates` reports CONFORMS. | (a) Accept as written: rejected, because "exit 0" and "no gate" understate a hole whose safety net is also unreachable, and the approving human is entitled to know which of the two it is. (b) Widen this plan to fix it: rejected, it is a different setter on a different code path, the plan's scope fence excludes it, and a fix belongs with its own tests; widening would also delay a measured user-facing bug fix. | Both spellings driven on one fixture; `_staged_backlog_done_items` scoping read in `check_engine`; post-bypass `aw check release-gates` measured CONFORMS. | yes |
| D-2 | The F-7 deferral promises a verbal hand-off. Leave it, or check whether the item exists? | CHECK, and it exists (`mawwlc`); rewrite the deferral to name it. | (a) Leave it: rejected, it would send the maintainer to file a duplicate of an item that already prescribes the fix and already credits this plan's author. (b) Close `mawwlc` as covered here: rejected outright, this plan does not fix it and marking it done would assert work that was not performed. | `.aw/records/backlog/open/20260926-gatebypass-01-mawwlc-...backlog.md` read in full. | yes |
| D-3 | E-06(a) asserts an empty `git status` on a fixture that never commits. Fix the item, or drop the assertion? | FIX THE ITEM, keeping the assertion. | (a) Drop the assertion: rejected, it is the one that detects a stray `git mv` and a stray sidecar, which is the whole defect on the specs side. (b) Add a gitignore to the fixture so the sidecar is invisible: rejected and explicitly forbidden in the item, because it would make the test pass while blinding it to the exact write it exists to catch. | `setUp` read (no commit); the commit-first precedent in the same file; the sidecar's ignore rule located in `.aw/.gitignore` and shown absent from a scratch repo. | yes |
| D-4 | The dry run also deletes unrecognized fields. Fold the fix in here, or only strengthen the test? | ONLY STRENGTHEN THE TEST (a fixture field plus byte identity); leave the renderer fix to `2yqt0a`. | (a) Fix the renderer here: rejected, `2yqt0a` owns it, declares the same files, and depends on this plan, so fixing it here would duplicate that plan and invalidate its own validation. (b) Say nothing: rejected, the data loss is real, it is caused by the very write this plan stops, and a fixture field covers it for free. | Measured field drop; `2yqt0a`'s `- Scope-Paths:` and `- Item-Dependencies: executed:wd6npl`. | yes |

### Deferred and open

- (none). All six findings were FIXED in place. PR-001 is the only one at HIGH severity, and its FIX is
  deliberately not in this plan: the finding is recorded, the adjacent hole is surfaced in the approval
  gate, and the remedy is owned by backlog `mawwlc`. Under the Fix Bar that is not a deferral of this
  plan's work, it is correct scoping of someone else's; nothing this plan is responsible for was left
  unfixed, and no question required the human (OQ-01 was already settled by the maintainer's brief and
  is now measurably the right call).

HONEST LIMIT, stated because it bounds what this round proves. I verified the DEFECTS and the plan's
edit targets; I did NOT implement the fix, so that the proposed gates land in exactly the right place
relative to every refusal remains E-01 through E-04's work and V-01 through V-04's evidence. In
particular `specs.run_set` has many refusal paths (illegal transition, human-authority floor, evidence,
review attestation, approval refusals, deferred gate, `--graduated-to`, `validate_spec` residual) and I
measured the sidecar-on-refusal behavior for only one of them (`--graduated-to`), plus the structural
fact that `_sidecar_append` precedes all of them; the other paths are asserted by E-03's expected
outcome rather than by my measurement. I also did not run the bare suite against a patched tree, so E-08
remains a real obligation. Finally, my F-7 escalation rests on one fixture and on reading the backstop's
scoping; I did not audit the real corpus for items closed through that path, and the 177 `done` items
carrying `- Blocks-Release:` in this repo are mostly grandfathered by design, so that count must NOT be
read as 177 bypasses.
