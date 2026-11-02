# Review findings: plan g4719s

- Subject-Id: g4719s
- Subject-Type: ipd
- Reviewed-At: 2026-11-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `f70329c47` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 2) is byte-identical to the tracked plan (committed, unmodified), so no pre-review
snapshot. `aw ipd lint --phase author` clean before revisions. After revisions `--phase review-finalize`
reports exactly one error, `IPD-Q501`, which is the intended gate from the new blocking OQ-01; a scratch
copy with OQ-01 set `Blocking: no` lints clean, so no other structural defect remains.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | Draft is a gitignored delivery copy | Adds size (78 lines, 11 requirements, research `7fe5zd`) and that no tracked artifact quotes it | The old E-01 wording claimed backlog `qph7c5` quotes the draft "in full"; it does not. |
| E-01 | "stop and ask the maintainer" if file absent | Report `AW_MISSING_INPUT`, do not reconstruct wording; cites OQ-01 | Non-interactive runners cannot ask; prevents invented wording. |
| E-01 | "(spec `ecmw83` MD-2)" | "(maintainer decision MD-2 of spec `ecmw83`)" | MD-2 is not a declared trace id; the qualified form was an unknown ref to SPEC-PLAN-TRACE. |
| E-04 | "pending plan `3bwrfx` E-03 names this path" | Executed `3bwrfx`, spec `k3yx72`, and shipped `p-proofread.md` name it | `3bwrfx` is executed. |
| Gate | Partial execution contract | Full contract (scope-fence declaration, paste output, finalize ownership) | S7 execution-contract rule. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PI-1 | E-01 | Source of the verbatim draft text | Tracked path of the draft | Commit the draft verbatim as a tracked record (OQ-01) | strong |

### Step T

1. Yes: it creates a shipped file other Orders point to and changes the target of prompt `wcisgc`, which spec `k3yx72` and `p-proofread.md` cite.
2. No.
3. No: 6 E-items, 2 task groups, one new file plus one prompt, one test, CHANGELOG.
4. Yes: four Scope-Paths, no `.spec.md`.
5. Low: additive file; the prompt rewrite is reversible through git.

Tier: standard.

### Step R1

- Checked: spec `ecmw83` R-01 to R-04, AC-01, AC-02, MD-2; backlog `qph7c5`; prompt `wcisgc` (headings 1 to 7, metadata comment); `engine.collect_source_members`, `engine.is_ignored_source_path`, `engine.SOURCE_EXCLUDED_NAMES`, `engine.install_into_repo`; `pyproject.toml` force-include `.aw/system`; `.gitignore` `tmp/`; `tests/support.py::SOURCE_WORKFLOWS`, `tests/support.py::init_repo`; `tests/test_agy_skill_install.py`; executed `3bwrfx` E-03; `plan-review/steps/p-proofread.md`; `e4n4p3` E-04; `lane_containment._INPUT_CLASSES`.
- Probe: installed a copy of `.aw/system` with an added `workflows/standards/technical-artifact-writing.md` into an `init_repo` target via `engine.install_into_repo`; output `installed: True True` (exists, bytes equal). The "no code change" claim holds.
- `tmp/` is absent from this worktree; the draft cannot be read here (PR-001).
- `wcisgc` line 101 holds an em dash ("from sources" + em dash + "not guesses") (PR-003).

### Step R2

- Checked: E/V bijection (6/6), Scope-Paths, Item-Dependencies none (Order 01, correct), V-item evidence concreteness, SPEC-PLAN-TRACE via `production_checks._compute_spec_trace_coverage`.
- Before revision this plan cited no qualified requirement or AC id and leaked `MD-2` as an unknown ref; after revision R-01 to R-04 and AC-01, AC-02 are covered and the unknown ref is gone (PR-004).
- V-01 grep `'^[0-9]*\. \*\*'` assumes a bold numbering form not verifiable without the draft (PR-005).

### Step R3

- Checked: the plan copies text from an untracked maintainer file into the shipped wheel. Added `aw sanitize --agent` to E-06/V-06 (PR-006). No secrets, no trust-boundary code.

### Step R4

- Checked: A not applicable (no data store); C reuses the installer with no code change; D invariant "the standard installs byte-identical" maps to the E-05 test; E test exercises the real installer (P16 compliant); F smallest design; right-sizing: each E-item one deliverable; spec sync: no spec text change is correct (spec already specifies the file).
- CHANGELOG has no "unreleased" heading; topmost is `## 2.0.0 (pending)` (PR-007).

