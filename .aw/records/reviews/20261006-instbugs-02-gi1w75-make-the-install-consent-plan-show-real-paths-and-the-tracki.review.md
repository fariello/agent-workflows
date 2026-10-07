# Review findings: plan gi1w75

- Subject-Id: gi1w75
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `6d434f537` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`). Plan committed and byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author
--agent` clean before semantic review; `aw ipd lint --phase review-finalize --agent` clean (0 findings) after revisions;
`check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (scratch repos under the temp dir, `AW_NO_REEXEC=1`, temp `HOME` for real installs):
- `render_pre_write_plan` vs `resolve_project_context(...).physical_classes`, per preset: `private-target` prints
  `<R>/.aw/config_project`, `<R>/.aw/state_durable`, while the resolver returns `<R>/.aw/config/project.json`,
  `<R>/.aw/state/durable`; companion and home branches print `.../.aw/<cls>` paths the resolver does not return (F-07).
- Real `aw install --preset private-target -y --no-interactive`: `project.json` `state_durable` =
  `target-tracked target-git`; `.aw/state/durable/install.json` and a root `.aw/state/install.json` both written.
- Real `aw install --preset completely-clean-target -y --no-interactive`: target still received
  `.aw/config/local.json`, `.aw/config/project.json`, `.aw/state/durable/install.json` (F-08, backlog `mbx0o4`).
- Upgrade path: `project.json` seeded with `git_policies: {"state_durable": "untracked", "system": "untracked"}`;
  `resolve_existing_policy` -> `existing git_policies.state_durable = target-git`;
  `resolve_policy_noninteractive` -> `resolved git_policies.state_durable = target-git` (F-06).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness / C. duplicate paths | `project_context.resolve_project_context` "Git Policies calculation per physical class" `RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value if resolved_preset in (Preset.PRIVATE_TARGET.value, ...)`; `install_wizard.get_preset_defaults` `else:` "Default fallback for custom" | E-03 named two of four sites emitting `state_durable: target-git`; the resolver's `git_policies` and the `custom` branch would keep reporting tracked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 covers all sites; `project_context.py` in Scope-Paths; V-03 and E-05(a2) demand the resolver value. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness (mechanism) | `install_wizard.resolve_existing_policy` builds `ProjectPolicy(...)` without placements/git_policies; probe above | E-04 assumed an upgrade loads and preserves the stored `state_durable`; it does not, so a "rewrite on upgrade" path would be dead code. The real gap is only the announcement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten to announce, before `persist_project_policy`, when the stored value differs; no new rewrite path. |
| PR-003 | HIGH | UNDER-SCOPE | Spec sync | spec `20260810-1447-01` Section 6 `private-target` row "Durable state: target tracked"; Section 3 rows "MAY be tracked according to policy" | Spec sync was conditional ("if it tabulates ... N/A"); it does tabulate it, so E-03 contradicts an implemented spec without an amendment, and the spec was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 amend Sections 6 and 3 via edit plus `aw specs note`; spec added to Scope-Paths; WHY stated. |
| PR-004 | MEDIUM | IN-SCOPE | A/F. Correctness, silent failure | `render_pre_write_plan` `except Exception: resolved_roots = {}` then the overwrite loop; resolver call omits `companion_dir`; `ctx.logical_roots` fallback | E-02 left the invented-path fallback on resolver failure implicit, did not pass the policy's companion dir (records path defaults to `<repo>.aw/records`), and its outcome was unverifiable for non-target presets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 specifies all three; outcome is "printed path equals resolver path" for every preset; V-02 adds the companion comparison. |
| PR-005 | HIGH | UNDER-SCOPE | Scope / honest documentation | F-08 scratch install; `persist_project_policy` `config_dir = p_repo / ".aw" / "config"` | Clean-delta presets write config and state into the target despite "ZERO AW-owned target files"; after E-02 the consent plan will print home paths the install ignores. Not owned by this plan or any sibling. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Filed backlog `mbx0o4` (bug, `Blocks-Release: next`); recorded as a carried Deferred row and in Scope OUT. |
| PR-006 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked resolved-OQ statement, explicit honesty rule, scope fence as declaration, temp-HOME safety for real installs, and conditional finalize ownership (it said `aw ipd set executed` unconditionally). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Ratify changing the emitted `state_durable` from `target-git` to `ignored` (OQ-01)? | Ratify | Option (b) of `2812t3`: strip `aw_home` and genuinely track durable state | backlog `2812t3` "Remaining divergence" names option (a) as honest and asks for its own plan; maintainer ruling 2026-09-12 kept ignoring `state/`; F-06 shows upgrades already rewrite the stored value | yes |
| D-2 | Fix clean-delta writer here or file it? | File backlog `mbx0o4` | Expand this plan | Different surface (writer, not consent); sibling `pfub72` owns only the state writer; keeps this plan one-pass | yes |
| D-3 | Amend the implemented spec within this plan? | Yes, as E-06 | Leave spec and add a history note only | AGENTS.md "A plan may amend a spec, and must declare it"; a note would leave the table contradicting the code | yes |
