# Review findings: ipd kbh055

- Subject-Id: kbh055
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran non-interactively in an isolated review-sweep lane worktree (run `run-20261124T195117Z-1319864`, HEAD `7af52b8ac`). The target plan `.aw/records/plans/pending/20261121-b1j6bl-01-kbh055-preserve-concern-and-scope-bullets-in-fixture-codemod-plan-s.ipd.md` was committed and unmodified (last commit `454131249`), so no pre-review snapshot commit was made. Before and after edits, `aw ipd lint --phase author --agent` returned `clean` with zero findings.

The review read backlog item `b1j6bl` (graduated, `Work-Kind: bug`, `Blocks-Release: next`), `tools/fixture_codemod.py::_plan_site` (the `norm in ("concern", "scope") and inferred_type == "ipd": continue` branch), `ModuleResult.totals`, `analyze_module`, `apply_rewrites_to_source`, `tests/record_builder.py::RecordBuilder.plan` and `_apply_raw_fields`, `agent_workflows/ipd_authoring.py::_AUTHORING_PLACEHOLDERS` and `authoring_placeholders_resolved`, `agent_workflows/ipd_lint.py::lint_text`, `LintResult`, `_draft_ready_advisory`, and `C_DRAFT_READY`, `tests/test_fixture_codemod.py`, `tests/test_fixture_codemod_slow.py`, `tests/slow_allowlist.txt`, and executed plans `j2xjtt`, `n0li9v`, and `59aiyh`. Scratch probes under `/tmp/opencode/kbh055/` (no repository writes) measured:

- The defect reproduces: on a four-site fixture (static IPD, lowercase-label plus f-string IPD, `Status: EXECUTED` IPD, spec), unpatched `_plan_site` emits empty `raw_fields` for the IPD sites, and a subprocess `--apply` refuses all three IPD sites as `not-equivalent`.
- The one-branch fix (`raw_fields_code[{"concern": "Concern", "scope": "Scope"}[norm]] = vexpr.code`) yields `raw_fields` `{'Concern', 'Scope'}` with `rewrite_class` `standard`, `{'Status', 'Concern'}` with `invalid-input` on the invalid sibling, leaves the spec site refused `unsupported-shape`, and a subprocess `--apply` reports `rewrites 3, refusals 1, not-equivalent 0, equivalent True`.
- A literal IPD with real values but no body headings lints `error` (`IPD-H202` x8, `IPD-Z601`), while its skeleton-built rewrite lints `conforming`. Both carry the `check.ipd-draft-ready-to-review` advisory.
- `RecordBuilder().plan(..., raw_fields={"Concern": "", ...})` renders `- Concern: ` (the overwrite path works with an empty value too).
- `tests/test_fixture_codemod.py` baseline: `11 passed in 7.96s` under `-n 0`; each subprocess case costs about 1.1 s.
- `git grep -l -E '"- (Concern|Scope): '` over `tests/test_*.py`: 54 modules at authoring commit `39400b74c`, 6 at HEAD. All 8 codemod sites in those 6 modules refuse for unrelated reasons (`legacy-format subject`, `setter-byte assertion`).
- `aw sanitize --agent` at HEAD: `clean`, 7188 files checked.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Step T

1. No: no spec, CLI flag, refusal reason code, or file format changes; the codemod's JSON report gains `raw_fields` entries it already supports.
2. No: none of the guard modules is touched; the change is one branch in a standalone maintenance tool plus tests.
3. Moderately: 4 E-items, one production branch, a new fixture, and edits to two test modules and the slow allowlist.
4. Yes: `- Scope-Paths:` lists every file; it covers the fallback move into the slow module that E-02 item 3 allows.
5. Low to medium: a wrong mapping would make codemod rewrites diverge from the original literals, but the apply-time equivalence proof refuses any such site.

