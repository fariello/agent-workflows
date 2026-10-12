# IPD: Family-root agent conformance gate for every CLI subparser root

- Date: 2026-10-12
- Kind: child
- Concern: No test drives a CLI FAMILY ROOT (a parser node that carries an `argparse._SubParsersAction`, e.g. `aw backlog`, `aw config exclude`, `aw runs`) under `--agent`. Every existing conformance sweep draws its universe from `command_surface.discover_parser_leaves`, which by construction yields only parsers with NO subparsers, so the 23 roots measured at authoring HEAD `fc3877544` are outside every gate. A bare invocation is a common way for an agent to probe a verb, so these are machine surfaces in practice, and the population already contained three defects of one shape (`upgrade-test`, fixed by `7pnneh`; `runs` and `config exclude`, still open as `l5dq92` and `o8cz48`).
- Scope: IN: (1) re-measure the root census and per-root behavior at the executing HEAD, as a gate (E-01); (2) add `command_surface.discover_parser_roots`, the alias-excluding inversion of `discover_parser_leaves`, beside it (E-02); (3) add a typed, citation-required `FAMILY_ROOT_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py` holding ONLY roots still non-conforming at execution, each citing its live backlog item (E-03); (4) a new behavioral test module sweeping every non-exempt root as a real subprocess, plus a registry contract test that refuses stale or unresolvable entries (E-04); (5) run the full suite (E-05). OUT: fixing `aw runs` (owned by `l5dq92`) or `aw config exclude` (owned by `o8cz48`); any change to `cli.py`, `_show_family_help`, `agent_schema`, or any production emit path; any change to `tests/test_agent_surface_conformance.py` or its `UNIVERSE`; `--json` parity for roots; adding roots to `COMMAND_INVENTORY` (which declares leaves only, per `7pnneh` F-rows).
- Scope-Paths: agent_workflows/command_surface.py, tests/conformance_matrix.py, tests/test_family_root_agent_conformance.py, .aw/records/backlog/open/
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: o7wwop
- Set: o7wwop
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 0qdl9e
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Re-measured at HEAD 9ff0658da: 23 roots, BAD = config exclude, runs; cited items now graduated.

- 2026-10-12 to-review (opencode): authored from open backlog item `o7wwop`; census and per-root behavior measured in lane `o7wwop` at HEAD `fc3877544`.
- 2026-10-12 draft (opencode): created.

## Goal

Put every CLI family root under a behavioral `--agent` conformance gate, so a bare `aw <family>` that emits a usage block, a bare payload, or a human status line on the machine surface fails a test instead of shipping. Known outstanding defects are carried by cited, self-pruning exemptions rather than by leaving the gate out.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure, then add the census

- [ ] E-01 RE-MEASURE the root census and each root's bare `--agent` behavior at the executing HEAD, before writing code. Run the authoring probe (recurse `cli._build_parser()` for nodes with an `_SubParsersAction`, alias-excluded by object identity, run `python3 -m agent_workflows <root> --agent` for each, parse the last `result`/`summary`/`error` stdout record, check `validate_agent_record == []` and `exit == returncode`). Record the root count, the list of non-conforming roots, and the open/done status of `l5dq92` and `o8cz48` via `aw find backlog <id6>`. This list, NOT the authoring-time list, decides E-03's registry contents.
  - Depends on: none
  - Expected outcome: A pasted census (count plus per-root OK/BAD line) and the two items' current status. At authoring HEAD `fc3877544` it read 23 roots, BAD = `config exclude` (stdout `FAIL     Usage: aw config exclude {add|list|rm} ...`, rc 2, no record) and `runs` (stdout `{"runs": []}`, rc 0, no record); every other root OK. If a root outside `{runs, config exclude}` is BAD at execution, do not admit it to the sweep: file a backlog item for it with `aw backlog new` (Work-Kind `bug`, gated per the repository bug rule) and exempt it under E-03 citing that new id6, recording the decision in the plan.
  - Execution state: pending

- [ ] E-02 ADD `discover_parser_roots(parser, prefix="") -> Set[str]` to `agent_workflows/command_surface.py`, directly after `discover_parser_leaves`. It returns the canonical command path of every node that HAS at least one `argparse._SubParsersAction`, excluding the top-level parser itself (empty prefix), and excludes aliases with the SAME first-key-by-identity rule `discover_parser_leaves` documents (`any(subparser is prior ...)`). Docstring states it is the inversion of `discover_parser_leaves` and that the two sets are disjoint by construction.
  - Depends on: E-01
  - Expected outcome: `discover_parser_roots(cli._build_parser())` returns exactly the E-01 census (23 at authoring, containing `backlog`, `config exclude`, `ipd dependencies`, `oc profile`, `runs`; containing no alias spelling such as `conf` or `opencode`), and its intersection with `discover_parser_leaves(cli._build_parser())` is empty. No existing function changes behavior.
  - Execution state: pending

