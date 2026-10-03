# Review findings: plan szkgb8

- Subject-Id: szkgb8
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
reports `clean` again at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator child-row check does not apply.

THE PLAN'S CENTRAL ARCHITECTURAL JUDGEMENT IS CORRECT AND I DID NOT DISTURB IT. The item's suggested
instrument (an AST sweep over `agent_workflows/`) genuinely is prohibited: `GUIDING_PRINCIPLES.md` P16
names `ast.parse` over production source explicitly, and backlog `1bxw6o` closed with a maintainer ruling
against restoring code-pinning guards. Substituting ruff `F811` and promoting it to CI is the right shape,
the enforcement gap is real (`grep -rn "ruff" .github/workflows/` returns nothing but an unrelated comment
in `local-leaks.yml`), and the plan's D-1 lays the reasoning out for dispute rather than burying it. The
deferral rows are unusually honest, each declining a carrier with a reason rather than parking work.

BUT THE GATE AS SPECIFIED WOULD NOT HAVE CAUGHT THE DEFECT IT WAS WRITTEN FOR, and that is PR-001. Ruff
exempts any name matching `lint.dummy-variable-rgx` from `F811`, and the default pattern
(`^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$`, read from `--show-settings`) matches EVERY leading-underscore
identifier. So `def _helper` defined twice is silently clean. This is not a corner: an AST census over
`agent_workflows/**/*.py` counts 4,335 top-level definitions of which 1,189 are leading-underscore, and
"lift a symbol, leave a thin private wrapper" is precisely what commit `12a5c05b` was doing when it
introduced the `locked_run` bug this item records.

I proved it decisive rather than arguing it. Taking the plan's own historical reconstruction (wrapper at
2695, stale copy re-inserted at 7035) and renaming `locked_run` to `_locked_run` makes the plan's own
specified command print `All checks passed!` and exit 0. Shadowing a LIVE private wrapper,
`oc_runipd._detect_driver_command` (`agent_workflows/oc_runipd.py:4115`), in a scratch copy is likewise
silent. Adding `--config 'lint.dummy-variable-rgx="^$"'` makes both report
`F811 Redefinition of unused '_locked_run' from line 2695` and exit 1. So the plan would have shipped a
green gate over the exact bug class it exists to refuse, which is worse than no gate because it
manufactures assurance. Fixed in E-01/E-02/E-03 and recorded as decision D-2 in the plan.

THE OVERRIDE HAS TO BE CLI-SCOPED, WHICH IS PR-004 AND IS THE KIND OF THING A LATER TIDY-UP BREAKS. The
natural move is a persistent `[tool.ruff.lint]` key. Measured, that reds the repository: with the pattern
emptied repo-wide, the pinned ruff's own full-default run reports six
`F841 Local variable '_' is assigned to but never used` findings in `tests/`, because `F841` uses the SAME
pattern to exempt intentional throwaway bindings. E-03 now carries that as an explicit DO-NOT with the
measurement, so an author shortening "a long CI command" into config does not silently red `main`.

THREE OF THE PLAN'S MEASUREMENTS WERE TAKEN WITH THE WRONG BINARY (PR-002). The plan pins `ruff==0.4.4`
correctly but measured with the ambient `0.16.3` on `PATH`, and the two disagree structurally: 60 enabled
rules by default versus 413. Consequences, all re-measured: F-05's "8,061 errors" is `0.16.3`'s figure and
`0.4.4` reports `All checks passed!` under its FULL default selection over `agent_workflows/`, `tests/`,
and the whole repo; F-06's claim that `tests/` NEEDS `--target-version py312` is false for `0.4.4`, which
is clean either way (the two `invalid-syntax` findings at `tests/test_check_engine_spec_criteria.py:236`
are `0.16.3` parsing 3.12-only f-string syntax at the inferred 3.9 floor); and F-02's "both versions agree
on the reconstruction" is true for the public name while both equally miss the private one. I kept both
flags and rewrote their justifications: `--select F811` is now justified by VERSION STABILITY (a bare
default selection would import thousands of findings on a future `rev` bump) and `--target-version py312`
as FUTURE-PROOFING, which is honest and still leaves both in the command. E-01 now mandates installing and
naming the pinned binary before measuring anything, and I verified `ruff==0.4.4` is pip-installable on
Python 3.14 in a clean venv with the gate command exiting 0 there, so the pin is deliverable and not just
desirable.

