# Review findings: ipd p06t7i

- Subject-Id: p06t7i
- Subject-Type: ipd
- Reviewed-At: 2026-11-27
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261127T062613Z-2263911`). The target plan `.aw/records/plans/pending/20261122-cliverbs-02-p06t7i-unify-read-only-views-under-aw-show-and-remove-aw-reviews-fo.ipd.md` was committed and clean (`f5a2c87e6`), so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The review examined `agent_workflows/cli.py`, `agent_workflows/reviews.py`, `agent_workflows/check_engine.py`, `agent_workflows/command_surface.py`, `agent_workflows/completion.py`, `docs/cli-output-contract.md`, `docs/artifact-lifecycles.md`, `.aw/records/reviews/README.md`, `.aw/system/workflows/plan-review/steps/s5-questions.md`, `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`, `.aw/system/cutover/metastore-docs.cutover.patch`, `tests/test_review_decisions.py`, `tests/test_cli_show.py`, `tests/test_read_verb_zero_match_refusal.py`, `tests/test_reviews_record_walkthrough_new.py`, `tests/test_command_surface_declarations.py`, `tests/test_usage_refusal_agent_record.py`, `tests/conformance_matrix.py`, spec `ogd2nv`, backlog `i8dc07`, approved spec `4sd62s`, executed metastore plan `724acb`, prerequisite plans `9ifwdx`, `mnlaoa`, and `e36q6r`, and Set `cliverbs` siblings `lmlji2` and `xocj8i`. It found one `BLOCKER` (`PR-001`), four `HIGH` (`PR-002..PR-005`), two `MEDIUM` (`PR-006`, `PR-007`), and one `LOW` (`PR-008`) findings. Six findings (`PR-003..PR-008`) were fixed in place. Two findings (`PR-001` and `PR-002`) require human maintainer decisions, remain `OPEN`, are escalated into `p06t7i` as `- Blocking: yes` open questions (`OQ-01` and `OQ-02`), and are emitted in the lane outcome JSON with `gates_verdict: true`. No production code or test code was modified.

### Step T

1. Yes; the plan alters the public `aw show` CLI surface (adding seven reserved views/subcommands and view flags), moves `aw reviews decisions` to `aw show decisions`, and proposes removing top-level `aw reviews` for 2.0.0.
2. No; it does not touch private-data redaction, git commits, worktree isolation, merges to main, or the host sandbox.
3. Yes; it spans seven read-only view surfaces, command-surface declarations, conformance matrices, multiple test suites, docs, workflow files, and interacts with Set `cliverbs` (`lmlji2`, `xocj8i`), Set `selectors` (`mnlaoa`, `e36q6r`), `9ifwdx`, and Set `metastore` (`4sd62s`, `724acb`, `cxxmyv`).
4. Yes; `- Scope-Paths:` originally listed 8 entries and omitted 10 affected files (now expanded to 18 entries covering all required production, declaration, test, and doc paths).
5. Yes; removing `aw reviews` outright deletes the shipped `aw reviews record` command (`724acb` / approved spec `4sd62s`) and breaks the pending metastore cutover (`cxxmyv`), and registering `_runs_viewer_flags` alongside `selectors.add_selector_args` on one parser crashes `argparse` at startup.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/cli.py` (`_ViewerOrLeafSubParsersAction` lines 1098-1158, `_RunsArgumentParser` lines 1178-1188, `_COMMAND_HELP` lines 440-489, `p_ipd_board` lines 2450-2472, `_runs_viewer_flags` lines 3365-3450, `p_runs` lines 3580-3614, `p_reviews` / `p_reviews_decisions` / `p_reviews_record` lines 4545-4667, `p_show` lines 5227-5266, `p_graduation` lines 5274-5300, `p_record_history` lines 5502-5517, `_run_plans` lines 12961-13055, `_run_show` / `_run_show_meta` lines 14387-14564, `_run_record_history` lines 14830-14935, `_run_graduation` lines 14937-15025, `_dispatch` lines 21656-21662, 22096-22130, 22406-22408, 22544-22556), `agent_workflows/reviews.py` (`run_decisions` lines 262-418, `run_record` lines 421-798), `agent_workflows/check_engine.py` (lines 557, 10983), `agent_workflows/command_surface.py` (lines 221-231, 682-699, 1690-1698, 2803-2846), `docs/cli-output-contract.md` (line 437), `docs/artifact-lifecycles.md` (line 535), `.aw/records/reviews/README.md` (lines 98-100), `.aw/system/workflows/plan-review/steps/s5-questions.md` (line 47), `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md` (line 54), `.aw/system/cutover/metastore-docs.cutover.patch` (25+ `aw reviews record` citations), `tests/test_review_decisions.py`, `tests/test_cli_show.py`, `tests/test_read_verb_zero_match_refusal.py`, `tests/test_reviews_record_walkthrough_new.py`, `tests/test_command_surface_declarations.py`, `tests/test_usage_refusal_agent_record.py`, `tests/conformance_matrix.py`, git commit chronology (`f5a2c87e6` vs `feb476c6e`), and specs `ogd2nv` and `4sd62s`.
- Found:
  - `p06t7i`'s central factual premise ("`aw reviews` holds only one subcommand (`decisions`), 13 occurrences across 6 files") became false three hours after `p06t7i` was committed when `724acb` landed `aw reviews record` under approved spec `4sd62s` (`PR-001`).
  - Two distinct shipped history views exist (`_run_show_meta(..., want_history=True)` durable history vs `_run_record_history` gitignored local sidecar), and neither `p06t7i` nor `ogd2nv` specifies which `aw show history <id6>` delegates to (`PR-002`).
  - Single-positional `p_show` cannot parse multi-token views or isolate `_runs_viewer_flags` from `selectors.add_selector_args` (`PR-003`).
  - `p06t7i` attributed `aw show` normalized selectors to `e36q6r` instead of `mnlaoa` E-03 (transitive via `e36q6r`) and missed 10 affected files (`PR-005`, `PR-006`).

