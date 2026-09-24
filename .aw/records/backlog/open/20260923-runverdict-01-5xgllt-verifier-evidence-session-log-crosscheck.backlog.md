- Id: 5xgllt
- Status: open
- Set: runverdict
- Priority: medium
- Work-Kind: followup
- Summary: Cross-check the verifier's claimed tests_run commands against the session log's actual tool calls

## Workflow history
- 2026-09-23 created (aw backlog): Cross-check the verifier's claimed tests_run commands against the session log's actual tool calls

FOUND while executing plan `bxx9af` (runverdict Order 05), and recorded as the KNOWN RESIDUAL WEAKNESS of the gate that plan shipped.

WHAT THE GATE DOES AND DOES NOT PROVE. `runner_shared.check_verifier_evidence` now requires a VERIFIED verdict to be accompanied by test activity in `tests_run`. It PROVES ACTIVITY, NOT CORRECTNESS: a determined verifier could write a plausible command string having run nothing, and the predicate would accept it. This is stated in the module header in as many words ("DO NOT DESCRIBE THIS PREDICATE AS FABRICATION-PROOF") and pinned by `HonestyTests::test_a_plausible_but_unrun_command_is_accepted_which_is_the_known_gap`, so the limit is durable rather than folklore.

WHY THE GATE CANNOT SIMPLY BE TIGHTENED. 131 of 263 measured corpus entries are BARE PROSE STRINGS carrying the command and its result in one line, so refusing prose would refuse roughly half of every historically genuine verification. A predicate that refuses a genuine outcome is a CLOSED LANE, which is strictly worse than the opaque bit it replaced - the calibration hazard that bit twice already in this Set (the backlog item's own bar refused 25 of 35; the plan's own replacement bar refused one more).

THE ACTUAL FIX, which is why this is its own item. Parse the verifier turn's session log, extract the tool calls it really made, and match them against the commands it CLAIMED in `tests_run`. That closes the fabrication gap without tightening the shape rule at all, so it costs no false negatives. It is a different subsystem (session-log parsing) with a different failure model (a log that cannot be read must not refuse a genuine verification), which is exactly why `bxx9af` scoped it out rather than absorbing it.

PROVENANCE: this is the backlog item `rbftpl`'s own strongest option and its test (e). That item said to scope it separately "if it proves expensive", and it is.
