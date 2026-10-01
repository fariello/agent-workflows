# IPD: Give aw set dry-run the same per-artifact noop disposition its apply path already reports

- Date: 2026-09-30
- Kind: child
- Concern: `aw set`'s machine DRY-RUN branch reports every matched artifact as an `update` even when the transition is a NO-OP, so a preview claims work the apply path then declines to do. MEASURED in this lane at HEAD `522598b6` on one artifact already at the target status, same repository, same selector, only the flag differing: dry-run emits `summary: "would update status on 1 artifact(s)"` with `changes: [{kind: "update", detail: "status: reviewed -> reviewed"}]`, while apply emits `summary: "updated status on 0 artifact(s)"` with `changes: [{kind: "noop", detail: "status: reviewed (unchanged)"}]`. The `noop` kind and the `(unchanged)` detail therefore ALREADY EXIST and the dry-run branch simply does not use them. The HUMAN surface is correct on both paths (both print `unchanged`), so a machine consumer is told something a human reading the same command is not. On a real multi-artifact selection the count is wrong rather than merely mislabelled: re-proven at review HEAD `13cf0fcc` because the authored fixture drifted, `aw ipd set approved awrenamesel --dry-run --json` over that Set's five now-`approved` plans reports `would update status on 5 artifact(s)` with five `update` entries all detailed `status: approved -> approved`, while the human form of the identical command prints `unchanged  (dry-run)` on all five lines, so the machine claims five and the human claims none.
- Scope: Make the machine dry-run branch of `status_set.run_set_command` report each matched artifact's real disposition, reusing the `noop` kind, the `(unchanged)` detail wording, and the changed/unchanged predicate the APPLY path in the same function already uses. IN: the `if is_dry_run:` machine branch's `Change` construction and its `summary` count; the same branch's `data["items"]` rows if they carry the same claim. OUT: the human dry-run line, which is already correct; the apply path, which is already correct; WHICH artifacts a selector matches; the zero-match and ambiguity refusals; `aw runs` (Order 01 of this Set); and `aw find` (owned by pending plan `zyj8io`).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: om3rzi
- Set: dispreach
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: 4x9min
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-401..PR-406, all FIXED. THE PLAN'S CENTRAL CLAIM REPRODUCES ON LIVE DATA AND I RAN THE REAL COMMANDS RATHER THAN READING THE CODE. On one artifact, same selector, only the flag differing: `aw set approved 95jk4s --json --dry-run` reports `would update status on 1 artifact(s)` / `update` / `status: approved -> approved`, while `--json --yes` reports `updated status on 0 artifact(s)` / `noop` / `status: approved (unchanged)` with the tree left byte-identical. F-04 verifies (the human form prints `unchanged` on both paths), F-05 verifies on a backlog item and on the untyped `aw set`, F-06 verifies (the apply predicate is post-write and structurally unavailable in a dry run), F-08 verifies (`noop` in the test file is only a fixture name and a local), F-11 verifies (no spec mentions `noop`; the agent schema validates the record envelope, not `Change.kind`), and OQ-02's cycle argument verifies (`run_selection_policy` imports `status_set`). THE MOST USEFUL FINDING (PR-401) IS THAT E-02 DID NOT NEED TO INVENT A KEY NAME: the APPLY path's `items` rows ALREADY carry `changed`, so the dry-run branch is missing a key its own sibling publishes, and the two row shapes then differ only by `dry_run`. PR-402 added the `applied=False` guard, because the apply path's parallel line is `applied=changed` and a mechanical "match the apply path" reading would make a preview claim work that never happened. PR-403 corrected the F-10 baseline, which had drifted from the authored `3246 passed` to `3401 passed` within a day and sits beside a midnight-boundary flake in `tests/test_backlog.py` (re-run in isolation, the diff is literally `2026-09-30` against `2026-10-01`), so the plan now demands a self-derived baseline compared by failing NODE IDS. PR-404 re-proved F-03 on the current tree after its fixture Set drifted from 3-reviewed/2-to-review to uniformly `approved`, which yields a STRONGER case (5 claimed versus 0 actual). PR-405 recorded a measured edge case where the prescribed predicate and the human renderer disagree for a statusless artifact targeted at `draft`, unreachable today across all 1915 tracked artifacts. PR-406 refreshed F-09's contention counts (8 and 4, from the authored 10 and 5, membership changed both ways). All three open questions were already resolved from in-tree evidence and I verified each rather than accepting it. Two decisions recorded in the typed review record, both `Reversible: yes`. Structural preflight `conforming` at `author` and at `review-finalize`.
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

3. THE COUNT IS WRONG ON A REAL SELECTION, not merely a label. Authoring measured Set `awrenamesel` when its five plans were three `reviewed` and two `to-review`; that Set is now uniformly `approved`, so the case was RE-PROVEN at review on the current tree and the re-proof is stronger (5 versus 0 rather than 5 versus 2):

   ```text
   $ aw ipd set approved awrenamesel --dry-run --json      (review HEAD 13cf0fcc)
     summary: would update status on 5 artifact(s)
     kinds:   Counter({'update': 5})
     details: Counter({'status: approved -> approved': 5})
   $ aw ipd set approved awrenamesel --dry-run             (human, same selector)
     5 lines, every one reading "unchanged  (dry-run)"
   ```

   So the human says none would change and the machine says five. BUILD YOUR OWN FIXTURE for the test: a tracked Set's statuses drift, as this one did between authoring and review.

WHY THIS IS THE `om3rzi` OBLIGATION AND NOT A SUBSTITUTE FOR IT. The item asks for "matched-vs-acted disposition reporting" on this verb. The distinction it wants is exactly matched (5) versus would-be-acted-on (2); the human surface draws it and the machine surface collapses it. Fixing the machine branch is therefore the whole of the item's ask for this verb, and the executor should not read the item's phrasing as licence to add a second reporting block to a surface that already has one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the dry-run branch tell the truth

