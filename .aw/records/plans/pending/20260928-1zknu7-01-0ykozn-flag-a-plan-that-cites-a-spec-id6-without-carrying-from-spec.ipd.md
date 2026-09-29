# IPD: Flag a plan that cites a spec id6 without carrying From-Spec, and ship the --from-spec setter that fixes it

- Date: 2026-09-28
- Kind: child
- Concern: The plan-to-spec join edge (`- From-Spec:`) is ABSENT on exactly the plans whose spec suffers from partial implementation, so `check.spec-criteria-uncovered` is structurally silent where it matters most. Re-measured in this lane at HEAD `0d3e07aa` (the item's own numbers were taken at `96e93f8c` and have since GROWN): 56 plans mention `c4gd2h` and 0 carry `- From-Spec: c4gd2h`; the item said 37. `check_engine.check_from_spec_dangling` validates only that a PRESENT link resolves, so nothing notices an absent one. THE DECISIVE MEASUREMENT, run in this lane rather than argued: `check_engine.check_spec_criteria_uncovered` returns ZERO findings repo-wide today, and `c4gd2h` is not among them because its `plans_by_spec` bucket is empty; when the 18 plans that cite `c4gd2h` on a front-matter line are fed into the SAME predicate, 9 of its 10 acceptance criteria (`A1`-`A8`, `A10`) match and `A9` is reported uncovered. So the missing edge, not a missing requirement parser, is the binding constraint, and adding it converts a silent spec into one real finding.
- Scope: Add ONE advisory (`info`) COMMIT-SCOPED `aw check` rule that flags a plan whose `- Concern:`/`- Scope:`/`- Scope-Paths:` front matter cites a resolvable spec id6 while it carries no `- From-Spec:`, and ship the `--from-spec` setter that AGENTS.md records as missing so the rule's recovery instruction is executable. Reuse the existing `_ITEM_FROM_SPEC_RE`, `_iter_spec_records`, `_iter_plan_ipds`, `ipd_schema.source_link_is_absent`, and `releases.set_from_backlog_line`'s insertion shape; add no second spec-id scanner and no second field writer. EXCLUDES any backfill of the 80 executed plans that would trip the naive whole-tree form of this rule (see `## Deferred`, and F-03: AGENTS.md forbids rewriting what an executed plan records); EXCLUDES requirement-level tracking (backlog `vy20et`, and `f1sw71` which is `done`); EXCLUDES the 19 id-less specs that are unreachable by any id6 join (backlog `sklbrt`); EXCLUDES any change to `check.from-spec-dangling`, `check.spec-criteria-uncovered`, or their severities.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/releases.py, agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_check_engine_from_spec_missing.py, tests/test_check_engine_spec_criteria.py, AGENTS.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 1zknu7
- Set: 1zknu7
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0ykozn

## Workflow history

- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `1zknu7`. Resolved the item's open design question from repository evidence: the rule must be COMMIT-SCOPED rather than whole-tree (the naive whole-tree form yields 91 findings, 80 of them on `executed` plans AGENTS.md forbids editing), and the `--from-spec` setter is a REQUIRED part of the fix rather than a separate concern, because without it the rule's recovery instruction cannot be followed with a tool.

## Goal

Make the absence of a plan-to-spec edge VISIBLE at the moment it is introduced, and make it FIXABLE with a tool, so that spec acceptance-criteria coverage becomes computable for the specs that need it most instead of being silently unreportable.

Two halves, and the second is what makes the first legitimate. The DETECTOR (`check.plan-spec-link-missing`, `info`, commit-scoped) flags a plan being added or modified in THIS commit that cites a resolvable spec id6 in its `- Concern:`, `- Scope:`, or `- Scope-Paths:` front matter while carrying no `- From-Spec:`. The SETTER (`aw ipd set ... --from-spec <id6>`) gives that finding an executable recovery, closing the gap AGENTS.md names outright: "there is no `--from-spec` setter yet: write the field when authoring the plan."

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared field writer and its CLI surface

- [ ] E-01 Add `releases.set_from_spec_line(text, value)`, the `From-Spec` twin of the existing `releases.set_from_backlog_line`, plus its `_FROM_SPEC_LINE_RE` module-level pattern. MIRROR `set_from_backlog_line` EXACTLY: strip any existing line first so the write is idempotent, remove the line when `value` is `None` or `'-'`, and otherwise insert `- From-Spec: <value>\n` after the `- Status:` line, falling back to after `- Id:`, then returning `text` unchanged. Place it directly BESIDE `set_from_backlog_line` in the same module, and state in its docstring that it is that function's spec-side sibling. DO NOT anchor it like `set_item_dependencies_line`, whose docstring records that it deliberately anchors after `- Scope-Paths:` because spec `25kzda` 2.7 mandates that position for `Item-Dependencies` specifically; `From-Spec` has no such positional mandate and must match its `From-Backlog` twin so the two links sit together. Reuse the value regex shape `(\S+)` already used by `_ITEM_FROM_SPEC_RE`.
  - Depends on: none
  - Expected outcome: one new function and one new compiled pattern in `releases.py`; `set_from_spec_line(t, 'c4gd2h')` inserts the bullet immediately after `- Status:`, calling it twice is byte-identical to calling it once, and `set_from_spec_line(t, '-')` removes it.
  - Execution state: pending

- [ ] E-02 Wire `--from-spec` into `aw ipd set` so it funnels through E-01's single shared writer, mirroring the `from_backlog` handling already present in `status_set.py` (the block that reads `getattr(args, "from_backlog", None)` and calls `_releases.set_from_backlog_line(tmp_text, fb)`). Add the argparse flag in `cli.py` beside the existing `--from-spec`-less `--from-backlog` declaration, with help text stating it records the spec id6 this plan graduated from and that `-` clears it. VALIDATE the value the way the rule does: a value that is neither `-` nor a resolvable spec id6 must be REFUSED with a message naming the unresolvable id6, because writing an unresolvable link would manufacture exactly the dangling edge `check.from-spec-dangling` errors on. Write no em or en dashes in the `--help` string (AGENTS.md governs user-facing prose).
  - Depends on: E-01
  - Expected outcome: `aw ipd set to-review <plan> --from-spec c4gd2h` writes the bullet and appends no spurious transition; `--from-spec nosuch` exits nonzero naming `nosuch`; `--from-spec -` removes the line.
  - Execution state: pending

### Task group 2: the detector

- [ ] E-03 Add `check_engine.parse_cited_spec_ids(plan_text, known_spec_ids)`, a PURE function returning the ordered, deduplicated spec id6s cited on a plan's `- Concern:`, `- Scope:`, or `- Scope-Paths:` front-matter lines. Scan ONLY those three bullets, never the whole document: the whole-document form was measured in this lane at 56 hits for `c4gd2h` against 18 for the front-matter form, and the extra 38 are body prose (a `## Findings` row, a `V-*` evidence demand) where a mention is a CITATION and emphatically not a graduation claim. Match a candidate as a 6-character `[0-9a-z]{6}` token on a word boundary, then keep ONLY tokens present in `known_spec_ids`, so an arbitrary six-letter English word can never be mistaken for a spec. Take the known-id set as a PARAMETER rather than computing it, so the function is unit-testable without a repository and so the caller keeps the single existing authority for that set.
  - Depends on: none
  - Expected outcome: a pure function; given `c4gd2h`'s known set it returns `['c4gd2h']` for a plan citing it in `- Scope:`, returns `[]` for a plan citing it only in a `## Findings` row, and returns `[]` for a plan whose `- Concern:` contains the word `hazard` when `hazard` is not a known spec id.
  - Execution state: pending

- [ ] E-04 Add `check_engine.check_plan_spec_link_missing(repo_root)` as a COMMIT-SCOPED detector, and register `check.plan-spec-link-missing` in `RULE_REGISTRY` at `info` / `ASSURANCE_REPOSITORY` / `DET_DETERMINISTIC` with invariant `""`. COMMIT-SCOPING IS THE LOAD-BEARING DESIGN DECISION AND MUST NOT BE WEAKENED TO A WHOLE-TREE SWEEP: measured in this lane, the whole-tree form yields 91 findings of which 80 sit on `executed` plans and 6 on `superseded`, and AGENTS.md forbids changing what an executed plan records, so 86 of 91 findings would be unactionable by construction. Copy the mechanism from `check_status_untooled`, whose docstring states the identical rationale ("ONLY files changed in the commit are examined, so historical records are never touched (NO grandfathering, NO whole-tree scan)"): diff the staged index against HEAD with `git diff --cached --name-status -M -- .aw/records/plans/`, fast-return `[]` when nothing is staged under plans, skip a pure deletion, and handle the rename/copy/modify path shapes as that function does. EXCLUDE a plan in a terminal directory (`executed/`, `superseded/`, `not-executed/`) for the same reason it does. Read the existing `- From-Spec:` with `_ITEM_FROM_SPEC_RE` and treat a sentinel value as absent via `ipd_schema.source_link_is_absent`, exactly as `check_spec_criteria_uncovered` already does. Build the known-spec-id set from `_iter_spec_records` plus `specs._existing_spec_ids`, the SAME union `check_from_spec_dangling` uses and for the reason its docstring records (an externally-redirected project makes either source alone produce false positives). Emit AT MOST ONE finding per plan, enriched through `enrich_drift` with `observed`/`required`/`recovery`, whose recovery names the E-02 command.
  - Depends on: E-02, E-03
  - Expected outcome: `info`-severity findings only, so `artifact_core.drift_exit_code` (which exempts exactly `info`) cannot change any exit code; staging a new plan citing `c4gd2h` with no edge produces exactly one finding; staging one carrying the edge produces none; `aw check` on a clean tree produces none and performs no plans scan.
  - Execution state: pending

- [ ] E-05 Reach the new detector from the `record_type == "plan"` full-sweep dispatch in its own `try`/`except Exception: pass`, placed immediately beside the existing `check_spec_criteria_uncovered` call and matching its fail-isolated shape and its comment style. State in the comment that the rule is advisory so it cannot move an exit code, that it is reached by BOTH `aw check plans` and the `aw check all` fan-out exactly once, and that it is commit-scoped so it is a fast no-op when nothing is staged under plans. Do NOT alter the neighbouring call, its arguments, or the ordering of any existing rule.
  - Depends on: E-04
  - Expected outcome: `aw check plans` and `aw check all` each reach the rule exactly once; an exception inside it cannot fail the surrounding sweep.
  - Execution state: pending

### Task group 3: documentation of the closed gap

- [ ] E-06 Correct the ONE sentence in `AGENTS.md` that now states something false, and change nothing else in that file. Today it reads "Note there is no `--from-spec` setter yet: write the field when authoring the plan." E-02 ships that setter, so replace the sentence with one naming the setter and the new advisory rule. THE EDIT SITE IS CONSTRAINED: that sentence sits at `AGENTS.md:222`, BELOW the `<!-- /aw:block -->` marker at line 125, so it is OUTSIDE every managed block and is safe to edit in place; verify that boundary by reading the markers before editing, and do NOT edit any line between `<!-- aw:block -->` and `<!-- /aw:block -->`, which `engine.py` installs into managed repos and would overwrite. Write no em or en dashes in the replacement prose.
  - Depends on: E-02, E-04
  - Expected outcome: `rg -n "no .--from-spec. setter" AGENTS.md` returns nothing; the replacement sentence names both `--from-spec` and `check.plan-spec-link-missing`; `git diff AGENTS.md` shows changes only below line 125.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ADVISORY SEVERITY IS A DESIGN TOOL WITH AN EXACT MEANING, and `info` is the only non-failing tier. `artifact_core.drift_exit_code` returns 1 for any finding whose `severity` is not exactly `info`, so `warning` would fail the gate precisely as `error` does. The `check.spec-criteria-uncovered` registry comment states this outright and calls its own severity "load-bearing", adding that registration is not bookkeeping because an unregistered id falls back to `_DEFAULT_RULESPEC` at `error`. This plan's rule is a necessary-not-sufficient heuristic, so it must be `info` and must be registered.
- COMMIT-SCOPING IS THE ESTABLISHED ANSWER TO "THE CORPUS IS FULL OF OLD VIOLATIONS", and `check_status_untooled` is the precedent to copy rather than a similar-looking function. Its docstring names the benefit in the exact terms this plan needs: "Commit-scoping is the key simplification: ONLY files changed in the commit are examined, so historical records are never touched (NO grandfathering, NO whole-tree scan)."
- THE KNOWN-SPEC-ID SET HAS ONE CORRECT CONSTRUCTION AND IT IS A UNION OF TWO AUTHORITIES. `check_from_spec_dangling`'s docstring records that `_iter_spec_records` walks the in-tree trees while `specs._existing_spec_ids` resolves through `record_producers.resolve_record_read_paths`, which in an externally-redirected project resolves OUTSIDE the repo; it reports verifying on a scratch repo that `_existing_spec_ids` was EMPTY while an in-tree spec plainly existed. Either source alone yields false positives on some real layout.
- `GUIDING_PRINCIPLES` P8 FORBIDS A SECOND MECHANISM FOR AN EXISTING QUESTION, and `check_from_spec_dangling` cites it by name ("a second mechanism for 'which spec ids exist' is precisely the drift GUIDING_PRINCIPLES P8 forbids"). Hence E-03 takes the id set as a parameter and E-01 adds a field writer beside its twin rather than a parallel one.
- A SENTINEL VALUE IS NOT A LINK. `ipd_schema.source_link_is_absent` treats `None`, empty, and the absent sentinels (`-`, `none`, `unresolved`) as absent after stripping quotes; `check_spec_criteria_uncovered` already routes its `From-Spec` read through it. A rule reading the raw regex group alone would treat `- From-Spec: -` as a satisfied edge.
- TEST OUTCOMES, NOT CODE STRUCTURE (AGENTS.md, `GUIDING_PRINCIPLES` P16). Every test this plan adds drives a real function or a real CLI over a real temporary repository and asserts on returned findings, written file content, and exit codes. No test may read production source with `inspect`, `ast`, regex, or substring search, and none may assert a symbol census or a line count.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `rg -l -- c4gd2h .aw/records/plans \| wc -l` -> `56`; `rg -l "^- From-Spec: c4gd2h" .aw/records/plans \| wc -l` -> `0`, both run in this lane at HEAD `0d3e07aa` | THE ITEM'S CORE CLAIM HOLDS AND ITS NUMBER IS NOW STALE IN THE WORSE DIRECTION. The item says 37 mentions; there are 56. The zero is unchanged. So the gap is widening on its own, which is the argument for a detector that fires at introduction time rather than a one-off backfill. |
| F-02 | HIGH | Ran `check_engine.check_spec_criteria_uncovered(repo)` in this lane: returns ZERO findings repo-wide. Then fed the 18 front-matter citers of `c4gd2h` through `extract_plan_validation_space` and the same criterion regex | THE CONSEQUENCE IS MEASURED, NOT ASSERTED, AND IT IS EXACTLY ONE FINDING. `c4gd2h` declares 10 criteria (`A1`-`A10`). With the edge absent its `plans_by_spec` bucket is empty and the rule `continue`s before parsing anything. With the edge present, 9 criteria match and `A9` is uncovered, and the namespace-in-use gate passes because `matched` is non-empty. So adding the edge is not bookkeeping: it converts a structurally silent spec into one real, actionable finding. |
| F-03 | HIGH | Prototyped the naive whole-tree predicate over `_iter_plan_ipds`: 91 findings, `{'executed': 80, 'superseded': 6, 'pending': 5}`. AGENTS.md: "Never change what a plan already in `.aw/records/plans/executed/` RECORDS" | THE ITEM'S CANDIDATE FIX AS WORDED WOULD BE 94 PERCENT UNACTIONABLE, WHICH IS WHY THIS PLAN COMMIT-SCOPES IT. 86 of 91 findings land on terminal plans the repository forbids editing. A rule whose findings cannot be acted on trains readers to ignore it. Commit-scoping reduces the live surface to the 5 pending plans and to every plan authored hereafter. |
| F-04 | HIGH | `AGENTS.md:222`: "Note there is no `--from-spec` setter yet: write the field when authoring the plan." `aw ipd set --help` shows `--from-backlog` and no `--from-spec` | THE RECOVERY INSTRUCTION HAD NO TOOL, SO THE DETECTOR ALONE WOULD BE A RULE THAT CANNOT BE OBEYED WITH TOOLING. This is why E-01/E-02 are in THIS plan and not deferred: AGENTS.md elsewhere instructs agents not to hand-name or hand-maintain managed fields, so shipping a nag whose only remedy is a hand edit would contradict the repository's own posture. |
| F-05 | MED | The 18 front-matter citers of `c4gd2h` are ALL in `executed/`; the whole-document set adds 38 more whose hits are `## Findings` rows and `V-*` evidence demands (e.g. a row reading "spec `c4gd2h` R22 forbids...") | THE PROSE-MENTION FALSE POSITIVE THE ITEM WARNS ABOUT IS REAL AND IS BOUNDED BY RESTRICTING THE SCAN TO THREE BULLETS. A body mention is overwhelmingly a CONSTRAINT CITATION ("R22 forbids this") rather than a graduation claim. This is the honest-limit half of the item's own candidate fix, answered structurally. |
| F-06 | MED | Inspected all 5 pending-plan hits of the front-matter predicate: `7dz3wv` (declares `25kzda`'s file in `Scope-Paths` and amends it), `ghna7l` (declares `pqsx96`'s file and amends its I-07 row), `eikajx`, `q32qeg`, `g1w58u` | THE LIVE FINDINGS ARE A MIX, AND THAT MIX IS WHY THE RULE IS ADVISORY RATHER THAN AN ERROR. Two of the five AMEND the spec they cite and declare its `.spec.md` in `Scope-Paths`, which is a strong graduation signal. The other three cite a spec as a CONSTRAINT they conform to (`g1w58u` explicitly states "No `.spec.md` is in `- Scope-Paths:` and none is amended"). A conforming plan legitimately carries no edge, so the correct severity is a nudge a human judges, never a gate. |
| F-07 | MED | `releases.set_item_dependencies_line` docstring: anchoring is "DELIBERATELY DIFFERENT from `set_blocks_release_line`/`set_from_backlog_line`" because spec `25kzda` 2.7 mandates the position for that field | THE INSERTION ANCHOR IS A REAL CHOICE WITH A WRONG ANSWER AVAILABLE. Copying the `Item-Dependencies` anchor would place `From-Spec` after `Scope-Paths` and separate it from its `From-Backlog` twin. E-01 states the correct anchor and the reason. |
| F-08 | LOW | `git show -s --date=short 8c437188` -> `2026-08-30`; the `runstop` Set's plans are dated `2026-08-29` and were authored by `6b2a7c6b` | THE LARGEST CLUSTER OF EDGE-LESS PLANS PREDATES THE FIELD ITSELF, so its absence is not author negligence. `From-Spec` shipped on 2026-08-30; the seven `runstop` plans graduating `c4gd2h` were authored the day before. This is further support for commit-scoping over a retroactive sweep, and it means no backfill is owed as a correctness matter. |
| F-09 | LOW | `lanectn` Set: all 8 members carry `- From-Spec: 7ckptx`. `runstop` Set: all 7 members carry none | THE REPOSITORY ALREADY CONTAINS BOTH THE GOOD AND THE BAD PATTERN AT SET GRANULARITY, giving the tests a real analogue rather than a synthetic one, and confirming the edge is a per-Set authoring habit that a commit-time nudge is well-shaped to correct. |

## Proposed changes (ordered, validatable)

1. `releases.py`: add `_FROM_SPEC_LINE_RE` and `set_from_spec_line`, mirroring `set_from_backlog_line` including its `- Status:` anchor (E-01).
2. `status_set.py` and `cli.py`: add `--from-spec` to `aw ipd set`, funnelled through the E-01 writer, refusing an unresolvable id6 (E-02).
3. `check_engine.py`: add the pure `parse_cited_spec_ids` restricted to the three front-matter bullets and filtered by a supplied known-id set (E-03).
4. `check_engine.py`: add the commit-scoped `check_plan_spec_link_missing` and register `check.plan-spec-link-missing` at `info` (E-04).
5. `check_engine.py`: dispatch it from the `plan` full-sweep beside `check_spec_criteria_uncovered`, fail-isolated (E-05).
6. `AGENTS.md`: correct the one now-false sentence, below the managed-block marker (E-06).
7. `tests/test_check_engine_from_spec_missing.py`: new outcome tests for the parser, the detector, and the setter.
8. `tests/test_check_engine_spec_criteria.py`: one added test pinning that a plan gaining the edge becomes visible to the coverage rule, which is F-02's mechanism as an executable assertion.

## Deferred / out of scope (with reason)

- BACKFILLING THE EDGE ONTO THE 80 EXECUTED AND 6 SUPERSEDED PLANS. Deferred permanently as stated, not merely postponed. AGENTS.md: "Never change what a plan already in `.aw/records/plans/executed/` RECORDS (its steps, evidence, results, or status)", and it directs a post-execution gap to a new corrective IPD rather than an in-place edit. F-08 makes the case stronger: the largest cluster was authored the day BEFORE the field existed, so no author erred. A maintainer who later wants `c4gd2h` coverage computable has a legitimate narrow route AGENTS.md permits, namely appending a dated `## Workflow history` line, which adds to the record without rewriting it; that is a deliberate decision with a real cost (86 file touches) and belongs to a human, so this plan does not smuggle it in. NO CARRIER IS FILED, because there is no defect: the detector prevents the population from growing, and a decision to backfill is a maintainer's call rather than tracked debt.
  - Carrier-Declined: No future work is owed, and filing an item would misrepresent a settled constraint as an outstanding task. AGENTS.md FORBIDS the only edit that would clear these 86 findings, and F-08 measures that the largest cluster predates the field by one day, so no author erred and there is no defect to carry. The one permitted route (appending a `## Workflow history` line to 86 terminal records) is a maintainer's judgement about cost against the value of computable `c4gd2h` coverage, not work this plan has established is wanted. Recorded here so a reviewer does not read the silence as a claim that the corpus is clean; the `- Under-scope:` entry states the same limit where a reader of the outcome will meet it.
- REQUIREMENT-LEVEL (`R*`) SPEC TRACKING. Owned by open backlog `vy20et` ("Specs have no machine-readable requirement-ID convention, so SPEC-PLAN-TRACE ... cannot be built"). Backlog `f1sw71`, the item this one distinguishes itself from, is `done`. This plan is deliberately the ARTIFACT-level edge one level up, exactly as the item states.
  - Carrier: vy20et
- THE 19 SPECS CARRYING NO `- Id:` BULLET. They are unreachable by ANY id6-keyed join, so no `From-Spec` edge can point at them and this plan's rule cannot fire for them. Measured in this lane: `_iter_spec_records` plus `_existing_spec_ids` yields 19 known ids.
  - Carrier: sklbrt
- ANY CHANGE TO `check.spec-criteria-uncovered`, `check.from-spec-dangling`, OR THEIR SEVERITIES. Both work as specified. This plan FEEDS the former by making edges exist and complements the latter by asking the absent-link question it deliberately does not ask.
  - Carrier-Declined: This row records a PROHIBITION on this plan, not a deferred defect, so nothing is owed. No finding here measures a fault in either rule; both behave as their docstrings specify. The prohibition is enforced inside this plan by the scope fence and by V-05's requirement that the neighbouring dispatch call be unchanged.
- A `--from-spec` FLAG ON `aw ipd scaffold`. Not required to close this item: the rule fires at commit time and `aw ipd set --from-spec` fixes it in one command. Adding it to scaffold as well would widen the surface without changing any outcome this plan validates.
  - Carrier-Declined: Nothing is owed once E-02 lands. This is a convenience that would change no outcome this plan validates: the detector fires at commit time and the setter already resolves every finding it can raise in one command, so a scaffold flag would add a second authoring surface for a field the set path already writes through the single shared writer. If a future author measures that the field is habitually forgotten at scaffold time DESPITE the commit-time nudge, that measurement is the evidence that would justify an item; asserting it now would file work nobody has shown is needed.
- A PRE-COMMIT HOOK. The rule is `info`; wiring an advisory nudge into a blocking hook would contradict its severity. `aw check` is the surface.
  - Carrier-Declined: No future work is owed, because this is a design conclusion rather than an unbuilt piece. OQ-02 resolves that the rule must stay advisory (F-06 measures that three of five live findings are conforming plans that legitimately carry no edge), and a blocking hook is exactly the enforcement an advisory severity rules out. A hook would only become coherent if the severity were ever raised, which is a maintainer's policy decision and a public-contract change; it is named in OQ-02 rather than carried as debt.

## Scope check

- Over-scope: none. The setter (E-01/E-02) could look like a second concern, but F-04 shows the detector's recovery instruction is unexecutable without it, so the two ship together or the rule nags at a remedy the repository's own conventions discourage.
- Under-scope: The 86 terminal plans keep no edge, so `c4gd2h` coverage stays uncomputable until a maintainer decides on the history-line route named in `## Deferred`. This plan STOPS THE BLEEDING and makes the fix tooled; it does not retroactively heal the corpus. Stated plainly because the item's headline number (56 plans) will NOT drop as a result of this plan, and a reader expecting that would be misled.

## Required tests / validation

Run the suite BARE as `python3 -m pytest` (AGENTS.md: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). Targeted files: `tests/test_check_engine_from_spec_missing.py`, `tests/test_check_engine_spec_criteria.py`, plus `tests/test_check_engine_release_gate.py` and any `releases`/`status_set`/`cli` suite touching the `From-Backlog` writer, since E-01 lands beside it. Also run `aw check`, `aw ipd lint`, and `aw sanitize --agent`.

Every test drives real code over a real temporary repository and asserts on returned findings, file content, and exit codes. Required coverage:

- `parse_cited_spec_ids`: cited in `- Concern:`; cited in `- Scope:`; cited in `- Scope-Paths:`; cited ONLY in a `## Findings` body row (must return `[]`); a six-letter word that is not a known spec id (must return `[]`); the same id cited on two bullets (must dedupe).
- `check_plan_spec_link_missing`: nothing staged (returns `[]` with no plans scan); a staged NEW pending plan citing a known spec with no edge (exactly one `info` finding naming plan and spec); the same plan carrying the edge (no finding); the same carrying `- From-Spec: -` (finding, via `source_link_is_absent`); a staged plan under `executed/` (no finding); a staged pure deletion (no finding); a staged rename (handled, not crashed).
- Exit-code control: a repository whose ONLY finding is this rule's must still exit 0 through `artifact_core.drift_exit_code`, pinning the `info` contract.
- `set_from_spec_line`: inserts after `- Status:`; idempotent under a second call; removes on `'-'`; falls back to after `- Id:` when no `- Status:` exists.
- `aw ipd set --from-spec`: writes the bullet; refuses an unresolvable id6 with a nonzero exit naming it; clears on `-`.
- Coverage linkage (F-02 as an assertion): a fixture spec with acceptance criteria plus a plan that gains `- From-Spec:` must move `check_spec_criteria_uncovered` from silent to reporting the uncovered criterion.

## Spec / documentation sync

NO `.spec.md` IS IN `- Scope-Paths:` AND NONE IS AMENDED, which is a deliberate verified conclusion rather than an omission. Two candidates were checked. Spec `pqsx96` (the agent-adherence invariant catalog, `draft`) carries the I-* rows this rule might claim; this rule claims invariant `""` instead, following the precedent `check.spec-criteria-uncovered` set in its own registry comment, which records choosing `""` rather than "claiming an existing I-* row that does not fit" because I-05 governs plan validation at finalize and I-07 governs release-gate preservation. Neither covers an absent provenance link, so no catalog row needs widening and no spec edit is owed. Note that pending plan `ghna7l` is concurrently amending that same I-07 row for a DIFFERENT rule; claiming `""` keeps this plan off that file entirely and avoids a collision. Spec `25kzda` Section 2.1 governs the `aw <host> run` FLAG SURFACE and is pinned as a FILE by `tests/test_run_flag_surface.py`, which fails both on a spec-declared flag the code lacks and the converse; E-02 adds a flag to `aw ipd set`, which is NOT a host run flag, so that test is unaffected and the spec needs no amendment. The only documentation change is E-06's one-sentence correction in `AGENTS.md`, below the `<!-- /aw:block -->` marker and therefore outside every managed block. No user-facing documentation describes `From-Spec` beyond that sentence.

## Open questions

### OQ-01: Should the rule also fire on a plan that declares a `.spec.md` path in `- Scope-Paths:` while carrying no `- From-Spec:`?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, AND THE ANSWER IS THAT THIS PLAN ALREADY COVERS IT WITHOUT A SEPARATE SIGNAL. Measured in this lane: 67 plans declare a `.spec.md` in `- Scope-Paths:` and only 9 carry any `- From-Spec:`, so a dedicated rule would be a 58-finding sweep on a corpus that is overwhelmingly terminal, reproducing F-03's unactionability problem. And it is unnecessary here: a declared `.spec.md` path CONTAINS the spec's id6 in its filename (the naming grammar is `YYYYMMDD-<id6>-NN-<id6>-<slug>.spec.md`), so E-03's `- Scope-Paths:` scan already detects that case, which is precisely why pending plans `7dz3wv` and `ghna7l` appear in F-06's live set. NOT BLOCKING: the behavior is specified by E-03 and validated by the `- Scope-Paths:` test case. REVERSIBLE: yes; nothing is deleted.

### OQ-02: Should a plan amending a spec be REQUIRED to carry `- From-Spec:`, making the rule an error rather than advisory?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED: NO, AND THE REASON IS SEMANTIC RATHER THAN MERELY CAUTIOUS. AGENTS.md states a plan MAY amend a spec and must declare the file in `- Scope-Paths:`; it does NOT say such a plan GRADUATED FROM that spec, and the two are different relations. `From-Spec` means "this plan graduated from that spec"; amending a spec in passing (E-06's own shape, or `2iye0e` appending a note to an OQ) is not graduation. F-06 measures the mix directly: of five live findings, two amend the cited spec and three cite it as a constraint they conform to, with `g1w58u` stating outright that no `.spec.md` is in its scope and none is amended. Erroring would force a false provenance claim onto conforming plans, which is the same class of harm as writing another role's attestation. Hence `info`. A maintainer who later wants a hard rule has the narrower predicate available (a DECLARED `.spec.md` in `Scope-Paths` plus an approved spec), but that is a policy decision and a public-contract change, so it is theirs and not smuggled in here. NOT BLOCKING: this plan ships `info` and nothing depends on a stricter severity.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the committed `set_from_spec_line` source and its `_FROM_SPEC_LINE_RE`. PASTE a Python transcript over a realistic plan front matter showing: (a) the bullet inserted IMMEDIATELY after the `- Status:` line, quoting the three adjacent lines to prove position; (b) `set_from_spec_line(set_from_spec_line(t, 'c4gd2h'), 'c4gd2h') == set_from_spec_line(t, 'c4gd2h')` -> `True` (idempotence); (c) `'-'` removing the line; (d) with no `- Status:` present, insertion after `- Id:`. PASTE the targeted test output. A transcript showing insertion after `- Scope-Paths:` FAILS this item, because that is the `Item-Dependencies` anchor F-07 identifies as the wrong answer.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `aw ipd set --help` showing `--from-spec` with its help text, and CONFIRM by reading that it contains no em or en dash. PASTE three real CLI transcripts against a temporary plan: writing `c4gd2h` (then paste the resulting front-matter bullet), refusing `nosuch` (paste the nonzero exit code and the message naming `nosuch`), and clearing with `-`. PASTE the diff hunk of the `status_set.py` wiring and CONFIRM it calls E-01's `set_from_spec_line`; a hunk that formats the bullet inline rather than calling the shared writer FAILS this item, because a second field writer is the P8 drift E-01 exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the test output for all six `parse_cited_spec_ids` cases named in Required tests. PASTE a transcript proving the body-mention exclusion on a REAL corpus file, not a fixture: run the parser over an executed plan whose only `c4gd2h` hits are body rows and show it returns `[]`, then over one citing `c4gd2h` in `- Scope:` and show it returns `['c4gd2h']`. PASTE the front-matter-only versus whole-document counts measured at execution (F-01/F-05 measured 18 against 56); a parser returning the whole-document count FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the `RULE_REGISTRY` entry showing `info` severity. PASTE test output for all seven detector cases in Required tests, plus the exit-code control proving a repository whose only finding is this rule exits 0. PASTE a transcript showing the fast no-op: with nothing staged under `.aw/records/plans/`, the function returns `[]`. PASTE proof the terminal-directory exclusion holds by staging a plan under `executed/` and showing zero findings. PASTE the known-id-set construction and CONFIRM it is the `_iter_spec_records` plus `_existing_spec_ids` UNION; a single-source construction FAILS this item, for the redirected-project reason `check_from_spec_dangling`'s docstring measured. PASTE `aw check` on the clean tree showing this rule contributes no finding and the exit code is unchanged from the pre-change baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the dispatch diff hunk showing the call inside its own `try`/`except Exception: pass` beside `check_spec_criteria_uncovered`, with the neighbouring call unchanged. PROVE single dispatch, not double: stage one violating plan, run `aw check plans` and then `aw check all`, and paste output showing EXACTLY ONE finding for that plan in each (a duplicated finding means the rule is reached twice by the fan-out). PROVE fail isolation by temporarily monkeypatching the detector to raise and showing the surrounding sweep still completes and reports its other findings; paste that transcript.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE `rg -n "no .--from-spec. setter" AGENTS.md` returning NOTHING. PASTE the replacement sentence and confirm it names both `--from-spec` and `check.plan-spec-link-missing` and contains no em or en dash. PASTE `git diff AGENTS.md` and CONFIRM every changed line number is greater than the `<!-- /aw:block -->` marker's line; any change inside a managed block FAILS this item, since `engine.py` would overwrite it in managed repos. ALSO carry the whole-plan no-regression evidence here, as the last item before commit: PASTE the BARE `python3 -m pytest` output including its `N passed` summary line and reconcile the total against the pre-change baseline recorded at execution, explaining any difference against a named E-item rather than waving it through; PASTE the targeted test files' output; PASTE `aw check`; PASTE `aw ipd lint` reporting conforming; PASTE `aw sanitize --agent`; and PASTE `git diff --cached --name-only` immediately before committing, which must list exactly the seven `- Scope-Paths:` entries and nothing else.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A`, never bare `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything you did not modify with `git restore --staged <path>`; this checkout may be shared, so another party's uncommitted work must never enter this commit. If a raw `git commit` is ever attempted and a hook rejects it, RE-VERIFY the staged set before retrying, since `pre-commit` restores unstashed changes and can leave unstaged paths in the index.

SCOPE FENCE. Touch only the seven declared paths. Do NOT weaken the `info` severity of the new rule. Do NOT convert the detector to a whole-tree sweep (F-03). Do NOT add a second spec-id scanner or a second `From-Spec` writer (P8). Do NOT edit any line inside `AGENTS.md`'s managed block. Do NOT backfill the edge onto any plan in `executed/`, `superseded/`, or `not-executed/`. Do NOT modify `check.from-spec-dangling` or `check.spec-criteria-uncovered`. Do NOT edit the backlog item's requirements. If the work GENUINELY requires a path outside the fence, make the edit and justify it, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. This plan requires explicit human approval before execution. After execution, every `V-*` item must carry pasted evidence and `aw ipd lint --phase pre-transition` must report conforming before the plan moves to `.aw/records/plans/executed/`. Do not claim done or move the plan on the strength of the execution checkmarks alone.
