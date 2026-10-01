# IPD: Transition spec kw5y2s to implemented through implementing with cited wslayout evidence

- Date: 2026-10-01
- Kind: child
- Concern: SPEC `kw5y2s` IS SHIPPED BUT STILL READS `approved`, SO `aw attention` CLASSES IT `ready` (work waiting to start) WHEN ITS IMPLEMENTING SET FULLY EXECUTED THREE WEEKS AGO. Backlog `jd01a0` carries plan `xx5b7a`'s OQ-01, which deliberately left the status question to a human. All four of the item's evidence points were RE-MEASURED at HEAD `850e6a19` on 2026-10-01 and all four HOLD (see Findings F-01..F-04). Two things the item does NOT anticipate were measured and change HOW the transition must be done rather than WHETHER. FIRST, `approved -> implemented` IS AN ILLEGAL TRANSITION AND IS REFUSED: `attention_contract.SPEC_TRANSITIONS['approved']` is `{implementing, reviewed, deferred, parked, superseded}` with no `implemented` member, and `aw specs set --status implemented` on this spec prints `illegal transition approved -> implemented` and exits 1. The item's own instruction ("run aw specs set implemented with the cited evidence") therefore CANNOT be followed as one step; the lifecycle requires the intermediate `implementing` hop, which is exactly what precedent spec `20260810-1447-01-physical-aw-hierarchy...` records doing ("advancing from approved to implementing ahead of the implemented transition"). SECOND, the setter RELOCATES the file to match status (`aw specs set --dry-run` prints `would move ... -> .aw/records/specs/implementing/...`), so the spec's path changes TWICE during this plan, and pending plan `xx5b7a` declares the CURRENT `approved/` path in its own `- Scope-Paths:`; executing this plan first would break that plan's declared scope. That ordering is resolved by an `- Item-Dependencies: executed:xx5b7a` edge, not by prose.
- Scope: IN: re-measure the four evidence points plus the two newly measured mechanics at the executing HEAD, with explicit stop conditions if any has inverted; move `kw5y2s` `approved -> implementing` recording the `wslayout` Set via `--graduated-to`; move `implementing -> implemented` with a resolvable `--evidence` citation naming the executed `wslayout` orchestrator; confirm `aw attention` reclassifies the spec from `ready` to `done` and that `aw check`/`aw specs check` stay clean across both hops; verify the two relocations landed as git renames and that no stale copy remains in `approved/` or `implementing/`. OUT: every WORD of the spec's body, which this plan does not edit (plan `xx5b7a` owns the text corrections and must land first); Section 3.4's traversal-exclusion widening, declared out of scope by the spec itself; any code, test, or `AGENTS.md` change, since the lifecycle machinery is working exactly as specified and the only thing missing is the transition; and the `- Status:` of any other spec.
- Scope-Paths: .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md, .aw/records/specs/implementing/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md, .aw/records/specs/implemented/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
- Item-Dependencies: executed:xx5b7a
- Status: to-review
- From-Spec: kw5y2s
- Work-Kind: chore
- Priority: low
- From-Backlog: jd01a0
- Set: jd01a0
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: dwivqd

## Workflow history
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `jd01a0`. All four of the item's evidence points re-measured at HEAD `850e6a19` and all four hold. The audit found TWO mechanics the item does not anticipate: `approved -> implemented` is an ILLEGAL transition (refused by `SPEC_TRANSITIONS`, so the item's one-step instruction cannot be followed and the `implementing` hop is mandatory), and the setter RELOCATES the spec file, which collides with pending plan `xx5b7a`'s declared `- Scope-Paths:` and forces an `executed:xx5b7a` dependency edge.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make spec `kw5y2s`'s recorded status agree with reality, so `aw attention` stops advertising a fully shipped design as `ready` work, and do it through the two legal hops the lifecycle actually permits (`approved -> implementing -> implemented`) with the executed-IPD evidence citation the `->implemented` authority requires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the premise before moving anything

