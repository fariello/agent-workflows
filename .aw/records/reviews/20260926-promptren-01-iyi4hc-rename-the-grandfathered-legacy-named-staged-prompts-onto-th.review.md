# Review findings: plan iyi4hc

- Subject-Id: iyi4hc
- Subject-Type: ipd
- Reviewed-At: 2026-09-27
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0adc7015` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy under
`.aw/state/lane-inputs/rev-9/` matches the tracked file.

THE PLAN'S CORE JUDGEMENT IS SOUND AND ITS HARD NUMBERS RE-DERIVE. I re-measured every count rather than
trusting the authoring pass: `git ls-files '.aw/records/prompts/*.prompt.md'` is 17, exactly 16 match
`^\d{8}-\d{4}-\d{2}-`, and only `20260920-plainlang-01-ng0ga4-...` is clustered, so F-1's correction of the
brief is right. `prompts.has_metadata_comment` is False for exactly 8 files, and they are the 8 the plan
names, so F-2 is right including its correction that the two `superseded/` prompts are also comment-less.
The `--to-id6` mechanism works as described: `inject_metadata_id6` returns text UNCHANGED when line 1 is not
an `aw-prompt` comment (so E-02's before-renaming ordering is load-bearing and not busywork), and a live
preview of a comment-less prompt prints `would record id6 ... in the FILENAME ONLY`, while a
comment-carrying one prints `would write 'Id: ...' into the aw-prompt metadata comment`. The dependency
edge parses and resolves: `runner_shared._read_item_dependencies` returns `['executed:5xzld0']` and that
id6 names the real pending plan.

I ALSO RE-RAN THE WHOLE MIGRATION IN SIMULATION, under post-`5xzld0` semantics (widened reference roots
including `.aw/records/reviews` and `tests`, short-handle to short-handle mapping, fenced-code masking, and
the shared-legacy-prefix skip), over all 16 prompts against the live tree. That simulation is where the
findings below come from; it is the only way to see the edit set this plan will actually produce, because
the plan's own `Scope-Paths` and F-7 were derived from PRE-dependency previews.

WHAT I FOUND, in descending order of consequence.

FIRST, TWO OF THE PLAN'S FOUR VERIFICATION BARS WERE UNREACHABLE OR MEANINGLESS. E-06 demanded that
`aw check prompts --all` report "zero findings". It cannot, by deliberate design: `check_engine.check_types`
appends one `info`-severity `check.collisions-not-checked` finding to every per-type run precisely so a
narrow check never renders an unqualified clean, and its docstring says so. Measured at HEAD:
`"outcome":"conforms","findings":1`, exit 0, that one diagnostic. An executor holding the plan's bar would
either report a conforming run as failed or, worse, quietly redefine the bar mid-execution. The second dead
bar was `aw prompts check`, which E-01 and E-06 both invoked conditionally: the verb does not exist
(`invalid choice: 'check' (choose from 'new')`), its implementing plan `mi4s9f` sits in `not-executed/` and
its spec `prompt-purity-lint` sits in `superseded/`, both retired on 2026-09-26 by an explicit maintainer
decision against any prompt-purity gate. Two of four validation legs were therefore unusable, and the
`check all` baseline the plan quoted (9 findings, `check.ipd-uncarried-obligation` x6) no longer matches
reality either (5 findings, none of those rules).

SECOND, THE PLAN'S OWN DECISION RESTED ON A SUPERSEDED SPEC. The 8-prompt DECISION paragraph justified
inserting a metadata comment partly on "the ONE non-prompt line the purity contract permits (spec
`prompt-purity-lint` P4)". That spec is retired, so the plan cited a withdrawn contract as live authority
for the single most invasive thing it does to a prompt file. The CONVENTION is unaffected and the decision
is still correct, but the citation had to move to surfaces that are actually live.

THIRD, THE LARGEST EDIT CLASS IN THIS MIGRATION WAS UNCHARACTERIZED. The simulation shows TWELVE executed
awphysical plans (Orders 00, 01, 02, 04 through 12) each carrying exactly one identical `legacy x1` hit of
`20260810-1544-01`, all in the same `/plan-review-long` history sentence. The plan's F-7 listed those
plans, and its `Scope-Paths` declares them, but nothing told the executor they are twelve copies of ONE
judgement. Treating them as twelve independent classifications is how a reviewer-executor loses focus and
starts approving rewrites; treating them as one batch with one justification and twelve diffs is honest and
cheap.

FOURTH, THE PLAN'S SAFETY STORY LEANED ON FENCE MASKING THAT DOES ALMOST NOTHING HERE. F-3 and the Goal
framed `5xzld0`'s fenced-code masking as a reason this migration is safe. Computing fence state line by
line with `ipd_lint._FENCE_RE` semantics over every occurrence in the edit set: every single citation in
the external citer set is OUTSIDE a fence. The only fenced hits anywhere are in `5xzld0`'s own review
record (whose last fence is UNCLOSED, so masking there runs to end of file). So the guard that actually
protects the twelve awphysical history lines and the `DECISIONS.md`/`kemhdg` research citations is E-03's
per-occurrence reading, and nothing else. A plan that implies otherwise invites an executor to skim.

FIFTH, TWO SCOPE-FENCE ERRORS IN OPPOSITE DIRECTIONS. `not-executed/` plan `mi4s9f` cites
`20260808-1948-01` twice and was NOT declared, so finalize would demand a `--scope-reason` for an edit the
plan fully intends. Conversely `1bdxcp` IS declared but receives no edit at all once the shared-prefix skip
lands, since its only hit was the `20260725-0957-01` cross-type contamination that skip exists to prevent,
so it needs a `--scope-ack`. Both are small; both would have surfaced as friction at the finalize gate
instead of as a decision at authoring time.

SIXTH, ONE SILENT-DAMAGE PATH NOBODY HAD CHECKED, AND IT IS SAFE. E-02 inserts a line ABOVE the `RETIRED`
banner of the two superseded prompts. That banner is READ, not decorative: `artifact_audit._has_retired_banner`
decides `CLASS_RETIRED` from it, and a demotion would have turned two evidenced retirements into `unknown`
with no error anywhere. I measured it on a copy: the banner is still detected, because `_RETIRED_BANNER_RE`
is multi-line-anchored over a 4096-byte header rather than pinned to line 1. Good news, but it was an
unexamined assumption in the riskiest byte-level edit in the plan, so it is now an explicit validation step.

SEVENTH, `--no-refs` WAS PRESCRIBED WITHOUT SAYING WHAT IT COSTS. E-04 said to run the refusing prompt with
`--no-refs --apply` and then "apply only that prompt's KEEP rewrites by hand", which reads as though
`--no-refs` suppresses the problematic rewrite. It suppresses ALL of them. For the one measured refusing
prompt (`20260727-0655-01`, and I confirmed by calling `find_unrewritable_path_citations` for all 16 that it
is the only one) the KEEP set is EMPTY, because its sole external citer's hit IS the historical `.agents/`
path. So the correct outcome is a rename with zero citation edits, and the plan needed to say that rather
than leaving an executor to report hand-applied rewrites for an empty set.

EIGHTH, ONE EDITED FILE IS SHIPPED PACKAGE CONTENT. `.aw/system/workflows/handoff/handoff.md` is not an
inert record: `pyproject.toml`'s wheel `force-include` maps `".aw/system"` into `agent_workflows/_data/`, and
the sdist `include` list carries `/.aw/system`. The edit is still right (a dangling path inside a shipped
workflow is worse than a changed one) and no test pins the cited line, but "this is a records migration"
was not the whole truth and a human approving it should know.

NINTH, THE `STATUS.md` DEFERRAL WAS TRUE BUT FLATTERING. It is not merely stale: two of its four prompt
citations are ALREADY DANGLING at HEAD, both missing the `.prompt` facet (lines 193 and 208). The deferral
stands, but without this note an executor's final grep would show four bad `STATUS.md` hits and could
plausibly report them as this migration's residue.

WHAT I CHECKED AND FOUND NO PROBLEM WITH. The one-at-a-time decision (OQ-01) is correct and its stated
reason is real: prompt `20260810-1530-01` does cite `20260810-1544-01` in its own metadata comment, so a
batch rename could rewrite a file it is also renaming. The shared-prefix census re-derives to exactly one
collision (`20260725-0957-01`, prompt and spec), matching `5xzld0`'s review. The out-of-scan-root sweep
really does return one file: `git grep -l` for all 16 legacy prefixes over `agent_workflows/`, `.aw/system/`,
`docs/` and root `*.md` (excluding `.aw/records`) yields only `handoff.md`, and the two host command shims
are `Read and execute @...` pointers that never name the prompt. The three `tests/` files that contain
legacy prompt names (`test_prompts_index.py`, `test_prompts_attention.py`) use them as INVENTED FIXTURE
names inside tmp repos, not as citations of these records, and the simulation confirms no rewrite lands in
`tests/` at all. `Work-Kind: chore` with no `Blocks-Release` is correct under the repository's gating rule
(the gating set is `bug`; this is a naming migration with no user-perceptible defect). The plan claims no
execution, carries no hand-written `- Readiness:`, and its gate already had the honesty rule, the
path-scoped commit, the never-push, the conditional finalize ownership, and a correctly narrow
STOP-AND-REPORT that fires only on genuine unsafety rather than on a scope question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / G. Executability (an unreachable acceptance bar) | `python3 -m agent_workflows check prompts --all --agent` -> `{"outcome":"conforms",...,"findings":1}` with diagnostic `check.collisions-not-checked` at `<collisions>`, exit 0; `check_engine.check_types` docstring: "a skipped scan now emits ONE `info`-severity `check.collisions-not-checked` finding" rather than "rendering an unqualified `CONFORMS / errors 0 warnings 0`"; `check all --agent` at HEAD -> 5 findings (`check.scope-drift` on `olkeju`, 3x `check.id6-identity-slot`, `check.system-layout-missing`), NOT the authored 9, and no `check.ipd-uncarried-obligation` fires at all | **THE PLAN'S PRIMARY VALIDATION BAR CANNOT BE MET BY A CONFORMING RUN, AND ITS BASELINE QUOTE IS ALREADY WRONG.** E-06 and V-06 demanded "zero findings" from `check prompts --all`; a correct run always reports one. An executor either reports a passing migration as failed, or silently reinterprets the bar, which is exactly the kind of mid-execution redefinition that makes a V-item worthless. The stale `check all` baseline compounds it: comparing against 9 phantom findings would have made any real new finding invisible in the noise. | C:Low; U:Low; S:Low; F:Medium (a green migration reported red, or a bar quietly rewritten mid-run); the FIX is Low | FIXED | E-06 rewritten: the bar is "nothing beyond `check.collisions-not-checked`", with the mechanism and the measured JSON cited; the `check all` count is required to be RE-DERIVED at execution and the stale 9-finding claim is replaced with the measured 5 plus the note that the authored rule names no longer fire. V-01 now requires both baseline finding SETS pasted in full (rule+location pairs), not counts, so V-06's line-by-line comparison is actually possible. Recorded as F-8. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Executability (two steps invoking a verb that does not exist) | `python3 -m agent_workflows prompts check` -> `error: argument prompts_command: invalid choice: 'check' (choose from 'new')`; `.aw/records/plans/not-executed/20260926-promptlint-01-mi4s9f-...ipd.md` banner: "maintainer decided against any prompt-purity gate ... no replacement"; `.aw/records/specs/superseded/20260808-1958-01-prompt-purity-lint.spec.md` `- Status: superseded` with the agreeing 2026-09-26 history note | **TWO CHECKLIST ITEMS CALLED A RETIRED VERB, AND ONE OF THEM GATED ON A PLAN THAT WILL NEVER RUN.** E-01 said to capture a baseline "if `5xzld0`'s sibling `mi4s9f` has landed" and E-06/V-06 said to run `aw prompts check` "if available". `mi4s9f` is `not-executed` by maintainer decision and its spec is `superseded`, so both conditions are permanently false. Left in place they invite an executor to either wait on a dependency that is dead or paste an `invalid choice` error as evidence. | C:Low; U:Low; S:Low; F:Medium (a dead gate read as a pending prerequisite) | FIXED | Every reference removed and replaced with an explicit statement that the verb does not exist and is not coming, with the retirement evidence, in E-01, E-06, V-06 and the "Proposed changes" list. Recorded as F-9. |
| PR-003 | MEDIUM | IN-SCOPE | F. Honest documentation (a decision resting on a withdrawn contract) | The 8-prompt DECISION cited "the ONE non-prompt line the purity contract permits (spec `prompt-purity-lint` P4)"; that spec is in `.aw/records/specs/superseded/`; `.aw/records/prompts/README.md` documents the `<!-- aw-prompt: ... -->` line and the `--to-id6` converter; `prompts.render_metadata_comment` docstring records why the metadata is a comment and not front matter | **THE PLAN'S MOST INVASIVE EDIT WAS JUSTIFIED BY A RETIRED SPEC.** Inserting a line into 8 prompt files is the one place this migration changes prompt CONTENT, and its stated authority was withdrawn on 2026-09-26. The convention is unchanged, so the decision survives; but a plan that cites a superseded spec as live teaches the next reader to cite it too, and `mi4s9f`'s retirement means nothing will ever enforce P4. | C:Low; U:Low; S:Low; F:Low | FIXED | Reason (3) rewritten to name the spec as HISTORY and to rest the convention on `.aw/records/prompts/README.md` and `render_metadata_comment`'s docstring. The Spec-sync section now states explicitly that no spec is amended, why amending a retired spec would be wrong, and that the superseded spec's own `20260808-1948-01` citation is a historical `.agents/` path that must not be rewritten. Recorded in F-9. |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Anti-regression / G. Executability (an uncharacterized bulk-edit class) | Post-`5xzld0` simulation over all 16 prompts: twelve executed awphysical plans (Orders 00, 01, 02, 04-12) each carry exactly one `legacy x1` hit of `20260810-1544-01`, every one in the same `/plan-review-long` sentence "...appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS..."; the 13th citer `jxqdcw` carries `full x1 + whole x1 + legacy x2` in E-item prose naming the FILE; fence-state computation puts all twelve OUTSIDE any fence | **THE DOMINANT EDIT CLASS WAS PRESENTED AS TWELVE SEPARATE JUDGEMENTS WITH NO GUIDANCE, AND ITS ONLY GUARD IS MANUAL READING.** Twelve of roughly twenty external citers are one repeated history sentence. E-03 gave rules but no batching, so an executor faces twelve near-identical classifications and, worse, may assume fence masking protects transcripts like these; it does not, because none of them is fenced. That combination (repetitive judgement plus a false sense of automatic protection) is how a history line gets silently rewritten. | C:Low; U:Low; S:Low; F:Medium (a falsified review history line in twelve executed plans) | FIXED | E-03 gains the measured census: the twelve are named as ONE rule-(c) batch with one justification, the 13th citer is separated as KEEP, and the previously-unlisted `mi4s9f` and `ubac5n.review.md` citers are added. V-03 permits one table row for the batch but still requires twelve individual `git diff` proofs, and requires the executor to say whether the live citer counts matched this simulation. Recorded as F-12/F-13. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness (a safety premise that does not hold) | Fence state computed with `ipd_lint._FENCE_RE` semantics (`^(\s*)(```\|~~~)`) over every occurrence in the edit set: all external citations are unfenced, including `DECISIONS.md` L2243/2247/2249/2267, `kemhdg` L30/33/44/70, `wn2jto` L14, and all twelve awphysical history lines; the only fenced hits are in `5xzld0`'s review record, whose fences toggle at lines 22, 32, 34, 39, 42 leaving `inside=True` at EOF (unclosed) | **F-3 AND THE GOAL IMPLY FENCE MASKING PROTECTS THIS MIGRATION'S TRANSCRIPTS. IT PROTECTS ALMOST NOTHING HERE.** The plan names fenced-code masking as one of three reasons `5xzld0` is a hard dependency. The other two (shared-prefix skip, short-handle mapping) genuinely bite; masking does not, because every citation this plan must classify is plain prose. Overstating an automatic guard directly reduces the care applied to the manual one. | C:Low; U:Low; S:Low; F:Medium (over-trust in an inapplicable guard) | FIXED | E-03 states plainly that fence masking protects almost nothing in this migration, names the one place it does bite, notes the unclosed fence, and instructs classification by READING rather than by assuming a transcript is fenced. Recorded as F-13. |
| PR-006 | MEDIUM | UNDER-SCOPE | D. Anti-regression (an unexamined silent-damage path) | `artifact_audit._has_retired_banner` is what makes `classify_difference` return `CLASS_RETIRED` ("retired into {actual}/ with a RETIRED banner and an agreeing - Status:"), else `CLASS_UNKNOWN` with "the retirement is unevidenced (no RETIRED banner)"; `_RETIRED_BANNER_RE` is `(?m)^[ \t]*(?:<!--[ \t]*)?(?:>[ \t]*)?\**RETIRED\b` read over a 4096-byte header; measured at review on a copy of `20260717-1950-01` with the rendered comment inserted as line 1: `_has_retired_banner` -> `True` | **E-02 MOVES A MACHINE-READ BANNER OFF LINE 1 IN TWO FILES AND THE PLAN NEVER CHECKED WHETHER THAT MATTERED.** Had the regex been line-1-anchored, both superseded prompts would have silently dropped from `retired` to `unknown` in the artifact audit, with no error raised anywhere and nothing in the plan's validation able to see it. The measurement says the insertion is safe, so this is a near miss rather than a defect, but an unverified assumption in the only byte-level content edit is not acceptable. | C:Low; U:Low; S:Low; F:Medium if the regex had been anchored; the FIX is Low | FIXED | E-02 records the measurement with the regex and the reason the banner survives, and instructs re-confirmation after the edit. V-02 now REQUIRES the pasted `_has_retired_banner` output for both superseded prompts after insertion, plus the chosen Kind's membership in `prompts.PROMPT_KINDS` (nothing validates that value, so an off-list Kind would be written silently). |
| PR-007 | MEDIUM | IN-SCOPE | A. Correctness (a flag whose blast radius was understated) | `run_rename_generic`: `update_refs = not bool(getattr(args, "no_refs", False))`, and `ref_edits` is computed only `if update_refs`, so `--no-refs` suppresses EVERY rewrite; `find_unrewritable_path_citations` called for all 16 prompts at review returns a non-empty list for exactly ONE, `20260727-0655-01`, on `.agents/prompts/pending/...` in `wn2jto` (the refusal condition being that `agents/prompts/pending` is neither a suffix of nor suffixed by the real dir `.aw/records/prompts/executed`); that prompt's only external citer is that same historical path | **E-04 READS AS THOUGH `--no-refs` DROPS THE PROBLEM CITATION; IT DROPS ALL OF THEM, AND THE PLAN THEN ASKS FOR A HAND-APPLIED KEEP SET THAT IS EMPTY.** An executor told to "apply only that prompt's KEEP rewrites by hand" for an empty set will either invent an edit or report work it did not do. The correct outcome is a rename with zero citation changes, which is a perfectly good answer that the plan did not permit itself to give. | C:Low; U:Low; S:Low; F:Medium (a fabricated or mis-reported edit at the one fail-loud step) | FIXED | E-04 rewritten: states that `--no-refs` suppresses every rewrite, re-derives the refusal set (exactly one prompt) with the reason the directory comparison fails, and states that this prompt's KEEP set is EMPTY so the expected result is a rename with no citation edit. V-04 accepts an explicit empty-set statement plus `git diff --stat` as evidence and flags a non-empty diff there as requiring explanation. Recorded as F-6 amendment. |
| PR-008 | LOW | IN-SCOPE | C. Architecture / F. Honest documentation (a packaged-content edit described as a record edit) | `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]`: `".aw/system" = "agent_workflows/_data/.aw/system"`; sdist `include` list contains `/.aw/system`; `git grep` of the cited prompt name across `tests/` returns nothing; `.opencode/commands/handoff.md` and `.claude/commands/handoff.md` are `Read and execute @.aw/system/workflows/handoff/handoff.md` shims that do not name the prompt | **THE GATE TOLD A HUMAN THEY WERE APPROVING "A RECORDS MIGRATION" WHILE ONE EDITED FILE SHIPS IN THE WHEEL.** E-07's parenthetical even says "only records and one shipped workflow body", so the author knew; the approval summary did not say it. A human deciding whether this is a low-risk records change deserves to know one line of packaged content moves. | C:Low; U:Low; S:Low; F:Low | FIXED | E-05 declares the file as shipped content with the `pyproject.toml` mapping cited and notes no test pins the line; F-11 records it; the gate's "WHAT A HUMAN IS APPROVING" now surfaces it as the first of two things a human should know before approving. Also confirmed and recorded that the two host command shims need no edit. |
| PR-009 | LOW | IN-SCOPE | G. Executability (a two-way scope-fence error) | Post-`5xzld0` simulation: `.aw/records/plans/not-executed/20260926-promptlint-01-mi4s9f-...ipd.md` receives `full x2 + whole x2` for `20260808-1948-01` and is absent from `- Scope-Paths:`; `.aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...ipd.md` is declared but receives ZERO edits once the shared-prefix skip lands, its only prior hit being the `20260725-0957-01` cross-type contamination `5xzld0` E-05 removes | **ONE INTENDED EDIT IS OUTSIDE THE FENCE AND ONE DECLARED PATH WILL NOT BE TOUCHED.** Neither is dangerous, but both surface at `aw ipd finalize` as friction (an unexplained `--scope-reason` demand and an unacknowledged declared path) at the worst moment, after the work is done, rather than as a decision now. | C:Low; U:Low; S:Low; F:Low | FIXED | `mi4s9f` added to `- Scope-Paths:`; the Scope check section records `1bdxcp` as deliberately declared-but-unmodified with the `--scope-ack` instruction and the reason for keeping it declared. Recorded as F-12. |
| PR-010 | LOW | IN-SCOPE | F. Honest documentation (a deferral that understates existing breakage) | `artifact_refs._SKIP_NAMES` = `{'INDEX.md','STATUS.md','README.md'}`; `.aw/records/plans/STATUS.md` L193 cites `.aw/records/prompts/executed/20260722-2317-01-token-efficient-managed-sections-research-prompt.md` and L208 cites `.aw/records/prompts/superseded/20260717-1950-01-session-handoff-resume-here.md`, both missing the `.prompt` facet and therefore dangling at HEAD; L196 and L198 cite two names this rename breaks; last regenerated 2026-08-17 | **THE `STATUS.md` DEFERRAL SAYS "STALE" WHERE THE TRUTH IS "HALF ITS PROMPT CITATIONS ARE ALREADY BROKEN".** The decline is correct. But the executor's final grep will surface four bad `STATUS.md` hits, and with the plan calling the file merely stale, the natural report is that this migration left four dangling citations, which would be false for two of them. | C:Low; U:Low; S:Low; F:Low | FIXED | The deferral entry is amended with the measured pre-existing breakage and an explicit instruction not to report those hits as this migration's residue; E-05 and V-05 require the executor to label which `STATUS.md` hits pre-dated the plan. Recorded as F-10. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `aw check prompts --all` can never report zero findings. Change the plan's bar, or have the executor pass `--agent` and filter, or ask the maintainer to make the notice suppressible? | CHANGE THE BAR to "nothing beyond `check.collisions-not-checked`", naming the mechanism. | (a) Have the executor filter the finding out of the output: rejected, it hides a deliberate design notice and makes the pasted evidence non-literal, which the honesty rule forbids. (b) Ask the maintainer for a suppression flag: rejected, `check_types`'s docstring already records this exact question as resolved (the three candidates considered, the `info` notice chosen as the cheapest that removes the false clean), so re-asking spends maintainer time on a settled design. (c) Leave "zero findings": rejected outright, it is unreachable and would make a conforming run look failed. | `check_engine.check_types` docstring and its `check.collisions-not-checked` emission gated on `if checked:`; measured `{"outcome":"conforms","findings":1}` exit 0; `drift_exit_code` ignores `info` | yes |
| D-2 | `aw prompts check` does not exist and its spec is superseded. Remove the references, or leave them as harmless conditionals? | REMOVE them and state the retirement with evidence. | (a) Leave the "if available" hedges: rejected, a dead conditional reads as a pending prerequisite; an executor could wait on `mi4s9f` or paste an `invalid choice` error as evidence of nothing. (b) Re-open the purity lint as part of this plan: rejected emphatically, the maintainer retired both plan and spec on 2026-09-26 with a stated reason, and resurrecting it inside a rename migration would be a scope invasion and a reversal of a human decision. | `prompts` subparser accepting only `new`; `mi4s9f` in `not-executed/` with its RETIRED banner; `prompt-purity-lint` in `superseded/` with the agreeing history note | yes |
| D-3 | The 8-prompt DECISION cites a superseded spec as live authority. Re-point the citation, or drop the reason entirely? | RE-POINT it to live surfaces and mark the spec as history. | (a) Drop reason (3): rejected, the "invisible when pasted" property is the actual reason a comment is acceptable inside a prompt at all, so deleting it would leave the decision weaker than it is. (b) Keep citing P4 as current: rejected, it teaches the next reader to cite a withdrawn contract, and nothing enforces P4 now that `mi4s9f` is retired. (c) Amend the superseded spec to remove the staleness: rejected, editing a retired spec asserts a history that did not happen. | `.aw/records/prompts/README.md`'s documented `aw-prompt` line and `--to-id6` converter; `prompts.render_metadata_comment` docstring on why a comment and not front matter; the spec's `superseded` status and history note | yes |
| D-4 | The `RETIRED` banner moves off line 1 in two files. Measure whether the audit still sees it, or restructure E-02 to insert BELOW the banner? | MEASURE IT, keep the comment on line 1, and require re-confirmation in validation. | (a) Insert the comment below the `RETIRED` banner: rejected on measurement, since the banner survives line-1 insertion and `prompts.inject_metadata_id6`/`validate_prompt_content` both require the `aw-prompt` comment to be the FIRST line (`if not lines or "<!-- aw-prompt:" not in lines[0]: return text`), so inserting below it would leave both files with an unreadable comment and no in-file id6. (b) Skip the comment for the two superseded prompts: rejected, it would leave the two oldest records with filename-only identity for no benefit. (c) Assume it is fine without measuring: rejected, this is the only byte-level content edit in the plan and its failure mode is silent. | `artifact_audit._has_retired_banner` + `_RETIRED_BANNER_RE` multi-line over a 4096-byte header; `classify_difference`'s `CLASS_RETIRED` branch requiring the banner; `prompts.inject_metadata_id6` line-1 requirement; measured `True` after insertion on a copy | yes |
| D-5 | Twelve executed awphysical plans each carry the same history-line citation. Batch them as one classification, or require twelve independent ones? | BATCH the JUDGEMENT (one row, one justification) but require twelve individual `git diff` proofs. | (a) Twelve independent classifications: rejected, they are byte-identical occurrences of one sentence; twelve separate judgements is busywork that degrades attention precisely where the guard is manual reading. (b) Batch both judgement AND evidence (one diff claim covering twelve files): rejected, that is exactly the unverifiable bulk claim that lets a rewrite slip through unnoticed; the diffs are cheap and are the only proof the revert happened. | The twelve measured occurrences, all in the same `/plan-review-long` sentence; fence-state computation showing all twelve unfenced; AGENTS.md's rule that a V-item must demand concrete pasted evidence | yes |
| D-6 | `1bdxcp` is declared in `Scope-Paths` but will receive no edit after the dependency lands. Remove it from the fence, or keep it and acknowledge? | KEEP it declared and instruct `--scope-ack`. | (a) Remove it: rejected, the prediction that it receives no edit rests on `5xzld0` behaving exactly as simulated; if the shared-prefix skip differs at all, the edit reappears and an undeclared path then needs a `--scope-reason` with no prior reasoning recorded. Keeping it costs one `--scope-ack`. (b) Say nothing: rejected, an unexplained declared-but-unmodified path is friction at the finalize gate. | Post-`5xzld0` simulation showing zero edits into `1bdxcp`; `5xzld0` E-05's shared-prefix skip and its own re-measured single collision; `aw ipd finalize`'s `--scope-ack` requirement for declared-but-unmodified paths | yes |

