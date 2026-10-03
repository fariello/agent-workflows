- Id: o7wwop
- Status: open
- Set: o7wwop
- Priority: low
- Work-Kind: followup
- Summary: no conformance gate asserts that every CLI family root emits a schema-valid agent record under --agent

## Workflow history
- 2026-10-02 created (aw backlog): no conformance gate asserts that every CLI family root emits a schema-valid agent record under --agent

Measured in lane lbbo9s at HEAD b8e1e0157 while authoring plan 7pnneh (from backlog lbbo9s).

THE GAP. The CLI parser tree has 22 nodes carrying an `_SubParsersAction` (family roots): `agy`, `agy profile`, `backlog`, `config`, `config exclude`, `host`, `ipd`, `ipd dependencies`, `oc`, `oc profile`, `project`, `prompts`, `releases`, `research`, `reviews`, `run`, `runs`, `specs`, `storage`, `upgrade-test`, `work`, `workflow`. NOT ONE of them is driven by any conformance sweep, because every existing sweep draws its universe from `command_surface.discover_parser_leaves`, and that function only yields a parser with NO subparsers, so a family root is never a leaf by construction. `tests/test_agent_surface_conformance.py` UNIVERSE (42 members) contains none of the 22.

WHY IT MATTERS, with the measurement that makes it concrete rather than theoretical. Driving all 22 roots with `--agent` and validating the terminal record found 19 conforming and THREE not: `upgrade-test` printed a 39-line argparse usage block (filed as `lbbo9s`, fixed by plan `7pnneh`), `runs` prints the bare non-envelope payload `{"runs": []}`, and `config exclude` prints the human status line `FAIL     Usage: aw config exclude {add|list|rm} ...` to stdout. Three defects of one shape, in a population nothing gates. A bare invocation is a COMMON way for an agent to probe a verb, so these are machine surfaces in practice.

THE GATE SHOULD ASSERT the same four properties the existing read-surface sweep applies, plus the two that make a record actionable: non-empty stdout; a terminal `result`/`summary`/`error` record parses from stdout; `agent_schema.validate_agent_record` returns `[]`; the record `exit` equals the process exit code; and (for a root with no default view) `outcome == "cannot-run"` with a `next` field present. Note the correct expectation is NOT uniform: `ipd` and `releases` legitimately exit 0, because they dispatch a bare invocation to a default view (their records read `cmd: "ipd board"` and `cmd: "releases list"`), so the gate must accept a clean exit-0 record as conforming and only require the refusal shape where no default view exists.

FEASIBILITY IS MEASURED: a subprocess sweep over all 22 roots took 28.93 seconds wall (about 0.5s per root), which is well inside the repository per-test hang budget and needs no `slow` marker. A root census can be computed by recursing the parser for nodes that HAVE an `_SubParsersAction`, which is a small inversion of the existing `discover_parser_leaves` walk and belongs beside it.

WHY IT IS FILED AS `followup` AND NOT `bug`: this is MISSING COVERAGE, not a user-visible defect. The three defects it would have caught are each filed on their own merits. Per the repository perceptibility test, an absent test is not itself something a user can notice, so it does not carry a release gate.

SEQUENCING, which is the one thing that must not be missed: this gate CANNOT be added green today. It would be RED on `runs` and on `config exclude`, both of which have their own open items. So it should land AFTER those two are fixed, or land with an exemption registry entry per outstanding root citing those item ids (the pattern `tests/conformance_matrix.EXEMPTION_REGISTRY` already uses, whose own module comment warns that adding an entry to silence a red sweep is the prohibited failure mode, so entries must cite a live item and be deleted by its executor). Also check first whether pending plan `gm9baj` behavioral `COMMAND_INVENTORY` gate has landed, since it occupies the same test module and a second root-sweep should be designed against whatever it lands rather than racing it.