WHAT I CHECKED THAT CAME BACK CLEAN, since a review that reports only failures is not informative. Every
one of F-01 through F-09's other claims reproduces. The `attention-check` job is exactly as described (a
single-OS, single-Python, read-only, fail-closed lane whose own comment states the "not per Python matrix"
precedent, already hosting five `python -m agent_workflows check ...` steps), so E-03's placement is right
and adding a 19th matrix cell would buy nothing for a property of source text. F-07's non-auto-fixability
re-verified by md5sum on both versions (file byte-identical, still exit 1), which matters because the local
hook passes `--fix` and an auto-fix would delete one of two definitions at random. F-04's four probes all
reproduce. F-08's `ALIAS = f` hole is real, persists under the override (so it is a property of the rule,
not of the configuration), and its three stated NON-holes (version-conditional, `try/except ImportError`,
`@typing.overload`) stay correctly silent - I re-ran all three in private-named form plus `for _ in ...`
and `_ = x` to confirm emptying the pattern introduces no false positive, which is the obvious objection
to PR-001's fix. F-09 is right that `tests/test_hostdedup_identical_lift.py` is gone and that pending plan
`vbhat9` independently declines to restore it, naming `s6om7k` as the carrier.

ONE PRE-EXISTING RECORD DEFECT SURFACED AND WAS FIXED (PR-008). The plan's two same-date history records
were authored `draft` then `to-review` descending the file, which a newest-first reader derives as the
backwards transition `to-review -> draft`, so `aw check plans` reported `check.lifecycle-transition-invalid`
against it. I confirmed on the PRE-REVIEW text that this is the plan's own latent defect rather than
something the review introduced; what the review changed is that adding a correctly-placed `reviewed`
record made the date group classifiable and surfaced it. Reordering the two records (content untouched)
clears it, and `aw check plans` now reports zero findings mentioning `szkgb8`.

