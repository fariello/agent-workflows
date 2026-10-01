# IPD: Specify the spec requirement-ID addressing convention and the SPEC-PLAN-TRACE contract

- Date: 2026-09-30
- Kind: child
- Concern: Approved spec `25kzda` 4.8 declares `SPEC-PLAN-TRACE` ("every mandatory spec requirement maps to at least one E item and every acceptance criterion maps to at least one V item"), and spec `z7nbn1` 4.4 DEFERRED it to backlog `vy20et` because a spec requirement carries no machine-readable id by any agreed convention. Its three sibling codes shipped (`production_checks.spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`); TRACE is the one hole in that row, and `z7nbn1` 4.4 additionally binds the repository to the negative claim that "a produced plan MUST NOT be described as trace-verified" until this exists. Nothing can be built first, because the convention decides what the parser reads and research `vkub9o` recommended AGAINST a parser on corpus-wide grounds; that recommendation must be reconciled against the narrower job TRACE actually has before any code is written.
- Scope: Produce the SPEC ONLY: the requirement-ID addressing convention for new specs, the retrofit/grandfathering policy, the parser's required behavior as a contract (not its implementation), and `SPEC-PLAN-TRACE`'s severity and failure mode. Re-measure the corpus at execution HEAD rather than trusting this plan's numbers, register the cutover date so the boundary is stamped rather than hardcoded, and answer OQ-01 (the mandatory-requirement marker) with the maintainer. NO parser, NO check code, NO `production_checks.py` edit, and NO edit to any spec's approved requirements: Order 02 builds against this spec once approved.
- Scope-Paths: .aw/records/specs, .aw/records/plans/pending/20260930-reqids-01-jjh4aj-specify-the-spec-requirement-id-addressing-convention-and-th.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: medium
- From-Backlog: vy20et
- Set: reqids
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: jjh4aj

## Workflow history

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-R01 through PR-R07 all FIXED in place. Structural lint conformed at `author` with ZERO findings and again at `review-finalize`. RE-MEASURED EVERY MATERIAL CLAIM at HEAD `36bcbfaa3`, including the ones the plan's case depends on, and the load-bearing ones HOLD: 38 specs / 20 live / 12 approved; exactly two live specs carry no requirement id of any form (`25kzda`, `kw5y2s`); 10 of 12 approved carry requirement ids and 7 carry acceptance ids; `_SPEC_ACTIONS` maps ONLY `approved` to `ACTION_PLAN`; and F-05's hinge is confirmed by reading the code, since the production call site computes `new_produced_paths` against `baseline_plan_ids` and passes it into `spec_plan_conformance` and `spec_plan_gate_carry`, so TRACE needs no pre-existing `- From-Spec:` edge. `25kzda` 4.8's TRACE row, its `RETRY, then FAIL ITEM` action and its message template all match the plan's quotation verbatim; TRACE has zero enforcement while its three siblings are built; `z7nbn1` 4.4's deferral and its 'MUST NOT be described as trace-verified' language read as quoted; and `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:<id6> --dry-run` validates. THE DOMINANT FINDING IS A SELF-CONTRADICTION THAT WOULD HAVE STOPPED THE PLAN: OQ-01 carries `- Blocking: no` with a reasoned resolution, while F-08 and the gate both asserted it BLOCKS and the gate added 'this plan is not ready to execute until the maintainer answers'. The field is what the machinery reads, so the prose asserted a stop nothing implements; resolved in favour of `no` and recorded as OQ-04 with the alternative stated (F-12). Three measurement corrections: F-09's acceptance breakdown was wrong in three places and contradicted F-03 (F-13), V-09 pinned a stale `3387 passed` baseline against a suite that now reports `3446 passed` plus one pre-existing unrelated failure owned by backlog `fnb8pl` (F-14), and E-06 said 'five features' over a six-item list while a sibling bullet listed a different five and `config.py`'s own comment says 'three' (F-16). Also recorded: E-09 edits Order 02's plan file, which is undeclared but implicitly allowed, so a `--scope-reason` is owed at finalize (F-15). Human approval is still required. (Review record: `.aw/records/reviews/20260930-reqids-01-jjh4aj-specify-the-spec-requirement-id-addressing-convention-and-th.review.md`.)
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): status transition applied by `aw ipd set reviewed jjh4aj`, kept beside the `/plan-review` line above as the attributed record of the transition itself. Its date is the setter's UTC stamp while the local date was 2026-09-30, the clock skew backlog `fnb8pl` owns.
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored review-ready while graduating backlog `vy20et`. Corpus RE-MEASURED at HEAD `764442f7` (38 specs, not the 36 research `vkub9o` measured on 2026-09-20), and the measurement CHANGES the recommendation's basis: TRACE is scoped to ONE dispatched spec, not the corpus, which is the reframing `vkub9o` did not apply. Produces a spec only; no code.

## Goal

Decide, as an approved spec, how a spec requirement and an acceptance criterion are ADDRESSED so that
`SPEC-PLAN-TRACE` can be built deterministically against a stated contract rather than against a
guess. The deliverable is the decision plus its honest limits, so that Order 02 implements a
specified check instead of inventing one, and so that `z7nbn1` 4.4's deferral has a carrier that
actually closes it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before deciding

- [ ] E-01 RE-MEASURE THE SPEC CORPUS AT EXECUTION HEAD, because every number in this plan and in research `vkub9o` dates instantly and the decision turns on them. `vkub9o` measured 36 specs on 2026-09-20 and recorded that the corpus went 27 -> 28 -> 29 -> 36 in twelve days; this plan measured 38 at HEAD `764442f7`. Derive, do not assume: enumerate `.aw/records/specs` RECURSIVELY (specs live in status subdirectories, so a flat glob goes blind), and for each spec record its `- Status:`, whether it carries `- Id:`, the distinct requirement-id shapes at declaration sites, the distinct acceptance-criterion id shapes, and whether it uses bare dotted paragraph ids. Derive the shape list FROM THE FILES by generalizing digit runs in the first token of each non-blank line (after stripping at most one leading bullet, table pipe, or heading marker), exactly as `vkub9o` Section 1 did, rather than running one grep per pre-guessed form: `vkub9o` records that a fixed grep list got the corpus wrong in BOTH directions and missed the most systematically id'd spec in the tree. REPORT the counts this plan's F-02 and F-03 assert and say plainly whether each still holds.
  - Depends on: none
  - Expected outcome: a reproducible census, with the script text recorded, giving: total specs, the live subset, which live specs carry NO requirement id of any form, which carry no `- Id:`, and the per-family id counts. The specific claims to confirm or correct are F-02 (2 live specs with no requirement id of any form), F-03 (10 of 12 `approved` specs already carry requirement ids, 7 carry acceptance ids) and the CORRECTED F-09 breakdown (7 approved specs carry acceptance-like ids, 4 have an acceptance section with none, 1 has no acceptance section). Review re-measured all three at HEAD `36bcbfaa3` and F-02 and F-03 both HELD while F-09 as authored did NOT, so treat F-09 as the one most likely to need care and classify `25kzda` explicitly: it carries 4 `A<n>:` table rows while having no acceptance HEADING, which is what the authored row got wrong in both directions (F-13).
  - Execution state: pending

