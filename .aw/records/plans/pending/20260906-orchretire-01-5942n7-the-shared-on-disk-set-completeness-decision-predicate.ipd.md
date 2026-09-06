# IPD: the shared on-disk Set-completeness decision predicate

- Date: 2026-09-06
- Kind: child
- Concern: The runner cannot answer "is this Set now complete?". `_set_children_all_executed` (`oc_runipd.py:751-770`) inspects `state["queue"]` ONLY, so a run that executes the Set's LAST outstanding child while earlier children were executed in PREVIOUS runs sees one child, not the Set. `wslayout` passed its check only incidentally (child `wpu5zu` executed in an earlier run and absent from the queue; the four present children happened to be `executed`). Its "no children in-queue" branch returns `(False, [])`, which produced `5e4sb6`'s event with `unfinished_children: []` and a run summary reading "dependency-blocked (unmet dependencies)" naming no dependency. And a check over EXISTING members is not sufficient: `rununify`'s two children are both `executed` on disk, yet its child table declares a row `03+` that was never authored, so a naive "all members executed" rule would wrongly retire `5e4sb6`.
- Scope: Build ONE shared, host-neutral predicate in `runner_shared.py` that decides whether a Set is retirement-eligible, reading the PLANS TREE rather than a run queue, and returning a typed reason for every refusal. Implements spec `77tr3o` R-1, R-2, R-3, R-9, R-10. It DECIDES ONLY and performs no transition (child 02 owns that) and touches no dispatch site (child 03 owns that). It does NOT change `_set_children_all_executed`'s callers, does NOT alter `EXECUTION_SUCCESS_STATES` (spec Section 4), and does NOT touch the `dependency-blocked` write.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: orchretire
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 5942n7
- Approval: 2026-09-06, recorded via aw ipd set: status set to approved
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history
- 2026-09-06 approved (aw set): status set to approved
- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-101..PR-105 fixed, Readiness go-pending-approval

- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-105 all FIXED, no deferrals, no open questions. E-01/E-02's expected outcomes were re-measured by actually calling `selectors.resolve` + `ipd_lint.parse` for every live Set and match exactly. The substantive finding is PR-101 (HIGH): E-03 parsed the child table as if orchestrators shared one column layout, and they do not. Measured across all five live orchestrators, the five layouts share only the FIRST column and `rununify` has NO `Id` column at all, so a parser keyed on a named header either crashes or vacuously passes on the one Set the check exists for; `rununify` also carries a `last` row token the plan never mentioned alongside `03+`. PR-102 (HIGH): the declared-vs-resolved comparison had no stated direction, and `runprofile` has SIX children on disk against five declared rows (`kgpptv`, Order 6), so a symmetric rule would refuse a legitimately-extended Set forever. PR-103 (MEDIUM): F-4 asserted `nna8yz` "carries `substantially-complete` today", but its PLAN FILE carries `Status: approved` and the value exists only in a run `state.json`; since this predicate reads the plans tree, the guard needed restating as defense against a value from another caller. PR-104 (MEDIUM): the status test was a denylist of known-bad values rather than an `executed`-only allowlist. PR-105 (MEDIUM): the gate lacked the scope-fence/commit wording and, more importantly, never stated the asymmetric failure direction that is the design's whole basis. Self-review disclosure in the review record.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o. Every cited line and measurement verified at HEAD 844d195c.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give both runners one truthful answer to "may this Set's orchestrator be retired now?", computed from
the plans tree so it is correct across runs, and carrying a typed reason so the four distinct refusal
causes stop sharing one misleading message.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the predicate

- [ ] E-01 Add a host-neutral Set-membership reader to `runner_shared.py` that returns every member of a Set from the PLANS TREE with its `Id`, `Order`, `Kind` and `Status`. Reuse the existing resolvers rather than adding a third "which plans exist" mechanism: `selectors.resolve(repo_root, "plans", setid)` already returns members across `pending/` and `executed/`, and `ipd_lint.parse(text).meta_fields` already yields the four fields. Verified working at HEAD: for `wslayout` it returns 5 children all `executed` plus orchestrator `rh5tt6` `approved`; for `lanectn` it returns 4 `executed` children plus `nna8yz`/`xdr83v` at `approved`.
  - Depends on: none
  - Expected outcome: a function that, given a repo root and a setid, returns the Set's members read from disk; a Set with members only in `executed/` is returned in full, which is the case the queue-scoped check cannot see.
  - Execution state: pending

