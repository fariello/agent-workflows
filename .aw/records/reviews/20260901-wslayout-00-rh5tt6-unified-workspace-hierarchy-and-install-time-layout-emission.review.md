# Review: Unified Workspace Hierarchy and Install-Time Layout Emission (Set wslayout, 6 plans)

- Plan-Id: rh5tt6
- Reviewed-At: 2026-09-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

PROCESS CORRECTION, recorded first because it changes how the findings below should be read. This round
initially escalated PR-001 and PR-004 as blocking open questions WITHOUT asking the maintainer, and
issued a final report. That was wrong: plan-review Step 3.2 requires asking interactively, and Step
3.3's non-interactive exception did not apply, because the maintainer was actively answering questions
in this session. The maintainer identified the omission. Both questions were then asked with full
measured context and ANSWERED (see D-1, D-2, and D-5). The two decisions are now the maintainer's, not
deferred; the verdict remains REJECT - NEEDS REPLAN on the remaining findings, which are unaffected by
the answers and none of which is a decision a reviewer may not make.

Reviewed at HEAD `df600461`; all six plans were committed and unchanged before review, so the
pre-review snapshot was correctly skipped. Author-phase `aw ipd lint --phase author --agent` returned
`conforming` (exit 0) for all six: structure, `E-*`/`V-*` bijection, state legality, and metadata are
clean. Every finding below is SEMANTIC, which is exactly the separation the workflow requires; a
passing structural lint clears none of it.

The Set's ambition is legitimate. Layout knowledge IS fragmented across the five modules the spec
names, and a non-Python tool genuinely cannot read the vocabulary today. Order 01 (`wpu5zu`) is
correctly sequenced as pure additive new code, and the decision to refactor consumers only after the
model exists is sound.

The Set is nonetheless not executable as written, for four independent reasons, three of which are
falsified factual premises rather than gaps:

1. The unified vocabulary SILENTLY DROPS two live types (`roadmaps`, `records`) and adds one the
   CLI does not accept (`reviews`). Executing Orders 02 and 03 as written would break a shipped CLI
   surface, and no V-item would catch it, because the plans validate only the tests they name.
2. Three of the six named validation test files DO NOT EXIST, so three V-items cannot be satisfied by
   the command they specify.
3. `aw setup-repo` DOES NOT EXIST as a CLI verb. The spec and two plans treat it as a real install
   entry point; it is a WORKFLOW (`.aw/system/workflows/setup-repo/`).
4. The spec's core justification for install-time emission ("eliminates git drift") is contradicted by
   this repository's own tracked `.aw/system/` tree AND by a maintainer decision recorded the previous
   day in backlog `ila6vl`, which resolved to STOP tracking generated manifests for that exact reason.
   Meanwhile `aw context --json` already emits `logical_roots` + `framework_version` machine-readably,
   which the spec never mentions and which weakens the stated need.

VERDICT REVISED TO `APPROVE WITH REVISIONS APPLIED`. This round FIRST concluded `REJECT - NEEDS REPLAN`.
The maintainer challenged that ("What exactly is required in the rewrite that the current set cannot
address without modification?"), and the challenge was correct: re-measurement showed every one of the
eight findings is a BOUNDED IN-PLACE EDIT, so the workflow's REPLAN bar ("the approach is fundamentally
unsound and cannot be repaired with bounded edits") is not met. The sequence the Set proposes (model
first, consolidate second, emit third, surface fourth) is sound, and the maintainer's UNION ruling makes
the consolidation purely additive rather than a vocabulary redefinition. Every child had room: none held
more than three E-items. All eight in-scope findings are now FIXED in place; see `### Edits applied` and D-6. A ninth finding, PR-009, was discovered while validating and is a defect in the SHARED LIFECYCLE PARSER rather than in these plans, so it stays OPEN with a recommended follow-up.

