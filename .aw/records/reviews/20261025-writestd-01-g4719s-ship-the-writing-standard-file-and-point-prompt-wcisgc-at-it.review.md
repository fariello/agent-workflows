# Review findings: plan g4719s

- Subject-Id: g4719s
- Subject-Type: ipd
- Reviewed-At: 2026-11-05
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

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

## Round 3

Reviewed at HEAD `bfdcb514f` in runner review-sweep lane `run-20261106T024139Z-372975` (non-interactive). The lane-input copy (revision 1) is byte-identical to the tracked plan, which is the pre-round-1 text: rounds 1 and 2 (`9b2d88cfd`, `f3c647b16`) sit on parked branches and never reached main. Round 2's commit was cherry-picked as this round's starting point (`ee7ec5904`), and its claims were re-checked against this tree. `aw ipd lint --phase author` was clean on the input.

New since round 2: maintainer commit `0cbfcc706` ("Add an installed technical writing standard for all technical text", 2026-11-02) shipped the standard that this plan was written to create, at a different path and with a different dash rule.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | "None exists" | "None existed at authoring", names `0cbfcc706` and the shipped path | Fact changed (PR-009). |
| Detailed Implementation Checklist | No warning | REPLAN PENDING paragraph: do not execute E-01 to E-05 as written | PR-009. |
| Findings | No mention of the shipped file | Bullet describing what `0cbfcc706` shipped and what it left out | PR-009. |
| Open questions | OQ-01 only | OQ-02 added; OQ-01 notes it may become moot | PR-009. |
| Gate | Waits on OQ-01 | Waits on OQ-01 and OQ-02 and a rewrite of the E-items | PR-009. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PI-1 | E-01 | Source of the verbatim draft (carried) | Tracked path of the draft | Moot if OQ-02 keeps the shipped file | strong |
| PI-2 | Whole plan | Which standard path and dash rule govern | Maintainer ruling on spec `ecmw83` vs commit `0cbfcc706` | Keep the shipped file; amend the spec; re-scope to diagrams and the procedure section (OQ-02) | strong |

### Step T

1. Yes: the plan would create a shipped file and repoint prompt `wcisgc`, and it now conflicts with a shipped contract (`technical-writing/technical-writing.md`, the `AGENTS.md` pointer from `engine.agents_pointer_prose`).
2. No.
3. No: 6 E-items, 2 task groups.
4. Yes: four Scope-Paths, no `.spec.md`.
5. Medium: executing as written would ship a second, conflicting standard into every managed repository.

Tier: standard.

### Step R1

- Checked: `git show --stat 0cbfcc706` (14 files, including `.aw/system/workflows/technical-writing/technical-writing.md`, `README.md`, `tests/test_technical_writing_delivery.py`, `agent_workflows/engine.py`, `AGENTS.md`, `docs/technical-artifact-writing.md`); the shipped standard's requirements 1 to 11, its concision and automated-checks paragraphs, and item 4 "This standard adds no dash rule of its own"; the shipped file has no diagram requirement and no proofreading procedure section (`grep -n "diagram\|Proofread"` matches only requirement 11's title); `engine.py:1501` names `technical-writing/technical-writing.md`; spec `ecmw83` R-01 (line 152), R-02 (153), MD-2 (70), AC-01 (168) still name the old path and the widened dash rule; `grep -l standards/technical-artifact-writing` matches all ten `writestd` plans and spec `ecmw83`, and no shipped file.
- `wcisgc` is unchanged (115 lines, one em dash). `p-proofread.md` still points at `wcisgc`.

### Step R2

- Checked: E/V bijection 6/6 still holds. E-01 to E-05 are executable only in a way that contradicts the shipped state: E-01 creates a second standard, E-01 and V-01 reverse the dash ruling, and E-05 duplicates `tests/test_technical_writing_delivery.py`. Repair needs the maintainer's choice of path and dash rule, so the E-items were not rewritten in this round (PR-009).

### Step R3

- Checked: no change from round 2.

### Step R4

- Checked: the Goal "exactly one shipped file" is violated by executing the plan as written. Spec sync: spec `ecmw83` now disagrees with the shipped code, so the replan needs a spec amendment listed in Scope-Paths.

### Step S5