ONE QUESTION I RAISED AND ANSWERED MYSELF, recorded as OQ-03 in the plan and D-3 below. The fix creates an
asymmetry: CI catches the private-symbol case and the local hook does not. I accepted it rather than
chasing parity, because parity needs a second separately-configured ruff hook invocation (the shared
setting cannot change, per PR-004), which alters every contributor's commit path and is disproportionate to
a plan whose own premise is that CI is the authority and local hooks are skippable. The honest consequence
(green local commit, red CI run) is now in the plan's Scope check rather than left for a contributor to
discover. That is strictly better than today, where neither surface catches it.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | D (anti-regression) / E (verification) | `ruff check --show-settings` -> `linter.dummy_variable_rgx = ^(_+\|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$`; `agent_workflows/oc_runipd.py:4115` `_detect_driver_command`; plan E-03 as authored | THE GATE WOULD HAVE MISSED THE DEFECT CLASS FOR EVERY PRIVATE SYMBOL, WHICH IS THE SHAPE THE ORIGINAL DEFECT TAKES HERE. Ruff exempts names matching `dummy-variable-rgx` from `F811`, and the default pattern matches every leading-underscore identifier, so a duplicated `def _helper` is silently clean. 1,189 of `agent_workflows/`'s 4,335 top-level definitions are leading-underscore, and "lift a symbol, keep a thin private wrapper" is exactly what `12a5c05b` was doing when it introduced the bug. Measured decisive: the plan's own historical reconstruction renamed to `_locked_run` makes the plan's specified command exit 0 with no finding, and shadowing the LIVE `_detect_driver_command` wrapper is likewise silent. The plan would have shipped a green gate over the bug it exists to refuse, which is worse than no gate because it manufactures false assurance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `--config 'lint.dummy-variable-rgx="^$"'` to the gate command in E-03, with the reasoning and blast-radius figures in its comment. E-01(b) now REQUIRES proving the override load-bearing by probe before CI is touched, and makes its absence a stop condition. E-02 now requires the private reconstruction and a live-wrapper shadow, with the without-override exit 0 as mandatory evidence. V-01/V-02/V-03 strengthened to demand both namings. Recorded as plan decision D-2 and finding F-10. |
| PR-002 | HIGH | IN-SCOPE | A (correctness of the record) / E | Pinned `0.4.4` (`~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff`) versus ambient `0.16.3`, same commands, same tree | THREE MEASUREMENTS WERE TAKEN WITH A BINARY THE GATE DOES NOT USE, AND ALL THREE ARE WRONG FOR THE PINNED ONE. The plan pins `ruff==0.4.4` but measured with ambient `0.16.3`; the two enable 60 versus 413 rules by default. So (a) F-05's "8,061 errors" is `0.16.3`'s number while `0.4.4` reports `All checks passed!` under its full default selection, voiding the stated justification for narrow selection; (b) F-06's "`tests/` NEEDS `--target-version py312`" is false for `0.4.4`, clean either way; (c) F-02's "both versions agree" is true only for the public name. An executor re-measuring per E-01 would have hit three contradictions and had no basis to tell a real divergence from a version artifact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 and F-06 rewritten with both versions' measurements and corrected conclusions; F-02 carries the scope correction; new F-11 records the root cause and the 60-versus-413 figure. Both flags RETAINED with honest justifications (`--select` for version stability, `--target-version` as future-proofing) rather than dropped. E-01 now mandates installing the pinned binary into a scratch venv and pasting `ruff --version` beside every figure; V-01/V-02 require the version output. Verified `ruff==0.4.4` pip-installs on 3.14 and the gate command exits 0 there. |
| PR-003 | MEDIUM | IN-SCOPE | G (execution contract) | Plan `## Approval and execution gate` as authored | THE EXECUTION CONTRACT WAS MISSING THREE REQUIRED ELEMENTS. It carried the path-scoped commit and never-push rules but had no scope-fence DECLARATION semantics (so an executor facing a necessary out-of-scope edit had no instruction), no explicit "paste the ACTUAL runner output" honesty rule, and no lifecycle-transition ownership statement (leaving ambiguous whether the executor or the runner finalizes). Per the 2026-09-01 maintainer ruling the fence must be make-and-justify rather than stop-and-report, which the plan also did not state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states the fence as a declaration reconciled afterwards via `aw ipd finalize --scope-reason`/`--scope-ack`, carries the explicit paste-the-actual-output honesty rule, and states the conditional transition ownership (runner finalizes when dispatched by `aw oc run`/`aw agy run`; a human executor runs `aw ipd finalize`). ONE genuine stop condition is stated SEPARATELY and correctly (if E-01 finds the override unnecessary the design premise has changed), which the ruling preserves as a different case. |
| PR-004 | MEDIUM | IN-SCOPE | C (operability) / D | `0.4.4 check --no-cache --config 'lint.dummy-variable-rgx="^$"' .` -> "Found 6 errors", all `F841`, incl. `tests/test_runner_shared.py:1988`, `tests/test_workflow_artifacts_prune.py:226` | THE OBVIOUS WAY TO APPLY PR-001'S FIX WOULD RED THE EXISTING PRE-COMMIT HOOK. Setting `dummy-variable-rgx` persistently in `pyproject.toml` breaks `F841`, which uses the same pattern to exempt intentional throwaway bindings, producing six findings in `tests/` on the hook's own full-default run. Left unstated, a later author tidying a long CI command into configuration would red `main` for a reason unrelated to this gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 carries an explicit DO-NOT with the measurement and the `F841` mechanism; the Scope check records that the override is per-invocation precisely so it is not a repository-wide config change; new finding F-12 records it. Verified the CLI-scoped form leaves the hook green (`--select F811` + override over all three directories, exit 0). |
| PR-005 | LOW | UNDER-SCOPE | C / F | `find tools -name '*.py'` -> 18 files; `wc -l tools/runner_fork_scan.py` -> 931; `pyproject.toml:122` `packages = ["agent_workflows"]` | THE GATE OMITTED `tools/` WITHOUT A STATED REASON. It holds 18 tracked Python files including `runner_fork_scan.py`, the very scanner `12a5c05b` used to measure this defect class, and `ipdrunner/`. It is already clean under the gate, so the omission was arbitrary rather than principled. Kept LOW because `tools/` is not shipped in the wheel, so a defect there has a smaller blast radius than one in the package. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `tools/` added to the gate command in E-03 and to the plan's `- Scope:`; OQ-01 widened to record the reasoning; new finding F-13. Verified the three-directory command exits 0 with the pinned binary. |
| PR-006 | LOW | UNDER-SCOPE | F (honest documentation) | Plan E-04 as authored; `tests/test_carrier_scan_single_item_contract.py` docstring KNOWN HOLE precedent | THE P16 AMENDMENT DID NOT REQUIRE THE GATE'S LIMITS TO BE STATED, so the paragraph would have read as a completeness claim. The plan knows two limits (F-08's `ALIAS = f` module-level-consumption hole, and that the gate binds future commits without proving history clean) but confined them to its own findings table, which no future reader of `GUIDING_PRINCIPLES.md` will consult. E-04 also lacked any instruction not to reword existing prohibition bullets while amending the section. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires both KNOWN HOLES in the paragraph, citing the `test_carrier_scan_single_item_contract.py` docstring precedent, requires the amendment be one paragraph phrased as a boundary clarification, and forbids weakening any existing P16 prohibition. V-04 now requires the holes quoted and `git diff GUIDING_PRINCIPLES.md` showing additions only. |
| PR-008 | LOW | IN-SCOPE | A (record correctness) | `ipd_lifecycle._plan_status_event_groups` on the plan text; `check_engine.check_lifecycle_transitions`; `check.lifecycle-transition-invalid` | THE PLAN'S TWO SAME-DATE HISTORY RECORDS WERE IN THE WRONG RELATIVE ORDER FOR A NEWEST-FIRST HISTORY, so `aw check plans` reported `check.lifecycle-transition-invalid` against it. Authored as `draft` then `to-review` descending the file, which a newest-first reader derives as the backwards transition `to-review -> draft`: `validate_transition` returns `ok=False, reason="missing predecessor: backwards transition 'to-review' -> 'draft'"`. Measured on the pre-review text, so it is the plan's own latent defect and not something this review introduced; adding a correctly-placed `reviewed` record is what made the group classifiable and surfaced it. Worth fixing rather than leaving: the rule is one of five other pending plans' findings too, and a plan whose own recorded lifecycle does not validate is a weak base for a plan about enforcement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered the two 2026-09-30 records so the history is newest-first throughout (`reviewed`, then `to-review`, then `draft`). `_plan_status_event_groups` now yields `('2026-09-30', [('draft',...), ('to-review',...)], True)` and `('2026-10-01', [('reviewed',...)], True)`, and `aw check plans` reports zero findings mentioning `szkgb8` (was 1). No history CONTENT was altered, only the order of two records within one date. |
| PR-007 | LOW | IN-SCOPE | A | Plan F-04 "every realistic shape of this defect"; F-02 "both versions agree"; the four original probes | TWO FINDINGS OVERSTATED THEIR SCOPE IN THE EXACT RESPECT PR-001 TURNS ON. F-04 claimed `F811` covers "every realistic shape ... including the ones a naive reading would expect it to miss", but all four of its probes used PUBLIC names, so the claim held only for public symbols. F-02 claimed the two ruff versions "agree on the reconstruction", which is true for the public name and conceals that both equally miss the private one. A reader trusting either would conclude no override was needed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 carries an explicit SCOPE CORRECTION naming F-10 as superseding it for private names and records that all four probes re-ran clean at review; F-02 carries the correction that version agreement must not be generalized; F-08 records that the three non-holes were re-measured in private-named form under the override and stay silent. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | `F811`'s default configuration misses every private symbol. Fix the gate, or retire the plan as unable to deliver the item's property? | FIX the gate with a CLI `--config 'lint.dummy-variable-rgx="^$"'` override. | (a) Ship as specified: REJECTED, it passes while the bug sits in the tree, manufacturing false assurance, which is worse than no gate. (b) Retire the plan and reopen the AST-sweep question: REJECTED, one flag closes the gap, so the prohibited instrument remains unnecessary and the item's property is fully deliverable. (c) Set the pattern in `pyproject.toml`: REJECTED on measurement, it reds `F841` (PR-004). (d) Accept public-only coverage and file a carrier for private symbols: REJECTED, the private case IS the measured defect's own shape, so deferring it would defer the item's actual content. | Default pattern from `--show-settings`; private reconstruction exits 0 without the override and reports `F811 ... from line 2695` with it; live `_detect_driver_command` shadow behaves identically; AST census 1,189 of 4,335 top-level defs leading-underscore; all three legitimate shapes plus `for _ in` and `_ = x` stay silent under the override. | yes |
| D-2 | Where must the `dummy-variable-rgx` override live? | ON THE COMMAND LINE of the gate's single invocation only. | Persistent `[tool.ruff.lint]` in `pyproject.toml`: REJECTED on measurement, it reds the existing pre-commit hook with six `F841` findings in `tests/` because `F841` shares the pattern. A dedicated `ruff.toml`: REJECTED for the same reason, since it would apply to the hook's invocation too. | `0.4.4 check --no-cache --config 'lint.dummy-variable-rgx="^$"' .` -> 6 `F841` errors; the same with `--select F811` over `agent_workflows/ tests/ tools/` -> exit 0. | yes |
| D-3 | The fix makes CI catch a case the local hook does not. Accept the asymmetry or bring the hook to parity? | ACCEPT the asymmetry; do not touch the hook in this plan. | Bring the hook to parity with a second separately-configured ruff hook invocation: REJECTED as disproportionate, it changes every contributor's commit path for a plan whose premise is that CI is the portable authority and local hooks are skippable and untrusted as the boundary. Change the shared setting: REJECTED, that is D-2. | The plan's own F-03 establishes CI as the authority (four measured local-only holes: `--no-verify`, fresh clone before `pre-commit install`, `default_stages: [pre-commit]`, and `pre-merge-commit` not firing on a fast-forward). PR-004's measurement forecloses the shared-config route. | yes |
| D-4 | `--target-version py312` is not needed by the pinned `0.4.4`. Drop it as dead weight or retain it? | RETAIN, relabelled as future-proofing with both measurements recorded. | Drop it: REJECTED, a future hook `rev` bump would then red `main` with two `invalid-syntax` errors at `tests/test_check_engine_spec_criteria.py` for a parse reason unrelated to duplicate definitions. Fix the two findings in that file instead: REJECTED as out of scope, nothing is broken for a user (CI runs the suite on 3.9 through 3.14 green). | `0.4.4` over `tests/` exits 0 with and without the flag; `0.16.3` without it reports 2 `invalid-syntax` at `:236` and with it "All checks passed!"; `pyproject.toml:12` `requires-python = ">=3.9"` is what ruff infers from. | yes |
| D-5 | Verdict and readiness, given the plan had a BLOCKER that is now fixed and carries no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REVIEWED - OPEN QUESTIONS`: REJECTED, all three open questions are `resolved` and none is `Blocking: yes`. `REJECT - NEEDS REPLAN`: REJECTED, the plan's approach is sound and the BLOCKER was repairable with bounded edits (one flag plus evidence strengthening), which is the documented test for REPLAN. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and explicitly says a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary and the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01) that a non-blocking open question does not force `no-go`. Zero findings left `OPEN` or `DEFERRED` at or above the `high` gate threshold (`review_findings_gate.block_at` default), so no escalation to a `Blocking: yes` question is owed. `aw ipd lint` reports `clean` at `author` and `review-finalize`. | yes |
