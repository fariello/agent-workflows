# Review findings: plan 381ml6

- Subject-Id: 381ml6
- Subject-Type: ipd
- Reviewed-At: 2026-11-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `417785106` in runner review-sweep lane `run-20261107T013051Z-1859811` (non-interactive). The lane-input copy (revision 1) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions with zero findings; after revisions `--phase author` and `--phase review-finalize` are clean with zero findings. All mutation probes ran in a scratch git worktree under `.aw/state/381ml6-review/` (gitignored), reset after each probe; no tracked plan other than `381ml6` was modified.

Controlling context: spec `ecmw83` R-08 to R-11, MD-4, N3, AC-06 to AC-08; the maintainer's `g4719s` OQ-02 answer (2026-11-05) keeps the standard at `.aw/system/workflows/technical-writing/technical-writing.md` with no dash rule of its own. Siblings `sfez3e` (Order 07) and `uog8nc` (Order 08) were reviewed in two rounds each and carry the guard, unit, carrier, and walkthrough design this plan now follows.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | "R-08 to R-10"; `revsteps` executing at authoring as fact | R-08 to R-11 with R-04; measured live set marked as context; R-09/R-10 cited | PR-010, PR-011. |
| Scope | Short exclusion list; Scope-Paths lacked `backlog/open/` | Full list of protected elements; carrier directory added | PR-002, PR-005, PR-008. |
| Definitions (new) | none | BASE, frozen plan, guard, plan unit, skip rule, editable text, protected elements, sweep line, dashes | PR-001 to PR-007. |
| E-01 | Baseline with `python3 -c` digests | Format precheck, error and staleness baselines, orchestrator `review-finalize`, digest script, guard at BASE | PR-001, PR-004, PR-009. |
| E-02 | One item sweeping every plan with a skip rule naming a queue the tool does not report | One committed plan unit per plan; skip rule on `setid`/`id6` | PR-003, PR-006. |
| E-03 | History line for changed plans only | Full guard with `--final` (exactly one sweep line per swept plan, none per skipped) | PR-001, PR-007. |
| E-04 | Digest compare, "revert inside the frozen region" | Digest script compare for frozen digest and coverage fingerprint | PR-002, PR-004. |
| E-05 | `aw ipd lint` over `pending/` and `reusable/` | `aw ipd lint` (no path), orchestrator `review-finalize`, `aw check all` staleness list | PR-009. |
| E-06 | Hand-named walkthrough; carrier only for skips and frozen defects | `set_records.write_walkthrough`; carrier also for `Unresolved` annotations | PR-005, PR-008. |
| E-07 | Check, gate, commit | Adds sanitizer and committed-path proof | PR-012. |
| Conventions | `standards/technical-artifact-writing.md`; "Purpose and scope" | Shipped path and real section names; measured digest coverage | PR-010. |
| Findings | Two bullets | Measured digest, staleness, coverage, approval-fallback, dash, and runner-monitor facts | PR-002 to PR-007. |
| Deferred | One carrier row | Adds terminal plans (N3) and scaffold dashes (`yz4jdm`) | PR-007. |
| Required tests | Command list | Guard and digest scripts with measured behavior | PR-001. |
| V-01 to V-07 | Partial evidence demands | Evidence demands matching each revised E-item, spec-qualified | PR-001, PR-009. |
| Gate | Old path; "Move the plan to executed/" | Full execution contract | PR-010, PR-012. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No: the plan edits plan prose only; no spec, CLI, file format, or configuration changes.
2. No: no code guarding private data, commits, worktrees, merges, or the sandbox.
3. Moderate: 7 E-items in 3 task groups; 23 live plans of one record type, about 786 KB.
4. Yes: four directory Scope-Paths.
5. Yes: a wrong edit to a reviewed plan can silently stale its review, withdraw its approval clearance, or stale an orchestrator's coverage record, and any of these blocks a run of that plan; each plan is its own commit and easy to revert.

Tier: standard.

### Step R1

- Checked: spec `ecmw83` R-04, R-08 to R-11, MD-4, N3, AC-06 to AC-08, Section 7 risk on Set `revsteps`; `ipd_lifecycle.frozen_region_digest`, `ipd_lifecycle._requirements_from_plan`, `ipd_lint.leaf_action_blocks`; `plan_readiness.review_staleness_index`, `plan_readiness.review_staleness_from_texts`, `plan_readiness.is_plan_review_approved`, `plan_readiness.is_review_history_entry`, `plan_readiness._REVIEW_WORDS`; `ipd_lint._review_stale_advisory` and `ipd_lint.C_REVIEW_STALE` (`check.ipd-review-may-be-stale`); `check_engine` staleness rule; `runner_shared.probe_cache_digest`, `runner_shared.PROBE_PROSE_SECTIONS`, `coverage_record.is_current`; `runners_monitor.extract_journey_info` and `to_dict` (no queue field); `set_records.write_walkthrough`; `ipd_authoring._VALID_INTRO`; walkthroughs README (D140); siblings `sfez3e`, `uog8nc`, orchestrator `8fvkmp` row 09 and E-09.
- `.aw/system/workflows/standards/technical-artifact-writing.md` does not exist (the standard shipped at `technical-writing/technical-writing.md`), and the standard has no "Purpose and scope" section (PR-010).
- `aw runners --once --json` live at review returned only this run (`setid` `writestd`, `id6` `381ml6`, `action` `review`), with no queue field (PR-006).