Tier: standard.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | "34 test modules (45 IPD rewrite sites measured on `HEAD`)" | 54 modules at `39400b74c`, 6 at HEAD with all 8 sites refused for other reasons; the defect stays live for future runs | PR-004 |
| E-01 | No instruction for the stale branch comment; non-IPD check unstated | Replace the comment; spec `- Concern:` still refuses `unsupported-shape` | PR-007 |
| E-02 item 1 | Fixture asserted `lint_text(...).disposition == "conforming"`; fixture tests' execution path unstated | Four exact sites with assertions that hold on literal and rewrite; `conforming` forbidden on a heading-less literal; fixture runs only under E-03 | PR-001, PR-003 |
| E-02 item 2 | Unspecified mix of dry-run and in-process tests | One dry-run subprocess call with exact totals and per-site assertions, plus one rendered-text test | PR-005 |
| E-02 item 3 | Bound only confirmed | Fallback to the slow module per `j2xjtt` if the bound is exceeded | PR-005 |
| E-03 | `totals["rewrites"] == 2`; one `rewrite_class` for all sites | `rewrites == 3`, `refusals == 1`, per-site classes; nested pytest shaped like `test_case_h` | PR-002 |
| E-04 | Ran pre-transition lint inside the item it gates; "lint" in outcome | Lint and finalize moved to the gate clause; typecheck labeled no-regression | PR-006 |
| Project conventions | Single baseline | Adds the review measurement and `j2xjtt` E-09 | PR-005 |
| F-04 | 34 modules, 45 sites, now-rewritten examples | Measured counts at both commits and their refusal reasons | PR-004 |
| Ordered changes 4, flowchart, Required tests | Pre-transition lint among the E-04 gates | Lifecycle gate listed separately | PR-006 |
| Deferred row 1 | "the 34 repository test modules" | "already done by hand for most of them" | PR-004 |
| V-02, V-03, V-04 | Vague assertion demands; V-04 demanded pre-transition lint `clean` | Exact assertion lines and counts; V-04 drops the lint demand | PR-002, PR-005, PR-006 |
| Gate POST-GATE LIFECYCLE | Finalize without `aw ipd begin` | Runner owns begin and finalize; standalone executor runs begin, then the work commit, then finalize | PR-006 |

#### Issues

- None remaining. Lint reports zero findings after revision; the plan contains no em or en dashes.

### Step R1

- Checked: every cited symbol exists at HEAD: `_plan_site`, `_parse_bullet_site`, `_template_to_value_expr`, `_is_known_ipd_non_skeleton_role`, `F01_PATTERN`, `ModuleResult.totals`, `analyze_module`, `apply_rewrites_to_source`, `RecordBuilder.plan`, `_apply_raw_fields`, `set_legacy_bullet_line`, `build_skeleton`, `_AUTHORING_PLACEHOLDERS`, `authoring_placeholders_resolved`, `lint_text`, `C_DRAFT_READY`, `_draft_ready_advisory`, `check_engine.check_ipd_draft_ready`. Executed plan `59aiyh` exists at the cited `Carrier-Evidence` path; backlog items `e0wwtc` and `lufe6m` exist.
- F-04 and the Concern reported 34 modules and 45 sites. Neither number reproduces: the counts are 54 at authoring and 6 at HEAD, and no HEAD site reaches `_plan_site`'s rewrite path (PR-004).

### Step R2

- Checked: E/V bijection 4/4; `Highest E allocated: 04` unchanged; dependencies E-01 -> E-02 -> E-03 -> E-04 are acyclic. `From-Backlog: b1j6bl`, `Work-Kind: bug`, and `Blocks-Release: next` match the backlog item.
- E-02 item 1 demanded `disposition == "conforming"` on a fixture literal; a literal that lacks body headings lints `error` while its rewrite lints `conforming`, so the demand either fails on the original or forces a `not-equivalent` refusal (PR-001).
- E-03 demanded `totals["rewrites"] == 2` and one `rewrite_class == "standard"` while E-02 requires an invalid-sibling site and a non-IPD site in the fixture (PR-002).
- The plan put assertions inside a `.py.txt` fixture without saying that only E-03's apply proof and nested pytest execute them (PR-003).
- E-04 ran `aw ipd lint --phase pre-transition` inside the item whose `pending` state makes that lint refuse, and ordered `aw ipd finalize` without `aw ipd begin` (PR-006).

### Step R3

- Checked: no new subprocess, filesystem, network, or untrusted-input surface. `vexpr.code` is the same expression source the branch already emits for other `raw_fields` entries; the apply-time proof still reverts any non-equivalent site. No security finding.

### Step R4

