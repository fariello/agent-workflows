- Id: 5mc38x
- Status: open
- Set: 5mc38x
- Priority: low
- Work-Kind: followup
- Summary: Decide the standing convention for a test that genuinely asserts something about the live checkout root: loud skip or synthesize

## Workflow history
- 2026-09-20 created (aw backlog): Carries OQ-01 from plan zx9dkq, which was narrowed at review to a question about FUTURE tests only; filed so it survives that plan reaching executed.

CARRIES `OQ-01` FROM PLAN `zx9dkq` (non-blocking, owner: maintainer). Filed because the plan is being executed and an open question recorded only inside an `executed` plan classes as `done` in `aw attention` and disappears.

THE QUESTION. For a test whose property GENUINELY depends on the checkout location, is the right answer a loud `skip` naming the condition, or synthesizing the input so the assertion runs everywhere?

WHAT `zx9dkq` SETTLED, so this is not re-litigated: NEITHER of the two tests it fixed had that property. Both assert "the sanitizer detects a home-style absolute path travelling through the renderer", and the live checkout root was merely a convenient source of such a path. Measured during its execution: `build_ruleset` yields the SAME eight fail-rule names for a home-tree root and a temp-directory root (empty symmetric difference), and the temp-root ruleset flags a home-style string at `fail` exactly as the repo-root ruleset does, because the `home-path` pattern is a hardcoded regex and `repo_root` only selects an optional repo allowlist. So a synthetic literal tests the SAME property rather than an adjacent one, the "FOR SKIPPING" branch had no applicable case, and no skip was introduced.

WHAT REMAINS OPEN, and it is a judgement about what a test is FOR rather than a measurement: if a FUTURE test really does want to assert something about THIS repository own root (not a property that merely happens to be reachable through it), a loud skip is arguably more honest than a synthetic substitute that quietly tests something adjacent. The competing view is that a skip in an environment nobody watches is indistinguishable from the vacuous pass the repository already forbids.

WHY IT IS LOW PRIORITY: no test in the tree needs the answer today. It becomes live the moment someone writes one, and having the convention decided in advance is cheaper than arguing it inside a review.

RELATED PRECEDENT worth citing when deciding: `tests/test_nested_tty_noninteractive.py` docstring records that lowering a threshold "would have made this pass while silently accepting a future change that actually removed a `stdin=`", which is the repository stated position that weakening a guard to make it pass is forbidden. A skip with a stated reason is the honest alternative; a vacuous pass is not.
