# Spec: Canonical status-setter dispatch: one engine per set verb

- Date: 2026-10-01
- Status: to-review
- Id: wy9aru
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: fcnz1r
- Priority: medium
- Work-Kind: chore
- Scope: Decide which behaviors of the forked aw backlog set / aw specs set dispatch paths are canonical, so the two can be unified onto one engine without silently dropping a gate or a deliberate difference
- Constrained-by: `.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md`
  (`implemented`), whose R2 and AC1 REQUIRE the `backlog set` and `specs set` writers to append a
  sidecar history record. `status_set.py` appends none, and that spec's own OQ-2 resolution records
  having traced exactly that ("`status_set.py` writes to it ZERO times"). Unification therefore
  cannot be performed without a ruling on the sidecar; Section 4.3 is that ruling and Section 6
  states the amendment it requires. This spec does not weaken that spec's durability model.
- Constrained-by: `.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md`
  (`2vev8j`, `approved`) C5, AC-7 and Section 4.4. C5 forbids recording an event for a transition
  that did not happen; 4.4 requires every writer to stamp UTC. Both are CONSUMED here as settled
  rulings rather than re-decided: 4.4 is what makes the clock divergence a defect with a known
  correct answer, so unification inherits it rather than choosing.
- Constrained-by: `.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`
  (`z7nbn1`, `implementing`), whose thesis is one selector and one action table consulted by every
  dispatcher, and whose 1.8 explicitly leaves the internal structure free ("MAY be structured as a
  thin router delegating to per-type handlers"). This spec is the per-verb instance of that thesis
  for the `set` family and adds no requirement to it.
- Constrained-by: `.aw/records/specs/implemented/20260815-0151-01-honest-human-approval-attestation.spec.md`
  (`implemented`), which OWNS the `--by-human` attestation model and names `specs.run_set` BY SYMBOL
  as its implementation site. The attestation BEHAVIOR is already duplicated into `status_set.py`, so
  unification does not change the contract; it changes WHERE that spec's named symbol lives, which
  Section 6 records.

## Workflow history
- 2026-10-01 to-review (aw set): Authored from backlog fcnz1r: rules the canonical side of each forked set-dispatch behavior so unification can proceed. Two previously-unknown gate bypasses on the positional specs path were MEASURED while authoring and filed as h4fiwa and fv4b6s; a dead prompts set verb was filed as 68sur3. OQ-1 (sidecar: type-conditional or dropped) is BLOCKING on a maintainer call.

- 2026-10-01 created (aw specs): Decide which behaviors of the forked aw backlog set / aw specs set dispatch paths are canonical, so the two can be unified onto one engine without silently dropping a gate or a deliberate difference

## 1. Problem statement

`aw backlog set` and `aw specs set` each have TWO spellings that reach TWO SEPARATE IMPLEMENTATIONS of
overlapping behavior. `cli.main` forks on whether `--status` was PASSED: absent routes to
`status_set.run_set_command`, present routes to `backlog.run_set` or `specs.run_set`. The fork is not
a thin alias layer; the two sides disagree on roughly forty behaviors, several of which are GATES.

THE DEFECT IS A RECURRING CLASS, NOT AN INSTANCE, which is why it earns a spec rather than a patch.
The same shape has been found and fixed FIVE times, three of them release-blocking:

1. `43p53n` (gate-field clearing): `status_set`'s own comment records that `backlog.run_set` cleared
   correctly "but the positional form routes here instead, so that fix was unreachable".
2. `gatefollows` / `vsgd48` (the release-gate default): fixed by deliberately wiring
   `decide_gate_default` into BOTH paths, whose comment states the principle a behavior wired into one
   spelling only "is worse than not shipping it because it teaches a false expectation".
3. `mawwlc` / `47ttnv` (the release-gate close predicate): the positional spelling closed a
   release-blocking item at exit 0.
4. `h4fiwa` (FILED 2026-10-01 while authoring this spec, MEASURED): positional
   `aw specs set implemented` bypasses the `--evidence` citation gate entirely.
5. `fv4b6s` (FILED 2026-10-01 while authoring this spec, MEASURED): positional
   `aw specs set deferred` writes a `Gate-Kind` outside the vocabulary that the other spelling
   refuses.

Every one of the first three was fixed by DUPLICATING the behavior into the second path. That is the
correct minimal fix for a release-blocking bug under time pressure, and it is also precisely why the
class keeps recurring: each fix leaves the fork intact and adds a sixth thing that must be remembered
twice. Items 4 and 5 are the measurement that the duplication strategy has not converged.

THE SPEC EXISTS BECAUSE UNIFICATION IS NOT A MECHANICAL REFACTOR. The two paths differ in ways that
are each DELIBERATE and SEPARATELY PINNED BY TESTS: one stages a single `git mv` rename and the other
writes-then-unlinks; one appends a sidecar record and the other appends none; `--gate-dir` is honored
by one only; multi-selector batch semantics exist on one only. Choosing a side for each is a decision
about a shipped contract, so it precedes any code movement. That is what this spec decides.

## 2. Evidence

Every row was MEASURED on 2026-10-01 at the authoring HEAD by driving the real surfaces, not read off
the source. The two newly filed defects were each reproduced in a scratch repository over identical
fixtures, with the fixture reset between spellings.

| # | Measurement | What it establishes |
|---|---|---|
| E-1 | `aw specs set <path> --status implemented` on an `implementing` fixture: rc 1, `requires a resolvable --evidence citation`, file unchanged. `aw specs set implemented abc123` on the SAME fixture: rc 0, file relocated to `specs/implemented/`. | A GATE `AGENTS.md` states as policy ("may NOT set `implemented` (needs cited evidence)") is reachable only through the LESS idiomatic spelling. Filed `h4fiwa`. |
| E-2 | `aw specs set <path> --status deferred --gate-kind bogus-kind --gate-ref x`: rc 1, nothing written. Positional same arguments: rc 0, and the spec on disk carries `- Gate-Kind: bogus-kind`. | The positional path writes a record that violates the typed-gate contract, converting a fail-closed refusal into an at-rest checker finding. Filed `fv4b6s`. |
| E-3 | `aw prompts set draft foo` -> `invalid choice: 'set' (choose from 'new')`, while `cli.main` carries a live `prompts set` dispatch branch and the help advertises the verb. | One of the claimed five `set` surfaces is DEAD, so the real reachable count is four. Filed `68sur3`. |
| E-4 | `status_set.apply_status_change` stamps `datetime.datetime.now(datetime.timezone.utc).date()`; `backlog._reattach_history` stamps `datetime.date.today()`. | The two spellings record DIFFERENT DATES for one transition for part of every day. Already filed three times (`2wae2x`, `fnb8pl`, `lq2w86`), and `2vev8j` 4.4 already rules UTC correct, so unification inherits the answer. |
| E-5 | `status_set._offer_self_commit` and `specs._offer_specs_set_commit` are near-identical: both `_git(reset --quiet HEAD --)` then `offer_commit(..., on_unrelated_staged="scope")`, both with the same `assume_yes` expression and the same `chore(specs): set status <s>` message shape. | Two functions, one contract. Deduplicating them is behavior-preserving and needs no ruling. |
| E-6 | The `From-Backlog` gate-inheritance block exists twice, in `status_set.apply_status_change` and `specs.run_set`, and BOTH print the literal string `aw set: inherited - Blocks-Release: ...` even though one of them is `aw specs set`. | Same. The duplicated copy has already drifted in its user-visible output, which is the predicted failure mode of duplication, observed. |
| E-7 | `tests/test_git_commit_helper.py::test_staged_rename_moves_and_duplicate_prevention` asserts the porcelain line `startswith("R")`, and its comment block records the measured 36-duplicate-id incident that motivated it. | The `git_mv` side of the relocation difference is NOT arbitrary; it is a pinned fix for a measured data-loss bug. Section 4.2 rules accordingly. |

## 3. Criteria

- C1 (MUST). For a given verb, BOTH spellings reach ONE implementation of transition validation, one
  implementation of the status write, and one implementation of relocation. A behavior may be
  implemented once and reached twice; it may not be implemented twice.
- C2 (MUST). No gate may be weaker on either spelling than it is today on the STRICTER spelling. The
  union of refusals is the floor; unification may not average them.
- C3 (MUST). A difference that is DELIBERATE and still wanted survives unification as an explicit,
  named parameter of the one engine, never as a second code path. Section 4 names each.
- C4 (MUST). Unification is behavior-preserving for every axis it does not explicitly rule on. An
  axis another live artifact owns is NORMALIZED AROUND, not fixed here (Section 7 lists them).
- C5 (SHOULD). The flag surfaces converge: a flag the shared engine honors SHOULD be declared on every
  verb that can reach it, so a documented flag is never silently inert.

## 3a. Non-goals

- Not a CLI grammar change. Both spellings keep working, with the same arguments, and no verb is
  renamed or removed. This is an internal convergence with no user-visible deprecation.
- Not a change to WHAT any status means, to any status vocabulary, or to any transition table.
- Not the backlog transition table (`t1gbwg` owns it). Unification leaves ONE place for that work to
  land instead of two, which is the whole benefit it confers on that item.
- Not a new storage model. `4sd62s` is the eventual replacement of the history model and this spec
  must not pre-empt it.

## 3b. Acceptance criteria

- AC-1 | C1. For each of `backlog` and `specs`, a differential harness drives BOTH spellings over
  identical fixtures and asserts the resulting record and the resulting file LOCATION agree on every
  axis Section 4 rules canonical, with the axes Section 7 defers normalized by SHAPE rather than by a
  second clock read.
- AC-2 | C2. Each of the five historical instances has a test proving the refusal fires on BOTH
  spellings. For `h4fiwa` and `fv4b6s` specifically: positional `specs set implemented` without
  resolvable `--evidence` REFUSES, and positional `specs set deferred --gate-kind bogus-kind`
  REFUSES and writes nothing.
- AC-3 | C1. `grep`-free proof of single implementation: the dedup is demonstrated by DRIVING both
  spellings, never by asserting a symbol census or a caller count (GUIDING_PRINCIPLES P16 forbids the
  latter outright).
- AC-4 | C3. `--gate-dir` remains honored, and the existing `BacklogGateDirSplitTests` pass unchanged.
- AC-5 | C3. A relocation performed by either spelling appears in `git status --porcelain` as a single
  `R` rename, so `test_staged_rename_moves_and_duplicate_prevention`'s property holds for both.
- AC-6 | C4. The whole bare suite's failure SET is unchanged except for tests this spec's plans
  explicitly edit, each named in advance.

## 3c. Honest limits

- THIS SPEC CANNOT MAKE THE CLASS IMPOSSIBLE, only much narrower. A single engine still has branches,
  and a gate can still be written inside a `if record_type == "specs"` arm that another type never
  reaches. What unification removes is the ENTRY-POINT fork, which is the specific mechanism all five
  measured instances went through.
- THE FLAG-SURFACE CONVERGENCE (C5) IS A `SHOULD`, DELIBERATELY. Declaring every flag on every verb
  would put `--gate-dir` on `aw ipd set`, where it is meaningless. C5 asks that a flag the engine
  honors be declared where it is MEANINGFUL, which is a judgement, so it cannot be a fail-closed MUST.
- THE SIDECAR RULING (4.3) IS A JUDGEMENT ABOUT AN `implemented` SPEC'S REQUIREMENT, and reasonable
  readers can disagree. OQ-1 states the alternative and what would change the answer.
- NO LINE-NUMBER CITATION APPEARS IN THIS SPEC. Offsets in the files under discussion expire quickly
  (`status_set.py` alone is 2785 lines and three live plans edit it), so every citation here is by
  SYMBOL. Several EXISTING specs cite `status_set.py` by line and those citations are already stale;
  this spec does not add more.

## 4. Design decisions

### 4.1 The canonical engine is `status_set`, and the flag paths become callers

RULED: `status_set.run_set_command` + `apply_status_change` + `validate_transition_allowed` is the
surviving implementation. `backlog.run_set` and `specs.run_set` keep their names and signatures (every
test constructs their `Namespace` by hand, and `runner_shared.close_backlog_item` builds argv for one
of them) but become THIN ADAPTERS that normalize their arguments and delegate.

WHY `status_set` AND NOT THE PER-TYPE MODULES. Three reasons, in order of weight. FIRST, it is already
the shared one: four reachable verbs plus `aw finish` reach it, against one each for the others, so
unifying the other way would mean re-implementing selector resolution, cross-type refusal, structured
output, the confirmation gate and auto-indexing three times. SECOND, it is where the capabilities the
flag paths LACK already live (multi-selector batch, setid resolution, `--force`, agent/JSON output),
so delegation is strictly additive for the flag spellings. THIRD, `2lcqno`'s setid semantics and
`z7nbn1`'s one-action-table thesis are both already implemented there.

WHAT THIS DOES NOT MEAN: it does not mean `status_set` absorbs every per-type RULE. A spec-only gate
belongs in a spec-owned predicate that the shared engine CONSULTS, exactly as `47ttnv` did with
`evaluate_blocking_close` and as `specs.run_set` already does for the `->reviewed` attestation. The
engine is shared; the per-type policy stays per-type and is reached through one call.

### 4.2 Relocation: `git mv` is canonical

RULED: the single staged rename (`core.git_mv` then `atomic_write` at the destination) is canonical.
`backlog.run_set`'s `atomic_write` + `unlink` is the defect side and is replaced.

WHY, AND THIS IS NOT A STYLE PREFERENCE: `status_set`'s own comment records that it USED to
`atomic_write` + `unlink` and that git saw that as TWO separate changes, and
`test_staged_rename_moves_and_duplicate_prevention` exists because that shape produced 36 duplicate
ids in a measured incident. The porcelain output differs observably today (`RM old -> new` versus `D
old` plus `?? new`). One side has a pinned regression test and a recorded data-loss incident; the
other has neither.

### 4.3 The sidecar: the shared engine appends one advisory record for `backlog` and `specs`

RULED: the shared engine appends exactly one `record_history.append_advisory` record for the record
types that have one today (`backlog`, `specs`), and appends none for the types that have none today
(`plans`, `prompts`, `research`). The write happens AFTER the durable write succeeds.

WHY NOT SIMPLY DROP IT, which would be the tidier unification: `1525-02` R2 is a MUST that names
`backlog set` and `specs set` explicitly, and AC1 pins it with a live test
(`test_backlog_set_appends_sidecar_and_preserves_inline`). Dropping the sidecar silently would violate
an `implemented` spec's MUST and delete a feature (`aw record-history <id6>`) that reads it.

WHY NOT EXTEND IT TO EVERY TYPE, which would be the tidier contract: `1525-02`'s own OQ-2 resolution
reasons AGAINST that at length, on the ground that the sidecar is gitignored and per-machine while
plan history is already durably inline. Extending it would add a per-machine write for plans whose
history is already clone-surviving, for no reader.

SO THE TYPE-CONDITIONALITY IS THE DELIBERATE DIFFERENCE C3 PRESERVES, and it becomes an explicit
parameter of one engine rather than an accident of which module ran. The ORDERING half (append after,
never before) is NOT this spec's to decide: `2vev8j` C5 and AC-7 already require it and plan `ulepef`
already carries it; this spec adopts the ordering as settled and must land AFTER it.

### 4.4 `--gate-dir` survives as a parameter, not as a path

RULED: the shared engine takes an optional gate root defaulting to the repo root. `--gate-dir` stays
declared on `aw backlog set` only, because that is the only verb where it is meaningful, and
`runner_shared.close_backlog_item` keeps working unchanged.

WHY IT CANNOT SIMPLY BE DROPPED: `runner_shared.close_backlog_item` documents that it uses the
`--status` spelling specifically "because only it honors `--gate-dir`", so dropping it breaks the
runner's own close path, and `BacklogGateDirSplitTests` plus
`test_backlog_set_declared_flag_surface_matches_parser` pin both the behavior and the declaration.

### 4.5 Multi-selector and selector vocabulary: the engine's capability is inherited, not withdrawn

RULED: the flag spellings INHERIT the shared engine's selector vocabulary (id6, setid, status, stem,
substring, path) and its all-or-nothing multi-selector pre-flight. Today `specs.run_set` accepts a
PATH ONLY, and `backlog.run_set` silently acts on `res.paths[0]` when a selector matches many.