- Checked (KISS): the fix is one branch body; declining new `RecordBuilder.plan` keyword parameters and an `F01_PATTERN` change is justified by repository evidence (`tests/test_finalize_sendback.py`, `tests/test_attention.py` already pass `raw_fields={"Concern": ...}`).
- Checked (performance): `tests/test_fixture_codemod.py` has about 2 s of headroom under its 10-second serial bound, enough for one more subprocess call; E-02 now allows exactly one and names the fallback (PR-005).
- Checked (code pinning): the `rg -n "inspect\.|getsource"` checks are hygiene greps over test files, not tests that read production source. Evaluating the codemod's emitted `replacement` string is an output assertion and complies with P16.
- E-01 left the branch comment `# Template-owned IPD skeleton bullets (not in REGISTRY["ipd"]).`, which would misdescribe the new behavior (PR-007).

### Step S5

- Checked: no question needs a human. OQ-01 stays resolved; every revision rests on measured repository behavior.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | G executability | Probe: heading-less literal lints `error` (`IPD-H202` x8, `IPD-Z601`); skeleton-built rewrite lints `conforming` | A fixture assertion of `disposition == "conforming"` fails on the original literal or forces a `not-equivalent` refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 item 1 forbids it unless the literal carries every required heading; the fixture asserts `C_DRAFT_READY` among advisories instead. |
| PR-002 | MEDIUM | IN-SCOPE | V correctness | Probe on the four-site fixture: `rewrites 3, refusals 1, not-equivalent 0`; `ModuleResult.totals` | `totals["rewrites"] == 2` and a single `standard` class contradict the fixture E-02 requires. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 assert `rewrites == 3`, `refusals == 1`, and per-site classes. |
| PR-003 | LOW | IN-SCOPE | G executability | `tests/test_fixture_codemod_slow.py::test_case_h_rewritten_fixture_module_tests_pass` runs the rewritten fixture under nested pytest; the core module never imports `.py.txt` fixtures | The plan did not say which step executes the fixture's own assertions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 item 1 states that only E-03's apply proof and nested pytest run them. |
| PR-004 | LOW | IN-SCOPE | R1 references | `git grep` for `"- Concern: "` or `"- Scope: "` literals over `tests/test_*.py`: 54 at `39400b74c`, 6 at HEAD; `analyze_module` refuses all 8 HEAD sites for other reasons | "34 test modules (45 IPD rewrite sites measured on HEAD)" does not reproduce and overstates current impact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, F-04, and deferred row 1 carry the measured counts and state the defect is live for future runs. |
| PR-005 | LOW | IN-SCOPE | Performance / testability | `11 passed in 7.96s`; each subprocess case about 1.1 s; `j2xjtt` E-09 fallback rule | Unbounded new dry-run calls could breach the 10-second bound; assertions were unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 item 2 allows one subprocess call with exact assertions; item 3 names the slow-module fallback. |
| PR-006 | MEDIUM | IN-SCOPE | Lifecycle | `aw ipd finalize --help` ("Validates the matching `aw ipd begin` receipt"); pre-transition lint refuses a `pending` E-item | E-04 ran pre-transition lint on itself and the gate ordered finalize without begin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lint and finalize moved to POST-GATE LIFECYCLE: runner-owned under `aw oc run`/`aw agy run`; otherwise begin, work commit, finalize. |
| PR-007 | LOW | IN-SCOPE | Maintainability | `_plan_site` comment `# Template-owned IPD skeleton bullets (not in REGISTRY["ipd"]).` | The stale comment would misdescribe the fixed branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 replaces it and states the spec-refusal invariant. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What should the fixture assert about lint? | `C_DRAFT_READY` among advisories plus `authoring_placeholders_resolved` | `disposition == "conforming"` (rejected: literal and rewrite disagree) | Probe; PR-001 | yes |
| D-2 | How many subprocess calls may the core module add? | One `--dry-run`, with the slow-module fallback | Several (rejected: about 2 s headroom) | Baseline timing; PR-005 | yes |
| D-3 | Review tier | standard | simple, deep | Step T answers 3 and 5 | yes |

### Plans reviewed and not reviewed

- ELIGIBLE: kbh055 (reviewed; APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED)
- NOT REVIEWED: (none)
