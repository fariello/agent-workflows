- Id: 2cnvh1
- Status: done
- Graduated-To: 2cnvh1
- Blocks-Release: next
- Set: 2cnvh1
- Priority: medium
- Work-Kind: bug
- Summary: aw check's CLI overwrites every finding's structured recovery with doctor's human fix string, so a rule that populates no recovery gets a fabricated one in the machine record

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw oc run: IPD wef7yo executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-2cnvh1-01-wef7yo-stop-the-check-cli-overwriting-a-finding-s-structured-recove.ipd.md); evidence .aw/records/plans/executed/20260929-2cnvh1-01-wef7yo-stop-the-check-cli-overwriting-a-finding-s-structured-recove.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: wef7yo
- 2026-09-28 created (aw backlog): filed as the declared carrier for the residue IPD iyilwm (backlog evwmm2) deliberately leaves out of scope

FOUND 2026-09-28 while authoring IPD `iyilwm` from backlog `evwmm2`. That item reports the HUMAN
surface discarding a finding's structured `recovery`, and asserts the machine record "carries it
verbatim". THE SECOND HALF IS FALSE at HEAD `4873a82a`, and this item carries the half `iyilwm`
does not fix.

WHAT IS WRONG. `cli._run_check` computes the HUMAN remediation string first
(`doctor._categorize_drift`, whose 5th return value is `build_remediation(...).detailed_fix`) and
then writes it INTO the finding's recovery field: `enriched = ce.enrich_drift(d, recovery=fix or "")`.
Because `enrich_drift` fills `recovery=recovery or drift.recovery`, a NON-EMPTY `fix` WINS over the
rule's own value. `finding_dict` then serializes that string as `recovery`.

MEASURED at HEAD `4873a82a` on this repository's own tree, `aw check all --json`, all five
`data.policy_findings[*].recovery` values:

    check.ipd-uncarried-obligation      -> 'inspect .aw/records/plans/pending/<...>.ipd.md frontmatter and schema conformity.'
    check.ipd-carrier-finished-unverified -> 'inspect .aw/records/plans/pending/<...>.ipd.md frontmatter and schema conformity.'
    check.system-layout-missing         -> 'inspect .aw/system/layout.json frontmatter and schema conformity.'

while `check_system_layout` populates that finding's recovery as
"run 'aw install <root>' to regenerate the emitted layout document". The `--agent` surface shows the
same string as its top-level `next`, and `aw check all --json` `next_actions` lists all five as
`command` values, so a prose sentence is presented where a runnable command belongs.

WHY THIS IS SEPARATE FROM `evwmm2`. `iyilwm` fixes `build_remediation` to PREFER `drift.recovery`
over the generic fallback. That incidentally repairs this path for every rule that POPULATES
recovery (verified in-memory while authoring: with the fix staged, the re-enriched value is
byte-identical to the engine's). What it does NOT repair is a rule with an EMPTY engine recovery: the
human fallback string is still written into the machine record, fabricating a recovery the rule never
authored. Reproduced with `check.ipd-uncarried-obligation` (engine recovery `''`), whose agent record
reads 'inspect a/b.ipd.md frontmatter and schema conformity.'

SUGGESTED FIX. Stop assigning the human string to `recovery` in `cli._run_check`. The human `Fix:`
already travels in `Diagnostic.fix`, which is the field the renderer reads, so the assignment buys
nothing and costs the field its meaning. Either call `ce.enrich_drift(d)` with no recovery kwarg, or
pass `recovery=d.recovery`. Then decide separately whether `next_actions` should carry a recovery
string at all, given that 8 of 22 recovery literals in `check_engine.py` contain `<placeholder>`
segments and are not runnable as printed.
