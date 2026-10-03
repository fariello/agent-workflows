- Id: bmhoxe
- Status: graduated
- Blocks-Release: next
- Set: negorder
- Priority: low
- Work-Kind: bug
- Summary: aw group/rename plans accept a negative --order and corrupt the plan: a duplicate - Order: line plus a filename outside the NN grammar

## Workflow history
- 2026-10-02 graduated (aw backlog): status -> graduated
- 2026-10-01 created (aw backlog): Measured while authoring plan xvi55d (from backlog oev4h7); see the body for the full reproduction and cause

MEASURED AT HEAD ee1f2eff2 while authoring plan xvi55d (from backlog oev4h7), in a throwaway git repo driving the real CLI with PYTHONPATH pinned to the lane under test (ccbe60: a bare -m agent_workflows from a lane imports the MAIN checkout, so an unpinned measurement tests the wrong source; the resolved agent_workflows.__file__ was printed and verified to point into the lane before any measurement was taken).

THE MEASUREMENT, ON BOTH VERBS. A seeded plan was moved with a NEGATIVE order:

    aw group plans hhh888 --set negset --order -1 --rename --apply

It exited 0 with no warning and produced TWO distinct corruptions in one call.

FIRST, A DUPLICATE FRONT-MATTER FIELD. The resulting file carries '- Order: -1' TWICE: once at its original position and once appended after the '- Id:' line. 'aw ipd lint' on the result reports '! IPD-M102: Order: duplicate field'.

SECOND, A FILENAME OUTSIDE THE NAMING GRAMMAR. The file was renamed to '20260920-negset--1-hhh888-orch.ipd.md', with a DOUBLE hyphen where the two-digit NN cluster facet belongs. The uniform grammar is YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md and '-1' is not an NN.

'aw rename plans' DOES THE SAME THING: 'aw rename plans --id kkk555 --order -1 --apply' produced '20260920-probeset--1-kkk555-nokind.ipd.md' with two '- Order:' lines, exit 0.

THE CORRUPTION THEN COMPOUNDS ON REPAIR. A later 'aw rename plans --id hhh888 --order 0 --apply' on the already-corrupted file renamed it to '20260920-negset-00-hhh888-negset-1-orch.ipd.md', i.e. it mangled the broken cluster prefix INTO the slug. So the obvious repair makes the name worse.

THE CAUSE, read rather than inferred. plans_refs._ORDER_LINE_RE is compiled as r"(?m)^- Order:\s*(\d+)\s*$". The \d+ character class cannot match a leading minus, so for a negative value plans_refs._set_metadata's substitution branch finds nothing; its guard 'if _SET_LINE_RE.search(text) and _ORDER_LINE_RE.search(text): return text' is therefore False, and control falls through to the INSERTION branch, which appends a second '- Order:' line after the '- Id:' anchor. The same regex is the reason _preserved_order cannot read a negative Order either. The filename half comes from the name builder formatting the order into the NN facet without validating its range.

THIS IS INDEPENDENT OF THE KIND-CONDITIONAL ORDER RULE, which is why it was filed rather than absorbed into xvi55d. That plan makes the two verbs consult ipd_schema's kind-conditional rule, which refuses a 'Kind: orchestrator' at any nonzero order and a 'Kind: child' below 1, so it INCIDENTALLY catches a negative order on a plan that declares a Kind. It does NOT catch the corruption itself: a plan carrying NO '- Kind:' line at all is silent under that rule (validate_metadata reads kind = fields.get('Kind') with no default, and 102 plans in this tree carry no such line), and the measurement above on the Kind-less plan kkk555 corrupts with nothing to stop it. Relying on xvi55d's refusal would be a false claim of coverage.

WHY 'bug' RATHER THAN 'followup'. The command exits 0 and reports success while writing an artifact that violates two separate contracts it is the sole owner of: the front-matter field grammar (IPD-M102 duplicate field) and the uniform filename grammar. That is a wrong outcome, not a slow one, and it is silent, so an operator has no signal until a later lint or a reader trips over the name. The accidental path is narrow (an operator must type a negative --order), which is why it is 'low' priority, not why it is not a bug.

IF BUILT, the fix is in plans_refs and has two halves that should land together. (1) VALIDATE THE RANGE AT BOTH WRITE SITES and refuse a negative resolved order with exit 2, nothing written, in the same shape the kind-conditional refusal uses: an Order is a non-negative integer by the grammar's own construction, independent of Kind, so this refusal is unconditional and must fire on a Kind-less plan too. Evaluate the RESOLVED order per plan, never the flag, for the same reason xvi55d does: plan_set_assign computes order = start_order + i per named plan, so position matters. (2) MAKE _ORDER_LINE_RE's FAILURE MODE SAFE rather than silent, because a regex that cannot match the value it is about to write is a trap for the next change too: either widen it to r"-?\d+" so the substitution branch is reached and the duplicate cannot be created, or make _set_metadata assert that it either substituted or inserted but never both. Widening alone would still write an out-of-grammar filename, so it does not substitute for (1).

TWO EXISTING PLANS ARE ADJACENT AND NEITHER COVERS THIS: qhcojn (approved, from r30nnz) closes the child half of the kind rule at these same two write sites, and xvi55d (to-review, from oev4h7) closes the orchestrator half. Read this item after those execute, since the refusal built here sits beside theirs.

THE CORPUS IS CLEAN, so this is preventive and nothing needs repair. Measured over all 1135 .ipd.md files under .aw/records/plans/**: zero carry a negative '- Order:' and zero have a filename whose cluster facet is not two digits. Re-measure before acting; this is a shared checkout.
