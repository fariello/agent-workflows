- Id: 9qya0k
- Status: open
- Set: 9qya0k
- Priority: low
- Work-Kind: chore
- Summary: docs/cli-agent-protocol.md Token control section says 'Two escape hatches' while its own surface has three

## Workflow history
- 2026-10-01 created (aw backlog): Filed while authoring plan c4btis (backlog qm04zi) as the carrier for a documentation wart that plan deliberately did not fix.

MEASURED 2026-10-01 while authoring plan `c4btis` from backlog item `qm04zi`.

`docs/cli-agent-protocol.md` opens its `## Token control` section with "Two escape hatches tune the token cost:" and then lists exactly two bullets, `--fields <a,b,c>` and `--verbose`. The count is wrong relative to the surface the repository actually ships and documents: `docs/cli-output-contract.md` `## 6. Token Control and Escape Hatches` lists THREE, naming `--fields`, `--limit` and `--verbose`, and `--limit` is a real declared flag (measured: 9 leaves accept it, including `check`, `find`, `search`, `index`, `rename`, `group`, `runs analyze`, `runs query` and `research index`).

So the agent-facing protocol reference under-counts its own token-control surface and omits the one escape hatch an agent most needs when a records query returns more than it can afford to read. A reader who takes the sentence literally concludes there is no way to bound output and pages through everything.

WHY THIS IS A CHORE AND NOT A BUG: nothing exits nonzero and no documented invocation fails. The omitted flag WORKS where it is honored, so this is a documentation completeness defect rather than a user-perceptible failure. Per AGENTS.md the gating work-kind set is `bug` alone, so this carries no release gate.

SUGGESTED FIX: correct the introductory count and add a `--limit` bullet to `docs/cli-agent-protocol.md` `## Token control`, matching the three-item list `docs/cli-output-contract.md` already carries. NOTE ONE CONSTRAINT: `--limit` is NOT uniformly honored. Backlog item `wdazvp` measures `aw find --agent --limit 20` accepting the flag, reaching the context, and then ignoring it because that command's bare-path branch returns before any record is built. So the bullet must describe `--limit` accurately rather than promising uniform behavior, or it should be written after `wdazvp` resolves. Related: `qm04zi` (the `--verbose` reach defect), `wdazvp` (`--limit` inert on `aw find --agent`), and executed plan `75ic2f` (the `--fields` reach fix).