- [ ] E-02 MEASURE WHICH SPECS CAN ACTUALLY REACH THE TRACE CHECK, which is the fact that decides whether the corpus-wide retrofit question `vkub9o` costed is even in scope. TRACE fires inside ONE code path: the spec production action, reached only when a spec's status maps to `ACTION_PLAN`. Read `run_selection_policy._SPEC_ACTIONS` and record which statuses map to `ACTION_PLAN` and which to `ACTION_SKIP`. Then read the call site in `runner_shared` that invokes `_pc.spec_plan_count`, `_pc.spec_plan_conformance` and `_pc.spec_plan_gate_carry` (locate by the content string `spec-production-out-of-scope-paths`, then read forward to the `findings.extend` block) and record: what the verifiers receive, specifically whether the produced plan paths are already computed and in hand. THE POINT OF THIS MEASUREMENT is that `vkub9o`'s decisive objection was a MISSING JOIN EDGE (0 plans carried `- From-Spec:` for the release-gating spec it studied, so coverage was uncomputable); if the dispatcher already holds the produced paths, that objection does not apply to TRACE-at-production, and the reasoning must be recorded either way rather than assumed in this plan's favour.
  - Depends on: none
  - Expected outcome: the measured status -> action mapping for specs, and a recorded finding stating whether the production dispatcher holds the produced plan paths at the moment the verifiers run. If it does NOT, say so: that would invalidate F-05 and the spec must then either specify how the edge is obtained or record TRACE as still unbuildable, which is a legitimate outcome of this plan.

  - Execution state: pending

### Task group 2: write the spec

- [ ] E-03 CREATE THE SPEC FILE with the tool and nothing more, so that identity and naming are never hand-authored. Run `aw specs new --title ... --slug ... --apply`, which mints a fresh id6 and writes both the conforming `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` filename and the matching `- Id:` bullet. Do NOT hand-name the file, do NOT hand-write the id6, and leave it at the `- Status: draft` the tool emits. Content comes in E-04 and later items; this item's whole deliverable is a correctly identified, correctly located, empty-of-normative-content spec file.
  - Depends on: E-01
  - Expected outcome: a new `.spec.md` exists under `.aw/records/specs/draft/`, tool-created, whose filename id6 equals its `- Id:` bullet and whose `- Status:` is `draft`.
  - Execution state: pending

- [ ] E-04 WRITE THE REQUIREMENT AND ACCEPTANCE NAMESPACES into that spec, which is the core normative decision the whole Set rests on. State (a) the requirement-ID convention for NEW specs, admitting the PREFIXED FAMILIES the corpus already uses rather than mandating a single letter, because E-01's census is expected to show a single-namespace rule would invalidate most live specs while a family-admitting rule invalidates almost none; and (b) the ACCEPTANCE-CRITERION namespace as DISTINCT from the requirement namespace, since TRACE has two halves that must not collide (`vkub9o` 1.2 records that counting `A*` as requirements "would roughly double the apparent id population while measuring the wrong thing"). Ground both in E-01's measured census, not in this plan's authoring numbers.
  - Depends on: E-03
  - Expected outcome: the spec states the requirement namespace and the families it admits, and separately states the acceptance-criterion namespace, with the census numbers cited.
  - Execution state: pending

- [ ] E-05 WRITE THE DECLARATION-SITE RULE AND THE ADDRESSING RATIONALE, the two things that make the convention usable and defensible. The declaration-site rule says WHERE an id is binding, so an id merely MENTIONED in prose is never mistaken for one DECLARED; without it a parser cannot tell a definition from a citation and TRACE would count a spec's own cross-references as requirements. The rationale carries `vkub9o`'s strongest evidence rather than dropping it: three of its five measured harm cases were ADDRESSING failures that a convention fixes and a coverage mechanism does not, including two wrong citations of one requirement by an author and their reviewer, and a code comment disagreeing with both.
  - Depends on: E-04
  - Expected outcome: the spec states the declaration-site rule and carries the addressing-failure rationale with `vkub9o`'s measured cases cited.
  - Execution state: pending

- [ ] E-06 SPECIFY THE RETROFIT AND GRANDFATHERING POLICY IN THAT SPEC, and specify it through the mechanism this repository already uses rather than inventing a second one. `config.KNOWN_FEATURE_CUTOVERS` is the single registry (its own block comment says "TO ADD A FEATURE: put its introduction date here, and let `sync_cutovers_on_install` stamp the per-repo boundary. Do not invent a second mechanism"), `resolve_cutover_date` reads it, and the registry carries SIX keys at review (`spec_id6`, `dependency_schema`, `carrier_obligations`, `setid_length`, `prompt_id6`, `walkthrough_id6`) of which THIS repository stamps five in `.aw/config/project.json` (all but `setid_length`). DO NOT RESTATE EITHER COUNT IN THE SPEC: F-16 measures that the authored "five features" contradicted its own six-item list, that the sibling conventions bullet lists a different five, and that `config.py`'s own block comment still says "three shipped features", so the number is drifting in the SOURCE and a spec quoting it would be stale on arrival. State the MECHANISM and name the key; if a count is genuinely wanted, re-derive it at execution and say which set it counts (registered versus stamped). The spec MUST state: the feature key name, that the boundary is STAMPED per repository rather than hardcoded, and that grandfathering is PER SPEC against that boundary, so a pre-cutover spec stays valid forever while a NEW spec is judged. It MUST also state the direction the repository has already chosen twice in this area: pre-cutover legacy spec NAMES are grandfathered, and `vkub9o` Q5 recommends GOING FORWARD with the prose-only live specs left alone. NAME THE CONSEQUENCE HONESTLY: under grandfathering, a reader cannot tell a conforming spec from an exempt one, which is the exact dilemma `vkub9o` Option B states; record it as an accepted cost with the reason, do not hide it.
  - Depends on: E-05
  - Expected outcome: a retrofit section in the spec naming the cutover feature key, the per-spec grandfathering rule, the going-forward decision for the live prose-only specs E-01 counted, and the stated cost of grandfathering. NO change to `config.py` in this plan: registering the key is Order 02's work, and the spec only says which key it will be.
  - Execution state: pending

