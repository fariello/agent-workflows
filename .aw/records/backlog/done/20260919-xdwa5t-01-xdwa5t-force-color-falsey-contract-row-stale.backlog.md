- Id: xdwa5t
- Status: done
- Set: xdwa5t
- Priority: medium
- Work-Kind: bug
- Summary: docs/cli-output-contract.md section 1.1 row 2 misstates FORCE_COLOR: it promises a falsey FORCE_COLOR both cancels NO_COLOR and enables color, and the shipped code does neither

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: duplicate of bar5t8
- 2026-09-19 created (aw backlog): docs/cli-output-contract.md section 1.1 row 2 misstates FORCE_COLOR: it promises a falsey FORCE_COLOR both cancels NO_COLOR and enables color, and the shipped code does neither

FOUND BY the Section 12a re-review of spec uonrjg (plan n4xq3l), 2026-09-19, while measuring the shipped color precedence chain that A13 of that spec now cites.

WHAT IS WRONG. docs/cli-output-contract.md section 1.1 row 2 reads: 'NO_COLOR (any value, including empty) disables, UNLESS FORCE_COLOR is set; FORCE_COLOR (any non-empty value) enables.' Taken at its word that makes FORCE_COLOR=0 do two things: cancel NO_COLOR (it IS set), and enable color (0 is non-empty). The shipped code does NEITHER.

MEASURED 2026-09-19 against term.should_color on a non-TTY stream at HEAD 0da6b672:

    FORCE_COLOR=0                 -> False   (document implies True)
    FORCE_COLOR=off               -> False   (document implies True)
    NO_COLOR=1 FORCE_COLOR=0      -> False   (document implies True)
    NO_COLOR=1 FORCE_COLOR=false  -> False   (document implies True)

WHY THE CODE IS RIGHT AND THE DOCUMENT IS THE STALE ARTIFACT. term._FORCE_COLOR_FALSEY is frozenset({'', '0', 'false', 'no', 'off'}) and both FORCE_COLOR readings route through the single term._force_color_is_forcing predicate. Its docstring records the measurement that forced that design: making only the FORCING site falsey-aware while leaving the CANCELLING site a bare presence test caused SIX of twelve NO_COLOR-set cells to colorize on a TTY, silently voiding the accessibility convention for any user who sets both variables. So a falsey FORCE_COLOR meaning 'do not force' (and NOT 'suppress', which is NO_COLOR's job) is deliberate and better. The defect is the documentation wording, not the behavior.

WHY THIS IS FILED AS A BUG rather than a chore, stated so a reviewer can dispute the judgement rather than a vibe: this file is published as the NORMATIVE output contract, and row 2 is the row an external script author reads before choosing how to suppress color in CI. Acting on it as written produces the wrong expectation, and on accessibility grounds the affected case is precisely a user who set NO_COLOR. That is user-perceptible impact from a document, not merely internal untidiness. If a maintainer judges a doc-only wording gap to be a chore, reclassify it; the measurement above does not change either way.

SUGGESTED FIX. Reword row 2 to state the falsey set explicitly and name the predicate, for example: 'NO_COLOR (any value, including empty) disables, UNLESS FORCE_COLOR is set to a FORCING value; FORCE_COLOR forces color on unless its value is one of "", 0, false, no, off (case-insensitive, stripped), in which case it neither forces nor suppresses and detection proceeds normally.' Add the four cells above to the worked-cases table beneath it, which currently enumerates only truthy FORCE_COLOR and so does not catch this. NOT FIXED IN THIS TURN because plan n4xq3l's Scope-Paths declares the uonrjg spec only, and editing a published contract doc is outside it; spec uonrjg A13 now records the discrepancy and instructs an implementer to follow the code.
