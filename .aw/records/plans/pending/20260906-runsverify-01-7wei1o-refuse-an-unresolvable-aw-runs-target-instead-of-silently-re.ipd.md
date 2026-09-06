# IPD: Refuse an unresolvable aw runs target instead of silently reporting success

- Date: 2026-09-06
- Kind: child
- Concern: `aw runs <token>` treats any first positional that is not a registered leaf name as a run-id/setid/substring TARGET. When that token resolves to nothing it is silently dropped and the command still exits 0, so a mistyped or not-yet-built subcommand reports success having done nothing. The measured case that matters: `aw runs verify <run-id>` renders an ordinary report and exits 0 while verifying nothing, and until 2026-09-05 the spec and seven shipped recovery messages told operators to run exactly that.
- Scope: Make an unresolvable target a nonzero refusal that names the registered leaves and the closest match, while preserving every currently-working invocation (a real run id, a setid, a bare `aw runs`, the viewer flags, the `--` escape hatch, and a legitimate leaf-name collision).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_viewer.py, tests/test_run_viewer.py, tests/test_cli_conformance_matrix.py
- Item-Dependencies: none
- Status: to-review
- Set: runsverify
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7wei1o
- From-Backlog: 6kq1lj
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `6kq1lj`, inheriting its `Blocks-Release: next` gate. Every claim below was measured at HEAD `63107a76` WITHOUT a shell pipe, because a piped `$?` reports the last pipeline stage and that exact mistake produced a false sibling finding in `zrzfkw` (corrected in `63107a76`). Measured: `aw runs verify <run-id>` exits 0 and prints the normal report; `aw runs totalgibberish` exits 0 and prints `no matching runs found`; `aw runs totalgibberish <real-run-id>` exits 0 and prints the real run's report with the bogus token silently dropped, which is the worst variant because the operator sees plausible output. Confirmed still-correct behavior that must not regress: a real run id, a setid (`lanectn`), and `--last` all exit 0 today.

## Goal

Make a wrong `aw runs` invocation fail loudly instead of looking like it worked. The specific harm is that an operator (or an agent following a recovery message) asks for an integrity check, receives a normal-looking report and a success exit, and reasonably concludes nothing is wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detect the unresolvable case

- [ ] E-01 In the `aw runs` viewer path, determine per-token whether each requested target RESOLVED to at least one run, and treat "one or more requested tokens resolved to nothing" as a distinct condition from "no targets were requested". `resolve_target_runs` (`run_viewer.py:1095`) currently returns only the union of matches, so an unmatched token is indistinguishable from an absent one by the time the caller sees the result. Return or expose the unresolved token list rather than re-deriving it in the caller, so one function owns the answer.
  - Depends on: none
  - Expected outcome: the caller can name exactly which requested tokens matched nothing, and a bare `aw runs` (no tokens) remains a distinct, non-error case.
  - Execution state: pending

- [ ] E-02 Make the unresolvable case exit NONZERO with a message that names the unresolved token, the registered leaves, and the closest leaf match when there is one (`verify` -> `verify-ledger` is a one-edit suggestion and is the case that motivated this plan). Use the existing invalid-invocation exit code rather than inventing one: `run_cli.EXIT_INVALID_INVOCATION` is 2 (`run_cli.py:58`) and `aw runs verify-ledger <absent>` already exits 2 for the analogous "cannot do what you asked" case, so 2 keeps the surface coherent.
  - Depends on: E-01
  - Expected outcome: `aw runs verify <run-id>` and `aw runs totalgibberish` both exit 2 with an actionable message; the message is printed to stderr so it does not pollute a parsed report on stdout.
  - Execution state: pending

### Task group 2: do not break what works

- [ ] E-03 Preserve every currently-working invocation, verified individually rather than assumed: a real run id; a setid (`lanectn` resolves today); a bare `aw runs` with no positionals (means "all runs", must stay exit 0 even when the repository has zero runs, since an empty repository is not an error); every viewer flag (`--last`, `--issues`, `--latest-only`, `--since`, ...); and the `--` escape hatch (`aw runs -- status` means the TARGET named `status`, handled pre-parse in `_dispatch` at `cli.py:10579`). Also preserve the documented AMBIGUITY RULE at `cli.py:652-657`: a first positional equal to a leaf name routes to the LEAF, and the escape hatch is the only way to reach a same-named target. Do NOT invert that precedence while adding the refusal.
  - Depends on: E-02
  - Expected outcome: each listed invocation behaves exactly as it does at `63107a76`, demonstrated case by case.
  - Execution state: pending