### Task group 2: registry and gate

- [ ] E-03 ADD `FAMILY_ROOT_EXEMPTION_REGISTRY: Dict[str, Exemption]` to `tests/conformance_matrix.py`, after `MUTATION_EXEMPTION_REGISTRY`, reusing the existing `Exemption` dataclass, with a module comment repeating the ceiling rule ("adding an entry to silence a red sweep is the prohibited failure mode"). Allowed `reason_kind` is `known_broken` ONLY, and `citation` must be an id6 of a LIVE backlog item, meaning one under `backlog/open/`, `backlog/graduated/` or `backlog/blocked/` (not `done/` or `parked/`). Both cited items were `graduated` at review (plans `t76qdk` and `2va0jb` carry them), so an open-only rule would reject the two legitimate entries on day one. Populate it with exactly the roots E-01 measured BAD: at authoring that is `"runs"` citing `l5dq92` and `"config exclude"` citing `o8cz48`. If E-01 shows either already conforming, OMIT its entry.
  - Depends on: E-01
  - Expected outcome: The registry exists with one entry per E-01 BAD root and no others; each entry's `reason` names the observed defect in one line (e.g. "bare payload {\"runs\": []} with no aw.agent/v1 envelope").
  - Execution state: pending

- [ ] E-04 CREATE `tests/test_family_root_agent_conformance.py` (no `slow` marker; every subprocess goes through `conformance_matrix.run_cli`, which pins env and cwd to `REPO_ROOT`). It reads no production source and asserts on no docstring or comment (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Contents:
  (a) `ROOTS = sorted(discover_parser_roots(cli._build_parser()))` computed at collection time from the live parser, never a hand list; a census test asserting `ROOTS` is non-empty, disjoint from `discover_parser_leaves(...)`, and that every `FAMILY_ROOT_EXEMPTION_REGISTRY` key is in `ROOTS`.
  (b) a unit test of `discover_parser_roots` on a SYNTHETIC `argparse` tree built in the test (one root with an alias, one nested root, one leaf), asserting the alias is excluded, the nested root is reported with its full path, and the leaf is not reported.
  (c) `test_family_root_agent_conformance`, parametrized over `ROOTS` minus the registry, running `<root> --agent` and asserting: stdout non-empty; a terminal `result`/`summary`/`error` record parses (last one wins); `validate_agent_record(rec) == []`; `rec["exit"] == returncode`; `"next" in rec`. Then the OUTCOME SHAPE, which is deliberately not uniform: if `returncode == 0` the root dispatched to a default view (measured: `ipd` -> `cmd "ipd board"`, `releases` -> `cmd "releases list"`) and the record's `outcome` must not be `cannot-run`/`error`; otherwise the record must be `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, with a non-empty `next`. No root name is special-cased in the test.
  (d) `test_family_root_exemption_registry_contract`: every entry has `reason_kind == "known_broken"`, non-empty citation and reason, and the citation resolves to a LIVE item, asserted by running `aw find backlog <id6>` through `run_cli` (returncode 0) and requiring the stdout path to contain one of `/backlog/open/`, `/backlog/graduated/`, `/backlog/blocked/`. A citation that has moved to `done/` or `parked/` fails, naming the entry to delete.
  (e) `test_exempted_family_root_still_nonconforming`, parametrized over the registry: re-runs the root and asserts it STILL fails at least one of the (c) properties, with a failure message telling the executor of the cited item to delete the entry. This makes the registry self-pruning, as the backlog item requires ("entries must cite a live item and be deleted by its executor").
  - Depends on: E-02, E-03
  - Expected outcome: The new module passes; temporarily deleting one registry entry makes (c) fail for that root with the root name and stdout in the message (demonstrated in V-04, then reverted).
  - Execution state: pending

### Task group 3: regression

- [ ] E-05 RUN the full suite bare (`python3 -m pytest`) and the narrowed new module, and `aw ipd lint` on this plan.
  - Depends on: E-04
  - Expected outcome: Full suite green apart from any failure demonstrably pre-existing at the base HEAD (shown by re-running that test at base); new module green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Conformance sweeps live in `tests/test_agent_surface_conformance.py` and draw their universe from `command_surface.discover_parser_leaves` filtered by `COMMAND_INVENTORY` (`compute_conformance_universe`). A family root is never a leaf, so it is never in `UNIVERSE`.
- Exemption registries are typed and cited: `tests/conformance_matrix.py` `Exemption(reason_kind, citation, reason)`, `EXEMPTION_REGISTRY` and `MUTATION_EXEMPTION_REGISTRY`, with the comment "THE REGISTRY IS A CEILING, NOT A CONVENIENCE ... a known_broken entry REQUIRES a filed item id". `test_mutation_exemption_registry_contract` resolves citations by running `aw find backlog <id6>`; this plan reuses that mechanism.
- Subprocess runs go through `conformance_matrix.run_cli`, which pins `PYTHONPATH` to `REPO_ROOT`, sets `stdin=DEVNULL`, and runs in `REPO_ROOT` by default.
- Alias handling: `discover_parser_leaves` docstring, "The canonical name is the FIRST key in ``sa.choices`` that maps to a given subparser object ... identity (``is``) is the test". Aliases are owned by `AliasEquivalenceTests`.
- Family roots that already conform call `cli._show_family_help` (e.g. `_show_family_help(parser, "storage", "aw storage status", term, context)`), which emits `kind: error`, `outcome: cannot-run`, `exit: 2`, `next: <hint>`.
- `COMMAND_INVENTORY` declares leaves only; plan `7pnneh` deleted the one root declaration (`upgrade-test`) for that reason. So the root universe must come from the parser, not the inventory.
- Suite is run bare (`python3 -m pytest`) per the repo-local development contract.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The root population is 23 at HEAD `fc3877544` (the backlog item measured 22; `lanes` has since been added). | Authoring probe output: `23`, then per-root lines including `OK  lanes 2 cannot-run lanes True`. |
| F-02 | Exactly two roots are non-conforming now: `config exclude` (rc 2, stdout `FAIL     Usage: aw config exclude {add|list|rm} ...`, no record) and `runs` (rc 0, stdout `{"runs": []}`, no record). `upgrade-test` now conforms (`OK  upgrade-test 2 cannot-run upgrade-test True`), confirming `7pnneh` landed. | Authoring probe lines `BAD config exclude 2 None None False ...` and `BAD runs 0 None None False {"runs": []}`. |
| F-03 | Both outstanding defects have LIVE, release-gated backlog items, so `known_broken` exemptions citing them are legitimate under the ceiling rule. RE-MEASURED AT REVIEW (HEAD `9ff0658da`): both are now `graduated`, carried by pending plans `t76qdk` (`l5dq92`, `aw runs`) and `2va0jb` (`o8cz48`, `config exclude`), both `to-review`. `2va0jb` E-04 already deletes any `0qdl9e` root entry citing `o8cz48`; `t76qdk` does not declare `tests/conformance_matrix.py`, so if it lands after this plan, E-04(e) turns red and its executor deletes the `runs` entry as an out-of-scope edit justified at finalize, which is the intended handoff. Whichever order they land in, E-01's measurement decides the registry. | `aw find backlog l5dq92` / `o8cz48` -> `.aw/records/backlog/graduated/...`; `grep -l 'From-Backlog: \(o8cz48\|l5dq92\)' .aw/records/plans/pending/`. |
| F-04 | Exit-0 default views exist and must be accepted: `aw ipd --agent` emits `cmd "ipd board"`, `outcome "clean"`, `exit 0`, `next null`; `releases` emits `cmd "releases list"`, exit 0. Hence the gate asserts `"next" in rec` (key present), not a non-null value, on exit 0. | `aw ipd --agent` last line pasted at authoring; probe line `OK  releases 0 clean releases list True`. |
| F-05 | The sweep is cheap: 23 serial subprocesses took 7.94 s wall at authoring, so no `slow` marker is needed; under `-n auto` it parallelizes. Re-measured at review on a heavily loaded host (load average 86) it took 75.44 s serial, about 3.3 s per subprocess, which is host load, not command cost (one `aw storage --agent` took 0.6 s user CPU). | Probe output `wall 7.94`; review probe `wall 75.44`, `uptime` load 86.18. |
| F-06 | Plan `gm9baj` (the behavioral `COMMAND_INVENTORY` gate the item says to check first) is `executed`, and it edited `tests/test_command_surface_declarations.py`, not the agent-surface sweep. Pending plans touching `tests/conformance_matrix.py` (`0z7ds3`, `34iwyp`, others) edit different registries/tables; this plan adds a NEW registry and a NEW test module, so it does not redesign anything they own. | `aw find plans gm9baj` -> `executed` (bare `aw find gm9baj` matches nothing); `grep -ln conformance_matrix.py .aw/records/plans/pending/*.md`. |
| F-07 | `0z7ds3` (from `91pjax`) explicitly scopes OUT family roots ("the family-root (subcommand-less group) case, already owned by `_show_family_help`") and `config exclude` (`o8cz48`), so no other plan already gates this population. | `0z7ds3` `- Scope:` OUT clause. |

## Proposed changes (ordered, validatable)

1. E-01 measurement gate (decides registry contents).
2. E-02 `discover_parser_roots` in `agent_workflows/command_surface.py`.
3. E-03 `FAMILY_ROOT_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py`.
4. E-04 `tests/test_family_root_agent_conformance.py`.
5. E-05 full-suite regression.

## Deferred / out of scope (with reason)

- Fixing `aw runs` / `aw runs list` envelope: owned by `l5dq92` (different fix site).
- Fixing `aw config exclude` bare refusal: owned by `o8cz48`.
- `--json` mode parity for roots: not requested by `o7wwop`; the item names the `--agent` properties only.
- Changing `tests/test_agent_surface_conformance.py` `UNIVERSE`: leaves and roots are disjoint populations with different expectations; a separate module avoids conflicting with pending plans that edit that file.

## Scope check

- Over-scope: none. Only a read-only parser walker, a test-side registry, and a test module are added.
- Under-scope: none. Every property the backlog item lists (non-empty stdout, terminal record parses, `validate_agent_record == []`, exit parity, `cannot-run` plus `next` where there is no default view, exit-0 default views accepted) is asserted by E-04(c); the census helper "beside" `discover_parser_leaves` is E-02; the exemption pattern with live citations and executor deletion is E-03 plus E-04(d)(e); the `gm9baj` check is F-06.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_family_root_agent_conformance.py` green (V-04).
- A negative demonstration: removing one registry entry turns (c) red for that root (V-04), then reverted.
- Full suite `python3 -m pytest` (V-05).
- `aw ipd lint` conforming on this plan.

## Spec / documentation sync

N/A: no spec governs the conformance test harness's universe, and `docs/cli-output-contract.md` already states the behavior the gate asserts (agent-mode `cannot-run` error record with `next`); this plan adds coverage, not a contract change. No CHANGELOG line, since no user-visible behavior changes.

## Open questions

### OQ-01: Should an exempted root that starts conforming fail the suite?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: YES (E-04(e)). The backlog item requires entries to "cite a live item and be deleted by its executor"; a strict still-broken check is the only way that obligation is enforced rather than hoped for, mirroring the ceiling rule in `tests/conformance_matrix.py`. Cost: the `l5dq92`/`o8cz48` executor sees one red test naming the entry to delete, which is the intended handoff. Reversible by deleting the test.

### OQ-02: Where does the root census live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: In `agent_workflows/command_surface.py` beside `discover_parser_leaves`, as the backlog item states ("belongs beside it"), so the alias rule is shared in one module rather than re-implemented in a test.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the actual probe output at the executing HEAD (`git rev-parse --short HEAD` plus root count plus every per-root OK/BAD line) and the `aw find backlog l5dq92` and `aw find backlog o8cz48` output lines. Code path: `cli._dispatch` per root, reached via `python3 -m agent_workflows <root> --agent`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/command_surface.py` showing only the added function, and the output of `python3 -c` printing `len(discover_parser_roots(cli._build_parser()))`, the sorted list, and `discover_parser_roots(p) & discover_parser_leaves(p)` (must print `set()`). The count and list must equal V-01's census.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `git diff tests/conformance_matrix.py` showing the new registry, and show its keys equal V-01's BAD set exactly (paste both).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the actual runner output of `python3 -m pytest -o addopts="" -q tests/test_family_root_agent_conformance.py` showing the `N passed` line, where N covers the census test, the synthetic unit test, one sweep case per non-exempt root, the registry contract test, and one still-broken case per exempt entry. Then paste the output of the same run with one registry entry (e.g. `runs`) temporarily removed, showing the sweep case for that root FAILED with its stdout in the message, and `git diff --stat` after restoring it showing the entry is back.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the tail of the actual bare `python3 -m pytest` output including the summary line, and the `aw ipd lint` result for this plan. Any failure must be shown pre-existing by re-running it at the base HEAD.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution.

On execution, follow the repository's agent execution contract: commit only the paths in `- Scope-Paths:` (plus this plan file) through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and after any failed commit attempt. Paste ACTUAL runner output.

Do not change backlog item `o7wwop`'s status: the runner sets it `graduated`. After every `E-*` is `performed` and every `V-*` is `pass`, run `aw ipd lint --phase pre-transition` until conforming. The terminal transition goes through the tooled lifecycle: under `aw oc run`/`aw agy run` the runner owns `aw ipd finalize`; when executing by hand, the executor runs `aw ipd finalize` itself.
