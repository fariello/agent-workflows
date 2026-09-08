# Review: agent-friendly aw runs analyze and query interface (child mm5p3v, Set runanalytics)

- Subject-Id: mm5p3v
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `3ec92ca4`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic review
(exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the eight-item split and the rewritten
V-item bijection.

METHOD. This plan touches the most heavily gated surface in the repository, so it was reviewed by EXERCISING that
surface: building the real parser and calling `discover_parser_leaves` and `find_undeclared_leaves` against it,
importing `agent_schema` to read the actual envelope constants, running the commands the plan promises to test,
and calling `resolve_target_runs` directly for each proposed leaf name. Four of the five HIGH findings came out of
those runs rather than out of reading, and the most consequential one is that the plan's declared file list could
not have shipped its own feature.

WHAT THE PLAN GETS RIGHT, and it is the hardest judgement in a query interface. Excluding arbitrary SQL,
expression evaluation, filesystem paths outside the resolved roots and unrestricted field projection is exactly
the right posture: an allowlisted filter and grouping schema is the only version of this feature that stays safe
as it grows, and the plan chose it unprompted. Refusing dynamic aliases and config-manufactured leaves is equally
right and is the failure mode that would have been tempting. Insisting `--open` be an explicit side effect, and
that analysis without it never launch anything, is correct and is stated as an invariant rather than a default.
And keeping the `--` escape contract rather than quietly breaking it shows the author read the routing code.

THE ROOT FINDING IS THAT REGISTERING A LEAF IS A THREE-FILE CONTRACT AND THE PLAN DECLARED ONE OF THEM. Measured:
`command_surface.COMMAND_INVENTORY` holds 129 declarations; `discover_parser_leaves` on the real parser reports
124 leaves; and `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves` asserts
`find_undeclared_leaves` is EMPTY. So a new parser leaf without a `CommandDeclaration` fails a NAMED fail-closed
CI job that runs across Python 3.9 through 3.14. The authored `Scope-Paths` listed neither `command_surface.py`
nor that test file, so an executor would have registered two leaves, watched CI fail, and had no in-scope file in
which to fix it. The compounding detail is what makes this worth its own item: that test file carries
`pytestmark = pytest.mark.slow` and `pyproject.toml` `addopts` supplies `-m 'not slow'`, so the BARE suite the
plan requires as its validation DESELECTS the only gate that would have caught the omission. The plan's own
validation would have reported green.

A SECOND MEASUREMENT MAKES THAT FINDING SHARPER. `find_undeclared_leaves` returns exactly five entries today
(`oc profile add`, `default`, `list`, `remove`, `show`), which is a live pre-existing failure of that assertion.
That baseline matters in both directions: without it an executor might "fix" five unrelated declarations while
believing it is doing this plan's work, or might see the test already red and conclude its own new leaf is fine.
The plan now pins the baseline set.

THE DIRECTION VIOLATION IS REAL AND WAS UNSTATED. `aw runs` is documented in code as "the READING half of the run
surface" and its description says "Read-only, with ONE exception: the `repair` verb". `analyze` updates a cache
and publishes a report bundle, so it is the SECOND exception. This is defensible, and I did not treat it as a
reason to move the command, because `aw run` is the ledger-transaction noun (`start`/`record`/`cancel`/`finalize`)
where an analytics build genuinely does not belong. But it has two mechanical consequences the plan missed:
`command_class` must be `mutation`, which changes the required scenario set that
`tests/conformance_matrix.required_scenarios` computes (`success_preview` rather than `domain_failure`), and the
noun's own help text becomes FALSE the moment the leaf lands.

THE COLLISION TEST WOULD HAVE PASSED BEFORE ANY CODE WAS WRITTEN, AND WOULD HAVE WALKED PAST A REAL BUG. This is
the finding I am most glad was measured rather than reasoned about. The plan promises to assert that
`aw runs -- analyze` resolves `analyze` as a viewer target. Run today, that command prints `no matching runs
found` and exits 0, and `resolve_target_runs(['analyze'])` returns 0 runs. So the assertion is vacuous. Then
`aw runs -- status`, the escape the help itself documents, turns out NOT to resolve a run named `status`: it
returns ALL 135 runs. The cause is that `resolve_target_runs`' final fallback greps the raw `state.json` TEXT for
`"<token>"`, and `status` is a JSON KEY present in every file, so the "setid" fallback matches a key rather than a
value. A test written as authored would have proven nothing, and a test written against the documented example
would have pinned a bug as expected behavior. The plan now requires a purpose-built fixture actually named
`analyze`, and requires the bug be REPORTED rather than depended upon or fixed here.

A RELATED STRUCTURAL POINT WORTH SEPARATING. The `--` escape cannot reach a leaf BY CONSTRUCTION: `_dispatch`
handles it pre-parse, forces `runs_command = None`, and hardcodes `run_viewer.run_viewer_cli`. So one half of the
promised behavior is structurally guaranteed and belongs in a code-level assertion, while the other half ("fixed
leaves win without `--`") is a property of the routing action. They are enforced in different places, and a purely
behavioral test would not distinguish them.

THE AGENT PROTOCOL ALREADY EXISTS, AND ITS BUDGET IS THE REAL DESIGN CONSTRAINT. The plan proposes "a versioned
query protocol". Measured, that protocol is `aw.agent/v1`: `agent_schema.SCHEMA_VERSION`, a closed
`RECORD_KINDS` of four values, a closed `VALID_OUTCOMES` of thirteen, a `validate_agent_record` that enforces
kind-specific mandatory fields plus explicit anti-greenwashing rules, and a `filter_record_fields` that already
implements bounded projection. So there is no room for a second envelope, only for a `data` payload inside this
one. The consequential part is `tests/test_cli_quality_gates.py`, which enforces `BYTE_BUDGET = 1200` and
`TOKEN_BUDGET = 400` PER RECORD. A `distributions` or `slices` view over the corpus Order 06 measured at 29766
fact rows breaches that by construction. Bounded default limits are therefore not ergonomics, they are what makes
the view conformant at all, and that decision belonged in the plan.

ONE MORE RECONCILIATION THE PLAN WOULD HAVE HIT AT TEST TIME. Exit codes are not restricted to 0/1/2 in the
inventory: eight declarations use a higher code (`run start` and `run record` at `(0,2,3,5,6)`, `runs status` at
`(0,1,3,5)`, `run finalize` at `(0,1,4,6)`, and four others). But `validate_agent_record` REQUIRES the record's
`exit` field to be in `(0,1,2)` for a `result`, `summary` or `error` kind. A leaf that emits an agent record
therefore cannot report a higher code inside it, and the plan's "documented exit codes" needed that distinction
stated rather than discovered.

TWO SMALLER GAPS. `--open` is greenfield: a repo-wide search finds no `webbrowser`, no `xdg-open`, no comparable
launch anywhere in the package, so "never launches without `--open`" has no existing seam and inspection is not
proof; it needs an injectable launcher that fails the test if invoked. And the authored test list promises "Help
and README command snippets are executable", for which there is no mechanism at all:
`tests/test_cli_output_docs_rollout.py` asserts that docs DESCRIBE exit codes, accessibility and schema kinds, and
executes no snippet. That claim had to be either implemented or downgraded, not left implied.

ON THE SPEC QUESTION, WHICH I RESOLVED RATHER THAN ESCALATED. The plan says "If the repository maintains a
controlling CLI grammar spec, execution must amend it before registering leaves". It does:
`20260818-1525-01-command-surface-redesign` is `Status: implemented` with a normative Section 3. I resolved this
as NOT an amendment, because that spec governs the noun-verb shape, the closed TYPE-noun set and the seven
cross-cutting verbs, and does not enumerate the existing nine `aw runs` leaves either; treating a conformant
addition as a spec change would make every future leaf one. The one genuine escalation is preserved in the gate:
if a mutating leaf on the reading noun is judged a grammar violation rather than a documented exception, that is
the maintainer's call and a STOP-and-raise.

ON SIZING. Three E-items, with E-03 bundling routing, compatibility, failure semantics, discoverability and help
output across five unrelated test surfaces, and E-02 bundling ten query views with a schema-versioning contract
and an output-format matrix. All ten children of this Set carry exactly three items and the count-based lint
passes at three by construction. This is the eighth sibling split for the same reason (`bzz5e6` 3->6, `lhccjf`
3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9, `6eq3oq` 3->8) and the eighth consecutive gate with no
execution contract.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing needed a human. The class question was settled by
reading the declaration machinery and the noun's own help, the protocol question by importing the schema module,
the collision question by running the commands, and the spec question by reading the spec. All four are recorded
as decisions with rejected alternatives. No BLOCKER and no unfixed HIGH remains.

ONE NOTE FOR THE MAINTAINER, spanning plans rather than belonging to this one. `test_no_undeclared_parser_leaves`
is red today on five `oc profile *` leaves, and because the file is `slow`-marked, nobody running the bare suite
sees it; only the `output-conformance` CI job does. That is worth a separate backlog item independent of this
Set, since the same invisibility is what would have hidden this plan's own omission.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-093 | HIGH | UNDER-SCOPE | G. executability; E. testing (an invisible gate) | called `discover_parser_leaves` (124 leaves) and `find_undeclared_leaves` (five `oc profile *`) on the real parser; read `COMMAND_INVENTORY` (129 declarations), the test's `pytestmark = pytest.mark.slow`, and the `output-conformance` CI job | **A NEW LEAF CANNOT SHIP FROM THE AUTHORED `Scope-Paths`.** Every parser leaf MUST carry a `CommandDeclaration` because `test_no_undeclared_parser_leaves` asserts `find_undeclared_leaves` is empty, and that runs as a named fail-closed CI job across six Python versions. Neither `command_surface.py` nor the test file was declared. Compounding it, the file is `slow`-marked and the BARE suite the plan uses as validation DESELECTS it, so the plan's own validation would have reported green while CI failed | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-01 owns the declaration contract and the scenario coverage its `command_class` implies; `command_surface.py` and `tests/test_cli_conformance_matrix.py` added to `Scope-Paths`; the five `oc profile *` entries pinned as a pre-existing baseline and fenced out of scope; the required-tests section and the gate both state that a bare green suite is NOT evidence and demand the explicit conformance run; V-01 requires it pasted |
| PR-094 | HIGH | IN-SCOPE | C. architecture; Honest documentation | read `cli.py`'s `runs` help entry, `_RUNS_DESCRIPTION`, the direction-split comment at `cli.py:111`, and `conformance_matrix.required_scenarios` | **`analyze` MUTATES ON A NOUN DOCUMENTED READ-ONLY AND THE PLAN NEVER SAID SO.** `aw runs` is "the READING half of the run surface ... Read-only, except the opt-in `repair` verb"; `analyze` updates a cache and publishes a bundle, making it the second exception. Two mechanical consequences were missed: `command_class` must be `mutation`, which changes the required scenario set, and the noun's description becomes false when the leaf lands | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | The Goal states the direction violation and the class; E-01 requires a deliberate `command_class` per leaf; E-02 requires `_RUNS_DESCRIPTION` and the help epilog updated so the read-only claim stays true; V-02 requires the updated text pasted; OQ-01/D-1 rejects both a false `read` declaration and relocating the verb to `aw run` |
| PR-095 | HIGH | IN-SCOPE | E. testing (a vacuous assertion); D. invariants | ran `aw runs -- analyze`, `-- query`, `-- status`; called `resolve_target_runs` for each token (0/0/135); confirmed `"status"` is a JSON key in every `state.json` | **THE COLLISION TEST WOULD HAVE PASSED BEFORE ANY CODE WAS WRITTEN AND WOULD HAVE WALKED PAST A REAL BUG.** `aw runs -- analyze` already prints `no matching runs found` exit 0, so the assertion is vacuous. And `aw runs -- status`, the documented example, returns ALL 135 runs rather than a run named `status`, because the final fallback greps raw `state.json` TEXT for `"<token>"` and `status` is a key in every file. A test built on the documented example would pin a bug as expected behavior | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-07 requires a PURPOSE-BUILT fixture actually named `analyze`/`query` plus the pre-change behavior pasted to prove the test distinguishes fixed from unfixed; requires the `"status"` bug REPORTED and not depended upon; fences fixing it out of scope with the reason; V-07 requires all of it; OQ-03/D-3 records the decision |
| PR-096 | HIGH | IN-SCOPE | C. architecture (second protocol); F. KISS | imported `agent_schema` and printed `SCHEMA_VERSION`, `RECORD_KINDS`, `VALID_OUTCOMES`; read `validate_agent_record` and `filter_record_fields`; read the quality-gate budgets | **THE AGENT PROTOCOL ALREADY EXISTS AND THE BUDGET MAKES THE PROPOSED VIEWS NON-CONFORMANT BY DEFAULT.** `aw.agent/v1` has a closed four-value `RECORD_KINDS`, a closed thirteen-value `VALID_OUTCOMES`, anti-greenwashing invariants, and an existing bounded projection helper, so a "versioned query protocol" is this envelope plus a payload. Separately `BYTE_BUDGET = 1200` / `TOKEN_BUDGET = 400` per record is enforced, which a distributions or slices view over 29766 rows breaches by construction | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-06 requires emission through the existing envelope, passing `validate_agent_record`, inside the measured budget BY DEFAULT, with pagination rather than silent truncation and `filter_record_fields` reused; the fence forbids raising the budget or adding a `VALID_OUTCOMES` value silently; V-06 requires the largest default record measured against 1200/400; OQ-02/D-2 records it |
| PR-097 | MEDIUM | IN-SCOPE | Spec/documentation sync | listed `.aw/records/specs/`; read `20260818-1525-01-command-surface-redesign` (`Status: implemented`, normative Section 3, R4) | **THE SPEC-SYNC SECTION DEFERS A DISCOVERY THAT IS ALREADY ANSWERED.** "If the repository maintains a controlling CLI grammar spec, execution must amend it before registering leaves" leaves an executor to find an IMPLEMENTED normative spec mid-run and plausibly edit it, while no `.spec.md` is declared in `Scope-Paths` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The section now states the spec exists, is implemented, and is NOT amended by adding leaves under an existing noun (it does not enumerate the existing nine either, and its R4 is a requirement this plan satisfies); the fence forbids editing it; the one genuine escalation (a mutating leaf judged a grammar violation) is preserved as a STOP-and-raise; OQ-04/D-4 records the reasoning |
| PR-098 | MEDIUM | IN-SCOPE | A. correctness; E. testing | read `_dispatch`'s pre-parse `--` block and `_ViewerOrLeafSubParsersAction`; ran the escape against a real run id | **THE `--` ESCAPE CANNOT REACH A LEAF BY CONSTRUCTION, SO ONE PROMISED BEHAVIOR IS ALREADY GUARANTEED AND THE TWO HALVES LIVE IN DIFFERENT PLACES.** `_dispatch` forces `runs_command = None` and hardcodes `run_viewer.run_viewer_cli`, so an escaped token is always a viewer target; "fixed leaves win without `--`" is a property of the routing action instead. A purely behavioral test would not distinguish them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 requires the dispatch-level guarantee asserted directly (that `runs_command` is forced to `None`) in addition to the behavioral matrix; the conventions record the mechanism and that half the promised behavior is structural; V-07 requires the assertion pasted |
| PR-099 | MEDIUM | UNDER-SCOPE | B. security/side effects; E. testing | grepped the package for `webbrowser`, `xdg-open` and `--open` (only an unrelated `--open-questions`) | **`--open` IS GREENFIELD WITH NO PRECEDENT AND NO TEST DOUBLE**, so "must never launch a browser" has no seam to assert against and inspection is not proof | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | New E-04 requires an injectable launch seam and a stub that FAILS if invoked, plus documented codes and remedies for the supported, unsupported and launch-failure paths; V-04 requires the raising-stub test pasted and the absence of precedent stated |
| PR-100 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | orchestrator `5lxvl3` OQ-01 read; item content counted against the workflow's split diagnostics; lint conforming both before and after | **MECHANICALLY SIZED.** E-03 bundled routing, compatibility, failure semantics, discoverability and help output across five unrelated test surfaces; E-02 bundled ten query views with a schema-versioning contract and an output-format matrix. Eighth sibling with this finding | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into EIGHT items across four groups (surface contract / analyze / query / routing and failure); `Highest E allocated` 03 -> 08; V-01..V-08 rewritten to bijection; a right-sizing note records the measurement; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-101 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); seven sibling review records | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions. Eighth consecutive sibling | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement, the load-bearing `6eq3oq` dependency and the three consuming Orders; a fence naming eight measured prohibitions; a concurrent-edit warning specific to `cli.py`/`command_surface.py` as high-traffic shared files; the honesty rule with the slow-marker trap called out explicitly; re-measure-every-number; and FIVE stop conditions |
| PR-102 | LOW | IN-SCOPE | Presentation; Evidence accuracy | `grep -o` count before the fix (78); bare suite run; read `tests/test_cli_output_docs_rollout.py` | Seventy-eight escaped backtick pairs rendered as literal backslashes, the worst count in the Set (after 6, 4, 10, 18, 16, 4 and 20). No baseline recorded despite requiring a bare suite run. And "Help and README command snippets are executable" has NO mechanism: the docs test asserts CONTENT and executes no snippet | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All 78 backticks unescaped, verified zero remaining with zero smart quotes or dashes; baseline recorded (`2 failed, 5655 passed, 3 skipped, 2 xfailed in 100.25s`) with both node ids attributed pre-existing; E-08 requires the snippet claim be IMPLEMENTED as a harness or explicitly DOWNGRADED, and V-08 requires the choice stated because an implied claim is a failed validation |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What `command_class` does each leaf declare, given `analyze` mutates on a read-only noun? | `query` = `read`, `analyze` = `mutation`, with the noun's description corrected to name both exceptions | Declaring `analyze` as `read` to avoid touching the description, rejected because it is a false declaration in the normative inventory and demands the wrong scenario coverage. Moving `analyze` to the WRITING noun `aw run`, rejected because that noun is the ledger-transaction surface (`start`/`record`/`cancel`/`finalize`) where an analytics build does not belong, and the requested contract is `aw runs analyze`. Routing it positionally like `repair` to dodge declaration, rejected on the routing action's own recorded grounds: invisible to `discover_parser_leaves`, no argparse help, and declaring it registers as drift | `cli.py:111` direction split; `_RUNS_DESCRIPTION`'s "ONE exception" text; `conformance_matrix.required_scenarios`; `repair` confirmed absent from all 129 declarations | yes |
| D-2 | Does `query` define a new protocol, or emit the existing envelope? | The existing `aw.agent/v1` envelope with a `data` payload, bounded and paginated by default | A parallel schema with its own version, rejected because two envelopes drift and every agent consumer would need to detect which it got. Raising `BYTE_BUDGET`/`TOKEN_BUDGET` so a distributions view fits, rejected because the budget exists to stop the machine convention bloating and the correct fix is a bounded default with pagination. Adding a `VALID_OUTCOMES` value for a refused slice without discussion, rejected because that set is a cross-cutting contract; `cannot-run` is the closest fit and a genuine gap is a maintainer question | `agent_schema.SCHEMA_VERSION`, `RECORD_KINDS`, the 13-value `VALID_OUTCOMES`, `validate_agent_record`, `filter_record_fields`; `BYTE_BUDGET = 1200` / `TOKEN_BUDGET = 400` in `tests/test_cli_quality_gates.py` | yes |
| D-3 | How is leaf-name collision behavior tested, given nothing in the tree collides? | A purpose-built fixture named `analyze` (and `query`), plus a direct code-level assertion of the dispatch guarantee | Asserting against the real corpus, rejected because nothing in it collides so the test is vacuous (measured: zero of 78 setids, 345 run tokens, 639 tracked plan tokens). Asserting via `aw runs -- status`, rejected because that returns ALL 135 runs due to the raw-JSON key match, so the test would pin a bug as expected behavior. Fixing that bug here, rejected as out of scope: it is `run_viewer` target resolution adjacent to Order 01's discovery work, and changing it alters what every existing viewer invocation matches | ran all three escape commands; `resolve_target_runs` returned 135/0/0 for `status`/`analyze`/`query`; `_dispatch` forces `runs_command = None` and hardcodes the viewer | yes |
| D-4 | Does registering two leaves amend the implemented CLI grammar spec? | NO. The spec governs the noun-verb shape and the cross-cutting verbs, not the leaf census under an existing noun | Amending the spec to enumerate the new leaves, rejected because it does not enumerate the existing nine either, so treating a conformant addition as a spec change makes every future leaf one. Leaving the question conditional as authored, rejected because an executor discovering an IMPLEMENTED normative spec mid-run would plausibly edit it, which the fence now forbids. Treating R4 as a change, rejected because documented exit codes plus `--json`/`--agent` is a requirement this plan satisfies rather than alters | `20260818-1525-01-command-surface-redesign.spec.md` read: `Status: implemented`, normative Section 3, R4; no `.spec.md` in `Scope-Paths` | yes |
| D-5 | Does the plan get `command_surface.py` and `tests/test_cli_conformance_matrix.py` in `Scope-Paths`, which it omitted? | YES, necessarily and minimally | Leaving them out, rejected because a leaf literally cannot be declared without the first, and the finalize scope gate would refuse the run over an undeclared edit mid-execution, which is the situation declare-then-reconcile exists to avoid. Declaring `cli.py` alone and hoping the conformance test tolerates a new leaf, rejected on measurement: the test asserts the undeclared set is EMPTY. Fixing the five pre-existing `oc profile *` declarations while in there, rejected and fenced out, because it would make a new regression unattributable | `find_undeclared_leaves` asserted empty by `test_no_undeclared_parser_leaves`; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` mechanics; the five-entry pre-existing baseline measured | yes |
