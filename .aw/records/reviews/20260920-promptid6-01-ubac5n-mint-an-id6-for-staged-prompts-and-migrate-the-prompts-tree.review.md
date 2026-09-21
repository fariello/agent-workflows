# Review: mint an id6 for staged prompts and migrate the prompts tree, child ubac5n (Set promptid6)

- Subject-Id: ubac5n
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed in an isolated lane worktree at HEAD `cd2e6adb`. `aw ipd lint --phase author` CONFORMING
before semantic review and `--phase review-finalize` CONFORMING after revision, so nothing found here
is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
RUNNING the mechanisms rather than re-reading the prose. Six things were executed rather than inspected
and five produced findings: `aw rename prompts --to-id6` was invoked in preview against the real tree
(which produced the BLOCKER); the id6 injection point was computed against a real prompt's line
structure; `config.resolve_cutover_date` was called for both `spec_id6` and `prompt_id6`;
`check_engine._iter_type_files` was called with and without `include_retired`; the prompt corpus and the
legacy-date ordering were enumerated directly; and both the named test file and the full suite were run.

THE GOAL AND THE MANDATE ARE SOUND, AND THE CORE PREMISE VERIFIES. 17 prompt files exist across
`pending/`, `executed/` and `superseded/`, none carries an id6, `ARTIFACT_TYPE_FACETS` already contains
`prompt` and `TYPE_FACET` already maps `prompts -> prompt`, and `build_clustered_name` can already
produce the target name. The maintainer's ruling is quoted verbatim and the plan is admirably honest
that it REVERSES `jxqdcw` OQ-02 rather than fixing an oversight; F-3 states that plainly and the gate
forbids relitigating it. No finding below disputes the plan's goal.

WHAT THE FINDINGS ARE ABOUT: four of the six E-items rested on measurements that no longer hold, and
two of those would have produced a WRONG implementation rather than a failed one, which is the harder
failure to catch after the fact.

THE BLOCKER IS THAT E-04's DELIVERABLE ALREADY EXISTS AND ALREADY CORRUPTS A PROMPT. `--to-id6` is a
GENERIC flag on the shared rename verb, not a per-type one, so prompts inherited it when specs got it.
Run in preview against the real tree it exits 0 and prints a complete, plausible plan: a correct
clustered rename, an id6 injection, and a citation rewrite into executed plan `jxqdcw`. The defect is
the injection: `_update_frontmatter_metadata` anchors the `- Id:` bullet after `- Status:`, else after
`- Date:`, else after the first `# ` heading, and a prompt has neither bullet, so the third anchor
fires. Computed against the real file, the bullet lands on line 3, immediately beneath the H1, as
VISIBLE TEXT inside the body a human pastes into a chat. That is a direct violation of approved spec
`20260808-1958-01-prompt-purity-lint` R1 and P4, the very contract this plan's own Scope section
promises to leave untouched. Nothing catches it, because `aw prompts check` (the lint that spec
specifies) is not implemented at all. So the item is a REPAIR of a shared code path, with a hard
requirement that specs' behavior stay byte-unchanged, and it is now the highest-risk item in the plan.

THE SECOND STRUCTURAL FINDING IS THAT E-03 WOULD HAVE MIRRORED A SUPERSEDED MECHANISM. The plan says to
add a constant "beside `SPEC_ID6_CUTOVER_DATE`", but that constant is now only a fallback: the live
resolver consults `config.resolve_cutover_date` first and the constant's own docstring calls itself
deprecated. The config path is live HERE, which is what makes copying the constant actively wrong
rather than merely old-fashioned: `project.json` sets `cutovers.spec_id6 = "2026-08-29"`, so the
effective spec boundary is `20260829` and NOT the `20260828` the plan proposed to copy as its model. An
executor following the original text would have shipped a boundary the maintainer cannot move without
editing Python, in a repository that already moved that capability into config. The revision also makes
the plan answer the `CARRIER_CUTOVER_DATE` counter-precedent rather than ignore it, since that constant
deliberately rejected config for a documented reason.

