# Review findings: plan 9vglxd

- Subject-Id: 9vglxd
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `15222860` in a lane worktree; the plan was authored against `fe6a1d1e`, which is an
ancestor. Structural preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0,
`findings: 0`) and `--phase review-finalize --agent` conforms after revision with zero findings. No
pre-review snapshot was owed: the plan was committed and unmodified (added by `fe6339f4`) with
`git status --short` empty at review start, and it is byte-identical to the lane input copy. The plan
carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. Every measurement
below was taken against scratch two-tree fixtures under a `TemporaryDirectory`, never against this
repository, and `git status --short` was verified empty afterwards.

THE DIAGNOSIS VERIFIED IN FULL, AND MORE PRECISELY THAN MOST. This is an exceptionally well-measured
plan and the review's job was to re-drive its fixtures and then look where it had not. Six of its ten
findings reproduce with the REASON STRINGS MATCHING ITS QUOTES CHARACTER FOR CHARACTER. F-01: the
`_carrier_is_executed` path test and its self-dating docstring ("Maintainer ruling 2026-09-26 (OQ-01,
backlog rwhbci, closescope 2a6phj)") are exactly as quoted, so the item's 2026-09-16 "currently
benign" reasoning is genuinely expired. F-02: main-shaped tree `legitimate=False` with the
carrier-not-executed refusal naming both carriers; lane-shaped tree `legitimate=True`, `arm=HANDOFF`.
F-03: the real CLI at `--dry-run` gives exit 1 against main-shaped and exit 0 against lane-shaped. F-04:
the `resolve_evidence_artifact` matrix is `(main,main)=True (main,lane)=False (lane,main)=False
(lane,lane)=True`, exactly the four cells claimed. F-05: `evaluate_backlog_close` against the same
main-shaped fixture returns `close=False, reason='IPD carrier(s) not executed: ...carrier-b...'`, so the
outer predicate really is what holds the hole shut. F-06: in ONE tree with no lane, the setter accepts
via HANDOFF while the runner refuses, and the cause is visible as an early `return` on the first
executed carrier inside the arm's loop. F-08: all four cells of the ordinary-single-carrier matrix
reproduce, including the crucial one where citing the LANE's executed path against a MAIN gate tree
REFUSES. So the plan's premise, its error direction, and its stated main risk are all true.

THE DOMINANT FINDING IS THAT E-05 IS UNEXECUTABLE AS SCOPED, AND THE PLAN'S OWN FENCE IS WHAT BLOCKS
IT. E-05 says "THE CALLER ALREADY HAS BOTH VALUES AND HAS NAMED THEM", which reads as though
`process_backlog_close` calls `runner_shared.close_backlog_item` and one file carries the change. It
does not. `close_backlog_item` at that call site is a KEYWORD-ONLY INJECTED PARAMETER
(`close_backlog_item: Callable[..., tuple[int, str]]`), the body calls the injected callable with five
positional arguments and no `run_checked`, and the module-level function REQUIRES `run_checked`
keyword-only, so the two cannot be the same object. The callable is supplied by a thin per-host wrapper
defined in BOTH runners. E-05 therefore needs four coordinated edits across three files, two of which
were absent from `- Scope-Paths:`. An executor following the plan would either hit a scope
reconciliation failure or, worse, widen one host and not the other, giving one driver a gated close and
the other the status quo with nothing to object. Classified BLOCKER because the plan's central
behavioral change cannot be performed within its own declared fence.

THE SECOND FINDING IS THAT E-03 RESTS ON A FALSE CLAIM ABOUT A TEST, AND V-03 WOULD HAVE PASTED A GREEN
RUN THAT PROVED NOTHING. E-03 says declaring the flag "is not optional tidiness" because
`test_zero_undeclared_parser_leaves` requires zero undeclared leaves. Measured:
`find_undeclared_leaves` is `discover_parser_leaves(parser) - get_declared_leaves()`, and
`discover_parser_leaves`'s own docstring calls its output "CANONICAL leaf command paths". There are 151
leaves at this HEAD, not one containing `--`, `backlog set` is already declared, and the undeclared set
is empty. So that test is invariant to whether `--gate-dir` is declared. The declaration is still worth
making, but the forcing function had to be replaced with the repository's real precedent, which is a
PER-COMMAND flag-surface test (`tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser`
for `--set`, and `tests/test_runs_repo_alias.py` for `--repo`/`--dir`).