### Step R2

- Checked: E/V bijection (upgraded from 4/4 to 5/5 with `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Item-Dependencies: executed:e36q6r, executed:9ifwdx`, post-cutover qualified spec citations (`ogd2nv R-09`, `ogd2nv R-10`, `ogd2nv R-11`, `ogd2nv AC-05`), re-derivation of mutable grep counts (replaced hardcoded "all 13 references" bar), runtime-demonstration reachability (`V-01..V-05` name the exact symbols and test suites), durable carriers in `## Deferred / out of scope`, and full execution contract in `## Approval and execution gate`.
- Found: missing qualified post-cutover spec citations (`ogd2nv R-*`/`AC-*`), hardcoded mutable count ("13 references across 6 files") used as a bar, missing core-tier validation commands and execution-contract clauses (`PR-006`, `PR-007`), and missing Scope-Paths that break Order 02's merge gate (`PR-005`). All fixed in place.

### Step R3

- Checked (full form, `complex` tier):
  - Read-only safety: `aw show stale-reviews` must keep `review_basis.stale_bases(repo_root, prune=False)` so inspecting stale reviews never deletes `.aw/state/review-basis/*.json` files (`E-02`).
  - Mutation isolation: preventing accidental deletion of `aw reviews record` (`PR-001`) preserves the metadata-log audit writer and avoids breaking post-cutover review attestation.
  - Trust-boundary input validation: invalid date/time selector expressions on any artifact-scoped `aw show` view must fail closed with exit 2 naming the offending token (`ogd2nv` R-03), and zero-match non-vocabulary selectors must preserve exit-2 refusal (`tests/test_read_verb_zero_match_refusal.py` and `tests/test_cli_show.py`).
  - No secrets, outbound calls, or privilege bypasses are introduced.

### Step R4

- Checked: correctness, architecture (`_ShowViewOrArtifactSubParsersAction` reusing `_ViewerOrLeafSubParsersAction`), anti-regression (`tests/test_cli_show.py`, `tests/test_reviews_record_walkthrough_new.py`, `tests/test_command_surface_declarations.py`, `tests/test_usage_refusal_agent_record.py`, `tests/test_read_verb_zero_match_refusal.py`), right-sizing/conceptual density per E-item, KISS, and `## Spec / documentation sync`.
- Found:
  - Missing parser architecture and `_runs_viewer_flags` vs `add_selector_args` `-s`/`-S`/`--status`/`--set` collision (`PR-003`).
  - Unwired normalized selector filtering on `show stale-reviews`, `show decisions`, and `show graduation` (`PR-004`).
  - Missing `command_surface.py`, `conformance_matrix.py`, `test_usage_refusal_agent_record.py`, `test_read_verb_zero_match_refusal.py`, `.aw/records/reviews/README.md`, workflow docs, and `CHANGELOG.md` (`PR-005`).
  - Coarse original `E-01` and `E-04` items bundled unrelated concerns (`PR-007`).
- Right-sizing check: Revised to 5 focused E-items across 3 task groups. Each E-item addresses one clear concern (router/dispatch, selector filtering + `reviews.py`, `aw reviews` retirement + surface/conformance parity, docs/workflows/changelog/spec sync, behavioral tests + validation).

### Step R5

- Checked through all eight reviewer personas (`.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`):
  - **QA/QC & Testing/regression:** Caught the 7 `["reviews", "decisions", ...]` calls in `tests/test_read_verb_zero_match_refusal.py`, `REQUIRED_LEAVES` count in `tests/test_usage_refusal_agent_record.py`, `RUNNABLE_ARGV` in `tests/conformance_matrix.py`, `test_command_surface_declarations.py` drift, and `tests/test_reviews_record_walkthrough_new.py` collision (`PR-001`, `PR-005`).
  - **UI/UX, Power user, Novice:** Caught the confusing divergence between `aw show history <id6>` and `aw show <id6> --history` (`PR-002`), ensured native per-view `--help` and strict wrong-view flag refusal via real subparsers (`PR-003`), and ensured `aw show artifact <reserved-name>` handles real filename/Set collisions cleanly (`E-01`, `E-05`).
  - **Architect & Software engineer:** Replaced ad-hoc positional branching with the repository's canonical `_ViewerOrLeafSubParsersAction` / `_RunsArgumentParser` architecture so `command_surface.discover_parser_leaves`, `completion.introspect_cli_tree`, and `_runs_viewer_flags` all compose without hacks (`PR-003`, `PR-004`).
  - **Stakeholder:** Protected approved spec `4sd62s` and the attended `metastore` cutover (`cxxmyv`) from accidental breakage by escalating `PR-001` as a gating human decision (`OQ-01`).

### Step R6

- Checked: Whether `p06t7i` (already Order 02 of Set `cliverbs`) should be split further.
- Finding: No split recommended. Although `- Scope-Paths:` grew to 16 work paths (triggering advisory `IPD-Z603` over the 8-path guidance), the plan has only 5 focused E-items across 3 task groups delivering one atomic CLI transition (`aw show` views + `aw reviews decisions` retirement); splitting `cli.py` parser changes from their `command_surface.py` / `conformance_matrix.py` / test mirrors would break the core merge gate between child plans. Recorded in `## Scope check` and `## Approval and execution gate`.

### Step R7

- Checked: Set `cliverbs` orchestrator `lmlji2`, sibling `m7jcis` (Order 01), sibling `xocj8i` (Order 03), prerequisite Set `selectors` (`mnlaoa`, `e36q6r`), prerequisite `9ifwdx`, and Set `metastore` (`4sd62s`, `724acb`, `cxxmyv`).
- Found:
  - `xocj8i` E-03 previously claimed `command_surface.py` cleanup for `reviews` and `show`, which would cause `p06t7i` (Order 02) to fail `tests/test_command_surface_declarations.py` at its own merge gate before Order 03 runs. Moved `command_surface.py` parity for `show` and `reviews` into `p06t7i` E-03 and documented the boundary in `## Deferred / out of scope` (`PR-005`).
  - `p06t7i` directly collided with executed metastore plan `724acb` and pending cutover `cxxmyv` (`PR-001` -> `OQ-01`).
  - `p06t7i` depends on `executed:e36q6r` (which transitively requires `executed:mnlaoa`) and `executed:9ifwdx`; updated Step 0 and Scope to credit `mnlaoa` E-03 accurately for `aw show` and `aw ipd board` selector wiring (`PR-006`).

### Step S5

- Checked: Original `## Open questions` read "None". Two material human decisions emerged during review and cannot be resolved on reviewer authority (`Reversible: no` public CLI contract conflicts):
  - `OQ-01` (escalating `BLOCKER` `PR-001`, `- Blocking: yes`, `- Finding: PR-001`): whether to keep `aw reviews` solely for `aw reviews record` (`724acb` / approved spec `4sd62s`) while removing `aw reviews decisions`, relocate `aw reviews record`, or defer removal past cutover `cxxmyv`.
  - `OQ-02` (escalating `HIGH` `PR-002`, `- Blocking: yes`, `- Finding: PR-002`): whether `aw show history <id6>` delegates to durable metadata history (`_run_show_meta(..., want_history=True)`) or the machine-local gitignored sidecar (`_run_record_history`).
- Both questions are left `open` and `- Blocking: yes` in `p06t7i`, carry explicit recommendations (`strong`), and are written to `.aw/state/lane-submissions/run-20261127T062613Z-2263911/02-p06t7i/attempt-1/outcomes/02-p06t7i.json` with `gates_verdict: true`.
- Three reversible architecture/scope decisions settled from repository evidence are recorded in `### Decisions` (`D-1..D-3`).

### Pass 2

- Trigger: `E-*`/`V-*` items expanded from 4 to 5 (`- Highest E allocated: 05`), `- Scope-Paths:` expanded from 8 to 18 entries, and `OQ-01`/`OQ-02` added.
- Re-checked the complete revised plan: front matter (`- Status: reviewed`, `- Readiness: no-go`, `- Review-Depth: complex`, `- Highest E allocated: 05`, `- Scope-Paths:` 18 entries), `## Workflow history`, `## Goal` and Mermaid flowchart (aligned with all 7 subparsers and fallback), `E-01..E-05`, Step 0, Findings, Proposed changes, Deferred (structured `- Carrier:` and `- Carrier-Declined:`), Scope check, Required tests, Spec sync, `OQ-01` and `OQ-02` (`- Blocking: yes`, `- Finding: PR-001`/`PR-002`), `V-01..V-05`, and full execution contract in the gate.
- Swept for superseded wording: removed stale "all 13 references across 6 files" bar, reconciled `Scope`, `E-02..E-05`, `V-02..V-05`, and `## Approval and execution gate` with `OQ-01` and `OQ-02`, and verified zero em or en dashes.
- Verified `5/5` E/V bijection, unchanged checkbox and execution states, and confirmed `aw ipd lint --phase review-finalize --agent` reports ONLY the expected `IPD-Q501` blocking-question findings on `OQ-01` and `OQ-02` (plus advisory `IPD-Z603` path-count guidance) and zero structural, carrier, or escalation errors.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R7 / Cross-spec conflict (`aw reviews record` vs removing `aw reviews`) | agent_workflows/cli.py::p_reviews_record:4592-4666; agent_workflows/reviews.py::run_record:421-798; agent_workflows/command_surface.py:683; tests/test_reviews_record_walkthrough_new.py:121-328; tests/test_usage_refusal_agent_record.py:92-94; .aw/records/plans/executed/20261109-metastore-268-724acb-build-the-dormant-reviews-record-and-walkthrough-new-command.ipd.md (`feb476c6e`, 2026-11-23); .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md; .aw/system/cutover/metastore-docs.cutover.patch | `p06t7i` E-02/V-02 instruct removing top-level `aw reviews` outright and asserting zero `aw reviews` matches across code, tests, and docs, resting on the 2026-11-22 premise (`i8dc07` OQ-05) that `aw reviews` holds only `decisions`. Three hours after `p06t7i` was committed (`f5a2c87e6`), metastore plan `724acb` executed (`feb476c6e`) and shipped `aw reviews record` under approved spec `4sd62s`, referenced 25+ times in `metastore-docs.cutover.patch` for pending cutover `cxxmyv`. Deleting `aw reviews` breaks approved spec `4sd62s` and the metastore cutover. | C:High; U:High; S:Low; F:High; Overall:High | OPEN | Escalated in `p06t7i` as `- Blocking: yes` `OQ-01` (`- Finding: PR-001`) and in lane outcome JSON (`q-aw-reviews-record-conflict`, `gates_verdict: true`). Recommended Option 1: keep `aw reviews` solely for `aw reviews record`, remove only `aw reviews decisions`, and amend `ogd2nv` R-11. Recommendation strength: strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / R4 / Ambiguous backend for `aw show history <id6>` | agent_workflows/cli.py::_run_show_meta:14509-14563 (`aw show <id6> --history`, spec `4sd62s` 4.8); agent_workflows/cli.py::_run_record_history:14830-14935 and p_record_history:5502-5516 (`aw record-history <id6>` local gitignored sidecar); `p06t7i` E-01, Findings:81; `ogd2nv` R-09 | `p06t7i` specifies `aw show history <id6>` without naming whether it delegates to durable tracked metadata history (`_run_show_meta(..., want_history=True)`, already exposed as `aw show <id6> --history`) or the machine-local gitignored sidecar (`_run_record_history`). Choosing the sidecar would make `aw show history <id6>` and `aw show <id6> --history` return completely different data. | C:Low; U:High; S:Low; F:Medium; Overall:Medium-High | OPEN | Escalated in `p06t7i` as `- Blocking: yes` `OQ-02` (`- Finding: PR-002`) and in lane outcome JSON (`q-aw-show-history-source`, `gates_verdict: true`). Recommended Option 1: delegate `aw show history <id6>` to durable metadata history (`_run_show_meta(..., want_history=True)`). Recommendation strength: strong. |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 / Single-positional `p_show` and `_runs_viewer_flags` flag collision | agent_workflows/cli.py::p_show:5227-5266; agent_workflows/cli.py::_runs_viewer_flags:3365-3450 (`-s`, `-S`, `--status`, `--set`); agent_workflows/cli.py::_ViewerOrLeafSubParsersAction:1098-1158; agent_workflows/cli.py::_RunsArgumentParser:1178-1188; `mnlaoa` E-03 (`add_selector_args(p_show)`); `9ifwdx` E-03 (`--diff`) | `p_show` currently takes one positional (`action_ref`), so multi-token views (`show artifact <sel>`, `show graduation <id6>`, `show history <id6>`, `show decisions <sel>`, `show runs <target>`) fail at parse time; registering `_runs_viewer_flags` alongside `selectors.add_selector_args(p_show)` crashes `argparse` with `conflicting option string` (`-s`, `-S`, `--status`, `--set`); flat view flags also fail to reject wrong-view flags and hide view leaves from `command_surface.discover_parser_leaves`. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Rewrote `E-01` and Mermaid diagram to adopt the repository's canonical `_ShowViewOrArtifactSubParsersAction` + `_ShowArgumentParser` hybrid subparser architecture with 7 real subparsers and a sibling fallback artifact parser, isolating `_runs_viewer_flags` on `show runs` and `--diff` on `show stale-reviews` (`D-1`). Recommendation strength: very strong. |
| PR-004 | HIGH | UNDER-SCOPE | R2 / R4 / Unwired normalized selectors on reserved `aw show` views (`ogd2nv` R-09) | `ogd2nv` R-09; `9ifwdx` Decision D4; agent_workflows/reviews.py::run_decisions:262-312; agent_workflows/cli.py::_run_graduation:14937-15025; `mnlaoa` E-03 (`_run_plans` `include_types=False`) | After `9ifwdx` and `mnlaoa`, only bare `aw show <ref>` and `aw ipd board` apply `selectors.filter_records`; `stale-reviews`, `decisions`, and `graduation` would parse and silently ignore normalized selector flags, and `show board` must use `include_types=False` while `show runs` is exempt per `ogd2nv` R-05. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Added explicit per-view selector wiring in `E-01` and `E-02` (`filter_records` on `stale-reviews`, `decisions`, and `graduation`; `include_types=False` on `stale-reviews` and `board`; `ValueError` -> exit 2 per `ogd2nv` R-03; `CommandResult.command = "show decisions"` in `reviews.run_decisions`) (`D-2`). Recommendation strength: very strong. |
| PR-005 | HIGH | UNDER-SCOPE | R2 / R4 / R7 / Missing command-surface, conformance-matrix, refusal-test, workflow, and changelog files | agent_workflows/command_surface.py:221,1690; tests/test_command_surface_declarations.py:52-146; tests/conformance_matrix.py:183,185; tests/test_read_verb_zero_match_refusal.py:164,215-273,344-360; tests/test_usage_refusal_agent_record.py:92-94; agent_workflows/cli.py::_COMMAND_HELP:440-489; .aw/records/reviews/README.md:98-100; .aw/system/workflows/plan-review/steps/s5-questions.md:47; .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md:54; CHANGELOG.md; `xocj8i` E-03 | `p06t7i` omitted 10 affected files and deferred `command_surface.py` updates to Order 03 (`xocj8i`), which would immediately fail Order 02's core pytest merge gate on `test_command_surface_declarations.py`, `test_read_verb_zero_match_refusal.py`, and `test_usage_refusal_agent_record.py` and leave stale `aw reviews decisions` guidance in docs/workflows and no 2.0.0 changelog entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all missing files to `- Scope-Paths:`, added dedicated parity work in `E-03`, doc/workflow/changelog sync in `E-04`, and test updates in `E-05`, clarifying the boundary with `xocj8i` in `## Deferred / out of scope` (`D-3`). Recommendation strength: very strong. |
| PR-006 | MEDIUM | IN-SCOPE | R2 / R4 / Unqualified post-cutover spec citations, misattributed prerequisite, incomplete validation and execution gate | `p06t7i` front matter (`- From-Spec: ogd2nv`), `Scope:6`, `Required tests:102-104`, `Approval and execution gate:143` | Post-cutover spec `ogd2nv` citations in `E-*`/`V-*` were missing `<spec-id6>` qualification (`SPEC-PLAN-TRACE`); Scope credited `aw show` selectors to `e36q6r` instead of `mnlaoa` E-03; `Required tests` omitted bare `python3 -m pytest`, parity suites, `aw specs check`, and `--agent` on `aw sanitize`; the gate omitted resolved-OQ, scope-fence (`--scope-reason`/`--scope-ack`), honesty, and conditional `AW_EXECUTION_ROLE=worker` vs standalone `aw ipd finalize` clauses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified all `ogd2nv R-*`/`AC-*` citations in `E-01..E-05` and `V-01..V-05`, credited `mnlaoa` accurately, expanded `Required tests / validation`, and added the full execution contract to `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / R4 / Hardcoded mutable reference count and coarse E-item granularity | `p06t7i` Concern:5, Scope:6, E-01:48, E-02:55, E-04:67, V-02:124 | Used a stale mutable count ("all 13 references across 6 files") as a bar instead of a re-derived property check; bundled parser + 7 views + selectors into one coarse E-01 and test migration + new tests + validation into one coarse E-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced hardcoded count bars with live grep property checks, split work into 5 focused E-items (`E-01..E-05`) with 1:1 `V-01..V-05`, and documented the `IPD-Z603` cohesion rationale. Recommendation strength: strong. |
| PR-008 | LOW | IN-SCOPE | P / Technical writing polish, `path::Symbol` citations, and Mermaid flowchart sync | `p06t7i` throughout; `.aw/system/workflows/technical-writing/technical-writing.md` | Missing `path::Symbol` citations in checklist items and Step 0; Mermaid flowchart did not reflect the 7 subparsers and sibling fallback parser; prose tightened for direct active voice and explicit error conditions with zero em/en dashes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Normalized `path::Symbol` citations, synchronized the Mermaid flowchart with the hybrid subparser architecture, and tightened prose across the plan. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`, `Scope-Paths`, `Short-Description`, `Highest E allocated`) | 8 Scope-Paths, 4 E-items, claimed removing `aw reviews` across 13 refs and credited `e36q6r` for `aw show` selectors | 18 Scope-Paths, 5 E-items, hybrid subparser architecture, `mnlaoa` attribution, `OQ-01` gate for `aw reviews record`, `- Status: reviewed`, `- Readiness: no-go`, `- Review-Depth: complex` | PR-001, PR-003, PR-005, PR-006, PR-007 |
| `## Goal` and Mermaid flowchart | Generic 5-branch flowchart without subparser/fallback distinction or `OQ-02` gate | Explicit `_ShowViewOrArtifactSubParsersAction` 7-subparser + sibling fallback flowchart aligned with `E-01` | PR-003, PR-008, technical writing standard requirement 12 |
| `E-01..E-05`, `V-01..V-05` | 4 coarse items without symbol anchors, selector wiring, command-surface parity, or qualified `ogd2nv` citations | Common rules plus 5 focused, symbol-cited E-items and 1:1 V-items with qualified `ogd2nv R-09..R-11`/`AC-05` citations and re-derived checks | PR-003..PR-008 |
| `## Project conventions discovered (Step 0)`, `## Findings`, `## Proposed changes`, `## Deferred / out of scope`, `## Scope check` | 4 bullets claiming single-subcommand `aw reviews` (13 refs in 6 files) | Documented `724acb` chronology, two history engines, `_ViewerOrLeafSubParsersAction`, `_runs_viewer_flags` collision, parity tests, `xocj8i` boundary, and `IPD-Z603` rationale | PR-001..PR-007 |
| `## Open questions` | "None" | Added `- Blocking: yes` `OQ-01` (`- Finding: PR-001`) and `OQ-02` (`- Finding: PR-002`) with context, options, and `strong` recommendations | PR-001, PR-002 |
| `## Required tests / validation`, `## Spec / documentation sync`, `## Approval and execution gate` | 3 narrow commands, 2 docs, one-line gate | Full targeted + bare core pytest, mypy, `aw specs check`, `aw attention --check`, `aw sanitize --agent`; all docs/workflows/changelog/spec; full execution contract | PR-005, PR-006 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| I-01 | `E-03`, `OQ-01` | Whether top-level `aw reviews` remains for shipped `aw reviews record` (`724acb` / approved spec `4sd62s`) or `aw reviews record` is relocated | Maintainer decision between retaining `aw reviews` for `record` only vs relocating `record` and amending `4sd62s` + `metastore-docs.cutover.patch` vs deferring removal | Keep `aw reviews` solely for `aw reviews record`, remove only `aw reviews decisions`, and amend `ogd2nv` R-11 | strong |
| I-02 | `E-01`, `OQ-02` | Whether `aw show history <id6>` displays durable metadata history (`_run_show_meta(..., want_history=True)`) or the machine-local sidecar (`_run_record_history`) | Maintainer confirmation of the intended backend for `aw show history <id6>` | Route `aw show history <id6>` to durable metadata history (`_run_show_meta(..., want_history=True)`), matching `aw show <id6> --history` | strong |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `p_show` parse seven named read-only views plus bare artifact selectors without colliding `_runs_viewer_flags` with `selectors.add_selector_args`? | Use a hybrid subparser router (`_ShowViewOrArtifactSubParsersAction` + `_ShowArgumentParser`) modeled on `_ViewerOrLeafSubParsersAction` / `_RunsArgumentParser`, with real subparsers per view (isolating `_runs_viewer_flags` on `show runs` and `--diff` on `show stale-reviews`) and a sibling fallback artifact parser. | Flat flags on `p_show` with manual `argv` inspection in `_run_show` (rejected: crashes `argparse` on `-s`/`-S`/`--status`/`--set` collision, hides leaves from `command_surface.discover_parser_leaves`, and provides no per-view `--help`). | `agent_workflows/cli.py:1098-1188`, `3365-3450`, `5227-5266`; `agent_workflows/command_surface.py:2803-2846`; `mnlaoa` E-03. | yes |
| D-2 | How should normalized selector flags apply to `show stale-reviews`, `show decisions`, `show graduation`, `show board`, and `show runs`? | Apply `selectors.filter_records` on `stale-reviews` (`include_types=False`), `decisions` (by subject artifact), `graduation` (on cluster artifacts), and `board` (`include_types=False` via `_run_plans`), while exempting `runs` (`_runs_viewer_flags` only, per `ogd2nv` R-05). | Leave selector flags unwired on `stale-reviews`/`decisions`/`graduation` (rejected: violates `ogd2nv` R-09 and silently ignores user flags). | `ogd2nv` R-05, R-09; `9ifwdx` Decision D4; `mnlaoa` E-03; `agent_workflows/reviews.py:262-312`. | yes |
| D-3 | Should `p06t7i` (Order 02) update `command_surface.py`, `conformance_matrix.py`, and `test_usage_refusal_agent_record.py` itself, or leave them to Order 03 (`xocj8i`)? | Own `show` and `reviews` parity in `p06t7i` E-03 so Order 02's core pytest merge gate passes independently; leave only completion updates and verb-first declarations in `xocj8i` E-03. | Defer `command_surface.py` cleanup to `xocj8i` (rejected: breaks `tests/test_command_surface_declarations.py` and `tests/test_usage_refusal_agent_record.py` when Order 02 runs). | `tests/test_command_surface_declarations.py:52-146`; `tests/test_usage_refusal_agent_record.py:92-94`; `xocj8i` E-03. | yes |

