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

## Round 2

Reviewed at HEAD `0274bc7c`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`). At the finalize checkpoint the linter caught TWO defects in my own
revisions, which is the argument for invoking it rather than paraphrasing it: `IPD-Q501` (I had indented
OQ-01's `- Resolution or deferral rationale:` bullet while inserting an addendum above it, so the
resolved question read as having no rationale) and `check.review-finding-unescalated` (round 1's PR-001
was recorded OPEN at BLOCKER, and the maintainer's OQ-02 ruling had since resolved it, but no round-2
record said so, so the gate correctly refused). Both are repaired below and the re-run conforms.

DISCLOSURE: same agent identity authored this Set and performed round 1, so this is a self-review of a
self-review. Every load-bearing claim was therefore RE-RUN rather than recalled, including the ones
round 1 recorded as measured. Two of round 1's own conclusions did not survive that.

VERDICT ON THE MAINTAINER'S RULINGS: both stand as DECISIONS, and both had a factual basis I could not
confirm. OQ-02's choice of option (a) is right, and for the reason that actually decided it: I
re-verified `install_wizard.py:288-294` raises `InvalidPolicyError` for a policy that would track
`state_runtime`, so the toolkit already forbids tracking this folder. But the ruling's COST argument
("it already BACK-FILLS missing rules into an existing file, so adding `state/` reaches already-installed
adopters on their next install") is FALSE: `_ensure_aw_gitignore` is a hand-maintained list of per-pattern
`if <literal> not in text` checks, so a template-only edit reaches FRESH installs only. Simulated it
rather than read it: wrote today's template into a scratch repo, appended `state/` to the template,
re-ran the function, and the existing file still had no `state/` line. Three other plans (`4r0qp1` F-14,
`yvvf98` F-7/E-06, `rh5tt6` F-12) each independently recorded this same two-edits rule for their own
patterns, so it is settled repository knowledge that this plan's resolution contradicted. The cost is two
`engine.py` edits plus a `kw5y2s` amendment, and E-04 was written to depend on the cheaper version.

THE BLOCKER IS THAT THE DIGEST'S ONE JUSTIFICATION WOULD NOT HAVE HELD AS ROUND 1 SPECIFIED IT. Round 1
concluded the child survives on exactly one ground, child-table sensitivity, and directed E-01 to get the
table from `ipd_set_plan.parse_child_table`. I did not check what that function RETURNS. It returns
`{order: (dep_orders,)}` and nothing else, so a digest keyed on it moves when a row is ADDED and does not
move when a child Id is SWAPPED or a description is REWRITTEN (measured on `yeh7gc`: `rows` byte-identical
for both, `{'1': (), '2': (), '3': ()}`). That is not a partial win. It is the actively-wrong failure mode
rather than the merely-useless one, because child 03 E-03 sends the child TABLE to the model as the probe
payload and requires payload and key be the same inputs: an edit the probe reads and the key ignores
serves a STALE VERDICT under apparent authority, which child 03 names as "the one way this cache can be
actively wrong". And it would not have been caught, because OQ-01's maintainer-specified fixture ADDS a
row, the one child-table edit both keys detect, and its mutation step would still show a failure. So the
plan carried a proof that looked sufficient and was not. Fixed by keying on row CELL TEXT, with E-03 now
requiring the Id-swap and description cases and V-03 requiring `parse_child_table(...).rows` be pasted
byte-identical for them, so the wrong implementation cannot pass.

ROUND 1 ALSO SENT THE EXECUTOR TO THE WRONG MODULE. `runner_shared` ALREADY OWNS a child-table row
scanner: `parse_declared_child_orders` (`:2398`) locates the section by `ipd_schema.H_CHILD_IPDS`, matches
rows with `_TABLE_ROW_RE`, skips the alignment row, then throws away every cell but the first. Extending
or factoring that keeps ONE definition of "a child row" shared by this cache and the retirement gate;
importing `ipd_set_plan` would have created a second, in a Set whose own E-07 exists to stop shared
symbols forking. One defect not to inherit: that scanner splits on a naive `.split("|")` where
`ipd_set_plan._split_table_row` is backtick-aware, and scanning every orchestrator found THREE
(`94dhrt`, `mvz3d2`, `rreixg`) carrying a backticked pipe, one splitting 12 cells instead of 4. Harmless
for cell 0, which is why it shipped; not harmless for an all-cells digest.

E-06's STALENESS RULE KEYED ON A VALUE THAT IS USUALLY ABSENT. `runner_profiles.resolve` returns
`model=None` with provenance `host-default` whenever no flag, named profile or per-runner default supplies
one (`:975-991`), and the runner prints `model=(host default)` (`oc_runipd.py:3150`). So the rule I added
in round 1 would compare `None` to `None` and accept a verdict of any age in the common case, which is a
guard that silently does not apply. The time bound must be the always-applicable guard, and the `None`
case must be decided rather than discovered.

TWO OF ROUND 1's MEASUREMENTS RE-RAN CLEAN, and one number moved. The five `frozen_region_digest`
properties reproduced exactly on `yeh7gc` (four executor mutations `same=True`, E-item edit `same=False`),
the adopter `check-ignore` reproduction reproduced (exit 1, `state/` absent from the template), and the
oc-to-agy count is still 47. The suite baseline moved `5632 passed` to `5648 passed` with an IDENTICAL
failing node id, which is the compare-node-ids-not-totals rule demonstrating itself inside one day; both
numbers are now marked do-not-trust-at-execution.

ONE FINDING WORTH MORE THAN THIS CACHE. In the adopter-shaped repo the SHIPPED control state is already
trackable: begin receipts, the finalize writer lock and finalize journals all return exit 1 from
`git check-ignore`. So the missing `state/` rule is a live framework defect wider than this child, which
is an argument for fixing it in the installer's own plan promptly and an argument against this child
smuggling it in.

ON SIZE: item count is UNCHANGED at seven. Every round-2 finding corrected the CONTENT of an existing
item (what E-01 extracts, what E-02 keys on, what E-04 waits for, what E-06 keys on) rather than adding a
deliverable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. privacy/leaks; C. operability | `install_wizard.py:288-294` re-verified; maintainer ruling recorded in OQ-02 2026-09-07 | Round 1's blocker (the store's siting rests on an ignore rule the framework never ships) was ANSWERED by the maintainer between rounds: option (a), add `state/` to the installer template and keep the store under `.aw/state/runtime/`. Carried forward here only to record that disposition, because the round-1 record left it OPEN and the escalation gate reads the CURRENT round | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved by the maintainer's OQ-02 ruling. The DEFECT it identified is unchanged and still unfixed in code, but it is no longer an open QUESTION: what remains is ownership of the installer edit, which is now PR-009/OQ-03. The location decision is settled |
| PR-009 | BLOCKER | UNDER-SCOPE | C. architecture/operability; G. executability | searched every pending plan and backlog item at round 2: `4r0qp1`/`yvvf98` cover the four INDEX manifests, `rh5tt6` the two layout artifacts, none covers `state/`; `engine.py:5357-5404`; adopter repro showing shipped receipts/lock/journals also trackable | **OQ-02's RESOLUTION CREATED A PREREQUISITE WITH NO OWNER, AND ITS COST WAS UNDERSTATED.** Option (a) requires the framework to ship a `state/` ignore rule before this child writes a verdict store, but no plan or backlog item owns that work, and this child's fence deliberately excludes `engine.py`. Measured, it is TWO edits (template AND the hand-maintained `_ensure_aw_gitignore` back-fill list) plus a `kw5y2s` amendment, not the one the ruling assumed. `Item-Dependencies` cannot name a plan that does not exist, so without an assignment E-04 executes into an adopter-tracked LLM-verdict file | C:Medium; U:Low; S:Medium; F:Medium; Overall:Medium | OPEN | Escalated as OQ-03 with `- Blocking: yes` and `- Finding: PR-009`, owner maintainer, four costed options and (b) recommended (`yvvf98` already opens both `engine.py` sites for this exact class of pattern). E-04 now states the prerequisite as a hard precondition; V-04 fails the item unless the landing plan or commit is cited and explicitly refuses a `check-ignore` obtained by hand-editing the scratch repo. Gate paragraph rewritten to name OQ-03. NOT FIXED: assigning another plan's scope, or widening this one's fence to a file that changes every adopter's install, is a maintainer decision |
| PR-010 | BLOCKER | IN-SCOPE | A. correctness; C. state/caching; E. testing | called `parse_child_table` on `yeh7gc` and mutations: Id swap `8tgg6g`->`qqqqqq` and full description rewrite BOTH leave `rows` byte-identical (`{'1': (), '2': (), '3': ()}`); added row differs. `ChildTableResult.rows` (`ipd_set_plan.py:194-203`); child 03 (`m7gvuz`) E-03 | **THE DIGEST'S SOLE JUSTIFICATION COLLAPSES UNDER ROUND 1's OWN DIRECTION.** Round 1 concluded this child survives only on child-table sensitivity and told E-01/E-02 to key on `parse_child_table`, whose return value is the ORDER GRAPH. So the new digest would have detected a row ADD and missed a child Id swap or a description rewrite: sensitive to row COUNT, blind to row CONTENT. This is the actively-wrong case rather than the useless one, because child 03 E-03 sends the child table as the probe payload and requires payload and key be identical inputs, so a row edit the key ignores serves a stale verdict with apparent authority. OQ-01's maintainer-specified fixture ADDS a row, so it would have passed and its mutation step would still have shown a failure, making the broken key look proven | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 rewritten to extract ROW CELL TEXT; E-02 states the row cells are load-bearing and why; E-03 requires FOUR real edits (E-item, added row, Id swap, description rewrite) plus a fifth no-op (prose INSIDE the child-IPDs section, pinning rows-not-section); V-03 requires BOTH contrasts, the `frozen_region_digest` non-movement AND `parse_child_table(...).rows` shown byte-identical for the two content edits; V-05 adds a second mutation check (make the digest ignore rows, show the OQ-01 fixture FAILS). New F-10; the Concern paragraph and a conventions bullet say it. OQ-01 gains a round-2 addendum stating its fixture alone cannot distinguish the two implementations |
| PR-011 | HIGH | IN-SCOPE | C. architecture; F. KISS/reuse | `runner_shared.parse_declared_child_orders:2398`, `_TABLE_ROW_RE:2227`, `_TABLE_SEPARATOR_CELL_RE:2230`, naive split `:2442`; `ipd_set_plan._split_table_row:206`; scanned all `Kind: orchestrator` plans | **ROUND 1 SENT THE EXECUTOR TO ANOTHER MODULE FOR A SCANNER `runner_shared` ALREADY OWNS.** `parse_declared_child_orders` already finds the child-IPDs section by schema heading, matches rows, skips the alignment row, then discards every cell but the first. Importing `ipd_set_plan` instead would create a SECOND definition of "a child row" in a Set whose E-07 exists to prevent exactly that forking, and would leave the cache and the retirement gate able to disagree. Separately, that scanner's naive `.split("\|")` diverges from the backtick-aware splitter on three live orchestrators (`94dhrt`, `mvz3d2`, `rreixg`; one splits 12 cells instead of 4), which is harmless for cell 0 and not harmless for an all-cells digest | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires factoring the existing row-walk so BOTH callers share it, using the backtick-aware split for the digest, and stating whether `parse_declared_child_orders` was left on the naive split and why. V-01 requires the shared helper named with both call sites plus its output on the three divergent orchestrators. New F-9; conventions bullets rewritten (`ipd_lint.parse` is still correct for E-item text) |
| PR-012 | HIGH | IN-SCOPE | A. correctness; honest documentation | `engine._ensure_aw_gitignore:5357-5404`; scratch-repo simulation; `4r0qp1` F-14, `yvvf98` F-7/E-06, `rh5tt6` F-12 | **THE MAINTAINER'S OQ-02 RULING RESTS PARTLY ON A FALSE FACT, AND THE PLAN RECORDED IT AS SETTLED.** The ruling cited that `_ensure_aw_gitignore` "already BACK-FILLS missing rules into an existing file, so adding `state/` reaches already-installed adopters on their next install rather than new ones only", and offered that as one of two facts making option (a) "cheaper than first assessed". The back-fill is a hand-maintained list of per-pattern literal checks, so a template-only edit reaches FRESH installs only. Three other plans already recorded this rule for their own patterns, so the plan asserted something the repository had contradicted three times | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-02 keeps its DECISION and gains a round-2 correction stating the false fact, the reproduction, and the true cost (two edits plus the amendment); the ruling's real basis (`install_wizard`'s invariant, re-verified) is preserved as what decided it. Deferred bullet and E-04 corrected to name both edits. New F-11. Feeds PR-009 |
| PR-013 | MEDIUM | IN-SCOPE | A. correctness; C. state/caching | `runner_profiles.resolve:975-991` (`PROVENANCE_HOST_DEFAULT` returns None for model/variant/agent); `oc_runipd.py:3150` prints `model=(host default)` | **E-06's STALENESS RULE, ADDED IN ROUND 1, KEYS ON A VALUE THAT IS ROUTINELY ABSENT.** `resolve` returns `model=None` whenever no explicit flag, named profile or per-runner default supplies one, which is the default unqualified run. So "a verdict recorded by a DIFFERENT model than the current run resolves reads as unknown" compares `None` to `None` in the common case and accepts a verdict of any age: a guard that appears to exist and silently does not apply, which is the same shape of defect as the unconsumed model field E-06 was created to fix | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now requires the time bound be the always-applicable guard, and the `model=None` case decided explicitly (never-match/re-probe, or time-bound-only) with the measurement cited. V-06 requires that case pasted. New F-12 and a conventions bullet |
| PR-014 | LOW | IN-SCOPE | Evidence accuracy; G. executability | `plan_readiness.has_unresolved_blocking_question` -> False; `approval_refusals` naming only the stale `Readiness` and the unresolved PR-001; OQ-02's own `- Blocking: no` | **THE GATE PARAGRAPH ASSERTED A BLOCK NO CODE ENFORCED.** It said "EXECUTION IS BLOCKED ON OQ-02 ... OQ-02 carries `Blocking: yes`, so the pre-execution checkpoint refuses while it is open", while OQ-02 has carried `- Blocking: no` and `- Status: resolved` since the maintainer's ruling. Measured, `has_unresolved_blocking_question` returned False, so no gate read that sentence and a reader would have believed a question was still pending that had already been answered. The same defect was found and fixed on sibling `yeh7gc` at its round 2, so this is a Set-wide pattern | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate paragraph rewritten to name OQ-03, which genuinely carries `- Blocking: yes`, with the measurement cited so the claim is checkable; E-04's unexpressable prerequisite stated separately and routed to V-04 rather than to a gate that cannot see it; the items executable before the prerequisite lands (E-01/E-02/E-03/E-07) named |
| PR-015 | LOW | IN-SCOPE | E. testing; evidence accuracy | bare `python3 -m pytest` at `0274bc7c`: `1 failed, 5648 passed, 3 skipped, 2 xfailed`; round 1 recorded `5632 passed` at `125105fe`; same failing node id `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` | The recorded baseline total drifted by 16 passes in one day while the failing node id stayed identical, so a plan whose baseline is a TOTAL would have shown a spurious mismatch at execution. Also `IPD-Q501` and `check.review-finding-unescalated` fired on my own revisions at the finalize checkpoint (an indented OQ-01 rationale bullet; round-1 PR-001 left OPEN at BLOCKER with no current-round disposition), which is why the linter is invoked rather than paraphrased | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline bullet re-measured with both numbers, the drift stated as the argument for node-ids-not-totals, and both marked do-not-trust-at-execution; E-07/V-07 likewise told to re-measure the 47 rather than assert it. OQ-01's rationale bullet de-indented; PR-001 given a round-2 disposition; `--phase review-finalize` re-run to conforming |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-7 | What exactly does the digest key on for the child table, given `parse_child_table` returns only the order graph? | The ROW CELL TEXT of every row in the `## Child IPDs` table, header included, in document order; explicitly NOT the parsed order graph and NOT the section's prose | Key on `ChildTableResult.rows`, rejected because measured it is blind to an Id swap and a description rewrite, which is precisely the content a coverage question turns on and precisely what child 03 sends the model. Key on the whole `## Child IPDs` SECTION, rejected because it carries explanatory paragraphs (`yeh7gc:54-56`) and would reintroduce the prose sensitivity `frozen_region_digest` deliberately excludes. Cancel the child, rejected because the row-text key does deliver the one property the existing digest lacks | called `parse_child_table` on `yeh7gc` plus three mutations (added row differs; Id swap and description rewrite byte-identical); `ipd_set_plan.py:194-203`; child 03 `m7gvuz` E-03's payload-equals-key requirement | yes |
| D-8 | Which module provides the row extraction, after round 1's cross-module reuse turned out to be wrong? | `runner_shared`'s OWN `parse_declared_child_orders` row-walk, factored so both it and the digest share one helper | Import `ipd_set_plan.parse_child_table` as round 1 directed, rejected because it returns the wrong shape (D-7) AND would fork the definition of a child row in a Set whose E-07 exists to stop symbol forking. Write a third parser, rejected for the same reason. Extend `ipd_lint.parse` to expose the table, still rejected on round 1's basis (`ipd_lint` must stay Kind-unaware per spec `77tr3o` R-5) | `runner_shared.py:2398`, `:2227`, `:2230`, `:2442`; `ipd_set_plan._split_table_row:206`; scanned every orchestrator, three diverge on the naive split | yes |
| D-9 | Does the backtick-aware split matter, or is the existing naive split good enough? | Use the backtick-aware split FOR THE DIGEST; leave `parse_declared_child_orders`'s own cell-0 read alone unless the executor chooses to fix it, and require that choice be stated | Reuse the naive split for both, rejected because a backticked plan filename fragments a row and three live orchestrators contain one, so the digest would key on shifted cells. Fix the retirement gate's splitter in this child, rejected as an unrequested behavior change to a shipped gate outside this plan's concern, though the executor may do it and say so | scanned all `Kind: orchestrator` plans comparing both splitters: `94dhrt`, `mvz3d2`, `rreixg` diverge, one 12 cells versus 4; cell 0 identical in every case | yes |
| D-10 | The maintainer's OQ-02 ruling cites a back-fill behavior that does not exist. Re-open the question, or keep the decision and correct the fact? | KEEP the decision, CORRECT the fact, and route the newly-visible cost to a new blocking question (OQ-03) | Re-open OQ-02 wholesale, rejected because the fact that was false (back-fill reach) is not the fact that DECIDED it (`install_wizard`'s hard invariant against tracking `state_runtime`, re-verified), so the choice survives its own correction. Silently fix the plan's prose without recording that a maintainer ruling contained a false premise, rejected because the next reader would inherit the same wrong cost model | `engine.py:5357-5404`; scratch-repo simulation (template + `state/` appended, `_ensure_aw_gitignore` re-run, existing file unchanged); `install_wizard.py:288-294`; `4r0qp1` F-14, `yvvf98` F-7/E-06, `rh5tt6` F-12 | yes |
| D-11 | Who owns the installer `state/` fix, and may this child just do it? | ESCALATE as OQ-03 `Blocking: yes`, readiness NO-GO, recommending option (b) (fold into `yvvf98`, which already opens both `engine.py` sites) | Widen this child's `Scope-Paths` to `engine.py` plus the spec, rejected because plan-review edits planning documents only and because a cache plan changing what every adopter receives on install is a maintainer's call, not a reviewer's. Let E-04 proceed and fix the ignore rule later, rejected because that ships a tracked LLM-verdict file to every adopter in between. Re-open OQ-02 for a location needing no rule, offered as option (d) rather than chosen | searched all pending plans and backlog for a `state/` owner and found none; adopter repro showing shipped receipts/lock/journals are ALSO trackable; ESCALATED in-plan as OQ-03 with `- Finding: PR-009`, and maintainer told 2026-09-08 in this review's final report | no |
| D-12 | E-06's rule keys on a model identity that is usually `None`. Choose the fallback, or require the executor to? | REQUIRE the executor to choose explicitly between never-match/re-probe and time-bound-only, and make the TIME BOUND the guard that always applies | Pick never-match myself, rejected because it makes every unqualified run re-probe every orchestrator on every run, a cost the maintainer may not accept and which the cache exists to avoid. Pick time-bound-only myself, rejected because it silently drops the model check the maintainer's own rationale asked for. Leave round 1's wording, rejected because measured it is a guard that does not apply in the common case | `runner_profiles.py:975-991` (`PROVENANCE_HOST_DEFAULT` -> None); `oc_runipd.py:3150` (`model=(host default)`) | yes |