### Step S5

- Checked: one human-only question (OQ-01, where the tracked verbatim draft lives). Not answerable from the repository; bringing maintainer text into tracked history is the maintainer's act. Raised `Blocking: yes`, `Finding: PR-001`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | G executability | `.gitignore` "tmp/"; `ecmw83` R-02 "wording preserved"; `lane_containment._INPUT_CLASSES` (plan, runbook) | E-01 copies verbatim from a gitignored file that no tracked artifact quotes and an isolated runner lane cannot read; the claim that `qph7c5` quotes the draft in full is false. | C:Low; U:Medium; S:Low; F:High; Overall:High | open | Escalated as OQ-01 (`Blocking: yes`). E-01 now reports `AW_MISSING_INPUT` and forbids reconstruction. Maintainer must commit the draft as a tracked record. |
| PR-002 | medium | IN-SCOPE | G execution contract | plan gate; `is2xiv` gate | Gate lacked scope-fence-as-declaration, paste-output MUST, never `git add -A`, and finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten with full contract. |
| PR-003 | medium | UNDER-SCOPE | D invariant | `wcisgc` section 6 examples paragraph, em dash; `ecmw83` AC-02 | Adopting `wcisgc` text would import an em dash; V-01 counts dashes before E-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 and E-03 reword dashes; V-03 re-runs the dash count after E-03. |
| PR-004 | medium | UNDER-SCOPE | G spec trace | `production_checks._compute_spec_trace_coverage` `cite_pattern` | No qualified `ecmw83` R-/AC- ids in E/V; `ecmw83` MD-2 counted as unknown ref. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Qualified R-01 to R-03 in E-01, E-03, E-04, E-05; AC-01, AC-02 in V-01 to V-05; MD-2 reworded. |
| PR-005 | low | IN-SCOPE | E testing | V-01 grep pattern | Pattern assumed bold numbering; V-01 did not prove wording preservation or requirement 11's sentence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | V-01 demands the requirement lines with stated pattern, requirement 11's sentence, and a diff against the tracked draft. |
| PR-006 | low | UNDER-SCOPE | B privacy | `pyproject.toml` force-include `.aw/system` | Text from an untracked draft enters the shipped wheel without a leak check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06/V-06 run `aw sanitize --agent`. |
| PR-007 | low | IN-SCOPE | R1 references | `CHANGELOG.md` "## 2.0.0 (pending)"; E-04 "pending plan `3bwrfx`" | "Unreleased heading" does not exist; `3bwrfx` is executed; E-05 named no harness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 names `tests.support.init_repo` + `SOURCE_WORKFLOWS` and the pending heading; E-04 and Findings cite executed `3bwrfx`, `k3yx72`, `p-proofread.md`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a new top-level `standards/` directory install without code change? | Yes, no code change | Add an installer entry | Probe via `engine.install_into_repo` printed `installed: True True`; `engine.collect_source_members` rglob | yes |
| D-2 | Edit `.aw/system/managed-sections.json` for the new file? | No | Add an entry | Executed `3bwrfx` added shipped step files with no edit to it | yes |
| D-3 | Review tier | standard | simple | Step T answers 1 yes, 5 low | yes |

## Round 2

Reviewed at HEAD `bd9d77e70` in runner review-sweep lane `run-20261102T235035Z-1842120` (non-interactive). The lane-input copy (revision 1) is byte-identical to the tracked plan, which is the pre-round-1 text: the round-1 review commit `9b2d88cfd` sits on parked branch `aw/parked/run-20261102T043053Z-1740891/g4719s` and never reached this lane. Its object is resolvable here (`git show 9b2d88cfd`). Round 1 was re-verified against this tree and carried forward unchanged (cherry-picked as the starting point of this round), then this round's fixes were applied. `aw ipd lint --phase author` was clean on the input; `--phase review-finalize` after revisions reports exactly one error, `IPD-Q501`, the intended gate from blocking OQ-01.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Gated on plan approval and OQ-01 only | Also gated on spec `ecmw83` approval, matching orchestrator `8fvkmp` | PR-008. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PI-1 | E-01 | Source of the verbatim draft text (carried from round 1) | Tracked path of the draft | Commit the draft verbatim as a tracked record (OQ-01) | strong |

### Step T

