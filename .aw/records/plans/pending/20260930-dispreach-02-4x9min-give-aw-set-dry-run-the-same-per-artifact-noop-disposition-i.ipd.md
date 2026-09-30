# IPD: Give aw set dry-run the same per-artifact noop disposition its apply path already reports

- Date: 2026-09-30
- Kind: child
- Concern: `aw set`'s machine DRY-RUN branch reports every matched artifact as an `update` even when the transition is a NO-OP, so a preview claims work the apply path then declines to do. MEASURED in this lane at HEAD `522598b6` on one artifact already at the target status, same repository, same selector, only the flag differing: dry-run emits `summary: "would update status on 1 artifact(s)"` with `changes: [{kind: "update", detail: "status: reviewed -> reviewed"}]`, while apply emits `summary: "updated status on 0 artifact(s)"` with `changes: [{kind: "noop", detail: "status: reviewed (unchanged)"}]`. The `noop` kind and the `(unchanged)` detail therefore ALREADY EXIST and the dry-run branch simply does not use them. The HUMAN surface is correct on both paths (both print `unchanged`), so a machine consumer is told something a human reading the same command is not. On a real mixed selection the count is wrong rather than merely mislabelled: `aw ipd set reviewed awrenamesel --dry-run --json` over a Set whose five plans include three already `reviewed` reports `would update status on 5 artifact(s)` with five `update` entries, where the human path prints `unchanged` for three of them and only two would in fact change.
- Scope: Make the machine dry-run branch of `status_set.run_set_command` report each matched artifact's real disposition, reusing the `noop` kind, the `(unchanged)` detail wording, and the changed/unchanged predicate the APPLY path in the same function already uses. IN: the `if is_dry_run:` machine branch's `Change` construction and its `summary` count; the same branch's `data["items"]` rows if they carry the same claim. OUT: the human dry-run line, which is already correct; the apply path, which is already correct; WHICH artifacts a selector matches; the zero-match and ambiguity refusals; `aw runs` (Order 01 of this Set); and `aw find` (owned by pending plan `zyj8io`).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: om3rzi
- Set: dispreach
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: 4x9min

## Workflow history

- 2026-09-30 to-review (opencode): Authored from backlog item `om3rzi`, whose deferred row 4 on orchestrator `7ewc74` is the carrier statement. Every claim below was MEASURED in this lane at HEAD `522598b6`, not read off the item, and the measurement CHANGED WHAT THE WORK IS. The item asks to extend matched-vs-acted disposition reporting to `aw ipd set` on the premise that it lacks such reporting. It does not lack it: measured, `aw ipd set reviewed <setid> --dry-run` prints one line per matched artifact reading either `unchanged` or `to-review -> reviewed`, so the HUMAN surface already reports exactly the matched-versus-acted distinction the item asks for, and `_format_status_transition_line` already takes a `changed` parameter for the purpose. The REAL defect is narrower, sharper and provable in one diff: the MACHINE dry-run branch ignores that distinction and calls every match an `update`, while the APPLY branch of the same function gets it right using a `noop` kind that already exists. So this plan fixes an internal DISAGREEMENT between two branches of one function rather than adding a new reporting surface, which is a smaller change with a much stronger correctness argument: there is a right answer already in the file. THE DEFECT SPANS EVERY ARTIFACT TYPE because `run_set_command` is the one shared implementation: measured, `aw backlog set open <id6> --json --dry-run` on an already-`open` item reports `update` / `status: open -> open` while its apply path reports `noop` / `status: open (unchanged)`, and the untyped `aw set` spelling reproduces it identically.
  DELIBERATE NON-EXTENSION, recorded so an executor does not widen this. Order 01 of this Set consumes `run_selection_policy.render_item_disposition` because `aw runs` has no per-artifact line at all. This plan does NOT import that renderer: `aw set` already has its own per-artifact line (`_format_status_transition_line`) whose shape is pinned by shipped tests, and replacing it would be a gratuitous output change to a correct surface. The shared vocabulary this plan reuses is the one already inside `status_set`: the `noop` kind, the `(unchanged)` wording, and the `changed` predicate.

## Goal

Make `aw set --dry-run` preview what `aw set` would actually do. A preview whose count and per-artifact kind disagree with the apply path for the same input is worse than no preview, because it is trusted: a script that runs the dry-run to decide whether to proceed reads `would update status on 5 artifact(s)` and acts on a number the apply path will contradict. The right answer is already in the same function; this plan makes one branch use it.

THREE FACTS ESTABLISHED AT AUTHORING so the executor does not re-derive them and does not inherit the item's falsified premise.