- [ ] E-01 RE-MEASURE THE BACKLOG ITEM'S FOUR EVIDENCE POINTS at the executing HEAD and paste each result. Do NOT trust this plan's snapshot; the whole point of the item is that a human wants the four points verified at the then-current HEAD. Let `SPEC` be the spec's path AS IT IS AT THAT MOMENT (it is under `approved/` before this plan runs, but resolve it rather than assuming: `aw find specs kw5y2s` or `ls .aw/records/specs/*/*kw5y2s*`).
  - (a) ALL SIX `wslayout` PLANS EXECUTED: `find .aw/records/plans -name "*wslayout*" | sort`, and confirm every hit is under `executed/`. Also paste `grep -n "From-Spec" .aw/records/plans/executed/20260901-wslayout-00-rh5tt6-*.ipd.md` to confirm the orchestrator still carries `- From-Spec: kw5y2s`.
  - (b) THE LAYOUT MODEL AND CLI EXIST (Sections 3/4/6): `ls agent_workflows/layout.py` and `aw layout --help` (usage, exit 0).
  - (c) THE ELEVEN-CLASS VOCABULARY SHIPPED IN BOTH VOCABULARIES (Section 3.2): run the census `python3 -c "from agent_workflows import artifact_types, record_producers; AT=set(artifact_types.ARTIFACT_TYPES); RC={m.value for m in record_producers.RecordClass}; rows=['plans','specs','research','backlog','reviews','releases','prompts','walkthroughs','roadmaps','comms','other']; [print(r, r in AT, r in RC) for r in rows]; print(len(AT), len(RC), sorted(RC-AT), sorted(AT-RC))"`.
  - (d) INSTALL-TIME EMISSION AND THE GITIGNORE BACK-FILL ARE WIRED (Sections 2.3/6.1): `grep -n "layout.json\|layout.schema.json" agent_workflows/engine.py | head`, `grep -n "layout" .aw/.gitignore`, and `git check-ignore -v .aw/system/layout.json .aw/system/layout.schema.json`. Also confirm the user's ROOT `.gitignore` is untouched by it: `grep -c layout .gitignore` (expect `0`).
  - WHY ALL FOUR AND NOT A SPOT CHECK: the item's "WHAT TO DO" names verification of the four points as the precondition for the transition, and the `->implemented` authority is `evidence: True` with no semantic verification (`attention_contract.TRANSITION_AUTHORITY`, `specs._evidence_resolvable`). The tool checks that the citation RESOLVES to an executed IPD, NOT that the work happened, so this item is the only thing standing between a resolvable string and a false `implemented` claim.
  - Depends on: none
  - Expected outcome: (a) six files, all under `.aw/records/plans/executed/`, orchestrator carries `- From-Spec: kw5y2s`; (b) the file exists and `aw layout --help` exits 0; (c) all eleven rows `True True`, `len(AT)` 11, `len(RC)` 12, `RC-AT == ['records']`, `AT-RC` empty; (d) `engine.py` references both emitted paths, `.aw/.gitignore` carries `system/layout.json` and `system/layout.schema.json`, `git check-ignore` confirms both ignored, root `.gitignore` has `0` layout hits. IF ANY POINT FAILS, STOP and report which: the premise of the transition is that the spec is implemented, and a failed point means it is not.
  - Execution state: pending

- [ ] E-02 RE-MEASURE THE TWO MECHANICS THIS PLAN DISCOVERED, because both are claims about tooling behavior that a reviewer should not have to take on trust and that a later commit could change.
  - (a) THE TRANSITION GRAPH: `python3 -c "from agent_workflows import attention_contract as A; print(sorted(A.SPEC_TRANSITIONS['approved'])); print(sorted(A.SPEC_TRANSITIONS['implementing'])); print(A.transition_allowed('approved','implemented'), A.transition_allowed('approved','implementing'), A.transition_allowed('implementing','implemented')); print(A.TRANSITION_AUTHORITY['->implemented'])"`.
  - (b) THE REFUSAL IS REAL, not merely inferred from the table: run the one-step form the backlog item asks for and paste its refusal, `aw specs set "$SPEC" --status implemented --evidence .aw/records/plans/executed/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.ipd.md --dry-run`. THIS IS SAFE TO RUN: it refuses at the transition gate before writing, and `--dry-run` writes nothing even on the paths that pass.
  - (c) THE EVIDENCE CITATION RESOLVES: `python3 -c "from pathlib import Path; from agent_workflows import specs; print(specs._evidence_resolvable(Path('<SPEC>'), '.aw/records/plans/executed/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.ipd.md'))"` with `<SPEC>` substituted. Measured `True` at authoring.
  - (d) THE SETTER RELOCATES: `aw specs set "$SPEC" --status implementing --graduated-to wslayout --dry-run` and paste the `would move ... -> .../specs/implementing/...` line WITHOUT applying it.
  - Depends on: E-01
  - Expected outcome: (a) `approved` permits `implementing` and NOT `implemented`; `implementing` permits `implemented`; the three booleans are `False True True`; the authority dict reads `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': True}`. (b) stderr contains `illegal transition approved -> implemented`. (c) `True`. (d) a `would move` line naming the `implementing/` destination. IF (a) NOW PERMITS `approved -> implemented` DIRECTLY, skip E-03 and say so in V-03 rather than performing a hop the graph no longer requires; the two-hop route is a consequence of the graph, not a goal.
  - Execution state: pending

### Task group 2: perform the two legal hops