## Round 2

This round ran in the same review-sweep lane worktree (`review-sweep-run-20261127T062613Z-2263911`, attempt 2) after the maintainer answered both blocking questions (`OQ-01` and `OQ-02`) over the terminal channel on 2026-11-27:
- `OQ-01`: Option 1 - keep top-level `aw reviews` solely for `aw reviews record` until after the `metastore` cutover (`cxxmyv`) lands, remove only `aw reviews decisions`, rename the new `aw show` view from `aw show decisions` to `aw show review-decisions` (matching `aw show stale-reviews`), and track relocating `aw reviews record` and removing `aw reviews` before 2.0.0 in follow-up backlog item `pqqqzf` (gated on `cxxmyv`, blocking release `f33nrj`).
- `OQ-02`: Option 1 - route `aw show history <id6>` to the durable git-tracked workflow and metadata history renderer matching `aw show <id6> --history` (`agent_workflows/cli.py::_run_show_meta`), while leaving `aw record-history <id6>` intact for the machine-local gitignored sidecar.

Draft spec `ogd2nv` (R-09, R-11, AC-05), sibling `xocj8i` (Order 03), and orchestrator `lmlji2` (Order 00) were already updated on `main` (commit `4a626eb41`), and follow-up backlog `pqqqzf` already exists in `.aw/records/backlog/blocked/20261127-pqqqzf-01-pqqqzf-rename-reviews-record-and-retire-aw-reviews.backlog.md`. Per maintainer instruction, this round updates only `p06t7i` and its review record in this lane, sweeps every superseded `aw show decisions` and `OQ-01`/`OQ-02` gate reference across `p06t7i`, and clears `PR-001` and `PR-002`.

