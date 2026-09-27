# Review findings: plan ounhsn

- Subject-Id: ounhsn
- Subject-Type: ipd
- Reviewed-At: 2026-09-27
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4bb6ffaf` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` returned `advisory` (exit 0) with ONE finding, `IPD-Z602` against E-05, which turned out to
name a real density problem (PR-008). `--phase review-finalize` conforms after revision with
`findings: 0`. No pre-review snapshot was needed: the plan was committed and unmodified, and the
lane-input copy at `.aw/state/lane-inputs/rev-1/` is byte-identical to the tracked file (`diff`
reported no difference).

THE DESIGN IS RIGHT AND THE MAINTAINER'S RULING IS NOT SECOND-GUESSED. Sending a merge-back conflict
to the agent that wrote the work, on its own session, in its own lane, bounded by the run's existing
`--retry-budget`, is the correct shape, and it reuses the right precedent: the gate-answer turn
(`perform_gate_answer` asked through `resume_via_launcher`) is an established follow-up turn inside an
item's own integration under the same budget, settled by the maintainer's 2026-09-20 "share it, add no
second knob" ruling. Siting the loop at the execute publish site is also right, because that is where
both the lock and `_publish` already are.

WHAT REVIEW FOUND IS THAT THREE OF THE PLAN'S MECHANICAL INSTRUCTIONS DO NOT WORK, and each was
measured rather than reasoned about. I built scratch repositories under the gitignored `tmp/` tree and
ran the real shipped code paths.

**THE WORST ONE IS A SILENT, SELF-DEFEATING FAILURE (PR-001/PR-002).** The plan told the agent to
commit its resolution with `aw commit <plan id6> -- <paths>`. Two measurements:

* `git commit -- <paths>` mid-merge exits 128: `fatal: cannot do a partial commit during a merge`. The
  path-scoped form the execution contract mandates cannot conclude a merge at all.
* `aw commit` does not conclude it either, and its failure is INVISIBLE. It routes through
  `git_commit_helper.offer_commit` -> `commit_lock.commit_isolated`, which snapshots HEAD into a
  detached throwaway worktree, commits there, and advances the branch by `update-ref` under a CAS.
  Measured: it reports `committed`, creates a SINGLE-PARENT commit, leaves `MERGE_HEAD` present, and
  leaves the incoming tip NOT an ancestor of the lane. The merge is recorded as an ordinary edit and
  the incoming side is never joined.

And the compounding defect: E-03's two proposed verification checks (no unmerged paths, no conflict
markers) BOTH PASS in exactly that state. I ran them on the post-`commit_isolated` lane and both
returned empty. So the runner would have declared the conflict resolved, re-run the merge-back, and
re-conflicted on the identical hunk (reproduced). The mechanism would have consumed the whole retry
budget producing nothing, then failed the item anyway with a worse record than today's.

**THE SHAPE SIGNAL WOULD HAVE BEEN DISCARDED (PR-004).** E-02 said to reuse
`classify_conflict_hunk_shape` for the shape. That predicate requires a `|||||||` base section and
git's DEFAULT conflict style emits none, so it correctly refuses to judge. Measured on one scratch
conflict: working-tree text -> `unknown` ("carry NO `|||||||` base section"), while
`classify_conflict_shape_from_stages` on the same conflict -> `adjacency-only`. The plan's own Concern
cites the adjacency signal as the reason this work is worth doing, so reusing the wrong entry point
would have thrown away the very fact the plan is built on, and told every agent the shape was unknown.

**A NON-`main` REPOSITORY WOULD HAVE FAILED OUTRIGHT (PR-005).** E-01 read the tip as `git rev-parse
main`. Measured in a scratch repo on `master`: exit 128, `fatal: ambiguous argument 'main'`. Every
shipped site that needs this value reads `HEAD` in `repo` (`_resolved_main_tip`, `git_head`), and the
lock has already recorded the correct value as `item["integration_serialization"]["main_tip_in_lock"]`.

