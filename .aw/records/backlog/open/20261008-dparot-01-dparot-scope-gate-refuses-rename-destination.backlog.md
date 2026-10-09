- Id: dparot
- Status: open
- Blocks-Release: next
- Set: dparot
- Priority: high
- Work-Kind: bug
- Summary: Scope-target dispatch gate refuses a plan whose declared rename DESTINATION does not exist yet

## Workflow history
- 2026-10-09 created (aw backlog): Scope-target dispatch gate refuses a plan whose declared rename DESTINATION does not exist yet

MEASURED 2026-10-08, run run-20261007T181927Z-1710911: plan j7dsci (tf4jz5) was refused at dispatch with fail-gate, scope_target_refused '.aw/records/plans/executed/20260723-instsafe-07-qrokie-...ipd.md -> moved-terminal (resolved: .aw/records/plans/executed/20260101-instsafe-07-qrokie-...ipd.md)'.

That path is the RENAME DESTINATION the plan exists to create (it git-mv's 20260101-...qrokie... to 20260723-...qrokie...). It declares BOTH the source and the destination in Scope-Paths, which is the correct way to declare a rename. `check_engine.stale_record_scope_paths` treats every missing literal `.aw/records/` path as a STALE pointer, resolves it by id6 (`qrokie`) to the existing source file in executed/, classifies that as moved-terminal, and `runner_shared` refuses dispatch. So a plan whose job is to rename or create a record can never be dispatched by the runner.

Spec 25kzda 5.7 premise: "Only literal .aw/records/ scope paths are checked because non-records paths (new code or test files) are legitimately absent before execution." Records paths are legitimately absent before execution too, when the plan creates or renames them.

Candidate fix (needs a plan): do not classify a missing entry as stale when the same id6 resolves to a path ALSO declared in the same Scope-Paths (declared rename pair), and/or allow a plan to mark an entry as a creation target. A test should drive the dispatch gate with a declared rename pair and assert the item dispatches, plus a real stale pointer that is still refused.

Workaround until fixed: j7dsci can only run with its destination temporarily removed from Scope-Paths (which then fails finalize scope reconciliation) or by hand. It stays approved and unrunnable.

User-perceptible: yes. An approved plan fails every unattended run it is queued in, at zero cost but with a red fail-gate row that a maintainer must investigate.
