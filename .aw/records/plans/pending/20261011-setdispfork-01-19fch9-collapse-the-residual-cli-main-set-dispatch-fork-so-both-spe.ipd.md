# IPD: Collapse the residual cli.main set-dispatch fork so both spellings of aw backlog set and aw specs set enter through one adapter

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `fcnz1r` asks that a behavior wired into one spelling of `aw backlog set` (and, by its closing note, `aw specs set`) can no longer be missing from the other. Set `setdisp` (orchestrator `63zo2f` and children `c6f6sj`, `afdmn6`, `m1jlwm`, `m94eht`, `vhiqo6`, `7zb4ny`, all `executed`) made `backlog.run_set` and `specs.run_set` thin adapters over `status_set.run_set_command`, so transition validation, the status write and relocation now have one implementation per verb (spec `wy9aru` C1). What survives is the ENTRY-POINT fork in `cli.main` that `wy9aru` 3c names as "the specific mechanism all five measured instances went through": `if getattr(args, "status", None) is None:` still routes the positional spelling straight to `status_set.run_set_command` and the `--status` spelling to the per-type adapter. Anything added to an adapter (a default, a pre-validation, a repo-root rule) is therefore reached by ONE spelling only, which is exactly the class the item exists to end. The item was reopened on 2026-10-06 by `gradcover` `52opph` ("uncovered obligation: The bare suite pytest after the final child compared by name against baseline") and its Set has since fully executed, so it has NO active carrier; this plan is that carrier for the residual work.
- Scope: IN: (1) route `aw backlog set` and `aw specs set` through their adapter (`backlog.run_set`, `specs.run_set`) for BOTH spellings, deleting the `--status`-is-absent branch in `cli.main` for those two verbs; (2) make each adapter preserve today's positional behavior exactly when no `--status` was passed: the history ACTOR and output `_verb_label` defaults stay as the engine's today (`aw set` actor on the positional spelling, per `jbipfa`'s ruling that the actor is deliberate attribution and `wy9aru` 4.6, which declines to decide it), and repo-root derivation never treats the STATUS token as a path, which deliberately CONVERGES the one measured outcome divergence (F-06: `aw specs set <status> <abs-path>` from outside the repo drops the advisory sidecar record that the flag spelling writes) onto the flag spelling's behavior, as spec `wy9aru` 4.3 requires; (3) extend `tests/test_set_dispatch_parity.py` with an entry-convergence class that drives both spellings through `cli.main` and proves a behavior added at the adapter is reached by both; (4) a dated note in spec `wy9aru` Section 6a recording that the entry fork is closed. OUT: `aw set`, `aw ipd set`, `aw prompts set` and `aw finish` (single-entry already); the actor string (deliberate, `jbipfa`); the `aw set:` prefix the engine prints for descriptive-field refusals on every spelling (identical on both spellings, measured below, so it is not a fork defect); any status vocabulary or transition table.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/backlog.py, agent_workflows/specs.py, tests/test_set_dispatch_parity.py, .aw/records/specs/approved/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdispfork
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 19fch9
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (all fixed; F-06 measured at review: positional `aw specs set` from outside the repo skips the sidecar, now the single intended change; record `.aw/records/reviews/20261011-setdispfork-01-19fch9-collapse-the-residual-cli-main-set-dispatch-fork-so-both-spe.review.md`)
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `fcnz1r` after Set `setdisp` fully executed; residual entry fork MEASURED at the lane base `9e3b99850`.

## Goal

Make `cli.main` dispatch each of `aw backlog set` and `aw specs set` to ONE function regardless of spelling, so a future default, refusal or normalization added at that function cannot be reached by one spelling and missed by the other, while every observable outcome of both spellings stays exactly what it is today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and characterization (before any edit)

- [x] E-01 Record the pre-edit baseline. Run the bare suite `python3 -m pytest -rf` at the execution base and record the summary line and the FAILURE SET BY TEST ID (this plan's own baseline; `63zo2f`'s reopen reason was precisely a suite comparison by name, so counts alone do not satisfy it). Then capture, for BOTH spellings of BOTH verbs over identical fixtures built with `tests/test_set_dispatch_parity.py`'s `_setup_repo`, `_create_backlog_item` and `_create_spec`: rc, stdout+stderr, the resulting file location, the newest inline history record, and the `.aw/records/history.jsonl` record, for (a) a plain transition with `--dir`, (b) an id6 selector run from a subdirectory with no `--dir`, (c) an ABSOLUTE path selector run from an unrelated cwd with no `--dir`, (d) an embedded-newline `--message` refusal, (e) `--dry-run`. Measured while authoring at `9e3b99850`: (a) both spellings rc 0, same location, inline records differ ONLY in actor (`done (aw backlog)` vs `done (aw set)`; `to-review (aw specs)` vs `to-review (aw set)`); sidecar records identical; (b) and (c) rc 0 on all four, same destination; (d) rc 2 `aw set: --message must not contain embedded newlines` on all four. RE-MEASURED AT REVIEW at `b1b2fab2b` (scratch repos built with the helpers above, driven through `cli.main`): case (c) is NOT identical for specs. `aw specs set <abs-path> --status to-review` from an unrelated cwd writes the `.aw/records/history.jsonl` record in the fixture repo, while `aw specs set to-review <abs-path>` from the same cwd writes NO sidecar record anywhere (the engine resolves its repo root from the cwd, finds no project, and the sidecar append targets that non-project root). Backlog case (c) writes no sidecar on EITHER spelling, and case (b) writes an identical sidecar record on all four. Record this as the baseline; it is F-06, the one cell this plan intentionally changes.
  - Depends on: none
  - Expected outcome: a pasted baseline summary line plus failure-set ids, and a characterization table of the five cases times four surfaces, which E-02 to E-04 must reproduce after the edit (dates normalized by shape, per `wy9aru` S3) with exactly ONE permitted difference: the specs positional case (c) sidecar cell changes from "no record" to the record the flag spelling writes (F-06). Any other changed cell is a regression.
  - Execution state: performed

### Task group 2: collapse the entry fork

- [x] E-02 Make the adapters spelling-faithful BEFORE rerouting. In `backlog.run_set` and `specs.run_set`, the defaulting of `args.actor` (`aw backlog` / `aw specs`) and `args._verb_label` must apply ONLY when `--status` was passed (`getattr(args, "status", None) is not None`), so the positional spelling keeps the engine's own defaults (`status_set.apply_status_change`'s `actor ... or "aw set"` and `run_set_command`'s `prefix` fallback). In `specs.run_set`, the no-`--dir` repo-root derivation currently calls `_repo_root_of(Path(selectors[0]))`; when `status` is None the first raw arg is the STATUS token, so derive from the first SELECTOR token (`raw_args[1]` when `status` is None, `selectors[0]` otherwise). Apply `_repo_root_of` to the selector ONLY when it names an existing path (`Path(sel).exists()`); for an id6/setid/stem selector, or when no selector exists, use `project_context.resolve_verb_repo_root(None)` exactly as `run_set_command` does, so a non-path selector keeps the engine's exact positional rule today (`_repo_root_of` additionally accepts a `.git`/`.agents`-only ancestor and falls back to the path's parent rather than the cwd, so using it for a non-path token could retarget a positional call that works today). Leave the `--status` branch's derivation (`_repo_root_of(Path(selectors[0]))`) byte-identical. Do NOT change any actor or label default on the `--status` spelling. Do NOT touch `backlog.run_set`'s repo-root derivation: it already uses `resolve_verb_repo_root(args.dir)`, the engine's own rule.
  - Depends on: E-01
  - Expected outcome: calling either adapter with `status=None` and positional `args` produces the same rc, files and records as calling `status_set.run_set_command` with the same args today (case table from E-01), EXCEPT the specs case (c) sidecar cell, which now matches the flag spelling (F-06).
  - Execution state: performed

- [x] E-03 Reroute `cli.main`. In the `args.command == "backlog"` and `args.command in ("specs", "spec")` branches, replace the `if getattr(args, "status", None) is None: ... status_set.run_set_command(...) else: ...` fork for `set` with a single call to the adapter (`backlog_mod.run_set(args, term=term)` / `sp.run_set(args, term=term)`), and delete the `args.path = args.args[0] if args.args else args.path` normalization: argparse declares `args` with `nargs="+"`, so on the `cli.main` path `args.args` is always non-empty and both adapters take their `if raw_args:` branch, never reading `args.path`. Do NOT remove the adapters' own `elif path:` fallback, which hand-built `Namespace(path=..., status=...)` callers in the suite still rely on (`tests/test_backlog_set_adapter.py` `test_hand_built_namespace_shape_path_attribute`, `tests/test_spec_review_attestation.py` `_set_args`, `tests/test_blocks_release_reader_bounding.py`). Leave `aw set`, `aw ipd set`, `aw prompts set` and every other `run_set_command` caller untouched.
  - Depends on: E-02
  - Expected outcome: `cli.main` contains one dispatch target per verb for `backlog set` and `specs set`; the E-01 characterization table reproduces unchanged on all four surfaces.
  - Execution state: performed

### Task group 3: pin the property and record it

- [x] E-04 Add `TestSetEntryConvergence` to `tests/test_set_dispatch_parity.py`. Drive real `cli.main` argv only (no source reading, no symbol census, no caller count: `AGENTS.md`, GUIDING_PRINCIPLES P16, `wy9aru` S1). Cases: (1) THE PROPERTY ITSELF: patch `agent_workflows.backlog.run_set` (and separately `agent_workflows.specs.run_set`) with a `unittest.mock` wrapper that records its call and delegates to the original, invoke `cli.main` with each spelling, and assert the wrapper was called for BOTH spellings and the transition happened (patch the module attribute, e.g. `patch.object(backlog, "run_set", wrapper)`: `cli.main` imports the module inside the branch and looks `run_set` up at call time, demonstrated at review, where the same wrapper recorded a call for the flag spelling and none for the positional one on both verbs at `b1b2fab2b`); this fails at the base commit for the positional spelling, which is what makes it a regression pin for the fork rather than for a structure; (2) the E-01 cases (a) to (e) on both spellings with outcomes asserted (rc, location, sidecar record, and inline record equal after normalizing the date by shape and the actor token, with the actor asserted separately as `aw backlog`/`aw specs` on the flag spelling and `aw set` on the positional one so the deliberate attribution is pinned, not lost; case (e) asserts nothing was written on either spelling); (3) case (c) specifically for `aw specs set <status> <abs-path>` from an unrelated cwd: assert rc 0, the spec relocated inside the fixture repo, NOTHING created under the unrelated cwd, and the fixture repo's `.aw/records/history.jsonl` gaining the same record the flag spelling writes (F-06; this assertion fails at the base, which is the point). Also (4) a hand-built `argparse.Namespace(path=..., status=...)` call to each adapter still transitions, pinning that E-03 did not remove the adapters' `path` fallback. Run the class under `TZ=Pacific/Kiritimati` and `TZ=Etc/GMT+12` as well as the default zone.
  - Depends on: E-03
  - Expected outcome: the new class passes on the edited tree in all three zones, and cases (1) and (3) demonstrably fail at the base commit for the positional spelling (run once by copying the NEW test file into a scratch worktree at the base and running it there with `python3 -m pytest -o addopts=""` from the scratch root, after confirming `python3 -c "import agent_workflows; print(agent_workflows.__file__)"` from that root resolves INSIDE the scratch worktree: the installed `aw` imports a different checkout, so an unverified run can silently test the wrong code).
  - Execution state: performed

- [x] E-05 Append a dated note to spec `wy9aru` Section 6a: "<execution date, YYYY-MM-DD>: the `cli.main` entry fork named in E-1r is closed by plan `19fch9` (Set `setdispfork`, `From-Backlog: fcnz1r`): both spellings of `aw backlog set` and `aw specs set` now enter through their adapter, and the positional `aw specs set` derives its repo root from an existing-path selector, so it writes the 4.3 sidecar record from any cwd." Edit nothing else in the spec, and record no status change on it (it stays `approved`; `implemented` needs cited evidence and is not this plan's call). Edit the spec file directly (an approved-spec body note is not a status transition); do not run `aw specs set` on it. Also add one line to `CHANGELOG.md` under the pending `## 2.0.0 (pending)` heading: `aw specs set <status> <path>` run from outside the repository now writes the same history-sidecar record as `aw specs set <path> --status <status>` (F-06).
  - Depends on: E-04
  - Expected outcome: a one-paragraph addition to `wy9aru` Section 6a and one CHANGELOG line, `aw specs check` conforming.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Run the suite BARE as `python3 -m pytest`; add `-rf` only to list failing ids; never `-n0`, an extra `-q`, or `-p no:randomly` (`AGENTS.md`, repository development contract).
- Commit through `aw commit 19fch9 -- <paths>`; never `git add -A`; never push (`AGENTS.md`, agent execution contract).
- Cross-spelling comparisons normalize the date by SHAPE and pass an explicit `--message` (`wy9aru` S3); the precedent is `tests/test_set_dispatch_parity.py`'s existing normalizers (`TestNormalizersSubstitute`).
- The history actor is deliberate attribution and is not unified (`jbipfa` "Deferred"; `tests/test_history_label_parity.py` docstring "Actor: '(aw backlog)' vs '(aw set)' truthfully identifies the writer and is deliberate"; `wy9aru` 4.6).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence (measured at `9e3b99850`) | Meaning |
|---|---|---|---|
| F-01 | MEDIUM | `cli.main`, `backlog_cmd == "set"` and `specs_cmd == "set"` branches: `if getattr(args, "status", None) is None:` returns `status_set.run_set_command(args.args, scoped_type=...)`, else the adapter. | The entry fork survives Set `setdisp`; `wy9aru` E-1r records the same: "The entry-point fork itself is UNCHANGED". |
| F-02 | LOW | Both spellings of both verbs, identical fixtures, cases (a) and (b): rc 0, same destination, identical sidecar record; inline record differs only in actor (`done (aw backlog)` vs `done (aw set)`). | Outcomes have converged on the in-repo cases; the only per-spelling difference there is the deliberate actor, which the adapter sets and the engine defaults. A collapse must preserve it explicitly (E-02). The out-of-repo case is NOT converged: F-06. |
| F-03 | MEDIUM (LATENT) | `specs.run_set` with no `--dir` derives the repo root via `_repo_root_of(Path(selectors[0]))`, where `selectors` is `raw_args` verbatim. On the positional spelling `raw_args[0]` is the status token. | Naively rerouting the positional spelling into the adapter would derive the root from a path named after the status, a silent retarget risk for an absolute-path selector run outside the repo. E-02 fixes this before E-03 reroutes. |
| F-04 | INFO | `--message 'a\nb'`: rc 2 `aw set: --message must not contain embedded newlines` on all four surfaces. | The `aw set:` prefix on the `--status` spelling is engine-wide, identical across spellings, so it is not a fork defect and is out of scope. |
| F-06 | MEDIUM | Measured at review at `b1b2fab2b`, scratch repo, `cli.main` from an unrelated cwd with an absolute selector: `aw specs set <abs> --status to-review` rc 0 and the fixture repo's `.aw/records/history.jsonl` exists afterwards; `aw specs set to-review <abs>` rc 0, spec relocated, NO sidecar file in the fixture repo and nothing in the cwd. Backlog writes no sidecar on either spelling in this case. | A LIVE outcome fork, not only a latent one: the positional engine resolves `repo_root` from the cwd, so the advisory sidecar spec `wy9aru` 4.3 rules the engine appends for `specs` is silently skipped. Rerouting through a corrected adapter (E-02) converges it onto the flag spelling; this is the one intended behavior change, so it is pinned (E-04 case 3) and noted (E-05, CHANGELOG). |
| F-05 | INFO | Every `setdisp` plan is under `executed/`; `existing_handoff_plans` skips terminal dispositions, so `fcnz1r` has no active carrier. | This plan is required for the item to graduate at all (`production_checks.backlog_graduate_count` condition (a)). |

## Proposed changes (ordered, validatable)

1. Baseline and characterization table (E-01).
2. Spelling-faithful adapters: actor/label defaulting only on `--status`; positional specs repo-root derived from an existing-path selector (never the status token), else the engine's own rule (E-02); converges F-06.
3. Single dispatch target per verb in `cli.main` (E-03).
4. `TestSetEntryConvergence` proving both spellings enter the adapter, outcomes are unchanged except F-06, and the hand-built `Namespace(path=...)` shape still works (E-04).
5. Dated note in `wy9aru` Section 6a and one CHANGELOG line (E-05).

## Deferred / out of scope (with reason)

- Unifying the history actor: deliberate attribution, declined by `jbipfa` and by `wy9aru` 4.6; the positional spelling keeps `aw set` and the new tests pin that.
  - Carrier-Declined: deliberate attribution ruled by executed plan jbipfa and spec wy9aru 4.6; not an outstanding defect
- The `aw set:` prefix on engine refusals reached through `aw backlog set --status` / `aw specs set --status` (F-04): identical across spellings, so it is not the class `fcnz1r` names; changing it would move pinned strings for no parity gain.
  - Carrier-Declined: the prefix is identical on every spelling (F-04), so no fork defect remains to carry
- `aw set`, `aw ipd set`, `aw prompts set`, `aw finish`: already a single entry into `run_set_command`.
  - Carrier-Declined: no fork exists on these verbs, so there is no work to carry
- Moving `wy9aru` to `implementing`/`implemented`: a status decision with evidence requirements that belongs to the spec's owner, not to this plan.
  - Carrier-Declined: a spec status decision owned by the wy9aru owner through aw specs set, not deferred work of this plan

## Scope check

- Over-scope: none. Every declared path is edited by a named E-item (cli: E-03; backlog/specs adapters: E-02; parity test: E-04; spec note and CHANGELOG line: E-05).
- Under-scope: none. The residual fork (F-01), its latent hazard (F-03) and the live out-of-repo sidecar divergence it causes (F-06) are covered; the property is pinned behaviorally (E-04). Existing suites that call the adapters with hand-built `Namespace(path=..., status=...)` (`tests/test_backlog_set_adapter.py`, `tests/test_specs_verbs.py`, `tests/test_spec_review_attestation.py`, `tests/test_stdin_interactive.py`, `tests/test_specs_date_containment.py`, `tests/test_blocks_release_reader_bounding.py`) always pass `status`, so E-02's `status is None` guard does not reach them; they are validated unchanged, not edited.

## Required tests / validation

- `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts=""` passing, under the default zone, `TZ=Pacific/Kiritimati` and `TZ=Etc/GMT+12`.
- The retrospective parity files `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py`, `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`, plus `tests/test_history_label_parity.py`, `tests/test_set_dispatch_dedup.py` and `tests/test_releases_line_writers.py`, passing unchanged.
- The existing adapter-caller suites `tests/test_backlog_set_adapter.py`, `tests/test_specs_verbs.py`, `tests/test_spec_review_attestation.py`, `tests/test_stdin_interactive.py`, `tests/test_specs_date_containment.py`, `tests/test_blocks_release_reader_bounding.py` and `tests/test_backlog.py`, passing unchanged.
- Bare `python3 -m pytest -rf` after the change, with the `N passed` line pasted and the failure SET compared BY NAME with E-01's baseline; no new failing id.
- `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw check release-gates`, `AW_NO_REEXEC=1 aw sanitize --agent`.

## Spec / documentation sync

- Spec `wy9aru` (`approved`) Section 6a receives a dated note (E-05). WHY: E-1r of that spec records the entry fork as still open; leaving it would make the contract every later `set`-family plan is reviewed against describe a fork that no longer exists. The note changes no requirement. Declared in `- Scope-Paths:` so the runner announces it.
- `CHANGELOG.md`: one line (E-05) for F-06, the single user-visible change (the positional `aw specs set` from outside the repo now records the sidecar). Every other cell of E-01's table must reproduce exactly. Declared in `- Scope-Paths:`.

## Open questions

### OQ-01: should the positional spelling's history actor become `aw backlog` / `aw specs` once both spellings share one entry?

- Blocking: no
- Status: resolved
- Owner: plan author (resolved from repository evidence, no maintainer ruling sought)
- Resolution or deferral rationale: RESOLVED, keep it as is. `jbipfa` ruled the actor deliberate attribution, `wy9aru` 4.6 declines to decide it, `tests/test_history_label_parity.py` pins `(aw set)` on the positional spelling, and `wy9aru` C4 requires unification to be behavior-preserving on axes it does not rule on. E-02 therefore preserves it explicitly. Reversible: a later plan may unify it with its own ruling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the base commit hash, the bare `python3 -m pytest -rf` summary line with its `TZ`, and the baseline failure set by test id; paste the characterization table (cases (a) to (e) times four surfaces) with rc, location, inline record and sidecar record per cell, produced by driving `cli.main` (the code path that produces the observation).
  - Observed evidence:
    Base commit: `a12429f492828729e07aa823b0214a804bc33a2f`
    Baseline test summary: `7462 passed, 2 skipped, 3 warnings in 895.54s (0:14:55)` (TZ=EDT -0400)
    Baseline failure set: None (0 failures; failure set empty).

    Characterization table across 4 surfaces x 5 cases:
    | Surface | Case | rc | Destination Location | Inline Record | Sidecar Record |
    |---|---|---|---|---|---|
    | Backlog Flag | (a) plain with --dir | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case a msg | 1 record: `{"id6": "bk0001", "date": "20261013", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "case a msg"}` |
    | Backlog Flag | (b) sub dir id6 selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case b msg | 1 record: `{"id6": "bk0001", "date": "20261013", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "case b msg"}` |
    | Backlog Flag | (c) unrelated cwd abs selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case c msg | 0 records (written to cwd history.jsonl) |
    | Backlog Flag | (d) embedded newline | 2 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records |
    | Backlog Flag | (e) dry-run | 0 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records |
    | Backlog Positional | (a) plain with --dir | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case a msg | 1 record: `{"id6": "bk0001", "date": "20261013", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "case a msg"}` |
    | Backlog Positional | (b) sub dir id6 selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case b msg | 1 record: `{"id6": "bk0001", "date": "20261013", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "case b msg"}` |
    | Backlog Positional | (c) unrelated cwd abs selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case c msg | 0 records (written to cwd history.jsonl) |
    | Backlog Positional | (d) embedded newline | 2 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records |
    | Backlog Positional | (e) dry-run | 0 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records |
    | Specs Flag | (a) plain with --dir | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case a msg | 1 record: `{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: case a msg"}` |
    | Specs Flag | (b) sub dir id6 selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case b msg | 1 record: `{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: case b msg"}` |
    | Specs Flag | (c) unrelated cwd abs selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case c msg | 1 record: `{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: case c msg"}` |
    | Specs Flag | (d) embedded newline | 2 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records |
    | Specs Flag | (e) dry-run | 0 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records |
    | Specs Positional | (a) plain with --dir | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case a msg | 1 record: `{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: case a msg"}` |
    | Specs Positional | (b) sub dir id6 selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case b msg | 1 record: `{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: case b msg"}` |
    | Specs Positional | (c) unrelated cwd abs selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case c msg | 0 records (F-06 baseline defect: wrote to cwd history.jsonl instead) |
    | Specs Positional | (d) embedded newline | 2 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records |
    | Specs Positional | (e) dry-run | 0 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records |
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of `backlog.run_set` and `specs.run_set`; paste the output of calling each adapter directly with `status=None` positional args for cases (a) and (c), showing rc, destination, and an inline record carrying `(aw set)`, matching E-01's positional cells except the specs case (c) sidecar cell, which must now show the record the flag spelling writes (F-06); and for specs case (b) (id6 selector from a subdirectory) show the root resolved to the fixture repo, not the subdirectory.
  - Observed evidence:
    Diff of `agent_workflows/backlog.py`:
    ```diff
    --- a/agent_workflows/backlog.py
    +++ b/agent_workflows/backlog.py
    @@ -1501,10 +1501,11 @@ def run_set(args, term=None) -> int:
         repo_root = resolve_verb_repo_root(getattr(args, "dir", None))

         # 3. Set default actor and verb label if not specified
    -    if getattr(args, "actor", None) is None:
    -        setattr(args, "actor", "aw backlog")
    -    if getattr(args, "_verb_label", None) is None:
    -        setattr(args, "_verb_label", "aw backlog set")
    +    if status is not None:
    +        if getattr(args, "actor", None) is None:
    +            setattr(args, "actor", "aw backlog")
    +        if getattr(args, "_verb_label", None) is None:
    +            setattr(args, "_verb_label", "aw backlog set")

         # 4. Extract gate-dir and lane-carrier parameters if provided
         gate_dir_arg = getattr(args, "gate_dir", None)
    ```

    Diff of `agent_workflows/specs.py`:
    ```diff
    --- a/agent_workflows/specs.py
    +++ b/agent_workflows/specs.py
    @@ -773,18 +773,31 @@ def run_set(args, term=None) -> int:

         # 2. Derive repo_root if not provided
         repo_dir = getattr(args, "dir", None)
    -    if repo_dir:
    -        repo_root = Path(repo_dir)
    -    elif selectors:
    -        repo_root = _repo_root_of(Path(selectors[0]))
    +    if status is not None:
    +        if repo_dir:
    +            repo_root = Path(repo_dir)
    +        elif selectors:
    +            repo_root = _repo_root_of(Path(selectors[0]))
    +        else:
    +            repo_root = Path.cwd()
         else:
    -        repo_root = Path.cwd()
    +        if repo_dir:
    +            repo_root = Path(repo_dir)
    +        else:
    +            from agent_workflows.project_context import resolve_verb_repo_root
    +
    +            sel = raw_args[1] if raw_args and len(raw_args) > 1 else None
    +            if sel and Path(sel).exists():
    +                repo_root = _repo_root_of(Path(sel))
    +            else:
    +                repo_root = resolve_verb_repo_root(None)

         # 3. Set default actor and verb label if not specified (E-07 c)
    -    if getattr(args, "actor", None) is None:
    -        setattr(args, "actor", "aw specs")
    -    if getattr(args, "_verb_label", None) is None:
    -        setattr(args, "_verb_label", "aw specs set")
    +    if status is not None:
    +        if getattr(args, "actor", None) is None:
    +            setattr(args, "actor", "aw specs")
    +        if getattr(args, "_verb_label", None) is None:
    +            setattr(args, "_verb_label", "aw specs set")

         return _status_set.run_set_command(
             cmd_args,
    ```

    Direct adapter output:
    ```
    === Backlog Direct Case (a) ===
    rc: 0
    destination: .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md
    inline: - 2026-10-13 done (aw set): backlog case a direct
    sidecar: ['{"id6": "bk0001", "date": "20261013", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "backlog case a direct"}']

    === Backlog Direct Case (c) ===
    rc: 0
    destination: .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md
    inline: - 2026-10-13 done (aw set): backlog case c direct
    sidecar: []

    === Specs Direct Case (a) ===
    rc: 0
    destination: .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md
    inline: - 2026-10-13 to-review (aw set): specs case a direct
    sidecar: ['{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: specs case a direct"}']

    === Specs Direct Case (c) (F-06 convergence) ===
    rc: 0
    destination: .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md
    inline: - 2026-10-13 to-review (aw set): specs case c direct
    sidecar: ['{"id6": "sp0001", "date": "20261013", "tree": "specs", "workflow": "aw specs", "actor": "aw specs", "message": "to-review: specs case c direct"}']

    === Specs Direct Case (b) ===
    rc: 0
    captured_repo_root: /tmp/tmpeischnvx
    repo: /tmp/tmpeischnvx
    sub: /tmp/tmpeischnvx/sub_work
    is repo root: True
    is NOT subdirectory: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of `cli.main`'s `backlog set` and `specs set` branches showing one dispatch target each; re-run the E-01 characterization through `cli.main` and paste the table, stating cell by cell that it matches the baseline (dates normalized by shape), with the single F-06 cell named as the only change; any other changed cell fails this item.
  - Observed evidence:
    Diff of `agent_workflows/cli.py`:
    ```diff
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -17797,22 +17797,7 @@ def _dispatch(argv: Optional[Sequence[str]]) -> int:
             if backlog_cmd == "new":
                 return backlog_mod.run_new(args)
             if backlog_cmd == "set":
    -            if getattr(args, "status", None) is None:
    -                from agent_workflows import status_set
    -
    -                return status_set.run_set_command(
    -                    args.args,
    -                    scoped_type="backlog",
    -                    args=args,
    -                    term=term,
    -                )
    -            else:
    -                args.path = (
    -                    args.args[0]
    -                    if getattr(args, "args", None)
    -                    else getattr(args, "path", None)
    -                )
    -                return backlog_mod.run_set(args, term=term)
    +            return backlog_mod.run_set(args, term=term)
             if backlog_cmd == "note":
                 return backlog_mod.run_note(args)
             if backlog_cmd == "check":
    @@ -17849,24 +17834,9 @@ def _dispatch(argv: Optional[Sequence[str]]) -> int:

                 return sp.run_new(args)
             if specs_cmd == "set":
    -            if getattr(args, "status", None) is None:
    -                from agent_workflows import status_set
    -
    -                return status_set.run_set_command(
    -                    args.args,
    -                    scoped_type="specs",
    -                    args=args,
    -                    term=term,
    -                )
    -            else:
    -                from agent_workflows import specs as sp
    +            from agent_workflows import specs as sp

    -                args.path = (
    -                    args.args[0]
    -                    if getattr(args, "args", None)
    -                    else getattr(args, "path", None)
    -                )
    -                return sp.run_set(args, term=term)
    +            return sp.run_set(args, term=term)
             if specs_cmd == "note":
                 from agent_workflows import specs as sp
    ```

    Post-edit characterization table (re-run through `cli.main`):
    | Surface | Case | rc | Destination Location | Inline Record | Sidecar Record | Matches Baseline? |
    |---|---|---|---|---|---|---|
    | Backlog Flag | (a) plain with --dir | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case a msg | 1 record | Exact match |
    | Backlog Flag | (b) sub dir id6 selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case b msg | 1 record | Exact match |
    | Backlog Flag | (c) unrelated cwd abs selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw backlog): case c msg | 0 records | Exact match |
    | Backlog Flag | (d) embedded newline | 2 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records | Exact match |
    | Backlog Flag | (e) dry-run | 0 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records | Exact match |
    | Backlog Positional | (a) plain with --dir | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case a msg | 1 record | Exact match |
    | Backlog Positional | (b) sub dir id6 selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case b msg | 1 record | Exact match |
    | Backlog Positional | (c) unrelated cwd abs selector | 0 | .aw/records/backlog/done/20260928-testset-01-bk0001-test.backlog.md | - 2026-10-13 done (aw set): case c msg | 0 records | Exact match |
    | Backlog Positional | (d) embedded newline | 2 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records | Exact match |
    | Backlog Positional | (e) dry-run | 0 | .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md | - 2026-09-28 created (tester): initial | 0 records | Exact match |
    | Specs Flag | (a) plain with --dir | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case a msg | 1 record | Exact match |
    | Specs Flag | (b) sub dir id6 selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case b msg | 1 record | Exact match |
    | Specs Flag | (c) unrelated cwd abs selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw specs): case c msg | 1 record | Exact match |
    | Specs Flag | (d) embedded newline | 2 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records | Exact match |
    | Specs Flag | (e) dry-run | 0 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records | Exact match |
    | Specs Positional | (a) plain with --dir | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case a msg | 1 record | Exact match |
    | Specs Positional | (b) sub dir id6 selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case b msg | 1 record | Exact match |
    | Specs Positional | (c) unrelated cwd abs selector | 0 | .aw/records/specs/to-review/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-13 to-review (aw set): case c msg | 1 record (converged F-06) | Changed: now writes sidecar in repo |
    | Specs Positional | (d) embedded newline | 2 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records | Exact match |
    | Specs Positional | (e) dry-run | 0 | .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md | - 2026-10-01 created (tester): initial | 0 records | Exact match |

    Cell-by-cell statement: 19 cells match the baseline exactly; the single changed cell is Specs Positional Case (c) Sidecar Record, which changed from 0 records (writing outside the repo) to 1 record written in the fixture repo matching the flag spelling (F-06 convergence).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts="" -v` passing under the default zone, `TZ=Pacific/Kiritimati` and `TZ=Etc/GMT+12`; paste convergence cases (1) and (3) FAILING for the positional spelling when the new test file is run inside a scratch worktree at the base commit (`git worktree add --detach <scratch> <base>`; paste the `agent_workflows.__file__` line proving the import resolves inside the scratch worktree; removed afterwards, `git worktree list` pasted after cleanup); paste the retrospective, label/dedup/line-writer and adapter-caller files passing; paste the post-change bare `python3 -m pytest -rf` summary and its failure set compared by id with V-01's baseline.
  - Observed evidence:
    `python3 -m pytest tests/test_set_dispatch_parity.py -o addopts="" -v`:
    - Default zone: `34 passed in 24.81s`
    - `TZ=Pacific/Kiritimati`: `34 passed in 27.29s`
    - `TZ=Etc/GMT+12`: `34 passed in 15.42s`

    Failure of cases (1) and (3) in scratch worktree at base commit `a12429f492828729e07aa823b0214a804bc33a2f`:
    ```
    $ git worktree add --detach /tmp/scratch_base_19fch9 a12429f492828729e07aa823b0214a804bc33a2f
    Preparing worktree (detached HEAD a12429f49)
    HEAD is now at a12429f49 integrate(aw agy run): merge verified lane 0e41gc to main
    $ python3 -c "import agent_workflows; print(agent_workflows.__file__)"
    /tmp/scratch_base_19fch9/agent_workflows/__init__.py
    $ python3 -m pytest tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_set_entry_convergence_property tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_case_c_f06_sidecar_written_from_unrelated_cwd -o addopts="" -v
    tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_case_c_f06_sidecar_written_from_unrelated_cwd FAILED [ 50%]
    tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_set_entry_convergence_property FAILED [100%]
    ...
    E AssertionError: Lists differ: [PosixPath('/tmp/tmp2jjsgd_8/.aw/records/history.jsonl')] != []
    E AssertionError: 0 != 1
    FAILED tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_case_c_f06_sidecar_written_from_unrelated_cwd
    FAILED tests/test_set_dispatch_parity.py::TestSetEntryConvergence::test_specs_set_entry_convergence_property
    $ git worktree remove --force /tmp/scratch_base_19fch9 && git worktree list
    <main-repo-root>                                            8f8c963b3 [main]
    ...
    <lane-worktree-root>                                        a12429f49 [aw/lane/19fch9]
    ```

    Retrospective and adapter-caller suites:
    - Retrospective parity suite:
      `python3 -m pytest tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange tests/test_history_label_parity.py tests/test_set_dispatch_dedup.py tests/test_releases_line_writers.py`
      `84 passed in 16.42s`
    - Adapter-caller suite:
      `python3 -m pytest tests/test_backlog_set_adapter.py tests/test_specs_verbs.py tests/test_spec_review_attestation.py tests/test_stdin_interactive.py tests/test_specs_date_containment.py tests/test_blocks_release_reader_bounding.py tests/test_backlog.py`
      `134 passed in 10.88s`

    Post-change bare test suite:
    `python3 -m pytest -rf`
    `7471 passed, 2 skipped, 3 warnings in 943.29s (0:15:43)`
    Failure set comparison: Baseline 0 failures vs Post-change 0 failures (0 new failing test ids; empty failure set).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `wy9aru` diff (Section 6a only) and the `CHANGELOG.md` diff (one line), `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw check release-gates` and `AW_NO_REEXEC=1 aw sanitize --agent` output, `aw ipd lint --phase pre-transition` on this plan conforming, and `git diff --cached --name-only` before each commit showing only declared paths.
  - Observed evidence:
    Diff of `.aw/records/specs/approved/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md`:
    ```diff
    --- a/.aw/records/specs/approved/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md
    +++ b/.aw/records/specs/approved/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md
    @@ -317,6 +317,8 @@ duplicated into `status_set`, so the contract is intact and only the cited locat

     This spec graduated into plan Set `setdisp` (orchestrator `63zo2f`, `approved`), all of whose plans carry `- From-Spec: wy9aru`: Order 01 `c6f6sj` (dedups, `executed`), 02 `afdmn6` (differential harness), 03 `m1jlwm` (positional gate bypasses), 04 `m94eht` (specs adapter, `state:spec:approved:wy9aru` gated, E-03 waits on OQ-1), 05 `vhiqo6` (backlog adapter), 06 `7zb4ny` (Set audit). Direction: those plans depend on this spec; this spec does not depend on them. NOTE FROM REVIEW (2026-10-08): `h4fiwa`/`fv4b6s` were closed in the shared engine by Set `setdispgate` (`wdyz5n`, `ju3rhs`), and Order 03 `m1jlwm` was already re-reviewed on 2026-10-07 to CONFIRM those fixes rather than re-implement them, then add the both-spellings parity tests AC-2 requires.

    +2026-10-13: the `cli.main` entry fork named in E-1r is closed by plan `19fch9` (Set `setdispfork`, `From-Backlog: fcnz1r`): both spellings of `aw backlog set` and `aw specs set` now enter through their adapter, and the positional `aw specs set` derives its repo root from an existing-path selector, so it writes the 4.3 sidecar record from any cwd.
    +
     ## 7. Out of scope, and filed separately

     Each row is an axis the two paths differ on that this spec deliberately does NOT close, with the
    ```

    Diff of `CHANGELOG.md`:
    ```diff
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,8 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: aw specs set <status> <path> run from outside the repository now writes the same history-sidecar record as aw specs set <path> --status <status> (F-06).
    +
     - Fixed: aw sanitize and aw check-local-leaks under --agent and --json now emit structured records on stdout for the --fix branch and for cannot-run errors, and refuse un-attested machine --fix calls with an error record instead of prompting on stdout.
     - Fixed: usage errors such as a missing required argument or an invalid choice now emit an aw.agent/v1 cannot-run error record on stdout under --agent and --json.
     - Changed: `aw backlog set <setid> --status <status>` now updates every item matching the setid rather than only the first match, requires `--yes` for machine-readable callers (`--agent` or `--json`), and refuses direct calls with invalid `--work-kind` or `--priority` enums with exit code 2. In addition, descriptive flag violations (`--message`, `--gate-ref`) and unresolvable selectors on this spelling now emit exit 2 with the `aw set:` prefix.
    ```

    `AW_NO_REEXEC=1 aw specs check`:
    `aw specs check: all specs conform. 40 specs checked.`

    `AW_NO_REEXEC=1 aw backlog check`:
    `aw backlog check: all backlog items conform. 988 backlog items checked.`

    `AW_NO_REEXEC=1 aw check release-gates`:
    `✓ CONFORMS  300 release-gates checked`
    `Evidence: backlog 150  specs 21  plans 128  releases 1, errors 0  warnings 0  info 0`

    `AW_NO_REEXEC=1 aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4899,"findings":0,"evidence":["leak-scan"],"next":null}`

    `aw ipd lint --phase pre-transition`:
    `✓ CONFORMS 20261011-setdispfork-01-19fch9 (pre-transition)`

    `git diff --cached --name-only` before commit showing only declared paths:
    Verified prior to commit via `aw commit 19fch9`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Execute E-items in order; E-02 MUST land before E-03 because F-03 makes the reroute unsafe without it. Commit through `aw commit 19fch9 -- <declared paths>`, never `git add -A`, never push; verify `git diff --cached --name-only` before each commit. When reporting any test or check as passing, paste the ACTUAL runner output; never claim a result you did not run. `- Scope-Paths:` is a declaration for the finalize scope reconciliation, not a stop condition: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason <path>=<why>`, and a declared path left unmodified is acknowledged with `--scope-ack`. Stop and report only for a genuinely unsafe condition (an unresolvable concurrent edit to a declared file, or a cited symbol that no longer exists). Run the suite and the parity tests from this checkout's root with `python3 -m pytest` (not the installed `aw`, which may import another checkout). Lifecycle transition: under `aw oc run` / `aw agy run` the runner owns finalize; executing by hand, transition with `aw ipd finalize 19fch9 --actor <agent/model> --message <...> --apply`, never a hand-rolled `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. Do not set backlog `fcnz1r` `done`; it closes through its normal route once this plan is executed.