THIS IS A DELIBERATE WIDENING AND THE ONLY ONE THIS SPEC AUTHORIZES. It is justified because the
alternative is worse in a specific way: `backlog.run_set`'s current behavior on an ambiguous selector
is to act on ONE arbitrary match and say nothing, which is a silent wrong-target write. The shared
engine refuses ambiguity unless `--force`. Replacing a silent partial action with a refusal is a
strengthening, and C2's floor is about refusals, which this raises rather than lowers.

### 4.6 History label, actor and message: inherit, do not re-decide

RULED: the shared engine's record shape (`- <utc-date> <label> (<actor>): <message>`) is canonical,
with `label` the target status or `same-status`. This spec does NOT decide the actor string or the
defaulted message, because plan `jbipfa` already owns the label parameter and has been reviewed, and
`jbipfa` explicitly DECLINES the actor unification as truthful attribution.

CONSEQUENCE FOR SEQUENCING, stated here because it is the one place this spec constrains order:
unification must land AFTER `jbipfa`, or it will conflict with a reviewed plan over the same function.
See Section 6.

### 4.7 Validation that exists on only one side is UNIONED

RULED: every refusal present on either side is present on both after unification. Named explicitly,
because C2 is the criterion the five historical instances all violated:

| Refusal | Lives today in | After |
|---|---|---|
| `implementing -> implemented` requires resolvable `--evidence` | `specs.run_set` only | both (`h4fiwa`) |
| `deferred` requires a gate kind IN the vocabulary and a valid ref shape | `specs.run_set` only | both (`fv4b6s`) |
| post-write `validate_spec` conformance refusal | `specs.run_set` only | both |
| `--message` / `--gate-ref` unsafe-descriptive refusal | `backlog.run_set` only | both |
| `--work-kind` / `--priority` enum refusal at the function | `backlog.run_set` only | both |
| ambiguous-selector refusal, cross-type refusal, confirmation gate | `status_set` only | both |
| `evaluate_blocking_close`, gate-field clearing, `decide_gate_default` | both already | both (unchanged) |

