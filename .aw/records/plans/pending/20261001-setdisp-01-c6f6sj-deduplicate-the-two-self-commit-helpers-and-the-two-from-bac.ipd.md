# IPD: Deduplicate the two self-commit helpers and the two From-Backlog gate-inheritance blocks

- Date: 2026-10-01
- Kind: child
- Concern: Two behaviors of the forked `set` dispatch are implemented TWICE in near-identical form, and one of the two copies has ALREADY DRIFTED in its user-visible output. (1) `status_set._offer_self_commit` and `specs._offer_specs_set_commit` both unstage the target paths with `_git(["reset","--quiet","HEAD","--",*paths])`, then call `git_commit_helper.offer_commit` with `on_unrelated_staged="scope"`, the same `assume_yes` expression (`--commit`, or `--yes` when not agent/json), the same `no_commit` read, and the same agent/json-versus-human reporting split; they differ only in the commit message label and in `print` versus `sys.stdout.write`. (2) The `From-Backlog` gate-inheritance block exists in `status_set.apply_status_change` and again in `specs.run_set`, each searching for an existing `- Blocks-Release:` line, each calling `backlog.blocks_release_of_item`, each calling `releases.set_blocks_release_line`; and BOTH print the literal prefix `aw set: inherited - Blocks-Release: ...` even though one of them is only ever reached by `aw specs set`, so the `aw specs set --status` spelling misattributes its own output to another verb. These are the measured, no-ruling-required half of backlog `fcnz1r`.
- Scope: IN: collapse each duplicated pair to ONE implementation reached by both callers, preserving today's observable behavior on every axis EXCEPT the one misattributed output prefix, which is corrected to name the verb that actually ran; author outcome tests driving both spellings for both behaviors. OUT, each with a reason recorded under "Deferred": any change to WHICH engine a spelling dispatches to (that is children 04 and 05, and it is gated on spec `wy9aru`); the self-commit message LABEL, which legitimately differs per record type; every axis Section 7 of `wy9aru` assigns elsewhere (clock, history label, dedup, sidecar order, dry-run `apply` read).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/specs.py, tests/test_set_dispatch_dedup.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: wy9aru
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: c6f6sj

