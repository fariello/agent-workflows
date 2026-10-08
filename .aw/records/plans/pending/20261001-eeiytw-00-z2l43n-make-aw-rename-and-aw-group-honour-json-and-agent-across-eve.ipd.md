# IPD: Make aw rename and aw group honour --json and --agent across every artifact type

- Date: 2026-10-01
- Kind: orchestrator
- Concern: `aw rename <type>` and `aw group <type>` emit NO `aw.agent/v1` payload under `--json` or `--agent`. Measured at HEAD: `'aw.agent/v1' in stdout` is False, stdout contains no `{` whatsoever, `json.loads(stdout)` raises, and a per-line JSONL scan recovers ZERO payload-shaped records on BOTH flags. This holds on all NINE artifact types, on preview and apply, on every refusal path, and on two further command spellings (`aw research mv`, `aw research set-assign`). A programmatic consumer cannot script either verb today. Three written contracts are violated at once: `docs/cli-output-contract.md` Section 7 (stdout "reserved strictly for final structured results"), Section 11.3 (the mutation feedback convention, which specifies the preview record field by field), and implemented spec `command-surface-redesign` R4/AC5 ("Every cross-cutting verb honors `--json`/`--agent`"). The repository's own `command_surface` inventory ALREADY declares both flags on both verbs, so the promise is made in machine-readable form and then not kept.
- Scope: Orchestrate the three children that close backlog item `eeiytw`: carry the facts out of the backends (Order 01), emit the payload once at each dispatch site (Order 02), and silence the nested manifest-refresh line so stdout is strictly parseable (Order 03). This plan performs NO work of its own; every deliverable belongs to a child.
- Scope-Paths: .aw/records/plans/pending/20261001-eeiytw-01-x7unul-carry-the-rename-and-group-facts-out-of-the-backends-in-a-ty.ipd.md, .aw/records/plans/pending/20261001-eeiytw-02-vfqjc0-emit-the-aw-agent-v1-payload-once-at-the-rename-and-group-di.ipd.md, .aw/records/plans/pending/20261001-eeiytw-03-gzb2rq-silence-the-nested-index-refresh-and-pin-the-machine-surface.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 5aa8e931bef7d7271a7e6fd1aae9ded0c6784b348b0704be92c24c4861a8a649
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: low
- From-Backlog: eeiytw
- Blocks-Release: next
- Set: eeiytw
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: z2l43n
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD e643abfd5. Cross-IPD checks each name their real owning child V-item; 87m438 recorded as executed; index exclusion now cites open carrier 4izduy (4uw9gy is done); eeiytw open state noted; scope-fence wording added. Coverage repair 2 attempts, passing. Review record .aw/records/reviews/20261001-eeiytw-00-z2l43n-make-aw-rename-and-aw-group-honour-json-and-agent-across-eve.review.md.
- 2026-10-07 coverage pass (aw oc run): fingerprint 5aa8e931bef7, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 9c6fbbdb55a9, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 to-review (aw set): returned to review: every Set-level check the coverage probe quoted now names its owning child (Order 03 gzb2rq) and the backlog close is the runner's; coverage pass recorded
- 2026-10-07 coverage pass (aw oc run): fingerprint 714c6c0da391, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 12f5ccbc860e, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Close backlog item eeiytw by making both verbs emit exactly one parseable aw.agent/v1 record

- 2026-10-06 coverage fail (aw oc run): fingerprint c90c03dc9e47, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `eeiytw` together with its three children. Every claim in this plan and its children was MEASURED at HEAD `f824b915f` through the real CLI in throwaway git repos. The item's diagnosis is CORRECT on its headline claim and NARROWER than the defect in two measured ways, both corrected in the children rather than repeated: it says "plans" where the defect spans all nine types, and it names one un-quieted `run_index` call where there are two.

## Goal

