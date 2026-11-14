# Review findings: plan 653ndz

- Subject-Id: 653ndz
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `2a7718c36` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_command_surface_declarations.py` printed `2 passed in 0.48s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-003 | MD-15, Section 7.2 |
| `## Detailed Implementation Checklist` (E-05) | E-05 lacked explicit directory creation for `.aw/state/653ndz/` | Added explicit `mkdir -p .aw/state/653ndz` instruction | PR-003 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list of 2 steps plus Mermaid `flowchart TD` | PR-002 (Requirement 12b) |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`") and narrow safety stop if `tools/fixture_codemod.py` or test modules are missing | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Produces tracked census tables F-30 and F-31 cited by all downstream batch conversion plans (Orders 38-40, 50, etc.) for `hand` conversion quotas, and documents `tools/fixture_codemod.py` in `tools/README.md`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact finishing plan with 2 execution items (E-05, E-06) across 1 work Scope-Path (`tools/README.md`).
4. Yes. `- Scope-Paths:` explicitly declares `tools/README.md` and the plan file.
5. Yes. The pilot uses a throwaway git worktree (`.aw/state/653ndz/pilot`), and inaccurate census counts would misallocate conversion quotas to downstream batch plans.

AW-TIER: standard

### Step R1

- Checked: `tools/README.md`; governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 6, Section 7 step 6); sibling plans `y3uowx` (Order 172), `j2xjtt` (Order 173), `n0li9v` (Order 216); and batch plans `x05v02`, `7qxey9`, `nbfg7w`, `1upea0`.
- Verified that `tools/fixture_codemod.py` and its test modules are authored and tested by upstream plans `y3uowx`, `j2xjtt`, and `n0li9v` in `- Item-Dependencies:`, leaving this plan scoped strictly to the pilot, census generation, documentation, and gate verification.

### Step R2

- Checked: 1:1 bijection between E-05..E-06 and V-05..V-06; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:y3uowx, executed:j2xjtt, executed:n0li9v`; and verification reachability.
- Confirmed that the throwaway pilot worktree (`.aw/state/653ndz/pilot`) is created and removed cleanly within E-05/V-05.

### Step R3

- Checked: worktree isolation and git state hygiene.
- The pilot worktree is created under `.aw/state/653ndz/pilot` (gitignored), runs in a detached head, and is removed before finishing, ensuring zero untracked state leaks into the checkout.

### Step R4

- Checked: right-sizing, anti-regression, and conceptual density.
- Sized cleanly (2 items, 1 work path) as the finishing part of the codemod family following the round-3 split.

### Step S5

- Checked: no unresolved open questions; OQ-01 and OQ-02 are resolved. All three review decisions (D-1..D-3) are recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `653ndz`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md:144-157`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:33-46` | The gate lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`") and lacked a narrow safety stop for missing prerequisite tool or test modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership and narrow unsafe-condition prerequisite stop (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / R6 | `.aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md:83-87`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` (strong). |
| PR-003 | LOW | IN-SCOPE | R2 / Executability | `.aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md:53-56` | E-05 directs saving `census-files.txt` and creating pilot worktree under `.aw/state/653ndz/` without an explicit directory creation step (`mkdir -p .aw/state/653ndz`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/653ndz` instruction in E-05 (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 653ndz` itself"), and a narrow unsafe-condition stop if prerequisite tool `tools/fixture_codemod.py` is absent | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop | `.aw/system/workflows/plan-review/steps/s7-finalize.md:33-46`; `AGENTS.md` "Agent execution contract" | yes |
| D-2 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating the pilot verification, census generation, documentation, and gate verification pipeline | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-3 | How should directory preparation for `.aw/state/653ndz/` be handled in E-05? | Add an explicit `mkdir -p .aw/state/653ndz` instruction in E-05 before creating files or the pilot worktree | Rely on implicit directory creation by git or shell redirects (risks failure if directory does not exist) | `s7-finalize.md`; `E-05` | yes |
