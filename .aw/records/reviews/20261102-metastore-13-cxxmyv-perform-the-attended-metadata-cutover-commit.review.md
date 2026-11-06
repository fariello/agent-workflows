# Review findings: plan cxxmyv

- Subject-Id: cxxmyv
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `acab80350` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 14) was byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them. New E-items were numbered by `aw ipd sync` (E-14 to E-17, watermark 13 to 17). One probe used a throwaway repository under the gitignored `.aw/state/`, which was removed afterwards. Nothing in phase B or phase C exists yet in the tree (`agent_workflows/artifact_meta.py` and `agent_workflows/migrations/` are absent), so every claim about sibling deliverables was checked against the sibling plans, not code.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | "deferral rows ... in all 12 sibling plans" | 11 of 12, `7ehv8l` has none, re-measured | PR-016. |
| F-01, F-02 | Count stale; OQs described as open | Re-measured list; OQs answered, applied by E-01 and E-14 | PR-016. |
| E-01 | Model decision plus OQ-01 code | Model decision only; OQ-01 code moved to E-14 | PR-007. |
| E-02, E-12 | AC-13 "before" values said to be recorded in E-02, which did not record them | E-02 records them with the cold-cache method | PR-011. |
| E-04 | Deletes the sidecar ignore line, INDEX files and STATUS.md before the migration | Code and installer template only; on-disk changes left to migration steps 2 and 5 | PR-001. |
| E-05, E-15 | Gates, readers and SR-601 in one item | Gates in E-05, readers in E-15, SR-601 removed (owned by `2xwb9b` E-12) | PR-006, PR-007. |
| E-06 | Builds `aw meta repair` | Removed (owned by `ffceq0` E-11); adds `command_surface` declarations and the `aw reviews` namespace text | PR-006. |
| E-07, E-09 | Core gate green before migration | Unmigrated-records refusals expected and listed; full green proven on the migrated copy | PR-003. |
| E-16 (new) | None | `Kind` option renames with aliases and the `90iqr1` F-07 tests | PR-008. |
| E-17 (new) | None | Full rehearsal on a copy, settling the one-commit mechanism with a stop condition | PR-002. |
| E-09, E-10 | No commit of this plan before the migration | Plan edits committed so the preflight sees a clean records tree | PR-004. |
| E-11 | Probes in the real checkout; AC list incomplete | Probes that commit run in a demo clone; adds AC-1, AC-11, AC-30 case 2, AC-41 cases 3 and 4, `attention --check`; AC-2 uses `file://` | PR-005, PR-010, PR-012. |
| E-13 | "confirm the orchestrator `63ib9r` can be retired" | Removed (orchestrator's own E-13); conditional finalize ownership stated | PR-015. |
| V-01 to V-17 | Several demands mismatched their E-item | Each V demands the evidence of its own E | PR-014, plus each fix above. |
| Scope-Paths | Missing `.aw/system/cutover/`, `.aw/system/managed-sections.json` | Added | PR-013. |
| Spec / documentation sync | "No spec change" | No change planned; conditional amendment of 5.2 step 7 if E-17 adds a staging mechanism | PR-002. |
| Gate | Partial execution contract | Scope fence, stop conditions, commit rules, honesty rule, conditional finalize ownership | PR-015. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. It flips the on-disk metadata format of every record, stamps `metadata_schema: 2`, adds two CLI commands, renames CLI options and amends the managed AGENTS.md block.
2. Yes. It changes the commit hooks (`executed_transition_gate`, the `meta/*.jsonl` append-only hook), makes one bulk commit under the integration lock, and runs the leak sanitizer on about 87 sidecar records that become tracked for the first time.
3. Yes. 17 E-items in 4 task groups across `artifact_meta`, the setters, the hooks, `check_engine`, the CLI, the test builder, the documentation and the whole records corpus.
4. Yes, as broad directory entries (`agent_workflows/`, `tests/`, `.aw/records/`).
5. Yes. A mistake rewrites every record in one commit. The spec states the commit can be reverted (section 6), but the sidecar is moved out of the tree in the same run.

AW-TIER: complex

### Step R1

- Checked: spec `4sd62s` 5.2 steps 0 to 7, 5.3, 5.4, 4.2 `overrides`, 4.3 write order, 4.4 SR-601 and the "implementing plan names that command" sentence, 3b AC-1, AC-1b, AC-2, AC-3, AC-6, AC-7, AC-9, AC-10, AC-11, AC-13, AC-16, AC-22, AC-30, AC-31, AC-34, AC-36, AC-40, AC-41; every `Carrier: cxxmyv` row in the 12 siblings; `dcerjg` E-01, E-04, E-06, E-11, E-13, E-15; `ya4ee4` E-08, E-10, OQ-02; `2xwb9b` E-12, OQ-02; `ffceq0` E-11; `9o83cr` E-14, F-21; `90iqr1` E-08 to E-10, F-07; `63ib9r` E-13; `.pre-commit-config.yaml`; `cli.py` `--kind` options; `aw reviews --help`.
- Spec 4.2 already holds the OQ-01 `overrides` key and the `--date` refusal, so OQ-01's "Spec `4sd62s` 4.2 is amended in the same change" is already true.
- `aw meta repair` is `ffceq0` E-11, and SR-601 is `2xwb9b` E-12; the plan claimed both (PR-006).
- `9o83cr`'s Deferred row about `INDEX.*` files says "These files exist in every unmigrated repository until `m0001` step 5 deletes them". `dcerjg`'s row about the sidecar ignore line says doing it early "would stop ignoring a sidecar the toolkit still writes". E-04 did both before the migration (PR-001).
- `90iqr1` and `59aiyh` each carry a `cxxmyv` row the Scope check did not map (PR-008, PR-009).
- `git clone --depth 1 <local path>` prints "warning: --depth is ignored in local clones; use file:// instead." Measured at review: `rev-list --count` 2 for a local path and 1 for `file://` (PR-005).

### Step R2

- Checked: the E/V bijection (17/17 after sync), the dependency graph, the scope fence, the reachability of each runtime demand, and live-artifact counts.
- Reachability: V-10's apply comes from `dcerjg`'s `m0001_metadata_v2.run`; V-17's rehearsal is created by E-17; V-11's hook refusals come from E-05; V-06's commands come from E-06. Before this review, no code path or E-item produced one commit that holds both the migration output and the task group 2 code. Spec 5.2 step 7 commits "the migration's own list of paths", and `dcerjg` E-11's marker accepts only the exact staged tree (PR-002).
- E-07 and E-09 demanded a green core gate after `CURRENT_METADATA_SCHEMA` became 2 and before the migration. `dcerjg` OQ resolution says that flip "makes every legacy repository refuse", and `tests/test_attention.py` scans `REPO_ROOT`, so that demand was unsatisfiable (PR-003).
- V-02 bar "the 34-row rename map" was a live count; it is now re-derived (PR-016).
- V-03's `rg` demand contradicted AC-1, which allows matches in `artifact_meta.py`; it is now behavioral, and the AC-1 audit is in V-11 (PR-014).

### Step R3

- Checked: the integration lock, `--force`/`--force-worktree`, `--no-verify`, the sidecar, the sanitizer and pushing.
- The sidecar holds records the maintainer purged from git. E-04's early removal of its ignore line would let a broad `git add` commit them (PR-001).
- The gate now forbids `--no-verify` and pushing. Overrides need the maintainer's decision, recorded in the plan. The sanitizer runs on the staged tree before the commit (E-10).
- AC-16's pre-push gate is run directly as `python3 -m agent_workflows attention --check --agent`, without pushing (E-11).

### Step R4

- A. Correctness: the commit is one step, but the plan's own edits and the patch's records-README hunks would dirty `.aw/records/` and trip the preflight (PR-004, handled in E-09, E-10 and E-17).
- C. Operability: real-repository probes that commit or merge (AC-3, AC-6, AC-16 case 2, AC-31, the AC-13 append time) would add commits to `main`; they now run in a demo clone (PR-012).
- D. Invariants: C10a (one format per commit) is kept by E-17 proving one commit; C9 is kept by E-03.
- E. Testing: both tiers now run green on a migrated copy before the real apply (E-17).
- Right-sizing: E-01 bundled a decision with code, and E-05 bundled gates with readers; both were split (PR-007). E-03 and E-11 remain dense. They are kept because E-03 is one mechanical switch and E-11 is a list of read-only checks with no code.
- Spec sync: now truthful, with the conditional 5.2 step 7 amendment.

### Step R5

- QA/QC and testing: the main gap was the unsatisfiable green gate (PR-003) and the missing rehearsal (PR-002).
- Architect: the one-commit mechanism was unspecified (PR-002).
- Software engineer: the duplicated sibling work (PR-006) would have produced two implementations.
- Power user: renamed options keep aliases (E-16).
- Novice and stakeholder: the gate now states the stop conditions in plain terms.
- UI/UX: not applicable beyond `--help` text.

### Step R6

- Checked: 17 E-items in 4 groups (limits 18 and 5). No split is recommended. The cohesion rationale holds: spec 5.2 and C10a require one commit, and every item except E-11 to E-13 must land in it. A split would need a long-lived branch, which the runner model does not have (spec section 7).

### Step R7

- Checked: every sibling's `Carrier: cxxmyv` rows, the `- Item-Dependencies:` of every sibling, and `63ib9r`'s child row and E-13.
- `- Item-Dependencies: executed:90iqr1, executed:dcerjg, executed:ya4ee4, executed:1ajqaa` reaches every other sibling transitively (`90iqr1` needs `9o83cr`, which needs `ffceq0`, `t4gl15`, `59aiyh`, `1ajqaa` and `dcerjg`; those need `tve77h`, `xexn45`, `2xwb9b` and `7ehv8l`).
- `63ib9r` row 13 matches this plan's dependencies.

### Step S5

- Checked: OQ-01 and OQ-02 are resolved by the maintainer, and their resolutions match spec 4.2 and `ya4ee4` OQ-02.
- PR-002 is a HOW question. It cannot be demonstrated at review because `m0001` does not exist yet. Per S5 rule 3 it became a first spike E-item (E-17), whose expected outcome is the demonstration and whose stop condition asks the maintainer. The verdict names the feasibility risk.
- No question needs the human now.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R3 / spec 5.2 steps 1, 2, 5 | `9o83cr` Deferred row "These files exist in every unmigrated repository until `m0001` step 5 deletes them"; `dcerjg` Deferred row "would stop ignoring a sidecar the toolkit still writes" | E-04 deleted the sidecar ignore line, the INDEX files and `STATUS.md` before the migration. That dirties `.aw/records/` (a preflight refusal) and un-ignores purged sidecar records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 changes code and the installer template only; migration steps 2 and 5 make the on-disk changes. V-04 checks this checkout is unchanged. |
| PR-002 | HIGH | UNDER-SCOPE | R2 reachability / spec 5.2 step 7 | Spec 5.2 step 7 "Commit with `aw commit --no-plan` and the migration's own list of paths"; `dcerjg` E-11 marker "its tree id equals the current `git write-tree`" | Nothing defines how the one migration commit also contains the task group 2 code, tests and documents, so E-10's "folding in" had no producing code path. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Spike E-17 rehearses on a copy, adds a staging mechanism if needed, and stops for the maintainer if none works; conditional spec 5.2 step 7 amendment. Feasibility risk named in the verdict. |
| PR-003 | HIGH | IN-SCOPE | R2 evidence feasibility | `dcerjg` OQ "makes every legacy repository refuse"; `tests/test_attention.py` `att.scan(REPO_ROOT)`; `pyproject.toml` `livecorpus` | E-07 and E-09 demanded a green core gate after the schema flip and before the migration, which tests over this repository's own records cannot give. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 and E-09 allow only listed "run `aw migrate metadata`" refusals; E-17 demands 0 failures on the migrated copy. |
| PR-004 | MEDIUM | IN-SCOPE | R4 A | `dcerjg` E-04 condition "(2) UNCOMMITTED: `git status --porcelain -- <records root>` non-empty" | This plan's own progress edits live under `.aw/records/` and would trip the preflight. | Overall:Low | FIXED | E-09 and E-10 commit the plan with `aw commit cxxmyv` before each migration run. |
| PR-005 | MEDIUM | IN-SCOPE | R1 measured | Probe at review: local-path `--depth 1` clone gave 2 commits and the warning; `file://` gave 1 | The AC-2 shallow clone would silently be a full clone. | Overall:Low | FIXED | E-11 uses `file://` and V-11 demands `rev-list --count` 1. |
| PR-006 | MEDIUM | OVER-SCOPE | R7 | `ffceq0` E-11 "Add `aw meta repair <id6> [--apply] [--confirm]`"; `2xwb9b` E-12 `review_attestation_missing` | E-06 and E-05 rebuilt work siblings own. E-06 also left the `aw reviews` text "the whole namespace is read-only and writes nothing". | Overall:Low | FIXED | Both removed with F-05; E-06 adds `command_surface` declarations and the namespace text. |
| PR-007 | MEDIUM | IN-SCOPE | R4 right-sizing | E-01 (decision plus setter code); E-05 (hooks plus readers) | Two items each had independent deliverables and test surfaces. | Overall:Low | FIXED | E-14 (OQ-01 code) and E-15 (readers) split out by `aw ipd sync`. |
| PR-008 | MEDIUM | UNDER-SCOPE | R7 | `90iqr1` Deferred row "Renaming any CLI option that carries the legacy `Kind` name ... and updating tests that assert pre-cutover text (F-07)"; `cli.py` `--kind` on four leaves | The Scope check did not map this row. | Overall:Low | FIXED | E-16 renames with aliases (precedent: `aw backlog new --kind` alias of `--work-kind`) and updates F-07 tests. |
| PR-009 | MEDIUM | UNDER-SCOPE | R7 | `59aiyh` Deferred row "The `tests/fixtures/review-pilot/plans/` corpus ... belongs with the migrated corpus" | Unmapped carrier row. | Overall:Low | FIXED | Added to E-07 and V-07. |
| PR-010 | MEDIUM | UNDER-SCOPE | AC coverage | `9o83cr` E-14 audit row; `dcerjg` row "final AC-10, AC-11, AC-16 and AC-41 evidence"; spec AC-30 (2), AC-41 (3)-(5), AC-16 (1) `attention --check` | E-11 omitted AC-1, AC-11, AC-30 case 2, AC-41 cases 3 to 5 and the pre-push gate. | Overall:Low | FIXED | Added to E-02 and E-11 with V-02 and V-11. |
| PR-011 | MEDIUM | IN-SCOPE | R2 | E-12 "before (recorded in E-02 on the unmigrated tree)" | E-02 did not record the AC-13 before values. | Overall:Low | FIXED | E-02 and V-02 record them. |
| PR-012 | MEDIUM | IN-SCOPE | R4 C | E-11 AC-3, AC-6, AC-16 case 2, AC-31; E-12 append time | Probes that commit, merge or edit an executed plan would run on the real checkout. | Overall:Low | FIXED | They run in `tmp/cxxmyv-demo`; V-11 checks this checkout is unchanged. |
| PR-013 | LOW | IN-SCOPE | R2 scope fence | `90iqr1` lane outcome note; E-08 deletes `.aw/system/cutover/...patch`; patch carries `.aw/system/managed-sections.json` | Two touched paths were undeclared. | Overall:Low | FIXED | Added to `- Scope-Paths:`. |
| PR-014 | MEDIUM | IN-SCOPE | R2 / AC-1 | V-03 "matches only under `agent_workflows/migrations/`" vs AC-1 "ONLY in `artifact_meta.py` and `migrations/m0001_metadata_v2.py`" | V-03 contradicted AC-1. | Overall:Low | FIXED | V-03 is behavioral; the AC-1 audit is in V-11. |
| PR-015 | MEDIUM | IN-SCOPE | S7 execution contract | Gate; E-13 "confirm the orchestrator `63ib9r` can be retired" vs `63ib9r` E-13 | The gate lacked a scope fence, stop conditions and conditional finalize ownership; E-13 duplicated the orchestrator's item. | Overall:Low | FIXED | Gate rewritten; E-13 states attended finalize ownership and commits the changelog. |
| PR-016 | LOW | IN-SCOPE | Proofreading / live counts | Concern "all 12"; F-02 "open"; V-02 "34-row" | Stale counts and a live count used as a bar. | Overall:Low | FIXED | Re-measured; bar re-derived at execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who builds `aw meta repair` and SR-601? | The siblings that already plan them | Build them twice here | `ffceq0` E-11; `2xwb9b` E-12 | yes |
| D-2 | When are the sidecar ignore line, INDEX files and `STATUS.md` removed from this repository? | By migration steps 2 and 5 | In E-04 before the migration | Spec 5.2 steps 1, 2, 5; `dcerjg` E-06, E-11 | yes |
| D-3 | How does one commit hold the migration and the code? | Spike E-17 on a copy, with a stop condition for the maintainer | Pick a mechanism at review without a demonstration; two commits (breaks C10a) | S5 HOW rule 3; spec 5.2 step 7; C10a | yes |
| D-4 | What does the pre-migration test gate require? | Pass except listed unmigrated-records refusals; full green on the migrated copy | Full green before migration (unsatisfiable) | `dcerjg` OQ on `CURRENT_METADATA_SCHEMA`; `tests/test_attention.py` | yes |
| D-5 | Do `Kind` option renames keep the old spelling? | Yes, as aliases | Hard rename | `cli.py` `--kind` alias of `--work-kind`; spec 5.4 | yes |