- [ ] E-07 SPECIFY THE TRACE CONTRACT AND ITS SEVERITY, which is the half of backlog `vy20et` that decides what Order 02 may ship. State: (a) the check's SCOPE, that it inspects a plan produced by the spec production action against the ONE spec that produced it, and not the corpus, with E-02's measured mapping as the citation; (b) its SEVERITY and failure mode, reconciled with what `25kzda` 4.8 already specifies for TRACE, whose Action column reads `RETRY, then FAIL ITEM` and whose message template is `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. ...` (the spec must either adopt that verbatim, as the three shipped siblings did, or state explicitly that it AMENDS `25kzda` and why); (c) the GRANDFATHERED-SPEC behavior, meaning what TRACE does when the producing spec predates the cutover or declares no ids, which must be a PASS rather than a failure, or the check would refuse production for specs nobody agreed to retrofit; and (d) THE HONEST LIMIT the backlog item requires be carried, verbatim in substance: a trace check proves a plan step CITES a requirement, not that it implements it. That limit is not a footnote: it is the reason this check may not be described as verifying coverage, and `z7nbn1` 4.4's "MUST NOT be described as trace-verified" language is what it replaces.
  - Depends on: E-05, E-02
  - Expected outcome: a TRACE contract section stating scope, severity, the `25kzda` 4.8 relationship (adopt or amend, decided explicitly), the grandfathered-spec pass behavior, and the citation-not-implementation limit. If the decision is to AMEND `25kzda`, the spec says so in its relations section; this plan still edits no `.spec.md` other than the one it creates.
  - Execution state: pending

- [ ] E-08 WRITE THE SPEC'S OWN OPEN-QUESTIONS SECTION, carrying the three decisions this plan resolved on repository evidence rather than on maintainer instruction, so the human ratifies them at SPEC REVIEW where the authority actually sits. This is not bookkeeping: OQ-01 (the mandatory-requirement marker), OQ-02 (adopt or amend `25kzda` 4.8) and OQ-03 (whether dotted section/paragraph ids count) are all recorded here as `resolved` with a RECOMMENDATION and a measured basis, and every one changes what Order 02 builds. Each must appear in the spec with: the question, the options measured (including the vacuity finding F-08 for OQ-01), the recommended answer, and the evidence for it. State plainly in the spec that these are AGENT RECOMMENDATIONS awaiting the approval attestation, not settled maintainer rulings, because a spec that presents an agent's choice as a ruling is the forgery shape this repository guards against.
  - Depends on: E-05, E-07
  - Expected outcome: the spec carries an open-questions section with the three questions, their options, the recommendations, and an explicit statement that they await human ratification via the approval attestation. No maintainer ruling is asserted anywhere in the spec.
  - Execution state: pending

- [ ] E-09 HAND THE SPEC OFF for human review WITHOUT asserting any review or approval outcome, then record the Set's state honestly. Move it out of `draft` with `aw specs set <path> --status to-review --message ...` (or `aw spec set to-review <id6>`) so the setter writes the transition and the history line rather than a hand edit. DO NOT write `reviewed`, DO NOT write `approved`, and DO NOT write an `- Approval:` or `- Readiness:` attestation anywhere: approval is the maintainer's, requires `--by-human`, and a spec reaching `approved` is what unblocks Order 02. Then state in this plan's own history what the next actor must do. ALSO RECORD the one thing a reader of `z7nbn1` needs: that `z7nbn1` 4.4's deferral of TRACE is addressed by this spec but NOT discharged until Order 02 executes, so nobody reads a written convention as a shipped check.
  THEN WRITE ORDER 02'S APPROVAL EDGE, which is the step that makes the Set's human gate machine-enforced instead of trusting an agent to stop (added at this Set's 2026-10-01 plan review; see the parent `9wzlou`'s "Cross-IPD validation" SECOND point for the measurement). Once this spec's id6 exists, set Order 02's dependency statement to BOTH edges with the dedicated verb, `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:<this-spec-id6> --yes`, never by hand-editing the field. That verb canonicalizes the edge order itself and refuses a malformed, dangling, ambiguous or cyclic edge BEFORE writing, so a typo cannot be persisted; it was confirmed at review by a `--dry-run` of exactly this two-edge statement against a real spec id6, which validated and reported `unchanged (dry-run)`. WHY THIS IS OWED HERE RATHER THAN AUTHORED IN ADVANCE: the id6 is MINTED by E-03's `aw specs new`, so it does not exist when Order 02 is written, which is exactly why Order 02 could not declare the edge itself. WHY IT IS WORTH DOING: `runner_shared.edge_satisfied`'s `state:` branch refuses the dependent with "spec <id6> is <actual>, needs exactly 'approved'" until the spec truly carries that status, so the runner holds Order 02 rather than dispatching it on the honour system. If the setter refuses the value, STOP and report rather than hand-editing the field; Order 02's own E-01 refusal is the second layer and is not a substitute for this edge.
  - Depends on: E-05, E-06, E-07, E-08
  - Expected outcome: the spec sits at `- Status: to-review` under `.aw/records/specs/to-review/`, moved by the setter with a history line naming this plan, carrying no approval or readiness attestation. `aw check specs` (or `aw check`) reports no finding against it. Order 02's `- Item-Dependencies:` now reads `executed:jjh4aj, state:spec:approved:<this-spec-id6>`, written by the setter, and `aw check` reports no dangling-dependency finding against it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A SPEC IS CREATED BY THE TOOL, NOT BY HAND. `aw specs new --title ... --slug ... --apply` mints an id6 and writes both the `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` filename and the `- Id:` bullet; the repository instructions state plainly "Specs now carry the stable `<id6>` in the filename GOING FORWARD". Verified by running `aw specs new --title Probe --slug probe` in preview at authoring, which reported it would write `.aw/records/specs/draft/<date>-<id6>-01-<id6>-probe.spec.md` with `- Status: draft` and a `## Workflow history` section.
- STATUS AND LOCATION AGREE, AND THE SETTER MOVES THE FILE. `.aw/records/specs/README.md`: "The status setters (`aw specs set <path> --status <enum>` and `aw set <status> <selector>`) automatically relocate the file to the matching directory upon status transition." So E-08 must not `git mv` the file itself.
- AN AGENT MAY NOT APPROVE A SPEC, AND MAY NOT WRITE ANOTHER ROLE'S ATTESTATION. Human approval needs `aw spec set approved <id6> --by-human`, and the repository instructions forbid hand-writing a `- Readiness:` or `- Approval:` field, naming a measured 2026-09-06 incident where an agent wrote `Readiness: go-pending-approval` into four plans having run no review. E-08 is written to leave both absent.
- THE CUTOVER REGISTRY IS SINGULAR AND ITS COMMENT SAYS SO. `config.KNOWN_FEATURE_CUTOVERS` carries the FEATURE INTRODUCTION date per feature and `sync_cutovers_on_install` stamps the per-repo boundary; `resolve_cutover_date` resolves it with `.aw/config/project.json` `cutovers.<feature>` first. This repository's stamped values at authoring are `spec_id6`, `dependency_schema`, `carrier_obligations`, `prompt_id6`, `walkthrough_id6`. E-06 follows this and adds no second mechanism.
- SPEC STATUS IS A BARE ENUM AND HISTORY CARRIES THE PROSE. `.aw/records/specs/README.md` requires a "machine-legible, single-line bare-enum `- Status:` front-matter bullet (no trailing prose; put rationale in history)".
- THE THREE SIBLING CODES ADOPTED `25kzda` 4.8's TEXT RATHER THAN RESTATING IT. `production_checks.py`'s module docstring names the three codes and each verifier's docstring quotes its `25kzda` 4.8 pass criterion verbatim under "Pass criterion (25kzda 4.8):". E-07 follows that precedent, which is why it requires an explicit adopt-or-amend decision rather than silent paraphrase.

