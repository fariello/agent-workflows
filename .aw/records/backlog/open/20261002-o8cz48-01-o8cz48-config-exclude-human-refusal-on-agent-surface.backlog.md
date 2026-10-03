- Id: o8cz48
- Status: open
- Blocks-Release: next
- Set: o8cz48
- Priority: low
- Work-Kind: bug
- Summary: aw config exclude with no subcommand prints a human FAIL status line to stdout under --agent instead of an aw.agent/v1 record

## Workflow history
- 2026-10-02 created (aw backlog): aw config exclude with no subcommand prints a human FAIL status line to stdout under --agent instead of an aw.agent/v1 record

Measured in lane lbbo9s at HEAD b8e1e0157 while authoring plan 7pnneh (from backlog lbbo9s), which fixed the sibling defect on `aw upgrade-test` and declined this one because it is one verb of a family that should be decided together.

THE DEFECT. `python3 -m agent_workflows config exclude --agent` exits 2 and writes the HUMAN status line `FAIL     Usage: aw config exclude {add|list|rm} ...` to STDOUT. `--json` writes the identical line. That is a human renderer string on a machine stream: not JSON at all, so a caller parsing stdout as JSONL gets a parse error rather than a refusal it can act on, and it carries no `outcome` a caller can branch on. It is also on STDOUT rather than stderr, so it pollutes the stream a script reads.

THE SITE is the `config exclude` handler in `agent_workflows/cli.py`, whose fall-through reads `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` followed by `return 2`. It does NOT call `cli._show_family_help`, which is the shared subcommand-less-group refusal that branches on `context.is_agent` and emits a `CommandResult(status="cannot-run", exit_code=2, ...)` with a `NextAction`.

THE SHAPE OF THE FIX is already shipped 18 times over. Driving all 22 family roots in the CLI with `--agent` measured 19 conforming (schema-valid terminal record, exit parity) and 3 not: `upgrade-test` (fixed by plan 7pnneh), `runs` (filed separately) and `config exclude`. Of the 19, 16 emit `{"kind":"error","outcome":"cannot-run","exit":2}` with a `next` field, which is exactly what this verb should emit. The likely fix is to route the fall-through through `_show_family_help(parser, "config exclude", "aw config exclude list", term, context)`; the next-action choice matters, and `list` is the only read-only one of the three subcommands.

WHY IT NEEDS ITS OWN ITEM rather than being folded into the upgrade-test fix: it is the FOURTH known `config`-family machine-surface defect, and the other three (`config show`, `config get`, `config is`) are already enumerated together in `tests/conformance_matrix.EXEMPTION_REGISTRY` as `known_broken`. Those three cite backlog `dtq6jr`, which is now DONE, so no live item covers this one. Repairing one `config` surface while its siblings are tracked elsewhere would split one family across two plans. The whole `config` family envelope should be decided in one pass.

NOTE ON THE SIBLING EXEMPTIONS: the three `dtq6jr` entries describe an ImportError crash (`cannot import name format_agent_json`), which is a DIFFERENT failure mode from this one (a human string on the machine stream). Whoever takes this item should re-measure all four `config` surfaces at that HEAD rather than assuming the registry text is current, and should delete any registry entry that has become stale.

NOT COVERED BY ANY EXISTING SWEEP: `config exclude` is a family root, so it is not a parser leaf and `tests/test_agent_surface_conformance.py` cannot reach it (its universe is drawn from `discover_parser_leaves`). Its declared leaf child `config exclude list` IS declared `agent_record_kind="result"` but is itself registry-exempted as `sanctioned_raw`.
