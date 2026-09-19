- Id: jt01do
- Status: open
- Set: jt01do
- Priority: low
- Work-Kind: chore
- Summary: bound_expiry_reaper's reap annotation Callable[[Any, Path], Any] contradicts its keyword call reaper(process, run_dir=run_dir), so a type checker errors on lane_containment.py:1208

## Workflow history
- 2026-09-19 created (aw backlog): Found while executing 5w8g8j (laneign). Pre-existing, unrelated to that plan's scope. Runtime-harmless because the default runner_shutdown.clean_shutdown declares run_dir as a named parameter, but the declared Callable type says positional-only-shaped two-arg, so pyright reports 'Expected 1 more positional argument'. Fix: annotate the protocol with the keyword, e.g. Callable[..., Any] replaced by a Protocol with (process, *, run_dir).
