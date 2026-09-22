# IPD: Stop losing a deliberate history message: write it on a same-status set and make durable history survive a clone

- Date: 2026-09-10
- Kind: child
- Concern: A deliberate provenance note can be silently lost in TWO different ways, and both exit 0. FIRST, `aw set` on a SAME-STATUS artifact DISCARDS an explicit `--message`: `status_set.apply_status_change` computes `content_changed`/`path_changed` and RETURNS EARLY (`status_set.py:867-870`) before the history write at `:880-896`, so the message is never recorded. Measured previously and filed as `x6tk1u` (high): roughly 2000 characters of evidence were swallowed at exit 0, caught only via `git status`. SECOND, and worse because it looks like it worked, the DURABLE history is GITIGNORED. Plan `awhistory-02` (`b0behn`, executed 2026-08-18, spec `20260818-1525-02` OQ-2) deliberately slimmed the inline `## Workflow history` block of specs and backlog items to the LATEST ONE record, on the premise that "the full chronological log lives in the global .aw/records/history.jsonl sidecar". That premise does not hold: `git check-ignore` confirms `.aw/.gitignore:11` ignores `records/history.jsonl`, so the durable log is PER-MACHINE and does not survive a clone.
  MEASURED CONSEQUENCE ON THIS REPOSITORY'S OWN RECENT WORK, which is what turns this from tidy-up into a real defect: three `aw specs note` calls during the 2026-09-10 setid cleanup recorded substantial reasoning (why one spec was superseded rather than revised, why invariant `I-16` was added and what the `I-09` misfiling was, why a finding must not be reported even at `info`). All three now exist ONLY in the gitignored sidecar; each spec shows exactly ONE inline record. The repository's own contract forbids precisely this: `AGENTS.md` states an answer must never live only in a gitignored tree because it "would not survive".
  AND THE EXPOSURE IS LARGE AND SILENT: 143 tracked backlog items and specs still carry MORE THAN ONE inline history record, all of it legacy, all of it committed-only, and one `aw backlog set` call on any of them truncates it to a single line. Meanwhile the sidecar on this machine covers 141 artifacts, so neither store is complete and the union exists nowhere in git.
  A NOTE ON WHAT IS *NOT* BROKEN, because an earlier report of mine got this wrong and the correction matters: the slimming itself is INTENTIONAL and reviewed, not an accidental renderer bug. `backlog._reattach_history` exists specifically to carry history forward and its own comment states the latest-one rule. Do not "fix" it by reverting to append-only; that would undo a reviewed decision and break the `aw attention` `last_history_at` derivation the decision was shaped around.
  AND A THIRD DEFECT FOUND AT REVIEW, which REORDERS THE FIX: `last_history_at` (`attention_contract.py:540-549`) takes the date of the LAST record in FILE ORDER, while plan history is NEWEST-FIRST. So the derivation is ALREADY WRONG wherever a record carries more than one line: 273 of 581 multi-record plans report a `last_history_at` that is not their newest record's date. Slimming specs and backlog to one line HID this, because with one record the first and last coincide. Therefore un-slimming them WITHOUT first fixing the reader would spread a live bug to two more trees, so this plan now fixes the reader (E-02) before the writer (E-08). This is the plan's most consequential correction and the reason its item order changed at review.
- Scope: The two ways a deliberate history message is lost. IN: writing the history record on a same-status transition when a `--message` is PRESENT (`x6tk1u`), without making every idempotent re-assertion grow duplicate history; making durable history survive a clone, by whichever of the recorded options review selects; closing the silent-failure hole where a swallowed sidecar write plus a successful inline slim loses a record entirely; adding the missing `aw backlog note` verb so annotating an item no longer requires abusing `set`; regression fixtures for each. OUT: the confirmation and terminal-reopen guards (Order 01 of this Set); reverting `awhistory-02`'s slimming decision; any change to `aw attention`'s derivation, which reads the latest inline record and must keep working.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/attention_contract.py, agent_workflows/plan_readiness.py, agent_workflows/record_history.py, agent_workflows/command_surface.py, .aw/records/specs/20260818-1525-02-sidecar-metadata-and-history.spec.md, .aw/records/backlog/README.md, tests/test_status_set.py, tests/test_history_routing.py, tests/test_attention_contract.py, tests/test_backlog.py
- Item-Dependencies: none
- Status: approved
- Blocks-Release: next
- Readiness: go-pending-approval
- Set: setterguard
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vhbvwz
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: x6tk1u

## Workflow history
- 2026-09-18 approved (aw set): status set to approved
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (BLOCKER) through PR-012, all 12 FIXED, none deferred; readiness GO - PENDING HUMAN APPROVAL. THE SET WAS RE-ORDERED (PR-001): E-02 as authored mandated newest-first ordering AND preserving prior records AND that `last_history_at` keep working, but that derivation takes the LAST record in FILE order, so the pair would have made it report the OLDEST date; measured by patching `specs._append_history` as authored. E-02 is now the READER fix and E-08 (split out) the writer change that depends on it. THE PLAN'S EXISTENCE PROOF WAS FALSE (PR-002): 273 of 581 multi-record plans ALREADY report a wrong `last_history_at`, so plans do not demonstrate the derivation tolerates multi-record newest-first history; un-slimming first would have spread a live bug to two more trees. E-01 WALKED INTO ITS OWN NAMED TRAP (PR-003): three identical calls produced three duplicate records, and both runners pass a constant message, so a dedup rule is now required. Also narrowed E-04's durability-inverting coupling, grew E-07 from one spec passage to six, corrected 143 to 139 and the `attention_contract.py:434` miscitation, recorded the three measured suite baselines, and declared three previously-undeclared paths.
- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `x6tk1u` (the discarded-message half) and `hg2oop` (the durability half), both filed after firing live during the setid cleanup. THE CENTRAL CORRECTION, made before authoring and recorded in `hg2oop` itself: I first reported the history truncation as an accidental renderer bug and was WRONG. Reading `awhistory-02`'s executed plan showed the slimming is a deliberate, reviewed decision with a stated rationale, so the defect is not the slim but the GITIGNORED destination it slims into. That correction changes the whole remedy: the plan must NOT restore append-only history. TWO NUMBERS MEASURED AT AUTHORING that size the problem: 143 tracked backlog items and specs still carry more than one inline record (legacy, committed-only, one `set` away from truncation), and the sidecar on this machine covers 141 artifacts, so neither store is complete and their union is nowhere in git. ALSO FOUND, and it is why E-04 exists: `backlog.py:557` swallows a sidecar write failure in a bare `except Exception: pass`, so a failed sidecar write followed by a successful inline slim loses the record with no signal at all.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a recorded reason durable AND correctly read: never silently discard a `--message`, ensure the history a tool claims to have written can be read by someone who clones the repository, and make "the newest record" mean the same thing to every reader of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop discarding the message

- [x] E-01 WRITE THE HISTORY RECORD ON A SAME-STATUS TRANSITION WHEN A `--message` IS PRESENT. Today `apply_status_change` returns at `status_set.py:867-870` when neither content nor path changed, which is BEFORE the history write at `:880-896`, so an explicit note is discarded. Make message PRESENCE the discriminator: a same-status call WITH a non-empty message proceeds to the history write; a same-status call WITHOUT one keeps returning early. FOLLOW THE PATTERN THAT ALREADY EXISTS IN THIS FUNCTION rather than inventing one: the `Blocks-Release`, `From-Backlog`, `Item-Dependencies` and `Priority` writes were each already hoisted out of the status-change branch for exactly this reason, so there are four precedents in the same body for "this field is written even when the status did not move".
  MESSAGE PRESENCE ALONE IS NOT SUFFICIENT, AND THE PLAN'S OWN NAMED TRAP FIRES. `x6tk1u` warns not to grow duplicate history on idempotent re-assertion, and the authored discriminator does exactly that. MEASURED at review with the minimal patch applied: running the IDENTICAL `aw ipd set reviewed aaaa01 --yes -m "identical note"` three times produced THREE identical records (4 total in the file). This is not hypothetical: both runners call `set_plan_approved` with a hardcoded constant message (`FULL_AUTO_APPROVAL_MESSAGE`, `oc_runipd.py:730-732`, `agy_runipd.py:830`) from two call sites each (`oc_runipd.py:2937`, `:6933`; `agy_runipd.py:1975`, `:3990`), so a re-run over an already-`auto-approved` plan would append a duplicate every time.
  SO ADD A DEDUPLICATION RULE and state it in the code: write the record only when the message is non-empty AND is not byte-identical to the NEWEST existing record's message for the same status and date. That keeps the `x6tk1u` case working (a genuinely new note is always recorded), keeps idempotent re-assertion silent, and needs no new vocabulary. If you choose a different rule, it must still make the measured three-identical-calls case produce exactly ONE record, and V-01 must show it.
  - Depends on: none
  - Expected outcome: `aw set <current-status> <artifact> --message "..."` records the message; the same call without a message writes nothing; the SAME message repeated writes exactly one record total, not one per invocation.
  - Execution state: performed