- [ ] E-02 Add the retirement-eligibility predicate returning a typed decision, not a bare bool. It is eligible ONLY when the Set has at least one child AND every child's on-disk `Status` is exactly `executed` (spec R-2). Refuse with a DISTINCT typed reason for each of: children exist but are unfinished (naming the unfinished ids and their actual statuses); the Set has no children at all; the orchestrator's child table declares rows that resolve to no plan (spec R-3, the `rununify` case). ACCEPT EXACTLY `executed` AND NOTHING ELSE, an allowlist rather than a denylist of known-bad values, so a status added later cannot silently become acceptable. `substantially-complete` in particular MUST NOT qualify: it means finalize refused (`i452hf`). Note precisely what that guard is, per F-5: `substantially-complete` is a RUN-STATE disposition and `nna8yz`'s PLAN FILE carries `Status: approved`, so a plans-tree read will not encounter the value at all; the guard defends against it arriving from another caller, and this plan must not claim `nna8yz`'s plan file carries it.
  - Depends on: E-01
  - Expected outcome: `wslayout` -> eligible; `lanectn` -> refused naming `nna8yz` and `xdr83v` with their real plan-file statuses (`approved`, not `substantially-complete`); `rununify` -> refused for unauthored child rows, NOT eligible; a synthetic child bearing any status other than `executed` -> refused.
  - Execution state: pending

- [ ] E-03 Implement the unauthored-child-row detection E-02 depends on, and make it FAIL CLOSED. Parse the orchestrator's `## Child IPDs, sequence, and dependencies` table for declared Order tokens and compare against the Orders that actually resolve to plans. The HEADING is safe to key on (schema-enforced, `ipd_schema.py:59` `H_CHILD_IPDS`, and identical in all five live orchestrators, verified); the TABLE BODY is not, so treat it as free-form prose per spec OQ-2.

  MEASURED COLUMN SHAPES, because assuming one is how this check silently passes everything. All five live orchestrators, at review time: `orchretire` `Order|Id|Child|Depends on`; `wslayout` `Order|Id|What it does|Set dependencies`; `runprofile` `Order|Id|Child|Responsibility|Depends on`; `lanectn` `Order|Id|Depth|Requirements owned|Prerequisite|What it delivers`; `rununify` `Order|What it does|Depends on` with NO Id column at all. So the ONLY column present in all five is the FIRST, and the Order token must be read positionally from it rather than by locating a named header. Do not require an `Id` column.

  ROW TOKENS ARE NOT ALL NUMERIC, also measured: `rununify` carries `03+` AND a row whose token is the word `last`. Treat any non-numeric, open-ended, or unparseable token as "declares more children than exist" and refuse. When the table cannot be parsed at all, REFUSE (spec OQ-2 permits a conservative refusal and R-3 requires one); never treat an unparseable table as "fully authored".

  THE COMPARISON IS ONE-DIRECTIONAL AND MUST STAY THAT WAY. Refuse only when a DECLARED row resolves to no plan. Do NOT refuse when a resolved child has no declared row: `runprofile` declares Orders 01-05 and has SIX children on disk (`kgpptv` at Order 6, `reviewed`), so a symmetric "table and disk must match" rule would refuse a Set that is legitimately more authored than its table. That direction is R-2's job (the extra child is simply not `executed`), not R-3's.
  - Depends on: E-01
  - Expected outcome: `5e4sb6`'s `03+` and `last` rows are detected as unauthored; `rh5tt6`'s table, whose five rows all resolve, is detected as fully authored; `rununify`'s Id-less column shape parses rather than crashing or vacuously passing; `runprofile`'s undeclared sixth child does NOT trigger an unauthored-rows refusal; a table with no recognizable rows refuses.
  - Execution state: pending

