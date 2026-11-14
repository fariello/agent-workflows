# Review findings: ipd j2xjtt

- Subject-Id: j2xjtt
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f65143de2` in an isolated runner review-sweep lane worktree. The lane-input
copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review
snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize`
was clean after them. Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (Section 7 step 6),
orchestrator `63ib9r` (row 173), split parent `653ndz` (E-04), research guidance `nj8zdp`, tool implementation
plan `y3uowx` (Order 172), and sibling test plan `n0li9v` (Order 216).

### Proofreading

Checked `.aw/records/plans/pending/20261109-metastore-173-j2xjtt-test-the-fixture-codemod-rewrite-invalid-input-dry-run-idemp.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:` | Replaced line 20 with standard compliance blockquote; added `- Review-Depth: standard` and `- Readiness: go-pending-approval` | PR-001. |
| `E-04` | Lacked explicit tool path definition and invocation convention | Defined `CODEMOD_PATH = Path(__file__).resolve().parent.parent / "tools" / "fixture_codemod.py"` and driving via `sys.executable` subprocess calls | PR-002. |
| `E-09` | Unnamed slow module path if 10s bound triggers | Explicitly named `tests/test_fixture_codemod_slow.py` with scope fence `--scope-reason` handling | PR-003. |
| `OQ-01`, `OQ-02` | `- Owner: none` on resolved questions | Updated `- Owner:` to `plan author (carried from 653ndz)` | PR-004. |
| `Proposed changes` | Numbered list without Mermaid diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-001. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Plan creates internal behavioral tests in `tests/test_fixture_codemod.py` and fixture modules under `tests/fixtures/fixture_codemod/` for maintenance tool `tools/fixture_codemod.py`; no public CLI or contract is altered.
2. No. Modifies no authorization gates, commit locks, sandbox boundaries, or worktree isolation logic.
3. No. 4 E-items in 2 task groups, focused entirely on test cases for the codemod tool.
4. No. Lists 4 Scope-Paths (`tests/test_fixture_codemod.py`, `tests/fixtures/fixture_codemod/**`, `tests/slow_allowlist.txt`, and the plan itself).
5. No. Test code and fixtures only, executed in temporary isolated repositories via `tests/support.py init_repo`; easily reversible via git.

AW-TIER: standard

### Step R1

