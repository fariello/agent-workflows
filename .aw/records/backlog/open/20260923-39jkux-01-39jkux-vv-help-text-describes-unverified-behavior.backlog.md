- Id: 39jkux
- Status: open
- Blocks-Release: next
- Set: 39jkux
- Priority: low
- Work-Kind: bug
- Summary: the two host runners describe DIFFERENT -vv behavior in their --help text while driving the same clean renderer, so at most one was ever true and the surviving string is unverified

## Workflow history
- 2026-09-23 created (aw backlog): Found by hostdedup Order 02 (nmlx47) E-04 while unifying _add_output_mode_flags. The DIVERGENCE is gone (commit 63b71d8b, both hosts now emit the opencode string); what is filed is that the surviving string's ACCURACY was never checked.

MEASURED 2026-09-23 at HEAD 525442c4.

THE TWO STRINGS. Before unification, `-v/--verbose` help read:

  oc:  'Increase live stream detail: -v also shows reads and searches (with line ranges and hit counts), -vv also shows diff hunks and diagnostics. Ignored under --raw/--quiet.'
  agy: 'Increase live stream detail: -v also shows reads and searches, -vv also shows raw tool parameters. Ignored under --raw/--quiet.'

THESE DESCRIBE DIFFERENT BEHAVIOR, not different wording: 'diff hunks and diagnostics' against 'raw tool parameters'. Both hosts drive the SAME `clean` renderer, so at most one description can be correct, and the divergence was therefore a documentation defect on one host whichever way it was resolved.

WHY IT IS A BUG AND NOT A CHORE. A `--help` string is a documented interface an operator reads to decide which flag to pass, and a wrong one wastes a real person's time in the exact moment they are trying to get MORE diagnostic output from a run that is already going badly. It is filed LOW because the cost is bounded (one operator, one wrong expectation) and no automation reads it.

WHAT THE UNIFICATION DID AND DID NOT DO. hostdedup Order 02 E-04 collapsed the two to the opencode string per the Set's oc-preferred ruling for drift, and DISCLOSED the change in its V-04 (the antigravity host's `--help` text changed, which is operator-visible). It did NOT verify that the surviving string is TRUE, because that is a question about the `clean` renderer's tier behavior rather than about de-duplication, and answering it inside a lift would have mixed a behavior investigation into a structural change.

THE WORK. Read `render_stream`'s verbosity tiers and determine what `-vv` actually adds; then either confirm the surviving string or correct it. Spec 25kzda asserts nothing about either host's help strings (verified during that plan's review), so no spec amendment is implied either way. The one definition now lives in `runner_shared.add_output_mode_flags`, so a correction is a single edit reaching both hosts.
