# IPD: Say plainly that no driver run writes a ledger instead of reporting a bare file-not-found

- Date: 2026-09-08
- Kind: child
- Concern: `aw runs verify-ledger <any-real-run>` CANNOT VERIFY ANY DRIVER RUN, AND ITS MESSAGE DOES NOT SAY SO. Re-measured at HEAD: `find . -name ledger.jsonl` returns ZERO results anywhere in the repository, and neither driver touches the store (`grep -c 'run_ledger_store\|RunLedgerStore' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` -> 0 and 0). Spec `25kzda`'s own header concedes it in as many words at `:29`: "the ledger is built but UNWIRED". Independently corroborated by a sibling plan measuring the live corpus: `8hald1`'s review records that `ledger.jsonl` is present in ZERO of 135 real run directories. So on every real target the command prints `error: ledger file not found for target '<id>'` and exits 2, which is an accurate statement about a FILE and a misleading one about the WORLD: the operator asked "is this run's record intact" and was told something that reads like a missing artifact rather than "this command cannot answer that question for any driver run".
  THE ITEM'S SECOND DEFECT IS FALSE AND THE ITEM ITSELF SAYS SO. As filed it claimed the command "exits 0 when the ledger is absent" and instructed a reader to "find where the nonzero is lost between leaf and process exit". The item's own 2026-09-06 correction retracts that: the original measurement piped through `head`, so the `$?` read was `head`'s status, not the command's. RE-VERIFIED INDEPENDENTLY at HEAD, unpiped: `aw runs verify-ledger run-20260824T140112Z-2227235 >/dev/null 2>&1; echo $?` prints `2`, exactly as `_run_verify_ledger`'s `return 2` intends (`run_cli.py:512-518`). There is no lost-nonzero plumbing bug. Anyone graduating this item without reading its correction would spend a session hunting a bug that does not exist, which is why this plan states it before anything else.
  SO WHAT SURVIVES IS THE ITEM'S OWN FIX #1, WHICH IT CALLS "worth doing on its own": make the absent-ledger path say plainly that driver runs do not currently write a ledger, so the operator knows the answer is "cannot verify", not "nothing wrong". The exit code is already correct and must not change.
  THE ITEM'S FIX #3 (the naming trap) IS PARTLY ADDRESSED ALREADY, and the remainder is small. "Ledger" names two unrelated substrates: the drivers say it 13 times in `oc_runipd.py` (re-measured: exactly 13) meaning `events.jsonl`, their own append-only event log which DOES exist and works; `verify-ledger` means the hash-chained `ledger.jsonl` owned by `run_ledger_store`, which nothing writes. `resolve_ledger_path` already refuses to conflate them and cites the prior bug where doing so made healthy runs report as corrupt (`run_cli.py:236-239`, naming `e6b9kt`). AND THE ITEM'S OWN SUGGESTION IS ALREADY DONE: it asks for "at minimum saying in `--help` which file the command reads", and the help already states "NOTE: a run id resolves only to a ledger.jsonl; the drivers' own events.jsonl is a different format." So only the REFUSAL MESSAGE lacks the disambiguation, which is exactly where an operator meets the confusion.
  THE ITEM'S FIX #2 IS A DESIGN DECISION THIS PLAN DELIBERATELY DOES NOT MAKE. Whether the drivers SHOULD write a ledger is genuinely open, is entangled with the `AW-Run:`/`AW-Item:` trailers (which `a8eufb` records as existing but unwritten, now graduated to `wao266`), and spec `25kzda` Section 4.2 assumes that substrate throughout. Approved plan `7wei1o` independently draws the same line, naming "whether driver runs should WRITE a `ledger.jsonl` at all" as "the remaining half of backlog `zrzfkw` and a genuine design question", explicitly out of its scope and "independent of this refusal".
