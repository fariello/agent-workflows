- Id: ihgjii
- Status: open
- Set: ihgjii
- Priority: medium
- Work-Kind: chore
- Summary: match_selector's type narrowing is duplicated and unreachable from the production call shape, so a scoped-resolution test can pass vacuously

## Workflow history
- 2026-09-21 created (aw backlog): match_selector's type narrowing is duplicated and unreachable from the production call shape, so a scoped-resolution test can pass vacuously

MEASURED 2026-09-21 while executing plan `w2y5ac` (setidfix 02), whose V-01 mutation check found it.

`status_set.match_selector` narrows by type in TWO places, and neither is observable from the shape
every production caller actually uses, so a test can pass VACUOUSLY while believing it pins spec
`2lcqno` N3.

THE TWO SITES:

1. the FAST PATH (the `cands = [r for r in all_records if not target_type or r.record_type ==
   target_type]` filter applied before the resolver is consulted), which filters the CALLER-SUPPLIED
   record list; and
2. the RESOLVER QUERY (`if scoped_type: record_types = (canonical,)`), which narrows which types
   `selectors.resolve` is asked about.

WHY THAT IS A HAZARD RATHER THAN MERELY REDUNDANT. Every caller in `run_set_command` obtains its record
list from `inventory_all_artifacts(repo_root, scoped_type=scoped_type_canonical)`, i.e. the list is
ALREADY narrowed to the scoped type before `match_selector` ever sees it. So the type safety of the
scoped path is established by the CALLER, and `match_selector`'s own two filters are belt-and-braces. A
test that mirrors the production call shape (passing the pre-narrowed inventory) therefore CANNOT
observe either filter failing.

MEASURED, and this is the part worth fixing: with BOTH narrowing sites mutated out (`if scoped_type:`
-> `if False:` and `cands = list(all_records)`), a test asserting that `match_selector('<a shared
setid>', inventory_all_artifacts(root, scoped_type='plans'), root, scoped_type='plans')` returns only
plans STILL PASSED. The same assertion against the FULL unnarrowed inventory (`scoped_type=None`) FAILS
under the identical mutation. Plan `w2y5ac`'s E-01 test now passes the unnarrowed inventory with an
in-code comment recording the trap, so that specific pin is sound; this item carries the underlying
shape, which the next author will meet again.

WHY IT MATTERS BEYOND ONE TEST. Spec `2lcqno` N3 makes type-scoped resolution normative, and the only
thing that makes it TESTABLE is `scoped_type` being load-bearing in the function under test. Today a
reader cannot tell from the call site whether the narrowing is defensive duplication or the actual
guarantee, which is precisely the confusion that produced `w2y5ac`'s worst authored instruction
(concluding the `Type mismatch` refusal was dead code because "the pre-filter narrows by type").

SUGGESTED SHAPE, not a decision: either state in `match_selector`'s docstring that callers pass a
pre-narrowed list and its own filters are defensive, so a future test author knows to pass an
unnarrowed list to exercise them; or drop the redundant fast-path filter and let `scoped_type` be the
single narrowing authority. The first is a comment. The second is a behavior change needing its own
measurement, because the fast path exists for performance (commit `4cfa2283`, "optimize attention and
set command performance").

FILED `chore`, NOT `bug`, DELIBERATELY: there is no wrong answer and no perceptible slowness, so it
fails the AGENTS.md user-perceptibility test for a defect. Its cost is paid by the next author who
writes a test believing it pins something it does not.
