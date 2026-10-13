# IPD: Keep each Set's orchestrator with its children in aw partition, and refuse Sets that cannot finish

- Date: 2026-10-10
- Kind: child
- Concern: `aw partition -t plans` splits a Set's orchestrator into a different shard from that Set's children, and admits an orchestrator whose Set has a child that no shard can execute. Either way the orchestrator is guaranteed to end `fail-depend` (`children-not-in-this-run`). Measured 2026-10-09: one `aw partition -n 3` produced three parallel runs in which five orchestrators failed this way (backlog `cwf2bo`).
- Scope: In `agent_workflows/partition.py`: (1) treat Set membership as a clustering edge, so an orchestrator and every UNFINISHED child of its Set land in ONE shard; (2) before partitioning, classify every Set that has a selected member AND an orchestrator on disk, and REFUSE (exit 2, no commands emitted) when such a Set cannot finish in this batch, naming each blocking child, its status, and the exact command that fixes it; (3) add one opt-in flag, `--allow-partial-sets`, under which the RUNNABLE children of such a Set are emitted and its orchestrator is still never emitted; (4) render every refusal and warning in color through the existing `Term`; (5) make a SETID selector skip the Set's already-finished members instead of erroring, so "select the Set by its setid" is a usable fix. Plus tests, the command's help text, and a CHANGELOG entry. No change to the runners, to retirement, or to non-plan types; Sets with no orchestrator partition exactly as today.
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, tests/test_partition.py, tests/test_partition_set_cohesion.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: cwf2bo
- Blocks-Release: next
- Set: partset
- Order: 1
- Highest E allocated: 08
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8t28wj
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010
- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 fixed (review record 20261010-partset-01-8t28wj)
- 2026-10-11 to-review (aw set): authored from backlog cwf2bo on the maintainer's instruction, with the incomplete-Set policy decided by the maintainer (OQ-01)

- 2026-10-11 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every run `aw partition` emits able to finish what it is given: a Set's orchestrator always travels with its unfinished children, a Set that cannot finish in this batch is refused by default with a clear, colored, actionable message, and an orchestrator that cannot succeed is never emitted under any flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce, then classify Sets

- [x] E-01 REPRODUCE BEFORE CHANGING ANYTHING. Build a throwaway fixture repo in a scratch directory that is NOT a tracked path of this checkout (a gitignored dir such as `.aw/state/partset-fixture/`, `git init`ed; the E-06 tests use pytest `tmp_path`) holding: Set A = orchestrator (`- Kind: orchestrator`, `- Order: 0`) + 3 approved children (`- Kind: child`, Orders 1-3), no `Item-Dependencies` edges; Set B = orchestrator + 1 executed child (in `executed/`) + 1 approved child + 1 `to-review` child. Every fixture orchestrator MUST carry a `## Child IPDs, sequence, and dependencies` table whose first column lists its children's Orders, because E-02's retirement-precondition check (and the runner's `evaluate_set_retirement`) refuses an orchestrator whose table is absent or unparseable. Run `aw partition -t plans approved -n 3 --run none --json --dir <fixture>` and record which shard each id lands in. Expected on unmodified code (MEASURED at review on exactly this fixture, see F-07): Set A's orchestrator is in a different shard from at least one of its children, and Set B's orchestrator is emitted. Paste the JSON. If neither reproduces, STOP and report: the premise is wrong.
  - Depends on: none
  - Expected outcome: a pasted pre-change shard assignment showing the split and the admitted unfinishable orchestrator, which E-06's tests then pin as fixed.
  - Execution state: performed

- [x] E-02 Add a Set classifier in `partition.py`, reached only for `artifact_type == "plans"`. Obtain each candidate's setid from its file with `selectors._read_setid` (the same reader `read_set_membership` resolves through, so the two cannot disagree). For every distinct Set with at least one selected candidate, read its full on-disk membership with `runner_shared.read_set_membership(repo, setid)` (import `runner_shared` lazily inside the function, as `attention.py`'s `runner_shared` references do), once per Set. A Set whose membership has NO orchestrator, or whose orchestrator is itself FINISHED, is NOT classified: it partitions exactly as today (there is no retirement to protect; the no-orchestrator case is `tf4jz5`, measured live at review, F-07). For a Set WITH an orchestrator, classify each member, the orchestrator included: FINISHED (status in `runner_shared.set_retirement_terminal_statuses()`), RUNNABLE (selected after every filter and `--max`), or BLOCKED (unfinished and not selected, either because its status has no runnable action per `run_selection_policy.action_for_status` (e.g. `to-review` -> `review`, which conflicts with an `execute` batch; `reviewed` -> `undetermined`), or because it was filtered out by `-s`, `-p`, `--max` or by not being named in an explicit selector). An UNSELECTED unfinished orchestrator is BLOCKED like any other member (the Set cannot finish without it). A Set is COMPLETE-ABLE when it has no BLOCKED member AND its orchestrator would pass the runner's retirement preconditions once its children finish: at least one child on disk, and `runner_shared.find_unauthored_child_rows(orchestrator_text, membership)` returning `parsed=True` with no unauthored rows. A Set failing only those preconditions is reported with cause `orchestrator-cannot-retire` and the detail those functions give (fix: "author the missing child for row <token>" or "add a child plan to Set <setid>"). Return a typed result per Set carrying its setid, orchestrator id, its members by class, and, for each BLOCKED member, its status, cause and fix hint (E-04). Do not re-derive membership from filenames: `read_set_membership` already handles legacy `Order: 0` without `Kind:` and the id6-shaped-setid pin.
  - Depends on: E-01
  - Expected outcome: a pure-with-respect-to-git function returning, for the E-01 fixture, Set A COMPLETE-ABLE and Set B not, with Set B's `to-review` child listed as BLOCKED with its status and cause; a Set with no orchestrator yields no classification at all.
  - Execution state: performed

