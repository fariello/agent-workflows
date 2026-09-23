- Id: vfmklc
- Status: open
- Set: promptid6
- Priority: low
- Work-Kind: chore
- Summary: Mass-rename the 17 grandfathered legacy-named prompts to the id6-clustered grammar

## Workflow history
- 2026-09-23 created (aw backlog): Mass-rename the 17 grandfathered legacy-named prompts to the id6-clustered grammar

DEFERRED BY IPD ubac5n (promptid6), which adopted the clustered grammar GOING FORWARD and grandfathered the existing corpus rather than renaming it.

CURRENT STATE, measured 2026-09-23: 16 of the 17 tracked prompts carry a legacy YYYYMMDD-HHMM-NN-<slug>.prompt.md name and therefore have NO id6, so none of them is resolvable by aw find or citable from the research report it produced. They are VALID (cutovers.prompt_id6 = 2026-09-21 grandfathers every one) and aw check prompts reports zero findings, so this is a capability gap, not a conformance failure.

THE TOOL ALREADY EXISTS, one file at a time: 'aw rename prompts <legacy-name> --to-id6 --apply' mints the id6, writes it into the single <!-- aw-prompt: ... --> comment, and rewrites inbound citations. ubac5n E-04 repaired that path (it previously injected a '- Id:' bullet into the prompt body).

WHY ubac5n DEFERRED IT: a bulk rename of tracked files with live citations is its own change with its own reference-updating risk, and the same precedent (ha55fi) left 24 legacy specs in place for the same reason.

TWO THINGS TO KNOW BEFORE DOING IT. FIRST, 6 of the 17 prompts have NO leading metadata comment, and the converter deliberately does NOT mint one (a new line above the body would violate prompt-purity-lint R1/P4), so those get their id6 in the FILENAME only; decide whether that is acceptable or whether those files should gain a comment first. SECOND, several prompts are CITED from plans in .aw/records/plans/executed/, and converting one rewrites that citation, which edits a file in executed/; that is legitimate reference-rewriting rather than adding commits to a finished plan, but it must be stated explicitly in the change.
