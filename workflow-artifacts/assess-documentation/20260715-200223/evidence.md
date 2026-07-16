# Assess documentation - evidence (what was inspected)

Read-only. No files modified during the assessment (the IPD + this run record are the workflow's own
deliverables, not changes to the project under review).

## Files inspected

- CHANGELOG.md (full), DECISIONS.md (D44/D46/D51/D74/D75 versioning + D79-D84 this session),
  RELEASING.md, CONTRIBUTING.md (versioning + self-test list), `.agents/workflows/VERSION`.
- Executed IPDs: `.agents/plans/executed/20260715-{1502-01,1451-01,1033-01,1602-01}`,
  `.agents/plans/executed/20260712-1901-01`, `.agents/plans/executed/20260713-0034-01`,
  `.agents/plans/executed/20260713-1419-01` (their own MINOR/PATCH scoping statements).
- README.md, ARCHITECTURE.md, AGENTS.md, TODO.md, GUIDING_PRINCIPLES.md.
- `.agents/README.md`, `.agents/docs/README.md` + bucket READMEs, `.agents/plans/README.md`,
  `.agents/plans/STATUS.md`, `.agents/workflows/README.md`, `.opencode/commands/README.md`,
  `.claude/commands/README.md`.
- `agent_workflows/engine.py:576-582` (the generated "check your inbox" clause), `agent_workflows/`
  module list (comms.py, plans.py, pypi_links.py present).
- Retired draft spec `.agents/docs/specs/20260712-2133-02-...` (RETIRED header) vs canonical
  `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md`.

## Commands / checks run (coordinator re-verification of High findings)

- `grep` for D80/D81/D82 placement in CHANGELOG.md -> confirmed under `## 1.2.1 (pending)` (L27) while
  `## 1.3.0 (pending)` is L7 with only D83/D84.
- `grep` TODO.md -> confirmed "on trial ... gated ... would be its own IPD" (L51-52) + retired-draft
  citations (L27,L47).
- `grep -c` "check your inbox"/"Inter-agent comms" in AGENTS.md -> 0 (clause absent from this repo's block).
- STATUS.md counts (Total 46 / pending 3 / executed 42) vs reality: `ls .agents/plans/pending/*.md`
  (excl README) = 0; `ls .agents/plans/executed/*.md` = 60.
- Counts spot-checked by lane 2: 18 command shims per side, 255 tests pass, latest D84, tag v1.2.0,
  VERSION 1.2.1, 17 workflow dirs + templates/. em/en dash scan across authored docs = 0 violations.

## Sampling / truncation notes

- DECISIONS.md is large (2100+ lines); lanes read the versioning entries and the D79-D84 range in full
  rather than the entire history. CHANGELOG, TODO, and the top-level docs were read in full.
