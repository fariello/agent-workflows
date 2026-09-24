# Review findings: plan hv9gar

- Subject-Id: hv9gar
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6810c451` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review, so nothing found below is structural;
`--phase review-finalize` conforms after revision.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them.

EVERY CLAIM IN THIS PLAN REPRODUCED, which is worth stating plainly because it is unusual across this
sweep. Built throwaway repos from the writer's REAL shape (`atomic_write` + `unlink`: destination
untracked, source deletion unstaged, confirmed as `" D open/a.md"` + `"?? done/"`), then drove the
gateway directly:

```text
# F-3, the ALREADY-FIXED route (explicit FILES)
EXPLICIT FILES -> status = committed   staged = ('done/a.md', 'open/a.md')
git show --name-status -> R100  open/a.md  done/a.md
git status --porcelain -> (empty)

# F-1, the OPEN route (source file + destination DIRECTORY)
DIRECTORY ARG -> status = committed   staged = ('open/a.md',)
                 detail = committed 1 path(s) as 3b435a73...
git show --name-status -> D  open/a.md          # the addition is NOT in the commit
git status --porcelain -> A  done/a.md          # it is left staged
```

So F-1 through F-5 all stand, and the plan's severity argument is sound. F-5 was additionally tightened
by inspection: BOTH existing rename tests build their fixture with `git mv`, which PRE-STAGES the
rename, so neither can reach the untracked-destination route, and no test in the module passes a
directory argument at all.

**THE FINDINGS BELOW ARE ADDITIONS, NOT CORRECTIONS. ONE IS A BLOCKER THE PLAN DID NOT MEASURE.**

```text
# PR-001: an ALL-DIRECTORIES call stages the move and then commits NOTHING, with no rollback
BOTH DIRS -> status = nothing-to-commit   staged = ()
git status --porcelain -> R  open/a.md -> done/a.md      # fully staged by the helper
git log --oneline       -> 6d750ed init                   # no new commit
```

The `git add` FAILURE path resets its own paths (`git reset --quiet HEAD -- *rel_paths`); this
`not our_staged` early return does not. So the caller is told "nothing to commit: requested paths have
no staged changes" -- a statement the index directly contradicts -- while the helper has silently
mutated the index. In a shared checkout that is exactly the contamination this module exists to prevent,
and it is a second route to the same one-half-of-a-move hazard.

```text
# PR-002: the plan's stated mechanism misdirects the fix
add_paths = [p for p in rel_paths if (repo_root / p).exists() or _in_index(repo_root, p)]
# the DIRECTORY exists on disk, so it IS in add_paths, and `git add -- done/` DOES stage done/a.md.
# The loss is at:  our_staged = now_staged & set(rel_paths)
#   now_staged holds 'done/a.md' (git reports FILES); rel_paths holds 'done/' -> no match.
# So the helper stages the destination and then declines to commit it.
```

F-1 reads as though the directory were never staged. An executor believing that could "fix" this by
adding directories to the ADD set, which changes nothing at all.

**AND THE ONE PRECONDITION THAT COULD HAVE BLOCKED OQ-01'S RECOMMENDATION IS NOW DISCHARGED.** The plan
required confirming no caller relies on a directory argument. Audited every in-tree call site:

```text
cli.py:5936  plans_archive.py:295  research_archive.py:400  runner_shared.py:27948
specs.py:862  status_set.py:1461  work_cmd.py:591
# SEVEN, not the four the module docstring and commit_lock name. Every one passes a computed
# FILE list. The exposed surface is `aw commit`'s user-supplied `-- <paths>` tail (work_cmd.run_commit),
# which is precisely how ca8e22e4 happened.
```

The decisive corroboration is that one caller ALREADY hit this trap and fixed it locally:

```text
# runner_shared.commit_backlog_close
# `-uall` is LOAD-BEARING. Git's default `--porcelain` collapses an untracked directory to the
# DIRECTORY entry (`?? .aw/records/backlog/done/`), whose basename carries no id6, so the
# id6 filter below silently matched nothing and the newly written item was never staged -- the
# move committed as a bare deletion, or not at all. Measured live before this flag was added.
...
if len(paths) < 2:
    return None        # fail closed on a partial view
