# Review findings: plan n5sxxk

- Subject-Id: n5sxxk
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-4-carbon
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at starting HEAD `9af25dfe7` in the isolated runner review-sweep lane `review-sweep-run-20261114T011656Z-594596`. The target plan `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` em-dash advisories on line 111), and all twelve family test modules passed (`217 passed in 5.85s`). After revision (including `E-04`/`V-04`, `- Highest E allocated: 04`) and Pass 2 re-review, both `aw ipd lint --phase author --agent` and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope | Bare module names in `rg -c` summary and omitted round-3 `--summary` and merge-test carriers | Names full `agent_workflows/*.py` paths, adds `E-04` to scope, and cites `b4y4ee`, `fekdwv`, `bir7xm`, `py2vu9` and `h06gs7` | PR-002, PR-003, PR-004 |
| Checklist preamble | Pre-split `PIN-FIRST RULE` instructing `.aw/state/n5sxxk/<E>-before.txt` and citing missing `D-1 to D-6` | Clarifies that per-part PIN-FIRST diffs run in `s95hj6`, `ernmom` and `x2dxvf`, while this plan modifies no Python or test source and stops on any part defect | PR-003 |
| E-03, V-03, F-04 | Two copy-pasted `Workflow history` and `f"- \{(date\|today\|hdate)\} "` greps that already return zero writer hits before any move | Four-check `rg` audit across all five modules (`artifact_meta` positive delegation, `atomic_write`/`write_text`/`git_mv` raw writes including `research_cmd.py` and `artifact_adopt.py`, history literals, and bullet/YAML/`aw-prompt` builders) recorded in `F-04` | PR-001 |
| E-04 (new), V-04 (new), Required tests | Omitted post-merge family pytest and core-gate runs that `s95hj6`, `ernmom` and `x2dxvf` deferred to `n5sxxk` | Runs all twelve family test modules together plus bare `python3 -m pytest` within the 30 s budget | PR-002 |
| Step 0, Findings (`F-01`..`F-03`), Behavior decisions (`D-1`, `D-2`) | Falsely claimed `n5sxxk` adds `write_legacy`, omitted `research_cmd.py` and `artifact_adopt.py` from `F-01`, cited `specs._append_history` and missing `E-05` in `D-1`, and used bare `module.func` citations | Attributes `write_legacy` to `7yr827`, records all 18 pre-move raw writes across the five modules in `F-01`, frames test counts as non-binding pointers in `F-02`/`F-03`, scopes `D-1` to this family's history-bearing types, and upgrades citations to `path::Symbol` | PR-003, PR-004 |
| Proposed changes, Deferred | Listed merge-independence test under `Carrier: xexn45` and had no diagram | Splits merge-independence test to `Carrier: b4y4ee` and adds a Mermaid `flowchart TD` diagram of the three parallel writer moves, `E-03` audit stop branch and `E-04` gate | PR-003, PR-004 |
| Validation preamble, Approval gate | Contained two em dashes (`IPD-C802`), stale PIN-FIRST move clause, and no missing-prerequisite or conflict stop clause | Replaced em dashes with commas, reconciled the honesty rule with `E-03`/`E-04`, and added the prerequisite/conflict stop clause | PR-002, PR-003, PR-004 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Although `n5sxxk` edits only its own plan record (`F-04`), seven downstream `metastore` plans (`fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`, `6e93gt`, `b4y4ee`, and `xexn45`) depend on `executed:n5sxxk` as the contract proof that all eleven writers across the five modules write through `artifact_meta`.
2. No. `- Scope-Paths:` contains only this plan file; `E-03` and `E-04` audit and test the five modules without modifying commit, lock, isolation, or sanitizer code.
3. Yes. It coordinates five writer modules across four metadata formats (plan bullets, walkthrough/backlog bullets, research YAML front matter, and `aw-prompt` HTML comments) integrated from three parallel sibling plans (`s95hj6`, `ernmom`, `x2dxvf`).
4. Yes. `- Scope-Paths:` explicitly names `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md`.
5. Yes. A tautological audit (`PR-001`) or missing post-merge test gate (`PR-002`) would let unmoved hand-built writers or conflicting parallel `artifact_meta.py` edits from `s95hj6`, `ernmom`, and `x2dxvf` pass silently into downstream `--summary` writers and the Order 13 cutover (`cxxmyv`).

AW-TIER: complex

### Step R1

