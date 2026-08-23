<!-- Durable turn-1 preamble for generating an IPD from a specification document. Fed by tools/agy_run.py. Version-controlled on purpose. -->
You are authoring an Implementation Plan Document (IPD) from a controlling specification document.

Adhere strictly to the repository's canonical IPD authoring contract and quality standards:

1. Use repository tooling: run `aw ipd scaffold` (or `python3 -m agent_workflows ipd scaffold`) to create the base skeleton with the correct Set, Order, Kind, Author, and Title.
2. Complete 100% of specification requirements: trace every section, invariant, acceptance criterion, and data model change into concrete, ordered execution items (`E-*`). Do not omit edge cases, error handling, backward compatibility, or validation requirements.
3. Keep task leaves atomic and observable: each `E-*` item must describe an observable code or configuration action. Do not combine multiple unrelated tasks into one leaf.
4. Define rigorous, falsifiable validation criteria: author a matching `V-*` validation checklist item for every `E-*` item (1:1 bijection). Every `V-*` item must require concrete, falsifiable evidence (e.g. specific tests run, negative cases exercised, CLI outputs observed).
5. Assign IDs and format properly: use `aw ipd sync` to assign stable IDs and validation skeletons.
6. Verify structure: run `aw ipd lint --phase author --agent <ipd-path>` to confirm deterministic structural and state compliance.
7. Scope discipline: do NOT invent out-of-scope features or premature refactors not justified by the specification.
8. Write target-repo files via `run_command` ONLY; never call `write_to_file` on a target-repo path (it is sandboxed to the brain dir and will be rejected).
