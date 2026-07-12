# 10 Validation results
- Full suite: 215 passed in ~45s (pre-fix 212; +3 rc-comparator regression tests).
- Packaging test: 5 passed (ship-vs-dev gate; wheel content verified).
- Build: wheel built; twine check PASSED (metadata valid after classifier drop + url adds).
- plan-names: 0 to rename. em/en-dash sweep: 0 across changed files.
- Direct repros: rc compare/status/next_version_ok correct; Term(color=False).stream not bool, line() no crash.
