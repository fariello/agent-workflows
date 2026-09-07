# Review: cache an orchestrator probe verdict against a content digest (child 8tgg6g, Set orchprobe)

- Subject-Id: 8tgg6g
- Subject-Type: ipd
- Reviewed-At: 2026-09-07
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `125105fe`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions with zero
findings. One note on that: my first revision INTRODUCED an `IPD-Z602` density advisory on my own
rewritten E-01 (three explanatory relative clauses read as three action clauses), which the pre-review
plan did not carry. I verified that by stashing the revision and re-linting rather than assuming, then
restructured the item so the single deliverable leads and the rationale sits in labelled paragraphs. The
advisory is gone and the item still says everything it needs to.

DISCLOSURE: the same agent identity authored this Set earlier in the session, so this is a self-review.
Every load-bearing claim was therefore RE-MEASURED rather than recalled, and the two most consequential
findings below are both cases where running the code contradicted what the plan asserted.

METHOD. This plan is almost entirely claims about what an existing digest function does and where a file
would be ignored, so neither was read and accepted: `frozen_region_digest` was CALLED on a real
orchestrator with each of six mutations applied, and the gitignore behavior was REPRODUCED in a
throwaway repository carrying only what the installer emits. The parser reuse claim was checked by
printing `ParsedDoc._fields`.

WHAT THE PLAN GOT RIGHT, and it is the core insight. The `xmqv5l` lesson is correctly identified as the
governing precedent, and framing the cache key as "hash the reviewed contract, not the file" is exactly
right. Refusing to modify `plan_content_digest` or `frozen_region_digest` because a begin-receipt gate
depends on them is the correct fence. Making a MISS return `unknown` rather than `pass` is the right
default and is the single most important safety property in the child. Recording which model answered is
good instinct, and Deferred's refusal to commit verdicts to git is well argued.