## Workflow history
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r` under spec `wy9aru`. This is the Set's UNGATED child: it needs no ruling from `wy9aru`'s open questions because it changes no dispatch and no gate. The duplication and the drifted output prefix were both read off the two functions at HEAD `ec857565a`; the suite baseline was measured BARE at that HEAD (`3512 passed, 2 skipped, 3 warnings in 111.12s`).
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Remove the two duplications in the `set` family that require no design decision, so that the later
dispatch-unification children have less duplicated surface to reconcile, and so the one place where
duplication has already produced a user-visible wrong string stops lying about which verb ran.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one self-commit helper

- [ ] E-01 Collapse `specs._offer_specs_set_commit` into `status_set._offer_self_commit`, so one function serves both spellings. Give the surviving function the label it already takes (`scoped_type_canonical`, which it already turns into `chore(<label>): set status <status>`), and have `specs.run_set` call it with the canonical type `specs`, which reproduces its current message `chore(specs): set status <new_status>` EXACTLY.

    PRESERVE THREE BEHAVIORS THAT LOOK INCIDENTAL AND ARE NOT. FIRST, the `_git(["reset","--quiet","HEAD","--",*paths])` call before `offer_commit` must stay, and must stay SCOPED TO THE VERB'S OWN PATHS: its comment records it as `jgcm68` D2, and a bare `reset` in a shared checkout would unstage a co-worker's staged work (`AGENTS.md`). SECOND, `on_unrelated_staged="scope"` must stay, for the same reason. THIRD, the empty-path early return must stay in the surviving function; both copies have it, and `offer_commit` with an empty path list is not the same as not calling it.

    THE ONE OBSERVABLE DIFFERENCE TO RESOLVE DELIBERATELY: the two copies report through different sinks. `_offer_self_commit` uses bare `print` for the human branch; `_offer_specs_set_commit` uses `sys.stdout.write` with explicit newlines. Both land on stdout with identical text, so KEEP THE SURVIVING FUNCTION'S `print` and record in the commit message that the sink changed for the specs path while the bytes did not. If a test captures stdout rather than patching `print`, this is invisible; verify that rather than assuming it.

    DO NOT "simplify" the `assume_yes` expression while moving it. It reads `--commit` OR (`--yes` AND NOT agent/json), and the agent/json exclusion is deliberate: an agent passing `--yes` to clear a confirmation gate must not thereby be taken to have authorized a commit. Both copies carry it identically; preserve it character for character.
  - Depends on: none
  - Expected outcome: `agent_workflows/specs.py` no longer defines `_offer_specs_set_commit`; `specs.run_set` calls the shared helper; `aw specs set <path> --status <s>` with `--commit` produces a commit whose message is byte-identical to today's (`chore(specs): set status <s>`), staging exactly the spec file(s) and nothing else; the same call with `--no-commit` commits nothing; an unrelated staged path is never folded in.
  - Execution state: pending

- [ ] E-02 Correct the misattributed output prefix in the `From-Backlog` inheritance notice, THEN collapse the duplicated block. Today both copies print `aw set: inherited - Blocks-Release: <gate> from backlog item <id6> (graduation handoff: the gate travels with the work)`. The copy inside `specs.run_set` is reached ONLY by `aw specs set <path> --status ...`, so it tells the user a verb they did not type.

    THIS IS THE FINDING THAT JUSTIFIES THE WHOLE SET AND IT MUST BE RECORDED, NOT JUST FIXED. The drift is the predicted consequence of duplication, observed in the wild: one copy was edited (or authored) without the other, and the surviving string names the wrong verb. Cite it in the commit message as the measured instance.

    Have the SHARED implementation take the verb label it should print and derive the prefix from it, so neither copy can drift again. The positional spelling keeps printing `aw set:` (it genuinely is `aw set`'s engine, and `aw ipd set`/`aw backlog set`/`aw specs set` all route there, so a per-verb prefix for the positional spelling is a SEPARATE question this plan does not open); the `aw specs set --status` spelling prints `aw specs set:`, matching every other message that function emits (`aw specs set: refused: ...`, `aw specs set: deferred requires ...`).

    PRESERVE THE THREE SEMANTICS OF THE BLOCK EXACTLY, each of which `status_set`'s comment records a reason for. (1) It is A WRITE, NEVER A REFUSAL: an un-inheritable gate must not fail the call, because `check.from-backlog-gate-mismatch` already catches a mismatch at rest. (2) An EXPLICIT `--blocks-release` in the same call WINS, which is why the block is guarded by `getattr(args, "blocks_release", None) is None`. (3) An EXISTING gate on the artifact is NEVER overwritten, which is why it searches for `- Blocks-Release:` first and does nothing when found.

    NOTE THE TWO COPIES RESOLVE THE REPO ROOT DIFFERENTLY and the shared implementation must take it as a parameter rather than re-deriving it: `status_set` already holds a `repo_root`, while `specs.run_set` computes `_repo_root_of(path)`. Passing it in keeps both call sites' current resolution intact; re-deriving inside would silently change one of them.
  - Depends on: none
  - Expected outcome: one implementation of the inheritance block, called from both sites; `aw specs set <path> --status implementing --from-backlog <id6>` on a gated item prints a notice prefixed `aw specs set:` and writes the inherited `- Blocks-Release:`; the positional spelling still prints `aw set:`; in both, an explicit `--blocks-release` wins, an existing gate is untouched, and an un-inheritable gate does not fail the call.
  - Execution state: pending

### Task group 2: fence both dedups with outcome tests

- [ ] E-03 Author `tests/test_set_dispatch_dedup.py` covering the SELF-COMMIT behavior through BOTH spellings. Every test DRIVES a CLI surface and asserts on the resulting git state; none may read production source with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). The point of this file is to prove ONE implementation by proving IDENTICAL OBSERVABLE BEHAVIOR, which is the only proof P16 permits.

    Cover, each as a named test: (a) `aw specs set <path> --status <s> --commit` produces exactly one commit whose message is `chore(specs): set status <s>` and whose staged set is exactly the spec file (assert on `git show --stat --name-only` and `git log -1 --format=%s`); (b) the POSITIONAL spelling over the same fixture produces the same message and the same single-path staged set; (c) with an UNRELATED staged file present, neither spelling folds it into the commit, and the unrelated staging survives the call (this is the `on_unrelated_staged="scope"` property, and it is the one with real consequences in a shared checkout); (d) `--no-commit` commits nothing on both spellings; (e) `--yes` WITHOUT `--commit` and WITH `--agent` commits nothing (the deliberate agent/json exclusion in `assume_yes`).

    Test (e) is the one a careless refactor of E-01 would break silently, so do not drop it as redundant: `--yes` is routinely passed by automation to clear the confirmation gate, and the distinction between that and commit authorization is the whole reason the expression is shaped as it is.
  - Depends on: E-01
  - Expected outcome: a new test module whose five named self-commit cases pass after E-01; case (c) demonstrably fails if `on_unrelated_staged="scope"` is dropped and case (e) if the agent/json exclusion is dropped (demonstrate both with a throwaway probe, then revert it and show `git status --porcelain` clean).
  - Execution state: pending

- [ ] E-04 Extend `tests/test_set_dispatch_dedup.py` with the `From-Backlog` INHERITANCE cases, through both spellings. Cover: (a) the `--status` spelling on a gated backlog item inherits the gate AND prints a notice prefixed `aw specs set:` (assert the prefix positively by name, so the corrected attribution is pinned and cannot silently revert to `aw set:`); (b) the positional spelling inherits the gate and prints `aw set:`; (c) an explicit `--blocks-release` in the same call WINS over inheritance on both spellings; (d) an artifact that ALREADY carries a `- Blocks-Release:` keeps its own value on both spellings; (e) `--from-backlog` naming an item that does not resolve does NOT fail the call and does NOT write a gate (the write-never-refuse property).

    Case (e) must assert the EXIT CODE is 0 and the status change still happened, because the tempting wrong fix is to refuse. `status_set`'s comment records why refusing is wrong: it would break a link the author is legitimately recording, and the at-rest checker already catches the mismatch.
  - Depends on: E-02
  - Expected outcome: five further named cases passing after E-02, with the `aw specs set:` prefix asserted by name in (a) and `aw set:` in (b), so a future regression that re-unifies the prefix to the wrong verb fails here.
  - Execution state: pending

### Task group 3: record the change

- [ ] E-05 Add ONE `CHANGELOG.md` entry under the pending-release heading recording the only USER-VISIBLE effect, which is that the message `aw specs set --status --from-backlog` prints when it inherits a release gate now names `aw specs set` instead of `aw set`.

    CONSTRAINTS ON THE WORDING. Describe only that effect. Name no private helper. Write no em or en dashes (user-facing prose, `AGENTS.md`). Do NOT describe the two deduplications: they are invisible to a user, and an internal refactor in a changelog teaches a reader to expect a behavior change that did not occur.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: one entry in the file's established voice naming the corrected message attribution and nothing else, containing no em or en dash.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites only symbols and quoted strings, deliberately: `status_set.py` is 2785 lines and three other live plans edit it.
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). "There is now only one implementation" is exactly the claim a lazy author pins with `grep`; it must instead be proven by driving both spellings and showing identical observable behavior.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden (several times slower here) and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- `git_commit_helper.offer_commit`'s `on_unrelated_staged="scope"` is the mechanism that makes a `set` self-commit safe in a SHARED CHECKOUT, where another agent's staged work may be present. Both duplicated copies pass it; it is a load-bearing argument, not a default.
- A self-commit is INTERACTIVE-GATED: TTY prompts, and non-interactive-without-`--commit` is a NO-OP. Tests must therefore pass `--commit` explicitly to exercise the commit path at all, which is why every case here names its flag.

## Findings

Every finding was established at HEAD `ec857565a` by reading the two function pairs in full and by running the suite bare. F-03 is a measurement of the tree, not of this change.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | LOW (DUPLICATION) | `status_set._offer_self_commit` and `specs._offer_specs_set_commit` read side by side: both early-return on empty paths, both `_gch._git(root, ["reset","--quiet","HEAD","--",*paths])`, both `_gch.offer_commit(..., on_unrelated_staged="scope")`, both carry the identical `assume_yes` expression and the identical agent/json reporting split. | **TWO FUNCTIONS, ONE CONTRACT, AND THE DIFFERENCES ARE COSMETIC.** They differ in the commit-message label (parameterized in one, hardcoded in the other) and in `print` versus `sys.stdout.write`. Neither difference is semantic, so this dedup needs no ruling from `wy9aru` and is the right first move in the Set: it reduces the surface the gated children must reconcile without depending on any open question. |
| F-02 | MEDIUM (DRIFT OBSERVED) | The `From-Backlog` inheritance block appears in `status_set.apply_status_change` and in `specs.run_set`. Both print the literal prefix `aw set: inherited - Blocks-Release: `. The second is reachable ONLY via `aw specs set <path> --status ...`. | **DUPLICATION HAS ALREADY PRODUCED A USER-VISIBLE WRONG STRING, WHICH IS THE WHOLE THESIS OF `fcnz1r` DEMONSTRATED RATHER THAN ARGUED.** A user running `aw specs set` is told `aw set:` did something. It is cosmetic in isolation, which is exactly why it survived: no gate failed, no test caught it, and the copy was never reconciled. Recording it matters more than fixing it, because it is evidence for the Set's premise that duplicating a behavior into a second path is not a durable fix. |
| F-03 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **THE BASE IS GREEN AT THIS HEAD, INCLUDING THE CROSS-SPELLING PARITY TEST, AND THAT IS A TIME-DEPENDENT FACT NOT A STABLE ONE.** `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` compares records across the two spellings and is RED whenever the machine's local date differs from UTC (plan `jbipfa` F-09 measured it red; it passes here). So an executor MUST re-derive the baseline and compare FAILURE SETS BY NAME, never counts against this row. |
| F-04 | LOW (SINK) | `_offer_self_commit` reports via bare `print`; `_offer_specs_set_commit` via `sys.stdout.write` with explicit `\n`. | **COLLAPSING THEM CHANGES THE SINK FOR ONE PATH WHILE THE BYTES STAY THE SAME.** Both land on stdout with identical text, so a test capturing stdout sees no change; a test patching `print` or `sys.stdout.write` by name would. E-01 requires verifying which, rather than assuming the first. |
| F-05 | LOW (ROOT RESOLUTION) | The two inheritance copies obtain the repo root differently: `status_set` uses the `repo_root` it already holds; `specs.run_set` computes `_repo_root_of(path)`. | **THE SHARED IMPLEMENTATION MUST TAKE THE ROOT AS A PARAMETER.** Re-deriving it inside would silently change one call site's resolution, which is the kind of invisible behavior change a "pure refactor" commit is least likely to be reviewed for. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/specs.py` + `agent_workflows/status_set.py`: one self-commit helper, called from both (E-01).
2. `agent_workflows/specs.py` + `agent_workflows/status_set.py`: one `From-Backlog` inheritance implementation, taking the verb label and the repo root as parameters, with the `aw specs set` prefix corrected (E-02).
3. `tests/test_set_dispatch_dedup.py`: new module, five self-commit cases (E-03) and five inheritance cases (E-04), all driving CLI surfaces.
4. `CHANGELOG.md`: one entry, for the corrected message attribution only (E-05).

