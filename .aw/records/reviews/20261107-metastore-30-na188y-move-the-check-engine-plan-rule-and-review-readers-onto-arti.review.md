# Review findings: ipd na188y

- Subject-Id: na188y
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ef392273b` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review
snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize`
was clean after them.

### Proofreading

Checked `.aw/records/plans/pending/20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Detailed Implementation Checklist` / `E-01`, `Scope check`, `Required tests / validation` | Instructed adding tests in `tests/test_readers_check_engine.py` without stating whether to create or extend it | Specified creating `tests/test_readers_check_engine.py` if absent (with `pytestmark = pytest.mark.core` and `TestCheckEngineReadersOrder30`) or appending `TestCheckEngineReadersOrder30` if Order 29 `w1cs3p` already created it | PR-001. |
| `Detailed Implementation Checklist` / `E-01`, `E-02`, `V-01`, `V-02` | Unnamed baseline outcome files ("baseline outcome list is saved") and demanded `ls -l .aw/state/ffceq0/check-before.txt` which may not exist in an isolated lane | Explicitly named `.aw/state/ffceq0/E-06-before-30.txt` and `.aw/state/ffceq0/E-07-after-30.txt` with `mkdir -p .aw/state/ffceq0`, and clarified `check-before.txt` creation/persistence across isolated lanes | PR-002. |
| `Findings` (`F-09`), `Required tests / validation` | No live verification measurements or documentation of baseline test suite runtimes | Added `F-09` recording 44 passing tests in 14.38s at commit `ef392273b` and documented the 12s full-repository spec conformity sweep in `tests/test_spec_review_attestation.py` | PR-003. |
| Header blockquote, Front matter, `Proposed changes` | Instructional boilerplate at line 20, missing Mermaid diagram, and missing review-depth/readiness metadata | Replaced line 20 with standard technical-writing compliance blockquote, added Requirement 12 Mermaid flowchart, added `- Review-Depth: complex` and `- Readiness: go-pending-approval`, and added newest-first workflow history entry | PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: modifies `agent_workflows/check_engine.py` working-tree metadata reading across 15 core validation functions.
2. Yes: directly affects repository validation checks run by `aw check` and commit gates (`check_ipd_draft_ready`, `evaluate_ipd_dependencies`, `check_spec_review_attestation`, `check_review_dangling`, `find_obligations_carried_by`).
3. Cross-cutting across 15 validation functions in `check_engine.py` and Set `metastore` split parts Orders 29 to 32.
4. No: 4 Scope-Paths, 2 E-items, 1 task group (split under maintainer step-complexity rule).
5. Yes: a regression in `check_engine` readers could mask illegal transitions or falsely fail clean checkouts across the entire repo.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/check_engine.py`, `tests/test_spec_review_attestation.py`, `tests/test_gate_ref_resolution.py`, `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, sibling split plans `w1cs3p` (Order 29), `i3b5zu` (Order 31), `ebrc4t` (Order 32), and split parent `ffceq0` (Order 08) at `HEAD` `ef392273b`.
- Confirmed all 24 working-tree metadata read site lines across the 15 named functions in `agent_workflows/check_engine.py` at `HEAD` `ef392273b`:
  - `check_ipd_draft_ready`: 2 sites (`_read_plan_status`, `_read_item_id`)
  - `check_ipd_review_stale`: 1 site (`_read_item_id`)
  - `check_scope_drift`: 1 site (`_read_item_id`)
  - `evaluate_ipd_dependencies`: 3 sites (`_read_declared_id`, 2x `_ITEM_DEPENDENCIES_RE`)
  - `check_plan_priority`: 2 sites (`_ITEM_PRIORITY_RE`, `_read_item_id`)
  - `check_plan_work_kind`: 2 sites (`_ITEM_WORK_KIND_RE`, `_read_item_id`)
  - `check_plan_priority_required`: 1 site (`_read_item_id`)
  - `_review_subject_id_sets`: 2 sites (2x `_read_item_id`)
  - `check_review_dangling`: 1 site (`_REVIEW_SUBJECT_ID_RE` / `_REVIEW_SUBJECT_TYPE_RE`)
  - `check_spec_review_attestation`: 2 sites (`Status` regex, `_read_item_id`)
  - `evaluate_review_finding_escalation`: 1 site (`_read_item_id`)
  - `evaluate_review_decision_escalation`: 1 site (`_read_item_id`)
  - `find_obligations_carried_by`: 1 site (`- Id:` regex)
  - `check_ipd_lint_reach`: 1 site (`- Date:` regex)
  - `check_orchestrator_not_review_ready`: 3 sites (`Kind`, `Status`, `Set` regexes)
