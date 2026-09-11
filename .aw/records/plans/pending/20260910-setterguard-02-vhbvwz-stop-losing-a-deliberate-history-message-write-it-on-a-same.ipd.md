# IPD: Stop losing a deliberate history message: write it on a same-status set and make durable history survive a clone

- Date: 2026-09-10
- Kind: child
- Concern: A deliberate provenance note can be silently lost in TWO different ways, and both exit 0. FIRST, `aw set` on a SAME-STATUS artifact DISCARDS an explicit `--message`: `status_set.apply_status_change` computes `content_changed`/`path_changed` and RETURNS EARLY (`status_set.py:867-870`) before the history write at `:880-896`, so the message is never recorded. Measured previously and filed as `x6tk1u` (high): roughly 2000 characters of evidence were swallowed at exit 0, caught only via `git status`. SECOND, and worse because it looks like it worked, the DURABLE history is GITIGNORED. Plan `awhistory-02` (`b0behn`, executed 2026-08-18, spec `20260818-1525-02` OQ-2) deliberately slimmed the inline `## Workflow history` block of specs and backlog items to the LATEST ONE record, on the premise that "the full chronological log lives in the global .aw/records/history.jsonl sidecar". That premise does not hold: `git check-ignore` confirms `.aw/.gitignore:11` ignores `records/history.jsonl`, so the durable log is PER-MACHINE and does not survive a clone.
  MEASURED CONSEQUENCE ON THIS REPOSITORY'S OWN RECENT WORK, which is what turns this from tidy-up into a real defect: three `aw specs note` calls during the 2026-09-10 setid cleanup recorded substantial reasoning (why one spec was superseded rather than revised, why invariant `I-16` was added and what the `I-09` misfiling was, why a finding must not be reported even at `info`). All three now exist ONLY in the gitignored sidecar; each spec shows exactly ONE inline record. The repository's own contract forbids precisely this: `AGENTS.md` states an answer must never live only in a gitignored tree because it "would not survive".
  AND THE EXPOSURE IS LARGE AND SILENT: 143 tracked backlog items and specs still carry MORE THAN ONE inline history record, all of it legacy, all of it committed-only, and one `aw backlog set` call on any of them truncates it to a single line. Meanwhile the sidecar on this machine covers 141 artifacts, so neither store is complete and the union exists nowhere in git.
  A NOTE ON WHAT IS *NOT* BROKEN, because an earlier report of mine got this wrong and the correction matters: the slimming itself is INTENTIONAL and reviewed, not an accidental renderer bug. `backlog._reattach_history` exists specifically to carry history forward and its own comment states the latest-one rule. Do not "fix" it by reverting to append-only; that would undo a reviewed decision and break the `aw attention` `last_history_at` derivation the decision was shaped around.
- Scope: The two ways a deliberate history message is lost. IN: writing the history record on a same-status transition when a `--message` is PRESENT (`x6tk1u`), without making every idempotent re-assertion grow duplicate history; making durable history survive a clone, by whichever of the recorded options review selects; closing the silent-failure hole where a swallowed sidecar write plus a successful inline slim loses a record entirely; adding the missing `aw backlog note` verb so annotating an item no longer requires abusing `set`; regression fixtures for each. OUT: the confirmation and terminal-reopen guards (Order 01 of this Set); reverting `awhistory-02`'s slimming decision; any change to `aw attention`'s derivation, which reads the latest inline record and must keep working.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/cli.py, .aw/records/specs/20260818-1525-02-sidecar-metadata-and-history.spec.md, .aw/records/backlog/README.md, tests/test_status_set.py, tests/test_history_routing.py
- Item-Dependencies: none
- Status: to-review
- Set: setterguard
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vhbvwz
- From-Backlog: x6tk1u

## Workflow history

- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `x6tk1u` (the discarded-message half) and `hg2oop` (the durability half), both filed after firing live during the setid cleanup. THE CENTRAL CORRECTION, made before authoring and recorded in `hg2oop` itself: I first reported the history truncation as an accidental renderer bug and was WRONG. Reading `awhistory-02`'s executed plan showed the slimming is a deliberate, reviewed decision with a stated rationale, so the defect is not the slim but the GITIGNORED destination it slims into. That correction changes the whole remedy: the plan must NOT restore append-only history. TWO NUMBERS MEASURED AT AUTHORING that size the problem: 143 tracked backlog items and specs still carry more than one inline record (legacy, committed-only, one `set` away from truncation), and the sidecar on this machine covers 141 artifacts, so neither store is complete and their union is nowhere in git. ALSO FOUND, and it is why E-04 exists: `backlog.py:557` swallows a sidecar write failure in a bare `except Exception: pass`, so a failed sidecar write followed by a successful inline slim loses the record with no signal at all.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a recorded reason durable: never silently discard a `--message`, and ensure the history a tool claims to have written can be read by someone who clones the repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop discarding the message

- [ ] E-01 WRITE THE HISTORY RECORD ON A SAME-STATUS TRANSITION WHEN A `--message` IS PRESENT. Today `apply_status_change` returns at `status_set.py:867-870` when neither content nor path changed, which is BEFORE the history write at `:880-896`, so an explicit note is discarded. Make message PRESENCE the discriminator: a same-status call WITH a non-empty message proceeds to the history write; a same-status call WITHOUT one keeps returning early. THE TRAP IS NAMED IN `x6tk1u` AND MUST BE HONORED: do NOT make every same-status call write, or idempotent re-assertion (which several tools and drivers perform) grows duplicate history on every invocation. FOLLOW THE PATTERN THAT ALREADY EXISTS IN THIS FUNCTION rather than inventing one: the `Blocks-Release`, `From-Backlog`, `Item-Dependencies` and `Priority` writes were each already hoisted out of the status-change branch for exactly this reason, so there are four precedents in the same body for "this field is written even when the status did not move".
  - Depends on: none
  - Expected outcome: `aw set <current-status> <artifact> --message "..."` records the message; the same call without a message writes nothing and stays idempotent.
  - Execution state: pending

### Task group 2: make durable history actually durable

- [ ] E-02 KEEP THE REASONING IN THE RECORD FOR SPECS AND BACKLOG, matching what plans already do, per the maintainer's 2026-09-10 ruling (OQ-01). Stop slimming the inline `## Workflow history` to a single line in `backlog._reattach_history` (`backlog.py:628-649`) and in `specs._append_history`/`_sidecar_append` (`specs.py:138-148`, `:342`), so a prior record is PRESERVED and the new one is added, exactly as `status_set.py`'s plan writer already does. KEEP WRITING THE SIDECAR TOO: it is a useful machine-local activity log and nine actions feed it; this item changes only whether the INLINE record is truncated. FOLLOW THE PLANS WRITER RATHER THAN INVENTING AN ORDER: `status_set.py:872-879` documents that plan history is NEWEST-FIRST (the new record is inserted directly under the heading) and that a reader wanting the latest entry must take the FIRST record via the shared `plan_readiness.extract_newest_history_entry`. Match that ordering so all three record types read identically and no second parser appears.
  THE CONSTRAINT THAT MUST SURVIVE, and it is the whole reason slimming existed: `aw attention`'s `last_history_at` derivation (`attention_contract.py:434`) reads the inline record, and `awhistory-02` kept exactly one line to protect it. Keeping MORE lines must not break it. Plans are the existence proof that it works, since they carry many inline records today and `attention` handles them; verify rather than assume, and if the derivation needs the newest-first ordering to be correct, say so.
  - Depends on: none
  - Expected outcome: a second `aw backlog set` or `aw specs note` on the same artifact leaves the earlier record in place; the file's history reads newest-first like a plan's; `aw attention` still derives `last_history_at` correctly.
  - Execution state: pending

