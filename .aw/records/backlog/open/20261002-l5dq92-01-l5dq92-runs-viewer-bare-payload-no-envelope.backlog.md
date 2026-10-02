- Id: l5dq92
- Status: open
- Blocks-Release: next
- Set: l5dq92
- Priority: low
- Work-Kind: bug
- Summary: aw runs and aw runs list emit the bare payload {"runs": []} under --agent with no aw.agent/v1 record

## Workflow history
- 2026-10-02 created (aw backlog): aw runs and aw runs list emit the bare payload {"runs": []} under --agent with no aw.agent/v1 record

Measured in lane lbbo9s at HEAD b8e1e0157 while authoring plan 7pnneh (from backlog lbbo9s), which fixed the sibling defect on `aw upgrade-test` and declined this one because it has a different fix site.

THE DEFECT. `python3 -m agent_workflows runs --agent` exits 0 printing exactly `{"runs": []}`, which is NOT an `aw.agent/v1` record: it has no `schema`, no `kind`, no `outcome` and no `exit` field. The declared leaf twin `aw runs list --agent` prints the IDENTICAL bare payload, and `--json` prints the same object pretty-printed. So a caller that parses stdout as JSONL and reads the terminal record finds none, and the exit-parity rule in `docs/cli-output-contract.md` Section 4 (a record embedded `exit` must equal the process exit code) has no record to apply to.

THE SITE is `run_viewer`s empty-state branch, which builds `payload: dict[str, Any] = {"runs": []}`, optionally adds `excluded_runs`, prints `json.dumps(...)` and returns 0. A comment two screens above it in the same module already records that this empty state USED to be the machine branch and that "the machine branch is the one automation actually reads", which is the reasoning this item extends.

WHY IT NEEDS ITS OWN ITEM rather than being folded into the upgrade-test fix. (1) The bare root `aw runs` is deliberately UNDECLARED in `command_surface.COMMAND_INVENTORY` (a family root is never a parser leaf), and the inventory comment states its contract is "carried by `runs list`, its identical alias, which IS a leaf". So the two spellings must be decided TOGETHER, and the decision lands on a declared leaf, not on a dispatch branch. (2) `runs list` is declared `agent_record_kind="summary"` with a 17-member `legacy_flags` tuple, so changing its emit shape touches the run-execution family contract. (3) `docs/cli-output-contract.md` Section 3 explicitly scopes that family out: it notes that "commands in the run-execution family (`aw run` and `aw runs`) carry a separate, wider exit vocabulary documented alongside those verbs, and reconciling that separate vocabulary with the three-state classification is outside the scope of this section". That reconciliation is part of what this item must decide.

WHAT TO DECIDE, not just what to change: whether the empty state becomes a `result`/`summary` record with `outcome: clean` and a zero count (the shape 16 other family roots use for a clean empty answer), and whether `runs list` keeps `agent_record_kind="summary"` or moves to `result`. Note that `aw runs --agent` returning a CLEAN EMPTY answer at exit 0 is CORRECT behavior per Section (standing questions about repository state are not refused); only the ENVELOPE is wrong, so this is not a change to the exit code.

NOT COVERED BY ANY EXISTING SWEEP: `runs list` is not in `tests/test_agent_surface_conformance.py` UNIVERSE (it is declared `summary`, and the universe predicate keeps only `result`), and the bare root is not a leaf, so neither spelling is driven by the existing conformance harness. No `EXEMPTION_REGISTRY` entry covers either.
