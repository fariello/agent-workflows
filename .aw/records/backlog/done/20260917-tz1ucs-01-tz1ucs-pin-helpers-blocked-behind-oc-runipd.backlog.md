- Id: tz1ucs
- Status: done
- Set: tz1ucs
- Priority: medium
- Work-Kind: chore
- Summary: The oc-to-agy import coupling grew by 4 because runner_shared cannot reach the af7i6p pin helpers

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by edcbbe27: pinned_child_env/pinned_module_argv live in runner_shared
- 2026-09-17 created (aw backlog): The oc-to-agy import coupling grew by 4 because runner_shared cannot reach the af7i6p pin helpers

FOUND 2026-09-17 while executing rununify 05 (ct4w0a) E-04, and it is the structural reason that plan could not do a pure lift.

THE FACT. `pinned_child_env`, `pinned_module_argv` and `runner_package_root` (plus `_AW_PIN_STRIP`/`_AW_PIN_BOOTSTRAP`/`_AW_PIN_PROBE`) are defined in `agent_workflows/oc_runipd.py` (:542-:611) and are the ONLY definitions in the package. `agy_runipd` reaches them by IMPORTING FROM `oc_runipd` (:333-337). That makes them the same object in both hosts, which is why they LOOK shared, but it does NOT make them reachable from `runner_shared`, which may never import a runner (tests/test_runner_shared.py::NoRunnerImportTests).

WHY IT MATTERS BEYOND ct4w0a. Any future shared symbol that launches a nested `aw` hits the same wall and must take the same two injected parameters. ct4w0a's `driver_begin` is the second such symbol (`run_checked` was the first, `818uru`), so the pattern is now established rather than incidental, and `driver_finalize` is the obvious third candidate with the same blocker.

THIS IS THE cnwy8g COUPLING, CONCRETELY. The oc-to-agy import baseline pinned in tests/test_orchestrator_probe_cache.py is 56 and ct4w0a left it UNCHANGED (verified: that test passes at the plan's execution HEAD), because the three names agy gained come from `runner_shared`, not from `oc_runipd`. But `pinned_child_env` and `pinned_module_argv` are STILL two of those 56, and they are the two this item is about: they cannot leave that list while they live in a host. Moving the pin helpers into a host-neutral module (`runner_shared`, or a small `runner_pin` module both can import) would let `driver_begin` and `driver_finalize` become pure moves with no injection, and would reduce that baseline for real.

SCOPE NOTE: not attempted in ct4w0a because it moves five module-level names that are NOT duplicated (they already have exactly one definition), so it is a re-layering rather than a de-duplication, and it touches the tool-identity probe, which no validation item in that plan covers. Decision 06-ct4w0a-D2 records the reasoning.
