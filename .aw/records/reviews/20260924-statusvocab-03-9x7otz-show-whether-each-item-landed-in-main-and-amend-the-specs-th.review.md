# Review findings: plan 9x7otz

- Subject-Id: 9x7otz
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 03 of Set `statusvocab`, the dependent child (`- Item-Dependencies: executed:cyamvi`)
and the ONLY child licensed to amend a spec. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) BEFORE semantic review, and `--phase review-finalize` conforms after the
revisions, so nothing below is structural. The plan file was committed and unchanged, so no pre-review
snapshot was needed.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
MEASURING the claims against the tree, and the two most serious findings came from doing exactly that:
counting the specs the plan claims to enumerate, and reading the renderer the plan proposes to change.

WHAT HOLDS, AND IT IS THE MAJORITY OF THE PLAN. All eight declared spec paths EXIST at the declared
subdirectories, which is notable because the sibling `cyamvi`'s round 1 found all seven of its spec
paths stale; this plan already absorbed that correction. The directory-is-the-authority premise is
correct and correctly cited (the 2026-09-19 maintainer ruling is recorded verbatim at `edge_satisfied`).
F-01's directional asymmetry is the right design frame, and `run_selection_policy` plus
`artifact_audit.classify_difference` independently corroborate that a non-`executed` terminal directory
must not be read as failure. OQ-01's `nmlx47` example is verified: it is in `superseded/` with
`- Status: superseded`.

WHAT DOES NOT HOLD. The plan says "THE EIGHT SPECS THAT NAME A LEGACY STATUS TOKEN" and repeats the
figure in its Concern, Scope, F-03, and `Spec / documentation sync`. Measured across the tree, 23 spec
files contain at least one legacy token. The eight are a defensible SCOPE JUDGEMENT and a false CENSUS,
and the difference matters because the plan's own Concern argues a stale spec "would re-authorize the
removed vocabulary for every future plan reviewed against it" - an argument that, taken at the census
reading, obliges 23 edits.

