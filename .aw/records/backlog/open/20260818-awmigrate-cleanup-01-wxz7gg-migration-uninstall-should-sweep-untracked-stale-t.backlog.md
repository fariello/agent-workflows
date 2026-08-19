- Id: wxz7gg
- Status: open
- Set: awmigrate-cleanup
- Priority: medium
- Kind: chore
- Summary: migration/uninstall should sweep untracked stale-tool leftovers under .agents/

## Workflow history
- 2026-08-18 created (aw backlog): migration/uninstall should sweep untracked stale-tool leftovers under .agents/

After the .agents/ -> .aw/ migration, untracked stale-tool litter remains under .agents/workflows/ (compiled __pycache__/*.pyc from tools that used to run from .agents/workflows/*/tools/, plus emptied tool dir skeletons). It is untracked (0 tracked files, not shipped) so the transactional migration - which moves TRACKED/inventoried content - never touches it. Problem: a naive 'ls .agents/workflows/' shows plausible-looking workflow dirs (assess/benchmark/conformance/setup-repo/verify) with no plan-review etc., which misleads an agent into thinking the old layout is still live (an opencode agent tripped on exactly this: tried to read .agents/workflows/plan-review/plan-review.md, which does not exist there; the real shims correctly point at .aw/system/workflows/). Fix: the leftover-disposition step of aw migrate-layout (and aw uninstall --deep) should DETECT untracked stale-tool leftovers under a migrated legacy root (e.g. .agents/workflows/**/__pycache__ + emptied *tools* dirs) and OFFER to remove them (respecting the existing keep/remove/defer leftover policy; never delete without consent). Distinct from the tracked-content migration which is already correct. Note: the real native command shims (.claude/commands, .opencode/command) already point at .aw/system/workflows/ - this is ONLY about disposable on-disk litter.