## Findings

| Id | What was measured | Evidence | Why it matters here |
|---|---|---|---|
| F-01 | `SPEC-PLAN-TRACE` has ZERO enforcement, and its three siblings are BUILT | `production_checks.py` implements `spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry` and its module docstring names exactly those three as "the three in-scope verification codes from spec 25kzda 4.8 / z7nbn1 4.4". Executed plan `aeq7f8` V-09 recorded `grep -rn 'SPEC-PLAN-TRACE' agent_workflows/` returning empty (exit 1). | TRACE is the one gap in an otherwise complete row, so the target is narrow and well bounded. It also means the landing site for Order 02 already exists. |
| F-02 | The live corpus is ALREADY almost entirely addressable | Measured at HEAD `764442f7` over 38 specs: exactly TWO live specs carry no requirement id of any form (`25kzda` itself, which is section-addressed, and `kw5y2s`). 20 specs are live (excluding `implemented`/`superseded`). | The retrofit cost that `vkub9o` treated as the central objection is small at the requirement level, and smaller still once E-02's scoping is applied. |
| F-03 | The specs that can actually reach TRACE are the best-addressed subset | Of 12 `approved` specs, 10 carry requirement ids and 7 carry acceptance-criterion ids; the only `approved` spec with neither is `kw5y2s`. | `approved` is the ONE status that maps to `ACTION_PLAN`, so the population TRACE judges is not the whole corpus and is already largely conforming. |
| F-04 | Three ADDRESSING FORMS exist and they are not interchangeable | `vkub9o` 1.1 derived them from the files: FORM A letter-prefixed ids (many spellings of ONE scheme), FORM B bare dotted paragraph ids, FORM C numbered sections. Re-derived at HEAD `764442f7`: `7ckptx` uses `R<n>.<n>` with `A<n>` acceptance ids; `6m4kow` uses `AC-<n>`; `z7nbn1` uses 37 bare dotted ids and no letter-prefixed ones; `25kzda` uses 57 numbered sections and is cited BY SECTION in prose and in a code comment. | The convention must admit families or it invalidates most live specs. This is exactly why the spec must be written before the parser: the parser's input grammar is this decision. |
| F-05 | `vkub9o`'s decisive objection was the MISSING JOIN EDGE, and that objection does not reach TRACE-at-production | `vkub9o` 3.2 measured 0 plans carrying `- From-Spec: c4gd2h` against 37 mentioning it, and concluded "The blocker is the missing plan-to-spec edge, not the missing requirement parser." But the production dispatcher computes the produced plans itself: `runner_shared` discovers them by diffing against `baseline_plan_ids` and passes the resulting list into `spec_plan_conformance` and `spec_plan_gate_carry`. | The produced paths are IN HAND at the moment TRACE would run, so TRACE needs no pre-existing edge for the plans it judges. E-02 must confirm this by reading the code, because it is the hinge of the whole decision. |
| F-06 | `vkub9o` recommended AGAINST a parser, and that recommendation is corpus-wide, not production-scoped | `vkub9o` 5 item 3: "Do NOT build: a requirement parser, a plan-side requirement declaration field, a partial spec status, a requirements-outstanding attention view, or `implemented` computed from coverage." Its Q3 reasoning is "A view needs coverage data, coverage needs the edge, and the edge is missing exactly where it matters." | THIS MUST BE CONFRONTED, NOT IGNORED. The recommendation's stated premise is the missing edge and a corpus-wide view; neither holds for a check scoped to one dispatched spec with its produced plans in hand. The spec must record that reconciliation explicitly, or a reviewer will reasonably read this Set as contradicting approved research. |
| F-07 | The maintainer ruled AFTER the survey, and the ruling is what authorizes this work | `z7nbn1` OQ-02 as revised: "REVISED 2026-09-26 by the maintainer at spec review: `SPEC-PLAN-TRACE` is DEFERRED to backlog `vy20et` (a separate spec defining a requirement-ID convention and parser)". The review record `20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.review.md` SR-003 records the same. | The ruling directs a convention AND a parser as a separate spec. It does not direct the survey's Option B-minus, and it postdates the survey by six days. |
| F-08 | The "mandatory requirement" half of TRACE's pass criterion has NO agreed marker | `25kzda` 4.8 requires "Every MANDATORY spec requirement maps to at least one E item". Measured: `[Must]` markers appear in 10 specs of 38 and in only 2 of 12 `approved` ones (`2vev8j`, `5tapom`). Most specs express obligation in prose (`MUST`) with no per-id marker. | Without a marker, "mandatory" is unparseable and TRACE either treats EVERY id as mandatory or needs a new annotation. This is a real design question, so it is OQ-01. CORRECTED AT REVIEW: this cell read "and it is BLOCKING", contradicting OQ-01's own `- Blocking: no` field and its resolution; see F-12. It is substantive and non-blocking, because the decision is ratified at the SPEC REVIEW that this plan's deliverable goes on to receive, and the runner holds Order 02 on the spec reaching `approved` regardless. |
| F-09 | The acceptance-criterion half is structurally weaker than the requirement half | CORRECTED AT REVIEW (see F-13 for the measurement and the three specific errors); the authored breakdown read "5 use `AC`/`A`-prefixed ids ..., 5 have an acceptance section with NO ids ..., and 2 have no acceptance section". Re-measured over the 12 `approved` specs at review HEAD `36bcbfaa3`: SEVEN carry acceptance-like ids (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11, `2vev8j` 11, `25kzda` 4), FOUR have an acceptance section carrying no ids (`5tapom`, `kw5y2s`, `2lcqno`, `r07vma`), and ONE has no acceptance section (`77tr3o`). This agrees with F-03's independent "7 carry acceptance ids", which the authored F-09 contradicted. | TRACE's V-item half still fires on more specs than its E-item half (five of twelve lack usable acceptance ids against two lacking requirement ids), so the conclusion holds and in fact rests on a cleaner margin. The spec must decide this explicitly, which is why E-07 requires the grandfathered/no-ids case to be a PASS. E-01 must RE-DERIVE these figures rather than citing either version. |
| F-10 | The plan-side parse target already exists and needs no new grammar | `ipd_lint` parses a plan into `ParsedDoc` with `exec_leaves` and `valid_leaves` of type `Leaf`, each carrying `kind` ("E"/"V"), `ident` (e.g. "E-01"), `text`, and for V rows a `target`. | Order 02 reads plan-side E/V items through a shipped parser. The only NEW parsing is the spec side, which is what this spec defines. |
| F-11 | No pending plan contends for the files this plan touches | Measured at HEAD `764442f7`: this plan creates one new spec file and edits no existing one. Five pending plans declare a `25kzda` edit in scope (`00pirb`, `cpi6p3`, `mt54wr`, `6uhtko`, `4gx141`), which is why E-07 is written to DECIDE whether to amend `25kzda` rather than to amend it here. CORRECTED AT REVIEW: the parent `9wzlou`'s own review measured that same five-plan list as "partly false and stale" (`00pirb` has executed; `mt54wr` and `6uhtko` never declared that path, including at the cited HEAD; 13 pending plans declare it now). The CONCLUSION is unaffected and in fact strengthened, since more plans contend for `25kzda` than this row claims, so E-07's adopt-rather-than-amend recommendation stands on a larger margin. RE-DERIVE the co-editor list at execution rather than citing either figure. | No `- Item-Dependencies:` edge is owed, and the Set avoids a contended file. If E-07 concludes `25kzda` must be amended, that amendment belongs to a separate declared change, not to this plan. |
| F-12 | ADDED AT REVIEW: THE PLAN CONTRADICTED ITSELF ON WHETHER OQ-01 BLOCKS, IN THE DIRECTION THAT WOULD HAVE STOPPED THE PLAN. OQ-01 carries `- Blocking: no` and a resolution arguing at length that blocking "would demand the decision TWICE from the same human", yet THREE other sites asserted the opposite: F-08's cell ("it is OQ-01 and it is BLOCKING"), and the gate's paragraph ("OQ-01 IS BLOCKING ... this plan is not ready to execute until the maintainer answers"). The FIELD is what the machinery reads, so the prose asserted a stop nothing implements; and a reviewer who resolved the contradiction the other way would have made `aw ipd lint` report `IPD-Q501` at every checkpoint, holding a plan its own author judged non-stopping. | `- Blocking: no` at OQ-01 versus the two prose sites, all four quoted. The non-blocking reading is CORRECT on measurement: the deliverable ships at `to-review`, cannot reach `approved` without `--by-human`, and Order 02 is additionally held by the `state:spec:approved:<id6>` edge E-09 writes, which `runner_shared.edge_satisfied` enforces with "spec <id6> is <actual>, needs exactly 'approved'". Resolved by correcting the prose, not the field. |
| F-13 | ADDED AT REVIEW: F-09's ACCEPTANCE-ID BREAKDOWN IS WRONG IN THREE PLACES, and E-07's grandfathered-PASS requirement rests on it. F-09 says 5 approved specs use `AC`/`A`-prefixed ids, 5 have an acceptance section with NO ids, and 2 have no acceptance section. Re-measured over the 12 `approved` specs: SEVEN carry acceptance-like ids (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11, `2vev8j` 11, and `25kzda` 4), FOUR have an acceptance section with no ids (`5tapom`, `kw5y2s`, `2lcqno`, `r07vma`), and ONE has no acceptance section (`77tr3o`). The specific errors: `2vev8j` is listed as having no ids but declares 11 `AC-N` rows in a table; `25kzda` is listed as having no acceptance section but carries 4 `A<n>:` rows (in a table, not under an acceptance heading, which is why both halves of its classification need care); and the totals therefore mis-sum. | Re-measured at review HEAD `36bcbfaa3`. `2vev8j` line 122 onward: `\| AC-1 \| C1 \| A reader of any artifact's history...`, 11 such rows by count. `25kzda`: `\| A1: scope violation discipline \| ...`, 4 rows, with no `## .*[Aa]cceptance` heading. F-03's separate "7 carry acceptance ids" figure is CORRECT and F-09 disagrees with it, which is the internal inconsistency this row resolves in F-03's favour. |
| F-14 | ADDED AT REVIEW: V-09 PINS A STALE SUITE BASELINE AND THE SUITE IS NOT GREEN, so the comparison V-09 demands cannot be made as written. V-09 requires confirming "the after-minus-before failing node-ID set is empty against the authoring baseline `3387 passed, 2 skipped` at HEAD `764442f7`". Measured at review HEAD `36bcbfaa3`: bare `python3 -m pytest` reports `1 failed, 3446 passed, 2 skipped`. The count moved by 59 tests, and there is ONE pre-existing failure, `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed time-dependent local-versus-UTC history-clock defect owned by backlog `fnb8pl` (`open`, `bug`, `Blocks-Release: next`), unrelated to this plan. An executor comparing against the authored absolute would read ordinary growth as a discrepancy, and one comparing against "empty failing set" would stall on another item's defect. | Measured at review; `.aw/records/backlog/open/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md`. |
| F-15 | ADDED AT REVIEW: E-09 EDITS A FILE THIS PLAN DOES NOT DECLARE, which is legal but must be stated or the finalize scope gate will prompt for it. E-09 writes Order 02's `- Item-Dependencies:` via `aw ipd dependencies set rtvdak ...`, touching `.aw/records/plans/pending/20260930-reqids-02-rtvdak-...ipd.md`. That path is NOT matched by either declared scope entry. It does NOT cause a commit refusal, because `ipd_lifecycle._is_implicitly_allowed` returns True for it via the implicit allowance `.aw/records/plans/**`, so `aw commit` permits it. But `aw ipd finalize` reconciles what was actually changed against what was declared, so the executor will owe a `--scope-reason` for it. | Measured: `_scope_match` returns False for that path against both declared entries, while `_is_implicitly_allowed(path, plan_rel)` returns True and `ipd_schema.scope_paths_implicit_allowances()` returns `('.aw/records/plans/**', '.aw/records/plans/INDEX.md', '.aw/records/**/index.md')`. Also measured: the declared `.aw/records/specs` directory entry DOES match a new spec at `specs/draft/...` and at `specs/to-review/...`, so the spec half of the scope is correct. |
| F-16 | ADDED AT REVIEW: E-06 SAYS "FIVE FEATURES" AND THEN LISTS SIX, and its sibling conventions bullet lists five different ones, so an executor cannot tell which set is real. Re-measured: `config.KNOWN_FEATURE_CUTOVERS` registers SIX keys (`spec_id6`, `dependency_schema`, `carrier_obligations`, `setid_length`, `prompt_id6`, `walkthrough_id6`), while THIS repository's `.aw/config/project.json` `cutovers` stamps FIVE (all but `setid_length`). So both numbers appear in the plan and both are defensible against different things, which is exactly why neither should be quoted without saying which it counts. | `config.py` block comment plus the six keys; `json.load('.aw/config/project.json')['cutovers']` returns the five stamped keys. The block comment itself says "three shipped features use this one", which is a third stale figure in the same place, so the count is drifting in the SOURCE too and is not a safe thing for a spec to restate. |

