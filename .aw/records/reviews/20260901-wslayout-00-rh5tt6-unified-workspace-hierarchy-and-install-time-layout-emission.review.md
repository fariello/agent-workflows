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
more than three E-items. All eight findings are now FIXED in place; see `### Edits applied` and D-6.

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

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the reviewer pick the correct unified record-class vocabulary (e.g. keep `roadmaps`, add `reviews`) and repair the six plans in place? | No. ASKED the maintainer interactively (Step 3.2). ANSWERED 2026-09-01: UNION, keep everything including `roadmaps`, add the missing `reviews`/`backlog`/`other`. | (a) Adopt the spec's list and treat `roadmaps` as deliberately retired; (b) union now but file separate work to retire `roadmaps`; (c) do not unify at all, keeping CLI nouns and storage classes as deliberately different lists. All three were PRESENTED to the maintainer with measured consequences; the maintainer chose the union. Not decided on reviewer authority precisely because it changes a closed public vocabulary. | Live vocabulary `agent_workflows/artifact_types.py:12-23`; `agent_workflows/record_producers.py:85-101,132-139`; `roadmaps` CLI surfaces `agent_workflows/artifact_rename.py:827-828,855-856`; 5 roadmap artifacts on disk incl. `.aw/records/roadmaps/`; `aw check reviews` errors today; spec table `kw5y2s:59-73`; maintainer answered interactively 2026-09-01 | no (escalated and answered, not self-resolved) |
| D-2 | Should the reviewer decide whether the emitted `.aw/system/layout.json` is git-tracked or gitignored in target repos? | No. ASKED the maintainer interactively (Step 3.2). ANSWERED 2026-09-01: GITIGNORED, via a `.gitignore` INSIDE the `.aw/` directory (not the user's root `.gitignore`). | (a) Tracked, matching the `.aw/system/VERSION` precedent; (b) gitignored plus an `aw check` presence/freshness rule; (c) emit no file at all and expose layout only through the CLI. All presented with measured trade-offs; the maintainer chose gitignored and SPECIFIED the mechanism. Not decided on reviewer authority because the two in-repo precedents point opposite ways and the choice is effectively one-way once target repos depend on it. | Tracked system tree measured (156 files under `.aw/system/`, `git ls-files`); `.aw/system/VERSION` tracked; `git check-ignore .aw/system/layout.json` -> not ignored; maintainer decision `.aw/records/backlog/open/20260831-idxtracked-01-ila6vl-...backlog.md:6`; existing framework-owned `.aw/.gitignore:1-15`; spec rationale `kw5y2s:40-43`; maintainer answered interactively 2026-09-01 | no (escalated and answered, not self-resolved) |
| D-6 | Is REPLAN the right verdict, or can all eight findings be fixed in place? | FIX IN PLACE. Verdict revised from `REJECT - NEEDS REPLAN` to `APPROVE WITH REVISIONS APPLIED`; all eight applied. | Standing by REPLAN and rewriting the Set. Rejected after the maintainer challenged the verdict and re-measurement falsified my premise: I had reasoned "the spec is wrong, therefore the plans are unsound", but the REPLAN bar is repairability, not spec correctness. Measured: every finding is a bounded edit (reword three V-items, add four E/V items, one metadata command, pin constants), and every child had room at 2-3 E-items with `aw ipd sync` available for pairing. The proposed sequence is sound and the UNION ruling makes consolidation additive. | plan-review Step 2.4 REPLAN criterion ("cannot be repaired with bounded edits"); measured E-item counts (2,2,2,2,3); `aw ipd dependencies set` and `aw ipd sync` availability; maintainer challenge 2026-09-01 | yes |
| D-7 | Should the reviewer edit spec `kw5y2s`, given a spec is a design document the maintainer owns? | Yes, correct its FACTUAL defects in place; do NOT approve it. | Leaving the spec untouched for the maintainer. Rejected on the maintainer's explicit instruction ("Fix all eight in place, then correct spec kw5y2s"), and because leaving it would strand the plans citing a spec whose tables contradict them. The edits are confined to measured facts (vocabulary, exclusions, non-existent verbs) and to transcribing the maintainer's own two rulings; no design choice was invented. `Status` deliberately left `draft`: an agent may not approve a spec, and `ipd-lifecycle.md:16` makes that approval the execution gate. | Maintainer instruction 2026-09-01; `ipd-lifecycle.md:16`; AGENTS.md rule that an agent may not self-approve; `aw specs check` -> all conform after edits | yes |
| D-5 | Was leaving OQ-1/OQ-2 merely escalated, without asking, correct for this run? | No. That was a PROCESS ERROR, corrected in Round 1 by asking both interactively before finalizing. | Leaving them `OPEN` under Step 3.3's non-interactive exception. Rejected because that exception applies only when the environment has "no human interaction channel", which was false here: the maintainer was answering questions throughout the session. Step 3.1's "do not ask what the repository already answers" licenses resolving ANSWERABLE questions from evidence; it does not license deferring a question the reviewer has itself determined requires a maintainer decision. Recorded so the mistake is auditable rather than invisible. | plan-review Step 3.2 (ask 1-3 per prompt, wait before the final report); Step 3.3 (non-interactive definition: "A delayed reply is not non-interactive"); this review's own D-1/D-2 both stating the decision was not a reviewer call | yes |
| D-3 | Is `REPLAN` correct here, rather than fixing the eight findings in place as the workflow's fix-by-default bar prefers? | Yes, REPLAN. | Fix in place: repair vocabulary, correct the test-file names, retarget `setup-repo` to `engine.install`, and add the missing full-suite V-items. Rejected because the falsified premises live in spec `kw5y2s`, which is still `Status: draft` and therefore unapproved: repairing only the plans would leave six plans implementing an unapproved spec whose vocabulary tables and central rationale are themselves wrong, and PR-001/PR-004 need maintainer decisions no reviewer edit can supply. | Fix Bar: PR-001 Overall High, PR-004 Overall Medium-High, both above the Medium-High deferral threshold; spec status `kw5y2s:4`; plan-review Step 2.4 REPLAN criterion | yes |
| D-4 | Should the six plans' `Status` be set to `reviewed`? | No. Left at `to-review`. | Set `reviewed` because the review did occur. Rejected: the workflow directs a `REJECT - NEEDS REPLAN` outcome toward replanning rather than advancing readiness, and the corrected decomposition will supersede these files, so marking them `reviewed` would imply a pipeline position they should not hold. Recorded here so the choice is visible rather than an omission. | plan-review Step 4 (`Status: reviewed` unless the contract requires another value); verdict definition REJECT - NEEDS REPLAN | yes |

### Edits applied (all eight findings FIXED in place)

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

### Validation of this review's own edits

- `aw ipd lint --phase review-finalize --agent` -> `clean`, `findings=0` for ALL SIX plans (re-run after
  every edit; two transient failures were caught and fixed mid-edit: an `IPD-I305` `Depends on:` grammar
  break from a parenthetical, and `IPD-I303`/`IPD-I304` from adding E-03 before pairing V-03 and
  advancing the watermark).
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
