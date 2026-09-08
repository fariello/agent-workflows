# Review: canonical run-root analytics namespace and discovery isolation (child xbwq8n, Set runanalytics)

- Subject-Id: xbwq8n
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `44d4950d`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions. Authored
by a different agent (Codex) and delivered through `.aw/inbox/`, so its claims were treated as untrusted
external input and re-measured rather than accepted.

METHOD. This plan's subject is entirely "what does the current code do", so nothing was reasoned about
that could be executed instead. All three run enumerators were CALLED against a synthetic reserved-tree
fixture; `state_root` and the project-context resolver were read; the `.aw/records/runs` literal was
grepped across `agent_workflows/`; the worker path-fence predicate was called; and the two candidate
controlling specs were opened and their statuses checked.

THE PLAN'S CORE JUDGEMENT IS RIGHT AND IS THE REASON THIS IS AN APPROVE. Reserving a namespace inside the
already-disposable runs tree, rather than inventing a second storage location with its own lifecycle and
cleanup policy, is the correct call and is well argued. Rejecting by CONTAINMENT before applying the run
predicate, rather than by name shape, is also right, and the plan reached that conclusion on its own. The
deferrals are clean and correctly assigned (cache formats to 02/07, leaf registration to 08, legacy-root
deletion excluded as a migration).

BUT THE PLAN DEFEATED ITS OWN PURPOSE IN ITS GOAL SENTENCE, which is the blocker. It stated the target as
`<repo>/.aw/records/runs/analytics/`, hardcoding the exact literal whose duplication this IPD exists to
eliminate, and the conventions section softened `state_root` to something to "reuse or deliberately
supersede". Measured: the runs root is RELOCATABLE, because `project_context` derives the records root
from `records_backend` (`repository` -> `<repo>/.aw/records`, `companion` -> `<repo>.aw/records` or a
configured `companion_dir`, `home` -> a per-project dir outside the repo, at `project_context.py:783-790`),
while `runner_shared.state_root` returns `repo / ".aw" / "records" / "runs"` and consults no authority at
all (`runner_shared.py:188-189`). So `state_root` is not an authority to reuse; it IS the defect. An
executor following the original Goal would have produced a correctly-named helper wrapping the same
hardcoded path and satisfied every V-item, and nine downstream plans would then have inherited it. This
also directly contradicted the source prompt, which required resolution through the storage authority
precisely because companion and home layouts exist.

THE SCOPE DECLARATION COVERED A THIRD OF THE SUBJECT. The literal is constructed at SIX live sites
(`runner_shared.py:189`, `run_viewer.py:1080`, `completion.py:452`, `run_cli.py:257`, `oc_runipd.py:5023`,
and the string hint at `worktree_lease.py:876`), plus four prose-only sites. `Scope-Paths` named two
source modules. A plan can only finalize against paths it declared, so this one could have consolidated
two of six and finalized clean.

THE MEASUREMENT THAT MOST CHANGES THE WORK is that there are THREE enumerators, not the two the plan
names, and they disagree about the reserved tree. Exercised with a synthetic
`analytics/snapshots/run-20260101T000000Z-1/state.json`: `discover_run_dirs` does NOT return it, but only
because its `run-` prefix test applies one level below the root, so nested output is skipped by ACCIDENT
OF DEPTH rather than by any reservation; `resolve_target_runs` by name or substring returns nothing; but
`resolve_target_runs` given that directory's EXPLICIT PATH RETURNS IT as a run, because that branch
(`run_viewer.py:1113-1129`) tests only `is_dir()` plus the presence of `state.json`; and
`completion.run_id_candidates` (`completion.py:448-460`) returns every non-dot child with no `run-` filter
whatever, so it offers `analytics` as a shell-completion candidate the moment the directory exists. The
consequence for testing is the sharp part: a test written against the directory scan, which is the obvious
thing to write from the plan's own wording, would PASS against unfixed code. V-02 now requires the
explicit-path branch specifically and a demonstrated pre-fix failure.

