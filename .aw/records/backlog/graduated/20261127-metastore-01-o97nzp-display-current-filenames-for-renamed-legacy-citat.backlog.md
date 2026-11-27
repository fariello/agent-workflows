- Id: o97nzp
- Status: graduated
- Graduated-To: i7wzcf
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Display current filenames for renamed legacy citations in aw show --history (spec 4sd62s AC-41 case 4)
- Short-Description: Display current filenames for renamed legacy citations in aw show --history (spec 4sd62s AC-41 case 4)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 graduated (aw set): Graduated to review-ready IPD i7wzcf (Set o97nzp, depends on executed:0zylig) for spec 4sd62s AC-41 case 4.
- 2026-11-27 created (aw backlog): Display current filenames for renamed legacy citations in aw show --history (spec 4sd62s AC-41 case 4)

Spec 4sd62s AC-41 case 4 and OQ-28 require that every raw imported history line citing an old legacy-timestamp filename is recovered byte for byte and that `aw show --history` displays it with the current clustered filename. Plan `1ajqaa` E-02 deferred this display mapping to `dcerjg`, and `dcerjg` deferred it to `cxxmyv`, but neither `agent_workflows/meta_cli.py` (`render_history_human` / `show_history`), `agent_workflows/artifact_meta.py` (`history`), nor `.aw/system/cutover/metastore-code.cutover.patch` implements the display resolution. Implement current-name annotation in `aw show --history` (using `artifact_paths` / rename mappings) and add behavioral tests so AC-41 case 4 passes on migrated repositories.