- [ ] E-03 MOVE `kw5y2s` `approved -> implementing`, recording the Set that implemented it: `aw specs set "$SPEC" --status implementing --graduated-to wslayout --message "wslayout Set fully executed (all six plans, Orders 00-05, under .aw/records/plans/executed/; orchestrator rh5tt6 carries - From-Spec: kw5y2s); advancing from approved to implementing ahead of the implemented transition, per backlog jd01a0 and the precedent of spec 20260810-1447-01." --yes`.
  - WHY `--graduated-to wslayout` BELONGS ON THIS HOP AND NOT THE NEXT: the specs README documents the field's setter spelling as `aw spec set implementing <id6> --graduated-to <setid>`, i.e. on the `implementing` transition, and the field is the FORWARD half of the `- From-Spec: kw5y2s` link the orchestrator already carries backwards. Setting it here closes that link at the moment the spec starts claiming implementation.
  - WHY THIS HOP IS NOT BOOKKEEPING THEATER: it is the ONLY legal route to `implemented` (E-02a), so skipping it does not shorten the plan, it makes the plan impossible. The precedent spec recorded the identical two-step with the identical reason, which is why E-03's message echoes its wording.
  - Depends on: E-02
  - Expected outcome: `- Status: implementing` in the file; the file now at `.aw/records/specs/implementing/20260901-kw5y2s-01-kw5y2s-...spec.md` and ABSENT from `approved/`; a `- Graduated-To: wslayout` bullet present; a new `implementing` line at the top of `## Workflow history`; `aw specs check` conforming.
  - Execution state: pending

- [ ] E-04 MOVE `kw5y2s` `implementing -> implemented` WITH THE REQUIRED EVIDENCE CITATION, using the spec's NEW path under `implementing/`: `aw specs set "<new-path>" --status implemented --evidence .aw/records/plans/executed/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.ipd.md --message "Implemented by the wslayout Set (all six plans executed): agent_workflows/layout.py is the canonical layout model (Sections 3-5), the eleven-class record vocabulary is closed in BOTH artifact_types.ARTIFACT_TYPES and record_producers.RecordClass (Section 3.2), engine.emit_layout_artifacts writes .aw/system/layout.json + layout.schema.json and back-fills .aw/.gitignore (Sections 2.3/6.1), and aw layout plus check.system-layout-missing/-drift ship the Section 6.2 surface. Re-measured at the executing HEAD per backlog jd01a0 E-01." --yes`.
  - USE THE PATH THE FILE IS AT AFTER E-03, NOT THE ORIGINAL. E-03 relocated it (E-02d measures this), so the `approved/` path no longer exists and passing it would fail to resolve. Re-resolve with `ls .aw/records/specs/implementing/*kw5y2s*` rather than hand-assembling it.
  - THE `--evidence` FLAG IS MANDATORY AND ITS VALUE IS CONSTRAINED, not free prose: `specs._evidence_resolvable` requires a safe, in-tree, EXISTING path under an `executed/` plans tree, so a summary string or a non-executed plan is refused. The orchestrator `rh5tt6` is cited because it is the Set-level artifact carrying `- From-Spec: kw5y2s`; E-02c verifies it resolves before this item runs.
  - Depends on: E-03
  - Expected outcome: `- Status: implemented`; the file at `.aw/records/specs/implemented/20260901-kw5y2s-01-kw5y2s-...spec.md` and ABSENT from both `approved/` and `implementing/`; a new `implemented` history line at the top naming the evidence; `aw specs check` conforming.
  - Execution state: pending

### Task group 3: confirm the tree agrees

- [ ] E-05 CONFIRM THE RECLASSIFICATION AND THE CLEAN TREE, which is the OUTCOME the item actually wants rather than a field edit. Paste: `aw attention --format json` filtered to this spec (for example piping through `python3 -c "import json,sys; [print(r) for r in json.load(sys.stdin).get('items', []) if 'kw5y2s' in json.dumps(r)]"`, adapting the key names to what the command actually emits rather than assuming them) showing its class is now `done` rather than `ready`, plus the `valid` field of the whole view; `aw specs check`; `aw check release-gates`; and `git status --porcelain`.
  - WHY `aw attention` IS THE ACCEPTANCE SURFACE: AGENTS.md says to consume the attention view rather than re-scanning raw files, and a spec at `approved` maps to `ready` while `implemented` maps to `done` (the specs README states the mapping). A status edit that did not move the class would mean the edit did not take effect where it matters. If the view reports `valid: false`, STOP and report the violations rather than claiming success.
  - ALSO CONFIRM NO STALE COPY SURVIVED: `ls .aw/records/specs/approved/ | grep -c kw5y2s` and the same for `implementing/`, both expected `0`, and `ls .aw/records/specs/implemented/ | grep kw5y2s` expected one hit. A relocation that COPIED rather than MOVED would leave two specs with the same `- Id:`, which is a far worse defect than the stale status this plan is fixing.
  - Depends on: E-04
  - Expected outcome: the spec's attention class is `done`; the view's `valid` is `true`; `aw specs check` and `aw check release-gates` both clean; `git status --porcelain` shows ONLY the spec's rename (and nothing outside `- Scope-Paths:`); zero hits in `approved/` and `implementing/`, exactly one in `implemented/`.
  - Execution state: pending