- [ ] E-03 PROVE THE 143 LEGACY MULTI-RECORD FILES ARE SAFE, which E-02 should achieve BY CONSTRUCTION rather than by migration. Measured at authoring: 143 tracked backlog items and specs still carry MORE THAN ONE inline history record, all of it legacy (it predates the sidecar, so nothing else holds it), and under today's behavior one `set` call slims any of them to a single line. Once E-02 stops slimming, nothing truncates them, so this item is a VERIFICATION rather than a rewrite: pick real legacy files, run a real transition, and show the prior records survive. DO NOT BULK-REWRITE THE 143 FILES: they belong to other agents' work in a shared checkout, E-02 removes the hazard without touching them, and a mass diff would be both unnecessary and hostile to review. If verification shows some files still lose records, that is a finding to report, not a licence to sweep.
  - Depends on: E-02
  - Expected outcome: the count of tracked files carrying more than one inline record does NOT fall after a transition; at least one real legacy file is demonstrated to keep its prior records; zero files were rewritten to achieve it.
  - Execution state: pending

- [ ] E-04 STOP SWALLOWING A FAILED SIDECAR WRITE. `backlog.py:544-558` wraps the `record_history.append(...)` call in a bare `try/except Exception: pass`, so a sidecar failure is invisible; combined with a successful inline slim, the record is lost from BOTH homes with no signal. Make the failure visible and make it BLOCK THE SLIM: if the durable write did not succeed, keep the record inline rather than dropping it. Check `specs.py`'s equivalent routing for the same pattern and fix both if present. A warning alone is insufficient here, because the inline slim has already discarded the only other copy by the time anyone reads the warning.
  - Depends on: E-02
  - Expected outcome: an induced sidecar-write failure leaves the record INLINE and reports the failure; no path loses a record silently.
  - Execution state: pending

### Task group 3: remove the reason to abuse the setter

- [ ] E-05 ADD `aw backlog note`, MIRRORING THE EXISTING `aw specs note`. Today the backlog verb set is `new`, `set`, `check` only, so appending a note to an item REQUIRES a status-setting call, which is how both defects in this plan were hit. `aw specs note` already exists and is the precedent to copy (same flag shape, same history-record behavior, no status change). This is the ergonomic fix that removes the incentive to reach for `set` when annotation is the intent. Register it on the backlog subparser beside `set`, and update `.aw/records/backlog/README.md`, which documents the verb set and becomes incomplete the moment the verb exists.
  - Depends on: E-01
  - Expected outcome: `aw backlog note <item> --message "..."` records a note without changing status; the README documents it; `aw specs note` behavior is unchanged.
  - Execution state: pending

### Task group 4: pin it

- [ ] E-06 PIN ALL FOUR BEHAVIORS WITH THE MEASURED CASES. Assert: a same-status call WITH a message records exactly ONE record (not zero, the `x6tk1u` bug, and not two, the duplicate-growth trap); a same-status call WITHOUT a message records nothing; history written by a note verb is readable in a FRESH CLONE (the E-02 property, which is the one a unit test can most easily fake, so clone or use a bare-repo push/fetch rather than reading the same working tree); an induced sidecar failure leaves the record inline. ALSO ASSERT THE PROPERTY THAT MUST NOT REGRESS: `aw attention`'s `last_history_at` still derives correctly, since `awhistory-02` kept exactly one inline record precisely to protect that derivation and E-02/E-03 may change how many records are inline.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: five assertions covering both defects, the ergonomic verb, the failure path, and the attention derivation that must survive.
  - Execution state: pending