- Checked: every code symbol, test module, and record cited by `n5sxxk`: `agent_workflows/ipd_authoring.py` (`_gate_body`, `build_skeleton`, `_atomic_write`, `run_scaffold`, `compute_sync`, `insert_id_line`, `backfill_plan_ids`, `run_sync`), `agent_workflows/set_records.py` (`write_local_projections`, `render_walkthrough`, `write_walkthrough`, `promote_question_to_backlog`, `close_on_answer`, `_extract_body`), `agent_workflows/research_cmd.py` (`build_frontmatter`, `_atomic_write`, `plan_new`, `plan_new_comparison`, `_emit_and_write`, `update_frontmatter_fields`, `run_set_outcome`, `_set_priority_line`, `run_set_priority`, `run_new`, `run_new_comparison`), `agent_workflows/artifact_adopt.py` (`plan_adoption`, `apply_adoption`), `agent_workflows/prompts.py` (`render_metadata_comment`, `has_metadata_comment`, `read_metadata_id6`, `inject_metadata_id6`, `read_metadata_status`, `update_metadata_status`, `run_new`), `agent_workflows/artifact_meta.py` (`read`, `append`, `create`, `render_legacy`, `append_legacy`), all 16 cited test files (`12` family modules + `4` Step-0/D-1/D-2 reference modules), spec `4sd62s` (4.2b, 4.3, N3, section 7 step 4), spec `2vev8j` (superseded, 4.4), IPD `2yqt0a`, backlog `a88210`, research `nj8zdp`, and sibling plans `tve77h`, `2xwb9b`, `7yr827`, `g6tw94`, `s95hj6`, `ernmom`, `x2dxvf`, `6e93gt`, `fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`, `b4y4ee`, `xexn45`, `63ib9r`.
- Found false/stale claims in `Step 0` (`this plan adds write_legacy`, actually `7yr827`), `F-01` (omitted `research_cmd.py` and `artifact_adopt.py` raw writes and misattributed `set_records.py` to `xexn45` E-14 instead of E-15), `D-1` (copied `specs._append_history` and non-existent `E-05`), and `Deferred` (`b4y4ee` merge test attributed to `xexn45`) (`PR-003`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`E-03` <-> `V-03`, `E-04` <-> `V-04`; `- Highest E allocated: 04`, with `01` and `02` previously allocated and moved in round 3), `- Scope-Paths:` completeness (only this plan is edited at execution time to fill `F-04`), `- Item-Dependencies:` (`tve77h` and `2xwb9b` verified under `executed/`; `7yr827` reviewed; `g6tw94`, `s95hj6`, `ernmom`, `x2dxvf` under `pending/`), non-tautological evidence in `V-03` and `V-04`, and non-binding test-count framing in `F-02`/`F-03`.
- Fixed tautological `E-03`/`V-03` evidence (`PR-001`) and missing `E-04`/`V-04` post-merge family regression and core-gate execution (`PR-002`).

### Step R3

- Checked: full security and privacy rubric. `n5sxxk` performs no network calls, privilege overrides, or production code edits; its safety role is preventing unmigrated metadata writers from bypassing `artifact_meta.validate_new_events` string/path validation (`spec 4sd62s` 4.2, `attention_contract.refuse_unsafe_descriptive`, `artifact_adopt.scan_drop_for_leaks`, prompt single-line comment purity). Strengthening `E-03` (`PR-001`) ensures none of the eleven writers bypasses `artifact_meta` validation.

### Step R4

- Checked: correctness and non-tautological audit coverage across all four metadata formats (`PR-001`), post-merge verification of the three parallel `artifact_meta.py` branches (`PR-002`), preservation of kept legacy behaviors (`D-1`, `D-2`), right-sizing (`E-03` static audit and `F-04` table update; `E-04` runtime regression and core-gate verification — two focused single-concern items), and truthful `Spec / documentation sync` (phase-B behavior is unchanged; `--summary` docs and `CHANGELOG.md` are verified in `h06gs7` and `xexn45` E-16).

### Step R5

- Checked: QA/QC (eliminated vacuous grep audit that passed on unmodified pre-move code), testing/regression (added combined 12-module `217`-test family suite + core gate after parallel `artifact_meta.py` merges), UI/UX (no user-facing change), architect (closed the `research_cmd.py` and `artifact_adopt.py` audit hole left by `xexn45` E-14/E-15), software engineer (removed stale `PIN-FIRST` / `E-05` instructions and clarified acceptable `F-04` hit classes including `xexn45` F-08 thin adapters), power user, novice, and stakeholder.

### Step R6

- Checked: decomposition and sizing. The plan was already decomposed in round 3 (`2026-11-09`) into `s95hj6`, `ernmom`, and `x2dxvf`; the remaining finishing plan has 2 focused `E-*` items in 1 task group and 1 `- Scope-Paths:` entry (`0` lint advisories). No further split is warranted.

### Step R7