```text
spec files carrying at least one legacy token : 23
declared by this plan                          : 8
excluded (ordinary-English `blocked`/`partial`,
          or `superseded/`)                    : 15
  e.g. attention-visible-backlog-tier   blocked x29
       attention-registry-cross-tree    blocked x10
       release-record-and-blocker-gate  blocked x9
       ipd-structure-and-linting        blocked x9, partial x3
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (correctness) | `.aw/records/specs/` (whole tree, measured); plan `E-03`, `F-03`, Concern, Scope | "THE EIGHT SPECS THAT NAME A LEGACY STATUS TOKEN" IS A FALSE COMPLETENESS CLAIM. 23 `.spec.md` files carry at least one legacy token, not eight. The eight are the right SCOPE (they describe the runner's written vocabulary) but the plan presents them as an exhaustive census, in four places. Two concrete harms: an executor re-deriving the census at execution finds 23, cannot tell which 15 were deliberately excluded or why, and either edits undeclared paths (which the finalize scope gate then refuses) or silently trusts a stale number; and a reviewer cannot check the claim, because the plan records no exclusion rule. This is also the live-artifact-count pattern the IPD rubric names, and the sibling `cyamvi` took PR-005 for the same class of error. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the scope is a JUDGEMENT not a census, gives the measured 23, records the explicit exclusion rule (ordinary-English usage, or `superseded/`) with the excluded files and counts named, forbids silently widening to 23, and REQUIRES the census re-derived at execution with any undeclared status-literal file REPORTED rather than edited. F-04 added. |
| PR-002 | HIGH | IN-SCOPE | C (architecture) / A (correctness) | `agent_workflows/run_viewer.py` `render_steps_table`, `audit_step_artifact`; `agent_workflows/artifact_audit.py` `_disposition_dir`, `ArtifactAudit.actual_dir`; `runner_shared.plan_bucket` | E-01 WOULD ADD A SECOND RESOLVER FOR A FACT THE TABLE ALREADY HAS, AND THE SECOND ONE IS WRONG FOR ARCHIVED PLANS. E-01 said to read the directory "exactly as `edge_satisfied`'s `executed:` branch already does via `plan_bucket`". But `render_steps_table` ALREADY calls `audit_step_artifact` once per row, and `ArtifactAudit.actual_dir` is the disposition directory computed by `_disposition_dir`, which explicitly climbs a monthly shard (`re.fullmatch(r"\d{6}", parent)` -> `executed/202608/` yields `executed`). `plan_bucket` returns the RAW parent segment and has no such branch, so an archived plan would yield `202608`, and the column would report a landed plan as NOT landed - the exact false-negative class F-01 exists to prevent. It also duplicates a per-row path resolution and violates the project's own canonical-mechanism rule. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 rewritten to feed the shared predicate from the per-row `ArtifactAudit.actual_dir`, with the archived-shard defect named as the reason; the predicate stays thin and shared so both hosts reach one object; `edge_satisfied` is retained as the precedent for WHY the directory is authoritative and explicitly NOT as the code to copy. V-01 now demands an archived case. F-05 added. |
| PR-003 | MEDIUM | UNDER-SCOPE | A (correctness) | `agent_workflows/run_viewer.py` `render_steps_table` `short` branch vs default branch | `render_steps_table` HAS TWO COLUMN VARIANTS AND THE PLAN NAMED ONE. The `short` branch renders 5 headers and the default renders 9, and each has its own `headers` list, its own parallel `aligns` list, and its own `rows.append([...])`. A column added to one variant only vanishes from half the surfaces, and a length mismatch between the three lists skews the box art rather than raising an error. The plan's Concern quotes only the 5-column set, so an executor could reasonably edit that branch alone. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now names both variants and all three parallel lists in each, requires both updated, and adds the module's own no-glyph constraint (`render_box_table` measures with `len(strip_ansi(cell))`, so a 2-code-point grapheme skews the column). V-02 now requires BOTH variants pasted plus one color-disabled render. |
| PR-004 | MEDIUM | IN-SCOPE | E (verification) | plan `V-02`; `.gitignore` | V-02 REQUIRED EVIDENCE FROM A GITIGNORED DIRECTORY WITH NO FALLBACK. It demanded `aw runs` output for `run-20260924T050407Z-3108751`; `.aw/records/runs/` is gitignored and is ABSENT from this worktree entirely, so in a lane or a fresh clone the evidence is unobtainable and the item would either be marked complete without it or stall. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 carries an explicit note: if the run directory is absent, SAY SO and substitute a synthetic run directory carrying the same three status-versus-landed disagreements rather than skipping the evidence. The gate repeats the rule generally. |
| PR-005 | MEDIUM | IN-SCOPE | G (executability) | plan `## Approval and execution gate` | The gate was ONE sentence and carried no execution contract: no scope fence, no honesty rule, no commit discipline, no lifecycle transition, no statement that the consequential half is eight spec amendments (five to `approved` specs), and no statement that the `executed:cyamvi` ordering is enforced rather than advisory. For the Set's only spec-amending child, the missing do-not-edit-an-undeclared-spec rule is the most costly omission, since PR-001's re-derived census will surface undeclared candidates. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with `Size assessment: standard`; what a human is approving; the enforced dependency edge and why hand-execution ahead of Order 01 is wrong; OQ-01 recorded resolved; a declaration-style scope fence; the non-discretionary do-not-edit-an-undeclared-spec rule with the run-end reconciliation named; the bare-`pytest` honesty rule with the absent-run-directory fallback; `aw commit` path-scoped and never-push with the `runner_shared.py` overlap noted as not a hazard; and the conditional lifecycle transition. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should `Landed` distinguish "in `main`" from a terminal directory that is not `executed/` (superseded, not-executed)? | YES, as the plan recommended, with a four-value mapping made explicit: `yes` for `executed/` (including a monthly shard), `n/a` for `superseded`/`not-executed`/`reusable`, `no` for a plan still in `pending/`, `unknown` for an unresolvable id6. | Two values (`yes`/`no`). Rejected: it reads `no` for a plan that correctly never intended to land, mimicking a failure, which is the same false-signal class F-01 is about. | Resolved from repository evidence rather than asked. `nmlx47` verified in `.aw/records/plans/superseded/` with `- Status: superseded`. The tree already draws this distinction in code: `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` enumerates four terminal segments rather than treating non-`executed` as failure, and `artifact_audit.classify_difference` earns `CLASS_RETIRED` from a `RETIRED` banner rather than inferring failure from the directory. The `unknown` value was already required by the plan's own E-02. | yes |
| D-2 | PR-001 shows the scope is 8 of 23. Should the plan be widened to all 23, or its judgement recorded? | Record the judgement and its exclusion rule; keep 8. | Widening to 23. Rejected: a spec using `blocked` as ordinary English is not stale, editing it churns approved contracts for no contract change, and two of the 23 are in `superseded/`, which must not be rewritten. | The excluded files' occurrences are ordinary English or retired records, verified by reading the counts per file. AGENTS.md requires a spec edit to be DECLARED, so widening at execution would edit undeclared paths and refuse at finalize. The honest fix is a recorded rule plus a re-derivation that REPORTS rather than edits. | yes |
| D-3 | Does the `Landed` column need a spec amendment of its own (it adds an operator-facing column that `0718`/`uonrjg` describe)? | No new spec obligation beyond the eight already declared; both `0718` and `uonrjg` are already in `- Scope-Paths:`. | Adding a ninth spec, or declaring the column out of spec scope. Rejected: the two specs that describe the run summary and its status styling are already declared and already being amended by E-03, so the column's contract can land in the same edit. | `0718` (`aw-run-deterministic-run-and-verify`) and `uonrjg` (`cross-artifact-lifecycle-symbols-and-ansi-status-styling`) are both in the declared eight. No undeclared spec describes the summary table. | yes |
| D-4 | The run directory underpinning F-01's measurement is absent from this worktree. Does that block the review? | No. Corroborate by proxy, and fix the plan's dependence on it (PR-004) rather than raising the absence as a defect. | Raising missing evidence as a finding, or reading the main checkout. Rejected: the lane is the complete authorized workspace, and `.aw/records/runs/` is gitignored so no clone has it. | Same as the `zngiya` and `787hb4` reviews' equivalent decision. The three F-01 counter-examples were corroborated directly: `m7gvuz` and `xdvglg` are both in `executed/`, and `nmlx47`'s superseded state was verified for OQ-01. What the absence DID reveal is a real plan defect, now PR-004. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent 9x7otz -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent 9x7otz -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

