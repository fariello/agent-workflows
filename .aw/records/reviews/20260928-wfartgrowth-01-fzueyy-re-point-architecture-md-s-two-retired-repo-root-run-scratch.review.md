# Review findings: plan fzueyy

- Subject-Id: fzueyy
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `086df9f2` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-9/` copy. NO TRACKED FILE
WAS MODIFIED BY THIS REVIEW except the plan itself and this record: every probe ran against a copy of
the tree under `/tmp`, the one installer probe ran in its own throwaway `git init` repo, and
`git status --short` was empty of product changes before and after.

**THE PLAN'S DIAGNOSIS IS CORRECT IN EVERY PARTICULAR AND EVERY MEASURED CLAIM REPRODUCED.** F-1
reproduces: `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returns two occurrences at
147 and 201, the first inside the section headed `### State: the authoritative run directory` and
reading `Every run creates \`workflow-artifacts/<workflow-name>/<RUN_ID>/\` (timestamped;` three lines
above `is the authoritative record`, the second reading `` `workflow-artifacts/` run records, user
code, or `.aw/records/`.`` after `Pruning is strictly scoped to the framework namespace`. F-4
reproduces at `CONTRIBUTING.md:251`. F-2 reproduces END TO END, which is the claim that makes this a
bug rather than a typo: review installed this lane into a throwaway repo and git reports exit 1 with
no output on `workflow-artifacts/probe` (nothing ignores it, and the fresh install writes NO root
`.gitignore` pattern for it) while `.aw/workflow-artifacts/probe` matches
`.aw/.gitignore:75:/workflow-artifacts/`. F-3's honesty holds too: in THIS checkout the retired path
matches `.gitignore:52`, so the leak lands on a target-repo reader, exactly as the plan states rather
than overreads. F-5 holds (`git show 19313eed --stat` lists `tests/test_docs.py | 472 ---`, the file is
absent, `rg bare_run_scratch tests/` returns nothing, and all three symbols recover from the parent
commit). F-6 holds (0 bare occurrences under `.aw/system/`, 0 under `docs/`). F-7 holds verbatim
(`File-based state makes runs recoverable, auditable, committable, and`, three lines below the first
occurrence, in the same `**Why externalize state to files:**` paragraph, still citing D7). F-8 holds
(`tests/test_packaging.py` absent at `503 ---`; `run_analytics_spa.py` still cites it in a
user-visible string). The two carrier ids resolve. The plan's per-file exclusion reasoning is right:
`DECISIONS.md` (40) and `CHANGELOG.md` (5) genuinely are dated records, and D19/D117-D121 read exactly
as the plan characterizes them. E-02's over-scope argument is SOUND and well evidenced: D120's own
entry names five prose defects of precisely this class left behind by the D117 sweep, so leaving
`committable` beside a corrected path would reproduce the defect D120 existed to clean up.

Five findings concern the guard this plan's whole value rests on, and four of them were measured by
building the guard and running it.

**PR-701 (HIGH): THE ROOT-DOC SURFACE WAS AN ENUMERATED ALLOWLIST, WHICH DECAYS SILENTLY IN EXACTLY
THE WAY THIS PLAN EXISTS TO PREVENT.** E-04 specified the third surface as seven literal filenames,
and the recovered sweep it builds on skips a non-existent path (`if not p.is_file(): continue`).
Review measured the consequence in a scratch copy: rename `ARCHITECTURE.md` away and the enumerated
sweep reports `scanned=6 offenders=[]` and PASSES, having silently stopped covering the very file this
plan is named after, with `assertTrue(scanned)` satisfied throughout. A new root doc is likewise
invisible to it. A `glob("*.md")` minus a named exclusion set picks the renamed file up, and review
measured that today it yields EXACTLY the seven names the allowlist carried, so the change costs no
coverage and removes the decay mode. This also DISSOLVES the cross-plan reconciliation `cf7f8z`'s
review raised as its PR-B02: with `tools/README.md` unreachable by any surface, the exclusion constant
needs no entry for it and there is no stale reason for either landing order to fix.

**PR-702 (HIGH): ONE SHARED `scanned` COUNTER ACROSS THREE SURFACES PASSES WHEN A WHOLE SURFACE
VANISHES.** The recovered test asserts `assertTrue(scanned, "no shipped bodies were scanned")`, which
is correct on ONE surface and becomes a hole on three. Measured: move `docs/` aside and the combined
counter reports `scanned=160` and PASSES while the `docs/` surface contributes ZERO files and is
silently unguarded. The plan's own Expected outcome asked only for "the number of files scanned",
singular, so an executor following it literally builds the hole.