Make both verbs emit exactly one parseable `aw.agent/v1` record on stdout under `--json` and `--agent`, on every artifact type, on preview, apply and refusal, so that `json.loads(stdout)` succeeds where it raises today. The work is split across three children because it contains three different KINDS of change with three different reviewer questions: a wide mechanical plumbing change across four modules that must alter no output, a narrow behavioral change at two dispatch sites that defines a machine contract, and one deliberate human-output change. Landing them together would make each unreviewable, because a reviewer could not attribute a broken test to the right half. Backlog item `eeiytw` currently reads `- Status: open` (reopened by the 2026-10-06 coverage demotion; re-graduating it is a backlog-tier act outside this Set), and it is closed by the runner's normal backlog close when the last of the three children executes (every child carries `- From-Backlog: eeiytw`); neither this plan nor any child closes it by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS ORCHESTRATOR CARRIES ORCHESTRATION ONLY AND NO WORK OF ITS OWN. Every item below confirms a child reached `executed`; none produces a deliverable, establishes a baseline, or reconciles records. That is deliberate: a runner RETIRES an orchestrator once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, on the premise that the parent's own items are performed by nobody. Work parked here would therefore be marked complete having never been performed. If a reviewer finds work this Set needs that no child covers, the remedy is to ADD A CHILD and a row to the table below, never to add an item here.

### Task group 1: confirm each child reached executed, in dependency order

- [ ] E-01 CONFIRM x7unul REACHED executed
  - Depends on: none
  - Expected outcome: `.aw/records/plans/executed/` contains `x7unul` with `- Status: executed`, and the facts the later Orders consume (per-target old/new pairs, the applied flag, reference edits, diagnostics, notes) are present on the shared `MutationResult` with human stdout byte-identical to HEAD.
  - Execution state: pending

- [ ] E-02 CONFIRM vfqjc0 REACHED executed
  - Depends on: E-01
  - Expected outcome: `.aw/records/plans/executed/` contains `vfqjc0` with `- Status: executed`, and `aw rename specs --json` / `aw group specs --json` (the types with no nested index line) emit exactly one parseable `aw.agent/v1` record.
  - Execution state: pending

- [ ] E-03 CONFIRM gzb2rq REACHED executed
  - Depends on: E-02
  - Expected outcome: `.aw/records/plans/executed/` contains `gzb2rq` with `- Status: executed`, and `json.loads(stdout)` succeeds for `aw rename plans --apply --json` and `aw group plans --apply --json`, the two commands backlog item `eeiytw` names.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `x7unul` | `20261001-eeiytw-01-x7unul-carry-the-rename-and-group-facts-out-of-the-backends-in-a-ty.ipd.md` | Widens the shared `MutationResult` with optional defaulted fields and populates them in `plans_refs`, `artifact_rename` and `research_refs`, so the facts a payload needs survive the backend's return. Changes no emitted byte and no exit code; its central claim is a NEGATIVE one, pinned by byte-equality tests. | none |
| 02 | `vfqjc0` | `20261001-eeiytw-02-vfqjc0-emit-the-aw-agent-v1-payload-once-at-the-rename-and-group-di.ipd.md` | Maps those facts onto a `CommandResult` and emits once per invocation at BOTH dispatch sites (`_run_noun_verb` and the `research_cmd in ("set-assign","mv")` branch), suppressing the backends' prose only in machine mode. Also amends `docs/cli-output-contract.md` to resolve a self-contradiction about `complete` on a preview record. | `executed:x7unul` (Order 01) |
| 03 | `gzb2rq` | `20261001-eeiytw-03-gzb2rq-silence-the-nested-index-refresh-and-pin-the-machine-surface.ipd.md` | Adds `quiet=True` to the two nested `run_index` calls that omit it, reports the manifest refresh as a `Change` instead of a stdout line, and tightens Order 02's assertions from payload-recoverability to strict `json.loads(stdout)` for `plans` and `research`. Contains the Set's ONE deliberate human-output change. | `executed:vfqjc0` (Order 02) |

## Completion criteria (the whole Set is done only when)

OWNERSHIP, stated once for every criterion and cross-check below: Order 03 `gzb2rq` performs the Set-wide end-to-end checks after the last child (its E-04 and V-04 assert strict `json.loads(stdout)` on all four types, the human-surface change, the manifest `Change`, the commit path-set and the two index verbs, and run the bare suite against its own baseline); Orders 01 `x7unul` and 02 `vfqjc0` each prove their own byte-equality and parseability claims and run the bare suite at their own boundary. This plan performs none of them.

