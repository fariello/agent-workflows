# Review: stop committing the generated index manifests while keeping them refreshed (child 4r0qp1, Set idxuntrack)

- Subject-Id: 4r0qp1
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `50fc2986` (the plan cites `7f80180e`; every citation below was re-verified at the
current HEAD, and the four sites the plan named are all still present at the lines it gives, so the
drift the plan warned about did not recur in this window). Structural preflight `aw ipd lint --phase
author` conformed BEFORE semantic review and `--phase review-finalize` conformed after the revisions.

THE PLAN'S CORE PREMISE IS TRUE AND I RE-VERIFIED IT INDEPENDENTLY. The four sites it names do put
generated manifest paths into commit path-sets, the finalize transaction really is the sharpest one, and
the sequencing argument (this child must land before child 02's `git rm --cached`) is correct. The plan
is also unusually disciplined in ways worth preserving: it says "locate by SYMBOL, not line number"
because its own inherited citations had drifted once, and it demands mutation checks on its tests.

WHAT ROUND 1 CHANGED is the plan's SCOPE and its model of the failure mode. Two independent problems,
either of which alone would have produced a broken execution:

FIRST, THE FAILURE MODE IS INVERTED (F-7). The plan's Concern says a missed site "either silently
no-ops or hard-fails". I measured it, because the whole sequencing argument rests on it. `git add --
<ignored>` exits 1 and stages NOTHING, including the non-ignored paths in the same invocation, so
`offer_commit` resets its own paths and returns `error` with `staged=()` and NO COMMIT CREATED. The
consequence is not a manifest that fails to be committed; it is the REAL ARTIFACT silently not being
committed. That is the same class of failure (correct work stranded by a generated file) that stranded
lane `ueg5cf` and motivated the parent item in the first place. This changes what "one missed site"
costs, and it is why I added E-06's guard at the shared helper.

SECOND, THE SITE ENUMERATION WAS WRONG IN BOTH DIRECTIONS (F-8/F-9/F-10/F-11). I found the four extra
sites by sweeping BACKWARD from every commit gateway rather than forward from `INDEX`, which is the
technique the plan's own E-05 did not specify:

- `artifact_rename._index_paths_for` (one of the plan's four) is UNREACHABLE DEAD CODE. Its auto-index
  blocks gate on `artifact_type in {"plans","research"}`, but `artifact_types.TYPE_BACKENDS` routes
  plans to `plans_refs` and research to `research_refs`; `artifact_rename` only ever sees
  specs/prompts/backlog/walkthroughs/roadmaps/releases/other, for all of which the helper returns `()`.
  So E-03 as authored would have changed nothing observable.
- The two LIVE producers (`plans_refs`, `research_refs`) and the two `cli.py` aggregation sites that
  actually perform the commit were entirely unscoped.
- Both `*_archive` modules append manifests to a `touched` list committed verbatim, so `aw archive` was
  unscoped too.
- `status_set.py:936-937,971-972`, which the plan cites as commit contributors, are NOT: they append
  `Change(...)` rows to the agent-mode CHANGES REPORT. Following the plan literally would have deleted
  correct reporting and broken a passing test.

Four named, eight real, one of the four inert. I want to state the implication plainly rather than just
fix the list, because it is the reason I widened scope beyond a pure enumeration fix: an enumeration
this Set has already gotten wrong once is not a control I trust to be right the second time. Hence
E-06 (degrade a missed site to a reported skip) and E-08 (exercise every verb under a REAL gitignore,
which is the only step that could have caught F-8/F-9/F-10 empirically).

I also pre-resolved a question the plan handed to the executor as a runtime discovery (F-13). E-01 said
"confirm no rollback/journal step keys on those two entries, and report if one does." Three do. Most
importantly `_rollback_precommit` runs `git restore --staged -- <p>` over `owned_paths`, which exits 1
on an untracked path (measured), so leaving a manifest there would make the rollback path emit a
spurious error precisely when something has already gone wrong. Enumerating them in the plan is better
than an executor finding them mid-transaction.

ONE FINDING IS DELIBERATELY DEFERRED TO CHILD 02, not dropped (F-14): the repo's `.aw/.gitignore` is
byte-identical to `engine._AW_GITIGNORE_TEMPLATE`, and `_ensure_aw_gitignore` back-fills patterns into
already-installed repos. If child 02 edits only the repo's file, every fresh `aw install` and every
managed repo keeps tracking the manifests. It is a real gap in the SET's goal but not in this child's
(this child touches no gitignore), so I recorded it in this child's Deferred section addressed to child
02 rather than silently expanding either plan. Child 02 has not yet been reviewed; this finding should
be carried into that review.

WHAT I DID NOT CHANGE, so the record is honest about the limits of this pass. I did not run the full
suite; I ran the four directly implicated modules (6 + 20 + 44 passed, pasted into the plan as the
executor's reference baseline) and left the full-suite requirement where the plan already had it. I did
not verify child 02's own claims beyond F-14 and the `stale-index` emitters I happened to read. And I
did not attempt to determine whether an ignored-path filter in `offer_commit` could mask a genuine
"caller asked to commit a file it should not have" bug; I judged the trade acceptable because the guard
REPORTS every path it drops, but a maintainer who disagrees should say so, since E-06 is the one item
here that changes shared behavior rather than removing a path from a list.

DISCLOSURE: the plan's `- Author:` names the same tool/model string I run as, so this may be a
SELF-REVIEW rather than an independent one, and is worth correspondingly less. I have no access to the
authoring session's context, so I treated the plan as an unfamiliar artifact and re-derived every claim
from the code; the four missed sites and the inverted failure mode are the evidence that the re-derivation
was not merely a re-reading. Even so, an independent reviewer would be a better control here, especially
on the scope-widening judgement in OQ-02.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | A. Correctness; G. Executability | `agent_workflows/git_commit_helper.py:450-457` | The plan's stated failure mode is wrong and the truth is worse: `git add -- <ignored>` exits 1 staging NOTHING, so `offer_commit` returns `error` and creates NO commit, losing the REAL ARTIFACT's commit, not just the manifest's. Measured: a two-path call with one ignored path returned `status=error`, `staged=()`, `git log` unchanged. A single missed site therefore silently stops artifacts being committed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Concern corrected to state the measured behavior; new E-06 adds an ignored-path filter at the shared gateway (drop + report, `nothing-to-commit` when empty, no `-f`), sequenced FIRST; new V-06 requires a before/after reproduction. |
| PR-002 | high | UNDER-SCOPE | G. Executability; D. Anti-regression | `agent_workflows/artifact_rename.py:62-80,658,804`; `agent_workflows/artifact_types.py:75-118` | One of the plan's four scoped sites is UNREACHABLE dead code: the auto-index blocks gate on `artifact_type in {"plans","research"}` but `TYPE_BACKENDS` routes those types to `plans_refs`/`research_refs`, never here, so `_index_paths_for` returns `()` for every type actually routed. E-03 as authored would have fixed nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-8 added; E-03 rewritten to fix the LIVE gateway and producers, still remove the dead contribution, and record that it was dead so the next reader is not misled. |
| PR-003 | high | UNDER-SCOPE | A. Correctness; G. Executability | `agent_workflows/plans_archive.py:159-182,283-307`; `agent_workflows/research_archive.py:274-283,387-411` | Two commit-path contributors missed entirely: both archive modules append the manifests to the `touched` list that `_offer_archive_commit` commits verbatim, so `aw archive plans`/`aw archive research` would hit PR-001 and commit nothing. `research_archive` appends with no `exists()` guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | F-9 added; new E-07 removes both append loops (keeping regeneration) with V-07 requiring pasted `--stat` evidence from both verbs. |
| PR-004 | high | UNDER-SCOPE | A. Correctness; C. Architecture | `agent_workflows/plans_refs.py:413-423,451,499`; `agent_workflows/research_refs.py:310-322,347,367`; `agent_workflows/cli.py:8557,11057` | The two LIVE `MutationResult.index_paths` producers and the two aggregation sites that actually commit them were unscoped, so `aw group`/`aw rename`/`aw research mv` were unprotected. The `MutationResult` docstring documents the contract being removed ("The commit path-set is `touched_paths + index_paths`") and would go stale. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | F-10 added; E-03 now fixes the two `cli.py` aggregation sites (the shared choke point covering all three producers), removes all three producer helpers, and mandates the docstring sync. |
| PR-005 | medium | IN-SCOPE | A. Correctness; D. Anti-regression | `agent_workflows/status_set.py:912-988` | The plan's citation of `status_set.py:936-937,971-972` as commit contributors is FALSE: those lines build the agent-mode `Change(...)` report, not a commit path-set. The only commit contributor in the module is `_index_paths_for_types` via `_offer_self_commit:1165`. Executing the plan literally would have deleted correct reporting and broken `test_aw_set_agent_output_includes_index_in_changes`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-11 added; E-02 rewritten to name the single real site, to say explicitly DO NOT touch `_auto_index_types`, and to require that test to keep passing UNCHANGED as proof. |
| PR-006 | medium | IN-SCOPE | E. Testing | `tests/test_auto_index_on_mutation.py`; `tests/test_selfcommit_adoption.py:265,348` | E-04's premise is false for the module it names: `test_auto_index_on_mutation.py` has ZERO commit assertions (`grep -c commit` -> 0), so "invert each case that asserts a manifest was committed" has no referent there. The real commit assertions are in `test_selfcommit_adoption.py`, which the plan never names. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-12 added; E-04 retargeted to the two real assertions, keeps the 6 refresh tests as the unchanged proof the refresh half survived, adds a case for E-06, and `Scope-Paths` extended to the test module. |
| PR-007 | medium | UNDER-SCOPE | A. Correctness; G. Executability | `agent_workflows/ipd_lifecycle.py:1681-1688,2410-2412` | E-01 delegated "confirm no rollback/journal step keys on those entries" to the executor as a runtime discovery. THREE do: `_rollback_precommit` runs `git restore --staged` over `owned_paths` (exits 1 on an untracked path, measured), `git_index_entries` captures stage lines, and `index_json_before`/`index_md_before` snapshot content and are read by nothing (verified). Leaving a manifest there makes rollback emit a spurious error exactly when something already went wrong. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | F-13 added; E-01 now enumerates all three consumers with the measured behavior and demands a recorded decision on each; V-01 requires each one's resolution pasted. |
| PR-008 | medium | UNDER-SCOPE | C. Architecture; F. Principles | `agent_workflows/engine.py:4274-4308,5323-5370` | The repo's `.aw/.gitignore` is byte-identical to `engine._AW_GITIGNORE_TEMPLATE` (verified) and `_ensure_aw_gitignore` back-fills patterns into installed repos. Child 02 edits only the repo file, so without a template + back-fill change every fresh install and every managed repo keeps tracking the manifests, and the Set's fix does not generalize. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | deferred | Deferred to child 02 (which owns all gitignore work); recorded as F-14 and as an explicit named dependency in this child's Deferred section so it cannot be lost. Not a defect of THIS child, which touches no gitignore. Must be carried into child 02's review. |
| PR-009 | medium | UNDER-SCOPE | E. Testing; D. Anti-regression | plan `## Detailed Implementation Checklist`, E-05 | E-05's forward sweep (grep `INDEX*`, classify) is the same method that produced the incomplete four-site list, so it could not have caught PR-002/003/004, and no step exercised the verbs under a real gitignore. Validation could pass while `aw archive` remained broken. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-05 now requires a BACKWARD sweep from every commit gateway as well; new E-08 applies child 02's ignore locally in a scratch tree and exercises all six mutating verbs, with V-08 requiring the experimental ignore be proven reverted. |
| PR-010 | low | IN-SCOPE | G. Executability | plan `## Approval and execution gate` | `Cohesion rationale: not required` while E-03 spans four files. The multi-file item needs its justification recorded so a reviewer can tell a cohesive change from a bundled one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Size assessment updated (8 leaves / 3 groups) and a cohesion rationale written: E-03's four files are one data-flow path (field + three producers + two aggregation sites) with no independently verifiable intermediate state. |
| PR-011 | low | IN-SCOPE | F. Principles (honest documentation) | `agent_workflows/plans_refs.py:148,150`; `agent_workflows/git_commit_helper.py:355-366` | Two in-code docstrings become false: `MutationResult`'s "The commit path-set is `touched_paths + index_paths`", and `offer_commit`'s promise that ONLY the given paths are staged "including ... any regenerated index". The plan's `Spec / documentation sync` said `N/A`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `Spec / documentation sync` rewritten to name both syncs as parts of E-03 and E-06 rather than N/A. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Delete `_index_paths_for_types` (and the three `_index_paths_for` helpers) or keep them returning empty? (the plan's OQ-01, handed to the executor) | Delete them, with their call sites. | Keep returning `()` with an explanatory docstring, which the plan allowed as an equal option. Rejected: once E-02/E-03 remove the only call, a retained function is dead code that reads as deliberately disabled, and the next reader cannot tell whether re-enabling it is intended. | `agent_workflows/status_set.py:1165` is `_index_paths_for_types`'s ONLY caller (grep over `agent_workflows/*.py`), and that call is itself removed by E-02; same shape for `plans_refs.py:451,499`, `research_refs.py:347,367`, `artifact_rename.py:658,804`. | yes |
| D-2 | Add a defensive ignored-path filter to the SHARED `offer_commit`, or keep the change confined to the enumerated call sites? (the plan's implicit assumption; now OQ-02) | Add it, and sequence it FIRST. | Rely on E-05's sweep alone. Rejected because that is the control that already failed here: the author's forward sweep produced four sites when there are eight. Also considered `git add -f`, rejected outright as it force-commits the very files the Set exists to untrack. | PR-001's measurement (a mixed path-set yields `status=error`, `staged=()`, no commit) makes a missed site cost the ARTIFACT's commit; `agent_workflows/git_commit_helper.py:450-457`. The guard is additive and inert while nothing is gitignored. | yes |
| D-3 | Does the installer-template gap (PR-008) belong in this child, child 02, or a new item? | Child 02, recorded as a named dependency in this child's Deferred section. | Expand this child's scope to `engine.py` (rejected: this child deliberately touches no gitignore, and `Scope-Paths` would then span the untracking work it is sequenced to precede). A third child (rejected as premature before the maintainer sees the finding). | `engine._AW_GITIGNORE_TEMPLATE == Path('.aw/.gitignore').read_text()` is `True`; `_ensure_aw_gitignore` (`engine.py:5323-5370`) is the back-fill path. Child 02's `Scope-Paths` already owns `.aw/.gitignore`. | yes |
| D-4 | E-08 needs a REAL gitignore to be meaningful, but child 02 owns that change. How can this child validate against it without pre-empting child 02? | A temporary LOCAL experiment in a scratch clone/worktree, explicitly reverted, with V-08 requiring proof of reversion. | Move the validation into child 02 (rejected: then child 01 ships unvalidated against the only condition that matters). Actually commit the ignore here (rejected: that IS child 02, and would invert the Set's deliberate sequencing). | The plan's own `Deferred` reasoning that doing the ignore here "would mean this child's own validation runs against files that are simultaneously tracked and gitignored"; `.aw/.gitignore` is a plain file a scratch tree can carry uncommitted. | yes |
