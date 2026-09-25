# IPD: Agent-side comms ack writing and per-message status aggregation

- Date: 2026-09-24
- Kind: child
- Concern: The ack FORMAT exists (`comms.ACK_STATES`, `comms.AGENT_ACK_STATES`, `comms.ACK_WRITER`, `comms.validate_ack`, `comms.ack_filename`) but nothing writes an agent ack and nothing answers "what is the state of message X?". `comms.validate_ack` says so itself: it "does NOT enforce authorized-writer (that needs the caller's identity, which the broker/agent supply in IPDs 2/3)". Backlog `0gd5w6` ("agent-comms IPD 3: agent-side ack writing + per-message status aggregation (depends on the broker)") is that half. Child 01 (`nomhl1`) writes the broker-side acks this plan aggregates.
- Scope: IN: a new stdlib-only module `agent_workflows/comms_acks.py`, agent-agnostic (usable by any agent, not only OpenCode), run as `python3 -m agent_workflows.comms_acks ack <msg-id> <state> --by <proj.agent>` and `python3 -m agent_workflows.comms_acks status [<msg-id>] [--format json]`; a one-paragraph addition to the installed comms README telling a target agent how to acknowledge; correcting the spec's stale ack path. OUT: any broker change, an `aw comms` CLI verb, surfacing comms in `aw attention`, and treating any ack as proof (the spec forbids it).
- Scope-Paths: agent_workflows/comms_acks.py, tests/test_comms_acks.py, agent_workflows/engine.py, .aw/records/comms/README.md, .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Item-Dependencies: executed:nomhl1
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: 0gd5w6
- Set: commsbroker
- Order: 3
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ozcfjr

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 0gd5w6; re-measured that `comms.py` ships the ack enum, writer table and validator with no writer or reader anywhere in `agent_workflows/` or `tests/`, and that the spec still names the pre-rename `local/acks/` path.

## Goal

Let a target agent record, as closed-enum metadata only, that it read or worked a message, and let anyone see one derived status per message, without ever turning an agent's claim into proof.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: writer

- [ ] E-01 Add `comms_acks.write_agent_ack(comms_dir, msg_id, state, by, now)`: refuse unless `comms.ack_writer_for(state) == "agent"` (so an agent can never write `delivered` or any broker state), `msg_id` and `by` pass `comms.is_filename_safe`, and the message exists in `untracked/inbox/`, `shared/inbox/` or `untracked/archive/`. Build `{"re", "state", "by", "at"}`, require `comms.validate_ack` to return no problems, and write `untracked/acks/<comms.ack_filename(msg_id, by, state)>` atomically (temp file then `os.replace`). Idempotent: an existing identical-name ack is left as is.
  - Depends on: none
  - Expected outcome: a writer that can only emit `AGENT_ACK_STATES` for a real message.
  - Execution state: pending
- [ ] E-02 Add `comms_acks.message_status(comms_dir, msg_id)` returning `{"msg_id", "delivery", "work", "unread", "acks"}`: `delivery` is the newest (by `at`) valid broker-state ack, `work` the newest valid agent-state ack, and `unread` is True exactly when a `delivered` ack exists and no `read`-or-later agent ack does (the spec: "`unread` is NOT a token: it is the ABSENCE of a `read` ack after `delivered`"). Invalid ack files, and any ack whose state's writer does not match its layer, are listed under `acks` with a `problem` and never counted. With no broker, `delivery` is None and `unread` is False, so the view degrades rather than fails.
  - Depends on: E-01
  - Expected outcome: one derived status per message; a forged broker-layer `read` is reported, not counted.
  - Execution state: pending
- [ ] E-03 Add the `__main__` entry with `ack` and `status` subcommands (`status` with no msg-id lists every inbox message; `--format json` emits the dicts), resolving the comms dir the same way `comms_broker` does. `ack` exits 2 on any refusal and writes nothing.
  - Depends on: E-02
  - Expected outcome: `python3 -m agent_workflows.comms_acks --help` lists both subcommands.
  - Execution state: pending

### Task group 2: docs, tests, spec, suite

- [ ] E-04 Add one paragraph to `engine._COMMS_README_TEMPLATE` under "## Acknowledgements", and the same paragraph to this repo's installed `.aw/records/comms/README.md`: after reading a message, a target agent MAY run `python3 -m agent_workflows.comms_acks ack <msg-id> read --by <proj.agent>` (and later `done`/`executed`/etc.), and acks are optional because the convention works without them.
  - Depends on: E-03
  - Expected outcome: the template and the installed copy carry the same new paragraph.
  - Execution state: pending
- [ ] E-05 Write `tests/test_comms_acks.py` (tmp dirs, no network): agent writing `delivered` refused; unknown msg-id refused; unsafe `by` refused; valid `read` written and passes `comms.validate_ack`; `status` gives `unread` True after a broker `delivered` ack and False after `read`; a hand-planted invalid ack is reported with a problem and not counted; no broker acks gives `delivery` None.
  - Depends on: E-04
  - Expected outcome: all pass; the writer-refusal test fails under the mutation named in V.
  - Execution state: pending