- [ ] E-04 Decide and implement the MIXED case deliberately, and state the choice in the message: `aw runs totalgibberish <real-run-id>` currently prints the real run and exits 0, silently dropping the bogus token. That is the most misleading variant. Refuse it (nonzero, naming the unresolved token) rather than rendering a partial result, because a partially-honored request that looks complete is the defect this plan exists to remove. If the executor concludes partial rendering plus a nonzero exit is better, that is acceptable ONLY if the unresolved token is named prominently on stderr; silently dropping it is not.
  - Depends on: E-02
  - Expected outcome: a mixed invocation cannot exit 0; the unresolved token is always named.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Test the whole matrix, and measure exit codes WITHOUT a pipe (`cmd >/dev/null 2>&1; echo $?`), because a piped `$?` reports the last pipeline stage and that error produced a false finding in this very Set. Cover: the motivating case (`runs verify <id>` -> nonzero); a wholly unknown token; the mixed case; each preserved case from E-03 including the empty-repository bare call; the escape hatch; and a leaf-name collision if one can be constructed in a fixture (none exists in the repo today per `cli.py:654`, so construct it rather than skip it). Assert the message NAMES the unresolved token, so a future refactor cannot degrade it to a bare exit code.
  - Depends on: E-03, E-04
  - Expected outcome: the refusal and every preserved behavior are pinned by tests, with exit codes measured unpiped.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` carries two shapes at once and argparse cannot express that, so `_ViewerOrLeafSubParsersAction` (`cli.py:623`) disambiguates explicitly: first token in `self._name_parser_map` routes to the leaf (`:672`), otherwise the whole list goes to the sibling viewer parser (`:676-682`). That single branch is the seam this plan changes.
- The nine viewer leaves are enumerated in `_RUNS_VIEWER_LEAVES` (`cli.py:1678-1690`): `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger`. Read the set rather than hardcoding a second copy, or the suggestion text will drift from the registration.
- Exit-code vocabulary already exists in `run_cli.py:46-62`; reuse `EXIT_INVALID_INVOCATION` (2) rather than adding a code. Note the spec's own exit table conflicts with this shipped one above 3 (recorded as an unreconciled conflict in spec `25kzda` Section 5.7 on 2026-09-05); this plan stays inside the shipped vocabulary and does not attempt that reconciliation.
- `_RunsTargetsPlaceholderAction` (`cli.py:685`) exists because a blind `setattr` erased resolved targets once already. Any change to target handling must not reintroduce that.
- MEASURE EXIT CODES UNPIPED. `cmd | head` reports `head`'s status. This repository already lost one finding to that mistake (`zrzfkw`, corrected 2026-09-06).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The routing branch has no third outcome: it is leaf-or-viewer, so an unknown token is a target by construction. | `cli.py:672-682` |
| F-2 | An unresolvable token exits 0. Measured unpiped: `aw runs totalgibberish` -> exit 0, prints `no matching runs found`. | measured at `63107a76` |
| F-3 | The motivating case exits 0 with plausible output: `aw runs verify <run-id>` -> exit 0, renders the full run report. | measured at `63107a76` |
| F-4 | The mixed case is worst: `aw runs totalgibberish <real-id>` -> exit 0, prints the real run, bogus token silently dropped. | measured at `63107a76` |
| F-5 | Not hypothetical. Until 2026-09-05 the spec documented `aw runs verify <run-id>` and seven shipped recovery messages in `run_evidence.py` told operators to run it, precisely when a ledger might be corrupt. Those strings are now corrected, but the fail-open path they pointed at is still open. | commit `98a0beed` |
| F-6 | The analogous honest case already exists and exits 2, so a nonzero refusal is consistent rather than novel: `aw runs verify-ledger <absent-ledger>` -> exit 2. | measured at `63107a76` |
| F-7 | Behavior that must be preserved, each measured exit 0 today: real run id, setid `lanectn`, `--last`. | measured at `63107a76` |

## Proposed changes (ordered, validatable)

1. Expose which requested tokens resolved to nothing (E-01).
2. Refuse that case nonzero with an actionable, leaf-naming message (E-02).
3. Preserve every working invocation, case by case (E-03).
4. Decide the mixed case deliberately and never drop a token silently (E-04).
5. Pin the matrix with unpiped exit-code assertions (E-05).

## Deferred / out of scope (with reason)

- Whether driver runs should WRITE a `ledger.jsonl` at all. That is the remaining half of backlog `zrzfkw` and a genuine design question touching tamper-evidence and ownership attribution; it is independent of this refusal.
- Renaming either sense of "ledger" (the drivers' `events.jsonl` versus the hash-chained `ledger.jsonl`). Tracked in `zrzfkw`; cosmetic and separable.
- Auditing every other `aw` verb for the same fail-open shape. Worth doing, but a sweep is a different plan; this one fixes the measured instance and its immediate siblings under `aw runs`.
- Reconciling the spec's exit-code table with the shipped one. Recorded as an unreconciled conflict in spec `25kzda` on 2026-09-05 and explicitly left there.

## Scope check

- Over-scope: none. One CLI module, one viewer module, two test modules.
- Under-scope: does not make `verify-ledger` able to verify a driver run (nothing writes the file), and does not sweep other verbs. Both are correct exclusions and named above.

## Required tests / validation

- `python3 -m pytest` bare, full suite, before and after, with counts stated.
- Targeted: `tests/test_run_viewer.py`, `tests/test_cli_conformance_matrix.py`.
- A live matrix of unpiped exit codes for every case in E-05, pasted as evidence.
- NOTE for the executor: `tests/test_run_viewer.py` reads run directories from `.aw/records/runs/`, which is gitignored. The module fails 14/42 in a bare worktree and passes 42/42 in the real checkout (measured 2026-09-05). Validate in the real checkout; a green run elsewhere proves nothing.

## Spec / documentation sync

Spec `25kzda`'s header already records (amended 2026-09-05) that `aw runs verify <run-id>` names no leaf and that the spelling exits 0 having verified nothing, citing backlog `6kq1lj`. When this plan lands, that note should be updated to say the spelling now REFUSES. Do that in the same pass, since leaving it would make the spec understate the fix. Update `_RUNS_DESCRIPTION`/`_RUNS_EPILOG` help text only if the refusal makes the existing wording inaccurate.

## Open questions

### OQ-01: Should a bare `aw runs` in a repository with zero runs be an error?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, it must stay exit 0. A repository with no runs is a legitimate healthy state, not a failed request, and the same reasoning already governs the `reviews` status selector, whose empty result spec `25kzda` Section 2.4a makes a SUCCESS rather than a zero-match error. The distinction this plan draws is between "you asked for something specific that does not exist" (an error) and "you asked for everything and there is nothing" (not an error).

### OQ-02: Should the refusal apply to a token that is a valid-looking run id for a run that was deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and no special case is warranted. From the operator's position "this run id does not resolve" is the same failure whether the id was mistyped or the run directory was removed, and both deserve a nonzero exit naming the token. Attempting to distinguish them would require guessing intent from the token's shape, which is exactly the kind of inference this repository rejects elsewhere (see the fail-open prohibition recorded in backlog `d07nz2`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolver's output for three inputs showing unresolved tokens are reported distinctly: one real id, one bogus token, and both together. Show that a bare call (no tokens) is distinguishable from "all tokens unresolved".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste UNPIPED exit codes and the stderr message for `aw runs verify <real-run-id>` and `aw runs totalgibberish`, using `cmd >/dev/null 2>&1; echo $?` for the code and a separate run for the text. Both must be nonzero, and the message must name the unresolved token and suggest `verify-ledger` for the `verify` case.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste UNPIPED exit codes for each preserved case: a real run id, the setid `lanectn`, bare `aw runs`, `--last`, and `aw runs -- status`. All must match their `63107a76` behavior. This is the anti-regression item; a nonzero here on a formerly-working invocation is a failed execution, not a pass.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the UNPIPED exit code and full output for `aw runs totalgibberish <real-run-id>`, showing the unresolved token is named and the exit is nonzero. State which rendering choice was implemented and why.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL output of the two targeted test modules and of the bare full suite with the `N passed` summary line, state before/after counts, and name the test that pins the message text. Confirm the run was in the real checkout, not a bare worktree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). The executor must commit ONLY the four paths in Scope-Paths, path-scoped, and must never push. Tests must be RUN and their actual output pasted into `Observed evidence`; a `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

TWO WARNINGS FOR THE EXECUTOR. FIRST, V-03 is the item that matters most: this change can only fail in one direction, by refusing an invocation that used to work. If any preserved case cannot be shown green, stop and report rather than proceeding. SECOND, measure every exit code UNPIPED; a piped `$?` reports the last pipeline stage, and that mistake already produced one false finding in this Set (`zrzfkw`, corrected 2026-09-06).

This plan does NOT touch `oc_runipd.py` or `agy_runipd.py`, so it does not collide with the `verifygap` Set or the four approved `orchretire` plans and may run alongside them.

On completion, close backlog `6kq1lj`, which this plan carries as `- From-Backlog:`.