- [ ] E-07 AMEND SPEC `20260818-1525-02` IN THIS SAME CHANGE, because E-02 changes behavior that spec describes. Its OQ-2 ruled the inline history of specs and backlog keeps only the LATEST ONE record; the maintainer reversed that premise on 2026-09-10 (OQ-01), so inline history is now the durable home for both types. Record the amendment with its date and the ruling, state that the sidecar remains a machine-local ACTIVITY LOG rather than the durable store, and state that plans were always exempt so all three types now share one model. DO NOT DELETE OQ-2's ORIGINAL REASONING: the slimming was a considered decision motivated by `aw attention`'s `last_history_at`, that motivation still constrains the design (E-02 must not break the derivation), so mark it superseded rather than erasing it. Use `aw specs note` for the history record, and note the irony to check: that verb is one of the nine writers this plan is fixing, so run it AFTER E-02 lands and confirm the amendment's own history record is preserved inline. That is a free end-to-end test of the fix.
  - Depends on: E-02
  - Expected outcome: the spec states inline provenance for specs and backlog with the ruling's date, OQ-2's reasoning preserved as superseded, and the spec's own new history record demonstrably kept inline by the very fix it documents.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SLIMMING IS DELIBERATE, NOT A BUG. `awhistory-02` (`b0behn`, executed, spec `20260818-1525-02` OQ-2) routed specs and backlog writers to the sidecar and slimmed inline history to the latest one record, KEEPING one line specifically so `aw attention`'s `last_history_at` (`attention_contract.py:434`) keeps working. Any fix must preserve that derivation.
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
| F-4 | HIGH | tracked corpus | 143 backlog items and specs still carry >1 inline record, committed-only, each one `set` call from truncation; the sidecar covers 141 artifacts, so neither store is complete. | counted at HEAD |
| F-5 | MEDIUM | `backlog.py:544-558` | A sidecar write failure is swallowed by a bare `except Exception: pass`, so a failed durable write plus a successful slim loses the record with no signal. | source read |
| F-6 | MEDIUM | `awhistory-02` (`b0behn`) | The slimming is INTENTIONAL and reviewed, so the remedy must not revert it. An earlier report of mine claimed otherwise and was corrected in `hg2oop`. | the executed plan's Concern and E-01(b) |
| F-7 | LOW | backlog verb set | There is no `aw backlog note`, so annotating requires a status call; `aw specs note` exists as the precedent. | `aw backlog --help` lists only `new`, `set`, `check` |

## Proposed changes (ordered, validatable)

1. E-01 makes message presence the discriminator, following the four existing hoisted-field precedents.
2. E-02 makes the durable store actually durable, per the option review selects.
3. E-03 protects the 143 legacy multi-record files from being truncated before their content is durable.
4. E-04 stops a failed durable write from being invisible, and blocks the slim when it fails.
5. E-05 adds `aw backlog note` so annotation no longer routes through the setter.
6. E-06 pins all of it, including the `attention` derivation that must not regress.

## Deferred / out of scope (with reason)

- THE CONFIRMATION AND TERMINAL-REOPEN GUARDS (`f5pttg`): Order 01 of this Set. Same file, different failure class (unguarded mutation rather than lost provenance) and different tests.
- REVERTING `awhistory-02`'s SLIMMING: explicitly rejected. It is a reviewed decision and reverting it would break the `attention` derivation it was shaped around; F-6 records that an earlier report of mine wrongly proposed this.
- CHANGING `aw attention`'s DERIVATION: out of scope and must keep working unchanged; E-06 asserts it.
- PLAN/IPD HISTORY BEHAVIOR: deliberately exempt from slimming per `awhistory-02`'s explicit guard (IPD-S405 needs the inline `executed` entry). Not touched.

## Scope check