1. THE TWO BRANCHES OF ONE FUNCTION DISAGREE ON IDENTICAL INPUT. Measured at HEAD `522598b6`, same fixture repo, same selector, one artifact already at the target status:

   ```text
   $ aw ipd set reviewed aaa111 --json --dry-run
     summary: would update status on 1 artifact(s)
     changes: [{kind: "update", applied: false, detail: "status: reviewed -> reviewed"}]

   $ aw ipd set reviewed aaa111 --json --yes
     summary: updated status on 0 artifact(s)
     changes: [{kind: "noop", applied: false, detail: "status: reviewed (unchanged)"}]
   ```

   Only the flag differs. `noop` and `(unchanged)` are the apply path's own vocabulary, already shipped.

2. THE HUMAN SURFACE IS ALREADY RIGHT ON BOTH PATHS, which is what makes this a machine-only fix and bounds the change:

   ```text
   $ aw ipd set reviewed aaa111 --dry-run   -> "-    plan  ...aaa111  unchanged  (dry-run)"
   $ aw ipd set reviewed aaa111 --yes       -> "-    plan  ...aaa111  unchanged"
   ```

3. THE COUNT IS WRONG ON A REAL MIXED SELECTION, not merely a label. Over Set `awrenamesel`, whose five pending plans are three `reviewed` and two `to-review`:

   ```text
   $ aw ipd set reviewed awrenamesel --dry-run --json
     summary: would update status on 5 artifact(s)
     details: reviewed -> reviewed (x3), to-review -> reviewed (x2)   [all five kind="update"]
   $ aw ipd set reviewed awrenamesel --dry-run          (human)
     3 lines "unchanged", 2 lines "to-review -> reviewed"
   ```

   So the human says two would change and the machine says five.

WHY THIS IS THE `om3rzi` OBLIGATION AND NOT A SUBSTITUTE FOR IT. The item asks for "matched-vs-acted disposition reporting" on this verb. The distinction it wants is exactly matched (5) versus would-be-acted-on (2); the human surface draws it and the machine surface collapses it. Fixing the machine branch is therefore the whole of the item's ask for this verb, and the executor should not read the item's phrasing as licence to add a second reporting block to a surface that already has one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the dry-run branch tell the truth