- [ ] E-04 Write `tests/test_orchestrator_retirement.py` covering the predicate against synthetic Sets in a temp repo, one test per typed reason, plus the FOUR real column shapes as fixtures derived from this repo's own measured states: `wslayout` (all-executed, eligible), `lanectn` (unfinished children), `rununify` (unauthored rows AND no `Id` column AND the non-numeric tokens `03+`/`last`), and `runprofile` (more children on disk than the table declares, which must NOT refuse per F-7). Copy each fixture's table shape rather than inventing a uniform one: a synthetic table in this plan's own format would exercise the one shape the parser is guaranteed to handle and none of the four that broke it. Include the cross-run case explicitly: a Set whose children are all in `executed/` and NONE of which is in any queue must be eligible, because that is the maintainer's stated requirement and the defect the queue-scoped check causes.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test module whose failures name the specific reason that regressed, and which covers all four measured column shapes rather than one idealized shape.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` is 4-6x slower here and a second `-q` suppresses the summary line this plan's evidence requires.
- The anti-re-fork discipline from `2r306y`/`818uru` is binding: shared runner logic lives in `runner_shared.py` exactly once and is IMPORTED by both hosts, never copied. This plan's whole purpose is to put the decision in that one place.
- `substantially-complete` is in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:274`) for DEPENDENCY-EDGE purposes. That is out of scope (spec Section 4) and must not be changed here; this predicate simply does not accept it.
- Reuse `selectors.resolve` and `ipd_lint.parse`; do not add a path literal for the plans tree.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | HIGH | `oc_runipd.py:751-770` | `_set_children_all_executed` reads `state["queue"]` only, so Set completeness cannot be evaluated across runs. This is why the maintainer's "fires when the last outstanding child completes" requirement is unimplementable today. | source read at HEAD `844d195c` |
| F-2 | HIGH | `rununify` | A completeness check over existing members is unsound: both children `executed`, orchestrator would be wrongly retired, but child row `03+` was never authored. | `aw find plans --set rununify` shows only Orders 01, 02; `5e4sb6` child table row `03+` |
| F-3 | MED | `5e4sb6` event | "no children in queue" returns `(False, [])`, producing "dependency-blocked (unmet dependencies)" naming none. The safe default is right; the message is the defect. | `events.jsonl`: `reason: not-all-children-executed, unfinished_children: []` |
| F-4 | MED | `nna8yz` | `substantially-complete` must not count as executed: its work is real but stranded on `aw/lane/nna8yz` (tip `396ddebf`, not an ancestor of HEAD), and its plan is still in `pending/`. | `git merge-base --is-ancestor` returns false; `aw find plans --id nna8yz` shows `pending` |
| F-5 | MED | this predicate's INPUT DOMAIN | `substantially-complete` is a RUN-STATE disposition, NOT a plan-file `Status:`. Measured: `nna8yz`'s plan file carries `Status: approved`, while `substantially-complete` appears for it only in `run-20260905T211011Z-3780617`'s `state.json` queue entry. Since E-01 reads the PLANS TREE, this predicate will never SEE that value from its own input, so "reject `substantially-complete`" is a guard against a value arriving from elsewhere rather than a case the plans tree produces. State it that way and do not let a passing test on a synthetic plan file carrying an impossible `Status:` be mistaken for proof about real data. | `nna8yz` plan `- Status: approved`; run `state.json` queue entry `substantially-complete` |
| F-6 | MED | child-table column shapes | The five live orchestrators use FIVE different column layouts and only the FIRST column is common; `rununify` has no `Id` column at all, and carries non-numeric row tokens `03+` AND `last`. Any parser keyed on a named header or assuming numeric tokens either crashes or vacuously passes. | measured across all five `-00-` plans at review time |
| F-7 | MED | `runprofile` | Disk can legitimately hold MORE children than the table declares: `runprofile` declares Orders 01-05 and has six children (`kgpptv`, Order 6, `reviewed`). So the declared-vs-resolved comparison must be one-directional, or a legitimately-extended Set is refused forever. | `selectors.resolve` returns Orders 0-6; the table's last row is `05` |

## Proposed changes (ordered, validatable)

1. E-01 membership reader over the plans tree, reusing `selectors.resolve` + `ipd_lint.parse`, separating the orchestrator from the children by `Kind`/`Order` rather than by path count.
2. E-03 unauthored-row detection: positional first-column Order token (no named-header assumption, no `Id` column requirement), non-numeric tokens refuse, one-directional declared-vs-resolved comparison, failing closed on an unparseable table.
3. E-02 eligibility predicate returning a typed decision consuming both, accepting exactly `executed` as an allowlist.
4. E-04 tests, including the cross-run case and all FOUR real column shapes.

## Deferred / out of scope (with reason)