### Deferred and open

- (none DEFERRED among findings). All ten findings are FIXED in place. PR-001 and PR-002 are `HIGH` and both
  are FIXED, so no finding at or above the repository's gate threshold (no `review_findings_gate` is
  configured in `.aw/config/project.json`, so the default `HIGH` applies) is left `OPEN` or `DEFERRED`, and
  nothing is owed an escalated `- Blocking: yes` question carrying `- Finding:`.
- No `Reversible: no` decision was taken, so nothing is owed an escalation to the maintainer. Every decision
  above changes only plan text and can be undone by editing the plan.
- The plan's single open question OQ-01 is `resolved` and `Blocking: no`, and its stated reason re-verifies
  (prompt `20260810-1530-01` genuinely cites `20260810-1544-01` inside its own metadata comment, so a batch
  rename could rewrite a file it is concurrently renaming).
- The two `Carrier-Declined` entries stand. Lowering `cutovers.prompt_id6` is a per-repo policy change for
  the maintainer, correctly declined. Regenerating `STATUS.md` remains declined, with PR-010's amendment
  recording that two of its prompt citations were already dangling before this plan.
- ONE ITEM A HUMAN MAY WANT TO WEIGH, raised here rather than as a finding because it is a judgement about
  appetite and not a defect: this plan edits the text of 20 tracked records, 15 of them in `executed/`, to
  change filenames of retired prompts. Every edit is legitimate reference rewriting and is declared, and the
  payoff is real (16 prompts become `aw find`-resolvable). But the benefit accrues mostly to prompts that are
  already `executed` or `superseded`, so a maintainer who would rather not touch fifteen executed plans for
  that payoff should say so before approval; the plan is correct either way, and that is a scope preference
  no repository evidence can settle.
