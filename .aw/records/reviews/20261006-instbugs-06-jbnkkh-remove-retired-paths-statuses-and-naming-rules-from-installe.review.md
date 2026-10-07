# Review findings: plan jbnkkh

- Subject-Id: jbnkkh
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `62409e724` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`). Plan committed and byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author
--agent` clean (advisories only) before semantic review; `aw ipd lint --phase review-finalize --agent` clean (advisory
`IPD-Z602` only) after revisions; `check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (scratch repo under the temp dir, `AW_NO_REEXEC=1`, temp `HOME`):
- Fresh `aw install --preset private-target -y --no-interactive`, `grep -rnoE '\.agents/(plans|prompts|comms|docs|workflows)'`
  over log, `.gitignore`, `.aw/.gitignore`, `.aw/records`: log:22 lanes (x2), log:438 `.agents/workflows/index.md`,
  `.gitignore:10` (x2), `.gitignore:23`, `.aw/records/comms/README.md:1` and `:52`. Matches the plan's inventory.
- Upgrade: committed, appended `# stale marker` to the research README, re-installed: `[no change]
  .aw/records/research/README.md`, `[no change] .aw/records/specs/README.md`, specs README md5 unchanged, marker still
  present (F-07).
- `diff` of the research template vs this repository's `.aw/records/research/README.md`: the repo copy already reads
  `| \`todo\` (legacy \`intake\`) |`, "Hot states (`todo`/`active`)", monthly `YYYYMM` shards (F-08).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / goal coverage | F-07 upgrade probe; `engine.ensure_docs_readmes` `if readme_path.is_file(): skipped.append(...)`; `engine._create_if_absent` | Every README fix reached NEW installs only; existing installs (the reporting user's case) keep the stale research, specs and comms READMEs forever. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-06/V-06: known-stale hash census and backed-up overwrite mirroring `xqf71x` (`RETIRED_RECORDS_ROOT_README_HASHES`, `classify_records_root_readme`); user-edited copies preserved; E-05(c)(d) test both. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / reuse | template-vs-repo `diff`; `research_archive` "monthly `YYYYMM`" | E-02 hand-patched `intake` but the template is stale on more than that (weekly shard text, missing pipeline-position axis, setid bounds); the corrected text already exists in this repository. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 syncs from `.aw/records/research/README.md`, then makes it target-correct; V-02 checks shard text and that no `specs/` citation remains. |
| PR-003 | LOW | UNDER-SCOPE | Honest documentation | `.aw/records/specs/README.md` "Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time)." | This repository's own specs README carries the same stale naming line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 edits that paragraph too; path added to Scope-Paths. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability | `cli._orient` "Or from any agent: 'Read and execute .agents/workflows/index.md'"; `InstallPlan` has no layout field | E-04 assumed a `target_layout` value reaches the print helpers; it does not, and `_orient` runs once per multi-repo `aw setup`, so a per-target path is not well defined there. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names each source symbol, uses `resolve_target_layout(plan.repo_root)`, parameterizes the comms template and untracked block, and makes `_orient` layout-neutral. |
| PR-005 | LOW | IN-SCOPE | Scope clarity | installed `.aw/system/**` bundle | The scan excludes the installed workflow bundle without saying so or naming who owns its `.agents/` mentions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope OUT and the Deferred `ka0g86` row state it. |
| PR-006 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, and conditional finalize ownership (it said `aw ipd set executed` unconditionally). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Repair stale READMEs in existing installs? | Yes, only byte-known shipped texts, with backup | Leave existing installs stale; overwrite unconditionally | Executed precedent `xqf71x` (same problem, same mechanism) and its "missed hash costs a stale file, never a destroyed user file" direction | yes |
| D-2 | Add an `Item-Dependencies` edge on `xzlu9b` for the `.aw/inbox/` pointer? | No; noted in Scope check | Add the edge | The orchestrator `i99ykd` child table lists this plan as dependency-free, and the pointer is correct prose regardless | yes |
| D-3 | Make `cli._orient` layout-aware or neutral? | Neutral | Resolve layout of the first repo | It prints once after possibly many repos of mixed layout | yes |