### Step T

1. Yes; unchanged from Round 1 (public CLI surface changes on `aw show` and removal of `aw reviews decisions`, keeping `aw reviews record` intact).
2. No; unchanged from Round 1.
3. Yes; 5 E-items across 3 task groups and 16 work Scope-Paths (spec `ogd2nv` removed from `- Scope-Paths:` because `4a626eb41` already synced it).
4. Yes; `- Scope-Paths:` lists all 16 work paths plus the plan file.
5. Yes; unchanged from Round 1 (preserving `aw reviews record` and `aw show` compatibility).

AW-TIER: complex

### Step R1

- Checked: updated spec `ogd2nv` (`R-09`, `R-11`, `AC-05`), updated sibling `xocj8i` (`E-03`), and follow-up backlog `pqqqzf` (`.aw/records/backlog/blocked/20261127-pqqqzf-01-pqqqzf-rename-reviews-record-and-retire-aw-reviews.backlog.md`) in this worktree. Confirmed exact alignment on `aw show review-decisions`, `aw reviews record` preservation, `aw show history <id6>` matching `aw show <id6> --history` (`_run_show_meta`), and `- Carrier: pqqqzf`.

### Step R2

- Checked: `5/5` E/V bijection, `- Scope-Paths:` (dropped `ogd2nv` since `4a626eb41` already updated it), `OQ-01` and `OQ-02` marked `Status: resolved` preserving `- Blocking: yes`, `- Owner: maintainer`, and `- Finding: PR-001`/`PR-002`, `- Carrier: pqqqzf` resolving cleanly, and `aw ipd lint --phase review-finalize --agent` returning clean (exit 0, 0 errors; advisory `IPD-Z603` only).

