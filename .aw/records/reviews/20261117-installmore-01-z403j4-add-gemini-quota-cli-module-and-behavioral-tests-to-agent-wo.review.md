# Review findings: ipd z403j4

- Subject-Id: z403j4
- Subject-Type: ipd
- Reviewed-At: 2026-11-18
- Reviewer: antigravity/gemini-4-hydrogen-high
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran at HEAD `4f4bd0cb8` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`exit: 0`, `2` non-blocking `info` `IPD-C802` advisories on the boilerplate validation rule), while `aw ipd lint --phase review-finalize --agent --verbose` exited `1` with error `check.ipd-uncarried-obligation` on the two deferred rows. Inspection against `pyproject.toml`, `.github/workflows/tests.yml`, `.pre-commit-config.yaml`, `conftest.py`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, `agent_workflows/agy_models.py`, `agent_workflows/term.py`, `agent_workflows/leak_sanitizer.py`, sibling plans `5qqgfb` / `58isyp`, and a repo-wide search for quota symbols produced findings PR-001..PR-006. PR-002..PR-006 were fixed in place; PR-001 cannot be answered from repository evidence and is escalated as blocking `OQ-02` (`questions[]` in `02-z403j4.json`) to await maintainer input.

### Proofreading

Checked `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Workflow history | `to-review` and `draft` lines only | Prepended `review progress` entry noting Round 1 PR-002..PR-006 revisions and blocking `OQ-02` | `steps/s6-rereview.md` non-verdict progress rule while parked `awaiting-human`. |
| E-01, E-02, Project conventions | Omitted Python 3.9 constraints, R3 security/atomicity guardrails, `--file` history/fallback isolation, and `supports_color` env rules | Added `from __future__ import annotations`, `datetime.timezone.utc`, cross-platform `/tmp` fallback, trust-boundary safety, atomic `HISTORY_PATH` writes, and `--file` isolation | PR-003, PR-004, Compatibility / Security / Reliability. |
| E-03, E-04, Required tests, V-02..V-04 | Omitted `pytestmark = pytest.mark.core`, bounded `--watch` test, and direct `mypy`/`ruff` checks in V-04 | Required `pytestmark = pytest.mark.core`, fast in-process calls, bounded `--watch` test, and direct `mypy`/`ruff` commands in E-04 / V-04 / Required tests | PR-003, PR-005, Core-tier and static-gate coverage. |
| Proposed changes diagram | Linearized `--file` through `record_history_sample` and omitted `--watch` loop | Branched `--file` to `load_history_samples` without live history write and added `--watch` loop edge | PR-004, Technical Writing Standard Requirement 12(d)/(e). |
| Deferred / out of scope | Two rows with no durable carriers | Added `- Carrier: 58isyp` (row 1) and `- Carrier-Declined:` (row 2) | PR-002, `check.ipd-uncarried-obligation` compliance. |
| Scope check | Claimed `Under-scope: none` | Recorded `PR-001` (`OQ-02`) pending maintainer schema/refresh specification | PR-001, `technical-writing.md` Requirement 10. |
| Open questions | Only resolved `OQ-01` | Added `OQ-02` (`Blocking: yes`, `Status: open`, `Owner: maintainer`, `Finding: PR-001`) | PR-001 escalation per `steps/s5-questions.md`. |
| Approval and execution gate | Unconditional `aw ipd finalize` prose without execution contract | Replaced with full execution contract (`OQ-02` gate, scope fence, safety stop, evidence honesty, path-scoped `aw commit`, conditional runner/executor finalize) | PR-006, `steps/s7-finalize.md` execution-contract rules. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
| I-01 | `E-01`, `E-02`, `OQ-01` | `z403j4` does not define the JSON schema of `/tmp/antigravity_quota.json` / `last_quota.json`, the live `refresh_quota` mechanism, the `quota_history.json` / `--json` keys, or `--context` semantics, yet `OQ-01` permits autonomous execution without out-of-lane reads. | Maintainer must either supply the exact Antigravity quota/history/`--json` schemas, `refresh_quota` protocol, and `--context` behavior (or pre-seed `agent_workflows/gemini_quota.py` on `main`), or explicitly approve a greenfield synthetic-compatible schema with cache-only/no-op live refresh. | Supply the real Antigravity quota payload schema, `refresh_quota` protocol, and `--context` behavior (or pre-seed the module on `main`) so `gemini-quota` works against live Antigravity files. | strong |

### Step T

1. Yes. Introduces a new runnable Python CLI module (`python3 -m agent_workflows.gemini_quota`) with flags (`--bar`, `--gemini`, `--3p`, `--json`, `--watch`, `--max-staleness`, `--no-color`, `--color`, `--plot`, `--context`, `--file`) and library functions consumed by sibling plan `58isyp`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact child plan with 4 execution items in 1 task group and 3 scope paths.
4. Yes. `- Scope-Paths:` lists `agent_workflows/gemini_quota.py`, `tests/test_gemini_quota.py`, and this plan file.
5. Yes. Installing/packaging a broken quota schema, leaking credentials/tokens, corrupting `quota_history.json`, or dropping Python 3.9 / core-tier compatibility would break users or CI gates.

AW-TIER: standard

### Step R1

- Checked: `.aw/records/plans/pending/20261117-installmore-00-5qqgfb-package-gemini-quota-and-add-opt-in-aw-install-more-with-dis.ipd.md`, `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md`, `pyproject.toml`, `.github/workflows/tests.yml`, `.pre-commit-config.yaml`, `Makefile`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, `conftest.py`, `agent_workflows/term.py`, `agent_workflows/agy_models.py`, `agent_workflows/leak_sanitizer.py`, `agent_workflows/check_engine.py`, `agent_workflows/ipd_lint.py`, and `tests/test_agy_models.py`.
- Checked: Repo-wide `rg` search for `remainingFraction`, `last_quota`, `quota_history`, `burn_forecast`, `analyze_bucket`, `format_single_status_bar`, and `antigravity_quota` returned zero matches outside `z403j4`.

### Step R2

- Checked: 1:1 bijection between `E-01..E-04` and `V-01..V-04`; `- Scope-Paths:` completeness; `- Item-Dependencies: none`; concrete evidence in `V-01..V-04`; runtime-demonstration reachability; and durable carriers on `## Deferred / out of scope` (`check.ipd-uncarried-obligation` fixed by PR-002).

