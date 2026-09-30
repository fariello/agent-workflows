# IPD: Record a satisfying close-evidence citation durably on the backlog item so the gate predicate can reconstruct a SATISFIED close at rest

- Date: 2026-09-30
- Kind: child
- Concern: THE `SATISFIED` ARM OF THE SHARED CLOSE PREDICATE IS UNRECONSTRUCTABLE AFTER THE FACT, AND CHILD 02 CANNOT SHIP WITHOUT IT. `check_engine.evaluate_blocking_close` accepts three legitimacy routes for a release-gated `done` close. Two of them (`HANDOFF`, `DE-GATED`) are decidable from PERSISTED state: the carrier artifact is a file on disk, and a cleared gate is the ABSENCE of a `- Blocks-Release:` bullet. The third, `SATISFIED`, is decidable ONLY from the transient `--evidence` argv string, which nothing durably records. `hooks/backlog_blocking_close_gate` already states this defect in its own module docstring ("A transient `--evidence` CLI arg is NOT visible to the hook, so the SATISFIED path is only honored here if child 02 durably records the evidence citation into the item (it does not today; that is out of the hook's reach by design)"). MEASURED at HEAD `7028ab5e`, driven end to end in a scratch repo: `aw backlog set aaaaaa --status done --evidence <an existing executed IPD path>` exited 0 and closed the item, and the resulting item file carries NO trace of the citation; re-asking the same predicate about that written item with no `evidence=` argument returns `legitimate=False, severity='error'`, reason "backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate". So a LEGITIMATE evidence-satisfied close is INDISTINGUISHABLE at rest from an illegitimate hand close, and any at-rest reader of the same predicate (the opt-in hook today, child 02's whole-tree arm next) must report it as a violation. Filing the citation is the prerequisite that makes the at-rest arm honest rather than a false-positive generator.
- Scope: IN: (1) a recognized, optional `- Close-Evidence:` metadata bullet on a backlog item, defined in the backlog record contract and validated for shape; (2) `backlog.run_set` writing that bullet when a `done` transition is legitimized by the predicate's `SATISFIED` route, so the citation that authorized the close is preserved beside the gate it satisfied; (3) `check_engine.evaluate_blocking_close` reading that bullet as an at-rest `SATISFIED` input when no `evidence=` argument is supplied, without changing the verdict for any caller that does supply one; (4) `runner_shared.close_backlog_item`'s existing citation reaching the same field through the setter it already calls (no new runner logic); (5) outcome tests; (6) a CHANGELOG line. OUT: the whole-tree scope change itself, which is child 02 and depends on this; any change to what counts as a resolvable citation (`check_engine.resolve_evidence_artifact` is untouched); the `HANDOFF` any-carrier-versus-all-carrier disagreement (owned by pending plan `2o5wka`, backlog `lsbd32`); the positional-spelling bypass (owned by pending plan `47ttnv`, backlog `mawwlc`); and any retroactive backfill of a citation onto an already-closed item, which would assert a history that did not happen.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/check_engine.py, .aw/records/backlog/README.md, tests/test_backlog_handoff_close.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nyzuyx
- Set: gateatrest
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: f7igdu

## Workflow history

- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nyzuyx` as child 01 of two. `nyzuyx` asks one question ("should `check.blocking-item-closed-without-gate` widen past its git-staged scope?"), and answering it yes requires this prerequisite first: an at-rest reader of the shared predicate cannot see the `SATISFIED` route at all, because the citation that authorizes it lives only in argv. Measured at HEAD `7028ab5e`: an evidence-satisfied close leaves NO durable trace, and the same predicate re-asked about the written item returns `legitimate=False, severity='error'`. Authored as its own plan rather than folded into child 02 because it changes the RECORD CONTRACT (a new recognized bullet) rather than a check's scope, and because child 02's correctness claim depends on it.
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a release-gate `SATISFIED` close leave a durable, machine-readable trace on the backlog item, so the one shared close predicate returns the SAME verdict when asked at rest as it did at the moment of the close. Without this, child 02's whole-tree arm would report every legitimate evidence-satisfied close as an error, and the scope widening `nyzuyx` asks about would be unshippable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the field and its contract

- [ ] E-01 DEFINE THE FIELD IN THE RECORD CONTRACT, in `.aw/records/backlog/README.md`'s metadata block, as `- Close-Evidence: <in-tree artifact path>   # optional; written by the setter on an evidence-satisfied done close`. State three properties in the prose beneath it, because each one is a decision a later reader would otherwise re-litigate: it is WRITTEN BY THE TOOL and never by hand (it is an attestation that a specific citation was resolved and accepted, so a hand-written value forges the acceptance, the same rule `AGENTS.md` states for `- Readiness:`); it is RETAINED on the item forever, since the close it records is permanent; and it is NOT a gate field, so it is never cleared by a status transition. Name the field `Close-Evidence` rather than `Gate-Evidence`: `Gate-*` is the blocked-gate family (`Gate-Kind`, `Gate-Ref`, and the `Gate-Summary` `backlog._render_item` deliberately DROPS on a non-`blocked` item), and a name in that family would be a magnet for exactly that drop rule.
  - Depends on: none
  - Expected outcome: the backlog README documents one new optional bullet with its writer, its permanence, and the reason for its name.
  - Execution state: pending

- [ ] E-02 PARSE AND VALIDATE THE FIELD in `agent_workflows/backlog.py`: add `close_evidence` to `BacklogItem.__slots__` and its `__init__`, add the reading regex to the `parse_item` field table beside `release_exempt_kind`/`release_exempt_ref`, and add a `validate_item` rule `backlog.close-evidence-unsafe` for a value that fails `attention_contract.is_safe_descriptive` (the same judgement `Summary` already gets through `backlog.summary-unsafe`). DO NOT validate that the path RESOLVES here: a citation can legitimately point at an artifact that was later archived or renamed, and `validate_item` is a shape checker with no repo root. VERIFIED that the field survives a round trip TODAY, before any parser change, so this item is about making it TYPED rather than making it PERSIST: driven at authoring, an item carrying `- Close-Evidence: README.md` taken through `aw backlog set <id6> --status open` kept the bullet byte-identically (plan `2yqt0a`'s source-order-preserving `_render_item` is what preserves it, since the key is not in `_TEMPLATE_OWNED_KEYS`), and `validate_item` returned `[]` for it. That measurement is why this item is cheap AND why it is not a no-op: an UNTYPED bullet is preserved but unreadable by any consumer, and `validate_item` silently accepts a malformed one.
  - Depends on: E-01
  - Expected outcome: `backlog.parse_item` exposes `item.close_evidence`; `validate_item` reports `backlog.close-evidence-unsafe` on a control-character or over-long value and nothing on a well-formed path; the whole live tree still conforms.
  - Execution state: pending

### Task group 2: the writer

- [ ] E-03 WRITE THE CITATION AT THE ONE SITE THAT ALREADY OWNS THE DECISION. In `backlog.run_set`, the close-legitimacy call is already made and its verdict already inspected (`verdict = _ce.evaluate_blocking_close(gate_root, src, new_status, evidence=getattr(args, "evidence", None), item_text=rendered, prior_priority=...)`, followed by the `not verdict.legitimate and verdict.severity == "error"` refusal). Add: when the verdict is legitimate AND `verdict.path == "SATISFIED"`, set the `- Close-Evidence:` line on `rendered` to the citation that was accepted, via a new `releases.set_close_evidence_line`-shaped helper following the exact idempotent replace-or-insert-after-`- Status:` pattern `backlog.set_release_exempt_kind_line` already uses. KEY ON `verdict.path`, NOT ON THE ARGUMENT BEING PRESENT: the predicate returns `SATISFIED` only when the citation actually resolved, and it returns `HANDOFF` first when a carrier exists, so keying on `args.evidence` would record a citation the predicate never consulted and would stamp an attestation on a close that was authorized by something else. Write NOTHING on any other path, so `HANDOFF` and `DE-GATED` closes are byte-identical to today.
  - Depends on: E-02
  - Expected outcome: `aw backlog set <item> --status done --evidence <resolvable path>` on a gated item writes `- Close-Evidence: <path>` into the closed item; the same command on an item that ALSO has an executed same-gate carrier writes nothing (the verdict is `HANDOFF`); a `--blocks-release -` close writes nothing.
  - Execution state: pending

- [ ] E-04 READ THE FIELD AS AN AT-REST INPUT in `check_engine.evaluate_blocking_close`'s `done` branch. Today the `SATISFIED` arm is `if evidence and resolve_evidence_artifact(repo_root, evidence)`. Change the citation it considers to `evidence` when the caller passed one, ELSE the item's own `- Close-Evidence:` value parsed from the same `text` the function already holds. Preserve two properties exactly: an explicitly-passed `evidence` argument WINS (so the setter's own in-flight call is unchanged, and a caller can still test a citation the item does not carry), and the citation must still RESOLVE through the unmodified `resolve_evidence_artifact`, so a stale or forged path is refused rather than trusted. ORDER IS UNCHANGED: `DE-GATED`, then `HANDOFF`, then `SATISFIED`, then the two refusals. Do not reorder to try the cheap field first; `HANDOFF` winning over `SATISFIED` is what E-03's `verdict.path` key depends on.
  - Depends on: E-03
  - Expected outcome: the predicate asked about a written, evidence-satisfied `done` item with NO `evidence=` argument returns `legitimate=True, path='SATISFIED'`; asked about the same item with its citation deleted it returns `legitimate=False, severity='error'`; asked about a citation that does not resolve it refuses.
  - Execution state: pending

### Task group 3: proof and record

- [ ] E-05 EXTEND `tests/test_backlog_handoff_close.py` WITH THE AT-REST CASES, in the behavioral style that file already uses (drive the CLI or the predicate against a fixture repo; assert outcomes, never source text). Four cases, each of which fails before E-03/E-04 and passes after: (a) the REGRESSION THAT MOTIVATES THE SET, written FIRST and demonstrated FAILING: close a gated item through `aw backlog set --status done --evidence <resolvable path>`, then ask `evaluate_blocking_close` about the WRITTEN item with no `evidence=` argument and assert `legitimate=True, path='SATISFIED'`; (b) the same item with its `- Close-Evidence:` bullet removed is refused, proving the pass in (a) comes from the field and not from some unrelated leniency; (c) an item carrying a `- Close-Evidence:` path that does NOT exist in the tree is refused, proving the resolver still gates; (d) a `HANDOFF` close and a `DE-GATED` close each leave NO `- Close-Evidence:` bullet, proving E-03 records an attestation rather than echoing argv. Case (a) is a MUTATION-SENSITIVE test by construction: reverting E-04 alone turns it red.
  - Depends on: E-04
  - Expected outcome: four new passing cases in the existing file, with (a) shown failing at HEAD before the fix and passing after.
  - Execution state: pending

- [ ] E-06 RECORD THE CHANGE for a reader who did not follow the Set: one `CHANGELOG.md` line under the pending 2.0.0 entry saying a backlog item closed on cited evidence now records that citation, so the release-gate check can tell a legitimate evidence-satisfied close from a hand close. No em or en dashes (user-facing prose).
  - Depends on: E-05
  - Expected outcome: one CHANGELOG line; `aw sanitize --agent` clean on the changed files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PREDICATE IS SINGLE-SOURCED AND MUST NOT BE COPIED. `check_engine.evaluate_blocking_close` backs four surfaces: the setter (`backlog.run_set`), `set_records.close_on_answer`, the `aw check` rule `check.blocking-item-closed-without-gate` (through `check_engine.check_release_gate_consistency`), and the opt-in `hooks.backlog_blocking_close_gate` (which calls that rule). `AGENTS.md` states this is why "they cannot diverge". E-04 therefore edits ONE function and every surface inherits it; adding a second reader of `- Close-Evidence:` anywhere else would be the defect this convention exists to prevent.
- AN ATTESTATION FIELD IS WRITTEN BY THE ROLE THAT PERFORMS THE STEP, NEVER BY HAND. `AGENTS.md` states the rule for `- Readiness:` and generalizes it ("never hand-write an `- Approval:` attestation, a `V-*` `Observed evidence` block you did not observe"). `- Close-Evidence:` is the same shape: it asserts that a specific citation was resolved and accepted by the predicate. E-01 writes that down in the README; E-03 makes the tool the only writer.
- THE METADATA SETTER PATTERN IS ESTABLISHED, so E-03 copies it rather than inventing one. `backlog.set_release_exempt_kind_line` and its `_ref` twin each strip any existing line, return early on `None`/`-`, and insert after `- Status:` with a fallback to after `- Id:`. `releases.set_blocks_release_line` is the same shape for the gate field.
- A NON-TEMPLATE-OWNED BULLET ALREADY SURVIVES A RE-RENDER, measured rather than assumed. `backlog._TEMPLATE_OWNED_KEYS` is `Id, Status, Set, Priority, Work-Kind, Kind, Summary, Gate-Kind, Gate-Ref`; anything else is emitted verbatim in source order by the `source_text` walk plan `2yqt0a` added. So this field needs no preservation work, only typing.
- `Gate-Summary` IS THE CAUTIONARY PRECEDENT FOR THE NAME. `backlog._render_item`'s rule (2) DROPS `- Gate-Summary:` on any item that is not `blocked`, matched via `attention_contract.GATE_SUMMARY_RE`. A citation named into the `Gate-*` family would be one refactor away from being dropped on exactly the `done` items that need it.
- TESTS ASSERT OUTCOMES, NEVER SOURCE STRUCTURE (`AGENTS.md`; GUIDING_PRINCIPLES P16). `tests/test_backlog_handoff_close.py` already follows this: its ten existing cases build a fixture repo and drive the real close.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | AN EVIDENCE-SATISFIED CLOSE IS INDISTINGUISHABLE AT REST FROM AN ILLEGITIMATE ONE. Driven at HEAD `7028ab5e` in a scratch repo: `aw backlog set aaaaaa --status done --evidence .aw/records/plans/executed/<an executed IPD>` exited 0 and moved the item to `done/`; the written file carries `- Blocks-Release: next` and no citation. Re-asking `evaluate_blocking_close(repo, <written item>, "done")` with no `evidence=` returns `legitimate=False, severity='error'`. | The written item's bullets, and the verdict tuple, both pasted at authoring. |
| F-02 | INFO | THE DEFECT IS ALREADY DOCUMENTED IN-TREE, so this is a known gap being closed rather than a discovery. `hooks/backlog_blocking_close_gate`'s module docstring: "A transient `--evidence` CLI arg is NOT visible to the hook, so the SATISFIED path is only honored here if child 02 durably records the evidence citation into the item (it does not today; that is out of the hook's reach by design)." | That docstring, quoted verbatim. |
| F-03 | MEDIUM | THE CORPUS CONTAINS ZERO `SATISFIED` CLOSES TODAY, which bounds the benefit honestly and is the reason this plan is `low` priority and `chore`. Measured over all 224 gated `done` items: the verdict path distribution is `HANDOFF` 175, illegitimate 49, `SATISFIED` ZERO. So no existing record gains a citation from this change; the value is entirely FORWARD, and specifically it is what lets child 02's at-rest arm be correct rather than a false-positive generator. | The per-item verdict-path census, pasted in V-01. |
| F-04 | MEDIUM | THE RUNNER ALREADY CITES EVIDENCE ON EVERY CLOSE IT MAKES, so the forward population is not hypothetical. `runner_shared.close_backlog_item` calls the gated `--status done` spelling WITH `--evidence <carrier path>`, and its history message is `closed by aw oc run: IPD <id6> executed (<reason>); evidence <path>`. Measured: 146 of the 224 gated `done` items carry that runner-authored line. Those closes resolve as `HANDOFF` (the carrier is executed, and `HANDOFF` is tried first), which is exactly why the `SATISFIED` count is zero; but a runner close of a NON-plan-carrier item would take the `SATISFIED` route and would, after this plan, record its citation with no runner change at all. | The history-line census and `close_backlog_item`'s argv construction. |
| F-05 | LOW | A NON-TEMPLATE BULLET ALREADY ROUND-TRIPS, so no preservation work is needed. Driven at authoring: an item carrying `- Close-Evidence: README.md` taken through `aw backlog set <id6> --status open` retained the bullet in place, and `validate_item` returned `[]`. The second half of that measurement is the finding: an untyped bullet is accepted WITHOUT validation, so a malformed value would pass silently. E-02 is what closes that half. | The round-tripped item file and the empty drift list. |

## Proposed changes (ordered, validatable)

1. `.aw/records/backlog/README.md`: document `- Close-Evidence:` with its writer, its permanence, and the reason it is not named `Gate-Evidence` (E-01).
2. `agent_workflows/backlog.py`: parse the field onto `BacklogItem`, validate its shape as `backlog.close-evidence-unsafe`, and add the idempotent line setter (E-02).
3. `agent_workflows/backlog.py`: in `run_set`, write the citation when and only when the shared verdict's `path` is `SATISFIED` (E-03).
4. `agent_workflows/check_engine.py`: in `evaluate_blocking_close`, fall back to the item's own citation when no `evidence=` argument is supplied, keeping the explicit argument's precedence and the resolver's gate (E-04).
5. `tests/test_backlog_handoff_close.py`: four behavioral cases, the first written failing (E-05).
6. `CHANGELOG.md`: one line (E-06).

## Deferred / out of scope (with reason)

- THE WHOLE-TREE SCOPE CHANGE ITSELF. That is child 02 (`b24o3q`) and is the question `nyzuyx` actually asks. It is deferred out of THIS plan because it is a policy change with a corpus-wide blast radius, while this one is a record-contract addition with none; keeping them separate lets a reviewer approve the prerequisite without approving the policy.
  - Carrier: b24o3q
- RETROACTIVE BACKFILL of a citation onto an already-closed item. `AGENTS.md` states the release-gate rule governs LIVE items only and that writing a gate onto a closed item "would assert a history that did not happen"; writing an ACCEPTANCE ATTESTATION onto a historical close is the same forgery in the other direction. The 49 illegitimate historical closes are child 02's grandfathering problem, not this plan's.
  - Carrier-Declined: Nothing is owed, because the backfill is FORBIDDEN rather than unfinished. `AGENTS.md` rules that writing a gate onto an already-closed item asserts a history that did not happen, and an acceptance attestation is the same forgery; filing a carrier would assert pending work for something we have decided must never be done. The 49 historical items are separately owned as an AUDIT (backlog `mbjuv5`), which reports rather than rewrites.
- WIDENING WHAT COUNTS AS A RESOLVABLE CITATION. `check_engine.resolve_evidence_artifact` is deliberately untouched, so this plan cannot make a previously-refused citation acceptable.
  - Carrier-Declined: There is no defect to carry. The resolver's current strictness is a deliberate shipped choice with its own recorded rationale (it is intentionally more permissive than the specs-side twin and no more), and this plan's value depends on NOT changing it, so a carrier would misrepresent a settled contract as outstanding work.
- THE `HANDOFF` ANY-CARRIER VERSUS ALL-CARRIER DISAGREEMENT. Owned by pending plan `2o5wka` (backlog `lsbd32`). Measured here for the record, because child 02 must not be surprised by it: 4 of the 175 `HANDOFF`-legitimate historical closes have at least one UNEXECUTED same-gate carrier and would become findings if that plan lands. Noted, not acted on.
  - Carrier: lsbd32
- THE POSITIONAL-SPELLING BYPASS. `aw backlog set done <id6>` routes through `status_set.apply_status_change`, which never consults the predicate. Owned by pending plan `47ttnv` (backlog `mawwlc`). This plan's writer therefore covers the `--status` spelling only, which is the only spelling that reaches a verdict to key on.
  - Carrier: mawwlc
- A `validate_item` RULE THAT THE CITATION RESOLVES. `validate_item(path, text)` has no repo root and a citation may legitimately point at an artifact archived after the close. The resolution check stays where it belongs, in the predicate.
  - Carrier-Declined: No obligation exists to carry. This is a placement decision, not a missing check: the resolution IS performed, by `evaluate_blocking_close` through `resolve_evidence_artifact`, which is the only caller that holds a repo root. Filing a carrier would assert that a check is absent when it is present one layer up.

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item: `backlog.py` by E-02/E-03, `check_engine.py` by E-04, the backlog README by E-01, `tests/test_backlog_handoff_close.py` by E-05, `CHANGELOG.md` by E-06.
- Under-scope: checked rather than assumed. A grep for the three `evidence` seams found `backlog.run_set` (the setter's predicate call), `check_engine.evaluate_blocking_close` (the `SATISFIED` arm), `check_engine.resolve_evidence_artifact` (the resolver, deliberately untouched), `specs._evidence_resolvable` (the specs-side stricter twin, out of scope: specs record their evidence in their own history), and `runner_shared.close_backlog_item` (which passes `--evidence` through the setter and so needs NO change, per F-04). `agent_workflows/set_records.py`'s `close_on_answer` calls the predicate but accepts no citation at all, so it cannot produce a `SATISFIED` verdict and needs no write site.

## Required tests / validation

`python3 -m pytest` bare (the repository contract: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`), plus `python3 -m pytest tests/test_backlog_handoff_close.py tests/test_backlog.py -o addopts=""` for the per-test counts of the two files this plan touches. Plus `aw check backlog --agent` and `aw check release-gates --agent` on the live tree, which must both still conform with the same finding counts as the pre-change baseline (this plan adds a field nothing in the live tree carries, so a nonzero delta is a defect in the change, not a discovery). Plus `aw ipd lint --phase pre-transition` on this plan before any terminal move.

## Spec / documentation sync

- `.aw/records/backlog/README.md` is edited by E-01 and is declared in `- Scope-Paths:`. It is the record-contract home for the backlog bullet grammar, so a new recognized bullet MUST appear there or the contract and the parser diverge.
- NO `.spec.md` IS AMENDED, and this is a deliberate judgement rather than an omission. The invariant-catalog spec `pqsx96` row I-07 names the predicate and its rules but describes the THREE ROUTES generically ("a resolvable evidence path"); adding a durable home for that path does not change the invariant's statement. `pqsx96` is additionally `- Status: draft` and being actively authored, so amending it here would collide with its author. Child 02, which DOES change what the rule examines, carries the spec question instead.
- `AGENTS.md`'s "Release gates" section states the three fixes including "(2) SATISFIED, a resolvable in-tree artifact citation `aw backlog set done <item> --evidence <path>`". That sentence remains true after this plan (the argument still works and still wins), so no edit is required. Deliberately NOT edited, to keep this plan's diff off a file three other pending plans also touch.

## Open questions

### OQ-01: Should `- Close-Evidence:` be multi-valued?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, single-valued, resolved from the shape of the thing being recorded rather than from preference. The predicate's `SATISFIED` arm accepts ONE citation (`evidence: Optional[str]`) and returns as soon as it resolves, so there is never more than one accepted citation to record; a multi-valued field would be able to express a state the predicate cannot produce. `- Graduated-To:` is multi-valued for the opposite reason (one source legitimately fans out to several Sets). If a future change makes the predicate accept several citations, widening a single-valued field is a smaller step than narrowing a multi-valued one.

### OQ-02: Should the setter also record the `HANDOFF` carrier path in a field?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and deliberately so: it would be redundant state that can go stale. A `HANDOFF` is already fully reconstructable at rest, because the carrier is a file on disk carrying `- From-Backlog: <item>` and the same `- Blocks-Release:`, which is exactly what `_from_backlog_carrier_index` reads. Recording the path as well would create a second copy that a later `aw rename`/`aw archive` could falsify while the reconstructable answer stayed correct. The `SATISFIED` route is different precisely because its input is NOT reconstructable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the added README block verbatim, showing the bullet, the "written by the tool, never by hand" property, the retention property, and the naming rationale. Paste the `git diff` for the README proving no other line changed. ALSO paste the re-measured verdict-path census that F-03 reports (`HANDOFF` / `SATISFIED` / illegitimate counts over every gated `done` item at execution HEAD), because those numbers WILL have moved and the README's claim that the field is forward-looking depends on the `SATISFIED` count still being zero at execution time; if it is NOT zero, say so and report which items already carry a citation. Confirm no em or en dashes were introduced (this is user-facing prose).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a driven demonstration, not a source excerpt: for a fixture item carrying `- Close-Evidence: README.md`, paste `backlog.parse_item(text).close_evidence`; for a fixture carrying a control-character or over-length value, paste the `validate_item` drift list showing exactly one `backlog.close-evidence-unsafe`; for the well-formed one, paste the EMPTY drift list. Then paste `aw check backlog --agent` on the LIVE tree showing the same outcome and finding count as the pre-change baseline (paste both), proving a new validation rule did not light up existing records.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste three driven closes and the resulting item bullets for each. (a) gated item, no carrier, `--evidence <resolvable path>`: exit 0 and the item carries `- Close-Evidence: <that path>`. (b) gated item WITH an executed same-gate carrier, same `--evidence` argument: exit 0 and the item carries NO `- Close-Evidence:` bullet, because the verdict path was `HANDOFF`; this is the case that proves the write keys on `verdict.path` and not on argv. (c) `--blocks-release -` close: exit 0 and no bullet. For each, paste the exact command and its output, and state which verdict path the predicate returned.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the predicate's verdict tuple (legitimate, severity, path, and the reason string) for four at-rest asks with NO `evidence=` argument: the written item from V-03(a) returning `path='SATISFIED'`; the same item with the bullet deleted returning `legitimate=False, severity='error'`; the same item whose citation points at a path that does not exist returning `legitimate=False`; and one ask WITH an explicit `evidence=` argument naming a DIFFERENT resolvable path, proving the argument still wins (state which citation the reason names). ALSO paste the unchanged `HANDOFF`-first ordering demonstration: an item that satisfies BOTH routes returns `HANDOFF`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the FAILING run of case (a) at HEAD before E-03/E-04 are applied, including the assertion error, then the passing run after. Paste `python3 -m pytest tests/test_backlog_handoff_close.py tests/test_backlog.py -o addopts=""` output with its per-test counts, and the bare `python3 -m pytest` summary line (the `N passed` line, which the configured `-q` already produces; do not add flags). A pasted pass without the pre-fix failure for case (a) FAILS this item, because a test written only after the fix cannot distinguish "the field is read" from "the fixture happened to pass".
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the added CHANGELOG line and confirm by inspection that it contains no em or en dash. Paste `aw sanitize --agent` output over the changed paths (exit 0, no findings). Paste `git diff --cached --name-only` for the commit, which must list exactly the five declared scope paths or a subset, and nothing else.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One new optional backlog bullet, written only by the tool, plus a fallback read in the one shared close predicate. The behavior change is narrow and one-directional: a `done` close that was ALREADY legitimate at the moment it happened stays legitimate when the same predicate is asked again later. Nothing that is refused today becomes accepted: the citation must still resolve through the unmodified resolver, an explicitly-passed argument still wins, and the `HANDOFF`-first ordering is untouched. No existing record is rewritten, and no historical close is backfilled.

WHY IT IS FILED AS `chore` AND `low`. Measured: the corpus contains ZERO `SATISFIED` closes, so nothing in the tree is currently misjudged by the gap. It is not user-perceptible today, which is the test `AGENTS.md` sets for `bug`. Its value is that it is the PREREQUISITE for child 02: without it, a whole-tree arm would report every future evidence-satisfied close as an error.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Paste actual runner output for every test claim. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence. On completion, move the plan to `.aw/records/plans/executed/` through the lifecycle tooling, not by hand.
