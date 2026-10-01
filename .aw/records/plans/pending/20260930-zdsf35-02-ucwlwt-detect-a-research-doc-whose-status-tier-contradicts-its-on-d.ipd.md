# IPD: Detect a research doc whose status tier contradicts its on-disk tier

- Date: 2026-09-30
- Kind: child
- Concern: Nothing detects a research doc whose status tier disagrees with its on-disk tier, so the drift sibling `mg8bag` removes can silently return and no checker will say so.
- Scope: Add ONE status-versus-tier drift rule to `research_index.check_drift` (so it surfaces through both `aw research index --check` and `aw check research`), register its severity, and cover both directions with fixture-driven tests. No corpus move (that is `mg8bag`), no new verb, no change to any existing rule.
- Scope-Paths: agent_workflows/research_index.py, agent_workflows/check_engine.py, tests/test_research_index.py, .aw/records/research/README.md
- Item-Dependencies: executed:mg8bag
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: zdsf35
- Set: zdsf35
- Order: 2
- Highest E allocated: 05
- Author: opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us
- Id: ucwlwt

## Workflow history

- 2026-09-30 to-review (opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `zdsf35` as Order 02 of the Set, implementing the item's remedy part 2. `- Work-Kind: chore` and `- Priority: low` are INHERITED and correct; the item carries no `- Blocks-Release:` and this plan invents none. THE ITEM'S ORDERING ARGUMENT IS ADOPTED AND ENFORCED MECHANICALLY, not by prose: `- Item-Dependencies: executed:mg8bag` means the runner re-checks the edge at dispatch and marks this item `dependency-blocked` rather than shipping a rule that would report 35 findings on day one. THE ITEM'S CORE CLAIM VERIFIES: measured at HEAD `7000df73`, nothing detects a tier mismatch at all; `research_index.check_drift` emits exactly `check.stale-index-missing`/`-stale`, `dangling-citation`, `stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer` and `unrecognized-model`, and not one reads a document's DIRECTORY. ONE CORRECTION TO THE ITEM, which changes this plan's validation rather than its deliverable: the item implies the checker is clean today and a rule would redden it. It is NOT clean - `aw research index --check` already exits 1 on 61 `dangling-citation` plus 35 `adopted-without-consumer` findings - so "clean after the migration" is unachievable as a validation signal and V-04 compares PER-RULE counts instead, demanding zero findings for the NEW rule specifically. ONE DESIGN DECISION TAKEN ON EXISTING EVIDENCE rather than deferred: the rule is registered at `warning`, matching its nearest sibling `check.stale-index-stale`, because tier drift is real-but-non-answer-corrupting exactly as a stale manifest is; the item's own "WHY THIS IS A CHORE AND NOT A BUG" paragraph is the argument for not making it `error`, and `artifact_core.drift_exit_code` exempts only `info`, so `warning` still fails the gate as the item intends. THE PRIMITIVES THIS NEEDS ALREADY EXIST AND ARE REUSED, NOT RE-DERIVED: `research_contract.SHARDED_STATUSES`, `HOT_STATUSES`, `REFERENCE_DIR`/`ARCHIVE_DIR` and `normalize_status`, the same four `status_set._validate_target_status` consumes for the WRITE-side refusal that plan `4a8yws` shipped. That symmetry is the point: `4a8yws` refuses the write that would strand a doc, `mg8bag` fixes the already-stranded corpus, and this plan detects any future stranding however it arrives.

## Goal

Close the loop the item describes by making status-versus-tier disagreement MACHINE-DETECTABLE, in both directions, through the checker a maintainer already runs. After `mg8bag` has made the corpus consistent, this rule is what keeps it consistent: a doc hand-moved into a shard while still `active`, or a doc whose `status` is hand-edited to `reference` without moving, becomes a reported finding instead of residue someone measures by hand months later.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the premise still holds

- [ ] E-01 RE-VERIFY AT EXECUTION HEAD that (a) no existing rule detects a tier mismatch and (b) `mg8bag` has actually made the corpus consistent, before adding a rule whose whole value depends on both. For (a), enumerate the rule ids `research_index.check_drift` can emit and confirm none reads a document's directory; the authoring enumeration, to be re-derived, is `check.stale-index-missing`, `check.stale-index-stale`, `dangling-citation`, `stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`, plus the name/frontmatter classes from `_scan_docs`. For (b), re-run `mg8bag`'s census: count docs with a cold normalized status at the research root, and docs with a hot normalized status inside a `reference/` or `archive/` subtree. BOTH MUST BE ZERO. If the first is nonzero, STOP: the dependency edge was satisfied but the corpus was not, and shipping the rule now reports findings on real documents. Record both numbers.
  - Depends on: none
  - Expected outcome: the enumerated existing rule ids with a statement that none is directory-aware, plus both census numbers recorded as actually measured, with a STOP recorded rather than a workaround if either is nonzero.
  - Execution state: pending

### Task group 2: the rule

- [ ] E-02 ADD the status-versus-tier drift rule to `research_index.check_drift`, reusing the existing vocabulary rather than re-listing it. For each scanned entry, derive the on-disk tier from the FIRST path component of `DocEntry.path` (which `_doc_entry` already sets to the posix path relative to the research root): a path with no directory component is the HOT ROOT, and a first component equal to `research_contract.REFERENCE_DIR` or `ARCHIVE_DIR` is that COLD tier. Normalize the document's status through `research_contract.normalize_status` so a legacy `intake` doc reads as `todo`. Emit ONE finding per offending doc, in the two directions the item names: a doc whose normalized status is in `SHARDED_STATUSES` while it sits at the hot root, and a doc whose normalized status is in `HOT_STATUSES` while it sits inside a cold tier. Use a single rule id (so one grep finds both) and put the direction in the detail text, naming the status, the actual tier, and the expected one. Follow the module's established emission shape: place the new block inside `check_drift` ONLY (never in `_doc_entry` or `_scan_docs`), which is the convention the `unrecognized-model` block states explicitly so the regenerate branch of `run_index` is not blocked by it. Do NOT compute the shard MONTH here: month placement is `mg8bag`'s measured-clean direction and a separate concern; this rule judges TIER only.
  - Depends on: E-01
  - Expected outcome: a new drift rule emitting at most one finding per doc for either direction, reusing `SHARDED_STATUSES`/`HOT_STATUSES`/`REFERENCE_DIR`/`ARCHIVE_DIR`/`normalize_status` with no duplicated status literals, and emitted only from `check_drift`.
  - Execution state: pending

- [ ] E-03 REGISTER the new rule id in `check_engine.RULE_REGISTRY` at `warning` severity, with a comment stating WHY that tier was chosen and what registration buys. The reasoning to record: `artifact_core.drift_exit_code` exempts ONLY `info`, so `warning` fails the gate (which the item wants: it asks for a drift rule, not a nudge), while `error` would overstate a defect the item itself argues is a chore because readers key on status and no answer is wrong. The nearest precedent is `check.stale-index-stale`, also `warning`, also a real-but-non-answer-corrupting inconsistency. Note in the comment that an UNREGISTERED id falls through to `_DEFAULT_RULESPEC` at `error`, so registration here is a deliberate downgrade and not bookkeeping. Register whatever id-forms the emission path needs so the severity actually attaches (check whether the finding must be passed through `check_engine.enrich_drift` to carry its severity, as the `stale-index` and `unrecognized-model` blocks do, and do so if required).
  - Depends on: E-02
  - Expected outcome: the rule id registered at `warning` with the rationale recorded, severity demonstrably attached to an emitted finding, and the fall-through-to-`error` consequence named in the comment.
  - Execution state: pending

### Task group 3: prove it, both directions

- [ ] E-04 ADD fixture-driven tests to `tests/test_research_index.py` asserting the rule's BEHAVIOR, in the style the existing `check_drift` tests already use (a throwaway repo, a written doc, `check_drift`, assertions on rule id and severity). Cover five cases: (1) a cold-status doc at the hot root is flagged; (2) a hot-status doc inside a `reference/` shard is flagged; (3) the same inside an `archive/` shard is flagged; (4) a correctly-placed doc of each tier produces NO finding of this rule (the negative case, which is what proves the rule is not just always-on); (5) a legacy `intake`-status doc inside a cold shard is flagged, proving normalization is applied rather than a raw string compared. Assert the emitted SEVERITY is `warning` and that `artifact_core.drift_exit_code` returns 1 for a flagged fixture, mirroring `test_stale_index_detected`. Assert on the finding's rule id, severity, location and exit-code effect; do NOT assert on the exact wording of the detail string, and do NOT read production source with `inspect`/`ast`/regex or assert on symbol censuses or line counts.
  - Depends on: E-03
  - Expected outcome: five passing behavioral tests covering both directions, both cold tiers, the clean negative case, and status normalization, asserting rule id, severity and exit-code effect through real `check_drift` calls.
  - Execution state: pending

- [ ] E-05 DOCUMENT the new rule in `.aw/records/research/README.md` where that file already lists what `--check` fails on. The existing sentence enumerates "missing/invalid frontmatter, name vs frontmatter mismatch, a stale generated view, or a dangling citation"; extend it to include a status-versus-tier mismatch, in the file's own voice and without em or en dashes (this is user-facing prose). Keep it to the enumeration: the README already states the invariant itself one section earlier ("Hot states (`todo`/`active`) stay flat at this directory's root ... Cold states live in monthly `YYYYMM` shards"), so restating the rule would duplicate it. Name the remedy verb (`aw research promote`) so a reader who hits the finding knows the fix.
  - Depends on: E-04
  - Expected outcome: the README's `--check` enumeration includes the tier mismatch and names `aw research promote` as the remedy, with the invariant NOT restated and no em or en dash introduced.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE STATUS AND TIER VOCABULARIES ALREADY EXIST AND MUST NOT BE RE-LISTED. `research_contract` defines `STATUSES`, `HOT_STATUSES`, `SHARDED_STATUSES`, `STATUS_NORMALIZATIONS`, `REFERENCE_DIR` and `ARCHIVE_DIR`. `status_set._validate_target_status` already consumes exactly this set for the WRITE-side refusal, including the first-path-component test this rule needs, so a second hardcoded copy would be the desync GUIDING_PRINCIPLES P8 forbids. `research_index` already imports the module as `R`.
- A NEW DRIFT RULE BELONGS IN `check_drift`, NOT IN `_doc_entry` OR `_scan_docs`. The `unrecognized-model` block states the reason inline: emitting from `check_drift` only keeps the REGENERATE branch of `run_index` from refusing to write the manifest, since that branch treats any `_scan_docs` drift as a reason to refuse.
- SEVERITY IS STAMPED AT THE EMITTER FOR THIS MODULE'S RULES. The `stale-index` block imports `check_engine` as `_ce` and wraps its findings in `_ce.enrich_drift`, with a comment recording WHY: neither `run_index` nor `check_engine.check_content` enriches these findings, so an un-enriched `severity=""` would still fail the gate. A new rule must follow that pattern to carry its registered severity.
- `drift_exit_code` EXEMPTS ONLY `info`. `artifact_core.drift_exit_code` returns 1 if any finding's severity is not `info`, and treats a legacy 3-field `Drift` (empty severity) as failing. So `warning` fails the gate and `info` would not.
- AN UNREGISTERED RULE ID DEFAULTS TO `error`. `check_engine` falls through to `_DEFAULT_RULESPEC`, so omitting the registry entry would make this rule gate harder than intended rather than not gate at all.
- `aw research index --check` IS ALREADY FAILING AT HEAD, so "clean" is not an available validation signal: 61 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, 2 `check.stale-index-missing` (`info`). Validation must be per-rule.
- TESTS MUST EXERCISE BEHAVIOR, NEVER CODE STRUCTURE. The execution contract forbids tests that read production source with `inspect`/`ast`/regex, assert on caller counts or symbol censuses, or pin docstrings. The existing `check_drift` tests are the model: build a throwaway repo, write a doc, call `check_drift`, assert on rule ids, severities and `drift_exit_code`.

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-01 | n/a | THE ITEM'S PREMISE VERIFIES: no existing rule is directory-aware. `check_drift` emits only the manifest, citation, stale-hot-state, provenance and model rules; none inspects a document's path components. The item's scratch-repo measurement ("a scratch repo clean before a stranding write is still `index --check: clean` after it") is consistent with this. | The deliverable is genuinely new detection, not a severity or wording change to an existing rule. |
| F-02 | MEDIUM | THE ITEM IMPLIES A CLEAN CHECKER AND THE CHECKER IS NOT CLEAN. `aw research index --check` exits 1 at HEAD on 61 `dangling-citation` plus 35 `adopted-without-consumer` findings, with 17 `stale-state-to-promote` besides. | "Clean after the migration" is unachievable as a validation signal. V-04 must demand zero findings FOR THE NEW RULE and show the other rules' counts unchanged, or it would fail on pre-existing drift and invite someone to weaken it. |
| F-03 | MEDIUM | THE 35 `adopted-without-consumer` FINDINGS COINCIDE IN COUNT WITH THE 35 STRANDED DOCS BUT ARE NOT THE SAME SET: the overlap is 17, and 18 of them sit on docs already in shards. | A validation matching on the number 35 could mistake one rule's findings for the other's. Per-rule grouping is required, not a total. |
| F-04 | LOW | THE WRITE-SIDE REFUSAL ALREADY SHIPPED AND COVERS ONLY ONE DIRECTION THROUGH ONE DOOR. `status_set._validate_target_status` refuses `aw set` on a research doc when the target status is in `SHARDED_STATUSES`, and separately refuses a `HOT_STATUSES` target when the record's first path component is `reference`/`archive` (the `4a8yws` E-02 guard). | The gap this plan fills is precisely stated: a WRITE through `aw set` is refused, but a hand edit, a hand `git mv`, an external tool, or a merge can still produce the state, and nothing reports it AT REST. This rule is the at-rest counterpart, which is why it belongs in the checker rather than in another refusal. |
| F-05 | LOW | THE FIRST-PATH-COMPONENT TEST IS THE RIGHT TIER DERIVATION AND HAS PRECEDENT. `status_set` computes `rel.parts[0]` relative to the resolved research root and compares against `REFERENCE_DIR`/`ARCHIVE_DIR`; `DocEntry.path` is already the posix path relative to the research root, so the same derivation is one split away. | No new path plumbing is needed, and the two sides of the invariant derive the tier the same way. |
| F-06 | LOW | EVERY INDEXED DOC IS EITHER AT THE ROOT OR UNDER `reference/`/`archive/`. Measured: of 124 indexed entries, 60 at the root, 32 under `reference`, 32 under `archive`, and ZERO under any other subdirectory. A legacy `opencode/...` subdirectory exists in the tree but contains only a `README.md`, which `_doc_entry` skips. | The rule needs no third "unknown tier" branch today. It should still not CRASH on one; treating any non-cold first component as not-a-cold-tier is sufficient and keeps the rule silent on an unexpected layout rather than guessing. |
| F-07 | LOW | `warning` IS THE DEFENSIBLE SEVERITY AND THE ALTERNATIVES ARE BOTH WRONG. `info` would not fail the gate (`drift_exit_code` exempts it), which contradicts the item's request for a drift rule; `error` (the fall-through default for an unregistered id) would outrank the item's own chore classification. `check.stale-index-stale` is `warning` for the same shape of defect. | E-03 registers `warning` deliberately and records the reasoning, so a later reader does not "fix" it in either direction. |
| F-08 | LOW | THE DEPENDENCY EDGE IS LOAD-BEARING AND IS ENFORCED, NOT ADVISORY. `- Item-Dependencies: executed:mg8bag` is re-checked at dispatch by the runner, which marks this item `dependency-blocked` and continues rather than failing the run. | The item's "it must come second" is mechanical rather than a note an executor could overlook. E-01 still re-measures the corpus, because a satisfied edge proves the plan executed, not that the corpus is clean. |

## Proposed changes (ordered, validatable)

1. Re-verify that no rule is directory-aware and that `mg8bag` left the corpus tier-consistent (E-01; F-01, F-08).
2. Add the two-direction status-versus-tier rule to `check_drift`, reusing the existing vocabulary (E-02; F-01, F-05, F-06).
3. Register the rule at `warning` with its rationale, ensuring the severity attaches (E-03; F-07).
4. Cover both directions, both cold tiers, the clean negative, and status normalization with behavioral tests (E-04; F-04, F-06).
5. Extend the README's `--check` enumeration and name the remedy verb (E-05).

## Deferred / out of scope (with reason)

- THE CORPUS MIGRATION. Owned by sibling `mg8bag` (Order 01), which this plan declares a hard `executed:` edge on. Shipping detection before the migration would report 35 findings on real documents, which is the item's stated reason for the ordering.
  - Carrier: mg8bag
- SHARD-MONTH VALIDATION (is a sharded doc in the month its `created` implies?). Out of scope: measured clean in both plans (64 of 64 sharded docs match their `created` month, 0 mismatches), so there is no defect to detect, and bundling a second predicate into this rule would make a single finding ambiguous between tier and month.
  - Carrier-Declined: Nothing is owed. A carrier would assert there is work to do on a direction measured clean twice; if a month mismatch ever appears, the honest trigger is that measurement, not a standing obligation filed now.
- WIRING THE RULE INTO A PRE-COMMIT HOOK. Out of scope: the rule surfaces through `aw research index --check` and `aw check research` (and so through CI), which the item asks for. A local hook is skippable with `--no-verify` and is not cloned, so it would add a weaker surface rather than a stronger one.
  - Carrier-Declined: Nothing is owed. The portable authority is the `aw check` surface this plan already lands on; the README itself notes `--check` "is wireable into a pre-commit or CI gate", so wiring remains available to a maintainer without an outstanding obligation.
- THE PRE-EXISTING `dangling-citation` AND `adopted-without-consumer` FINDINGS (F-02). Out of scope: they predate this Set, concern citation resolution and `consumed-by` provenance rather than tier, and reducing them is a separate curation judgement per document.
  - Carrier-Declined: Nothing is owed by this plan. They are recorded here only because they make "clean" unavailable as a validation signal (V-04 handles that), not as work this plan displaces.
- `- Work-Kind: chore` IS INHERITED AND IS CORRECT. The rule prevents a future inconsistency and corrects no wrong answer; readers key on frontmatter status. No release gate attaches.
  - Carrier-Declined: Nothing is owed. This row records an inherited classification, not deferred work.

## Scope check

- Over-scope: none. `check_engine.py` is touched for the registry entry only, and `.aw/records/research/README.md` for the `--check` enumeration only; both are required for the rule to carry its intended severity and to be discoverable.
- Under-scope: shard-month validation and hook wiring are both excluded with reasons above. The rule detects tier disagreement; it does not REPAIR it (the remedy stays the deliberate `aw research promote`, consistent with spec `5tapom` Section 4's rule that ongoing drift is REPORTED and remediated deliberately, never auto-mutated).

## Required tests / validation

New behavioral tests in `tests/test_research_index.py` (E-04), following the existing `check_drift` test style: a throwaway repo, a written fixture doc, a real `check_drift` call, assertions on rule id, severity, location and `artifact_core.drift_exit_code`. Five cases: cold-status-at-root flagged; hot-status-in-`reference/` flagged; hot-status-in-`archive/` flagged; correctly-placed docs of both tiers producing no finding of this rule; and a legacy `intake` doc in a cold shard flagged, proving normalization.

Plus the whole bare suite (`python3 -m pytest`) with its actual summary pasted, and a per-rule before/after comparison of `aw research index --check` on the real corpus (V-04) showing zero findings for the NEW rule and unchanged counts for every pre-existing rule.

## Spec / documentation sync

One README edit is in scope and declared: `.aw/records/research/README.md`'s enumeration of what `--check` fails on (E-05).

NO SPEC AMENDMENT IS REQUIRED, and the reason is specific rather than an absence: spec `5tapom` Section 5 item 2 already enumerates the drift classes `--check` must flag, and Section 4 already states that ongoing drift is REPORTED by `--check` and remediated deliberately. This rule is an instance of that existing contract applied to a layout invariant the research README already mandates, not a new contract. No `.spec.md` path appears in `- Scope-Paths:` and none is edited. Were a reviewer to judge that the enumerated drift list in `5tapom` Section 5 is exhaustive rather than illustrative, the correct response is to amend that list in this same change and declare the spec path; the author's reading is that Section 4's general reporting rule governs, which is why no amendment is proposed.

## Open questions

### OQ-01: Should the rule be one id covering both directions, or two ids?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED as ONE id with the direction in the detail text, decided on in-repo evidence rather than preference. The precedent cuts both ways and the distinguishing factor is measurable: `check.stale-index-missing` and `-stale` were deliberately SPLIT, and the comment in `research_index` records why, namely that the two needed DIFFERENT SEVERITIES (`info` for a never-generated manifest, `warning` for a stale one). Here both directions are the same defect at the same severity with the same remedy verb, so splitting would buy nothing and would halve the value of a grep for the invariant. Measurement supports it too: the reverse direction has ZERO instances in the corpus, so a second id would ship permanently unexercised against real data. If a future maintainer needs to gate the directions differently, the split is mechanical and the severity difference would then be the justification, exactly as it was for the manifest rules.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the enumerated rule ids `check_drift` can emit, with an explicit statement that none derives a tier from a document's path, plus both census numbers (cold-status-at-root, hot-status-in-cold-shard) pasted as measured. BOTH must be zero before proceeding; if either is not, paste the STOP and the investigation rather than a workaround.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the diff of the new `check_drift` block, plus a demonstration on a THROWAWAY fixture (not the real corpus) that both directions produce exactly one finding each, with the detail text naming the status, the actual tier and the expected one. Confirm the status vocabulary is referenced through `research_contract` symbols with no new hardcoded status or directory literal (paste the relevant diff lines), and confirm the emission is inside `check_drift` only by showing `aw research index` still REGENERATES the manifest on a fixture containing a tier-mismatched doc.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `RULE_REGISTRY` diff showing `warning` plus the recorded rationale, AND proof the severity actually attaches to an emitted finding (paste the finding's `severity` field from a fixture run, not the registry entry alone, since the module's own comment warns an un-enriched finding carries `severity=""`). Also show `artifact_core.drift_exit_code` returns 1 for that fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the actual output of the new tests run by name, plus the bare `python3 -m pytest` summary line pasted verbatim. AND the per-rule corpus comparison: `aw research index --check` findings grouped by rule BEFORE and AFTER this change, showing ZERO findings for the new rule id on the real corpus and UNCHANGED counts for every pre-existing rule. State that the overall exit code remains 1 both times because of pre-existing `dangling-citation`/`adopted-without-consumer` findings, so a reader does not read the failing gate as a regression. Confirm no new test reads production source with `inspect`/`ast`/regex and that none asserts on symbol censuses, caller counts, or line counts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the README diff, with a check that the enumeration now includes the tier mismatch and names `aw research promote`, that the invariant sentence one section earlier is UNCHANGED (no duplication), and that no em or en dash was introduced (paste a grep for both characters over the changed lines returning empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and must not be executed by the agent that authored it in the same turn.

IT ALSO CANNOT EXECUTE UNTIL `mg8bag` IS EXECUTED. `- Item-Dependencies: executed:mg8bag` is re-checked at dispatch; an unmet edge marks this item `dependency-blocked` and the run continues rather than failing. E-01 re-measures the corpus anyway, because a satisfied edge proves the sibling plan reached its terminal state, not that the tree is tier-consistent.

On execution: commit ONLY the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence, including the actual test output and the per-rule before/after comparison.