## Deferred / out of scope (with reason)

- THE DISPATCH FORK ITSELF IS NOT TOUCHED HERE. `cli.main` still routes on whether `--status` was passed, and both engines still exist. That is deliberate: moving a spelling from one engine to another is gated on spec `wy9aru`, whose OQ-1 (the sidecar) is BLOCKING on a maintainer call, while these two dedups are gated on nothing. Splitting them is what lets the Set make real progress before that call arrives.
  - Carrier: 63zo2f
- THE SELF-COMMIT MESSAGE LABEL IS NOT UNIFIED. `chore(specs): ...` versus `chore(backlog): ...` is correct: the label names the record type the commit touches, and the surviving function already parameterizes it.
  - Carrier-Declined: not a defect; the label is per-type by design and the surviving implementation already takes it as an argument
- THE POSITIONAL SPELLING'S `aw set:` PREFIX IS NOT MADE PER-VERB. E-02 corrects the `aw specs set --status` copy to name its own verb, but leaves the positional spelling printing `aw set:` even when the user typed `aw backlog set` or `aw ipd set`. That is a wider question (one engine serves four verbs, and every message it emits would have to take the invoked verb's name), it affects messages this plan does not touch, and conflating it with a two-line attribution fix would make the fix unreviewable.
  - Carrier-Declined: deliberately not filed; the positional engine's prefix is CONSISTENT today (always `aw set:`) and so is merely terse rather than wrong, unlike the specs copy which names a different verb than the one that ran. Recorded in F-02 so a later author can take it up on its merits.
- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is untouched and must be normalized around, not fixed: the UTC-versus-local clock, the history label token, the same-status dedup asymmetry, the sidecar write order, and the dead `apply` read in the dry-run guard.
  - Carrier: wy9aru
- THE TWO MEASURED POSITIONAL GATE BYPASSES ARE NOT FIXED HERE. They are child 03's whole subject and each has its own release-gated carrier.
  - Carrier: m1jlwm

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-01, E-02), `agent_workflows/specs.py` (E-01, E-02), `tests/test_set_dispatch_dedup.py` (E-03, E-04), `CHANGELOG.md` (E-05).
- Under-scope: none. This plan declares no spec edit: it amends no contract, because correcting a message prefix that names the wrong verb is a defect fix against the existing contract rather than a change to it. Spec `wy9aru` governs the Set but is not edited by this child. The plan's own file under `.aw/records/plans/**` needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline on the tree as found before any edit and compare FAILURE SETS BY NAME, not counts: F-03 measured `3512 passed, 2 skipped` at HEAD `ec857565a`, but `test_release_exempt_setter_roundtrip_and_parity` is red for part of every day on the local-versus-UTC clock skew (`2wae2x`), so a changed count may mean nothing happened and a green base is not guaranteed.
- The new `tests/test_set_dispatch_dedup.py`, run and named individually, with case (c) (unrelated staged file) and case (e) (`--yes --agent` does not commit) each DEMONSTRATED to fail under a throwaway probe that removes the property they pin, and the probe then reverted with `git status --porcelain` shown clean.
- `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET, not an exit code. Re-derive the set before and after and require them identical. Do NOT attempt to make either exit 0, and specifically do not "fix" another plan's conformance finding or another lane's state: that is a co-worker's work in a shared checkout.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

Spec `wy9aru` (`to-review`) governs this Set and is NOT edited by this child. This plan implements its
Section 4.1 observation that the duplicated helpers need no ruling, and its Evidence rows E-5 and E-6
are the two duplications fixed here. No spec requirement changes, so no amendment is owed: `wy9aru`
Section 6's amendment obligation attaches to the children that MOVE the sidecar write site, which are
children 04 and 05.

No user-facing documentation describes either duplicated helper, so none needs updating. The single
user-visible effect (the corrected message prefix) is recorded in `CHANGELOG.md` by E-05.

## Open questions

### OQ-01: does any test assert the self-commit human output by patching `print` or `sys.stdout.write` rather than by capturing stdout?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: F-04 establishes that collapsing the two helpers changes the SINK for the specs path while leaving the bytes identical, so a stdout-capturing test is unaffected and a sink-patching test would break. The question is answerable in one search at execution time and its answer changes only whether E-01 must also adjust a test; it cannot change the design. Resolve it before E-01 and record the answer in E-01's evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git log -1 --format=%s` and `git show --stat --name-only HEAD` from a scratch repository after `aw specs set <path> --status <s> --commit`, showing the message `chore(specs): set status <s>` and exactly the spec file staged; the same pair after the POSITIONAL spelling showing the same message and path set; pasted output of the same call with `--no-commit` plus `git log --oneline` proving no commit was created; and the answer to OQ-01 stated with the search that produced it.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted stdout of `aw specs set <path> --status implementing --from-backlog <id6>` on a gated item showing a notice prefixed exactly `aw specs set:` and the resulting `- Blocks-Release:` line read back from the file; pasted stdout of the positional spelling showing `aw set:`; pasted evidence for all three preserved semantics (an explicit `--blocks-release` winning, an existing gate surviving untouched, and an unresolvable `--from-backlog` exiting 0 with the status changed and no gate written).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_set_dispatch_dedup.py -o addopts=""` output naming all five self-commit cases as passed; plus the throwaway-probe demonstration for cases (c) and (e), each showing the FAILURE output with the property removed and `git status --porcelain` empty after reverting the probe.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_set_dispatch_dedup.py -o addopts=""` output naming all five inheritance cases as passed, including the two cases asserting the prefix strings `aw specs set:` and `aw set:` by name, and case (e) asserting exit code 0 with no gate written.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted diff of the `CHANGELOG.md` hunk; a grep over it for em and en dashes returning nothing; and a statement that it describes ONLY the corrected message attribution, with the two deduplications absent from it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It is the Set's one child that is NOT gated on spec `wy9aru`'s open questions, because it
changes no dispatch route and no gate; it may therefore be reviewed, approved and executed while OQ-1
awaits the maintainer.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never
`--no-verify`, and never push. Paste ACTUAL runner output for every test claim; a claim of success
without pasted output is a contract violation regardless of whether the tests passed. Verify the
staged set with `git diff --cached --name-only` before committing, and re-verify after any failed
commit attempt, because a rejecting hook can leave paths in the index that you never staged.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Do not set the backlog item `fcnz1r` to any status: it has five
carriers in this Set and the orchestrator `63zo2f` owns its disposition.