**PR-703 (HIGH): E-05's FALSIFICATION METHOD WROTE TO TRACKED FILES IN A SHARED CHECKOUT AND RELIED ON
A REVERT IT CANNOT GUARANTEE.** The item instructed the executor to "reintroduce ONE bare reference"
into a shipped body, a `docs/` page and `ARCHITECTURE.md` in turn, then "revert immediately, verifying
with `git status --short`". `AGENTS.md` states other agents and humans may be working concurrently in
this checkout, and the safety here is a revert AFTER the damage: a failing assertion, a timeout or an
interrupted turn leaves the poison in a tracked file, and `git status --short` then reports the problem
rather than preventing it. Review performed the ENTIRE falsification against temporary copies instead
and it worked first time, so the safe method is not merely preferable but demonstrated: green over the
post-fix tree at `shipped: scanned=153, docs: scanned=28, root-docs: scanned=7`, then three separate
reds, each naming only its own file and surface while the other two stayed green, with no tracked file
written at any point.

**PR-704 (MEDIUM): THE RESTORATION RECIPE NAMED NO DEPENDENCY SET, THE SAME GAP THAT COST `cf7f8z`'s
RECIPE 13 `NameError`s.** Rather than assume this restoration is simpler, review ran the same AST
free-variable pass: `_bare_run_scratch_refs` closes over `re`; `ShippedRunScratchPathTests` over
`REPO_ROOT`, `_bare_run_scratch_refs` and `unittest`; the falsifiability class over
`_bare_run_scratch_refs` and `unittest`. So three imports suffice and no module-level helper is hidden
(a genuinely better outcome than `cf7f8z`'s, worth recording as such). The finding is that NONE of the
deleted file's four production-module imports (`docs_check`, `docs_render`, `host_adapters`,
`host_capability_registry`) is referenced, so a mechanical carry-everything would make a file the plan
declares free of production reads import three production modules and contradict its own OQ-02.

**PR-705/PR-706 (LOW): THE TRANSCRIBED COLLECTED BASELINE HAD DRIFTED 120 TESTS AND THE PRESCRIBED
COMMAND USES THE WRONG MARKER.** The plan records `3122/3322 (200 deselected)`; review measured
`3237/3442 (205 deselected)` at HEAD, and the sibling plans of this sweep recorded the identical
failure mode three times (drifts of 60, 138 and 93). Separately, `pyproject.toml` `addopts` reads
`-m 'not slow and not livecorpus'` while the plan's reproduction command passes `-m "not slow"`, which
review measured collects `3242/3442 (200 deselected)`, five tests more than the bare suite, so a delta
computed with it is wrong before this plan changes anything.

**PR-707 (LOW): F-9's EVIDENCE COMMAND CANNOT SUCCEED.** It is written `rg 'docs_check\|docs_render'`,
which searches for the LITERAL string `docs_check\|docs_render` rather than the alternation, so it
returns nothing whether callers exist or not and proves nothing. Review verified both forms against a
file that does contain `docs_check`: the escaped form exits 1, the correct alternation matches. THE
CLAIM ITSELF IS TRUE under the correct pattern, so this is an evidence defect and not a false finding,
and it is worth fixing because the same string is quoted in backlog `gzmr54` as its evidence.

**PR-708 (LOW): TWO INTERNAL CONTRADICTIONS LEFT BY AN AUTHORING-TIME REVISION.** `Proposed changes`
item 6 read "File backlog items for..." while E-06 says `DO NOT CREATE A SECOND PAIR` and its whole
deliverable is verification; a reader acting on the summary does the thing the item forbids. And
`- Scope-Paths:` declared `.aw/records/backlog/open/` although E-06 writes nothing there, which is
precisely the declared-but-unmodified path `aw ipd finalize` refuses to complete without a
`--scope-ack` for.

**PR-709 (MEDIUM, UNDER-SCOPE): THE GATE HAD NO SCOPE FENCE AND NO APPROVAL SUMMARY.** It carried a
strong execution contract and post-gate section, but no declaration for the runner to reconcile the
diff against, and nothing telling a human in one place what they are approving. This plan carries six
distinct prohibitions spread across its Scope statement and five Deferred rows, and one of them
(`tools/README.md`, owned by pending plan `cf7f8z`) is a genuine collision hazard with a concurrently
reviewed plan.