- Over-scope: none. `.aw/.gitignore` was declared while OQ-01 was open and has been REMOVED now that the maintainer chose inline provenance over tracking the sidecar; the ignore rule is untouched. Every remaining declared path is touched by a named item: `status_set.py` (E-01), `backlog.py` and `specs.py` (E-02, E-04), `cli.py` and `.aw/records/backlog/README.md` (E-05), the awhistory spec (E-07), and the two test modules (E-06).
- Under-scope: none remaining. E-03 (the 143 legacy files) and E-04 (the swallowed failure) were absent from the two backlog items and were added from measurement. E-07 (the spec amendment) was added AFTER the maintainer's ruling, because choosing inline provenance contradicts the shipped spec's OQ-2 and a plan that changes behavior a spec describes MUST carry the amendment in the same change.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. Beyond the suite: a FRESH CLONE demonstration for E-02 (clone the repository, or push to a bare repo and clone from it, then read the history that a note verb wrote), because reading the same working tree cannot distinguish tracked from ignored; the before/after count of the 143 legacy multi-record files for E-03; and an induced sidecar failure for E-04.

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
  THE ONE CONSTRAINT THAT MUST SURVIVE, and it is why `awhistory-02` slimmed at all: `aw attention`'s `last_history_at` derivation reads the inline record and was the stated reason for keeping exactly one line. Keeping MORE lines must not break it. The plans side is the existence proof that it works (plans carry many inline records and `attention` handles them), and `plan_readiness.extract_newest_history_entry` is the shared reader to follow. E-06 asserts this.
  ALSO CORRECTED, TWICE, AND WORTH RECORDING SO NEITHER ERROR REPEATS: I first reported the slimming as an accidental renderer bug (it is a reviewed decision), and then warned that tracking the sidecar risked constant merge conflicts (it is append-only with ~11 records/day and a one-line `union` merge setting would have handled it, so the warning was overstated). Neither claim survived measurement. The decision above rests on the caller trace, which is evidence rather than inference.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a same-status call WITH `--message` showing exactly ONE new record written, and the SAME call repeated showing history does NOT grow again unless a new message is supplied (the duplicate-growth trap). Paste a same-status call WITHOUT a message showing nothing written. Name which of the four existing hoisted-field precedents you followed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a FRESH CLONE (or bare-repo push then clone) in which the history written by a note verb is READABLE, with the command and its output. Reading the same working tree does NOT satisfy this item, because it cannot distinguish tracked from ignored content. State which option was implemented, why, and paste the measurement that decided it (in particular, if the sidecar was tracked, the evidence about concurrent-write conflict risk).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the BEFORE count of tracked files carrying more than one inline record (expect 143) and the AFTER state, and state the method (migrated, or slim-refused). Demonstrate on ONE real legacy file that a `set` call no longer drops its prior records. If any tracked file was rewritten in bulk, say how many and paste the diffstat, since this is a shared checkout.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste an INDUCED sidecar-write failure showing the record kept INLINE and the failure reported. Show the bare `except Exception: pass` is gone. Confirm whether `specs.py` had the same pattern and what you did about it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw backlog note <item> --message "..."` recording a note with the item's STATUS UNCHANGED and its file NOT moved. Paste `aw specs note` still working unchanged. Paste the README diff documenting the new verb.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all five assertions passing. Include a MUTATION CHECK on the `x6tk1u` fix (restore the early return, show the same-status-with-message test FAILS, revert, show it passes) and an explicit assertion that `aw attention`'s `last_history_at` still derives correctly, since `awhistory-02` kept one inline record specifically to protect it.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the amended spec passage showing inline provenance stated with the maintainer's ruling and its date, AND showing OQ-2's original reasoning still present and marked superseded rather than deleted. Then paste the spec's OWN `## Workflow history` proving the amendment's record was preserved inline alongside the prior records, which is the end-to-end proof that E-02 works on the specs path (`aw specs note` is one of the writers being fixed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 7 E-leaves in 4 groups, at the upper end of comfortable. It stays one plan because all seven serve one property (a recorded reason must be durable) and share one test surface. E-07 (the spec amendment) was added after the maintainer ruled, because a plan changing behavior a spec describes must carry the amendment in the same change; it is not separable without leaving a shipped spec contradicting the code.
- Cohesion rationale: E-01 is the discarded-message fix and is independent. E-02, E-03 and E-04 are one durability concern in three parts: the store, the existing content in it, and the failure path into it. E-05 is the ergonomic fix that removes the incentive to trigger either defect. E-06 is the shared regression surface, including the one property (`attention`'s derivation) that every other item could break.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. If E-03 rewrites tracked legacy files, say how many and show the diffstat: this is a SHARED CHECKOUT and those artifacts belong to other agents' work. Never revert or commit a file you did not change.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved vhbvwz --by-human --message ...`) before execution, AND its `Blocking: yes` OQ-01 must be answered first: `aw ipd lint` refuses a plan carrying an unresolved blocking question, which is the intended fail-closed stop. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
