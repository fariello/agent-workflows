# IPD: Assess documentation - repository written docs for agent-workflows

- Date: 2026-07-03
- Concern: documentation (repository written docs: README, ARCHITECTURE, DECISIONS,
  CONTRIBUTING, AGENTS, index.md, release-review MANIFEST/README)
- Scope: whole repository's written documentation (not the workflow instruction bodies
  themselves, which are the framework's "product")
- Status: PENDING (awaiting human approval; not executed)
- Author: assess-documentation workflow (agent)

## Goal

Ensure this repo's written documentation is accurate (describes what the framework does
today), complete enough for a newcomer to orient and use it, and internally consistent
after many rounds of change. This repo's stated value IS "disciplined, honest
documentation" (CONTRIBUTING.md), so doc accuracy is a first-class quality axis here.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (present; P2 = honest docs, P8 = single
  source of truth).
- Plan/IPD lifecycle: `.agents/plans/pending/` + terminal `done/` (this repo predates
  the D26 `executed/` canonicalization and keeps `done/` as an accepted alias).
- Contributor contract: `AGENTS.md` (workflow pointer), `CONTRIBUTING.md` (doc-sync
  rules, no em dashes, single-source).
- Docs present: README, ARCHITECTURE, DECISIONS, GUIDING_PRINCIPLES, CONTRIBUTING,
  AGENTS at root; `.agents/workflows/index.md`, `release-review/README.md`,
  `release-review/MANIFEST.md`. No CHANGELOG (DECISIONS.md serves that role).

## Overall assessment

The documentation is broadly accurate and genuinely strong: no stale
`release-review.zip` or old installer references remain, no broken internal `.md`
links, `repository-review/` mentions are correct (they describe legacy migration), and
there are no aspirational claims. Verdict: **adequate**.

Re-verification note (findings re-checked against the current repo before finalizing):
between drafting this IPD and finalizing it, the top-level README was rewritten as an
on-ramp, which **already resolved D3, D4, and D5** (plan/IPD lifecycle now explained via
the pipeline diagram; DECISIONS named as the changelog; a newcomer pipeline primer
present). Only **D1 and D2** remain actionable, both in `release-review/MANIFEST.md`.

## Findings

Severity = impact if left alone; Remediation Risk = the Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| D1 | Medium | Low (usability) | software-engineer | accuracy | `release-review/MANIFEST.md` Files table lists `plan-review.md` (which is NOT in `release-review/` - it lives in the `plan-review/` sibling dir, D17) and OMITS two items that ARE present: `MANIFEST.md` itself and `templates/`. So the table both names a missing file and misses two present ones. | Verified: `plan-review.md` in MANIFEST vs. `ls .agents/workflows/release-review/plan-review.md` -> not found (actual: `.agents/workflows/plan-review/plan-review.md`); `MANIFEST.md` and `templates/` present but absent from the table. |
| D2 | Low | Low (usability) | software-engineer | accuracy/drift | `release-review/MANIFEST.md` enumerates the `assess-*` commands ("performance, security, secrets, accessibility, testing, guiding-principles, compliance, and more") - a hand-maintained partial list that drifts as lenses are added. The authoritative list is `index.md`. | `release-review/MANIFEST.md` lines ~45-47. |
| D3 | Medium | - | complete-novice | completeness | RESOLVED before finalization. The README rewrite added the plan/IPD lifecycle (pipeline diagram, `assess-<concern> -> IPD in .agents/plans/pending/ -> ... -> execute`). No action needed. | README.md line ~94 (pipeline diagram) and the setup/lifecycle mentions. |
| D4 | Low | - | software-engineer | navigation | RESOLVED before finalization. README now states DECISIONS.md "is also the project's changelog". No action needed. | README.md line ~166. |
| D5 | Low | - | complete-novice | getting-started | RESOLVED before finalization. The README rewrite's usage section now shows the pipeline and states the assess workflows "do not change code / do not auto-execute". No action needed. | README.md usage section + pipeline block. |

## Proposed changes (ordered, validatable)

Only D1 and D2 remain (D3-D5 were resolved by the README rewrite). Both are low
Remediation Risk and both edit only `release-review/MANIFEST.md`.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | D1 | Fix the MANIFEST Files table: remove the `plan-review.md` row (not a release-review file; reference it as the sibling `../plan-review/plan-review.md` in prose if useful), and add the two present-but-undocumented items `MANIFEST.md` and `templates/`. | `.agents/workflows/release-review/MANIFEST.md` | Low | Every file named in the Files table exists in `release-review/`, and every top-level item in `release-review/` is either listed or intentionally omitted. |
| 2 | D2 | Replace the hand-enumerated assess-command list in MANIFEST with a pointer to `index.md` as the authoritative command list (keep at most one or two illustrative examples). | `.agents/workflows/release-review/MANIFEST.md` | Low | MANIFEST no longer enumerates a drift-prone command list; points to index.md. |

## Deferred / out of scope (with reason)

- None deferred. All findings are low Remediation Risk. (No finding met the Medium-High
  bar.)
- Explicitly NOT proposed: reformatting/rewriting the docs for style, or adding a
  separate CHANGELOG.md (over-scope - DECISIONS.md already serves that role; D4 just
  points to it). Guarded by the Complexity axis.

## Scope check

- Over-scope: none proposed. Avoided adding a CHANGELOG and avoided doc-style churn.
- Under-scope: the plan-lifecycle explanation (D3) is the one genuinely missing piece
  for a newcomer; Step 3 adds it.

## Required tests / validation

- After Step 1/2: `ls` every file named in the MANIFEST Files table and confirm it
  exists at the stated location; confirm no drift-prone command enumeration remains.
- After Step 3/4/5: a read-through from a cold-start perspective - can a newcomer, from
  README alone, learn what the workflows are, how to run them per tool, and how the plan
  lifecycle works?
- Repo convention checks: no em dashes added (CONTRIBUTING rule); internal `.md` links
  resolve.

## Spec / documentation sync

This IPD's changes ARE documentation; no code behavior changes. No separate spec to
sync. If the plan-lifecycle wording is added, ensure it matches the D26 canonical
(`pending/` -> `executed/`, `done/` alias) and the assess harness's Step 0.

## Open questions

1. Terminal-dir wording in the new README lifecycle section: state the canonical
   `executed/` with `done/` as alias (matches D26), even though THIS repo uses `done/`?
   (Recommended yes, for accuracy about the framework's default.)
2. Put the DECISIONS-as-changelog pointer (D4) in README or CONTRIBUTING? (Recommend
   README, where a reader looks first.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. All items are low-risk documentation fixes; none are
urgent. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow on it).
2. On approval, apply Steps 1-5, run the validation, keep changes em-dash-free.
3. Then move this IPD from `.agents/plans/pending/` to `.agents/plans/done/` (this
   repo's terminal dir).