- [ ] E-06 RUN THE SUITE BARE as `python3 -m pytest` and paste the summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
  - WHY THIS IS A CHEAP REGRESSION CHECK AND NOT A COUPLING THIS EDIT SHOULD BREAK: three tests cite `kw5y2s` in PROSE (`test_installer.py`, `test_layout.py`, `test_record_producers.py` per plan `xx5b7a`'s F-07, which measured that none opens the spec by path). RE-MEASURE that rather than inheriting it, with `rg -rn "kw5y2s" tests/`, because this plan MOVES the file and a test that globbed `specs/approved/` would break where a test reading the text would not. If a test does resolve the spec by its directory, report it: that is a real coupling to a path this plan changes.
  - Depends on: E-04
  - Expected outcome: the suite's `N passed` summary with no new failures versus a pre-change baseline; `rg -rn "kw5y2s" tests/` hits are all prose citations, none resolving the spec through `specs/approved/`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN AGENT MAY NOT SET A SPEC `implemented` WITHOUT CITED EVIDENCE (AGENTS.md: an agent "may NOT set `implemented` (needs cited evidence)"). The tooling enforces the evidence half mechanically (`attention_contract.TRANSITION_AUTHORITY['->implemented']` carries `evidence: True`, checked by `specs._evidence_resolvable`), and NOT the judgement half. This is why E-01 re-measures the four points instead of trusting this plan's snapshot, and why OQ-01 asks whether a human must authorize the transition at all.
- A SPEC'S DIRECTORY ALWAYS AGREES WITH ITS `- Status:`, and the setters relocate the file to match (`.aw/records/specs/README.md`: "The status setters ... automatically relocate the file to the matching directory upon status transition"). A plan that changes a spec's status therefore changes its PATH, which is why this plan declares all three paths in `- Scope-Paths:`.
- `- Graduated-To: <setid>` is the FORWARD half of a plan's `- From-Spec: <spec-id6>`, written with `aw spec set implementing <id6> --graduated-to <setid>` (specs README). The `wslayout` orchestrator already carries the backward half.
- DO NOT HAND-EDIT A SPEC'S STATUS OR HISTORY; use the owner verbs, which validate the transition and typed gates, write atomically, and relocate (specs README). This plan therefore performs no text edit of the spec at all.
- A FACTUAL-STATUS CORRECTION TO AN APPROVED SPEC LEAVES IT `approved` (precedent `a59f2c53`), which is why plan `xx5b7a` correctly did NOT fold this transition into its text corrections and raised OQ-01 instead.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `850e6a19` on 2026-10-01.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-01 | INFO | Set `wslayout` | EVIDENCE POINT 1 HOLDS. All six plans (Orders 00-05: `rh5tt6`, `wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`) are under `.aw/records/plans/executed/`, and the orchestrator carries `- From-Spec: kw5y2s`. | `find .aw/records/plans -name "*wslayout*" \| sort` -> six paths, every one under `executed/`; `grep -n "From-Spec" ...rh5tt6...` -> `- From-Spec: kw5y2s` |
| F-02 | INFO | `agent_workflows/layout.py`, `aw layout` | EVIDENCE POINT 2 HOLDS (spec Sections 3/4/6). The module exists and the CLI verb resolves. | `ls -la agent_workflows/layout.py` -> present; `aw layout --help` -> `usage: agent-workflows layout ... [--schema]`, exit 0 |
| F-03 | INFO | `artifact_types.ARTIFACT_TYPES`, `record_producers.RecordClass` | EVIDENCE POINT 3 HOLDS (Section 3.2's union ruling). All eleven record classes are in BOTH vocabularies; `RecordClass` additionally carries the `records` root carve-out Section 3.2.1 requires. | the eleven-row census: every row `True True`; `len(AT)` 11, `len(RC)` 12, `RC-AT == ['records']`, `AT-RC` empty |
| F-04 | INFO | `agent_workflows/engine.py`, `.aw/.gitignore` | EVIDENCE POINT 4 HOLDS (Sections 2.3/6.1). `engine.py` defines `AW_LAYOUT_JSON_PATH` and `AW_LAYOUT_SCHEMA_PATH`, `engine.emit_layout_artifacts` writes both, and the `.aw/.gitignore` back-fill is present and EFFECTIVE. The root `.gitignore` is untouched, as Section 2.3 requires. | `grep -n "layout.json\|layout.schema.json" agent_workflows/engine.py` -> the two path constants plus the emitter and the gitignore back-fill loop; `git check-ignore -v .aw/system/layout.json .aw/system/layout.schema.json` -> both matched by `.aw/.gitignore:33` and `:34`; `grep -c layout .gitignore` -> `0` |
| F-05 | HIGH | `attention_contract.SPEC_TRANSITIONS` | **THE BACKLOG ITEM'S PRESCRIBED COMMAND CANNOT BE RUN AS WRITTEN: `approved -> implemented` IS ILLEGAL AND IS REFUSED.** The item says to "run `aw specs set implemented` with the cited evidence", but `SPEC_TRANSITIONS['approved']` is `{implementing, reviewed, deferred, parked, superseded}` and contains no `implemented`. The attempt fails at the graph gate BEFORE the evidence gate, so a perfectly resolvable `--evidence` citation does not help. The transition requires the `implementing` hop, which is why this plan has two move items rather than one. This is a defect in the ITEM'S RECIPE, not in the tooling: the graph is behaving as the specs README documents. | `python3 -c "...SPEC_TRANSITIONS['approved']..."` -> `['deferred', 'implementing', 'parked', 'reviewed', 'superseded']`; `transition_allowed('approved','implemented')` -> `False`; and the live refusal `aw specs set <spec> --status implemented --evidence <executed rh5tt6 path> --dry-run` -> `aw specs set: illegal transition approved -> implemented` |
| F-06 | MEDIUM | the specs status setter | **THE SETTER RELOCATES THE FILE, SO THIS PLAN CHANGES THE SPEC'S PATH TWICE.** The specs README states the directory always agrees with the status and that the setters relocate on transition; measured directly, a dry-run `--status implementing` prints `would move .aw/records/specs/approved/...kw5y2s... -> .aw/records/specs/implementing/...kw5y2s...`. Two consequences the plan must handle rather than discover: E-04 must use the NEW path (the `approved/` one will not exist), and `- Scope-Paths:` must declare all THREE paths or the finalize scope gate sees an undeclared write. | `aw specs set <spec> --status implementing --graduated-to wslayout --dry-run` -> the `would move ... -> .../specs/implementing/...` line; `.aw/records/specs/README.md` "The status setters ... automatically relocate the file to the matching directory upon status transition" |
| F-07 | HIGH | pending plan `xx5b7a` | **A PENDING PLAN DECLARES THE PATH THIS PLAN MOVES, SO ORDER IS LOAD-BEARING.** `xx5b7a` (Set `speckwfix`, `- Status: approved`, `- Readiness: go-pending-approval`) declares exactly `.aw/records/specs/approved/20260901-kw5y2s-...spec.md` in its `- Scope-Paths:` and edits that file in five places. If THIS plan executes first, that path no longer exists: `xx5b7a`'s E-01 measurements would fail to resolve, its `aw commit` path would name a nonexistent file, and its finalize scope reconciliation would be against a stale declaration. The reverse order is harmless, because `xx5b7a` only edits text and leaves `- Status: approved` untouched (its own OQ-01 says so explicitly). Hence `- Item-Dependencies: executed:xx5b7a`. | `grep -rln "specs/approved/20260901-kw5y2s" .aw/records/plans/pending/` -> the `xx5b7a` plan; its `- Scope-Paths:` line; its OQ-01 "This plan therefore corrects the text and leaves `- Status: approved` untouched" |
| F-08 | INFO | precedent spec `20260810-1447-01` | THE TWO-HOP ROUTE HAS AN EXACT PRECEDENT IN THIS TREE, including the reason to state in the message. That spec's history records `- 2026-08-17 implementing (aw specs): awphysical Set executing/complete; advancing from approved to implementing ahead of the implemented transition.` followed next day by its `implemented` line. Three further implemented specs (`20260813-1833-01`, `20260815-0151-01`, `20260818-1525-03`) show the same `implementing` then `implemented` pair, so E-03 is the house style rather than an invention. | `grep -n "implementing (aw specs)" .aw/records/specs/implemented/20260810-1447-01-*.spec.md` -> the quoted line; the same grep across `implemented/` -> the three further pairs |
| F-09 | INFO | `specs._evidence_resolvable` | THE INTENDED EVIDENCE CITATION ALREADY RESOLVES, so E-04 will not be refused at the evidence gate. The predicate requires a safe, in-tree, EXISTING path under an `executed/` plans tree; the `wslayout` orchestrator satisfies it. Verified by calling the predicate directly rather than by inspecting its source. | `specs._evidence_resolvable(<spec path>, '.aw/records/plans/executed/20260901-wslayout-00-rh5tt6-...ipd.md')` -> `True` (also `True` for the Order 01 child, so the citation choice is not fragile) |
| F-10 | MEDIUM | `TRANSITION_AUTHORITY['->implemented']` | **THE TOOL CHECKS THE CITATION, NOT THE CLAIM, SO E-01 IS THE REAL GATE.** The authority entry is `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': True}`: no human attestation is required, and `specs._evidence_resolvable` verifies the path RESOLVES to an executed IPD, not that the spec is implemented. `APPROVAL_FLOOR` states this limit in terms ("aw specs enforces presence + format + resolvability, NOT semantic verification that the work truly happened"). So a plan could satisfy every gate while writing a false `implemented`; what prevents that here is E-01's measurement, not the tooling, which is also why OQ-01 is worth asking. | the authority dict as printed; `APPROVAL_FLOOR`'s quoted sentence in `attention_contract.py`; `->implemented` carries `by_human: False` where `->approved` carries `by_human: True` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the backlog item's four evidence points at the executing HEAD, with an explicit stop if any fails.
2. E-02 re-measures the two mechanics this plan turns on (the transition graph plus its live refusal, the evidence predicate, and the relocation), with an explicit branch if the graph has changed.
3. E-03 moves the spec `approved -> implementing`, recording `- Graduated-To: wslayout`.
4. E-04 moves it `implementing -> implemented` with the resolvable executed-IPD evidence citation, using the relocated path.
5. E-05 confirms the outcome on the acceptance surface: `aw attention` reclassifies the spec `ready -> done`, the checks stay clean, and exactly one copy of the spec exists.
6. E-06 runs the bare suite and re-measures that no test resolves the spec through the directory this plan moves it out of.

## Deferred / out of scope (with reason)

- Every word of spec `kw5y2s`'s BODY, including the five stale passages in Sections 1.2, 3.2, 5.1 and the missing snapshot convention.
  - Carrier-Declined: owned by plan `xx5b7a`, which this plan depends on (F-07). Editing the same file for two unrelated reasons in two plans would collide; this plan changes only the status field and the file's location, both through the owner verbs.
- Section 3.4's traversal-exclusion widening (`node_modules`, `venv`, `.venv`).
  - Carrier-Declined: the spec itself declares it OUT of scope ("Adding them is a DELIBERATE BEHAVIOR CHANGE ... out of scope for the initial model"), and the backlog item repeats that it is not a blocker. An unimplemented out-of-scope idea does not prevent the spec being implemented.
- Any code, test, or `AGENTS.md` change.
  - Carrier-Declined: nothing is broken. F-05's refusal is the documented graph working correctly, and F-10's limit is stated deliberately in `APPROVAL_FLOOR`. This plan consumes the lifecycle rather than changing it.
- Whether `->implemented` SHOULD require a human attestation given F-10.
  - Carrier-Declined: that is a change to the authority contract affecting every spec, far outside a status transition for one spec. OQ-01 raises the narrow question for THIS spec; a general change would need its own spec amendment.

## Scope check

- Over-scope: none. The plan touches exactly one artifact, the spec, and changes only its `- Status:`, its `- Graduated-To:`, its history, and its directory, all through `aw specs set`. The three declared paths are the SAME FILE at its three successive locations, not three artifacts.
- Under-scope: the backlog item also admits the alternative outcome, "record why the spec stays approved". This plan commits to the TRANSITION because all four evidence points were measured to hold (F-01..F-04); if E-01 finds one failing, its stop condition fires and the alternative becomes the honest outcome, which V-01 must then record rather than pressing on.
- Under-scope, ACCEPTED AND STATED: this plan does not verify every normative clause of the spec's Sections 5-7 individually, only the four points the item names plus the Section 6.2 check rule reached incidentally through F-04. A full clause-by-clause audit of a 438-line spec is a different and much larger exercise; the item defines the evidence standard and this plan meets it.
- Scope-Paths justification: three paths for one file because the setter relocates it (F-06). The `approved/` path is the pre-state (deleted by E-03), `implementing/` the intermediate (created by E-03, deleted by E-04), `implemented/` the terminal (created by E-04). Declaring only one would leave two of the three writes undeclared at finalize.

## Required tests / validation

- `aw specs check` after EACH hop (E-03, E-04), so a failure is attributable to one transition rather than to the pair.
- `aw attention` showing the spec's class moved from `ready` to `done`, with the view's `valid` field `true` (E-05). This is the acceptance surface, not the file contents.
- `aw check release-gates` clean (E-05), confirming no gate was disturbed; the spec carries no `- Blocks-Release:` and must not acquire one.
- A directory census proving exactly ONE copy of the spec survives (E-05), guarding against a copy-rather-move defect that would duplicate an `- Id:`.
- Bare `python3 -m pytest` (E-06) with the summary line pasted, plus a re-measurement that no test resolves the spec through `specs/approved/`. Run it BARE: no `-n0`, no second `-q`, no `-p no:randomly`.

## Spec / documentation sync

- THIS PLAN CHANGES SPEC `kw5y2s`'s STATUS AND LOCATION, declared in `- Scope-Paths:` as all three successive paths. WHY: the spec is shipped (F-01..F-04) but reads `approved`, so `aw attention` advertises a completed design as `ready` work and any agent reading the tree is told the implementation is still owed. It amends NO normative clause and edits NO prose; the only writes are those `aw specs set` makes (`- Status:`, `- Graduated-To:`, a history line, and the relocation). Both runners announce declared spec edits before the run and reconcile them at finalize, so the three declared paths are what makes this visible rather than a surprise.
- No user-facing docs change. The specs README already documents the status enum, the relocation behavior, and the `--graduated-to` spelling this plan uses; nothing in it needs correcting.

## Open questions

### OQ-01: Must a human authorize this `implemented` transition, given that the tooling does not require it?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: THE AUTHORIZATION IS ALREADY ON RECORD, SO THIS QUESTION OWES NOTHING AND NEEDS NO CARRIER. The tension is real and worth naming: AGENTS.md says an agent "may NOT set `implemented` (needs cited evidence)", while the tooling's `->implemented` authority is `by_human: False` with only `evidence: True` (F-10). Two readings exist. The STRICT reading treats the parenthetical as a human-only gate, which would forbid E-04 outright. The reading this plan adopts is that the parenthetical names the CONDITION (cited evidence) rather than a second actor, which is exactly why the machinery demands a resolvable citation and NOT `--by-human`, in deliberate contrast to `->approved`, which does carry `by_human: True`; the two entries sit adjacent in `TRANSITION_AUTHORITY` and differ precisely on this point, so the asymmetry is designed rather than an omission. WHAT DECIDES IT is neither reading but the maintainer's recorded instruction: backlog item `jd01a0` exists to settle this question and its "WHAT TO DO" says to verify the four points and "then either run aw specs set implemented with the cited evidence, or record why the spec stays approved". That is an explicit, conditional authorization to transition when the evidence holds, and AGENTS.md's backlog-graduation contract directs an agent to "record the maintainer's instruction as the approval attestation ... rather than stopping for a separate approve round trip" and to resolve open questions from repository evidence, asking a human only where the repo cannot answer. The repo answers here, so this is recorded as resolved rather than parked on a carrier. THE RESIDUAL HUMAN CONTROL IS NOT LOST, it is relocated to plan approval: E-01 carries a hard stop if any evidence point fails, and a maintainer who would rather run the two commands personally can say so at review, striking E-03/E-04 and leaving this a verification-only plan whose E-01, E-02 and E-05 measurements stand unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste all four E-01 outputs (a) through (d) VERBATIM, including the complete eleven-row census with both boolean columns rather than a summary, and the `git check-ignore -v` lines in full. State the executing HEAD from `git rev-parse HEAD`. Then state, in one sentence per point, whether it HOLDS. IF ANY POINT FAILED, this item must record that the plan STOPPED and that the honest outcome is the backlog item's alternative branch ("record why the spec stays approved"), naming the failing point; do NOT mark it verified on three of four.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste (a) the three transition-graph lines and the authority dict, (b) the VERBATIM refusal text of the one-step attempt including the words `illegal transition approved -> implemented`, (c) the `_evidence_resolvable` boolean, and (d) the `would move` line. THE LOAD-BEARING CHECK IS (b): it is what proves F-05 empirically rather than by reading a table, and it is the reason this plan has two move items instead of the one the backlog item asked for. If (a) now permits `approved -> implemented` directly, state that here and explain what E-03 did instead.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw specs set` invocation and its output; the resulting `- Status: implementing` line; the `- Graduated-To: wslayout` line; the new top-most `## Workflow history` record; `ls .aw/records/specs/implementing/ | grep kw5y2s` (one hit) alongside `ls .aw/records/specs/approved/ | grep -c kw5y2s` (`0`); and `aw specs check` conforming. Also paste `git status --porcelain` for this hop showing the move as a RENAME (`R`) rather than an add plus an unrelated delete, so the file's history is preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw specs set` invocation (showing the `implementing/` path was used, not the original `approved/` one) and its output; the resulting `- Status: implemented` line; the new history record naming the evidence citation; `ls .aw/records/specs/implemented/ | grep kw5y2s` (one hit); and `aw specs check` conforming. CONFIRM EXPLICITLY that the `--evidence` value names a file that exists under `.aw/records/plans/executed/`, by pasting `ls` on that exact path, since the transition is gated on resolvability and a plan quoting a path it never listed has not shown the gate was really satisfied.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw attention` output for this spec showing its class is `done` (and state what it was BEFORE, namely `ready`, from a pre-change run or from the mapping the specs README documents), plus the view's `valid` field. Paste `aw specs check` and `aw check release-gates` outputs. Paste the three directory censuses (`approved/` `0`, `implementing/` `0`, `implemented/` exactly one). Paste `git status --porcelain` and confirm in one sentence that no path outside `- Scope-Paths:` was modified. If `aw attention` reports `valid: false`, this item FAILS regardless of the spec's own class.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line (the `N passed` line; if it is missing you added a second `-q`, so re-run bare). State the after-minus-before failing node-ID set, which must be empty. Paste the full `rg -rn "kw5y2s" tests/` output with a one-line statement per hit confirming it is a prose citation rather than a resolution of the spec through `specs/approved/`. If any test DOES resolve it by directory, say so and report it as a real coupling this plan's relocation broke.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Two `aw specs set` commands that move spec `kw5y2s` from `approved` to `implemented`, plus the measurements that justify them. NO PROSE IN THE SPEC IS EDITED and no code or test changes; the only writes are the ones the owner verb makes (`- Status:`, `- Graduated-To: wslayout`, a history line per hop, and the file's relocation through two directories). The spec is shipped on all four of the evidence points backlog `jd01a0` names, each RE-MEASURED at HEAD `850e6a19`: six `wslayout` plans executed with the orchestrator carrying `- From-Spec: kw5y2s`, `agent_workflows/layout.py` plus a resolving `aw layout` verb, all eleven record classes present in BOTH vocabularies, and install-time emission wired with an EFFECTIVE `.aw/.gitignore` back-fill (`git check-ignore` confirms) and an untouched root `.gitignore`.

THREE THINGS THAT DEPART FROM THE BACKLOG ITEM'S LETTER, all measured. FIRST, THE ITEM'S COMMAND CANNOT BE RUN: it says to "run `aw specs set implemented`", but `approved -> implemented` is ILLEGAL (`SPEC_TRANSITIONS['approved']` has no `implemented` member) and the live attempt prints `illegal transition approved -> implemented`, failing at the graph gate before the evidence gate. So this plan performs the mandatory `implementing` hop first, exactly as spec `20260810-1447-01` recorded doing with the same stated reason. SECOND, THE SPEC'S PATH CHANGES TWICE, because the setter relocates the file to match its status; `- Scope-Paths:` therefore declares all three successive paths for the one file, and E-04 must use the relocated path rather than the original. THIRD, THIS PLAN MUST NOT RUN FIRST: pending plan `xx5b7a` (`approved`) declares the CURRENT `approved/` path in its own `- Scope-Paths:` and edits that file in five places, so executing this plan before it would invalidate its declaration and its commit path. That is why `- Item-Dependencies: executed:xx5b7a` is declared; the runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` rather than run it out of order, and an agent executing by hand must honor the same order.

THE HONEST LIMIT ON WHAT THE TOOLING GUARANTEES, stated because it decides where the real gate is. The `->implemented` authority is `{'who': 'executor', 'by_human': False, 'evidence': True}`, and `APPROVAL_FLOOR` says plainly that `aw specs` enforces "presence + format + resolvability, NOT semantic verification that the work truly happened". A resolvable path to any executed IPD would therefore satisfy the machinery. What makes this transition TRUE rather than merely permitted is E-01's measurement of the four points, which is why V-01 requires the raw outputs pasted and why it must record a STOP rather than a pass if any point fails. OQ-01 raises the related question of whether a human must authorize the transition at all, recommends that approving this plan IS that authorization (the backlog item instructs the transition on the evidence holding), and is non-blocking because striking E-03/E-04 leaves the rest of the plan intact.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the single spec file at its three successive paths. If an edit outside it proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path. Note that exactly TWO of the three declared paths will be unmodified-as-declared in the terminal state (the `approved/` and `implementing/` paths end up absent), which is the expected consequence of a relocation and should be acknowledged rather than treated as a scope violation.

HONESTY RULE (hard MUST): every claim pastes the ACTUAL command output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITIONS:
1. If E-01 finds ANY of the four evidence points failing, stop and report it. The honest outcome is then the backlog item's own alternative branch, "record why the spec stays approved", and the spec must NOT be transitioned.
2. If the spec's `- Status:` is no longer `approved` when E-03 runs, stop and report: someone else moved it, and this plan's premise needs re-establishing against whatever state it is in.
3. If plan `xx5b7a` has NOT reached `executed`, do not execute this plan (the declared dependency). The runner enforces this; a hand executor must too.
4. If E-04's `--evidence` citation fails to resolve, stop rather than substituting a different citation to get past the gate: a citation chosen to satisfy a check rather than to name the implementing work is the exact failure F-10 warns about.
5. If E-05's `aw attention` reports `valid: false`, stop and report the violations; the spec's own class being `done` does not redeem an invalid view.

Commit ONLY the spec's relocation through `aw commit dwivqd -- .aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md .aw/records/specs/implementing/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md .aw/records/specs/implemented/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md` (never `git add -A`, never push). NOTE that `aw specs set` offers to commit its own change (`--commit`/`--no-commit`); if you let it commit, do not then re-commit the same change, and say in V-03/V-04 which surface made the commit. The runner announces this declared spec edit before the run starts. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Backlog `jd01a0` reaches `graduated` on this plan being authored and `done` once this plan has executed.