### Task group 2: make durable history actually durable

- [x] E-02 FIX `last_history_at` TO MEAN THE NEWEST RECORD, BEFORE ANY WRITER KEEPS MORE THAN ONE LINE. THIS ITEM WAS INVERTED AT REVIEW and the reason must be read before touching either writer: as authored, E-02 told the executor to keep prior records AND to use NEWEST-FIRST ordering, while `attention_contract.last_history_at` (the REAL location is `attention_contract.py:540-549`, not `:434` as this plan and the awhistory spec both cite) takes the date of the **LAST matching record in file order**. Those two instructions contradict each other: with newest-first ordering the LAST record is the OLDEST one, so the derivation the plan promises to protect would start reporting the oldest date on every multi-record spec and backlog item. MEASURED, not reasoned: patching `specs._append_history` exactly as authored and appending a `2026-06-06` record to a file holding `2026-01-01` made `last_history_at` return `2026-01-01`.
  THE BUG ALREADY EXISTS ON PLANS, WHICH DESTROYS THIS PLAN'S OWN EXISTENCE PROOF. The plan asserts "plans are the existence proof that it works, since they carry many inline records today and `attention` handles them". They do not. Measured over the whole corpus with the production parser (`attention._history_section_lines` + `HISTORY_RECORD_RE`): of 581 plans carrying more than one inline record, **273 (46%) already report a `last_history_at` that is not their newest record's date** (e.g. `97df1z` reports `2026-08-29` while its newest record is `2026-09-03`). So `attention` does not handle newest-first history correctly today; the defect is merely invisible because specs and backlog were slimmed to one line, where first and last coincide. E-02 as authored would have PROPAGATED a live bug to two more trees while citing it as proof of safety.
  SO DO THIS FIRST, AS ITS OWN CHANGE: make the newest-record derivation single-sourced and correct. `plan_readiness.extract_newest_history_entry` (`plan_readiness.py:185-203`) ALREADY implements the correct rule for newest-first sections and carries an explicit warning not to "fix" it back to the last record; `last_history_at` is the second, contradictory reader. Reconcile them so ONE rule decides which record is newest, and state in the code which ordering is canonical. Update `tests/test_attention_contract.py:188-196`, whose fixture is oldest-first and therefore passes under either rule, which is why the contradiction survived. DO NOT rewrite the 273 plan files; this is a READER fix, so their history is already correct on disk and only the derivation is wrong.
  - Depends on: none
  - Expected outcome: `last_history_at` returns the NEWEST record's date for a newest-first section; the 273 currently-mismatching plans report correctly with zero files rewritten; one shared rule decides "newest", with the contradictory second reader gone; `aw attention --check` passes.
  - Execution state: performed

- [x] E-08 THEN STOP SLIMMING FOR SPECS AND BACKLOG, per the maintainer's 2026-09-10 ruling (OQ-01), which is safe ONLY ONCE E-02 LANDS. Stop truncating the inline `## Workflow history` to a single line in `backlog._reattach_history` (`backlog.py:628-649`, the `hist_block = new_record` line that drops `body`) and in `specs._append_history` (`specs.py:342-358`, the `new_section = ["", record]` line), so prior records are PRESERVED and the new one is added, exactly as `status_set.py`'s plan writer already does. Use NEWEST-FIRST ordering to match plans (`status_set.py:872-879`). KEEP WRITING THE SIDECAR TOO: it is a useful machine-local activity log; this item changes only whether the INLINE record is truncated.
  MEASURED AT REVIEW so the executor knows what to expect: patching only the specs half breaks exactly one test, `tests/test_history_routing.py::HistoryRoutingTests::test_specs_slims_inline` (`1 failed, 5958 passed` against a `5959 passed` baseline). That test ASSERTS the slimming, so it must be REWRITTEN to assert preservation rather than deleted, and its module docstring (`tests/test_history_routing.py:2`, "slimmed to the latest one record") must change with it. Expect the backlog half to need the same treatment.
  - Depends on: E-02
  - Expected outcome: a second `aw backlog set` or `aw specs note` leaves the earlier record in place, newest-first; `test_specs_slims_inline` is rewritten to assert preservation; `last_history_at` still reports the newest date (which is what E-02 guarantees).
  - Execution state: performed

- [x] E-03 PROVE THE LEGACY MULTI-RECORD FILES ARE SAFE, which E-08 should achieve BY CONSTRUCTION rather than by migration. RE-MEASURED AT REVIEW: **139**, not 143, tracked backlog items and specs carry MORE THAN ONE inline history record (of 211 such files), counted with the production parser at `be6d2ab9`. The count is a moving target in a shared checkout, so RE-COUNT at execution and report the number you measured rather than reusing either figure; the point of the item does not depend on the exact value. All of it is legacy (it predates the sidecar, so nothing else holds it), and under today's behavior one `set` call slims any of them to a single line. Once E-08 stops slimming, nothing truncates them, so this item is a VERIFICATION rather than a rewrite: pick real legacy files, run a real transition, and show the prior records survive. DO NOT BULK-REWRITE THEM: they belong to other agents' work in a shared checkout, E-08 removes the hazard without touching them, and a mass diff would be both unnecessary and hostile to review. If verification shows some files still lose records, that is a finding to report, not a licence to sweep.
  - Depends on: E-08
  - Expected outcome: the count of tracked files carrying more than one inline record does NOT fall after a transition; at least one real legacy file is demonstrated to keep its prior records; zero files were rewritten to achieve it.
  - Execution state: performed