### Step R3

- Checked: Security and privacy across trust boundaries (`refresh_quota` outbound calls, external cache/fixture JSON, `quota_history.json` atomic writes, `subprocess` usage, terminal ANSI/control-char sanitization, secret/token non-exposure, and offline test isolation). Hardened `E-01`/`E-02`/`E-03` via PR-004.

### Step R4

- Checked: Engineering rubric, Python 3.9–3.14 / Windows compatibility, `@pytest.mark.core` tier selection (`conftest.py::pytest_collection_modifyitems`) and `>2s` slow-allowlist compliance, `mypy` / `ruff` gate parity with `V-04`, and right-sizing (4 E-items, 1 task group, 3 Scope-Paths). Identified missing schema/protocol architecture in PR-001.

### Step S5

- Checked: Pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`). Added blocking `OQ-02` (`Blocking: yes`, `Status: open`, `Owner: maintainer`, `Finding: PR-001`) and emitted corresponding gating question in `questions[]` of `.aw/state/lane-submissions/run-20261118T041454Z-805005/02-z403j4/attempt-1/outcomes/02-z403j4.json`. Recorded autonomous reversible decisions `D-1..D-5` in `### Decisions`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | HIGH | UNDER-SCOPE | Architecture / Executability (`r4-engineering.md`, `askme.md`) | `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md:36-44,110-115` (`E-01`, `E-02`, `OQ-01`) | `OQ-01` authorizes an autonomous lane (with no out-of-lane reads) to implement `agent_workflows/gemini_quota.py` from `z403j4` alone, yet `z403j4` omits the JSON schema for `/tmp/antigravity_quota.json` and `last_quota.json`, the live `refresh_quota` protocol/source, the `quota_history.json` / `--json` schemas, and `--context` semantics (none of which exist anywhere in the repo). | C:Medium; U:High; S:Low; F:High; Overall:High | OPEN | Escalated to maintainer as `OQ-02` (`- Blocking: yes`, `- Finding: PR-001`) and recorded in `questions[]` (`gates_verdict: true`). Recommendation strength: strong — supply the real Antigravity schema/refresh specification (or pre-seed `gemini_quota.py` on `main`) rather than letting an executor invent an incompatible schema. |
| PR-002 | HIGH | IN-SCOPE | Governance / Durable Carriers | `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md:88-92` (`## Deferred / out of scope (with reason)`) | `aw ipd lint --phase review-finalize` exited 1 with `check.ipd-uncarried-obligation` because neither deferred bullet carried `- Carrier:`, `- Carrier-Evidence:`, or `- Carrier-Declined:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Carrier: 58isyp` to row 1 and `- Carrier-Declined:` with explicit rationale to row 2. Recommendation strength: strong. |
| PR-003 | HIGH | IN-SCOPE | Compatibility / Python 3.9 & Core Test Tier | `pyproject.toml:12`; `.github/workflows/tests.yml:35,84-85`; `conftest.py::pytest_collection_modifyitems:130-161` | `E-02` specifies `list[str] \| None` without requiring `from __future__ import annotations` or Python 3.9–3.14 / Windows compatibility, and `E-03` omits `pytestmark = pytest.mark.core` (causing bare `python3 -m pytest` to deselect `tests/test_gemini_quota.py` and leaving `gemini_quota.py` uncovered in the core gate). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `from __future__ import annotations`, `datetime.timezone.utc`, and Windows `/tmp` fallback requirements to `E-01`/`E-02`/`Project conventions`, and required `pytestmark = pytest.mark.core` and fast in-process test calls in `E-03`/`V-03`. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | Security, Atomicity & Side-Effect Isolation | `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md:36-49,73-82` (`E-01`..`E-03`, `Proposed changes`) | `--file` was shown flowing through `record_history_sample` (mutating live `HISTORY_PATH`), missing `--file` fallback behavior was unspecified, `--watch` lacked test coverage, and `E-01` omitted atomic writes, `https://`/loopback + timeout guards on `urllib`, `shell=False` on `subprocess`, control-char sanitization, and secret non-exposure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01`, `E-02`, `E-03`, `V-02`, `V-03`, and the Mermaid flowchart to isolate `--file` from live history writes and fallback refresh, require R3 security/atomicity guardrails, and add a bounded `--watch` test. Recommendation strength: strong. |
| PR-005 | MEDIUM | IN-SCOPE | Testing / Verification Alignment | `.pre-commit-config.yaml:120-125` (`static-type-gate-commit`); `Makefile:10-11` (`typecheck`) | `E-01` and `E-04` claim `mypy` and `ruff` pass, whereas `V-04` only checked `pre-commit run --files ...` (whose `static-type-gate-commit` inspects the staged index via `git write-tree`, skipping unstaged `--files` targets). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-04`, `Required tests / validation`, and `V-04` to run `python3 -m mypy agent_workflows`, `ruff check`, `ruff format --check`, and `aw check-local-leaks` directly alongside `pre-commit` and `pytest`. Recommendation strength: strong. |
| PR-006 | MEDIUM | IN-SCOPE | Governance / Execution Gate | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`; `.aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md:141-146` | `## Approval and execution gate` unconditionally instructed `aw ipd finalize` and omitted the execution-contract clauses (open-questions status, scope fence, safety stop, evidence honesty, path-scoped `aw commit` / never-push, conditional finalize ownership). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced gate prose with the full execution contract. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | How should `z403j4` satisfy `check.ipd-uncarried-obligation` on `## Deferred / out of scope`? | Add `- Carrier: 58isyp` to row 1 and `- Carrier-Declined:` with explicit opt-in design rationale to row 2. | Mark both `- Carrier-Declined:` (inaccurate for row 1, which `58isyp` actively implements). | `agent_workflows/check_engine.py::evaluate_carrier_obligation:10074-10190`; `58isyp` | yes |
| D-2 | How should Python 3.9–3.14 and core-tier requirements be enforced for `gemini_quota.py` and `tests/test_gemini_quota.py`? | Require `from __future__ import annotations`, `datetime.timezone.utc`, graceful missing-`/tmp` handling, `pytestmark = pytest.mark.core`, and fast in-process CLI calls. | Leave Python 3.9 and core-tier marking unspecified (fails CI Python 3.9 leg or leaves `gemini_quota.py` deselected by bare `pytest`). | `pyproject.toml:12`; `.github/workflows/tests.yml:35,84-85`; `conftest.py::pytest_collection_modifyitems:130-161` | yes |
| D-3 | Should `--file` mutate `HISTORY_PATH` or fall back to `refresh_quota` when unreadable? | No: `--file` reads only the named path without falling back to cache/refresh and does not write live `HISTORY_PATH`. | Allow `--file` to write `~/.gemini/antigravity-cli/quota_history.json` or fall back to cache (corrupts user history during fixture inspection). | `z403j4` `E-02`, `E-03`; `steps/r3-security.md` | yes |
| D-4 | How should `V-04` verify `mypy` and `ruff` claims from `E-01` and `E-04`? | Run `python3 -m mypy agent_workflows`, `ruff check`, and `ruff format --check` directly in addition to staged `pre-commit` and `aw check-local-leaks`. | Rely solely on `pre-commit run --files ...` (skips `static-type-gate-commit` on unstaged files). | `.pre-commit-config.yaml:120-125`; `Makefile:10-11` | yes |
| D-5 | How should `## Approval and execution gate` specify lifecycle transition and execution rules? | Include the full execution contract with conditional runner/executor `aw ipd finalize z403j4` ownership (`never a hand git mv` to `executed/`). | Keep unconditional `aw ipd finalize` prose (violates `steps/s7-finalize.md`). | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | yes |