- Checked: `tools/fixture_codemod.py` is authored by prerequisite Order 172 (`y3uowx`) and driven as a standalone script.
- Checked: Prerequisite dependencies in `- Item-Dependencies:` (`9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `y3uowx`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 173.
- Checked: `tests/support.py` (`init_repo` at line 281) and `tests/slow_allowlist.txt` exist on disk and resolve correctly.
- Checked: Carrier references in `Deferred / out of scope`: `n0li9v` (Order 216) for case (d) and `y3uowx` (Order 172) for the tool itself both resolve in `.aw/records/plans/`.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection is exact (`E-04, E-08, E-09, E-10` <-> `V-04, V-08, V-09, V-10`), with `- Highest E allocated: 10`.
- Reachability: `V-04`, `V-08`, `V-09` verify each test case group passes under pytest with duration output, and assert `rg -n "inspect\.|getsource"` is empty (enforcing behavioral testing); `V-10` verifies total duration under 10s or slow module allowance, runs core gate `python3 -m pytest`, and checks path-scoped commits.

### Step R3

- Checked: Tests drive the tool on synthetic fixture repositories in temporary directories (`init_repo`); no production code or credentials touched.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- A (State & atomicity): Subprocess execution is sandboxed in temporary directories; rewritten files are verified against expected outcomes.
- C (Architecture & operability): Comprehensive test coverage of the rewriter, dry-run, idempotence, invalid input handling, and equivalence proof isolation before any batch migration plan runs it on repository test modules.
- D & E (Anti-regression & verification): Tests enforce observable outcomes; no inspection of production AST or source; duration is bounded to 10s to protect core test suite speed.
- Spec sync: Implements the test-harness half of `4sd62s` section 7 step 6.

### Step R5

- Checked through review personas:
  - QA / QC: Verified that subprocess tests assert on stdout/stderr, exit codes, and rewritten file contents.
  - Test Engineer: Verified the 10-second core tier duration safeguard and `tests/slow_allowlist.txt` fallback.
  - Technical Writer: Added Requirement 12 Mermaid flowchart and replaced authoring prompt boilerplate with standard compliance blockquote.

### Step R6

- Decomposition check: 4 E-items in 2 task groups, 3 work Scope-Paths plus fixtures. Partitioned cleanly from parent `653ndz` under research `nj8zdp` guidance. No further split needed.

### Step R7

- Cross-plan consistency: Verified coordination across Set metastore:
  - Prerequisite `y3uowx` (Order 172) builds the tool.
  - Current plan `j2xjtt` (Order 173) tests cases (a), (b), (c), (e), (f), (g), (h).
  - Sibling plan `n0li9v` (Order 216) tests case (d) (static refusal reason codes).
  - Finishing plan `653ndz` runs the pilot and census.
  - Orchestrator `63ib9r` rows 49, 172, 173, 216 align with this exact decomposition.

### Step S5

- Checked: OQ-01 and OQ-02 attribution updated from `none` to `plan author (carried from 653ndz)`. Zero open questions remain. All findings `FIXED` in place. No human decision needed.

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified `aw ipd lint --phase review-finalize --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute file paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261109-metastore-173-j2xjtt-test-the-fixture-codemod-rewrite-invalid-input-dry-run-idemp.ipd.md:20` | Authoring template prompt blockquote present; missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`); `Proposed changes` lacked a Requirement 12 Mermaid diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added `- Review-Depth: standard` and `- Readiness: go-pending-approval` to front matter, and added `flowchart TD` Mermaid diagram to `Proposed changes`. |
| PR-002 | LOW | IN-SCOPE | R1 / R2 Executability | `.aw/records/plans/pending/20261109-metastore-173-j2xjtt-test-the-fixture-codemod-rewrite-invalid-input-dry-run-idemp.ipd.md:52` | `E-04` did not specify the `CODEMOD_PATH` constant definition or subprocess invocation convention for driving `tools/fixture_codemod.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Explicitly defined `CODEMOD_PATH = Path(__file__).resolve().parent.parent / "tools" / "fixture_codemod.py"` and specified subprocess execution via `sys.executable` with `--dry-run` and `--apply` flags in temporary repositories created with `tests/support.py init_repo`. |
| PR-003 | LOW | IN-SCOPE | R2 / R4 Scope & Test Governance | `.aw/records/plans/pending/20261109-metastore-173-j2xjtt-test-the-fixture-codemod-rewrite-invalid-input-dry-run-idemp.ipd.md:62,69` | `E-09` and `E-10` did not name the conventional module path for the slow test module if wall time exceeds 10s, leaving scope fence handling ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named `tests/test_fixture_codemod_slow.py` as the conventional slow module path and clarified scope fence handling via `--scope-reason` if created. |
| PR-004 | LOW | IN-SCOPE | S5 Questions & Governance | `.aw/records/plans/pending/20261109-metastore-173-j2xjtt-test-the-fixture-codemod-rewrite-invalid-input-dry-run-idemp.ipd.md:123,130` | `OQ-01` and `OQ-02` carried `- Owner: none` despite being resolved with substantive rationale, leaving ownership unattributed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner:` on both resolved open questions to `plan author (carried from 653ndz)`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `CODEMOD_PATH` and subprocess invocation be specified in `tests/test_fixture_codemod.py`? | Define `CODEMOD_PATH = Path(__file__).resolve().parent.parent / "tools" / "fixture_codemod.py"` and invoke via `sys.executable` subprocess calls with explicit `--dry-run` and `--apply` flags in temporary repositories initialized with `support.init_repo` | Rely on PATH lookup (`subprocess.run(["fixture_codemod.py", ...])`) or direct python module import | Tool test pattern in `tests/test_gate_drop_audit.py` and `Project conventions discovered (Step 0)` | yes |
| D-2 | How should the slow-module path and scope handling be resolved if the 10-second duration bound triggers? | Use conventional name `tests/test_fixture_codemod_slow.py`, justified at finalize via `--scope-reason` if created, while `tests/slow_allowlist.txt` remains pre-declared in `- Scope-Paths:` | Hardcode `tests/test_fixture_codemod_slow.py` in `Scope-Paths` upfront (forces `--scope-ack` if execution finishes under 10s without creating the file) | Scope fence rules in Section `Approval and execution gate` and `tests/slow_allowlist.txt` registration convention | yes |
| D-3 | How should ownership of resolved open questions `OQ-01` and `OQ-02` be attributed? | Update `- Owner: none` to `- Owner: plan author (carried from 653ndz)` to reflect who authored the resolution | Leave `- Owner: none` | `steps/s5-questions.md` Section 3.1 and `653ndz` split provenance | yes |
