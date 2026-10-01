- Id: 6wd42q
- Status: open
- Set: 6wd42q
- Priority: low
- Work-Kind: chore
- Summary: Decide whether command_surface exit_contract is meant to enumerate signal-derived codes (130/143) at all

## Workflow history
- 2026-09-30 created (aw backlog): Decide whether command_surface exit_contract is meant to enumerate signal-derived codes (130/143) at all

`oc_runipd.main` and `agy_runipd.main` each return `143 if is_sigterm else 130` on the uncooperative-interrupt path, so both codes are OBSERVABLE on the two driver verbs. Neither appears in those verbs' `command_surface` `exit_contract`, and no declaration anywhere in the 163-entry inventory enumerates a signal-derived code, including the 155 that take the plain `(0, 1, 2)` default. THE QUESTION IS ABOUT THE FIELD'S MEANING, not about these two verbs: does `exit_contract` enumerate every integer the process can return, or only the codes produced by the command's own normal return path? Answering it one way obliges adding 130/143 to every verb that can be interrupted; answering it the other way obliges saying so, once, where the field is defined. FOUND BY plan u28vqb (OQ-03) while correcting those two declarations to admit the measured exit 3. u28vqb deliberately declared ONLY the code it measured reaching the process exit through the normal return path, and its E-02 states that limit explicitly so the omission is not mistaken for an oversight. Declaring 130/143 on two verbs alone would make the inventory inconsistent in a NEW way while claiming to fix an inconsistency. LOW RISK: the two declarations become more accurate either way, and adding the signal codes later is purely additive.