**WHAT REVIEW CHECKED AND FOUND SOUND.** The regex is correctly reused rather than re-derived, and its
three deliberate non-matches are each real: the template file
`.aw/system/workflows/templates/workflow-artifacts-README.md` exists and its CONTENT measures 0 bare
occurrences, `scan_secrets.py`'s `SKIP_DIR_NAMES` entry is bare with the quoted comment, and
`.aw/.gitignore:75` is the anchored pattern with the `/inbox/` explanation above it. The occurrences
unit (not lines) is right. E-03's prerequisite argument is correct, not opportunism. Both
`Carrier-Declined` rows are honest rather than formulaic, and the reason given for `DECISIONS.md` is
the strongest form of it (filing an item would schedule the falsification of a record). The
already-filed carriers are the right call and the plan's explanation of WHY they were filed at
authoring (the `error`-severity `check.ipd-uncarried-obligation` rule refuses a dangling `Carrier:`)
is accurate. Right-sizing is appropriate at six E-items. The `6vozur` collected-count lesson is
carried and is the right lesson. The no-spec-amendment conclusion is correct: `u7xtni` already rules
the live path, so there is no contract to change.

Review also recorded a limit the plan did not, so its under-scope statement is not overread:
`agent_workflows/engine.py` carries twelve bare occurrences and EVERY ONE is correct, each naming the
retired path as its subject. So excluding production source costs no real coverage here, and a later
plan should not "close" that as a gap.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a `- Blocking:
yes` question is owed and none was written. Both open questions survive review UPHELD, with their
`Owner` corrected from `none` to `plan author` (a resolved question records who chose), and OQ-01 is
now largely moot by construction after PR-701.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | E. Testing / D. Anti-regression | scratch-copy rename probe: enumerated seven-name sweep reports `scanned=6 offenders=[]` and PASSES after `ARCHITECTURE.md` is renamed away, while `glob("*.md")`-minus-exclusions picks the renamed file up at `scanned=7`; measured equivalence today, the glob form yields exactly `AGENTS.md ARCHITECTURE.md CONTRIBUTING.md GUIDING_PRINCIPLES.md README.md RELEASING.md TODO.md`; `tools/README.md` is not a root `*.md`, not under `docs/`, not under `.aw/system/workflows/` | THE ROOT-DOC SURFACE WAS AN ENUMERATED ALLOWLIST, WHICH DECAYS SILENTLY. A renamed or newly added root doc leaves the guard passing with coverage lost, which is the same silent-decay class this plan exists to repair. The listed-exclusion design also forced a `tools/README.md` entry whose stated reason plan `cf7f8z` invalidates, creating the cross-plan reconciliation that plan's review raised as PR-B02. | C:Low; U:Low; S:Low; F:Low; Overall:Low (derive the surface from a glob and keep a two-entry exclusion constant; review measured the result identical today) | FIXED | E-04 gained a GLOB-MINUS-EXCLUSIONS paragraph with the rename measurement, the required non-emptiness assertion on the derived surface, and an explicit prohibition on a `tools/README.md` entry with the reason (no surface reaches it, so the entry would be inert). Added F-11 and F-12. V-04 now requires the derivation expression, the seven yielded names, and confirmation that no `tools/README.md` entry exists. Proposed change 4 updated. |
| PR-702 | HIGH | IN-SCOPE | E. Testing and verification | scratch-copy probe: with `docs/` moved aside the `docs` surface scans 0 files while a single shared counter reports `scanned=160` and PASSES; the recovered assertion is `self.assertTrue(scanned, "no shipped bodies were scanned")`, written for one surface | ONE SHARED `scanned` COUNTER ACROSS THREE SURFACES PASSES WHEN A WHOLE SURFACE VANISHES. The plan's Expected outcome asked for "the number of files scanned" (singular), so an executor following it literally builds a guard that cannot detect losing an entire swept surface. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gained a COUNT PER SURFACE paragraph carrying the docs-removal measurement and requiring per-surface non-emptiness plus the surface named in every failure message. Expected outcome now says PER SURFACE, not one shared total. V-04 requires a separate count per surface AND the three assertions pasted. Added F-11. |
| PR-703 | HIGH | IN-SCOPE | B. Security / C. Operability (shared checkout) | the item's own wording, "reintroduce ONE bare reference ... and revert immediately, verifying with `git status --short`", against `AGENTS.md`'s shared-checkout rule; review's temp-copy run: green at `shipped: scanned=153, docs: scanned=28, root-docs: scanned=7`, then three reds naming only `.aw/system/workflows/plan-review/plan-review.md`, `docs/architecture.md` and `ARCHITECTURE.md` respectively with the other two surfaces green, no tracked file written | E-05's FALSIFICATION WROTE TO TRACKED FILES IN A SHARED CHECKOUT AND DEPENDED ON A REVERT IT CANNOT GUARANTEE RUNS. A failed assertion, timeout or interrupted turn leaves a bare reference in `ARCHITECTURE.md` or a shipped workflow body, and the prescribed `git status --short` reads the damage rather than preventing it. | C:Low; U:Low; S:Low; F:Low; Overall:Low (review performed the safe method end to end) | FIXED | E-05 rewritten to poison a TEMPORARY COPY, with review's green and red measurements quoted as proof the method suffices, plus a preference for encoding the cases as permanent tests over one-off probes. E-04 gained a requirement that the sweep be ROOT-PARAMETERIZED, which is what makes this possible. Expected outcome now demands an EMPTY `git status --short` throughout rather than a restored one. V-05 requires the temp-copy method be stated, the other two surfaces shown green, and the permanent-versus-probe choice declared. Added F-13. The scope fence forbids editing any file to produce a red run. |
| PR-704 | MEDIUM | IN-SCOPE | E. Testing / G. Plan executability | AST free-variable pass: `_bare_run_scratch_refs: ['re']`, `ShippedRunScratchPathTests: ['REPO_ROOT', '_bare_run_scratch_refs', 'unittest']`, `ShippedRunScratchGuardFalsifiabilityTests: ['_bare_run_scratch_refs', 'unittest']`; the deleted file's import block carries `docs_check as dc`, `docs_render as dr`, `host_adapters as ha`, `host_capability_registry as hcr`, none referenced by the three recovered symbols; `tests/support.py` defines `REPO_ROOT = Path(__file__).resolve().parent.parent` | THE RESTORATION RECIPE NAMED NO DEPENDENCY SET, the gap that cost `cf7f8z`'s recipe 13 `NameError`s. Here no hidden helper exists (better than that case), but the deleted file imports FOUR production modules the recovered symbols do not use, so a mechanical carry-everything would make a file this plan declares free of production reads import three production modules, contradicting its own OQ-02 and the srcguard argument E-04 rests on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gained a paragraph with the measured free-variable sets, the exact three-name import set (`re`, `unittest`, `REPO_ROOT` from `tests.support`), and an explicit instruction not to carry the four production imports, with the reason. Expected outcome names the import set. V-04 requires the import block pasted and the four names shown absent. OQ-02's rationale now cites the measurement. Added F-10. |
| PR-705 | LOW | IN-SCOPE | E. Testing (live-artifact criteria) | plan records `3122/3322 tests collected (200 deselected)`; review measured `3237/3442 (205 deselected)` at HEAD `086df9f2`; `cf7f8z`'s review record documents drifts of 60, 138 and 93 in three sibling plans of this same sweep | A TRANSCRIBED COLLECTED TOTAL WAS USED AS AN ACCEPTANCE BAR AND HAD ALREADY DRIFTED 120 TESTS. A collected count is a live population, so per the live-artifact convention the bar must be the PROPERTY with the baseline re-derived at execution time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Step-0 conventions bullet stating the drift and forbidding a transcribed total as a bar. Required tests now demands the baseline be RE-DERIVED on the pre-change tree first, marks review's figures CONTEXT ONLY, and states the bar as the property. V-06 requires both measured figures and forbids comparing against any number written in the plan. Added F-14. |
| PR-706 | LOW | IN-SCOPE | E. Testing and verification | `pyproject.toml` `[tool.pytest.ini_options] addopts` reads `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; the plan's command passes `-m "not slow"`; measured `3242/3442 (200 deselected)` under the plan's marker versus `3237/3442 (205 deselected)` under the real one | THE PRESCRIBED COLLECT COMMAND USES THE WRONG MARKER EXPRESSION, omitting `not livecorpus`, so it collects five more tests than the bare suite and any delta computed with it is wrong before this plan changes anything. The Step-0 bullet also quoted the `addopts` string incorrectly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Step-0 bullet corrected to quote `addopts` verbatim and record both measured collections. Required tests and V-06 now use `-m "not slow and not livecorpus"`. Added F-14. |
| PR-707 | LOW | IN-SCOPE | Step 1 evidence quality | `rg 'docs_check\|docs_render' /tmp/...` exits 1 against a file containing `from agent_workflows import docs_check as dc`, while `rg 'docs_check\|docs_render'` (unescaped alternation) matches it | F-9's EVIDENCE COMMAND CANNOT SUCCEED: the escaped pipe makes it search for a literal string, so it returns nothing whether callers exist or not. The underlying claim is TRUE under the correct pattern, so this is an evidence defect, and it matters because backlog `gzmr54` quotes the same broken command as its own evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9's Evidence cell corrected to the working alternation, with a note recording that both forms were run and that the claim was confirmed under the correct one. |
| PR-708 | LOW | IN-SCOPE | G. Plan executability (internal consistency) | `Proposed changes` item 6 read "File backlog items for the dangling `tests/test_packaging.py` claim..." while E-06 reads `DO NOT CREATE A SECOND PAIR` and `This item's whole deliverable is verification`; `- Scope-Paths:` listed `.aw/records/backlog/open/` although E-06 writes nothing there | TWO INTERNAL CONTRADICTIONS LEFT BY AN AUTHORING-TIME REVISION. The summary line instructs the executor to do exactly what the E-item forbids, and the declared path is the declared-but-unmodified case `aw ipd finalize` refuses to complete without a `--scope-ack` for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Proposed change 6 rewritten to VERIFY, not file, recording the correction. `.aw/records/backlog/open/` removed from `- Scope-Paths:`, with E-06 carrying a note explaining why. Added F-15. |
| PR-709 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | the gate as authored: a strong execution contract and post-gate lifecycle, no scope fence and no approval summary; six prohibitions spread across the Scope statement and five Deferred rows, one of them (`tools/README.md`) a live collision with pending plan `cf7f8z` | THE GATE HAD NO SCOPE FENCE AND NO APPROVAL SUMMARY. The runner had no declaration to reconcile the diff against, and a human approving had no single statement of what changes, what was measured, or which judgement they might want to overrule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a WHAT A HUMAN WOULD BE APPROVING paragraph (the three prose edits and one test file, no production code, the measured `git check-ignore` evidence, and E-02 named as the one severable judgement) and a SCOPE FENCE listing the three paths and all seven negative constraints, written as a DECLARATION with no "STOP and report" clause per the 2026-09-01 maintainer ruling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The root-doc surface decays silently as an allowlist. Should review replace it with a glob, widen it further (e.g. all `*.md` anywhere), or leave it and add a coverage assertion? | GLOB THE ROOT DIRECTORY MINUS A TWO-ENTRY EXCLUSION CONSTANT, and assert the derived surface is non-empty. | (a) Leave the allowlist and add an assertion that all seven files exist - rejected: that pins filenames, so a deliberate rename breaks the guard for the wrong reason and a NEW root doc still goes uncovered, which is half the defect. (b) Widen to every `*.md` in the repository - rejected: that sweeps `.aw/records/` (hundreds of plans and executed records legitimately quoting the retired path, including this very plan), so it would be red on arrival and would pressure a future author into editing records. (c) Keep the allowlist and accept the decay - rejected: the plan exists because a guard decayed. | The rename probe (`scanned=6 offenders=[]` PASS) and the measured equivalence of the two forms today; the exclusion reasoning already in the plan for `DECISIONS.md`/`CHANGELOG.md`; `tools/README.md`'s unreachability by any surface. | yes |
| D-2 | `cf7f8z`'s review recorded a cross-plan ordering obligation resting on `fzueyy` excluding `tools/README.md` by a named reason. Should this review honor it, or remove the need for it? | REMOVE THE NEED. Forbid a `tools/README.md` entry in the exclusion constant, because no surface reaches that file, and record why as F-12. | (a) Keep the entry and its reason, then reconcile whichever plan lands second - rejected: the entry would be INERT (the file is not a root `*.md`, not under `docs/`, not under `.aw/system/workflows/`), so it asserts a fact the structure already provides and buys nothing but a future reconciliation. (b) Widen the guard to cover `tools/` now so the file is genuinely swept - rejected: `cf7f8z` is actively rewriting that file and declares it in its own `- Scope-Paths:`; sweeping a file another pending plan is mid-rewrite invites the collision. Recorded as an accepted under-scope with the note that a later plan may widen once `cf7f8z` lands. (c) Edit `cf7f8z` - rejected: it is not this review's target and it is already `reviewed`. | `tools/README.md`'s path relative to all three surfaces; `cf7f8z`'s E-05 and its review record PR-B02/F-08; `cf7f8z`'s `- Scope-Paths:`. | yes |
| D-3 | E-05 falsified the guard by writing to tracked files in a shared checkout. Should review forbid that outright or merely tighten the revert discipline? | FORBID IT. Require a temporary copy, and require E-04 to make the sweep root-parameterized so the copy is usable. | (a) Tighten the revert (e.g. `try/finally`, or stash) - rejected: `AGENTS.md` explicitly warns that `git stash` in this checkout can discard a co-worker's edit, and a `finally` still leaves a window plus depends on the process surviving. (b) Allow it in a lane worktree only - rejected: the plan cannot know it will execute in one, and the runner's isolation is not something a plan may assume for a deliberate tracked-file mutation. (c) Drop the per-surface red proof and rely on the string-level falsifiability cases - rejected outright: those exercise the regex, not the sweep, so they cannot catch a surface that scans nothing (PR-702's exact hole). | `AGENTS.md`'s shared-checkout and no-stash rules; review's own temp-copy run producing all three reds with `git status` untouched. | yes |
| D-4 | Three findings are HIGH. Does that make this plan NO-GO, or is escalation owed? | NEITHER. All three were FIXED by in-place revision, so no unfixed finding sits at or above the gate threshold, and readiness is `go-pending-approval`. | (a) NO-GO on the HIGHs - rejected: severity is for reporting and the Fix Bar alone decides fixing; each fix is Low Remediation Risk on all four axes (specify a glob, split a counter, copy a tree), touches no production code, and review already ran the resulting design green and red. (b) Escalate as `- Blocking: yes` questions - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the threshold, and none is. (c) REPLAN - rejected: the diagnosis is correct in every particular, the design is the right one, and the defects were all in the guard's SHAPE, which bounded edits fix. | the `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision (exit 0, `findings: 0`); `review_findings_gate` absent from `.aw/config/project.json`, so the default `HIGH` threshold applies and nothing sits unfixed at it. | yes |
| D-5 | Is E-02 (the `committable` correction) over-scope that review should cut, as the plan itself offers? | KEEP IT, and record why, while preserving the plan's own severability note for the human. | (a) Cut it to a backlog item - rejected on measured grounds: D120's entry names FIVE prose defects of exactly this class left behind by the D117 sweep and exists solely to clean them up, so deliberately leaving a sixth beside a path this plan is correcting recreates the defect that decision was created to fix, in the same paragraph. (b) Widen it into a general sweep for stale tracking prose across the root docs - rejected: that is a different plan, and review measured the swept surfaces otherwise clean of the retired path. | D120 read in full in `DECISIONS.md`; the sentence quoted verbatim at review three lines below E-01's first occurrence in the same paragraph; the plan's own severability offer, left standing so the human may still overrule. | yes |
| D-6 | Both open questions carried `Owner: none` while being `resolved`. Should review leave that (the linter accepts it) or correct it? | CORRECT BOTH to `plan author`, and mark them UPHELD at review. | (a) Leave `none` - rejected: `ipd_lint`'s `has_owner` treats `none` as absent and only ENFORCES an owner on a DEFERRED question, so a resolved one passes with `none`; but the workflow rule is that a question resolved on the author's own authority records who chose, and `none` hides that a judgement was made. (b) Write `Owner: maintainer` - rejected as a forged attestation: no maintainer was asked, and the workflow names that exact false label as a measured failure (plan `vtkfq8` OQ-03). | `ipd_lint.py`'s `has_owner` computation and `ipd_schema.open_question_error`, read at review; the `/plan-review` Step 3.1 owner rule. | yes |
| D-7 | The plan's under-scope note says the guard reads no production source. Should review check whether that leaves a real gap in `agent_workflows/`? | MEASURE IT AND RECORD THAT THE GAP IS EMPTY, rather than leaving the limit for a future reader to misread as debt. | (a) Say nothing - rejected: a bare "we exclude production source" invites a later plan to "close the gap" and add exactly the source-pinning test the 2026-09-26 ruling retired. (b) Widen the guard to `agent_workflows/` - rejected: it would report twelve findings on its first run, every one a false positive, and it is the retired test class. | review's count of twelve bare occurrences in `engine.py`, each inspected and found to name the retired path as its subject (`RETIRED_ROOT_ARTIFACTS_DIR`, the migration docstrings, the anchoring comments); the maintainer's 2026-09-26 srcguard ruling as cited by the plan. | yes |
