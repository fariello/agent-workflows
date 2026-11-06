# Review findings: plan sfez3e

- Subject-Id: sfez3e
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2f2b01f35` in runner review-sweep lane `run-20261106T033613Z-1047571` (non-interactive). The lane-input copy (revision 1, sha256 `d2a1c1a4...`) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions (one info `IPD-Z602` on E-02: three bundled action clauses). After revisions `--phase review-finalize` is clean with zero findings.

Controlling context: the maintainer answered `g4719s` OQ-02 on 2026-11-05 ("Keep shipped file; amend spec; re-scope g4719s (recommended)"). The standard ships at `.aw/system/workflows/technical-writing/technical-writing.md` with no dash rule of its own, and Orders 02 to 09 are re-reviewed against that ruling (`gzhw9c` PR-005 and its Deferred row, carrier `8fvkmp`). This review applies it to Order 07.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | Status counts "3 draft, 1 to-review, 1 reviewed, 10 approved..." as fact | Measured counts marked as context; E-01 re-derives | PR-007 (live-artifact count convention). |
| Scope, Scope-Paths | Includes `reviewed/`; "per changed spec" | Drops vanished `reviewed/`; every swept spec; adds `backlog/open/` | PR-001, PR-003, PR-008. |
| E-02 | One item, three bundled clauses, dash hunt | Spec-unit definition; split by size into E-02, E-03; dash only where the advisory reports | PR-005, PR-006, PR-010. |
| E-03 (old) | `aw specs note <id6>` | `aw specs note <spec path>` inside the spec unit | PR-002. |
| E-04 | "no metadata changed except none" | Full guard run with `--final` | PR-004, PR-011. |
| E-05 | `<date>-writestd-07-spec-sweep-walkthrough.md` | `set_records.write_walkthrough` with own id6 and `Target-Id` | PR-009. |
| E-06 (new) | none | Backlog carrier for `Unresolved` annotations | PR-008. |
| Conventions, gate | `standards/technical-artifact-writing.md`; "Purpose and scope" | Shipped path; actual section name | PR-012. |
| Gate | Partial contract | Full execution contract | PR-013. |
| Required tests | Command list | Adds the guard script and its measured behavior | PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it edits the text of 22 live specs, 11 of them approved contracts that other plans review against.
2. No: no code guarding private data, commits, worktrees, merges, or the sandbox.
3. Yes: about 1.65 MB of spec text in one plan; 7 E-items in 3 task groups.
4. Yes: seven directory Scope-Paths covering every live spec directory.
5. Yes: a rewording can silently change an approved obligation or break a quoted-text citation in another plan; each is hard to detect after the fact.

Tier: complex.

### Step R1

- Checked: spec `ecmw83` R-04, R-08, R-09, R-10, R-11, MD-2 to MD-5, N3, AC-06, AC-08, Section 5.2 flowchart; the shipped standard's sections ("Scope", "How it combines with other rules", "Requirements", "Checking your work"; no "Purpose and scope" section, no requirement 12 and no "Proofreading procedure" yet, both added by `g4719s` E-02 and E-03); `aw find specs --status-not implemented --status-not superseded` (22 specs; no `reviewed/` or `deferred/` directory); per-file sizes and line counts; Mermaid block counts; `specs.run_note` (reads `args.path` as a file; `aw specs note or061f` printed "cannot read or061f: [Errno 2] No such file or directory"); `specs._append_history` (prepends one line, keeps prior records); `set_records.write_walkthrough` (mints own id6, writes `- Target-Id:`); `.aw/records/walkthroughs/README.md` and D140; `.aw/config/project.json` `walkthrough_id6` 2026-09-27; `check_engine.stale_record_scope_paths` and the dispatch refusal in `runner_shared` (`scope_target_refused`); `spec_citations.stale_spec_anchors` (0 line-anchor citations into specs from code); `runner_shared.declared_spec_paths` (only literal `.spec.md` entries are announced); `ipd_authoring.compute_sync` (refuses on approved plans).
- Probe: in a scratch git repo inside the lane (`.aw/state/`), `aw specs note <path>` appended `- 2026-11-06 note (aw specs): ...` and `set_records.write_walkthrough` produced `20261106-writestd-07-o531cy-spec-sweep.walkthrough.md` with `- Id: o531cy` and `- Target-Id: sfez3e`.
- Plan claims re-measured: `4sd62s` is 2,373 lines (plan said about 1,690); live total is about 15,400 lines (plan said about 12,700). Corrected in Findings (PR-007).

### Step R2

- Checked: E/V bijection 7/7 after revision; each `V-*` demands pasted commands, hashes, or guard output; no V-item demands a runtime observation; spec trace cites `ecmw83` R-04, R-08, R-11, AC-06, AC-08 qualified; `- Item-Dependencies:` match the orchestrator `8fvkmp` row 07; Scope-Paths now resolve (the `reviewed/` entry was `vanished`, an `error` in `aw check all` and a dispatch refusal).
- `aw check all` errors: 14 before revision (one is this plan's `check.scope-path-target-stale`), 13 after.

### Step R3

- Checked: no code, credentials, or trust boundary. The sweep edits tracked records only. E-07 runs `aw sanitize --agent`, because spec text is public and rewording could introduce a local path.

### Step R4

- Checked: invariants named and mapped to a check: metadata unchanged, status directory unchanged, headings, stable IDs, inline code spans, numbers, non-diagram fenced blocks, history records, modal verbs, and text quoted elsewhere (all by the guard); one sweep note per spec (`--final`); no new `aw check` error (E-07). The guard is a validation script for this plan's own output, not a repository test, so P16 does not apply; it is kept under `.aw/state/` and never committed.
- Guard sensitivity measured: in a scratch copy, a status change, a removed `E-03`, a removed history line, a changed quoted passage, and `must` changed to `should` each produced a problem line and exit 1; an unchanged tree produced `problems=0` and exit 0. Full run at HEAD: about 40 seconds, `TOTAL live=22 checked=22 problems=0`.
- Limitation stated in the plan: the guard cannot prove that a reworded sentence keeps its meaning.
- Spec sync: no contract change; the directories in Scope-Paths are not announced by `declared_spec_paths` (literal `.spec.md` only), so the plan names this in its spec-sync section.

### Step R5

- QA/QC: the old E-04 Expected outcome ("no metadata changed except none") was not checkable and covered metadata only (PR-004, PR-011).
- Testing and regression: no mechanism detected meaning drift or broken quoted-text citations; 1,322 passages in live specs are quoted by other tracked files (PR-004).
- UI/UX: not applicable.
- Architect: the sweep reuses `aw specs note`, `aw commit`, `set_records.write_walkthrough`, and `aw backlog new`; no new mechanism.
- Software engineer: the old E-03 command shape fails (PR-002).
- Power user: one commit per spec keeps finished units if a turn ends; resumption rule added to E-03 (PR-005).
- Novice: the spec unit is defined once with ordered steps.
- Stakeholder: approved specs keep status and obligations; `Unresolved` items reach a tracked carrier (PR-008).

### Step R6

- Checked: 1.65 MB of spec text in one plan. A split into separate child plans was considered and rejected: every spec unit is the same procedure, independently committed and guard-checked, so the risk is turn length, not conceptual density. The plan splits the work into two E-items by size (E-02 small, E-03 large) and makes each spec a resumable committed unit. Recorded as D-4. No Set split recommended.

### Step R7

- Checked: orchestrator `8fvkmp` row 07 and its cross-IPD claim "`sfez3e` V-05 pastes the final `aw specs check --agent` advisory count" (still true: V-05 pastes it); siblings `g4719s` (adds requirement 12 and the procedure section), `gzhw9c` (amends `ecmw83` R-05, AC-03, N1, N2), `k2x0yl` (adds `spec.prose-dash`), `e4n4p3` (amends `k3yx72`), `uog8nc` and `381ml6` (same sweep shape; their `aw backlog note <id6>` and walkthrough-name steps should be checked against PR-002 and PR-009 in their own reviews, because a finding is fixed in the owning plan); `metastore` plans `7ehv8l` and `cxxmyv` edit `4sd62s` and `2vev8j` (the guard keeps the passages they quote).

### Step S5

- Checked: no pre-existing open question. The dash question is answered by the maintainer's `g4719s` OQ-02 ruling and spec `ecmw83` AC-06 as written (D-1). Other questions resolved from evidence (D-2 to D-5). No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | IN-SCOPE | R2 executability | `check_engine.stale_record_scope_paths`; `aw check all` "Scope-Paths entry '.aw/records/specs/reviewed/' is vanished" (error); `runner_shared` `scope_target_refused` | The `reviewed/` Scope-Path does not exist, so `aw check all` reports an error and the runner refuses to dispatch the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed; status `reviewed` stays in the Scope prose for execution-time re-derivation. |
| PR-002 | high | IN-SCOPE | R1 references | `specs.run_note` `path = Path(args.path)`; probe "cannot read or061f" | E-03 ran `aw specs note <id6>`, which fails on every spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Spec unit uses `aw specs note <spec path>`. |
| PR-003 | high | UNDER-SCOPE | D invariant | `ecmw83` R-08 "Each swept artifact must get one history line" | The plan noted only changed specs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Every swept spec gets the note; `--final` checks exactly one per spec. |
| PR-004 | high | UNDER-SCOPE | D invariant; E testing | `ecmw83` R-08 "must not change any status, approval ... identity, or provenance field"; 1,322 passages quoted elsewhere | Only metadata was diffed; nothing caught a changed heading, ID, number, modal, fenced block, history record, or quoted passage. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Guard script added and measured; run per spec and in full. |
| PR-005 | medium | IN-SCOPE | R4 right-sizing | `aw ipd lint` `IPD-Z602` on E-02; 1.65 MB across 22 specs | E-02 bundled several actions and all 22 specs in one item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Spec unit defined once; split into E-02 (small) and E-03 (large); resumption rule. |
| PR-006 | medium | IN-SCOPE | D invariant | `technical-writing.md` "This standard adds no dash rule of its own"; `g4719s` OQ-02; `ecmw83` AC-06 | E-02 required replacing every prose dash, which assumes the widened dash rule the maintainer did not keep. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Reword only dashes the advisory reports (AC-06 as written); AC-06 and the 5.1 flowchart node deferred to `8fvkmp`. |
| PR-007 | low | IN-SCOPE | R2 live counts | Concern status counts; Findings `4sd62s` "about 1,690" (measured 2,373) | Live-artifact counts stated as fact, and two were wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Counts re-measured and marked as context; E-01 re-derives. |
| PR-008 | medium | UNDER-SCOPE | G executability | `.aw/records/walkthroughs/README.md` "nothing scans its contents for outstanding work" | `Unresolved` annotations were recorded only in a walkthrough, which no gate revisits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 files one backlog carrier; `backlog/open/` in Scope-Paths. |
| PR-009 | medium | IN-SCOPE | R1 references | D140; `check.id6-identity-slot`; `set_records.write_walkthrough` | The walkthrough name lacked the clustered grammar and its own id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 uses `write_walkthrough`; V-05 checks the rule. |
| PR-010 | medium | UNDER-SCOPE | G executability | spec unit; `ecmw83` R-11 | No annotation format, no per-spec commit command, no guard step inside the unit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Spec unit gives the `SW-NN` format, the `aw commit` command, and the guard step. |
| PR-011 | low | IN-SCOPE | P proofread | old E-04 "no metadata changed except none" | Unclear Expected outcome. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Replaced by the guard's `problems=0`. |
| PR-012 | high | IN-SCOPE | R1 references | `g4719s` OQ-02 answer; shipped path | Conventions and gate named `standards/technical-artifact-writing.md` and a "Purpose and scope" section, neither of which exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Shipped path and real section names. |
| PR-013 | medium | IN-SCOPE | G execution contract | plan gate | Gate lacked fence-as-declaration wording, the paste-output MUST, never `git add -A`, finalize ownership, and the Order preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the sweep remove every prose dash from specs? | Only dashes `spec.prose-dash` reports, to meet `ecmw83` AC-06 as written; defer AC-06 itself to `8fvkmp` | Remove all dashes (reverses the kept ruling); ignore dashes (fails AC-06) | `g4719s` OQ-02 maintainer answer 2026-11-05; `technical-writing.md` "How it combines with other rules" item 4; `gzhw9c` Deferred row naming Orders 07 to 09; measured 2 prose dashes in live specs | yes |
| D-2 | Note every swept spec or only changed ones? | Every swept spec | Changed only (original plan) | `ecmw83` R-08 "Each swept artifact must get one history line" | yes |
| D-3 | How to prove meaning was preserved? | Mechanical guard over protected elements plus per-diff reading; state that the guard cannot prove meaning | Diff metadata only; a repository test | `ecmw83` R-08, Risks "A proofreading pass can change meaning by accident"; guard measured on scratch mutations; P16 (a repository test of record text would pin content) | yes |
| D-4 | Split the plan into several child plans by spec? | Keep one plan; two E-items by size; one committed unit per spec | Child plan per spec group | Identical procedure per spec; committed units survive a turn end; `lane_containment.MAX_TURN_TIMEOUT` 8 h | yes |
| D-5 | Where do `Unresolved` annotations become tracked work? | One backlog carrier via `aw backlog new` | Walkthrough only (untracked); one item per annotation | walkthroughs README "nothing scans its contents"; AGENTS.md durable-carrier rule | yes |
