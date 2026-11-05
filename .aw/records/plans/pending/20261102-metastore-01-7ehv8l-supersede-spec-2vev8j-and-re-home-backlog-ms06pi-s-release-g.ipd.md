# IPD: Supersede spec 2vev8j and re-home backlog ms06pi's release gate to 4sd62s

- Date: 2026-11-02
- Kind: child
- Concern: Approved spec `4sd62s` SUPERSEDES approved spec `2vev8j` (4sd62s "Relation to prior work"; OQ-4, maintainer ruling 2026-10-24, SR-102), but the records still say otherwise. Measured 2026-11-02: `2vev8j` sits in `.aw/records/specs/approved/` with `- Status: approved`, `- From-Backlog: ms06pi` and `- Blocks-Release: next`, so `aw releases show next` lists BOTH `2vev8j` and `4sd62s` as live blockers of release 2.0.0 (`f33nrj`); `4sd62s` carries no `- From-Backlog:`, so backlog `ms06pi` (`graduated`, `Blocks-Release: next`) hands its gate only to a spec that will never be implemented; and `rg -l 2vev8j agent_workflows tests` returns 16 files (8 modules, 8 tests) whose comments, docstrings and one user-facing recovery string cite the superseded spec as the authority. Spec section 7 requires this to be fixed by the first plan of phase A, "so that the records are consistent before any code changes".
- Scope: Records and citation hygiene only. Transition `2vev8j` to `superseded` with a history message citing `4sd62s`, and clear its `- From-Backlog:` so it stops counting as an unshippable carrier of `ms06pi`; add `- From-Backlog: ms06pi` to `4sd62s` with the tooled setter; record the handoff on `ms06pi`; re-point every `2vev8j` citation in `agent_workflows/` and `tests/` to the `4sd62s` section that now holds the rule. EXCLUDES any behavior change, any code other than comments, docstrings and one recovery-hint string, and `CHANGELOG.md` (released history).
- Scope-Paths: .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, .aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md, agent_workflows/artifact_core.py, agent_workflows/attention.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, agent_workflows/ipd_authoring.py, agent_workflows/record_history.py, agent_workflows/specs.py, agent_workflows/status_set.py, tests/test_backlog.py, tests/test_backlog_history_dedup_parity.py, tests/test_history_date_clock.py, tests/test_history_date_clock_parity.py, tests/test_history_date_clock_residual.py, tests/test_history_date_clock_sidecar.py, tests/test_history_label_parity.py, tests/test_scaffold_history_clock.py, .aw/records/plans/pending/20261102-metastore-01-7ehv8l-supersede-spec-2vev8j-and-re-home-backlog-ms06pi-s-release-g.ipd.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7ehv8l

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the records agree with the maintainer's ruling that `4sd62s` replaces `2vev8j`: one live metadata spec, one carrier of `ms06pi`'s release gate, and code comments that cite the spec that now owns each rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Record the baseline before any change: save `aw check --agent` to `/tmp/opencode/7ehv8l-check-before.jsonl`, and save the output of `aw releases show next`, `aw specs check`, `rg -l 2vev8j agent_workflows tests` and `python3 -c "from pathlib import Path; from agent_workflows import check_engine as c; print(c.find_from_backlog_artifacts(Path('.').resolve(), 'ms06pi'))"`.
  - Depends on: none
  - Expected outcome: the release blocker list names `2vev8j` and `4sd62s`; the carrier list names only `2vev8j`; `rg` lists 16 files.
  - Execution state: pending

### Task group 2: records

- [ ] E-02 Supersede `2vev8j` through the tooled setter and clear its backlog link in the same call: `aw specs set superseded 2vev8j --from-backlog - --message "Superseded by spec 4sd62s (4sd62s OQ-4, maintainer ruling 2026-10-24, SR-102). Surviving rules folded into 4sd62s 4.2, 4.2a, 4.2b, 4.5. Release-gate handoff of backlog ms06pi moved to 4sd62s (plan 7ehv8l)." --no-commit`. Leave its `- Blocks-Release: next` line unchanged (a superseded spec is not a live blocker: measured on a scratch copy, `aw releases show next` stops listing it after the transition, and rewriting the line would alter what the record says it gated).
  - Depends on: E-01
  - Expected outcome: the file moves to `.aw/records/specs/superseded/`, carries `- Status: superseded`, no `- From-Backlog:` line, and a new history line naming `4sd62s`.
  - Execution state: pending

