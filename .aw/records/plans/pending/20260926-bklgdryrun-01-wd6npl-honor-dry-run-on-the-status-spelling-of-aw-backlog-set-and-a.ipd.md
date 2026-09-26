# IPD: Honor --dry-run on the --status spelling of aw backlog set and aw specs set

- Date: 2026-09-26
- Kind: child
- Concern: The --status spelling of aw backlog set and aw specs set accepts --dry-run and ignores it: backlog.run_set rewrites the record and specs.run_set git-mv's the spec to another disposition directory, both exit 0, and both append the history.jsonl sidecar before any gate (even before a refusal).
- Scope: IN: backlog.run_set and specs.run_set dry-run gates placed after every validation/refusal (incl. evaluate_blocking_close and the specs human-authority floor) and before the sidecar, any write, git mv, or commit offer; moving both sidecar appends after every refusal; outcome tests for both spellings; one CHANGELOG line. OUT: unifying the two spellings; the positional path's missing close gate (F-7).
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/specs.py, tests/test_backlog.py, tests/test_specs_status_dirs.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: bxi1o0
- Blocks-Release: next
- Set: bklgdryrun
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wd6npl

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED, none deferred, no open question raised. Reviewed at HEAD `1aae8813`; `aw ipd lint --phase author` conformed before revision. EVERY authored finding reproduced, and both halves were driven LIVE: `aw backlog set <path> --status open --dry-run` exited 0, rewrote the item, deleted an unrecognized `- Custom-Field:` and created the sidecar; `aw specs set <path> --status to-review --dry-run` exited 0 and git-mvd the spec from draft/ to to-review/. Both refusal paths were confirmed to write the sidecar before refusing, so the F-4/F-5 widening is the same defect class and not scope creep. ESCALATED F-7 (PR-001, HIGH): the positional spelling not only skips evaluate_blocking_close but SELF-COMMITS its move, and because check.blocking-item-closed-without-gate is deliberately STAGED-SCOPED, a post-bypass `aw check release-gates` reports CONFORMS with errors 0, so the gate is unenforced AND the backstop is unreachable; the fix stays out of scope and is owned by backlog `mawwlc`, which already exists and which the plan stale-deferred to a verbal hand-off (PR-002). Corrected the gate stop condition, which named backlog id f2kqas as a plan (the plan is 2yqt0a, which declares Item-Dependencies executed:wd6npl and is therefore ordered after this one). Fixed two test items that would have failed for unrelated reasons: E-06(a)s empty-git-status assertion cannot pass on a fixture setUp that never commits (PR-004), and V-05 instructed an out-of-lane `git worktree add /tmp/...` (PR-006). Added F-9, the measured silent deletion of unrecognized fields, folded into E-05s fixture as byte identity so it does not pre-empt plan 2yqt0a which owns the renderer fix. Findings recorded in `.aw/records/reviews/20260926-bklgdryrun-01-wd6npl-honor-dry-run-on-the-status-spelling-of-aw-backlog-set-and-a.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog bxi1o0: honor --dry-run on the --status spelling of aw backlog set and aw specs set, gated after every refusal and before any sidecar, write, move, or commit offer.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `--dry-run` a real no-write preview on the `--status` spelling of `aw backlog set` and `aw specs set`: exit 0, print the would-move line, and leave the record file, its directory, and `.aw/records/history.jsonl` untouched, while still refusing every transition the real write would refuse.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: backlog.run_set

- [ ] E-01 In `backlog.run_set`, move the `record_history.append_advisory` block (the `if item.id:` block commented "Append this transition to the GLOBAL sidecar as well (awhistory Order 02)") from its current position right after `_reattach_history` to immediately before `dest_dir.mkdir(...)` / `core.atomic_write(dest, rendered)`, i.e. AFTER the `evaluate_blocking_close` refusal and after the new dry-run gate (E-02). Keep its arguments unchanged.
  - Depends on: none
  - Expected outcome: no code path that returns before `core.atomic_write` (arg errors, blocked-without-gate, the illegitimate-close refusal, the dry-run gate) appends to the sidecar. The successful write still appends exactly one sidecar record.
  - Execution state: pending

- [ ] E-02 In `backlog.run_set`, replace the write guard `if not getattr(args, "apply", True):  # set applies by default` with `if getattr(args, "dry_run", False) or not getattr(args, "apply", True):` (keeping `apply` so direct callers that pass `apply=False` keep working), printing the existing `--- would move {src} -> {dest} (status {new_status}) ---` line and returning 0. The gate stays where it is: after all validation, after the gate-default notice, and after the `evaluate_blocking_close` refusal, so a dry run of an illegitimate blocking close still exits 1 with the refusal text.
  - Depends on: E-01
  - Expected outcome: `aw backlog set <path> --status X --dry-run` exits 0, prints the would-move line, writes nothing; a dry run of an illegitimate close still exits 1 and prints `refused:`.
  - Execution state: pending

