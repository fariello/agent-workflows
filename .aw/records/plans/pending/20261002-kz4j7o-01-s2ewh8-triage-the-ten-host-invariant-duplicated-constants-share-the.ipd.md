# IPD: Triage the ten host-invariant duplicated constants: share the three real ones, delete the four dead ones, decline the three per-host ones

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `kz4j7o` names ten host-invariant constants duplicated as literals in `oc_runipd` and `agy_runipd` with no shared definition, and asks for them to be triaged individually rather than swept mechanically. Performing that triage finds the item's own framing is wrong for SEVEN of the ten: four are DEAD (no reader anywhere in the tree, so the fix is deletion and not a shared home), and three are deliberately per-host (one a mutable flag the shared module's docstring prohibits, two a tuning seam a shipped test drives). Only three are genuine shared-home candidates. The identical-copy hazard the item cites is real for those three and is not addressed by a shared home for the other seven.
- Scope: Triage all ten individually and act on the measurement. SHARE the three genuinely host-invariant immutable values (`DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `LANE_PROMPT_TIMEOUT`) by pointing each host at one `runner_shared` definition. DELETE the four with zero readers (`OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE`, `_close_process_streams`) from both hosts, since a shared home for dead surface preserves the surface rather than removing the hazard. DECLINE the three per-host ones with their reasons recorded in the code. No behavior change: every resolved value, every argv, and the grace-tuning seam are identical before and after.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_forkresid_shared_shells.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: kz4j7o
- Set: kz4j7o
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: s2ewh8
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: suite bar by failing node-id set; F-11 failures may be fixed by 8c460a9a1), PR-002 (LOW, fixed: b02ohu/76ic0k are executed), PR-003 (MEDIUM, fixed: out-of-scope STOPs converted to declarations; runner/hand finalize ownership and kz4j7o close added), PR-004 (LOW, fixed: E-03 checks the runagy vars() shim for re readers; none measured), PR-005 (LOW, fixed: stale _close_process_streams docstring example noted). Re-verified at ca03f0c56: ten names defined in both hosts, four dead names have no reader, agy re used only by the two compiles, three share candidates equal across hosts, ruff F401/F821 clean, test_runagy 11 failed/14 passed baseline.

- 2026-10-02 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): authored from backlog `kz4j7o`. THE TRIAGE THE ITEM ASKS FOR WAS PERFORMED AT AUTHORING TIME, because the item's question is empirical ("each of the ten needs its own judgement rather than a mechanical move") and an unmeasured plan would have had to guess all ten answers. HEADLINE, and it contradicts the item's own stated fix direction: the item proposes "likely sharing the plain immutable values (`DEFAULT_RUNBOOK_TEXT`, `OUTPUT_MODES`, the three timeouts) and explicitly declining `_LANE_PROMPT_DISABLED`". Measured, FOUR of the ten have ZERO readers anywhere in the tree and are DEAD, including `OUTPUT_MODES`, which the item lists as a share candidate. Giving a dead constant a shared home would preserve the duplicate surface under a new name and leave a reader believing it is consulted; deletion is the correct fix and it also removes the divergence hazard completely rather than relocating it. A second correction: the item frames `DEFAULT_STALL_TIMEOUT` as "already a THREE-way case ... with both hosts holding their own `900.0` literal and ignoring it", and the hosts do NOT ignore it (each reads its own at four call sites); `LANE_PROMPT_TIMEOUT` is the undisclosed three-way case, equal to `runner_shared.GATE_PROMPT_TIMEOUT` by design and documented as such in that constant's own comment. A third: the item declines `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` by implication only; they are declined here EXPLICITLY and on a measured reason (a shipped test tunes them per host), with the probe showing reference-initialization would in fact have preserved the seam, so the decline rests on the pair being genuinely per-host policy rather than on a mechanical obstacle. Nothing is pushed.
- 2026-10-02 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Discharge backlog `kz4j7o` by triaging its ten constants individually and acting on each verdict, so that after this plan NO host-invariant constant is duplicated as a literal for lack of a decision. Three gain one shared definition, four are deleted as dead surface, and three carry an explicit in-code decline naming why a shared home would be wrong. The identical-copy hazard the item cites is removed for all ten: by unification for three, by deletion for four, and by a recorded reason plus the shipped host-vs-host guard for three.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure, then act on the measurement

- [ ] E-01 RE-RUN THE TEN-WAY TRIAGE MEASUREMENT AT EXECUTION HEAD and record it, rather than trusting this plan's authoring numbers. Perform four probes and paste each: (a) the co-defined host-invariant census that produced the item's list of ten, re-derived (module-level assignments in both hosts, intersected, filtered to equal resolved values whose RHS is not already `runner_shared.<NAME>`); (b) for each of the ten, a READER census, namely whether the host module itself contains a bare `Name` load of it (an `ast.walk` over the host's own tree is reading the HOST SOURCE and is therefore prohibited by P16 for a TEST, but this is an authoring/execution MEASUREMENT and not a shipped assertion; see the Step 0 convention bullet) plus a text search for the name across `agent_workflows/`, `tests/` and `tools/`; (c) whether each name is reachable as public surface (`oc_runipd.__all__`, and whether `tools/ipdrunner/runagy.py`'s `vars()` loop re-exports it to `tools/ipdrunner/test_runagy.py`); (d) which of the ten are ALSO defined in `runner_shared` under the same or a different name. Do NOT edit anything in this item.
  - Depends on: none
  - Expected outcome: A per-constant verdict table matching this plan's four groups, OR a stated delta. The authoring expectation, to be re-derived and not matched: ten constants, of which FOUR have zero readers in either host and zero readers anywhere else in the tree (`OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE`, `_close_process_streams`), THREE are live and host-invariant and immutable (`DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `LANE_PROMPT_TIMEOUT`), and THREE are live and deliberately per-host (`_LANE_PROMPT_DISABLED`, `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS`). IF ANY OF THE FOUR DEAD ONES IS FOUND TO HAVE A READER, E-02 MUST NOT delete it: say so plainly, treat that name as moving into the share-or-decline triage instead, and treat E-02 as partially refused rather than forcing the delete. The reverse also binds: if one of the three share candidates turns out to have a per-host reason this plan missed, E-03 must not unify it.
  - Execution state: pending

### Task group 2: delete the dead four

