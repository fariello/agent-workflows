- Id: zftbta
- Status: done
- Graduated-To: zftbta
- Blocks-Release: next
- Set: zftbta
- Priority: low
- Work-Kind: bug
- Summary: aw rename leaves 44 record citations dangling in agent_workflows source, so a maintainer keeps hand-fixing the shipped package after every rename

## Workflow history
- 2026-09-30 set (aw backlog): closed by aw oc run: IPD 68hdic executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.ipd.md); evidence .aw/records/plans/executed/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 68hdic
- 2026-09-26 created (aw backlog): aw rename leaves 44 record citations dangling in agent_workflows source, so a maintainer keeps hand-fixing the shipped package after every rename

FOUND 2026-09-26 during /plan-review of plan 5xzld0 (renamescan Order 01). That plan fixes the citation rewriter to reach .aw/records/reviews/ and tests/, which is what its carrier item 7oql4z asked for. The same defect class extends to PRODUCTION SOURCE, which 5xzld0 deliberately leaves out of scope, so this item carries the remainder.

MEASURED AT REVIEW. 44 citations of real record filenames or legacy YYYYMMDD-HHMM-NN prefixes live in agent_workflows/*.py. Examples, each a real record that exists today:
  - attention_contract.py cites 20260808-1945-01-attention-registry-and-cross-tree-status.spec.md (FULL filename)
  - ipd_schema.py cites 20260802-1904-01-ipd-structure-and-linting.spec.md (FULL filename)
  - check_engine.py cites 20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md and 20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
  - install_wizard.py, project_context.py, project_layout.py, project_registry.py, project_schema.py, record_producers.py and storage.py all cite physical-layout spec filenames
  - engine.py, layout_inventory.py, cli.py, backlog.py, specs.py and others cite legacy prefixes such as 20260817-2124-01 and 20260818-1525-02

CORROBORATION FROM THE MAINTAINER'S OWN HAND-FIX. Commit d6b2fa00 ('records: rename specs 25kzda and 5tapom onto the id6 grammar') lists, among the things the tool did not cover and that had to be fixed by hand: 'two spec handles in runner_shared.py comments'. So this has already cost manual work at least once, in exactly the way the reviews/ omission did.

WHY IT WAS NOT FOLDED INTO 5xzld0. Rewriting the shipped package from a records rename is a materially higher-risk operation than rewriting tests/ or reviews/: a bad substitution in agent_workflows/*.py changes runtime behavior rather than a document, and none of these modules is in that plan's Scope-Paths. It deserves its own risk assessment.

FIX DIRECTION (not decided). Most likely a third scan list (agent_workflows/, .py only) applied to reference rewriting with the SAME protections 5xzld0 builds: fenced-code masking, short-handle mapping, and the shared-legacy-prefix skip. Worth deciding explicitly whether it should ask for confirmation as 5xzld0 does for tests/, since the blast radius is larger. A cheaper alternative worth considering first: a CHECK that reports a dangling record citation in source rather than rewriting it, which surfaces the rot without the rewrite risk.

BLOCKS-RELEASE: carries the gate as a bug (the user-visible cost is that the shipped package accumulates citations of files that no longer exist, and a maintainer discovers them by hand).