### Task group 2: specs.run_set

- [ ] E-03 In `specs.run_set`, split the `if not same_status_message_is_duplicate(...)` block: keep the in-memory `_append_history(out, ...)` there, but record a local flag (for example `sidecar_msg = f"{new}: {msg}"`, else `None`) instead of calling `_sidecar_append` inline. Call `_sidecar_append(repo_root, new_text, sidecar_msg)` only after the dry-run gate (E-04) and after the `validate_spec` residual refusal, immediately before the `moving`/`atomic_write` branch.
  - Depends on: none
  - Expected outcome: no refusal path (illegal transition, human-authority floor, evidence, review attestation, approval refusals, deferred gate, `--graduated-to` error, `validate_spec` residual) and no dry run appends to the sidecar; a real write appends exactly one record as before.
  - Execution state: pending

- [ ] E-04 In `specs.run_set`, after `dest_path`, `src_rel`, `dest_rel` and `moving` are computed and BEFORE `dest_path.parent.mkdir`, `core.git_mv`, `core.atomic_write`, and `_offer_specs_set_commit`, add: `if getattr(args, "dry_run", False): sys.stdout.write(f"--- would move {path} -> {dest_path} (status {new}) ---\n"); return 0` (use `would set` wording when `not moving`). The human-authority floor (`auth.get("by_human")`) and every other refusal above it are unchanged, so `--status approved --dry-run` without `--by-human` on a non-interactive stdin still exits 1.
  - Depends on: E-03
  - Expected outcome: `aw specs set <path> --status to-review --dry-run` exits 0, no `git mv`, no file write, no commit offer, no sidecar; `--status approved --dry-run` without `--by-human` still refused.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-05 Add tests to `tests/test_backlog.py` driving the CLI (`cli.main(["backlog", "set", <path>, "--status", ..., "--dry-run", "--dir", <repo>])`): (a) `--status open --dry-run` on an open item: exit 0, file bytes identical, the backlog directory listing identical, `.aw/records/history.jsonl` absent (or byte-identical if pre-seeded); (b) an item carrying `- Blocks-Release: <id6>` of a planned release record, `--status done --dry-run` with no evidence: exit 1, stderr contains `refused:`, file and sidecar unchanged; (c) the positional spelling `["backlog", "set", "open", <id6>, "--dry-run", "--dir", <repo>]` still exits 0 and leaves the file byte-identical (regression guard proving the two spellings agree on `--dry-run`). GIVE THE (a) FIXTURE ITEM AN UNRECOGNIZED FIELD, for example `- Custom-Field: KEEP-ME` (added at review, F-9): the byte-identity assertion then also detects the template-rebuild data loss that the current dry run causes. Measured at review on the pre-change code: a `--status open --dry-run` dropped `- Custom-Field: KEEP-ME` entirely (`grep -c` went 1 -> 0) while exiting 0. Keep the assertion as BYTE IDENTITY rather than adding a field-specific assertion, so this test does not duplicate or pre-empt plan `2yqt0a`, which owns the renderer fix and depends on this plan.
  - Depends on: E-02
  - Expected outcome: three tests, all passing; (a) and (b) fail on HEAD before E-01/E-02.
  - Execution state: pending