## Proposed changes (ordered, validatable)

1. Re-measure the corpus and the TRACE code path at execution HEAD (E-01, E-02), correcting F-02, F-03 and F-05 in writing if they have moved.
2. Create the spec with `aw specs new` and write the convention: requirement namespace admitting prefixed families, a distinct acceptance namespace, the declaration-site rule, and the addressing rationale (E-03).
3. Write the retrofit/grandfathering policy onto the existing cutover mechanism, naming the feature key and stating grandfathering's cost (E-06).
4. Write the TRACE contract: production scope, severity reconciled with `25kzda` 4.8, grandfathered-spec pass, and the citation-not-implementation limit (E-07).
5. Move the spec to `to-review` with the setter and record the handoff, asserting no review or approval (E-08).

## Deferred / out of scope (with reason)

- THE PARSER AND THE CHECK ITSELF. Building both in one plan would hardcode the convention in code and make the maintainer's approval of the design unreviewable separately from its implementation.
  - Carrier: rtvdak
- RETROFITTING ANY EXISTING SPEC's REQUIREMENT IDS. `vkub9o` Q5 recommends going forward with the live prose-only specs left alone, and E-06 records that as POLICY rather than performing it. Retrofitting would edit approved specs' requirement text, which this plan is forbidden to do.
  - Carrier-Declined: This is a SETTLED POLICY DECISION recorded in the spec, not deferred work: E-06 writes "going forward, pre-cutover specs are grandfathered per spec" as the answer, so there is no outstanding obligation for a carrier to hold. Reopening it would mean overriding `vkub9o` Q5 and editing approved specs' requirement text.
