# IPD: Agent-side comms ack writing and per-message status aggregation

- Date: 2026-09-24
- Kind: child
- Concern: The ack FORMAT exists (`comms.ACK_STATES`, `comms.AGENT_ACK_STATES`, `comms.ACK_WRITER`, `comms.validate_ack`, `comms.ack_filename`) but nothing writes an agent ack and nothing answers "what is the state of message X?". `comms.validate_ack` says so itself: it "does NOT enforce authorized-writer (that needs the caller's identity, which the broker/agent supply in IPDs 2/3)". Backlog `0gd5w6` ("agent-comms IPD 3: agent-side ack writing + per-message status aggregation (depends on the broker)") is that half. Child 01 (`nomhl1`) writes the broker-side acks this plan aggregates.
- Scope: IN: a new stdlib-only module `agent_workflows/comms_acks.py`, agent-agnostic (usable by any agent, not only OpenCode), run as `python3 -m agent_workflows.comms_acks ack <msg-id> <state> --by <proj.agent>` and `python3 -m agent_workflows.comms_acks status [<msg-id>] [--format json]`; a one-paragraph addition to the installed comms README telling a target agent how to acknowledge; correcting the spec's stale ack path. OUT: any broker change, an `aw comms` CLI verb, surfacing comms in `aw attention`, and treating any ack as proof (the spec forbids it).
- Scope-Paths: agent_workflows/comms_acks.py, tests/test_comms_acks.py, agent_workflows/engine.py, .aw/records/comms/README.md, .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Item-Dependencies: executed:nomhl1
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: 0gd5w6
- Set: commsbroker
- Order: 3
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ozcfjr
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED (PR-002 BLOCKER: mixed-offset ack at raises TypeError); review record written

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED. PR-001 (uncarriered OQ, `check.ipd-uncarried-obligation` at `error`), PR-002 (BLOCKER: measured that `comms.validate_ack` accepts BOTH an offset-aware and an offset-naive `at`, so "newest by `at`" raises `TypeError` on a legitimately mixed acks dir and the status view crashes), PR-003 (an ack filename is not re-splittable - `ack_filename("m.a","b",s)` and `ack_filename("m","a.b",s)` collide - and `is_filename_safe` permits glob metachars, so acks must be selected by the `re` field), PR-004 (claimed to detect a forged broker-written `read`, impossible with one shared `acks/` lane and a self-asserted `by`), PR-005 (`read`-or-later not derivable: `AGENT_ACK_STATES` index puts `not-done` below `executed` and no ordering constant exists), PR-006 (a SECOND stale `local/inbox/` in the spec that `grep local/acks` misses, plus a forbidden hand-edit of spec history), PR-007 (crash on a fresh clone with no `untracked/` lane), PR-008 (gate carried almost no execution contract) all FIXED. Findings in `.aw/records/reviews/20260924-commsbroker-03-ozcfjr-agent-side-comms-ack-writing-and-per-message-status-aggregat.review.md`. Readiness go-pending-approval.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 0gd5w6; re-measured that `comms.py` ships the ack enum, writer table and validator with no writer or reader anywhere in `agent_workflows/` or `tests/`, and that the spec still names the pre-rename `local/acks/` path.

## Goal

Let a target agent record, as closed-enum metadata only, that it read or worked a message, and let anyone see one derived status per message, without ever turning an agent's claim into proof.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: writer