**AN APPROVED SPEC SAYS THE OPPOSITE OF THIS PLAN (PR-003).** Spec `25kzda` Section 2.1a states
"EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge
conflict that does not positively classify", and Section 2.1 says the ladder "never applies to a
genuine merge conflict ... none of which repetition fixes". The plan's spec-sync section asserted no
spec is amended, on the reasoning that `fail-merge` remains the status for an unresolved conflict.
That is true and insufficient: the plan changes WHEN that status is reached, which is precisely what
2.1a legislates. AGENTS.md is explicit that a plan changing behavior a spec describes should carry the
amendment in the same change and declare the spec file in `Scope-Paths`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness | E-02 as authored ("commit with `aw commit <plan id6> -- <paths>`"); measured: `git commit -- f.txt` mid-merge -> `fatal: cannot do a partial commit during a merge` (rc 128); `commit_lock.commit_isolated(repo, ['f.txt'])` on a conflicted lane -> `status=committed`, commit has ONE parent, `MERGE_HEAD` still present, `git merge-base --is-ancestor <main tip> HEAD` fails | **THE INSTRUCTED COMMIT CANNOT CONCLUDE THE MERGE, AND FAILS SILENTLY.** The pathspec form git refuses outright; the `aw commit` path reports success while recording the resolution as an ordinary single-parent edit that never joins the incoming side. Re-running the merge-back then re-conflicts on the same hunk (reproduced), so the whole retry budget is spent achieving nothing and the item still ends `fail-merge` - with a worse record than today, because it now claims the agent resolved it. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-02 now instructs `git add -- <conflicted paths>` then a bare `git commit --no-edit`, and REQUIRES the prompt to carry both measured reasons so the agent does not "correct" itself back to the contract. Recorded as the plan's own F-6 and F-7. The gate's WHAT A HUMAN IS APPROVING section now names this as a deliberate bounded exception to the commit contract, with the measurements, rather than leaving it to be discovered. The false claim that out-of-scope paths are "recorded automatically" was removed (nothing records them: the lane's finalize reconciliation already ran before merge-back). |
| PR-002 | BLOCKER | UNDER-SCOPE | A. Correctness / D. Anti-regression | E-03's verification as authored (`git diff --name-only --diff-filter=U` empty and a marker grep empty); measured on the post-`commit_isolated` lane: unmerged paths `[]`, marker grep `[]`, yet `MERGE_HEAD` PRESENT and main NOT an ancestor | **THE CONSUMMATION CHECK WAS ONE CONDITION SHORT OF DETECTING PR-001.** Both authored conditions pass on a lane where the merge was never concluded, so the check could not tell a real resolution from the broken one the plan's own instruction would have produced. This is the guard that makes the mechanism safe to run unattended, and as written it would have passed the exact failure mode the plan shipped. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-03 now requires THREE conditions, with the third named load-bearing: `merge_in_progress(lane)` FALSE **and** `git merge-base --is-ancestor <prep.merge_head> <lane HEAD>` succeeding. A failure of (iii) is classified an UNRESOLVED attempt rather than a git fault, so it consumes the attempt honestly. Condition (ii) is kept path-scoped and line-anchored with the `diff_has_conflict_markers` reasoning cited (a whole-tree scan would reject a lane for pasting pytest output). E-08 case (e) was added to pin it, and V-08 requires proof the case is not vacuous. Recorded as F-7. |
| PR-003 | HIGH | UNDER-SCOPE | C. Architecture / spec sync | plan's "Spec / documentation sync" section as authored ("No `.spec.md` is amended"); spec `25kzda` Section 2.1a ("EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge conflict that does not positively classify") and Section 2.1 ("never applies to a genuine merge conflict ... none of which repetition fixes") | **THE PLAN CONTRADICTS AN APPROVED SPEC AND DECLARED IT DID NOT.** The plan's reasoning (that `fail-merge` remains the terminal status) is true but answers a different question: 2.1a legislates WHEN a genuine conflict becomes terminal, and this plan changes exactly that. Shipping code-only would leave an approved contract asserting the opposite of the behavior, and would also mean the runners never ANNOUNCE the change, since that announcement is driven off declared spec paths. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | New E-07 amends `25kzda` with a sibling Section 2.1b recording the maintainer's 2026-09-27 ruling and the agent-correction-versus-repetition distinction (parallel to 2.1a's recomputed-versus-retried), stating the four properties that bound it and leaving every ladder sentence, the two-quantity budget distinction and 2.1a itself untouched. The spec file is added to `- Scope-Paths:` so both runners announce it. V-07 requires the diff to show 2.1/2.1a unchanged plus `tests/test_run_flag_surface.py` green (that suite binds this spec's flag grammar bidirectionally). Recorded as F-11. |
| PR-004 | HIGH | IN-SCOPE | A. Correctness | E-02 as authored ("Reuse `classify_conflict_hunk_shape` for the shape"); measured on one scratch conflict: `classify_conflict_hunk_shape(<working-tree text>)` -> `unknown`, reason "hunk(s) 1 of 1 carry NO `\|\|\|\|\|\|\|` base section (git's DEFAULT two-way style)"; `classify_conflict_shape_from_stages(repo, ['f.txt'])` -> `adjacency-only` | **THE WRONG CLASSIFIER ENTRY POINT WOULD HAVE DISCARDED THE PLAN'S OWN PREMISE.** The bare hunk predicate needs a `\|\|\|\|\|\|\|` base section, which git's default conflict style does not write, so it correctly returns `unknown` for the working-tree file. The Concern cites `CONFLICT_SHAPE_ADJACENCY_ONLY` as the reason this work is worth doing, so every agent would have been told the shape was unknown and given the weaker instruction, for exactly the conflicts the plan exists to resolve cheaply. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now takes the mapping `build_conflict_resolver_detail` returns and reuses `classify_conflict_shape_from_stages` through it, with an explicit DO NOT naming the bare predicate and the measured `unknown` versus `adjacency-only` pair. E-03 was also corrected to build that detail WHILE THE MERGE IS IN PROGRESS, since the classifier reads the three index stages (the same ordering `integrate_lane_branch` already observes). The Concern's own symbol citation was corrected. V-02 now demands the adjacency render name `adjacency-only` rather than `unknown`. Recorded as F-8. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | E-01 as authored ("the tip is `git rev-parse main` read in `repo`"); measured in a scratch repo on `master`: `git rev-parse main` -> rc 128, `fatal: ambiguous argument 'main': unknown revision or path not in the working tree`; `git rev-parse HEAD` -> rc 0 | **THE TIP READ ASSUMES A BRANCH NAME THE CODEBASE DELIBERATELY DOES NOT ASSUME.** `_resolved_main_tip` and `git_head` both read `HEAD` in `repo`, and the value is already recorded by the lock this code runs inside. A hardcoded `main` fails outright on any repository using another integration branch name. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now reads the tip as `git rev-parse HEAD` in `repo`, and PREFERS the value the lock already recorded at `item["integration_serialization"]["main_tip_in_lock"]` (E-03 calls it inside that lock, so it is the same tip). E-05 case (4) pins a non-`main` repository and V-01 requires that evidence. Recorded as F-9. |
| PR-006 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Operability | E-01/E-03 as authored (no idempotency guard, no terminal-arm cleanup); measured: a second `git merge --no-ff --no-commit` with `MERGE_HEAD` present -> rc 128, `fatal: You have not concluded your merge (MERGE_HEAD exists)`; `lane_holds_finalized_plan` reads the lane BRANCH TREE and `reintegrate_lane` re-reads the lane | **AN UNCONCLUDED MERGE POISONED BOTH THE NEXT LOOP PASS AND THE HUMAN RECOVERY PATH.** The loop calls E-01 again after an unresolved attempt, and with `MERGE_HEAD` still present git refuses with an error whose real cause is the previous attempt, which E-01 would have reported as an unexplained git failure. Worse, the terminal arm left the lane mid-merge, and `aw <host> integrate <id6>` is the documented human remedy after `fail-merge` - so the plan could have stranded the work in a state where the remedy it points at also refuses. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-01 gains an entry guard: `merge_in_progress(handle.path)` true returns `ok=False` naming the unconcluded merge rather than running a doomed second merge. E-03's terminal arm now runs `git merge --abort` IN THE LANE (never in `repo`) when a merge is in progress before falling through, and records it, so every terminal path leaves the lane integrable by the existing human verb. V-01 requires the guard case; V-03 requires the post-terminal no-`MERGE_HEAD` evidence. Recorded as F-10. |
| PR-007 | MEDIUM | IN-SCOPE | B. Security / C. Operability | E-03 as authored (cause token read described as "the reason carries the `git-merge-conflict` cause token"); `read_integration_cause` is documented "The ONE reader" and `tag_integration_cause` "The ONE writer"; `perform_gate_answer`'s call site wraps the ask in `except (KeyboardInterrupt, StallTimeout)` so an interrupted follow-up leaves the refusal STANDING | **TWO ESTABLISHED DISCIPLINES WERE LEFT IMPLICIT AT A NEW CALL SITE.** The reason string is a deliberately PARSED INTERFACE whose format is a named constant precisely so no site spells the match itself, and the plan's phrasing invited a hand-rolled prefix test. Separately, the template the plan copies contains interrupt containment that the plan did not mention, so a Ctrl-C during a send-back could have raised out of the publish site instead of leaving the refusal standing, which is the fail-closed direction. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | E-03 now names `read_integration_cause` explicitly ("the ONE reader, never by matching the raw prefix") and requires the same `except (KeyboardInterrupt, StallTimeout)` containment the gate-answer caller uses, with the reason stated. The project-conventions section records both disciplines. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. Right-sizing and conceptual density | `aw ipd lint --phase author --detail` -> `IPD-Z602 (line 59): E-05: action text may bundle multiple concerns (3 clauses)`; rubric G diagnostics (b) and (c) | **ONE E-ITEM BUNDLED TWO TEST HARNESSES.** E-05 carried direct helper calls (a lane/main fixture and a prompt render) AND a full driver path with a patched spawn, a retry budget and event assertions. Those are two unrelated test surfaces needing two fixtures and two failure modes, which is diagnostic (b), and they are independently executable and verifiable, which is (c). Bundled, a fixture fault in the driver harness is indistinguishable from a helper regression in one V-item's evidence. The linter flagged it independently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05 (five UNIT cases over `prepare_lane_for_conflict_resolution` and `merge_conflict_question`, no driver, no spawn) and E-08 (five DRIVER outcome cases over the real publish site with a faked spawn, including the new consummation regression (e)). V-05 and V-08 added; `Highest E allocated` raised to 08; dependency edges re-pointed (E-05 on E-01/E-02, E-08 on E-03/E-04/E-05, E-06 on E-07/E-08). The E/V bijection is 8/8 and the linter now reports `conforming` with NO advisory. |
| PR-009 | LOW | IN-SCOPE | E. Testing | V-03 through V-06 as authored | Validation items demanded only the positive half of each change and cited E-05 for evidence that now lives in E-08. V-03 asked for cases (a) and (b) but nothing proving the merge was consummated; V-05 asked only that the file's cases pass. A fix that removed markers without joining the incoming side would have satisfied all of them. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-01 adds the non-`main` and already-in-progress cases; V-02 adds the shape-name regression and requires the commit instruction verbatim with an explicit absence assertion (no `aw commit`, no pathspec form); V-03 adds `consummated: true`/`false` records and the post-terminal no-`MERGE_HEAD` evidence; V-08 requires proof case (e) is NOT vacuous by running it against a two-condition implementation and showing it passes there. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan instructs `aw commit`, which cannot conclude a merge. Instruct a bare `git commit`, or make `aw commit` merge-aware? | Instruct a bare `git commit --no-edit` in the prompt, and say plainly in the gate that this is a bounded exception. | (a) Teach `commit_lock.commit_isolated` to conclude a merge: rejected as a much larger and riskier change to the shared commit path every `aw` verb and both runners depend on, well outside this plan's scope and its declared `Scope-Paths`; its whole safety property is that it commits in a DETACHED worktree, which is structurally incompatible with concluding a merge in the real one. (b) Have the RUNNER commit the resolution instead of the agent: rejected because it takes authorship of merged content away from the party that resolved it, and the runner cannot tell a finished resolution from an abandoned one. | Measured: `git commit -- <paths>` -> `fatal: cannot do a partial commit during a merge`; `commit_isolated` -> single-parent commit with `MERGE_HEAD` retained and the incoming tip not an ancestor. Git is the only thing that can conclude a merge it started, and the commit remains hook-gated and never pushed, so the protections the contract exists for are preserved while the mechanism becomes possible. | yes |
| D-2 | Is the two-condition consummation check sufficient, or does it need a merge-was-joined proof? | Three conditions, adding `merge_in_progress` false AND `merge-base --is-ancestor`. | Trust the agent's report; check only `MERGE_HEAD`; check only ancestry. | Measured: both authored conditions PASS on the post-`commit_isolated` lane where the merge was never joined, so the pair cannot detect the exact failure the plan's own instruction produced. `MERGE_HEAD` alone is insufficient too, since a `git merge --abort` clears it while joining nothing; ancestry alone would miss a half-finished merge. Both are needed and both are cheap. | yes |
| D-3 | Does this plan require a spec amendment, as its spec-sync section denies? | Yes; add E-07 amending `25kzda` with a new Section 2.1b. | (a) Ship code-only on the plan's reasoning that `fail-merge` remains the status: rejected because 2.1a legislates WHEN a genuine conflict becomes terminal, which is what changes. (b) Edit Sections 2.1/2.1a in place: rejected as strictly worse - those sentences were true when written and other plans were reviewed against them, so a sibling section following 2.1a's own precedent preserves the record. | Spec 2.1a: "EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge conflict that does not positively classify". AGENTS.md: a plan changing behavior a spec describes SHOULD carry the amendment in the same change and MUST declare the `.spec.md` in `- Scope-Paths:`. 2.1a is itself the precedent for a narrow carve-out added as a sibling section. | yes |
| D-4 | Which conflict-shape entry point should the prompt use? | `build_conflict_resolver_detail` (which uses `classify_conflict_shape_from_stages`). | Keep `classify_conflict_hunk_shape` on the working-tree file; set `merge.conflictStyle=diff3` in the lane so the bare predicate works. | Measured: the working-tree file yields `unknown` and the stage-based classifier yields `adjacency-only` for the same conflict. The shipped code already documents why (`git merge-file --diff3 IS USED RATHER THAN THE WORKING-TREE FILE, because the tree holds whatever conflict style git was configured with`). Mutating a lane's git config to make a weaker path work would add a config dependency for no gain, and `build_conflict_resolver_detail` is what the refusal path already calls. | yes |
| D-5 | Should the send-back count against `--retry-budget` or `--integration-retry-limit`? | `--retry-budget`, as authored; no change. | `--integration-retry-limit`; a third knob. | Spec 2.1 draws the distinction on cost: `--integration-retry-limit` counts re-attempts that "spend no agent turn", while a correction retry "spends a paid agent turn". This send-back spends an agent turn, so it belongs to `--retry-budget`, and the maintainer's 2026-09-20 gate-answer ruling ("share it, add no second knob") already settled the same question for the same shape of turn. E-07 records this explicitly so the two-quantity distinction is visibly preserved. | yes |
| D-6 | Split E-05, or accept the `IPD-Z602` advisory with a rationale? | SPLIT into E-05 (unit) and E-08 (driver). | Accept the advisory; split three ways (helper / prompt / driver). | AGENTS.md and this workflow both state a sizing signal is "an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed", and here the split falls cleanly along the harness boundary. A three-way split was rejected as over-splitting: the helper and the prompt are both direct pure-ish calls over the same scratch fixture and share a verification shape. After the split the linter reports `conforming` with no advisory and the bijection stays 8/8. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. The plan's single pre-existing open question (OQ-01, the maintainer's ruling that a
conflict should go back to the agent) was already `resolved` and non-blocking, and review did not
disturb it.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `advisory`, `findings: 1`, `IPD-Z602` against
  E-05 (before edits). `--detail` names it: "E-05: action text may bundle multiple concerns (chains
  multiple semicolon-separated action clauses (likely multi-concern; 3 clauses ...))".
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  (after edits, including the E-05/E-08 split, the V rebuild and the `Scope-Paths` widening). The
  `IPD-Z602` advisory is cleared.