- AMENDING `25kzda` 4.8. E-07 DECIDES whether an amendment is owed and records the answer; it does not perform one. Five pending plans already declare `25kzda` edits, so an unnecessary sixth would contend for the repository's most-reviewed contract file.
  - Carrier-Declined: The DECISION is a deliverable of this plan (E-07, validated by V-07), not deferred work. If E-07 concludes AMEND, the spec names the carrying plan and that plan owns the edit; if it concludes ADOPT (the recommendation, per OQ-02), no amendment is ever owed. Either way nothing outstanding survives this plan unrecorded.
- A REQUIREMENTS-OUTSTANDING `aw attention` VIEW, A PARTIAL SPEC STATUS, A PLAN-SIDE REQUIREMENT DECLARATION FIELD, AND `implemented` COMPUTED FROM COVERAGE.
  - Carrier-Declined: All four are `vkub9o` Option C, which that survey RECOMMENDS AGAINST on costs this Set does not disturb: a `SPEC_STATUSES` change is pinned by totality tests, and an `implemented` computed from plan-side declarations inverts `APPROVAL_FLOOR`'s explicit refusal to verify semantically. A rejected option is not an outstanding obligation; should the maintainer later want it, `vkub9o` is the durable record of the costing.
- CLOSING BACKLOG `vy20et` AS `done`.
  - Carrier-Declined: Not an obligation but a PROHIBITION. The runner sets the item `graduated` on verification, and `done` would claim code that Order 02 has not yet written. The item itself remains the durable record until Order 02 executes.

## Scope check

- Over-scope: none, BUT ONE EDIT IS UNDECLARED AND MUST BE JUSTIFIED AT FINALIZE RATHER THAN FORGOTTEN (F-15). This plan writes one new spec file and this plan file, and it edits no source, no test, and no existing spec. E-09 ALSO writes Order 02's `- Item-Dependencies:` through `aw ipd dependencies set`, which touches `.aw/records/plans/pending/20260930-reqids-02-rtvdak-...ipd.md`. That path matches neither declared entry. Measured, it does NOT cause a commit refusal, because `ipd_lifecycle._is_implicitly_allowed` admits it under the implicit allowance `.aw/records/plans/**`; but `aw ipd finalize` reconciles actual against declared, so a `--scope-reason` is owed for it. Supply "Order 02's approval edge can only be written once E-03 mints the spec id6; the Set parent's review (`9wzlou`, Cross-IPD validation SECOND) assigns this write to Order 01 E-09." DO NOT add the path to `- Scope-Paths:` to silence this: D141 freezes the declaration to preserve the said-versus-did signal, and the implicit allowance plus a stated reason is the sanctioned route. Measured separately and in the plan's favour: the declared `.aw/records/specs` directory entry DOES match a new spec under both `specs/draft/` and `specs/to-review/`, so the setter's relocation in E-09 stays in scope.
- Under-scope: the convention is written but NOT enforced by this plan, and the spec ships at `to-review` rather than `approved`, so nothing in the repository behaves differently when this plan finishes. That is deliberate on two counts: an agent may not approve a spec, and Order 02 is gated on the approval rather than on the authoring. The visible consequence is that `z7nbn1` 4.4's deferral remains open until Order 02 executes, which E-08 requires be stated so nobody mistakes a written convention for a shipped check.

## Required tests / validation

NO AUTOMATED TEST IS ADDED OR CHANGED BY THIS PLAN, because it ships no code. The validation is
therefore documentary and structural, and each V item below names the artifact or command output that
settles it. The suite is still run bare (`python3 -m pytest`) once, as a regression guard proving a
records-only change moved nothing: a NEW failing node id would mean this plan touched something it did not
declare. READ IT AS A DELTA AGAINST A SELF-MEASURED BASELINE, NOT AGAINST AN AUTHORED COUNT AND NOT AS A
GREEN BAR (F-14): the authored `3387 passed` figure is stale (`3446` at review), and the suite carries one
pre-existing unrelated failure owned by backlog `fnb8pl` which must be named rather than investigated,
fixed, or counted against this plan. `aw check` must also report no finding against the new spec,
which is the deterministic structural gate on the artifact this plan produces.

## Spec / documentation sync

THIS PLAN'S ENTIRE DELIVERABLE IS A SPEC, so the sync question is which OTHER artifacts must point at
it. Three, and each is handled explicitly. (1) `z7nbn1` 4.4 and its OQ-02 name backlog `vy20et` as
TRACE's owner; the new spec must cite `z7nbn1` 4.4 as the deferral it answers, and E-08 records that
the deferral is not DISCHARGED until Order 02 executes. (2) `25kzda` 4.8 already specifies TRACE's
pass criterion, message template and Action column; E-07 decides adopt-or-amend explicitly and the
new spec states the direction in its relations section, following the precedent that `z7nbn1` 0.2
states its own `25kzda` relationship with the direction named. (3) Research `vkub9o` recommended
against a parser; the new spec must cite it and record the reconciliation from F-05 and F-06, because
a spec that silently contradicts an in-tree survey leaves the next reader unable to tell which is
current. NO `.spec.md` OTHER THAN THE NEW ONE IS EDITED, which is why `- Scope-Paths:` names the
`.aw/records/specs` directory rather than any existing spec file.

## Open questions

### OQ-01: How is a "mandatory" spec requirement identified, given that no marker is in general use?