- Empirically ran baseline suites `tests/test_spec_review_attestation.py` and `tests/test_gate_ref_resolution.py` (44 passed in 14.38s).
- Confirmed `tests/test_readers_check_engine.py` does not yet exist on disk in this checkout.

### Step R2

- Checked 1:1 `E-*`/`V-*` bijection (`E-01..E-02` <-> `V-01..V-02`, `- Highest E allocated: 02`).
- Aligned baseline output filenames `.aw/state/ffceq0/E-06-before-30.txt` and `.aw/state/ffceq0/E-07-after-30.txt` with `V-01` and `V-02`.
- Confirmed evidence demands in `V-01` and `V-02` are verifiable and executable.

### Step R3

- Checked security, isolation, and containment: reads go through `artifact_meta.read`, `query`, and `history`. No write side is touched.
- Test module uses `tmp_path` fixtures and invokes `aw check <type> --agent` through the public CLI without modifying git history or primary checkouts.
- Baseline state directory `.aw/state/ffceq0/` is gitignored and survives lane integration.

### Step R4

- Verified reader contracts against `4sd62s` section 7 step 5.
- Confirmed body-prose bullet scanning (`Concern`, `Scope`, `Scope-Paths`, `Carrier*` bullets) is excluded from `artifact_meta` and remains unperturbed in `check_engine.py` per N3 and `ffceq0` E-14.
- Confirmed status normalization follows `D-1` (`plans.normalize_status`) and region-bounded reading follows `D-4`.

### Step R5

- Evaluated against the eight reviewer personas:
  - QA/QC & Testing: caught missing `tests/test_readers_check_engine.py` handling for parallel/isolated lanes (PR-001) and explicit baseline outcome file paths (PR-002).
  - Performance & Budget: caught 12s full-spec sweep runtime in `test_spec_review_attestation.py` (PR-003).
  - Architect & Software Engineer: verified the 24 site lines across 15 functions against `artifact_meta` APIs.
  - Technical Writer: caught instructional boilerplate at line 20 and missing Requirement 12 Mermaid diagram (PR-004).

### Step R6

- Decomposition check: 2 `E-*` items in 1 task group, 24 site lines, 4 Scope-Paths. Well within `IPD-Z603` limits (exit 0 from `aw ipd lint`). No further split needed.

### Step R7

- Cross-plan consistency: checked against sibling split plans `w1cs3p` (Order 29, 23 site lines), `i3b5zu` (Order 31, 23 site lines), `ebrc4t` (Order 32, 23 site lines), split parent `ffceq0` (Order 08, 93 working-tree site lines total), git-reader plan `t4gl15` (Order 09), and orchestrator `63ib9r`. All 93 working-tree site lines are accounted for across Orders 29 to 32 without gaps or overlaps.

### Step S5

