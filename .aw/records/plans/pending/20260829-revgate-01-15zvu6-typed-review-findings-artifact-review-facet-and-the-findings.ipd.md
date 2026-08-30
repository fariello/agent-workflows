# IPD: Typed review findings artifact, review facet, and the findings-gate config key

- Date: 2026-08-29
- Kind: child
- Concern: Review findings (severity + decision) exist only in prose, so no gate, check, or report can see them; severity appears zero times in `ipd_lint.py` and `check_engine.py`.
- Scope: Introduce a machine-readable `.review.md` findings artifact under `.aw/records/reviews/`, add `review` to the closed artifact-type facet enum, add the `review_findings_gate` project-config key (default threshold `high`), and a dangling-reference check. The artifact carries a decisions section as well as findings, so `c621h9` (Order 04) can populate it. This plan does NOT gate anything: enforcement is `plqjt7` (Order 02) and dependency cascade is `7nkcgp` (Order 03).
- Scope-Paths: agent_workflows/artifact_naming.py, agent_workflows/config.py, agent_workflows/review_findings.py, agent_workflows/check_engine.py, agent_workflows/record_producers.py, agent_workflows/engine.py, agent_workflows/status_set.py, .aw/records/reviews/README.md, tests/test_review_findings.py
- Item-Dependencies: none
- Status: approved
- Set: revgate
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 15zvu6
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (aw set): /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-206. Verified the premise exactly: F-1 confirmed (BLOCKER/HIGH/Severity/Remediation Risk each grep to 0 in both ipd_lint.py and check_engine.py), F-2 confirmed (no .aw/records/reviews tree), the closed-enum rationale confirmed verbatim at artifact_naming.py:59-70. Found a HIGH ripple the draft did not examine (F-8): TYPE_FACET is ITERATED, not inert, and status_set.detect_artifact_type (status_set.py:175-177) loops every entry and returns the matched type, so the drafted 'reviews'->'review' addition would make a .review.md file resolve as a status-settable artifact to aw set although a review has no status lifecycle; nothing in E-02..E-08 needs that mapping, so E-01 now requires an explicit choice (omit the entry, recommended, or add it with a reviews skip beside the existing comms exemption) and must prove the aw set behavior either way. Found a HIGH registration gap (F-9): the plan introduced the first new .aw/records/ subtree but registered it NOWHERE, so reviews is absent from the closed RecordClass enum and _RECORD_CLASS_SUBPATHS (making E-06's dangling check undiscoverable by supported means), absent from _DEEP_CLEANUP_ROOTS (aw uninstall --deep would orphan it), and absent from the installer dir map and .gitkeep list (a fresh repo would never create the tree the E-04 README describes); added E-09 plus V-09 and grew Scope-Paths by record_producers.py, engine.py, and status_set.py. De-risked E-05 by measurement (F-10): project.json's strict parser preserves unknown keys in unknown_fields AND writes them back on serialize, so review_findings_gate round-trips safely and must NOT be added to CONFIG_SCHEMA (the cutover precedent is absent from it too). Corrected a mis-citation (F-11): the dependency_schema_cutover precedent is config.py:781-822, not :282-316 (which is add_config_item); its characterization was otherwise exactly right. Re-measured the corpus figures, which had DRIFTED upward since authoring (F-5: 880 history lines across 362 plans, not 863/352; F-6: 94 lines across 52 plans, not 48/49), and reframed both as measurements rather than constants while confirming their conclusions hold. Made E-06's advisory severity deliberate against its all-error siblings, forbade hardcoding the reviews path in check_engine.py, and pre-verified that the two RecordClass test modules do not assert an exact set (16 passed at 65b685e) so E-09 is safe.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from a maintainer-directed investigation into whether plan-review's High/Blocker findings are ever left unresolved; the measurement gap is the subject of this plan.

## Goal

Make a review's findings durable, typed, and machine-readable, so a High or Blocker left unfixed
becomes a fact the tooling can act on instead of prose buried in a workflow-history line. This plan
lays the data foundation only; the two sibling plans enforce on top of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the artifact and its name

- [ ] E-01 Add `review` to `ARTIFACT_TYPE_FACETS` in `agent_workflows/artifact_naming.py:59` (a CLOSED
      enum, so a dotted slug is never mis-parsed as a facet). A review file therefore takes the uniform
      clustered name `YYYYMMDD-<setid>-NN-<id6>-<slug>.review.md`, where `<id6>` is the REVIEWED PLAN's
      id6, which is the stable join key. Adding the facet token is safe and local: `_FACET_ALT`
      (`:70`) and the clustered regex (`:93`) derive from the tuple automatically.
      DO NOT BLINDLY ADD THE `reviews` -> `review` ENTRY TO `TYPE_FACET`, which the draft required
      without checking that map's consumers. `TYPE_FACET` is ITERATED by machinery this plan does not
      intend to change, so a new entry has ripple effects (F-8): `status_set.detect_artifact_type`
      (`status_set.py:175`) loops over EVERY `TYPE_FACET` item and returns the matched type, which would
      make a `.review.md` file look like a status-settable artifact to `aw set` even though a review has
      no status lifecycle; and `artifact_refs.py:274` / `artifact_rename.py:144` resolve facets through
      it. `check_engine._TYPE_FACET` (`check_engine.py:242-255`) is SAFE because it re-derives from an
      explicit allowlist tuple, which is also the precedent for how to opt a type out.
      DECIDE AND RECORD ONE of: (a) add the `TYPE_FACET` entry AND add `reviews` to
      `status_set.detect_artifact_type`'s skip set beside the existing `comms` exemption (`:176-177`),
      which is the established pattern for a facet with no status flow; or (b) do not add the
      `TYPE_FACET` entry at all in this plan, since nothing in E-02 through E-08 actually needs the
      plural->facet mapping (the writer builds its own name and the parser reads a path it is given).
      Option (b) is the smaller change and is RECOMMENDED unless a sibling plan needs the mapping; state
      which you chose and why, and prove the `aw set` behavior either way.
  - Depends on: none
  - Expected outcome: the naming grammar accepts and round-trips a `.review.md` name; existing facets
    are unchanged; and a `.review.md` file is NOT mistaken for a status-settable artifact by
    `status_set.detect_artifact_type` (proven, not assumed).
  - Execution state: pending

- [ ] E-02 Create `agent_workflows/review_findings.py` with a pure parser and writer for the findings
      table. One file per reviewed plan at `.aw/records/reviews/<clustered-name>.review.md`, holding a
      metadata block (`- Plan-Id:`, `- Reviewed-At:`, `- Reviewer:`, `- Verdict:`) and the findings
      table whose columns are the ones plan-review already writes: `ID | Severity | Scope | Area |
      Finding | Remediation Risk | Decision | Resolution`. Severity is the closed set
      `blocker|high|medium|low`; Decision is `fixed|deferred|open|replan`. The parser MUST be pure and
      never raise on a malformed row: it returns typed findings plus diagnostics, mirroring
      `ipd_lint`'s parse-then-diagnose shape.
  - Depends on: E-01
  - Expected outcome: a `.review.md` round-trips through writer -> parser with identical findings, and a
    malformed row yields a diagnostic rather than an exception.
  - Execution state: pending

- [ ] E-03 Support MULTIPLE review rounds per plan by appending rounds within the one file (a repeated
      `## Round <N>` section), because plans are demonstrably re-reviewed: the corpus has 863
      `/plan-review` history lines across 352 plans. The parser MUST expose which round is CURRENT
      (the last one), since the gate in `plqjt7` acts on current findings only, not on a finding that a
      later round already fixed.
  - Depends on: E-02
  - Expected outcome: a two-round file parses to two rounds, and `current_findings()` returns only the
    latest round's rows.
  - Execution state: pending

- [ ] E-08 Give the artifact a `## Decisions` section alongside its findings table, so a reviewer's
      SELF-RESOLVED judgement calls are recorded in the same file as its findings. Columns:
      `ID | Question | Chosen | Alternatives considered | Basis | Reversible`. The parser exposes them
      as typed decisions (same pure, never-raise contract as E-02). This plan only defines and parses
      the section; `c621h9` (Order 04) owns making reviewers WRITE it and surfacing it for audit. The
      section is OPTIONAL so a review with no autonomous decisions is still valid.
  - Depends on: E-02
  - Expected outcome: a `## Decisions` section round-trips through writer -> parser; a file without one
    parses cleanly with zero decisions.
  - Execution state: pending

- [ ] E-04 Write `.aw/records/reviews/README.md` documenting the tree: the flat layout (reviews do NOT
      move when a plan moves `pending/` -> `executed/`, so `aw ipd finalize` stays a single-file
      transaction), the id6 join key, the round convention, and the severity/decision enums.
  - Depends on: E-02
  - Expected outcome: the convention is documented where a future agent will look.
  - Execution state: pending

- [ ] E-09 REGISTER THE NEW TREE WHERE EVERY OTHER RECORDS TREE IS REGISTERED, because this plan
      introduces the first new `.aw/records/` subtree in a while and the draft treated it as a bare
      directory. Verified gaps (F-9): (1) `reviews` is NOT in the closed `RecordClass` enum
      (`record_producers.py:85-101`) nor in `_RECORD_CLASS_SUBPATHS` (`:126-135`), so
      `resolve_record_read_paths` cannot locate the tree and E-06 has no supported discovery path;
      (2) `.aw/records/reviews` is absent from `_DEEP_CLEANUP_ROOTS` (`engine.py:3683-3696`), which
      enumerates every records tree, so `aw uninstall --deep` would silently ORPHAN this tree; (3) the
      installer's records-dir map (`engine.py:4202-4213`) and its `.gitkeep` scaffolding list (`:5070`)
      do not create it, so a freshly set-up repo has no `reviews/` tree at all while this plan's README
      claims one.
      Do the minimum that makes the tree first-class and no more: add the `RecordClass` member and its
      subpath so discovery works, add the deep-cleanup root so uninstall reaches it, and add the
      installer dir + `.gitkeep` so a new repo gets it. Do NOT add it to the LEGACY `.agents/` map
      (`engine.py:4216-4226`): reviews are net-new and no legacy tree exists to read, so mapping it
      there would invent history. GOOD NEWS, MEASURED AT REVIEW so you do not have to discover it: the
      two test modules that touch `RecordClass` (`tests/test_awphysical_routing.py`,
      `tests/test_releases.py`) reference enum MEMBERS individually and iterate the enum without
      asserting an exact set, so adding a member should not break them; both were green at `65b685e`
      (`16 passed`). Re-run them and confirm. If some other test DOES assert the exact record-class set,
      STOP and report which test rather than weakening the assertion.
  - Depends on: E-01
  - Expected outcome: `resolve_record_read_paths` resolves the `reviews` class; `aw uninstall --deep`
    lists `.aw/records/reviews`; a fresh `aw setup` creates `.aw/records/reviews/` with a `.gitkeep`;
    the legacy `.agents/` map is unchanged.
  - Execution state: pending

### Task group 2: the configurable threshold

- [ ] E-05 Add the `review_findings_gate` key to `agent_workflows/config.py`, read from
      `.aw/config/project.json`, following the EXISTING precedent of `dependency_schema_cutover`
      (`config.py:781-822`; the draft cited `:282-316`, which is `add_config_item` and unrelated,
      corrected at review): read directly from project.json (NOT via the XDG user config, which drops
      unknown keys), tolerate a bare string for convenience, and never raise. Shape:
      `{"block_at": "high"}` with `block_at` in `medium|high|blocker|off`. DEFAULT WHEN ABSENT IS
      `high` (maintainer decision, 2026-08-29). Note this default is deliberately NOT fail-open, unlike
      the cutover marker: an absent key means the gate is ACTIVE at `high`. Provide a
      `findings_gate_threshold(repo_root) -> str` accessor and an `is_gating(severity, threshold)`
      predicate so both sibling plans share ONE comparison and cannot diverge.
  - Depends on: none
  - Expected outcome: threshold resolves to `high` on a repo with no key set, honors an explicit value,
    and `off` disables gating.
  - Execution state: pending

- [ ] E-06 Add `check.review-dangling` to `agent_workflows/check_engine.py`: a `.review.md` whose
      `Plan-Id:` resolves to no plan is a finding, mirroring the existing `check.from-backlog-dangling`
      treatment of an unresolvable cross-tree reference. Register it in the `RuleSpec` table beside the
      existing dangling rules (`check_engine.py:111-135`) and pick its severity DELIBERATELY: the
      neighbouring `*-dangling` rules are all `"error"`, while the plan wants advisory because a review
      of a superseded plan is untidy rather than dangerous. Use `"warning"` and say so explicitly, with
      `check.orphaned-live-blocker` (`:117-119`) as the in-tree precedent for an advisory rule, so the
      choice reads as intentional rather than as an inconsistency with its siblings.
      DISCOVERY DEPENDS ON E-09: the check must ENUMERATE `.review.md` files, and `reviews` is not a
      resolvable record class today (F-9), so this item cannot be built before E-09 registers it. Do NOT
      work around that by hardcoding a `.aw/records/reviews` path string in `check_engine.py`; the repo
      resolves record trees through one authority and a second hardcoded path is exactly the duplicate
      mechanism the house rules forbid.
  - Depends on: E-01, E-02, E-09
  - Expected outcome: a review file pointing at a nonexistent id6 is reported as a warning; a valid one
    is not; the rule appears in the `RuleSpec` table; and the file enumeration goes through the record
    path authority rather than a hardcoded string.
  - Execution state: pending

### Task group 3: prove the foundation

- [ ] E-07 Write `tests/test_review_findings.py` covering: the naming round-trip; writer/parser
      fidelity; a malformed row producing a diagnostic and NOT an exception; multi-round parsing with
      `current_findings()`; threshold resolution including the absent-key default of `high` and the
      `off` case; `is_gating` at each severity/threshold combination; the `## Decisions` section
      round-trip plus the no-decisions case from E-08; and the dangling check firing and not
      over-firing. Include the adversarial case for the closed enum: a plan slug containing a dot
      (e.g. `foo.bar`) must NOT be mis-parsed as a facet. ALSO cover the two review-added hazards:
      the F-8 guard, asserting a `.review.md` file is NOT resolved as a status-settable artifact by
      `status_set.detect_artifact_type` (this test must FAIL if someone later adds a bare `TYPE_FACET`
      entry without the skip); and the E-09 registration, asserting `reviews` resolves through the
      record-path authority. Add the F-10 guard too: a `project.json` carrying `review_findings_gate`
      round-trips through `parse_portable_policy` without losing the key.
  - Depends on: E-01, E-02, E-03, E-05, E-06, E-08, E-09
  - Expected outcome: the whole foundation is covered by tests that fail if any piece regresses.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ARTIFACT_TYPE_FACETS` (`artifact_naming.py:59`) is explicitly a CLOSED enum, with the stated reason
  that a dotted slug must never be mis-parsed as a facet. Adding `review` must preserve that property,
  hence the adversarial dotted-slug test in E-07.
- `dependency_schema_cutover` (`config.py:781-822`; the draft's `:282-316` was a mis-citation of
  `add_config_item`, corrected at review per F-11) is the precedent for a project-config key: read
  straight from `.aw/config/project.json`, tolerate a bare string, never raise. Reuse that shape rather
  than inventing a second config-reading style. NOTE the deliberate divergence: that marker is
  fail-OPEN (absent means no cutover); this key's absent-default is `high` (gate active).
- The new key needs NO schema registration and is round-trip safe (F-10, measured): `project.json`'s
  strict parser preserves unknown keys in `unknown_fields` and writes them back on serialization, and
  the cutover precedent is likewise absent from `CONFIG_SCHEMA`. Do NOT add the key to `CONFIG_SCHEMA`.
- `ipd_lint` parses open questions into `List[Dict[str, str]]` (`ipd_lint.py:162`, `:258`) and then
  diagnoses them separately (`check_open_questions`, `:597`). The findings parser should mirror that
  parse-then-diagnose split so `plqjt7` can compare findings to open questions with both already
  parsed.
- `aw attention` knows five trees (`backlog`, `plans`, `releases`, `research`, `specs` via
  `attention_contract.CLASS_MAPS`). Reviews are deliberately NOT added as a sixth attention tree in
  this plan; surfacing is deferred (see Deferred) because an attention mapping needs its own
  status-class semantics.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Severity is invisible to every deterministic gate. | `grep -c` for `BLOCKER`, `HIGH`, `Severity`, `Remediation Risk` in `agent_workflows/ipd_lint.py` + `check_engine.py` returns `0` for all four |
| F-2 | There is no findings artifact anywhere today. | No `.aw/records/reviews/` tree exists; no `*review*.json` under `.aw/records/` |
| F-3 | Findings live only in prose, in two places. | The plan's `## Workflow history` line and the session transcript under `.aw/records/runs/*/sessions/` |
| F-4 | Because of F-3, the corpus cannot be measured reliably. | An attempt to count findings by scraping transcripts yielded 55 severity+decision rows, and 33 of 278 session files contain a verbatim copy of `plan-review.md` (which itself contains the literal text `` `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW` ``), so scraped totals conflate instructions with findings |
| F-5 | Re-review is normal, so a findings file needs rounds. CONFIRMED and RE-MEASURED at review: the counts are a live measurement, not a constant, and they GREW during authoring-to-review. Do not treat the plan's numbers as fixed; the CONCLUSION (lines far exceed distinct plans, so re-review is routine and rounds are required) holds under both readings. | plan text: 863 lines / 352 plans. Re-measured at `65b685e`: 880 `/plan-review` history lines across 362 distinct plan files |
| F-6 | Reviews reaching an open-questions verdict are common. RE-MEASURED at review: the plan's figures understate it, and the drift direction matters because `plqjt7` gates on exactly this population. | plan text: 48 lines / 49 plans / 44 executed. Re-measured at `65b685e`: 94 lines across 52 plan files, of which 44 are in `executed/`, 8 in `pending/`, and 0 in `superseded/`+`not-executed/`. Note 94 lines over 52 files independently corroborates F-5's re-review conclusion |
| F-7 | Plans move between lifecycle directories, so a co-located review file would couple finalize to two files. | `aw ipd finalize` moves a plan `pending/` -> `executed/`; the repo already has a live class of bug from lifecycle state coupled across locations |
| F-8 | ADDED AT REVIEW (HIGH): the draft's `TYPE_FACET` edit has UNEXAMINED ripple effects. That map is not inert lookup data, it is ITERATED. `status_set.detect_artifact_type` loops over EVERY `TYPE_FACET` entry and returns the matched record type, with an explicit `comms` skip because comms has no status flow; adding `reviews` would therefore make a `.review.md` file resolve as a status-settable artifact to `aw set`, though a review has no status lifecycle. Nothing in E-02..E-08 actually needs the plural->facet mapping. E-01 now requires choosing between adding the entry PLUS a `reviews` skip, or omitting the entry entirely (recommended), and proving the `aw set` behavior. | `status_set.py:175-177` (the loop and the `comms` skip); consumers at `artifact_refs.py:274`, `artifact_rename.py:144`; `check_engine.py:242-255` is safe because it re-derives from an explicit allowlist |
| F-9 | ADDED AT REVIEW (HIGH): the plan introduces a new `.aw/records/` subtree but registers it NOWHERE, so three integration points would silently disagree with the README E-04 writes. `reviews` is absent from the closed `RecordClass` enum and `_RECORD_CLASS_SUBPATHS`, so `resolve_record_read_paths` cannot locate the tree and E-06's dangling check has no supported discovery path; `.aw/records/reviews` is absent from `_DEEP_CLEANUP_ROOTS`, which enumerates every other records tree, so `aw uninstall --deep` would orphan it; and the installer's records-dir map and `.gitkeep` list do not create it, so a freshly set-up repo would have no `reviews/` tree. Added E-09 to close all three, deliberately excluding the legacy `.agents/` map. | `record_producers.py:85-101` (`RecordClass`), `:126-135` (`_RECORD_CLASS_SUBPATHS`), `:601` (`resolve_record_read_paths`); `engine.py:3683-3696` (`_DEEP_CLEANUP_ROOTS`, listing plans/prompts/comms/backlog/research/specs/walkthroughs/roadmaps/releases but not reviews); `engine.py:4202-4213` + `:5070-5077` (installer dirs + `.gitkeep`) |
| F-10 | ADDED AT REVIEW (MED, DE-RISKS E-05): the `review_findings_gate` key is SAFE to add to `project.json` and needs no schema registration, which the plan asserted only implicitly. Verified two things the executor would otherwise have to discover: `parse_portable_policy` is fail-closed on `schema_version`/`preset`/`role` but PRESERVES unknown keys in `unknown_fields` rather than rejecting them, and those fields are written BACK on serialization, so the key survives a project.json rewrite. Also verified the key does NOT belong in `CONFIG_SCHEMA` (only 9 keys, and the `dependency_schema_cutover` precedent is absent from it too), so E-05 must not add it there. | measured: `parse_portable_policy({... 'review_findings_gate': {'block_at':'high'}})` yields `unknown_fields: {'review_findings_gate': ...}` and the serialized dict still contains the key; `'dependency_schema_cutover' in config.CONFIG_SCHEMA` is `False` |
| F-11 | ADDED AT REVIEW (LOW): the plan's `config.py:282-316` citation for the `dependency_schema_cutover` precedent is WRONG; that range is `add_config_item`, unrelated list-key mutation. The real precedent is `config.py:781-822`, and its characterization in the plan (read straight from project.json, tolerate a bare string, never raise, fail-open default) is otherwise exactly accurate. Corrected in E-05 and the conventions list. | `grep -n dependency_schema_cutover agent_workflows/config.py` -> `:781`, `:788`, `:791`, `:818`; `sed -n '275,330p'` shows `add_config_item` |

## Proposed changes (ordered, validatable)

1. Add the `review` facet to the closed naming enum, deciding the `TYPE_FACET` question deliberately so
   a review is not mistaken for a status-settable artifact (E-01).
2. Add the pure findings parser/writer and the flat `reviews/` tree (E-02, E-04).
3. Support multiple rounds with an explicit current round (E-03).
4. Register the new tree as a first-class record class, in uninstall, and in the installer (E-09).
5. Add the configurable threshold with a shared `is_gating` predicate (E-05).
6. Add the dangling-reference check, enumerating through the record-path authority (E-06).
7. Cover all of it with tests, including the closed-enum adversarial case and the two review-added
   hazard guards (E-07).

## Deferred / out of scope (with reason)

- **Any gating or blocking behavior.** Deferred to `plqjt7` (Order 02) by design: this plan must be
  landable without changing whether anything executes, so the data layer can be verified in isolation.
- **The dependency cascade.** Deferred to `7nkcgp` (Order 03).
- **Backfilling the 352 existing reviewed plans.** Deliberately out of scope. Their findings exist only
  in prose and transcripts, and F-4 shows scraping them is unreliable; manufacturing a typed record
  from an unreliable scrape would put false precision into the tree. New reviews get records going
  forward, exactly as the spec-id6 cutover grandfathered pre-cutover names.
- **Adding `reviews` as a sixth `aw attention` tree.** Deferred: it needs its own native-status ->
  attention-class mapping in `attention_contract.CLASS_MAPS`, which is a separate design question
  (a review is not "ready/active/blocked" in the same sense a plan is).
- **Changing the plan-review workflow to EMIT the artifact.** Deferred to `plqjt7`, which owns the
  enforcement and therefore the instruction change; splitting the emitter from the format would leave
  this plan unverifiable on its own.

## Scope check

- Over-scope: none. Every E-item is data-layer or registration only; nothing gates.
- UNDER-SCOPE FOUND AND FIXED AT REVIEW: the plan created a new `.aw/records/` subtree without
  registering it anywhere (F-9), so `Scope-Paths` grew by `record_producers.py`, `engine.py`, and
  `status_set.py`, and E-09 was added. These are not scope creep: without the record-class registration
  E-06 has no supported way to find the files it checks, and without the uninstall/installer entries the
  README E-04 writes would describe a tree that a fresh repo never creates and an uninstall never
  removes.
- `status_set.py` is in `Scope-Paths` ONLY for the F-8 decision (a `reviews` skip beside the existing
  `comms` exemption), and only if E-01 chooses option (a). If E-01 chooses option (b), omitting the
  `TYPE_FACET` entry, then `status_set.py` needs NO edit and must be left untouched; say which happened.
- Under-scope otherwise: acknowledged and unchanged. After this plan NOTHING is gated: a High left
  `open` still blocks nothing, because the enforcement lives in `plqjt7`. The honest claim is "findings
  can now be recorded and read by machine", not "unfixed findings are now caught".

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings.py` green, run BARE (the repo's `addopts` supplies
   `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0` or a second `-q`).
2. Full default suite green with counts pasted, compared against a baseline YOU measure at execution
   time. Do not reuse a recorded number: concurrent agents are committing to this checkout, and the
   corpus counts in F-5/F-6 already drifted between authoring and review.
3. Naming safety demonstrated: the closed-enum property still holds for a dotted slug.
4. Threshold default demonstrated on a repo with NO `review_findings_gate` key, showing it resolves to
   `high`.
5. The layout/record-class tests must be run explicitly and pasted, because E-09 touches the closed
   `RecordClass` enum and the installer's dir map, which are spec-governed and have their own
   conformance coverage. Name which test modules you ran. If one of them FAILS because it asserts the
   exact record-class set, STOP and report rather than editing the assertion to fit.
6. `aw check` must be run on THIS repo after the change and show no new drift, since E-06 adds a rule
   that scans a tree this repo will now have.

## Spec / documentation sync

- `.aw/records/reviews/README.md` is a deliverable (E-04). It must NOT describe a tree the tooling does
  not create: E-09 makes the tree real (record class, installer, uninstall), so the README and the code
  agree. If E-09 is descoped for any reason, E-04's README must say plainly that the tree is
  hand-created, rather than implying `aw setup` provides it.
- The `review` facet joins a documented closed enum; `artifact_naming.py`'s module docstring lists the
  facet types (`:7-9`) and must be updated in the same edit as E-01.
- If E-01 takes option (a), `status_set.detect_artifact_type`'s docstring states that only `comms` is
  intentionally unresolved; adding a second exemption means that sentence must be updated too, or it
  becomes false.
- No spec governs review findings today. If this Set lands, the plan-review workflow body becomes the
  natural place to document the artifact, which `plqjt7` owns.

## Open questions

### OQ-01: Should a review file be named by the plan's id6 or get its own id6?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during authoring
- Resolution or deferral rationale: RESOLVED - use the REVIEWED PLAN's id6. The join must survive a
  plan rename or a `pending/` -> `executed/` move, and the id6 is the repo's stable cross-tree handle
  (the same role it plays in `From-Backlog`, `From-Spec`, and `Item-Dependencies`). A separate id6 would
  add a second identity with no join value and would need its own dangling check in both directions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session showing a `.review.md` clustered name parsed by
    `artifact_naming` and round-tripped, plus the ADVERSARIAL case: a slug containing a dot is NOT
    parsed as a facet. Paste the diff of `ARTIFACT_TYPE_FACETS` proving no existing facet changed.
    STATE which `TYPE_FACET` option you took (add-plus-skip, or omit) and WHY. Then paste the F-8 proof
    either way: `status_set.detect_artifact_type` called on a real `.review.md` path returns something
    other than a status-settable `reviews` type, so `aw set` cannot be pointed at a review file. If you
    chose option (a), also paste the `reviews` skip beside the `comms` exemption; if you chose (b), paste
    a grep proving `status_set.py` was NOT modified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a written `.review.md` and the parser's output for it, showing every column
    recovered. Then paste the malformed-row case showing a DIAGNOSTIC and no traceback (a parser that
    raises fails this item).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a two-round file and the parsed result, showing `current_findings()`
    returns ONLY round 2. Include a case where round 1 has a `HIGH/open` finding that round 2 marks
    `fixed`, proving a superseded finding is not reported as current.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the README, and confirm it states the three load-bearing conventions
    (flat/no-move, id6 join key, round semantics) plus both enums.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste threshold resolution in four conditions: no key present (MUST be `high`),
    explicit `medium`, explicit `blocker`, explicit `off`. Paste the `is_gating` truth table for all
    severity x threshold combinations. Also paste a malformed-key case proving it does not raise.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw check` reporting `check.review-dangling` for a review whose `Plan-Id:`
    resolves to nothing, AND paste a run with a valid review showing the rule does NOT fire (proving it
    is not vacuous or over-firing). Paste the new `RuleSpec` entry and state the chosen severity with its
    in-tree precedent, since the neighbouring `*-dangling` rules are `error` and this one is deliberately
    advisory. Paste a grep proving the file enumeration goes through the record-path authority and that
    no `.aw/records/reviews` path string was hardcoded into `check_engine.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste a `.review.md` containing a `## Decisions` section and the parser's typed
    output for it, showing every column recovered. Then paste a review file with NO decisions section
    parsing cleanly with zero decisions (proving the section is optional, not silently required).
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `resolve_record_read_paths` resolving the `reviews` class (a Python session
    showing the returned path), the `_DEEP_CLEANUP_ROOTS` diff including `.aw/records/reviews`, and a
    fresh-repo `aw setup` (or the installer's dir map + `.gitkeep` list diff) showing the tree is
    created. Paste proof the LEGACY `.agents/` map was NOT extended. Then paste the existing
    record-class/layout tests still green, naming which ones you ran, since `RecordClass` is a closed
    spec-governed enum and this is the item most likely to trip a conformance test.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the full test file result with counts, and the full default suite result
    with counts. Every V-item above must have a corresponding test; name which test covers which.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 9 E-leaves across 3 task groups, under the thresholds. E-09 was
  added at review as a separate leaf rather than folded into E-01 because it is a distinct concern
  (registering a records tree across three modules) with its own test surface, and bundling it would have
  made E-01 both a naming change and a layout change.

This plan is `to-review` and requires explicit human approval before execution.

REVIEW NOTE FOR THE APPROVER (two judgment calls, neither hidden): first, E-01 now offers a documented
CHOICE about the `TYPE_FACET` entry, because adding it naively would make a `.review.md` file look
status-settable to `aw set` (F-8); the recommendation is to omit the entry, since nothing in this plan
needs it, but if a sibling plan needs the plural->facet mapping, take option (a) with the skip. Second,
E-09 touches the closed `RecordClass` enum and the installer, which are spec-governed; if you would
rather a new records tree go through its own layout change, E-09 should be split out and this plan's
README (E-04) must then state the tree is hand-created.

RESOLVE-BEFORE-REFUSING (maintainer instruction, 2026-08-29): if you hit an obstacle while executing
this plan, you MUST first do the work of finding a strong recommended path from repository evidence.
Throwing up your hands and reporting "cannot proceed" is a LAST resort, and it is only acceptable when
you can state (a) what you tried, (b) the specific evidence that blocks each candidate approach, and
(c) a concrete recommended option with its trade-offs for the maintainer to choose. A bare refusal, or
an open question that merely restates the obstacle without a recommendation, is not an acceptable
outcome for this plan.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries
pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
