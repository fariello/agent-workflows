# IPD: Keep each Set's orchestrator with its children in aw partition, and refuse Sets that cannot finish

- Date: 2026-10-10
- Kind: child
- Concern: `aw partition -t plans` splits a Set's orchestrator into a different shard from that Set's children, and admits an orchestrator whose Set has a child that no shard can execute. Either way the orchestrator is guaranteed to end `fail-depend` (`children-not-in-this-run`). Measured 2026-10-09: one `aw partition -n 3` produced three parallel runs in which five orchestrators failed this way (backlog `cwf2bo`).
- Scope: In `agent_workflows/partition.py`: (1) treat Set membership as a clustering edge, so an orchestrator and every UNFINISHED child of its Set land in ONE shard; (2) before partitioning, classify every Set that has a selected member, and REFUSE (exit 2, no commands emitted) when a selected Set cannot finish in this batch, naming each blocking child, its status, and the exact command that fixes it; (3) add one opt-in flag, `--allow-partial-sets`, under which the RUNNABLE children of such a Set are emitted and its orchestrator is still never emitted; (4) render every refusal and warning in color through the existing `Term`. Plus tests, the command's help text, and a CHANGELOG entry. No change to the runners, to retirement, or to non-plan types.
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, tests/test_partition.py, tests/test_partition_set_cohesion.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: cwf2bo
- Blocks-Release: next
- Set: partset
- Order: 1
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8t28wj

## Workflow history
- 2026-10-11 to-review (aw set): authored from backlog cwf2bo on the maintainer's instruction, with the incomplete-Set policy decided by the maintainer (OQ-01)

- 2026-10-11 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every run `aw partition` emits able to finish what it is given: a Set's orchestrator always travels with its unfinished children, a Set that cannot finish in this batch is refused by default with a clear, colored, actionable message, and an orchestrator that cannot succeed is never emitted under any flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce, then classify Sets

- [ ] E-01 REPRODUCE BEFORE CHANGING ANYTHING. Build a throwaway fixture repo (tests use `tmp_path`, never this checkout) holding: Set A = orchestrator + 3 approved children, no `Item-Dependencies` edges; Set B = orchestrator + 1 executed child + 1 approved child + 1 `to-review` child. Run `aw partition -t plans approved -n 3 --run none --json` against it and record which shard each id lands in. Expected on unmodified code: Set A's orchestrator is in a different shard from at least one of its children, and Set B's orchestrator is emitted. Paste the JSON. If neither reproduces, STOP and report: the premise is wrong.
  - Depends on: none
  - Expected outcome: a pasted pre-change shard assignment showing the split and the admitted unfinishable orchestrator, which E-05's tests then pin as fixed.
  - Execution state: pending

- [ ] E-02 Add a Set classifier in `partition.py`, reached only for `artifact_type == "plans"`. For every distinct Set with at least one selected candidate, read its full on-disk membership with `runner_shared.read_set_membership(repo, setid)` (import it lazily inside the function; `attention.py` already does this). Classify each member: FINISHED (status in `runner_shared.set_retirement_terminal_statuses()`), RUNNABLE (selected AND its action is not skip/undetermined per `run_selection_policy.action_for_status`), or BLOCKED (unfinished and not runnable in this batch, either because its status has no runnable action, e.g. `to-review` under `--action execute`, or because it was filtered out by `-s`, `-p`, `--max` or an explicit selector). A Set is COMPLETE-ABLE when it has no BLOCKED member. Return a typed result per Set carrying its orchestrator id, its children by class, and, for each BLOCKED child, the reason and a fix hint (E-04). Do not re-derive membership from filenames: `read_set_membership` already handles legacy `Order: 0` without `Kind:` and the id6-shaped-setid pin.
  - Depends on: E-01
  - Expected outcome: a pure-with-respect-to-git function returning, for the E-01 fixture, Set A COMPLETE-ABLE and Set B not, with Set B's `to-review` child listed as BLOCKED with its reason.
  - Execution state: pending

### Task group 2: enforce cohesion and refusal

- [ ] E-03 Make Set membership a clustering edge. In `components` (or a wrapper the plans path calls), add an undirected edge between a selected orchestrator and each of its RUNNABLE children, so `partition` places them in one component. Keep `in_selection_edges` unchanged for declared dependencies, so ordering within a shard still follows `dependency_depths`. Then ensure the orchestrator sorts LAST within its shard's slice for its Set (it retires after its children; the runner already orders an orchestrator after its children via `queue_sort_key`, so this is about the emitted command reading sensibly, not correctness). An oversized component is still split by today's rule, EXCEPT that a Set component is never split: if one Set is larger than the per-shard cap, it goes whole into one shard and the result notes the imbalance.
  - Depends on: E-02
  - Expected outcome: for the E-01 fixture's Set A, the orchestrator and all three children are in the same shard at every `-n` from 1 to 4.
  - Execution state: pending