- [ ] E-06 Add tests to `tests/test_specs_status_dirs.py` (the git-initialised fixture that already exercises `specs.run_set` relocation): (a) `cli.main(["specs", "set", <draft-path>, "--status", "to-review", "--dry-run"])` exits 0, the spec is still at `draft/<name>` with identical bytes, `to-review/` gains nothing, `git status --porcelain` is empty, and no `history.jsonl` appears; (b) a `reviewed` spec with `--status approved --dry-run` and no `--by-human`, stdin non-interactive: exit 1, file unchanged; (c) the positional spelling `["specs", "set", "to-review", <id6>, "--dry-run", "--dir", <repo>]` leaves the tree unchanged. FIXTURE PRECONDITION FOR (a), verified at review (PR-004): `SpecStatusDirectoriesTests.setUp` git-inits and mkdirs but does NOT commit, so a spec written in the test body is UNTRACKED and `git status --porcelain` is NON-EMPTY before the command even runs. Copy the `git add -A` + `git commit -m initial` pair that the existing relocation tests in this file already perform after writing their spec, or the assertion fails for a reason unrelated to the fix. Note also that the sidecar is gitignored in THIS repo only via `.aw/.gitignore` (`records/history.jsonl`), which a scratch fixture does not inherit; that is WHY it shows up as `?? .aw/records/history.jsonl` in a scratch repo (measured) and therefore why the empty-`git status` assertion genuinely detects a stray sidecar write rather than being vacuous. Do not add a gitignore to the fixture to make it pass.
  - Depends on: E-04
  - Expected outcome: three tests, all passing; (a) fails on HEAD.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-07 Add one `- Fixed:` line to the `## 2.0.0 (pending)` section of `CHANGELOG.md`: `aw backlog set <item> --status <s> --dry-run` and `aw specs set <spec> --status <s> --dry-run` previously ignored `--dry-run` and performed the change (a spec was even moved to another folder); both now preview only. No em or en dashes.
  - Depends on: E-02, E-04
  - Expected outcome: one new line, user-facing wording, no dashes.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest`, then `python3 -m agent_workflows check plans --agent` and `aw sanitize --agent`.
  - Depends on: E-05, E-06, E-07
  - Expected outcome: 0 failed; no new check or sanitizer finding in touched files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw backlog set` and `aw specs set` fork on `--status` in `cli.main` (the `if getattr(args, "status", None) is None:` branches in the `backlog_cmd == "set"` and `specs_cmd == "set"` dispatch, cli.py ~:13672 and ~:13715): positional goes to `status_set.run_set_command`, `--status` to `backlog.run_set` / `specs.run_set`. Every fix to one setter must be checked against the other spelling.
- The positional path's dry-run handling (`status_set.run_set_command`, `is_dry_run = getattr(args, "dry_run", False)` ~:1959 and `if is_dry_run:` ~:2012) is the reference behavior.
- `record_history.append_advisory` writes the gitignored machine-local sidecar `.aw/records/history.jsonl` (`record_history.history_path`); the inline `## Workflow history` is the durable record (plan `vhbvwz`).
- Tests: outcome only (maintainer standing rule). No test pins source text, docstrings, or function shape.
- Commit via `aw commit wd6npl -- <paths>`; never push. Cite by symbol; line numbers are at HEAD `92679444` and approximate.

## Findings

Authored at HEAD `92679444`. EVERY row F-1 through F-8 was RE-VERIFIED at review HEAD `1aae8813` and all reproduced, including both live reproductions (the backlog rewrite plus sidecar, and the specs `git mv` to another disposition directory under `--dry-run`). F-7 was escalated with new measurement, and F-9/F-10 were added at review.