all 8 declared spec paths                     EXIST at their declared subdirectories (verified file by file)
spec files carrying a legacy token (tree-wide) 23        <- PR-001: the plan says 8
  of which declared                            8
  of which excluded                           15         (ordinary English, or superseded/)

render_steps_table variants                    2: short (5 headers) and default (9 headers)
  each with its own headers / aligns / rows.append triple      <- PR-003
ArtifactAudit.actual_dir                       already computed once per row by audit_step_artifact
artifact_audit._disposition_dir                climbs a monthly shard: executed/202608/ -> 'executed'
runner_shared.plan_bucket                      returns the RAW parent segment (no shard branch)  <- PR-002
run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS  executed, superseded, not-executed, reusable   (D-1)

nmlx47                                         .aw/records/plans/superseded/, - Status: superseded  (OQ-01)
m7gvuz, xdvglg                                 both in .aw/records/plans/executed/   (F-01 corroborated)
.aw/records/runs/                              ABSENT from this worktree (gitignored)  -> PR-004, D-4
```

NOT RE-RUN AT REVIEW, stated rather than implied: the suite. This review changed only planning prose, so
the authored baseline (`8850 passed, 5 skipped, 2 xfailed` on `main` `a631a1f6`) is neither confirmed nor
refuted here; the plan already requires re-deriving it at execution.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open. OQ-01 was resolved
from repository evidence (D-1), so this plan now carries NO open questions.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: the
consequential half of this plan is EIGHT SPEC AMENDMENTS, five of them to `approved` specs, and a spec is
the contract every future plan is reviewed against. The plan is correctly last in the Set and its
`executed:cyamvi` edge is enforced at dispatch, so it cannot land a contract ahead of the implementation.