TWO EVIDENCE CORRECTIONS WORTH NAMING. F-10's own evidence sentence is FALSE in the plan's favour: it
claims a grep finds "only a completion-classification assertion in `tests/test_completion.py`" for the
pre-commit hook, and the grep finds NOTHING AT ALL - the line the authoring pass evidently matched is
`("n", False, "internal gate")`, about something else. So the hook has ZERO coverage, which makes
OQ-02's "defensible for a three-line delegation" a weaker position than stated, and the plan now says
so rather than flattering itself. And every one of F-07's six corpus figures drifted within a single
day (673 items not 653, 358 gated not 349, 277 carriers not 255, 32 multi not 31, 17 exposed not 16);
the CONCLUSION is drift-proof, but the figures were cited as bare numbers an executor would re-derive
and could mistake for a regression, so they are now labelled as drifting context.

WHAT THIS REVIEW DID NOT CHANGE. The route is untouched and it is a good one: E-03/E-04 ship the knob,
E-05 is the first caller, E-06 exists to prove the ordinary close survives and may legitimately
WITHDRAW E-05, and the ordering rationale between E-04 and E-05 is correct and load-bearing. F-14 was
added to record that E-04's risk analysis is right: all four "must not move" reads and the
gate-before-dry-run ordering are exactly where E-04 says they are. The `check_engine.py` exclusion, the
three OQ resolutions' reasoning, the four deferral dispositions (all carriers verified live), and the
no-spec-amendment argument all stand as authored.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | BLOCKER | UNDER-SCOPE | C. Architecture / G. Plan executability | `process_backlog_close`'s signature declaring `close_backlog_item: Callable[..., tuple[int, str]]` keyword-only; its call `rc, out = close_backlog_item(write_repo, item_path, item_id6, verdict.evidence or "", message)` (five positional, no `run_checked`); `runner_shared.close_backlog_item`'s `*, run_checked` requirement; `rg "close_backlog_item\("` -> exactly `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`; both host wrappers read | **E-05 IS UNEXECUTABLE WITHIN THE PLAN'S OWN FENCE.** It claims one caller in one file; the real chain is FOUR symbols in THREE files, because `process_backlog_close` calls an INJECTED callable supplied by a thin wrapper defined in EACH host. `oc_runipd.py` and `agy_runipd.py` were not in `- Scope-Paths:`, so two of the four edits were forbidden. Worse than a blocked edit: a one-sided widening would give one driver a gated close and the other the status quo, silently, which is the exact hazard `runner_shared`'s module docstring warns about. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (two one-line forwards once the chain is known) | FIXED | Both host files added to `- Scope-Paths:`; E-05 rewritten to enumerate all four symbols with what each must do and to require the two wrappers be widened IDENTICALLY, citing the both-drivers warning; new F-11; Scope check bounds the host edits to one forwarded keyword each; the gate gained a third specific gate naming the chain; V-05(b) requires both wrappers pasted side by side; OQ-04 records the widen-versus-split decision as D-1. |
| PR-702 | HIGH | IN-SCOPE | E. Testing and verification | `command_surface.find_undeclared_leaves` = `discover_parser_leaves - get_declared_leaves`; `discover_parser_leaves`'s docstring ("CANONICAL leaf command paths"); probe: 151 leaves, zero containing `--`, `backlog set` present, `find_undeclared_leaves` returns `set()`; `tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser`; `tests/test_runs_repo_alias.py` | **E-03'S STATED REASON FOR DECLARING THE FLAG IS FALSE AND V-03'S PROOF CANNOT PROVE IT.** `test_zero_undeclared_parser_leaves` compares COMMAND PATHS, so it passes whether or not `--gate-dir` is declared. The declaration would have shipped unverified while V-03 pasted a green run of an invariant test as evidence - decorative evidence of exactly the kind this workflow exists to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the correct precedent is shipped and cited) | FIXED | E-03 rewritten: false justification replaced with the true one (`legacy_flags` is the machine-readable surface), the per-command precedent cited by name, and a NEW flag-surface assertion required in E-02's class, written one-directionally so it cannot turn the pre-existing `--evidence`/`--yes`/`--commit` debt red. V-03(b) now demands that assertion and explicitly FORBIDS submitting the invariant test as the proof. New F-12. |
| PR-703 | HIGH | IN-SCOPE | Evidence accuracy | `rg -n "backlog_blocking_close_gate\|backlog-blocking-close-gate" tests/` -> no match; the `tests/test_completion.py` line the claim evidently matched is `("n", False, "internal gate")` | **F-10'S EVIDENCE SENTENCE IS FALSE IN THE PLAN'S OWN FAVOUR.** It states a grep finds "only a completion-classification assertion" for the hook; the grep finds NOTHING, so no test so much as imports the hook module. OQ-02 leans on that sentence when calling the gap "defensible for a three-line delegation", so the resolution rests on a stronger coverage claim than the tree supports. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected to state ZERO coverage with the actual grep result and the misattributed line named; OQ-02's weighing paragraph rewritten to say the delegation is "entirely unverified rather than incidentally touched" and that a reviewer should weigh the stronger version. The out-of-scope disposition is unchanged (it rests on the coupling being vacuous at the repo root, not on coverage). |
| PR-704 | MEDIUM | IN-SCOPE | D. Anti-regression (live-artifact counts) | Review re-measurement: 673 items / 358 gated / 277 with >=1 carrier / 32 with >1 / 17 with >1 AND gated / distribution `{1: 245, 2: 15, 3: 3, 4: 8, 5: 3, 6: 1, 9: 2}` against the authored 653 / 349 / 255 / 31 / 16 / `{1: 224, ...}` | **ALL SIX F-07 CORPUS FIGURES DRIFTED IN ONE DAY**, and they are cited as bare numbers. An executor re-deriving them at execution finds six mismatches and cannot tell whether the population moved or the plan was wrong, which is the failure the repository's live-artifact convention exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 now carries both measurements side by side, labels the figures as a DRIFTING POPULATION to be re-derived rather than an acceptance bar, cites the convention, and states explicitly that no E- or V-item depends on the number so the drift changes no decision. The conclusion (~17 exposed items, small but non-zero, supporting `medium`) is unchanged and noted as drift-proof. |
| PR-705 | MEDIUM | IN-SCOPE | E. Testing and verification | Bare `python3 -m pytest` at review on a clean tree -> `3069 passed, 2 skipped, 3 warnings in 41.11s`; per-file `11 / 37 / 27 / 1 passed`; `git merge-base --is-ancestor fe6a1d1e HEAD` | THE AUTHORED BASELINE IS SPENT, and E-08/V-08 demand a before-and-after comparison with no reference figure. Also worth stating positively: the tree IS fully green here, unlike several sibling plans in this sweep that carry a pre-existing unrelated failure, so an executor who assumed one would misattribute in the other direction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 with the aggregate and four per-file baselines; E-08 and V-08 carry them, state the bar as ZERO failures, and note the `11 passed` figure independently confirms the plan's own "all eleven existing tests" claim. |
| PR-706 | MEDIUM | IN-SCOPE | A. Correctness / F. Prevent silent failure | `resolve_verb_repo_root`'s docstring ("an EXPLICIT `--dir` is honored verbatim (resolved, no climb)" and "every other caller takes the cwd fallback SILENTLY"); `project_context.is_project_dir`'s docstring ("Used by repo-scoped verbs to decide between running and emitting `no_project_message`") | E-04 REQUIRES A LOUD REFUSAL FOR A NON-PROJECT `--gate-dir` BUT NAMES NO MECHANISM, and the resolver will not supply one: it honors an explicit path verbatim with no validation. Left unspecified, `--gate-dir /tmp/nothing` resolves to a records-free tree and every gated close then refuses with a message blaming the ITEM, which is the worse failure E-04 itself describes. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now names `project_context.is_project_dir` as the predicate (with its docstring's own statement of purpose), requires exit 2 (admitted by `backlog set`'s declared `exit_contract=(0, 1, 2)`), requires the message name the FLAG and PATH rather than the item, and requires the guard fire only when the flag is passed so the default path gains no failure mode. New F-15. |
| PR-707 | LOW | IN-SCOPE | E. Testing and verification | The `backlog set` declaration's own comment ("`--evidence`, `--yes` and `--commit/--no-commit` are accepted by the parser and remain undeclared here ... The existing agreement test is one-directional") | V-03(c) ASKS FOR A CLAIM THE EXECUTOR CANNOT SAFELY MAKE AS PHRASED. It requires stating the pre-existing undeclared debt "was NOT widened", but if the new flag-surface assertion is written bidirectionally it would turn that debt RED and force an out-of-fence fix to three unrelated flags. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03(c) now require the new assertion be written in the SAME one-directional shape (`declared - accepted == set()` plus an explicit `assertIn`), with the entry's own comment quoted to show the debt is pre-existing and deliberately left. |
| PR-708 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | The authored gate: commit/never-push and honesty rules present, `check_engine` fence and E-06 withdrawal present, but no statement of who performs the terminal transition | THE GATE LACKS FINALIZE OWNERSHIP, risking a double finalize under `aw oc run`. (Noted for balance: this gate is otherwise one of the better ones in this sweep - it already carries the scope fence, the honesty rule, and an explicit legitimate-withdrawal path for E-05.) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a LIFECYCLE TRANSITION paragraph with conditional runner-versus-executor ownership and the never-hand-roll-`git mv` rule, beside the new third gate naming E-05's call chain. |
| PR-709 | LOW | IN-SCOPE | D. Anti-regression | All four E-01 baselines re-driven at review HEAD with their verdicts, arms and reason strings; the two API details that cost review a failed attempt (`executed_overrides` is `Mapping[str, str]` of repo-relative strings; `CloseVerdict`'s arm field is named `path`) | E-01'S STOP-AND-RE-SCOPE TRIGGER HAS NO CURRENT REFERENCE VALUES. It tells the executor to re-measure four facts and stop if (a) has moved, but gives only the authoring HEAD's narrative, so a difference in wording rather than in verdict could read as a moved premise. Two API shapes are also easy to get wrong and would produce a spurious "fact has moved". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now carries all four review-measured results quoted verbatim for comparison, plus the two API details (override key type, verdict field name) recorded so the executor does not misread a harness error as an expired premise. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-05 needs edits in two host runners outside the fence. Widen `Scope-Paths`, or split E-05 into its own plan? | WIDEN by exactly two files, bounding each host's edit to one forwarded keyword. | (a) Split E-05 and E-06 into a second plan whose fence covers the hosts - rejected: E-06 exists to VALIDATE E-05 and may legitimately WITHDRAW it, so separating the change from the proof that may retract it makes a withdrawal unverifiable, and it would mean two plans touching the same function in sequence for one behavior. (b) Route the gate root through the existing five positional arguments so the wrappers need no edit - rejected as strictly worse: it reinterprets the wrappers' signatures instead of widening them, a silent contract change at exactly the seam `runner_shared`'s docstring warns about. | `process_backlog_close`'s injected-parameter signature and call site; `runner_shared.close_backlog_item`'s `*, run_checked`; the three call sites; both host wrappers; the plan's own E-04-before-E-05 ordering rationale | yes |
| D-2 | E-03's forcing-function test cannot see a flag. Drop the declaration requirement, or replace the test? | REPLACE the justification and require a NEW per-command flag-surface assertion. | (a) Drop the declaration as unnecessary since no test forces it - rejected: `legacy_flags` is the machine-readable flag surface other tooling reads, and the `backlog set` entry's own comment treats undeclared flags as debt, so omitting it would add to a debt the entry already apologizes for. (b) Keep citing `test_zero_undeclared_parser_leaves` with a note that it is weak - rejected: it is not weak, it is INVARIANT, so citing it at all would leave V-03 pasting proof of nothing. | The two `command_surface` functions and the 151-leaf probe; `tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser`; `tests/test_runs_repo_alias.py`; the `backlog set` entry's own debt comment | yes |
| D-3 | F-07's six corpus figures all drifted in a day. Re-measure them, or drop them? | RE-MEASURE and relabel as drifting context to be re-derived, keeping both sets side by side. | (a) Drop the numbers and argue exposure qualitatively - rejected: the row's stated purpose is that "the severity is a number rather than a vibe", and the number is what supports `medium` over `high`. (b) Replace the authored figures silently with the new ones - rejected: the drift is itself the useful fact, and showing both is what tells the executor to re-derive rather than to trust either. | Review re-measurement over the backlog and carrier trees; the repository's live-artifact re-derivation convention; the fact that no E- or V-item depends on the figure | yes |
| D-4 | F-10's coverage claim is false in the plan's favour, and OQ-02 leans on it. Correct the row only, or reopen the resolution? | CORRECT the row AND the OQ's weighing paragraph, keeping the out-of-scope disposition. | (a) Correct F-10 and leave OQ-02 as written - rejected: the OQ explicitly weighs the gap as "defensible ... and it is not nothing", a sentence whose force comes from the coverage that does not exist. (b) Reopen OQ-02 and bring the hook into scope - rejected: the disposition rests on the coupling being VACUOUS at the repo root (pre-commit's cwd), which is independent of coverage and still holds; adding a knob would change nothing observable. | The empty grep over `tests/`; the misattributed `("n", False, "internal gate")` line; the hook's `check`/`main` and the generator template; OQ-02's own reasoning structure | yes |
| D-5 | E-04's loud refusal has no mechanism. Specify one, or leave it to the executor? | SPECIFY `project_context.is_project_dir`, exit 2, message naming the flag and path, guard only when the flag is passed. | (a) Leave the mechanism open - rejected: the resolver's documented behavior (explicit path honored verbatim, silent cwd fallback for nearly every caller) means the default outcome of leaving it open is NO guard, and the failure mode is a refusal that blames the item, which is precisely what E-04 set out to avoid. (b) Hand-roll a `.aw` existence check - rejected: `is_project_dir` exists for this decision by its own docstring and also handles the legacy `.agents` marker, which a hand-rolled check would miss. | `resolve_verb_repo_root`'s and `is_project_dir`'s docstrings; `backlog set`'s declared `exit_contract=(0, 1, 2)` | yes |

### Deferred and open

None. Every finding is FIXED, including the BLOCKER. No finding was left OPEN or DEFERRED, so no
escalation to a `- Blocking: yes` open question is owed under the repository's `HIGH` gate threshold.
The plan's three pre-existing open questions (OQ-01, OQ-02, OQ-03) were already `resolved`; OQ-01 and
OQ-03 were re-verified and stand as written, OQ-02's reasoning was corrected where it rested on a false
coverage claim (PR-703) while its disposition stands, and OQ-04 was added to record decision D-1 in the
plan itself. All four Deferred-row carriers were verified live: `lsbd32` `open`, `mawwlc` `open`,
`le31pr` `open`, `a4em7s` `graduated`. No decision above carries `Reversible: no`.

FINAL GATES: `aw ipd lint --phase review-finalize --agent` exit 0 `findings: 0`;
`check_engine.evaluate_durable_carrier` returns zero drifts for this plan; `aw check` unchanged at its
pre-existing findings with none on this plan; `aw sanitize --agent` clean; `git status --short` showing
exactly the plan (modified) and this review record (new), with the throwaway probe removed.
