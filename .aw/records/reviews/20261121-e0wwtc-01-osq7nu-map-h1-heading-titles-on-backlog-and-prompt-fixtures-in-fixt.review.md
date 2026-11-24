# Review findings: ipd osq7nu

- Subject-Id: osq7nu
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at local HEAD `4e6ee9406` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-e0wwtc-01-osq7nu-map-h1-heading-titles-on-backlog-and-prompt-fixtures-in-fixt.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is Order 1 of Set `e0wwtc`, graduated from backlog `e0wwtc` (`Work-Kind: bug`, `Status: graduated`), and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The central result: the approach is sound and every code claim in the plan matched `tools/fixture_codemod.py` and `tests/record_builder.py` at HEAD. Two rewrite shapes the plan did not cover would still emit a wrong replacement (F1, F2), and one of them occurs in a live test module today. The test work was one oversized E-item and is now two (F3).

AW-TIER: standard

### Step T

- Checked: the five tier questions in `steps/t-tier.md`.

1. No: no command-line flag, refusal reason code, or spec text changes. `tools/README.md` does not document H1 handling.
2. No: the plan changes test tooling (`tools/fixture_codemod.py`) and tests only.
3. No: five E-items after the split, five Scope-Paths, no sandbox or commit-guard code.
4. Yes: `- Scope-Paths:` is present and covers every file the E-items edit.
5. Low: a wrong rewrite is caught by the codemod's own per-module pytest equivalence proof, which reverts a breaking site.

`AW-TIER: standard`

### Step R1

- Checked: `tools/fixture_codemod.py::_parse_bullet_site` (skips a leading `# ` line), `_plan_site` step 5 (type inference), step 7 heading-title handling (`ipd`/`spec` to `title`, `release` to `version` via `setdefault`), the field loop (`summary` and `short-description` labels map through `_registry_field_map`), and the body branch (`# Release:` and `# Walkthrough:` prepends); `_infer_type_from_template` (returns `""` for titleless headings, `None` for no match); `_template_to_value_expr` (a whole-value single placeholder returns the bare expression); `_PROMPT_COMMENT_SITE_RE`; `tests/record_builder.py::RecordBuilder.backlog` (`summary="Demo backlog item"`, no H1) and `RecordBuilder.prompt` (`short_description="Demo staged prompt"`, `# Prompt: {short_description}\n\nPrompt body.\n` when `body is None`).
- Found F1: for `f"# Backlog Item {idx}\n\n..."`, `_infer_type_from_template` returns the title as one bare placeholder, so `_template_to_value_expr` yields `idx` and the planned `setdefault("summary", title_vexpr.code)` emits `summary=idx`. `RecordBuilder().backlog(id6="bkl001", summary=1, status="open", text_only=True)` raised `AttributeError: 'int' object has no attribute 'strip'`. The live site `tests/test_partition_set_cohesion.py::test_partition_split_sets_for_backlog` has this exact shape with an `int` `idx`. The equivalence proof would revert it as `not-equivalent`, so the bug the plan fixes would recur on the one live titled site. Fixed: E-01 step 3 wraps a bare placeholder as `str(<expr>)` (or `format(<expr>, '<spec>')`), E-05 case (j) tests it, and E-03 expects `summary=str(bkl_tag)`.
- Found F2: a bullet-dialect prompt with an H1 and no `## ` section gets no `body`, so `RecordBuilder.prompt` renders `# Prompt: {short_description}\n\nPrompt body.\n`. A probe rendered `short_description="Audit cache parity"` as `# Prompt: Audit cache parity` followed by `Prompt body.`, which changes a path-inferred `# Audit cache parity` heading and adds text. Fixed: E-01 step 4 emits `body=<raw_h1_line>` in that case; E-05 case (e) asserts it; the flowchart shows the third branch.
- Found F5: the F-04 census (23 sites, naming `tests/test_readers_attention.py`, `tests/test_status_set.py`, and others) is stale. Re-running `analyze_module` over all 784 `tests/test_*.py` modules (0 errors) found 7 backlog or prompt rewrite sites, of which only one carries a non-empty H1 title (the F1 site). Fixed: F-04 now records the re-measure and says the regression tests, not the live corpus, carry the proof.

### Step R2

- Checked: the E/V bijection, `Depends on` edges, Scope-Paths completeness, the right-sizing rule, the 10-second serial budget of `tests/test_fixture_codemod.py`, and whether each V-item demands concrete evidence.
- Found F3: E-02 bundled two files and about eleven test cases (the fixture module, its own CLI and reader assertions, and the in-process core tests), and V-02 checked them together. That breaks the one-step-per-E-item rule the plan itself states. Fixed: E-02 is now the fixture module alone; new E-05 holds the core tests; V-02 and new V-05 check each with its own evidence; E-03 depends on E-01 and E-02, and E-04 on E-03 and E-05.
- Found F4: E-02 said the fixture's tests should assert that `search` and `read_text` "observe the preserved H1 titles", without naming outcomes. The fixture's own tests are the only thing that makes E-03's equivalence proof fail before E-01, so they must be discriminating. Fixed: E-02 names the measured outcomes (below), requires exactly three record literals (E-03 asserts `totals["sites"] == 3`), and forbids `ALPHA_SECRET` or `BETA_BODY` in filenames so a hit can only come from record text.
- Found F6: E-02 called `analyze_module` and `apply_rewrites_to_source` in process without saying how to import a module from `tools/`, which has no `__init__.py`. Fixed: E-05 names `from tools import fixture_codemod`, the pattern `tests/test_dead_status_token_scan.py` already uses.
- Budget: `python3 -m pytest -o addopts="" -n 0 -q --durations=3 tests/test_fixture_codemod.py` printed `11 passed in 8.51s` and `0 unlisted slow tests`. E-05 keeps new tests in process and states the `j2xjtt` E-09 fallback if the bound is still exceeded.

