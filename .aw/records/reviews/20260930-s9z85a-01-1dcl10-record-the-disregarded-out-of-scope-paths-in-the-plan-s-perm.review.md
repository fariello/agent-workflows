# Review findings: plan 1dcl10

- Subject-Id: 1dcl10
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (HIGH, fixed), PR-303 (MEDIUM, fixed), PR-304 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `62b18f47`. The plan file is committed and unmodified
(`git status --short` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY in fresh temp repos built with the suite's
own `support.ready_plan_text` fixture, rather than reading the plan's findings back. All scratch work
was done under the gitignored `tmp/` (`git check-ignore -v tmp/x` -> `.gitignore:42:tmp/`) and removed
afterwards; `git status --short` verified clean throughout. No production file and no test was modified.

THE PLAN'S DIAGNOSIS IS CORRECT AND UNUSUALLY WELL MEASURED. Nine of its findings reproduce exactly:

- F-01 REPRODUCES, so the backlog item really is falsified. Arrangement A (the out-of-scope path alone
  in an untrailered commit, the item's headline) gives `attribution_source: none-fail-closed`,
  `out_of_scope_paths: ['agent_workflows/render.py']`, `disregarded_unowned_paths: []`, and
  `finalize(apply=False, env={})` exit **1** demanding the reason. Arrangement B (same commit carrying
  `AW-Item: abc123`) is likewise still demanded. The item claims exit 0 for A; it is exit 1.
- F-02 REPRODUCES. Arrangement D (in-scope commit PLUS solo untrailered out-of-scope commit) gives
  `attribution_source: commit-cohesion`, `out_of_scope_paths: []`,
  `disregarded_unowned_paths: ['agent_workflows/render.py']`, and finalize with NO reasons exits **0**
  with `scope_reconciliation.resolved: True`. The escape is real; only its stated mechanism was wrong.
- F-04 REPRODUCES AND IS THE PLAN'S STRONGEST FINDING. After `finalize(apply=True)` on that shape:
  exit 0, the moved plan's history line is the bare
  `- 2026-09-30 executed (opencode/test): execute demo`, the plan text does NOT contain `render.py`,
  and `git log -1 --format=%B` does not either. The permanent record is SILENT, not merely incomplete.
- F-05 REPRODUCES. One arrangement holding a foreign-trailered path and an own-untrailered path yields
  `disregarded_unowned_paths: ['agent_workflows/mine.py', 'agent_workflows/theirs.py']` undifferentiated,
  with `trailer_attribution` `foreign_commits: 1, owned_paths: []`. The discarding arms are confirmed by
  reading: `elif classification == "foreign": foreign_count += 1` and `else: unknown_count += 1` both
  drop the `paths` list the owned arm keeps via `owned_paths.update(paths)`.
- F-07 REPRODUCES VERBATIM, including the fabricated-claim text. The false-demand shape gives
  `out_of_scope_paths: ['agent_workflows/coworker.py']`;
  `runner_shared.compute_scope_reconciliation(root, plan, labels=RS.OC_HOST_LABELS)` returns
  `{'agent_workflows/coworker.py': "changed by the plan's approved execution (auto-reconciled by aw oc run)"}`;
  and after finalize the executed plan's history line reads
  `[Scope reconciliation - out-of-scope agent_workflows/coworker.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]`,
  with identical text in the lifecycle commit. The asymmetry the plan rests on is real.
- F-08 REPRODUCES. `inspect.signature(LC.begin)` is
  `(repo_root, plan_path, actor, *, timestamp, isolated_baseline=False)`, keyword-only `timestamp`
  confirmed; `finalize` carries `env` exactly as described.
- F-09's PROTOTYPE WORKS, and I built my own rather than trusting the plan's: folding the note into
  finalize's `message` on the F-02 shape yields exit 0 with the path in both the plan history line and
  the lifecycle commit. The verdict is genuinely untouched.
- F-10 REPRODUCES. `test_case_2_untrailered_falls_back` carries exactly 3 assertions (the plan says
  five across the module, which matches `rg`: 4 in that file plus 1 in `test_ipd_lifecycle_cli.py:1075`).
  Its docstring does call the behavior intended. Targeted run: `60 passed in 21.02s`.
- The citations hold. `a6xbso` OQ-03 is quoted accurately ("the trailer's value is that it records a
  LIVE RUN's claim ... stays untrailered, i.e. unknown"). `h9cn0y` E-01 does forbid a lane-branch diff
  because `teardown_worktree` deletes the branch (its F-15 row says so). `9m4ujh` is `- Status: reviewed`
  at the declared path. The spec-sync claim verifies: `rg -lin` over
  `.aw/system/workflows/ipd-lifecycle/` for `cohesion|untrailered|unowned|disregard|AW-Item|heuristic`
  returns ZERO matches, and the `HONEST LIMIT` asymmetry paragraph E-04 cites exists verbatim
  ("MISSING demand ... never a false CLAIM written into permanent history").
- One citation is imprecise but harmless: the plan calls the adherence catalog `pqsx96`, and the spec's
  filename carries `pqsx96` while its own `- Id:` line reads `l`. The anchor resolves; noted, not filed
  (Step 1 disposition: anchor resolves, at most a LOW batched note).

TWO HIGH FINDINGS CAME FROM DRIVING THE PROPOSED DESIGN RATHER THAN THE DIAGNOSIS, and both would have
shipped a note that fails in the ordinary case. This is the review's substance: the plan's analysis of
the DEFECT is sound, and its FIX had two mechanical errors that only a prototype surfaces.

PR-301 (HIGH): F-06's inference was false and the design rested on it. The row concluded that naming
only the no-evidence class bounds volume. But F-06's own twelve co-worker commits are UNTRAILERED, so
they classify `unknown`, not `foreign`. Re-measured: `foreign_commits: 0, unknown_commits: 13`, and all
twelve paths are in the class the note WOULD name. I prototyped E-03 exactly as authored on that
arrangement: the moved plan's history line is 539 characters naming all twelve co-worker paths. The
same twelve commits carrying `AW-Item: zzz999` give an empty class and a 51-character line, which is
what the row mistook for the general case. The bound is weakest precisely where the plan matters, since
F-03 shows the runner already demands the path, so the escaping shape is the HAND execution, where
`a6xbso` OQ-03 rules the absent trailer correct. Scale on the live tree: of 279 no-merge commits in the
last 24h, 28 are untrailered and they touch 49 distinct paths. FIXED: F-06 rewritten with the
correction and the prototype numbers; E-03 now caps the enumeration at 5 sorted paths, always states
the total, and points the tail at the audit key; E-05 gains case (g) and V-03 gains the cap arm.

PR-302 (HIGH): the no-evidence class was to be derived by SUBTRACTION, which silently drops a path that
is this execution's own. E-02 as authored said the class is `disregarded_unowned_paths` minus
`disregarded_foreign_owned_paths`, derived at the point of use. Measured counter-case: write
`agent_workflows/shared.py` first in a commit trailered `AW-Item: zzz999`, then again in this
execution's own untrailered commit. Then `disregarded_unowned_paths: ['agent_workflows/shared.py']`,
the foreign set is `['agent_workflows/shared.py']`, and the difference is `[]`. The note falls SILENT
about the exact path the plan exists to record, and that silence is indistinguishable from a clean
execution: the defect reintroduced by its own derivation. Two agents editing one shared file is
ordinary, not exotic. FIXED: new finding F-13; E-01 now also collects `unknown_paths`; E-02 stores
`disregarded_no_evidence_paths` POSITIVELY and permits the two keys to overlap; V-01/V-02 gain overlap
arms plus the uncommitted case (a working-tree-only disregarded path appears in no commit and so in
neither E-01 set, which a bare intersection would also drop); E-05 gains case (f); OQ-02's rationale
corrected, since it had stated the exclusion as foreign-set membership.

PR-303 (MEDIUM): the gate did not state the honest limit of what the record now claims. The note
truthfully says a path could not be attributed and was justified by nobody, but it cannot say THIS PLAN
changed it, and after PR-301 the enumeration is also capped. A human approving this plan should know
they are getting class-level truth rather than actor-level attribution. FIXED: a fourth paragraph added
to the gate, and the under-scope line records the accepted bound.

PR-304 (LOW): E-01's constructor-compatibility note named one new field and one default, which after
PR-302 is two; it also under-described the two positional `TrailerAttribution(frozenset(), 0, 0, 0)`
early returns that the defaults must keep working. FIXED in E-01's revised text.

NOTHING WAS DEFERRED and no finding is left OPEN, so no escalation to a `- Blocking: yes` question is
required by Step 4's gate threshold (`review_findings_gate.block_at`, default `HIGH`).

OQ-01 verified genuinely non-blocking and correctly carried. The direction ruling is not needed for
this plan, because the plan changes only the record: I confirmed the prototype returns the identical
exit code with and without the note. The carrier is `s9z85a`, which the runner sets `graduated` rather
than `done`, so the question stays visible in `aw attention`. OQ-02 was `resolved` but on a rationale
that PR-301 and PR-302 both falsified; its answer (name only the no-evidence class) survives, its
reasoning is corrected, and it remains `resolved` because the corrected reasoning is measured.

`aw ipd lint --phase review-finalize --agent` reports `conforming` after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-03 bound the volume of paths it writes into permanent history, given PR-301 shows the class split does not bound it? | Cap the enumeration at 5 sorted paths, ALWAYS state the total count, and leave the full set in E-02's audit key. | (a) Leave it unbounded, rejected because the measured line is 539 chars naming 12 co-worker paths and reproduces the `mm6wuz` over-attribution the ownership filter removed; (b) name only a count and no paths, rejected because F-04's whole harm is that no path reaches a durable artifact, so a bare count restores the silence; (c) filter to paths matching the plan's own touched set, rejected as unavailable (F-11 measures lane isolation unsound and `h9cn0y` E-01 forbids the lane-branch diff). | Measured prototype: 12 untrailered co-worker commits produce a 539-char history line naming all 12 (`tmp` probe, this lane); `agent_workflows/ipd_lifecycle.py` `_execution_cohesive_committed_paths` ACCEPTED COST paragraph records the `mm6wuz` incident (10 demanded, 8 foreign) as the reason the filter exists. | yes |
| D-2 | Should the no-evidence class be derived by subtracting the foreign set, or computed positively from `unknown`-classified commits? | Positively, from `unknown_paths`, with the foreign and no-evidence keys permitted to OVERLAP. | Subtraction (as authored), rejected on measurement: with one path in both a foreign-trailered and an own untrailered commit the difference is `[]`, silencing the very deviation the plan records. Also considered normalizing the overlap by precedence (foreign wins), rejected for the same reason. | Measured probe in this lane: `disregarded_unowned_paths: ['agent_workflows/shared.py']`, foreign set `['agent_workflows/shared.py']`, difference `[]`. Recorded as F-13. | yes |
| D-3 | Does OQ-02's answer change now that both its stated grounds are falsified? | No: still name only the no-evidence class, but on corrected grounds (foreign trailer is positive evidence of another owner) and with exclusion redefined as foreign-AND-not-also-unknown. | Reopening it as an unresolved question, rejected because the corrected rationale is itself measured and the answer is unchanged; naming the foreign class too, rejected because it would write another agent's work into this plan's history. | `_commit_run_ownership` docstring's fail-closed rule ('unknown' is NEVER treated as 'foreign'); the `mm6wuz` note in `_execution_cohesive_committed_paths`; F-13's measurement for the overlap redefinition. | yes |
| D-4 | Is OQ-01 (the demand-versus-excuse direction) blocking for this plan? | No, leave it `open`, non-blocking, carried by `s9z85a`. | Marking it blocking, rejected because the plan provably changes no verdict (prototype exits 0 both ways) and a blocking question would hold a correct plan; resolving it myself, rejected because the backlog item states it needs a maintainer ruling and no such ruling exists in specs, plans, reviews, research, `DECISIONS.md` or the workflows. | Prototype exit-code invariance measured in this lane; `.aw/records/backlog/graduated/20260928-s9z85a-01-s9z85a-...backlog.md` ('needs a maintainer ruling on which direction fails safe'); `tests/test_finalize_trailer_attribution.py::test_case_2_untrailered_falls_back` pins the current direction. | yes |