- Checked: OQ-01 (carried) and new OQ-02. Both are the maintainer's: OQ-02 changes a spec contract and a recorded maintainer ruling. Non-interactive run: both left `open`, `Blocking: yes`, and listed in the lane outcome `questions[]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | G executability | `.gitignore` "tmp/"; `ecmw83` R-02 "wording preserved" | Carried: E-01 copies from a gitignored draft. | C:Low; U:Medium; S:Low; F:High; Overall:High | open | OQ-01 remains blocking. It becomes moot if OQ-02 keeps the shipped file. |
| PR-002 | medium | IN-SCOPE | G execution contract | plan gate | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-003 | medium | UNDER-SCOPE | D invariant | `wcisgc` section 6 em dash | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-004 | medium | UNDER-SCOPE | G spec trace | `production_checks._compute_spec_trace_coverage` | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-005 | low | IN-SCOPE | E testing | V-01 | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-006 | low | UNDER-SCOPE | B privacy | `pyproject.toml` force-include `.aw/system` | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-007 | low | IN-SCOPE | R1 references | `CHANGELOG.md` "## 2.0.0 (pending)" | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-008 | low | UNDER-SCOPE | G execution contract | `8fvkmp` gate | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-009 | blocker | IN-SCOPE | D invariant; G spec sync | `0cbfcc706`; `.aw/system/workflows/technical-writing/technical-writing.md` item 4 "This standard adds no dash rule of its own"; `engine.py:1501`; spec `ecmw83` R-01, R-02, MD-2 | The standard now ships at `technical-writing/technical-writing.md` with no dash rule, by maintainer ruling. E-01 to E-05 would add a second standard at `standards/technical-artifact-writing.md`, reverse the dash ruling, and duplicate the install test. That breaks the plan's own Goal. Spec `ecmw83` and all ten `writestd` plans still name the old path. | C:Medium; U:High; S:Low; F:High; Overall:High | replan | Escalated as OQ-02 (`Blocking: yes`). Warning added above the checklist. Minimum sound replacement: amend spec `ecmw83` to the shipped path and dash ruling; re-scope this plan to add requirement 12 and the proofreading procedure to the shipped file and reduce `wcisgc` to a pointer; drop E-05; then re-review Orders 02 to 09 against the new path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-6 | Rewrite the E-items to target the shipped file in this round? | No; mark REPLAN and ask | Rewrite to the shipped path now | The choice reverses either spec `ecmw83` MD-2 or the ruling recorded in `0cbfcc706`; both are the maintainer's | yes |
| D-7 | Carry rounds 1 and 2 forward | Cherry-pick `f3c647b16` and append round 3 | Re-review from scratch | Round 2 claims re-checked in this tree (Step R1) | yes |

## Round 4

Reviewed at HEAD `a4e2b293a` in runner review-sweep lane `run-20261106T024139Z-372975`, attempt 2. The maintainer answered the round-3 questions through the terminal channel: OQ-02 "Keep shipped file; amend spec; re-scope g4719s (recommended)" and OQ-01 "Moot under OQ-02 recommended answer". This round applies those answers and re-reviews the re-scoped plan.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope, Scope-Paths, Goal | Create `standards/technical-artifact-writing.md`; new install test | Extend the shipped `technical-writing/technical-writing.md`; amend spec `ecmw83`; no new test | OQ-02 answer. |
| E-01 to E-06, V-01 to V-06 | Copy draft, add req 12, procedure, pointer, install test, gate | Spec amendment, req 12, procedure, pointer, CHANGELOG, gate | OQ-02 answer; PR-010. |
| Findings, Deferred, Spec sync | Spec needs no change | Spec amended in-plan; Orders 02 and 03 deferred to re-review under `8fvkmp` | OQ-02 answer. |
| Open questions | OQ-01, OQ-02 open | Both resolved with the maintainer's quoted answers | S5 return path. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it amends spec `ecmw83` and changes the shipped standard that `AGENTS.md` points to.
2. No.
3. No: 6 E-items, 3 task groups.
4. Yes: four Scope-Paths, including one `.spec.md`.
5. Low: additive text in one shipped file, a spec edit, and a prompt rewrite, all reversible through git.

Tier: standard.

### Step R1

