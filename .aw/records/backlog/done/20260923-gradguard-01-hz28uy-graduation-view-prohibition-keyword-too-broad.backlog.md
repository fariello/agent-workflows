- Id: hz28uy
- Status: done
- Set: gradguard
- Priority: low
- Work-Kind: bug
- Summary: graduation-view rule prohibition matches the bare words graduation and duplicate, rejecting unrelated rules with a misdiagnosing message

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: guard test removed in 19313eed
- 2026-09-23 created (aw backlog): graduation-view rule prohibition matches the bare words graduation and duplicate, rejecting unrelated rules with a misdiagnosing message

Found while executing plan `bwgyum`, which had to RENAME a correct new rule to get past this guard.

WHAT IT IS. `tests/test_graduation_view.py::NoUniquenessRuleTests::test_no_check_rule_was_registered_for_this_view`
asserts that NO id in `check_engine.RULE_REGISTRY` contains the substring `graduation` OR `duplicate`.

THE UNDERLYING RULING IS CORRECT AND SHOULD NOT BE WEAKENED. The `graduate` Set's OQ-01 resolved that a
source carrying several artifacts is LEGITIMATE decomposition (33 sources in this repo do, the largest
cluster being ten), so a `count > 1` check rule would report correct work as a defect and teach readers to
ignore the surface. Keeping that prohibition structural, rather than trusting a comment, is right.

THE DEFECT IS THE PROXY. The guard's subject is artifact CLUSTERING PER SOURCE, but its test is a KEYWORD
MATCH on two common English words, so it also forbids any unrelated rule whose id happens to contain
`duplicate`. Measured: `bwgyum` registered `check.graduated-to-duplicate` for a setid listed twice WITHIN
ONE FIELD (unambiguously an author error, nothing to do with clustering) and this test failed. The rule was
renamed to `check.graduated-to-repeated`, which was the cheap correct move for that plan, but the next
author hitting this will face the same choice and may instead weaken the guard, losing a real invariant to
a word.

WHY IT IS FILED AS A BUG rather than a nit: the guard's failure message states a reason that is FALSE for
the rule it just rejected ("a rule would fire on every legitimate multi-artifact cluster"), so it
misdirects the reader about what is wrong with their code. A guard whose message misdiagnoses its own
finding is a defect in the guard.

POSSIBLE FIX DIRECTION (not designed here). Assert the prohibition against what it actually means: no rule
that COUNTS artifacts per source. For example pin the specific forbidden ids, or scope the keyword match to
ids in the graduation-view family, so an unrelated rule using a common word is not collateral.