- [ ] E-03 Link `4sd62s` to the backlog item with the tooled setter: `aw specs set approved 4sd62s --from-backlog ms06pi --message "Inherits the release-gate handoff of backlog ms06pi from superseded spec 2vev8j (4sd62s OQ-4; plan 7ehv8l). Status unchanged." --no-commit`. Status stays `approved`; the call is a same-status write whose only field change is `- From-Backlog: ms06pi` (measured on a scratch copy). Its existing `- Blocks-Release: next` already matches `ms06pi`, so `check.from-backlog-gate-mismatch` has nothing to report.
  - Depends on: E-02
  - Expected outcome: the `4sd62s` front matter gains exactly one line, `- From-Backlog: ms06pi`, and one history line; no other byte of the spec changes.
  - Execution state: pending

- [ ] E-04 Record the handoff on the backlog item without changing its status: `aw backlog set graduated ms06pi --message "Release-gate handoff moved from superseded spec 2vev8j to spec 4sd62s, which now carries - From-Backlog: ms06pi and the same - Blocks-Release: next (4sd62s OQ-4; plan 7ehv8l). Still graduated, not done: no code is written." --no-commit`.
  - Depends on: E-03
  - Expected outcome: `ms06pi` stays in `graduated/` with `- Status: graduated` and `- Blocks-Release: next`; one new history line names `4sd62s`.
  - Execution state: pending

### Task group 3: citations

- [ ] E-05 Re-point the 8 module citations, comment and docstring text only plus one recovery hint, using this mapping (each 4sd62s section quoted from the spec): `2vev8j` 4.4 UTC writer rule -> `4sd62s` 4.2b; `2vev8j` 4.3 per-artifact seq -> `4sd62s` 4.2; `2vev8j` C5 (no event before the durable write) -> `4sd62s` C6; `2vev8j` E1 (shared JSONL append conflicts) -> `4sd62s` C3 and 4.7 (per-artifact logs so different artifacts never share a file). Files: `artifact_core.py` (the `utc_history_date` banner and docstring), `attention.py`, `backlog.py` (two sidecar-order comments), `check_engine.py` (the `check.lifecycle-transition-unvalidated` rule comment and docstring, its `recovery=` hint which becomes "wait for spec 4sd62s 4.2 per-artifact seq", and the namespace-gate comment, which becomes "spec 6m4kow and the superseded artifact-metadata-storage spec (now 4sd62s)"), `ipd_authoring.py`, `record_history.py`, `specs.py`, `status_set.py`.
  - Depends on: E-01
  - Expected outcome: `rg -n 2vev8j agent_workflows` prints nothing; `git diff --stat agent_workflows` shows only those 8 files; every changed line is a comment, a docstring, or the one `recovery=` string.
  - Execution state: pending

- [ ] E-06 Re-point the 8 test-file citations (module docstrings and inline comments only; no assertion reads the spec id, measured with `rg -n 2vev8j tests`): `test_backlog.py`, `test_backlog_history_dedup_parity.py`, `test_history_date_clock.py`, `test_history_date_clock_parity.py`, `test_history_date_clock_residual.py`, `test_history_date_clock_sidecar.py`, `test_history_label_parity.py`, `test_scaffold_history_clock.py`, using the E-05 mapping (the "One timezone for every writer" rule is `4sd62s` 4.2b "One clock for each stored value").
  - Depends on: E-01
  - Expected outcome: `rg -l 2vev8j agent_workflows tests` prints nothing; no test logic changes.
  - Execution state: pending

### Task group 4: verification and commit