1. Yes: creates a shipped file other Orders point to and repoints prompt `wcisgc`, which spec `k3yx72` and `plan-review/steps/p-proofread.md` cite.
2. No.
3. No: 6 E-items, 2 task groups.
4. Yes: four Scope-Paths, no `.spec.md`.
5. Low: additive file; prompt rewrite reversible through git.

Tier: standard.

### Step R1

- Checked: re-verified every round-1 citation in this tree. `tmp/` absent in the lane; `.gitignore` "tmp/"; the only tracked mentions of the draft (research `7fe5zd`, `53jbi5`) describe it and do not quote it; `wcisgc` still has exactly one em dash (section 6, "from sources[em dash]not guesses"); `engine.collect_source_members` rglob; `lane_containment._INPUT_CLASSES` (plan, runbook); `tests.support.init_repo`, `tests.support.SOURCE_WORKFLOWS`; `CHANGELOG.md` topmost heading "## 2.0.0 (pending)"; `check_engine` reads the `aw-prompt:` first-line comment; `3bwrfx` is in `executed/`; `e4n4p3` E-04 repoints `p-proofread.md`.
- Probe (re-run this round): copied `SOURCE_WORKFLOWS`, added `standards/technical-artifact-writing.md`, ran `engine.install_into_repo` into an `init_repo` target; printed `installed: True True` (exists, bytes equal), about 3 s wall.

### Step R2

- Checked: E/V bijection 6/6; Scope-Paths; `Item-Dependencies: none` (Order 01); each V-item demands pasted output; no live-artifact counts as bars.
- `check.ipd-carrier-ungated` (info) fires because OQ-01 names `Carrier: qph7c5` with no edge to it. Not a defect: the plans README "Carrier records durable ownership, not a dispatch gate", and the blocking flag already gates dispatch (`IPD-Q501`). No edge added (D-4).

### Step R3

- Checked: no new trust-boundary code; round-1 PR-006 sanitizer step remains in E-06/V-06.

### Step R4

- Checked: rubric A to F as in round 1; spec sync claim holds (spec `ecmw83` R-01 to R-04 already specify the file and the `wcisgc` pointer, so no spec edit). Spec `ecmw83` is `to-review`, yet the gate did not require its approval (PR-008).

### Step S5

- Checked: OQ-01 remains the only question, still the maintainer's (bringing maintainer-authored text into tracked history). Non-interactive run: left `open`, `Blocking: yes`, `Finding: PR-001`, and surfaced in the lane outcome `questions[]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | G executability | `.gitignore` "tmp/"; `ecmw83` R-02 "wording preserved"; `lane_containment._INPUT_CLASSES` | E-01 copies verbatim from a gitignored draft that no tracked artifact quotes and an isolated lane cannot read. | C:Low; U:Medium; S:Low; F:High; Overall:High | open | Still escalated as OQ-01 (`Blocking: yes`). Maintainer must commit the draft as a tracked record and E-01 must cite it. |
| PR-002 | medium | IN-SCOPE | G execution contract | plan gate | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-003 | medium | UNDER-SCOPE | D invariant | `wcisgc` section 6 em dash | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-004 | medium | UNDER-SCOPE | G spec trace | `production_checks._compute_spec_trace_coverage` | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-005 | low | IN-SCOPE | E testing | V-01 | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-006 | low | UNDER-SCOPE | B privacy | `pyproject.toml` force-include `.aw/system` | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-007 | low | IN-SCOPE | R1 references | `CHANGELOG.md` "## 2.0.0 (pending)" | Carried from round 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Round 1 fix verified present. |
| PR-008 | low | UNDER-SCOPE | G execution contract | spec `ecmw83` "- Status: to-review"; `8fvkmp` gate "only after spec `ecmw83` is approved" | This child's gate did not require approval of the spec it implements, unlike its orchestrator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate now requires spec `ecmw83` approval. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-4 | Add a `state:backlog:...:qph7c5` edge to silence `check.ipd-carrier-ungated`? | No | Add the edge | `.aw/records/plans/README.md#Carrier records durable ownership, not a dispatch gate`; OQ-01 `Blocking: yes` already gates via `IPD-Q501`; an edge on the parent backlog item would block until it closes, which only happens after this plan executes | yes |
| D-5 | Carry round 1 forward rather than re-deriving it | Cherry-pick `9b2d88cfd` and append round 2 | Discard and re-review from scratch | Every round-1 claim re-verified in this tree (Step R1) | yes |