- Lane input identity: `diff .aw/state/lane-inputs/rev-1/plan-...ipd.md
  .aw/records/plans/pending/20260927-mergeagent-01-ounhsn-....ipd.md` -> no difference. The plan was
  committed and unmodified, so no pre-review snapshot was owed.
- Scratch repository measurements (gitignored `tmp/` tree in the lane, real shipped code):
  - `git commit -- f.txt` during a conflicted merge -> rc 128, `fatal: cannot do a partial commit
    during a merge`. A bare `git commit --no-edit` from the same state -> rc 0, and the resulting
    commit has TWO parents.
  - `commit_lock.commit_isolated(<repo>, ['f.txt'], message=...)` on a conflicted lane -> `committed`,
    commit `0f0bee950191`, `parents=abd88d6` (ONE parent), `MERGE_HEAD` still present,
    `git merge-base --is-ancestor <main tip> HEAD` -> NO. The re-run merge-back then reported
    `CONFLICT (content): Merge conflict in f.txt` on the same hunk.
  - E-03's two authored checks on that same lane: `git diff --name-only --diff-filter=U` -> empty;
    `git grep -nE '^(<<<<<<<|>>>>>>>)' -- f.txt` -> empty. Both PASS while `MERGE_HEAD` is PRESENT and
    main is NOT an ancestor. This is the measurement behind PR-002.
  - Control: resolving with `git add f.txt` + bare `git commit --no-edit` gave `lane parents: ce8ce0e
    033a577` (two parents) and the merge-back then reported `Merge made by the 'ort' strategy` with
    `f.txt` containing both sides.
  - `classify_conflict_hunk_shape(<working-tree f.txt>)` -> `unknown`, "hunk(s) 1 of 1 carry NO
    `|||||||` base section (git's DEFAULT two-way style)". `classify_conflict_shape_from_stages(repo,
    ['f.txt'])` -> `adjacency-only`, "all 1 hunk(s) have an EMPTY base section".
  - In a repo on `master`: `git rev-parse main` -> rc 128, `fatal: ambiguous argument 'main'`;
    `git rev-parse HEAD` -> rc 0.
  - A second `git merge --no-ff --no-commit main` with `MERGE_HEAD` present -> rc 128, `fatal: You
    have not concluded your merge (MERGE_HEAD exists)`.
  - `work_cmd._staged_paths(<repo>)` during a merge that touched two files -> `['f.txt', 'o.txt']`;
    under a plan declaring only `f.txt`, `out_of_scope` -> `['o.txt']`, so `aw commit <plan>` would
    have refused on scope before reaching the commit at all.
  - The plan's own `Scope-Paths` parse: `['agent_workflows/runner_shared.py',
    'tests/test_merge_conflict_sendback.py', 'tests/test_runner_shared.py', 'CHANGELOG.md']`,
    `grandfathered=False`, and `agent_workflows/upgrade_rehearsal.py` (one of the measured conflicting
    files from the Concern) is NOT in scope, which is what makes PR-001's `aw commit` refusal concrete.
- Every claim in the plan's F-1 through F-5 re-verified at its symbol: `integrate_lane_branch`'s
  `merge_in_progress` arm and its "Nothing is RETRIED" comment; `classify_integration_refusal`
  returning False for `fail-merge` and `decide_integration_deferral`'s first terminal arm;
  `TURN_RETRY_CLASSIFICATION`'s `fail-merge` row reading "integration refused; owned by the
  integration deferral ladder or human"; `conflict_resolver_remedy`'s adjacency-only keep-both advice.
  `test_merge_conflict_terminal_and_budget_independence` confirmed as the pin the plan names.
- The precedent the plan copies confirmed at its symbols: `perform_gate_answer`'s docstring records the
  maintainer's 2026-09-20 budget-sharing ruling and its `retry_budget` parameter is
  `frozen_retry_budget(state)`; its call site's `resume_via_launcher` argument shapes differ per host
  exactly as the plan describes, and it is wrapped in `except (KeyboardInterrupt, StallTimeout)`.
- No code, test, or configuration file was modified. This review edited the plan and wrote this record.
