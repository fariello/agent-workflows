# Review findings: ipd e36q6r

- Subject-Id: e36q6r
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261124T195133Z-1320375`). The target plan `.aw/records/plans/pending/20261122-selectors-03-e36q6r-wire-normalized-artifact-selectors-into-runner-clis-shell-co.ipd.md` was committed and clean (last touched by `f5a2c87e6`), so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author` reported the plan conforming (size `[medium]`). The review read spec `ogd2nv`, the sibling plans `bzsoai` and `mnlaoa` (both `reviewed`, `go-pending-approval`), and the code paths the plan names, and measured parser behavior with narrow `argparse` and `complete_query` checks. No test suite was run.

### Step T

1. Yes; the plan adds public selector flags to `aw oc run`/`review` and `aw agy run`/`review`, removes `-p` from `aw agy exec`, and changes completion and docs.
2. Partly; it changes which artifacts a run queues (the queue build in `runner_shared.py`), but no commit, worktree, merge, or sandbox code.
3. Yes; after review it has 5 E-items across 7 production modules, 7 test files, and 3 docs.
4. Yes; `- Scope-Paths:` now lists every touched file (the original omitted `runner_shared.py`, `selectors.py`, the spec, 6 test files, `tools/README.md`, and `CHANGELOG.md`).
5. Yes; a filter that silently fails to apply, or applies after the queue freezes, would execute artifacts the operator meant to exclude.

AW-TIER: standard

### Step R1

- Checked: how `aw oc run`/`review` and `aw agy run`/`review` reach the drivers (`cli.py` around lines 21359-21372, `expand_host_review_argv` line 21045), where the queue is built (`runner_shared._initialize_run_core_once` line 40571, `expand_selectors` line 18194), the driver `start`/`resume` parsers (oc lines 5022/5203, agy lines 4184/4358), and `agy_run.py`'s parser.
- Found that registering flags on the drivers alone would parse and then ignore them, because the queue is built in `runner_shared.py`, which the plan never named (`PR-001`); that `add_selector_args` with types fails on both drivers with `argument -t/--type/--tree: conflicting option string: --type`, because the runner already owns a run-type `--type` with a different vocabulary (spec `25kzda` Section 2.1) (`PR-002`); that `agy_run.py` is the `aw agy exec` one-shot prompt runner with no queue, so E-01 wiring selectors into it was wrong (`PR-003`); and that the driver parsers use `allow_abbrev=True`, so the new long flags make `--st`, `--sta`, `--se`, `--da`, `--c`, `--mo`, and `--mod` ambiguous (`PR-004`).

### Step R2

- Checked: E/V bijection, dependency order, `- Item-Dependencies: executed:mnlaoa`, each V-item's test home, the validation commands, and the gate.
- Found that E-01 bundled three modules and E-04 bundled tests with validation, that no item named a file:line, test class, or test command (`PR-008`); that the validation omitted `-o addopts=""`, the bare core gate, `aw sanitize --agent`, `aw specs check`, and several test files the changes touch (`PR-009`); and that the gate lacked the full execution contract and the `aw ipd finalize e36q6r` sentence (`PR-009`).

### Step R3

- Checked: the `resume` path (`refuse_frozen_flags_on_resume`, `runner_shared.py` line 21218, called at oc line 5975 and agy line 4746) and the empty-result rules (`EmptyStatusSelection` line 309, `DriverError` exits 2).
- Found that the plan never said where the filter sits relative to the draft gate and dependency closure, what an emptied queue reports, or what happens on `resume` (`PR-005`). Measured: `resume RUN -p high` already exits 2 with `unrecognized arguments`, which is the right refusal for a frozen queue.

### Step R4

- Checked: completion for the runner leaves, `_is_status_position` (line 1084), the latency test (`tests/test_completion.py` around line 1369), and `command_surface.py` `legacy_flags`.
- Found that `complete_query` returns `[]` for `aw oc run --`, `aw agy run --`, `aw oc review --`, and `aw agy exec --` because these are REMAINDER forwarders, and that building the driver parser at completion time costs about 210 to 320 milliseconds (plus about 1.3 seconds to import `runner_shared` cold) against a 250 millisecond test bound (`PR-006`); that `_is_status_position` does not know the R-02 canonical `--not-status` (`PR-006`); and that the `legacy_flags` tuples for `specs set`, `group`, `rename`, and `set` will name flags `mnlaoa` renames, which two parity tests assert against the parser (`PR-007`).

### Step R7

- Checked: `mnlaoa` (Order 02) owns every non-runner surface, `dest_prefix`, `selector_records`, and the `find -p` change in `tests/test_record_builder_slow.py`, and tells this plan to advertise `--new-date` and `--history-date`; `bzsoai` (Order 01) leaves the `ValueError`-to-exit-2 mapping to callers; `lmlji2` (Set `cliverbs`) depends on this plan.
- Found that this plan's Scope line claimed `tests/test_record_builder_slow.py`, which `mnlaoa` now owns (`PR-010`), and that the completions and docs had to name the post-`mnlaoa` spellings (`PR-010`).

### Step S5