- [ ] E-01 Add `comms_acks.write_agent_ack(comms_dir, msg_id, state, by, now)`: refuse unless `comms.ack_writer_for(state) == "agent"` (so an agent can never write `delivered` or any broker state), `msg_id` and `by` pass `comms.is_filename_safe`, and the message exists in `untracked/inbox/`, `shared/inbox/` or `untracked/archive/`. Build `{"re", "state", "by", "at"}`, require `comms.validate_ack` to return no problems, and write `untracked/acks/<comms.ack_filename(msg_id, by, state)>` atomically (temp file then `os.replace`). Idempotent: an existing identical-name ack is left as is.
  - WRITE A TIMEZONE-AWARE UTC `at`, and make that the module's ONLY spelling. `now` defaults to `datetime.now(timezone.utc)` and `at` is its `.isoformat()`, so every ack THIS module writes is offset-aware. This is the write half of the normalization E-02 must do on read (E-02 still has to normalize, because the broker and hand-written acks are not bound by this rule).
  - CREATE THE LANE; DO NOT ASSUME IT. `untracked/acks/` does NOT exist in a fresh clone: the lane is gitignored (measured: `git check-ignore -v` reports `.aw/.gitignore:6:records/*/untracked/`) and `engine` materializes `COMMS_UNTRACKED_SUBDIRS` only as an install side effect, so in THIS worktree `.aw/records/comms/untracked/` is an EMPTY directory with no `acks/` or `inbox/` inside it (measured). So `mkdir(parents=True, exist_ok=True)` the acks dir before writing, and treat a missing `inbox/` as "message not found" (a clean refusal) rather than letting a `FileNotFoundError` escape. This is the same defect PR-005 found in child 01.
  - Depends on: none
  - Expected outcome: a writer that can only emit `AGENT_ACK_STATES` for a real message, writes an offset-aware `at`, and works against a repo that has never been installed into.
  - Execution state: pending
- [ ] E-02 Add `comms_acks.message_status(comms_dir, msg_id)` returning `{"msg_id", "delivery", "work", "unread", "acks"}`: `delivery` is the newest (by `at`) valid broker-state ack, `work` the newest valid agent-state ack, and `unread` is True exactly when a `delivered` ack exists and no agent ack does (see the `read`-or-later clarification below). Invalid ack files are listed under `acks` with a `problem` and never counted. With no broker, `delivery` is None and `unread` is False, so the view degrades rather than fails.
  - COMPARING `at` VALUES WILL RAISE UNLESS YOU NORMALIZE THE OFFSET, and this is measured, not hypothetical. `comms.validate_ack` accepts ANY value `comms.parse_not_before` parses, and that function returns an offset-NAIVE datetime for `2026-09-24T11:00:00` and an offset-AWARE one for `...Z`. Both pass validation, so a real acks dir can legitimately hold one of each, and comparing them raises. Measured at review: `sorted(acks, key=lambda a: comms.parse_not_before(a["at"]))` over exactly those two values raises `TypeError: can't compare offset-naive and offset-aware datetimes`. So "the newest by `at`" MUST normalize first: treat a naive parse as UTC (`dt.replace(tzinfo=timezone.utc)` when `dt.tzinfo is None`) before any comparison, and never sort raw parse results. A tie or an unparseable `at` must not raise either: fall back to a stable order (filename) rather than crashing a read-only status view.
  - `read`-OR-LATER IS NOT DERIVABLE FROM THE ENUM, so do NOT write a rank comparison. `comms.AGENT_ACK_STATES` is a tuple whose ORDER IS NOT A LATTICE (measured: `index("not-done")` is 3 and `index("executed")` is 4, so a tuple-index rank would make the terminal refusal `not-done` rank BELOW `executed`), and the module exposes no ordering constant (measured: no `ORDER`/`RANK`/`LATTICE` name in `dir(comms)`). Since `AGENT_ACK_STATES` membership ALREADY means the target asserted it, the honest rule is the spec's literal one: `unread` is True when a `delivered` ack exists and NO valid agent-state ack exists. Any agent ack clears `unread`. Do not invent a state ordering this repo has not defined.
  - SELECT A MESSAGE'S ACKS BY THE FILE'S `re` FIELD, NOT BY PARSING OR GLOBBING ITS NAME. `comms.ack_filename` joins its three parts with `.` and neither part is dot-free, so the name is NOT re-splittable: measured, `ack_filename("m.a", "b", "read")` and `ack_filename("m", "a.b", "read")` are BOTH `m.a.b.read.json`, and a real msg-id is full of dots (`...--to--c.d-ask-x` produced a 7-part split). Globbing is also unsafe, because `comms.is_filename_safe` PERMITS glob metacharacters (measured: `a[b`, `a*b`, `a?b` all return True), so a `Path.glob(f"{msg_id}.*")` silently matches the wrong file or nothing. So: read every `*.json` in `untracked/acks/`, parse it, and keep the ones whose `re` equals `msg_id`. The filename is a convenience for humans; the JSON body is the authority. An unparseable or non-object file is an `acks` row with a `problem`, never an exception.
  - WRITER-LAYER MISMATCH IS NOT CHECKABLE FROM A FILE, and the original wording claimed otherwise ("any ack whose state's writer does not match its layer"). There is no per-file "layer": every ack lands in the SAME `untracked/acks/` dir (`engine.COMMS_UNTRACKED_SUBDIRS` has one `acks` entry and `COMMS_SHARED_SUBDIRS` has none, measured), and the `by` field is self-asserted exactly as the Deferred list says. So a forged broker-written `read` is INDISTINGUISHABLE on disk from a genuine agent-written one. Do not claim to detect it. What this function CAN and MUST do is classify each ack by `comms.ack_writer_for(state)` and report `delivery` from broker states and `work` from agent states, so a state is never counted in the wrong bucket; the docstring MUST state plainly that the writer of a given file is unverified.
  - Depends on: E-01
  - Expected outcome: one derived status per message that never raises on a mixed-offset acks dir, with `unread` derived from the spec's literal rule and the unverifiable-writer limit written down.
  - Execution state: pending