### Step R3

- Checked: preserving `aw reviews record` protects the schema-2 review-round audit writer (`724acb` / approved spec `4sd62s`) and pending cutover `cxxmyv`.

### Step R4

- Checked: `show history <id6>` also accepts `--format text|json` (default `None`) so `aw show history <id6> [--format json]` matches `aw show <id6> --history [--format json]` cleanly through `_run_show_meta`.

### Step R7

- Checked: cross-plan alignment with `ogd2nv` (R-09, R-11, AC-05), `xocj8i` (E-03), `lmlji2`, and `pqqqzf` (commit `4a626eb41`). Zero remaining drift across Set `cliverbs` or Set `metastore`.

### Step S5

- Checked: both `OQ-01` (`- Finding: PR-001`) and `OQ-02` (`- Finding: PR-002`) are now `Status: resolved` by the maintainer (2026-11-27, terminal channel). Both gating findings (`PR-001`, `PR-002`) are marked `FIXED` in this round's `### Findings` table. No open question remains; attempt-2 outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised `p06t7i` end to end and swept for every superseded `show decisions` / `aw show decisions` / `OQ-01` / `OQ-02` gating reference: zero stale `show decisions` tokens remain anywhere in `p06t7i` (only historical references to `aw reviews decisions` where naming the retired command).
- Verified `5/5` E/V bijection, zero em or en dashes, `- Readiness: go-pending-approval`, and `aw ipd lint --phase review-finalize --agent` passing with exit 0 (advisory `IPD-Z603` only).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R7 / Cross-spec conflict (`aw reviews record` vs removing `aw reviews`) | Maintainer resolution of `OQ-01` (2026-11-27, terminal channel); `ogd2nv` R-09/R-11/AC-05 (commit `4a626eb41`); `.aw/records/backlog/blocked/20261127-pqqqzf-01-pqqqzf-rename-reviews-record-and-retire-aw-reviews.backlog.md` | Removing top-level `aw reviews` outright conflicted with shipped `aw reviews record` (`724acb` / approved spec `4sd62s`) and pending cutover `cxxmyv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Applied maintainer's `OQ-01` resolution (Option 1): `E-01..E-05` and `V-01..V-05` now retire only `aw reviews decisions`, keep top-level `aw reviews` solely for `aw reviews record`, rename the `aw show` view to `aw show review-decisions`, record `- Carrier: pqqqzf` in `## Deferred / out of scope`, drop `ogd2nv` from `- Scope-Paths:` (already synced in `4a626eb41`), and mark `OQ-01` `resolved` (`D-4`). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / R4 / Ambiguous backend for `aw show history <id6>` | Maintainer resolution of `OQ-02` (2026-11-27, terminal channel); `ogd2nv` R-09/AC-05 (commit `4a626eb41`); `agent_workflows/cli.py::_run_show_meta:14509-14563` | `aw show history <id6>` did not specify durable tracked metadata history (`_run_show_meta`) vs the machine-local gitignored sidecar (`_run_record_history`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Applied maintainer's `OQ-02` resolution (Option 1): `E-01`, `E-04`, `E-05`, `V-01`, and the Mermaid flowchart route `aw show history <id6>` (with optional `--format` `text` or `json`) to `_run_show_meta(..., want_history=True)` matching `aw show <id6> --history`, leaving `aw record-history <id6>` intact for the local sidecar, and mark `OQ-02` `resolved` (`D-5`). Recommendation strength: very strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`, `Scope-Paths`, `Readiness`, `Short-Description`), `## Workflow history` | `aw show decisions`, `OQ-01` gate, `ogd2nv` in Scope-Paths, `- Readiness: no-go` | `aw show review-decisions`, `aw reviews record` preserved until `pqqqzf`, `aw show history` routed to `_run_show_meta`, `ogd2nv` removed from Scope-Paths (16 work paths, synced in `4a626eb41`), `- Readiness: go-pending-approval`, Round 2 `/plan-review` history line | PR-001, PR-002 |
| `## Goal`, Mermaid flowchart, `E-01..E-05`, `V-01..V-05` | `decisions` view name and conditional `OQ-01`/`OQ-02` branches | Unconditional `review-decisions` subparser/cmd/hints, `show history <id6>` wired to `_run_show_meta` (with `--format`), `aw reviews record` preserved, and unconditional test assertions | PR-001, PR-002 |
| `## Project conventions`, `## Findings`, `## Proposed changes`, `## Deferred / out of scope`, `## Spec / documentation sync`, `## Open questions`, `## Approval and execution gate` | `OQ-01`/`OQ-02` `open` and blocking execution | `OQ-01` and `OQ-02` marked `resolved` with exact maintainer answers, `- Carrier: pqqqzf` added in `## Deferred / out of scope`, `4a626eb41` sync noted, gate cleared of open questions | PR-001, PR-002 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-4 | How should `p06t7i` handle `aw reviews` and name the read-only review-decisions view? | Keep `aw reviews` solely for `aw reviews record` until after `cxxmyv` (tracking full removal in `pqqqzf`), remove only `aw reviews decisions`, and name the new view `aw show review-decisions` (maintainer decision on `OQ-01`). | Remove top-level `aw reviews` now or keep `aw show decisions` (rejected by the maintainer on 2026-11-27). | Maintainer answer to `OQ-01` (2026-11-27, terminal channel); `ogd2nv` R-09/R-11/AC-05 (commit `4a626eb41`); backlog `pqqqzf`. | yes |
| D-5 | Which history source should `aw show history <id6>` display? | Route `aw show history <id6>` to durable git-tracked workflow and metadata history (`_run_show_meta(..., want_history=True)`, with optional `--format` `text` or `json`), leaving `aw record-history <id6>` intact for the local sidecar (maintainer decision on `OQ-02`). | Route `aw show history` to `_run_record_history` or add `--sidecar` (rejected by the maintainer on 2026-11-27). | Maintainer answer to `OQ-02` (2026-11-27, terminal channel); `ogd2nv` R-09/AC-05 (commit `4a626eb41`). | yes |
