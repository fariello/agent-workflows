- Id: hd5bkk
- Status: open
- Blocks-Release: next
- Set: selquiet
- Priority: medium
- Work-Kind: bug
- Summary: aw find reports a zero-match selector as CLEAN exit 0, the same fail-open aw attention just fixed

## Workflow history
- 2026-09-21 created (aw backlog): aw find reports a zero-match selector as CLEAN exit 0, the same fail-open aw attention just fixed

MEASURED 2026-09-21 at HEAD ef640388 while executing plan fqnj8k (attsel): `aw find plans zzzzzz` prints `CLEAN  no matching plans` with the selector echoed under "Active filters:" and exits 0, on BOTH the human and the --agent surface.

WHY THIS IS A BUG AND NOT MERELY A DIVERGENCE. `aw find` is at least EXPLICIT about having found nothing, which is more than `aw attention` did, so it is a lesser defect than the one fqnj8k fixed. But the exit code carries the same fail-open: a script that resolves an id6 through `aw find` and gets exit 0 with an empty result concludes "nothing to do", which is the wrong conclusion, and the operator cannot distinguish a typo from a genuinely empty tree.

THE REPOSITORY HAS ALREADY RULED for selector-resolving verbs: spec 25kzda (Status: approved) Section 2.3 states "Zero matches return exit 2", with Section 2.4a exempting STATUS selectors only, closing "A misspelled id6 still exits 2; only the status selectors are exempt". `aw runs` implements exactly that (exit 2, outcome cannot-run, unresolved_targets). `aw attention` now does too, as of fqnj8k, including the vocabulary exemption.

SO THE DIVERGENCE IS NOW TWO-TO-ONE rather than one-to-one, which is what makes this worth filing: `aw find` is the remaining verb whose zero-match is a silent success.

WHAT A FIX NEEDS, and it is not a one-line exit change. `aw find`'s selector resolution is its own path with its own output contract; it accepts vocabulary tokens too, so it needs the same standing-question exemption `attention.selector_vocabulary()` now implements (reusing that function is the obvious first move). `aw ipd board` and any other selector-taking read verb should be surveyed in the same pass, since fixing one at a time is how the codebase ended up with three conventions.

DELIBERATELY OUT OF SCOPE OF fqnj8k, which declared only attention.py/cli.py/test_attention.py and states in its own deferred section that widening to N verbs would make one change to N contracts at once.
