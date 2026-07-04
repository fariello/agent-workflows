# IPD: Toolkit discovery (`/list`) and version stamping

- Date: 2026-07-04
- Concern: usability / discoverability (of both capabilities and installed state)
- Scope: a new discovery workflow generated from the manifest; a framework version
  marker; a `--version` on the tools. No change to existing workflow behavior.
- Status: PENDING (proposal for human approval; not executed)

## Goal

Let a user (or agent) answer, in-agent, "what can this toolkit do, and which version is
installed here?" without reading `index.md` by hand. This is the companion to the
parameterized `/assess <thing>` (IPD 1): it is how you discover the `<thing>` values.

## Why

- There is no in-agent capability listing today; discovery means manually reading the
  manifest. This gets worse once concerns collapse behind `/assess <thing>` (IPD 1),
  because per-concern menu autocomplete goes away.
- Installed copies carry no version, so neither a user nor `setup-repo`'s conformance
  check can say "this repo has framework vX; the source is vY, you are behind."

## Proposed design

1. **A `/list` (or `/toolkit`, `/workflows`) discovery workflow** that reads
   `.agents/workflows/index.md` (the manifest, single source of truth) and presents:
   the core workflows, the assess concerns (grouped), and the advise personas (once IPD
   4 exists), each with its one-line description and how to run it per tool. Optional
   argument to filter/describe one item (`/list security`, `/list assess`).
   - Generated FROM the manifest so it never drifts; do not hand-maintain a second list.
2. **Version stamping:** add a `VERSION` (or a field in the manifest / a
   `.agents/workflows/VERSION`) that the installer stamps. On install into a target,
   record the installed version so `setup-repo` (D26 conformance) and `/list` can report
   "installed vX". Decide the version scheme (date-based `YYYY.MM.DD`, or semver).
3. **`--version` on the tools:** `install-workflows.py --version` and
   `scan_secrets.py --version` print the framework/tool version. Small, self-documenting.

## Scope check

- Over-scope: no package registry, no auto-update mechanism, no telemetry. Just
  listing + a version string.
- Under-scope: discoverability is the point; ensure `/list` output is genuinely usable
  (grouped, with run instructions), not a raw dump.

## Dependencies / sequencing

- Should ship with or before **IPD 1** (it restores the discoverability IPD 1 removes).
- Version stamping composes with `setup-repo`'s conformance check (D26) - version-aware
  drift detection is a natural follow-on.

## Required validation

- `/list` output matches the manifest exactly (no drift); filtering one item works;
  cross-tool run instructions are correct.
- Installer stamps a version; `--version` prints it; a target repo can report its
  installed version.

## Open questions

1. Command name: `/list`, `/toolkit`, or `/workflows`? (`/list` is short; `/toolkit`
   is unambiguous.)
2. Version scheme: date-based (`2026.07.04`) vs. semver. Date-based fits a
   continuously-evolving instruction set; semver implies compatibility contracts we do
   not really make.
3. Where the version lives: a dedicated `VERSION` file, a manifest header field, or
   both (file for tooling, header for humans).

## Approval and execution gate

Proposal only. Low risk, high usability value; a good early build. Approve/reorder
before execution.
