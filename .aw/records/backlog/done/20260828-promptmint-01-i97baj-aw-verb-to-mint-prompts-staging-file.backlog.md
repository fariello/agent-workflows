- Id: i97baj
- Status: done
- Blocks-Release: next
- Set: promptmint
- Priority: high
- Work-Kind: chore
- Summary: Add an aw verb to mint a conforming prompts/ staging-lane file (YYYYMMDD-HHMM-NN-<slug>.prompt.md + aw-prompt metadata) so the /aw research producer workflow does not hand-name/hand-write staged prompt files

## Workflow history
- 2026-09-01 done (aw set): Design shipped: plan jxqdcw is executed (From-Backlog: i97baj). Verified on main: 'aw prompts' is a registered command surface.
- 2026-08-30 graduated (aw set): design handed off to plan jxqdcw (promptmint-01, to-review, carries From-Backlog: i97baj and Blocks-Release: next); gate preserved via handoff. The item's OPEN DESIGN QUESTION (aw prompt noun vs extending aw research) is RESOLVED from repo evidence, no maintainer decision needed: the APPROVED prompt-purity spec already establishes the 'aw prompts <verb>' namespace by name, and prompts is already a registered artifact type with a prompt facet and rename/group backends missing only 'new'. Also measured two facts the item did not record: the metadata drift is already real (only 7 of 13 executed prompts carry the aw-prompt comment), and the documented filename grammar is self-contradictory three ways.
- 2026-08-28 open (aw set): Mark as a 2.0.0 (next) release blocker: every /aw research run currently produces an untooled, non-conformant staged prompt (hand-named + hand-written metadata); the mint verb should exist before ship.
- 2026-08-28 open (aw set): Reclassify blocked->open: this is actionable now (no external blocker). The verb-naming/home question is design work WITHIN the item, not a typed external gate; the earlier decision Gate-Ref was invalid (decision refs must match ^D\d+$). Corrects an AGENTS.md-nonconformant blocked state.
- 2026-08-28 created (aw backlog): Add an aw verb to mint a conforming prompts/ staging-lane file (YYYYMMDD-HHMM-NN-<slug>.prompt.md + aw-prompt metadata) so the /aw research producer workflow does not hand-name/hand-write staged prompt files

GAP: There is no 'aw' verb that creates a conforming file in the operational prompt STAGING lane .aw/records/prompts/pending/. 'aw research new' creates a durable research DOCUMENT under .aw/records/research/ (the results home, research grammar with <id6>), which is a DIFFERENT home (see .aw/records/prompts/README.md, 'the prompt -> results convention'). The staging lane wants YYYYMMDD-HHMM-NN-<slug>.prompt.md with a leading '<!-- aw-prompt: Kind: research | Status: pending | ... -->' metadata comment (see .aw/system/workflows/research-prompt/research-prompt.md Step 3-4 and .aw/records/prompts/README.md naming).

IMPACT: The /aw research producer workflow (research-prompt.md) instructs the agent to HAND-NAME the file and HAND-WRITE the front-matter/metadata, which violates the house rule 'use aw verbs to create conforming artifacts; do not hand-name or hand-maintain files'. Every research-prompt run currently creates an untooled artifact.

DESIRED: an 'aw' verb (candidate: 'aw prompt new --kind research --slug ... [--targets ... --concerns ... --status pending]') that (a) computes the YYYYMMDD-HHMM-NN sequence for the minute, (b) writes the leading aw-prompt HTML-comment metadata line, (c) lands the file in .aw/records/prompts/pending/ with Status: pending, (d) is dry-run by default with --apply (mirroring 'aw backlog new'/'aw research new'), and (e) does NOT auto-stage/commit. Consider whether this unifies under 'aw research' or is its own 'aw prompt' noun (the two homes are deliberately distinct per the prompts README). Update research-prompt.md Step 4 to call the verb instead of hand-writing.

OPEN DESIGN QUESTION (resolve during execution, not an external gate): the verb naming and home - a standalone 'aw prompt new' noun vs. extending 'aw research' - given the two prompt homes (.aw/records/prompts/ staging vs .aw/records/research/ results) are deliberately distinct per the prompts README.

DISCOVERED: while running /aw research to produce a research prompt about a user-extensible workflow-step mechanism; there was no aw verb to tool the staged-prompt file creation.
