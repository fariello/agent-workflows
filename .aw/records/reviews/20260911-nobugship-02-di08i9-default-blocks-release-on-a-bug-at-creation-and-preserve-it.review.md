# Review: default Blocks-Release on a bug at creation and preserve it through graduation, child di08i9 (Set nobugship)

- Subject-Id: di08i9
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `165e35e8`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(clean, exit 0, 0 findings) before semantic review, and `--phase review-finalize` conformed again after
every revision below.

SELF-REVIEW DISCLOSURE: this Set was authored in the same repository by the same model family, so treat
this as a near-self-review worth less than an independent one. Its value rests on what was EXECUTED
rather than on the reading, which is why the blocker below is an implementation measurement and not an
argument.

SCOPE OF THE LEDGER. The invocation named this child only, so the ledger is that one plan. The
orchestrator `qmgn12` and siblings `zqs0px` / `rgaasb` were read as EVIDENCE and NOT edited, matching how
this repository reviews a Set (each member carries its own record). Two findings below concern child 03
and are recorded as things this plan must HAND to it, not as edits to it.

SHARED CHECKOUT NOTE. Another party was editing this checkout during the review: a backlog item
(`o9inwt`) moved `open` -> `done` in the working tree, uncommitted and not mine. It was left untouched and
is not part of this review's commit. That is also why the plan now carries an explicit index-reverification
clause in its gate.

THE PLAN'S THESIS IS CORRECT AND ITS SHAPE WAS NOT CHANGED. Defaulting at creation plus preserving at
graduation is the right two-part answer, and the underlying defect reproduces exactly: `run_new` reads
`--blocks-release` and applies nothing when it is absent (`backlog.py:388-397`), and the graduation leak
recomputes identically to the authored claim (11 of 11 graduated gateless bugs have a `From-Backlog`
carrier, 13 carriers in total, 0 of 13 gated). Every E-item survived; four were rewritten and none was
removed.

THE BLOCKER WAS FOUND BY IMPLEMENTING THE PLAN, NOT BY READING IT. E-01 instructed the executor to REFUSE
when `next` does not resolve. Patched into `backlog.run_new` exactly as written, in a throwaway copy of
the repository, that produced `10 failed, 77 passed` across `tests/test_backlog.py`,
`tests/test_backlog_work_kind_rename.py`, `tests/test_backlog_blocking_close_gate.py` and
`tests/test_release_gate_close.py`, every failure being a fixture that creates no release record. The
cause is not the fixtures. Driven on an empty repo, `aw install` creates NO `.aw/records/releases/`
directory at all, and `resolve_release` returns None when the directory is absent
(`releases.py:138-141`), so `--blocks-release next` exits 2 there. A refusal would therefore make
`aw backlog new --work-kind bug` FAIL OUTRIGHT in every freshly installed adopter repo. Re-patched to
fall back to ungated on an ABSENT flag while preserving the refusal for an EXPLICIT unresolvable value,
the bare suite passed `5971 passed, 3 skipped, 2 xfailed in 58.71s`.

THE SECOND MEASURED COLLISION IS THAT THE DEFAULT MANUFACTURES AN ITEM THE SHIPPED CHECKER REJECTS.
`aw backlog new --work-kind bug --status done` is legal, and with the default applied it writes a `done`
item carrying `Blocks-Release: next` with no handoff and no evidence. Driven through the CLI in a scratch
repo with the patched code and then staged, `check_engine.check_release_gate_consistency` returned exactly
one `check.blocking-item-closed-without-gate`, which is registered at `error` under `I-07`
(`check_engine.py:105-107`) and sits in the exit-blocking sweep. The setter is not the hole: driven on a
gated item, `aw backlog set <path> --status done` REFUSED with exit 1 and the three documented fixes.
Creation would have been the only route that creates the violation child 03 exists to eliminate.

THE GRADUATION HALF IS NARROWER THAN THE PLAN CLAIMED, and this was settled by provenance rather than by
argument. Of the 13 existing `From-Backlog` carriers, 12 carry the field in the FILE'S FIRST COMMIT, so
they were hand-authored at scaffold time with no setter involved; exactly 1 gained it later.
`aw ipd scaffold` accepts no `--from-backlog` flag at all (its options are
`--kind --title --path --set --order --legacy-name --author --apply --overwrite`), and `--from-backlog` is
registered on exactly one parser, `p_ipd_set` (`cli.py:1292-1297`), so `aw specs set` has no route even
though a spec is an accepted carrier. E-03 still earns its place because it strictly reduces FUTURE
mismatch, but its framing as closing the leak was inflated.

