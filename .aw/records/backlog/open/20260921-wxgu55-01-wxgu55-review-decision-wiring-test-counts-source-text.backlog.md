- Id: wxgu55
- Status: open
- Set: wxgu55
- Priority: low
- Work-Kind: chore
- Summary: tests/test_review_decisions.py proves wiring-exactly-once by counting a symbol's occurrences in check_engine.py source text, so any prose mention of that symbol fails it

## Workflow history
- 2026-09-21 created (aw backlog): Found while executing lintreach k9awrq. test_wired_into_the_plans_type_content_path_exactly_once does src.count('check_review_decision_unescalated') minus definitions and requires 1, so a DOCSTRING naming that symbol reads as a second call site and fails the test. This repository already recorded the general form of this defect: tests/test_durable_capture.py's header explains it removed its own two inspect.getsource pins because 'a substring search cannot establish either: the positive is satisfied by a COMMENT naming the symbol (measured twice in this repository)'. The k9awrq execution hit it a third time and worked around it by citing the neighbour rule by RULE ID instead of by symbol name, so the brittleness is still there for the next author who mentions the symbol. Fix: assert the wiring by DRIVING it (the sibling test test_reached_by_both_check_plans_and_check_all already does the positive half) or by counting only non-comment lines, rather than by substring search over source text.