- All three children are in `.aw/records/plans/executed/` with `- Status: executed`, each with every `V-*` item carrying concrete pasted evidence.
- `json.loads(stdout)` SUCCEEDS for `aw rename <type> --json` and `aw group <type> --json` on at least `plans`, `specs`, `backlog` and `research`, on preview AND apply. This is the item's headline claim and the Set is not done without it on the `plans` type specifically, which is the one the item names.
- Under `--agent`, every non-blank stdout line parses and exactly ONE carries `schema == "aw.agent/v1"`, on the same types and paths.
- A refusal emits an `error` record (`kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `verified` false, `complete` false) with a non-empty `diagnostics`, and the process exit code equals the record's `exit` on every measured path.
- `aw rename all` / `aw group all` emit exactly ONE record for the whole invocation, not one per expanded type, carrying the mixed outcome (the successful change AND the no-match diagnostics) that the `all` expansion really produces.
- `aw research mv --json` and `aw research set-assign --json` each emit one parseable record, since they reach the same backend from a different dispatch site.
- No emitted record contains an absolute filesystem path, and `aw sanitize --agent` is clean.
- The HUMAN surface is unchanged except for the single deliberate removal Order 03 owns (the nested manifest-refresh line), and that removal is pinned by a test rather than left to be rediscovered as a regression.
- `aw index plans` and `aw research index` run directly still print their own outcome lines, proving the nested CALLER was silenced and not the verb.
- A commit made by `aw rename plans --apply --commit` contains no manifest path.
- Bare `python3 -m pytest` is green against the executor's own clean-tree baseline, with the two pre-existing live-corpus failures recorded in each child's Findings confirmed still pre-existing and not absorbed as targets.

## Cross-IPD validation

Each check below names the child V-item that performs it (corrected at review 2026-10-07: `gzb2rq` V-04 alone does not cover every bullet, so each bullet now names its real owner).

- NO DOUBLE-EMIT ACROSS THE TWO DISPATCH SITES. Orders 02 and 03 both touch the research path, and `research_refs` is reachable from two call sites. [Owner: `vfqjc0` V-05(a) for `aw research mv`/`set-assign`, `vfqjc0` E-06(a)/(e) and `gzb2rq` V-04(a) for `aw rename research`.] Confirm `aw rename research --json` and `aw research mv --json` each emit exactly ONE `aw.agent/v1` record, counted explicitly, not merely "at least one". The repository already learned this lesson for the sibling concern: `_run_noun_verb`'s own comment records that the self-commit offer is placed at the dispatch site "ONCE ... (PR-012: never inside a shared backend, or `aw group research` would double-fire)".
- THE BYTE-EQUALITY CLAIMS MUST COMPOSE RATHER THAN CONTRADICT. Order 01 asserts human stdout is byte-identical; Order 02 asserts the same six invocations stay byte-identical and that suppression fires only under a machine flag; Order 03 then DELIBERATELY changes human stdout on those same invocations. [Owner: `x7unul` V-02(d)/V-03(d), `vfqjc0` E-06(f), `gzb2rq` V-01(b)/V-02(c).] Confirm the three are consistent in sequence: identical after 01, identical after 02, and differing after 03 by exactly the manifest line and nothing else. If Order 03's diff removes anything more, the Set's human-surface claim is false.
- THE ASSERTION TIGHTENING ACTUALLY HAPPENED. Order 02 is permitted to assert payload RECOVERABILITY for `plans` and `research` because the nested line is still present when it lands; Order 03 must REPLACE that with strict `json.loads(stdout)`. [Owner: `gzb2rq` V-04(b).] Confirm no loose assertion survives beside the strict one, because a passing loose assertion would hide a later regression in the strict property.
- NO SPEC WAS AMENDED AND ONE DOC WAS. No child's `- Scope-Paths:` names a `.spec.md` (an authored fact, re-measured at review 2026-10-07, and the finalize scope gate refuses an undeclared edit), because the Set makes code obey contracts already written. The single documentation amendment is the one Order 02 declares (`docs/cli-output-contract.md` Section 5's `complete` value), with Section 11.3's rule text untouched. [Owner: `vfqjc0` V-01(a), which fails on any doc diff beyond that one value.]
- THE COMMIT PATH-SET INVARIANT HOLDS THROUGHOUT. Orders 01 and 03 both touch the structure that feeds `_offer_records_commit`. [Owner: `gzb2rq` V-03(b)/V-04(d) for plans, `vfqjc0` V-05(d) for research.] Confirm no manifest path (`INDEX.json`, `INDEX.md`) ever enters a commit, which `MutationResult`'s own docstring prohibits citing idxuntrack `4r0qp1` E-03.
- THE SHARED-FILE HAZARD WAS HANDLED. All three children declare `agent_workflows/plans_refs.py` or a sibling backend, and plan `87m438` (Set `awrenamesel`) declared `agent_workflows/plans_refs.py` for an unrelated selector fix. Re-measured at review 2026-10-07: `87m438` is now in `executed/`, so its change is already on the base every child starts from and is no longer a concurrent edit. [Owner: each child's own diff-by-inspection V-01(a), which fails on any change beyond its declared edit.] Note for a human reading this as a RUNTIME risk rather than an authoring note: `aw oc run` / `aw agy run` give each execute item its own isolated worktree and return changes through a merge-and-revalidate gate, so file overlap is not a scheduling hazard; this item is about a HAND edit or a genuinely unresolvable conflict at merge.

## Deferred / out of scope (with reason)

- **`aw index <type>` and `aw archive <type>` having the same missing-payload defect.** Measured: `aw index plans --json` emits a bare `wrote ...` line and no payload; `aw archive plans --json` emits the human sweep listing. `index` overlaps item `4uw9gy` (now `done`), whose own notes warn that `--limit` on `index` means a HOT-WINDOW SIZE that IS honoured in the human path, so a fixer must not unify it with the other verbs. `archive` declares neither flag in `command_surface`, so giving it one is a surface ADDITION rather than a contract fix, and it dispatches through `_run_archive` rather than `_run_noun_verb`.
  - Carrier-Declined: NOTHING IS OWED BY THIS SET. The only part of `aw index` that touches these two verbs is the nested regeneration line, and Order 03 silences it at the CALLER. `index`'s own machine surface is CARRIED by open backlog `4izduy` ("aw index --agent emits bare human text instead of an aw.agent/v1 record on its write path", `- Blocks-Release: next`), re-measured at review 2026-10-07, and duplicating it here would create two items for one defect. For `archive` there is no broken promise at all: its own declaration lists no machine flag, so nothing is violated, and adding one is a maintainer's feature decision rather than an executor's bug fix. Both were measured rather than assumed, which is what distinguishes a scoping decision from an oversight.
- **Reviving the dormant conformance harness.** `tests/conformance_matrix.required_scenarios` computes a REQUIRED `json` scenario and a `success_preview` scenario for both verbs, and three reviewed goldens exist authored for `cmd: "rename"` carrying exactly the record shape this Set builds. Nothing executes any of it: `build_matrix`, `required_scenarios` and `GOLDEN_DIR` have no callers outside their own definitions, and the one live agent sweep filters to `read`/`check`/`bare` classes, excluding both `mutation`-class verbs. That is WHY the suite is green today despite the defect, and it is worth a reviewer knowing: this Set authors its own targeted coverage rather than depending on a harness that asserts nothing.
  - Carrier: h0tiaw
- **Moving the refusal prose from stdout to stderr on the HUMAN surface.** `docs/cli-output-contract.md` Section 11.4 assigns a human usage error to stderr; these verbs print refusals to stdout. The Set fixes the MACHINE surface (a refusal becomes an `error` record on stdout, which Section 7 requires) and deliberately leaves the human stream where it is, because four live parametrized tests in `tests/test_group_verb_policy.py` assert on `no plan has Id 'zzzzzz'` reaching STDOUT and moving it breaks them.
  - Carrier-Declined: NOTHING IS OWED BY THIS SET, because after Order 02 the machine surface is contract-correct without the human stream moving: in machine mode the prose is suppressed entirely and a structured `error` record takes its place. What remains is a human-surface stream preference with its own test population to reconcile, which is a separate defect for a separate owner. Recorded so a reviewer sees it was measured and scoped out deliberately rather than missed.
- **The `index all` crash.** Measured incidentally while probing `all` expansion: `aw index all --json` exits 1 with an unhandled `FileNotFoundError` from `prompts_index.run_index` writing into a non-existent `.aw/records/prompts/` directory.
  - Carrier-Declined: NOTHING IS OWED BY THIS SET, because it is a different defect (an unguarded directory write) on a different verb (`index`) that no child modifies. It is recorded rather than dropped because an executor probing `all` expansion WILL hit it and should know it is pre-existing and not caused by this Set. Whether to file an item from this measurement is a maintainer's scoping call, not an authoring side effect.

## Scope check

- Over-scope: none. This plan's `- Scope-Paths:` are its three children and nothing else, which is correct for an orchestrator that performs no work.
- Under-scope: the four items argued in Deferred. The Set's own claim is bounded and stated honestly: it closes the missing-payload defect on `rename` and `group` (and the two research spellings), and it does NOT claim to close the same defect class on `index` or `archive`. The three children between them cover every path the backlog item names plus the two it did not (all nine types, and the second un-quieted `run_index` call).

## Required tests / validation

- Each child's own `## Required tests / validation` section, in full. This plan adds no test of its own.
- The Set-wide end-to-end check, performed by Order 03 `gzb2rq` (V-04 (e)): `json.loads(stdout)` succeeding for `aw rename plans --apply --json` and `aw group plans --apply --json` in a throwaway repo, which are the exact two commands backlog item `eeiytw` names.
- Bare `python3 -m pytest` green against the executor's own clean-tree baseline after each child, run by each child in its final V-item.
- `aw check all` clean on this repository (Order 02 `vfqjc0` edits a documentation file and checks it), `aw sanitize --agent` clean, and `aw ipd lint --phase pre-transition` conforming on each child, each run by that child before its own terminal move.

## Open questions

### OQ-01: Should this Set have been one plan rather than three?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: THREE, and the split is by KIND OF CHANGE rather than by file, which is what makes each independently reviewable. Order 01 is a WIDE MECHANICAL change across four modules whose central claim is that it changes NOTHING observable, checkable by diff plus byte-equality. Order 02 is a NARROW BEHAVIORAL change at two dispatch sites that defines a machine contract and amends a contract document, checkable by driving the CLI and parsing. Order 03 contains the Set's ONE deliberate human-output regression-shaped change, which a maintainer may want to object to in isolation. Folded into one plan, a failing byte-equality test could be caused by any of the three and a reviewer could not attribute it; and the human-output change would be buried inside a 500-line diff where it is exactly the thing most likely to draw an objection. The cost of the split is real and is accepted: Order 02 must leave two assertions LOOSE until Order 03 tightens them, which is why Order 02's V-06(b) forces the executor to state which option they took rather than leaving it implicit. ALTERNATIVE REJECTED: split by FILE (one plan per backend module), which would have put the same mechanical change in three plans and the contract decision in none of them, and would have made the `all`-aggregation question (which spans every type at once) unassignable.

### OQ-02: Should the Set also fix `aw index` and `aw archive`, so the whole defect class closes at once?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: NO, and the two have DIFFERENT reasons, which is why neither is carried. `aw index` genuinely has the same missing-payload defect (measured), and is now carried by open backlog `4izduy` (release-gated `next`); item `4uw9gy` (now `done`) also warns that `--limit` on `index` means a hot-window size that IS honoured in the human path and that a fixer must not unify it with the other verbs; adding `index` here would collide with that item's territory and risk breaking a working feature to fix an unrelated one. `aw archive` is not a contract violation at all: its `command_surface` declaration lists neither `--json` nor `--agent` in `legacy_flags`, so no promise is being broken, and it dispatches through `_run_archive` rather than `_run_noun_verb`, so it would not even benefit from Order 02's emit site. Giving it the flags is a feature a maintainer should choose. The honest consequence, stated so this Set's `- Blocks-Release:` gate is not read as a wider claim than it is: after this Set, the missing-payload defect class is closed on `rename`, `group` and the two research spellings, and remains open on `index` and `archive`. REVERSIBLE: yes; either could be added by a later plan without undoing anything here.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: (a) PASTE the path showing `x7unul` is in `.aw/records/plans/executed/` and QUOTE its `- Status: executed` line. (b) CONFIRM ITS CENTRAL NEGATIVE CLAIM HELD by quoting its V-02(d) / V-03(d) / V-04(c) byte-equality evidence, not merely its `Result: pass` marks: this Order's whole purpose is that it moved no output, and a reviewer of the Set needs to see the equality rather than a checkmark asserting it. (c) CONFIRM NO EXIT CODE CHANGED, by quoting its V-04(b) evidence that the research path still exits 0 with its frontmatter diagnostics present, which is the one place that Order could have silently changed a verdict.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) PASTE the path showing `vfqjc0` is in `.aw/records/plans/executed/` and QUOTE its `- Status: executed` line. (b) PASTE A LIVE RE-DERIVATION, not a quotation of the child's own evidence: run `aw rename specs --apply --json` and `aw group specs --rename --apply --json` in a throwaway repo and show `json.loads(stdout)` succeeding, since `specs` is a type with no nested index line and is therefore strictly parseable at this point in the Set. (c) CONFIRM THE `all` AGGREGATION by running `aw rename all <id6> --json` and COUNTING the records: exactly one. (d) CONFIRM THE DOC AMENDMENT LANDED AS SCOPED by quoting the changed line and confirming Section 11.3's rule text is untouched. (e) CONFIRM EXIT PARITY on a refusal: the process exit code equals the record's `exit` field.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) PASTE the path showing `gzb2rq` is in `.aw/records/plans/executed/` and QUOTE its `- Status: executed` line. (b) PASTE THE SET'S HEADLINE PROOF, re-derived live rather than quoted: `aw rename plans --apply --json` and `aw group plans --apply --json` in a throwaway repo with `json.loads(stdout)` SUCCEEDING. These are the two exact commands backlog item `eeiytw` names and this is the single piece of evidence a reader should be able to find fastest. (c) CONFIRM THE DELIBERATE HUMAN CHANGE IS EXACTLY ONE LINE'S WORTH: paste no-flag stdout before the Set and after it for `rename plans --apply`, and confirm the ONLY difference is the removed manifest line. (d) CONFIRM THE TWO INDEX VERBS ARE UNAFFECTED by running `aw index plans` and `aw research index` directly and showing their own outcome lines still print. (e) CONFIRM THE COMMIT PATH-SET carries no manifest path, by running `aw rename plans --apply --commit` and pasting the commit's file list. (f) CONFIRM THE LOOSE ASSERTION IS GONE, not merely superseded: state that Order 02's payload-recoverability assertion for `plans` and `research` was REPLACED by the strict form rather than left in place beside it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Explicit human approval is required before execution, on each child. This plan carries no `- Approval:` field and no `- Readiness:` field: both are attestations of acts (a human sign-off, a `/plan-review`) that have not happened, and writing either here would forge the evidence a gate reads.

THIS PLAN IS AN ORCHESTRATOR AND PERFORMS NO WORK. Its three items confirm child transitions and nothing else. An agent told to "execute eeiytw" should execute the children IN ORDER (01, then 02, then 03, which is both the Order sequence and the declared `- Item-Dependencies:` chain), then confirm this plan's items from the children's own recorded evidence plus the live re-derivations V-02(b) and V-03(b) demand. Do NOT add a work item here: the runner retires an orchestrator once every child is `executed` and skips the pre-transition checkpoint, so anything parked here would be marked complete having never been performed. If work is missing, ADD A CHILD and a row to the child table.

THE DEPENDENCY CHAIN IS REAL AND DECLARED, not advisory. Order 02 declares `- Item-Dependencies: executed:x7unul` and Order 03 declares `executed:vfqjc0`. Order 02 without Order 01 has no facts to map and would drive an executor to re-derive them inside `cli.py`, which is exactly the coupling the split exists to prevent. Order 03's E-01 and E-02 are one keyword each and WOULD work standalone, which makes early landing tempting; it must not happen, because it would silently falsify the byte-equality evidence Orders 01 and 02 both record.

ONE SEQUENCING CONSEQUENCE A REVIEWER SHOULD CHECK RATHER THAN ASSUME: between Order 02 and Order 03, the `plans` and `research` types have a CORRECT payload on stdout preceded by a nested manifest line, so strict `json.loads(stdout)` fails there for a reason Order 02 does not own. Order 02's V-06(b) requires the executor to state which of two honest options they took (declare a dependency on Order 03 and run it first, or assert payload recoverability and let Order 03 tighten it). The intended reading is the second, which keeps each Order independently landable.

BEFORE COMMITTING ANY CHILD, verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged <path>`: this is a shared checkout. (Plan `87m438`, which also declared `agent_workflows/plans_refs.py`, is already `executed`, so its change is part of the base.)

Scope fence: each plan's `- Scope-Paths:` is a DECLARATION for reconciliation, not a stop directive; an out-of-scope edit is made and then justified at finalize with `--scope-reason`.

All open questions are resolved and none is blocking.

Before this orchestrator retires, every child must be in `.aw/records/plans/executed/` with every `V-*` item carrying concrete pasted evidence, and the completion criteria above must hold. V-03(b) is the one that makes the Set meaningful: it is the backlog item's own two commands, parsing. Each child's terminal transition runs through `aw ipd finalize` (or the runner, in a managed lane); never `git mv` a plan into `executed/` by hand and never hand-edit `- Status: executed`.
