- Id: 2cqs11
- Status: open
- Set: runexitvocab
- Priority: medium
- Work-Kind: chore
- Summary: approved plan u28vqb E-05 directs a new docs/cli-output-contract.md section 3.1 that already exists (Severity Tier Contract), so the executor will collide or renumber a cross-referenced heading

## Workflow history
- 2026-10-02 created (aw backlog): found while graduating h9kgjp; affects an already-approved sibling plan

APPROVED plan `u28vqb` (Set `runexitvocab`, `- Status: approved`, so it is runnable unattended today) instructs its E-05 to document the run-execution exit vocabulary as "a new \`### 3.1\` subsection of \`docs/cli-output-contract.md\`", and its F-15 records that destination as DECIDED at review precisely so the executor would not have to invent it.

MEASURED AT HEAD: `### 3.1` IS ALREADY TAKEN. `docs/cli-output-contract.md` carries `### 3.1 Severity Tier Contract and Gate Semantics`, landed by executed plan `wm40yl` (commit subject 'Document the severity tier contract so warning is not mistaken for advisory, and pin the six consumers that enforce it'), which postdates `u28vqb`'s authoring and its review. The heading census under Section 3 is: `## 3. Exit Code Semantics`, then `### 3.1 Severity Tier Contract and Gate Semantics`, then its three `#### ` children.

WHY THIS MATTERS RATHER THAN BEING COSMETIC: an executor following E-05 literally has only bad options. It can add a SECOND `### 3.1` (two identical headings in one document, breaking the 'stable anchor' property F-15 gives as the whole reason for choosing that number), or it can RENUMBER the existing severity section to 3.2, which is a cross-referenced heading. Either way E-03 and E-04, which are required to 'point at the one place E-05 writes it', point at an ambiguous or moved anchor.

SECOND, SMALLER DRIFT IN THE SAME PLAN: `u28vqb`'s F-01 asserts that `rwvzqm` is 'in `.aw/records/plans/pending/`, NOT `executed/`' and that therefore 'Section 3 of the contract doc is UNAMENDED and still makes the bare claim', concluding this plan 'writes the FIRST honest statement rather than replacing a weaker one'. Both halves are now stale: `rwvzqm` is `executed`, and Section 3 ALREADY carries a scoping sentence it added ('Note that commands in the run-execution family (\`aw run\` and \`aw runs\`) carry a separate, wider exit vocabulary documented alongside those verbs, and reconciling that separate vocabulary ... is outside the scope of this section'). So E-03 is amending a surface that already has a partial acknowledgement, and the honest framing is 'complete and sharpen it', not 'write the first one'. `u28vqb` E-01 is already a re-measure-and-STOP gate, which is the right place for this to surface, but the destination decision needs a human or a corrective amendment rather than an executor improvising.

NOT FIXED BY THE h9kgjp GRADUATION that found it: that plan's whole scope is one module docstring in `agent_workflows/run_cli.py`, and editing an approved sibling plan's checklist is outside it. RECOMMENDED ACTION: pick the next free number (`### 3.2`) or a titled subsection, and refresh F-01, before `runexitvocab` is run.
