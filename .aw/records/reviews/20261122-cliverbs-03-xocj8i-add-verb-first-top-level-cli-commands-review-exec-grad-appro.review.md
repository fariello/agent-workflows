# Review findings: ipd xocj8i

- Subject-Id: xocj8i
- Subject-Type: ipd
- Reviewed-At: 2026-11-27
- Reviewer: antigravity/gemini
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261127T062613Z-2263911`). The target plan `.aw/records/plans/pending/20261122-cliverbs-03-xocj8i-add-verb-first-top-level-cli-commands-review-exec-grad-appro.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The review examined `agent_workflows/cli.py`, `agent_workflows/run_dispatch.py`, `agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/status_set.py`, `agent_workflows/command_surface.py`, `agent_workflows/completion.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/conformance_matrix.py`, `tests/test_command_surface_declarations.py`, spec `ogd2nv`, backlog `i8dc07`, approved prerequisite plans `m7jcis` (Order 01), `e36q6r`, `9ifwdx`, `55tt85`, reviewed sibling `p06t7i` (Order 02), and orchestrator `lmlji2`. It found three `BLOCKER` (`PR-001`, `PR-002`, `PR-003`), three `HIGH` (`PR-004`, `PR-005`, `PR-006`), one `MEDIUM` (`PR-007`), and one `LOW` (`PR-008`) findings. Six findings (`PR-003..PR-008`) were fixed in place. Two `BLOCKER` findings (`PR-001` on `aw validate`'s missing driver backend; `PR-002` on `m7jcis`'s handed-off `agy` dispatch adapter scope decision) require human maintainer decisions, remain `OPEN`, are escalated into `xocj8i` as `- Blocking: yes` open questions (`OQ-01`, `OQ-02`), and are emitted in the lane outcome JSON with `gates_verdict: true`. No production code or test code was modified.

### Step T

1. Yes; the plan introduces five new top-level public CLI commands (`review`/`rev`, `exec`, `plan`/`grad`/`graduate`, `validate`, `approve`), enables `--action execute` in `runner_shared.py`, updates completions, command declarations, docs, and `CHANGELOG.md`.
2. Yes; `aw approve` directly governs human approval attestation (`--by-human`, `--message`, TTY auto-attestation) and delegates into `status_set.run_set_command` alongside the `9ifwdx` bulk-stale and `55tt85` unreviewed-plan guards.
3. Yes; spans 5 E-items across 12 work Scope-Paths and coordinates the whole Set `cliverbs` (`m7jcis`, `p06t7i`, `xocj8i`) and Set `selectors` (`e36q6r`).
4. Yes; `- Scope-Paths:` originally listed 9 entries and omitted 4 required files (`runner_shared.py`, `tests/test_oc_runipd.py`, `tests/conformance_matrix.py`, `CHANGELOG.md`; now 13 entries total).
5. Yes; forwarding `--action execute` today fails unconditionally (`ACTION_IMPLEMENTED` excludes it), `aw validate` has no driver action, resolved `agy` hosts fail with `"no dispatch adapter"`, and a loose `aw approve` gate could let unattended agents bypass human approval rules.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/runner_shared.py` (`ACTION_CHOICES` and `ACTION_IMPLEMENTED` lines 39645-39646, `enforce_requested_action` lines 40537-40620, `action_for` lines 28130-28150), `agent_workflows/oc_runipd.py` (`--action` lines 5133-5145, `--validate` lines 5174-5195), `agent_workflows/agy_runipd.py` (`--action` lines 4304-4315, `resolve_verification_decision` lines 2202-2218), `agent_workflows/run_dispatch.py` (`RUNNER_ADAPTERS` lines 98-148, `dispatch_named`/`dispatch_default` lines 245-299), `agent_workflows/cli.py` (pre-`parse_args` forwarding lines 1614-1632, 3665-3693, 21149-21177, 21465-21565), `agent_workflows/status_set.py` (spec `stdin_is_interactive` lines 1117-1135, `approval_refusals` lines 1239-1246, `run_set_command` lines 3235-3455), `agent_workflows/command_surface.py` (lines 734-745, 1473-1492, 2211-2219), `tests/conformance_matrix.py` (lines 531-582), `tests/test_oc_runipd.py` (lines 5581-5610), `tests/test_agy_runipd_cli.py` (line 1861), and approved Order 01 `m7jcis` (lines 97-104, 159-161, 184-190).
- Found:
  - Neither `runner_shared.py`, `oc_runipd.py`, nor `agy_runipd.py` implements standalone `--action validate` (`/verify-execution` on executed plans) (`PR-001`).
  - `run_dispatch.RUNNER_ADAPTERS` is OpenCode-only and `m7jcis` explicitly handed the `agy` adapter decision to `xocj8i` (`Carrier: xocj8i`), which `xocj8i` omitted (`PR-002`).
  - `--action execute` is excluded from `runner_shared.ACTION_IMPLEMENTED` and raises `"not implemented"` on every call, pinned by `tests/test_oc_runipd.py:5583-5606` (`PR-003`).
  - `cli.py` forwarded runner leaves use `add_help=False` + `REMAINDER` + pre-`parse_args` interception, not `selectors.add_selector_args` in `cli.py` (`PR-004`).
  - `status_set.py` checks `stdin_is_interactive()` on specs only (not plans) and refuses empty positional targets (`PR-005`).

### Step R2

- Checked: E/V bijection (upgraded from 4/4 to 5/5 with `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Item-Dependencies: executed:m7jcis, executed:p06t7i, executed:e36q6r`, runtime-demonstration reachability (flagged unreachable `aw validate` and `--action execute` demands under `PR-001` and `PR-003`), qualified post-cutover `ogd2nv` citations, durable carriers in `## Deferred / out of scope`, and full execution contract in `## Approval and execution gate`.
- Found: unreachable runtime demonstrations (`--action execute` and standalone `aw validate`), missing `runner_shared.py`/`conformance_matrix.py`/`test_oc_runipd.py`/`CHANGELOG.md` in `- Scope-Paths:`, unqualified `ogd2nv` citations, and incomplete validation and gate (`PR-001`, `PR-003`, `PR-006`, `PR-007`).