- Blocking: no
- Status: resolved
- Owner: maintainer (ratifies at spec review, not at plan execution)
- Resolution or deferral rationale: `25kzda` 4.8's pass criterion is "Every MANDATORY spec requirement maps to at least one E item", so TRACE cannot be BUILT without an answer. Measured (F-08): `[Must]` appears in 10 of 38 specs and in only 2 of 12 `approved` ones, so an annotation-based reading would exempt most specs silently. THREE OPTIONS. (a) EVERY declared requirement id is mandatory unless explicitly marked optional; needs no retrofit, but makes TRACE strictest on the best-documented specs, since a spec declaring 45 ids (`6kwd2e`) would need all 45 cited. (b) Adopt the existing `[Must]` marker as the discriminator; matches a real in-tree convention, but on today's corpus it would make TRACE near-vacuous for 10 of 12 `approved` specs, i.e. a check that passes by default. (c) Require the PRODUCING SPEC to declare its mandatory set explicitly and locally. RESOLVED AS (a), with an explicit optional-marker opt-out, on two pieces of repository evidence rather than on taste: option (b) is measurably vacuous on the exact population TRACE judges (F-08, F-03), and this repository has already recorded that a rule which cannot fire "would red every run and teach readers to ignore it" as the failure mode that usually decides such questions (`vkub9o` Option B). Option (a) fails CLOSED, which is the direction every comparable gate here takes. WHY THIS DOES NOT BLOCK EXECUTION, which is the substantive point and not a convenience: this plan's ONLY deliverable is a spec that ships at `to-review` and that CANNOT reach `approved` except by human attestation (`aw spec set approved --by-human`), and Order 02 is gated on that approval. So the maintainer's ratification point is the spec review, where E-08 will have placed this question, its three options and this recommendation in the spec's OWN open-questions section for exactly that purpose. Blocking this plan would demand the decision TWICE from the same human and stall the authoring that surfaces it. If the maintainer prefers (b) or (c) at spec review, the spec changes and no plan is re-authored, because nothing downstream has been built yet.

### OQ-02: Does the spec ADOPT `25kzda` 4.8's TRACE row verbatim, or AMEND it?

- Blocking: no
- Status: resolved
- Owner: maintainer (ratifies at spec review, not at plan execution)
- Resolution or deferral rationale: `25kzda` 4.8 already fixes TRACE's pass criterion, message template and Action column (`RETRY, then FAIL ITEM`). The three shipped siblings ADOPTED their rows verbatim, quoting them in docstrings under "Pass criterion (25kzda 4.8):", so precedent favours adoption. RESOLVED AS ADOPT, with the new spec adding only what `25kzda` does not state (the id convention, the grandfathered-spec pass, the honest limit). The reasoning is asymmetric reversibility: adopting changes no existing contract, whereas amending `25kzda` touches the contract every runner plan is reviewed against, and five pending plans already queue edits to that one file (F-11). E-07 records the decision and V-07 requires it be quoted, so it is auditable rather than implicit. AS WITH OQ-01, the maintainer's ratification point is the SPEC REVIEW: E-08 places this question, its options and this recommendation in the spec's own open-questions section, and the spec cannot reach `approved` except by human attestation. Blocking here would demand the same decision twice from the same human.

### OQ-03: Does the convention bind FORM C (section-addressed) specs, or only id-declaring ones?

- Blocking: no
- Status: resolved
- Owner: maintainer (ratifies at spec review, not at plan execution)
- Resolution or deferral rationale: `25kzda` itself is section-addressed (57 numbered sections, cited as "`25kzda` 2.9" in prose and as "spec 2.1's 0..10 bound" in a code comment) and `z7nbn1` states every normative clause as a bare dotted paragraph id (37 measured at HEAD `764442f7`, with zero letter-prefixed ones). `vkub9o` 2.2 notes that for such specs "retrofit may mean DECLARING AN EXISTING SCHEME CANONICAL rather than minting parallel ids". RESOLVED AS ADMIT: dotted section/paragraph ids are a legitimate requirement namespace, because two of the repository's most load-bearing specs already depend on it and refusing it would either invalidate them or force parallel ids nobody cites. E-01's census measures how much of the corpus this covers and E-04 writes the answer. AS WITH OQ-01 AND OQ-02, ratification is at the SPEC REVIEW via E-08, not here; the spec cannot reach `approved` without human attestation, and Order 02 is gated on that approval.

### OQ-04: Was the OQ-01 blocking contradiction resolved by correcting the prose or by setting the field?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: BY CORRECTING THE PROSE, and this is recorded as a question rather than buried in a diff because it is the single most consequential judgement this review made: the two readings differ by whether the plan can execute at all. The contradiction is measured at F-12: OQ-01 carries `- Blocking: no` with a resolution arguing at length for that, while F-08's cell and the gate's paragraph both asserted it BLOCKS and the gate added "this plan is not ready to execute until the maintainer answers". RESOLVED IN FAVOUR OF `no` on three pieces of repository evidence. (1) THE AUTHOR'S OWN REASONING IS SOUND AND MEASURED: the deliverable is a spec shipping at `- Status: to-review`, which cannot reach `approved` except by `aw spec set approved --by-human`, and E-08 places the question in that spec's own open-questions section, so the human decides once, at the spec review, where the authority sits. (2) THE RUNNER ENFORCES THE GATE INDEPENDENTLY: E-09 writes `state:spec:approved:<id6>` onto Order 02, and `runner_shared.edge_satisfied` refuses the dependent with "spec <id6> is <actual>, needs exactly 'approved'", so Order 02 cannot consume an unratified decision even if this plan executes. (3) THE COST OF THE OTHER READING IS CONCRETE: setting `- Blocking: yes` makes `aw ipd lint` report `IPD-Q501` at EVERY checkpoint including `author`, which would hold a plan whose only output is the artifact that surfaces the question for decision, and the maintainer ruling of 2026-09-10 (plan `qhy3i3` OQ-01) is explicit that the `- Blocking:` flag exists precisely to record which questions must stop work. THE ALTERNATIVE REJECTED, stated so it can be overruled: set the field to `yes` and hold the plan. That is defensible if a maintainer wants the marker question settled before any convention is written down, and it costs only latency; a reviewer or maintainer who prefers it should say so, since the recommendation in OQ-01 (option (a), fail-closed) would then be answered first and E-04 and E-07 would write a settled rule rather than a recommendation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the census script text AND its full output, showing the recursive spec count, the live subset, the per-spec requirement/acceptance id shapes, and the live specs carrying no requirement id. Then state explicitly whether F-02 (2 live specs with no requirement id) and F-03 (10 of 12 `approved` carry requirement ids, 7 carry acceptance ids) HOLD, and if not, paste the corrected numbers and say which plan claims they invalidate.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `_SPEC_ACTIONS` mapping as read from `run_selection_policy`, showing which statuses map to `ACTION_PLAN`. Paste the `findings.extend` block from the production call site in `runner_shared` showing what the three verifiers receive, plus the lines that compute the produced plan list against `baseline_plan_ids`. State in one sentence whether the produced paths are in hand when the verifiers run, i.e. whether F-05 holds. If it does NOT hold, the plan must say what that does to E-07.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw specs new ... --apply` command and its full output, proving the tool minted the name and id6 rather than a hand edit. Paste `ls` of the created path and the spec's front matter, confirming `- Status: draft`, that the filename matches `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`, and that `- Id:` equals the id6 embedded in the filename.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: quote the spec's sentences stating the requirement namespace and the families it admits, and separately the sentences stating the acceptance-criterion namespace. Confirm the two namespaces are stated as DISTINCT and quote the census numbers the spec cites for each, showing they are E-01's measured figures rather than this plan's authoring numbers.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: quote the declaration-site rule verbatim, and quote the addressing rationale showing it names `vkub9o`'s measured addressing-failure cases. Confirm the rule distinguishes a DECLARED id from a MENTIONED one in terms a parser could implement.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: quote the retrofit section's sentences naming the cutover FEATURE KEY, the per-spec grandfathering rule against the stamped boundary, the going-forward decision for the live prose-only specs, and the stated COST of grandfathering (that a reader cannot distinguish conforming from exempt). Then prove this plan changed no code: paste `git diff --stat` for the commit showing only `.aw/records/` paths, and confirm `agent_workflows/config.py` is NOT among them.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: quote the TRACE contract section's sentences covering all four required elements: production scope (with the `_SPEC_ACTIONS` citation from E-02), severity and the explicit adopt-or-amend decision against `25kzda` 4.8's `RETRY, then FAIL ITEM` row, the grandfathered/no-ids PASS behavior, and the citation-not-implementation limit. The limit must be present in substance; quote it. If the decision was AMEND, quote the relations sentence declaring it and confirm no `25kzda` edit was made in this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: quote the spec's open-questions section in full for all three questions, showing for each the question text, the options considered, the recommended answer, and the measured evidence cited. Paste the sentence stating explicitly that these are agent recommendations awaiting human ratification. Then paste `grep -niE 'maintainer (ruled|ruling|decided)' <spec>` and confirm NO output asserting a ruling on OQ-01/02/03 (a citation of a PRIOR, real ruling such as `z7nbn1` OQ-02's 2026-09-26 revision is legitimate and must be distinguished in the report if it matches).
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the setter command and output moving the spec to `to-review`, then `ls` the spec's new path under `.aw/records/specs/to-review/` and paste its `- Status:` line and its newest `## Workflow history` entry. Paste `grep -nE '^- (Approval|Readiness):' <spec>` showing NO match (proving no forged attestation). Paste `aw check` (or `aw check specs`) output showing no finding against the new spec. Paste the bare `python3 -m pytest` summary line and compare it against a baseline THE EXECUTOR MEASURES ITSELF on this tree, by FAILING NODE ID: the bar is that no NEW failing node id appears. DO NOT compare against the authoring figure `3387 passed, 2 skipped`, which F-14 measures as stale (`3446 passed` at review), and DO NOT require an empty failing set: the suite carries one pre-existing unrelated failure, `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, owned by backlog `fnb8pl`. Name it as pre-existing, present in both runs, and neither investigate nor fix it. Then paste `git status --short` and the staged set, and for E-09's edit to Order 02's plan file state the `--scope-reason` supplied for it, since F-15 measures that path as undeclared-but-implicitly-allowed rather than in scope. Finally, quote this plan's history line stating that `z7nbn1` 4.4's deferral is addressed but NOT discharged until Order 02 executes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A DESIGN DECISION WRITTEN DOWN, AND NOTHING EXECUTABLE. This plan produces
one new spec at `to-review` and changes no code, no test, and no existing spec, so the repository
behaves identically before and after. What is being approved is the DIRECTION: that a spec requirement
gets a stable id drawn from the families the corpus already uses, that the policy is going-forward with
per-spec grandfathering on the existing cutover mechanism, and that `SPEC-PLAN-TRACE` is scoped to the
plans a spec production action just wrote rather than to the corpus.