### Step R2

- Checked: E/V bijection 7/7; every `V-*` demands pasted output, hashes, or guard output; V-05's staleness demand is reachable through `ipd_lint._review_stale_advisory` (measured: an E-item edit committed after a `plan-review:` commit produced `check.ipd-review-may-be-stale` from `aw ipd lint --agent`); spec citations qualified with `ecmw83`; `- Item-Dependencies:` match orchestrator `8fvkmp` row 09; Scope-Paths now include `.aw/records/backlog/open/` for the carrier (PR-008); original E-05 named `aw ipd lint` "over `pending/` and `reusable/`", and `aw ipd lint .aw/records/plans/pending/` exits 2 (cannot-run) because a directory is not a plan path (PR-009).

### Step R3

- Checked: no code or trust boundary. The swept plans are public records and rewording could introduce a local path, so E-07 runs `aw sanitize --agent` (PR-012).

### Step R4

- Checked: invariants mapped to the guard: metadata block (every gate, readiness, coverage, and release field), E/V ids and checkboxes, state and question fields, frozen-plan sub-fields, `frozen_region_digest`, coverage fingerprint, review-approval predicate, headings, stable IDs, inline code spans, numbers, non-diagram fences, history records, modal verbs, quoted text, and exactly one sweep line. The guard and digest script are validation scripts kept under `.aw/state/`, not repository tests.
- Guard sensitivity, scratch worktree of HEAD `417785106` (exit 1 each): E-01 action edit (`frozen_region_digest changed`); `- Expected outcome:` edit; `- Required evidence:` edit; OQ `Blocking: yes` to `no` in `g4719s`; deferral `Carrier:` change; `- Resolution or deferral rationale:` edit; `- Readiness:` change; `MUST` to `MUST NOT` in gate prose (`modal count fell: must 13->12`); one word in `8fvkmp` `## Goal` (`probe_cache_digest (orchestrator coverage) changed`); dash reworded in `63ib9r`; sweep line on a frozen plan whose `- Readiness:` had been removed (`review-approval predicate changed`). Exit 0 each: unchanged tree (`TOTAL live=23 checked=23 problems=0`, about 23 seconds); `## Goal` reword in `uog8nc`; dash reworded in `7ehv8l`; sweep line with `--final` on `uog8nc`; an edit to `381ml6` itself (excluded). The scripts extracted verbatim from the revised plan reproduce the baseline and the digest table.
- Right-sizing: 23 plans at about 786 KB fit one E-item of per-plan committed units with a resume rule, as in `sfez3e` E-02/E-03 and `uog8nc` E-02.
- Spec sync: N/A, substantiated (no spec file is in scope; `ecmw83` already describes this sweep).

### Step R7

- Checked against `sfez3e` and `uog8nc` (both `reviewed`): same guard lineage, unit shape, carrier, walkthrough grammar, and `cxxmyv` precheck; `Unresolved` prefix `PW-` so the three carriers do not collide. Orchestrator `8fvkmp` E-09, completion criterion "`381ml6` V-04 compares frozen-region digests", and row 09 stay true. Plans `sfez3e` and `uog8nc` may each file a carrier in `backlog/open/` before this plan runs; that is outside this plan's sweep set (backlog, not plans).

### Step S5