### Step R3

- Checked (full form, `complex` tier):
  - Approval authority integrity: `aw approve` MUST enforce `ogd2nv` R-16 strictly before invoking `status_set.run_set_command` so non-interactive/`--agent`/`--json` callers cannot approve plans or specs without BOTH `--by-human` and a non-empty `--message`, and interactive TTY calls still pass through `plan_readiness.approval_refusals`, `9ifwdx` bulk-stale confirmation (`--accept-stale`), and `55tt85` unreviewed-plan refusal (`--allow-unreviewed`) (`PR-005`).
  - Action-safety boundary: enabling `"execute"` in `runner_shared.ACTION_IMPLEMENTED` preserves `enforce_requested_action`'s refusal of `draft`, `to-review`, and non-IPD items before any run starts (`PR-003`).
  - No hardcoded secrets, outbound calls, or privilege bypasses are introduced.

### Step R4

- Checked: architecture (pre-`parse_args` forwarding + `REMAINDER` matching `aw run as`/`ipd` and `aw oc review`), anti-regression (`tests/test_oc_runipd.py`, `tests/test_command_surface_declarations.py`, `tests/test_agent_surface_conformance.py`, `tests/test_completion.py::CompleteQueryLatencyTests`), right-sizing (5 focused E-items across 3 task groups), KISS, and `## Spec / documentation sync`.
- Found: `PR-003..PR-007`, all fixed in place.

### Step R5

- Checked through all eight reviewer personas (`.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`):
  - **QA/QC & Testing/regression:** Caught the `"not implemented"` failure on `--action execute` (`tests/test_oc_runipd.py:5583`), the missing `conformance_matrix.py` exemptions, and the missing `test_command_surface_declarations.py`/`test_agent_surface_conformance.py` validation checks (`PR-003`, `PR-006`, `PR-007`).
  - **UI/UX, Power user, Novice:** Ensured leading `--help` on verb-first runner commands exits 0 without requiring `default_runner`, made selector-only `aw approve -s reviewed --sid <set>` actually work instead of hitting `status_set`'s empty-target refusal, and surfaced the `agy` dispatch gap instead of letting Antigravity users hit a surprise exit 2 (`PR-002`, `PR-004`, `PR-005`).
  - **Architect & Software engineer:** Aligned top-level runner verbs with `cli.py`'s pre-`parse_args` forwarding and `e36q6r`'s static completion constant so zero driver flags are duplicated and completion latency stays under 250ms (`PR-004`, `PR-006`).
  - **Stakeholder:** Surfaced the missing `/verify-execution` runner action (`PR-001`) and `m7jcis`'s handed-off `agy` adapter decision (`PR-002`) before implementation rather than letting execution fail or ship broken promises.