- [ ] E-02 DELETE the four zero-reader constants from BOTH hosts, conditional on E-01 confirming zero readers for each. Remove `OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE` and `_close_process_streams` from `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, with the stale comments that introduce them. This is EIGHT deletions (four names, two hosts). Each is dead for a traceable reason worth preserving in the commit message rather than in the files: `OUTPUT_MODES` was superseded when the display-mode flag trio moved into `runner_shared.add_output_mode_flags`, which spells the three modes as `store_const` values and a `set_defaults`, so the tuple is consulted by nothing; `_ID_RE`/`_STATUS_RE` were orphaned when `parse_plan_file` moved to `runner_shared` and reached its readers through `selectors`; `_close_process_streams` is a re-export of `runner_shutdown._close_process_streams` whose only reader was a test deleted in `19313eed`, and the shared reaper calls its own copy directly. NOTE: the docstring of `tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality` cites `_close_process_streams` as its example of a non-`isupper()` co-defined symbol; after this deletion that example is stale prose (no assertion reads it, so nothing fails). Leaving it is acceptable; if you correct it, that is an out-of-scope edit to justify with `--scope-reason`. DO NOT delete `_read_id` from either host: it is a different question, it HAS a live out-of-suite reader on agy, and pending plan `sznlsf` owns it (F-09).
  - Depends on: E-01
  - Expected outcome: `hasattr` is False for all four names on both host modules. The bare suite's FAILING NODE-ID SET is unchanged from the executor's OWN pre-change baseline captured in this run (compare the set of failing test ids, not a passed count). `python3 -m ruff check --select F401,F821 agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` reports no new finding.
  - Execution state: pending

- [ ] E-03 REMOVE `agy_runipd`'s NOW-UNUSED `re` IMPORT, which is a direct and easily-missed consequence of E-02 rather than a separate cleanup. Measured at authoring: `agy_runipd` uses the `re` module at exactly TWO sites, both of them the `_ID_RE`/`_STATUS_RE` compiles E-02 deletes, so after E-02 the import is unused and `ruff`'s `F401` will flag it. `oc_runipd` is NOT symmetric here and its import must STAY: it has a third use (a `re.search` call in its own body), so deleting its import would break the module. Verify per host rather than assuming symmetry, and if `agy_runipd` is found to have acquired another `re` use at execution HEAD, KEEP the import and say so. ALSO confirm no consumer reads `re` THROUGH the `tools/ipdrunner/runagy.py` `vars()` re-export (for example a bare `re.` in `tools/ipdrunner/test_runagy.py` with no local `import re`): measured at review, that file's `re.search` calls sit inside a generated fake-agent script that does its own `import json, pathlib, re, sys, time`, so they do not read the host's `re`.
  - Depends on: E-02
  - Expected outcome: `python3 -m ruff check --select F401 agent_workflows/agy_runipd.py` passes with no `re` finding, `import re` is absent from `agy_runipd` and PRESENT in `oc_runipd`, and both modules still import cleanly (`python3 -c "import agent_workflows.oc_runipd, agent_workflows.agy_runipd"` exits 0).
  - Execution state: pending

### Task group 3: share the live three

- [ ] E-04 DEFINE the three genuinely host-invariant constants ONCE in `agent_workflows/runner_shared.py` and point both hosts at them. `DEFAULT_RUNBOOK_TEXT` (the 667-character runbook string, byte-identical in both hosts) is NEW to the shared module. `DEFAULT_STALL_TIMEOUT` ALREADY EXISTS there with the same `900.0` value, so this is not a new definition but the removal of two shadowing literals: delete each host's own `DEFAULT_STALL_TIMEOUT: float = 900.0` and bind `DEFAULT_STALL_TIMEOUT = runner_shared.DEFAULT_STALL_TIMEOUT` so the hosts stop carrying a second copy of a value the shared module already owns. `LANE_PROMPT_TIMEOUT` is the undisclosed THREE-way case: `runner_shared.GATE_PROMPT_TIMEOUT` is `180.0` and its own comment says it exists so "the two prompts in this package cannot disagree about how long a run may wait for a human", citing `_lane_reclaim_prompt`'s 180s, so the two values are already intended to be one. Do NOT collapse `LANE_PROMPT_TIMEOUT` INTO `GATE_PROMPT_TIMEOUT` by deleting the lane name: the two prompts are different prompts and a future decision to diverge them is legitimate. Instead add a shared `LANE_PROMPT_TIMEOUT` defined as `GATE_PROMPT_TIMEOUT`'s value with a comment recording that the equality is deliberate and where it is documented, and point both hosts at it. Keep each host-level NAME and every call site untouched; the hosts' own comments that explain each constant's PURPOSE stay and are amended only to say the value is now read from `runner_shared`.
  - Depends on: none
  - Expected outcome: For each of the three names and each host, `getattr(host, NAME) is getattr(runner_shared, NAME)` is True (the `is` is the part that changed; all three are currently equal-but-distinct or shadowing). The RESOLVED values are unchanged: `DEFAULT_RUNBOOK_TEXT` is byte-identical to the pre-change string on both hosts, and both timeouts are `900.0` and `180.0`. The runbook literal appears exactly ONCE in `agent_workflows/`.
  - Execution state: pending

- [ ] E-05 RECORD THE THREE DECLINES IN THE CODE, so the next reader of this family does not re-open a settled question or "finish the job" by sharing them. Add a short comment at each of the three declined constants in BOTH hosts (six comments) naming the reason and where it is pinned: `_LANE_PROMPT_DISABLED` is MUTABLE per-process state written through `global`, so one shared home would make one host's suppression visible to the other (a behavior change, not a de-duplication), `runner_shared`'s module docstring independently PROHIBITS module-level mutable state, and that docstring plus `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests` already hold the reason; `_SIGINT_GRACE_SECONDS` and `_SIGTERM_GRACE_SECONDS` are a deliberate PER-HOST TUNING SEAM that `runner_shared.terminate_process`'s docstring describes at length and that `tests/test_oc_runipd.py` drives by assigning the host's own constants, which is why the shared function takes them as no-default parameters. STATE THE DECLINE HONESTLY RATHER THAN OVERSTATING IT for the grace pair: measured at authoring, initializing the host constants FROM a shared value would NOT have broken the tuning seam (a test rebinding the host attribute still wins, because the wrapper reads the host global at call time), so the reason to decline is that the values are per-host POLICY a host should be free to differ on, not that the mechanism forbids it. Do not write a comment claiming a test would fail when the probe shows it would not.
  - Depends on: none
  - Expected outcome: Each of the six sites carries a one-to-three-line reason. No comment claims a mechanical impossibility the authoring probe contradicts. `rg` for the three names shows them still DEFINED in both hosts and absent from `runner_shared`.
  - Execution state: pending

### Task group 4: guard the unification

- [ ] E-06 EXTEND THE SHIPPED PER-VALUE GUARD to cover the three newly-shared constants, in `tests/test_forkresid_shared_shells.py`, beside the existing `test_question_timeouts_are_180s`, which already asserts both hosts' `LANE_PROMPT_TIMEOUT` and `runner_shared.GATE_PROMPT_TIMEOUT` are `180.0` and is therefore the established home for exactly this assertion. Assert, BY VALUE and by identity against `runner_shared`, that each host's three constants resolve to the shared object; and assert the three DECLINED names are still defined per host (so a later sweep that shares them fails a test rather than silently changing suppression behavior). DO NOT add an AST walk, `inspect.getsource`, a census count, or a module-dictionary placement assertion: GUIDING_PRINCIPLES P16 forbids all four, executed sibling `b02ohu` restated the surviving code-structure pins in `tests/test_runner_shared.py`, and executed sibling `76ic0k` ships a guard refusing the construct at author time. Use plain `getattr` on imported modules. The existing host-vs-host sweep in `tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality` already covers the DIVERGENCE direction for every `isupper()` co-defined name and needs NO edit from this plan; do not duplicate it.
  - Depends on: E-04, E-05
  - Expected outcome: The new assertions pass. A deliberate mutation of ONE host's `DEFAULT_RUNBOOK_TEXT` makes them FAIL naming the constant; a deliberate `del` of one host's `_LANE_PROMPT_DISABLED` also fails. `rg -n 'ast\.(parse|walk|unparse)|inspect\.getsource' tests/test_forkresid_shared_shells.py` returns no MORE hits than before this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A MEASUREMENT PROBE IS NOT A SHIPPED TEST, and this plan depends on the distinction. GUIDING_PRINCIPLES P16 prohibits `ast.parse`/`inspect.getsource` reads of production source and module-dictionary placement pins IN TESTS, and executed sibling `76ic0k` ships an author-time guard enforcing it. This plan's E-01 uses an AST probe to COUNT and CLASSIFY constants, which is authoring/execution evidence pasted into a V-item and is not committed as an assertion; E-06 by contrast ships assertions and is therefore restricted to `getattr` on imported modules. Keeping the two separate is the single likeliest way an executor silently breaks the `structpin` Set.
- A COUNT OVER THE LIVE TREE IS RE-DERIVED, NOT MATCHED. The suite count here grows weekly and the hosts are two of the most heavily co-edited files in the repo, so every V-item captures its own pre-change baseline and compares against THAT. Measured at authoring HEAD `f19b37197`: bare `python3 -m pytest` gives `3 failed, 4624 passed, 2 skipped, 3 warnings`, with three pre-existing failures unrelated to this plan's surface (F-11). A nearby executed plan (`90z361`) recorded `4201 passed` days earlier and `fjsbvt`'s review recorded `3414 passed` before that, which is the drift rate this convention exists to absorb.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Pending plan `sznlsf`'s review demonstrated this on its own evidence, finding two of its cited offsets had expired in the commits since authoring.
- THE SHARED-CONSTANT SHAPE IS ESTABLISHED AND IS `<NAME> = runner_shared.<NAME>` IN BOTH HOSTS. Nine co-defined constants already have it (`ACTION_CHOICES`, `ACTION_IMPLEMENTED`, `EXECUTION_SUCCESS_STATES`, `FULL_AUTO_ACTOR`, `FULL_AUTO_APPROVAL_MESSAGE`, `SUCCESS_STATES`, `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES`, plus the non-`isupper()` `canonical_terminal_status`), each with a comment naming the plan that unified it. E-04 follows that shape exactly rather than inventing one, and `FULL_AUTO_ACTOR` shows the variant for a host-VARYING value (`runner_shared.OC_HOST_LABELS.full_auto_actor`), which is the shape this plan deliberately does NOT use, because all three of its subjects are host-invariant.
- `runner_shared` MUST NOT IMPORT EITHER HOST, and `tests/test_runner_shared.py` asserts the absence. Every constant E-04 adds is a plain literal with no host dependency, so the rule is not strained; it is recorded because it is what rules out the alternative design of a host descriptor field (F-07).
- `testpaths = ["tests"]` in `pyproject.toml`, so `tools/` IS NOT COLLECTED by a bare run. `tools/ipdrunner/test_runagy.py` reads private names off `agy_runipd` through `runagy.py`'s `vars()` re-export loop, so a green bare suite is NOT evidence that deleting a private host name is safe. E-01(c) checks that file explicitly for each of the four deletions, which is the check that distinguishes this plan's four dead names from `_read_id`, whose one live reader lives exactly there.

## Findings

| # | Severity | Subject | Finding | Evidence |
|---|---|---|---|---|
| F-01 | BLOCKER for the item's stated fix direction | FOUR of the ten are DEAD, including one the item lists as a share candidate | The item proposes "likely sharing the plain immutable values (`DEFAULT_RUNBOOK_TEXT`, `OUTPUT_MODES`, the three timeouts)". MEASURED: `OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE` and `_close_process_streams` have ZERO readers. Neither host contains a bare `Name` load of any of the four; no other module, test, or tool references them on a host; none appears in `oc_runipd.__all__`; and `agy_runipd` declares no `__all__`. Deleting all three `isupper()` ones in memory and then building BOTH hosts' parsers and parsing a `start` command succeeds with `output_mode` still defaulting to `clean`, which is the positive proof that `OUTPUT_MODES` is consulted by nothing. GIVING A DEAD CONSTANT A SHARED HOME IS WORSE THAN DELETING IT: it preserves two import-time bindings that nothing reads, under a name that now implies the shared module depends on it, and it leaves a reader believing the tuple is the mode vocabulary when the real vocabulary is the `store_const` values in `runner_shared.add_output_mode_flags`. Deletion also removes the divergence hazard completely rather than relocating it. | AST probe over both hosts collecting bare `Name` loads and `Attribute` accesses: all four absent from both hosts' load sets (`_close_process_streams` appears only as the `attr` of the `runner_shutdown.<attr>` RHS that defines it). Tree-wide search for `OUTPUT_MODES` returns only the two defining lines plus three `.aw/records/` prose mentions. In-memory probe deleting `OUTPUT_MODES`/`_ID_RE`/`_STATUS_RE` from both modules, then `oc_runipd.build_parser()` and `agy_runipd.build_parser()` each parsing `start --repo . v6zie5`: both OK, `output_mode default: clean` for each. |
| F-02 | HIGH | each dead constant's death has a traceable cause, which is what makes deletion safe rather than merely unreferenced-looking | A name with no readers could be a re-export someone depends on; these four are not, and each has a commit that orphaned it. `OUTPUT_MODES` entered in `15c56f02d` ("clean colored progress output instead of raw JSON dump") alongside an `argparse` `choices=OUTPUT_MODES` usage; the flag registration later moved into the shared `add_output_mode_flags`, which spells the three modes as two `store_const` arguments plus `set_defaults(output_mode="clean")` and consults no tuple, leaving the constant behind. `_ID_RE`/`_STATUS_RE` were orphaned when `parse_plan_file` moved to `runner_shared` (`sy7uwh`), which is the same mechanism that orphaned `_read_id`, and the hosts' own comment at that site says the neighbouring `_KIND_RE`/`_PLAN_FILENAME_RE` were moved for exactly the reason that "leaving a duplicate CONSTANT behind would reproduce the same defect one layer down" - advice the two regexes next to it did not receive. `_close_process_streams` is a re-export added in `2256846ef` when the reaper was consolidated; its only reader was `tests/test_stall_progress.py`, which patched `runner_shutdown._close_process_streams` (the OWNER, not the host re-export), and that file was deleted in `19313eed`. | `git log -S` for each name; `git show 15c56f02d` adding `OUTPUT_MODES` and `git log -S"choices=OUTPUT_MODES"` showing the usage existed and is gone; `runner_shared.add_output_mode_flags` body read in full; the `rununify 06 (sy7uwh)` comment block read verbatim in `oc_runipd` above `_ID_RE`; `git show 2256846ef` showing `_close_process_streams` turn from a local `def` into the re-export; `git grep _close_process_streams 19313eed7^ -- tests/` returning the one deleted reader, which patches the `runner_shutdown` owner. |
| F-03 | HIGH | deleting the two regexes makes `agy_runipd`'s `re` import unused, and the hosts are NOT symmetric | An easily-missed consequence that would fail the pre-commit `ruff` hook mid-execution. `agy_runipd` uses the `re` module at exactly TWO sites, both the `_ID_RE`/`_STATUS_RE` compiles, so after E-02 its `import re` is unused and `F401` fires. `oc_runipd` has THREE uses: the same two compiles plus one `re.search` elsewhere in its body, so its import must stay. This asymmetry is why E-03 exists as its own item and why it requires a per-host check rather than a mirrored edit. | AST probe listing every `re.<attr>` access per host with line numbers: `oc_runipd` -> `re.compile`, `re.compile`, `re.search` (3); `agy_runipd` -> `re.compile`, `re.compile` (2). `python3 -m ruff check --select F401 agent_workflows/agy_runipd.py` currently passes, so any new finding is attributable to this plan. |
| F-04 | HIGH | the three share candidates are genuinely host-invariant, and ONE is already a shadowed shared constant | `DEFAULT_RUNBOOK_TEXT` is byte-identical in both hosts (667 characters, compared by `ast.literal_eval` rather than by source text) and is passed to `runner_shared.initialize_run_core` as its `default_runbook_text` argument by each host, which is the clearest possible evidence that the shared module is the value's real consumer: the shared function already has a fallback string of its own ("This runbook guides automated execution.") for a host that passes none. `DEFAULT_STALL_TIMEOUT` is ALREADY DEFINED in `runner_shared` with the same `900.0`, and the shared module reads its OWN copy at two sites while each host reads its own at four, so three copies of one number exist and the hosts' two are pure shadows. `LANE_PROMPT_TIMEOUT` is `180.0` in both hosts and equals `runner_shared.GATE_PROMPT_TIMEOUT`, whose comment states the equality is deliberate. None of the three is mutated anywhere. | `ast.literal_eval` comparison of both hosts' `DEFAULT_RUNBOOK_TEXT` -> `identical: True len 667 667`; both hosts' `initialize_run_core` call sites passing `default_runbook_text=DEFAULT_RUNBOOK_TEXT, default_stall_timeout=DEFAULT_STALL_TIMEOUT`; `runner_shared`'s own `DEFAULT_STALL_TIMEOUT: float = 900.0` and its two reads (`build_turn_budget_notice`, the `StallTimeout` handler in `run_queue`); runtime probe: `shared 900.0 oc 900.0 agy 900.0`, `GATE_PROMPT_TIMEOUT 180.0`, `oc/agy LANE_PROMPT_TIMEOUT 180.0`, `shared has LANE_PROMPT_TIMEOUT: False`, `shared has DEFAULT_RUNBOOK_TEXT: False`. |
| F-05 | MEDIUM | the item's `DEFAULT_STALL_TIMEOUT` characterization is wrong in a way that matters for E-04 | The item says the hosts hold "their own `900.0` literal and ignoring it". They do not ignore it: each host reads its own constant at FOUR sites (the `initialize_run_core` argument, an `options.get` fallback, an `argparse` `default=`, and on agy additionally the flag's `help` text f-string). So this is not a dormant third copy that can simply be deleted; it is a live shadow whose removal must rebind the host name rather than drop it, which is exactly what E-04 specifies. Recorded because an executor acting on the item's wording would delete the host lines outright and break four call sites per host. | Per-host grep for `DEFAULT_STALL_TIMEOUT` with line numbers: `oc_runipd` at the `initialize_run_core` call, `options.get("stall_timeout", DEFAULT_STALL_TIMEOUT)`, `default=DEFAULT_STALL_TIMEOUT`; `agy_runipd` the same three plus `help=f"... (default: {DEFAULT_STALL_TIMEOUT}; ...)"`. |
| F-06 | MEDIUM | the grace pair's decline rests on POLICY, not on a mechanical obstacle, and the obvious reason for it is false | `runner_shared.terminate_process`'s docstring says the grace values are "PARAMETERS WITH NO DEFAULTS" because each host's wrapper "reads them AT CALL TIME, so a caller or test that tunes its host's `_SIGINT_GRACE_SECONDS` still takes effect", warning that reading shared constants inside the shared function "would have silently broken that tuning seam". That is TRUE of reading them inside the shared FUNCTION and FALSE of initializing the host CONSTANT from a shared value, which is what E-04's shape would do. MEASURED: setting the host attribute to a shared value and then having a test rebind `driver._SIGINT_GRACE_SECONDS = 0.3` still delivers `0.3` to the reaper, because the wrapper reads the host global at call time and the test's rebinding replaces it. So the seam would survive. The pair is therefore declined on the honest ground that reaping timing is per-host policy a host should be free to differ on, and E-05 forbids writing a comment that claims otherwise. | `runner_shared.terminate_process` docstring read in full; both hosts' wrapper bodies passing `sigint_grace=_SIGINT_GRACE_SECONDS`; `tests/test_oc_runipd.py` tuning both constants at three separate test sites and restoring them; probe assigning the host constant from a shared value, then rebinding to `0.3`/`0.3` and capturing the reaper's kwargs -> `{'sigint': 0.3, 'sigterm': 0.3}`, `tuning seam preserved: True`. |
| F-07 | MEDIUM | `_LANE_PROMPT_DISABLED` is correctly declined and the reason is already pinned in three places | The item's instinct here is right and this plan does not disturb it, but the reason deserves to be cited rather than re-derived. `runner_shared`'s module docstring names this symbol SPECIFICALLY as one of "TWO SYMBOLS THAT COULD NOT MOVE AT ALL", explaining that a shared `global` "would write THIS module's flag while each runner's `_lane_reclaim_prompt` kept reading its OWN, and prompt suppression on a repeated interrupt would silently stop working". The same docstring independently prohibits "NO module-level mutable state", recording that a registration seam was "DECLINED by the maintainer". `runner_shared.lane_reclaim_prompt` takes `disabled` and the host's `disable_lane_prompt` as keyword-only parameters with no defaults for this reason, and `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests` patches `host._LANE_PROMPT_DISABLED` per host to pin it. A HOST DESCRIPTOR FIELD is also wrong for all three declined names and for the three shared ones: `HostLabels` fields are host-VARYING data, these values are either host-invariant (share them) or mutable per-process (cannot live in a `NamedTuple` at all), and executed plan `90z361` already rejected the descriptor-field route for an invariant value on the same reasoning. | `runner_shared`'s module docstring sections "WHAT MAY NEVER HAPPEN HERE" and "TWO SYMBOLS THAT COULD NOT MOVE AT ALL" read verbatim; `lane_reclaim_prompt`'s signature and its "WHY THE TWO PROMPT CALLABLES ARE INJECTED" paragraph; `tests/test_forkresid_shared_shells.py` `_run_lane_prompt_checks` patching `host._LANE_PROMPT_DISABLED` at three points; `90z361`'s "ADDING A `HostLabels` FIELD is REJECTED" row. |
| F-08 | HIGH | the DIVERGENCE direction is already guarded, which is why this plan is low priority and needs no new sweep | The item's own mitigation note says plan `90z361` E-03 would add a host-vs-host guard over every co-defined host-invariant constant. SHIPPED AND VERIFIED: `tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality` sweeps `sorted(k for k in vars(oc_runipd) if k.isupper() and k in vars(agy_runipd))`, exempting a declared `EXPECTED_HOST_VARYING` set, and `90z361`'s own V-03 evidence lists the compared names including nine of this item's ten. So a future one-sided edit to any of them FAILS A TEST rather than shipping silently, and this plan is a cleanup of a guarded hazard rather than a fix for a live one. TWO LIMITS, stated so the guard is not trusted further than it holds: `_close_process_streams` is not `isupper()` and so is NOT swept (harmless, since both hosts bind the identical `runner_shutdown` object), and the sweep compares RESOLVED VALUES, so it cannot see that two equal values come from two separate literals, which is precisely the hazard this plan removes. | The sweep's committed body read in `tests/test_runner_shared.py`; `90z361` V-03's pasted compared-names list containing `DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `LANE_PROMPT_TIMEOUT`, `OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE`, `_LANE_PROMPT_DISABLED`, `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS`; `"_close_process_streams".isupper()` -> False. |
| F-09 | MEDIUM | one pending plan shares two Scope-Paths and owns an ADJACENT name this plan must not touch | `sznlsf` (Set `s4jctz`, Order 01, `- Status: approved`) declares `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` and resolves the `_read_id` re-exports: it DELETES oc's and RETAINS agy's, because `tools/ipdrunner/test_runagy.py` reads `driver._read_id` through `runagy.py`'s `vars()` loop. That is the same import region as this plan's `_ID_RE`/`_STATUS_RE` deletions and the same orphaning mechanism (`parse_plan_file` moving to `runner_shared`), so the two plans are easy to confuse. THEY TOUCH DISJOINT NAMES: `sznlsf` touches `_read_id` only and explicitly forbids sweeping `_read_status`/`_read_set`/`_read_order`/`_read_kind`; this plan touches neither `_read_id` nor any `_read_*` name. No dependency is declared because no edge exists in either direction, and the runner isolates each item in its own worktree and merges through revalidation. `sznlsf`'s review also establishes TWO method rules this plan adopts: self-relative suite baselines, and proving a deletion's blast radius IN MEMORY rather than by editing these two high-contention files on disk. | `sznlsf` front matter and E-01/E-02/E-03/E-04 read in full; its F-2 naming `test_runagy.AgyParserAndDiscoveryTests.test_read_deps_and_set` (which asserts `driver._read_id(text)` returns `"a1b2c3"`) and `runagy.py`'s `for _k, _v in vars(agy_runipd).items()` loop, both re-verified here; a tree-wide search confirming none of this plan's four deleted names appears in `tools/ipdrunner/test_runagy.py`. |
| F-10 | LOW | the shared module is the right home and the admission rule is not strained | `runner_shared`'s ADMISSION RULE requires a moved SYMBOL's bodies to have been proven AST-identical, which is about functions; `90z361` established the precedent for admitting a plain host-invariant CONSTANT under the same roof, adding `FULL_AUTO_APPROVAL_MESSAGE` with a comment recording why. E-04 follows that precedent for three more. The module already hosts a constants section (`# ---- rununify: constants and shared models`) and already owns `DEFAULT_STALL_TIMEOUT` and `GATE_PROMPT_TIMEOUT`, so two of the three subjects have an obvious neighbour to sit beside. Nothing E-04 adds creates a host dependency, so the "MUST NOT import either runner" rule is untouched. | `runner_shared` module docstring "THE ADMISSION RULE" section; `90z361` E-01's committed constant and its `#:` comment; the module's constants banner and the existing `DEFAULT_STALL_TIMEOUT`/`GATE_PROMPT_TIMEOUT` definitions. |
| F-11 | HIGH | BASELINE AND SURFACE, with three pre-existing failures an executor must not attribute to this change | Bare `python3 -m pytest` at authoring HEAD `f19b37197` reports `3 failed, 4624 passed, 2 skipped, 3 warnings in 115.58s`. The three failures are `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, and `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. None touches a file this plan declares (specs conformance, selector type containment, and run-finding reachability respectively). REVIEW NOTE (2026-10-07): commit `8c460a9a1` ("Fix baseline test failures on main (spec scope length, readiness invariant, reachability test, selector containment test)") targets exactly these three, so they may be GONE at execution HEAD; the baseline is therefore re-derived, never assumed to contain them. So the bar is that no test in or reachable from the four Scope-Paths regresses and the new assertions pass, NOT that the suite is green. The surface is small: the four dead names appear only at their defining lines plus `.aw/records/` prose; the runbook literal appears once per host; no `.md` outside `.aw/records/` mentions any of the ten; and no spec governs them. | The pasted suite tail above, captured on a clean tree (`git status --short` empty before and after); per-name tree-wide searches for all ten; no `.spec.md` hit for any of the ten. |