THE ONE REMAINING GATE IS EXTERNAL TO THE PLANS: `ipd-lifecycle.md:16` requires the controlling SPEC to be
formally approved by the human maintainer before execution may start, and `kw5y2s` is `Status: draft`.
Its factual defects have now been corrected in place (see D-7), but only the maintainer may approve it.
Readiness is therefore NO-GO until that approval, then `GO - PENDING HUMAN APPROVAL` on the plans
themselves.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | D. Anti-regression / A. Correctness | Spec table `kw5y2s:59-73` and emitted doc `:176-237`; real vocabulary `agent_workflows/artifact_types.py:12-23` (`roadmaps` present) and `:26-39`; `agent_workflows/record_producers.py:85-101` (`RECORDS = "records"`, no `backlog`, no `other`); measured diff below | The spec's `record_classes` is presented as the single source of truth but does not match either existing vocabulary. Measured: `ARTIFACT_TYPES` contains `roadmaps`, absent from the spec; `RecordClass` contains `records` (subpath `""`, `record_producers.py:136`), absent from the spec; the spec adds `reviews`, which `ARTIFACT_TYPES` does not accept (`aw check reviews` errors: "unknown artifact type 'reviews'"); the spec adds `backlog`/`other` to the record-class set, which `RecordClass` lacks. `roadmaps` is live in 12 modules including real CLI surfaces (`artifact_rename.py:827-828,855-856` `run_rename_roadmaps`/`run_group_roadmaps`, `artifact_refs.py:215`, `artifact_naming.py:95`, `artifact_core.py:169`) with 5 artifacts on disk including one under `.aw/records/roadmaps/`. Deriving `ARTIFACT_TYPES` from this model (Order 02 E-01) would DELETE a shipped noun and break those commands, and deriving `_RECORD_CLASS_SUBPATHS` (Order 03 E-01) would drop the `records` root-level class. | C:Medium; U:High; S:Low; F:High; Overall:High | FIXED | DECIDED, not yet implemented. Asked the maintainer interactively; answered 2026-09-01: UNION, keep everything including `roadmaps`, add `reviews`/`backlog`/`other` where missing (D-1). OQ-1 in `rh5tt6` updated from blocking to resolved. Still REPLAN because the corrected vocabulary must be written into draft spec `kw5y2s` and the child decomposition rebuilt around it, including the `records` carve-out and the net-new `aw check reviews` behavior. |
| PR-002 | BLOCKER | UNDER-SCOPE | E. Testing and verification | `zvk796:69,84` (`tests/test_awcmdsurf_vocab_and_parsers.py`, `tests/test_selector_resolver_matrix.py`); `rodj06:69,84,89` (`tests/test_record_producers.py`, `tests/test_project_context.py`); `hauwqh:68,83,88` (`tests/test_engine_install.py`, `tests/test_setup_repo_cli.py`); existence measured below | Three of six named validation test files do not exist: `tests/test_record_producers.py`, `tests/test_engine_install.py`, `tests/test_setup_repo_cli.py`. `rodj06` V-01 and `hauwqh` V-01/V-02 therefore specify a command that cannot pass as written, so an executor either invents a file the plan never scoped or reports a false pass. `hauwqh` E-02 says "Add test assertions in" those two files, which reads as editing existing files rather than creating them, and its `Scope-Paths` lists them as if extant. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | NOT FIXED. Belongs in the replan: each V-item must either name an existing file (measured) or explicitly require CREATING it, with the creation named as an E-item deliverable. Not repaired in place because the correct target files depend on the PR-001 vocabulary decision. |
| PR-003 | HIGH | IN-SCOPE | G. Plan executability | `kw5y2s:317` ("During `engine.install(target_repo, ...)` and `aw setup-repo`"), `:333`, `:346`; `hauwqh:6,24,39` and `Scope-Paths:7`; `30jug9` V-02; invocation form `.aw/system/workflows/index.md:108,121` and `agent_workflows/engine.py:3597` | CORRECTED 2026-09-01 (maintainer): the spelling is `/aw setup-repo` (or the alias `/setup-repo`), an AGENT SLASH-COMMAND, not `aw setup-repo`. My original wording conflated the two, though the underlying defect stands and is in fact sharper: `setup-repo` is a WORKFLOW BODY an agent reads and executes (`.aw/system/workflows/setup-repo/setup-repo.md`, shim `.opencode/commands/setup-repo.md`), so it has NO Python call site into which file emission can be wired, and it does not itself install the bundle. The real relationship is the REVERSE of the plans' assumption: `aw install` runs FIRST and then RECOMMENDS `/setup-repo` as a follow-up conformance pass (`engine.py:3581-3597`, "NEXT STEP ... run /setup-repo"). Therefore emission belongs solely in `engine.install()`, and `/setup-repo` inherits it transitively with no work. `hauwqh` E-01's expected outcome and its `tests/test_setup_repo_cli.py` V-item rest on a surface that cannot receive the wiring. `aw update` (`kw5y2s:333`) is likewise not a verb; the idempotent updating entry point is `aw install`. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Wording corrected per the maintainer. Substance unchanged: the replan targets `engine.install()` only, drops `tests/test_setup_repo_cli.py` (see PR-002: it does not exist anyway), and states that `/aw setup-repo` needs no emission code. Whether the WORKFLOW should additionally gain a layout conformance CHECK is a scope question for the replan, not an emission site. |
| PR-004 | HIGH | IN-SCOPE | C. Architecture / F. KISS | Spec rationale `kw5y2s:40-43`; tracked system tree measured below (156 files under `.aw/system/`, including the generated-marker precedent `.aw/system/VERSION`); `git check-ignore .aw/system/layout.json` reports NOT ignored; maintainer decision `.aw/records/backlog/open/20260831-idxtracked-01-ila6vl-...backlog.md:6`; existing machine-readable surface `aw context --json` `data.logical_roots` + `data.effective_framework_version` (`agent_workflows/cli.py` context runner) | Two premises of the install-time-emission design are falsified. (a) "Eliminates git drift": `.aw/system/` is TRACKED here (156 files) and `layout.json` is not gitignored, so emitting into it creates exactly the tracked generated file the rationale says to avoid, in the same tree whose sibling `INDEX.json` churn the maintainer resolved to stop tracking one day earlier in `ila6vl` ("stop tracking the four generated INDEX.json/INDEX.md manifests"). The plans never state whether `layout.json` is tracked or ignored in the target, which is the single most consequential unstated decision in the Set. (b) "Non-Python tools cannot inspect the hierarchy": `aw context --json` already emits all four `logical_roots` as RESOLVED ABSOLUTE paths plus `effective_framework_version`, which is strictly more useful to a shell/Go/Rust caller than the spec's relative strings, and `aw path <root>` prints a single path for scripting. The residual genuine gap is the RECORD-CLASS vocabulary (patterns, lifecycle subdirs, aliases), which is narrower than the Set's framing. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium-High | FIXED | DECIDED, not yet implemented. Asked the maintainer interactively; answered 2026-09-01: GITIGNORED, via the framework-owned `.aw/.gitignore` (never the user's root `.gitignore`), consistent with the `ila6vl` ruling and the spec's own anti-drift rationale (D-2). OQ-2 in `rh5tt6` updated from blocking to resolved. Still REPLAN because the decision must be encoded in the spec and the plans must own its consequence: a fresh clone has no `layout.json` until an install runs, so readers must tolerate absence and the `aw check` presence/version rule becomes required rather than optional. The scope narrowing (versus `aw context --json`) remains in the replan shape. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | Spec `kw5y2s:88-90` vs `agent_workflows/selectors.py` `EXCLUDED_RECORD_DIRS` measured below | The spec's `traversal_exclusions` adds `node_modules`, `venv`, `.venv` to the real set (`.git`, `runs`, `scratch`, `temp`, `tmp`, `.system_generated`, `__pycache__`). The real set is a strict subset, so sourcing `EXCLUDED_RECORD_DIRS` from the model (Order 02 E-02) silently WIDENS traversal exclusion. That is probably desirable but it is a behavior change presented as a pure consolidation, and no V-item asserts the resulting set. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | NOT FIXED (folded into the replan). The widening must be stated as an intentional behavior change with a test asserting the exact resulting set, or the model must emit the current set verbatim. Not fixed in place only because `zvk796` is being replanned wholesale under PR-001. |
| PR-006 | MEDIUM | UNDER-SCOPE | G. Plan executability / D. Anti-regression | `zvk796:34` ("re-exports the layout model definitions seamlessly"), `:41`; `rodj06:34,41`; spec `kw5y2s:335` ("100% backward compatibility") | "100% backward compatibility" is the central safety claim of Orders 02 and 03 and no V-item verifies it as such. Both plans validate only two narrow test files each; neither requires the BARE FULL SUITE, which is the only evidence that a re-export broke no other caller. The repo contract requires a bare `python3 -m pytest` run and pasted output; only the orchestrator (`rh5tt6` V-02) and `30jug9:78` ask for the full suite, so a child could be finalized green while having broken an unnamed consumer. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | NOT FIXED (folded into the replan). Each consolidating child needs a V-item requiring bare `python3 -m pytest` with pasted output, plus an explicit assertion that the public names each module exported before still exist with identical values. |
| PR-007 | MEDIUM | IN-SCOPE | G. Plan executability / B. Sequencing | `Item-Dependencies: none` on all five children (`wpu5zu:8`, `zvk796:8`, `rodj06:8`, `hauwqh:8`, `30jug9:8`) vs the orchestrator's own table `rh5tt6:46-52` (02, 03, 04 depend on 01; 05 depends on 04) and each child's prose (`zvk796:60`, `rodj06:60`, `hauwqh:59`) | The machine-readable dependency field contradicts the human-readable sequence in the orchestrator and in the children's own "deferred" prose. Every child declares no dependency, so a scheduler reading metadata may start Order 02 (which imports `layout.py`) before Order 01 creates it, producing an ImportError-level failure. This is the same defect class the repo already flagged and fixed elsewhere (compare `604wra` PR-002, where prose and metadata disagreed on a dependency). | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | NOT FIXED. Mechanically fixable with `aw ipd dependencies set`, but deliberately left for the replan so the dependency graph is written once against the corrected child decomposition rather than twice. Named explicitly so it cannot be lost. |
| PR-008 | LOW | IN-SCOPE | F. KISS / UX | `30jug9:6,32`; existing verbs `aw migrate-layout` (measured present), `aw context`, `aw path`; `aw layout` measured absent | The proposed verb `aw layout` sits one word away from the existing, unrelated `aw migrate-layout` (a transactional physical-layout MIGRATION), inviting a destructive-sounding confusion in tab completion, and overlaps `aw context`, which already prints the resolved roots. Not a blocker, but the replan should justify a new top-level noun against extending `aw context --layout` or making it a subcommand, per the project's own preference for existing canonical mechanisms. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | NOT FIXED (folded into the replan). Recorded so the naming choice is made deliberately rather than by default. |
| PR-009 | MEDIUM | IN-SCOPE | A. Correctness (TOOLING, not this Set) | `agent_workflows/ipd_lifecycle.py:637-638` ("Inline history is stored newest-first; reverse to oldest-first"); measured event streams below; `check_engine.py:1039-1052`; original authoring commit `7d222547` | `aw check plans` reports `check.lifecycle-transition-invalid` on ALL SIX wslayout plans: "recorded lifecycle transition 'to-review' -> 'draft' is invalid: backwards transition". Investigated rather than assumed, and the plans are NOT at fault. `ipd_lifecycle._plan_status_events` REVERSES the parsed history because it assumes newest-first storage (`:637-638`), so an oldest-first history is inverted and its first transition becomes backwards. Measured: `_plan_status_events` returns `['to-review','draft']` for `rh5tt6`. But oldest-first is the repo's ACTUAL convention: a sampled executed plan (`20260101-instsafe-07-qrokie`) runs 2026-07-23 draft -> 07-25 -> 07-26 executed, i.e. oldest-first, and the wslayout plans match it. Verified PRE-EXISTING by reconstructing the tree at the original authoring commit `7d222547`: all 6 already fired there, before any review edit. Repo-wide there are 9 such diagnostics, 3 on unrelated plans including APPROVED ones (`6knsrx` and `wlxkoz` show `approved -> reviewed`), so this is a systemic parser/convention mismatch, not a wslayout defect. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | NOT FIXED, and deliberately NOT worked around. Reordering these six histories to newest-first would satisfy the parser while CONTRADICTING the convention every other plan follows, and would leave the 3 unrelated plans still failing. This is a defect in `ipd_lifecycle._plan_status_events` (or in the undocumented storage-order contract it asserts) and belongs in its own corrective item, not in a plan-review edit to six unrelated plans. FILED as backlog `tk1gqo`. Non-blocking for this Set: it is a warning-class consistency report on RECORDED EVENTS that runs alongside, and explicitly does not override, the authoritative `- Status:` read (`check_engine.py:1052`). |

#### PR-009 stays OPEN: why it is not fixed here

`aw check plans` reports `check.lifecycle-transition-invalid` on all six plans. It is a TOOLING defect,
not a defect in this Set, and the distinction was established by measurement rather than assumed:

- `ipd_lifecycle._plan_status_events` REVERSES parsed inline history, documenting the assumption
  "Inline history is stored newest-first; reverse to oldest-first for derivation"
  (`ipd_lifecycle.py:637-638`). Measured output for `rh5tt6`: `['to-review', 'draft']`, i.e. inverted.
- The repo's ACTUAL convention is oldest-first. A sampled executed plan
  (`20260101-instsafe-07-qrokie`) runs 2026-07-23 draft -> 07-25 -> 07-26 executed. The wslayout plans
  follow that same order, so they are conformant with practice and non-conformant only with the parser.
- PRE-EXISTING, verified by reconstructing the plans tree at the original authoring commit `7d222547`
  and re-running the check: all 6 already fired there, before any review edit touched them.
- SYSTEMIC: 9 such diagnostics repo-wide, 3 on unrelated plans, including APPROVED ones (`6knsrx` and
  `wlxkoz` report `approved -> reviewed`).

WHY NOT WORK AROUND IT: reordering these six histories to newest-first would silence the warning while
contradicting the convention every other plan follows, and would still leave the 3 unrelated plans
failing. That trades a visible tooling bug for an invisible corpus inconsistency.

WHAT IT NEEDS: a repository-contract decision on which storage order is normative, then either fix the
parser (if oldest-first is normative) or migrate the corpus (if newest-first is). FILED as backlog item `tk1gqo`
(`.aw/records/backlog/open/20260901-historder-01-tk1gqo-lifecycle-history-order-mismatch.backlog.md`), which
carries the measurement, the repro command, the contract question, and the blast radius. Non-blocking for this Set, because the rule validates recorded events ALONGSIDE, and
explicitly does not override, the authoritative `- Status:` read (`check_engine.py:1052`).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the reviewer pick the correct unified record-class vocabulary (e.g. keep `roadmaps`, add `reviews`) and repair the six plans in place? | No. ASKED the maintainer interactively (Step 3.2). ANSWERED 2026-09-01: UNION, keep everything including `roadmaps`, add the missing `reviews`/`backlog`/`other`. | (a) Adopt the spec's list and treat `roadmaps` as deliberately retired; (b) union now but file separate work to retire `roadmaps`; (c) do not unify at all, keeping CLI nouns and storage classes as deliberately different lists. All three were PRESENTED to the maintainer with measured consequences; the maintainer chose the union. Not decided on reviewer authority precisely because it changes a closed public vocabulary. | Live vocabulary `agent_workflows/artifact_types.py:12-23`; `agent_workflows/record_producers.py:85-101,132-139`; `roadmaps` CLI surfaces `agent_workflows/artifact_rename.py:827-828,855-856`; 5 roadmap artifacts on disk incl. `.aw/records/roadmaps/`; `aw check reviews` errors today; spec table `kw5y2s:59-73`; raised with the maintainer and answered 2026-09-01 (maintainer asked interactively, maintainer told the decision) | no |
| D-2 | Should the reviewer decide whether the emitted `.aw/system/layout.json` is git-tracked or gitignored in target repos? | No. ASKED the maintainer interactively (Step 3.2). ANSWERED 2026-09-01: GITIGNORED, via a `.gitignore` INSIDE the `.aw/` directory (not the user's root `.gitignore`). | (a) Tracked, matching the `.aw/system/VERSION` precedent; (b) gitignored plus an `aw check` presence/freshness rule; (c) emit no file at all and expose layout only through the CLI. All presented with measured trade-offs; the maintainer chose gitignored and SPECIFIED the mechanism. Not decided on reviewer authority because the two in-repo precedents point opposite ways and the choice is effectively one-way once target repos depend on it. | Tracked system tree measured (156 files under `.aw/system/`, `git ls-files`); `.aw/system/VERSION` tracked; `git check-ignore .aw/system/layout.json` -> not ignored; maintainer decision `.aw/records/backlog/open/20260831-idxtracked-01-ila6vl-...backlog.md:6`; existing framework-owned `.aw/.gitignore:1-15`; spec rationale `kw5y2s:40-43`; raised with the maintainer and answered 2026-09-01 (maintainer asked interactively, maintainer told the decision) | no |
| D-6 | Is REPLAN the right verdict, or can all eight findings be fixed in place? | FIX IN PLACE. Verdict revised from `REJECT - NEEDS REPLAN` to `APPROVE WITH REVISIONS APPLIED`; all eight applied. | Standing by REPLAN and rewriting the Set. Rejected after the maintainer challenged the verdict and re-measurement falsified my premise: I had reasoned "the spec is wrong, therefore the plans are unsound", but the REPLAN bar is repairability, not spec correctness. Measured: every finding is a bounded edit (reword three V-items, add four E/V items, one metadata command, pin constants), and every child had room at 2-3 E-items with `aw ipd sync` available for pairing. The proposed sequence is sound and the UNION ruling makes consolidation additive. | plan-review Step 2.4 REPLAN criterion ("cannot be repaired with bounded edits"); measured E-item counts (2,2,2,2,3); `aw ipd dependencies set` and `aw ipd sync` availability; maintainer challenge 2026-09-01 | yes |
| D-7 | Should the reviewer edit spec `kw5y2s`, given a spec is a design document the maintainer owns? | Yes, correct its FACTUAL defects in place; do NOT approve it. | Leaving the spec untouched for the maintainer. Rejected on the maintainer's explicit instruction ("Fix all eight in place, then correct spec kw5y2s"), and because leaving it would strand the plans citing a spec whose tables contradict them. The edits are confined to measured facts (vocabulary, exclusions, non-existent verbs) and to transcribing the maintainer's own two rulings; no design choice was invented. `Status` deliberately left `draft`: an agent may not approve a spec, and `ipd-lifecycle.md:16` makes that approval the execution gate. | Maintainer instruction 2026-09-01; `ipd-lifecycle.md:16`; AGENTS.md rule that an agent may not self-approve; `aw specs check` -> all conform after edits | yes |
| D-5 | Was leaving OQ-1/OQ-2 merely escalated, without asking, correct for this run? | No. That was a PROCESS ERROR, corrected in Round 1 by asking both interactively before finalizing. | Leaving them `OPEN` under Step 3.3's non-interactive exception. Rejected because that exception applies only when the environment has "no human interaction channel", which was false here: the maintainer was answering questions throughout the session. Step 3.1's "do not ask what the repository already answers" licenses resolving ANSWERABLE questions from evidence; it does not license deferring a question the reviewer has itself determined requires a maintainer decision. Recorded so the mistake is auditable rather than invisible. | plan-review Step 3.2 (ask 1-3 per prompt, wait before the final report); Step 3.3 (non-interactive definition: "A delayed reply is not non-interactive"); this review's own D-1/D-2 both stating the decision was not a reviewer call | yes |
| D-3 | Is `REPLAN` correct here, rather than fixing the eight findings in place as the workflow's fix-by-default bar prefers? | SUPERSEDED BY D-6. Originally decided "Yes, REPLAN"; that was WRONG and is retained only as the record of the reasoning. See D-6 for the corrected decision (fix in place). | Fix in place, which is what D-6 chose after the maintainer challenged the verdict. The original rejection rested on the premise that a wrong spec makes the plans unsound; the REPLAN bar is actually repairability, and every finding proved to be a bounded edit. | Fix Bar: PR-001 Overall High, PR-004 Overall Medium-High; spec status `kw5y2s:4`; plan-review Step 2.4 REPLAN criterion; SUPERSEDED: see D-6 and the maintainer challenge of 2026-09-01 | yes |
| D-4 | Should the six plans' `Status` be set to `reviewed`? | No. Left at `to-review`, and that answer SURVIVES the D-6 verdict change, for a different reason than originally given. | Set `reviewed` now that the verdict is APPROVE WITH REVISIONS APPLIED. Rejected because the plans are not executable regardless: `ipd-lifecycle.md:16` gates execution on approval of controlling spec `kw5y2s`, which remains `draft`, and advancing to `reviewed` would signal a pipeline position the Set cannot occupy until the maintainer approves that spec. The original rationale (a replan would supersede these files) is obsolete and is superseded by this one. | plan-review Step 4; `ipd-lifecycle.md:16`; spec status `kw5y2s:4` (still `draft`); supersedes the REPLAN-based rationale per D-6 | yes |

### Edits applied (the eight in-scope findings FIXED in place; PR-009 is a tooling defect left OPEN)

- `wpu5zu` E-01: pinned to the UNION vocabulary of eleven record classes with the measured live sets
  cited, an explicit instruction NOT to copy the draft spec's table, the `records` empty-subpath
  carve-out, exact alias reproduction, and exclusions pinned to the current seven. E-02 gained a
  vocabulary-parity regression test (superset of both source vocabularies) and an exclusion-equality
  assertion. V-01 gained a pasteable differential proof (`missing_from_model: []`,
  `roadmaps_present: True`, `excl_equal: True`); V-02 now demands actual runner output.
- `zvk796` E-01: `roadmaps`/`roadmap` declared non-negotiable, and the net-new `aw check reviews`
  behavior made explicit rather than accidental. E-02: exclusions reframed as a deliberate decision with
  two permitted outcomes. V-01 gained the no-narrowing proof plus the BARE FULL SUITE (PR-006); V-02
  gained the exact-set paste and a rule that an unexplained change is a FAILED validation (PR-005).
- `rodj06` E-01: mandatory `records` carve-out, subpath rules for the three new members, and preservation
  of `_LEGACY_RECORD_CLASS_SUBPATHS`. E-02 now also CREATES `tests/test_record_producers.py`. V-01
  corrected to a create-and-verify with a carve-out proof and the bare suite; V-02 gained an enum-member
  preservation proof.
- `hauwqh` E-01: `engine.install()` named the SOLE emission site with the `/aw setup-repo` relationship
  corrected (PR-003), plus determinism and mode. NEW E-02 adds the `.aw/.gitignore` entries per the OQ-2
  ruling, using the existing framework-owned file and never the user's root. NEW E-03 creates
  `tests/test_engine_install.py`; `tests/test_setup_repo_cli.py` dropped from scope. Three V-items with
  pasteable evidence including `git check-ignore -v`, an untouched root `.gitignore`, and idempotency.
  `Scope-Paths` and `Required tests` updated; watermark advanced to 03.
- `30jug9` E-01: naming must be justified before implementing, with the `aw migrate-layout` adjacency and
  the `aw context` overlap stated (PR-008), plus a requirement that the command work with NO emitted file
  (the OQ-2 consequence). E-02: the check rule is now REQUIRED, with three distinguished states so a
  fresh clone does not fail by design. E-03 gained the union-vocabulary CLI fence. V-items demand the
  recorded decision, three check states, the fresh-clone case, `aw check reviews`/`roadmaps` both
  succeeding, and the bare suite.
- All five children: `Item-Dependencies` written via `aw ipd dependencies set` so metadata matches the
  orchestrator's sequence table (PR-007): `zvk796`/`rodj06`/`hauwqh` -> `executed:wpu5zu`, `30jug9` ->
  `executed:hauwqh`.
- `kw5y2s` (spec): Section 3.2 rewritten to the measured union of eleven classes with per-row provenance
  and two stated corrections; NEW Section 3.2.1 for the `records` carve-out; Section 3.4 corrected to the
  seven real exclusions with the removed three named as an undeclared behavior change; NEW Section 2.3
  recording the GITIGNORED ruling, its rationale, and the fresh-clone consequence; NEW Section 2.4 fixing
  the scope boundary against `aw context --json`; the emitted example document corrected (added
  `roadmaps`, fixed exclusions); Sections 5.1, 6.1, 7, and 8 corrected so `engine.install()` is the sole
  emission site and the non-existent verbs are gone. Status left `draft` pending maintainer approval.

### Open-question state (corrected after a maintainer challenge, "No open questions?")

A second maintainer challenge caught three defects in how this review recorded its questions. All are
fixed; the correction is recorded because the original evidence was misleading.

1. `Blocking: resolved` WAS NOT A LEGAL VALUE. `ipd_schema.py:1251` admits only `yes`/`no`
   (`OQ_BLOCKING_VALUES`). The schema carries a SEPARATE `Status:` field (`open`/`resolved`/`deferred`,
   `:1252`) plus a required rationale, which is what should have expressed resolution. The three
   questions are now `Blocking: no` + `Status: resolved` + a full rationale.
2. THE EARLIER "LINT CONFORMING" DID NOT COVER THIS SECTION. `ipd_lint.py:307-311` only ingests an open
   question under an `### OQ-NN:` HEADING; the questions had been written as prose bullets, so
   `check_open_questions` (`:595-615`) received ZERO items and validated nothing. Measured before the
   fix: `len(doc.open_questions) == 0`; after: `== 3`, each with its fields parsed. The clean lint was
   therefore a FALSE NEGATIVE on this section, not evidence of conformance. This is exactly the limit
   the workflow warns about: the linter proves structure only, and a section it cannot see is a section
   it cannot check.
3. OQ-03 WAS STALE AND SELF-CONTRADICTORY. It read "non-blocking, resolve during replan" and described
   PR-003 as outstanding, but there is no replan and PR-003 is fixed. It is now `Status: resolved` with
   the measured entry-point facts and a pointer to where the fix landed.

CURRENT STATE, verified by parsing each plan rather than by reading prose:

| Plan | OQs parsed | State |
|---|---|---|
| `rh5tt6` | 3 | OQ-01/02/03 all `Blocking: no`, `Status: resolved` (the two maintainer rulings plus the entry-point correction) |
| `wpu5zu` | 0 | none; its constraints are E-item requirements, not decisions |
| `zvk796` | 1 | OQ-01 `open`, non-blocking: keep seven traversal exclusions (safe default) or widen to ten as an explicit change (PR-005) |
| `rodj06` | 0 | none |
| `hauwqh` | 0 | none |
| `30jug9` | 1 | OQ-01 `open`, non-blocking: justify a new `aw layout` verb or move it under an existing noun (PR-008) |

The two remaining questions are deliberately `open` and assigned to the EXECUTOR, not to the human: each
has a stated safe default, each is non-blocking because either choice satisfies the spec, and each has a
V-item that FAILS if the choice is made without being recorded. That is the honest state; claiming zero
open questions would have hidden two real decisions inside E-item prose.

### Validation of this review's own edits

- `aw ipd lint --phase review-finalize --agent` -> `clean`, `findings=0` for ALL SIX plans (re-run after
  every edit; three defect classes were caught and fixed mid-edit: an `IPD-I305` `Depends on:` grammar
  break from a parenthetical, `IPD-I303`/`IPD-I304` from adding E-03 before pairing V-03 and advancing
  the watermark, and the open-question format defect described above, which the linter could NOT catch
  because it never parsed the section).
- Open-question parsing verified DIRECTLY, not inferred from a clean lint:
  `python3 -c "...ipd_lint.parse(...).open_questions"` reports 3 / 0 / 1 / 0 / 0 / 1 across
  `rh5tt6`/`wpu5zu`/`zvk796`/`rodj06`/`hauwqh`/`30jug9`, with every field (`Blocking`, `Status`,
  `Finding`, rationale) populated. Before the fix the orchestrator parsed ZERO.
- `aw ipd lint --phase pre-execution` on `rh5tt6` -> `error`, `IPD-S404: status 'to-review' is
  incompatible with checkpoint 'pre-execution'`. This is the CORRECT and desired result: the Set cannot
  execute until the maintainer approves, which is the gate `ipd-lifecycle.md:16` describes.
- `aw specs check` -> `all specs conform`.
- Bare full suite `python3 -m pytest` -> `4004 passed, 3 skipped, 4 xfailed in 40.53s`. No product code
  was touched by this review; this is the untouched-baseline confirmation.
- `aw check-local-leaks --agent` -> `outcome: clean, findings: 0`.

### Minimum shape of the work that remains (was: "of a sound replacement")

Superseded in part: items 2-6 below are now WRITTEN INTO the plans rather than pending a rewrite. Item 1
remains, because only the maintainer can approve a spec.

1. FIX THE SPEC FIRST. `kw5y2s` is `draft`; correct its two vocabulary tables against measured
   reality (`ARTIFACT_TYPES`, `RecordClass`, `EXCLUDED_RECORD_DIRS`), WRITE IN the two maintainer
   decisions below, and drop or retarget every `aw setup-repo` / `aw update` reference. Then seek
   approval. No child plan should execute against a draft spec.

   MAINTAINER DECISIONS TO ENCODE (answered 2026-09-01, see D-1/D-2):
   - VOCABULARY = UNION. Keep every type that exists today, INCLUDING `roadmaps`; add `reviews`,
     `backlog`, and `other` where a module lacks them. The model documents reality; the consolidation
     deletes nothing. `roadmaps` must survive in `ARTIFACT_TYPES` and keep its `aw rename roadmaps` /
     `aw group roadmaps` verbs working. `records` (empty subpath, `record_producers.py:136`) needs an
     explicit carve-out, not an ordinary type entry. `reviews` becoming a CLI noun means `aw check
     reviews` must stop erroring, which is net-new behavior the replan owns and must test.
   - EMITTED FILES ARE GITIGNORED, via the FRAMEWORK-OWNED `.aw/.gitignore`, never the user's root
     `.gitignore`. Add `system/layout.json` and `system/layout.schema.json` (paths relative to `.aw/`).
     That file already exists and already carries this convention for four other generated/box-local
     paths (`.aw/.gitignore:1-15`). Because a fresh clone will then have NO layout.json until an install
     runs, every non-Python reader must tolerate absence, CI reading it needs an install step, and the
     `aw check` presence/version rule (`30jug9` E-02) becomes the loud-failure backstop rather than an
     optional extra.
2. NARROW THE JUSTIFIED SCOPE. `aw context --json` already publishes `logical_roots` and
   `framework_version`. The genuine, unserved gap is the record-class vocabulary (subpath, pattern,
   lifecycle subdirs, aliases) and the state-class map. Scope the emission to what is actually
   missing, and say why the existing surface does not suffice.
3. KEEP ORDER 01's SHAPE. A standalone additive `layout.py` plus `tests/test_layout.py` remains the
   right first step and is the one child that survives this review nearly intact; it only needs its
   constants pinned to the corrected vocabulary.
4. MAKE CONSOLIDATION PROVABLY NON-BREAKING. Each consolidating child asserts, per module, that every
   previously exported public name still exists with an identical value, and validates with a bare
   `python3 -m pytest` plus pasted output, not two narrow files.
5. WRITE THE DEPENDENCY GRAPH ONCE, in metadata, matching the orchestrator table
   (`aw ipd dependencies set`), so no child declares `none` while its prose declares a predecessor.
6. JUSTIFY THE CLI SURFACE against `aw context` / `aw path` before adding a top-level `aw layout`
   adjacent to the existing `aw migrate-layout`.

## Round 2

Scope of THIS round: the ORCHESTRATOR `rh5tt6` only, which is what was requested. The five children were
READ (to verify round 1's fixes actually landed) but were not re-reviewed, so they are not candidates in
this round's ledger and their `Status` is deliberately left untouched. That inconsistency is itself
recorded as an advisory finding in the plan (F-9) with a recommended next step.

Reviewed at HEAD `12159af5`; the plan was committed and unchanged, so the pre-review snapshot was
correctly skipped. Author-phase `aw ipd lint --phase author --agent` returned `conforming` for the
orchestrator and for all five children; `review-finalize` likewise conforming after this round's edits.

THE HEADLINE IS THAT ROUND 1'S ONE REMAINING GATE HAS CLEARED. Round 1 concluded readiness NO-GO for a
single reason external to the plans: `ipd-lifecycle.md:16` forbids executing against an unapproved
controlling spec, and `kw5y2s` was `draft`. Measured this round, that spec is now `- Status: approved`,
approved `--by-human` with the maintainer's verbatim in-session attestation recorded in its workflow
history (commit `6db54f8b`), carrying both maintainer rulings. Readiness therefore moves to
`GO - PENDING HUMAN APPROVAL` on the orchestrator.

ROUND 1'S FIXES WERE VERIFIED RATHER THAN TRUSTED, by re-reading the children and re-measuring the code:

- `Item-Dependencies` now match the sequence table on all five children (PR-007 genuinely fixed).
- `wpu5zu` E-01 carries the union vocabulary, the `records` empty-subpath carve-out, exact alias
  reproduction, and exclusions pinned to seven (PR-001 genuinely fixed).
- `rodj06` E-02 and `hauwqh` E-03 now CREATE the two test files that do not exist, and
  `tests/test_setup_repo_cli.py` is gone from scope (PR-002/PR-003 genuinely fixed). All three files
  confirmed still absent on disk this round, so the CREATE framing is still correct.
- The union claim CHECKS OUT against live code: `ARTIFACT_TYPES` 10 members, `RecordClass` 9, union 12
  names = the eleven modeled classes plus `records` held separately; `_RECORD_CLASS_SUBPATHS[RECORDS]`
  is `""`; `EXCLUDED_RECORD_DIRS` is exactly the seven pinned; aliases include `roadmap -> roadmaps`.
- The Set's premises are still live, so the work is not already done: `aw layout` is an invalid choice
  and `aw check reviews` still errors (`outcome: error, exit 2`).
- PR-009's tooling defect still fires on all six plans (9 repo-wide) and backlog `tk1gqo` is still
  `open`, so it is now written into the execution contract as an EXPECTED diagnostic with an explicit
  instruction not to "fix" it by reordering histories.

What round 1 did not examine, because it was occupied with the children's factual defects, is the
orchestrator's OWN quality. That is where every finding below comes from: it had no execution contract,
two unfalsifiable V-items, a completion criterion contradicting round 1's own correction, vague
cross-IPD checks, and prose-bullet findings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-010 | HIGH | UNDER-SCOPE | G. Plan executability | `rh5tt6` gate section as written (four lines: size, cohesion, nothing else); comparable orchestrator `3m0urk` gate (eight numbered clauses); measured scope collisions below | **The orchestrator had NO execution contract at all.** Its "Approval and execution gate" contained only `Size assessment` and `Cohesion rationale`. The repo contract and the plan-review rubric both require the gate to carry resolved-questions state, a scope fence, the paste-the-actual-output honesty rule, path-scoped commit + never-push, and the lifecycle move; a comparable orchestrator in this repo carries all of it. Separately MEASURED and previously unrecorded: two LIVE concurrent scope collisions. APPROVED plan `e32j35` (Set `findidx`) declares `agent_workflows/selectors.py`, which `zvk796` rewrites; REVIEWED plan `6knsrx` declares `agent_workflows/engine.py`, which `hauwqh` edits and which is itself the lander for a stack of unmerged lane branches. Across pending plans `cli.py` is declared by 13, `engine.py` by 3, and `selectors.py`/`artifact_types.py`/`record_producers.py` by 3 each. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-01. Added a ten-clause execution contract: spec gate cleared, serial execution gated on predecessors reaching `executed`, orchestrator authors no product code, PER-CHILD re-measurement of the measured collisions (not a one-time Set-start check, because the colliding work may land mid-Set), pasted-evidence rule with the false-negative-lint anecdote as its justification, path-scoped commit + shared-checkout staging verification + never-push, primary-checkout validation, a scope fence declaring the delegation and the `--scope-reason`/`--scope-ack` reconciliation without a stop-on-scope directive, the expected `tk1gqo` diagnostic with a do-not-work-around instruction, and the lifecycle transition as a POST-gate step. |
| PR-011 | HIGH | UNDER-SCOPE | E. Testing and verification | `rh5tt6` V-01 and V-02 as written (one line each); child V-items which a child can satisfy alone | **Both orchestrator V-items were unfalsifiable one-liners that could be satisfied without checking anything the children had not already claimed.** V-01 asked only that the five plans "are finalized in executed/ with pre-transition lint passing", which is a directory listing; it never required that each child's own `V-*` items carry NON-EMPTY evidence, so a child moved to `executed/` with blank evidence would pass the orchestrator's gate. V-02 asked for a suite pass and leak check, which every child already does, and never required the ONE behavioral proof the Set exists for and that no child owns: that an install actually emits both files, that they are actually gitignored through the framework-owned file, that the layout surface actually reads them, and that everything degrades when the file is ABSENT (the fresh-clone case the GITIGNORED ruling creates). | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-01. V-01 now demands, per child, the resolved `executed/` path, the `- Status: executed` line, the `pre-transition` lint result, a confirmation that every child `V-*` carries non-empty evidence with `Result: pass`, and a re-check that `Item-Dependencies` still agree with the sequence table at completion time. V-02 now demands the complete bare suite summary with the baseline RE-MEASURED at execution time (round 1's `4004 passed` explicitly marked historical), `aw check` showing no NEW diagnostic class with the six `tk1gqo` reports named as expected, `aw sanitize` clean, and the full end-to-end temporary-repo proof (install -> emitted -> `git check-ignore -v` via `.aw/.gitignore` with root untouched -> surface reads it -> graceful absence). E-02 gained the matching action. |
| PR-012 | MEDIUM | IN-SCOPE | A. Correctness | `rh5tt6` completion criteria as written ("`engine.install()` and `aw setup-repo` bake ...") vs round 1 PR-003's own correction | **A completion criterion still asserted the falsified premise round 1 had already corrected elsewhere in the same Set.** Round 1 established that `aw setup-repo` is NOT a CLI verb but an agent slash-command backed by a workflow body with no Python call site, and fixed `hauwqh` accordingly, but the orchestrator's completion criteria still named it as a baking site. An executor reading the orchestrator's definition of done would look for emission in a surface that cannot receive it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. The criterion now names `engine.install()` as the SOLE emission site and restates the correction explicitly (slash-command, workflow body, inherits transitively, no code of its own), so the contradiction cannot be re-derived from this file. The gitignored-via-framework-file criterion and the absent-file behavior criterion were added alongside, since both are consequences of the maintainer's ruling that nothing in the completion criteria captured. |
| PR-013 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `rh5tt6` cross-IPD validation as written (four bullets, no assertions, no baselines) | **The cross-IPD section named topics rather than checks**, e.g. "Maintain single layout vocabulary imported by all downstream modules" with nothing to compare against and no threshold. Since this section is precisely where a cross-child regression (Orders 02 and 03 combining to narrow the vocabulary) would be caught, topic-shaped bullets leave the Set's central anti-regression claim unverifiable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Rewritten as five falsifiable cross-cutting assertions, each with the measured round-2 baseline to beat: vocabulary-did-not-narrow (with the 10/9/12 counts and the `roadmaps` verb requirement), emitted-matches-model in a temporary repo, combined backward compatibility across the whole suite rather than per child, the net-new `aw check reviews` behavior with `aw check roadmaps` as the no-regression control, and the fresh-clone absence case. |
| PR-014 | LOW | IN-SCOPE | G. Plan executability | `rh5tt6` Findings section as written (a single prose bullet); template shape used by every other reviewed plan in this repo | **The Findings section was one prose bullet with no evidence citations**, so nothing in the orchestrator recorded what had been measured or where to re-check it, and round 1's substantial verification work was recoverable only from the review record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-01. Converted to the standard `Id / Finding / Evidence` table with nine rows: the sound decomposition (F-1), the cleared spec gate (F-2), verified round-1 fixes (F-3), the re-measured union vocabulary (F-4), the still-live premises (F-5), the expected `tk1gqo` diagnostic (F-6), the missing execution contract (F-7), the measured scope collisions (F-8), and the children's stale `to-review` status as an advisory (F-9). Project conventions and Scope check were also filled in with the measured facts an executor needs. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-8 | Round 1 held all six plans at `to-review` because the controlling spec was `draft`. That spec is now approved. Should this round advance the plans' `Status`? | Advance the ORCHESTRATOR to `reviewed` (it was reviewed this round); leave the five CHILDREN at `to-review` and record the inconsistency as advisory finding F-9 with a recommended next step. | (a) Advance all six on round 1's recorded authority, rejected because this round's ledger was the orchestrator alone and setting `reviewed` on five plans I did not re-review would overstate the review performed, which is exactly the kind of unearned pipeline signal `reviewed` is supposed to mean something against. (b) Leave all six at `to-review`, rejected because the orchestrator WAS reviewed this round and holding it back would misreport that. (c) Silently leave the children and say nothing, rejected because the Set's plans then disagree about their own pipeline position with no record of why. | Round 1 record D-4 (the hold and its stated reason); spec now `approved` at `...kw5y2s...spec.md:4`; plan-review Step 4 (`reviewed` means the review occurred); this round's stated scope | yes |
| D-9 | Round 1 left PR-009 (`check.lifecycle-transition-invalid`) OPEN as a tooling defect. Should round 2 revisit it, now that execution is imminent? | Keep it OPEN and unfixed, but WRITE IT INTO the execution contract as an expected diagnostic with an explicit do-not-work-around instruction. | (a) Reorder the six histories to newest-first to silence it, rejected for round 1's reason, re-verified this round: it still fires on 3 unrelated plans including approved ones (9 repo-wide), so the workaround would trade a visible tooling bug for an invisible corpus inconsistency and would not even clear the check. (b) Escalate it to blocking, rejected because the rule reports on recorded events alongside, and explicitly does not override, the authoritative `- Status:` read. (c) Leave it purely in the review record, rejected because the executor reads the plan, not the review, and would reasonably treat a red check as their own regression. | `aw check plans --agent` re-measured this round (9 diagnostics, 3 non-wslayout); backlog `tk1gqo` still `open`; `check_engine.py:1052` | yes |
| D-10 | Should the orchestrator's V-02 require the end-to-end install-and-read proof, given that `hauwqh` already tests emission and `30jug9` already tests the surface? | Yes. Require it at the orchestrator. | Rely on the children's own tests, rejected because each child proves its own unit in isolation while the Set's actual deliverable is the COMPOSITION (install emits -> file is ignored -> surface reads it -> absence degrades gracefully), and no child observes that chain. This is the same reasoning that makes the combined-suite check belong here rather than in Orders 02 and 03. | Child scopes (`hauwqh` E-01/E-03, `30jug9` E-01/E-02); the GITIGNORED ruling's fresh-clone consequence recorded in spec Section 2.3; plan-review rubric on cross-IPD validation | yes |

### Edits applied (round 2)

- `rh5tt6` gate: added the cleared-spec-gate statement and a ten-clause execution contract (PR-010).
- `rh5tt6` V-01 / V-02: rewritten as falsifiable, evidence-demanding items including the end-to-end
  behavioral proof and the non-empty-child-evidence check (PR-011); E-01 and E-02 gained the matching
  actions and the per-child collision re-measurement.
- `rh5tt6` completion criteria: `engine.install()` named the sole emission site with the `aw setup-repo`
  correction restated; gitignored-via-framework-file and absent-file behavior added (PR-012).
- `rh5tt6` cross-IPD validation: four vague bullets -> five falsifiable assertions with measured
  baselines (PR-013).
- `rh5tt6` Findings: prose bullet -> nine-row evidence table (PR-014), including advisory F-9 on the
  children's stale status.
- `rh5tt6` Project conventions, Scope check, Required tests, Spec/documentation sync: filled in with the
  measured facts, the CREATE-not-edit test files, the collision record, the re-measure-the-baseline
  instruction, and a do-not-edit-the-approved-spec rule.
- `Status`: `to-review` -> `reviewed` via `aw ipd set` (orchestrator only; see D-8).

### Validation of this review's own edits (round 2)

- `aw ipd lint --phase author --agent` -> `clean` for the orchestrator and all five children, before edits.
- `aw ipd lint --phase review-finalize --agent` -> `clean`, `findings=0` for the orchestrator after every
  edit, including after the F-9 insertion.
- Round 1's fixes verified by direct measurement, not by reading the round 1 record: `Item-Dependencies`
  across the Set, the union vocabulary imported live (10 / 9 / 12 with the `records` carve-out at
  `_RECORD_CLASS_SUBPATHS[RECORDS] == ""`), `EXCLUDED_RECORD_DIRS` == the seven pinned, aliases including
  `roadmap`/`misc`/`others`, and the three named test files confirmed still absent.
- Set premises re-verified live: `aw layout` -> invalid choice; `aw check reviews` -> `outcome: error, exit 2`.
- Scope collisions measured by `grep -l` over pending plans with each plan's `- Status:` read.
- `aw check plans --agent` -> the six wslayout `check.lifecycle-transition-invalid` diagnostics reproduce,
  plus 3 on unrelated plans (9 total), confirming PR-009 is still systemic and still not this Set's defect.
- `aw sanitize --agent` -> `outcome: clean, findings: 0`.
- No product code was touched by this round; no suite run is claimed.

## Round 3

Scope of THIS round: the CHILD `wpu5zu` (Order 01) alone, which is what was requested. This is the first
of the five children to be re-reviewed after round 2 flagged (F-9) that they were still `to-review` on an
expired rationale. The other four remain `to-review`; that advisory stands for them.

Reviewed at HEAD `90434d47`; the plan was committed and unchanged, so the pre-review snapshot was
correctly skipped. `aw ipd lint --phase author --agent` returned `conforming` before edits and
`--phase review-finalize` `conforming` after.

WHAT ROUND 1 GOT RIGHT, re-verified live rather than trusted: the union-vocabulary pinning in E-01 is
accurate (`ARTIFACT_TYPES` 10 members, `RecordClass` 9, union 12 = the eleven modeled classes plus
`records`), `_RECORD_CLASS_SUBPATHS['records'] == ''` confirms the carve-out, `EXCLUDED_RECORD_DIRS` is
exactly the seven pinned, and `_ALIASES` carries `roadmap -> roadmaps` and `misc`/`others -> other`. The
additive-first shape remains the right first step. The external spec gate is now cleared.

WHAT ROUND 1 DID NOT EXAMINE, and where every finding below comes from: whether this plan actually
delivers the INTERFACE its three dependent children import. Round 1 was occupied with the vocabulary
question and validated E-01 against the vocabulary alone. Order 01 is the foundation of the Set, so the
dangerous failure here is not a bug in `layout.py` but an interface that looks complete, validates green,
and then fails in Order 02 or 03 at import time, or worse, silently changes directory traversal.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-015 | HIGH | UNDER-SCOPE | C. Architecture / G. Plan executability | `selectors.KNOWN_PRIMARY_TYPES` measured (9 members); `record_producers.DurableStateClass` (5) and `RuntimeStateClass` (6) measured; `record_producers._LEGACY_RECORD_CLASS_SUBPATHS` measured; consumer requirements at `zvk796:53` and `rodj06:36`; spec Section 5 `LayoutModel` fields | **E-01's promised surface is INCOMPLETE for its own consumers, and the gap fails in a LATER child rather than here.** E-01 named `RecordClassDefinition`, `LayoutModel`, `build_default_layout`, `to_dict`, `to_json`, `to_schema`, `get_record_subpath`, `is_known_type`, `normalize_type` and the record-class vocabulary. But `zvk796` E-02 sources `KNOWN_PRIMARY_TYPES` from `layout.py`, and that is a DISTINCT, NARROWER set than the union: measured 9 members, exactly `ARTIFACT_TYPES` minus `other`, so a model carrying only the eleven-name union cannot reproduce it without an explicit rule. `rodj06` E-01 sources `DurableStateClass`/`RuntimeStateClass`, whose live values (`install, history, actions, migrations, routing_receipts` and `transactions, locks, staging, backups, cache, tmp`) E-01 never mentions even though the spec's own `LayoutModel` declares `durable_state_classes`/`runtime_state_classes`. `rodj06` must also preserve `_LEGACY_RECORD_CLASS_SUBPATHS` (three `docs/`-prefixed entries), which means one class can have two subpaths, a shape E-01 did not provide for. Each omission validates green in this plan and surfaces downstream. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. E-01 gained an explicit CONSUMER-INTERFACE block enumerating each item with its measured live value and naming the child that imports it: the primary-type set (or a documented derivation such as an `is_primary` flag), both state-class vocabularies member-for-member, the legacy multi-subpath requirement, and the `RootClass` six-vs-four warning from spec Section 5.1 item 4. E-02 must ASSERT the whole surface and V-01 must PASTE it, including which representation was chosen, since Order 02 consumes exactly that. F-4 records it. |
| PR-016 | HIGH | IN-SCOPE | A. Correctness | `selectors.record_dirs` `if record_type == "other"` branch; measured `record_dirs(repo, "other")` -> `['.aw/records/reviews', '.aw/records/prompt-library']`; `ls -d .aw/records/*/` shows no `other/`; `pyproject.toml:12`; spec `:358-372`; house pattern `attention_contract.py:38,41` | **Two distinct correctness traps, both of which would have been coded wrong from the plan as written.** (a) `other` NEEDS A SECOND CARVE-OUT and the plan named only the `records` one. `record_dirs` does not look up a subpath for `other`; it computes the COMPLEMENT of `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` over the records root, plus a literal `other/` if one exists. Measured, it returns `reviews` and `prompt-library`, and no `.aw/records/other/` directory exists at all. Modeling `other` as `subpath: "other"` would look correct, pass a naive test, and silently change what Order 02's traversal finds. (b) THE SPEC SNIPPET IS NOT 3.9-VALID while `requires-python = ">=3.9"`: its dataclass fields are annotated `tuple[str, ...]`/`dict[str, str]`, which are evaluated at class-creation time and fail on 3.9 without `from __future__ import annotations`. The plan told the executor to implement that snippet. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-01. E-01 now models `other` explicitly as a computed/complement class with the measured output cited and a "never `subpath: other`" instruction, and pins the 3.9 floor with the three-module house pattern (`from __future__ import annotations` + `typing` generics), stating the spec snippet is a SHAPE not copyable source. E-02 must assert `other` is representable without a literal subpath and must run under 3.9 semantics; V-01 requires the import block as pasted evidence. F-5 and F-6 record both. |
| PR-017 | MEDIUM | IN-SCOPE | C. Architecture / supply chain | `pyproject.toml:50` (`dependencies = ["filelock>=3"]`) and `:68` (`test = ["pytest>=8", "pytest-xdist>=3", "pytest-randomly>=3"]`); zero `import jsonschema` matches under `agent_workflows/` or `tests/`; `jsonschema` 4.26.0 importable on this machine; `pyproject.toml` `filelock` comment ("An accidental transitive install is not a dependency"); D138 | **E-02 proposed an UNDECLARED dependency.** It named "JSON schema validation using `jsonschema` (or stdlib schema checker)". `jsonschema` imports fine here at 4.26.0 but is declared in neither the runtime deps nor the `[test]` extra, and nothing in the package or the suite imports it today. Taking it would make a clean `pip install '.[test]'` and CI run different code than the maintainer, which is precisely the reproducibility hole `pyproject.toml`'s own `filelock` comment was written to close. D138 permits a JUSTIFIED dependency, so this is not a prohibition; the defect is the "or" leaving an undeclared import as an acceptable outcome. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | FIXED 2026-09-01. E-02 now states the DECLARE-OR-DO-NOT-IMPORT rule with the measured evidence, defaults to stdlib structural validation (asserting the emitted document's required keys, types and enums against the emitted schema, which is in-scope), and permits the dependency route ONLY if `jsonschema` is added to the `[test]` extra in the same change. Scope check records that route as requiring `pyproject.toml` in `Scope-Paths`; V-02 requires either a grep proving no `import jsonschema` or the declaring diff, and calls an undeclared import a FAILED validation. F-7 records it. |
| PR-018 | LOW | UNDER-SCOPE | G. Plan executability | Gate section as written (2 lines); Findings as written (1 prose bullet); `Project conventions`, `Scope check`, `Required tests`, `Open questions` as written | **The plan carried no execution contract and four placeholder sections.** The gate held only `Size assessment` and `Cohesion rationale`; `Required tests` was the single line `pytest tests/test_layout.py` (not the bare-suite form the repo contract requires); `Scope check` was "none/none"; `Open questions` was "- none." with nothing recorded; `Findings` was one uncited sentence. Same class as PR-010 on the orchestrator. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Added a nine-clause execution contract naming the foundation risk explicitly (an interface that looks finished), the additive-only rule, the two correctness traps, the declare-or-do-not-import rule, the honesty rule, shared-checkout path-scoped commits, primary-checkout validation, a scope fence with the conditional `pyproject.toml` path, the expected `tk1gqo` diagnostic, and the post-gate lifecycle step. Findings converted to a seven-row evidence table; conventions, scope check, required tests (bare suite + re-measured baseline) and spec sync filled in; `Open questions` now records that round 2 resolved three decisions from evidence rather than leaving a bare "none". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-11 | `KNOWN_PRIMARY_TYPES` is a 9-member set that differs from the 11-name union by more than one rule. Should the model expose it as its own constant, or derive it? | Require the model to expose it OR expose a documented derivation rule (e.g. a per-class `is_primary` flag), and require V-01 to state WHICH was chosen. Do not let the consumer re-hardcode it. | (a) Mandate a specific representation now, rejected because either is defensible and the executor holds the implementation context; what matters is that the choice is explicit and asserted. (b) Leave it to Order 02 to hardcode, rejected because that recreates the duplication the whole Set exists to remove, in the very module being consolidated. | Measured `selectors.KNOWN_PRIMARY_TYPES` (9) vs `ARTIFACT_TYPES` (10), differing exactly by `other`; `zvk796:53` sources it from `layout.py`; spec Section 5.1 item 3 | yes |
| D-12 | How should `other` be modeled, given it has no directory and is computed? | As a computed/complement class, explicitly NOT `subpath: "other"`, with the complement rule stated in E-01 and asserted in E-02. | (a) Model it as an ordinary class with `subpath: "other"`, rejected because measured behavior is a complement over the records root (`reviews` + `prompt-library` today) and no `other/` directory exists, so this would silently narrow traversal in Order 02 while passing a naive test. (b) Exclude `other` from the model, rejected because it is a live `ARTIFACT_TYPES` member with `misc`/`others` aliases and the maintainer's UNION ruling keeps everything. | `selectors.record_dirs` complement branch; measured `record_dirs(repo,'other')`; `ls -d .aw/records/*/`; maintainer UNION ruling (round 1 D-1) | yes |
| D-13 | Should E-02's schema validation be allowed to use `jsonschema`? | Default to stdlib structural validation; permit `jsonschema` only if DECLARED in the `[test]` extra in the same change, with `pyproject.toml` added to `Scope-Paths`. | (a) Forbid the dependency outright, rejected because D138 explicitly clarifies that dependency minimization is a principle and not a prohibition, so a blanket ban would misstate the repo's own decision. (b) Allow the undeclared import since it works here, rejected because `pyproject.toml`'s `filelock` comment names exactly this failure ("An accidental transitive install is not a dependency") and it would desync CI from the maintainer. | `pyproject.toml:50,68`; zero in-repo `import jsonschema`; D138; the `filelock` declaration rationale | yes |

### Edits applied (round 3, `wpu5zu` only)

- E-01: added the CONSUMER-INTERFACE block (primary types, both state-class vocabularies, legacy
  multi-subpath, `RootClass` six-vs-four), the `other` complement carve-out, and the Python 3.9 pinning
  with the house annotation pattern (PR-015, PR-016).
- E-02: declare-or-do-not-import rule for `jsonschema` with the stdlib default; consumer-surface
  assertions; concrete byte-equality determinism assertion; 3.9 constraint (PR-015, PR-016, PR-017).
- V-01: added the consumer-interface proof and the 3.9 import-block proof, with an honesty clause for the
  case where no 3.9 interpreter is available (PR-015, PR-016).
- V-02: bare-suite form with re-measured baseline, the dependency evidence (grep or declaring diff), and
  the determinism paste (PR-017).
- Gate: nine-clause execution contract naming the foundation risk (PR-018).
- Findings: prose bullet -> seven-row evidence table; `Project conventions`, `Scope check`,
  `Required tests`, `Spec / documentation sync`, `Open questions` filled in (PR-018).
- `Status`: `to-review` -> `reviewed` via `aw ipd set`.

### Validation of this review's own edits (round 3)

- `aw ipd lint --phase author --agent` -> `clean` before edits; `--phase review-finalize --agent` ->
  `clean`, `findings=0` after.
- Round 1's vocabulary claims re-measured live: `ARTIFACT_TYPES` 10, `RecordClass` 9, union 12,
  `_RECORD_CLASS_SUBPATHS['records'] == ''`, `EXCLUDED_RECORD_DIRS` == the seven pinned, `_ALIASES`
  containing `roadmap`/`misc`/`others`.
- New findings measured, not inferred: `KNOWN_PRIMARY_TYPES` 9 members differing from `ARTIFACT_TYPES` by
  `other`; `DurableStateClass` 5 and `RuntimeStateClass` 6 members enumerated; `_LEGACY_RECORD_CLASS_SUBPATHS`
  three `docs/`-prefixed entries; `record_dirs(repo,'other')` -> `['.aw/records/reviews',
  '.aw/records/prompt-library']` with no `other/` directory; `jsonschema` importable at 4.26.0 with zero
  in-repo imports and no declaration; `requires-python = ">=3.9"` against the spec's `tuple[...]` snippet.
- `aw sanitize --agent` -> `outcome: clean, findings: 0`.
- No product code was touched by this round; no suite run is claimed.

## Round 4

Scope of THIS round: the FULL SET `wslayout` (all six plans: orchestrator `rh5tt6` and children `wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`), as requested by `/aw plan-review-long wslayout`.

Reviewed at HEAD `754dd6f1`; all six plans were committed and unchanged before review, so the pre-review snapshot was correctly skipped. `aw ipd lint --phase author --agent` returned `conforming` for all six before edits, and `--phase review-finalize --agent` returned `conforming` for all six after edits.

ALL FIVE CHILDREN ARE NOW HARDENED AND AT `Status: reviewed`, resolving orchestrator advisory finding F-9. All six plans now carry the mandatory structured `- Readiness: go-pending-approval` machine-readable front-matter field. There are ZERO blocking open questions remaining across the entire Set (all open questions were previously answered and encoded, or resolved by the maintainer).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-019 | HIGH | UNDER-SCOPE | G. Plan executability | `zvk796:135`, `rodj06:130`, `hauwqh:161`, `30jug9:173` gates as written (two lines each); `wpu5zu` and `rh5tt6` gates | **Four child plans had NO execution contract in their Approval and execution gate.** Their gates contained only `Size assessment` and `Cohesion rationale`, omitting the cleared spec gate, prerequisite plan execution, scope fence, honesty rule (paste actual runner output), shared-checkout staging verification (`git diff --cached --name-only`), path-scoped commit, never-push, primary-checkout validation, expected `tk1gqo` diagnostic instruction, and lifecycle transition as a post-gate step. Live concurrent scope collisions (`selectors.py` declared by approved plan `e32j35`, `engine.py` declared by reviewed plan `6knsrx`, `cli.py` declared by 13 pending plans) were unrecorded in their gates. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-04. Added complete eleven-clause execution contracts to all four child plans with per-child prerequisites, collision warnings, honesty rules, staging verification, and lifecycle post-gate steps. |
| PR-020 | HIGH | UNDER-SCOPE | E. Testing and verification | `rodj06:7,60,107-110` | **Plan 03 (`rodj06`) omitted `tests/test_record_producers.py` from its `Scope-Paths`.** E-02 and V-01 explicitly require creating and verifying this new file, but `Scope-Paths` listed only `agent_workflows/record_producers.py, agent_workflows/project_schema.py`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Added `tests/test_record_producers.py` to `Scope-Paths` and `Scope check` in `rodj06`. |
| PR-021 | MEDIUM | IN-SCOPE | A. Correctness | `hauwqh:6,30,36,41,127`, `rh5tt6:69,92`; `agent_workflows/engine.py:5420` | **Plan 04 (`hauwqh`) and orchestrator `rh5tt6` named `engine.install()` as the emission function.** The actual function in `agent_workflows/engine.py` is `engine.install_into_repo()` (lines 5420-5560). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Corrected function name to `engine.install_into_repo()` across `hauwqh` and `rh5tt6`. |
| PR-022 | LOW | UNDER-SCOPE | G. Plan executability | `zvk796:73`, `rodj06:74`, `hauwqh:89`, `30jug9:95` | **Plans 02, 03, 04, 05 had single prose-bullet Findings sections without evidence citations or structured tables.** Also carried minimal placeholder sections for conventions, scope check, and required tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-04. Converted Findings to structured `Id / Finding / Evidence` tables with measured repository citations, and filled in conventions, scope checks, and bare-suite test requirements with baseline re-measurement. |
| PR-023 | LOW | IN-SCOPE | G. Plan executability / Lifecycle | All 6 plans front-matter; `rh5tt6` F-9 advisory | **All six plans lacked the mandatory structured `- Readiness:` machine-readable front-matter field.** Orchestrator `rh5tt6` advisory finding F-9 flagged the children as `Status: to-review` on an expired rationale; with this review, all four remaining children advance to `Status: reviewed`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-04. Added `- Readiness: go-pending-approval` to all six plans, advanced Plans 02, 03, 04, 05 from `to-review` to `reviewed`, and updated F-9 in `rh5tt6` to resolved. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-14 | Should the four remaining child plans (`zvk796`, `rodj06`, `hauwqh`, `30jug9`) be advanced to `Status: reviewed` and assigned `Readiness: go-pending-approval`? | Advance all four to `Status: reviewed` and assign `Readiness: go-pending-approval` across all six plans. | (a) Leave children at `to-review`, rejected because all four were thoroughly reviewed, hardened, and verified clean with `aw ipd lint --phase review-finalize` in this round. (b) Advance without structured readiness, rejected because the workflow contract mandates `- Readiness: <go \| go-pending-approval \| no-go>` in front-matter. | Plan-review Step 2 & 3; `rh5tt6` F-9 advisory; `aw ipd lint` clean across Set | yes |
| D-15 | Should `tests/test_record_producers.py` be added to `Scope-Paths` in `rodj06`? | Yes. Add to `Scope-Paths` and `Scope check`. | Omit from `Scope-Paths` and require `--scope-reason` during finalization. Rejected because the plan explicitly creates the file in E-02 and verifies it in V-01, so omitting it from `Scope-Paths` was an authoring oversight. | `rodj06` E-02 / V-01 text; PR-002 resolution in round 1 | yes |
| D-16 | What is the exact function name in `agent_workflows/engine.py` for repository installation? | `engine.install_into_repo`. Update references in `hauwqh` and `rh5tt6`. | Retain `engine.install()`, rejected because no such function exists in `engine.py` (`cli.py:4226` and tests invoke `engine.install_into_repo`). | `agent_workflows/engine.py:5420`; `cli.py:4226` | yes |
| D-17 | What execution contract should be added to the four child plans? | Standard eleven-clause execution contract matching `wpu5zu` and `rh5tt6`: cleared spec gate, serial prerequisites, concurrent scope collision checks, invariant preservation, honesty rule (actual pasted runner output), shared-checkout staging verification, primary-checkout validation, scope fence, expected `tk1gqo` diagnostic, and post-gate lifecycle finalization. | Leave minimal gates, rejected because the repository execution contract and review rubric require the gate to carry these essential safeguards. | Plan-review rubric Section A; `wpu5zu:232-243`; `rh5tt6:238-251` | yes |

### Edits applied (round 4, all 6 plans)

- `rh5tt6`: Added `- Readiness: go-pending-approval`; updated Workflow history; updated `engine.install()` references to `engine.install_into_repo()` in completion criteria and conventions; resolved F-9 advisory in Findings (PR-021, PR-023).
- `wpu5zu`: Added `- Readiness: go-pending-approval`; updated Workflow history (PR-023).
- `zvk796`: Advanced `Status: to-review` -> `reviewed`; added `- Readiness: go-pending-approval`; updated Workflow history; added 11-clause execution contract with `e32j35` collision check; converted Findings to 6-row evidence table; expanded conventions, scope check, and bare-suite testing (PR-019, PR-022, PR-023).
- `rodj06`: Advanced `Status: to-review` -> `reviewed`; added `- Readiness: go-pending-approval`; added `tests/test_record_producers.py` to `Scope-Paths` and `Scope check`; updated Workflow history; added 12-clause execution contract; converted Findings to 5-row evidence table; expanded conventions and bare-suite testing (PR-019, PR-020, PR-022, PR-023).
- `hauwqh`: Advanced `Status: to-review` -> `reviewed`; added `- Readiness: go-pending-approval`; corrected `engine.install()` to `engine.install_into_repo()` in Goal, Scope, E-01, V-01, and conventions; updated Workflow history; added 12-clause execution contract with `6knsrx` collision check; converted Findings to 5-row evidence table; expanded conventions, scope check, and bare-suite testing (PR-019, PR-021, PR-022, PR-023).
- `30jug9`: Advanced `Status: to-review` -> `reviewed`; added `- Readiness: go-pending-approval`; recorded maintainer resolution on OQ-01 in E-01; updated Workflow history; added 12-clause execution contract with 13-plan `cli.py` collision check; converted Findings to 5-row evidence table; expanded conventions, scope check, and bare-suite testing (PR-019, PR-022, PR-023).

### Validation of this review's own edits (round 4)

- `aw ipd lint --phase review-finalize --agent` -> `clean`, `findings=0` across ALL SIX plans.
- All six plans carry valid `- Readiness: go-pending-approval` front-matter fields.
- Open questions parsed cleanly: `rh5tt6` (3 resolved), `wpu5zu` (0), `zvk796` (1 resolved), `rodj06` (0), `hauwqh` (0), `30jug9` (1 resolved). Zero blocking open questions remaining.
- `aw specs check` -> all specs conform.
- `aw check-local-leaks --agent` -> `outcome: clean, findings: 0`.
- No product code was touched by this round; no suite run is claimed.

## Round 5

Scope of THIS round: the ORCHESTRATOR `rh5tt6` ALONE, which is what the invocation named. The five
children were NOT candidates and are NOT reviewed here; they remain `Status: to-review` /
`Readiness: no-go` from the round-4 demotion. Round 5 did edit one paragraph in each child (the stale
reopened-spec-gate claim, PR-024), because plan-review Step 2.4 requires fixing a cross-plan finding in
the owning plan; correcting a false paragraph is NOT a review and did not promote any child. That
consequence is now recorded as `rh5tt6` F-13.

Reviewed at HEAD `cf7dceea`. All six plans were committed and unchanged before review, so the pre-review
snapshot was correctly SKIPPED. `aw ipd lint --phase author --agent` returned `clean` for all six before
edits, and `--phase review-finalize --agent` returned `clean` for `rh5tt6` after edits (the five children
were re-linted at `--phase author` and remain `clean`).

THE HEADLINE: THE ROUND-4 SPEC GATE REOPENING IS STALE, IN THE PLANS' FAVOUR. Round 4 demoted all six
plans to `to-review`/`no-go` because the maintainer-directed installer/layout-API terminology correction
had returned spec `kw5y2s` to `to-review`. That correction was then reviewed and RE-APPROVED `--by-human`
459 seconds LATER (demotion `298be4b2` at 00:10:38 -0400, re-approval `3e05c2ba` at 00:18:17 -0400), so
every one of the six plans has since been carrying a gate paragraph whose premise had already expired.
This is the SECOND time this Set has carried a spec-gate statement that was true when written and false
when read (round 2 found the mirror-image case). The durable fix is not another correction but the
re-verify-at-execution-time instruction now in the gate.

WHAT ROUND 4 CLAIMED AND ROUND 5 FOUND UNTRUE, verified by re-reading code rather than the record. Round 4
PR-021 stated the `engine.install()` -> `engine.install_into_repo()` correction was applied "across
`hauwqh` and `rh5tt6`"; it had in fact been missed in `rh5tt6` OQ-03 (PR-028). Round 4 also asserted the
orchestrator's `Scope-Paths` is the children's union; it was not (PR-025). Both are the same failure mode
the earlier rounds kept naming and then repeating: trusting a prior round's resolution text.

THE TWO SUBSTANTIVE CORRECTNESS FINDINGS are PR-026 and PR-027, and neither was reachable from the plan
text alone; both required reading `engine.py` and running a real install into a temporary repo.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-024 | HIGH | IN-SCOPE | G. Plan executability / Lifecycle | `.aw/records/specs/20260901-kw5y2s-...spec.md:4` (`- Status: approved`) + its `2026-09-04 approved (aw set, --by-human)` history line; `git log` `298be4b2` (1788495038) vs `3e05c2ba` (1788495497); the "REOPENED" paragraph in all six plans; `aw specs check --agent` -> `clean, checked: 26` | **All six plans asserted the controlling spec was `to-review` and that execution was blocked, which is FALSE.** The spec was re-approved `--by-human` 459 seconds AFTER the plans were demoted, so the demotion text outlived its premise. Left alone, a correct executor reading `ipd-lifecycle.md:16` would refuse to start a Set that is in fact spec-cleared, and a careless one would "discover" the contradiction and be tempted to self-approve. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Rewrote the gate paragraph in `rh5tt6` and in all five children to state the gate is CLEARED with the timeline that made the old claim stale, plus a standing instruction to RE-VERIFY the spec's `- Status:` at execution time instead of trusting the paragraph (the defect has now occurred twice, in both directions). `rh5tt6` F-2, `wpu5zu` F-3 and the four children's spec-sync bullets updated to match. Readiness `no-go` -> `go-pending-approval` for the orchestrator. |
| PR-025 | HIGH | UNDER-SCOPE | G. Plan executability / scope fence | Set-difference of the children's `- Scope-Paths:` against `rh5tt6:7`; `hauwqh:7` (`.aw/.gitignore`); `30jug9:7` (`command_surface.py`, `doctor.py`); `rh5tt6` `Scope check` ("`Scope-Paths` is the UNION of what the children edit") | **The orchestrator's `Scope-Paths` was NOT the union it claims to be.** Three child-declared paths were missing: `.aw/.gitignore` (`hauwqh` E-02), `agent_workflows/command_surface.py` and `agent_workflows/doctor.py` (both `30jug9`). The plan's own `Scope check` asserts the union property, so the declaration contradicted the plan, and `aw ipd finalize`'s scope reconciliation would have demanded a `--scope-reason` for legitimate, planned child edits. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Added the three paths to `Scope-Paths` and verified programmatically that EVERY child-declared path is now covered by this plan's declaration (the four new test files are covered by the `tests/` entry). Recorded as F-10 and in `Scope check`. |
| PR-026 | HIGH | IN-SCOPE | A. Correctness / C. Architecture | `agent_workflows/engine.py:5420-5576` (`install_into_repo`), `:5656` (`run`); `cli.py:5639-5757` (`_run_setup`), `:4202-4314` (`_install_one`), `:4226`; `hauwqh` E-01 as written; direct `install_into_repo` call into a temporary repo at round 5 | **The Set treated "sole emission site" as "sole install path", and there are TWO CLI install paths.** `install_into_repo` is a CHOKEPOINT with three callers: `engine.run()` (`aw install`), `cli._install_one` (`aw setup`, the machine-wide first-run wizard, a REAL verb distinct from both `aw install` and the `/setup-repo` slash-command), and direct library use. The plans discussed only `aw install` and the slash-command. An executor wiring emission into `engine.run()` would satisfy every stated test while leaving `aw setup` silently emitting nothing, and the resulting workspace would have no `layout.json` for any non-Python tool. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-04. `hauwqh` E-01 gained an explicit PUT-THE-CALL-INSIDE-`install_into_repo` instruction with all three callers cited and measured; `hauwqh` V-01 now demands the diff hunk proving placement plus emission demonstrated through the SECOND path (`aw setup`/`_install_one`), and calls a caller-level wiring a FAILED validation. `rh5tt6` completion criteria, conventions, OQ-03 and V-02 updated; recorded as `rh5tt6` F-11 and `hauwqh` F-1. |
| PR-027 | HIGH | IN-SCOPE | A. Correctness | `engine.py:4208-4222` (`_AW_GITIGNORE_TEMPLATE`), `:5236-5261` (`_ensure_aw_gitignore` + its `additions` back-fill and the `records/history.jsonl` regression comment at `:5254-5257`), `:2576` (`ensure_backups_gitignored`), `:2698-2735` (`ensure_untracked_gitignore`), `:5506-5507` (both called from `install_into_repo`); temporary-repo install at round 5; template-vs-installed-file diff | **Two false premises about gitignoring, one of which would have produced a no-op change and one an impossible validation.** (a) A target's `.aw/.gitignore` is GENERATED from a template and back-filled by an explicit `additions` list, NOT copied; editing this repo's checked-in `.aw/.gitignore` (the only artifact `hauwqh` E-02 named) changes NOTHING for any target repo, while still passing a naive "the file contains the line" test. The back-fill list is also where a previous lane was already missed once, per the `records/history.jsonl` comment in the code. (b) Five places demanded evidence the user's ROOT `.gitignore` is "untouched", but `install_into_repo` legitimately writes an untracked-safety `aw:block` AND the installer-backups line into it; verified in a temporary repo. That validation would fail on correctly-working code, and V-02 specifically demanded `git diff -- .gitignore` show no change. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-04. `hauwqh` E-02 now names BOTH edit sites (template for fresh installs, `additions` for already-installed repos) with the measured mechanism cited, and states the root-`.gitignore` rule precisely as "never add a LAYOUT entry" with the installer's real root-file writes enumerated. `hauwqh` V-02 replaced the no-diff assertion with `grep -n layout .gitignore` returning no match plus `check-ignore` attribution, and now requires idempotency proof on BOTH generation paths (fresh AND back-fill), the latter being the case a template-only edit silently fails. `rh5tt6` completion criteria, conventions, E-02, V-02 and `hauwqh` F-2 updated. |
| PR-028 | MEDIUM | IN-SCOPE | A. Correctness | `rh5tt6` OQ-03 as written (`engine.install()`); `agent_workflows/engine.py:5420` (`install_into_repo`, the only such function); round-4 PR-021 resolution text claiming the fix was applied "across `hauwqh` and `rh5tt6`" | **A non-existent function name survived in `rh5tt6` OQ-03 after round 4 recorded it as corrected.** No `engine.install` exists. The resolution paragraph a reader consults to learn WHICH function receives the emission wiring named the wrong one, which is the same defect round 4 raised as PR-021 and reported fixed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. OQ-03 now reads `engine.install_into_repo()` with the `engine.py:5420-5576` citation and an explicit note that round 4 missed this occurrence. Also corrected the `engine.py:3581-3597` citation repeated across the Set: the `/setup-repo` recommendation is at `:3598-3613` inside `print_summary` (`:3515-3613`), and `:3581` lands on the staging notice above it. |
| PR-029 | MEDIUM | IN-SCOPE | E. Testing and verification | `aw check plans --agent` at round 5 (16 `check.lifecycle-transition-invalid`, 14 on this Set) vs the "six"/"9 repo-wide" figures in `rh5tt6` completion criteria, F-6, contract clause 9 and V-02; `e32j35`/`6knsrx` both resolving under `plans/superseded/`; round-5 scan finding `2r306y` (approved) on `selectors.py` and 7 non-wslayout pending plans on `cli.py`; `record_dirs(repo,'other')` -> `['.aw/records/prompt-library']` vs the round-2 pair; commit `d802e917`; HEAD citation `12159af5` | **Every quantitative baseline in the plan had drifted, and two of them would cause a FALSE validation failure or a wrong test expectation.** (a) The expected `check.lifecycle-transition-invalid` count is now 16 (14 on this Set), not six, and it RISES with every appended history line, so a count-based assertion fails for a reason unrelated to the work. (b) The named collision plans are both superseded; the live overlaps are different plans. (c) `record_dirs(repo,'other')` no longer returns the reviews path, because `d802e917` added `NON_PRIMARY_RECORD_DIRS` to stop exactly that; a test pinning the round-2 pair would fail against correct code. (d) The HEAD cited for the vocabulary measurement is stale. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Converted every count assertion to a CLASS assertion with a self-measured baseline requirement (completion criteria, F-6, clause 10, `Required tests`, V-02), re-measured and replaced the collision set (F-8, clause 5, `Scope check`, E-01), re-measured the `other` complement in `rh5tt6` Cross-IPD validation and `wpu5zu` F-5 with an explicit warning not to reuse the old pair as an expected result, and refreshed the HEAD citation in F-4/F-5. Added a Cross-IPD assertion that `other` still excludes reviews after Orders 02 and 03 BOTH land, which is a combined state no child observes. |
| PR-030 | MEDIUM | UNDER-SCOPE | G. Plan executability | `rh5tt6` contract clause 1 as written; `zvk796:122` and `30jug9:141` (both `- Status: resolved`); absence of any honesty clause in the contract; `rh5tt6` E-01 ("05 declares `executed:hauwqh`") vs `30jug9:8` (`executed:hauwqh,executed:zvk796`); V-01 as written | **Three gate/checklist defects.** (a) Clause 1 described `zvk796` OQ-01 and `30jug9` OQ-01 as "remaining `open` questions ... assigned to the EXECUTOR"; both are `Status: resolved` by maintainer ruling, so the contract invited an executor to re-decide settled questions. (b) The contract carried NO honesty rule, which the plan-review rubric requires explicitly, even though this orchestrator's whole purpose is to catch children that claim completion without evidence. (c) E-01 said Order 05 declares one dependency edge when its metadata declares two, and V-01 asked only that metadata and table "still agree" rather than naming the values. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. Clause 1 rewritten to state ZERO open questions remain Set-wide, verified per plan. Added clause 3, the honesty rule (paste actual runner output, bare suite, no fabricated pass, an honest `pending` over a false claim), and renumbered the contract to 12 sequential clauses with the three internal cross-references repointed. E-01 now pins each child's literal `Item-Dependencies` value and flags the two-edge case; V-01 now demands the literal values pasted plus proof the OBSERVED execution order matched the graph, since metadata declaring an edge is not evidence it was honored. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-18 | The plans say the spec gate is reopened; the spec says `approved`. Which is authoritative, and may this review clear the gate on its own authority? | Treat the SPEC ARTIFACT as authoritative and record the gate as cleared, because clearing it asserts nothing about human approval of the PLANS, which remains separately required and unmet. | (a) Leave the reopened claim and ask the maintainer to re-confirm, rejected because plan-review Step 3 forbids asking what the repository already answers unambiguously: the spec carries `- Status: approved` plus a `--by-human` attestation line, and the git timeline shows exactly why the plan text is stale. (b) Also promote the five children on the same reasoning, rejected as out of scope for this invocation and because their demotion had a second, independent effect (they were returned for re-review), which only a review of each child can discharge. | `.aw/records/specs/...kw5y2s...spec.md:4` and its `approved (aw set, --by-human)` history line; commit timestamps `298be4b2` (00:10:38) vs `3e05c2ba` (00:18:17); `ipd-lifecycle.md:16`; plan-review readiness table (`reviewed` != approved) | yes |
| D-19 | Should `Readiness` be `go-pending-approval` when the orchestrator is clean but its five children are `no-go`? | Yes for THIS plan, and record the Set-level consequence explicitly as F-13. | (a) Keep `no-go` to signal the Set cannot run, rejected because the workflow defines `Readiness` as the reviewed plan's OWN state and reserves `no-go` for a genuine not-ready condition in that plan (open question, unfixed BLOCKER/HIGH, or a non-passing verdict), none of which applies; misusing the field would also make a clean plan invisible to automation that fails closed on it. (b) `go`, rejected because human approval has not happened. | plan-review readiness table and the `Readiness` field contract; the five children's `- Status:`/`- Readiness:` | yes |
| D-20 | `hauwqh` E-02 named only `.aw/.gitignore`. Should the fix name the template, the back-fill list, or both? | BOTH, and say which serves which case (template = fresh install, `additions` = already-installed repo). | (a) Template only, rejected because a repo installed before this change would never gain the entries, which is precisely the regression the `records/history.jsonl` comment at `engine.py:5254-5257` records having already shipped once. (b) Leave it to the executor, rejected because the plan as written pointed at a file whose edit is a no-op for every target, so the likely outcome was a change that validates green and does nothing. | `engine.py:4208-4222`, `:5236-5261`; the template-vs-installed-file diff measured at round 5 | yes |
| D-21 | V-02 demanded the root `.gitignore` show no diff. Weaken it, or drop it? | Re-scope it to "carries no LAYOUT entry", keeping the protection while making it satisfiable. | (a) Drop the root-`.gitignore` check entirely, rejected because the maintainer's OQ-2 ruling is specifically that the framework-owned file is used and the user's root file is not the mechanism, so the check guards a real ruling. (b) Keep the no-diff form, rejected because `install_into_repo` provably writes an `aw:block` and the backups line into that file, so the validation would fail on correct code and train the executor to wave it through. | `engine.py:2576`, `:2698-2735`, `:5506-5507`; temporary-repo install at round 5 showing the root `aw:block` with the pre-existing user line preserved; spec Section 2.3 | yes |
| D-22 | Is `aw setup` in scope to mention, given the Set never names it? | Yes: name it in `hauwqh` E-01/V-01 and in the orchestrator's conventions, without adding it to any `Scope-Paths`. | (a) Say nothing, since wiring the chokepoint happens to cover it, rejected because the plan's own text argues the emission site from the CALLERS it enumerated, and that enumeration was incomplete; an executor could reasonably wire `engine.run()`. (b) Add a separate E-item for `aw setup`, rejected as unnecessary work: no code change is needed there, only the correct placement of one call. | `cli.py:5748`, `:4226`; `engine.py:5656`; verified emission-by-chokepoint with a direct `install_into_repo` call at round 5 | yes |

### Edits applied (round 5)

- `rh5tt6` front matter: `Scope-Paths` +3 paths (PR-025); `Status` `to-review` -> `reviewed`; `Readiness` `no-go` -> `go-pending-approval`.
- `rh5tt6` gate: spec-gate paragraph rewritten with the stale-claim timeline and a re-verify-at-execution instruction (PR-024); clause 1 rewritten (zero open questions, PR-030); NEW clause 3 honesty rule (PR-030); clauses renumbered 1-12 with the three internal cross-references repointed; clauses 5 and 10 re-measured (PR-029).
- `rh5tt6` E-01: literal per-child `Item-Dependencies` pinned, two-edge case for Order 05 flagged, collision examples refreshed (PR-029, PR-030). E-02: root-`.gitignore` wording corrected (PR-027).
- `rh5tt6` V-01: literal dependency values + observed-execution-order proof (PR-030). V-02: split into class-based `aw check`, corrected root-`.gitignore` evidence, both-install-path proof, and the `other`-isolation assertion (PR-026, PR-027, PR-029).
- `rh5tt6` completion criteria: emission-inside-the-chokepoint, generated-gitignore reality, class-not-count `aw check` (PR-026, PR-027, PR-029).
- `rh5tt6` Cross-IPD validation: vocabulary baseline re-measured with a re-measure instruction; `reviews` conditional removed; NEW `other`-complement cross-cutting assertion (PR-029).
- `rh5tt6` conventions: three-caller chokepoint, corrected `:3598-3613` citation, generated-`.aw/.gitignore` mechanism (PR-026, PR-027, PR-028).
- `rh5tt6` OQ-03: `engine.install()` -> `engine.install_into_repo()` + the sole-site-vs-sole-path refinement (PR-026, PR-028).
- `rh5tt6` Findings: F-2, F-3, F-4, F-5, F-6, F-8 re-measured; NEW F-10, F-11, F-12, F-13.
- `hauwqh` (owning plan for the emission findings): E-01 chokepoint-placement instruction; E-02 template + back-fill + precise root-`.gitignore` rule; V-01 shared-chokepoint proof; V-02 corrected root-`.gitignore` evidence and dual-path idempotency; F-1, F-2, F-5 re-measured; `Scope check` and `Required tests` updated (PR-026, PR-027, PR-029).
- `wpu5zu` F-5: `other` complement re-measured with a do-not-reuse-the-old-pair warning (PR-029). F-3 and spec-sync: stale gate claim (PR-024).
- `zvk796`, `rodj06`, `30jug9`: stale spec-gate paragraph and spec-sync bullet corrected (PR-024). No other change; these plans were NOT reviewed this round.

### Validation of this review's own edits (round 5)

- `aw ipd lint --phase author --agent` -> `clean, findings 0` for all six plans BEFORE edits.
- `aw ipd lint --phase review-finalize --agent` -> `clean, exit 0, findings 0` for `rh5tt6` after edits; all five children re-linted `--phase author` -> `clean, exit 0`.
- Vocabulary re-measured live: `ARTIFACT_TYPES` 10, `RecordClass` 9, union 12, `_RECORD_CLASS_SUBPATHS['records'] == ''`, `EXCLUDED_RECORD_DIRS` == the seven pinned, `KNOWN_PRIMARY_TYPES` 9 (= `ARTIFACT_TYPES` minus `other`), aliases `roadmap`/`misc`/`others` intact.
- Set premises re-verified: `python3 -m agent_workflows layout` -> `invalid choice: 'layout'`; `aw check reviews --agent` -> `outcome: error, exit 2`.
- `record_dirs(repo,'other')` -> `['.aw/records/prompt-library']` (round-2's reviews entry is gone; `d802e917`).
- Installer behavior measured in a TEMPORARY repo, not inferred: `aw install` writes an untracked-safety `aw:block` + `.agent-workflows-installer-backups/` into the target's ROOT `.gitignore` while preserving a pre-existing user line; `git check-ignore -v` attributes `.aw/system/layout*.json` to `.aw/.gitignore:15-16` when the entries are added there; a direct `engine.install_into_repo()` call (bypassing `engine.run()`) produces `.aw/.gitignore` and `.aw/system/VERSION`, confirming the chokepoint.
- Scope-Paths union verified programmatically: every child-declared path is now covered by `rh5tt6`'s declaration.
- `aw check plans --agent` -> 16 `check.lifecycle-transition-invalid` (14 on this Set, 2 unrelated) + 4 `check.scope-drift` on an unrelated plan; `aw check --agent` -> 35 findings across six classes, none caused by this Set.
- `aw specs check --agent` -> `clean, checked: 26`. `aw sanitize --agent` -> `clean, findings: 0`.
- No product code was touched by this round; NO suite run is claimed or needed (planning documents only).

## Round 6

Scope of THIS round: the CHILD `wpu5zu` (Order 01) ALONE, which is what the invocation named. The
orchestrator and the other four children were NOT candidates. `wpu5zu` was the only plan edited.

Reviewed at HEAD `e96ebc61`. The plan was committed and unchanged, so the pre-review snapshot was
correctly SKIPPED. `aw ipd lint --phase author --agent` -> `clean` before edits;
`--phase review-finalize --agent` -> `clean` after.

WHY THIS ROUND FOUND ANYTHING AT ALL, given rounds 1-4 had already hardened this plan: every previous
round verified the plan's VOCABULARY claims (which are all accurate, re-verified once more here) but
never EXECUTED the plan's technical assertions. Round 6 ran them. A 3.9 interpreter is present on this
machine, so round 2's central Python-version claim was testable rather than arguable, and it turned out
to be false. The same applies to the exclusion-parity assertion, which is a two-line experiment that
nobody had run.

THE HEADLINE: ROUND 2'S 3.9 RATIONALE IS WRONG, AND ITS CONCLUSION IS RIGHT. Round 2 told the executor
that the spec's `tuple[str, ...]`/`dict[str, str]` dataclass field annotations "are evaluated at
class-creation time and fail on 3.9". Measured on `python3.9` (3.9.25), the spec's exact
`RecordClassDefinition`/`LayoutModel` shape creates its classes, instantiates, and resolves through
`typing.get_type_hints` with no error and no `__future__` import. PEP 585 builtin generics have been legal
since 3.9; the construct that actually raises on 3.9 is PEP 604 (`str | None` ->
`TypeError: unsupported operand type(s) for |`), and the spec snippet contains no union. The
`from __future__ import annotations` + `typing` instruction is nonetheless CORRECT, on the ground that it
is the universal house pattern (132 of 132 modules under `agent_workflows/`) and makes a later `| None`
safe by construction. This matters beyond pedantry: a plan that teaches a false language fact will have
that fact repeated by the next agent that reads it, and an executor who "discovers" the claim is wrong may
reasonably conclude the whole constraint is bogus and drop the house pattern too.

THE SECOND SUBSTANTIVE FINDING WOULD HAVE PRODUCED A FLAKY TEST. Both E-02 and V-01 prescribed
`tuple(model.traversal_exclusions) == tuple(selectors.EXCLUDED_RECORD_DIRS)`. That constant is a
FROZENSET, so the comparison tests hash iteration order; three `PYTHONHASHSEED` values produced three
different orderings. The repository deliberately keeps `pytest-randomly` enabled (it is a DECLARED
dependency precisely because it changes observed behavior), so this would surface as an intermittent
failure that an executor might "fix" by pinning the model to one accidental ordering.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-031 | HIGH | IN-SCOPE | A. Correctness / F. Honest documentation | `python3.9` (3.9.25) executing the spec's exact dataclass shape: class creation, instantiation and `typing.get_type_hints` all succeed with no `__future__` import; PEP 604 `str \| None` raising `TypeError` on the same interpreter; spec snippet `:340-392` containing no `\|` union; `pyproject.toml:12`; `.github/workflows/tests.yml:31,172`; 132/132 `from __future__ import annotations` measured | **Round 2's Python 3.9 rationale is FALSE, and the plan states it three times as established fact** (E-01, conventions, F-6). PEP 585 builtin generics as dataclass field annotations are legal on 3.9; nothing "fails at class creation". The real 3.9 boundary is PEP 604 union syntax, which the spec never uses. Left standing, the plan teaches a wrong language fact that the next reader inherits, and an executor who tests it may discard the (correct) house-pattern instruction along with the (incorrect) reason. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-04. E-01, `Project conventions`, F-6 and contract clause 2 rewritten: the `__future__` + `typing` instruction RETAINED and re-justified on the universal house pattern (132/132) plus future `\| None` safety, with the false class-creation claim replaced by the measured truth and PEP 604 named as the actual hazard. Added that 3.9 is CI-enforced across the matrix, so the floor itself is real. |
| PR-032 | HIGH | IN-SCOPE | E. Testing and verification | `type(selectors.EXCLUDED_RECORD_DIRS).__name__` -> `frozenset`; `PYTHONHASHSEED=1/2/3` yielding three different `tuple(...)` orderings; `pyproject.toml:59-66` (`pytest-randomly` DECLARED because it changes observed behavior) and `:152` (`addopts` never disables it); house precedent `tests/test_selector_resolver_matrix.py:277-285` using set algebra | **The exclusion-parity assertion was specified in a FLAKY form in BOTH E-02 and V-01.** `tuple(m.traversal_exclusions) == tuple(S.EXCLUDED_RECORD_DIRS)` compares frozenset iteration order, which varies by hash seed. It can therefore report a mismatch against a completely correct model, pass locally and fail in CI, or differ across xdist workers. The likely executor response, pinning the model to one observed ordering, would encode hash noise as a contract. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-04. V-01's pasteable command now uses `set(...) == set(...)`, with an explicit note on why the tuple form was wrong. E-02 gained a COMPARE-AS-SETS clause citing the three-seed measurement, the house set-algebra precedent, and the rule that an intentionally ORDERED contract must be asserted against a literal expected sequence rather than a frozenset's incidental order. Contract clause 4 generalizes it to any set-valued parity assertion. F-8 records it. |
| PR-033 | HIGH | UNDER-SCOPE | A. Correctness / E. Testing | `artifact_types.py:50-73` read and executed: `normalize_type('all')` -> `'all'` (explicit special case at `:52-53`), error text advertising `..., other, all` at `:58`, `expand_types('all', ARTIFACT_TYPES)` -> all 10 types; `normalize_type('nosuchtype'/''/None)` -> `ValueError`; `selectors.py:188-195` docstring ("Returns [] for an unknown/unresolvable type rather than raising") | **The plan claims ownership of `normalize_type` while omitting the `all` token entirely, and demanded NO negative-path evidence anywhere.** Two distinct gaps. (a) `all` is a first-class token consumed by every `aw <verb> all` invocation; it is not a record class and must not become one, but a model that silently drops it breaks that surface, and the plan never mentions it. (b) The two live helpers this model replaces DISAGREE on error handling (`normalize_type` raises, `record_dirs` degrades), and the plan required no unknown-type, empty-string, or `None` behavior at all, so an executor could unify them either way and land a behavior change in Order 02 with every stated validation green. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | FIXED 2026-09-04. E-01 gained an explicit `all`-token clause requiring a RECORDED decision on which side of the model boundary it sits (either representation is defensible; silence is not). V-01 gained a NEGATIVE-PATH proof requiring pasted behavior for unknown/`''`/`None` plus the `records` carve-out, with the two live contracts spelled out per helper and an instruction not to unify them silently. Contract clause 5 added. F-9 records it. |
| PR-034 | MEDIUM | UNDER-SCOPE | G. Plan executability (right-sizing) | `Cohesion rationale: not required` as written; `aw ipd lint` thresholds (>18 E-leaves, >5 groups) vs this plan's 2 E-items in 2 groups; E-01 carrying 6 `MUST` clauses over 54 lines | **Right-sizing was never assessed, only inherited from a count-based lint that cannot measure conceptual density.** The rubric requires the judgement explicitly and warns that a passing size lint does NOT clear it. E-01 names one file but carries six MUST clauses spanning vocabulary, two carve-outs, aliases, exclusions, annotation style and a consumer surface, which is exactly the shape that prompts a split question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-04. Replaced `not required` with a real cohesion rationale: the answer is NO SPLIT, because the six clauses are constraints on ONE pair of dataclasses that must hold together, and any split would leave `layout.py` importable-but-incomplete, which is the precise foundation failure this plan's own gate warns about. Recorded the trigger that WOULD change the answer (a `to_schema()` needing bespoke per-class logic becomes its own E-item). |
| PR-035 | MEDIUM | IN-SCOPE | C. Architecture / supply chain | `.github/workflows/tests.yml:58` (`pip install --upgrade pip build pytest pytest-xdist`), `:31,172` (matrix includes 3.9); `python3 -c "import jsonschema"` -> 4.26.0 vs `python3.9 -c "import jsonschema"` -> `ModuleNotFoundError` | **PR-017's dependency risk is understated: it is a CERTAIN CI failure, and the sanctioned escape route is insufficient.** CI never installs the `[test]` extra, only `pytest`/`pytest-xdist`, so ANY undeclared third-party test import fails outright rather than merely diverging from a maintainer venv. Worse, the plan's permitted alternative (declare `jsonschema` in `[test]`) would STILL leave it absent on the CI runner, so that route silently requires a skip guard or a workflow change the plan never scoped. Confirmed concretely: `jsonschema` is missing on `python3.9`, a matrix version. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | FIXED 2026-09-04. E-02's dependency clause, `Project conventions`, `Scope check` and contract clause 3 now carry the CI-install fact, the 3.9 absence measurement, and the consequence that the declare-it route needs a skip guard or workflow change (a further scope expansion). The stdlib route is now "strongly preferred", not merely "the default". F-10 records it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-23 | Round 2's 3.9 rationale is false but its instruction is sound. Drop the instruction, or keep it with a corrected reason? | KEEP the `__future__` + `typing` instruction, REPLACE the reason, and name PEP 604 as the real hazard. | (a) Drop the instruction as unnecessary, rejected because it is the universal house pattern (132/132 modules) and consistency in a brand-new core module has independent value, plus it makes a future `\| None` safe automatically. (b) Leave the false reason in place because the outcome is the same, rejected because a plan that asserts a wrong language fact propagates it to every later reader, and an executor who tests the claim may discard the correct instruction with the incorrect justification. | `python3.9` 3.9.25 executing the spec's exact shape successfully; PEP 604 failing on the same interpreter; 132/132 measurement; `.github/workflows/tests.yml:31,172` | yes |
| D-24 | How should the model-vs-live exclusion parity be asserted, given the live constant is a frozenset? | As SETS (`set(...) == set(...)`, or `sorted(...) == sorted(...)`), with an explicit carve-out that a deliberately ORDERED model contract must be asserted against a literal expected sequence. | (a) Keep the tuple comparison, rejected as measurably flaky (three seeds, three orderings) under a suite that deliberately randomizes. (b) Make the model expose a sorted tuple so the tuple comparison becomes stable, rejected because it invents a contract the consumer (`zvk796`) never asked for and hides the real issue: the LIVE side is unordered, so no comparison against its iteration order is ever meaningful. | `type(EXCLUDED_RECORD_DIRS)` -> `frozenset`; three-seed measurement; `tests/test_selector_resolver_matrix.py:277-285`; `pyproject.toml:59-66,152` | yes |
| D-25 | The `all` token and the two divergent error contracts are unspecified. Decide them here, or require the executor to record a choice? | REQUIRE A RECORDED CHOICE, enforced by V-01, rather than mandating one representation. | (a) Mandate that the model owns `all`, rejected because `all` is an argument-parsing concern rather than a layout fact and forcing it into the layout model may be the wrong architecture; the executor holds the implementation context. (b) Mandate that the model raises everywhere for consistency, rejected because `record_dirs`'s degrade-to-`[]` behavior is DOCUMENTED and depended upon, so a blanket rule would silently change Order 02. (c) Leave both unstated, rejected because that is the status quo that allows a green-validating behavior change. | `artifact_types.py:50-73` executed; `selectors.py:188-195`; the round-3 precedent (D-11) of requiring a recorded choice rather than dictating a representation | yes |

### Edits applied (round 6, `wpu5zu` only)

- E-01: corrected 3.9 rationale with the measured evidence and PEP 604 as the real hazard (PR-031); alias map verified exact (12 entries); NEW `all`-token clause requiring a recorded decision (PR-033).
- E-02: NEW compare-as-sets clause with the three-seed measurement and house precedent (PR-032); dependency clause strengthened with the CI-install fact and the 3.9 absence, making the declare-it route explicitly insufficient on its own (PR-035).
- V-01: pasteable command switched from `tuple(...)` to `set(...)` with the reason (PR-032); 3.9 proof now requires an ACTUAL `python3.9` run and the round-2 escape clause removed as an unnecessary loophole (PR-031); NEW negative-path proof with the two live error contracts stated per helper and the `all` boundary (PR-033).
- Gate: `Cohesion rationale` replaced with a real right-sizing assessment plus the trigger that would change it (PR-034); contract clauses 2 and 3 corrected, NEW clauses 4 and 5, renumbered to 11 sequential clauses (PR-031..PR-033, PR-035).
- `Project conventions`: 3.9 reality, CI-installs-only-pytest fact, PEP 604 hazard (PR-031, PR-035).
- `Scope check`: the `jsonschema` route's true cost (PR-035).
- `Required tests`: stale "six diagnostics" -> CLASS assertion with the re-measured 16 repo-wide / 3 on this plan.
- Findings: F-2 re-verified with a current HEAD citation and more constants; F-6 rewritten as a correction; NEW F-8, F-9, F-10.
- Removed a self-contradicting leftover sentence in the gate ("This plan is returned to `to-review`"), introduced by round 5's edit.
- `Status` `to-review` -> `reviewed`; `Readiness` `no-go` -> `go-pending-approval`.

### Validation of this review's own edits (round 6)

- `aw ipd lint --phase author --agent` -> `clean, findings 0` BEFORE edits; `--phase review-finalize --agent` -> `clean, exit 0, findings 0` AFTER.
- Python 3.9 claims EXECUTED, not argued: `python3.9` is 3.9.25; the spec's exact frozen-dataclass shape with `tuple[str, ...]`/`dict[str, str]` fields creates, instantiates and `get_type_hints`-resolves cleanly with NO `__future__` import; `str | None` raises `TypeError` on the same interpreter; `import agent_workflows` succeeds on 3.9.
- Frozenset ordering MEASURED across `PYTHONHASHSEED=1,2,3` -> three distinct `tuple()` orderings.
- Live helper behavior EXECUTED: `normalize_type('nosuchtype'/''/None)` -> `ValueError` with the valid-type list; `normalize_type('all')` -> `'all'`; `normalize_type('roadmap')` -> `'roadmaps'`; `expand_types('all', ARTIFACT_TYPES)` -> all 10 types in order.
- Vocabulary re-verified: `ARTIFACT_TYPES` 10, `RecordClass` 9, union 12, `_RECORD_CLASS_SUBPATHS['records'] == ''`, `EXCLUDED_RECORD_DIRS` the seven pinned, `KNOWN_PRIMARY_TYPES` 9 == `ARTIFACT_TYPES` minus `other` (asserted programmatically), durable 5, runtime 6, `LogicalRoot` 4, `RootClass` 6, legacy map's three `docs/` entries.
- Every `path:line` citation in the plan opened and confirmed: `pyproject.toml:12,50,68`; `artifact_types.py:12-23,26-39`; `record_producers.py:85-101,136,148-152`; `project_schema.py:46-62`; `attention_contract.py:38,41`; `worktree_lease.py:24,32`; `artifact_core.py:21,30`; D138 at `DECISIONS.md:2449`.
- `.github/workflows/tests.yml` read: matrix `["3.9".."3.14"]` at `:31,172`; install line at `:58` is `pip install --upgrade pip build pytest pytest-xdist` (no `[test]` extra).
- `tests/test_layout.py` confirmed still ABSENT, so E-02 remains a CREATE.
- `aw check plans --agent` -> 16 `check.lifecycle-transition-invalid` repo-wide, 3 on this plan.
- `aw sanitize --agent` -> `clean, findings: 0`.
- No product code was touched by this round; NO suite run is claimed (planning documents only).