- Checked: `## Open questions` read "None". The runner `--type` collision is a public-interface question, but repository evidence settles it: the runner `--type` is shipped behavior of the approved spec `25kzda` Section 2.1, used by `tests/test_spec_review_dispatch.py` and `tests/test_typed_queue_entries.py`, and `mnlaoa` D-4 already set the `include_types=False` precedent for a command owning its own type flag. It is recorded as decision `D-1` with a spec amendment in E-05, and a non-gating question in the outcome file lets the maintainer overrule it.
- Every other finding was settled from repository evidence.

### Pass 2

- Re-checked the complete revised plan: front matter (Concern, Scope, Scope-Paths, Short-Description, watermark `05`), the common rules, `E-01..E-05`, Step 0, Findings, Proposed changes and its Mermaid flowchart, Deferred, Scope check, Required tests, Spec sync, Open questions, `V-01..V-05`, and the gate.
- Verified `5/5` E/V bijection, unchanged checkbox and execution states, no `E-NEW` leaves, no em or en dashes, `aw ipd sync` reporting nothing to sync, and `aw ipd lint --phase review-finalize` reporting only the advisory `IPD-Z603` path-count note.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / Missing queue seam | agent_workflows/runner_shared.py:40571, ~40647, ~40667 (`_initialize_run_core_once`, `resolve_run_types`, `expand_selectors_fn`); oc_runipd.py:1948, agy_runipd.py:2219 | The queue is built in `runner_shared.py`, absent from the plan, so driver-only wiring would parse the flags and never filter. | C:Med; U:Low; S:Med; Overall:Med | fixed | New E-01 places `filter_records` right after `expand_selectors_fn` and before the draft gate, freezes `options.selector_filter`, and adds `runner_shared.py` to Scope-Paths. |
| PR-002 | HIGH | IN-SCOPE | R1 / `--type` collision | measured `argument -t/--type/--tree: conflicting option string: --type` on both drivers; runner_shared.py:~19266 (`--type`, `RUN_TYPE_CHOICES`); spec `25kzda` Section 2.1; spec `ogd2nv` R-06, AC-03 | The runner already owns a repeatable run-type `--type` with a different vocabulary, so the full builder cannot be registered. | C:Low; U:Med; S:Low; Overall:Low | fixed | E-02 uses `add_selector_args(start, include_types=False)` and keeps the runner `--type` (D-1); E-05 amends `ogd2nv` R-06/AC-03; spec added to Scope-Paths. |
| PR-003 | HIGH | IN-SCOPE | R1 / `agy_run.py` misread | agent_workflows/agy_run.py:197-200 (`--prompt`/`-p`, dest `prompt_target`), 656 (external `agy -p`); cli.py `aw agy exec` forwarder; `4579ba873` (added 2026-08-28, after `v1.3.0-rc.1`) | `agy_run.py` is the `aw agy exec` one-shot runner, not a queue runner; it needs only the `-p` release, and 17 test uses plus `tools/README.md` use `-p`. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-03 drops `-p`, keeps the external `agy -p`, migrates `tests/test_agy_run.py`, `tests/test_agy_tools_graduation.py:135,154`, and `tools/README.md:35,42`; no alias (unreleased). |
| PR-004 | MEDIUM | IN-SCOPE | R1 / Abbreviation ambiguity | measured `ambiguous option: --sta could match --stall-timeout, --status`; driver `build_parser` `allow_abbrev=True` | New long flags make seven existing prefixes ambiguous on the drivers. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-02 records the accepted behavior change (no test, doc, or workflow uses those prefixes) and declines `allow_abbrev=False` as out of scope (Deferred, Carrier-Declined). |
| PR-005 | MEDIUM | IN-SCOPE | R3 / Filter semantics | runner_shared.py:309 (`EmptyStatusSelection`), 19723 (`RunFlagRefusal`), 21218 (`refuse_frozen_flags_on_resume`); measured `resume RUN -p high` exit 2 | No placement relative to the draft gate and dependency closure, no empty-result rule, and no resume rule. | C:Low; U:Low; S:Med; Overall:Low | fixed | E-01 fixes placement, empty-result exit 0 for `reviews` and exit 2 otherwise with a filter summary, `ValueError` to exit 2; E-02 keeps selector flags off `resume`. |
| PR-006 | MEDIUM | IN-SCOPE | R4 / Runner completion | measured `complete_query(["aw","oc","run","--"])` returns `[]`; oc import plus `build_parser` 210-320 ms; tests/test_completion.py:~1369 (250 ms bound); completion.py:1084 (`_is_status_position`) | Runner flags cannot be introspected, building the driver parser breaks the latency bound, and `--not-status` is not a status position. | C:Low; U:Med; S:Low; Overall:Low | fixed | E-04 adds a static runner flag list from a `selectors` spellings constant, wires it into the generators, adds `--not-status`, and keeps the latency test unchanged. |
| PR-007 | MEDIUM | IN-SCOPE | R4 / Stale `legacy_flags` | agent_workflows/command_surface.py:597, 616, ~740, ~1847; tests/test_specs_evidence_gate_parity.py:724-743; tests/test_group_verb_policy.py:1036-1043 | After `mnlaoa`, the `specs set`, `group`, `rename`, and `set` declarations name renamed or missing option strings, and two tests assert them against the parser. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-04 updates the four tuples to `--history-date` and `--new-date` and runs both parity tests. |
| PR-008 | MEDIUM | IN-SCOPE | R2 / Step granularity | original E-01 (three modules), E-04 (tests plus validation); no file:line or test names | Items were too coarse for a modest executor and named no tests. | C:Low; U:Low; S:Low; Overall:Low | fixed | Rewritten as five items with common rules, file:line anchors, named `@pytest.mark.core` test classes, and one V-item each. |
| PR-009 | LOW | IN-SCOPE | S7 / Validation and gate | original validation (no `-o addopts=""`, no bare gate, bare `aw sanitize`); one-sentence gate | Validation missed touched test files and the core gate; the gate lacked the execution contract. | C:Low; U:Low; S:Low; Overall:Low | fixed | Required tests list every touched test file, the bare `python3 -m pytest`, mypy on seven modules, `aw specs check`, `aw attention --check`, and `aw sanitize --agent`; gate copied from the Set's contract with `aw ipd finalize e36q6r`. |
| PR-010 | LOW | IN-SCOPE | R7 / Sibling alignment | `mnlaoa` E-04 (owns `tests/test_record_builder_slow.py`), E-08 (`--new-date`), E-09 (`--history-date`), Spec sync | Scope claimed a file `mnlaoa` owns, and the completions and docs did not name the post-`mnlaoa` spellings. | C:Low; U:Low; S:Low; Overall:Low | fixed | Dropped the file; E-04 and E-05 name `--paths`, `--short`, `--details`/`--desc`, `--new-date`, and `--history-date`. |
| PR-011 | LOW | IN-SCOPE | Docs home | docs/cli-output-contract.md Sections 1-15 (last at line 564); tests/test_docs_test_citations.py; CHANGELOG.md:7 | The docs item named no section, and the release notes had no entry for renamed public flags. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-05 adds Section 16 with the flag table, grammar, exceptions, renames, and exemptions, plus one `CHANGELOG.md` bullet. |
| PR-012 | LOW | IN-SCOPE | Plan size | `aw ipd lint` advisory `IPD-Z603` (17 work Scope-Paths) | The hardened plan exceeds the path-count guidance. | C:Low; U:Low; S:Low; Overall:Low | deferred | Advisory only; each production change carries its own test file, and each E-item names its files. Scope check records it. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern`, `Scope`, `Scope-Paths`, `Short-Description` | Selectors wired into three driver modules, 9 paths | Queue seam, `include_types=False`, `agy exec --prompt`, spec amendment, exclusions; 18 paths | PR-001, PR-002, PR-003, PR-010 |
| Task group 1 | One E-01 for three modules | Common rules; E-01 queue seam; E-02 driver registration; E-03 `agy exec --prompt` | PR-001 to PR-005, PR-008 |
| Task group 2 | E-02 completion, E-03 docs, E-04 tests and validation | E-04 completion and `legacy_flags`; E-05 spec, docs, changelog, parity tests, validation | PR-006, PR-007, PR-011 |
| Step 0, Findings, Proposed changes | Three conventions, one finding, four lines | Measured forwarding, queue, vocabulary, and sibling facts; five findings; five steps and a Mermaid dependency flowchart | PR-001, PR-002, technical writing standard requirement 12 |
| Deferred, Scope check | One carrier; "none" | Runner `-t/-T` and `allow_abbrev` declined with reasons; size advisory | PR-002, PR-004, PR-012 |
| Required tests, V-01..V-05 | Five test files, bare `aw sanitize` | Every touched test file, bare core gate, `aw specs check`, `aw sanitize --agent`, named test classes per V-item | PR-009 |
| Open questions, gate | "None"; one sentence | D-1 rationale; full execution contract | PR-002, PR-009 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How do the runners take a type selector? | Keep the runner's run-type `--type`; register selectors with `include_types=False`; amend `ogd2nv` R-06/AC-03 | Rename the runner `--type` (rejected: breaks approved spec `25kzda` 2.1 and shipped tests); add only `-T`/`--not-type` (rejected: no requester, a second type vocabulary) | PR-002; `mnlaoa` D-4 partition precedent | yes |
| D-2 | Where is the filter applied? | In `runner_shared._initialize_run_core_once`, after `expand_selectors_fn` and before the draft gate and dependency closure | In each driver (rejected: two copies); after the closure (rejected: would drop requested prerequisites) | PR-001, PR-005 | yes |
| D-3 | How are runner flags completed? | Static list from a `selectors` spellings constant | Build the driver parser at completion time (rejected: breaks the 250 ms bound) | PR-006 measurements | yes |
| D-4 | Does `aw agy exec` keep a `-p` alias? | No | Hidden alias (rejected: unreleased flag, and it would keep the collision) | PR-003; `4579ba873` postdates `v1.3.0-rc.1` | yes |
| D-5 | Are the new prefix ambiguities on the drivers acceptable? | Yes, documented | `allow_abbrev=False` on the drivers (rejected: out of scope) | PR-004 | yes |