| # | Location (HEAD 92679444) | Finding |
| --- | --- | --- |
| F-1 | `cli._build_parser`, `p_backlog_set` / `p_specs_set` `"--dry-run"` (~:5057, ~:5374) | Confirmed: both parsers register `--dry-run`; neither registers `--apply`. Measured: `_build_parser().parse_args(["backlog","set","x","--status","open","--dry-run"])` has `dry_run=True` and NO `apply` attribute, so `backlog.run_set`'s `getattr(args, "apply", True)` guard (~:1200) is always True. |
| F-2 | `agent_workflows/specs.py`, `agent_workflows/backlog.py` | Confirmed: `grep -n dry_run` returns nothing in either file. |
| F-3 | scratch repo, measured at authoring | `aw backlog set <path> --status open --dry-run` exited 0, printed `aw backlog set: ... -> open`, rewrote the file (appended a history record, dropped `- Custom-Field:`, reordered `- Graduated-To:`) and created `.aw/records/history.jsonl`. The positional `aw backlog set open abc123 --dry-run` wrote nothing. |
| F-4 | `backlog.run_set` sidecar block (~:1076) vs `evaluate_blocking_close` refusal (~:1180-1191) | BRIEF CLAIM REFINED: the sidecar append precedes not only the write but also the close REFUSAL. Measured: `--status done` on a `Blocks-Release` item with no evidence exited 1 with `refused:` and still created `.aw/records/history.jsonl`. So E-01 moves the sidecar after the refusal as well as after the dry-run gate; a refused close must not log a transition that never happened. |
| F-5 | `specs.run_set` `_sidecar_append` (~:741) vs `validate_spec` residual refusal (~:803) | Same shape: a spec set refused as non-conforming (or by a bad `--graduated-to`) has already appended a sidecar record. E-03 fixes this with the same move. |
| F-6 | `specs.run_set` `core.git_mv` (~:832) and `_offer_specs_set_commit` (~:847) | Confirmed; the dry-run gate (E-04) must precede both. |
| F-7 | `runner_shared` docstring "THE `--status` SPELLING IS DELIBERATE AND LOAD-BEARING (zhr6mc D1)" (~:29117) and measured | The positional spelling does NOT run `check_engine.evaluate_blocking_close`: measured, `aw backlog set done abc123 --yes` closed an item carrying `- Blocks-Release: rel001` with no evidence, exit 0. This is why the backlog item's preferred fix (route both spellings through one implementation) is NOT taken here: routing `--status` through `status_set` would drop the close gate. CONFIRMED AND ESCALATED AT REVIEW, and it is worse than "exit 0" conveys. Re-measured on one scratch repo, same item, both spellings: the `--status` form REFUSED with the three legitimate fixes (exit 1) while `aw backlog set done abc123 --yes` closed it, MOVED it to `done/`, and SELF-COMMITTED the move (`Committed 2 path(s): 8334d048...`). The self-commit is the part that matters, because the documented backstop is STAGED-SCOPED: `check_engine.check_release_gate_consistency` iterates `_staged_backlog_done_items(repo_root)` and deliberately grandfathers history ("only a backlog item whose close-to-`done` is STAGED in THIS commit is examined"). A path that commits its own move therefore leaves NOTHING staged, so `aw check release-gates` on the post-bypass repo reported `CONFORMS, errors 0`. Measured. So for this spelling the gate is unenforced AND the backstop is unreachable, and `mawwlc` owns the fix. | verified at review HEAD `1aae8813`: both spellings driven on one fixture; `aw check release-gates` after the bypass reports `CONFORMS` |
| F-8 | `.aw/records/backlog/open/20260921-19lmbe-01-19lmbe-backlog-set-status-ignores-dry-run.backlog.md` | NOT IN THE BRIEF: item `19lmbe` (bug, high, `Blocks-Release: next`) is a DUPLICATE of the backlog half of `bxi1o0`. This plan fixes it too; the gate section tells the executor to close it with evidence. CONFIRMED at review: `19lmbe` is genuinely the same defect (its own text says it fired on a reviewer during `/plan-review` of `yv4tb1` and silently closed item `6h7y2y` from `graduated` to `done`), and both it and `bxi1o0` carry `- Blocks-Release: next`, so BOTH need a legitimate close. Note the closes must satisfy `evaluate_blocking_close` (handoff, evidence, or de-gate); a bare `aw backlog set done` on the POSITIONAL spelling would appear to succeed while enforcing nothing (F-7), so use the `--evidence` form the gate reads. |
| F-9 (ADDED at review) | `backlog._render_item` reached via the same `run_set` this plan edits | **A DRY RUN TODAY ALSO SILENTLY DROPS UNRECOGNIZED FIELDS, AND THAT IS A SECOND PLAN'S CONCERN ON THE SAME FUNCTION.** In the review reproduction the `--dry-run` write did not merely rewrite the item: it DELETED `- Custom-Field: KEEP-ME` (measured: `grep -c Custom-Field` went 1 -> 0). That data loss is owned by plan `2yqt0a` (Set `rendrop`, from backlog `f2kqas`), which declares `agent_workflows/backlog.py` and `tests/test_backlog.py` and whose `- Item-Dependencies:` is `executed:wd6npl`, i.e. it waits on THIS plan. Recorded because it strengthens this plan's priority (the ignored `--dry-run` is the delivery vehicle for an unrelated data-loss bug) and because it identifies the real ordering: this plan first, then `2yqt0a`. | scratch repro: `Custom-Field` count 1 -> 0 after `--status open --dry-run`; `2yqt0a` front matter read |
| F-10 (ADDED at review) | this plan's own gate, "Genuine stop condition" | **THE NAMED DEPENDENT PLAN ID IS A BACKLOG ID, NOT A PLAN ID.** The gate says "plan `rendrop` / f2kqas depends on this one and edits `backlog.run_set` next". `f2kqas` is the BACKLOG ITEM (`.aw/records/backlog/graduated/20260923-rendrop-01-f2kqas-...backlog.md`); the plan that graduated from it and declares `- Item-Dependencies: executed:wd6npl` is `2yqt0a`. An executor checking for a concurrent editor would search for a plan that does not exist under that id. | `find`/`grep` over the records tree: `f2kqas` resolves only to a backlog item; `2yqt0a` is the plan and declares the dependency |