ONE THING THE PLAN DID NOT NEED TO DO, recorded so nobody adds it: the analytics tree is ALREADY
worker-forbidden. `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` contains `.aw/records/runs/`, so
`path_is_worker_forbidden('.aw/records/runs/analytics/index.html')` is True today and `lane_containment`
refuses such a request as a coordinator surface. That is correct behavior to PRESERVE, and a plausible
wrong turn during execution would be weakening it to let a lane write analytics.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | C. Architecture / reuse | plan Goal (pre-fix); `runner_shared.py:188-189`; `project_context.py:783-790` | The Goal hardcoded `<repo>/.aw/records/runs/analytics/`, the literal this IPD exists to remove, and the conventions section framed `state_root` as an authority to "reuse". `state_root` consults no project context, while the records root IS relocatable via `records_backend` (`repository`/`companion`/`home`). An executor could satisfy every V-item with a renamed wrapper around the same hardcoded path, and Orders 02-10 would inherit it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Goal rewritten to `<resolved-runs-root>/analytics/` with an explicit statement that this is not a spelling of the repo path and that a renamed literal is a failed item; E-01 requires resolution through project-context; V-01 requires a non-`repository` backend be tested and the literal proven absent from `state_root`'s body. |
| PR-102 | HIGH | UNDER-SCOPE | A. Correctness / scope declaration | grep of `.aw/records/runs` across `agent_workflows/` | The literal is built at SIX live sites; `Scope-Paths` declared two source modules, so the plan could finalize having consolidated a third of its subject. `completion.py` and `run_cli.py` were entirely absent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added `agent_workflows/completion.py`, `agent_workflows/run_cli.py`, `tests/test_completion.py` (verified to exist; there is no `tests/test_run_cli.py`). All six sites enumerated with line numbers in the conventions section. |
| PR-103 | HIGH | UNDER-SCOPE | E. Testing / discriminating evidence | all three enumerators exercised against a synthetic reserved-tree fixture | There are THREE enumerators, not two. The scan and name-matching already exclude nested analytics by accident of depth, so the obvious test passes against UNFIXED code; the real leak is `resolve_target_runs` given an explicit PATH (returns the analytics dir as a run), and `completion.run_id_candidates` (no `run-` filter at all, offers `analytics`). | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-02 names all three enumerators plus the ledger builder and both explicit-target branches; E-03 requires the nested case be asserted through the explicit-path branch; V-02 requires a demonstrated pre-fix FAILURE, and required-tests adds an explicit negative-control clause. |
| PR-104 | HIGH | IN-SCOPE | G. Plan executability / execution contract | gate section (pre-fix) | The gate carried none of the five required elements: scope fence, paste-actual-output honesty rule, path-scoped commit, never-push, lifecycle move (`.aw/records/plans/README.md:98-136`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five added; fence worded as a DECLARATION per the 2026-09-01 ruling, with two genuinely-unsafe stop conditions named (concurrent-edit conflict, and the `kw5y2s` approved-spec case). |
| PR-105 | MEDIUM | IN-SCOPE | G. lifecycle | plan:18-19 (pre-fix) | History was oldest-first, contradicting the newest-first contract, so `ipd_lifecycle._plan_status_events` derived `to-review -> draft` and `validate_transition` refused it as backwards; `aw check plans` flagged `check.lifecycle-transition-invalid`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered; stream now `draft -> to-review -> reviewed`, all transitions `ok=True`, and the plan no longer appears in that rule's output. |
| PR-106 | MEDIUM | IN-SCOPE | D. Domain invariants / evidence | 135 `state.json` files parsed | The Findings table asserted "no real run corpus is present in this checkout". False: 135 run directories exist, all with `state.json`, `events.jsonl` and `sessions/`. The corpus is also single-host with three driver generations (120 `oc_runipd.py`, 13 legacy `runipd.py`, 2 `ipdrunner.py`, zero `agy_runipd.py`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row corrected with measured counts; the corpus is designated a read-only smoke corpus, never committed and never durable evidence, with fixtures remaining authoritative. |
| PR-107 | MEDIUM | UNDER-SCOPE | G. Specification synchronization | spec `kw5y2s` Section 3.4 and Section 6 (`- Status: approved`); spec `25kzda` | Spec-sync left "if execution discovers a controlling layout spec, amend it" for the executor to rediscover. One exists: `kw5y2s` is approved and DOES fix `runs`, but only as one of seven `traversal_exclusions`, saying nothing about runs-root resolution. Unresolved, this invited an executor to either edit an approved spec or diverge silently. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Resolved in place: `kw5y2s` named with its status and what it actually fixes, stated NOT amended by this IPD and to be treated as immutable, with the escalate-rather-than-edit path if E-01 needs more; `25kzda` assigned to Orders 08/09. |
| PR-108 | MEDIUM | IN-SCOPE | E. Testing and verification | V-01..V-03 (pre-fix); 6 escaped backticks | All three V-items described conclusions ("focused tests show...") without demanding any pasted artifact, so each could be marked pass by assertion. Six `\`` sequences rendered as literal backslash-backtick. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three V-items now demand specific pasted output; V-03 requires the bare-suite `N passed` line and a stated pre-change baseline. Backticks unescaped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101 shows the plan's central deliverable was mis-stated. Is that a REPLAN, or repairable in place? | Repairable in place. Rewrote the Goal, E-01 and V-01 to require resolution through the project-context authority. | Mark REPLAN and return the Set's first child for re-authoring. | `plan-review.md:527-530` reserves REPLAN for an approach that is unsound and not repairable with bounded edits. The APPROACH here (reserve a namespace in the disposable runs tree, exclude by containment) is sound and was the plan's own good judgement; only the resolution mechanism was wrong, and naming the authority plus requiring a non-`repository` backend in V-01 is a bounded edit. | yes |
| D-2 | Which modules belong in `Scope-Paths`: the two enumerators the plan named, all six literal sites, or something between? | The four source modules this plan must actually change (`runner_shared`, `run_viewer`, `completion`, `run_cli`) plus three test modules. `worktree_lease.py` deliberately EXCLUDED. | Declare all six sites including `worktree_lease.py` and `oc_runipd.py` as separate entries. | `worktree_lease.py:876` is a string HINT in a path-fence allowlist, not a runs-root construction, and it must be PRESERVED byte-identical (V-02 asserts this), so declaring it would invite an edit. `oc_runipd.py:5023` is a real site, but fourteen other pending plans already declare that module and Order 04 owns runner edits in this Set; it is named in the conventions section with its concurrent-edit warning instead. | yes |
| D-3 | Does this IPD amend spec `kw5y2s`, and should the review decide that or leave it to the executor? | Decide it now: it does NOT amend it, and the plan says so with the escalation path if execution finds otherwise. | Leave the plan's original conditional wording for the executor to resolve at runtime. | Read the spec: `kw5y2s` is `approved` and fixes `runs` only in `traversal_exclusions` (Section 3.4, reproduced from `selectors.EXCLUDED_RECORD_DIRS`) and in the emitted layout document; it specifies nothing about runs-root resolution or an `analytics/` child. Leaving it conditional risks the worse outcome, since an executor discovering an approved spec mid-run either edits it (invalidating a human attestation) or diverges silently. | yes |
| D-4 | Is the corpus fact worth a finding, given this IPD's work is path logic that does not read run content? | Yes, PR-106, but scoped narrowly: the corpus becomes a read-only smoke check for "real-run enumeration unchanged", not test evidence. | Silently correct the sentence; or ignore it as another child's problem. | The claim is false and the plan draws an implementation consequence from it ("implement against source contracts and checked-in fixtures"). Here the correction is mild because 135 real runs are genuinely useful for proving enumeration is unchanged, which is cheaper than a fixture. The heavier consequences (Agy absence, legacy generations) belong to Orders 05 and 10 and are bound from the orchestrator. | yes |

No `Reversible: no` decision was taken in this round.