## Proposed changes (ordered, validatable)

1. Re-measure the ten-way triage at execution HEAD and record a per-constant verdict, refusing any
   action the measurement contradicts (E-01).
2. Delete the four zero-reader constants from both hosts, with their stale introducing comments
   (E-02; F-01, F-02).
3. Remove `agy_runipd`'s now-unused `re` import, keeping `oc_runipd`'s, which is still used (E-03;
   F-03).
4. Define `DEFAULT_RUNBOOK_TEXT` and `LANE_PROMPT_TIMEOUT` once in `runner_shared`, drop the hosts'
   shadowing `DEFAULT_STALL_TIMEOUT` literals, and point all three host names at the shared
   definitions as one-line references (E-04; F-04, F-05, F-10).
5. Record the three declines in the code at both hosts, with reasons that do not overstate the
   mechanism (E-05; F-06, F-07).
6. Extend the shipped per-value guard to pin the three unifications and the three declines, using
   `getattr` and no AST walk (E-06; F-08).

## Deferred / out of scope (with reason)

- THE `_read_id` RE-EXPORTS are not touched, although they sit in the same import region as
  `_ID_RE`/`_STATUS_RE` and were orphaned by the same commit. Approved plan `sznlsf` owns them and
  reaches a SPLIT verdict this plan has no evidence to revisit (oc's is dead, agy's has one live
  out-of-suite reader). Sweeping them here would collide with an approved sibling on two shared
  Scope-Paths.
  - Carrier-Evidence: .aw/records/plans/pending/20260930-s4jctz-01-sznlsf-resolve-the-two-read-id-re-exports-in-the-host-runners-again.ipd.md