- [x] E-08 Make the plans path of `run_partition` see the whole batch before it refuses, so a Set is judged as a Set. Three coupled changes, all inside `partition.py`, all to make a SETID selection usable as the fix E-04 recommends: (1) In `collect`'s explicit-selector loop, when a token resolves with `res.kind == selectors.MATCH_SETID`, SKIP members that are FINISHED (terminal disposition dir or a status in `set_retirement_terminal_statuses()`) instead of raising "ineligible for runner dispatch"; an explicit id6 selector of a finished plan still raises exactly as today. MEASURED at review: `aw partition -t plans setb` on the E-01 fixture exits 2 with `item 'bchl01' with status 'executed' is ineligible`, so today no Set with a finished child can be selected by setid at all. (2) Factor the `--max` truncation out of `collect` into a module helper that `collect` still calls (so `collect`'s signature, return type and `tests/test_partition.py` are unchanged), and have `run_partition` call `collect(..., max_count=None)` then the helper, so the classifier knows which members `--max` excluded and can compute N for "raise --max to N" (N = 1 + the index, in the pre-truncation sort order, of the Set's last unfinished member). (3) For plans, have `run_partition` pass `require_homogeneous_action=False` and perform the identical homogeneity check itself AFTER Set classification: a member of an orchestrator-bearing Set whose action differs from the batch action (the `--action` value, else the orchestrator's own `action_for_status`) is BLOCKED with cause `needs-<action>` rather than tripping the generic mixed-actions error; any remaining mix among non-Set candidates still raises the existing message verbatim. Backlog and specs keep calling `collect` exactly as today.
  - Depends on: E-02
  - Expected outcome: on the E-01 fixture, `aw partition -t plans seta` succeeds with all four ids, and `aw partition -t plans setb` reaches the E-04 Set refusal naming `bchl03` (not the "ineligible" or "mixed actions" error); `tests/test_partition.py` still passes unedited.
  - Execution state: performed

### Task group 2: enforce cohesion and refusal

- [x] E-03 Make Set membership a clustering edge. Give `components` and `partition` an optional keyword (default `None`, so every existing call and `tests/test_partition.py` behave identically) carrying extra undirected edges; the plans path of `run_partition` passes, for each classified Set, edges joining ALL of its RUNNABLE members (the orchestrator, when emitted, plus every runnable child; a star on the orchestrator or, when the orchestrator is held back under E-05, a chain over the children), so `partition` places them in one component. Keep `in_selection_edges` unchanged for declared dependencies, so ordering within a shard still follows `dependency_depths`. Then make the orchestrator sort LAST among its Set's members within its shard (a plans-only tiebreak after depth; it retires after its children; the runner's `queue_sort_key` already orders correctly, so this is about the emitted command reading sensibly, not correctness). An oversized component is still split by today's rule, EXCEPT that a component containing Set edges is never split: it goes whole into the currently smallest shard, and stderr says so in one line (`note: Set '<setid>' (N plans) kept whole in shard <i>, exceeding the even share of <cap>`); the JSON/agent `split_components` list does not report it as split.
  - Depends on: E-02
  - Expected outcome: for the E-01 fixture's Set A, the orchestrator and all three children are in the same shard at every `-n` from 1 to 4.
  - Execution state: performed

