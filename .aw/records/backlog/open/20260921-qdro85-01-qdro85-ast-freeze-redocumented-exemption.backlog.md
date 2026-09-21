- Id: qdro85
- Status: open
- Set: qdro85
- Priority: low
- Work-Kind: followup
- Summary: The AST-freeze harness had no route for a REVISED docstring; DOCUMENTED_SINCE_MOVE only handles a GAINED one

## Workflow history
- 2026-09-21 created (aw backlog): Filed by plan 2iye0e execution turn; the immediate gap is already closed by that plan's REDOCUMENTED_SINCE_MOVE, this item records the residual design concern.

FOUND WHILE EXECUTING 2iye0e E-04, whose plan text prescribed a remedy that does not work, so the gap is recorded rather than left implicit.

THE GAP. tests/test_runner_shared.py's DOCUMENTED_SINCE_MOVE subtracts the leading docstring from the CURRENT source only and then requires equality with the pre-move capture VERBATIM. That is correct for a symbol that GAINED a docstring, because its capture has none to subtract (measured: plan_bucket's captured body does not start with a docstring Expr). It is structurally unable to handle a symbol whose captured body ALREADY contains a docstring and whose docstring TEXT later changes: the comparison then puts a stripped body against an unstripped capture and can never match.

MEASURED, not reasoned: adding describe_lane to DOCUMENTED_SINCE_MOVE (which plan 2iye0e explicitly instructed, twice, as the correct route and contrasted against regenerating the fixture) FAILED with 'describe_lane was NOT a pure move' in test_every_clean_symbol_is_a_STRICT_fingerprint_match, and the failure message misleadingly said the difference was about an EXECUTABLE statement when only the docstring had changed.

WHAT 2iye0e DID ABOUT IT: added a second enumerated list, REDOCUMENTED_SINCE_MOVE, plus a _capture_without_docstring helper that applies the same subtraction to the CAPTURE side, plus test_a_redocumented_symbol_is_still_held_to_its_executable_body proving the exemption is narrow (it requires the capture to genuinely contain a docstring, requires the strict comparison to genuinely fail, and mutates an executable statement to prove the subtraction still refuses). The fixture was NOT regenerated and is byte-unchanged; len(clean) is still 22 so the drift guard was not relaxed.

THE RESIDUAL CONCERN WORTH A LOOK LATER, which is why this is filed rather than closed silently: there are now TWO docstring exemptions differing only by which side of the comparison needs stripping, and the correct one to use is not obvious from either name. A future author facing the same situation may reach for the wrong one and read the resulting failure as an executable-body change, which is the exact misdiagnosis this turn had to work through. A single two-sided mechanism (strip both sides whenever the name is exempt) would collapse them, but that is a deliberate widening of an intentionally narrow guard and should be reviewed on its merits rather than done opportunistically inside an unrelated plan.