## Proposed changes (ordered, validatable)

1. E-01, E-02: backlog sidecar move plus dry-run gate.
2. E-03, E-04: specs sidecar deferral plus dry-run gate before `git mv` / write / commit offer.
3. E-05, E-06: outcome tests through `cli.main` for both spellings.
4. E-07: CHANGELOG line. E-08: suite, check, sanitizer.

## Deferred / out of scope (with reason)

- Collapsing the two spellings of `aw backlog set` / `aw specs set` into one implementation (the backlog item's option 1).
  - Carrier-Declined: the maintainer's brief for this plan chose the explicit gate; unification cannot be done safely until the positional path enforces the close gate (F-7), and E-05(c)/E-06(c) already assert both spellings agree on `--dry-run`, which is the item's option 2 for this flag.
- The positional spelling skipping `evaluate_blocking_close` (F-7), a separate live defect.
  - Carrier-Declined: outside this plan's fix. STATUS UPDATED AT REVIEW: it no longer needs a verbal hand-off, because it IS ALREADY FILED as backlog item `mawwlc` (`.aw/records/backlog/open/20260926-gatebypass-01-mawwlc-positional-done-skips-release-gate.backlog.md`, `bug`/`high`/`Blocks-Release: next`, Set `gatebypass`), whose text credits this plan's author for confirming it and already prescribes the fix (call `check_engine.evaluate_blocking_close` on the positional path, with an outcome test that both spellings refuse the same gated close). So the correct deferral is "owned by `mawwlc`", and the authoring-report route is obsolete. Reference it rather than re-reporting it.
- The remaining machine-output shape of a dry run under `--agent` / `--json` on the `--status` path (it prints the plain would-move line, as the existing `apply=False` branch already did).
  - Carrier-Declined: preview output shape is not the defect; the defect is the write, and no consumer of a structured dry-run record on this path exists.

## Scope check

- Over-scope: F-4/F-5 widen the change from "gate before write" to "no sidecar on any refusal"; same lines, same concern (a record of a transition that did not happen). Confirmed reasonable at review: both refusals were measured to write the sidecar, so this is the same defect class rather than added scope.
- Under-scope: none known. The `apply` fallback is kept so existing direct callers in `tests/test_backlog.py` that pass `apply=True` are unaffected. VERIFIED at review: `tests/test_backlog.py` has many `apply=True` call sites, so dropping the fallback would break them; keeping it is correct.
- Adjacent plan, checked at review: `2yqt0a` (Set `rendrop`) declares `agent_workflows/backlog.py` and `tests/test_backlog.py` too, and carries `- Item-Dependencies: executed:wd6npl`, so it is ORDERED AFTER this plan and is not a concurrency hazard under the runner (which re-checks dependencies at dispatch and isolates each item in its own lane). File overlap only.

## Required tests / validation

Outcome tests only (maintainer standing rule): each asserts what an operator observes (exit code, file bytes, directory listing, sidecar presence, `git status`), never source text or function shape. Six tests total across `tests/test_backlog.py` and `tests/test_specs_status_dirs.py`, driven through `cli.main` so the real argparse wiring is exercised (the bug lived in the wiring). Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended: no spec describes the `--dry-run` behavior of these two setters (the flag's own help text, "Preview without writing.", already states the intended contract, which this plan makes true). `CHANGELOG.md` gains one `Fixed:` line (E-07).

## Open questions

### OQ-01: Explicit gate in both setters, or route both spellings through one implementation?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Explicit gate, per the maintainer's brief for this plan. Repository evidence supports it: the positional `status_set` path does not run the release-gate close predicate (F-7, measured, and documented in `runner_shared` as the reason the runner uses `--status`), so unifying now would trade this bug for a release-gate bypass. The fork is guarded for this flag by E-05(c) and E-06(c).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: in a scratch repo with an item carrying `- Blocks-Release:` of a planned release, paste `aw backlog set <path> --status done; echo rc=$?; ls .aw/records/history.jsonl` showing `rc=1`, the `refused:` line, and `No such file or directory`. Then paste a real `--status parked` run showing `rc=0` and `wc -l .aw/records/history.jsonl` reporting `1`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `sha256sum <item>` before and after `aw backlog set <item> --status open --dry-run --dir <repo>; echo rc=$?`, showing identical hashes, `rc=0`, the `--- would move` line, and `git status --porcelain` empty.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a scratch run of `aw specs set <draft-spec> --status to-review --graduated-to 'BAD SET'; echo rc=$?` showing `rc=2` and no `.aw/records/history.jsonl`; then a real `--status to-review` run and `wc -l .aw/records/history.jsonl` reporting `1`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `find .aw/records/specs -name '*.spec.md'` before and after `aw specs set <draft-spec> --status to-review --dry-run; echo rc=$?`, identical listings, `rc=0`, the `--- would move` line, and empty `git status --porcelain`. Then paste `aw specs set <reviewed-spec> --status approved --dry-run < /dev/null; echo rc=$?` showing `rc=1` and the `human-only transition` message.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_backlog.py -o addopts="" -q -k dry_run` showing 3 passed, AND the same tests shown FAILING against the pre-change code for (a) and (b), proving they detect the bug. PREFER AN IN-TREE METHOD (revised at review, PR-006): temporarily revert the E-01/E-02 hunks in place (or `git stash` them), re-run, paste the failures, restore, re-run green. Do NOT create a git worktree outside this workspace: an execute turn runs in an isolated lane whose directory is its complete authorized workspace, so `git worktree add /tmp/...` writes outside it and also registers a worktree in the shared object store that the lane teardown does not own. If a separate checkout is genuinely wanted, place it INSIDE the lane (for example `.aw/tmp-basecheck/`, removed afterwards) and say so.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_specs_status_dirs.py -o addopts="" -q -k dry_run` showing 3 passed, plus evidence that (a) fails without E-04 (same in-tree method as V-05; no out-of-lane worktree). Also confirm (a) is not passing for the wrong reason: paste the `git status --porcelain` the test asserts on, so a non-empty status caused by an uncommitted fixture spec (PR-004) is visibly excluded.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` line under `## 2.0.0 (pending)`, and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed (name any failure as pre-existing with its node id and evidence it fails at the base commit), plus the exit code of `python3 -m agent_workflows check plans --agent` and of `aw sanitize --agent`, both 0 or with no finding naming a touched file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one defect (an ignored `--dry-run`) in two forked setters that share the same structure; the sidecar move is the same edit site and the same concern (never record a transition that did not happen).

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a behavior fix to two record setters (dry runs stop writing; refused transitions stop logging to the sidecar), six outcome tests, one CHANGELOG line. No spec change, no public flag change.

WHAT THE REVIEW CONFIRMED, because this plan's claims are unusually consequential. Both halves of the defect were reproduced live at review HEAD `1aae8813`: `aw backlog set <path> --status open --dry-run` exited 0 and REWROTE the item (also silently dropping an unrecognized `- Custom-Field:`, F-9) and created `.aw/records/history.jsonl`; `aw specs set <path> --status to-review --dry-run` exited 0 and `git mv`'d the spec from `draft/` to `to-review/`. Both refusal paths were confirmed to write the sidecar before refusing (F-4, F-5). So the defect, its blast radius, and the sidecar-on-refusal widening are all measured, not argued. F-7 was ESCALATED: the positional spelling not only skips the release-gate close predicate but SELF-COMMITS its move, and because the documented backstop `check.blocking-item-closed-without-gate` is deliberately STAGED-SCOPED, a post-bypass `aw check release-gates` reports `CONFORMS, errors 0`. That defect is NOT this plan's to fix and is already filed as backlog `mawwlc`; it is named here only so the approving human knows the adjacent hole exists and that this plan deliberately does not widen into it.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `backlog.py` only `run_set`, within `specs.py` only `run_set`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to `backlog.run_set` or `specs.run_set` that cannot be safely combined. THE PLAN TO WATCH IS `2yqt0a` (Set `rendrop`), not `f2kqas`, which is its BACKLOG item and not a plan (id corrected at review, F-10); `2yqt0a` declares `agent_workflows/backlog.py` plus `tests/test_backlog.py` and carries `- Item-Dependencies: executed:wd6npl`, so it waits on THIS plan and should not be running concurrently. If it somehow is, that edge is the thing to stop on.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit wd6npl -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize wd6npl --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from `bxi1o0`; after execution set `bxi1o0` `done` with `--evidence` citing the executed plan, and ALSO set duplicate item `19lmbe` `done` with the same `--evidence` (F-8). BOTH carry `- Blocks-Release: next`, so both closes must satisfy `evaluate_blocking_close`: use the `--status done ... --evidence <path>` form, which runs the gate, NOT the positional `aw backlog set done <id6>`, which does not (F-7) and would appear to succeed while enforcing nothing.