ONE PROVENANCE CLAIM COULD NOT BE VERIFIED AND IS NOW MARKED AS SUCH. The plan attributes its figures to
HEAD `2ff2b1b1`; `git cat-file -t 2ff2b1b1` reports "Not a valid object name" in this repository, so that
anchor is unresolvable and every count was re-derived from disk instead: 196 items, 112 `Work-Kind: bug`,
68 live, 22 gateless (10 `open`, 11 `graduated`, 1 `blocked`) against the authored 187/103/60/32/28.

TEN THINGS WERE DRIVEN RATHER THAN RECALLED: the five population counts recomputed from disk; the
graduation leak and its 13 carriers recomputed with `check_engine.find_from_backlog_artifacts`; those
carriers' git provenance traced to their first commit; `resolve_release(repo, 'next')` confirmed to return
`f33nrj` (2.0.0); a fresh `aw install` inspected for a releases directory; the prescribed refusal patched
in and the affected tests run; the corrected fallback patched in and the BARE suite run; the `done`
collision driven through the CLI and fed to the shipped checker; the setter's refusal on a gated close
driven to exit 1; and `aw backlog set --help`, `aw ipd scaffold --help` and `aw specs set --help` each
invoked to establish the route inventory.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Rubric A/C (correctness, operability) | `backlog.py:388-397`; `releases.py:138-141` | E-01 instructs a REFUSAL when `next` does not resolve. Implemented as written in a throwaway copy, that produced `10 failed, 77 passed` across four existing test files, and a fresh `aw install` creates no releases directory at all, so the verb would refuse in every newly installed adopter repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 rewritten: check resolution as a PREDICATE and fall back to ungated with a notice on an ABSENT flag, while still refusing an EXPLICIT unresolvable value. Corrected patch measured `5971 passed, 3 skipped, 2 xfailed`. V-01 cases 4 and 5 pin both halves. |
| PR-002 | HIGH | IN-SCOPE | Rubric A/D (correctness, invariants) | `check_engine.py:105-107`, `:2170-2199` | The default applied to `aw backlog new --status done --work-kind bug` writes a `done` item carrying a gate with no handoff, which the shipped `check.blocking-item-closed-without-gate` ERROR rule flags. Driven through the CLI and the checker: exactly one finding. The setter refuses this transition (exit 1); creation did not. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now skips the default for `done` (and `parked`) and reports the skip; V-01 requires the created item to be fed to `check_release_gate_consistency` with zero findings; E-04 case 9 pins it. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric F (prevent silent failure) | `backlog.py:414-462` | OQ-01 resolved to ANNOUNCE the default, but `run_new`'s `--agent`/`--json` branch emits a `CommandResult` and returns before the human `sys.stdout.write`, so a notice on the human surface alone is invisible to a runner, which is the most likely caller. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the fact to be carried in the structured result as well as the human line; E-04 case 3 and V-01 case 2 require the JSONL record to be pasted. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability, honest scope) | `cli.py:1292-1297`; git provenance of the 13 carriers | E-03 was framed as making the graduation inheritance real, but 12 of 13 existing carriers were hand-authored in the file's first commit, `aw ipd scaffold` has no `--from-backlog` flag, and `aw specs set` has none either. The setter route covers at most 1 of 13 historically. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 rewritten to claim only the setter route, to require the measured route inventory as its deliverable, and to name the hand-authoring and spec-setter routes as uncovered and handed to child 03. Both added to Deferred with reasons. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric E (testing) | measured blast radius (four test files) | E-04's case list omitted the two cases that actually matter: the absent-flag-with-no-release case whose refusal broke 10 tests, and the explicit-unresolvable case that must NOT change. It also did not require the four already-affected existing test files to be run. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now enumerates ten cases including both, labels case 8 a REGRESSION GUARD exempt from falsification, and requires the four blast-radius files to be run and pasted with an explicit prohibition on "fixing" their fixtures. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric G (dependencies, sequencing) | `b5sfwm` front matter; `aw backlog set --help` | E-02 treated the `b5sfwm` deferral as a fallback, when it is the expected outcome: that plan is `reviewed`/`go-pending-approval` in `pending/`, and `aw backlog set --help` lists no `--work-kind`, so no reclassification can arrive at all. The plan also did not warn that the verb has TWO dispatch paths, so a later default could fire on one spelling only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewritten: the recorded deferral IS the deliverable, with the measured evidence named, an explicit prohibition on duplicating `b5sfwm`'s scope here, and the two-dispatch-path requirement (`cli.py:11270-11286`) handed to whoever lands it. V-02 requires the `--help` output as proof. |
| PR-007 | MEDIUM | UNDER-SCOPE | Rubric E (validation), project test contract | plan's "Required tests" section | The plan required only a bare-suite baseline with "no figure stated deliberately", giving the executor no checker baseline and no fast signal, although this child's specific hazard is a shipped ERROR rule rather than pytest. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The section now adds the four-file blast-radius checkpoint (with the measured `10 failed` / `87 passed` contrast), a `check_release_gate_consistency` baseline, and the bare-run guidance against adding `-n0`/`-q`. |
| PR-008 | MEDIUM | UNDER-SCOPE | Project execution contract, shared checkout | `AGENTS.md:63`; observed working-tree state | The gate lacked the lifecycle move, the finalize scope-justification mechanics, and any shared-checkout index reverification, the last being live rather than theoretical during this review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the path-scoped/never-push rule, the `--scope-reason`/`--scope-ack` finalize mechanics, the terminal lifecycle move, the index reverification clause, and the three measured hazards. |
| PR-009 | LOW | IN-SCOPE | Evidence integrity | `git cat-file -t 2ff2b1b1` | Every authored figure is attributed to a commit that does not exist in this repository, so the plan's provenance anchor is unresolvable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The authored history line now records that the anchor could not be verified and that the figures were re-derived; the Concern carries the re-measured counts with a resolvable HEAD. |
| PR-010 | LOW | IN-SCOPE | Rubric G (scope declaration) | `command_surface.py:1170-1195` | `backlog new`'s declared flag set lives in `command_surface.py`, which is not in `- Scope-Paths:`. E-01 adds no new flag so it should not need editing, but the plan did not say so, leaving an undeclared-edit trap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check now states that no declaration change is expected and that touching the file requires either a prior `- Scope-Paths:` addition or a finalize `--scope-reason`. Also records that no CLI help change is mandated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | When `next` does not resolve and no gate flag was passed, should the tool refuse (as the plan said) or fall back to ungated? | FALL BACK to ungated and say so, while still refusing an EXPLICIT unresolvable value. | Refuse, as authored (rejected: measured 10 test failures, and a fresh `aw install` has no releases directory, so the verb would break in every new adopter repo). Refuse only when a releases directory EXISTS but has no planned release (rejected: still refuses on a repo whose release is `shipped` rather than `planned`, for no gain, and adds a third state to reason about). | The maintainer's 2026-09-10 ruling on plan `y4adch` OQ-01: fall back to the default AND warn, with fail-closed "declined on blast radius" for a shared tracked-state case while a per-invocation mistake still refuses; plus the measured suite failures and `releases.py:138-141`. | yes |
| D-2 | Should the default apply when `--status done` is passed at creation? | NO, skip it (and skip `parked`), reporting the skip. | Apply it anyway (rejected: measured, it produces a `check.blocking-item-closed-without-gate` ERROR from the shipped exit-blocking sweep, so the tool would create the violation child 03 exists to remove). Apply it and let child 03's backfill clean up (rejected: the item is born already-invalid, and the setter refuses the same transition, so creation would be an inconsistent second door). | `check_engine.py:105-107` and `:2170-2199`; the driven CLI-plus-checker experiment; the setter's exit-1 refusal on the same case. | yes |
| D-3 | Does E-03 close the graduation leak, as the plan framed it? | NO. It covers the setter route only; the hand-authoring route and the spec-setter gap are recorded as uncovered and handed to child 03. | Widen this child to add `--from-backlog` to `aw specs set` and gate inference to `aw ipd scaffold` (rejected: a new CLI surface on two other verbs, outside this child's declared paths and its concern, and a scaffolder that reads the backlog tree is a larger design decision). Leave the framing as authored (rejected: it would report the leak closed while 12 of 13 measured carriers remain uncovered, which is the false-confidence failure the plan itself warns about). | Git provenance of the 13 carriers (12 present in the first commit); `aw ipd scaffold --help` and `aw specs set --help` flag sets; `cli.py:1292-1297`. | yes |
| D-4 | Is E-02's deferral to `b5sfwm` acceptable, or must this child implement the reclassification default itself? | ACCEPT the deferral and make the recorded statement the deliverable. | Implement a work-kind setter here so the default has somewhere to attach (rejected: it duplicates `b5sfwm`'s entire reviewed scope and would land the change in a second place from the one that plan is reviewed to change). | `b5sfwm` front matter (`reviewed`, `go-pending-approval`, in `pending/`); `aw backlog set --help` showing no `--work-kind`; `cli.py:11270-11286` for the two-path hazard. | yes |