THE LAST ROW IS THE POINT OF THE TABLE: three behaviors already had to be written twice. After
unification a sixth instance of this class has one place to be written.

## 5. Constraints the implementation MUST bind

- S1. No test may verify unification by reading production source with `inspect`, `ast`, regex or
  substring search, by counting callers, or by asserting a symbol census. Every proof DRIVES a surface
  and asserts on outputs, exit codes and written files (`AGENTS.md`, GUIDING_PRINCIPLES P16). This is
  stated as a MUST because "there is now only one implementation" is exactly the claim a lazy author
  would pin with `grep`.
- S2. `backlog.run_set` and `specs.run_set` keep their current names and callable signatures. Dozens
  of tests build their `Namespace` by hand and `runner_shared.close_backlog_item` builds argv for one;
  renaming them converts a behavior change into a mass test rewrite that hides it.
- S3. Every cross-spelling comparison normalizes the DATE BY SHAPE and passes an explicit `--message`,
  until the clock and defaulted-message axes are closed elsewhere. A comparison omitting either is red
  for part of every day; `test_release_exempt_setter_roundtrip_and_parity` is the measured precedent.
- S4. The migration is INCREMENTAL AND PER-VERB, never one commit. `specs` and `backlog` land
  separately, each with its differential harness green before the next starts.