- COLLAPSING `LANE_PROMPT_TIMEOUT` INTO `GATE_PROMPT_TIMEOUT` is declined rather than deferred. The
  two values are equal by deliberate design and the shared comment says so, but they describe two
  DIFFERENT prompts (a lane-reclamation offer and a gate phrase confirmation), and a future decision
  to give one a different timeout is legitimate. E-04 therefore gives the lane name its own shared
  definition rather than deleting it in favour of the gate's.
  - Carrier-Declined: Nothing is owed. This records a design choice internal to E-04, enforced by
    E-04's own expected outcome that both host names survive and resolve to a shared
    `LANE_PROMPT_TIMEOUT`. No one has asked for the two prompts to share one knob, and merging them
    would be a behavior coupling rather than a de-duplication.
- THE THREE DECLINED CONSTANTS are not given a shared home, by design and with reasons measured
  (F-06, F-07). This is the item's own "explicitly declining `_LANE_PROMPT_DISABLED`" direction,
  extended to the grace pair and made explicit in code by E-05.
  - Carrier-Declined: There is nothing to carry. The divergence risk these three retain is covered
    going forward by the shipped host-vs-host sweep (F-08), which reaches all three, and E-05's
    comments plus E-06's assertions are this plan's internal enforcement that they stay per host.