## Round 3

Round 3 exists ONLY to close PR-009, whose escalated question the maintainer answered on 2026-09-08. It
re-critiques nothing: every other round-2 finding was already `FIXED` and is superseded unchanged
(PR-001, PR-010..PR-015).

WHY IT IS NEEDED: the escalation contract (`plan-review.md:335-341`) defines the path INTO a blocking
question and no path back, so the answered question left PR-009 reading `OPEN` and
`subject_gating_blocks` kept refusing the plan on a decision that had been made. Measured at HEAD
`dcb5a2a4`: plan OQ-03 reads `- Status: resolved` carrying `- Finding: PR-009` and the maintainer's
choice, while the finding still gated. Appending a round is the sanctioned mechanism, since
`current_findings` reads only the last round (`review_findings.py:236-243`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-009 | BLOCKER | UNDER-SCOPE | C. Architecture (a prerequisite with no owner) | plan OQ-03 (`- Status: resolved`, `- Finding: PR-009`) | Carried forward from round 2 and now CLOSED BY THE MAINTAINER. Round 2 measured that this child's verdict store needs a `state/` ignore rule the framework does not ship, requiring two `engine.py` edits plus a spec amendment that no pending plan or backlog item owned, while this child's fence deliberately excludes `engine.py`. The maintainer ruled option (b) on 2026-09-08: FOLD the installer fix into `yvvf98`, which already opens both `engine.py` sites for exactly this class of pattern, so the marginal cost is about two lines plus the amendment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's recorded decision. The prerequisite now has an owner (`yvvf98`), so E-04's unmet dependency is resolved without widening this child's fence. Whoever executes this child must confirm `yvvf98` landed the `state/` rule before writing the store, and should carry an `Item-Dependencies` edge if `yvvf98` is still pending at that time. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-009's question is answered in the plan but the finding still reads `OPEN`, so the plan is gated on a settled decision. Close the finding, or leave it open until `yvvf98` actually lands? | Close it `FIXED` now, and state the landing check as an execution-time obligation on this child. | Leaving PR-009 `OPEN` until `yvvf98` executes, rejected because the finding records a MISSING OWNER and the owner now exists; conflating "unowned" with "not yet delivered" would keep the plan gated for the entire life of another plan and would misreport what the finding says. An `Item-Dependencies` edge is the right expression of the delivery ordering, not an open finding. | Plan OQ-03's recorded maintainer decision of 2026-09-08 naming `yvvf98` as the owner; `current_findings` semantics at `review_findings.py:236-243`. | yes |