- Checked: `technical-writing.md` has "eleven" at lines 45 and 58 only, has no em or en dash, and has no "diagram" or "Proofreading procedure" text. `engine.py:1501` says "every numbered requirement", so a twelfth requirement needs no managed-block change. Spec `ecmw83` locations R-01 (line 152), R-02 (153), MD-2 (70), AC-01 (168), AC-02 (169), Section 4 "Standard" row (98) all checked. `wcisgc` headings 1 to 7 (lines 18 to 103), its scope rule excludes user-facing prose (line 12), and its section 6 example paragraph quotes project phrases. `CHANGELOG.md` line 105 holds the existing standard entry under `## 2.0.0 (pending)`. `aw specs note` appends history without a status change.
- `tests/test_technical_writing_delivery.py` compares installed and source bytes, so it covers the edited file with no change; its install case is `@pytest.mark.slow`, so E-06 runs it explicitly.

### Step R2

- Checked: E/V bijection 6/6. Each V-item demands pasted output that is reachable by construction (diffs, greps, test runs). Spec trace: R-01 to R-04, AC-01, AC-02 cited. `aw ipd lint --phase review-finalize` reports `clean`, with `info` notes only: `IPD-Z602` on E-01 (six edits to one spec file is one concern, so the item is not split, D-8) and `check.ipd-review-may-be-stale` (the change recorded by this round).

### Step R3

- Checked: no trust-boundary code. E-06 keeps the sanitizer run.

### Step R4

- Checked: the Goal "one source" now holds, because the plan extends the shipped file instead of adding a second one. P16: no text-pinning test was added (D-9). Spec sync: the amendment is declared in Scope-Paths and explained in the plan. The spec's remaining dash-dependent rows (R-05 dash clause, R-07) and non-goals N1 and N2 conflict with the shipped scope. They are deferred to the re-review of Orders 02 and 03 under carrier `8fvkmp`, because changing them here would decide those plans' scope without their review.

### Step S5

- Checked: OQ-01 and OQ-02 are resolved with the maintainer's quoted answers and `Owner: maintainer`. No new question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | G executability | OQ-01 answer 2026-11-05 | The draft source is no longer needed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | OQ-01 resolved (moot); E-01 no longer copies from `tmp/`. |
| PR-002 | medium | IN-SCOPE | G execution contract | plan gate | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-003 | medium | UNDER-SCOPE | D invariant | `wcisgc` section 6 em dash | That em dash sits in the example paragraph, which E-03 no longer copies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Not imported. |
| PR-004 | medium | UNDER-SCOPE | G spec trace | plan E/V citations | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | R-01 to R-04, AC-01, AC-02 cited. |
| PR-005 | low | IN-SCOPE | E testing | V-01 | Carried; V-items rewritten for the new scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-006 | low | UNDER-SCOPE | B privacy | `pyproject.toml` force-include `.aw/system` | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Sanitizer kept in E-06/V-06. |
| PR-007 | low | IN-SCOPE | R1 references | `CHANGELOG.md` "## 2.0.0 (pending)" | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-008 | low | UNDER-SCOPE | G execution contract | `8fvkmp` gate | Carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Present. |
| PR-009 | blocker | IN-SCOPE | D invariant; G spec sync | OQ-02 answer 2026-11-05; `0cbfcc706` | The plan would add a second standard and reverse the dash ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Re-scoped to extend the shipped file and amend spec `ecmw83` (E-01 to E-04). |
| PR-010 | medium | IN-SCOPE | R1 references; D invariant | `technical-writing.md:45`, `:58` "eleven"; `wcisgc` line 12 scope exclusion | Adding requirement 12 would leave "all eleven" stale. Importing the `wcisgc` scope rule would contradict the shipped scope, which covers documentation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 changes both counts to "twelve"; E-03 omits the `wcisgc` scope rule and the example paragraph. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-8 | Split E-01 because of `IPD-Z602`? | No | One E-item per spec row | All six edits serve one concern (make one spec file match the shipped file) and are verified by one diff (V-01) | yes |
| D-9 | Add a test that the standard contains requirement 12? | No; verify by V-items | Text-presence test | GUIDING_PRINCIPLES P16 and `AGENTS.md` forbid tests that pin document text; the shipped delivery test already covers installation | yes |
| D-10 | Amend spec R-05, R-07, N1, N2 here too? | No; defer to Orders 02 and 03 re-review under `8fvkmp` | Amend all dash and scope rows now | The OQ-02 answer names R-01, R-02, MD-2, AC-01 and says to reconsider Orders 02 and 03, which own those rows | yes |