- Scope: Make the absent-ledger refusal TRUTHFUL about why it cannot verify, and disambiguate the two senses of "ledger" at the one surface that still conflates them. Exit codes and every verification behavior stay exactly as they are. EXCLUDES deciding whether drivers should write a ledger (the item's fix #2, a design question), and excludes the sibling fail-open in `6kq1lj`, which approved plan `7wei1o` already owns.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_cli_ledger_message.py
- Item-Dependencies: none
- Status: to-review
- Set: ledgerhonest
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i1hlgx
- From-Backlog: zrzfkw

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `zrzfkw`, NARROWED to the item's fix #1 plus the unfinished remainder of its fix #3. DEFECT 2 IS DEAD BY THE ITEM'S OWN CORRECTION and was independently re-verified unpiped at HEAD: exit is 2, not 0 (`run_cli.py:512-518`), so there is no lost-nonzero bug and the item's instruction to hunt one is explicitly not carried forward. DEFECT 1 SURVIVES and was re-measured three ways: zero `ledger.jsonl` files anywhere, zero `run_ledger_store` references in either driver, and spec `25kzda:29` conceding "the ledger is built but UNWIRED"; sibling plan `8hald1`'s review independently measured it absent from all 135 real runs. FIX #3 IS PARTLY OBSOLETE: the item asks "at minimum" for a `--help` note naming the file, and the help ALREADY says "a run id resolves only to a ledger.jsonl; the drivers' own events.jsonl is a different format", so only the REFUSAL MESSAGE remains, and the drivers' 13 "ledger" mentions were re-counted as exactly 13. FIX #2 IS EXCLUDED as a design question, which approved plan `7wei1o` independently reached, naming it "the remaining half of backlog `zrzfkw`" and out of its own scope. This plan therefore does not touch the exit contract, the verification logic, or the drivers.

## Goal

Make a command that cannot answer the question say so, so an operator diagnosing a run is not left reading a missing-file error as evidence that nothing is wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state, because one of the item's two defects is fictional

- [ ] E-01 RE-VERIFY BOTH THE SURVIVING DEFECT AND THE RETRACTED ONE, and write both results down. This item was filed with a measurement error and corrected itself; the correction must be re-confirmed rather than trusted, and the surviving half must be re-confirmed rather than assumed still true.
  MEASURE THE EXIT CODE UNPIPED. `aw runs verify-ledger <real-run-id> >/dev/null 2>&1; echo $?` must print 2. DO NOT pipe the command through `head`, `grep` or anything else when reading `$?`: a pipeline reports the LAST stage's status, which is the exact error that produced this item's false defect 2. If you measure 0, then something regressed and this plan's shape changes; report it rather than proceeding.
  MEASURE THE LEDGER'S ABSENCE THREE WAYS, since it is the plan's whole premise: no `ledger.jsonl` anywhere in the repository; zero `run_ledger_store` or `RunLedgerStore` references in `oc_runipd.py` and `agy_runipd.py`; and the spec's own concession at `25kzda:29`.
  IF A DRIVER HAS SINCE BEEN WIRED TO WRITE A LEDGER, STOP AND RE-SCOPE. The message this plan writes would then be false, which is worse than the vague message it replaces.
  - Depends on: none
  - Expected outcome: a written record of the unpiped exit code, the three absence measurements, and an explicit STOP if either result has changed.
  - Execution state: pending

### Task group 2: make the refusal truthful

- [ ] E-02 REPLACE THE BARE FILE-NOT-FOUND WITH A MESSAGE THAT NAMES THE REAL SITUATION, at `_run_verify_ledger`'s absent-ledger branch (`run_cli.py:512-518`).
  THE MESSAGE MUST DISTINGUISH THREE THINGS an operator conflates here: that this command reads the hash-chained `ledger.jsonl` owned by `run_ledger_store`; that NO driver run currently writes one, so the answer is "cannot verify" rather than "nothing wrong"; and that the drivers' own `events.jsonl` is a DIFFERENT file in a different format that does exist. The third clause is the item's fix #3 landing where the confusion actually happens.
  KEEP THE EXIT CODE AT 2. It is already correct (the item's defect 2 was a measurement error) and `7wei1o` E-02 explicitly cites `aw runs verify-ledger <absent>` exiting 2 as the precedent it aligns ITS refusal with. Changing it here would silently move the reference point an approved plan is being written against.
  DO NOT ASSERT SOMETHING THE CODE CANNOT KNOW. The message may say that no driver run writes a ledger today (measured, and conceded by the spec), but it must not claim the run is fine, that the run is broken, or that a ledger will exist later. It should also not tell the operator to file a bug: the gap is known and tracked.
  HONOR THE MACHINE PATH IDENTICALLY. The branch already emits `{"ok": False, "error": ..., "exit_code": 2}` for `--agent`/`--json`; the improved text must reach that consumer too, since a machine consumer is exactly who cannot infer context from a terse string. Keep the record's shape.
  WRITE NO EM OR EN DASHES: this is operator-facing prose.
  - Depends on: E-01
  - Expected outcome: the absent-ledger refusal names the file it wanted, states that no driver run writes one so the answer is "cannot verify", and distinguishes `events.jsonl`; exit stays 2; the machine record carries the same text and shape.
  - Execution state: pending

- [ ] E-03 CHECK WHETHER THE SIBLING READERS NEED THE SAME SENTENCE, and treat "no" as a legitimate answer rather than expanding the plan. `resolve_ledger_path` feeds SEVERAL leaves (`run_cli.py` constructs a `RunLedgerStore` at five distinct call sites), and each may have its own absent-file branch with the same vague text.
  ENUMERATE THEM FIRST, THEN DECIDE. If a sibling leaf's absent-ledger message has the same problem, fixing it is in scope and cheap because the wording already exists. If a sibling's message is already specific, or the leaf is reached only with an explicit path argument (where "file not found" IS the whole truth), leave it and say so.
  DO NOT EXTRACT A SHARED HELPER UNLESS THERE ARE AT LEAST TWO REAL CALLERS. A one-caller helper adds indirection for nothing; a genuine second caller makes it worth it. Decide from the enumeration, not in advance.
  DO NOT CHANGE ANY VERIFICATION BEHAVIOR while in this file. The chain verification, evidence validation and completion predicates are out of scope entirely.
  - Depends on: E-02
  - Expected outcome: an enumeration of the sibling absent-ledger branches with a per-leaf decision, a shared helper only if two or more callers genuinely need one, and no verification logic touched.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 TEST THE MESSAGE AND PIN THE EXIT CODE, including the pipeline trap that produced this item's false defect.
  FOUR ASSERTIONS MINIMUM: the absent-ledger human message contains the three required clauses (the file it reads, that no driver writes one, and that `events.jsonl` is different); the exit code is 2, measured UNPIPED; the `--agent` record carries the same text with `ok: False` and `exit_code: 2`; and a PRESENT, valid ledger still verifies clean with its existing exit code, proving the happy path is untouched.
  ASSERT THE EXIT CODE WITHOUT A PIPELINE, and say so in the test's own comment naming why: this item exists in its corrected form precisely because a piped `$?` reported `head`'s status. A test that captures output through a pipe and then reads a return code is repeating the original error in a place that will be trusted.
  BUILD A FIXTURE LEDGER for the happy-path case rather than looking for a real one, since none exists in the repository (that is the plan's premise) and `8hald1`'s review independently measured zero across 135 real runs.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-03
  - Expected outcome: four assertions passing, the exit code pinned unpiped with the reason commented, a fixture-based happy path, and an empty bare-suite delta with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE EXIT CODE IS ALREADY CORRECT. `_run_verify_ledger` returns 2 on the absent path (`run_cli.py:512-518`) and re-measuring unpiped confirms 2. The item's defect 2 was a piped-`$?` measurement error and it retracted it itself.
- A PIPED `$?` REPORTS THE LAST STAGE. This is the trap that produced the false defect; measure exit codes with `cmd >/dev/null 2>&1; echo $?`.
- THE LEDGER IS UNWIRED, THREE WAYS: no `ledger.jsonl` anywhere; zero `run_ledger_store` references in either driver; spec `25kzda:29` says "the ledger is built but UNWIRED". Sibling plan `8hald1`'s review measured it absent from all 135 real runs.
- "LEDGER" NAMES TWO SUBSTRATES: the drivers say it exactly 13 times in `oc_runipd.py` meaning `events.jsonl` (which exists and works); `verify-ledger` means the hash-chained `ledger.jsonl` (which nothing writes).
- THE CONFLATION IS ALREADY GUARDED IN CODE: `resolve_ledger_path` refuses to resolve a bare run id to `events.jsonl` and cites `e6b9kt`, where doing so made healthy runs report as corrupt (`run_cli.py:236-239`).
- THE `--help` DISAMBIGUATION IS ALREADY DONE: the target's help text already says a run id resolves only to a `ledger.jsonl` and that `events.jsonl` is a different format. The item asked for exactly this "at minimum".
- AN APPROVED PLAN CITES THIS EXIT CODE AS ITS PRECEDENT: `7wei1o` E-02 aligns its own refusal with `aw runs verify-ledger <absent>` exiting 2. Do not move that reference point.
- `7wei1o` ALSO DRAWS THE SAME SCOPE LINE, naming the drivers-should-write-a-ledger question as "the remaining half of backlog `zrzfkw`" and out of its scope.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the item's defect 2 is FALSE | It claimed exit 0 on an absent ledger and told a reader to hunt lost plumbing. Re-measured UNPIPED: exit is 2, exactly as `return 2` intends. The item retracted this itself; the original reading was `head`'s status through a pipe. | `aw runs verify-ledger <run> >/dev/null 2>&1; echo $?` -> 2; `run_cli.py:512-518` |
| F-2 | HIGH | defect 1 survives, measured three ways | No `ledger.jsonl` exists anywhere; zero `run_ledger_store`/`RunLedgerStore` references in either driver; spec `25kzda:29` concedes "the ledger is built but UNWIRED". | `find . -name ledger.jsonl` -> empty; `grep -c` -> 0 and 0; the spec line |
| F-3 | HIGH | independently corroborated on the live corpus | A sibling plan's review measured `ledger.jsonl` present in ZERO of 135 real run directories and marked the ledger adapter fixture-only. | `8hald1`'s review record |
| F-4 | MEDIUM | fix #3's "minimum" is already shipped | The item asks "at minimum" for a `--help` note naming the file read; the help already states a run id resolves only to `ledger.jsonl` and that `events.jsonl` differs. Only the REFUSAL message lacks it. | `aw runs verify-ledger --help` |
| F-5 | MEDIUM | the naming trap is real and already guarded in code | `oc_runipd.py` says "ledger" exactly 13 times meaning `events.jsonl`; `resolve_ledger_path` refuses to conflate them and cites `e6b9kt`, where conflation reported healthy runs as corrupt. | `grep -c ledger oc_runipd.py` -> 13; `run_cli.py:236-239` |
| F-6 | MEDIUM | an approved plan depends on this exit code | `7wei1o` E-02 aligns its own new refusal with `aw runs verify-ledger <absent>` exiting 2, citing it as the coherent precedent. Changing it would move an approved plan's reference point. | `7wei1o` E-02 and its F-6 |
| F-7 | MEDIUM | fix #2 is a design question with an owner-shaped gap | Whether drivers should write a ledger is entangled with the unwritten `AW-Run:` trailers (`a8eufb`, now plan `wao266`) and with spec 4.2's assumptions. `7wei1o` names it "the remaining half of backlog `zrzfkw`" and excludes it. | `7wei1o`'s Deferred section; `a8eufb` |
| F-8 | LOW | several sibling leaves construct the same store | `run_cli.py` builds a `RunLedgerStore` at five call sites, so more than one absent-file branch may carry the same vague text. | grep for `RunLedgerStore(` in `run_cli.py` |
| F-9 | LOW | the machine path needs the same text | The absent branch already emits `{"ok": False, "error": ..., "exit_code": 2}`, and a machine consumer is exactly who cannot infer missing context. | `run_cli.py:512-518` |

## Proposed changes (ordered, validatable)

1. Re-verify the unpiped exit code and the ledger's absence three ways, stopping if either has changed (E-01).
2. Rewrite the absent-ledger refusal to name the file, state that no driver writes one, and distinguish `events.jsonl`, keeping exit 2 and the machine record's shape (E-02).
3. Enumerate the sibling absent-ledger branches and fix only those with the same problem, extracting a helper only if two or more need it (E-03).
4. Assert the three message clauses, the unpiped exit code, the machine record, and an untouched happy path (E-04).

## Deferred / out of scope (with reason)

- WHETHER THE DRIVERS SHOULD WRITE A LEDGER (the item's fix #2). A genuine design question, not a message fix: it is entangled with the `AW-Run:`/`AW-Item:` trailers that exist but are unwritten (`a8eufb`, graduated to `wao266`), and spec `25kzda` Section 4.2 assumes the hash-chained ledger throughout. Approved plan `7wei1o` independently reached the same conclusion and named it "the remaining half of backlog `zrzfkw`". The item itself says fix #1 "is worth doing on its own and does not depend on 2".
- THE SIBLING FAIL-OPEN IN `6kq1lj`. Approved plan `7wei1o` owns it: an unrecognized `aw runs` leaf degrading into a target search and exiting 0. That IS a genuine fail-open; this plan's target is not. Do not touch that surface.
- CHANGING ANY EXIT CODE. The absent path's 2 is correct, and an approved plan cites it as its precedent (F-6).
- ANY VERIFICATION BEHAVIOR: chain verification, evidence validity, completion predicates. Out of scope entirely; this plan changes one refusal message.
- RENAMING EITHER SENSE OF "LEDGER" IN PROSE. The item offers this as an alternative to disambiguating in the message. Declined: renaming `events.jsonl`'s 13 in-driver mentions touches the highest-contention files in the repository for a wording gain, while the message change reaches the operator at the exact moment of confusion.
- THE `--help` TEXT. Already correct (F-4); the item's "at minimum" ask is shipped.
- AMENDING SPEC `25kzda`'s "UNWIRED" CONCESSION. The spec is honest today. If fix #2 is ever decided, that decision amends the spec; recording a message improvement does not.

## Scope check

- Over-scope: none. One refusal message, possibly one shared helper, one test module.
- Scope-Paths justification: `agent_workflows/run_cli.py` holds `_run_verify_ledger` and its absent-ledger branch (E-02), `resolve_ledger_path` whose docstring already records the conflation history, and the five sibling `RunLedgerStore` call sites E-03 must enumerate; `tests/test_run_cli_ledger_message.py` is new and carries the four assertions including the unpiped exit-code pin. Deliberately NOT in scope: `agent_workflows/run_ledger_store.py` (the store is correct and unwired, which is a wiring question, not a defect), either driver (they are the subject of the excluded fix #2 and are under concurrent edit), and `agent_workflows/run_viewer.py` (the `6kq1lj` surface `7wei1o` owns).
- Under-scope, stated rather than left as `none`: this plan does not decide whether drivers should write a ledger, does not touch the `6kq1lj` fail-open, changes no exit code, changes no verification behavior, renames neither sense of "ledger", does not edit the already-correct help text, and does not amend the spec. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE UNPIPED EXIT CODE for the absent-ledger case, measured as `cmd >/dev/null 2>&1; echo $?` and pasted, before and after, both 2. A piped measurement does not satisfy this and is the exact error that produced this item's false defect.
- THE HUMAN MESSAGE pasted verbatim, showing all three clauses: the file it reads, that no driver run writes one so the answer is "cannot verify", and that `events.jsonl` is a different file.
- THE `--agent` RECORD pasted, showing the same text with `ok: False` and `exit_code: 2` and an unchanged shape.
- A FIXTURE-BASED HAPPY PATH: a present, valid ledger still verifies clean with its existing exit code, proving the change is confined to the absent branch.
- THE SIBLING ENUMERATION from E-03 with its per-leaf decision, so a reviewer can see what was deliberately left alone.
- A SEARCH proving no verification logic changed and no exit code moved.
- `aw sanitize --agent` clean, and a check that the new prose contains no em or en dash.

## Spec / documentation sync

Spec `25kzda`'s header already concedes "the ledger is built but UNWIRED" (`:29`), which is exactly the fact this plan surfaces to the operator, so NO spec change is needed and the spec file is deliberately not declared in `Scope-Paths`. If the executor finds spec text claiming that `verify-ledger` CAN verify a driver run, that is a false claim and must be reported for an amendment rather than edited here.

`resolve_ledger_path`'s docstring is the authoritative in-code statement of the two-substrate distinction and already cites the `e6b9kt` bug. Extend it with one sentence noting that the absent-ledger MESSAGE now carries the same distinction, so a future reader editing either place finds the other.

The refusal text is OPERATOR-FACING PROSE: write no em or en dashes, do not imply the operator did something wrong, and do not tell them to file a bug, since the gap is known and tracked.

## Open questions

### OQ-01: Should the message say that driver runs never write a ledger, or only that this file is absent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SAY THE STRONGER, MEASURED THING, because the weaker one is what makes the current message misleading. "File not found" invites the reading that this particular run is unusual, when in fact NO driver run has ever written one: measured zero `ledger.jsonl` files repo-wide, zero store references in either driver, zero across 135 real runs per `8hald1`'s review, and the spec's own "built but UNWIRED". Stating it converts a puzzling absence into a known limitation and stops the operator hunting. The bound on this claim, which E-02 enforces: the message may state that no driver writes one TODAY, and must not claim the run is healthy, that it is broken, or that a ledger will exist later.

### OQ-02: Should the absent case exit nonzero at all, given the file is expected to be missing?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, KEEP 2, AND DO NOT REVISIT IT. Two independent reasons. First, "cannot verify" is not "verified clean", so exit 0 would be the actual fail-open, which is the mistake the item's own false defect 2 accidentally accused the code of. Second, an approved plan already depends on it: `7wei1o` E-02 cites `aw runs verify-ledger <absent>` exiting 2 as the precedent it aligns its own new refusal with, so changing it would move a reference point under a plan currently queued for execution. The item's fix #1 asks only that the absent path "exit NONZERO and say plainly" why, and the nonzero half is already satisfied.

### OQ-03: Should this plan also fix the sibling leaves that read a ledger?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY THOSE WITH THE SAME DEFECT, decided per leaf by enumeration rather than in advance. `run_cli.py` constructs a `RunLedgerStore` at five call sites, and a vague absent-file message is a defect only where the operator could reasonably have supplied a bare RUN ID and expected an answer. Where a leaf is reached only with an EXPLICIT path argument, "file not found" is the whole truth and needs no expansion, and rewriting it would add noise. E-03 therefore enumerates and decides, and is explicitly allowed to conclude that no sibling needs changing. The anti-goal is a sweeping message refactor across a file whose verification logic this plan must not touch.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the UNPIPED exit-code measurement (`cmd >/dev/null 2>&1; echo $?`) showing 2, and state explicitly that no pipeline was used. Paste all three absence measurements: the `ledger.jsonl` search, the per-driver `run_ledger_store` counts, and the spec line. If any result differs from this plan's premise, paste the STOP and do not proceed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new human message VERBATIM and identify its three clauses one by one. Paste the `--agent` record showing the same text, `ok: False`, `exit_code: 2` and an unchanged shape. Paste the unpiped exit code AFTER the change, still 2. Paste a search showing the prose contains no em or en dash, and confirm in one sentence that the message asserts nothing about the run's health.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the enumeration of every `RunLedgerStore` call site with its absent-file behavior and your per-leaf decision (changed, or left alone with the reason). If you extracted a shared helper, name the two or more callers that justified it; if you did not, say so. Paste a search proving no verification logic (chain, evidence, completion) was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of all four assertions. QUOTE the exit-code assertion and its comment, showing it measures without a pipeline and says why. Paste the fixture-ledger happy-path result with its exit code, proving the absent branch alone changed. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS DELIBERATELY SMALL AND CARRIES NO BLOCKING QUESTION. The item it graduates from contained two defects, one of which the item itself retracted, and a design question this plan excludes. What remains is one refusal message on one branch, which the item calls "worth doing on its own", and the unfinished remainder of its naming-disambiguation ask.

THE ONE THING THAT WOULD CHANGE ITS SHAPE is E-01's re-measurement: if a driver has since been wired to write a ledger, the message this plan writes would be false, and if the absent path no longer exits 2, an approved plan's cited precedent has moved. Either finding is a STOP, not a detail to work around.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. MEASURE EVERY EXIT CODE UNPIPED (`cmd >/dev/null 2>&1; echo $?`); a piped `$?` is what produced this item's false defect and repeating it in a test would enshrine the error. Do NOT change any exit code, any verification behavior, either driver, or the `run_viewer` surface that `7wei1o` owns. Re-locate every symbol by NAME rather than by the line numbers cited here. Write no em or en dashes in the operator-facing message. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the verbatim message with its three clauses identified and the unpiped exit code measured before and after.
