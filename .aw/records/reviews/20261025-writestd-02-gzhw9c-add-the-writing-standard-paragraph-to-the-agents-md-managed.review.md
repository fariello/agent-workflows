# Review findings: plan gzhw9c

- Subject-Id: gzhw9c
- Subject-Type: ipd
- Reviewed-At: 2026-11-05
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `af311d95f` in runner review-sweep lane `run-20261106T024139Z-372975` (non-interactive). The lane-input copy (revision 3) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions; after revisions `--phase review-finalize` is clean (one info `IPD-Z602`).

Controlling context: the maintainer answered `g4719s` OQ-02 on 2026-11-05 with "Keep shipped file; amend spec; re-scope g4719s (recommended)". That answer keeps the standard shipped by `0cbfcc706` and its dash ruling ("This standard adds no dash rule of its own"), and says to reconsider Orders 02 and 03. This review applies it to Order 02.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Title, Concern, Scope, Goal | Add paragraph; widen dash rule in six places; DECISIONS entry | Amend spec `ecmw83` R-05, AC-03, N1, N2 to the shipped state | PR-001, PR-002. |
| E-01 to E-08 | Eight code and policy edits | E-01 spec amendment; E-02 confirm and commit | PR-001, PR-002. |
| Scope-Paths | 11 files | The spec file only | PR-001, PR-002. |
| Gate | Partial contract; old standard path | Full contract; shipped path; `g4719s` precondition | PR-004, PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it amends spec `ecmw83`.
2. No.
3. No: 2 E-items.
4. Yes: one Scope-Path, a `.spec.md`.
5. Low: a spec text edit, reversible through git.

Tier: simple.

### Step Q

- Checked: the remaining work is one spec file; no code, no shipped behavior changes; reversal is a git revert. Gate is `executed:g4719s` because both plans edit the same spec.

### Step S5

- Checked: no open questions. The dash and path decision is the maintainer's 2026-11-05 answer (`g4719s` OQ-02); D-1 and D-2 apply it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | OVER-SCOPE | R1 references | `agent_workflows/engine.py` "### Technical writing standard"; `AGENTS.md` "### Technical writing standard"; `tests/test_technical_writing_delivery.py` (2 passed at review); `python3 -m tools.regen_agents_block --check` "Up to date" | E-01, E-03, E-04 add a managed paragraph, regenerate the block, and add an install test that `0cbfcc706` already shipped. Executing them would add a second, conflicting paragraph and a duplicate test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed; E-02 now confirms the shipped state. |
| PR-002 | blocker | OVER-SCOPE | D invariant | `g4719s` OQ-02 answer 2026-11-05; `.aw/system/workflows/technical-writing/technical-writing.md` "This standard adds no dash rule of its own" | E-02, E-05, E-06, E-07 widen the dash rule in six places and record a DECISIONS entry for it, reversing the maintainer's kept ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed. |
| PR-003 | medium | UNDER-SCOPE | G spec sync | spec `ecmw83` R-05, AC-03, N1, N2 | The spec still requires the widened dash clause and a "Technical artifact writing" heading, and its non-goals contradict the shipped scope. Order 01 amends only R-01, R-02, MD-2, AC-01, AC-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 amends the four rows; spec listed in Scope-Paths. |
| PR-004 | medium | IN-SCOPE | G execution contract | plan gate | Gate named the old `standards/` path and lacked fence-as-declaration, paste-output MUST, and finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten. |
| PR-005 | low | UNDER-SCOPE | R7 cross-plan | `8fvkmp` child row 02 and completion criterion "widened dash rule" | The orchestrator and Orders 03, 07 to 09 still assume the widened dash rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Recorded under Deferred with carrier `8fvkmp` for those plans' own re-reviews (fix in the owning plan). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep any dash-widening edit? | No | Widen only P13 or only the contract | `g4719s` OQ-02 maintainer answer keeps the shipped dash ruling | yes |
| D-2 | Retire the plan instead of re-scoping? | Re-scope to the spec amendment | Retire to `not-executed/` and move R-05 work into `g4719s` | The R-05, AC-03, N1, N2 amendment is real remaining work owned by this Order; retiring is a lifecycle act outside a review | yes |
| D-3 | Tier | simple | standard | Step T answers; `Size assessment: standard` kept because `IPD-Z601` accepts only `standard` or `exception` | yes |