- [ ] E-06 Amend the spec: correct the ack path from `.agents/comms/local/acks/` to the `untracked/acks/` lane (the layout block already says `untracked/ ... acks/`), add a short "Agent acks and status" subsection naming `comms_acks` and the derivation rules, remove agent-side ack writing from the Deferred list, and append a `## Workflow history` note line.
  - Depends on: E-05
  - Expected outcome: the spec's ack path agrees with its own layout block and with `comms.ack_filename`'s docstring.
  - Execution state: pending
- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The installed comms README is `engine._COMMS_README_TEMPLATE`, written by `engine` into `{dirs['comms']}/README.md`. The repo's own copy differs from the template by 3 bytes today (measured: 2220 vs 2223 characters), so E-04 edits both by hand rather than regenerating.
- Stdlib only; runtime dependencies are `dependencies = ["filelock>=3"]`.

## Findings

- F-1: no reader or writer of `comms.validate_ack`, `comms.ack_filename` or `comms.ACK_WRITER` exists outside `comms.py` (grep of `agent_workflows/` and `tests/`).
- F-2: the spec's Acknowledgements section still reads "`.agents/comms/local/acks/<msg-id>.<from-agent>.<state>.json`" while its layout block and `comms.ack_filename`'s docstring say `untracked/acks/` (the `local/` lane was renamed, commit "fix(untracked): retire the last live local/ lane refs"). E-06 fixes the stale string.
- F-3: `tests/test_comms.py`, which plan `ssmov3` created, no longer exists (removed in "test: trim test suite from 9,136 to under 2,000 tests"), so the ack helpers are currently untested; E-05 restores coverage for the parts this plan consumes.
- F-4: the dependency on child 01 is on the broker ack LAYER, which the aggregation reads; the writer itself would work without a broker.

## Proposed changes (ordered, validatable)

1. Agent ack writer (E-01), status aggregation (E-02), entry point (E-03).
2. README paragraph (E-04), tests (E-05), spec correction and amendment (E-06), bare suite (E-07).

## Deferred / out of scope (with reason)

- Surfacing unread or unanswered comms in `aw attention`: comms records have no lifecycle status today and adding one is a cross-cutting attention change.
  - Carrier-Declined: Separate design question; file a backlog item if the status view proves useful.
- An `aw comms` CLI family: would require `command_surface` declarations and conformance-matrix coverage.
  - Carrier-Declined: Surface choice, not an obligation; the module entry points keep this opt-in and small.
- Authenticating the `by` field: it is self-asserted, exactly as the comms sender identity is.
  - Carrier-Evidence: .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md

## Scope check

- Over-scope: `agent_workflows/engine.py` is touched ONLY for the `_COMMS_README_TEMPLATE` paragraph. Do not change `create_setup_artifacts` or any other installer logic.
- Under-scope: if an installer or packaging test pins the README template text, updating that test's expected text is in scope; declare its path before editing.

## Required tests / validation

- `tests/test_comms_acks.py` targeted, plus a mutation run showing the writer-refusal test FAILS.
- `python3 -m pytest` bare with the summary line pasted.

## Spec / documentation sync

- Amends `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` (declared in `- Scope-Paths:`): the stale `local/acks/` path is a live contract error (F-2), and the Deferred list would otherwise still name shipped work.
- Updates the installed comms README template and this repo's copy (E-04).

## Open questions

### OQ-01: Should a target agent be required, rather than permitted, to write a `read` ack?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: permitted only. The spec says the convention "MUST work fully WITH OR WITHOUT any broker", and a mandatory ack would add a step to every non-OpenCode agent; the README paragraph says MAY.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_comms_acks.py -k write -v` showing PASSED for broker-state refused, unknown msg refused, unsafe `by` refused, and valid `read` written.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `-k status` run showing PASSED for unread-after-delivered, not-unread-after-read, invalid ack reported not counted, and no-broker delivery None.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m agent_workflows.comms_acks --help`, and an `ack` of state `delivered` in a tmp repo exiting 2 (`echo $?`) with `ls untracked/acks/` empty.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- agent_workflows/engine.py .aw/records/comms/README.md` showing the same paragraph added to both and no other change in `engine.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest -o addopts="" tests/test_comms_acks.py` summary, then the same run with the `ack_writer_for(state) == "agent"` check locally removed, showing the broker-state-refused test FAILED; revert and show the file matches the intended version.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `grep -n "local/acks" .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` returning nothing, and the spec diff showing the new subsection and note line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line (`N passed`, 0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-01 is `Blocking: no` with a stated default. This plan is `to-review`, depends on `nomhl1` being executed, and requires explicit human approval before execution. The executor commits only the `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never pushes, and pastes actual runner output. On completion `aw ipd lint --phase pre-transition` must conform before the terminal transition, owned by the runner in a managed lane and otherwise by `aw ipd finalize`.