- Checked: no pre-existing open question. Choices resolved from evidence are D-1 to D-5. No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | UNDER-SCOPE | D invariant; E testing | `ecmw83` R-08 "must not change any status, approval, `Readiness` ... field"; old E-02 to E-05 | The only mechanical proof was the frozen digest; nothing caught a changed metadata field, question field, heading, ID, code span, number, history record, modal, or quoted passage, and old E-03 noted only changed plans although R-08 says each swept artifact gets a line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Guard script added and measured; one sweep line per swept plan, checked by `--final`. |
| PR-002 | high | UNDER-SCOPE | D invariant | `ipd_lint.leaf_action_blocks` stops before sub-fields; scratch: `- Expected outcome:` edit left `frozen_region_digest` unchanged | For a frozen plan, the reviewed `Expected outcome` and `Required evidence` text were editable under the old wording and invisible to V-04, so a reviewed contract could change while V-04 passed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Definitions protect every indented E/V sub-field of a frozen plan; the guard enforces it. |
| PR-003 | high | IN-SCOPE | D invariant | `plan_readiness.is_plan_review_approved` fallback reads `extract_newest_history_entry`; scratch: True before, False after a `proofread` line on top when `- Readiness:` is absent | Old E-03 appended a history line with no placement or label rule; on a frozen plan without `- Readiness:` a newest non-review line withdraws review clearance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Sweep line rule (label `proofread`, newest first, no review words); such a plan is skipped; guard checks the approval predicate. |
| PR-004 | high | UNDER-SCOPE | R7 cross-plan; D invariant | `runner_shared.PROBE_PROSE_SECTIONS` includes `Goal`, `Scope check`; scratch: `8fvkmp` Goal edit gave `IPD-S408` "coverage-record-stale" at `review-finalize` | Old E-02 listed Goal and Child IPDs prose as editable for orchestrators; that text is in the coverage fingerprint, so a proofread stales `8fvkmp` and `63ib9r` and blocks their review-finalize lint until a model re-probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Fingerprint-covered text protected; guard and digest table check `probe_cache_digest`; E-05 compares orchestrator `review-finalize`. |
| PR-005 | medium | UNDER-SCOPE | G executability | `ecmw83` R-11, AC-08; walkthroughs README D140 | No `Unresolved` annotation procedure or carrier; walkthrough named by hand without its own id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `PW-NN` annotation step; E-06 uses `write_walkthrough` and files one carrier. |
| PR-006 | medium | IN-SCOPE | R2 executability | `runners_monitor.RunnerInfo.to_dict` has no queue field; live output at review | The skip rule required knowing whether a run's queue includes the plan, which `aw runners --once --json` does not report, and it did not exempt the run executing this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Skip on matching `id6` or `setid`, excluding this plan's own run; a running Set is treated as queued. |
| PR-007 | medium | IN-SCOPE | D invariant | `technical-writing.md` "This standard adds no dash rule of its own"; 14 live plans with the `ipd_authoring._VALID_INTRO` dashes | The plan said nothing about dashes although AC-06 measures the sweep by them, and the only live dashes sit in a sentence that executed plans quote and that the orchestrator fingerprint covers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Reword only `IPD-C802`-reported dashes the guard permits; generator dashes deferred to carrier `8fvkmp`. |
| PR-008 | medium | UNDER-SCOPE | R2 scope fence | old E-06 `aw backlog new`; old Scope-Paths | The carrier is written to `.aw/records/backlog/open/`, which Scope-Paths did not declare. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added to Scope-Paths; gate names the `--scope-ack` case. |
| PR-009 | medium | IN-SCOPE | R2 evidence feasibility | `aw ipd lint .aw/records/plans/pending/` exits 2 (cannot-run) | Old E-05/V-05 ran lint over directories, which cannot run; the staleness check had no baseline list. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `aw ipd lint --agent` with no path, orchestrator `review-finalize`, and the `aw check all` staleness list, each against E-01. |
| PR-010 | high | IN-SCOPE | R1 references | `g4719s` OQ-02 answer; shipped standard headings | Conventions and gate named `standards/technical-artifact-writing.md` and a "Purpose and scope" section, neither of which exists; Concern cited R-08 to R-10 though R-11 governs `Unresolved` text. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Shipped path and real section names; R-04 and R-11 cited. |
| PR-011 | low | IN-SCOPE | R2 live counts | old Concern "At authoring time Set `revsteps` was executing" | Live state at authoring stated without measurement or re-derivation note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Concern gives the measured live set as context; E-01 re-derives. |
| PR-012 | medium | IN-SCOPE | G execution contract; B privacy | old gate | Gate lacked fence-as-declaration wording, the paste-output MUST, never `git add -A`, Order preconditions, and finalize ownership (it said "Move the plan to executed/"); no sanitizer run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten as in `sfez3e`; E-07 runs `aw sanitize --agent`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Protect `Expected outcome` and `Required evidence` of frozen plans although the digest ignores them? | Protect every indented E/V sub-field of a frozen plan | Allow edits (digest stays equal) | Spec `ecmw83` MD-4 "keep their status" and R-08 meaning-preservation; a reviewed contract includes them | yes |
| D-2 | How to apply R-10 when the runner monitor does not list a run's queue? | Treat every plan in a running Set as queued; exempt this plan's own run | Read `state.json` directly (outside the lane, unsupported by any verb) | `runners_monitor.to_dict`; isolated lane cannot read the main checkout's run directory | yes |
| D-3 | Allow proofreading of orchestrator fingerprint-covered prose and re-run `aw ipd coverage`? | Protect it | Re-probe after editing | Re-probing writes `- Coverage-*` metadata, which R-08 forbids, and needs a model host | yes |
| D-4 | Note a frozen plan that lacks `- Readiness:`? | Skip it with a recorded reason | Note it and accept lost clearance; append the line at the bottom | `plan_readiness.is_plan_review_approved` fallback; history is newest-first (`s7-finalize.md`) | yes |
| D-5 | Fix the generator dashes in `ipd_authoring._VALID_INTRO`? | Defer to carrier `8fvkmp` | Edit the module here | Outside Scope-Paths and spec `ecmw83`; plan `yz4jdm` owns that module | yes |