- [ ] E-04 Refuse an incomplete Set by default. If any selected Set is not COMPLETE-ABLE and `--allow-partial-sets` was NOT passed, emit NO commands, exit 2, and print one block per blocked Set to stderr in this shape (colored via `Term.colorize`: the leading word red and bold, ids bold, fix commands cyan; plain under `--no-color`/`NO_COLOR` and in `--json`/`--agent`):

      error: Set 'netnsfilter' cannot finish in this batch, so none of it was scheduled.
        blocked: 2j4pd0 (to-review, needs review), wn956n (to-review, needs review)
        fix:     /plan-review 2j4pd0 wn956n, then approve them; or rerun with --allow-partial-sets
                 to run the ready plans now and leave the orchestrator m0kl28 for a later batch.

  Fix hints by cause: `to-review` or `reviewed` -> review and approve; filtered out by a selector or filter -> "add <id6> to the selection" (or the setid); excluded by `--max` -> "raise --max to N or select the Set by its setid"; any other non-runnable status -> name the status and "see aw ipd board <id6>". In `--json`/`--agent` output the refusal carries the same facts as structured fields (`blocked_sets: [{setid, orchestrator, blocked: [{id6, status, reason, fix}]}]`) and the existing exit-2 contract.
  - Depends on: E-02
  - Expected outcome: the E-01 fixture without the flag exits 2, prints nothing on stdout, and names Set B's blocked child with its fix; in `--json` the same refusal is structured.
  - Execution state: pending

- [ ] E-05 Add `--allow-partial-sets` to the `partition` parser in `agent_workflows/cli.py`, help text: "Schedule the ready plans of a Set that cannot finish in this batch. The Set's orchestrator is never scheduled until every child can run." With it: each incomplete Set's RUNNABLE children are emitted (clustered together as one component), its orchestrator is DROPPED, and a yellow `warning:` block per Set says which orchestrator was held back, which children block it, and the same fix hints as E-04. An orchestrator whose Set is not COMPLETE-ABLE is never emitted, with or without the flag. Under the flag the exit code is 0.
  - Depends on: E-04
  - Expected outcome: the E-01 fixture with the flag emits Set A whole plus Set B's one approved child, never Set B's orchestrator, and prints the warning; exit 0.
  - Execution state: pending

### Task group 3: pin, document, prove

- [ ] E-06 Add `tests/test_partition_set_cohesion.py`, driving `aw partition` through `cli.main` against `tmp_path` fixture repos and asserting on stdout commands, stderr text, the JSON payload and exit codes (never on source text). Cases: (a) cohesion: Set orchestrator and children share a shard for `-n` 1..4; (b) default refusal: exit 2, no stdout, stderr names each blocked child, its status and its fix; (c) `--allow-partial-sets`: ready children emitted, orchestrator absent, warning present, exit 0; (d) a Set whose children are all FINISHED except the orchestrator: the orchestrator alone is emitted (it can retire with no agent turn); (e) filtered-out child: selecting only some children of a Set by id6 refuses, naming the missing child with the "add it to the selection" fix, and selecting by setid passes; (f) `--max` truncation that would split a Set refuses with the "raise --max" fix; (g) color: with `--color` the refusal contains ANSI escapes, with `--no-color` it contains none; (h) a selection with no orchestrators at all partitions byte-identically to today (no regression); (i) backlog and specs types are unaffected. Each of (a), (b), (c) must FAIL on the pre-change code; show that by running them against a checkout of the base commit and pasting the failures.
  - Depends on: E-05
  - Expected outcome: the new module passes, and (a)-(c) are demonstrated failing before the change.
  - Execution state: pending