```

That is simultaneously independent proof the gateway defect is real, the reason a refusal is safe, and
the model for how E-02 should enumerate the files it refuses.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A (correctness); B (shared-checkout safety) | isolated repo: `offer_commit(root, ['open/','done/'])` -> `status='nothing-to-commit'`, `staged=()`, `git status --porcelain` -> `R open/a.md -> done/a.md`, `git log` unchanged; the `not our_staged` early return performs no reset while the `git add` failure path does | AN ALL-DIRECTORIES CALL STAGES THE MOVE AND COMMITS NOTHING, WITHOUT ROLLBACK. The plan measured only the mixed file+directory shape. This second shape is worse: the outcome message asserts the paths had no staged changes while the index holds the full rename the helper itself staged, and no rollback occurs. A fix covering only the mixed shape leaves it live. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Recorded as plan F-6. Concern, Goal and Scope extended; E-01 must reproduce it; E-02 must cover BOTH shapes and site its refusal BEFORE staging (which fixes both at once and restores the no-mutation property); E-03 must reach the `nothing-to-commit` branch; E-04 must assert an unchanged index after a refusal; spec-sync must correct that outcome's false message. |
| PR-002 | MEDIUM | IN-SCOPE | F (honest documentation); G (plan executability) | the `add_paths` comprehension; `git status` showing `A done/a.md` staged after the mixed call | THE STATED MECHANISM IS WRONG IN A MISDIRECTING WAY. F-1 says a directory "contributes nothing to `our_staged`" as though it were never staged. It IS staged (it exists on disk, so it reaches `add_paths`); the loss is at the intersection, because git reports the file and the caller named the directory. An executor trusting the original wording could add directories to the ADD set and change nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-7. Concern corrected; E-01 now requires locating the loss point explicitly; E-02 opens by stating the mechanism and forbidding the no-op "fix". |
| PR-003 | MEDIUM | IN-SCOPE | G (plan executability) | seven `offer_commit` call sites audited; `runner_shared.commit_backlog_close`'s `-uall` comment and `len(paths) < 2` guard | THE SCOPE CHECK'S PRECONDITION WAS LEFT TO THE EXECUTOR THOUGH THE REPOSITORY ANSWERS IT. OQ-01's recommendation (refuse) was conditional on "no caller passes a directory today", which the plan deferred. Audited: all seven in-tree callers pass computed FILE lists, and one of them already fixed this exact trap per-caller. So refusal is safe and OQ-01 can be resolved now rather than during execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as plan F-8. OQ-01 RESOLVED to REFUSE with the audit as its basis (D-1); the scope-check bullet marked DISCHARGED with an instruction to re-confirm rather than re-derive; conventions corrected from "four" callers to seven. |
| PR-004 | MEDIUM | IN-SCOPE | C (architecture) | F-6's no-rollback measurement; the `git add` failure path's `git reset --quiet HEAD -- *rel_paths` | THE CHOICE BETWEEN REFUSE AND EXPAND WAS PRESENTED AS A TOSS-UP, and PR-001 breaks the tie decisively. Expansion cannot restore the "a refused call mutates nothing" property, because it still stages, so the all-directories shape would keep mutating the index; it would also have to re-derive gitignore semantics the staging path already owns. Refusal sited before staging fixes both shapes and leaves the index untouched. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope item (a) rewritten to name refusal and EXCLUDE expansion, with the reason; E-02 requires the refusal fire before staging and reuse an EXISTING outcome status; a scope-check bullet makes "site it after the add" a STOP rather than a fallback. |
| PR-005 | MEDIUM | UNDER-SCOPE | E (testing/verification); D (anti-regression) | both existing rename tests calling `git(repo, "mv", ...)`; no directory argument anywhere in `tests/test_git_commit_helper.py` | E-04'S TEST COULD HAVE BEEN WRITTEN SO IT CANNOT FAIL. The module's only two rename tests build their fixture with `git mv`, which pre-stages the move and is precisely why the current code passes them; a new test copying that idiom would test the already-fixed route. The plan warned about fixture realism in prose but did not name the `git mv` idiom as the specific trap, nor require the starting state be asserted. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now forbids a `git mv` fixture by name, requires the untracked/unstaged starting state be ASSERTED in the test so it cannot drift back, requires both directory shapes, and requires the two existing rename tests stay green as the parser-regression guard. F-5 tightened with the inspection evidence. |
| PR-006 | LOW | UNDER-SCOPE | F (honest documentation) | the `nothing-to-commit` message "requested paths have no staged changes"; `AGENTS.md`'s `aw commit -- <paths>` guidance | TWO DOCUMENTATION SURFACES ARE FALSE OR INCOMPLETE. The `nothing-to-commit` message asserts something the index contradicts in the F-6 case, and `AGENTS.md` instructs agents to use `aw commit ... -- <paths>` without warning that a directory silently loses work -- which is how the authoring agent produced `ca8e22e4`. Spec-sync covered only `offer_commit`'s docstring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync expanded: correct the `nothing-to-commit` text, record the refusal and WHY it fires before staging, and consider generalizing the "name destination FILES" instruction (which this plan's own gate already carries) into the agent-facing guidance. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: refuse a directory argument, or expand it to its files? | RESOLVED: REFUSE, sited BEFORE staging, naming the contained files. Written into the plan with the audit as basis. | EXPAND: rejected on PR-001's measurement. Expansion still stages, so the all-directories shape would keep mutating the index on a call that commits nothing, and it would have to re-derive `.gitignore` semantics the staging path already owns. The authored reason (refusal is louder) is correct but secondary; the deciding reason is that only a pre-staging refusal restores "a refused call changes nothing". | the seven-call-site audit (all pass files); `commit_backlog_close`'s prior per-caller fix; the `git add` failure path's existing reset versus the `not our_staged` return's absence of one | yes |
| D-2 | Does resolving OQ-01 at review overstep, since the plan assigned it to the executor? | No. Resolve it and record the audit, because the repository answers the one question the recommendation was conditional on. | Leaving it open for the executor: rejected because `plan-review.md` Step 3.1 forbids asking (or deferring to) a decision the repository already answers, and the audit is exactly that answer. The executor is still required to RE-CONFIRM at their HEAD, since a new caller could appear. | `plan-review.md` Step 3.1; the plan's own scope-check bullet naming this as the precondition | yes |
| D-3 | Is PR-001 a finding against THIS plan, or a separate defect needing its own artifact? | Against this plan: it is the same hazard (half a records move) in the same function, reachable through the sibling outcome branch, and the plan's Goal already claims to make the gateway "incapable of committing one half of a records move". | Filing a separate backlog item: rejected because a second artifact editing the same early return in the same function is the collision the scope fences exist to prevent, and because a fix for the mixed shape that ignored this one would leave the plan's own stated Goal false. | the plan's Goal and Scope wording; `AGENTS.md` (one owner per code region) | yes |
| D-4 | The plan's F-4 (shortfall not reported) is MED and E-03 is "defense in depth". Should E-03 survive now that E-02 is a hard refusal? | Keep it, and extend it to the `nothing-to-commit` branch. | Dropping E-03 as redundant once directories are refused: rejected on the plan's own reasoning, which review confirms: the silent-shortfall shape is reachable by ANY argument form the intersection does not match (a glob, a pathspec, a typo), so E-02 removes one cause while E-03 makes the class visible. PR-001 shows the class has a second outcome branch, which strengthens rather than weakens the case. | the plan's E-03 rationale; the intersection being a generic filter, not directory-specific | yes |
| D-5 | Should this review verify the plan's claim that `aw backlog set` still uses write+unlink (the premise of OQ-02)? | Verified rather than assumed: `backlog.py` carries `core.atomic_write(dest, rendered)` followed by `src.unlink()`, with no `git mv`. OQ-02's premise holds and it stays deferred with a carrier. | Taking the plan's word for it: rejected as the same unverified-premise failure this sweep found elsewhere. Adopting OQ-02 here: rejected, the plan's gateway-over-writer argument is sound and PR-003 strengthens it (a per-caller fix already existed and did not protect the gateway). | `agent_workflows/backlog.py` `atomic_write` + `unlink`; the 2026-09-13 `status_set` conversion referenced in `_staged_paths`' docstring | yes |

### Deferred and open

No finding is DEFERRED, OPEN, or REPLAN. Every finding above is FIXED, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule (default `block_at: HIGH`;
no `review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 is now `- Status: resolved` (D-1). OQ-02 remains OPEN by design: it is `- Blocking: no`,
maintainer-owned, a genuinely separate writer change with its own test surface, and it now carries a
durable carrier (`mx1b4v`). A non-blocking open question does not make a plan `NO-GO`.

### Notes on what was NOT changed, and why

- No code or test file was touched by this review. Only the plan under review and this record. All
  reproduction happened in throwaway git repositories under a scratch directory, which was removed;
  the lane's own tree was verified clean before and after.
- F-1 through F-5 were NOT retracted or downgraded. All five re-measured TRUE, and F-5 was strengthened
  with the `git mv`-fixture inspection. This plan's analysis was accurate; the findings are things it
  did not go far enough to measure.
- The `26519096` staged-rename parser was NOT touched and is explicitly protected: E-04 now requires
  the two existing rename tests stay green as the regression guard.
- OQ-02 was NOT adopted. Its premise was verified (`backlog.py` still writes-and-unlinks), and the
  plan's argument for fixing the gateway rather than one writer is strengthened by PR-003, which found
  a per-caller fix that already exists and does not protect the gateway.
- `- Blocks-Release: next` was left in place. It is inherited from `mx1b4v`, a live `bug`, and PR-001
  shows the hole is WIDER than filed (a second outcome branch loses the move and mutates the index),
  so the gate is still earned.
- The plan's `- Status:` is left at `to-review` in the file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