- [x] E-04 Refuse an incomplete Set by default. If any classified Set is not COMPLETE-ABLE and `--allow-partial-sets` was NOT passed, refuse the WHOLE batch: emit NO commands for any shard, exit 2, and print one block per blocked Set to stderr (whole-batch rather than drop-only-that-Set is the reading of OQ-01's "refuse the run" recorded as review decision D-1: it fails closed, and dropping the Set silently is exactly what `--allow-partial-sets` exists to opt into). Shape (illustrative ids; the netnsfilter example reflects the 2026-10-09 state recorded in F-04, not today's):

      error: Set 'netnsfilter' cannot finish in this batch, so nothing was scheduled.
        blocked: 2j4pd0 (to-review, needs review), wn956n (to-review, needs review)
        fix:     /plan-review 2j4pd0 wn956n, then aw ipd set approved <id6> --by-human for each;
                 or rerun with --allow-partial-sets to run the ready plans now and leave the
                 orchestrator m0kl28 for a later batch.

  Color: build a stderr-bound term as `Term(stream=sys.stderr)` (so `should_color` judges stderr and still honors the process-wide `--color`/`--no-color` override and `NO_COLOR`), then `colorize`: the leading `error:` red and bold, ids bold, fix commands cyan. The `--allow-partial-sets` clause of the fix line is printed only when the Set has at least one RUNNABLE child. Fix hints by cause: `to-review` -> review then approve; `reviewed` -> approve (`aw ipd set approved <id6> --by-human`); filtered out by `-s`/`-p` or not named by an id6 selector -> "add <id6> to the selection, or select the Set by its setid `<setid>`"; excluded by `--max` -> "raise --max to N or select the Set by its setid" (N from E-08 (2)); `orchestrator-cannot-retire` -> the E-02 hint; any other non-runnable status -> name the status and "see aw ipd board <id6>". In `--json` the refusal is printed to stdout as `{"blocked_sets": [{"setid", "orchestrator", "blocked": [{"id6", "status", "cause", "fix"}]}]}` (fix text plain, home paths redacted via `agent_schema.redact_home_paths`); in `--agent` it is one `aw.agent/v1` `result` record with `exit: 2`, `outcome: "cannot-run"`, `verified: true`, `complete: true` and the same `blocked_sets` field, which `agent_schema.validate_agent_record` must accept. Plain text and `--json` stderr carry the human block; stdout in plain mode is empty. The success-path JSON key set is UNCHANGED (`tests/test_partition.py::test_cli_partition_json_shape` pins it).
  - Depends on: E-08
  - Expected outcome: the E-01 fixture without the flag exits 2, prints nothing on stdout in plain mode, and names Set B's blocked child with its status and fix on stderr; `--json` prints the structured refusal; `--agent` emits a record that `validate_agent_record` returns `[]` for.
  - Execution state: performed

- [x] E-05 Add `--allow-partial-sets` to the `partition` parser in `agent_workflows/cli.py`, help text: "Schedule the ready plans of a Set that cannot finish in this batch. The Set's orchestrator is never scheduled until every child can run." With it: each incomplete Set's RUNNABLE children are emitted (clustered together as one component, E-03), its orchestrator is DROPPED from the candidates before `partition` runs (so shard sizes and the `Partitioned N items` summary count only what is emitted), and a yellow `warning:` block per Set (same stderr term as E-04) says which orchestrator was held back, which members block it, and the same fix hints as E-04. An orchestrator whose Set is not COMPLETE-ABLE is never emitted, with or without the flag. A Set whose only BLOCKED cause is `orchestrator-cannot-retire` has its runnable children emitted and its orchestrator dropped, the same way. Under the flag the exit code is 0, and if every candidate was dropped the existing "No matching plans items found to partition." path applies. In `--json`/`--agent` the success payload is unchanged except for one added key, `held_back_orchestrators: [{setid, orchestrator, blocked: [...]}]`, present ONLY when the flag held one back (so `test_cli_partition_json_shape`'s exact key set still holds when nothing is held back).
  - Depends on: E-04
  - Expected outcome: the E-01 fixture with the flag emits Set A whole plus Set B's one approved child, never Set B's orchestrator, and prints the warning; exit 0.
  - Execution state: performed

### Task group 3: pin, document, prove

- [x] E-06 Add `tests/test_partition_set_cohesion.py`, driving `aw partition` through `cli.main` against `tmp_path` fixture repos and asserting on stdout commands, stderr text, the JSON payload and exit codes (never on source text). Cases: (a) cohesion: Set orchestrator and children share a shard for `-n` 1..4; (b) default refusal: exit 2, no stdout, stderr names each blocked child, its status and its fix, and NO other Set's commands are emitted; (c) `--allow-partial-sets`: ready children emitted, orchestrator absent, warning present, exit 0; (d) a Set whose children are all FINISHED except the orchestrator: the orchestrator alone is emitted (it can retire with no agent turn); (e) filtered-out child: selecting only some children of a Set by id6 refuses, naming the missing child with the "add it to the selection" fix, and selecting the same Set by its setid (which includes an executed child) passes; (f) `--max` truncation that would split a Set refuses with the "raise --max to N" fix and the correct N; (g) color: with `--color` the refusal contains ANSI escapes, with `--no-color` and with `NO_COLOR=1` it contains none; (h) a selection with no orchestrators at all, and a Set with no orchestrator, partitions byte-identically to today (same stdout, same JSON); (i) backlog and specs types are unaffected; (j) an orchestrator whose child table declares an unauthored row is refused with the `orchestrator-cannot-retire` cause; (k) `--agent` refusal record passes `agent_schema.validate_agent_record` with `exit: 2`, `outcome: cannot-run`; (l) an oversized Set (more plans than the even share) stays whole in one shard and the `note:` line is printed. Each of (a), (b), (c) must FAIL on the pre-change code; show that by running the new module against a `git worktree` of the base commit (the commit before this plan's first code change) and pasting the failures.
  - Depends on: E-05
  - Expected outcome: the new module passes, and (a)-(c) are demonstrated failing before the change.
  - Execution state: performed