### Step R6

- Checked: Whether `xocj8i` (Order 03 of Set `cliverbs`) should split further.
- Finding: No split recommended for the thin CLI wrapper work itself (5 E-items, 12 work Scope-Paths). However, `OQ-01` (`aw validate` driver backend) and `OQ-02` (`agy` dispatch adapter) both recommend splitting those heavy runner-driver backends into separate plans rather than overloading `xocj8i`.

### Step R7

- Checked: Set `cliverbs` orchestrator `lmlji2`, approved Order 01 `m7jcis`, reviewed Order 02 `p06t7i`, approved `e36q6r`, approved `9ifwdx`, approved `55tt85`, and spec `ogd2nv`.
- Found:
  - `m7jcis` OQ-01 explicitly passed `Carrier: xocj8i` for the `agy` dispatch adapter decision, which `xocj8i` had not addressed (`PR-002` -> `OQ-02`).
  - `p06t7i` E-03 already owns `show` and `reviews` `command_surface.py` parity; clarified `xocj8i` E-03 so it does not duplicate that work (`PR-006`).
  - Note for orchestrator `lmlji2`: once `xocj8i` finishes review with 5 E-items (`E-05`/`V-05` owning whole-Set validation), `lmlji2`'s `E-04`/`V-04` citations will align during `lmlji2`'s own review.

### Step S5

- Checked: Original `## Open questions` read "None". Two material human scope/architecture decisions cannot be settled on reviewer authority:
  - `OQ-01` (escalating `BLOCKER` `PR-001`, `- Blocking: yes`, `- Finding: PR-001`): how `aw validate` should be scoped given that no standalone `--action validate` (`/verify-execution` on executed plans) exists in `runner_shared.py`, `oc_runipd.py`, or `agy_runipd.py`.
  - `OQ-02` (escalating `BLOCKER` `PR-002`, `- Blocking: yes`, `- Finding: PR-002`): whether to add the `agy` dispatch adapter (`run_dispatch.py` + `agy_runipd.py`) before/in `xocj8i` or ship OpenCode-only dispatch with a follow-up backlog carrier (carrying forward `m7jcis` OQ-01).
- Both questions are left `open` and `- Blocking: yes` in `xocj8i`, carry `strong` recommendations, and are emitted in `.aw/state/lane-submissions/run-20261127T062613Z-2263911/03-xocj8i/attempt-1/outcomes/03-xocj8i.json` with `gates_verdict: true`.
- Three reversible technical decisions settled from repository evidence are recorded in `### Decisions` (`D-1..D-3`).

### Pass 2