- [ ] E-01 COMPUTE THE CHANGED/UNCHANGED FACT IN THE MACHINE DRY-RUN BRANCH of `status_set.run_set_command` (the `if is_dry_run:` block guarded by `if ctx.is_agent or ctx.is_json:`) and emit `kind="noop"` with the `(unchanged)` detail wording for a no-op, exactly as the APPLY path does. REUSE THE PREDICATE THE HUMAN DRY-RUN PATH IN THE SAME FUNCTION ALREADY USES rather than writing a third one: that path computes `changed = curr != nstat.strip().lower()` from `normalize_target_status` and the record's current status, and passes it to `_format_status_transition_line(..., changed=changed)`. Prefer lifting that expression into ONE local helper consumed by BOTH dry-run branches over duplicating it, since three copies of one predicate in one function is the drift this plan exists to remove. DO NOT reuse the apply path's predicate verbatim: measured, it is `(old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, which requires the write to have HAPPENED and so is unavailable in a dry run; that asymmetry is the reason the defect exists and E-01 must not pretend otherwise. Also correct the branch's `summary` so its count is the number that WOULD change, matching the apply path's `len([r for r in results if r[3]])` shape rather than `len(matched_records)`.
  - Depends on: none
  - Expected outcome: for an artifact already at the target status, the machine dry-run emits `kind="noop"` and a detail matching the apply path's `(unchanged)` wording; for one that would change, it still emits `kind="update"` with the `old -> new` detail; the `summary` count equals the number that would change; every matched artifact still appears in `changes` exactly once, so the preview remains a complete list of what the selector matched.
  - Execution state: pending

- [ ] E-02 RECONCILE THE BRANCH'S `data["items"]` ROWS with the same fact, since they carry the same claim in a second place. Each row currently reports `old_status` and `new_status` with no indication that the two may be equal, so a consumer reading `items` rather than `changes` is misled even after E-01. Add the changed/unchanged fact to each row using the SAME helper E-01 lifted, and keep every existing key so no consumer breaks. If inspection shows `items` and `changes` would then carry one fact twice, say so in the evidence and state which is authoritative rather than silently leaving two sources of truth.
  - Depends on: E-01
  - Expected outcome: a consumer reading either `changes` or `data["items"]` gets the same answer about the same artifact; all existing keys remain present; the two structures cannot disagree because both derive from one helper.
  - Execution state: pending

### Task group 2: coverage

- [ ] E-03 ADD TESTS to `tests/test_status_set.py` driving the REAL CLI and asserting on the emitted machine payload: a no-op dry run emits `noop` and the `(unchanged)` detail; a real transition still emits `update`; a MIXED selection (the sharpest case, F-03) reports the correct changed count and the correct per-artifact kinds; and THE CROSS-PATH AGREEMENT PROPERTY, which is the assertion that actually pins this defect closed - for the same fixture and selector, the dry-run payload's per-artifact kinds and changed count MATCH what the apply path then emits. Cover at least TWO artifact types (a plan and a backlog item), because `run_set_command` is shared and the defect was measured on both, and cover the untyped `aw set` spelling alongside a typed one. Assert on payload fields and exit codes only; do NOT read production source text, count callers, or pin a docstring (GUIDING_PRINCIPLES P16).
  - Depends on: E-02
  - Expected outcome: the new tests FAIL on the pre-E-01 tree (the no-op case fails asserting `noop` where `update` is emitted, and the mixed case fails on the count) and pass after E-02; the cross-path agreement test would go red again if either branch's predicate drifted; the human dry-run line's existing shipped assertions still pass unmodified.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `status_set.run_set_command` is the ONE implementation behind every `set` spelling: the typed `aw ipd set`, the untyped `aw set`, and `aw backlog set` (via `work_cmd`) all reach it, which is why a fix here covers every artifact type and why a regression here would too.
- `status_set._format_status_transition_line` renders the HUMAN per-artifact line and already takes a `changed` parameter; its `unchanged` branch carries an in-code note that `unchanged` "IS NOT A LIFECYCLE STATUS AND MUST NOT BE ROUTED THROUGH THE RESOLVER" (plan `9zvl2w` E-02, spec `uonrjg` R10.3). An executor must not turn `unchanged` into a lifecycle status to make the machine branch symmetrical.
- The APPLY path in `run_set_command` builds its `Change` list with `kind="update" if changed else "noop"` and the detail `f"status: {norm_stat} (unchanged)"`, and counts with `len([r for r in results if r[3]])`. That is the shape E-01 makes the dry-run branch match.
- `result_types.Change` carries `path`, `kind`, `applied` and `detail`; the `noop` kind is already part of the shipped vocabulary, so this plan adds no new machine token.
- `aw.agent/v1` conformance: the `--agent` surface emits a schema-validated record, so any payload change must keep it valid; the repository validates with `agent_schema.assert_valid_agent_record`.
- ASSERT ON OBSERVABLE BEHAVIOR, never on code structure (`AGENTS.md`, GUIDING_PRINCIPLES P16).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT IS AN INTERNAL DISAGREEMENT BETWEEN TWO BRANCHES OF ONE FUNCTION, which is a stronger warrant than the backlog item's framing.** On identical input in one fixture repo, the machine dry-run emits `{kind: "update", detail: "status: reviewed -> reviewed"}` with `summary: "would update status on 1 artifact(s)"`, while the apply path emits `{kind: "noop", detail: "status: reviewed (unchanged)"}` with `summary: "updated status on 0 artifact(s)"`. There is no ambiguity about the correct answer, because one branch already gives it. | Fixture repo built in this lane with one plan at `- Status: reviewed`; both commands run with `--json`; both payloads captured in full. |
| F-02 | THE ITEM'S PREMISE FOR THIS VERB IS FALSIFIED, and this is the finding that reshaped the plan. `om3rzi` implies `aw ipd set` lacks matched-vs-acted reporting. Measured, its HUMAN surface has it: `aw ipd set reviewed awrenamesel --dry-run` prints five lines, three reading `unchanged` and two reading `to-review -> reviewed`, and `_format_status_transition_line` takes a `changed` parameter for exactly this purpose. So the work is to fix the MACHINE branch that ignores the distinction, not to add a reporting surface. | Command run against the tracked `awrenamesel` Set (five pending plans, statuses read individually); output counted (`3` unchanged, `2` transitions); `_format_status_transition_line`'s signature and its `changed`/`unchanged` branch read. |
| F-03 | THE COUNT IS WRONG, NOT MERELY THE LABEL, on a real mixed selection, which is the sharpest evidence and the case a test should pin. `aw ipd set reviewed awrenamesel --dry-run --json` reports `would update status on 5 artifact(s)` with all five entries `kind="update"`, where only TWO would change. A script reading that number to decide whether to proceed is misinformed by 150 percent. | The `--json` payload captured and its `changes` kinds counted (`Counter({'update': 5})`); the five plans' actual statuses read from their front matter; the human output counted for contrast. |
| F-04 | THE HUMAN SURFACE IS CORRECT ON BOTH PATHS, which bounds this plan to the machine branch and rules out an output change users would see. `aw ipd set reviewed aaa111 --dry-run` prints `unchanged  (dry-run)` and the apply path prints `unchanged`. | Both commands run in the fixture repo; both lines captured. |
| F-05 | THE DEFECT SPANS EVERY ARTIFACT TYPE AND EVERY `set` SPELLING, because `run_set_command` is the single shared implementation. `aw backlog set open bbb222 --json --dry-run` on an already-`open` item emits `update` / `status: open -> open` while its apply path emits `noop` / `status: open (unchanged)`; the untyped `aw set reviewed aaa111 --json --dry-run` reproduces the plan case identically. This is why E-03 requires two artifact types and both spellings. | A backlog item added to the fixture; four commands run (`backlog set` dry-run and apply, untyped `set` dry-run); every payload captured; `grep` for `run_set_command` across `agent_workflows/` showing `work_cmd` and `cli` as the callers. |
| F-06 | THE APPLY PATH'S PREDICATE IS STRUCTURALLY UNAVAILABLE IN A DRY RUN, which is the ROOT CAUSE and the trap E-01 must route around. It is `changed = (old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, computed AFTER `apply_status_change` has written the file, so it cannot be reused verbatim where nothing is written. The human dry-run path already solves this with a pre-write predicate, `changed = curr != nstat.strip().lower()`, in the same function. So the fix is to reuse the PRE-WRITE predicate, and E-01 says so explicitly. | Both predicates read in `run_set_command`; the write ordering read (the apply predicate follows the `apply_status_change` call and a `read_text` of the destination). |
| F-07 | THE `noop` KIND AND THE `(unchanged)` WORDING ALREADY SHIP, so this plan adds NO new machine vocabulary and no consumer sees an unfamiliar token. The apply path constructs `kind="update" if changed else "noop"`, and `result_types.Change` carries the `kind` field. | The apply path's `Change` construction read in full; `result_types.Change` read; the `noop` kind observed in a real apply-path payload (F-01). |
| F-08 | NO EXISTING TEST COVERS THE MACHINE DRY-RUN DISPOSITION, so E-03 is new coverage rather than a duplicate. `tests/test_status_set.py` contains `noop` only inside an unrelated fixture name (`gatenoop`) and one `rc_noop` local for a human-path no-op exit code; neither asserts on an emitted `kind`. No test asserts on a dry-run `changes[].kind` at all. | Searches over `tests/test_status_set.py` for `noop` (two hits, both classified by reading them) and for a dry-run payload-kind assertion (none). |
| F-09 | NO OTHER PENDING PLAN DECLARES THIS PLAN'S EXACT PAIR, but BOTH ITS FILES ARE CONTENDED and the executor must expect to re-read before editing. Measured by scanning every pending `- Scope-Paths:` and reading each plan's `- Id:`: `agent_workflows/status_set.py` is declared by TEN other plans (`0ykozn`, `5poaqh`, `ghna7l`, `4a8yws`, `47ttnv`, `xvon5j`, `nvsz19`, `x4vf9p`, `tr8ugt`, `jw6cm3`) and `tests/test_status_set.py` by FIVE (`5poaqh`, `4a8yws`, `nvsz19`, `tr8ugt`, `jw6cm3`). NONE targets the dry-run machine branch: their subjects are a `From-Spec` field, setter refusal hints, release-gate exemptions, the research vocabulary, the positional close gate, bounded identity reads, routing plan transitions through the lifecycle predicate, release sentinel succession, a bounded-section test conversion, and documenting the two `match_selector` narrowing sites. File overlap is not a runtime hazard under the runner (each item gets an isolated worktree and returns through the merge-and-revalidate gate), but it IS a reason to re-read the function before editing. | Scan of `- Scope-Paths:` across all pending plans with each plan's `- Id:` read directly (counts verified as 10 and 5, not eyeballed from filenames); each contending plan's scope line read to classify its subject. |
| F-10 | THE SUITE IS GREEN AT THIS LANE'S HEAD, giving the baseline validation compares against: `3246 passed, 2 skipped, 3 warnings in 144.70s` from a BARE `python3 -m pytest` at HEAD `522598b6`. | Bare `python3 -m pytest` run in this lane; summary line captured. |
| F-11 | NO SPEC GOVERNS THE `Change.kind` VOCABULARY, so no amendment is owed. `grep` across `.aw/records/specs/` for `noop` returns no requirement defining the `Change` kinds, and the machine-surface contract documents live in `docs/`, not in a spec. The one spec-adjacent constraint found is the in-code note that `unchanged` must not be routed through the lifecycle resolver (`9zvl2w` E-02, spec `uonrjg` R10.3), which this plan honors by not making `unchanged` a status. | `grep` of `.aw/records/specs/`; the `_format_status_transition_line` note read in full. |
| F-12 | ORDER 01 OF THIS SET DOES NOT TOUCH THIS FILE, so the two children of this Set cannot collide. `9jkek2` declares `agent_workflows/run_viewer.py` and `tests/test_run_viewer.py`; this plan declares `agent_workflows/status_set.py` and `tests/test_status_set.py`. The two share no path and no symbol, and neither depends on the other, which is why both carry `- Item-Dependencies: none`. | Both plans' `- Scope-Paths:` compared. |

## Proposed changes (ordered, validatable)

1. Lift the pre-write changed/unchanged predicate into one helper and make the machine dry-run branch emit `noop` with the `(unchanged)` detail for a no-op, correcting its `summary` count to the number that would change (E-01).
2. Carry the same fact into that branch's `data["items"]` rows from the same helper, keeping every existing key (E-02).
3. Add CLI-driven tests over two artifact types and both `set` spellings, including the cross-path agreement property that pins the defect closed (E-03).

## Deferred / out of scope (with reason)

- CHANGING THE HUMAN DRY-RUN OR APPLY LINE is rejected rather than deferred. Both are already correct (F-04), their shape is pinned by shipped tests, and `unchanged` carries an explicit in-code prohibition against being routed through the lifecycle resolver. If any human line moves, the plan has failed.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan, not an outstanding defect: the human surface is the CORRECT reference this plan makes the machine surface match, so no future work is owed.
- IMPORTING `run_selection_policy.render_item_disposition` into `status_set` is rejected rather than deferred. Order 01 of this Set consumes that renderer because `aw runs` has NO per-artifact line; `aw set` already has one whose shape shipped tests pin, so adopting a second format here would be a gratuitous change to a correct surface, and it would add an import to a module `run_selection_policy` itself imports (`status_set`), which is a cycle the executor would then have to defer. The vocabulary this plan reuses is `status_set`'s own `noop` kind (F-07).
  - Carrier-Declined: Nothing is owed. This is a design decision resolved from in-tree evidence in OQ-02, not deferred work, and the cycle direction makes the alternative structurally unavailable rather than merely unattractive.
- MAKING THE APPLY PATH'S PREDICATE AND THE DRY-RUN PREDICATE ONE EXPRESSION is out of scope. They answer the same question from different information (post-write text comparison versus pre-write status comparison, F-06) and unifying them would mean changing how the apply path decides what changed, which is a correctness-critical path this plan has no measurement against. E-01 unifies only the TWO dry-run branches, which genuinely do share a predicate.
  - Carrier-Declined: Nothing is owed AT AUTHORING TIME because no defect has been observed: the two predicates answer the same question from different information and this plan has not measured that they can actually disagree on any real input. The obligation is discharged INSIDE this plan rather than by a carrier: V-01 REQUIRES the executor to state how many changed-predicates remain in `run_set_command` after the change and where each is, and to file a carrier THEN, with the measurement, if more than one path can still disagree about the same artifact.
- EXTENDING THE FIX TO ANY OTHER VERB'S DRY RUN is out of scope. This plan's measurement covers `run_set_command` only. Other verbs with a `--dry-run` may or may not have the same divergence, and asserting they do without measuring would be a claim this plan cannot support.
  - Carrier-Declined: Nothing is owed for the same reason: no other verb has been MEASURED to have this divergence, so an item asserting one would be speculation. V-03 requires the executor to STATE whether any other verb's `--dry-run` was checked and what was found, and to file a carrier THEN, naming its id6, if a real divergence is measured.
- `aw find` AND `aw runs` are out of scope: `aw find` is owned in full by pending plan `zyj8io` (which declares `agent_workflows/cli.py` and `tests/test_cli_find.py` and whose E-03 computes the per-token match fact), and `aw runs` is Order 01 of this Set (`9jkek2`).
  - Carrier-Declined: Nothing is owed. Both obligations `om3rzi` names are held by live plans, so filing an item would assert debt that already has an owner.
- CHANGING WHICH ARTIFACTS A SELECTOR MATCHES, or the zero-match and ambiguity refusals, is rejected rather than deferred. This plan reports on the matched set; it does not compute it. The zero-match refusal (`No <type> artifact matched '<tok>'.` at exit 2) and the kind-aware ambiguity refusals are shipped behavior outside this fence.
  - Carrier-Declined: Nothing is owed; these are prohibitions on this plan rather than defects. Note one adjacent observation recorded for honesty and NOT claimed as this plan's work: the zero-match loop returns on the FIRST unmatched token without reporting the tokens that DID resolve, so a multi-token selection hides which tokens were fine. That is a selector-reporting question in a refusal path, not a disposition-reporting question in a preview path, and this plan neither fixes nor measures it beyond noting it.

## Scope check

- Over-scope: none. `agent_workflows/status_set.py` carries E-01's helper and machine-branch change and E-02's `items` reconciliation; `tests/test_status_set.py` carries E-03's tests. No other module is edited, no new import is added, and no new machine token is introduced (F-07). No spec is amended (F-11). The human surface is untouched (F-04).
- Under-scope: stated rather than left as `none`. This plan does NOT unify the apply path's post-write predicate with the dry-run's pre-write one (F-06), leaving that duplication in place with an obligation on E-01 to report how many copies remain. It does not touch `aw find` (owned by `zyj8io`) or `aw runs` (Order 01). It does not check any other verb's `--dry-run` for the same divergence. And it does not fix the zero-match loop's first-token bail, which is noted in Deferred as an observation rather than claimed as work.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against the F-10 baseline of `3246 passed, 2 skipped`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_status_set.py -o addopts=""` for the per-test counts on the one test file this plan edits.
- A DELIBERATE-FAILURE DEMONSTRATION for E-03: the no-op test and the mixed-count test must be shown FAILING on the pre-E-01 tree, with the pasted failure showing `update` where `noop` is expected and the wrong count. A test that was never red proves nothing.
- A CROSS-PATH AGREEMENT PROBE, which is the central evidence: for the same fixture and selector, run the machine dry-run and then the machine apply, and assert the per-artifact kinds and the changed count AGREE. Paste both payloads side by side. Run it over a MIXED selection, not only a single no-op, because a single-artifact fixture's counts can agree by accident.
- A HUMAN-SURFACE BYTE-IDENTITY PROBE: capture the human dry-run and human apply output for the same fixtures BEFORE the change and assert the post-change output is byte-identical (ANSI-stripped if the harness colors). This is the check that E-01 did not leak into the correct surface.
- A NO-MATCH-SET-CHANGE PROBE: over a fixture spanning several artifact types and both `set` spellings, assert the SET of artifacts appearing in `changes` (and its length) is unchanged from HEAD for every invocation, so the preview still lists everything the selector matched and this plan changed only each entry's kind and the summary count. Paste the number of invocations compared and the count of disagreements, which must be zero.
- A SCHEMA-VALIDITY CHECK: the `--agent` payload must still validate through `agent_schema.assert_valid_agent_record`; paste the validator invocation and result rather than asserting validity by eye.
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote local command output including absolute fixture paths.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be, per F-11.

No spec defines the `result_types.Change` kind vocabulary: `grep` across `.aw/records/specs/` for `noop` returns no requirement governing it, and this plan introduces no new kind in any case, reusing the `noop` the apply path already emits (F-07). The one spec-adjacent constraint in the code being edited is the in-code note that `unchanged` "IS NOT A LIFECYCLE STATUS AND MUST NOT BE ROUTED THROUGH THE RESOLVER" (plan `9zvl2w` E-02, spec `uonrjg` R10.3); this plan honors it by keeping `unchanged` an OUTCOME word in a detail string and never a status value, and an executor must not make the machine branch symmetrical by promoting it.

No shipped contract moves in a direction any consumer can be broken by: the `changes` array keeps its length and its entries' keys, and the only changes are a `kind` value that becomes accurate and a `summary` count that becomes correct. A consumer treating `noop` as unknown already had to handle it, because the apply path emits it today. The `--agent` record must remain schema-valid and the Required tests demand the validator be run rather than assumed.

The machine-surface contract documents live under `docs/` rather than in a spec. The executor must SEARCH `docs/` for any statement about `aw set --dry-run`'s payload, count, or `Change` kinds at execution time; if one exists and this change contradicts it, updating it is an in-scope necessity to justify at finalize with `--scope-reason`, not a reason to stop. This plan does not pre-declare a `docs/` path because none was found to describe this branch.

## Open questions

### OQ-01: Which predicate should the dry-run branch use to decide changed-versus-unchanged?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM IN-TREE EVIDENCE as THE PRE-WRITE PREDICATE THE HUMAN DRY-RUN PATH ALREADY USES, `changed = curr != nstat.strip().lower()`, and it needs no maintainer ruling because the same function already contains the answer for the same situation. Reusing the APPLY path's predicate is REFUSED as structurally impossible rather than merely undesirable: it is `(old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, computed after `apply_status_change` has written the destination and re-read it, so in a dry run there is no `new_text` and no destination to compare (F-06). That unavailability is precisely why the defect exists, and an executor who tries to reuse it will either perform a write in a dry run (unacceptable) or fabricate a comparison. Writing a THIRD predicate is also REFUSED: `run_set_command` would then hold three answers to one question and the two dry-run branches could disagree with each other, which is the same class of defect one layer down. E-01 therefore lifts the existing pre-write expression into one helper consumed by both dry-run branches, and E-01's evidence must state how many changed-predicates remain in the function afterwards so the residual duplication with the apply path is recorded rather than hidden.

### OQ-02: Should this verb adopt `run_selection_policy`'s disposition renderer, as Order 01 does?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as NO, and the reason is structural as well as editorial. EDITORIALLY: `aw runs` has no per-artifact line at all, so Order 01 consuming the shared renderer ADDS a surface; `aw set` already has `_format_status_transition_line`, whose output shape shipped tests pin, so adopting a second format would change a surface measured to be CORRECT (F-04) for no gain, and would put two per-artifact line formats in one verb family. STRUCTURALLY: `run_selection_policy` imports `status_set` as a first-party dependency, so an import in the other direction would be a cycle; the alternative is therefore unavailable rather than merely unattractive, and no deferral is owed. The matched-vs-acted VOCABULARY this plan reuses is the one already inside `status_set`: the `noop` kind, the `(unchanged)` detail wording, and the pre-write `changed` predicate (F-07, OQ-01). That satisfies `om3rzi`'s ask, which is about the DISTINCTION being reported, not about a particular renderer being called.

### OQ-03: Should the dry-run `summary` count matched artifacts or would-change artifacts?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as WOULD-CHANGE, with the matched total preserved elsewhere, because that is what the apply path does and what makes the preview comparable to it. The apply path counts `len([r for r in results if r[3]])` and reports `updated status on 0 artifact(s)` for a no-op; a dry run reporting `would update status on 1 artifact(s)` for the same input is not a preview of it (F-01). Counting MATCHED artifacts is REFUSED for the summary line specifically, because the word in that sentence is "update" and reporting a count of things that would not be updated makes the sentence false; that is the measured 150-percent overstatement in F-03. THE MATCHED TOTAL MUST NOT BE LOST, though, since `om3rzi` is about reporting every matched artifact: it is preserved by the `changes` array continuing to carry ONE ENTRY PER MATCHED ARTIFACT, which E-01's expected outcome requires and the Required tests' no-match-set-change probe pins. So the preview answers both questions, as the apply path does: the array says what matched, the summary says what would be acted on.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/status_set.py` as it stands after E-01 ONLY, showing the lifted predicate helper, the machine dry-run branch emitting `kind="noop"` with the `(unchanged)` detail for a no-op, and the corrected `summary` count. The diff must show NO change to `_format_status_transition_line`, NO change to the apply path, and no new import. Paste the machine dry-run payload for THREE fixtures: an artifact already at the target status (expect `noop` and a count of 0), one that would change (expect `update` and a count of 1), and a MIXED selection (expect the per-artifact kinds and the count to match the human path's, which is the F-03 case). Paste the HUMAN-SURFACE BYTE-IDENTITY PROBE from Required tests, comparing against a pre-change capture rather than against the new code's own output. DISCHARGE OQ-01's RESIDUAL-DUPLICATION OBLIGATION: state how many changed-predicates remain in `run_set_command` after the change and where each is; if more than one path can still disagree about the same artifact, file a carrier with that measurement and name its id6 here. A diff that reuses the apply path's post-write predicate, or that performs any write in the dry-run branch, FAILS this item even if every payload is correct.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/status_set.py` in full (both E-01 and E-02 present), showing the `data["items"]` rows carrying the changed/unchanged fact from the SAME helper and retaining every pre-existing key. Paste a `--json` payload for the mixed fixture showing, per artifact, that the `changes` entry and the `items` row AGREE; paste the key list of one `items` row before and after to prove no key was dropped. State in one sentence which of the two structures is authoritative if a consumer reads both, and if the fact is now carried twice, say so plainly rather than leaving two undeclared sources of truth. Paste the SCHEMA-VALIDITY CHECK: the `--agent` record validated through `agent_schema.assert_valid_agent_record`, with the invocation and its result pasted; do not assert validity by eye.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new tests, and confirm in one sentence that each asserts OBSERVABLE behavior (payload fields, counts, exit codes) and that none reads production source text, counts callers, or pins a docstring (GUIDING_PRINCIPLES P16). Paste the no-op test and the mixed-count test run on the PRE-E-01 tree, both FAILING, with output showing `update` where `noop` is expected and the wrong count. Paste the CROSS-PATH AGREEMENT PROBE over a MIXED selection, with both payloads side by side and the per-artifact kinds and counts shown to agree. Paste evidence that the tests cover TWO artifact types (a plan and a backlog item) and BOTH `set` spellings (typed and untyped), which is what F-05 requires. Paste the NO-MATCH-SET-CHANGE PROBE with the number of invocations compared and zero disagreements. State whether any OTHER verb's `--dry-run` was checked for the same divergence and what was found; if one was found, file a carrier and name its id6 rather than fixing it here. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and state it against the F-10 baseline of `3246 passed, 2 skipped`, comparing failing NODE IDS rather than totals; paste `python3 -m pytest tests/test_status_set.py -o addopts=""`; paste `aw ipd lint` on this plan reporting conforming; paste `aw check`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/status_set.py`, `tests/test_status_set.py` and this plan. Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this-plan>` and checking every hit is either the literal section heading or a mention inside a required-evidence sentence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph, because the plan is NARROWER than its backlog item proposed and deliberately so. `om3rzi` asks to extend matched-vs-acted disposition reporting to `aw ipd set`, implying the verb lacks it. Measured, its HUMAN surface already has it: a dry run over a five-plan Set prints `unchanged` for three and a transition for two, and the renderer takes a `changed` parameter for the purpose (F-02). The real defect is that the MACHINE dry-run branch of `status_set.run_set_command` ignores that distinction and calls every match an `update`, while the APPLY branch of the same function gets it right using a `noop` kind that already ships (F-01, F-07). So this fixes an internal disagreement between two branches of one function, where the correct answer is already in the file, and the count is measurably wrong rather than merely mislabelled: five claimed where two would change (F-03). Because `run_set_command` is the one implementation behind `aw ipd set`, the untyped `aw set` and `aw backlog set`, the fix covers every artifact type (F-05). The fence is two files, no new import, no new machine token, and no spec amendment.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and `status_set.py` is contended by ten other pending plans and its test file by five (F-09), so another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches none of them.

FIRST, REUSING THE APPLY PATH'S PREDICATE. It looks like the obviously correct source of truth and it is unavailable here: it compares file text AFTER a write, so importing it into the dry-run branch means either writing during a dry run, which is the worst possible outcome of this plan, or fabricating a comparison that happens to pass the tests. The human dry-run path in the same function already has the right pre-write predicate (F-06, OQ-01). V-01 fails the item on a diff that does either.

SECOND, A THIRD PREDICATE. Writing a fresh changed-check for the machine branch passes every test and leaves `run_set_command` with three answers to one question, so the two dry-run branches can later disagree with each other. That is the same defect one layer down. E-01 requires ONE helper for both dry-run branches, and V-01 requires the executor to COUNT the remaining predicates and report them.

THIRD, FIXING `changes` AND FORGETTING `items`. The `data["items"]` rows carry the same old_status/new_status claim, so a consumer reading `items` stays misled after a `changes`-only fix, and no shipped test reads `items` at all (F-08). E-02 exists for this and V-02 requires per-artifact agreement between the two structures.

FOURTH, AND THE ONE THAT WOULD BE WORST FOR USERS: LEAKING INTO THE HUMAN SURFACE. The human lines are already correct on both paths and their shape is pinned by shipped tests, but a refactor that lifts a predicate can easily change what `_format_status_transition_line` receives. There is also an explicit in-code prohibition here: `unchanged` must not be routed through the lifecycle resolver, because it is an outcome word and not a status, and doing so prints `?` for a SUCCESSFUL no-op. Do not make the machine branch symmetrical by promoting `unchanged` to a status. V-01's byte-identity probe against a pre-change capture is the check.

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. It does not unify the dry-run and apply predicates (F-06); a residual duplication remains and V-01 requires it to be counted and reported. It does not check any other verb's `--dry-run`. It does not touch `aw find`, which `zyj8io` owns, and does not touch `aw runs`, which is Order 01 of this Set. It also does not fix the zero-match loop's bail on the first unmatched token, which is noted in Deferred as an observation and must not be claimed as fixed. The true claim is that `aw set`'s machine dry run now reports each matched artifact's real disposition and a correct would-change count, agreeing with its own apply path.

THIS PLAN AND ORDER 01 ARE INDEPENDENT. `9jkek2` declares `run_viewer.py` and its test file; this plan declares `status_set.py` and its test file. They share no path and no symbol, neither depends on the other, and both carry `- Item-Dependencies: none` (F-12), so either may execute first.

This plan carries `- Work-Kind: followup` and `- Priority: low`, inherited from backlog item `om3rzi`, which carries NO `- Blocks-Release:` gate. Do not invent one. Backlog item `om3rzi` is set to `graduated` by the runner on verification; do not set it `done` and do not close it here.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted, concrete evidence. Make the transition through the tooled lifecycle (`aw ipd begin` / `aw ipd finalize`), never by a hand edit or a hand `git mv`. In a managed lane the RUNNER owns the transition and `aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001`; if that happens, record the refusal, leave the plan in `pending/` with its evidence, and let the runner finalize.