OQ-02 IS THE MOST INSTRUCTIVE FINDING, because its conclusion was right and its evidence was false in
both halves. It asserted that the newest legacy tracked prompt date is `20260920` and that a
`20260920`-dated legacy name remains in `pending/`. Measured: the newest legacy name is
`20260829-1520-01-session-allocation-policy.prompt.md`, and the only `20260920` prompt in the tree is
the CONFORMING hand-made one. The second reason rested on a file in the `untracked/` quarantine lane,
and that lane DOES NOT EXIST in a lane worktree, with no `20260920-12*` file anywhere in the tree. I
kept `20260921` on rewritten reasoning (a cutover at or below `20260920` would make the hand-made
file's conformance load-bearing, and the strictly tighter `20260830` buys nothing) and recorded a
warning not to restore the discarded argument.

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/prompts.py` (docstring
`:1-27`, `_STAGED_NAME_RE` `:62`, `next_sequence` `:107-122`, `build_staged_name` `:125`),
`agent_workflows/artifact_naming.py` (`:38-50`, `build_clustered_name` `:182`, `ARTIFACT_TYPE_FACETS`
`:66`), `agent_workflows/check_engine.py` (`SUPPORTED` `:21-31`, `SPEC_ID6_CUTOVER_DATE` `:40`,
`is_retired` `:598-632`, `_spec_requires_id6` `:744-762`, `CARRIER_CUTOVER_DATE` `:4687`),
`agent_workflows/config.py` (`resolve_cutover_date` `:1204`), `agent_workflows/artifact_rename.py`
(`_ID_LINE_RE` `:209`, `_update_frontmatter_metadata` `:214-266`, the apply path `:586-596`),
`agent_workflows/cli.py` (`--to-id6` `:3707-3714`), `.aw/config/project.json`, both prompts READMEs,
`.aw/system/workflows/research-prompt/research-prompt.md:9`, two shipped templates, specs
`20260808-1958-01-prompt-purity-lint` (P4/P5 `:30-31`, R1 `:58`) and
`20260730-2152-01-agents-artifact-organization` (`:4`, `:182`, `:218`, `:248`), executed plan `jxqdcw`
OQ-02, `tests/test_prompts_new.py`, and `tests/test_standalone_verify.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | A. Correctness / D. Invariants | `agent_workflows/artifact_rename.py:214,241-260`; `cli.py:3708` | E-04's deliverable ALREADY EXISTS and already violates an approved contract. `--to-id6` is generic, so `aw rename prompts <legacy> --to-id6` runs today; its metadata writer injects a `- Id:` bullet after the first `# ` heading when no front-matter bullet exists (every prompt), putting the id6 as visible text in the pasteable body. Violates `prompt-purity-lint` R1/P4. Unguarded: `aw prompts check` is unimplemented. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 rescoped BUILD -> REPAIR: write the id6 into the existing `<!-- aw-prompt: ... -->` comment via E-02's writer, condition the shared path on artifact type, require specs' behavior byte-unchanged, and note the citation rewrite into `jxqdcw` so it is not a surprise in the diff. |
| PR-202 | HIGH | IN-SCOPE | C. Architecture | `check_engine.py:40,744-762`; `.aw/config/project.json` | E-03 would mirror a DEPRECATED mechanism. `SPEC_ID6_CUTOVER_DATE` is a fallback; the live resolver is config-first and the constant is self-described as deprecated. The config path is live here, so the effective spec cutover is `20260829`, not the `20260828` constant the plan copies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now builds `_prompt_requires_id6` as the config-first twin of `_spec_requires_id6` with a non-`None` module fallback, writes `cutovers.prompt_id6 = "2026-09-21"`, declares `project.json`, and answers the `CARRIER_CUTOVER_DATE` counter-precedent in writing. |
| PR-203 | HIGH | IN-SCOPE | A. Correctness | measured corpus; `ls .aw/records/prompts/untracked/` | OQ-02's evidence was FALSE in both halves: the newest legacy tracked prompt date is `20260829` not `20260920`, and the `untracked/` lane it cited does not exist in a lane worktree (no `20260920-12*` file anywhere). A resolved blocking question resting on absent files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reasoning rewritten while keeping the `20260921` answer, which now rests on the conforming `20260920` file rather than on a phantom legacy one; the tighter `20260830` alternative is named and declined with a reason; an explicit warning forbids restoring the discarded argument. |
| PR-204 | HIGH | UNDER-SCOPE | F. Honest documentation | `grep -rn "YYYYMMDD-HHMM-NN"` | FIVE surfaces assert the legacy grammar, not three. The two missed (`prompts/pending/README.md:5`, which also carries a wrong bare `.md` facet, and `research-prompt.md:9`) were absent from both E-05 and `Scope-Paths`; the workflow file is what an agent reads while producing a prompt, so leaving it stale means the next handoff uses the old grammar. Two shipped templates also carry it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now enumerates all five, both were added to `Scope-Paths`, and the template question must be answered in writing either way with its consequence recorded. |
| PR-205 | HIGH | IN-SCOPE | E. Testing | `ls tests/`; `tests/test_prompts_new.py:83,183` | BOTH declared test files DO NOT EXIST (`tests/test_prompts.py`, `tests/test_artifact_naming.py`), and the real tests PIN the legacy behavior: one asserts the literal legacy filename, one asserts the per-minute `-01`/`-02` increment OQ-01 discards. They fail BY DESIGN once E-01 lands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Declared paths corrected to `tests/test_prompts_new.py` and `tests/test_naming_authority_single_source.py`; validation now states those two assertions will fail by design and must be UPDATED in the same change, not read as regressions. |
| PR-206 | HIGH | IN-SCOPE | E. Testing | `_iter_type_files(..., include_retired=False)` -> 2 files | V-03's "ZERO findings against the 17 grandfathered prompts" is UNOBTAINABLE as written: a default `aw check prompts` examines 2 of 17, because `is_retired` excludes the `executed/`/`superseded/` segments where 15 live. An executor would paste "CONFORMS, 2 prompts checked" as proof about 17. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now requires the retired-inclusive call with the FILE COUNT pasted beside the findings count, explicitly fails a pasted 2-file result, and additionally requires the resolved cutover value be non-`None`. |
| PR-207 | MEDIUM | IN-SCOPE | E. Testing | `grep -rn "does NOT add an id6\|deliberately NOT used here"` | V-05's grep is too narrow to see three of the five surfaces: it matches only `artifact_naming.py:41` and `prompts.py:11`, so it would PASS while two READMEs and the workflow still assert the legacy grammar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now greps the GRAMMAR (`YYYYMMDD-HHMM-NN`) across all surfaces rather than two phrasings, and requires every surviving hit to be corrected or justified (a historical citation in an executed plan is legitimate; a live instruction is not). |
| PR-208 | MEDIUM | IN-SCOPE | E. Testing | `pytest tests/test_standalone_verify.py` -> `28 passed` | The pre-authorized failure does NOT exist: the section claims `TheAuditCannotTouchTheFinishedPlan` has "TWO failures that are PRE-EXISTING". Pre-authorizing an absent failure licenses ignoring a real regression in that file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Claim removed and replaced with the measured lane baseline (`1 failed, 7942 passed, 3 skipped, 2 xfailed`; the failure being the ambient-environment `test_turn_bounds.py` case), plus a node-id delta bar. |
| PR-209 | MEDIUM | UNDER-SCOPE | G. Executability / spec sync | spec `:4`, `:182`, `:248`; `discover_specs` | Three unstated facts constrain the spec amendment: its `- Status:` is `implemented` (the one status an agent may not SET, though body amendment is permitted), it carries NO `- Id:` so it is invisible to `discover_specs` and must be cited by path, and it already uses a dated `AMENDED` convention plus tool-attributed history notes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section now states all three, mandates citing by path and using `aw specs note`, forbids changing the status or converting the spec's own name, and records the runner's declared-spec-edit reconciliation obligation. |
| PR-210 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan gate section | The gate lacked the shared-checkout staging discipline and a declaration-style scope fence, and gave an unconditional `aw ipd finalize` instruction which is wrong when a runner owns begin/finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the staged-set verification and post-failed-hook re-verification rules, a declaration-style fence naming the widened paths and the genuinely stop-worthy conditions, the paste-actual-output rule aimed at the two items that have no lint to cite, and conditional finalize ownership. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-04's deliverable already exists and is broken. Rescope, or replan the item? | Rescope in place from BUILD to REPAIR, with a type-conditioned fix and a no-change requirement for specs. | (a) Leave it as "ship the converter", which describes work already done and hides the defect; (b) REPLAN the whole plan, rejected because five of six items are sound and only this one's premise was wrong. | Live preview run shows the verb working; `artifact_rename.py:241-260` shows the H1 anchor; `prompt-purity-lint` R1/P4 makes the injected bullet a violation. | yes |
| D-2 | Should the prompt cutover be a bare constant or config-driven? | Config-first via `resolve_cutover_date(repo_root, "prompt_id6")` with a non-`None` module fallback, mirroring `_spec_requires_id6`. | (a) The bare constant the plan proposed, which copies a self-described deprecated shape; (b) config-only, which risks `None` grandfathering everything (the documented `CARRIER_CUTOVER_DATE` failure). | `check_engine.py:744-762` is config-first; the constant's docstring says "deprecated"; `project.json` already carries `cutovers.spec_id6`, making the live spec boundary `20260829`. | yes |
| D-3 | OQ-02's evidence is false. Change the answer, or the argument? | Keep `20260921`; rewrite the argument and warn against restoring the old one. | (a) Retighten to `20260830`, the literal precedent rule, declined because it buys nothing and adds a way to fail on a file the plan did not create; (b) leave the false reasoning, which would be cited later as fact. | Measured newest legacy date `20260829`; the only `20260920` prompt is conforming; `untracked/` does not exist in a lane worktree. | yes |
| D-4 | Are the two shipped templates carrying the legacy sentence in scope? | Neither in nor out by reviewer fiat: E-05 must ANSWER it in writing, with the consequence recorded. | Silently including them (changes what every managed repo is told) or silently excluding them (leaves templates contradicting this repo's README with nobody noticing). | `templates/prompts-README.md:4` and `templates/agents-docs-README.md:13` are installed into target repos, which have no cutover and no minted id6s until they install this version. | yes |
| D-5 | V-03 cannot get a 17-file result from a default check. Loosen the bar or change the method? | Change the method: require the retired-inclusive call plus a pasted file count. | Loosening to "the prompts that are checked", which would let a 2-file pass stand as evidence about 17. | `_iter_type_files` returns 2 vs 17 for `include_retired` False/True; `is_retired` excludes those path segments. | yes |
| D-6 | May this plan amend a spec whose `- Status:` is `implemented`? | Yes: amending the BODY is permitted; SETTING the status is not, and this plan does neither to the status. | Refusing to amend (leaves requirement E3's enumerated vocabulary contradicting the code) or changing the status (forbidden to an agent). | AGENTS.md restricts an agent from SETTING `implemented`; the spec's own 5.4 already carries dated `AMENDED` entries made by tooling. | yes |
| D-7 | Should this plan implement `aw prompts check`, the unimplemented purity lint? | No: record it as out of scope with the honest consequence that E-04's purity property has no mechanical guard. | Building it here, rejected because it has its own approved spec and would make one review cover a naming migration plus a new lint. | `aw prompts check` exits 2 ("invalid choice: 'check'"); the lint is specified by spec `20260808-1958-01`. | yes |
| D-8 | The two declared test files do not exist. Create them or redeclare? | Redeclare to the real files and require updating their legacy-pinning assertions. | Creating new files beside the existing ones, which would leave two test files covering one verb and the old assertions still failing. | `tests/test_prompts.py`/`test_artifact_naming.py` absent; `tests/test_prompts_new.py:83,183` pin the legacy name and the per-minute increment. | yes |
| D-9 | Is the `Scope-Paths` widening a reviewer over-reach? | No: four additions and two corrections, each justified in the scope check. | Leaving the fence as authored, which would make every new surface an out-of-scope edit discovered at finalize, and would keep two undeclarable nonexistent test paths. | Each addition traces to a finding (F-11, F-12, F-13, F-16); declaring a nonexistent path yields an unsatisfiable `--scope-ack` demand. | yes |
| D-10 | Is the plan's approach sound overall, or does the reversal itself need re-litigating? | Sound; no REPLAN. The reversal is the maintainer's recorded ruling and the plan handles it honestly. | REPLAN, rejected because the goal, the mint seam, the facet support, and the grandfathering strategy all verify; only four premises were stale. | Maintainer ruling quoted verbatim in the history; `ARTIFACT_TYPE_FACETS`/`TYPE_FACET` already support `prompt`; `mint_id6` is the established seam. | yes |

No `Reversible: no` decision was made in this round, so no escalation under the irreversible-decision
rule is owed. No finding was left `OPEN` or `DEFERRED`, so none requires escalation as a blocking
question under the gate threshold (`HIGH`). Both of the plan's blocking open questions were already
`resolved` and remain so; OQ-02's resolution text was corrected rather than reopened, because its
ANSWER was right and only its stated evidence was wrong.