THE ONE THING A REVIEWER SHOULD PUSH ON. This Set proceeds where in-tree research `vkub9o` recommended
"Do NOT build: a requirement parser". That is a real tension and it is not waved away: the maintainer's
ruling of 2026-09-26 postdates the survey by six days and directs "the convention and parser ... as its
own spec" (F-07), and the survey's decisive objection was a MISSING JOIN EDGE which does not reach a
check whose produced plan paths are already in hand (F-05). Both claims are re-measured by E-01 and
E-02 before anything is written, and if E-02 finds the paths are NOT in hand, the honest outcome is a
spec recording TRACE as still unbuildable. A reviewer who disagrees with the reconciliation should say
so now, because Order 02 builds against whatever this spec says.

OQ-01 IS SUBSTANTIVE BUT DOES NOT BLOCK THIS PLAN, AND THAT DISTINCTION IS LOAD-BEARING. Whether every
declared requirement is mandatory, or only `[Must]`-marked ones, decides whether TRACE is a gate or
decoration: on today's corpus the marker-based reading would make it near-vacuous for 10 of 12 `approved`
specs (F-08). The recommendation is the fail-closed option (a). WHAT IT DOES NOT DO IS STOP THIS PLAN, for
the reason OQ-01's own resolution states and F-12 measures: this plan's only deliverable is a spec that
ships at `- Status: to-review`, which cannot reach `approved` except by human attestation
(`aw spec set approved --by-human`), and Order 02 is held by BOTH an `executed:jjh4aj` edge and the
`state:spec:approved:<id6>` edge E-09 writes. So the maintainer's ratification point is the SPEC REVIEW,
where E-08 places the question, its three options and the recommendation. Blocking this plan would demand
the same decision twice from the same human and would stall the authoring that surfaces it.
CORRECTED 2026-09-30 AT REVIEW, because the contradiction was real and consequential: this paragraph read
"OQ-01 IS BLOCKING ... this plan is not ready to execute until the maintainer answers", while the question's
own `- Blocking:` field reads `no` and its resolution argues at length for exactly that. Two further sites
said the same (F-08's "it is OQ-01 and it is BLOCKING" and the Set parent's reading). The FIELD is what any
gate reads, so the prose was asserting a stop the machinery does not implement, and a reviewer resolving the
contradiction the other way (setting `- Blocking: yes`) would have made `aw ipd lint` report `IPD-Q501` at
every checkpoint and held a plan whose author had already judged it non-stopping. See F-12.

EXECUTION CONTRACT. Commit only the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>`;
never `git add -A`, never push, never `--no-verify`. Create the spec with `aw specs new --apply` and move
it with the status setter, never by hand and never with `git mv`. Write NO `- Readiness:` and NO
`- Approval:` field on any artifact, and do NOT set the new spec `reviewed` or `approved`: those are the
maintainer's, and `approved` is what gates Order 02. Do not edit backlog `vy20et`'s requirements and do
not set it `done`. Paste real command output in every `V-*`; a validation item without observed evidence
is not verified.

POST-GATE LIFECYCLE MOVE. When every `E-*` is performed and every `V-*` carries pasted evidence, run
`aw ipd lint --phase pre-transition` and confirm it reports conforming. Reaching
`.aw/records/plans/executed/` is then unconditionally owed, but its OWNER is conditional: under
`aw oc run` / `aw agy run` the RUNNER owns that transition, so do NOT invoke `aw ipd finalize` yourself in a
runner-driven execution; a HAND execution invokes it. Never hand-edit the status line and never hand-roll a
`git mv` to `executed/`. Note that finalize will ask about E-09's edit to Order 02's plan file, which is
undeclared-but-implicitly-allowed (F-15); the Scope check carries the `--scope-reason` to supply.