- [x] E-04 STOP SWALLOWING A FAILED SIDECAR WRITE. `backlog.py:544-558` wraps the `record_history.append(...)` call in a bare `try/except Exception: pass`, so a sidecar failure is invisible. `specs.py:145-156` has the SAME pattern (confirmed at review, so this is not an open question to investigate: `_sidecar_append`'s `except Exception: pass`), and `backlog.py:443` is a third site to inspect. Make the failure visible at all of them.
  DO NOT WRITE THE "BLOCK THE SLIM" COUPLING THE AUTHORED VERSION ASKED FOR. Once E-08 lands there IS no slim to block, so the instruction describes a state this plan removes, and implementing it would add a durability coupling (an inline write conditioned on a sidecar result) that the maintainer's OQ-01 ruling deliberately reversed: inline is now the durable home and the sidecar is a machine-local activity log, so a sidecar failure must NOT gate the durable write. The correct remedy is narrower and still fixes the real defect: report the failure (a warning naming the artifact and the error) instead of discarding it, and ensure the INLINE record is written regardless. If you find any ordering where the inline write can still be lost because a sidecar write failed, that is a finding to report.
  - Depends on: E-08
  - Expected outcome: an induced sidecar-write failure at each of the three sites is REPORTED, not swallowed, and the inline record is present anyway; no bare `except Exception: pass` remains around a history write; no new inline-depends-on-sidecar coupling was introduced.
  - Execution state: performed

### Task group 3: remove the reason to abuse the setter

- [x] E-05 ADD `aw backlog note`, MIRRORING THE EXISTING `aw specs note`. Today the backlog verb set is `new`, `set`, `check` only, so appending a note to an item REQUIRES a status-setting call, which is how both defects in this plan were hit. `aw specs note` already exists and is the precedent to copy (same flag shape, same history-record behavior, no status change). This is the ergonomic fix that removes the incentive to reach for `set` when annotation is the intent. Register it on the backlog subparser beside `set`, and update `.aw/records/backlog/README.md`, which documents the verb set and becomes incomplete the moment the verb exists.
  - Depends on: E-01
  - Expected outcome: `aw backlog note <item> --message "..."` records a note without changing status; the README documents it; `aw specs note` behavior is unchanged.
  - Execution state: performed

### Task group 4: pin it

- [x] E-06 PIN EVERY BEHAVIOR WITH THE MEASURED CASES. Assert: (a) a same-status call WITH a message records exactly ONE record (not zero, the `x6tk1u` bug); (b) THE SAME MESSAGE REPEATED THREE TIMES still yields exactly ONE record, which is the measured duplicate-growth trap and the assertion the authored item most needed, since without it E-01's obvious implementation ships the very defect `x6tk1u` warned about; (c) a same-status call WITHOUT a message records nothing; (d) history written by a note verb is readable in a FRESH CLONE (clone or bare-repo push/fetch, never reading the same working tree, which cannot distinguish tracked from ignored); (e) an induced sidecar failure at each of the three sites is reported and the inline record is present anyway.
  AND ASSERT THE DERIVATION DIRECTLY, NOT MERELY THAT IT "STILL WORKS": a NEWEST-FIRST multi-record section must yield the NEWEST date from `last_history_at`. That assertion FAILS on today's code, which is why it is the load-bearing test of this plan; write it so it would have caught the 273-plan corpus mismatch. Do NOT reuse the shape of `tests/test_attention_contract.py:188-196`, whose fixture is oldest-first and therefore passes under either rule; that fixture is the reason the contradiction went unnoticed, and it must be joined by a newest-first case.
  - Depends on: E-01, E-02, E-08, E-03, E-04, E-05
  - Expected outcome: six assertions covering both defects, the duplicate-growth trap, the ergonomic verb, the three failure paths, and a newest-first `last_history_at` case that fails before E-02 and passes after.
  - Execution state: performed

- [x] E-07 AMEND SPEC `20260818-1525-02` IN THIS SAME CHANGE, because E-08 changes behavior that spec describes. Its OQ-2 ruled the inline history of specs and backlog keeps only the LATEST ONE record; the maintainer reversed that premise on 2026-09-10 (OQ-01), so inline history is now the durable home for both types. Record the amendment with its date and the ruling, state that the sidecar remains a machine-local ACTIVITY LOG rather than the durable store, and state that plans were always exempt so all three types now share one model. DO NOT DELETE OQ-2's ORIGINAL REASONING: the slimming was a considered decision motivated by `aw attention`'s `last_history_at`, that motivation still constrains the design, so mark it superseded rather than erasing it.
  AMEND FOUR MORE PASSAGES THAN THE AUTHORED ITEM NAMED, each measured at review, because leaving any of them would leave the spec instructing the opposite of the shipped code: **R2** (`:59`, "SLIM the inline `## Workflow history` to the LATEST ONE record line"), **R6** (`:63`, "keep reading ... the latest-one history line"), **AC1** (`:67`, "slims its inline `## Workflow history` to a single (latest) record line"), and **AC4** (`:70`, "`last_history_at` still resolves from the retained latest-one inline line"). ALSO CORRECT THE SPEC'S OWN CITATION at `:49`, which says the derivation lives at `attention_contract.py:434` and "reads the LAST inline record's date": the location is wrong (it is `:540-549`) and the behavior description is the very contradiction E-02 fixes, so the amendment must state the corrected rule.
  THE SPEC IS `Status: implemented` (measured), and the legal transitions from there are only `deferred` and `superseded` (`attention_contract.SPEC_TRANSITIONS`), so DO NOT try to move its status: amend the text and record the change with `aw specs note`, which appends a history record WITHOUT a status change (`specs.py:839-852`). Note the irony to check: that verb is one of the writers this plan is fixing, so run it AFTER E-02 and E-08 land and confirm the amendment's own record is preserved inline. That is a free end-to-end test of the fix.
  - Depends on: E-08
  - Expected outcome: R2, R6, AC1, AC4, OQ-2 and the `:49` citation all amended; OQ-2's reasoning preserved as superseded; the spec's status untouched at `implemented`; the spec's own new history record demonstrably kept inline by the very fix it documents.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SLIMMING IS DELIBERATE, NOT A BUG. `awhistory-02` (`b0behn`, executed, spec `20260818-1525-02` OQ-2) routed specs and backlog writers to the sidecar and slimmed inline history to the latest one record, KEEPING one line specifically so `aw attention`'s `last_history_at` keeps working. Any fix must preserve that derivation.
- `last_history_at` TAKES THE **LAST** RECORD IN FILE ORDER, WHICH CONTRADICTS NEWEST-FIRST ORDERING, and this is the single most important fact in this plan. It lives at `attention_contract.py:540-549`, NOT at `:434` (that line is inside the `TRANSITION_AUTHORITY` table). Both this plan and the awhistory spec `:49` cite the wrong line, and the spec additionally states the LAST-record behavior as a thing to protect. Because plans are newest-first, the derivation is ALREADY WRONG for them: 273 of 581 multi-record plans report a `last_history_at` that is not their newest record's date. Measured with `attention._history_section_lines` + `HISTORY_RECORD_RE`, the production readers.
- THERE ARE ALREADY TWO CONTRADICTORY "NEWEST RECORD" READERS. `plan_readiness.extract_newest_history_entry` (`plan_readiness.py:185-203`) takes the FIRST record and documents at length that taking the last one is "the bug this function replaced"; `attention_contract.last_history_at` takes the LAST. One of them must win, and until E-02 reconciles them no writer may keep more than one inline record without silently changing what `attention` reports.
- THE EXISTING TEST FIXTURES HIDE THE CONTRADICTION. `tests/test_attention_contract.py:188-196` and `tests/test_history_routing.py:52-55` both use oldest-first or single-record fixtures, where the first and last record coincide, so both pass under either rule. Any new test must include a NEWEST-FIRST multi-record case.
- `aw specs note` APPENDS HISTORY WITHOUT A STATUS CHANGE (`specs.py:839-852`), which is what makes E-07 possible: spec `20260818-1525-02` is `Status: implemented`, and the only legal transitions from `implemented` are `deferred` and `superseded`, so an amendment must NOT touch its status.
- PLANS ARE DELIBERATELY EXEMPT from the slimming: `awhistory-02` carries an explicit guard that it must NOT slim plan/IPD history, because `ipd_lint` IPD-S405 requires the inline `executed` entry at post-transition. So plan history behaves DIFFERENTLY from spec and backlog history, and that asymmetry is intentional.
- FOUR FIELDS ARE ALREADY HOISTED OUT OF THE STATUS-CHANGE BRANCH in `apply_status_change` (`Blocks-Release`, `From-Backlog`, `Item-Dependencies`, `Priority`), each because it must be written even when the status does not move. E-01 follows that established shape rather than inventing a new one.
- `status_set.py` DOES NOT WRITE TO THE SIDECAR AT ALL (`grep -c record_history` -> 0), unlike `specs.py` (1) and `backlog.py` (2). So a message discarded by `x6tk1u` is lost from both homes, and E-01's fix is the only thing that records it.
- THE HISTORY WRITER PREPENDS, NEWEST-FIRST, for plans (`status_set.py:872-879` documents this at length and warns that a reader wanting the latest entry must take the FIRST record via `plan_readiness.extract_newest_history_entry`). Do not hand-roll another parser.
- SUITE BARE: `python3 -m pytest`. Compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `status_set.py:867-870` vs `:880-896` | The early return precedes the history write, so a same-status `--message` is discarded at exit 0. | source read; `x6tk1u`'s measured ~2000-character loss |
| F-2 | HIGH | `.aw/.gitignore:11` | The durable history store is GITIGNORED, so the log the slimming relies on does not survive a clone. | `git check-ignore -v .aw/records/history.jsonl` -> `.aw/.gitignore:11:records/history.jsonl` |
| F-3 | HIGH | this cleanup's own specs | Three `aw specs note` records from 2026-09-10 exist ONLY in the sidecar; each spec shows 1 inline record. This violates the `AGENTS.md` rule that an answer must not live only in a gitignored tree. | `grep -c '^- 2026'` -> 1 on both specs; the four messages present in the sidecar |
| F-4 | HIGH | tracked corpus | **139** (re-measured at review, not 143) of 211 backlog items and specs carry >1 inline record, committed-only, each one `set` call from truncation; the sidecar covers 141 artifacts (204 records), so neither store is complete. The count drifts in a shared checkout; re-count at execution. | production-parser census at `be6d2ab9` |
| F-5 | MEDIUM | `backlog.py:544-558`; `specs.py:145-156`; `backlog.py:443` | A sidecar write failure is swallowed by a bare `except Exception: pass`. THREE sites, not one: the authored plan asked the executor to "check `specs.py` for the same pattern", and the answer is confirmed YES. | source read at all three |
| F-6 | MEDIUM | `awhistory-02` (`b0behn`) | The slimming is INTENTIONAL and reviewed, so the remedy must not revert it. An earlier report of mine claimed otherwise and was corrected in `hg2oop`. | the executed plan's Concern and E-01(b) |
| F-7 | LOW | backlog verb set | There is no `aw backlog note`, so annotating requires a status call; `aw specs note` exists as the precedent. | `aw backlog --help` lists only `new`, `set`, `check` |
| F-8 | BLOCKER | `attention_contract.py:540-549` vs E-02's newest-first instruction | E-02 AS AUTHORED IS SELF-CONTRADICTORY AND WOULD BREAK THE ONE PROPERTY IT PROMISES TO PROTECT. `last_history_at` returns the date of the LAST matching record in FILE ORDER; E-02 mandates NEWEST-FIRST ordering; so with prior records preserved the derivation returns the OLDEST date. Fixed by inverting the Set: E-02 now repairs the reader FIRST, E-08 then stops slimming. | patched `specs._append_history` as authored, appended `2026-06-06` to a file holding `2026-01-01`, and `last_history_at` returned `2026-01-01` |
| F-9 | HIGH | `.aw/records/plans/**`; this plan's E-02 and OQ-01 | THE PLAN'S "EXISTENCE PROOF" IS FALSE. It asserts plans prove newest-first multi-record history works with `attention`. Measured: 273 of 581 multi-record plans (46%) already report a wrong `last_history_at` (e.g. `97df1z` reports `2026-08-29`, newest is `2026-09-03`). The bug is invisible only because specs/backlog were slimmed to one line. E-08 would have propagated a live bug to two more trees while citing it as safety evidence. | corpus scan with `attention._history_section_lines` + `HISTORY_RECORD_RE` |
| F-10 | HIGH | measured patch of `status_set.py:867-870` | E-01's DISCRIMINATOR TRIGGERS THE TRAP `x6tk1u` NAMED. Message presence alone means an idempotent re-assertion with a CONSTANT message appends a duplicate every run: three identical calls produced three identical records. Both runners call `set_plan_approved` with the hardcoded `FULL_AUTO_APPROVAL_MESSAGE` from two sites each, so this is a live path. Fixed by requiring a dedup rule in E-01. | the 3x-repeat scratch run showing 4 records; `oc_runipd.py:730-732`, `:2937`, `:6933`; `agy_runipd.py:830`, `:1975`, `:3990` |
| F-11 | MEDIUM | `.aw/records/specs/20260818-1525-02-*.spec.md:49,59,63,67,70` | The spec amendment is LARGER than E-07 described: R2, R6, AC1 and AC4 each state the latest-one rule, and `:49` both miscites the derivation's location (`:434`) and states its LAST-record behavior as a thing to protect. Amending only OQ-2 would leave four normative statements contradicting the code. | grep of the spec |
| F-12 | MEDIUM | E-04's "block the slim" instruction | E-04 asked for a coupling that contradicts the maintainer's OQ-01 ruling and describes a state E-08 removes: after E-08 there is no slim to block, and making the inline (now durable) write conditional on a sidecar (now advisory) result inverts the durability model. Narrowed to "report, never swallow, and always write inline". | OQ-01's ruling text; E-08's effect |
| F-13 | MEDIUM | `tests/test_attention_contract.py:188-196`; `tests/test_history_routing.py:52-55` | The existing fixtures are oldest-first or single-record, so they pass under either newest-record rule. That is why F-8's contradiction survived review of `awhistory-02`, and why E-06 must add a newest-first case. | test source read |
| F-14 | LOW | `.aw/records/specs/20260818-1525-02-*.spec.md:4` | The spec is `Status: implemented`, whose only legal transitions are `deferred`/`superseded`, so E-07 must amend text and use `aw specs note` without touching status. The authored item did not say this. | `SPEC_TRANSITIONS['implemented']` |

## Proposed changes (ordered, validatable)

1. E-01 makes message presence PLUS a dedup rule the discriminator, following the four existing hoisted-field precedents without re-introducing the duplicate-growth trap.
2. E-02 fixes `last_history_at` to mean the newest record and reconciles the two contradictory readers. THIS MUST LAND FIRST; nothing else in group 2 is safe before it.
3. E-08 then stops slimming for specs and backlog, per the maintainer's ruling.
4. E-03 verifies the legacy multi-record files are safe by construction, rewriting none of them.
5. E-04 stops a failed sidecar write from being invisible at all three sites, without coupling the inline write to it.
6. E-05 adds `aw backlog note` so annotation no longer routes through the setter.
7. E-06 pins all of it, including a newest-first `last_history_at` case that fails before E-02.
8. E-07 amends the six spec passages that would otherwise contradict the shipped code.

## Deferred / out of scope (with reason)

- THE CONFIRMATION AND TERMINAL-REOPEN GUARDS (`f5pttg`): Order 01 of this Set. Same file, different failure class (unguarded mutation rather than lost provenance) and different tests.
- REVERTING `awhistory-02`'s SLIMMING: explicitly rejected. It is a reviewed decision and reverting it would break the `attention` derivation it was shaped around; F-6 records that an earlier report of mine wrongly proposed this.
- CHANGING `aw attention`'s DERIVATION: out of scope and must keep working unchanged; E-06 asserts it.
- PLAN/IPD HISTORY BEHAVIOR: deliberately exempt from slimming per `awhistory-02`'s explicit guard (IPD-S405 needs the inline `executed` entry). Not touched.

## Scope check

- Over-scope: none. `.aw/.gitignore` was declared while OQ-01 was open and has been REMOVED now that the maintainer chose inline provenance over tracking the sidecar; the ignore rule is untouched. Every declared path is touched by a named item: `status_set.py` (E-01), `attention_contract.py` and `plan_readiness.py` (E-02's reader reconciliation), `backlog.py` and `specs.py` (E-08, E-04), `cli.py` and `.aw/records/backlog/README.md` (E-05), the awhistory spec (E-07), and the four test modules (E-02, E-08, E-06).
- ADDED AT EXECUTION (2026-09-22), three paths that were necessary and undeclared, declared now rather than committed silently: `agent_workflows/record_history.py` hosts E-04's shared `append_advisory` helper, which is the ONE place the report-never-swallow decision lives (putting it in the three call sites instead would have been the duplication E-04 exists to prevent); `agent_workflows/command_surface.py` had to DECLARE E-05's new `backlog note` CLI leaf, because `tests/test_run_analytics_cli.py::DeclarationContractTests::test_no_new_undeclared_parser_leaf` and `tests/test_run_analytics_export.py::test_no_new_undeclared_leaf_was_introduced` fail closed on an undeclared leaf (both were red until the declaration was added); and `tests/test_backlog.py` held a THIRD test asserting the slimming (`test_set_transitions_status_moves_file_and_appends_history`, `assertEqual(len(inline), 1)`) that E-08 necessarily changes, and now also carries E-05's `BacklogNoteVerbTests`. The plan predicted one slimming-asserting test on the specs side and one on the backlog side; there were three in total.
- Under-scope: none remaining. E-03 (the legacy files) and E-04 (the swallowed failure) were absent from the two backlog items and were added from measurement. E-07 (the spec amendment) was added AFTER the maintainer's ruling. AT REVIEW: E-02 was SPLIT into a reader fix (E-02) plus the writer change (E-08) because the authored single item was self-contradictory (F-8) and would have broken the property it promised to protect; `attention_contract.py`, `plan_readiness.py`, `tests/test_attention_contract.py` and `tests/test_work_kind.py`-adjacent fixtures were UNDECLARED and are now in `- Scope-Paths:`; and E-01 gained the dedup requirement the measured trap (F-10) demands.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. THE BASELINE AND TWO EXPERIMENTS ARE ALREADY MEASURED at `be6d2ab9` and must be reproduced rather than re-derived: unpatched, `5959 passed, 3 skipped, 2 xfailed`; with E-01's minimal patch alone, still `5959 passed` (so E-01 breaks no test, which is exactly why the duplicate-growth trap needs its OWN new assertion rather than trusting the suite); with E-08's specs half applied as authored, `1 failed, 5958 passed`, the failure being `tests/test_history_routing.py::HistoryRoutingTests::test_specs_slims_inline`, which asserts the slimming and must be REWRITTEN, not deleted.

Beyond the suite: a FRESH CLONE demonstration for E-08 (clone the repository, or push to a bare repo and clone from it, then read the history that a note verb wrote), because reading the same working tree cannot distinguish tracked from ignored; the re-counted before/after number of legacy multi-record files for E-03 (139 at review, expected NOT to fall); an induced sidecar failure at each of the three sites for E-04; the 3x-identical-message run for E-01 showing ONE record; and the corpus re-scan for E-02 showing the 273 mismatching plans now report their newest date.

## Spec / documentation sync

`.aw/records/backlog/README.md` is DECLARED IN SCOPE and edited by E-05, which documents the new `note` verb; the README currently describes the verb set and becomes incomplete the moment the verb exists.

SPEC `20260818-1525-02` (`.aw/records/specs/20260818-1525-02-sidecar-metadata-and-history.spec.md`) IS AMENDED BY THIS PLAN AND IS DECLARED IN `- Scope-Paths:`. Its OQ-2 ruled that the inline `## Workflow history` of specs and backlog items keeps only the LATEST ONE record, on the premise that the full log lives in the global sidecar. The maintainer reversed that premise on 2026-09-10 (OQ-01 above): inline history is the durable home for these two types, matching plans. E-07 carries the amendment.

WHY THE AMENDMENT IS REQUIRED RATHER THAN OPTIONAL: the repository's own rule is that a plan changing behavior a spec describes SHOULD carry the spec edit in the same change, so the two never drift, and `aw oc run` announces declared spec edits before a run starts. Landing E-02 without E-07 would leave a shipped spec instructing the opposite of the code, which is the exact drift this plan exists to close in the history layer.

WHAT THE AMENDMENT MUST AND MUST NOT SAY. It MUST record that inline history is preserved for specs and backlog, that the sidecar remains as a machine-local activity log rather than the durable store, and that the change was a maintainer ruling with its date. It MUST NOT delete OQ-2's original reasoning: the slimming was a considered decision with a real motivation (`aw attention`'s `last_history_at`), and that motivation still constrains the design, so the record of why it was chosen stays and is marked superseded rather than erased.

## Open questions

### OQ-01: Which durability option should E-02 implement, and does it require amending the awhistory spec?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): **KEEP THE REASONING IN THE RECORD, MATCHING WHAT PLANS ALREADY DO.** That is option (2), inline provenance, and it therefore REQUIRES AMENDING spec `20260818-1525-02` OQ-2, which specified a single latest-one stub line for specs and backlog. `.aw/records/specs/20260818-1525-02-*.spec.md` must be added to `- Scope-Paths:` before execution, and the amendment must state that inline history is the durable home for these two types.
  WHAT DECIDED IT, and the reasoning is the maintainer's: PLANS ALREADY WORK THIS WAY AND ARE UNAFFECTED. Tracing the actual CALLERS (the maintainer asked twice for the actions, not the writer, which is what surfaced this) showed that the sidecar is written by exactly nine deliberate record-keeping actions: `aw backlog new`, `aw backlog set`, `aw specs set`, `aw specs note`, `aw rename <type>`, `aw group <type>`, the plans and research ref-rewrite passes, and the explicit `aw record-history` verb. `status_set.py` writes to it ZERO times, and `ipd_lifecycle`'s only reference is a READER (`_plan_status_events` parses INLINE history to derive status). So plan history is already inline, already version-controlled, and already protected by `ipd_lint` IPD-S405, which requires the inline `executed` entry. The August decision left specs and backlog on a DIFFERENT durability model from plans, and that split is the actual defect. One model, the one that already works, is the answer.
  CONSEQUENCES FOR THIS PLAN, which narrow it in one place and widen it in another. NARROWED: the sidecar does NOT need to be tracked, so `.aw/.gitignore` comes OUT of `- Scope-Paths:` and the `union` merge-driver question is moot. WIDENED: E-02 becomes "keep inline history for specs and backlog" rather than "track the sidecar", E-03's 143 legacy multi-record files stop being at risk BY CONSTRUCTION (nothing slims them any more) rather than needing migration, and the awhistory spec must be amended in the same change.
  THE ONE CONSTRAINT THAT MUST SURVIVE, and it is why `awhistory-02` slimmed at all: `aw attention`'s `last_history_at` derivation reads the inline record and was the stated reason for keeping exactly one line. Keeping MORE lines must not break it.
  CORRECTED AT REVIEW: THE "EXISTENCE PROOF" IN THE NEXT SENTENCE WAS FALSE, and the correction is why this Set was re-ordered. The authored text claimed "the plans side is the existence proof that it works (plans carry many inline records and `attention` handles them)". It does not handle them: `last_history_at` (`attention_contract.py:540-549`) takes the LAST record in FILE order while plans are NEWEST-FIRST, so 273 of 581 multi-record plans already report the wrong date. The maintainer's RULING (inline provenance, one model for all three types) is unaffected and stands; what changed is that delivering it safely requires FIXING the reader first, which is now E-02, with the writer change as E-08. `plan_readiness.extract_newest_history_entry` is indeed the correct shared reader to follow, and it is the one that already implements the right rule. E-06 asserts the corrected property with a falsifiable test.
  ALSO CORRECTED, TWICE, AND WORTH RECORDING SO NEITHER ERROR REPEATS: I first reported the slimming as an accidental renderer bug (it is a reviewed decision), and then warned that tracking the sidecar risked constant merge conflicts (it is append-only with ~11 records/day and a one-line `union` merge setting would have handled it, so the warning was overstated). Neither claim survived measurement. The decision above rests on the caller trace, which is evidence rather than inference. A THIRD correction was made at review and is recorded in F-8/F-9 above: the claim that plans prove the derivation tolerates multi-record newest-first history.

### OQ-02: When E-02 reconciles the two contradictory "newest record" readers, should `last_history_at` change meaning, or should the writers change ordering?

- Blocking: no
- Status: open
- Owner: maintainer
- Finding: F-8, F-9
- Resolution or deferral rationale: NOT BLOCKING, because either answer delivers the required property (`last_history_at` reports the genuinely newest record) and E-02 is written to demand that outcome rather than a mechanism. Recorded because the two routes have different blast radii and the choice is a contract judgement rather than a mechanical one, and because a reviewer should not silently pick between them.
  ROUTE A, CHANGE THE READER (recommended): make `last_history_at` take the NEWEST record by date rather than the last in file order, delegating to the rule `plan_readiness.extract_newest_history_entry` already implements and documents. Blast radius is one function plus the oldest-first fixture at `tests/test_attention_contract.py:188-196`; it FIXES 273 currently-wrong plan readings with zero files rewritten; and it makes newest-first the single canonical ordering across all three trees. Cost: it changes what a shipped, spec-described derivation returns, and the awhistory spec's `:49` text must be amended (E-07 already does this).
  ROUTE B, CHANGE THE WRITERS to append oldest-first so the last record really is the newest. Blast radius is far larger and mostly bad: it contradicts `status_set.py:872-879`'s documented newest-first contract, contradicts `extract_newest_history_entry`'s explicit warning against the last-record rule, and would leave 581 existing multi-record plans in the opposite order from every new one unless they are rewritten, which the shared-checkout rule forbids.
  RECOMMENDATION: Route A. Not resolved unilaterally because it changes the observable meaning of a derivation named in an implemented spec, and because the maintainer may prefer to hear the 273-plan number before that changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a same-status call WITH `--message` showing exactly ONE new record written. Paste THE SAME MESSAGE REPEATED THREE TIMES showing exactly ONE record total in the file, since the measured pre-fix behavior was three duplicates (F-10) and this is the assertion that proves the dedup rule works. Paste a same-status call WITHOUT a message showing nothing written. State the dedup rule you implemented, and name which of the four existing hoisted-field precedents you followed.
  - Observed evidence: VERIFIED. Three identical same-status calls with `-m` produced exactly ONE record (pre-fix: three); a call with no message left the file byte-identical; a different message was still recorded. Dedup rule + precedent named, and 5 CLI-level regression tests pass. Detail below.
    THE DEDUP RULE IMPLEMENTED: `status_set.same_status_message_is_duplicate(text, status, date, message)` returns True only when the artifact's NEWEST existing record carries the same status token, the same date, and a byte-identical message. The write happens when the message is non-empty AND that predicate is False. Compared against the NEWEST record ONLY (not the whole file), so a genuinely new note that reuses an older wording is still recorded; the ACTOR is deliberately not compared. Recorded as DECISION 24-vhbvwz-D2.
    PRECEDENT FOLLOWED: the `From-Backlog` write (`status_set.py`, "the same hoisted, status-branch-independent shape as the Blocks-Release write above, so `aw ipd set --from-backlog <id6|->` persists even on a no-op (same-status) transition"). That is the closest of the four because it was hoisted for exactly this reason; the other three (`Blocks-Release`, `Item-Dependencies`, `Priority`) carry the same shape.
    THREE IDENTICAL CALLS, then a no-message call, then a DIFFERENT message, driven through `apply_status_change` on a real plan file:
    ```
    === THREE IDENTICAL same-status calls WITH --message ===
    - 2026-09-22 reviewed (aw set): identical note
    - 2026-01-01 draft (aw set): created.
    records in section: 2

    === a same-status call with NO message ===
    file unchanged: True

    === a DIFFERENT message on the same status ===
    - 2026-09-22 reviewed (aw set): a genuinely new reason
    - 2026-09-22 reviewed (aw set): identical note
    - 2026-01-01 draft (aw set): created.
    ```
    So: ONE record from three identical calls (pre-fix behavior was three), nothing at all without a message, and a new message still recorded.
    THE SAME PROPERTIES THROUGH THE CLI, pinned as regressions in `tests/test_status_set.py::SameStatusMessageIsRecordedTests` (5 tests: one-record, three-identical-yields-one, new-message-after-a-repeat, no-message-is-a-true-no-op, and the predicate's own truth table):
    ```
    tests/test_status_set.py .....
    5 passed, 76 deselected in 1.43s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `last_history_at` returning the NEWEST date for a NEWEST-FIRST multi-record section, and show the same assertion FAILING before the fix (that failure is the proof the test is falsifiable). Paste the corpus re-scan showing the previously-mismatching multi-record plans (273 at review) now report their newest date, with ZERO plan files rewritten (`git status --porcelain` proving it). State which reader is now canonical and show the contradictory second reader is gone or delegates, so no two rules can disagree about "newest" again.
  - Observed evidence: VERIFIED. `last_history_at` now returns the NEWEST date on a newest-first section, single-sourced in `attention_contract.newest_history_record` which both readers consume; corpus re-scan shows 533 artifacts newly correct with ZERO files rewritten; mutation check reddens 7 tests. Two residues reported and filed as `jhrao5`. Detail below.
    THE CANONICAL READER: `attention_contract.newest_history_record(history_lines)` - the FIRST record of the bounded section matching `HISTORY_RECORD_RE`. `last_history_at` now delegates to it (it reads the record and returns its date), and `plan_readiness.extract_newest_history_entry` delegates to it too (imported as `_newest_history_record`), so the contradictory second rule is GONE rather than merely aligned: neither function contains a scan of its own any more. Pinned by `tests/test_attention_contract.py::HistoryTests::test_the_newest_record_rule_is_single_sourced`, which asserts the plan-side reader returns exactly what the shared rule returns.
    THE RULE IS POSITIONAL, NOT GREATEST-BY-DATE, and that was measured rather than assumed. A date-max rule changes which record `extract_newest_history_entry` returns for 67 plans, and for 20 of them it flips `plan_readiness.history_verdict_approves` from False to True (e.g. `20260712-unify-install-00-wbr6u8` -> `APPROVE`, `20260802-ipdstruct-01-ktv5h3` -> `APPROVE`), silently widening the unattended approval gate. Recorded as DECISION 24-vhbvwz-D1 with OQ-02's Route A/B analysis.
    NEWEST-FIRST MULTI-RECORD SECTION, and the mutation check proving the assertion is falsifiable. With `newest_history_record` reverted to the last-record rule (the pre-fix behavior):
    ```
    MUTATION 2 APPLIED: newest_history_record reverted to the LAST-record rule (the E-02 defect)
    FAILED tests/test_plan_readiness.py::ExtractorTests::test_every_history_shape_yields_its_newest_bounded_record
    FAILED tests/test_plan_readiness.py::ReviewEntryDiscriminatorTests::test_the_newest_review_records_verdict_is_read_from_every_history_shape
    FAILED tests/test_history_routing.py::HistoryRoutingTests::test_backlog_set_appends_sidecar_and_preserves_inline
    FAILED tests/test_history_routing.py::HistoryRoutingTests::test_specs_preserves_inline
    FAILED tests/test_attention_contract.py::HistoryTests::test_the_newest_record_rule_is_single_sourced
    FAILED tests/test_attention_contract.py::HistoryTests::test_last_history_at
    FAILED tests/test_attention_contract.py::HistoryTests::test_newest_first_section_yields_its_newest_record
    7 failed, 78 passed in 3.18s
    ```
    Reverted, and green again:
    ```
    MUTATION 2 REVERTED in place
    tests/test_attention_contract.py ...................................     [ 41%]
    tests/test_history_routing.py ..........                                 [ 52%]
    tests/test_plan_readiness.py ........................................    [100%]
    85 passed in 2.51s
    ```
    THE CORPUS RE-SCAN, with the production parser (`attention._history_section_lines` + `HISTORY_RECORD_RE`) at `2362b102`. Re-measured at execution rather than reusing the review figure: the review said 273 of 581 multi-record plans; the tree has grown, and the number is now 373 of 679.
    ```
    plans:   multi=679 wrong_before(last-rule)=373 FIXED_by_first_rule=372 still_wrong=1
    backlog: multi=200 wrong_before(last-rule)=153 FIXED_by_first_rule=153 still_wrong=0
    specs:   multi=21  wrong_before(last-rule)=8   FIXED_by_first_rule=8   still_wrong=0
    TOTAL multi=900 newly-correct=533 oldest-first-legacy=77
    ```
    533 artifacts now report their newest date correctly. TWO RESIDUES, reported rather than hidden: ONE plan is wrong under BOTH rules because its own records are out of date order internally, and 77 artifacts (66 plans, 3 backlog items, 8 specs) store their history OLDEST-FIRST on disk, so they now report their oldest date where the positional last-record rule happened to be right about them. That is a DATA problem (the writer/author disagreement backlog `tk1gqo` catalogues), not a reader problem, and fixing it in the reader is exactly the date-max change measured above to widen the approval gate. Filed as backlog `jhrao5` (bug, `Blocks-Release: next`) with the measurement and the recommended fix (the explicit `seq` field spec `2vev8j` 4.3 already approves).
    ZERO FILES REWRITTEN: `git status --porcelain .aw/records/` after the whole E-02 pass listed only `.aw/records/backlog/README.md` (E-05's own documentation edit). No plan, spec or backlog artifact was touched to achieve any of the above.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste a second `aw specs note` and a second `aw backlog set` on the same artifacts showing the EARLIER record still present, newest-first. Paste the rewritten `test_specs_slims_inline` (renamed or re-asserted to preservation, NOT deleted) and its module docstring update. Paste a FRESH CLONE (or bare-repo push then clone) in which the history written by a note verb is READABLE, with the command and its output; reading the same working tree does NOT satisfy this, because it cannot distinguish tracked from ignored. Confirm `last_history_at` still reports the NEWEST date on those now-multi-record files, which is what E-02 guarantees.
  - Observed evidence: VERIFIED. This plan's own spec amendment kept the prior `implemented` record inline, newest-first; a real legacy 11-record backlog item went to 12, not 1; the three slimming-asserting tests were REWRITTEN to assert preservation; a real `git clone` test reads the note back while the gitignored sidecar is absent. Detail below.
    A SECOND `aw specs note` ON A REAL SPEC, namely this plan's own E-07 amendment to `20260818-1525-02`, which is the end-to-end proof the plan asked for:
    ```
    ## Workflow history

    - 2026-09-22 note (aw specs): AMENDED by plan vhbvwz (setterguard Order 02) per the maintainer's 2026-09-10 ruling: ...
    - 2026-08-19 implemented (aw specs): Implemented by the awhistory Set (global history.jsonl sidecar + writer routing + inline slimming + migration excluding plans + aw record-history verb); suite 1079 passed 1 skipped.
    ```
    The prior `implemented` record SURVIVED, newest-first. Pre-fix this call would have replaced it with the single new line. And the derivation agrees:
    ```
    spec inline records: 2
    last_history_at: 2026-09-22      # the NEWEST record's date, which is what E-02 guarantees
    ```
    A SECOND `aw backlog set` ON A REAL LEGACY ITEM (`tk1gqo`, 11 records, copied byte-for-byte into a sandbox so the shared checkout is untouched):
    ```
    REAL legacy backlog item 20260901-historder-01-tk1gqo-lifecycle-history-order-mismatch.backlog.md
      records BEFORE: 11
      aw backlog set rc=0
      records AFTER: 12  (prior records preserved: True)
      newest record leads: '- 2026-09-22 set (aw backlog): a real transition on a real legacy file'
      oldest prior record still present: '- 2026-09-01 corrected (opencode/...): ...' -> True
    ```
    THE REWRITTEN TESTS, renamed rather than deleted, each asserting PRESERVATION where it asserted slimming: `test_specs_slims_inline` -> `test_specs_preserves_inline` (now asserts all three records present in newest-first order plus `last_history_at == "2026-01-03"`); `test_backlog_set_appends_sidecar_and_slims_inline` -> `test_backlog_set_appends_sidecar_and_preserves_inline` (asserts 3 records, the new one leading, and the sidecar record STILL written); and `tests/test_backlog.py::test_set_transitions_status_moves_file_and_appends_history`, a third test that also asserted `len(inline) == 1`, now asserts 2 with the transition leading and `created` beneath. The module docstring of `tests/test_history_routing.py` was rewritten too: its old first line said writers "slim inline history to the latest one record"; it now states preservation and records WHY the reversal happened (the sidecar is gitignored).
    THE FRESH CLONE, as a real test rather than a one-off shell run: `tests/test_history_routing.py::HistoryRoutingTests::test_specs_note_history_survives_a_fresh_clone` commits a spec in a sandbox repo that gitignores `records/history.jsonl` exactly as this repository does, runs `aw specs note`, commits, `git clone`s into a separate directory, and asserts from the CLONE that both the new note AND the pre-existing record are readable - and that `.aw/records/history.jsonl` is NOT present there, which is what proves the assertion is about tracked content rather than a file that came along for the ride.
    ```
    tests/test_history_routing.py ..........
    10 passed in 1.06s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the BEFORE count of tracked files carrying more than one inline record (RE-COUNTED at execution; 139 at review, not the 143 originally authored) and the AFTER state, and state the method. Demonstrate on ONE real legacy file that a `set` call no longer drops its prior records. If any tracked file was rewritten in bulk, say how many and paste the diffstat, since this is a shared checkout.
  - Observed evidence: VERIFIED. 221 tracked backlog items and specs carry more than one inline record (re-counted at execution; 139 at review); two REAL legacy files kept every prior record through a real transition; ZERO files rewritten in bulk. A defect found during this verification (prose-quoted records promoted into history) was fixed and pinned. Detail below.
    METHOD: the production parser (`attention._history_section_lines` + `attention_contract.HISTORY_RECORD_RE`) over every `*.backlog.md` under `.aw/records/backlog/` and every `*.spec.md` under `.aw/records/specs/`, counting files with more than one matching record. Re-counted at execution as the item instructs, not reused from review.
    ```
    tracked backlog items + specs: 530
    carrying MORE THAN ONE inline history record: 221
    ```
    221, not the 139 measured at review and not the 143 originally authored. The count drifts in a shared checkout exactly as E-03 predicted, and the item's point does not depend on the value: what matters is that the number does NOT FALL after a transition, which is now true by construction because nothing slims.
    THE DEMONSTRATION ON REAL LEGACY FILES (both copied byte-for-byte into a sandbox; the tracked originals were never written to):
    ```
    REAL legacy backlog item 20260901-historder-01-tk1gqo-lifecycle-history-order-mismatch.backlog.md
      records BEFORE: 11
      aw backlog set rc=0
      records AFTER: 12  (prior records preserved: True)

    REAL legacy spec 20260725-0957-01-external-delivery-and-skills.spec.md
      records BEFORE: 2
      aw specs note rc=0
      records AFTER: 3  (prior records preserved: True)
      every prior record survived: True
    ```
    ZERO FILES REWRITTEN IN BULK. `git status --porcelain .aw/records/` after this verification showed only `.aw/records/backlog/README.md` (E-05's documentation edit). No diffstat to paste because no legacy artifact was modified.
    A FINDING THE VERIFICATION PRODUCED, which is what E-03 exists to catch and which would have corrupted 1 of the 2 real files above. The first E-08 implementation scanned the whole post-heading region and matched `line.strip()`, so FIVE INDENTED, PROSE-QUOTED history lines inside `tk1gqo` (it is a bug report about history ordering, and it quotes history lines verbatim) matched as records and were re-emitted into the item's own history: 11 records became 17, and quoted examples were promoted into real provenance. Fixed by bounding the block exactly as `_strip_metadata_and_history` bounds it and requiring a record to start at column zero (`backlog._prior_history_records`), and pinned by `tests/test_history_routing.py::LegacyMultiRecordItemsSurviveATransitionTests::test_prose_quoted_record_lines_are_not_promoted_into_history`. `specs._append_history` was checked against the same hazard and is safe, because it preserves the section verbatim rather than re-emitting it.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste an INDUCED sidecar-write failure at EACH of the three sites (`backlog.py:544-558`, `specs.py:145-156`, `backlog.py:443`) showing the failure REPORTED and the inline record present anyway. Show no bare `except Exception: pass` remains around a history write. State plainly that you did NOT implement the authored "block the slim" coupling and why (F-12), or if you did, justify it against the OQ-01 durability ruling.
  - Observed evidence: VERIFIED. An induced `OSError` at each of the three sites is REPORTED on stderr and the inline record is present anyway; no bare `except Exception: pass` remains around a history write; the authored 'block the slim' coupling was deliberately NOT implemented (F-12) and no ordering was found where a sidecar failure can cost the inline record. Detail below.
    THE THREE SITES, located at execution (the authored line numbers had drifted): `backlog.run_new`'s `if item.id:` sidecar block, `backlog.run_set`'s sidecar block, and `specs._sidecar_append`. The plan's third citation `backlog.py:443` is now `_render_item`, which writes the INLINE `created` record and never touched the sidecar, so the three real call sites are the two in `backlog.py` plus the one in `specs.py`.
    AN INDUCED FAILURE AT EACH (`record_history.append` patched to raise `OSError(28, "No space left on device")`):
    ```
    SITE 1 backlog.run_new: rc= 0
      stderr: aw backlog new: warning: could not append to the history sidecar (.aw/records/history.jsonl) for 20260922-demo-01-ybzq5k-a-summary.backlog.md: OSError: [Errno 28] No space left on device. The inline `...
      inline record present anyway: True
    SITE 2 backlog.run_set: rc= 0
      stderr: aw backlog set: warning: could not append to the history sidecar (.aw/records/history.jsonl) for 20260101-demo-01-aaa222-x.backlog.md: OSError: [Errno 28] No space left on device. The inline `## Workf...
      inline record present anyway: True
      prior record preserved: True
    SITE 3 specs.run_note: rc= 0
      stderr: aw specs: warning: could not append to the history sidecar (.aw/records/history.jsonl) for aaa333: OSError: [Errno 28] No space left on device. The inline `## Workflow history` record is the durable o...
      inline record present anyway: True
    ```
    Pinned as regressions in `tests/test_history_routing.py::SidecarFailureIsReportedTests` (one test per site plus one over the shared helper's return value).
    NO BARE SWALLOW REMAINS AROUND A HISTORY WRITE. All three sites now call the single shared `record_history.append_advisory`, which warns on stderr and returns False. Two `except Exception` blocks remain in these modules and NEITHER is around a history write: `specs._spec_files` (a read-path resolver fallback) and `specs._review_attestation_refusal` (documented fail-closed on an unreadable reviews tree). The one inside `append_advisory` is deliberately broad and is the REPORTING path, not a swallow.
    I DID NOT IMPLEMENT THE AUTHORED "BLOCK THE SLIM" COUPLING, and F-12 is the reason. After E-08 there IS no slim to block, so the instruction describes a state this plan removes; and making the INLINE write (now the durable one) conditional on a SIDECAR result (now advisory) would inverte the exact durability model the maintainer's OQ-01 ruling chose. The narrower remedy was implemented instead: report the failure, and write the inline record regardless. I checked for the residual hazard the item asks about and found NONE: at both `backlog` sites the inline record is already assembled into `rendered` before the sidecar call and is written by the `atomic_write` that follows, and in `specs.run_note`/`run_set` the sidecar call cannot return early or raise, so no ordering exists in which a sidecar failure costs the inline record. Recorded as DECISION 24-vhbvwz-D3.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `aw backlog note <item> --message "..."` recording a note with the item's STATUS UNCHANGED and its file NOT moved. Paste `aw specs note` still working unchanged. Paste the README diff documenting the new verb.
  - Observed evidence: VERIFIED. `aw backlog note` records a note with the status UNCHANGED and the file NOT moved, and a second note preserves the first; `aw specs note` is unchanged (it carried this plan's own amendment); README documents the verb; the new CLI leaf also had to be DECLARED in `command_surface.py` to satisfy two fail-closed declaration tests. Detail below.
    `aw backlog note` THROUGH THE REAL CLI (`python3 -m agent_workflows backlog note aaa444 --message ...`):
    ```
    rc: 0
    stdout: aw backlog note: appended a history record to /tmp/.../backlog/open/20260101-demo-01-aaa444-x.backlog.md
    --- file after ---
    - Id: aaa444
    - Status: open
    - Priority: medium
    - Work-Kind: chore
    - Set: demo
    - Summary: a summary

    ## Workflow history
    - 2026-09-22 note (aw backlog): the reason this matters
    - 2026-01-01 created (aw backlog): a summary

    still in open/ (file NOT moved): True
    ```
    STATUS UNCHANGED (`- Status: open`), FILE NOT MOVED (still in `open/`), and a second note preserved the first:
    ```
    - 2026-09-22 note (aw backlog): a second reason
    - 2026-09-22 note (aw backlog): the reason this matters
    - 2026-01-01 created (aw backlog): a summary
    ```
    `aw specs note` STILL WORKS UNCHANGED: it recorded this plan's own E-07 spec amendment (see V-08 and V-07), and its behavior tests pass:
    ```
    tests/test_specs_verbs.py ...............
    ```
    Pinned by `tests/test_backlog.py::BacklogNoteVerbTests` (4 tests: records-without-changing-status-or-moving-the-file, a-second-note-preserves-the-first, refuses-an-empty-message-and-an-unknown-item, and the-cli-registers-the-verb).
    THE README DIFF (`.aw/records/backlog/README.md`, the "Verbs" section):
    ```
    +- `aw backlog note <id6|fname|path> --message "..."` append a history record WITHOUT changing the
    +  item's status and without moving its file. Use this whenever the intent is to record a reason, a
    +  decision, or a finding on an item. Reach for `set` only when the status actually changes: a
    +  same-status `set` is a transition call doing an annotation's job, and history is what suffers.
    ...
    +History is recorded INLINE in the item's `## Workflow history`, newest record first, and prior records
    +are kept. That inline block is the durable copy, because it is the one that is committed and therefore
    +the one that survives a clone. The `aw record-history <id6>` sidecar is an additional machine-local
    +activity log: it is gitignored, so never rely on it as the only home for a reason worth keeping.
    ```
    ALSO REQUIRED AND NOT IN THE AUTHORED ITEM: the new leaf had to be DECLARED in `command_surface.py`, because `tests/test_run_analytics_cli.py::DeclarationContractTests::test_no_new_undeclared_parser_leaf` and `tests/test_run_analytics_export.py::test_no_new_undeclared_leaf_was_introduced` fail closed on an undeclared CLI leaf. Both were red after registration and are green after the declaration was added (mirroring the `specs note` entry: `mutation`, `human_recipe="text"`, `mutation_gate="none"`, flags `--message`/`--date`, exits `(0, 2)`).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste all six assertions passing, naming each. Include a MUTATION CHECK on the `x6tk1u` fix (restore the early return, show the same-status-with-message test FAILS, revert, show it passes) AND a second mutation check on the newest-first `last_history_at` case (revert E-02's reader fix, show that test FAILS, restore, show it passes). A `last_history_at` assertion that passes both before and after E-02 is NOT acceptable evidence: it means the fixture is oldest-first and proves nothing (F-13).
  - Observed evidence: VERIFIED. All six required assertions pass, each named below, plus four added from measurement. BOTH mutation checks performed: restoring the early return reddens 3 E-01 tests, and reverting the reader rule reddens 7 including the newest-first `last_history_at` case; both reverted and green. Detail below.
    THE SIX REQUIRED ASSERTIONS, each named with the test that carries it:
    (a) a same-status call WITH a message records exactly ONE record - `test_status_set.py::SameStatusMessageIsRecordedTests::test_a_same_status_call_with_a_message_records_exactly_one_record`.
    (b) THE SAME MESSAGE REPEATED THREE TIMES yields exactly ONE record - `...::test_the_same_message_repeated_records_once` (plus `test_a_genuinely_new_message_is_still_recorded_after_a_repeat`, which proves the dedup rule does not over-reach, and `test_the_dedup_predicate_is_exposed_and_pure`).
    (c) a same-status call WITHOUT a message records nothing - `...::test_a_same_status_call_without_a_message_records_nothing` (asserts the file is byte-identical).
    (d) history written by a note verb is readable in a FRESH CLONE - `test_history_routing.py::HistoryRoutingTests::test_specs_note_history_survives_a_fresh_clone` (real `git clone`, and it also asserts the gitignored sidecar is ABSENT there).
    (e) an induced sidecar failure at each of the three sites is reported and the inline record is present anyway - `test_history_routing.py::SidecarFailureIsReportedTests` (4 tests).
    (f) THE DERIVATION DIRECTLY: a NEWEST-FIRST multi-record section yields the NEWEST date - `test_attention_contract.py::HistoryTests::test_newest_first_section_yields_its_newest_record`, joined by `test_the_newest_record_rule_is_single_sourced`. The pre-existing oldest-first fixture (`test_last_history_at`, the F-13 fixture) was KEPT but is now documented in the class docstring as NOT evidence about the rule, and its expectation was corrected to the newest-first answer.
    Two further tests were added from measurement rather than from the item: `LegacyMultiRecordItemsSurviveATransitionTests::test_a_legacy_item_keeps_every_prior_record_through_a_transition` and `::test_prose_quoted_record_lines_are_not_promoted_into_history` (the defect V-03 records), plus `BacklogNoteVerbTests` (4) for E-05.
    MUTATION CHECK 1, on the `x6tk1u` fix (the early return restored to unconditional):
    ```
    MUTATION 1 APPLIED: the unconditional early return (the x6tk1u defect) is back
    FAILED tests/test_status_set.py::SameStatusMessageIsRecordedTests::test_a_same_status_call_with_a_message_records_exactly_one_record
    FAILED tests/test_status_set.py::SameStatusMessageIsRecordedTests::test_the_same_message_repeated_records_once
    FAILED tests/test_status_set.py::SameStatusMessageIsRecordedTests::test_a_genuinely_new_message_is_still_recorded_after_a_repeat
    3 failed, 2 passed, 76 deselected in 2.82s
    ```
    Reverted:
    ```
    MUTATION 1 REVERTED
    tests/test_status_set.py .....
    5 passed, 76 deselected in 3.64s
    ```
    MUTATION CHECK 2, on E-02's reader (`newest_history_record` reverted to the last-record rule): 7 tests FAIL including the newest-first `last_history_at` case, then all 85 pass after the revert. Full output pasted in V-02. The newest-first assertion therefore FAILS before E-02 and PASSES after, which is the falsifiability F-13 demands.
    NO MUTATION SURVIVED: `git diff --stat` and a grep for the mutant text confirm both files are back to their intended state, and the final full-suite run below was made against that state.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the amended text for ALL SIX passages (OQ-2, R2 `:59`, R6 `:63`, AC1 `:67`, AC4 `:70`, and the `:49` citation), showing inline provenance stated with the maintainer's ruling and its date and the corrected derivation rule and location. Show OQ-2's original reasoning still present and marked superseded rather than deleted. Confirm the spec's `- Status:` is UNCHANGED at `implemented`. Then paste the spec's OWN `## Workflow history` proving the amendment's record was preserved inline alongside the prior records, which is the end-to-end proof that E-08 works on the specs path.
  - Observed evidence: VERIFIED. All six passages amended (Section 2.2 citation, R2, R6, AC1, AC4, OQ-2) with the ruling and its date; OQ-2's original reasoning preserved and labelled superseded, not deleted; `- Status:` UNCHANGED at `implemented`; the spec's own amendment record is preserved inline beside the prior one. Detail below.
    ALL SIX PASSAGES AMENDED in `.aw/records/specs/20260818-1525-02-sidecar-metadata-and-history.spec.md`, each carrying the amendment date and the maintainer's 2026-09-10 ruling:
    1. SECTION 2.2 CITATION (was `:49`): now states that the original text was wrong in BOTH halves - the location (`:434` is inside `TRANSITION_AUTHORITY`; the derivation was at `:610`) and the behavior, since "reads the LAST inline record's date" was itself the defect. States the corrected rule (`attention_contract.newest_history_record`, the FIRST record of the bounded section, consumed by both `last_history_at` and `plan_readiness.extract_newest_history_entry`) and the measurement (373/679 plans, 153/200 backlog, 8/21 specs misreported).
    2. R2 (was `:59`): "PRESERVE the full inline `## Workflow history`, newest-first" replaces "SLIM the inline `## Workflow history` to the LATEST ONE record line", with the gitignored-sidecar reason and the three lost `aw specs note` records.
    3. R6 (was `:63`): now says readers take the NEWEST record of the section rather than "the latest-one history line", and states plainly that `last_history_at`'s behavior DID change, deliberately and correctively.
    4. AC1 (was `:67`): now requires the writer to "prepend exactly one record ... leaving every prior record in place", naming the two tests that pin it.
    5. AC4 (was `:70`): now requires `last_history_at` to resolve to the NEWEST record's date ON A MULTI-RECORD SECTION, and records why a single-record fixture cannot tell the two rules apart (which is why the contradiction survived this spec's own review).
    6. OQ-2: retitled "RESOLVED, THEN SUPERSEDED 2026-09-10", `Status: resolved (superseded)`.
    OQ-2'S ORIGINAL REASONING IS PRESENT AND MARKED SUPERSEDED, NOT DELETED. The original resolution line is retained verbatim under an explicit "(ORIGINAL, 2026-08-18, PRESERVED AS SUPERSEDED - do not delete)" label, followed by a paragraph stating WHY it is kept: the slimming was a considered decision whose motivation (`aw attention`'s `last_history_at`) still constrains the design, so any future change must still satisfy that reader. The superseding resolution then records the ruling, why the original premise failed (`git check-ignore` resolves the sidecar to `.aw/.gitignore`), what decided it (the caller trace showing `status_set` writes to the sidecar zero times), that the sidecar is NOT removed, and that the original constraint was honored by fixing the reader FIRST.
    STATUS UNCHANGED:
    ```
    $ grep -n "^- Status:" ...20260818-1525-02-...spec.md
    4:- Status: implemented
    $ grep -c "^- Status: implemented" ...
    1
    ```
    No status transition was attempted; the amendment was recorded with `aw specs note`, which appends history without a status change, as E-07 requires (`implemented` legally transitions only to `deferred`/`superseded`).
    THE SPEC'S OWN HISTORY, which is the end-to-end proof E-08 works on the specs path: the amendment's record is preserved INLINE alongside the prior `implemented` record, newest-first, where the pre-fix writer would have replaced it.
    ```
    ## Workflow history

    - 2026-09-22 note (aw specs): AMENDED by plan vhbvwz (setterguard Order 02) per the maintainer's 2026-09-10 ruling: OQ-2's latest-one inline slimming is SUPERSEDED, ... Status deliberately UNCHANGED at implemented: the only legal transitions from there are deferred/superseded, and this is a text amendment, not a lifecycle move.
    - 2026-08-19 implemented (aw specs): Implemented by the awhistory Set (global history.jsonl sidecar + writer routing + inline slimming + migration excluding plans + aw record-history verb); suite 1079 passed 1 skipped.
    ```
    And the spec still conforms: `aw specs check: all specs conform.`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 8 E-leaves in 4 groups, at the upper end of comfortable. It stays one plan because all eight serve one property (a recorded reason must be durable) and share one test surface. E-07 (the spec amendment) was added after the maintainer ruled. E-08 was SPLIT OUT OF E-02 AT REVIEW because the authored E-02 bundled a reader fix with a writer change and, in that order, would have broken the very derivation it promised to protect (F-8); they are now separate items with an explicit dependency so the reader is correct before any writer keeps a second line.
- Cohesion rationale: E-01 is the discarded-message fix and is independent. E-02 is the READER correctness fix and is the precondition for the rest of group 2. E-08, E-03 and E-04 are then one durability concern in three parts: the writer, the existing content, and the failure path. E-05 is the ergonomic fix that removes the incentive to trigger either defect. E-06 is the shared regression surface, including the newest-first derivation case that is this plan's load-bearing test. E-07 keeps the spec from contradicting the code.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. If E-03 rewrites tracked legacy files, say how many and show the diffstat: this is a SHARED CHECKOUT and those artifacts belong to other agents' work. Never revert or commit a file you did not change. ORDERING IS A CORRECTNESS REQUIREMENT HERE, not a preference: do NOT land E-08 before E-02, because in that order every multi-record spec and backlog item silently starts reporting its OLDEST date as `last_history_at`.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved vhbvwz --by-human --message ...`) before execution. OQ-01 is RESOLVED (the maintainer ruled on 2026-09-10), and OQ-02 added at review is non-blocking, so no open question gates execution. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