- THE SIX LARGE FORKED FUNCTIONS the fork scanner reports (`build_parser`, `execute_item`,
  `handle_audit_command`, `initialize_run`, `main`, `run_queue`) are untouched. They are DIVERGENT,
  not identical, so deciding which side is authoritative is the intellectual work `runner_shared`'s
  docstring explicitly reserves for a dedicated plan, and this item is about identical copies.
  - Carrier-Declined: Out of this item's subject entirely. Backlog `kz4j7o` names ten CONSTANTS whose
    values are equal; a divergent function body is the opposite case and is already visible in
    `tools/runner_fork_scan.py`'s standing census, which this plan must leave unmoved.
- CHANGING ANY VALUE is out of scope: the runbook text, both timeouts, and both grace values keep
  their exact current values, and no CLI default, help string, or run option changes.
  - Carrier-Declined: Nothing is owed. This plan is a de-duplication with no behavior change, which
    is an INVARIANT it enforces internally (V-04's resolved-value and argv comparisons), not deferred
    work. The shipped values are the ones the maintainer already has.

## Scope check

- Over-scope: none. Each of the four Scope-Paths entries is required by a named E-item:
  `runner_shared.py` by E-04, both host modules by E-02/E-03/E-04/E-05, and
  `tests/test_forkresid_shared_shells.py` by E-06. No descriptor file, viewer, dashboard, or
  third-host test is declared and none is needed: this plan adds no `HostLabels` field (F-07), so
  `tests/test_hostdedup_third_host.py` stays out, and it edits no AST walk, so
  `tests/test_runner_shared.py` stays out too.
- Under-scope: the `_read_id` re-exports (owned by `sznlsf`), the three declined constants (declined
  with reasons), the six divergent forked functions, and `GATE_PROMPT_TIMEOUT`'s relationship to the
  lane timeout, each recorded above with its reason.
- `tests/test_runner_shared.py` and `tests/test_hostdedup_third_host.py` are deliberately NOT
  declared. The first holds the host-vs-host sweep this plan leaves unchanged (F-08), so editing it
  would duplicate a shipped guard; the second is only reachable by adding a `HostLabels` field, which
  F-07 rejects. Neither edit is expected. This is a DECLARATION, not a stop: if execution shows an
  edit to either is genuinely required, make it and justify it at finalize with `--scope-reason`.

## Required tests / validation

- Bare `python3 -m pytest` (already `-q -n auto` per `pyproject.toml` `addopts`), pasted TWICE: a
  baseline captured BEFORE any edit in the execution run, and the post-work tail. RE-DERIVE THE
  BASELINE rather than comparing against this plan's figure. Measured at authoring:
  `3 failed, 4624 passed, 2 skipped, 3 warnings`, with three pre-existing failures named in F-11,
  none touching a declared path. The bar is that no test in or reachable from the four Scope-Paths
  regresses and the new assertions pass, NOT that the suite is green. If those three failures are
  still present, say so and attribute them rather than claiming green or blaming this change; if
  they are absent (commit `8c460a9a1` targets them), say that instead. Compare by failing node-id set.
- `python3 -m pytest tests/test_forkresid_shared_shells.py tests/test_runner_shared.py
  tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_hostdedup_third_host.py
  -o addopts=""` green, which covers the new assertions, the shipped host-vs-host sweep this plan
  must leave passing, both hosts' CLI behavior, the grace-tuning tests that pin the declined pair,
  and the descriptor contract this plan must leave untouched.
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts=""` run before and after, with the
  SAME set of failures in both arms. This file is NOT collected by a bare run (`testpaths =
  ["tests"]`) and is partly red at HEAD for unrelated reasons, and it is the one place a private host
  name is read through `runagy.py`'s `vars()` loop. It is the check that distinguishes this plan's
  four dead names from `_read_id`; running the bare suite alone would NOT catch a wrongly-deleted
  private name.
- A DELIBERATE-FAILURE DEMONSTRATION FOR E-06, which is the guard's whole point and must be shown
  rather than asserted: mutate ONE host's `DEFAULT_RUNBOOK_TEXT` in memory, show the new assertion
  goes RED naming the constant, restore, show green. Then a SECOND, DISTINCT demonstration: `del`
  one host's `_LANE_PROMPT_DISABLED` and show the decline assertion goes RED. Both arms must be
  in-memory; do NOT edit these two high-contention host files on disk to stage a failure (the method
  rule `sznlsf`'s review established, and the loss AGENTS.md's shared-checkout rule exists to
  prevent).
- A RESOLVED-VALUE AND IDENTITY PROBE for all three shared constants on both hosts, pasted: `==` and
  `is` against `runner_shared`, plus the pre-change values shown byte-identical to the post-change
  ones (the runbook string compared by length AND equality, not eyeballed).
- AN ARGV / OPTIONS PROBE proving no behavior moved: drive each host's `build_parser()` and parse a
  `start` command, pasting the resolved `stall_timeout` and `output_mode` before and after, shown
  identical. `output_mode` is the one E-02 could plausibly break, since it deletes the tuple that
  LOOKS like the mode vocabulary.
- A SEARCH SHOWING E-06 ADDED NO NEW AST WALK: `rg -n 'ast\.(parse|walk|unparse)|inspect\.getsource'
  tests/test_forkresid_shared_shells.py` pasted, with no more hits than before. This is what keeps
  the plan compatible with executed siblings `b02ohu` and `76ic0k`, and it is the single likeliest
  way an executor silently breaks the `structpin` Set.
- `python3 -m ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
  agent_workflows/runner_shared.py` before and after, with NO NEW finding by location. The before-run
  is required because the tree already reports findings in these files; compare locations, not counts.
- `python3 tools/runner_fork_scan.py` before and after. Baseline at authoring HEAD: 56 co-defined, 49
  sanctioned thin wrappers, 7 REAL FORKS (1 byte-identical: `disable_lane_prompt`; 6 divergent). The
  identical fork is `disable_lane_prompt`, which this plan DECLINES to share, so the census should not
  move; re-derive rather than matching, and account for any delta.
- `python3 -c "import agent_workflows.oc_runipd, agent_workflows.agy_runipd"` exiting 0, the cheapest
  proof that E-03 did not remove an import something still needs.
- `aw sanitize --agent` over the changed files and this plan, since V-items paste probe output that can
  carry absolute interpreter paths.
- `git diff --cached --name-only` immediately before committing, which must list exactly the four
  Scope-Paths entries plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be: no spec governs any of the
ten constants (searched; no hit in `.aw/records/specs/`). No shipped contract changes. The CLI surface
is byte-identical, including `--stall-timeout`'s default and its agy help string (both still render
`900.0`) and the `--quiet`/`--raw`/`-v` trio, whose registration never consulted the deleted
`OUTPUT_MODES` (F-01, F-02). The `aw.agent/v1` JSON contract, every run option, and the runbook written
into each run directory are unchanged. No user-facing documentation mentions any of the ten. The
in-source comments that need amending (each host's constant comments and the two
`# noqa`-adjacent blocks the deletions leave stale) are in files already in scope and are amended by
E-02, E-04 and E-05 themselves. `runner_shared`'s module docstring is NOT edited: its
`_LANE_PROMPT_DISABLED` paragraph stays correct under this plan, which declines that symbol, and its
"TWO SYMBOLS THAT COULD NOT MOVE AT ALL" claim remains true.

## Open questions

### OQ-01: Should the four zero-reader constants be deleted, or given a shared home like the other six?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: DELETED, resolved from repository evidence rather than left open,
  and this REVERSES the backlog item's stated direction for one of them (`OUTPUT_MODES`, which the
  item lists among the "plain immutable values" to share). Three reasons, all measured. FIRST, a
  shared home for a dead constant preserves the dead surface: both hosts keep an import-time binding
  nothing reads, and the shared module gains a name implying it is consulted. SECOND, deletion removes
  the divergence hazard COMPLETELY, where sharing only relocates it. THIRD, each of the four has a
  traceable orphaning commit (F-02), so this is removing residue with a known cause rather than
  deleting something merely unreferenced-looking. The risk of a hidden reader is real for private
  names on `agy_runipd` specifically, because `runagy.py` re-exports `vars()` wholesale; that is why
  E-01(c) and the `tools/ipdrunner/test_runagy.py` before-and-after run exist, and why E-01 refuses
  the delete if a reader appears. Reversible: the four lines are recoverable from git, and a restore
  is two lines per host.