- Performing the transition: child 02. This plan decides only, so a wrong decision cannot move a plan.
- Wiring the dispatch sites and removing the terminal-status write: child 03.
- `EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for dependency EDGES: spec Section 4; a real defect (it is why `xdr83v` was dispatched against an unlanded prerequisite) but separately owned.
- Retiring the four currently-stuck orchestrators: a consequence of the Set, not part of the mechanism.

## Scope check

- Over-scope: none.
- Under-scope: the predicate is unreachable from a real run until child 03 wires it. That is deliberate sequencing, and child 02 and 03 both declare the dependency.

## Required tests / validation

`python3 -m pytest` bare, with the new module's per-reason tests passing and no pre-existing test regressing. The baseline MUST be measured at execution time and pasted, not carried from this plan: the suite reported `4517 passed, 3 skipped, 4 xfailed` at HEAD `844d195c`, and a lane worktree legitimately reports more failures (35 measured on `xdr83v`'s lane, all lane-environment artifacts), so compare failing NODE IDS, never totals.

## Spec / documentation sync

Spec `77tr3o` R-1/R-2/R-3/R-9/R-10 are implemented here; no spec text changes. `AGENTS.md` correction is child 03 (R-11).

## Open questions

### OQ-01: how strictly must the child-IPD table be parsed to satisfy R-3?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, and CONFIRMED BY THE MAINTAINER 2026-09-06 when asked directly (spec `77tr3o` OQ-2). He chose TABLE PARSING over the alternative of requiring an explicit "child set complete" field on every orchestrator, because the field would have to be backfilled everywhere before the check could be trusted, and until then an unbackfilled parent would be indistinguishable from an incomplete one. He accepted the acknowledged weakness: the table is prose and `5e4sb6`'s row token is literally `03+`, so exact numeric parsing is impossible in the one case that matters. E-03 therefore treats any non-numeric or open-ended token, and any unparseable table, as "declares more children than exist" and refuses. This can only produce a FALSE REFUSAL (an orchestrator lingers, the status quo), never a false retirement, so the failure direction is safe by construction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session calling the new reader for `wslayout` and `lanectn` against this repo, showing the returned members with Id/Order/Kind/Status. `wslayout` must show 5 children all `executed` plus orchestrator `rh5tt6` `approved`; `lanectn` must show 4 `executed` children plus `nna8yz` and `xdr83v` at `approved` and orchestrator `h0zljh`. Both must be read with NO run state present, proving the plans tree is the source. Note `selectors.resolve` returns the ORCHESTRATOR among the paths (measured: 6 paths for `wslayout`, 7 for `lanectn`, 3 for `rununify`), so show that the reader distinguishes it by `Kind`/`Order` rather than counting paths as children.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the typed decision for all three real Sets: `wslayout` eligible; `lanectn` refused naming both unfinished ids WITH their real plan-file statuses; `rununify` refused for unauthored rows. Also paste a synthetic case where a child is `substantially-complete` and show it is REFUSED with the reason naming that status, AND state explicitly that this is a guard on a value the plans tree does not itself produce (F-5: `nna8yz`'s plan file carries `approved`). Finally show the allowlist behaves as one: a child bearing some OTHER non-`executed` status is refused too, so the guard is not a denylist of known-bad values.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the detection result for all FOUR measured column shapes: `5e4sb6`/`rununify` (unauthored, triggered by `03+`, and show the `last` row token is also handled, on a table with NO `Id` column); `rh5tt6` (fully authored, all five rows resolve); `h0zljh`/`lanectn` (six-column shape with a `Depth` column, parsed rather than crashed); and `3m0urk`/`runprofile` (declares 01-05, has SIX children on disk, and must NOT report unauthored rows per F-7). Then paste a synthetic unparseable table showing it REFUSES rather than passing. A pass on this plan's own table shape alone does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line showing the new module's tests passing and the total not regressing against a baseline measured in the same worktree at execution time. Then paste one deliberate SABOTAGE per typed reason (e.g. flip a child's status to `substantially-complete`) showing the corresponding test FAILS, proving the tests bind behavior rather than merely passing. Include a sabotage for the column-shape coverage specifically: make the row parser require a named `Id` column and show the `rununify` fixture FAILS, which is the regression a single-shape test suite would have missed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Stay inside `Scope-Paths`; `oc_runipd.py` and `agy_runipd.py` are explicitly OUT of
bounds for this child even though they are the eventual consumers, because child 03 owns wiring and two
plans editing the same dispatch region is the contention this Set is sequenced to avoid. Do not expand
scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in
the two-way scope reconciliation at finalize (`aw ipd finalize` refuses without a `--scope-reason` per
out-of-scope path and a `--scope-ack` per declared-but-unmodified path). Do not change
`EXECUTION_SUCCESS_STATES`, `TERMINAL_STATES`, or the `dependency-blocked` write.

THE FAILURE DIRECTION IS THE WHOLE DESIGN, and it is asymmetric on purpose: a FALSE REFUSAL leaves an
orchestrator lingering in `pending/`, which is exactly today's status quo and costs nothing new; a FALSE
ELIGIBILITY retires a plan whose Set is not done, asserting completion that never happened. So whenever
the code cannot tell, REFUSE. Accept exactly `executed` as an allowlist, never a denylist of known-bad
statuses. Parse the child table defensively: read the Order token POSITIONALLY from the first column (the
five live orchestrators share no other column, and `rununify` has no `Id` column at all), refuse on any
non-numeric or open-ended token (`03+`, `last`), and compare DECLARED-to-RESOLVED only, never the reverse
(`runprofile` legitimately has six children against five declared rows).

PASTE ACTUAL OUTPUT for every `V-*`; a claim of success without pasted evidence is a contract violation.
Test against the FOUR real column shapes, not a synthetic uniform one; a parser validated only on this
plan's own table format is validated on the one shape that was never going to break. Measure the suite
baseline in YOUR worktree before asserting a regression, and compare failing node ids rather than totals.
Commit path-scoped only (`git commit -m msg -- <path>`); never `git add -A`/bare/`-a`; never push; never
tag or release; and because others may be working in this checkout, verify `git diff --cached
--name-only` before each commit and unstage anything that is not yours. All open questions are resolved;
no maintainer decision is outstanding.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