- Trigger: `E-*`/`V-*` expanded from 4 to 5 (`- Highest E allocated: 05`), `- Scope-Paths:` expanded from 9 to 13 entries, and `OQ-01`/`OQ-02` added.
- Re-checked the complete revised `xocj8i` end to end: verified `5/5` E/V bijection, unchanged checkbox and execution states, qualified `ogd2nv` citations, zero em or en dashes, `OQ-01`/`OQ-02` carrying `- Blocking: yes` and `- Finding: PR-001`/`PR-002`, and `aw ipd lint --phase review-finalize --agent` reporting ONLY the two expected `IPD-Q501` blocking-question findings plus advisory `IPD-Z603` (zero structural, carrier, or escalation errors).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 / Unreachable `aw validate` (`/verify-execution` runner action does not exist) | agent_workflows/runner_shared.py:39645-39646 (`ACTION_CHOICES`, `ACTION_IMPLEMENTED`); agent_workflows/oc_runipd.py:5137-5141; agent_workflows/agy_runipd.py:4308-4312; `xocj8i` E-01:50, Scope-Paths:7 | `xocj8i` E-01 requires `aw validate` to dispatch AI `/verify-execution` on executed plans via `run_dispatch.dispatch_for_state`, but neither driver has a standalone `--action validate` action, prompt builder, or terminal-plan queue selector, and neither driver is in `- Scope-Paths:`. | C:High; U:Medium; S:Low; F:High; Overall:High | OPEN | Escalated in `xocj8i` as `- Blocking: yes` `OQ-01` (`- Finding: PR-001`) and in lane outcome JSON (`q-validate-runner-backend`, `gates_verdict: true`). Recommended Option 1: keep `xocj8i` as the thin CLI wrapper and split standalone `--action validate` driver support into a dedicated plan. Recommendation strength: strong. |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R7 / OpenCode-only `RUNNER_ADAPTERS` (`m7jcis` OQ-01 carrier handoff) | agent_workflows/run_dispatch.py:101-148 (`RUNNER_ADAPTERS`); agent_workflows/agy_runipd.py:2208-2212; `.aw/records/plans/pending/20261122-cliverbs-01-m7jcis-add-per-state-runner-profile-routing-path-host-fallback-and.ipd.md:100,160-161,184-190` (`Carrier: xocj8i`) | `run_dispatch.RUNNER_ADAPTERS` registers `"oc"` only and `agy_runipd.py` has no `as <profile>` clause; approved Order 01 `m7jcis` explicitly handed this decision to `xocj8i`. Without an `agy` adapter, every verb-first command exits 2 with `"no dispatch adapter"` whenever the resolved host is `agy`. | C:High; U:High; S:Low; F:High; Overall:High | OPEN | Escalated in `xocj8i` as `- Blocking: yes` `OQ-02` (`- Finding: PR-002`) and in lane outcome JSON (`q-agy-dispatch-adapter-scope`, `gates_verdict: true`). Recommended Option 1: add a prerequisite child plan for the `agy` dispatch adapter and `agy_runipd.py` `as <profile>` support before `xocj8i`. Recommendation strength: strong. |
| PR-003 | BLOCKER | IN-SCOPE | R1 / R2 / `--action execute` refused unconditionally by `ACTION_IMPLEMENTED` | agent_workflows/runner_shared.py:39646,40580-40599 (`ACTION_IMPLEMENTED`, `enforce_requested_action`); tests/test_oc_runipd.py:5581-5606; tests/test_agy_runipd_cli.py:1861 | `xocj8i` E-01 forwards `--action execute` from `aw exec`, which unconditionally raises `DriverError("--action execute is not implemented yet")` because `"execute"` is absent from `runner_shared.ACTION_IMPLEMENTED` (pinned by `tests/test_oc_runipd.py:5583-5606`). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added `agent_workflows/runner_shared.py` and `tests/test_oc_runipd.py` to `- Scope-Paths:` and updated `E-01` to enable `"execute"` in `ACTION_IMPLEMENTED` (accepting derived `execute` and `orchestrate` in `enforce_requested_action` while still refusing `draft`, `to-review`, and non-IPD items) and update `tests/test_oc_runipd.py` (`D-1`). Recommendation strength: very strong. |
| PR-004 | HIGH | IN-SCOPE | R1 / R4 / Forwarding vs `cli.py` flag parsing on top-level runner verbs | agent_workflows/cli.py:1624-1631,3675-3680,21149-21177,21469-21565 (`_dispatch`, `expand_host_review_argv`); agent_workflows/run_dispatch.py:24-30; `m7jcis` E-05; `e36q6r` E-02 | Original `E-01` attached `selectors.add_selector_args` and `--model`/`--variant` in `cli.py`, contradicting `e36q6r` (driver-side selectors), `m7jcis` E-05 (`dispatch_for_state` never injects `--model`/`--variant`), and `cli.py`'s pre-`parse_args` `REMAINDER` forwarding (preventing `--agent` collisions and leading-flag drops). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Rewrote `E-01` and Mermaid diagram to use thin `add_help=False` + `REMAINDER` parsers with pre-`parse_args` interception peeling only `--host` and `--as`, handling leading `--help` without `default_runner`, and forwarding the verbatim tail to `dispatch_for_state` (`D-2`). Recommendation strength: very strong. |
| PR-005 | HIGH | IN-SCOPE | R3 / R4 / `aw approve` attestation gate, selector-only targets, and guard integration | agent_workflows/status_set.py:1117-1134,1239-1246,3235-3455; `mnlaoa` E-09; `9ifwdx` E-06; `55tt85` E-01/E-02; `xocj8i` E-02:57-59 | `status_set.py` auto-attests TTY on specs only (not plans), does not enforce required `--message` on non-interactive approvals, and refuses empty positional targets (breaking `xocj8i`'s own `aw approve -s reviewed --sid <set>` example). | C:Low; U:Medium; S:Medium; F:Medium; Overall:Medium | FIXED | Rewrote `E-02` to register `p_approve` with `dest_prefix="sel_"`, `--accept-stale`, `--allow-unreviewed`, `--allow-open-questions`, `--commit`/`--no-commit`, enforce `ogd2nv` R-16 TTY-vs-non-TTY `--by-human` + `--message` before writes, and expand selector-only targets across plans and specs before calling `status_set.run_set_command` (`D-3`). Recommendation strength: very strong. |
| PR-006 | HIGH | UNDER-SCOPE | R2 / R4 / R7 / Missing `conformance_matrix.py`, `CHANGELOG.md`, static completion flags, and `p06t7i` boundary | tests/conformance_matrix.py:531,552,578; tests/test_command_surface_declarations.py; tests/test_agent_surface_conformance.py; `e36q6r` E-04 (`SELECTOR_FLAG_SPELLINGS`); `p06t7i` E-03; `CHANGELOG.md` | Adding five new top-level commands without `tests/conformance_matrix.py` exemptions breaks `test_agent_surface_conformance.py`; `REMAINDER` runner verbs need `e36q6r`'s static selector completion list to keep `<250ms` latency; `CHANGELOG.md` was omitted; and `p06t7i` E-03 already owns `show`/`reviews` `command_surface.py` parity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/conformance_matrix.py` and `CHANGELOG.md` to `- Scope-Paths:`, wired `e36q6r`'s static selector spellings into `E-03`, and scoped `command_surface.py` to the five new verbs without duplicating `p06t7i`. Recommendation strength: very strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / R4 / Unqualified post-cutover spec citations, coarse E-04, validation, and gate | `xocj8i` front matter (`- From-Spec: ogd2nv`), E-01..E-04, Required tests:105-107, gate:146 | Missing qualified `ogd2nv R-12..R-16` / `AC-06` citations; E-04 bundled new tests with whole-Set validation; `Required tests` omitted bare `python3 -m pytest`, parity/conformance suites, and `--agent` on `aw sanitize`; gate lacked resolved-OQ, scope-fence, honesty, and conditional `AW_EXECUTION_ROLE=worker` vs standalone `aw ipd finalize` clauses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified all `ogd2nv` citations, split `E-04` (tests) and `E-05` (whole-Set validation), expanded `Required tests / validation`, and added the full execution contract to `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-008 | LOW | IN-SCOPE | P / Technical writing polish, `path::Symbol` citations, and Mermaid flowchart sync | `xocj8i` throughout; `.aw/system/workflows/technical-writing/technical-writing.md` | Missing `path::Symbol` citations and Mermaid flowchart out of sync with pre-`parse_args` forwarding, `ACTION_IMPLEMENTED`, and `OQ-01`/`OQ-02` gates. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Normalized `path::Symbol` citations, synchronized the Mermaid flowchart, and verified zero em or en dashes. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`, `Scope-Paths`, `Highest E allocated`) | 9 Scope-Paths, 4 E-items, no `runner_shared.py`, `conformance_matrix.py`, `test_oc_runipd.py`, or `CHANGELOG.md` | 13 Scope-Paths, 5 E-items, `--action execute` enablement, `OQ-01`/`OQ-02` gates, `- Status: reviewed`, `- Readiness: no-go`, `- Review-Depth: complex` | PR-001..PR-007 |
| `## Goal`, Mermaid flowchart, `E-01..E-05`, `V-01..V-05` | Coarse 4 items attaching selectors in `cli.py`, omitting R-16 mechanics and `conformance_matrix.py` | Common rules, pre-`parse_args` forwarding, `--action execute` in `runner_shared.py`, full `aw approve` R-16 + selector expansion, static completions + declarations + conformance + changelog, split E-04/E-05 with qualified `ogd2nv` citations | PR-003..PR-008 |
| `## Project conventions`, `## Findings`, `## Proposed changes`, `## Open questions`, `## Required tests`, `## Approval and execution gate` | "None" open questions, 3 narrow validation commands, one-line gate | Documented `ACTION_IMPLEMENTED`, missing `validate` backend, `m7jcis` `agy` handoff, escalated `- Blocking: yes` `OQ-01` (`- Finding: PR-001`) and `OQ-02` (`- Finding: PR-002`), full validation suite, and full execution contract | PR-001..PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| I-01 | `E-01`, `OQ-01` | No standalone `--action validate` (`/verify-execution` on executed plans) exists in `runner_shared.py`, `oc_runipd.py`, or `agy_runipd.py` | Maintainer scope decision: split standalone `--action validate` driver support into its own plan, expand `xocj8i` to build it across both drivers, or forward to one-shot `aw oc/agy prompt` | Split standalone `--action validate` driver support into its own dedicated plan and keep `xocj8i` as the thin CLI wrapper | strong |
| I-02 | `E-01`, `OQ-02` | `run_dispatch.RUNNER_ADAPTERS` is OpenCode-only and `m7jcis` deferred the `agy` adapter decision to `xocj8i` | Maintainer scope decision: add the `agy` dispatch adapter (`run_dispatch.py` + `agy_runipd.py`) before/in `xocj8i`, or ship OpenCode-only dispatch with a follow-up backlog carrier | Add a dedicated prerequisite child plan for the `agy` dispatch adapter and `agy_runipd.py` `as <profile>` support before `xocj8i` | strong |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `aw exec` avoid hitting `"--action execute is not implemented yet"`? | Enable `"execute"` in `runner_shared.ACTION_IMPLEMENTED` (accepting derived `execute` and `orchestrate` in `enforce_requested_action`) and update `tests/test_oc_runipd.py:5583-5606`. | Omit `--action execute` from `aw exec` (rejected: would allow `aw exec <to-review-id6>` to review a plan instead of refusing, violating `ogd2nv` R-13 and spec `25kzda` 2.6). | `agent_workflows/runner_shared.py:39646,40580-40599`; `tests/test_oc_runipd.py:5581-5606`. | yes |
| D-2 | How should `aw review`/`exec`/`plan`/`validate` parse options in `cli.py`? | Register `add_help=False` + `argparse.REMAINDER` parsers and intercept in `_dispatch` before `parse_args`, peeling only `--host` and `--as` and forwarding the rest verbatim to `run_dispatch.dispatch_for_state`. | Register `selectors.add_selector_args` and `--model`/`--variant` in `cli.py` (rejected: duplicates driver parsing, collides with OpenCode `--agent`, and breaks `REMAINDER` leading options). | `agent_workflows/cli.py:1624-1631,21469-21565`; `agent_workflows/run_dispatch.py:24-30`; `m7jcis` E-05; `e36q6r` E-02. | yes |
| D-3 | How should `aw approve` handle selector-only invocations like `aw approve -s reviewed --sid <set>` and R-16 non-TTY rules? | Enforce R-16 (`--by-human` + non-empty `--message` on non-TTY/`--agent`/`--json`; auto `--by-human` on TTY) up front, and expand selector-only flags across plans and specs before calling `status_set.run_set_command`. | Pass empty targets to `run_set_command` (rejected: exits 2 with `"at least one target selector is required"`) or rely on `status_set`'s spec-only TTY check (rejected: does not cover plans or require `--message`). | `agent_workflows/status_set.py:1117-1134,3235-3455`; `mnlaoa` E-09; `ogd2nv` R-16. | yes |