### OQ-02: Should `_SIGINT_GRACE_SECONDS` / `_SIGTERM_GRACE_SECONDS` be shared, since the tuning seam provably survives?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the reason had to be CORRECTED rather than inherited. The
  obvious reason to decline (sharing would break the per-host tuning seam a shipped test drives) is
  FALSE for the shape this plan would use: the probe in F-06 shows a test rebinding
  `driver._SIGINT_GRACE_SECONDS` still wins, because each host's wrapper reads its own global at call
  time regardless of what that global was initialized from. The shared module's docstring warns
  against reading shared constants INSIDE the shared function, which is a different thing. They are
  declined on the honest ground that child-reaping timing is per-host POLICY: the two hosts launch
  different agents with different shutdown behavior, and a host should be free to differ here without
  editing a shared file. E-05 therefore forbids writing a comment claiming a mechanical
  impossibility. The alternative considered and rejected was sharing them and relying on the test to
  catch a problem: that would make the two hosts' reaping timing one knob by default, which is a
  coupling decision dressed as a cleanup. If a maintainer prefers them shared, the change is two
  lines per host and the guard in E-06 would need its decline assertions inverted.

### OQ-03: Does deleting `agy_runipd`'s `re` import risk breaking a dynamic use an AST scan cannot see?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. An AST scan over `agy_runipd` finds exactly two `re.<attr>`
  accesses, both the compiles E-02 removes (F-03), and a dynamic use would have to reach the module
  global by name (`getattr(agy_runipd, "re")` or `globals()["re"]`), which a text search for `re`
  cannot usefully confirm but which E-03's own expected outcome catches directly: the module must
  still IMPORT cleanly and the targeted suite plus `tools/ipdrunner/test_runagy.py` must behave
  identically. `ruff`'s `F821` (undefined name) is also selected in E-02's expected outcome, which
  reports a bare `re` left behind. Reversible in one line. Noted for the executor: `oc_runipd` is NOT
  symmetric and its import must stay, so this must be decided per host rather than mirrored.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: Paste the four probes' output in full: (a) the re-derived co-defined
    host-invariant census; (b) the per-constant reader census for all ten, showing for each whether
    either host contains a bare `Name` load of it and whether any other file in `agent_workflows/`,
    `tests/` or `tools/` references it; (c) the public-surface check (`'<name>' in oc_runipd.__all__`
    for each, and a search of `tools/ipdrunner/test_runagy.py` for all ten); (d) the
    also-in-`runner_shared` flag for each. Then paste a TEN-ROW VERDICT TABLE assigning each constant
    to delete / share / decline, and state in one sentence whether it matches this plan's grouping or
    differs. If it differs for ANY name, say which E-item is refused or narrowed and why, and do not
    proceed on that name.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff` for both host modules showing the eight deletions and the
    stale comments removed, with NO other executable change. Paste a probe printing
    `hasattr(host, name)` for all four names on both hosts (eight `False` results). Paste the
    pre-change baseline suite tail captured in THIS run and the post-E-02 tail, and state the delta
    by failing node-id set, attributing any failure present in BOTH arms as pre-existing (the three
    F-11 failures may already be fixed by `8c460a9a1`). Paste `python3 -m ruff check --select F401,F821
    agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` with its findings, compared BY
    LOCATION against a before-run of the same command. Paste
    `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts=""` before and after, and confirm the
    failure SET is identical in both arms (it is partly red at HEAD; the bar is no NEW failure).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the `re`-usage probe for BOTH hosts at post-E-02 state, showing
    `agy_runipd` at zero uses and `oc_runipd` still at one. Paste the diff removing only
    `agy_runipd`'s `import re`. Paste `python3 -m ruff check --select F401 agent_workflows/agy_runipd.py`
    passing, and a probe confirming `import re` is ABSENT from `agy_runipd` and PRESENT in
    `oc_runipd`. Paste `python3 -c "import agent_workflows.oc_runipd, agent_workflows.agy_runipd"`
    exiting 0. State in one sentence that the asymmetry was checked per host rather than mirrored.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` in full: it must show the
    two NEW constants with their `#:` comments and NO other executable change (`DEFAULT_STALL_TIMEOUT`
    is already there and must be untouched). Paste the diff for both hosts showing three one-line
    references each. Paste a probe printing, for each of the three names and each host, `==` and `is`
    against `runner_shared` (six `True`/`True` pairs; the `is` is what changed). Paste the RESOLVED
    values before and after, shown identical: both timeouts as numbers, and `DEFAULT_RUNBOOK_TEXT`
    compared by `len()` AND `==` against the pre-change string on each host. Paste a search showing
    the runbook literal appears exactly ONCE in `agent_workflows/`. Paste the argv/options probe:
    each host's `build_parser()` parsing a `start` command, with the resolved `stall_timeout` and
    `output_mode` shown identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste all six added comments verbatim. Confirm in one sentence per family that
    the stated reason matches the measured one: that `_LANE_PROMPT_DISABLED` is declined for mutable
    per-process state (citing `runner_shared`'s docstring prohibition and
    `LanePromptSuppressionTests`), and that the grace pair is declined as per-host POLICY and NOT on a
    claim that sharing would break the tuning seam. QUOTE the comment text for the grace pair and
    state explicitly that it makes no such claim, since F-06 measured that claim to be false. Paste a
    probe showing all three names are still defined on BOTH hosts and absent from `runner_shared`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the full committed source of the new assertions and paste them PASSING.
    Paste the FIRST deliberate failure: an in-memory mutation of ONE host's `DEFAULT_RUNBOOK_TEXT`,
    the test RED with the constant name visible, restored and green. Paste the SECOND, DISTINCT
    deliberate failure: an in-memory `del` of one host's `_LANE_PROMPT_DISABLED`, the decline
    assertion RED, restored and green. State in one sentence that neither demonstration edited a host
    file on disk. Paste `rg -n 'ast\.(parse|walk|unparse)|inspect\.getsource'
    tests/test_forkresid_shared_shells.py` with its hit count and confirm the new assertions
    contribute NONE of those hits. Confirm in one sentence that the new code reads no production
    `.py` source text and makes no census-count or module-placement assertion, by any mechanism.
    Finally paste the targeted five-file run green, the full-suite post-work tail, and
    `python3 tools/runner_fork_scan.py` compared against a baseline re-derived in this run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the four declared Scope-Paths plus this plan, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Verify the staged set with