- Evaluated `OQ-01` (resolved, step complexity fits). Zero open questions remain. All findings `FIXED` in place.

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R2 | `.aw/records/plans/pending/20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md:7,41,117`; `agent_workflows/check_engine.py` | `Scope-Paths` and `E-01` instruct adding behavioral characterization tests in `tests/test_readers_check_engine.py`, but that file does not yet exist on disk in this checkout or in an isolated runner lane where Order 29 (`w1cs3p`) has not yet run or merged; the plan did not state whether `na188y` creates the module or appends to it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified in `E-01`, `Scope check`, and `Required tests / validation` that `na188y` creates `tests/test_readers_check_engine.py` if not yet present (defining `pytestmark = pytest.mark.core` and `class TestCheckEngineReadersOrder30`) or appends `TestCheckEngineReadersOrder30` if the module already exists (strength: very strong) |
| PR-002 | HIGH | IN-SCOPE | R1 / R2 | `.aw/records/plans/pending/20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md:43,48,172,177` | `V-01` and `V-02` demand comparing saved outcome lists `.aw/state/ffceq0/E-06-before-30.txt` and `.aw/state/ffceq0/E-07-after-30.txt`, but `E-01` and `E-02` text used vague phrasing without explicitly naming those paths or providing `mkdir -p .aw/state/ffceq0` for isolated worktrees; additionally `V-01` demanded `ls -l .aw/state/ffceq0/check-before.txt` which would fail in an isolated lane if `na188y` runs before earlier split parts | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Explicitly named `.aw/state/ffceq0/E-06-before-30.txt` and `.aw/state/ffceq0/E-07-after-30.txt` in `E-01` and `E-02` with `mkdir -p .aw/state/ffceq0`, and clarified in `E-01` and `V-01` that `check-before.txt` is created by the first part to execute in that checkout and preserved if already present (strength: very strong) |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 | `.aw/records/plans/pending/20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md:41,117`; `tests/test_spec_review_attestation.py:112` | Baseline test `tests/test_spec_review_attestation.py` includes `test_every_real_spec_in_this_repository_still_conforms`, which executes 12.14s on the live repository; the plan did not document this runtime characteristic in `Findings` or `Required tests / validation`, risking budget confusion during validation runs | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added live verification measurements to `F-09` (44 tests in ~14.4s, noting the 12s full-spec sweep) and documented the runtime budget expectation under `Required tests / validation` (strength: strong) |
| PR-004 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md:20,101-104` | Line 20 contained instructional boilerplate instead of the required standard compliance blockquote, `## Proposed changes` lacked a `technical-writing.md` Requirement 12 flowchart diagram, and front matter lacked `- Review-Depth: complex` and `- Readiness: go-pending-approval` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced line 20 with standard technical writing blockquote, added a Mermaid `flowchart TD` diagram to `## Proposed changes`, added `- Review-Depth: complex` and `- Readiness: go-pending-approval` to front matter, and added newest-first workflow history entry (strength: strong) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `na188y` handle `tests/test_readers_check_engine.py` given that split parts Orders 29 to 32 share the module across isolated lanes? | Create `tests/test_readers_check_engine.py` if not present (defining `pytestmark = pytest.mark.core` and `TestCheckEngineReadersOrder30`) or append `TestCheckEngineReadersOrder30` if the module already exists from Order 29 (`w1cs3p`) | Assume `w1cs3p` ran first and only edit the file (fails if `na188y` runs first or in an isolated lane), or create a separate file `test_readers_check_engine_order30.py` (proliferates test files contrary to `Scope-Paths`) | Lane isolation, `Scope-Paths`, and Order 29..32 partition structure | yes |
| D-2 | How should `na188y` handle `.aw/state/ffceq0/check-before.txt` and baseline files across isolated lanes? | Create `.aw/state/ffceq0/` with `mkdir -p`, save `.aw/state/ffceq0/check-before-30.txt` and `.aw/state/ffceq0/E-06-before-30.txt` for this part, and write `.aw/state/ffceq0/check-before.txt` only if it does not already exist | Fail if `check-before.txt` is missing (fails in any lane where `w1cs3p` did not deposit it), or overwrite `check-before.txt` unconditionally (destroys pre-split baseline for parent `ffceq0`) | Split parent `ffceq0` E-06/E-07 and isolated runner lane execution model | yes |