### Step R3

- Checked (short form): the change rewrites test source text and the tests run in temporary directories. No credentials, network, shell interpolation, or user configuration is touched. `_pytest_workdir_and_env` already strips xdist variables and sets `PYTHONDONTWRITEBYTECODE`.
- No security finding.

### Step R4

- Checked by probe at `4e6ee9406`: the three fixture shapes in E-02 were written to a temporary repository twice, once as the legacy literals and once as the hand-built `RecordBuilder` equivalents E-03 expects. In both, `search -p ALPHA_SECRET` returned 0 naming all three files, `search BETA_BODY` returned 1, and `search -F -p BETA_BODY` returned 0 naming the `bkl001` and `prm001` files. `artifact_meta.read_text` read `prm001` as `status == "reviewed"` in both. So E-03's expected replacements are equivalent and E-02's assertions are satisfiable.
- Checked: at HEAD, `analyze_module` on those shapes rewrites the two backlog sites to `standard` and the prompt site to `invalid-input` with `raw_fields={'Status': 'reviewed'}` but no `summary` or `short_description`, which confirms the defect and E-03's class counts.
- Checked: a comment-dialect prompt with a post-comment `# Prompt: Kept Title` already rewrites with that line in `body`, which confirms `OQ-02`.
- `python3 -m mypy tools/fixture_codemod.py` printed `Success: no issues found in 1 source file`.

### Step S5

- Checked: `OQ-01` and `OQ-02` are resolved from repository evidence that this review re-verified. The three judgement calls this review made are recorded in Decisions D1 to D3 and are reversible. No question needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. E-01 to E-05 map one-to-one to V-01 to V-05, `Highest E allocated: 05`, and the flowchart shows the new edges. `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings) after the edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Correctness | `tools/fixture_codemod.py::_template_to_value_expr` (bare placeholder); `tests/test_partition_set_cohesion.py::test_partition_split_sets_for_backlog` `f"# Backlog Item {idx}\n\n"`; probe `summary=1` -> `AttributeError` | A bare non-`str` placeholder title would be emitted as `summary=idx` and crash `RecordBuilder.backlog`, on the one live titled site. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 step 3 emits `str(<expr>)`; E-05 case (j); E-03 expects `summary=str(bkl_tag)`. |
| F2 | MEDIUM | IN-SCOPE | R1 / Equivalence | `tests/record_builder.py::RecordBuilder.prompt` default `initial_text`; probe rendered `# Prompt: Audit cache parity` plus `Prompt body.` | A bullet prompt with an H1 and no `## ` section would gain a changed heading and placeholder body text. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 step 4 emits `body=<raw_h1_line>`; E-05 case (e); flowchart branch. |
| F3 | MEDIUM | IN-SCOPE | R2 / Right-sizing | Plan E-02 (two files, about eleven cases, one V-item) | One E-item held the fixture module and the whole core test set. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Split into E-02 (fixture) and E-05 (core tests) with V-02 and V-05; dependencies updated. |
| F4 | MEDIUM | IN-SCOPE | R2 / Validation strength | Plan E-02 item 1 "observe the preserved H1 titles"; E-03 `totals["sites"] == 3` | The fixture's own assertions, which make the equivalence proof discriminating, were unnamed, and the site count was not pinned. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 names measured exit codes and matches, exactly three literals, and token-free filenames. |
| F5 | LOW | IN-SCOPE | R1 / Stale evidence | `analyze_module` over 784 modules at `4e6ee9406`: 7 backlog or prompt sites, 1 titled | F-04's 23-site census named modules that no longer yield such sites. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | F-04 rewritten with the re-measure. |
| F6 | LOW | IN-SCOPE | R2 / Executability | `ls tools/__init__.py` -> no such file; `tests/test_dead_status_token_scan.py` `from tools.dead_status_token_scan import` | In-process tests did not say how to import the tool. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-05 names `from tools import fixture_codemod`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | How should a bare placeholder title become a `str`? | `str(<expr>)`, or `format(<expr>, '<spec>')` with a spec | Refuse as `dynamic-construction`; always emit an f-string | `f"{x}"` equals `str(x)` and `f"{x:spec}"` equals `format(x, spec)`; refusing would leave the live site to hand conversion, the defect being fixed | yes |
| D2 | Split E-02 or keep it whole? | Split into E-02 and E-05 | Keep one E-item | The plan's own right-sizing rule; the two parts have separate evidence | yes |
| D3 | What body does a titled bullet prompt with no `## ` section get? | `body=<raw_h1_line>` | Leave `body` unset | Unset renders a different heading and adds `Prompt body.`, measured by probe | yes |

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `Highest E allocated: 04` | `05` | F3 |
| Scope | Fixture and core tests as one item | Names E-02 and E-05 | F3 |
| E-01 steps 3 and 4, expected outcome | `setdefault(..., title_vexpr.code)`; body prepend only | `str()` wrapping for bare placeholders; `body=<raw_h1_line>` when no `## ` section | F1, F2 |
| E-02, new E-05, E-03, E-04 | One combined test item; vague fixture assertions | Fixture item with measured outcomes; separate core-test item; corrected dependencies and allowlist format | F3, F4, F6 |
| Findings F-04, F-05 | 23-site census; one baseline | Re-measured census; second baseline | F5 |
| Proposed changes, flowchart | Four steps, linear order, two body branches | Five steps, branching order, three body branches | F2, F3; requirement 12 |
| Validation | V-02 covered both test files | V-02 for the fixture, new V-05 for core tests | F3 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