- S5. No commit may both unify a path and fix an axis Section 7 defers. The two are separately
  reviewable and a combined commit makes the gate change unreviewable.

## 6. Migration

ORDER IS CONSTRAINED BY THREE LIVE ARTIFACTS, not by preference. Each is `reviewed` or `approved`
already and edits a function unification touches, so landing first costs nothing and landing second
costs a conflict with work a human already reviewed.

1. `jbipfa` (`reviewed`) gives `backlog._reattach_history` its label parameter. Unification's history
   parity depends on the label agreeing, and `jbipfa` edits the same function. MUST land first.
2. `ulepef` (`to-review`, `Blocks-Release: next`) moves the sidecar append after the durable write and
   ALREADY carries the `2vev8j` amendment. 4.3 adopts its ordering as settled. MUST land first.
3. `nvsz19` (`approved`, `Blocks-Release: next`) wires the plan transition table into
   `status_set.validate_transition_allowed`, the exact function 4.7 unions refusals into. MUST land
   first.

THEN, in order: the two behavior-preserving dedups (4.1's duplicated helpers, needing no ruling), the
differential harness (which must be GREEN on the already-agreed axes BEFORE anything moves, so a
regression is attributable), then `specs`, then `backlog`.

SPEC AMENDMENT THIS WORK REQUIRES. `1525-02` R2 names `specs set` and `backlog set` as the writers
that append a sidecar record. After 4.3 the writer is the shared engine, conditioned on record type.
The REQUIREMENT is unchanged and the SITE moves, so R2 takes a dated amendment note recording the new
site, in the style that spec already uses for its 2026-09-22 and 2026-09-28 amendments. Likewise
`0151-01` names `specs.run_set` by symbol as the `--by-human` site; that attestation is already
duplicated into `status_set`, so the contract is intact and only the cited location moves.

## 7. Out of scope, and filed separately

Each row is an axis the two paths differ on that this spec deliberately does NOT close, with the
artifact that owns it. Unification NORMALIZES AROUND each (C4, S3) rather than fixing or assuming it.

| Axis | Owner | Why not here |
|---|---|---|
| UTC versus local clock | `2wae2x` / `fnb8pl` / `lq2w86` (all `open`, all release-gated) | A live release-blocking bug filed three times; `2vev8j` 4.4 already rules UTC correct. Absorbing it into a `chore` would silently swallow gated work. |
| History label token | `jbipfa` (`reviewed`) | Owned by a reviewed plan over the same function. 4.6 defers. |
| Same-status dedup asymmetry | `r74211` (`open`) | Decides whether a write HAPPENS, not what it says; different blast radius. |
| Sidecar write ORDER | `ulepef` (`to-review`) | Already carries the `2vev8j` amendment. 4.3 adopts its ordering. |
| Backlog transition table | `t1gbwg` (`open`) | A vocabulary DESIGN question; unification only reduces the enforcement sites from two to one. |
| `--dry-run` dead `apply` read | `19lmbe` (`open`, release-gated) | The symptom is repaired; the dead read survives. Unification removes it as a side effect, so the item must be closed EXPLICITLY with evidence, never silently. |
| Audit of items already closed through the ungated spelling | `mbjuv5` (`open`) | A report over history, not a code change. |
| Hand-edited illegal transitions | `4ynlcg` (`open`) | The UNTOOLED path; unification is entirely about the tooled one. |
| `aw prompts set` registered or removed | `68sur3` (`open`, filed here) | A scope decision (register versus delete), not a dispatch question. |
| `production_checks.backlog_graduate_legitimacy` tautological clause | recorded in `jbipfa` F-07 | Needs a contract decision about what that check should test. |
| Actor string, defaulted message | `jbipfa` Deferred (declined) | Declined there as truthful attribution; no carrier wanted. |

## 8. Open questions

### OQ-1 (BLOCKING): is type-conditional sidecar behavior acceptable, or should the sidecar be dropped entirely?

4.3 rules that the shared engine appends a sidecar record for `backlog` and `specs` only. That keeps
`1525-02` R2 satisfied at the cost of a type conditional inside the newly unified engine, which is
mildly against the spirit of unification.

THE ALTERNATIVE is to drop the sidecar write entirely, making the engine uniform and leaving inline
history as the single durable record. That is cleaner and is arguably where `1525-02`'s own amendments
were already heading (its R3 and R4 were both amended to describe the sidecar as a machine-local
activity log that is NOT the durable store). It would require amending R2 from a MUST to a removal,
deleting `test_backlog_set_appends_sidecar_and_preserves_inline`, and deciding the fate of
`aw record-history`.

WHAT WOULD CHANGE THE ANSWER: whether anyone uses `aw record-history`. If the answer is no, dropping
is better and the conditional disappears. This is a maintainer call about a shipped read verb, not an
implementation detail, which is why it blocks rather than being resolved by the author.

- Blocking: yes
- Owner: maintainer

### OQ-2 (NON-BLOCKING): should 4.5's selector widening apply to `aw specs set --status`?

4.5 gives the flag spellings the shared selector vocabulary. For `backlog` this is a clear
improvement (it replaces a silent `paths[0]` write with a refusal). For `specs` the flag path takes a
PATH ONLY today, so widening it to accept an id6 or a setid is a genuine new capability rather than a
correction, and a setid selector could transition several specs in one call, which for an
approval-gated artifact deserves a moment's thought.

AUTHOR'S RECOMMENDATION: widen it, because the positional spelling ALREADY accepts those selectors for
specs, so the capability is reachable today by typing the other spelling; withholding it from one
spelling preserves exactly the kind of false expectation this spec exists to remove. Proceeding on
that reading unless the maintainer objects.

- Blocking: no
- Owner: maintainer
