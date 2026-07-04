# IPD: Command-surface redesign (`/assess <thing>`, `/advise <persona>`)

- Date: 2026-07-04
- Concern: usability / command sprawl (the toolkit has 34 commands and is growing)
- Scope: how workflows are exposed as commands; the installer's shim generation; the
  manifest format. Does NOT change any workflow's behavior/content.
- Status: PENDING (proposal for human approval; not executed)

## Goal

Cap the top-level command surface as concerns and personas grow, without losing
capability. Collapse the 28 `/assess-<concern>` commands into a single parameterized
`/assess <thing>`, and (paired with the future `advise` workflow, IPD 4) `/advise
<persona>`. Keep genuinely distinct workflows (release-review, plan-review, setup-repo,
scaffold, and future verify/list/etc.) as their own commands.

## Why

- 34 commands today, heading well past 100 if every concern and every future expert
  persona is its own command. That is unusable in a slash-command menu and violates
  KISS.
- The `assess` family already shares one body (the harness) selected by a lens; a
  parameterized command matches that architecture exactly.
- Argument-carrying commands work in OpenCode and Claude Code (`$ARGUMENTS`); tools
  without native commands use the read-and-execute fallback either way.

## Proposed design

1. **`/assess <thing>`**: one command; the argument names the concern (lens). The shim
   passes the argument to the harness, which resolves it to `assess/lenses/<thing>.md`.
   Examples: `/assess security`, `/assess prose`, `/assess compliance-readiness nist-800-171`
   (extra args flow through as scope/options).
2. **Bare invocation is an interactive picker.** `/assess` with no argument lists the
   available concerns (from the manifest) and asks which to run. This turns "must know
   the arg" into guided discovery and pairs with the harness's existing "if no lens,
   ask the user" behavior.
3. **Argument aliases / fuzzy match:** accept common short forms (`a11y` ->
   accessibility, `perf` -> performance, `deps`/`supply` -> supply-chain). Resolve
   case-insensitively; on an unknown value, show the closest matches and the picker.
4. **Manifest change:** the manifest gains a way to mark a workflow as "parameterized
   over a set" (the assess concerns), so the installer generates ONE `/assess` shim
   plus the catalog data, rather than one shim per concern. Concern lenses remain
   individually listed (they are the source of truth for the picker/catalog and for
   IPD 2's `/list`).
5. **Cross-tool behavior:** OpenCode/Claude Code get the native `/assess <thing>`;
   other agents use "read and execute the assess harness with lens `<thing>`". The
   `AGENTS.md` pointer and the catalog (IPD 2) preserve discoverability.

## The trade-off this accepts (and how it is mitigated)

Collapsing to one command **loses per-concern autocomplete** (typing `/assess-` no
longer enumerates 28 concerns in the menu). Mitigation: the bare-invocation picker
(step 2) and the `/list` catalog (IPD 2) restore discoverability better than a
28-entry menu did. This is the deliberate reason IPD 2 (discovery) should ship with or
before this one.

## Scope check

- Over-scope: do not redesign the core workflows' invocation or rename them; only the
  assess (and, via IPD 4, advise) families collapse.
- Under-scope: discoverability must not regress - hence the dependency on IPD 2.

## Dependencies / sequencing

- Pairs with **IPD 2 (discovery/`list`)** - ship together or IPD 2 first, so users can
  find the `<thing>` values.
- The `/advise <persona>` half depends on **IPD 4** (the advise workflow) existing.
- Requires an installer change (shim generation + manifest parsing). Backward
  compatibility: decide whether to KEEP the old `/assess-<concern>` shims for one
  transition period or remove them on install (open question).

## Required validation

- Installer generates exactly one `/assess` shim (per tool) plus the catalog; the
  harness resolves an arg (and an alias) to the right lens; bare invocation triggers
  the picker; an unknown arg shows suggestions.
- Cross-tool: native arg works in OpenCode/Claude Code; fallback wording is correct.
- README/index/`Running a workflow (by tool)` updated to the new surface.

## Open questions

1. Command word: `/assess <thing>` (keep the verb) - confirmed direction. Same pattern
   for `/advise <persona>`?
2. Transition: on install, remove the legacy `/assess-<concern>` shims immediately, or
   keep them for a deprecation period alongside `/assess`? (Removing is cleaner;
   keeping avoids breaking anyone's muscle memory briefly.)
3. Aliases: maintain a small curated alias map, or rely only on fuzzy matching?

## Approval and execution gate

Proposal only. Approve/reorder before execution. It changes the command surface and the
installer, so it should be plan-reviewed and ideally sequenced with IPD 2.
