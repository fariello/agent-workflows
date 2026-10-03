- Id: gia5i7
- Status: graduated
- Graduated-To: gia5i7
- Set: gia5i7
- Priority: low
- Work-Kind: chore
- Summary: runner_shared cites the test class NoRunnerImportTests at eight sites and it exists nowhere in tests/

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: 9vtas9
- 2026-09-29 created (aw backlog): runner_shared cites the test class NoRunnerImportTests at eight sites and it exists nowhere in tests/

MEASURED 2026-09-29 in lane nbu56f at HEAD 4bf73373 while authoring plan cvs2b7 (backlog nbu56f).

`agent_workflows/runner_shared.py` cites `tests/test_runner_shared.py::NoRunnerImportTests` at EIGHT comment sites as the AST guard that enforces its no-runner-import layering rule, and `agent_workflows/oc_runipd.py` cites it once more. The class does not exist:

    $ grep -rn 'NoRunnerImportTests' agent_workflows/*.py | wc -l   -> 9 (8 in runner_shared, 1 in oc_runipd)
    $ grep -rn 'class NoRunnerImport' tests/                        -> no match (exit 1)

THIS IS THE SAME CLASS OF DEFECT ALREADY RECORDED ONCE. Executed plan `nzznlm` F-7 measured three sibling dangling citations in the same neighborhood (`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`, `::TheTwoMeasurementsAreComparable`, `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`) and recorded that neither FILE exists. Re-checked here: both files are still absent. So at least four cited guard classes across two absent files plus one absent class are cited as live enforcement.

WHY IT MATTERS RATHER THAN BEING COSMETIC: each citation is load-bearing PROSE, offered as the reason a design constraint is safe to rely on. `runner_shared`'s layering rule (the module may not import either host driver) and its injection-not-import design for `run_suite_check` are both justified by pointing at this guard. Since the guard is absent, the constraint is a CONVENTION that nothing enforces, while the comments assert it is tested. That misleads in the expensive direction: a reader trusts the constraint is machine-checked and does not check it, and the next author who does check finds nothing and cannot tell whether the constraint was abandoned or the citation merely rotted.

FILED chore, NOT bug, on the same reasoning `pn7rw3` records: no user-perceptible behavior is wrong and no operator waits on anything. The cost falls on a future maintainer.

THE REMEDY IS ALREADY SETTLED BY A MAINTAINER RULING, so this item needs no restore-or-strike decision. The class was DELETED in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), measured here with `git log -S "class NoRunnerImportTests"`, which is the SAME commit that deleted the two guard files sibling item `pn7rw3` records. `pn7rw3` carries the ruling, dated 2026-09-28: "Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." That governs this item too, since `NoRunnerImportTests` was exactly such a pin: it AST-walked module source rather than exercising behavior, which is what AGENTS.md and GUIDING_PRINCIPLES P16 now forbid. SO THE FIX IS TO STRIKE THE NINE CITATIONS, not to restore the guard. When striking, preserve each comment's still-true DESIGN point (the layering rule, and the injection-not-import shape of `run_suite_check`) and remove only the false claim that a test enforces it; a reader should end up knowing the constraint is a convention, not an enforced invariant.

RELATIONSHIP TO `pn7rw3`, stated so a triager can decide whether to merge them: same root cause (`19313eed`), same ruling, same fix shape, but DIFFERENT FILES and different symbols. `pn7rw3` is about a comment in `tests/test_runner_shared.py` citing two deleted files for `should_color`; this item is about nine comments in `agent_workflows/runner_shared.py` and `agent_workflows/oc_runipd.py` citing one deleted class for the layering rule. Merging them into one sweep is defensible and may be the efficient call; they are filed separately because the shipped-package citations are the ones a packaged-source detector would cover and the test-file one is not.

RELATED BUT DISTINCT: pending plan `68hdic` builds a `--source-citations` detector for dangling RECORD-filename citations under `agent_workflows/` and `tools/`. It does not cover TEST-CLASS citations, so it will not catch this family. Whether the detector should be extended to cover `module::Class` citations is a reasonable follow-on question but is not this item.

FOUND WHILE: authoring plan `cvs2b7`, which corrects a different stale claim in two of the very comments that carry this dangling citation. That plan declares this OUT OF SCOPE and carries this item as its carrier; its E-05 is required not to add a new citation to a nonexistent class.