`git diff --cached --name-only` before committing and unstage anything you did not modify with
`git restore --staged <path>`: this plan's Scope-Paths include the repository's three most heavily
co-edited runner modules, so a co-worker's restored path entering the index is the realistic failure.
Paste ACTUAL runner output for every V-item; a claimed pass with no pasted output does not satisfy this
plan. PROVE EVERY BLAST RADIUS IN MEMORY, not by editing a host file on disk to stage a failure: two
of these files are the highest-contention files in this shared checkout, and the in-memory method is
the one `sznlsf`'s review established for exactly this case.

THREE STOP-AND-REPORT DIRECTIVES AND ONE PROHIBITION, each narrow and none a scope question. STOP if E-01 finds a READER
for any of the four names E-02 deletes: that name moves into the share-or-decline triage and the
delete is refused for it, which is a measurement outcome and not a scope decision. STOP if either
host's value for any of the three shared constants differs from the other at execution time: this
plan's safety argument rests on their being equal (F-04), so a divergence found then is a live defect
to report and file, not something to normalize by picking one. Do NOT add a `HostLabels` field (F-07
rejects it for all ten names); if one appears necessary, the plan's premise is wrong for that name,
so record it as a deferred question instead of adding the field. STOP if E-06 appears to need `ast.parse`, `ast.walk`,
`ast.unparse` or `inspect.getsource`: `getattr` on imported modules is sufficient for every assertion
this plan asks for, so reaching for an AST walk means the approach is wrong rather than the
prohibition, and adding one is refused by executed sibling `76ic0k`'s guard and P16.

POST-GATE LIFECYCLE. Execute only after explicit human approval (or a recorded automated clear). On
completion, run `aw ipd lint --phase pre-transition` to conforming and verify every V-item carries pasted
evidence. The plan then moves to `.aw/records/plans/executed/` through the tooled transition: under
`aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin`/`finalize`, so leave the plan in `pending/`
with its evidence recorded; only when executing by hand, run `aw ipd begin s2ewh8` first and
`aw ipd finalize s2ewh8 --actor <agent/model> --message <summary> --apply` last. Never hand-`git mv`
the plan. Scope fence: `- Scope-Paths:` is a declaration; a necessary out-of-scope edit is made and
justified with `--scope-reason`, a declared path left unmodified is acknowledged with `--scope-ack`.
After execution, backlog `kz4j7o` may be closed `done` with `--evidence` citing the executed plan; it
carries no `- Blocks-Release:`. Do not
mark it executed on the strength of the implementation alone: the two deliberate-failure
demonstrations and the per-constant verdict table are the substance of this plan, since the code
change itself alters no behavior.