- Checked: orchestrator `63ib9r` (`E-23` / `V-23`, Order 23 row), upstream prerequisites (`tve77h`, `2xwb9b`, `7yr827`, `g6tw94`, `s95hj6`, `ernmom`, `x2dxvf`), and downstream dependents (`fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`, `6e93gt`, `b4y4ee`, `xexn45`). Confirmed zero sibling plans reference `n5sxxk` internal `E-*` IDs (`03` or `04`).
- Cross-plan notes for sibling reviewers (outside `n5sxxk`'s authorized scope): (1) `s95hj6` E-01 (`20261109-metastore-122-s95hj6-...:41`) also uses the vacuous `rg -n "Workflow history" agent_workflows/research_cmd.py` check even though `research_cmd.py` uses YAML front matter and never mentions `Workflow history`; (2) `s95hj6:77-78`, `ernmom:84-85`, and `x2dxvf:82-83` list whole-move items (merge-independence test, AC-21, F-09, docs, full gates) under `Carrier: n5sxxk`, whereas `b4y4ee` and `xexn45` own those after `n5sxxk`; (3) `xexn45` E-14 and E-15 omit `research_cmd.py` and `artifact_adopt.py` from F-09's ten-module raw-write audit, which `n5sxxk` `E-03` now covers in `F-04`.

### Step S5

- Checked: open questions and decisions. No pre-existing or new human-owned open questions exist; all findings (`PR-001`..`PR-004`) have Low Remediation Risk and were fixed in place. Decisions `D-1`..`D-3` below record the reviewer's evidence-grounded choices (all reversible).

### Pass 2

- Re-reviewed `E-03`, `E-04`, `V-03`, and `V-04` per `steps/s6-rereview.md` rule 1 because `E-04` and `V-04` were added (`- Highest E allocated: 04`).
- Swept superseded tokens (`D-1 to D-6`, `E-05` outside `xexn45` E-05 provenance, `specs._append_history` in `D-1`, `.aw/state/n5sxxk`, `Add further leaves`, and em/en dashes): zero stale occurrences remain. Both `aw ipd lint --phase author --agent` and `aw ipd lint --phase review-finalize --agent` report `clean` with `0` findings.
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2, R4-D, R4-E / E-03, V-03, F-04 | `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md:40`, `:114`; `agent_workflows/ipd_authoring.py:251`; `agent_workflows/set_records.py:410`; `agent_workflows/research_cmd.py:74`, `:571`; `agent_workflows/artifact_adopt.py:866`; `agent_workflows/prompts.py:310`, `:608`; `.aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md:49`, `:54` | `E-03` and `V-03` copied `g6tw94`'s `Workflow history` and `f"- \{(date\|today\|hdate)\} "` greps, which already return zero writer hits on unmodified pre-move code (only two docstrings match, because these five modules build YAML front matter, `aw-prompt` comments, `- Field:` bullets, or call `backlog._render_item` + `atomic_write`), making `V-03` tautological and leaving `research_cmd.py` and `artifact_adopt.py` raw writes unaudited by `xexn45` E-14/E-15. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the vacuous grep pair with a four-check `rg` audit across all five modules: (1) positive `artifact_meta` call presence in every module (`0` hits pre-move), (2) `atomic_write`/`write_text`/`git_mv` raw writes across all five modules, (3) history literals, and (4) bullet, YAML front-matter, and `aw-prompt` builders, with every remaining hit justified in `F-04`. Recommendation strength: very strong. |
| PR-002 | MEDIUM | UNDER-SCOPE | R2, R4-E, R7 / E-04, V-04, Required tests | `.aw/records/plans/pending/20261109-metastore-122-s95hj6-move-the-research-create-and-setter-writers-onto-artifact-me.ipd.md:77-78`; `.aw/records/plans/pending/20261109-metastore-123-ernmom-move-the-plan-scaffold-plan-sync-and-prompt-create-writers-o.ipd.md:84-85`; `.aw/records/plans/pending/20261109-metastore-135-x2dxvf-move-the-adopt-and-set-records-create-and-setter-writers-ont.ipd.md:82-83`; `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md:99`, `:128` | `s95hj6`, `ernmom`, and `x2dxvf` modify `artifact_meta.py` in parallel and defer the family finish and core gate to `Carrier: n5sxxk`, and `n5sxxk`'s own honesty rule demands running the named modules and `python3 -m pytest`, yet `n5sxxk` had no `E-*`/`V-*` item running the 12 family test modules or the core gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `E-04` and `V-04` (`- Highest E allocated: 04`) running all 12 family test modules (`217` tests) and bare `python3 -m pytest` within the 30 s budget, and reconciled `Required tests / validation` with the gate. Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1, R7 / Scope, Checklist preamble, Step 0, F-01..F-03, D-1, Deferred | `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md:36`, `:49`, `:66`, `:73`, `:89-90`; `.aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md:119-120` | Stale pre-split copy-paste claimed `n5sxxk` adds `write_legacy` (`7yr827` owns it), instructed `.aw/state/n5sxxk/<E>-before.txt` move diffs and cited missing `D-1 to D-6` / `E-05` / `specs._append_history`, omitted `research_cmd.py` (5 hits) and `artifact_adopt.py` (1 hit) from `F-01` while miscounting `ipd_authoring._atomic_write`, and attributed `b4y4ee`'s merge-independence test to `xexn45`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Scope`, the checklist preamble, `Step 0`, `F-01`..`F-03` (recording all 18 raw writes across the five modules and non-binding test counts), `D-1`, and `Deferred` (`Carrier: b4y4ee` for the merge test). Recommendation strength: very strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading, S7 / Proposed changes, Validation preamble, Approval gate | `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md:45`, `:49-60`, `:76-80`, `:111`, `:124` | Line 111 had two `IPD-C802` em dashes, line 45 left scaffold `E-NEW` boilerplate, citations used bare `module.func` instead of `path::Symbol`, `Proposed changes` lacked a Requirement 12 diagram for the 5-module / 3-part branching audit flow, and `Approval gate` lacked a prerequisite/conflict stop clause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with commas, removed `E-NEW` boilerplate, upgraded citations to `path::Symbol`, added a Mermaid `flowchart TD` diagram, and added the missing-prerequisite/conflict stop clause. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `E-03` audit five modules spanning four metadata formats (plan bullets, walkthrough/backlog bullets, research YAML front matter, and `aw-prompt` HTML comments) without being tautological or duplicating code edits? | Run four `rg` checks across all five modules—positive `artifact_meta` call presence (`>=1` per module), `atomic_write`/`write_text`/`git_mv` raw writes (including `research_cmd.py` and `artifact_adopt.py`), history literals, and bullet/YAML/`aw-prompt` builders—recording every remaining hit and reason in `F-04` and stopping if any of the 11 moved writers bypasses `artifact_meta`. | Keep the two `Workflow history` / `f"- \{(date\|today\|hdate)\} "` greps (rejected: tautological—already zero writer hits on unmodified `HEAD 9af25dfe7`, and leaves `research_cmd.py` and `artifact_adopt.py` raw writes unaudited); edit the five modules in `n5sxxk` (rejected: violates the round-3 split scope owned by `s95hj6`, `ernmom`, `x2dxvf`). | `agent_workflows/ipd_authoring.py:251`, `agent_workflows/set_records.py:410`, `agent_workflows/research_cmd.py:74`, `:571`, `agent_workflows/artifact_adopt.py:866`, `agent_workflows/prompts.py:310`, `:608`; `.aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md:49`, `:54`, `:96`; `steps/r2-executability.md` | yes |
| D-2 | Should `n5sxxk` execute the 12 family test modules and bare `python3 -m pytest` core gate in addition to the static `rg` audit? | Yes: add `E-04`/`V-04` running all 12 family test modules (`217` tests) plus bare `python3 -m pytest`, while keeping whole-move tests and docs deferred to `b4y4ee` and `xexn45`. | Leave `n5sxxk` as a grep-only check (rejected: `s95hj6`, `ernmom`, and `x2dxvf` touch `artifact_meta.py` in parallel and explicitly defer the family finish and core gate to `Carrier: n5sxxk`, and `n5sxxk`'s own gate requires pasting the named modules and `python3 -m pytest`). | `.aw/records/plans/pending/20261109-metastore-122-s95hj6-move-the-research-create-and-setter-writers-onto-artifact-me.ipd.md:77-78`, `.aw/records/plans/pending/20261109-metastore-123-ernmom-move-the-plan-scaffold-plan-sync-and-prompt-create-writers-o.ipd.md:84-85`, `.aw/records/plans/pending/20261109-metastore-135-x2dxvf-move-the-adopt-and-set-records-create-and-setter-writers-ont.ipd.md:82-83` | yes |
| D-3 | How should `n5sxxk` handle the inherited `PIN-FIRST RULE` and `D-1` (`specs._append_history`, `E-05`) prose from before the round-3 split? | Replace the move-specific `PIN-FIRST` instructions with an audit-only scope note pointing at `.aw/state/<part-id6>/`, and scope `D-1` to history-bearing record types in this family (plans, walkthroughs, backlog items, and prompts). | Keep the copied `specs._append_history` and `.aw/state/n5sxxk/<E>-before.txt` text (rejected: contradicts `n5sxxk`'s zero-code `- Scope-Paths:` and references a non-existent `E-05`). | `.aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md:7`, `:24` | yes |
