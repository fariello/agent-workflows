# Review: Prune aged workflow-artifacts run dirs with a dry-run-by-default archive route

- Subject-Id: muza7y
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) before review,
and `--phase review-finalize` reported `clean`, exit 0 after the revisions (one `IPD-Z602` prose-density
advisory remains on E-10, which pairs CLI tests with the bare suite, a pairing this repository's plans
use routinely).

THE AUTHOR'S MECHANICAL CLAIMS ALL HOLD, and I re-derived each rather than trusting the table. The
misroute reproduces verbatim: `aw archive workflow-artifacts` prints "no research doc or set matches
'workflow-artifacts'" and exits 0, and `artifact_types.normalize_type("workflow-artifacts")` raises
`ValueError: unknown artifact type`, exactly the fall-through F-6 describes. The readers in F-3 are real
and behave as stated (`run_cli._run_decisions` and `_run_questions` each return 2 on a missing
projection; `set_records.promote_local_checkpoints` reads the same dir to promote unflushed state "so a
crash never loses a recorded decision"). The house pattern in the conventions section is accurate. The
retention arithmetic in OQ-02 is correct: I recomputed it against the measured `assess-documentation`
shape (6 runs, all older than 30 days) and exactly ONE run is planned for deletion, the oldest at index
5, because the AND rule keeps the newest five regardless of age.

THE DOMINANT FINDING IS PR-701, AND IT IS THAT THE PLAN'S ONLY SAFETY RULE CANNOT FIRE ON ANY RUN THAT
ACTUALLY EXISTS. E-02 keys on `set_records.OPEN_QUESTIONS_FILE` existing without the empty marker. But the
plan's own F-5 measured 10 `decisions.md` and ZERO `open-questions.md`, and that asymmetry is IMPOSSIBLE
for the writer E-02 assumes: `set_records.write_local_projections` writes `decisions.md`,
`open-questions.md` and `deferred-work.md` in a single call, which I verified by calling it with zero
records and getting all three files, the questions file holding `_No unresolved questions._`. So a second
producer exists, and it is the `assess` workflow, which hand-authors `decisions.md` and whose own artifact
table says that file holds "Key decisions and assumptions, ... and any open questions for the user" - in
PROSE, with no `open-questions.md` written at all. I built that shape and confirmed the consequence
directly: the run dir contains `decisions.md` and `report.md`, `open-questions.md` does not exist, E-02's
predicate is false, and the run is eligible for deletion despite carrying unresolved questions. The plan
therefore shipped a reader-safety rule that protects nothing in the population it measured, while reading
as though the hazard were covered.

THE SECOND MATERIAL FINDING IS PR-702, and it is the one I would most want the maintainer to see, because
it is about what is LOST rather than about a rule not firing. The plan's F-5 infers that deleting an aged
`decisions.md` "loses no durable record", citing backlog `zzsaq2` and `revgate c621h9`. That inference is
sound for the `set_records` DECISION REGISTER, whose durable copy is the tracked review artifact - and the
backlog item says exactly that, scoping its claim to "set_records.py:143-158 writes the autonomous-decisions
register". It does not transfer to an `assess` run record. `assess.md` states the workflow "**does** write
two durable outputs: the IPD ... and a run record", and for a run that proposed no IPD it documents a
closing report reading "Created: none." - in which case the run record is the ONLY output that run
produced. Deleting it destroys the sole evidence of an assessment. The same class of problem applies to
`release-review`, whose protocol calls `.aw/workflow-artifacts/release-review/<RUN_ID>/` "the authoritative
run record" and, for fresh-context phases, "the authoritative state", and labels two of its registers
"Durable register". An aborted-pre-flight or mid-audit run is live resumable state, and nothing in the
plan distinguished it from finished scratch.

I want to be fair to the author here: the plan is unusually well-evidenced, it identified the reader
hazard as the central risk and built the AND rule, the mtime trap (F-2) and the confinement check
specifically to address it. The gap is narrow and specific - it keyed the safety rule on one projection
shape and then measured a tree containing only the other.

TWO SMALLER CORRECTNESS ITEMS I found only by running things. PR-703: `Path.is_dir()` returns True for a
symlink pointing at a directory (measured on a temp tree: `is_dir=True is_symlink=True`), so E-03's
`is_symlink` half is load-bearing rather than defensive - an `is_dir`-only check would follow the link and
`rmtree` a target outside the root. The plan said "not a symlink" but did not say why, and a later reader
trimming a redundant-looking check is exactly how that protection disappears. PR-704: `args.age` defaults
to `None`, not to a number, and `duration.parse_age_duration`'s own default is `14.0`, so a route that
forgets to pass `default_days=30` silently gets a 14-day window - twice as aggressive as the plan's stated
conservative default, on a permanent delete.

PR-705 is a flag-documentation mismatch the plan would have inherited. `--keep` is already
`action="append"`, so the plan's plural "pin run ids" works unchanged (good), but its help text reads "In a
sweep, send this `<id6>` to reference instead of archive", which describes the research-specific MOVE and is
simply false for a route that deletes. Leaving it would ship a flag whose documentation contradicts its
behavior on one of its two routes.

PR-706 concerns what the operator can SEE. The plan's preview names each deletion candidate but folds the
kept runs into a bare count. For a route whose entire safety story is the keep rules, a silently-kept run is
indistinguishable from a keep rule that never ran - which is precisely the failure PR-701 found. Naming each
reader-safety keep with its reason turns the guard into something an operator can verify at the moment it
matters.

PR-707 is right-sizing. The original E-06 bundled a nine-assertion planner fixture, the CLI tests, and the
bare suite into one item; the original E-04 bundled parser wiring, flag declaration, output formatting and
the commit decision. Both are split, and the plan is now ten items against six, still one concern.

PR-708 is a baseline finding the plan carried into review: `aw check plans` reported
`check.ipd-uncarried-obligation` at `error` severity for its two open questions. Both were answerable from
the repository - OQ-01 from the shipped `archive` declaration and the parser-leaf measurement, OQ-02 from
re-deriving the author's own arithmetic - so leaving them open was holding the plan for decisions the tree
already settled, and the same predicate gates `pre-transition`.

ONE THING I CHECKED AND FOUND FINE, recorded so it is not re-litigated: the plan adds no parser leaf.
`discover_parser_leaves` reports `archive` as a single leaf and `find_undeclared_leaves` does not list it,
so the positional value needs no new declaration, completion row or conformance row - which is the strongest
argument for OQ-01's resolution. The `archive` declaration's `exit_contract` is `(0, 2)`, which the plan
never mentioned; E-10 now asserts the route stays inside it, since a skipped-unsafe path is the obvious
place a bare exit 1 would creep in.

`aw check reviews` conforms and `evaluate_durable_carrier` returns zero findings for this plan after the
revisions. Backlog `zzsaq2` is `graduated`, `Work-Kind: chore`, and carries no `- Blocks-Release:`, so the
every-live-bug-gates-the-release rule does not apply and no gate handoff is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | BLOCKER | IN-SCOPE | A. Correctness and data integrity | Measured: `set_records.write_local_projections(td, wf, rid, [])` created `decisions.md`, `deferred-work.md` AND `open-questions.md` (the last holding `_No unresolved questions._`); plan's own F-5 measured 10 `decisions.md` and 0 `open-questions.md`; `.aw/system/workflows/assess/assess.md` artifact table lists `report.md`, `findings.csv`, `decisions.md`, `evidence.md`, `ipd-link.md` and NO `open-questions.md`; a synthesized assess run reproduced E-02's predicate returning false | THE ONLY READER-SAFETY RULE CANNOT FIRE ON ANY RUN IN THE MEASURED TREE. E-02 keys on `open-questions.md` existing, which is written ONLY by `set_records.write_local_projections` - and that function writes all three projections together, so its runs can never produce the 10-decisions-zero-questions asymmetry F-5 measured. That asymmetry proves a different producer: the `assess` workflow, which hand-authors `decisions.md` holding "any open questions for the user" in PROSE and writes no questions file. So every run that actually exists in the tree is eligible for deletion regardless of unresolved questions, while the plan reads as though the hazard were handled. This is the plan's central safety claim and the deletion is permanent on a gitignored tree. | C:Medium; U:Low; S:Low; F:High; Overall:Medium (two added rules keyed on artifacts the workflows demonstrably write; no prose parsing) | FIXED | Corrected F-5 into F-5/F-5a/F-5b with the measurements. E-02 now states its reach explicitly and why E-03 must exist. Added E-03 keying on the `assess` shape (a `decisions.md` with no `open-questions.md` is kept as `unreviewed-decisions` unless `ipd-link.md` resolves to an existing IPD), with an explicit prohibition on parsing `decisions.md` prose, since a false negative there deletes a record. V-03 requires the keep test AND its fail-without-fix, and names this as the plan's most important evidence. |
| PR-702 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression | `.aw/system/workflows/assess/assess.md`: "It **does** write two durable outputs: the IPD ... and a run record", and the no-IPD closing report "Created: none."; `release-review/00-run-protocol.md`: "`.aw/workflow-artifacts/release-review/<RUN_ID>/` is the authoritative run record", "the authoritative state" for fresh-context phases, and `03-findings-register.csv`/`04-action-register.csv` labelled "Durable register"; backlog `zzsaq2` scopes its durability claim to "set_records.py:143-158 writes the autonomous-decisions register" | THE "DISPOSABLE SCRATCH" PREMISE IS NOT UNIFORMLY TRUE, AND THE PLAN'S DURABILITY INFERENCE OVER-GENERALIZES ITS SOURCE. F-5 argues deletion loses no durable record, citing `revgate c621h9` - sound for the `set_records` decision register, whose durable copy is the tracked review artifact, and which is exactly what the backlog item scoped the claim to. It does not transfer. For an `assess` run that proposed no IPD, the run record is the ONLY output that run produced, so deleting it destroys the sole evidence of the assessment. For `release-review`, an aborted-pre-flight or mid-audit run is live RESUMABLE state that its own protocol calls authoritative, and nothing in the plan distinguished it from a finished run. Worst case: the operator runs `--apply` and loses an assessment that was never written anywhere else, unrecoverably, because the tree is gitignored. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added F-5c quoting both workflows. Added E-04 with two cases and distinct reasons: `unfinished-run` for a `release-review` run lacking positive completion evidence, and `sole-durable-output` for an `assess` run whose `ipd-link.md` is absent or records no IPD. E-04 requires the executor to state which completion artifact it keyed on and why, since that choice IS the safety. V-04 requires both keeps plus both fail-without-fix runs and the quoted protocol sentence. E-08 additionally requires reconciling the README's existing "treat its contents as disposable" sentence, which is the sentence that makes this deletion look safe. |
| PR-703 | MEDIUM | IN-SCOPE | B. Security / A. Correctness | Measured on a temp tree: a symlinked run dir reported `is_dir=True is_symlink=True`; depth-1 `README.md` correctly skipped as a non-dir | THE CONFINEMENT CHECK'S LOAD-BEARING HALF LOOKS REDUNDANT AND IS NOT. `Path.is_dir()` follows symlinks, so it is True for a link pointing at a directory; only the `is_symlink` test distinguishes a real run dir from a link out of the tree, and without it `shutil.rmtree` would delete the TARGET, outside the artifacts root. The original E-03 said "not a symlink" without saying why, which is how a later reader trims an apparently-redundant check and silently removes the one protection keeping deletion inside the root. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | E-05 now states the measurement and that the `is_symlink` half is load-bearing, and requires `ignore_errors=False` so a partial delete is reported rather than swallowed. V-05 requires the symlink-confinement test to pass AND to FAIL with the `is_symlink` half removed, with the target's sentinel file as the observable. |
| PR-704 | MEDIUM | IN-SCOPE | A. Correctness | Measured: parsing `archive workflow-artifacts` yields `args.age is None`; `duration.parse_age_duration` signature is `(val, default_days: float = 14.0)` | THE ROUTE'S STATED 30-DAY DEFAULT SILENTLY BECOMES 14 IF WRITTEN THE OBVIOUS WAY. `--age` has no argparse default, so the route receives `None` and must pass `default_days=30` itself; calling `parse_age_duration(args.age)` inherits the parser's `14.0`. The result is a window twice as aggressive as the plan's deliberately conservative default, on a permanent delete, and nothing in the plan's tests as originally written would have caught it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now names the exact call form with the measurement, and states explicitly not to rely on the parser default. V-06 requires a test asserting the effective default is 30 days when `--age` is absent. |
| PR-705 | LOW | IN-SCOPE | F. Honest documentation | `cli.py` `--keep` is `action="append"` (so the plan's plural pinning works); its help reads "In a sweep, send this `<id6>` to reference instead of archive" | A REUSED FLAG'S DOCUMENTATION WOULD BE FALSE ON THE NEW ROUTE. `--keep`'s help describes the research-specific behavior of MOVING a doc to `reference/` instead of archiving it. On a route that deletes, "send to reference" names something that does not happen; the flag pins a run id against deletion. Shipping it unchanged leaves one flag whose help contradicts its behavior depending on which route you are on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 requires widening the `--keep` help to cover both meanings, and records that `action="append"` already supports repetition so no behavior change is needed. V-06 requires the widened text be pasted. |
| PR-706 | MEDIUM | UNDER-SCOPE | F. Prevent silent failure / UX | Original E-04 preview spec: per-deletion lines "plus the kept count"; the four keep reasons are the plan's entire safety story | A SILENTLY-KEPT RUN IS INDISTINGUISHABLE FROM A KEEP RULE THAT NEVER RAN. The preview names every deletion candidate but reduces the keeps to a number, so the operator has no way to confirm at the decision point that a reader-safety rule actually fired on the run it was meant to protect. Given PR-701 found exactly that failure - a rule that could not fire on anything real - a bare count is the wrong output for this route: it hides the one signal that would have revealed the defect. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split output into its own item, E-07, requiring every reader-safety keep to be NAMED with its reason (`open-questions`, `unreviewed-decisions`, `unfinished-run`, `sole-durable-output`, `pinned`) alongside the deletion candidates, the kept count, reclaimable bytes and the `--apply` hint. V-07 requires a preview containing at least one of each. |
| PR-707 | MEDIUM | UNDER-SCOPE | G. Plan executability (right-sizing) | Original E-06 bundled a 9-assertion planner fixture + CLI tests + the bare suite; original E-04 bundled parser routing + flag declaration + output format + the commit decision; `aw ipd lint` passed on count | TWO ITEMS BUNDLED INDEPENDENT DELIVERABLES AND TEST-SURFACES, which the count-based size lint cannot see. E-06 in particular was a whole test suite plus a suite run in one checkbox, meaning a single `Execution state: performed` mark would cover nine unrelated assertions and the bare run - and its `V-06` asked only for "N passed" plus the suite line, so most of those assertions had no named evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low (decomposition only) | FIXED | Split into 10 items: E-02/E-03/E-04 (three safety rules), E-05 (deleter), E-06 (routing and flags), E-07 (output), E-08 (README), E-09 (planner/deleter tests with per-rule falsification), E-10 (CLI tests, exit contract, bare suite). 10:10 E/V bijection; `Highest E allocated` corrected 06 -> 10 (an `IPD-I304` error once the items were added). Cohesion rationale rewritten. |
| PR-708 | LOW | IN-SCOPE | A. Correctness / D. Anti-regression | `evaluate_durable_carrier` at review: `2 obligation(s) name no durable carrier: OQ-01 ... OQ-02 ...`, severity `error`; `check_engine.evaluate_durable_carrier`; `ipd_schema.DEFERRED_SUBFIELD_RE` accepts only an indented `- Carrier:`/`- Carrier-Evidence:`/`- Carrier-Declined:` | THE PLAN ENTERED REVIEW CARRYING AN ERROR-SEVERITY FINDING from two uncarried open questions, and the same predicate gates `aw ipd lint --phase pre-transition`, so it would have blocked execution later. Both questions were answerable from the repository - OQ-01 from the shipped `archive` declaration and the parser-leaf measurement, OQ-02 by re-deriving the author's own arithmetic - so leaving them open also held the plan for decisions the tree had already settled. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved both from evidence with `Status: resolved`, `Owner: none`, and a `Carrier-Declined` reason each; OQ-01's resolution records the residual move-versus-delete cost and the mitigations (E-07's wording, E-08's permanence note) rather than dismissing it. `evaluate_durable_carrier` now returns 0 findings for this plan. Recorded as D-1 and D-2. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should deletion live under `aw archive` or a new `aw prune` verb? | `aw archive workflow-artifacts`, with the delete-versus-move difference mitigated in output and docs rather than left implicit. | (a) A dedicated `aw prune` verb - rejected on measurement: `archive` already carries `mutation_gate="dry_run_default"`, `legacy_flags=("--keep","--apply")` and `exit_contract=(0,2)`, and `discover_parser_leaves` reports `archive` as ONE leaf not listed by `find_undeclared_leaves`, so the positional value needs no declaration, completion or conformance row, while a new verb needs all four for one untracked tree. (b) Ask the maintainer - rejected: the declaration and leaf facts answer it, and the question was also an error-severity uncarried obligation. (c) Put it under `archive` and say nothing about the semantic difference - rejected: `archive` MOVES records and this DELETES them permanently on a gitignored tree, so the difference must be visible at the point of use. | Measured `get_declaration('archive')` fields; `discover_parser_leaves`/`find_undeclared_leaves` output; plan Deferred row already records the new-verb alternative and its trigger | yes |
| D-2 | OQ-02: are `--keep-last 5` and `--age 30d` the right defaults? | Yes, kept as authored. | (a) A shorter window to reclaim more - rejected: the bias for a permanent delete on an untracked tree should be to under-delete, and the measured payoff is 972K, so aggressiveness buys almost nothing against real risk. (b) Leave open for the maintainer - rejected: re-derivation confirms the author's own figure, and both values are flags. | Recomputed the AND rule against the measured `assess-documentation` shape (6 runs, all >30d): exactly one run at index 5 is planned for deletion, every other kept by the newest-5 window | yes |
| D-3 | The `assess` `decisions.md` carries open questions in prose. How does the planner detect "still has unresolved questions" without parsing prose? | Do NOT parse prose. Key on a POSITIVE completion artifact instead: `ipd-link.md` resolving to an existing IPD means the run handed its durable output off and is prunable; its absence means keep. | (a) Grep `decisions.md` for question-like text ("?", "open question", "UNANSWERED") - rejected: unbounded natural language, and a false negative DELETES a record; the backlog item itself warns that a naive discriminator gets a guard disabled as noisy. (b) Keep every `assess` run forever - rejected: it would make the verb useless on the only population that exists, since assess runs are the whole measured tree. (c) Require the operator to pin each one with `--keep` - rejected: it moves the safety burden onto the person least able to know, and defaults to destruction. | `.aw/system/workflows/assess/assess.md` artifact table (`ipd-link.md` = "The path to the IPD this run wrote"); backlog `zzsaq2` "a naive grep-style guard ... needs a real discriminator or it will be disabled as noisy" | yes |
| D-4 | `release-review` runs need a completion test. Should the review pick the exact artifact, or leave it to the executor? | Leave the exact artifact to the executor, but REQUIRE it to be derived from the protocol's required-artifact list and justified in a comment and in V-04's evidence. | (a) Pin it here to `08-checkpoints.md` plus a terminal status in `00-run-metadata.md` - offered in E-04 as the suggested shape but not mandated, because I did not measure a real completed release-review run (none exists in this lane) and pinning an untested discriminator would be exactly the kind of authoring-time assertion that rots. (b) Say "keep all release-review runs" - rejected: it silently exempts the workflow with the largest run records, defeating the verb's purpose. | `release-review/00-run-protocol.md` required-artifacts table; the run dir is called "the authoritative run record" and "the authoritative state", so the discriminator carries real safety weight and must be justified rather than guessed | yes |

## Round 1 escalation

No finding was left `OPEN` or `DEFERRED` - all eight are `FIXED` - so no `- Blocking: yes` question was
owed under Step 4's escalation rule, and `evaluate_review_finding_escalation` returns zero findings. No
decision is recorded `Reversible: no`: each of D-1 through D-4 is undoable by editing the plan or the new
module before anything ships, and none publishes an interface, migrates data, or deletes anything.

WORTH THE MAINTAINER'S ATTENTION ANYWAY, despite nothing being formally escalated. PR-701 and PR-702 are a
BLOCKER and a HIGH whose subject is irreversible data loss, and the fix is a set of DISCRIMINATORS that
this review specified but could not fully measure: no completed `release-review` run and no live
artifacts tree exist in this lane, so D-4's completion test is a justified proposal rather than a verified
one. If the maintainer knows of a run shape these rules would misclassify, that is worth saying before
approval, because the cost of a wrong keep is wasted disk and the cost of a wrong delete is an assessment
record that existed nowhere else.