THE BLOCKER IS THAT THE STORE'S SITING RESTS ON AN IGNORE RULE THE FRAMEWORK NEVER SHIPS, and the
finding that authorized it cited the wrong file. F-3 said `.aw/.gitignore` already ignores the runtime
tree, so no new rule was needed, and E-03 sited the store there on that basis. Measured:
`.aw/.gitignore` says NOTHING about `state/`; its only occurrence of the string `state` is a comment
about `records/runs/`. What ignores the path in THIS repository is the ROOT `.gitignore:60`, and
`engine.py` is explicit that the installer never writes that file ("it is NOT the user's root
`.gitignore` (that is never touched here)", `:4312-4313`); `_AW_GITIGNORE_TEMPLATE` contains zero
occurrences of `state/`. Reproduced in a throwaway repo carrying only that template: `git check-ignore
-v .aw/state/runtime/probe-verdicts.json` exits 1, NOT ignored. So the verdict store would be
gitignored here by an accident of this repository's own history and a TRACKED file in every adopter.
That matters beyond tidiness: the file records LLM verdicts keyed to machine-local plan paths, which is
the class of content the leak-sanitizer exists to keep out of public artifacts. And V-03 would have
passed: it asked for `git check-ignore` without saying where to run it, so it would have been run here,
where the answer is misleadingly correct. There is a related asymmetry worth recording: `install_wizard`
already REFUSES a config that tracks `state_runtime` (`:288-294`), so the framework asserts the policy
in its validator while not shipping the mechanism that enforces it on disk.

THE SECOND MEASUREMENT UNDERMINES MOST OF THE CHILD'S STATED JUSTIFICATION, AND RESCUES IT WITH ONE
CASE. E-02 proposed proving the `xmqv5l` trap avoided by showing four executor mutations leave the
digest unchanged and an E-item edit changes it. Called against `frozen_region_digest` on orchestrator
`cczotj`: ticking a checkbox, filling an `Observed evidence`, appending a history line and editing a
prose section ALL leave it unchanged, and an E-item action edit DOES change it. All five properties
already hold in shipped code, so E-02's proof would have demonstrated parity with a function the plan
had already decided not to touch. The gap that does justify a new digest is the one the plan never
mentioned: a CHILD-TABLE edit does not move `frozen_region_digest`, because `_requirements_from_plan`
(`:517-548`) reads only `Scope-Paths`, E-item text and V-item text. For a probe whose question is
"which of this parent's items are covered by a child", the child table is precisely the input that must
invalidate a cached answer. So the child survives, on one narrow and previously unstated ground, and
V-03 now requires the contrasting measurement (the same mutation shown NOT moving the old digest) so
the new function has to earn its existence rather than assert it.

E-01's STATED REUSE DOES NOT EXIST. It said `ipd_lint.parse` already separates the extraction needed for
both the E-item text and the child table. It does for the first (`Leaf.text` versus `Leaf.fields` and
`Leaf.checked`) and not at all for the second: `ParsedDoc` has no child-table field. The executor would
have hit that mid-implementation and most likely written a second table parser next to
`ipd_set_plan.parse_child_table`, which already resolves columns by header name and returns a typed
refusal reason. Split into E-01 (get the table from the parser that has it, lazily) and E-02 (build the
key), with the lazy-import requirement stated because `runner_shared` carries exactly one module-level
first-party import and `ipd_lifecycle` reaches `ipd_lint` lazily at all seven of its sites.

ONE GAP THE PLAN CREATED FOR ITSELF. It records which model answered and justifies that as letting "a
future reader distrust an old one", but nothing consumed the field, so a verdict from a model nobody
would ask today would be served as authoritative indefinitely. A cache of LLM judgements with no
staleness rule is a cache that eventually answers for a retired model. New E-06 requires a stated rule
with a default, and V-06 requires it shown to discriminate rather than to reject everything.

ON SIZE, since this review took the child from five E-items to seven. E-01 is a split of work E-02
already implied, and E-06 is the missing consumer of a field the plan already wrote, so the growth is
decomposition plus one genuine gap rather than scope creep. The `engine.py` fix that F-3 implies is
deliberately NOT added: it is one of OQ-02's options, it changes every adopter's tree, and it needs a
spec amendment, so it belongs to a human's decision and not to this child's fence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. privacy/leaks; C. operability; honest documentation | throwaway-repo reproduction: `git check-ignore -v .aw/state/runtime/probe-verdicts.json` exits 1 under `_AW_GITIGNORE_TEMPLATE` alone; root `.gitignore:60`; `engine.py:4308-4313`; `.aw/.gitignore`; `install_wizard.py:288-294` | **THE STORE'S SITING RESTS ON AN IGNORE RULE THE FRAMEWORK NEVER SHIPS, AND F-3 CITED THE WRONG FILE.** F-3 claimed `.aw/.gitignore` already ignores the runtime tree; it says nothing about `state/` (its only `state` string is a comment about `records/runs/`). The rule that ignores it HERE is the ROOT `.gitignore:60`, which the installer explicitly never writes, and `_AW_GITIGNORE_TEMPLATE` has zero `state/` entries. So in every adopter the verdict store is a TRACKED file holding LLM verdicts keyed to machine-local paths, which is leak-sanitizer territory. V-03 asked for `git check-ignore` without saying where, so it would have been run here and passed while proving nothing. Note `install_wizard` already refuses a tracked `state_runtime` policy, so the framework asserts the invariant in its validator while not enforcing it on disk | C:Medium; U:Low; S:Medium; F:Medium; Overall:Medium | OPEN | Escalated as OQ-02 with `- Blocking: yes` and `- Finding: PR-001`, owner maintainer, four costed options (add `state/` to the installer template; site under an already-ignored path; ship a nested `.gitignore` as a deliverable; move outside the repo) with (a)-as-correct and (c)-as-interim recommended. F-3 rewritten as a BLOCKER with the reproduction. E-04 now forbids assuming the ignore status and requires proving it in a fresh repo; V-04 requires the check run there, not here. The gate blocks execution on OQ-02. NOT FIXED because one option mutates every adopter's tree and needs a spec amendment |
| PR-002 | HIGH | IN-SCOPE | A. correctness; E. testing; evidence accuracy | called `frozen_region_digest` on `cczotj` with six mutations: checkbox/evidence/history/prose all `same=True`, E-item edit `same=False`, child-table edit `same=True`; `ipd_lifecycle.py:517-548` | **FOUR OF THE FIVE PROPERTIES THE CHILD WAS AUTHORED TO ESTABLISH ALREADY HOLD IN SHIPPED CODE, AND THE ONE REAL GAP WAS NEVER STATED.** E-02's `xmqv5l` proof (four no-op mutations plus one real edit) is satisfied TODAY by `frozen_region_digest`, so as written it would have proven parity with a function the plan had already fenced off, and a reader could reasonably have asked why the new digest exists. The gap that DOES justify it: a child-table edit does not move `frozen_region_digest`, because `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item text. For a probe reasoning about which parent items a child covers, that is exactly the input that must invalidate a cached verdict | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now states what is genuinely new (child-table sensitivity only) and what it deliberately drops relative to `frozen_region_digest` (`Scope-Paths`, V-item text), with that divergence required in its docstring. E-03 adds the child-table mutation as a required case. V-03 requires the CONTRAST: the same child-table mutation run through `frozen_region_digest` showing it does NOT move, so the new function earns its existence. New F-4; the Concern paragraph and a new conventions bullet say it |
| PR-003 | HIGH | IN-SCOPE | G. executability | printed `ipd_lint.ParsedDoc._fields` (no child/table member); `ipd_set_plan.parse_child_table:334` | **E-01's STATED REUSE DOES NOT EXIST FOR HALF OF WHAT IT CLAIMS.** The plan says `ipd_lint.parse` already provides the extraction for the E-item text AND the child table. It provides the first and not the second: `ParsedDoc` exposes no child table. The executor would have discovered this mid-implementation and most plausibly written a second table parser beside `ipd_set_plan.parse_child_table`, which already locates the section by schema heading, resolves columns by header name rather than index, and returns a typed refusal reason | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-01 (reuse `ipd_set_plan.parse_child_table`, do not write a second parser, and if its `rows` shape is insufficient say precisely what is missing) and E-02 (build the key). V-01 requires stating whether the reuse held. New F-5 and a conventions bullet naming `ParsedDoc`'s actual fields |
| PR-004 | MEDIUM | UNDER-SCOPE | C. architecture | `runner_shared.py:136` (sole module-level first-party import); `ipd_lifecycle.py:515`, `:560`, `:950`, `:1326`, `:1783`, `:2046`, `:2618` (all lazy) | **THE IMPORT DISCIPLINE WAS UNSTATED, AND THIS CHILD MUST REACH THE IPD PARSERS FROM A MODULE BOTH DRIVERS IMPORT.** `runner_shared` has exactly one module-level first-party import (`render_stream`), and `ipd_lifecycle` reaches `ipd_lint` through a function-local import at every one of its seven sites. Nothing in the plan said so, so an executor adding a module-level `ipd_lint`/`ipd_set_plan` import to `runner_shared` would change the import graph for both host drivers as a side effect of a cache | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires the lazy import with the precedent cited; V-01 requires an AST walk proving `runner_shared` still has exactly one module-level first-party import. New F-6 and a conventions bullet |
| PR-005 | MEDIUM | UNDER-SCOPE | C. state/caching; honest documentation | pre-revision E-03 versus the plan's own E-items; no staleness rule anywhere | **THE RECORDED MODEL WAS WRITTEN AND NEVER READ.** E-03 stores which model answered and justifies it as letting "a future reader be able to distrust an old one", but no item consumed the field, so a verdict is served as authoritative forever regardless of which model produced it or how long ago. The plan therefore accepted the premise (an old verdict may be untrustworthy) while providing no mechanism to act on it, which is the shape of a field that quietly becomes decoration | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-06 requires a stated staleness rule with a default bound: at minimum a verdict from a different model than the run resolves, or older than the bound, reads as `unknown` rather than its recorded value. V-06 requires it shown to DISCRIMINATE (a stale verdict rejected AND a fresh one accepted), so a rule that rejects everything does not pass. New F-8 |
| PR-006 | MEDIUM | UNDER-SCOPE | A. correctness (lane visibility) | `ipd_lifecycle._runtime_dir:267-274`; backlog `dh0uno` | **THE STORE PATH WAS NOT REQUIRED TO GO THROUGH `checkout_control_root`, WHICH IS THE EXACT DEFECT `dh0uno` RECORDS.** E-03 said to site the store "with the other runtime state (`.aw/state/runtime/`)" but did not say how to derive the path. `_runtime_dir` routes through `checkout_control_root` precisely because composing `repo_root / ".aw" / ...` gives a LANE its own store: an in-lane `aw` wrote receipts the driver could not see and teardown deleted. A probe cache written per-lane would be invisible to the driver that must read it, and this Set's probe runs pre-run while lanes exist | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 requires the path be derived via `checkout_control_root` with the `dh0uno` reason stated; V-04 requires the resolved path be IDENTICAL computed from the main tree and from a linked worktree. New conventions bullet |
| PR-007 | LOW | IN-SCOPE | A. correctness; E. testing | pre-revision OQ-01; the remedy's actual effect on both digest inputs | **OQ-01 ASKED THE EXECUTOR TO CONFIRM SELF-INVALIDATION WITHOUT NAMING THE PROPERTY THAT MAKES IT TRUE.** It said a genuine fix "edits the orchestrator's E-item text and so changes the digest", leaving the executor to rediscover why. The real reason is stronger and worth writing down: the remedy for a `CONTAINS EXECUTIONS` verdict is moving the work into a NEW child, which edits both the E-item text AND the child table, and E-02's digest covers both | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now names the property and requires it demonstrated by PERFORMING the remedy on a fixture and showing the digest move, not inferred; V-05 requires that fixture evidence when a fail is cached |
| PR-008 | LOW | IN-SCOPE | Evidence accuracy | `ipd_lifecycle.py:462` (`frozen_region_digest`), `:146-155` (`Leaf`); AST count 47; measured suite baseline | Three small citation and figure errors, each of which a V-item would otherwise have been checked against: `frozen_region_digest` cited at `:461` (it is `:462`), `Leaf` at `:149` (the NamedTuple is `:146-155`), and "~46 names" imported from `oc_runipd` (measured 47; `cnwy8g` recorded 40, so it is growing and a `~` is not a checkable baseline). The plan also carried no measured suite baseline at all | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citations corrected; E-07 states 47 with the method and date and V-07 requires the before/after count; a measured baseline bullet added (`1 failed, 5632 passed, 3 skipped, 2 xfailed` at HEAD `125105fe`, with the one failure named as a live-repo status coupling unrelated to this child). New F-7 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Does this child still have a reason to exist, given `frozen_region_digest` already satisfies four of its five stated properties? | YES, on one narrow ground: child-table sensitivity, which the existing digest lacks. Say so explicitly and require the contrast as evidence | Cancel the child and reuse `frozen_region_digest`, rejected because a child-table edit does not move it, and the child table is exactly the input a coverage question depends on. Keep the plan's original framing, rejected because it justifies the new function on properties that already hold, which invites a later reader to delete it as redundant | measured six mutations against `frozen_region_digest` (four no-ops unchanged, E-edit changed, child-table edit UNCHANGED); `ipd_lifecycle._requirements_from_plan:517-548` reading only `Scope-Paths`, E-text and V-text | yes |
| D-2 | Where does the child-table extraction come from, given `ipd_lint.parse` does not expose one? | `ipd_set_plan.parse_child_table`, imported lazily | Write a new parser in `runner_shared`, rejected as a re-fork of a parser that already resolves columns by header name and returns typed refusal reasons. Extend `ipd_lint.parse` to expose the table, rejected because `ipd_lint` must stay Kind-unaware per spec `77tr3o` R-5 and this Set's CID-1 asserts zero "orchestrator" occurrences in it | printed `ParsedDoc._fields`; `ipd_set_plan.parse_child_table:334`; `.aw/records/specs/...77tr3o...` R-5 and `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` | yes |
| D-3 | Module-level or lazy import for the IPD parsers from `runner_shared`? | LAZY, function-local | Module-level, rejected because `runner_shared` has exactly one module-level first-party import today and both host drivers import it, so the graph change would be a side effect of adding a cache; `ipd_lifecycle` already establishes the lazy pattern at all seven of its `ipd_lint` sites | AST walk over `runner_shared`'s col-0 `ImportFrom` nodes; `ipd_lifecycle.py:515`, `:560`, `:950`, `:1326`, `:1783`, `:2046`, `:2618` | yes |
| D-4 | Escalate the gitignore/siting defect, or fix it by adding `state/` to the installer template? | ESCALATE as OQ-02 `Blocking: yes`, readiness NO-GO, with four options and a recommendation | Add the template entry myself, rejected on two grounds: plan-review edits planning documents only and never code, and the change mutates what EVERY adopter receives on install plus owes a `kw5y2s` spec amendment, so it is a maintainer decision rather than a reviewer's. Silently site the store elsewhere, rejected because that picks one of four options with different costs on the maintainer's behalf | throwaway-repo reproduction (`check-ignore` exit 1); `engine.py:4308-4313`; root `.gitignore:60`; `install_wizard.py:288-294`; ESCALATED in-plan as OQ-02 with `- Finding: PR-001`, and maintainer told 2026-09-07 in this review's final report | no |
| D-5 | Add a staleness rule, when the plan only asked to RECORD the model? | YES, as E-06, with a stated default bound | Leave the field unconsumed as authored, rejected because the plan's own justification for recording it (a future reader must be able to distrust an old verdict) is unachievable without a mechanism, so the field would be decoration and the cache would serve a retired model's judgement indefinitely | pre-revision E-03's stated rationale against the absence of any consumer in the plan | yes |
| D-6 | How to handle the `IPD-Z602` density advisory my own revision introduced on E-01? | RESTRUCTURE the item so the single deliverable leads and the rationale sits in labelled paragraphs | Dismiss it as a false positive on explanatory clauses, rejected because the workflow treats a density signal as a finding to investigate rather than to argue with, and the restructured item is genuinely easier to execute from. Split E-01 further, rejected because it has one deliverable | stashed the revision and re-linted to confirm the advisory was NOT pre-existing (`Z602 present pre-review: False`), then re-linted after restructuring (clean, 0 findings) | yes |