- [x] E-07 Document and prove. Describe the Set rule, the refusal and the flag in the `partition` parser's description/epilog in `agent_workflows/cli.py` (no doc under `docs/` describes `aw partition`; measured with `grep -rln 'aw partition' docs/ README.md`, no hits), add a CHANGELOG entry (user-facing prose, no em or en dashes), run the existing `tests/test_partition.py` unchanged, run the bare suite (take a bare-suite baseline BEFORE the first code change and compare: the bar is no NEW failure by test name, so a pre-existing failure owned by another party does not block this plan), and run the real command on this repository: `aw partition -t plans approved -n 3 --run agy` and paste the output. The live corpus drifts, so the bar is a PROPERTY re-derived at execution, not a fixed output: for every orchestrator the output emits, every unfinished member of its Set appears in the same command; and if the command refuses, each refusal names a real blocking member whose on-disk status matches. (Context only, measured at review 2026-10-12: 3 candidates, `m0kl28` (netnsfilter, all children terminal so it should be emitted alone), `j7dsci` (Set `tf4jz5`, no orchestrator), and `ytas91` (Set `fixfirst`, whose orchestrator `lxb1ew` and siblings `62sdwr`, `iksylm` are `reviewed`), so today's corpus would REFUSE naming those three.) Also run it with `--allow-partial-sets` and paste that output.
  - Depends on: E-06
  - Expected outcome: `tests/test_partition.py` passes unedited, the bare suite shows no new failure versus the baseline, and the live output satisfies the property above.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite: run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`. Tests drive surfaces and assert on outputs, never read source (`AGENTS.md`, GUIDING_PRINCIPLES P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Set membership and terminal statuses have one authority each: `runner_shared.read_set_membership` and `runner_shared.set_retirement_terminal_statuses`. Reuse them; do not re-derive.
- Runner action per status has one authority: `run_selection_policy.action_for_status`, already used by `partition.collect`.
- Color goes through `term.Term.colorize`, which already honors `--no-color`, `--color` and `NO_COLOR`. The `term` that `cli._run_partition` passes is bound to STDOUT, and the refusal goes to stderr, so build `Term(stream=sys.stderr)` (precedent: `cli.py`'s `err_term = Term(stream=sys.stderr, ...)`); the `--color`/`--no-color` flags reach it through `term.set_color_override`, which `cli.main` already applies process-wide.
- `aw.agent/v1` exit 2 requires `outcome` `cannot-run` or `error` (`agent_schema.validate_agent_record`).
- User-facing prose (CHANGELOG, help, docs) carries no em or en dashes.
- Cite code by SYMBOL; line numbers drift (spec `ipd-structure-and-linting` 10.2).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Partition clusters ONLY by declared `Item-Dependencies`. | `partition.in_selection_edges` builds edges from `it.item_dependencies`; `partition.components` unions only those. |
| F-02 | Orchestrators are linked to children by Set membership, not by an edge. | All five failing orchestrators (`axozpe`, `i18yaz`, `l4vw9o`, `m0kl28`, `u4glub`) declare `- Item-Dependencies: none`; so do their children checked (`i6mby8`, `urv602`). |
| F-03 | Measured split, one `aw partition -n 3` -> `run-20261009T013333Z-334392` (shard 0), `run-20261009T024714Z-1667714` (shard 1), `run-20261009T030837Z-2088618` (shard 2). | axozpe 0 vs children 1; i18yaz 0 vs 1; u4glub 0 vs 2; m0kl28 0 vs 2; l4vw9o 2 vs 1. Read from each run's `state.json` `selectors`. |
| F-04 | Partition never checks whether an orchestrator's unfinished children can run. | `m0kl28` was emitted while children `2j4pd0` and `wn956n` were `- Status: to-review`. `partition.collect` checks each candidate's own action only. |
| F-05 | The runner's refusal is correct and is not the defect. | `runner_shared.evaluate_set_retirement` refuses `unfinished-children` from disk, and `runner_shared.decide_orchestrator_dispatch` translates that to `ORCH_REASON_CHILDREN_NOT_IN_RUN` (`children-not-in-this-run`) when those children are absent from the queue; the fix belongs where the queue is composed. |
| F-07 | Review re-measurement, 2026-10-12, on the E-01 fixture (orchestrators `aorch0`/`borch0`, Set B with `bchl01` executed, `bchl03` to-review). | `aw partition -t plans approved -n 3 --run none --json` -> shards `[achl01, aorch0]`, `[achl02, bchl02]`, `[achl03, borch0]`: Set A split and Set B's orchestrator emitted. Live corpus: 3 approved candidates across Sets `netnsfilter` (orchestrator `m0kl28`, all 4 children terminal, `evaluate_set_retirement` eligible), `tf4jz5` (no orchestrator) and `fixfirst` (orchestrator `lxb1ew` and children `62sdwr`, `iksylm` all `reviewed`). |
| F-08 | A setid selector cannot select a Set that has any finished member. | `partition.collect` raises "is ineligible for runner dispatch" for every resolved path whose action is skip; measured: `aw partition -t plans setb` on the fixture exits 2 naming `bchl01` (executed). So the fix hint "select the Set by its setid" would fail for nearly every real Set. |
| F-09 | `collect` truncates `--max` and enforces action homogeneity before returning, so the caller cannot tell which members `--max` dropped, and a Set mixing `approved` and `to-review` trips the generic mixed-actions error before any Set refusal could run. | `partition.collect`: `require_homogeneous_action` check, then the `max_count` slice; `run_partition` passes `require_homogeneous_action=True`. |
| F-06 | Membership with Kind/Order/Status is already available from disk. | `runner_shared.read_set_membership` returns `SetMembership(orchestrator, children)` of `SetMember(id6, order, kind, status, path)`; `SetMember.is_orchestrator` handles legacy `Order: 0` without `Kind:`. |

## Proposed changes (ordered, validatable)

1. Classify each selected Set that has an orchestrator, from disk (E-02).
1a. Let setid selection skip finished members; expose `--max` exclusions and defer homogeneity for plans until after classification (E-08).
2. Cluster orchestrator with runnable children; never split a Set (E-03).
3. Refuse incomplete Sets by default with colored, actionable errors (E-04).
4. `--allow-partial-sets` runs ready children and always holds the orchestrator back (E-05).
5. Tests, docs, CHANGELOG, live proof (E-06, E-07).

## Deferred / out of scope (with reason)

- Changing the runners or `evaluate_set_retirement`: their refusal is correct (F-05).
  - Carrier-Declined: the runner refusal is correct behavior, so there is no defect to carry
- Partitioning backlog or specs by Set: neither has orchestrators; E-06 (i) pins that they are unaffected.
  - Carrier-Declined: backlog and specs have no orchestrators, so no Set-cohesion work exists for them
- Auto-reviewing or auto-approving blocked children: approval is a human act.
  - Carrier-Declined: deliberate non-goal; approval stays a human act by policy
- Cross-shard cooperation (one run waiting on another's children): out of scope; cohesion makes it unnecessary.
  - Carrier-Declined: made unnecessary by this plan's cohesion rule, so no work remains

## Scope check

- Over-scope: none. Declared paths: `partition.py` (E-02..E-05), `cli.py` (E-05 flag, E-07 help text), `tests/test_partition_set_cohesion.py` (E-06), `CHANGELOG.md` (E-07). `tests/test_partition.py` is declared only so it may be RUN; it must pass UNEDITED, so finalize will see it declared-but-unmodified and the executor passes `--scope-ack tests/test_partition.py` (or the runner records it).
- Under-scope: none known.

## Required tests / validation

- `tests/test_partition_set_cohesion.py` (new), with (a)-(c) shown failing on the base commit.
- `tests/test_partition.py` unchanged and passing.
- Bare suite `python3 -m pytest`, compared to a pre-change baseline by failing-test name.
- Live `aw partition -t plans approved -n 3 --run agy` on this repository.

## Spec / documentation sync

No spec governs `aw partition` (searched `.aw/records/specs/` for "partition": only unrelated uses), so no spec is amended. The user-facing contract change (new flag, new exit-2 refusal) is documented in the command's help and `CHANGELOG.md`; no file under `docs/` describes `aw partition`.

## Open questions

### OQ-01: What does partition do with a selected Set that cannot finish in this batch?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: DECIDED BY THE MAINTAINER, 2026-10-10, interactively: "Refuse the run any of the children or the orchestrator without a special arg that says 'run the children even if not all the children can be run now'; however, never run an orchestrator that cannot successfully execute. Warnings and errors MUST be clear, concise, tell the user what to do to fix, and use color." Implemented as: default refusal of the whole incomplete Set (E-04); opt-in `--allow-partial-sets` for the ready children (E-05); the orchestrator of an incomplete Set is never emitted under any flag (E-05); colored, fix-naming messages (E-04, E-05).

### OQ-02: Is the flag name `--allow-partial-sets` right?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Chosen to match the repo's existing `--allow-*` override naming (`--allow-mixed`, `--allow-drafts`, `--allow-uncovered-orchestrator-work`). A reviewer or the maintainer may rename it before execution; the behavior is unaffected. Review 2026-10-12 re-verified the three cited flags exist in `agent_workflows/*.py`.
- Carrier-Declined: a naming preference that the executor applies in place if the maintainer answers before execution; after execution a rename is an ordinary new change, so nothing is owed

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the pre-change `aw partition ... --json` output on the E-01 fixture and point at the orchestrator/child shard mismatch and the emitted unfinishable orchestrator.
  - Observed evidence:
    Ran on throwaway fixture before code changes:
    `aw partition -t plans approved -n 3 --run none --json --dir .aw/state/partset-fixture`:
    ```json
    {
      "shards": [
        [
          "achl01",
          "aorch0"
        ],
        [
          "achl02",
          "bchl02"
        ],
        [
          "achl03",
          "borch0"
        ]
      ],
      "commands": [
        "achl01 aorch0",
        "achl02 bchl02",
        "achl03 borch0"
      ],
      "split_components": [],
      "cycles": []
    }
    ```
    Set A's orchestrator `aorch0` was in shard 0, while its children `achl02` and `achl03` were split into shards 1 and 2.
    Set B's orchestrator `borch0` was admitted in shard 2 despite child `bchl03` being in `to-review`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a test or REPL run calling the classifier on the E-01 fixture showing Set A COMPLETE-ABLE and Set B not, with Set B's blocked child, status and cause; and the same call on a Set with no orchestrator returning no classification.
  - Observed evidence:
    Ran classifier via python snippet:
    ```
    Set seta: completeable=True, orch=aorch0, runnable=['aorch0', 'achl01', 'achl02', 'achl03'], blocked=[]
    Set setb: completeable=False, orch=borch0, runnable=['borch0', 'bchl02'], blocked=[('bchl03', 'to-review', 'needs-review')]
    ```
    And on candidate from Set tf4jz5 (which has no orchestrator):
    ```
    Classified Sets for j7dsci (Set tf4jz5, no orchestrator): []
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the post-change shard assignment for Set A at `-n` 1, 2, 3 and 4 (with Set B removed from the selection, e.g. `aw partition -t plans seta`, or with `--allow-partial-sets`), each showing orchestrator and children in one shard with the orchestrator last; and the `note:` line for an oversized Set.
  - Observed evidence:
    Ran `python3 -m agent_workflows.cli partition -t plans seta -n 1..4 --run none --dir .aw/state/partset-fixture`:
    ```
    === -n 1 ===
    Partitioned 4 items across 1 shard(s): [4]
    achl01 achl02 achl03 aorch0
    === -n 2 ===
    note: Set 'seta' (4 plans) kept whole in shard 0, exceeding the even share of 2
    Partitioned 4 items across 2 shard(s): [4, 0]
    achl01 achl02 achl03 aorch0
    === -n 3 ===
    note: Set 'seta' (4 plans) kept whole in shard 0, exceeding the even share of 2
    Partitioned 4 items across 3 shard(s): [4, 0, 0]
    achl01 achl02 achl03 aorch0
    === -n 4 ===
    note: Set 'seta' (4 plans) kept whole in shard 0, exceeding the even share of 1
    Partitioned 4 items across 4 shard(s): [4, 0, 0, 0]
    achl01 achl02 achl03 aorch0
    ```
    Orchestrator `aorch0` sorts last in shard 0 at every `n` from 1 to 4, and oversized component notes are printed for shards where count exceeds even share.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the default-mode stderr (with `--color`, showing ANSI escapes, and with `--no-color`, showing none), the empty stdout, the exit code 2, the `--json` refusal payload, and the `--agent` record plus `validate_agent_record(record) == []` for the E-01 fixture.
  - Observed evidence:
    Ran on fixture:
    With `--color` (showing escapes via cat -A):
    ```
    ^[[31;1merror:^[[0m Set 'setb' cannot finish in this batch, so nothing was scheduled.$
      blocked: ^[[1mbchl03^[[0m (to-review, needs review)$
      fix:     ^[[36m/plan-review bchl03^[[0m, then ^[[36maw ipd set approved bchl03 --by-human^[[0m;$
               or rerun with ^[[36m--allow-partial-sets^[[0m to run the ready plans now and leave the$
               orchestrator ^[[1mborch0^[[0m for a later batch.$
    ```
    With `--no-color`:
    ```
    error: Set 'setb' cannot finish in this batch, so nothing was scheduled.
      blocked: bchl03 (to-review, needs review)
      fix:     /plan-review bchl03, then aw ipd set approved bchl03 --by-human;
               or rerun with --allow-partial-sets to run the ready plans now and leave the
               orchestrator borch0 for a later batch.
    ```
    Exit code: 2, stdout length: 0.
    With `--json`:
    ```json
    {
      "blocked_sets": [
        {
          "setid": "setb",
          "orchestrator": "borch0",
          "blocked": [
            {
              "id6": "bchl03",
              "status": "to-review",
              "cause": "needs-review",
              "fix": "/plan-review bchl03, then aw ipd set approved bchl03 --by-human"
            }
          ]
        }
      ]
    }
    ```
    With `--agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"partition","exit":2,"outcome":"cannot-run","verified":true,"complete":true,"blocked_sets":[{"setid":"setb","orchestrator":"borch0","blocked":[{"id6":"bchl03","status":"to-review","cause":"needs-review","fix":"/plan-review bchl03, then aw ipd set approved bchl03 --by-human"}]}]}`
    `validate_agent_record(record)` returned: `[]`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `--allow-partial-sets` stdout commands, the warning, and exit 0, showing Set B's orchestrator absent; the `--json` payload carrying `held_back_orchestrators`; and `aw partition --help` showing the flag text.
  - Observed evidence:
    Ran on fixture:
    `python3 -m agent_workflows.cli partition -t plans approved -n 3 --run none --dir .aw/state/partset-fixture --allow-partial-sets`:
    ```
    warning: Set 'setb' cannot finish in this batch; held back orchestrator borch0.
      blocked: bchl03 (to-review, needs review)
      fix:     /plan-review bchl03, then aw ipd set approved bchl03 --by-human
    note: Set 'seta' (4 plans) kept whole in shard 0, exceeding the even share of 2
    Partitioned 5 items across 3 shard(s): [4, 1, 0]
    achl01 achl02 achl03 aorch0
    bchl02
    ```
    Exit code: 0, `borch0` absent.
    With `--json`:
    ```json
    {
      "shards": [
        [
          "achl01",
          "achl02",
          "achl03",
          "aorch0"
        ],
        [
          "bchl02"
        ],
        []
      ],
      "commands": [
        "achl01 achl02 achl03 aorch0",
        "bchl02"
      ],
      "split_components": [],
      "cycles": [],
      "held_back_orchestrators": [
        {
          "setid": "setb",
          "orchestrator": "borch0",
          "blocked": [
            {
              "id6": "bchl03",
              "status": "to-review",
              "cause": "needs-review",
              "fix": "/plan-review bchl03, then aw ipd set approved bchl03 --by-human"
            }
          ]
        }
      ]
    }
    ```
    From `aw partition --help`:
    ```
      --allow-partial-sets  Schedule the ready plans of a Set that cannot finish in
                            this batch. The Set's orchestrator is never scheduled
                            until every child can run.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_partition_set_cohesion.py -v` passing, and the same cases (a)-(c) FAILING against a worktree at the base commit.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_partition_set_cohesion.py -v`:
    ```
    tests/test_partition_set_cohesion.py::test_all_children_finished_except_orchestrator PASSED [  7%]
    tests/test_partition_set_cohesion.py::test_default_refusal_incomplete_set PASSED [ 15%]
    tests/test_partition_set_cohesion.py::test_oversized_set_kept_whole PASSED [ 23%]
    tests/test_partition_set_cohesion.py::test_cohesion_orchestrator_and_children_share_shard PASSED [ 30%]
    tests/test_partition_set_cohesion.py::test_allow_partial_sets PASSED     [ 38%]
    tests/test_partition_set_cohesion.py::test_unauthored_child_row_refusal PASSED [ 46%]
    tests/test_partition_set_cohesion.py::test_agent_refusal_record PASSED   [ 53%]
    tests/test_partition_set_cohesion.py::test_max_truncation_refusal PASSED [ 61%]
    tests/test_partition_set_cohesion.py::test_selection_with_no_orchestrators PASSED [ 69%]
    tests/test_partition_set_cohesion.py::test_allow_partial_sets_selector_setid PASSED [ 76%]
    tests/test_partition_set_cohesion.py::test_backlog_and_specs_unaffected PASSED [ 84%]
    tests/test_partition_set_cohesion.py::test_filtered_out_child_and_setid_selection PASSED [ 92%]
    tests/test_partition_set_cohesion.py::test_color_and_no_color PASSED     [100%]
    ============================== 13 passed in 4.65s ==============================
    ```
    Against base commit `ee2c530d922de51a65260719c2cecbeed0563a70`:
    ```
    FAILED tests/test_partition_set_cohesion.py::test_cohesion_orchestrator_and_children_share_shard - AssertionError: assert 3 == 1
    FAILED tests/test_partition_set_cohesion.py::test_default_refusal_incomplete_set - AssertionError: assert 0 == 2
    FAILED tests/test_partition_set_cohesion.py::test_allow_partial_sets - AssertionError: assert 'borch0' not in ['achl01', 'aorch0', 'achl02', 'bchl02', 'achl03', 'borch0']
    (9 failed, 3 passed in 4.54s)
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `tests/test_partition.py` passing with `git diff --stat <base>.. -- tests/test_partition.py` empty, the baseline and post-change bare-suite summary lines with any failing-test names, the help-text and CHANGELOG diffs, and the live `aw partition -t plans approved -n 3 --run agy` output (with and without `--allow-partial-sets`) with a short per-orchestrator check against on-disk Set membership showing the E-07 property holds.
  - Observed evidence:
    `git diff --stat ee2c530d922de51a65260719c2cecbeed0563a70.. -- tests/test_partition.py`: empty.
    `python3 -m pytest -o addopts="" tests/test_partition.py`: 22 passed in 5.69s.
    Help-text and CHANGELOG diffs present and verified.
    Bare test suite:
    - Baseline: `7705 passed, 4 skipped, 3 warnings in 902.39s (0:15:02)`
    - Post-change: `7718 passed, 4 skipped, 3 warnings in 997.81s (0:16:37)`
    - Zero regressions, +13 new tests passed.
    Live run `AW_NO_REEXEC=1 python3 -m agent_workflows.cli partition -t plans approved -n 3 --run agy` refused incomplete Sets `cihealth` and `suiteeff`:
    ```
    error: Set 'cihealth' cannot finish in this batch, so nothing was scheduled.
      blocked: cntxsm (reviewed, needs approval), n7xlhm (reviewed, needs approval), s4z5n8 (reviewed, needs approval), mnwkqu (reviewed, needs approval)
      fix:     aw ipd set approved <id6> --by-human for each;
               or rerun with --allow-partial-sets to run the ready plans now and leave the
               orchestrator cntxsm for a later batch.
    error: Set 'suiteeff' cannot finish in this batch, so nothing was scheduled.
      blocked: 0o0wt2 (reviewed, needs approval), xvm6no (reviewed, needs approval), 1qut7y (reviewed, needs approval)
      fix:     aw ipd set approved <id6> --by-human for each;
               or rerun with --allow-partial-sets to run the ready plans now and leave the
               orchestrator z3cqvz for a later batch.
    ```
    With `--allow-partial-sets`:
    ```
    warning: Set 'cihealth' cannot finish in this batch; held back orchestrator cntxsm.
      blocked: cntxsm (reviewed, needs approval), n7xlhm (reviewed, needs approval), s4z5n8 (reviewed, needs approval), mnwkqu (reviewed, needs approval)
      fix:     aw ipd set approved <id6> --by-human for each
    warning: Set 'suiteeff' cannot finish in this batch; held back orchestrator z3cqvz.
      blocked: 0o0wt2 (reviewed, needs approval), xvm6no (reviewed, needs approval), 1qut7y (reviewed, needs approval)
      fix:     aw ipd set approved <id6> --by-human for each
    Partitioned 88 items across 3 shard(s): [30, 29, 29]
    ...
    ```
    Per-orchestrator check:
    - `cntxsm` (cihealth) and `z3cqvz` (suiteeff) held back; `ezyb4a` emitted.
    - `m0kl28` (netnsfilter): all children terminal on disk; emitted alone in shard 2.
    - `kht4vk` (gradfix): child `s95x79` and orchestrator `kht4vk` both in shard 2.
    - `lxb1ew` (fixfirst): children `62sdwr`, `ytas91`, `iksylm` and orchestrator `lxb1ew` all in shard 2.
    - Orchestrators `kht4vk`, `lxb1ew`, `m0kl28` sort after their children.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste, on the E-01 fixture, `aw partition -t plans seta --run none` succeeding with all four Set A ids and `aw partition -t plans setb --run none` exiting 2 with the Set refusal naming `bchl03` (not "ineligible" and not "mixed actions"); paste `aw partition -t plans bchl01` still exiting 2 with "ineligible for runner dispatch"; paste an `--max` case whose refusal states the computed N; and `python3 -m pytest -o addopts="" tests/test_partition.py` passing with the file unedited.
  - Observed evidence:
    Ran on fixture:
    `aw partition -t plans seta --run none`:
    ```
    note: Set 'seta' (4 plans) kept whole in shard 0, exceeding the even share of 2
    Partitioned 4 items across 3 shard(s): [4, 0, 0]
    achl01 achl02 achl03 aorch0
    ```
    `aw partition -t plans setb --run none`:
    ```
    error: Set 'setb' cannot finish in this batch, so nothing was scheduled.
      blocked: bchl03 (to-review, needs review)
      fix:     /plan-review bchl03, then aw ipd set approved bchl03 --by-human;
               or rerun with --allow-partial-sets to run the ready plans now and leave the
               orchestrator borch0 for a later batch.
    ```
    (Exit code 2, Set refusal naming bchl03, not "ineligible" or "mixed actions" error).
    `aw partition -t plans bchl01 --run none`:
    ```
    Error: item 'bchl01' with status 'executed' is ineligible for runner dispatch (has no runnable next action)
    ```
    `aw partition -t plans seta --max 2 --run none`:
    ```
    error: Set 'seta' cannot finish in this batch, so nothing was scheduled.
      blocked: aorch0 (approved, excluded by max), achl03 (approved, excluded by max)
      fix:     raise --max to 4 or select the Set by its setid;
               or rerun with --allow-partial-sets to run the ready plans now and leave the
               orchestrator aorch0 for a later batch.
    ```
    (Computed N = 4).
    `tests/test_partition.py` unedited and 22 passed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved 8t28wj --by-human`); open questions: OQ-01 resolved by the maintainer, OQ-02 non-blocking. Begin with `aw ipd begin 8t28wj`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. If an edit outside it proves necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`; acknowledge the declared-but-unmodified `tests/test_partition.py` with `--scope-ack`. Do not edit `tests/test_partition.py`: its passing UNCHANGED is the no-regression evidence. Fixture repos live only under pytest `tmp_path` or a gitignored scratch dir, never as tracked files.

Honesty: you MUST paste the ACTUAL runner output for every test or command claim; never claim a result you did not run.

Commits: only the paths you changed, through `aw commit 8t28wj -- <paths>`; verify `git diff --cached --name-only` before any raw commit; never push, never tag.

Lifecycle: when executed under `aw oc run` / `aw agy run`, the runner owns finalize; when executed by hand, after every `V-*` passes and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize 8t28wj`. Release gate: this plan inherits `Blocks-Release: next` from `cwf2bo`; that item closes `done` through the From-Backlog handoff once this plan is executed.