- [ ] E-03 Add the `__main__` entry with `ack` and `status` subcommands (`status` with no msg-id lists every inbox message; `--format json` emits the dicts). `ack` exits 2 on any refusal and writes nothing.
  - RESOLVE `comms_dir` BY THE SHIPPED LAYOUT RULE, and do NOT express it as "the same way `comms_broker` does". That module does not exist yet (this plan's `- Item-Dependencies: executed:nomhl1` makes it a prerequisite, but a citation to an unwritten function is not checkable, and if child 01 stops at its spike per its E-01 the named shape may never exist). Call `engine.resolve_target_layout` and `engine._record_scaffold_dirs` directly and take the `comms` key, which is what child 01's E-05 was corrected to say. A missing `untracked/inbox/` is ZERO messages: `status` prints an empty list and exits 0.
  - Depends on: E-02
  - Expected outcome: `python3 -m agent_workflows.comms_acks --help` lists both subcommands; `status` against a repo with no `untracked/` lane exits 0 with an empty list.
  - Execution state: pending

### Task group 2: docs, tests, spec, suite

- [ ] E-04 Add one paragraph to `engine._COMMS_README_TEMPLATE` under "## Acknowledgements", and the same paragraph to this repo's installed `.aw/records/comms/README.md`: after reading a message, a target agent MAY run `python3 -m agent_workflows.comms_acks ack <msg-id> read --by <proj.agent>` (and later `done`/`executed`/etc.), and acks are optional because the convention works without them.
  - THE 3-BYTE DRIFT IS TWO PATH SUBSTITUTIONS, NOT NOISE, so keep them. Measured the diff rather than the byte count: the disk copy differs from the template on exactly TWO lines, its H1 (`# .aw/records/comms/` vs the template's `# .agents/comms/`) and its closing pointer (`.aw/records/specs/` vs `.agents/docs/specs/`). Those are deliberate layout substitutions in the INSTALLED copy. So "the same paragraph in both" means the same paragraph TEXT; do not reconcile the two files, do not regenerate the disk copy from the template, and do not "fix" either H1.
  - WRITE A PATH-AGNOSTIC PARAGRAPH so the one text is correct in both files: name the module (`python3 -m agent_workflows.comms_acks`) and the `acks/` lane RELATIVE to the comms dir, and do NOT hardcode `.aw/records/comms` or `.agents/comms` in it. A hardcoded root would be wrong in the legacy layout, which `engine._record_scaffold_dirs` still emits.
  - NO TEST PINS THE TEMPLATE TEXT, so the Under-scope clause below is a genuine no-op here (measured: the only test touching this file asserts installer ROLLBACK removes `.aw/records/comms/README.md`, and no test compares its content). Do not go looking for an expected-text fixture to update.
  - Depends on: E-03
  - Expected outcome: the template and the installed copy carry the same new paragraph text, and the two pre-existing layout substitutions are untouched.
  - Execution state: pending
- [ ] E-05 Write `tests/test_comms_acks.py` (tmp dirs, no network): agent writing `delivered` refused; unknown msg-id refused; unsafe `by` refused; valid `read` written and passes `comms.validate_ack`; `status` gives `unread` True after a broker `delivered` ack and False after `read`; a hand-planted invalid ack is reported with a problem and not counted; no broker acks gives `delivery` None.
  - PLUS THE CASES THE REVISIONS ADDED, each of which is a defect this review MEASURED rather than a hypothetical. (a) MIXED-OFFSET `at`: plant two valid acks whose `at` values are `...T10:00:00Z` and `...T11:00:00` (both pass `comms.validate_ack`, measured) and assert `message_status` returns a status instead of raising; this test FAILS with `TypeError: can't compare offset-naive and offset-aware datetimes` against the naive sort. (b) DOT-BEARING MSG-ID: use a realistic msg-id containing dots (`20260924-1200-01-a.b--to--c.d-ask-x`) and assert its ack is found, which a name-splitting or globbing selector misses. (c) GLOB METACHAR IN MSG-ID: a msg-id containing `[` (which `comms.is_filename_safe` PERMITS, measured) is selected correctly, proving the selector is not `Path.glob`. (d) NO LANE AT ALL: against a comms dir with no `untracked/` subdirectory (the state of a fresh clone, measured in this worktree), `write_agent_ack` creates `acks/` and succeeds, and `message_status` returns `delivery` None without raising. (e) `not-done` DOES NOT RANK BELOW `executed`: assert `unread` is False after ANY agent ack including `not-done`, pinning the "no state ordering" decision so a later rank-based rewrite fails.
  - Depends on: E-04
  - Expected outcome: all pass; the writer-refusal test fails under the mutation named in V, and cases (a) and (c) fail against the pre-revision approach.
  - Execution state: pending
- [ ] E-06 Amend the spec: correct the ack path from `.agents/comms/local/acks/` to the `untracked/acks/` lane (the layout block already says `untracked/ ... acks/`), add a short "Agent acks and status" subsection naming `comms_acks` and the derivation rules (including that the writer of an ack FILE is unverified, per E-02), and remove agent-side ack writing from the Deferred list.
  - THERE IS A SECOND STALE `local/` REFERENCE, so fix BOTH. Measured: the spec contains `local/` on three lines, and only one is the ack path. The "Cooperative check-in" section still tells agents to check `local/inbox/`, while the installed `AGENTS.md` block `engine` writes says `untracked/inbox/` (measured in `engine`'s "Inter-agent comms (check your inbox)" template). That is the same rename miss as F-2 and is a live contract error in the same way. The third `local/` mention is the layout block's parenthetical "(was `local/`)", which is HISTORY and must be LEFT ALONE.
  - DO NOT HAND-EDIT `- Status:` OR `## Workflow history`. `.aw/records/specs/README.md` forbids it ("Do NOT hand-edit the status or history. Use the owner verbs") and routes the history line through `aw specs note <path> --message <text>`. Write the SECTION BODIES ONLY; the spec stays `implemented`. Verified at review that the verb accepts this spec unchanged (a copy in a scratch repo took a note and prepended it newest-first, exit 0), so the tooled route is available and no hand edit is needed. Same instruction child 02's E-09 carries.
  - Depends on: E-05
  - Expected outcome: `grep -n "local/" <spec>` returns exactly the one HISTORY line ("(was `local/`)"); the note line was appended by `aw specs note`, not by hand.
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
- F-5 (measured at review): `comms.validate_ack` accepts BOTH an offset-aware and an offset-naive `at`, because `comms.parse_not_before` parses both and the validator only checks that it parses. Comparing the two raises: `sorted([{'at':'2026-09-24T10:00:00Z'},{'at':'2026-09-24T11:00:00'}], key=lambda a: comms.parse_not_before(a['at']))` -> `TypeError: can't compare offset-naive and offset-aware datetimes`. "The newest by `at`" therefore has to normalize before comparing (E-02), and the writer pins one spelling (E-01).
- F-6 (measured at review): an ack FILENAME is not re-splittable back into its parts, so acks must be selected by the `re` FIELD. `comms.ack_filename("m.a","b","read")` and `comms.ack_filename("m","a.b","read")` both return `m.a.b.read.json`, and a realistic msg-id splits into 7 parts. Globbing is unsafe too: `comms.is_filename_safe` returns True for `a[b`, `a*b` and `a?b`, so a glob pattern built from a msg-id can match the wrong file.
- F-7 (measured at review): `comms.AGENT_ACK_STATES` order is NOT a progress lattice (`index("not-done")` 3 < `index("executed")` 4) and `comms` exposes no ordering constant, so "`read`-or-later" as originally written was not derivable. The spec's literal rule (any agent ack clears `unread`) is what E-02 now implements.
- F-8 (measured at review): a forged broker-written `read` ack is UNDETECTABLE on disk. There is one `acks` lane (`engine.COMMS_UNTRACKED_SUBDIRS` has `acks`; `COMMS_SHARED_SUBDIRS` does not), so there is no per-file "layer" to compare a writer against, and `by` is self-asserted. E-02 no longer claims to report the mismatch and instead records the limit.
- F-9 (measured at review): the spec carries `local/` on THREE lines, only one of which is the ack path F-2 names. The "Cooperative check-in" section still says `local/inbox/` while `engine`'s installed AGENTS.md block says `untracked/inbox/`; the third is the deliberate history note "(was `local/`)". E-06 now fixes two and preserves one.
- F-10 (measured at review): the README drift is not noise but two deliberate layout substitutions in the INSTALLED copy (its H1 and its closing spec pointer), so the paragraph text must be path-agnostic and the two files must not be reconciled. No test pins the template content (the only test touching the file asserts installer rollback removes it), so the Under-scope clause below is a verified no-op.
- F-11 (measured at review): `.aw/records/comms/untracked/` exists in this worktree but is EMPTY (no `inbox/`, no `acks/`), because the lane is gitignored (`.aw/.gitignore:6:records/*/untracked/`) and `engine` materializes the subdirs only as an install side effect. Both E-01 and E-03 now treat that as a normal state, the same defect child 01's PR-005 fixed.

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
- Under-scope: if an installer or packaging test pins the README template text, updating that test's expected text is in scope; declare its path before editing. VERIFIED at review that none does (F-10), so this clause should stay a no-op.
- Under-scope, RESOLVED IN PLACE at review: E-02 originally claimed to report an ack "whose state's writer does not match its layer", which is not derivable from a single shared `acks/` lane (F-8), and derived `unread` from a `read`-or-later ordering the enum does not define (F-7). Both are now stated as the limits they are. E-01/E-02's timestamp handling (F-5) and ack selection (F-6) were unspecified and are now pinned, each with a test in E-05.

## Required tests / validation

- `tests/test_comms_acks.py` targeted, plus a mutation run showing the writer-refusal test FAILS.
- The five added cases (mixed-offset `at`, dot-bearing msg-id, glob-metachar msg-id, absent `untracked/` lane, `not-done` clears `unread`), with the mixed-offset one shown FAILING against a naive sort so the fix is proven non-vacuous.
- `aw specs check` on the amended spec, and `grep -n "local/"` returning only the history line.
- `python3 -m pytest` bare with the summary line pasted.

## Spec / documentation sync

- Amends `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` (declared in `- Scope-Paths:`): the stale `local/acks/` path is a live contract error (F-2), the "Cooperative check-in" section carries a SECOND stale `local/inbox/` that contradicts the installed AGENTS.md block (F-9), and the Deferred list would otherwise still name shipped work. The amendment also records the unverifiable-ack-writer limit (F-8), since the spec's authorized-writer table is what a reader would otherwise take as enforced.
- The spec stays `- Status: implemented` and its `## Workflow history` is written by `aw specs note`, never by hand (`.aw/records/specs/README.md`).
- Note child 02 (`ex539u`) ALSO declares this spec in its `- Scope-Paths:` and amends a different section (a broker target registry subsection). The two amendments do not overlap, and the runner isolates each item in its own worktree and merges through the revalidation gate, so no ordering is owed; if this plan runs second, re-read the spec before editing rather than assuming the section offsets.
- Updates the installed comms README template and this repo's copy (E-04), keeping their two deliberate layout substitutions intact (F-10).

## Open questions

### OQ-01: Should a target agent be required, rather than permitted, to write a `read` ack?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: permitted only. The spec says the convention "MUST work fully WITH OR WITHOUT any broker", and a mandatory ack would add a step to every non-OpenCode agent; the README paragraph says MAY.
- Carrier-Declined: Nothing is outstanding under the default. "Permitted" is the shipped behavior this plan builds (E-04 writes MAY), so no later work is owed unless the maintainer chooses to make acks mandatory, which is a new scope decision rather than a deferred obligation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_comms_acks.py -k write -v` showing PASSED for broker-state refused, unknown msg refused, unsafe `by` refused, and valid `read` written. PLUS the no-lane case (d): paste the written ack's JSON showing `at` carries an OFFSET (a trailing `+00:00` or `Z`), and the test name proving `acks/` was created under a comms dir that had no `untracked/` subdir.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `-k status` run showing PASSED for unread-after-delivered, not-unread-after-read, invalid ack reported not counted, and no-broker delivery None. PLUS, because these are the measured defects and a happy-path run cannot distinguish them: the MIXED-OFFSET test (a) passing, and a paste of the SAME test failing against a naive `sorted(..., key=parse_not_before)` (the `TypeError` line is the required output, not a claim that it would fail); the dot-bearing (b) and glob-metachar (c) msg-id tests passing; and the `not-done` test (e) passing. A `-k status` paste that does not name these five is NOT sufficient evidence for this item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m agent_workflows.comms_acks --help`, and an `ack` of state `delivered` in a tmp repo exiting 2 (`echo $?`) with the acks dir absent or empty. PLUS `grep -n "resolve_target_layout\|_record_scaffold_dirs" agent_workflows/comms_acks.py` showing the layout rule is CALLED rather than reimplemented, and a `status` run in a repo with no `untracked/` lane exiting 0.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- agent_workflows/engine.py .aw/records/comms/README.md` showing the same paragraph added to both and no other change in `engine.py`. The diff MUST show the two pre-existing layout substitutions UNTOUCHED (no hunk on either file's H1 line or closing-pointer line), and the added paragraph MUST contain no hardcoded `.aw/records/comms` or `.agents/comms` root.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest -o addopts="" tests/test_comms_acks.py` summary, then the same run with the `ack_writer_for(state) == "agent"` check locally removed, showing the broker-state-refused test FAILED; revert and show the file matches the intended version.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `grep -n "local/" .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` (NOT `local/acks`, which would miss the second stale reference this review found) returning EXACTLY ONE line, the layout block's historical "(was `local/`)". Plus the spec diff showing the new subsection, and `aw specs check .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` conforming. The history line must appear as an `aw specs note` record; paste the command you ran, since a hand-written history block is forbidden by `.aw/records/specs/README.md`.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line (`N passed`, 0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-02, because four of its five added cases are defects whose WRONG implementation still returns a plausible status object: a mixed-offset acks dir raises only when both spellings are present, a name-splitting selector returns the right answer for a dot-free msg-id, a `Path.glob` selector works until a metacharacter appears, and a rank-based `unread` agrees with the correct rule on every state except `not-done`. So V-02 demands the named test cases and the pasted `TypeError` from the pre-revision sort, not a green `-k status` summary. V-06 is the other exposure: `grep local/acks` returns nothing even while the second stale `local/inbox/` reference survives, which is why the required grep is `local/`.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `nomhl1` is not in `executed/`, since E-02's `delivery` half aggregates a broker ack layer nothing else writes (note the ack WRITER in E-01 stands alone, per F-4, so a re-scope to writer-only is the sensible report rather than abandonment); or `comms.AGENT_ACK_STATES`, `comms.ack_writer_for` or `comms.validate_ack` no longer has the shape E-01 and E-02 rely on, since the closed-enum guarantee is what makes an agent-only writer enforceable.

SCOPE FENCE (a declaration, not a stop). The executor edits only the declared `- Scope-Paths:`. An out-of-scope edit is MADE and then JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Note `agent_workflows/engine.py` is declared for the `_COMMS_README_TEMPLATE` paragraph ONLY (see the Scope check).

OQ-01 is `Blocking: no` with a stated default and a declined carrier, so no open question blocks execution. This plan is `to-review`, carries `- Item-Dependencies: executed:nomhl1`, and requires explicit human approval (`- Status: approved`) before execution. Commit only the `- Scope-Paths:` via `aw commit ozcfjr -- <paths>`, never `git add -A`, and never push. This plan carries NO `- Blocks-Release:` and neither does backlog `0gd5w6` (verified: its front matter has no such field), so no release gate is owed or inherited; close `0gd5w6` only after this plan reaches `executed/`. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-07 carry pasted evidence.