- [x] E-01 COMPUTE THE CHANGED/UNCHANGED FACT IN THE MACHINE DRY-RUN BRANCH of `status_set.run_set_command` (the `if is_dry_run:` block guarded by `if ctx.is_agent or ctx.is_json:`) and emit `kind="noop"` with the `(unchanged)` detail wording for a no-op, exactly as the APPLY path does. REUSE THE PREDICATE THE HUMAN DRY-RUN PATH IN THE SAME FUNCTION ALREADY USES rather than writing a third one: that path computes `changed = curr != nstat.strip().lower()` from `normalize_target_status` and the record's current status, and passes it to `_format_status_transition_line(..., changed=changed)`. Prefer lifting that expression into ONE local helper consumed by BOTH dry-run branches over duplicating it, since three copies of one predicate in one function is the drift this plan exists to remove. DO NOT reuse the apply path's predicate verbatim: measured, it is `(old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, which requires the write to have HAPPENED and so is unavailable in a dry run; that asymmetry is the reason the defect exists and E-01 must not pretend otherwise. Also correct the branch's `summary` so its count is the number that WOULD change, matching the apply path's `len([r for r in results if r[3]])` shape rather than `len(matched_records)`.
  LEAVE `applied=False` ON EVERY DRY-RUN ENTRY, added at review because the apply path's parallel line is `applied=changed` and a mechanical "match the apply path" reading would wrongly copy it. Nothing is applied in a dry run, so `applied` must stay `False` for BOTH kinds; the apply path's own no-op entry is also `applied=False` (measured), so the only row where the two branches legitimately differ on this field is a real transition, where apply writes `True` and a preview must not.
  ONE MEASURED EDGE CASE, so the executor is not surprised by it: the prescribed predicate compares `(r.status or "")` while `_format_status_transition_line` internally defaults a missing status to `"draft"`, so for an artifact with an EMPTY or absent `- Status:` targeted at `draft` the predicate yields `changed=True` while the human line still prints `unchanged`. Measured at review: ZERO of 1098 plans, 779 backlog items and 38 specs in the tracked tree have an empty or absent `- Status:`, so the case is unreachable today and this plan does NOT change the predicate to chase it. Do not "fix" it by introducing a second default inside the new helper; if a fixture makes it reachable, record it in V-01's evidence rather than silently diverging from the human path.
  - Depends on: none
  - Expected outcome: for an artifact already at the target status, the machine dry-run emits `kind="noop"` and a detail matching the apply path's `(unchanged)` wording; for one that would change, it still emits `kind="update"` with the `old -> new` detail; `applied` is `False` on every entry regardless of kind; the `summary` count equals the number that would change; every matched artifact still appears in `changes` exactly once, so the preview remains a complete list of what the selector matched.
  - Execution state: performed

- [x] E-02 RECONCILE THE BRANCH'S `data["items"]` ROWS with the same fact, since they carry the same claim in a second place. Each row currently reports `old_status` and `new_status` with no indication that the two may be equal, so a consumer reading `items` rather than `changes` is misled even after E-01. USE THE KEY NAME `changed`, AND DO NOT INVENT ONE: review MEASURED that the APPLY path's `items` rows ALREADY carry exactly this key (its row keys are `['changed', 'new_status', 'old_status', 'path', 'type']` with `changed: false` on a no-op, against the dry-run branch's `['dry_run', 'new_status', 'old_status', 'path', 'type']`), so the dry-run branch is not missing a fact that needs a new name, it is missing a key its own sibling branch already publishes. Adding `changed` therefore makes the two branches' `items` rows CONVERGE on one shape, which is the same argument E-01 makes for `changes`, and inventing a different spelling (`is_noop`, `unchanged`, `will_change`) would create the very divergence this plan exists to remove. Populate it from the SAME helper E-01 lifted, and keep every existing key, including `dry_run`, so no consumer breaks.
  THE FACT IS THEN DELIBERATELY CARRIED TWICE, which is correct and must be stated rather than treated as a defect to resolve: `changes[].kind` is the MACHINE-CONTRACT surface (the `Change` record a generic consumer reads across every verb) and `data["items"][].changed` is the COMMAND-SPECIFIC surface, and the apply path already carries it in both places for the same reason. Both derive from one helper, so they cannot disagree; state in the evidence that `changes[].kind` is authoritative for a cross-verb consumer and that `items[].changed` is the convenience mirror, matching what the apply path already does.
  - Depends on: E-01
  - Expected outcome: the dry-run branch's `items` rows carry a `changed` boolean whose name and meaning MATCH the apply path's existing key, every pre-existing key (including `dry_run`) is retained, a consumer reading either `changes` or `data["items"]` gets the same answer about the same artifact, and the two branches' `items` row key sets differ only by the dry-run branch's `dry_run` flag.
  - Execution state: performed

### Task group 2: coverage

- [x] E-03 ADD TESTS to `tests/test_status_set.py` driving the REAL CLI and asserting on the emitted machine payload: a no-op dry run emits `noop` and the `(unchanged)` detail; a real transition still emits `update`; a MIXED selection (the sharpest case, F-03) reports the correct changed count and the correct per-artifact kinds; and THE CROSS-PATH AGREEMENT PROPERTY, which is the assertion that actually pins this defect closed - for the same fixture and selector, the dry-run payload's per-artifact kinds and changed count MATCH what the apply path then emits. Cover at least TWO artifact types (a plan and a backlog item), because `run_set_command` is shared and the defect was measured on both, and cover the untyped `aw set` spelling alongside a typed one. Assert on payload fields and exit codes only; do NOT read production source text, count callers, or pin a docstring (GUIDING_PRINCIPLES P16).
  - Depends on: E-02
  - Expected outcome: the new tests FAIL on the pre-E-01 tree (the no-op case fails asserting `noop` where `update` is emitted, and the mixed case fails on the count) and pass after E-02; the cross-path agreement test would go red again if either branch's predicate drifted; the human dry-run line's existing shipped assertions still pass unmodified.
  - Execution state: performed

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
| F-02 | THE ITEM'S PREMISE FOR THIS VERB IS FALSIFIED, and this is the finding that reshaped the plan. `om3rzi` implies `aw ipd set` lacks matched-vs-acted reporting. Measured at authoring, its HUMAN surface has it: `aw ipd set reviewed awrenamesel --dry-run` printed five lines, three reading `unchanged` and two reading `to-review -> reviewed`, and `_format_status_transition_line` takes a `changed` parameter for exactly this purpose. RE-VERIFIED AT REVIEW on the drifted tree, which confirms the premise independently of the fixture: the same verb over the same Set (now uniformly `approved`, targeted at `approved`) prints `unchanged  (dry-run)` on all five lines, so the human surface still draws the distinction the item says is missing. So the work is to fix the MACHINE branch that ignores the distinction, not to add a reporting surface. | Command run against the tracked `awrenamesel` Set at authoring (counted `3` unchanged, `2` transitions) and re-run at review HEAD `13cf0fcc` (five `unchanged` lines); `_format_status_transition_line`'s signature read, along with its `changed`/`unchanged` branch and the in-code `unchanged` prohibition note. |
| F-03 | THE COUNT IS WRONG, NOT MERELY THE LABEL, which is the sharpest evidence and the case a test should pin. Authoring measured it over Set `awrenamesel` when its five plans were three `reviewed` and two `to-review`: `aw ipd set reviewed awrenamesel --dry-run --json` reported `would update status on 5 artifact(s)` with all five `kind="update"`, where only TWO would change. THE PARTICULAR FIXTURE HAS SINCE DRIFTED (re-measured at review: all five of that Set are now `approved`), SO THE DEFECT WAS RE-PROVEN ON THE CURRENT TREE RATHER THAN RE-CITED: `aw ipd set approved awrenamesel --dry-run --json` reports `would update status on 5 artifact(s)` with `Counter({'update': 5})` and every detail reading `status: approved -> approved`, while the HUMAN form of the same command prints `unchanged (dry-run)` on all five lines. That is a 5-versus-0 disagreement, a stronger case than the authored 5-versus-2. THE LESSON FOR THE EXECUTOR: build your own mixed fixture rather than selecting a tracked Set, because a tracked Set's statuses move. | Both the authored and the review re-measurement run against the live tree; `--json` payloads captured and their `changes` kinds counted; the human output of the identical selector captured for contrast; the five plans' current statuses read from their front matter. |
| F-04 | THE HUMAN SURFACE IS CORRECT ON BOTH PATHS, which bounds this plan to the machine branch and rules out an output change users would see. `aw ipd set reviewed aaa111 --dry-run` prints `unchanged  (dry-run)` and the apply path prints `unchanged`. | Both commands run in the fixture repo; both lines captured. |
| F-05 | THE DEFECT SPANS EVERY ARTIFACT TYPE AND EVERY `set` SPELLING, because `run_set_command` is the single shared implementation. `aw backlog set open bbb222 --json --dry-run` on an already-`open` item emits `update` / `status: open -> open` while its apply path emits `noop` / `status: open (unchanged)`; the untyped `aw set reviewed aaa111 --json --dry-run` reproduces the plan case identically. This is why E-03 requires two artifact types and both spellings. | A backlog item added to the fixture; four commands run (`backlog set` dry-run and apply, untyped `set` dry-run); every payload captured; `grep` for `run_set_command` across `agent_workflows/` showing `work_cmd` and `cli` as the callers. |
| F-06 | THE APPLY PATH'S PREDICATE IS STRUCTURALLY UNAVAILABLE IN A DRY RUN, which is the ROOT CAUSE and the trap E-01 must route around. It is `changed = (old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, computed AFTER `apply_status_change` has written the file, so it cannot be reused verbatim where nothing is written. The human dry-run path already solves this with a pre-write predicate, `changed = curr != nstat.strip().lower()`, in the same function. So the fix is to reuse the PRE-WRITE predicate, and E-01 says so explicitly. | Both predicates read in `run_set_command`; the write ordering read (the apply predicate follows the `apply_status_change` call and a `read_text` of the destination). |
| F-07 | THE `noop` KIND AND THE `(unchanged)` WORDING ALREADY SHIP, so this plan adds NO new machine vocabulary and no consumer sees an unfamiliar token. The apply path constructs `kind="update" if changed else "noop"`, and `result_types.Change` carries the `kind` field. | The apply path's `Change` construction read in full; `result_types.Change` read; the `noop` kind observed in a real apply-path payload (F-01). |
| F-08 | NO EXISTING TEST COVERS THE MACHINE DRY-RUN DISPOSITION, so E-03 is new coverage rather than a duplicate. `tests/test_status_set.py` contains `noop` only inside an unrelated fixture name (`gatenoop`) and one `rc_noop` local for a human-path no-op exit code; neither asserts on an emitted `kind`. No test asserts on a dry-run `changes[].kind` at all. | Searches over `tests/test_status_set.py` for `noop` (two hits, both classified by reading them) and for a dry-run payload-kind assertion (none). |
| F-09 | NO OTHER PENDING PLAN DECLARES THIS PLAN'S EXACT PAIR, but BOTH ITS FILES ARE CONTENDED and the executor must expect to re-read before editing. THE COUNTS AND THE MEMBERSHIP BOTH DRIFT, which is why this row is context and not a bar. Authoring measured TEN plans declaring `agent_workflows/status_set.py` and FIVE declaring `tests/test_status_set.py`; re-measured at review HEAD `13cf0fcc` the counts are EIGHT (`47ttnv`, `5poaqh`, `e25iy9`, `izh17y`, `jw6cm3`, `nvsz19`, `x4vf9p`, `xvon5j`) and FOUR (`5poaqh`, `jw6cm3`, `nvsz19`, `tr8ugt`), with membership changed in both directions (`e25iy9` and `izh17y` arrived; `0ykozn`, `ghna7l`, `4a8yws` and `tr8ugt` left the module list). NONE targets the dry-run machine branch. File overlap is not a runtime hazard under the runner (each item gets an isolated worktree and returns through the merge-and-revalidate gate), but it IS a reason to re-read the function before editing. DO NOT treat either number as an acceptance criterion; re-derive it if you need it. | Scan of `- Scope-Paths:` across all pending plans with each plan's `- Id:` read directly, re-run at review (8 and 4, against the authored 10 and 5); each contending plan's scope line read to classify its subject. |
| F-10 | **CORRECTED AT REVIEW: THE AUTHORED BASELINE IS STALE AND THE BARE TREE IS NOT UNCONDITIONALLY GREEN, so "compare against `3246 passed`" is the wrong bar twice over.** Authoring measured `3246 passed, 2 skipped, 3 warnings in 144.70s` at HEAD `522598b6`. Re-measured at review HEAD `13cf0fcc`: `1 failed, 3401 passed, 2 skipped, 3 warnings in 118.74s`, a drift of 155 tests. The one failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` and it is a MIDNIGHT-BOUNDARY FLAKE, not a regression and not this plan's: the test writes two records in sequence and compares their rendered history lines, so it fails when the UTC date rolls over between the two writes (re-run in isolation, the assertion diff is `- 2026-09-30 HIST_ACTOR` against `+ 2026-10-01 HIST_ACTOR`). That file is outside this plan's `- Scope-Paths:` and is unmodified in this lane (`git diff --name-only tests/test_backlog.py` is empty). Order 01 of this same Set (`9jkek2`) recorded the identical finding at its own review, independently. THE CONSEQUENCE: re-derive your own pre-change baseline and compare FAILING NODE IDS rather than totals, because zero failures is not achievable at every hour of the day. | Bare `python3 -m pytest` run at review HEAD and its summary pasted; the single failure re-run with `-o addopts=""` showing the date diff; `git status --short` clean. |
| F-11 | NO SPEC GOVERNS THE `Change.kind` VOCABULARY, so no amendment is owed. `grep` across `.aw/records/specs/` for `noop` returns no requirement defining the `Change` kinds, and the machine-surface contract documents live in `docs/`, not in a spec. The one spec-adjacent constraint found is the in-code note that `unchanged` must not be routed through the lifecycle resolver (`9zvl2w` E-02, spec `uonrjg` R10.3), which this plan honors by not making `unchanged` a status. | `grep` of `.aw/records/specs/`; the `_format_status_transition_line` note read in full. |
| F-12 | ORDER 01 OF THIS SET DOES NOT TOUCH THIS FILE, so the two children of this Set cannot collide. `9jkek2` declares `agent_workflows/run_viewer.py` and `tests/test_run_viewer.py`; this plan declares `agent_workflows/status_set.py` and `tests/test_status_set.py`. The two share no path and no symbol, and neither depends on the other, which is why both carry `- Item-Dependencies: none`. | Both plans' `- Scope-Paths:` compared, re-verified at review (`9jkek2` is `- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py`; disjoint from this plan's pair). |
| F-13 | **ADDED AT REVIEW, AND IT DECIDES E-02's KEY NAME: THE APPLY PATH'S `items` ROWS ALREADY CARRY A `changed` KEY, so the dry-run branch is not missing a fact that needs a new name, it is missing a key its own sibling already publishes.** Measured on the same artifact, same selector, only the flag differing: the apply row's keys are `['changed', 'new_status', 'old_status', 'path', 'type']` with `changed: false` on a no-op, while the dry-run row's are `['dry_run', 'new_status', 'old_status', 'path', 'type']`. So adding `changed` makes the two branches' `items` shape CONVERGE, and any other spelling (`is_noop`, `unchanged`, `will_change`) would introduce exactly the divergence this plan exists to remove. | `aw set approved 95jk4s --json --yes` and `--json --dry-run` run against the live tree; both `data["items"][0]` key lists captured and compared; the apply path's `"changed": changed` row construction read in `run_set_command`. |
| F-14 | **ADDED AT REVIEW: `applied` MUST NOT BE COPIED FROM THE APPLY PATH, which a mechanical "match the apply path" reading would do.** The apply path builds `applied=changed`, so copying that line into the dry-run branch would make a PREVIEW of a real transition claim `applied: true` for work that did not happen, which is a worse defect than the one being fixed. Measured: the apply path's own no-op entry is `applied=False`, so the two branches legitimately agree on `applied` for a no-op and must differ for a transition. | The apply path's `Change(... applied=changed ...)` construction read; a real apply-path no-op payload captured showing `applied: false`; the dry-run branch's existing `applied=False` read. |
| F-15 | **ADDED AT REVIEW, LOW AND UNREACHABLE TODAY: the prescribed predicate and the human renderer disagree for an artifact with NO status targeted at `draft`.** `_format_status_transition_line` internally defaults a missing status to `"draft"` (`old_status = (rec.status or "draft").strip().lower()`) and renders `unchanged` when `old_status == norm_stat_clean`, while the dry-run predicate compares `(r.status or "")`, yielding `changed=True`. Measured at review: ZERO of 1098 plans, 779 backlog items and 38 specs in the tracked tree carry an empty or absent `- Status:`, so no real artifact reaches it. | The renderer's `or "draft"` default and its `not changed or old_status == norm_stat_clean` condition read; the predicate simulated over the three inputs (`None`, `""`, `"draft"`); a scan of all three record trees for an empty or absent `- Status:` returning zero. |
| F-16 | **ADDED AT REVIEW: `status_set.py` is the ONLY producer of `kind="noop"` in the whole package, which strengthens F-07's "no new vocabulary" claim and also bounds it honestly.** A scan of `agent_workflows/**/*.py` for a `Change(kind=...)` literal finds `noop` at exactly one site, the apply path this plan copies. Separately, `result_types.Change`'s own docstring comment enumerates the kinds as `"modify", "create", "delete", "rename"`, which lists NEITHER `update` nor `noop`, so that comment is already stale against shipped behavior independently of this plan. | `grep` for `"noop"` across `agent_workflows/*.py` (four hits, three unrelated: two migration return values and two run-analytics taxonomy values) and for `kind="..."` literals; `result_types.Change` read in full. |

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
- CORRECTING `result_types.Change`'s STALE KIND-VOCABULARY COMMENT is out of scope, ADDED AT REVIEW (F-16) so it is recorded rather than discovered. That docstring enumerates the kinds as `"modify", "create", "delete", "rename"` and names NEITHER `update` nor `noop`, both of which ship today, so it is already wrong independently of this plan and this plan does not make it more wrong: `noop` is emitted by the apply path now and `update` by the dry-run branch now. Fixing it would put `agent_workflows/result_types.py` in `- Scope-Paths:` for a comment, and that file is the shared machine-contract type every verb's payload flows through, which is a wider blast radius than a two-branch reconciliation warrants.
  - Carrier-Declined: NOTHING IS OWED BY THIS PLAN and no gap is being hidden, because the comment's inaccuracy predates this plan and is unchanged by it. It is recorded here as a FINDING (F-16) with the measurement, which is the durable form for an observation a later reader can act on; filing an item would assert that this plan discovered a defect it is declining to fix, when what it actually did was measure that an adjacent comment was already stale. If a maintainer wants the comment corrected, it is a one-line edit in a file no E-item here touches.
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

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted. COMPARE FAILING NODE IDS AGAINST YOUR OWN PRE-CHANGE BASELINE, NOT AGAINST A NUMBER IN THIS PLAN: F-10 was corrected at review because the authored `3246 passed` had already drifted to `3401 passed` within a day, and because the tree carries a midnight-boundary flake (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`) that fails whenever the UTC date rolls over mid-test, so "zero failures" is not achievable at every hour. Capture a bare run BEFORE editing, capture one after, and show the failing-node-id SET is unchanged. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
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

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/status_set.py` as it stands after E-01 ONLY, showing the lifted predicate helper, the machine dry-run branch emitting `kind="noop"` with the `(unchanged)` detail for a no-op, and the corrected `summary` count. The diff must show NO change to `_format_status_transition_line`, NO change to the apply path, and no new import. Paste the machine dry-run payload for THREE fixtures: an artifact already at the target status (expect `noop` and a count of 0), one that would change (expect `update` and a count of 1), and a MIXED selection (expect the per-artifact kinds and the count to match the human path's, which is the F-03 case). Paste the HUMAN-SURFACE BYTE-IDENTITY PROBE from Required tests, comparing against a pre-change capture rather than against the new code's own output. SHOW `applied` IS `False` ON EVERY DRY-RUN ENTRY of both kinds (F-14), since the apply path's parallel line is `applied=changed` and copying it would make a preview of a real transition claim work that did not happen. DISCHARGE OQ-01's RESIDUAL-DUPLICATION OBLIGATION: state how many changed-predicates remain in `run_set_command` after the change and where each is; if more than one path can still disagree about the same artifact, file a carrier with that measurement and name its id6 here. A diff that reuses the apply path's post-write predicate, or that performs any write in the dry-run branch, FAILS this item even if every payload is correct.
  - Observed evidence: PASS. Predicate helper lifted into dry-run branch, machine payloads and byte-identity verified below.
    1. `git diff agent_workflows/status_set.py` after E-01 ONLY:
       ```diff
       @@ -2265,21 +2265,32 @@ def run_set_command(
                return get_renderer(ctx).emit(res, ctx)

            if is_dry_run:
       +        def _dry_run_disposition(r: ArtifactRecord) -> tuple[str, bool]:
       +            nstat = normalize_target_status(target_status, r.record_type)
       +            curr = (r.status or "").strip().lower()
       +            return nstat, curr != nstat.strip().lower()
       +
       +        dry_results = [(r, *_dry_run_disposition(r)) for r in matched_records]
       +
                if ctx.is_agent or ctx.is_json:
                    changes = [
                        Change(
                            path=str(r.path),
       -                    kind="update",
       +                    kind="update" if changed else "noop",
                            applied=False,
       -                    detail=f"status: {r.status or '-'} -> {normalize_target_status(target_status, r.record_type)}",
       +                    detail=(
       +                        f"status: {r.status or '-'} -> {nstat}"
       +                        if changed
       +                        else f"status: {nstat} (unchanged)"
       +                    ),
                        )
       -                for r in matched_records
       +                for r, nstat, changed in dry_results
                    ]
                    res = CommandResult(
                        command="set",
                        status="clean",
                        exit_code=0,
       -                summary=f"would update status on {len(matched_records)} artifact(s)",
       +                summary=f"would update status on {len([r for r, _, changed in dry_results if changed])} artifact(s)",
                        changes=changes,
                        data={
                            "items": [
       @@ -2300,10 +2311,7 @@ def run_set_command(
                    )
                    return get_renderer(ctx).emit(res, ctx)

       -        for r in matched_records:
       -            nstat = normalize_target_status(target_status, r.record_type)
       -            curr = (r.status or "").strip().lower()
       -            changed = curr != nstat.strip().lower()
       +        for r, nstat, changed in dry_results:
                    term.line(
                        _format_status_transition_line(
                            r, r.path, nstat, term, args, dry_run=True, changed=changed
       ```
       Diff shows no changes to `_format_status_transition_line`, no changes to apply path, and no new imports.
    2. Machine dry-run payloads for three fixtures:
       - Already at target (pl0001, reviewed -> reviewed):
         `summary: "would update status on 0 artifact(s)"`
         `changes: [{"path": ".aw/records/plans/pending/20261001-fix01-01-pl0001-plan.ipd.md", "kind": "noop", "detail": "status: reviewed (unchanged)", "applied": false}]`
       - Would change (pl0002, draft -> reviewed):
         `summary: "would update status on 1 artifact(s)"`
         `changes: [{"path": ".aw/records/plans/pending/20261001-fix02-01-pl0002-plan.ipd.md", "kind": "update", "detail": "status: draft -> reviewed", "applied": false}]`
       - Mixed selection (mix01: mx0001 reviewed, mx0002 reviewed, mx0003 draft, target reviewed):
         `summary: "would update status on 1 artifact(s)"`
         `changes: [{"path": "...mx0002...", "kind": "noop", "detail": "status: reviewed (unchanged)", "applied": false}, {"path": "...mx0001...", "kind": "noop", "detail": "status: reviewed (unchanged)", "applied": false}, {"path": "...mx0003...", "kind": "update", "detail": "status: draft -> reviewed", "applied": false}]`
    3. Human-surface byte-identity probe against pre-change capture:
       - Fixture 1: `-    plan        20261001-fix01-01-pl0001  [medium]  unchanged  (dry-run)` -> byte-identical (True).
       - Fixture 2: `-    plan        20261001-fix02-01-pl0002  [medium]  draft → ◑  reviewed  (dry-run)` -> byte-identical (True).
       - Fixture 3: 3 lines matching pre-change capture exactly -> byte-identical (True).
    4. `applied` is False on every dry-run entry:
       Captured `applied` values across all fixtures: `[False, False, False, False, False]`. All are False.
    5. OQ-01 residual duplication obligation:
       Exactly two changed-predicates remain in `run_set_command`:
       (a) `_dry_run_disposition` at the top of `if is_dry_run:` (pre-write status comparison, shared by machine and human dry-run branches)
       (b) Apply path post-write check at line 2321: `changed = (old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`.
       Both paths agree on every valid transition; no carrier is owed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/status_set.py` in full (both E-01 and E-02 present), showing the `data["items"]` rows carrying the changed/unchanged fact from the SAME helper and retaining every pre-existing key. PROVE THE KEY NAME MATCHES THE APPLY PATH (F-13): paste the sorted `items` row key list from the dry-run branch and from the apply path for the SAME artifact, and show they differ ONLY by the dry-run branch's `dry_run` flag; the dry-run row must carry `changed`, not any other spelling. Measured at review before the change, for contrast: apply is `['changed', 'new_status', 'old_status', 'path', 'type']` and dry-run is `['dry_run', 'new_status', 'old_status', 'path', 'type']`. Paste a `--json` payload for the mixed fixture showing, per artifact, that the `changes` entry and the `items` row AGREE; paste the key list of one `items` row before and after to prove no key was dropped. State in one sentence that the fact is deliberately carried twice, with `changes[].kind` authoritative for a cross-verb consumer and `items[].changed` the convenience mirror, which is what the apply path already does. Paste the SCHEMA-VALIDITY CHECK: the `--agent` record validated through `agent_schema.assert_valid_agent_record`, with the invocation and its result pasted; do not assert validity by eye.
  - Observed evidence: PASS. data["items"] rows carry changed matching apply path, schema verified below.
    1. Full `git diff agent_workflows/status_set.py`:
       ```diff
       diff --git a/agent_workflows/status_set.py b/agent_workflows/status_set.py
       index 2834221c7..4fef5cdb6 100644
       --- a/agent_workflows/status_set.py
       +++ b/agent_workflows/status_set.py
       @@ -2265,21 +2265,32 @@ def run_set_command(
                return get_renderer(ctx).emit(res, ctx)

            if is_dry_run:
       +        def _dry_run_disposition(r: ArtifactRecord) -> tuple[str, bool]:
       +            nstat = normalize_target_status(target_status, r.record_type)
       +            curr = (r.status or "").strip().lower()
       +            return nstat, curr != nstat.strip().lower()
       +
       +        dry_results = [(r, *_dry_run_disposition(r)) for r in matched_records]
       +
                if ctx.is_agent or ctx.is_json:
                    changes = [
                        Change(
                            path=str(r.path),
       -                    kind="update",
       +                    kind="update" if changed else "noop",
                            applied=False,
       -                    detail=f"status: {r.status or '-'} -> {normalize_target_status(target_status, r.record_type)}",
       +                    detail=(
       +                        f"status: {r.status or '-'} -> {nstat}"
       +                        if changed
       +                        else f"status: {nstat} (unchanged)"
       +                    ),
                        )
       -                for r in matched_records
       +                for r, nstat, changed in dry_results
                    ]
                    res = CommandResult(
                        command="set",
                        status="clean",
                        exit_code=0,
       -                summary=f"would update status on {len(matched_records)} artifact(s)",
       +                summary=f"would update status on {len([r for r, _, changed in dry_results if changed])} artifact(s)",
                        changes=changes,
                        data={
                            "items": [
       @@ -2287,12 +2298,11 @@ def run_set_command(
                                    "path": str(r.path),
                                    "type": r.record_type,
                                    "old_status": r.status,
       -                            "new_status": normalize_target_status(
       -                                target_status, r.record_type
       -                            ),
       +                            "new_status": nstat,
       +                            "changed": changed,
                                    "dry_run": True,
                                }
       -                        for r in matched_records
       +                        for r, nstat, changed in dry_results
                            ]
                        },
                        verified=True,
       @@ -2300,10 +2311,7 @@ def run_set_command(
                    )
                    return get_renderer(ctx).emit(res, ctx)

       -        for r in matched_records:
       -            nstat = normalize_target_status(target_status, r.record_type)
       -            curr = (r.status or "").strip().lower()
       -            changed = curr != nstat.strip().lower()
       +        for r, nstat, changed in dry_results:
                    term.line(
                        _format_status_transition_line(
                            r, r.path, nstat, term, args, dry_run=True, changed=changed
       ```
    2. Prove key name matches apply path (F-13):
       Sorted dry-run items[0] keys: `['changed', 'dry_run', 'new_status', 'old_status', 'path', 'type']`
       Sorted apply items[0] keys:   `['changed', 'new_status', 'old_status', 'path', 'type']`
       Keys diff (dry - app): `{'dry_run'}`
       Keys diff (app - dry): `set()`
       Dry-run row carries `changed`, matching the apply path exactly.
    3. `--json` payload for mixed fixture and agreement:
       Per-artifact agreement verified:
       - mx0001: kind='noop' -> changed=False (agreement: True)
       - mx0002: kind='noop' -> changed=False (agreement: True)
       - mx0003: kind='update' -> changed=True (agreement: True)
       Key list before: `['dry_run', 'new_status', 'old_status', 'path', 'type']`
       Key list after:  `['changed', 'dry_run', 'new_status', 'old_status', 'path', 'type']`
       No key dropped.
    4. Two-surface statement:
       The changed/unchanged fact is deliberately carried twice, with `changes[].kind` authoritative for a cross-verb generic consumer and `items[].changed` the convenience mirror for command-specific consumers, matching what the apply path already does.
    5. Schema validity check:
       Ran `agent_schema.assert_valid_agent_record(agent_record)` against `--agent` payload; validated cleanly with no exceptions.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new tests, and confirm in one sentence that each asserts OBSERVABLE behavior (payload fields, counts, exit codes) and that none reads production source text, counts callers, or pins a docstring (GUIDING_PRINCIPLES P16). Paste the no-op test and the mixed-count test run on the PRE-E-01 tree, both FAILING, with output showing `update` where `noop` is expected and the wrong count. Paste the CROSS-PATH AGREEMENT PROBE over a MIXED selection, with both payloads side by side and the per-artifact kinds and counts shown to agree. Paste evidence that the tests cover TWO artifact types (a plan and a backlog item) and BOTH `set` spellings (typed and untyped), which is what F-05 requires. Paste the NO-MATCH-SET-CHANGE PROBE with the number of invocations compared and zero disagreements. State whether any OTHER verb's `--dry-run` was checked for the same divergence and what was found; if one was found, file a carrier and name its id6 rather than fixing it here. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line from BEFORE and AFTER the change and show the failing-node-id SET is unchanged, which is the comparison F-10 requires; do NOT compare against any total written in this plan, since the authored `3246` had drifted to `3401` within a day and the tree carries a midnight-boundary flake, so a bare total is not a bar; paste `python3 -m pytest tests/test_status_set.py -o addopts=""`; paste `aw ipd lint` on this plan reporting conforming; paste `aw check`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/status_set.py`, `tests/test_status_set.py` and this plan. Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this-plan>` and checking every hit is either the literal section heading or a mention inside a required-evidence sentence.
  - Observed evidence: PASS. Observable test suite added, deliberate failure demo red, and suite no-regression verified below.
    1. Full committed source of new tests:
       `tests/test_status_set.py` `TestDryRunMachineDisposition` (methods: `test_dry_run_noop_plan_emits_noop_and_unchanged_detail`, `test_dry_run_transition_plan_emits_update`, `test_dry_run_mixed_selection_counts_and_dispositions`, `test_cross_path_agreement_property_mixed_selection`, `test_dry_run_backlog_item_typed_and_untyped_spellings`, `test_dry_run_agent_schema_conformance`).
       Confirmation: Each test asserts strictly on observable behavior (payload fields, exit codes, summary counts, JSON dictionaries, and schema conformance) and none reads production source text, counts callers, or pins a docstring (GUIDING_PRINCIPLES P16).
    2. Deliberate failure demonstration on PRE-E-01 tree:
       ```
       FAILED tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings - AssertionError: 'would update status on 1 artifact(s)' != 'would update status on 0 artifact(s)'
       FAILED tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_transition_plan_emits_update - KeyError: 'changed'
       FAILED tests/test_status_set.py::TestDryRunMachineDisposition::test_cross_path_agreement_property_mixed_selection - AssertionError: 'would update status on 2 artifact(s)' != 'would update status on 1 artifact(s)'
       FAILED tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_noop_plan_emits_noop_and_unchanged_detail - AssertionError: 'would update status on 1 artifact(s)' != 'would update status on 0 artifact(s)'
       FAILED tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_mixed_selection_counts_and_dispositions - AssertionError: 'would update status on 3 artifact(s)' != 'would update status on 1 artifact(s)'
       ================== 5 failed, 1 passed, 82 deselected in 7.13s ==================
       ```
    3. Cross-path agreement probe over mixed selection:
       Dry-run: `summary: "would update status on 1 artifact(s)"`, 2 noops, 1 update.
       Apply: `summary: "updated status on 1 artifact(s)"`, 2 noops, 1 update (plus manifest index updates).
       Every matched artifact's kind, detail, and changed boolean agree 1:1.
    4. Two artifact types and both spellings:
       Covered in `test_dry_run_backlog_item_typed_and_untyped_spellings` (backlog item, typed `aw backlog set` and untyped `aw set`) and plan tests (plan, typed `aw ipd set` and untyped `aw set`).
    5. No-match-set-change probe:
       9 invocations compared; 0 disagreements between matched selector records and dry-run preview changes array.
    6. Other verbs' `--dry-run`:
       Inspected all `--dry-run` occurrences in `agent_workflows/cli.py` (`setup-repo`, `uninstall`, `companion`, `shell-integration`). None are status/disposition setters; `status_set.py` is the single engine for artifact transitions in the repository. No other verb has this divergence.
    7. Bare `python3 -m pytest` output:
       Before change:
       `3665 passed, 2 skipped, 3 warnings in 133.86s (0:02:13)`
       After change:
       `3671 passed, 2 skipped, 3 warnings in 122.37s (0:02:02)`
       Failing node ID set is identical (empty set before and after; 0 failures).
    8. `python3 -m pytest tests/test_status_set.py -o addopts=""`:
       `============================= 88 passed in 13.42s ==============================`
    9. `aw ipd lint` on this plan:
       `-    ◕  approved     plan        20260930-dispreach-02-4x9min  [low]  conforming`
    10. `aw check`:
        Clean for plan 4x9min and status_set (0 findings).
    11. `aw sanitize --agent`:
        `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    12. `git diff --cached --name-only`:
        Lists exactly `agent_workflows/status_set.py`, `tests/test_status_set.py`, and this plan file.
    13. No placeholder text:
        `grep -n 'TODO' <this-plan>` matches only the section header on line 70 and the mention in line 217.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph, because the plan is NARROWER than its backlog item proposed and deliberately so. `om3rzi` asks to extend matched-vs-acted disposition reporting to `aw ipd set`, implying the verb lacks it. Measured, its HUMAN surface already has it: a dry run over a five-plan Set prints `unchanged` for three and a transition for two, and the renderer takes a `changed` parameter for the purpose (F-02). The real defect is that the MACHINE dry-run branch of `status_set.run_set_command` ignores that distinction and calls every match an `update`, while the APPLY branch of the same function gets it right using a `noop` kind that already ships (F-01, F-07). So this fixes an internal disagreement between two branches of one function, where the correct answer is already in the file, and the count is measurably wrong rather than merely mislabelled: five claimed where two would change (F-03). Because `run_set_command` is the one implementation behind `aw ipd set`, the untyped `aw set` and `aw backlog set`, the fix covers every artifact type (F-05). The fence is two files, no new import, no new machine token, and no spec amendment.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and both files are contended by other pending plans (F-09, measured at review as eight and four, down from the authored ten and five, with membership changed in both directions, so re-derive rather than citing either figure), so another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches none of them.

FIRST, REUSING THE APPLY PATH'S PREDICATE. It looks like the obviously correct source of truth and it is unavailable here: it compares file text AFTER a write, so importing it into the dry-run branch means either writing during a dry run, which is the worst possible outcome of this plan, or fabricating a comparison that happens to pass the tests. The human dry-run path in the same function already has the right pre-write predicate (F-06, OQ-01). V-01 fails the item on a diff that does either.

SECOND, A THIRD PREDICATE. Writing a fresh changed-check for the machine branch passes every test and leaves `run_set_command` with three answers to one question, so the two dry-run branches can later disagree with each other. That is the same defect one layer down. E-01 requires ONE helper for both dry-run branches, and V-01 requires the executor to COUNT the remaining predicates and report them.

THIRD, FIXING `changes` AND FORGETTING `items`. The `data["items"]` rows carry the same old_status/new_status claim, so a consumer reading `items` stays misled after a `changes`-only fix, and no shipped test reads `items` at all (F-08). E-02 exists for this and V-02 requires per-artifact agreement between the two structures.

FOURTH, AND THE ONE THAT WOULD BE WORST FOR USERS: LEAKING INTO THE HUMAN SURFACE. The human lines are already correct on both paths and their shape is pinned by shipped tests, but a refactor that lifts a predicate can easily change what `_format_status_transition_line` receives. There is also an explicit in-code prohibition here: `unchanged` must not be routed through the lifecycle resolver, because it is an outcome word and not a status, and doing so prints `?` for a SUCCESSFUL no-op. Do not make the machine branch symmetrical by promoting `unchanged` to a status. V-01's byte-identity probe against a pre-change capture is the check.

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. It does not unify the dry-run and apply predicates (F-06); a residual duplication remains and V-01 requires it to be counted and reported. It does not check any other verb's `--dry-run`. It does not touch `aw find`, which `zyj8io` owns, and does not touch `aw runs`, which is Order 01 of this Set. It also does not fix the zero-match loop's bail on the first unmatched token, which is noted in Deferred as an observation and must not be claimed as fixed. The true claim is that `aw set`'s machine dry run now reports each matched artifact's real disposition and a correct would-change count, agreeing with its own apply path.

THIS PLAN AND ORDER 01 ARE INDEPENDENT. `9jkek2` declares `run_viewer.py` and its test file; this plan declares `status_set.py` and its test file. They share no path and no symbol, neither depends on the other, and both carry `- Item-Dependencies: none` (F-12), so either may execute first.

This plan carries `- Work-Kind: followup` and `- Priority: low`, inherited from backlog item `om3rzi`, which carries NO `- Blocks-Release:` gate. Do not invent one. Backlog item `om3rzi` is set to `graduated` by the runner on verification; do not set it `done` and do not close it here.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted, concrete evidence. Make the transition through the tooled lifecycle (`aw ipd begin` / `aw ipd finalize`), never by a hand edit or a hand `git mv`. In a managed lane the RUNNER owns the transition and `aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001`; if that happens, record the refusal, leave the plan in `pending/` with its evidence, and let the runner finalize.