- [ ] E-07 Verify and commit: rerun the E-01 commands and diff `aw check --agent` against the baseline; run `python3 -m pytest -o addopts="" -n auto tests/test_backlog.py tests/test_backlog_history_dedup_parity.py tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_residual.py tests/test_history_date_clock_sidecar.py tests/test_history_label_parity.py tests/test_scaffold_history_clock.py tests/test_check_engine_release_gate.py tests/test_release_gate_one_way_mismatch.py`, the bare core gate `python3 -m pytest`, `aw check release-gates` and `aw sanitize --agent`; commit through `aw commit 7ehv8l -- <every Scope-Paths path that changed>`. Never push.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: both pytest runs pass; `aw check` shows no new error or warning (the only path change is `2vev8j`'s pre-existing `check.spec-criteria-uncovered` advisory moving with the file); `aw releases show next` lists `ms06pi` and `4sd62s` and not `2vev8j`; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec status is owned by `aw specs set` (AGENTS.md "What needs attention"); `attention_contract.SPEC_TRANSITIONS["approved"]` contains `superseded`, so `approved -> superseded` is a legal edge and needs no override. The setter relocates the file to `superseded/` (`.aw/records/specs/README.md`, "Location agrees with status").
- `aw specs set` accepts `--from-backlog <id6|->` on any call, including a same-status call (`aw specs set --help`); measured on a scratch copy, `aw specs set approved 4sd62s --from-backlog ms06pi` writes `- From-Backlog: ms06pi` and reports status `unchanged`.
- The close-legitimacy predicate is `check_engine.evaluate_blocking_close`. Its HANDOFF route requires at least one same-gate carrier AND that EVERY carrier from `check_engine.find_from_backlog_artifacts` is finished per `check_engine._carrier_is_executed` (a spec counts only at `implemented`). A superseded spec never reaches `implemented`, so a `2vev8j` that kept `- From-Backlog: ms06pi` would block `ms06pi` from closing through HANDOFF forever (measured below, F-04).
- Setters append to the gitignored sidecar `.aw/records/history.jsonl` (`record_history.append`); that file is never committed.
- Commits go through `aw commit <id6> -- <paths>` (AGENTS.md execution contract); setters here run with `--no-commit` so the plan's single commit holds every change.

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | `rg -l 2vev8j agent_workflows tests` lists 16 files; `rg -c` gives 18 lines in 8 modules and 14 lines in 8 tests | Matches the spec's OQ-4 count of 16 files. |
| F-02 | `aw releases show next` lists `ms06pi`, `2vev8j` and `4sd62s` | `2vev8j` is still counted as a live blocker of 2.0.0. |
| F-03 | `find_from_backlog_artifacts(repo, 'ms06pi')` returns only the `2vev8j` spec | The gate is handed to the superseded spec only. |
| F-04 | Scratch copy, `2vev8j` superseded with its `From-Backlog` kept and `4sd62s` linked: `evaluate_blocking_close(..., 'done')` refuses and names BOTH carriers as not shipped | Clearing `2vev8j`'s `From-Backlog` is required, not cosmetic. After clearing it, the verdict names only `4sd62s`, which is correct until `4sd62s` is implemented. |
| F-05 | Scratch copy after E-NEW steps: `aw releases show next` lists `ms06pi` and `4sd62s`; `aw check release-gates` reports 0 errors; `aw check` adds no finding for `2vev8j`, `ms06pi` or `4sd62s` once the metastore plans are present | The record change is safe for every release-gate rule. |
| F-06 | `rg -n "per-artifact seq" tests` returns nothing | No test asserts the `check_engine` recovery hint text, so re-pointing it changes no test. |
| F-07 | `CHANGELOG.md` cites `2vev8j` twice (lines for the lifecycle-unvalidated rule and the UTC unification) | Those are entries describing work as it shipped; see Deferred. |

## Proposed changes (ordered, validatable)

1. E-01 baseline.
2. Records: supersede `2vev8j` and clear its link; link `4sd62s`; note the handoff on `ms06pi`.
3. Citations: modules, then tests.
4. Verify, gates, commit.

## Deferred / out of scope (with reason)

- `CHANGELOG.md` citations of `2vev8j`: changelog entries describe what shipped and what it cited at the time; rewriting them would misstate history.
  - Carrier-Declined: released-history text is not re-pointed; the superseded spec stays findable through `4sd62s` "Relation to prior work".
- Citations of `2vev8j` inside other records (82 record files, including executed plans and implemented spec `wy9aru`): AGENTS.md forbids changing what executed records say, and the spec's OQ-4 scope is the code and test files only.
  - Carrier-Declined: record history is immutable by repository rule; the cutover citation rewrite (5.2 step 3) covers only the 34 renamed legacy filenames, not this id.
- Recording `- Graduated-To: metastore` on `ms06pi`: not required for the gate handoff, which `From-Backlog` on the carrier establishes.
  - Carrier-Declined: optional navigation field; the handoff link is the carrier's `- From-Backlog:`.

## Scope check

- Over-scope: none.
- Under-scope: none. Spec OQ-4 asks for three things (supersede with a reference, re-point the 16 files, move the `ms06pi` handoff) and lists `2vev8j` in Scope-Paths; all are covered, with both the old and new path of `2vev8j` declared because the setter moves the file.

## Required tests / validation

- Acceptance criteria: this plan OWNS no `4sd62s` AC and CONTRIBUTES to none; it implements OQ-4 and the section 7 sentence "The first plan of phase A also SUPERSEDES `2vev8j`".
- Release-gate behavior: `aw releases show next` before and after; `evaluate_blocking_close` carrier list before and after; `aw check release-gates`.
- No behavior change: the named history-clock and release-gate test modules plus the bare core gate pass.

## Spec / documentation sync

Amends two spec records through tooled setters only, both declared in Scope-Paths: `2vev8j` moves to `superseded/` and loses `- From-Backlog:`; `4sd62s` gains `- From-Backlog: ms06pi`. Why: OQ-4 of `4sd62s` requires the supersession and the handoff, and the handoff is what lets `ms06pi` close legitimately once `4sd62s` is implemented. No spec body text changes.

## Open questions

### OQ-01: Does a same-status `aw specs set approved 4sd62s` read as a second approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The setter writes a history line whose token is `approved` with the explicit message "Status unchanged", carries no `--by-human` attestation, and leaves the existing 2026-11-02 human approval line intact. The alternative, `aw specs note`, cannot write `--from-backlog` (its help lists no such option), and a hand edit of the field would bypass the tooled-write rule. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the baseline `aw releases show next` rows for `ms06pi`, `2vev8j` and `4sd62s`; the printed `find_from_backlog_artifacts` list (one `2vev8j` path); and the 16-line `rg -l 2vev8j agent_workflows tests` output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git status --short` showing the rename `specs/approved/...2vev8j... -> specs/superseded/...2vev8j...`, and `git diff -M` of that file showing `- Status: approved` -> `- Status: superseded`, the removed `- From-Backlog: ms06pi` line, the unchanged `- Blocks-Release: next` line, and the new history line containing `4sd62s`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff` of the `4sd62s` spec showing exactly two added lines (`- From-Backlog: ms06pi` in the front matter and one history line containing `ms06pi`) and no removed line; paste `aw specs check` output reporting all specs conform.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff` of the `ms06pi` backlog file showing one added history line naming `4sd62s` and no change to `- Status: graduated` or `- Blocks-Release: next`; paste the post-change `find_from_backlog_artifacts(..., 'ms06pi')` output listing exactly the `4sd62s` path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n 2vev8j agent_workflows` (empty output and exit code 1), `git diff --stat -- agent_workflows` listing exactly the 8 named modules, and the `git diff` hunk of the `check_engine.py` `recovery=` string.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `rg -l 2vev8j agent_workflows tests` (empty output, exit code 1) and `git diff --stat -- tests` listing exactly the 8 named test files, plus `git diff -U0 -- tests | rg '^[-+][^-+]'` showing every changed line is a comment or docstring line.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the summary lines of the named pytest run and of the bare `python3 -m pytest`; the post-change `aw releases show next` rows (`ms06pi` and `4sd62s` present, `2vev8j` absent); the `aw check release-gates` summary line (0 errors); a before/after diff of `(location, rule)` pairs from the two `aw check --agent` captures showing only the `2vev8j` advisory path move; the `aw sanitize --agent` result record; and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited only with a justification recorded in the finalize scope reconciliation. Run every setter with `--no-commit`, then commit only through `aw commit 7ehv8l -- <paths>`; never push. Paste actual command and test output into each `V-*`. Move the plan to `.aw/records/plans/executed/` only through `aw ipd finalize 7ehv8l`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