- [ ] E-07 Document and prove. Describe the Set rule, the refusal and the flag in the `partition` parser's description/epilog in `agent_workflows/cli.py` (no doc under `docs/` describes `aw partition`; measured with `grep -rln 'aw partition' docs/ README.md`, no hits), add a CHANGELOG entry (user-facing prose, no em or en dashes), run the existing `tests/test_partition.py` unchanged, run the bare suite, and run the real command on this repository: `aw partition -t plans approved -n 3 --run agy` and paste the output, which must either schedule each Set whole or refuse naming what blocks it.
  - Depends on: E-06
  - Expected outcome: `tests/test_partition.py` passes unedited, the bare suite passes, and the live output contains no orchestrator separated from its children.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite: run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`. Tests drive surfaces and assert on outputs, never read source (`AGENTS.md`, GUIDING_PRINCIPLES P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Set membership and terminal statuses have one authority each: `runner_shared.read_set_membership` and `runner_shared.set_retirement_terminal_statuses`. Reuse them; do not re-derive.
- Runner action per status has one authority: `run_selection_policy.action_for_status`, already used by `partition.collect`.
- Color goes through `term.Term.colorize`, which already honors `--no-color`, `--color` and `NO_COLOR`.
- User-facing prose (CHANGELOG, help, docs) carries no em or en dashes.
- Cite code by SYMBOL; line numbers drift (spec `ipd-structure-and-linting` 10.2).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Partition clusters ONLY by declared `Item-Dependencies`. | `partition.in_selection_edges` builds edges from `it.item_dependencies`; `partition.components` unions only those. |
| F-02 | Orchestrators are linked to children by Set membership, not by an edge. | All five failing orchestrators (`axozpe`, `i18yaz`, `l4vw9o`, `m0kl28`, `u4glub`) declare `- Item-Dependencies: none`; so do their children checked (`i6mby8`, `urv602`). |
| F-03 | Measured split, one `aw partition -n 3` -> `run-20261009T013333Z-334392` (shard 0), `run-20261009T024714Z-1667714` (shard 1), `run-20261009T030837Z-2088618` (shard 2). | axozpe 0 vs children 1; i18yaz 0 vs 1; u4glub 0 vs 2; m0kl28 0 vs 2; l4vw9o 2 vs 1. Read from each run's `state.json` `selectors`. |
| F-04 | Partition never checks whether an orchestrator's unfinished children can run. | `m0kl28` was emitted while children `2j4pd0` and `wn956n` were `- Status: to-review`. `partition.collect` checks each candidate's own action only. |
| F-05 | The runner's refusal is correct and is not the defect. | `runner_shared.evaluate_set_retirement` refuses `children-not-in-this-run` exactly when children are absent from the queue; the fix belongs where the queue is composed. |
| F-06 | Membership with Kind/Order/Status is already available from disk. | `runner_shared.read_set_membership` returns `SetMembership(orchestrator, children)` of `SetMember(id6, order, kind, status, path)`; `SetMember.is_orchestrator` handles legacy `Order: 0` without `Kind:`. |

## Proposed changes (ordered, validatable)

1. Classify each selected Set from disk (E-02).
2. Cluster orchestrator with runnable children; never split a Set (E-03).
3. Refuse incomplete Sets by default with colored, actionable errors (E-04).
4. `--allow-partial-sets` runs ready children and always holds the orchestrator back (E-05).
5. Tests, docs, CHANGELOG, live proof (E-06, E-07).

## Deferred / out of scope (with reason)

- Changing the runners or `evaluate_set_retirement`: their refusal is correct (F-05).
- Partitioning backlog or specs by Set: neither has orchestrators; E-06 (i) pins that they are unaffected.
- Auto-reviewing or auto-approving blocked children: approval is a human act.
- Cross-shard cooperation (one run waiting on another's children): out of scope; cohesion makes it unnecessary.

## Scope check

- Over-scope: none. Every declared path is touched: `partition.py` (E-02..E-05), `cli.py` (E-05 flag), the two test modules (E-06; `tests/test_partition.py` is declared so it may be RUN, and it must pass unedited), `cli.py` help text and `CHANGELOG.md` (E-07).
- Under-scope: none known.

## Required tests / validation

- `tests/test_partition_set_cohesion.py` (new), with (a)-(c) shown failing on the base commit.
- `tests/test_partition.py` unchanged and passing.
- Bare suite `python3 -m pytest`.
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
- Resolution or deferral rationale: Chosen to match the repo's existing `--allow-*` override naming (`--allow-mixed`, `--allow-drafts`, `--allow-uncovered-orchestrator-work`). A reviewer or the maintainer may rename it before execution; the behavior is unaffected.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the pre-change `aw partition ... --json` output on the E-01 fixture and point at the orchestrator/child shard mismatch and the emitted unfinishable orchestrator.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a test or REPL run calling the classifier on the E-01 fixture showing Set A COMPLETE-ABLE and Set B not, with Set B's blocked child, status and reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the post-change shard assignment for Set A at `-n` 1, 2, 3 and 4, each showing orchestrator and children in one shard.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the default-mode stderr (with `--color` and with `--no-color`), the empty stdout, the exit code 2, and the `--json` refusal payload for the E-01 fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `--allow-partial-sets` stdout commands, the warning, and exit 0, showing Set B's orchestrator absent; and `aw partition --help` showing the flag text.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_partition_set_cohesion.py -v` passing, and the same cases (a)-(c) FAILING against a worktree at the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `tests/test_partition.py` passing with `git diff --stat` showing it unchanged, the bare-suite summary line, the help-text and CHANGELOG diffs, and the live `aw partition -t plans approved -n 3 --run agy` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved 8t28wj --by-human`). Commit only the Scope-Paths files, through `aw commit 8t28wj -- <paths>`; never push. Paste actual runner output for every test claim. Do not edit `tests/test_partition.py`: its passing UNCHANGED is the no-regression evidence. After every `V-*` passes, finalize with `aw ipd finalize 8t28wj` (or let the runner self-finalize); `aw backlog set` closes `cwf2bo` through the From-Backlog handoff when this plan executes.
