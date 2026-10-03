# Review findings: plan ug85or

- Subject-Id: ug85or
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `02de25cfc` in an isolated review lane. The plan was committed and byte-identical to the
sealed lane input (sha256 `440a3563...`), so no pre-review snapshot was needed. `aw ipd lint --phase author
--agent` was clean before semantic review, and `--phase review-finalize` was clean after revision.

Re-verified (probes only, no production edit):
- `command_surface.get_all_declarations()`: 163 declarations, 0 containing `130` or `143`; 162 declared leaves;
  `oc runipd`, `agy runipd` and `pwatch` each `(0, 1, 2)`.
- `cli.main` (`agent_workflows/cli.py:15796`) has `except KeyboardInterrupt: ... return 130` and `except EOFError:
  ... return 130`; with `cli._dispatch` patched, `cli.main(["status"])` and `cli.main(["check"])` returned 130 on
  both exception types.
- Real signal, `start_new_session=True` + `os.killpg` after 2s against `python3 -m agent_workflows doctor`:
  SIGINT -> 130, SIGTERM -> -15 (WIFSIGNALED).
- `oc_runipd.main` `return 143 if is_sigterm else 130`; `render_stream.install_exit_signal_handler` default raises
  `KeyboardInterrupt("Terminated by SIGTERM")`; `pwatch.stop_cleanly` raises `SystemExit(0)` and
  `except (KeyboardInterrupt, SystemExit): return 0`.
- `pyproject.toml` `[project.scripts]` binds all three names to `agent_workflows.cli:main`.
- No spec mentions `exit_contract`; `docs/cli-output-contract.md` Section 3 names it without defining it.
- `DECISIONS.md` tail is `D158`; carriers `x31lcm`, `h0tiaw` resolve; `u28vqb` is `approved` and its OQ-03 carries
  `- Carrier: 6wd42q`.
- Additional sites found: `upgrade-test`'s `except KeyboardInterrupt: return 130` inside `cli._dispatch`
  (`cli.py:15401`), and `run_evidence._CLASSIFICATION_EXITS` mapping `AGGREGATE_INTERRUPTED` to `130`
  (unreachable via `runner_shared.run_exit_code`, which passes no `interrupted=`).
- Non-vacuity mechanism: `mock.patch.object(command_surface, "get_all_declarations", ...)` with one declaration
  widened by `dataclasses.replace` made the exclusion comprehension report `['status']`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A. Correctness of the contract definition | `agent_workflows/cli.py:15401` (`upgrade-test` `except KeyboardInterrupt: return 130`); `agent_workflows/run_evidence.py:2416` (`AGGREGATE_INTERRUPTED: 130`) | E-02 frames the excluded class as "signal-derived" and argues from `cli.main`'s arm, but `130` is also returned from inside a verb and is a named run-aggregate classification. Without defining the class by CAUSE, an editor could read those as "own return path" codes and widen a tuple, contradicting E-04's tree-wide exclusion, or read E-04 as contradicting spec `25kzda` 5.6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now defines the excluded class by cause (interrupt), names both in-verb sites as still excluded, and states why that does not contradict the spec row; V-02 demands it. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (non-vacuity evidence) | V-04 "temporarily mutate one declaration in a scratch copy or via monkeypatch ... then confirm the mutation was reverted" | V-04 permitted editing the production tuple to prove non-vacuity, which is the exact silent-failure mode the gate names and is unnecessary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now requires `mock.patch.object(command_surface, "get_all_declarations", ...)` with no file edit (demonstrated at review); E-04 requires the test to reach the inventory through the module attribute so that patch works. |
| PR-003 | LOW | IN-SCOPE | E. Testing (evidence honesty) | E-04 "driven for at least two different declared leaves, by patching `cli._dispatch`" | With `_dispatch` patched the argv is ignored, so two leaves prove nothing about verb independence; demanding it overstates the assurance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now says multiple argvs are permitted but not evidence, and points the docstring at E-01's real-signal probe as the per-verb evidence. |
| PR-004 | MEDIUM | IN-SCOPE | G. Execution contract (scope fence wording) | Gate SCOPE FENCE "must STOP and report rather than widen the fence" | Contradicts the 2026-09-01 maintainer ruling that a fence is a declaration and must not instruct a stop over a scope question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten: out-of-scope edits are made and justified via `aw ipd finalize --scope-reason`/`--scope-ack`; a needed spec amendment is recorded and filed as backlog rather than edited, because of the `u28vqb` E-07 collision. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract (lifecycle) | Gate POST-GATE LIFECYCLE "the executor moves this file to `.aw/records/plans/executed/`" | Read as a hand-rolled move; ownership was not conditional on runner versus hand execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now: runner owns finalize under `aw oc run`/`aw agy run`; by hand the executor uses `aw ipd finalize` per `ipd-lifecycle`; never `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is OQ-01's resolution from evidence (returned codes only, interrupt codes excluded) sound enough to stand without a human? | Keep it resolved | Escalate as a blocking question to the maintainer | All four load-bearing measurements reproduced at `02de25cfc` (see above); change is confined to a comment, two doc sentences, one test and one decision entry; no tuple or runtime code changes | yes |
| D-2 | Should the in-verb `130` sites be added to the plan's scope (e.g. widen `upgrade-test`)? | No; exclude them by the cause-based definition | Widen `upgrade-test`'s tuples to include 130 | Widening contradicts the adopted reading and the universal floor argument; `AGGREGATE_INTERRUPTED` is unreachable via `runner_shared.run_exit_code` | yes |
