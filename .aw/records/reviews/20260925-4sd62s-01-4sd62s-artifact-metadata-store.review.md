# Review findings: spec 4sd62s

- Subject-Id: 4sd62s
- Subject-Type: spec
- Reviewed-At: 2026-10-26
- Reviewer: Codex/unknown
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-001 | blocker | UNDER-SCOPE | D (decisions) / G (plannable) | 4.2 path rule `meta/<id6>.jsonl`; `.aw/records/reviews/README.md` "Naming"; 338 of 338 review files reuse their subject's id6, 0 carry an own `- Id:` | A review record and its subject would claim the SAME log file. Review filenames deliberately reuse the reviewed artifact's id6, yet 4.2 keys logs on id6 and its field list named `subject-id/type (reviews)`, implying reviews get a log. The second writer would corrupt or refuse the first's history. Unaddressed anywhere in the spec. | C:Medium;U:Low;S:Low;F:High;Overall:Medium | fixed | Maintainer decision 2026-09-25 (asked): reviews get no log; each round is an `op: review` event in the SUBJECT's log. Added 4.1a, `review` to the op list, a round-count drift rule in 4.6, AC-14, and OQ-5 (resolved). |
| SR-002 | high | UNDER-SCOPE | F (compatibility) / D | 5.2 step 4 rewrites every artifact; AGENTS.md "Do NOT add commits to a plan already in `.aw/records/plans/executed/`"; `hooks/executed_transition_gate.py`; 1055 terminal-directory files at review | The single-commit migration rewrites every terminal artifact, which the repo's own rule forbids and the executed-plan hook partly enforces. The spec never mentions the conflict, so an implementer hits the hook or bypasses it with `--no-verify`. | C:Medium;U:Low;S:Medium;F:Medium;Overall:Medium | fixed | Maintainer decision 2026-09-25 (asked): rewrite them as a named one-time exception. Added 5.2 step 4a (journaled marker the hook accepts, no `--no-verify`, still refuses later edits, AGENTS.md amended), AC-16, an honest-limit on `git blame`, OQ-6 (resolved). |
| SR-003 | high | IN-SCOPE | A (current measurements) / G | section 1 table; 5.2 step 3; `aw rename --help` (`--to-id6` converts only `YYYYMMDD-HHMM-NN-<slug>` names) | The "542 records have no `- Id:`" figure drives migration step 3 but is the wrong population: re-measured, 549 lack the BULLET yet only 64 lifecycle records lack an id6 in any form; 339 of the 549 are reviews, which must not get one. Step 3 also assumes `aw rename --to-id6` can mint ids for all of them, but it handles only legacy timestamp names. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Section 1 row and 5.2 step 3 rewritten with the review-time counts by type, reviews excluded, and an instruction that the plan name a minting path for non-legacy names. |
| SR-004 | medium | IN-SCOPE | A | section 1 table vs `rg -l "## Workflow history" agent_workflows` (23 files); history sidecar 306 records | Several load-bearing counts were stale or low: history-referencing modules ~13 (measured 23), `v1.3.0-rc.1..HEAD` 4050 (4125), sidecar "176+" records (306, of which 240 backlog). The migration's preflight also did not account for the sidecar existing on only one machine. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Counts updated in place with authoring and review values; 5.2 step 2 now names the 306 records and requires the preflight to report sidecar presence and refuse without `--force` when it is expected but absent. |
| SR-005 | medium | IN-SCOPE | B (testable) / G | O1 row and 4.4 "The 6 HEAD-vs-staged code paths"; `rg` finds `hooks/ipd_dependency_statement_gate.py` and others reading HEAD/staged content | "6 code paths" was presented as an inventory but omits at least `ipd_dependency_statement_gate`, so a plan built from it would leave a gate reading `- Status:` after cutover. | C:Low;U:Low;S:Medium;F:Medium;Overall:Low | fixed | List extended and labeled a FLOOR; plan step 5 must re-derive the full set by search and record each consumer's disposition. |
| SR-006 | medium | UNDER-SCOPE | D / G | 4.4 IPD-M107 bullet; `plan-review.md` "Write the structured `Readiness` field"; `aw --help` has no plan-review verb | "`readiness` can only be set by a `plan-review` event" had no mechanism: plan-review is an agent workflow that hand-writes `- Readiness:` today, not an aw verb that can emit an event. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.4 now ties readiness to an `op: review` event in the same append (4.1a), states that the review workflows change to a tooled recording command named in plan step 4, and covers `aw ipd recheck-readiness`. AC-15 added. |
| SR-007 | medium | UNDER-SCOPE | F | 4.5 "Resolved via `git rev-parse --git-common-dir`"; `project_context.resolve_project_context`; `runner_shared.state_root`; `records_backend` companion/home | The cache and log locations assumed `<repo>/.aw/`, ignoring the shipped companion/home records backends that place records outside the repo. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.5 now resolves through the project-context authority and states logs live under the resolved records root; AC-18 added. |
| SR-008 | medium | IN-SCOPE | D | OQ-4; `2vev8j` C8, AC-11, C4, 4.5 vs this spec's C9 and 4.1 | The amendment relationship understated a direct contradiction: `2vev8j` REQUIRES incremental migration and a valid partially migrated corpus, which C9's hard cutover forbids. The relation line did not list C8/AC-11 as replaced. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Relation line now lists C8 and AC-11 as replaced; OQ-4 states the amendment must say C9 supersedes them, citing the 2026-09-25 rulings. |
| SR-009 | medium | UNDER-SCOPE | C (coverage) | 4.7 same-artifact conflict; 3c limit; no AC covered it | The same-artifact concurrency path (the only non-clean merge case) had no acceptance criterion, and the status-mirror line collides alongside the log tail. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | AC-17 added; 4.7 now names the front-matter mirror collision. |
| SR-010 | low | IN-SCOPE | G | 4.8 "Add `aw show`"; `aw show --help` (exists, no `--history`); 5.1 `aw migrate metadata` vs existing `aw migrate-layout` | `aw show` already exists, so "add" risks a second command; `aw migrate` does not exist while `aw migrate-layout` does, giving two migration spellings. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.8 says EXTEND `aw show`; 5.1 requires the plan to decide the migrate spelling, citing research `ffi66q`. |
| SR-011 | low | IN-SCOPE | F (honest limits) | 3c; `aw attention` stranded-lane surface (gitignored `.aw/records/runs/`); review findings tables stay prose | Honest limits did not say C2 covers records only (not run/lane state), nor that review findings tables stay hand-editable after the verdict moves to the log. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Three limits added to 3c. |
| SR-012 | low | IN-SCOPE | A | `runner_shared.py:5317` and `selectors.py:112-120` citations | Two citations were bare line offsets that had already drifted (`integrate_lane_branch` is now at 5477). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Replaced with symbol citations (`runner_shared.integrate_lane_branch`, the `_STATUS_RE` parity note). |
| SR-013 | low | IN-SCOPE | D | 4.2 `from`/`to` "validated against the lifecycle table"; only specs and plans have enforced tables | Implied every type has a transition table; backlog, research, prompts, and releases validate the value only, and N2 forbids inventing tables. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.2 now says per-type table where one exists, value-only otherwise, citing N2. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Should an explicit Blocks-Release be added to this spec? | No; left absent. | Adding `Blocks-Release: next`. | The spec asserts no release gate and 2.0.0 gating is a scope decision reserved to the maintainer; nothing in the repo marks it as a blocker. | yes |
| D-2 | Is the `5.2` claim that this migration must reuse `layout_migration.MigrationManager` sound? | Yes, kept. | A new transaction engine. | `MigrationManager` already provides the journal, writer lock, and rollback the spec needs; the 72qlya/vv6y7e work shows it is live. | yes |
| D-3 | Should the two-key front-matter decision (F2) be revisited given review records now carry `subject`/`subject_type` instead of `id`? | No; F2 stands for lifecycle records, reviews are a named variant in 4.1a. | A third key for all types. | F2 was a maintainer decision (2026-09-25) and 4.1a narrows only the review shape. | yes |

## Round 2

Re-review requested by the maintainer on 2026-10-24 to check the spec against the current toolkit (HEAD `46ab9fdbf`, about 7950 commits after round 1). Structural preflight `aw specs check` was clean before and after the edits. Every measured claim was re-derived; the four maintainer decisions are marked.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-101 | high | UNDER-SCOPE | D (decisions) | spec 4.3 `read(id6)` replayed the log; only find/attention/board used SQLite (4.5 "Replaces") | The maintainer requires that every tool read metadata from SQLite and that logs only feed the cache. The spec did not guarantee this: per-artifact reads and every gate replayed logs directly. | C:Medium;U:Low;S:Low;F:Medium;Overall:Medium | fixed | Maintainer decision 2026-10-24 (asked). Added C5a, AC-1a, the 4.3 loader-only rule, staged/HEAD reads via blob-sha-keyed cache rows (`read_at`), the authority-on-disagreement rule, the 4.5 role statement, two honest limits, OQ-7. |
| SR-102 | high | IN-SCOPE | D / G (plannable) | `2vev8j` C8, AC-11, C4, 4.5 still in force; no pointer to this spec; OQ-4 never executed | Two approved specs governing the same subject contradicted each other (incremental vs hard cutover), so no plan could satisfy both. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision 2026-10-24 (asked): supersede `2vev8j`, fold its 4.4 (as amended 2026-10-13) and 4.7 into new 4.2a/4.2b; OQ-4 resolved with the retirement, citation re-pointing (16 files), and `ms06pi` gate re-homing assigned to the first plan. |
| SR-103 | high | UNDER-SCOPE | G | section 7 "4-6 land together on one branch"; `runner_shared.integrate_lane_branch` merges each item; 49 modules, 268 test files, runner_shared.py 52,534 lines | The prescribed order required a single unmerged branch spanning writers, readers and parser deletion; the runner merges per plan, so `main` would be dual-format or broken between plans, and the combined change exceeds one session. | C:Medium;U:Low;S:Low;F:Medium;Overall:Medium | fixed | Maintainer decision 2026-10-24 (asked): facade-first. Section 7 rewritten as phases A/B/C; C10a and AC-1b added; honest limits on phase-B testability. |
| SR-104 | high | UNDER-SCOPE | D / F (compatibility) | 13 `20261024-specflow-*` review records carry their own id6 (subject `18hh1u`); `18hh1u` 6.3 verdicts; 28 of 1271 verdicts outside `plan_readiness.VERDICTS` | 4.1a assumed every review reuses its subject id6 and uses an approval verdict; the refinement pipeline breaks both, and the migration would refuse or guess 28 verdicts. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision 2026-10-24 (asked): typed review kinds `gate`/`refinement`, own id6 kept as `review_ref`, legacy verdicts verbatim. 4.1a round-2 amendment, AC-14a, OQ-9. |
| SR-105 | high | IN-SCOPE | F | `2vev8j` 4.4 (amended 2026-10-13, `hinpcf`); `plans_archive._age_days`; `check_engine._DATE_LINE_RE`; `config.applies_to_artifact_date`; 8 `cutovers` in `.aw/config/project.json` | The 4.6 rule "filename date must equal `create.at` day" compared a LOCAL filename date with a UTC timestamp, the exact mixed-clock error the reader-clock rule forbids; every evening creation would drift, and date-based cutover grandfathering had no stated source after `- Date:` leaves front matter. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | New 4.2b: a LOCAL creation `date` field in the log, the drift rule compares against it, every `- Date:` reader is named and re-pointed with its clock unchanged; AC-19. |
| SR-106 | medium | UNDER-SCOPE | C (coverage) / F | `25kzda` 2.5e + `coverage_record.py` + `IPD-M112`; `k3yx72` 12 `Review-Depth`; `4iyd78` `Pipeline`; `Scope-Exceeded` (40), `Close-Evidence` (55), `Attended`, `Findings` (431 reviews), `Release-Exempt-*` | Fields and one attestation (coverage, same shape as Readiness) added since round 1 were absent from the registry list; the coverage attestation would remain forgeable. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | New 4.2c registry obligations table, `op: coverage` event and M112 rewrite in 4.4, M113/`l56tyz` ported, AC-20 census. |
| SR-107 | medium | IN-SCOPE | A (measurements) / G | `status_set._prepare_status_change`; `plan_readiness.review_staleness_index`; `agent_workflows/hooks/backlog_blocking_close_gate.py`; `artifact_audit.FinalizeEvidenceIndex` reads commit subjects | The HEAD/staged inventory omitted at least four content readers, mis-listed `artifact_audit`, and gave the wrong hooks path. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.4 inventory re-derived and dispositioned, still labeled a floor; `leak_sanitizer` must scan logs. |
| SR-108 | medium | UNDER-SCOPE | C | `Carrier-Declined: owned by spec 4sd62s` in plans `me227c`, `wja06w`, `pw2ln3`, `l56tyz`, `fhinri`; `Carrier: 4sd62s` in `63zo2f`; backlog `6tjye0` retired moot | Executed plans handed obligations to this spec that it never recorded, so they would be silently dropped. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | New 4.4a inherited-obligations table and AC-21. |
| SR-109 | medium | IN-SCOPE | A | section 1 and section 6 tables; e.g. records 1969 -> 4374, terminal 1055 -> 2828, INDEX files 4 -> 6 (`prompts_index.py`), sidecar 306 -> 408, parsers ~9 -> 11+ | Nearly every load-bearing count was stale, several by more than 2x, and new parsers and a third INDEX producer were missing. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Both tables re-measured with round-1 values bracketed; 4.5, 5.2 steps 2/3/4a/5 and 6 updated (prompts INDEX, `placement_switch.py`). |
| SR-110 | medium | IN-SCOPE | A | `59t9x5`, `8cpbia`, `hg2oop` all `done`; `attention_contract.newest_history_record`; `BACKLOG_TRANSITIONS` (`cc2m29`) | Claims that this spec subsumes or fixes already-closed items, that `last_history_at` is still wrong, and that backlog has no transition table were obsolete. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | P5 rebased on whole-corpus rescans; 4.4 notes the port; 4.2 lists current tables; benefits paragraph corrected. |
| SR-111 | medium | UNDER-SCOPE | F | specs `k3yx72` 12, `4iyd78` 6.1, `wy9aru` 3a/4.3, `18hh1u`, `yfz5u9` R-72/R-90 | Five specs written since round 1 interact with this one and none was named; `wy9aru` keeps the sidecar this spec retires. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | New section 9 compatibility table; 4.8 names the `wy9aru` engine and sidecar retirement. |
| SR-112 | low | IN-SCOPE | F | unsafe-descriptive-value refusals `uz05bl`, `deftzy`, `dtg7dz`, `xnogdl` | Moving Summary/Scope to body sections would leave the injection refusals with no stated home. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.2 states the refusals move with the field and also cover every log and front-matter string. |
| SR-113 | low | IN-SCOPE | B (testable) | AC-1 "a test enforcing it"; repository rule against source-reading tests; plan OQ rows' `Carrier` bullets | AC-1's enforcement test as written invited a code-pinning test, and its `rg` would match body-prose bullets N3 keeps. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | AC-1 requires a behavioral test and an explicit exclusion list. |
| SR-114 | low | IN-SCOPE | A / G | `19313eed` suites re-added 2026-10-16/17; `project.json` `schema_version: 2`; `aw set` has no `--priority`; `ffi66q` is an inventory at `todo`; roadmaps, prompt-library, `.data/` dirs | Several small facts were stale or unnamed. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 5.1, 5.4 and 4.1 corrected; distinct stamp key required. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-4 | Does the pause on other work remove the need for facade-first? | No; facade-first kept for per-step proof, fixture consolidation and session size. | One switch-over plan; long-lived side branch. | Maintainer chose facade-first after the reasons were stated; the runner merges per plan (`runner_shared.integrate_lane_branch`). | yes |
| D-5 | Must the cache update be atomic with the log write? | No; log and front-matter mirror are atomic, the cache is best-effort and reloads on the next read. | Fail the write when the cache update fails. | C6 concerns the durable record; a gitignored cache failure must not block a durable write (AC-8). | yes |
| D-6 | Are `18hh1u`/`yfz5u9` draft fields pre-registered? | No; whichever lands second conforms. | Pre-register them now. | Both are `draft` and may change; registering unreleased fields would pin a draft's design. | yes |
| D-7 | Is `yfz5u9`'s `events.jsonl` in scope? | No; it is a run log, covered by N4. | Unify it with artifact logs. | N4 excludes run records. | yes |

## Round 3

Re-review requested by the maintainer on 2026-10-24 (HEAD `46ab9fdbf` plus `f276c9d9b`, the round-2 hardening). Round 2 was authored by this same reviewer in this same session, so this round deliberately targeted internal consistency and the soundness of the round-2 additions rather than re-deriving round 2's findings. `aw specs check` was clean before and after the edits. No question needed the maintainer: each was settled from repository evidence, and the evidence is cited on each row.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-201 | high | UNDER-SCOPE | F (failure modes) / G | `record_history.history_path` (`project_records_dir(repo_root) / "history.jsonl"`); `.aw/.gitignore` sidecar line; runner isolated worktrees (`isolate_worktree`) | The sidecar holding the only copy of 408 records exists only in the main checkout, and a runner lane worktree has none. The cutover plan, run by the runner as usual, would hit the sidecar-absent refusal, or lose records if `--force` were used. Neither the spec nor section 7 said where the cutover runs. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 5.2 step 1 and section 7 step 9 now require the cutover to run attended in the checkout holding the sidecar, under the integration lock, and to refuse in a lane. New honest limit and AC-22. |
| SR-202 | high | IN-SCOPE | D / B (testable) | 1273 review files: 1149 with one round, 124 with two or more, but each file has ONE `- Verdict:`; 5 subjects reviewed by several files (`18hh1u` by 16) | Round 2's migration and drift rules were unsound on the real corpus. They gave each round its own verdict, while a file's single verdict line cannot be assigned to earlier rounds without inventing data. And "the file's round count equals the subject's review events" fails whenever one subject has several review files. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.1a point 5a: the file's verdict goes on its last round only, and earlier rounds get `legacy_verdict: null`. Point 4 and 4.6: round counts are attributed per (subject, file) via `review_ref`. |
| SR-203 | medium | IN-SCOPE | A | `rg` of Subject-Id vs filename id6: 20 mismatches (18 `specflow`, plus `dcri4s` and `bbxvpq` records) | Round 2 stated that 13 records carry their own id6 and that all other reviews are gate reviews reusing the subject id6 (1257). Re-counted, there are 20, two of which are gate reviews, so a rule keyed on "refinement" alone would mishandle them. Round 2's table also gave a verdict breakdown that summed to 25 of the 28. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 1 row re-counted. 4.1a point 4 now covers ANY review record whose filename id6 differs from its subject. Verdict list worded "among them". |
| SR-204 | medium | IN-SCOPE | B / C | AC-1a vs 3c "testable only from the cutover commit"; AGENTS.md repository suite contract (core tier merge gate vs `make test-all`) | AC-1a's evidence could not be produced during phase B, and C10a's "the full suite passes at every commit" did not say which tier, although this repository has two with different budgets. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | AC-1a has a cutover form and a phase-B form, and its mechanism changed from "make unreadable" to counting opens. C10a/AC-1b: core tier at each merge, thorough tier at each phase end and at the cutover. |
| SR-205 | medium | UNDER-SCOPE | F | 4.3 "Every public read function first brings the cache up to date" | The freshness rule implied about 7,500 stats per corpus-wide read, with no statement of cost or of which shortcuts are safe. A natural shortcut (directory mtimes) is UNSAFE, because an in-place file edit does not change its directory's mtime. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.3 "STALENESS CHECK COST" states the baseline, a never-stale bar for any shortcut, the two shortcuts that fail it, and AC-13 as the measure. |
| SR-206 | medium | IN-SCOPE | D | section 7 step 8 "in the cutover commit or immediately before it"; C10a | Docs landing before the cutover would describe verbs and a storage model that `main` does not yet have, contradicting C10a. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Step 8 now lands IN the cutover commit, with the reason. Section 7 also places the 2vev8j supersession first and states how a `k3yx72`/`4iyd78` plan landing mid-Set adds a field. |
| SR-207 | low | IN-SCOPE | A / D | Scope line; O1/O2 rows; N2; section 6 duplicated table header; 5.2 step 4a long line; `v1.3.0-rc.1..HEAD` 12,133; section 9 header | Several round-2 leftovers: a Scope line that still described the old design, an O2 row that read as if it contradicted C5a, an N2 pointing at a superseded spec without noting the new verdict vocabulary, a broken table header, a stale commit count, and table headers mislabeled by round. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | All corrected in place. |
| SR-208 | low | IN-SCOPE | G | 4.3 "ONE function ... no other function, inside or outside `artifact_meta`" | Taken literally, this forbade splitting the loader and left `aw meta repair` and the migration with no stated read path. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | "One code path / component with one entry point"; repair and migration read through it and write through `append`'s atomic path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-8 | Should the maintainer be asked where the cutover runs? | No; resolved from evidence. | Ask. | The sidecar's only location (`record_history.history_path`) and the runner's isolated worktrees leave exactly one place where the migration can succeed without loss; the existing preflight refusal (5.2 step 2) already encodes the maintainer's no-loss ruling. | yes |
| D-9 | How is a multi-round file's single verdict mapped onto events? | Last round only; earlier rounds null. | Copy the verdict to every round; map rounds from git history. | 4.2a forbids invented precision; git-history mapping is possible later as an `inferred-from-git` enrichment without changing the format. | yes |
| D-10 | Are directory-mtime shortcuts acceptable for freshness? | No. | Allow them as an optimization. | POSIX directory mtime changes on entry add/remove/rename, not on in-place content edits, so a shortcut based on it can serve a stale row, breaking C5a's log-wins guarantee. | yes |

## Round 4

Re-review requested by the maintainer on 2026-10-24. Structural preflight `aw specs check` was clean before and after the edits. Every measured claim was re-derived; findings SR-301..SR-308 all FIXED from repository evidence without requiring maintainer questions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-301 | high | UNDER-SCOPE | D (decisions) / B (testable) / F (compatibility) | Spec 4.1a (point 4), 4.6 (Review rounds row), AC-14; 4 multi-review subjects (`rtvdak`, `e25iy9`, `l4vw9o`, `urv602`) sharing subject id6 | Round 3's attribution rule assumed that only refinement reviews with differing id6s share a subject. In fact, 4 historical subjects each have 2 review files (from 2026-09-30 and 2026-10-07) where both files share the subject id6. Under the round-3 rule, neither file has a differing id6 so both emit events with no `review_ref`, causing `aw check meta` to fail on round counts for all 4 subjects across the migrated corpus. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.1a point 4, 4.6, and AC-14 updated: `review_ref` disambiguates ANY multi-review subject. When id6 differs (17 specflow files), `review_ref` is that id6; when multiple files share the subject id6, `review_ref` is the distinct date/stem prefix (e.g. `20260930-reqids-02` vs `20261007-reqids-02`). Single-file subjects omit `review_ref`. Zero files renamed. |
| SR-302 | medium | IN-SCOPE | C (coverage) / B (testable) | AC-14 table text vs 4.1a (point 4) and 4.6 | AC-14 stated that "the file's round count equals the subject's review-event count", which fails for any subject with multiple review files (such as 18hh1u with 17 files, or the 4 re-review pairs). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | AC-14 updated to "the file's round count equals the subject's review-event count attributed to that file". |
| SR-303 | medium | IN-SCOPE | D (decisions) / G (plannable) | Spec 4.1 "Artifact file shape" vs 4.1a (point 2) and 5.2 (step 4) | Review records have no `id` or `status`, yet Section 4.1 and 5.2 step 4 specified "two-key front matter and banner" without defining the review banner template. An agent reading a standard banner pointing to `meta/<id>.jsonl` would seek a non-existent review log. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.1/4.1a updated with the review banner template: `<!-- aw-managed: review metadata lives in .aw/records/meta/<subject>.jsonl; use aw show <subject>; agents read .aw/AGENT_QUICKSTART.md -->`. |
| SR-304 | medium | IN-SCOPE | B (testable) / D (decisions) / G (plannable) | Spec 4.2 "Event schema (v1)" vs 4.1a and 4.4 | 4.2 enumerated top-level event keys but omitted the payload fields for `op: review` (`round`, `verdict`, `kind`, `review_ref`, `findings_summary`, `legacy_verdict`, `readiness`) and `op: coverage` (`coverage`, `coverage_fingerprint`, `coverage_checked`), leaving schema validation underspecified. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.2 Event schema (v1) updated with explicit field listings for `op: review` and `op: coverage`. |
| SR-305 | low | IN-SCOPE | A (current measurements) / G | `.aw/records/history.jsonl` (413 records); `git ls-files .aw/records/*.md` (4381); reviews (1275); `v1.3.0-rc.1..HEAD` (12,135) | Sidecar count grew from 408 to 413 (specs 77 -> 82), tracked records from 4374 to 4381, reviews from 1273 to 1275, commits from 12,133 to 12,135. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 1, 2, 3c, 5.2 step 2, and Section 7 updated with fresh counts. |
| SR-306 | low | IN-SCOPE | A (current measurements) | Section 1 (line 32) and 4.1a (point 5, line 290) verdict census | The 28 off-vocabulary verdicts were misstated as containing 9 `MATERIAL CHANGES APPLIED` and a "template placeholder". Re-measured: 13 `REVIEWED - MATERIAL CHANGES APPLIED`, 11 `REVIEWED`, 3 `REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION`, 1 `REVIEWED - CONVERGED WITH REVISIONS`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Corrected census breakdown in Section 1 and 4.1a point 5. |
| SR-307 | low | IN-SCOPE | F (compatibility) / D (decisions) | Spec 4.5 "SQLite cache: .aw/state/index.db" table listings | Cache table schemas listed `events(id6, seq, ...)` and `files(path, size, mtime_ns, blob_sha)` without worktree keys, risking cross-worktree collisions when multiple runner lanes share one common cache. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.5 updated to key `files` and `events` by `worktree`. |
| SR-308 | low | IN-SCOPE | F (compatibility) / G (plannable) | Spec Section 9; backlog item `tg80ht` (spec-to-plan bridge) | Backlog `tg80ht` bridges approved specs to runner dispatch and IPD Set authoring, directly citing `4sd62s`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 9 updated to reference `tg80ht`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-11 | How are multiple review files sharing the subject id6 disambiguated in events and drift checks? | Disambiguate by distinct date/stem prefix (e.g. `20260930-reqids-02`) as `review_ref`. | Merge historical files; delete older files. | Zero file deletions or renames; preserves all 1275 historical review files; fully deterministic attribution in `aw check meta`. | yes |
| D-12 | What banner is written to review files? | Subject-directed banner referencing `meta/<subject>.jsonl` and `aw show <subject>`. | No banner; standard banner with non-existent id. | Prevents agents from attempting to read non-existent `meta/<review_id>.jsonl` while maintaining consistent pointer guidance. | yes |

## Round 5

Re-review requested by the maintainer on 2026-10-24. Structural preflight `aw specs check` was clean before and after the edits. Every measured claim was re-derived; findings SR-401..SR-407 all FIXED from repository evidence without requiring maintainer questions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-401 | high | IN-SCOPE | F (compatibility) / D (decisions) / G (plannable) | Spec 4.5 line 548: "Where lane worktrees share one cache, rows are keyed by worktree root (located with `git rev-parse --git-common-dir`), so a lane never reads another tree's state as its own." | `git rev-parse --git-common-dir` returns the common `.git` dir of the repository, which is identical across all worktrees. Using it to key worktree rows causes all lane worktrees to share the exact same key in `artifacts`, `events`, and `files`, defeating lane cache isolation and causing concurrent runner lanes to overwrite or read each other's branch-local metadata cache. `git rev-parse --show-toplevel` identifies the unique worktree root, while `--git-common-dir` locates the repository root / shared cache database. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Correct 4.5 to specify that `git rev-parse --show-toplevel` keys worktree rows in `artifacts`, `events`, and `files`, while `--git-common-dir` locates the common `.git` directory / shared database location. |
| SR-402 | high | UNDER-SCOPE | B (testable) / D (decisions) / G (plannable) | Spec 4.4 (lines 460-469) vs C5/C5a; `check_engine.py` (`check_status_untooled`), `status_untooled_gate.py` | `artifact_meta.read_at(id6, rev)` was specified as resolving only `meta/<id6>.jsonl` at `rev` (caching folded state under blob SHA). But gates like `status_untooled_gate` and `check_status_untooled` check whether the front-matter `status` in the staged/committed artifact `.md` differs from the folded log state at `rev`. If `read_at` only loads the log blob, gates would be forced to parse the artifact `.md` blob themselves, violating C5/C5a. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Update 4.4 and 4.5 to clarify that `artifact_meta.read_at(id6, rev)` resolves and caches both `meta/<id6>.jsonl` and the artifact `.md` file at `rev`, returning a `State` containing both the replayed log state and the front-matter mirror status at that revision, so gates verify untooled changes or drift at `rev` without parsing raw blobs. |
| SR-403 | medium | UNDER-SCOPE | D (decisions) / F (memory/resources) / G (plannable) | Spec 4.5 lines 540-563; `runner_shared.cleanup_lane_worktree`; isolated worktree creation | Worktree-keyed rows in `artifacts`, `events`, and `files` accumulate across temporary runner worktrees without a stated pruning or garbage-collection mechanism. In an active repository with hundreds of runner lane worktrees created and torn down, the shared `index.db` would indefinitely retain dead rows for deleted worktrees. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Update 4.5 to define worktree lifecycle pruning: `aw index rebuild`, `aw check meta`, and lane teardown (`cleanup_lane_worktree`) prune cache rows whose worktree directory no longer exists on disk (`DELETE FROM ... WHERE worktree NOT IN ...`). In addition, incremental cache refresh drops entries from `files` and `artifacts` when files are removed or moved (such as when plans transition between lifecycle directories). |
| SR-404 | medium | IN-SCOPE | D (decisions) / G (plannable) | Spec 4.1 line 210 ("YAML-delimited, exactly two keys, fixed order") vs 4.1a (point 2 and point 4 defining `subject`, `subject_type`, and optional `ref`) | Section 4.1 states that front matter is "YAML-delimited, exactly two keys, fixed order" without qualifying review records. Section 4.1a specifies that review records carry `subject:` and `subject_type:` front matter, plus an optional `ref:` when `review_ref` is present (point 4). A strict two-key line grammar parser built from 4.1 would reject review records carrying `ref:`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Clarify 4.1 to state that lifecycle records carry exactly two keys (`id`, `status`), while review records carry `subject`, `subject_type`, and optional `ref` (4.1a). |
| SR-405 | medium | IN-SCOPE | F (compatibility) / G (plannable) | Spec 4.5 line 566: "`aw index <type>` becomes `aw index rebuild`"; AGENTS.md, `ipd_lifecycle.py:5912`, `runner_shared.py` | The replacement of `aw index <type>` by `aw index rebuild` did not state whether `aw index plans`, `aw index research`, and `aw index prompts` are retained as backward-compatible aliases. Existing documentation in AGENTS.md, lifecycle recovery strings, and scripts frequently invoke `aw index plans`. Abruptly failing these commands causes breakage across workflows and user muscle memory. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Update 4.5 to specify that `aw index [plans, research, prompts]` is retained as a compatibility alias that routes to `aw index rebuild` with an informational notice. |
| SR-406 | low | IN-SCOPE | D (decisions) / Security | Spec 4.2 lines 314, 321; Spec 4.5 | Security defense-in-depth: Spec 4.2 does not explicitly mandate regex validation `^[a-z0-9]{6}$` for `id6` on all `artifact_meta` path resolution calls to prevent directory traversal in `meta/<id6>.jsonl`; and Spec 4.5 does not explicitly require all SQLite queries to be strictly parameterized (`?`). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Add explicit security constraints in 4.2/4.3 (strict `id6` format validation preventing path traversal) and 4.5 (mandatory parameterized queries). |
| SR-407 | low | IN-SCOPE | A (current measurements) / G (plannable) | Commit 7b8675ec8 (specflow iteration 18); `.aw/records/reviews/` | The round-4 review counts and off-vocabulary verdict counts drifted with iteration 18 of specflow: 18 review files now have filename id6 != Subject-Id (spec said 17; `18hh1u` now has 18 review files); off-vocabulary verdicts are now 29 (14 `REVIEWED - MATERIAL CHANGES APPLIED`, spec said 13); tracked records are 4382; `v1.3.0-rc.1..HEAD` is 12,137 commits; records with workflow history are 2922; non-review files lacking an id6 in any form are 39 (spec said 51). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Update counts across Sections 1, 2, 4.1a, 5.2 step 2/3, and Section 9. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-13 | How is worktree root identified for cache keying? | By `git rev-parse --show-toplevel`. | Use `git rev-parse --git-common-dir`. | In git worktrees, `--git-common-dir` points to the primary repository `.git` dir and is identical across all worktrees, whereas `--show-toplevel` gives the unique worktree root. | yes |
| D-14 | How does `read_at(id6, rev)` serve gates checking untooled status changes? | By resolving both `meta/<id6>.jsonl` and the artifact `.md` at `rev` into `State`. | Force gates to parse the `.md` blob themselves. | Preserves C5/C5a prohibition on external front-matter parsing and satisfies `status_untooled_gate` needs. | yes |
| D-15 | How are stale worktree rows in SQLite pruned? | Pruned on `aw index rebuild`, `aw check meta`, and lane teardown when the worktree path is gone; deleted files pruned during incremental refresh. | Leave them indefinitely; drop entire cache on every run. | Prevents unbounded growth in multi-worktree execution while keeping caching fast and incremental. | yes |
| D-16 | Are `aw index <type>` invocations preserved as compatibility aliases? | Yes, aliased to `aw index rebuild` with a notice. | Fail immediately with an error. | Preserves existing scripts and AGENTS.md conventions. | yes |

## Round 6

Re-review requested by the maintainer on 2026-10-24 (HEAD `61fce3bfd`). Structural preflight `aw specs check` was clean before and after the edits. This round re-verified the round-4/5 additions against code rather than prose; three were factually wrong. No question needed the maintainer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-501 | medium | IN-SCOPE | F (compatibility) / D (decisions) | `agent_workflows/runner_shared.py:392` `state_root` via `project_context.resolve_project_context`; measured: called inside lane worktree `.aw/worktrees/pkz19w` it returns `.aw/worktrees/pkz19w/.aw/state` | 4.5 (rounds 4/5, SR-307/SR-401) asserted that "lane worktrees share one cache" located via `--git-common-dir`. But the placement rule 4.5 itself mandates resolves the `repository`-backend state root PER WORKTREE, so each lane has its own `index.db`. The spec stated two incompatible placements, and a planner could not tell which to build. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.5 states the measured placement fact (per-worktree cache for `repository`, shared only under companion/home), keeps worktree keying for the shared case, and records that sharing via `--git-common-dir` is NOT decided here; the cold-lane cost is left to AC-13. |
| SR-502 | low | IN-SCOPE | G (plannable) | `rg "def cleanup_lane_worktree" agent_workflows` returns nothing; teardown is `runner_shared.teardown_isolation_worktree` (`runner_shared.py:1667`) over `worktree_lease.teardown_worktree` (`worktree_lease.py:1192`) | 4.5 named a non-existent function `cleanup_lane_worktree` as the lane-teardown pruning hook. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Replaced with the real teardown path and noted pruning is a no-op for a per-worktree cache. |
| SR-503 | low | IN-SCOPE | Security / B (testable) | `agent_workflows/artifact_core.py:55` `ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")` vs spec 4.2 `^[a-z0-9]{6}$` | The round-5 traversal guard (SR-406) wrote `^...$`; under Python `re.match`, `$` matches before a trailing newline, so `"abc123\n"` passes. The repository already has the correct full-match constant. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.2 now cites `artifact_core.ID6_RE` and states why `^...$` is insufficient. |
| SR-504 | low | IN-SCOPE | A (current measurements) / C | `aw` corpus re-count at HEAD `61fce3bfd`: 1276 reviews, 19 id6-mismatched (all `18hh1u`), 30 off-vocabulary verdicts (15 `MATERIAL CHANGES APPLIED`), 4383 tracked records, 12,139 commits since `v1.3.0-rc.1`; 0 review records with an unresolvable Subject-Id | Counts drifted again by one specflow iteration. AC-14a still said "each of the 28 off-vocabulary verdicts", a stale number that would make the AC's evidence unsatisfiable as worded. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 1 rows marked with r6 values; 4.1a point 4 count updated; AC-14a reworded to "each DISTINCT off-vocabulary string found at implementation time" so it no longer rots. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-17 | Should 4.5 decide that lanes share one cache under `--git-common-dir`? | No; record the measured per-worktree placement and leave sharing undecided. | Mandate a shared cache at `<git-common-dir>`; mandate per-worktree only. | Choosing a placement is a design decision the spec never made (rounds 4/5 asserted a fact that was false); the measured behavior of the resolver the spec already mandates is the conservative reading, and AC-13 measures the cost. | yes |
| D-18 | Which id6 validator does 4.2 require? | `artifact_core.ID6_RE` (full match). | A new regex. | Existing single authority; avoids a 96th regex literal (P1). | yes |

## Round 7

Re-review requested by the maintainer on 2026-10-24 (HEAD `2edf1f3ac`). Structural preflight `aw specs check` was clean before and after the edits. Every cited symbol in 4.3-4.5 and the 4.4 inventory was re-located by `rg` and resolves; section 9 statuses are current. One design gap found; no question needed the maintainer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-601 | medium | UNDER-SCOPE | C (coverage) / G (plannable) | `agent_workflows/attention_contract.py:581` `TRANSITION_AUTHORITY["->reviewed"]` (`review_record: True`); `agent_workflows/review_findings.py:1022` `review_attestation_missing` checks Subject-Id, Subject-Type and parse only, never the verdict; consumers `specs.py:1240` `_review_attestation_refusal`, `status_set.py:811`, `check_engine.py:8236` `check_spec_review_attestation`; 21 refinement records with `Subject-Type: spec` for `18hh1u` | 4.1a point 3 says a `refinement` event "never satisfies the `->reviewed` transition authority on its own", but no section names the consumer that enforces it, and no AC tests it. Today's single predicate would accept a refinement-only record set, so a plan built from the spec could port the predicate unchanged and silently violate 4.1a. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.4 gains a bullet re-pointing the one predicate (still shared by both setters and `aw check`) at the folded state and requiring a `gate` review event; migrated gate events count, so no spec at `reviewed` is invalidated. AC-14a extended with the refusal and success cases. |
| SR-602 | low | IN-SCOPE | A (current measurements) | re-count at HEAD `2edf1f3ac`: 1278 reviews, 21 id6-mismatched (all `18hh1u`), 32 off-vocabulary verdicts (17 `MATERIAL CHANGES APPLIED`), 4391 tracked records, sidecar 414 lines over 296 id6s, 12,144 commits since `v1.3.0-rc.1` | Counts drifted by further specflow iterations. AC wording already avoids fixed counts (SR-504), so only the measurement rows were stale. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 1 rows and 4.1a point 4 carry r7 values. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-19 | Do migrated legacy gate reviews satisfy the post-cutover `->reviewed` attestation? | Yes; a migrated event of kind `gate` counts regardless of `legacy_verdict`. | Require a non-legacy gate event (would invalidate the specs at `reviewed` today, `4sd62s` and `4iyd78`, at cutover). | 4.1a point 5 forbids legacy events as readiness/APPROVAL signals, not as proof a review occurred, which is all the attestation proves (`attention_contract.py:577` honest limit); `check_spec_review_attestation` docstring forbids retroactive invalidation (R-13). | yes |

## Round 8

Maintainer-directed design pass on 2026-10-25 (HEAD `5981c8c1e`), following the maintainer's questions on the round-7 entity diagram. The two decisions below were put to the maintainer and answered "yes". Structural preflight `aw specs check` was clean before and after. All 10 Mermaid blocks render with mermaid-cli.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-701 | medium | UNDER-SCOPE | G (plannable) / F | `.aw/records/runs/` gitignored (`.aw/.gitignore:14`), 597 run dirs, about 34,000 run events; `runner_shared.load_state` (`runner_shared.py:1107`); `run_analytics_cache.source_fingerprint` | Artifacts could not be joined to the runs and attempts that acted on them, and N4 excluded run records entirely. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Maintainer decision 2026-10-25: index runs read-only (new 4.5b) through the runner's own readers; N4 reworded to "storage unchanged"; zero indexed is reported as unknown. AC-25. |
| SR-702 | high | UNDER-SCOPE | D (decisions) / Security | 4.2 `actor` was one free-text string; spec `18hh1u` defines ACE/Requested-Model/Resolved-Model/Variant; `leak_sanitizer.py:88` `session-id` rule | The tracked, irreversible log format could not answer "which model changed what in which run" without parsing text (P1), and gave no rule for keeping session ids out of tracked history. | C:Low;U:Low;S:Medium;F:Medium;Overall:Low | fixed | 4.2 actor is a structured object (`tool`, `ace`, `host`, `model`, `variant`, `run_id`, `attempt`), with session ids, command lines and paths forbidden. AC-24. |
| SR-703 | medium | IN-SCOPE | B / D | measured: `Kind:` = plan role on 1,596 plans, `Work-Kind`, `Gate-Kind`, `Subject-Type` | "type" and "kind" are overloaded, and a bare `Kind` field names nothing. | C:Low;U:Medium;S:Low;F:Low;Overall:Low | fixed | Maintainer decision 2026-10-25: new 4.5c naming rule; the migration renames `Kind` to `plan_role` (irreversible, recorded as such); flags and docs updated (5.4). |
| SR-704 | high | IN-SCOPE | Functionality | 4.3 staleness rule compared known `files` rows only | A per-file `stat` cannot discover a NEW file, so a log or record arriving by `git pull` or checkout would be invisible until a manual rebuild, which breaks C5a's "the log wins". | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.3 is now two checks: directory mtime for membership, per-file stat for content. New `directories` table. AC-26. |
| SR-705 | blocker | IN-SCOPE | F (honest limits) | 4.3 "The log and the mirror change together or not at all"; three separate files (log, `.md`, directory move) | The spec claimed an atomicity it cannot deliver; the rubric treats a spec claiming more than it delivers as a blocker. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.3 defines an ordered write with the log as the commit point; a later failure is reported, detected by `aw check meta`, and repaired deterministically. AC-5 extended with fault injection; an honest limit added. |
| SR-706 | medium | IN-SCOPE | D | SR-501 measurement (per-worktree cache for `repository`); companion/home share one records root | The worktree key column was constant in a per-worktree cache and duplicated one truth in a shared one. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Removed; one cache per resolved records root, keyed by `id6`, with `meta.records_root` mismatch forcing a rebuild. Worktree pruning deleted. |
| SR-707 | medium | UNDER-SCOPE | Functionality | 4.5 "Schema version row" hand-maintained; per-type tables generated from the registry | A forgotten version bump would let an old cache silently miss a new column. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | `meta.schema_hash` is a digest of the registry; any registry change rebuilds. AC-23. |
| SR-708 | medium | UNDER-SCOPE | B / G | `Item-Dependencies` measured forms: `executed:` 464, `exists:` 5, `state:` 5, plus `none`, `unresolved`; `ipd_dependency_statement_gate` distinguishes `none` from absent | Dependencies were unspecified in the store, and a naive link table would lose the condition, the required status, and the none/absent distinction a gate depends on. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 4.2 stores dependencies parsed, with `dependency_declaration`; 4.5a has a `dependencies` table; the migration refuses unparseable values. AC-24. |
| SR-709 | medium | UNDER-SCOPE | D / G | 4.5 tables ended in `...`; round-7 diagram drew an unsupported FILES-to-BLOBS FK and keyed revision state on one sha | The cache schema was too thin to plan from, and `read_at` state depends on two blobs. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | New 4.5a: design rules (typed columns, not name/value; relationships named for their meaning; raw plus resolved references with no FK constraints; history as events; one clock rule), the full table set, indexes, rejected alternatives. `rev_log_states` and `rev_mirrors` replace `blobs`. Diagrams 4.9.1 to 4.9.4 and 4.9.6 redrawn; 4.9.8 added. AC-23. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-20 | Index run records in this spec? | Yes, read-only, via the runner's readers. | Leave runs out and only reserve `run_id`/`attempt` in the actor. | Maintainer answer 2026-10-25; the artifact-to-run join is the main value of a shared cache. | yes |
| D-21 | Rename `Kind` to `plan_role` in the logs at migration? | Yes. | Keep `Kind` in logs, rename only in the cache. | Maintainer answer 2026-10-25; the cutover rewrites every artifact anyway, so it is the cheapest moment. | no (maintainer decided) |
| D-22 | Generic name/value field storage? | No; typed columns generated from the registry. | EAV `fields`/`event_fields`; JSON blob per artifact. | Closed registry plus disposable cache removes EAV's benefits and keeps its costs. | yes |
| D-23 | Foreign-key constraints on reference columns? | No; raw plus resolved columns, dangling is an `aw check` finding. | Enforced FKs. | A cache must load what the logs say; refusing rows would hide a defect instead of reporting it. | yes |

## Round 9

Re-review requested on 2026-10-25 (HEAD `34f785e4d`), after the maintainer's OQ-1/OQ-2/OQ-3/OQ-12 answers and the `--force-worktree` / `aw install --migrate` / AC-27..AC-29 edit (commit `70273e9d5`). Structural preflight `aw specs check` was clean before and after. The new 5.1/5.2 text and AC-27/AC-28 are consistent with each other and with diagram 4.9.6; `aw install --help` confirms no `--migrate` exists today and `-y, --yes` reads "Skip preflight confirmations". The gaps found are in what OQ-2 and the sidecar import left unspecified. Three decisions were put to the maintainer via the question tool and answered.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-801 | high | UNDER-SCOPE | B (testable) / G (plannable) | spec 4.1 walkthrough bullet ("the two-key front matter"); `agent_workflows/attention_contract.py:190` `TREE_POLICY` walkthroughs "no lifecycle status in v1 (OQ8)"; measured 24 of 27 tracked walkthroughs carry no `- Status:` line, 3 carry free prose | OQ-2 gave walkthroughs the two-key front matter (`id`, `status`), but walkthroughs have no status vocabulary, and N2 forbids adding one. A planner would have to invent the value of every walkthrough's `status:` line. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision 2026-10-25: walkthroughs carry `id` only and no status; their logs never hold a `transition`; prose Status lines move to the body. 4.1, section 0 (artifact), 4.6 (status and orphan rows), AC-29 updated. |
| SR-802 | high | UNDER-SCOPE | D (decisions) / G | `agent_workflows/record_history.py:199` `append_rename`; `agent_workflows/artifact_rename.py:23`; measured 37 of 462 sidecar records carry `verb`/`from_name`/`to_name`; spec 4.2 `op` list | The sidecar also holds the `aw rename`/`aw group` ledger. The spec retires the sidecar writer but names no event for renames after the cutover, and no shape for importing the 37 ledger records, in a tracked format that cannot be reversed. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision 2026-10-25: new `op: rename` (`verb`, `from_name`, `to_name` basenames), appended with any `set` of `set`/`order`; imported ledger records stay `legacy` with `source: sidecar`. 4.2, 4.8, 5.2 step 2, diagram 4.9.1; AC-31. |
| SR-803 | high | UNDER-SCOPE | F (security, failure modes) | measured 8 sidecar records for 7 `id6` values with no tracked record; commit `ed82ce52f` "purge OpenCode security-disclosure campaign ... per maintainer directive" deleted backlog `3srje9`, whose sidecar record remains; spec 4.6 orphan rule; 5.2 step 6 requires `aw check meta` clean | Importing every sidecar record into logs would either fail the migration's own verification (orphan logs) or re-commit history the maintainer purged from git, permanently. Separately, deleting the sidecar's ignore line while the file stays on disk lets a later broad `git add` commit it. | C:Low;U:Low;S:Medium;F:Medium;Overall:Low | fixed | Maintainer decision 2026-10-25: no log for an `id6` with no tracked record; census lists them; records go to a gitignored export beside the journal. The sidecar file moves into that export before its ignore lines (`.aw/.gitignore:11`, the `engine.py` template and install re-add, `placement_switch.py:65`) are removed. AC-30. |
| SR-804 | medium | IN-SCOPE | A (current claims) / D | spec 3c and 5.2 step 2 "the only copy of 413 records"; measured about 367 of 462 sidecar records repeat a line in the record's own `## Workflow history` (setters write both, e.g. `specs._sidecar_append` docstring "The inline `## Workflow history` record is the durable one") | The "only copy" claim was overstated, and the spec did not say whether the duplicates are imported twice, which changes every migrated log. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Maintainer decision 2026-10-25: keep both, tag each `legacy` event with `source` (`history` or `sidecar`); a display may hide exact duplicates. 3c, section 1, 4.2, 5.2 step 2 corrected. |
| SR-805 | medium | UNDER-SCOPE | B (testable) | 5.2 step 2 "when a sidecar is expected but not present" with no definition | The sidecar refusal (AC-22) could not be tested, because "expected" had no observable condition. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Defined from evidence: expected when the tree has a spec or backlog item with an `id6`, since `specs._sidecar_append`, `backlog.run_new` and `status_set.apply_status_change` append for those types. |
| SR-806 | low | IN-SCOPE | A (current measurements) | re-run at HEAD `34f785e4d`: 39 id-less non-review records INCLUDE the 4 prompt-library and 2 research templates | Section 1 and 5.2 step 3 said the 39 excluded the templates, so the step-3 population was off by 6 and the minted count was never stated. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 1 annotated; 5.2 step 3 states 22 records receive an `id6` (14 specs, 8 walkthroughs), templates follow the plan's 4.1 decision. New r9 measurement label. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-24 | What does a walkthrough carry in front matter? | `id` only; no status, no transitions. | Fixed one-value status; a new small lifecycle. | Maintainer answer 2026-10-25; N2 adds no vocabulary; `TREE_POLICY` already treats walkthroughs as status-less. | yes |
| D-25 | How are renames recorded after the cutover? | New `op: rename`; imported ledger records stay `legacy`. | `set` plus free-text `note`; leave to the plan. | Maintainer answer 2026-10-25; free text reintroduces P1; legacy order is unknown (4.2a). | no (maintainer decided) |
| D-26 | Sidecar records with no tracked record? | No log; census plus gitignored export. | Orphan logs with an exemption; drop them. | Maintainer answer 2026-10-25; keeps 4.6 strict and does not re-publish purged history. | yes |
| D-27 | Sidecar records that repeat an inline line? | Keep both, tagged by `source`. | Exact-match de-duplication. | Maintainer answer 2026-10-25; a text match cannot prove two lines are one event; nothing guessed. | yes |
| D-28 | When is a sidecar "expected"? | When any spec or backlog item with an `id6` exists. | Always; never (warn only). | Those are exactly the types whose setters append (`specs._sidecar_append`, `backlog.run_new`, `status_set.apply_status_change`). | yes |

## Round 10

Internal-consistency pass requested by the maintainer on 2026-10-25 (HEAD `933b94b74`). The whole spec was cross-read section against section (terms, criteria, ACs, design, diagrams, migration steps, open questions, section 9). Structural preflight `aw specs check` was clean before and after; all 10 Mermaid blocks render with mermaid-cli 12.0.0. Three format decisions were put to the maintainer via the question tool and answered; the rest were fixed from repository evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-807 | high | IN-SCOPE | D / G | spec 4.2 "`0` is the migration checkpoint" vs 4.2a "unordered legacy events before the checkpoint"; C4 seq is contiguous from 0 | Legacy events could not be both before seq 0 and in a contiguous non-negative sequence; their effect on replay was unstated. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision: legacy events follow the checkpoint (inline, then sidecar, then review events) and change no field; 4.2, 4.2a, 5.2 steps 2 and 4, diagram 4.9.6. AC-32. |
| SR-808 | high | IN-SCOPE | D / Functionality | 4.1a K6 "`Reviewed-At` becomes `at`" vs 4.2 `at` is RFC 3339; all 1,287 `Reviewed-At` values are dates (`^- Reviewed-At: 9999-99-99` census); 4.4 `last_history_at` = highest-seq `at` | Day-only values would become invented times, and every migrated artifact would look touched on cutover day in `aw attention`. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer decision: migrated events take the migration `at`; days go in `observed_day`; checkpoint `last_history_day`; `last_history_at` falls back to it, with stated precision. Maintainer added: day-only values are for filenames only and must not be written into history/metadata going forward (4.2 `at` rule). 4.1a, 4.2, 4.2b, 4.4, 4.5a rule 5 and `artifacts`, diagram 4.9.1. AC-32. |
| SR-809 | medium | UNDER-SCOPE | B / D | 4.5c forbids a bare `kind`; research YAML `kind:` on 161 records, prompt `aw-prompt: Kind:` on 25 | Only the plan `Kind` was mapped, so the naming rule contradicted two field sets the migration must carry. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Maintainer decision: `research_kind`, `prompt_kind`. 4.2, 4.2c, 4.5c, 4.6, 5.4. |
| SR-810 | medium | IN-SCOPE | B (testable) | AC-15 "(3) the same two cases for `coverage`" vs 4.4 coverage is written only by `op: coverage`, not by a review event | AC-15 tested a coverage rule the design does not have. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | AC-15 states and tests the coverage-event rule. |
| SR-811 | medium | IN-SCOPE | D | 4.2 coverage event carried `coverage_checked`; measured values are `<day> by <model>` (39 plans); 4.2 actor and `at` already record who and when | A day-plus-model string duplicated the event's `at`/`actor` and conflicted with the new no-day-only rule. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | `coverage_checked` kept for migrated values only; new events use `at` and `actor`. |
| SR-812 | medium | IN-SCOPE | B / D | 4.1 walkthroughs get logs; section 0 "event log" and "registry", 4.5a `artifacts` and `files.file_role` named artifacts only | Walkthroughs (round 9) had logs but no place in the registry, the cache or the file roles. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 0, 4.5a `artifacts` (status NULL) and `file_role` `walkthrough`, diagram 4.9.1 (FILES). |
| SR-813 | low | IN-SCOPE | A (current) | `aw specs` tree: `4iyd78` in `approved/`, `wy9aru` in `implemented/` | Section 9 and 4.2c showed stale statuses. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Section 9 header "Status at r9" and rows; 4.2c `4iyd78` approved. |
| SR-814 | low | IN-SCOPE | A | 5.2 step 2 "At round 5, it held the only copy of 413 records" vs round-9 3c/section 1 | Round 9 corrected the claim in 3c but left the old one in 5.2. Step 2 also said "add its records to the logs" before step 4 creates checkpoints. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Step 2 reads the sidecar first and step 4 writes its events; counts aligned; diagram node S2 aligned. |
| SR-815 | low | IN-SCOPE | A | 4.2c coverage row "(34)"; 4.5c "1,596 plans" | Counts behind r9 measurement (39; 1,603). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | r9 values added beside the old ones. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-29 | Where do legacy events sit in a migrated log? | After the checkpoint, seq 1..n, no state effect. | Embedded inside the checkpoint. | Maintainer answer 2026-10-25; keeps one event per line and contiguous seq. | no (maintainer decided) |
| D-30 | How are migrated events timed? | Migration `at`; original day in `observed_day`; checkpoint `last_history_day`. | Day at 00:00Z. | Maintainer answer 2026-10-25, plus the rule that day-only values are for filenames only; 4.2a forbids invented precision. | no (maintainer decided) |
| D-31 | Names for research and prompt `kind`? | `research_kind`, `prompt_kind`. | Leave to plan step 1. | Maintainer answer 2026-10-25; direct application of 4.5c. | no (maintainer decided) |
| D-32 | `last_history_at` output when only a day is known? | Keep the key name; value is a day; output states the precision. | Synthesize a time. | It is a published `aw attention --format json` key (`attention_contract.last_history_at` docstring); inventing a time breaks D-30. | yes |

## Round 11

Re-review pass requested by the maintainer on 2026-10-26 (HEAD `b5697af54`). Corpus measurements, review records census, history sidecar records, and cross-spec dependencies were re-measured at current HEAD after merges of `specflow` research, candidate spec `1tx9t8`, and `revsteps` plans (`3bwrfx`, `gv3smb`, `uiyoax`, `is2xiv`). Structural preflight `aw specs check` was clean before and after. Two consistency findings were recorded and fixed from repository evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-816 | low | IN-SCOPE | A (current) | spec 1, 3c, 4.1a, 5.2 step 2, AC-14a | Measured counts drifted since r9/r10: tracked records 4,416 (plans 1,705, reviews 1,287, backlog 1,128, research 171, specs 46, prompts 34, walkthroughs 26); terminal records 2,829; review records with differing id6 vs Subject-Id 24 (all specflow 18hh1u refinement reviews); off-vocabulary review verdicts 35 in 4 strings; history sidecar 466 records for 320 id6 values (331 backlog, 113 specs, 8 plans, 11 research, 2 walkthroughs, 1 roadmap; 427 status/history, 39 rename/regroup). | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | r11 measurement checkpoints added to Section 1 fact table, 3c, 4.1a/AC-14a, and 5.2 step 2. |
| SR-817 | low | IN-SCOPE | G (specs) | Section 9 table | Section 9 compatibility matrix omitted candidate spec `1tx9t8` (draft candidate 02 in `specflow`), and did not note that `k3yx72` Stage 1 plans (`3bwrfx`, `gv3smb`, `uiyoax`, `is2xiv`) have executed and merged to `main`, landing `Review-Depth` in the legacy schema ahead of Phase B. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Added `1tx9t8` row to Section 9 compatibility table and updated `k3yx72` row noting Stage 1 execution status. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-33 | How does candidate spec `1tx9t8` relate to `4sd62s`? | Subject to standard two-key front matter and C10 naming rules; adds no registry fields at draft. | Add new registry fields now. | Consistent with Section 9 treatment of draft candidates `18hh1u` and `yfz5u9`. | yes |

## Round 12

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-818 | high | IN-SCOPE | D/F: graduation relationships | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1003; .aw/records/specs/README.md:56; agent_workflows/check_engine.py:5566 graduation_cluster | Reversing artifact lineage cannot recover a declared Graduated-To Set, especially with no linked child. The proposed table discards a distinct declaration. | C:Medium; U:Medium; S:Low; F:High; Overall:Medium-High | open | Await maintainer choice in OQ-15. Strong recommendation: retain explicit Set declarations and combine them with reverse lineage without inventing child links. |
| SR-819 | high | IN-SCOPE | D/F: dates | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:613; agent_workflows/research_cmd.py:299 plan_new; agent_workflows/research_contract.py:290 ResearchName | One date cannot mean both filename date and creation day: research uses the Set date in filenames. 28 tracked research records have different filename and creation days. | C:Medium; U:Medium; S:Low; F:High; Overall:Medium-High | open | Await maintainer choice in OQ-16. Strong recommendation: preserve filename date and creation day separately; retain unknown creation timestamps as unknown. |
| SR-820 | high | IN-SCOPE | D/F: run entities | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1026; agent_workflows/runner_shared.py:41891 attempt_no; agent_workflows/run_analytics_cache.py:343 source_fingerprint | Attempt identity used artifact id instead of queue position. Repeated queue items collide. Deleted runs, changed roots and partial actor joins also lacked explicit handling. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Key attempts by run, item position and attempt number; retain artifact lookup; report ambiguous actor joins and incomplete run data; invalidate deleted runs and root changes. AC-25 and ER/run flow aligned. SQLite probe retained both attempt-1 rows. |
| SR-821 | high | IN-SCOPE | B/F: cache correctness | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:677; baseline 4.3/4.5 | Matching timestamps can hide changed bytes or directory members. Target-only changes leave resolved references stale. Invalid logs and in-memory fallback could look like clean empty results. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Verify working bytes and membership, refresh target resolution, evict invalid state and report incomplete aggregates. In-memory SQLite follows the same validation; genuine source/resource failures still fail. AC-1a/AC-26 extended. Same-size/mtime and target-only probes reproduced the problems. |
| SR-822 | high | IN-SCOPE | B/F: write recovery | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:717 | A committed create event cannot reconstruct an unwritten Markdown body. Rename recovery and retry rules were unstated despite the promise of deterministic repair. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Retain durable local creation/move recovery data, distinguish the log commit point, refuse new appends while repair is pending, and repair mirrors without duplicating events. AC-5 covers creation, transition and rename failures. Scratch recovery preserved the exact body and log. |
| SR-823 | high | IN-SCOPE | D/F: review identity | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:428; baseline R3 and K4 | The sole-file NULL reference changes meaning when another file is added; stems can change on rename. Equal round counts do not establish matching identities. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Make file references permanent and unique within subject; retain the default NULL binding; check a bijection of file/round identities. Missing subjects/files remain diagnosable. AC-14 and review ER aligned; SQLite demonstrated adding a second file. |
| SR-824 | high | IN-SCOPE | B/F: replay and revision reads | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:572; .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:787 | Legal transition edges alone do not prove continuity with the prior state. Initial shape, identity mutation and revision-path lookup were underspecified. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Require valid initial event, immutable identity, supported versions and matching transition from-state; keep attestation ownership. Resolve historical paths inside the requested revision and distinguish absence from invalid revision. Added AC-33. |
| SR-825 | medium | IN-SCOPE | B/D: review event schema | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:541; .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:461; .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md:574 | The schema required verdict/reviewer strings for all review events, contrary to legacy round import; R1 omitted refinement verdicts, and review_depth lacked its event slot. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Separate new gate/refinement fields from migration-only legacy nulls and unknown reviewers; include review_depth; preserve unknown historical values without inventing them. |
| SR-826 | medium | IN-SCOPE | D/F: logical types and vocabulary | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1067; agent_workflows/research_contract.py:290 ResearchName | Calling type the filename facet contradicts the research table: research facets classify report kind. The glossary also restricted Sets to plans and implied every sequence starts at zero. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Use logical record type, keep research_kind distinct, define cross-type Sets, and distinguish migrated seq 0 from new seq 1. Align ER labels. No filename or lifecycle contract changed. |
| SR-827 | medium | IN-SCOPE | D/security: generated SQL | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:922; baseline 4.5 and 4.5a | Banning all SQL construction conflicts with registry-generated table/column names: SQL value parameters cannot name identifiers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Bind all values; generate identifiers only from validated registry/internal names and quote them. SQLite probe confirms identifier placeholders fail and SQL-looking values remain data. |
| SR-828 | medium | IN-SCOPE | B: prose/diagram consistency | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1138 | Diagrams admitted invalid reads to the successful answer path, required events for invalid rows and items for empty runs, made missing review subjects impossible, bypassed the common revision loader, and omitted directed phase ordering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Align cardinalities, failure paths, run item ownership, loader routing, both-input revision join and phase C edge. Checked all ten Mermaid blocks against prose and tables; all ten rendered with the locally installed Mermaid CLI after a sequence-label syntax correction. |
| SR-829 | medium | IN-SCOPE | B/F: same-artifact merges | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1103; baseline AC-17 and 3c | The spec promised a git conflict for every same-artifact change and every status mirror. Identical appends can merge cleanly; notes do not change status. Repair could rewrite a committed prefix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Require valid merged replay regardless of git conflict; retain the winning committed prefix and explicitly confirm divergent-tail changes. AC-17 covers identical and differing appends. git merge-file demonstrated both outcomes. |
| SR-830 | medium | IN-SCOPE | F/security: provenance limits | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:258; GUIDING_PRINCIPLES.md P15 | Claims that hooks detect events no tool wrote and valid manual review edits contradict the self-asserted actor model. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | State the actual limit: validators check shape and append rules; they do not authenticate a valid event or prose edit. Preserve the existing honest actor limitation. |
| SR-831 | medium | IN-SCOPE | C/F: acceptance evidence | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:215; AGENTS.md Test outcomes, not code structure | AC-1a asserted caller ownership and open-call counts, contrary to the repository rule against code-pinning tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Use behavioral cache/source tests and keep ownership as a manual architecture audit. Extended acceptance cases for the repaired failure paths without adding production tests. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | How should SR-820 be resolved? | Key attempts by run, item position and attempt number; retain artifact lookup; report ambiguous actor joins and incomplete run data; invalidate deleted runs and root changes. AC-25 and ER/run flow aligned. SQLite probe retained both attempt-1 rows. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1026; agent_workflows/runner_shared.py:41891 attempt_no; agent_workflows/run_analytics_cache.py:343 source_fingerprint; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-2 | How should SR-821 be resolved? | Verify working bytes and membership, refresh target resolution, evict invalid state and report incomplete aggregates. In-memory SQLite follows the same validation; genuine source/resource failures still fail. AC-1a/AC-26 extended. Same-size/mtime and target-only probes reproduced the problems. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:677; baseline 4.3/4.5; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-3 | How should SR-822 be resolved? | Retain durable local creation/move recovery data, distinguish the log commit point, refuse new appends while repair is pending, and repair mirrors without duplicating events. AC-5 covers creation, transition and rename failures. Scratch recovery preserved the exact body and log. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:717; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-4 | How should SR-823 be resolved? | Make file references permanent and unique within subject; retain the default NULL binding; check a bijection of file/round identities. Missing subjects/files remain diagnosable. AC-14 and review ER aligned; SQLite demonstrated adding a second file. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:428; baseline R3 and K4; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-5 | How should SR-824 be resolved? | Require valid initial event, immutable identity, supported versions and matching transition from-state; keep attestation ownership. Resolve historical paths inside the requested revision and distinguish absence from invalid revision. Added AC-33. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:572; .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:787; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-6 | How should SR-825 be resolved? | Separate new gate/refinement fields from migration-only legacy nulls and unknown reviewers; include review_depth; preserve unknown historical values without inventing them. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:541; .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:461; .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md:574; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-7 | How should SR-826 be resolved? | Use logical record type, keep research_kind distinct, define cross-type Sets, and distinguish migrated seq 0 from new seq 1. Align ER labels. No filename or lifecycle contract changed. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1067; agent_workflows/research_contract.py:290 ResearchName; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-8 | How should SR-827 be resolved? | Bind all values; generate identifiers only from validated registry/internal names and quote them. SQLite probe confirms identifier placeholders fail and SQL-looking values remain data. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:922; baseline 4.5 and 4.5a; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-9 | How should SR-828 be resolved? | Align cardinalities, failure paths, run item ownership, loader routing, both-input revision join and phase C edge. Checked all ten Mermaid blocks against prose and tables; all ten rendered with the locally installed Mermaid CLI after a sequence-label syntax correction. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1138; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-10 | How should SR-829 be resolved? | Require valid merged replay regardless of git conflict; retain the winning committed prefix and explicitly confirm divergent-tail changes. AC-17 covers identical and differing appends. git merge-file demonstrated both outcomes. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1103; baseline AC-17 and 3c; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-11 | How should SR-830 be resolved? | State the actual limit: validators check shape and append rules; they do not authenticate a valid event or prose edit. Preserve the existing honest actor limitation. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:258; GUIDING_PRINCIPLES.md P15; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-12 | How should SR-831 be resolved? | Use behavioral cache/source tests and keep ownership as a manual architecture audit. Extended acceptance cases for the repaired failure paths without adding production tests. | Retain the contradictory or underspecified contract. | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:215; AGENTS.md Test outcomes, not code structure; reviewer correction preserves the chosen architecture; mechanism evidence below where applicable. | yes |
| D-13 | Should the cache use a generic entity/attribute/value or generic links model instead? | Retain typed per-type state, typed child tables, raw declarations plus resolved targets, and immutable source events. Strong recommendation for the stated closed-registry, rebuildable-cache contract. | Generic name/value or link tables; a tracked database; a separate log-reading path. | Spec 2 option O5, C5a, 4.5a rules 1-4 and maintainer decisions OQ-7/OQ-10; these fit required queries. Future performance remains an AC-13 measurement, not a claim of universal optimality. | yes |

### Scope and evidence

Explicit re-review of spec `4sd62s`, already `reviewed`, at baseline commit
`3c4b5cc22c8c92a6215dc243a9bdc8d3f2e7fc82`. All rubric views and the security lens were applied
serially. No other spec was a review candidate. Earlier rounds and spec history are preserved.
The four requested checks covered prose/diagrams, required repository compatibility, the eleven
technical writing requirements, and entity/data-structure fitness for stated and foreseeable use.
No runtime implementation, test suite change, or implementation plan was authored.

Current measurement: 4,405 tracked Markdown records excluding READMEs, including 1,706 plans,
1,287 reviews, 1,129 backlog records, 168 research records, 46 specs, 30 prompts and 26 walkthroughs.
There are 466 sidecar entries. The definition differs from historic inventories that counted templates;
old measurements remain explicitly historical. Of the research records, 28 have a filename day that
differs from their recorded creation day. Examples (id, filename day, creation day):
`cxe3dw, 20260903, 20260923`; `auwidn, 20261014, 20261018`; `kdg4uz, 20261016, 20261017`.

Compatibility checks included research naming/creation, explicit graduation declarations and reverse
links, runner item-local attempts, gate-ref types, review event ownership (`k3yx72` section 12),
quick-plan metadata/release gates (`4iyd78` section 6), and canonical setter behavior (`wy9aru`).
The facade-first build, human approval gate, force/worktree decisions, review ownership and terminal
migration exception remain intact. The current task does not adopt the writing standard into AGENTS.md.

The following output came from isolated SQLite, filesystem and git merge-file probes. These prove
specific mechanisms and counterexamples, not the unimplemented metadata subsystem or a full test suite.

```text
Original attempt key: second queue item for same artifact collides.
Revised attempt key: two item-local attempt 1 rows retained.
Stable review references: original NULL/default remains matched after adding a second file.
Review round check: equal counts do not imply matching round identities.
Freshness: unchanged size/mtime can hide changed working bytes; content digest detects it.
Reference freshness: resolving next against refreshed targets follows target-only changes.
SQL value binding: SQL-looking text remains data; the table survives.
Creation recovery: retained journal restores exact prose without appending another event.
Identical concurrent appends: git merge-file succeeds and retains one sequence 2 event.
Different concurrent appends: git merge-file reports a conflict.
SQL identifiers: value placeholders cannot name generated tables.
```

Preliminary validation before the two pending maintainer decisions:

```text
Review parse diagnostics: ()
Round 12 findings: 14
aw specs check: outcome=clean, exit=0, checked=1, findings=0
aw check all baseline: findings=69, exit=1
aw check all after review edits: findings=67, exit=1
New diagnostics: []
aw sanitize: outcome=clean, findings=0, exit=0
```

The repository-wide check is not clean; its remaining findings predate this review. No product test
suite was run because this change edits only a specification and its review record. The isolated
probes above are not implementation acceptance evidence.

## Round 13

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-818 | high | IN-SCOPE | D/F: graduation relationships | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1014 (\| `graduation_targets` \|); round 12 records original repository evidence | Reversing artifact lineage cannot recover a declared Graduated-To Set, especially with no linked child. The proposed table discards a distinct declaration. | C:Medium; U:Medium; S:Low; F:High; Overall:Medium-High | fixed | Maintainer accepted preservation through /askme on 2026-10-26 (OQ-15). Added graduation_targets for explicit Set declarations alongside lineage, preserved raw and unresolved references, and aligned navigation, ER diagram and AC-24. No reason was given. |
| SR-819 | high | IN-SCOPE | D/F: dates | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:613 (### 4.2b); round 12 records original repository evidence | One date cannot mean both filename date and creation day: research uses the Set date in filenames. 28 tracked research records have different filename and creation days. | C:Medium; U:Medium; S:Low; F:High; Overall:Medium-High | fixed | Maintainer accepted separate facts through /askme on 2026-10-26 (OQ-16). Separate filename_date, known legacy created_day and full created_at; unknown times stay unknown. Aligned migration, reader clocks, ER diagram and AC-19/AC-32. No reason was given. |
| SR-820 | high | IN-SCOPE | D/F: run entities | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1046 (### 4.5b); round 12 records original repository evidence | Attempt identity used artifact id instead of queue position. Repeated queue items collide. Deleted runs, changed roots and partial actor joins also lacked explicit handling. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Key attempts by run, item position and attempt number; retain artifact lookup; report ambiguous actor joins and incomplete run data; invalidate deleted runs and root changes. AC-25 and ER/run flow aligned. SQLite probe retained both attempt-1 rows. |
| SR-821 | high | IN-SCOPE | B/F: cache correctness | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:687 (- THE CACHE ANSWERS EVERY READ); round 12 records original repository evidence | Matching timestamps can hide changed bytes or directory members. Target-only changes leave resolved references stale. Invalid logs and in-memory fallback could look like clean empty results. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Verify working bytes and membership, refresh target resolution, evict invalid state and report incomplete aggregates. In-memory SQLite follows the same validation; genuine source/resource failures still fail. AC-1a/AC-26 extended. Same-size/mtime and target-only probes reproduced the problems. |
| SR-822 | high | IN-SCOPE | B/F: write recovery | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:727 (- WRITES); round 12 records original repository evidence | A committed create event cannot reconstruct an unwritten Markdown body. Rename recovery and retry rules were unstated despite the promise of deterministic repair. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Retain durable local creation/move recovery data, distinguish the log commit point, refuse new appends while repair is pending, and repair mirrors without duplicating events. AC-5 covers creation, transition and rename failures. Scratch recovery preserved the exact body and log. |
| SR-823 | high | IN-SCOPE | D/F: review identity | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:428 (K4. How each event); round 12 records original repository evidence | The sole-file NULL reference changes meaning when another file is added; stems can change on rename. Equal round counts do not establish matching identities. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Make file references permanent and unique within subject; retain the default NULL binding; check a bijection of file/round identities. Missing subjects/files remain diagnosable. AC-14 and review ER aligned; SQLite demonstrated adding a second file. |
| SR-824 | high | IN-SCOPE | B/F: replay and revision reads | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:572 (- Every `create`); round 12 records original repository evidence | Legal transition edges alone do not prove continuity with the prior state. Initial shape, identity mutation and revision-path lookup were underspecified. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Require valid initial event, immutable identity, supported versions and matching transition from-state; keep attestation ownership. Resolve historical paths inside the requested revision and distinguish absence from invalid revision. Added AC-33. |
| SR-825 | medium | IN-SCOPE | B/D: review event schema | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:541 (For a new `op: review`); round 12 records original repository evidence | The schema required verdict/reviewer strings for all review events, contrary to legacy round import; R1 omitted refinement verdicts, and review_depth lacked its event slot. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Separate new gate/refinement fields from migration-only legacy nulls and unknown reviewers; include review_depth; preserve unknown historical values without inventing them. |
| SR-826 | medium | IN-SCOPE | D/F: logical types and vocabulary | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1087 (### 4.5c); round 12 records original repository evidence | Calling type the filename facet contradicts the research table: research facets classify report kind. The glossary also restricted Sets to plans and implied every sequence starts at zero. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Use logical record type, keep research_kind distinct, define cross-type Sets, and distinguish migrated seq 0 from new seq 1. Align ER labels. No filename or lifecycle contract changed. |
| SR-827 | medium | IN-SCOPE | D/security: generated SQL | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:932 (- ROLE. The cache); round 12 records original repository evidence | Banning all SQL construction conflicts with registry-generated table/column names: SQL value parameters cannot name identifiers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Bind all values; generate identifiers only from validated registry/internal names and quote them. SQLite probe confirms identifier placeholders fail and SQL-looking values remain data. |
| SR-828 | medium | IN-SCOPE | B: prose/diagram consistency | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1158 (### 4.9); round 12 records original repository evidence | Diagrams admitted invalid reads to the successful answer path, required events for invalid rows and items for empty runs, made missing review subjects impossible, bypassed the common revision loader, and omitted directed phase ordering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Align cardinalities, failure paths, run item ownership, loader routing, both-input revision join and phase C edge. Checked all ten Mermaid blocks against prose and tables; all ten rendered with the locally installed Mermaid CLI after a sequence-label syntax correction. |
| SR-829 | medium | IN-SCOPE | B/F: same-artifact merges | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:1123 (### 4.7); round 12 records original repository evidence | The spec promised a git conflict for every same-artifact change and every status mirror. Identical appends can merge cleanly; notes do not change status. Repair could rewrite a committed prefix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Require valid merged replay regardless of git conflict; retain the winning committed prefix and explicitly confirm divergent-tail changes. AC-17 covers identical and differing appends. git merge-file demonstrated both outcomes. |
| SR-830 | medium | IN-SCOPE | F/security: provenance limits | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:258 (- Tool-written events); round 12 records original repository evidence | Claims that hooks detect events no tool wrote and valid manual review edits contradict the self-asserted actor model. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | State the actual limit: validators check shape and append rules; they do not authenticate a valid event or prose edit. Preserve the existing honest actor limitation. |
| SR-831 | medium | IN-SCOPE | C/F: acceptance evidence | .aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:215 (\| AC-1a \|); round 12 records original repository evidence | AC-1a asserted caller ownership and open-call counts, contrary to the repository rule against code-pinning tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Use behavioral cache/source tests and keep ownership as a manual architecture audit. Extended acceptance cases for the repaired failure paths without adding production tests. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Which graduation relationship contract should replace the lossy proposal? | Preserve explicit plan-Set declarations and individual origin links. | Infer every output solely from individual origin links. | User accepted the recommendation via /askme on 2026-10-26; spec OQ-15. No reason was given. Source schema becomes hard to reverse after migration. | no |
| D-2 | Should filename dates and creation information remain separate? | Preserve filename date, known legacy creation day, and full timestamps for new creations; never invent missing times. | Keep only filename date for migrated records. | User chose separate facts via /askme on 2026-10-26; spec OQ-16. No reason was given. Source schema becomes hard to reverse after migration. | no |

### Final assessment

This round closes the two decisions left open in round 12 and carries forward the twelve reviewed
fixes so the current round contains the complete disposition. Round 12 and all earlier rounds remain
unchanged. Both answers are recorded in the spec before finalization. The review remains a spec
review; no human approval has been recorded.

The chosen model fits the stated objectives after these corrections. Per-record logs retain history;
typed state and relationship tables support the required queries; the disposable database can evolve
with the registry. Explicit group declarations, individual origins, creation information and queue-item
identity must remain distinct. A generic name/value or generic relationship table would not resolve
those semantic distinctions. No claim is made that this model is optimal for every future workload;
AC-13 still requires real end-to-end measurements before implementation performance can be claimed.

The writing check covered all eleven supplied requirements, including consistent terms, explicit
exceptions, actionable acceptance evidence and preservation of previous decisions. New question ids
are OQ-15/OQ-16 because OQ-13/OQ-14 were already used by historical decisions. The separate request to
make /askme mandatory was recorded and committed as backlog n2lr3g; it is not part of the spec's scope.

### Final validation

Structural and review-record checks:

```text
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
Review parse diagnostics: ()
Current round: 13 findings: 14 unresolved: 0
aw check all: 67 findings; exit 1
New diagnostics: []
aw sanitize: clean findings 0 exit 0
```

`aw check all` was compared with the pre-review baseline of 69 findings, not represented as a clean
repository. The current 67 diagnostics are all in that baseline. `git diff --check` exited 0 with
no output. All ten diagrams rendered with the installed Mermaid CLI; actual renderer output:

```text
Found 10 mermaid charts in Markdown input
 ✅ ./metastore-final-rendered-5.svg
 ✅ ./metastore-final-rendered-2.svg
 ✅ ./metastore-final-rendered-1.svg
 ✅ ./metastore-final-rendered-6.svg
 ✅ ./metastore-final-rendered-4.svg
 ✅ ./metastore-final-rendered-3.svg
 ✅ ./metastore-final-rendered-7.svg
 ✅ ./metastore-final-rendered-8.svg
 ✅ ./metastore-final-rendered-10.svg
 ✅ ./metastore-final-rendered-9.svg
 ✅ /tmp/metastore-final-rendered.md
```

The diagram check required running the installed Chromium renderer outside the filesystem sandbox;
only temporary render files were produced. The first new sequence label contained a semicolon that
Mermaid treated as syntax; it was corrected before the successful run. This rendering check establishes
syntax, not semantic correctness; the prose/schema comparison supplies the separate semantic review.
No product suite was run for these document changes. The review record includes the isolated mechanism
probe output in round 12 and does not claim that unimplemented acceptance criteria have passed.

## Round 14

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-901 | high | UNDER-SCOPE | B/D: attestation ownership | agent_workflows/status_set.py:1689-1725 (the `rec.record_type == "plans"` branches matching `^- Approval:` and `^- Readiness:`); spec section 1 P2 names `Approval`; 62 plans carry `- Approval:` | The spec gives `readiness` and `coverage` owning events, but `approval` (named as forgeable in P2) had no owner, so it would become a generic `set` field that anyone could write. The setter's existing side effects (write `Approval` on entering `approved`, strip it on leaving, strip `Readiness` on a backward move to `draft`/`to-review`) were not carried into the event model, so a replay could keep a stale attestation. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | fixed | 4.4 adds a transition-owned `approval` rule and same-append `unset` rules for leaving `approved` and moving backward, refused on replay; AC-15 extended with cases (4) and (5). Port of current behavior; no new rule. |
| SR-902 | medium | UNDER-SCOPE | F/G: new repositories | spec 5.3 and AC-11; `aw install --help`; `aw setup --help` | 5.3 refuses every command when `metadata_schema` is below 2, and only the migration writes the stamp. A brand-new repository has no stamp, so every command on a fresh install would refuse and tell the user to migrate records that do not exist. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | fixed | 5.3 now stamps `metadata_schema: 2` at install or setup when no legacy record exists; absent stamp with legacy records still means unmigrated; only the migration and this install case write it. AC-11 gains cases (2) and (3). |
| SR-903 | medium | IN-SCOPE | D/F: lossless import vs output safety | spec 4.2 prose-field bullet; agent_workflows/attention_contract.py:752 `refuse_unsafe_descriptive`, :668 `MAX_PROSE_DESCRIPTIVE_LEN = 4300`; measured 34 of 82,506 inline history lines fail `is_safe_prose_descriptive` (33 too long, max 5,736; 1 control character) | 4.2 required the unsafe-value refusal on EVERY string `artifact_meta` writes into a log, while 4.2a and AC-10 require every legacy line byte-for-byte. The two rules contradict on 34 real lines, so the migration would refuse or truncate history. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | 4.2 exempts only the migration's imported values (`legacy.line`, sidecar object, `legacy_verdict`), keeps the refusal for every other writer, and requires display through the output-safety rules; AC-10 adds the long-line and control-character round-trip cases and a refusal case for a post-cutover setter. |
| SR-904 | low | IN-SCOPE | A: compatibility table | spec section 9 `k3yx72` row; `.aw/records/plans/executed/` holds all six `revsteps` plans (tiwj2o, 3bwrfx, gv3smb, uiyoax, is2xiv, kk62qt); `ipd_schema.META_REVIEW_DEPTH` | The row listed four Stage 1 plans as executed; the orchestrator `tiwj2o` and pilot `kk62qt` are also executed, and Stage 2 is unauthored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Row updated with all six plans and the schema symbol. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | How is the plan `approval` attestation owned in the event model (SR-901)? | Owned by the `approved` transition; unset in the same append when leaving `approved`; `readiness` unset on backward moves to `draft`/`to-review`. | Generic field; a separate `op: approval` event. | Ports `status_set.py:1689-1725` exactly; P2 and the existing readiness/coverage ownership pattern in 4.4; adds no new rule, so it does not change what the spec decides. | yes |
| D-2 | How does a new repository get a stamp (SR-902)? | Install or setup stamps `metadata_schema: 2` only when no legacy record exists. | Treat an absent stamp as new (would let an unmigrated repository bypass 5.3); require `aw migrate metadata` on empty repositories (useless step). | 5.3 intent (refuse only unmigrated data); C9 (one format). Implementation detail inside the spec's own decision. | yes |
| D-3 | Which rule wins when lossless import meets the output-safety refusal (SR-903)? | Lossless import wins for migration-imported values only; every other writer keeps the refusal; display uses output-safety rendering. | Truncate or refuse long legacy lines (loses history, contradicts AC-10); drop the refusal everywhere (weakens `uz05bl`/`dtg7dz`). | 4.2a and AC-10 (no legacy text lost) and the maintainer's lossless-migration rulings (OQ-13, OQ-14, OQ-16); measured 34 affected lines. | yes |

### Scope and evidence

Explicit re-review of spec `4sd62s`, already `reviewed`, at baseline commit
`45a1b3e33695426c5e9fb2081673faa59ec6bc71` (round 13 head). Reviewer:
opencode/its_direct/pt3-claude-opus-5.5-1m-us. All rubric views A to G, the eight personas and the
security lens were applied to the full text. Earlier rounds are preserved unchanged. No code, test or
plan was written.

Re-verified anchors (all resolve): `specs._sidecar_append` (specs.py:234),
`specs._review_attestation_refusal` (:1240), `review_findings.review_attestation_missing` (:1022),
`review_findings.subject_gating_blocks` (:848), `check_engine.graduation_cluster` (:5566),
`check_engine._status_meta` (:3266), `check_engine._blob_text` (:3251),
`check_engine.check_spec_review_attestation` (:8236), `plan_readiness.review_staleness_index` (:1372),
`ipd_lifecycle._LEGAL_BACKWARD_EDGES` (:1172), `ipd_lifecycle._release_own_plan_edit_before_landing`
(:3773), `runner_shared.integrate_lane_branch` (:8081), `runner_shared.read_merge_stage` (:5324),
`runner_shared._body_change_is_history_insert_only` (:4920), `record_history.append_rename` (:199),
`record_history.append_advisory` (:80), `research_cmd.plan_new` (:212), `research_contract.ResearchName`
(:303), `run_analytics_cache.source_fingerprint` (:343), `project_context.resolve_project_context`
(:1635), `layout_migration.MigrationManager` (:274), `layout.TRAVERSAL_EXCLUSIONS` (:110),
`artifact_audit._INDEX_CACHE` (:1085), `config.applies_to_artifact_date` (:2313),
`artifact_core.ID6_RE` = `\A[0-9a-z]{6}\Z`, `pyproject.toml` dependencies `["filelock>=3"]`,
`.aw/.gitignore` `records/history.jsonl` (line 11) and `/state/` (line 65). `agent_workflows/migrations/`
and `aw migrate` do not exist yet, as 5.1 states. `aw show --help` has no `--history`, as 4.8 states.

Path-collision probe for 4.2 (one log per id6): 3,044 distinct id6 values in front-matter `- Id:` or
YAML `id:` across non-review, non-comms records; 0 shared by two records; 0 shared across record types.

Current measurements (r14): 468 sidecar lines; 82,506 inline history lines, 34 failing
`is_safe_prose_descriptive`; 62 plans with `- Approval:`.

### Final validation

```text
aw specs check <spec>: all specs conform. 1 specs checked.
git diff --check <spec>: exit 0
aw check all (before and after): errors 13, warnings 0, info 54 (unchanged; no new diagnostic)
```

## Round 15

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-905 | high | UNDER-SCOPE | F: details view | `attention._extract_detail` reads `- Summary:`, `Scope`, `Concern`, `Question`, `Title`, then H1; spec 4.2 moved those bullets to body prose; 4.5a `artifacts` had only `title` | `aw attention --details` would lose its source at the cutover; no short description was stored anywhere. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | fixed | Maintainer decision OQ-19: tracked `short_description` field plus `artifacts.short_description`; migration fills it in today's order and refuses (does not truncate) a too-long source. AC-36. |
| SR-906 | high | UNDER-SCOPE | D/F: path history | spec 4.2 `rename` stored "basenames, never paths"; moving transitions recorded no path; `artifacts.path` current only | Path history was unrecoverable except via `git log --follow`, which squash merges and shallow clones lose. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | Maintainer decision OQ-17: every path-bearing event carries the NEW records-root-relative `path` only (the previous path is the prior event's); who moved it is `actor`/`by_human`; new `artifact_paths` table. AC-34. |
| SR-907 | high | UNDER-SCOPE | F: execution record | `outcomes/*.json` `files_changed` (gitignored); plan body E/V items (N3); `state.json` attempt `verify_verdict_state`, `verify_has_evidence` | Actual changed files, E/V item state, V-item evidence and the agreed verification decision existed only in prose or in local run state; nothing could be queried or survived a clone. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Maintainer decision OQ-18: tracked `finalize` event (merged-diff `changed_paths`, `scope_result`, per-item `verification` with evidence digest, not text); `plan_items` and `changed_paths` tables; drift rule `evidence-changed-after-finalize`. AC-35. |
| SR-908 | high | UNDER-SCOPE | F: tokens, time, cost | `state.json` attempt `tokens`/`verify_tokens`/`cost` (3,291 / 981 / 2,220 of 3,752 attempts); session `step_finish` tokens and cost; `run_analytics_pricing` `currency: str = "USD"` | Tokens and cost were not in the schema at any level; amounts carried no currency; no question about cost per E-item or V-item could be answered. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Maintainer decision OQ-20: tracked `turn` events with per-turn totals; cache-only `turn_steps`; `AW-ITEM` marker with self-reported per-item totals (`turn_items`); amounts as exact decimal strings with ISO 4217 codes, converted only on display with a named dated rate. N4 amended for totals only. AC-37, 3c limits. |
| SR-909 | medium | UNDER-SCOPE | F: run index | 4.5b indexed about 14 of about 60 attempt fields and no other run file; measured 598 runs, about 2.3 GB | `aw runs analyze` and attention queries could not use the cache, so run analytics kept a second reader of run state (P1). | C:Low; U:Low; S:Medium; F:Low; Overall:Low | fixed | Maintainer decision OQ-21: index every structured field (state, events, outcomes, questions, telemetry, step usage) with `extra_json` for unnamed fields; never copy text bodies (path and digest in `run_files`). AC-38. |
| SR-910 | medium | IN-SCOPE | B: diagram detail | 4.9.1 notes were short or absent for most attributes; maintainer asked for full notes on every entity and attribute | Readers could not tell meaning, source, allowed values or NULL rules from the diagrams. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | 4.9.1 rewritten as five diagrams with a full note on every entity and column; a script cross-check confirmed all 31 tables in 4.5a/4.5b match their diagram columns (0 mismatches); all 12 mermaid blocks render. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Where does the short description live (OQ-19)? | Tracked log field plus `artifacts` column. | Third front-matter key; body-only. | Maintainer via /askme 2026-10-26. | no |
| D-2 | How are path changes recorded (OQ-17)? | New path only on each path-bearing event; actor and time on the event. | from and to on each event; current path only. | Maintainer via /askme 2026-10-26, with the reason that the previous path is the previous entry. | no |
| D-3 | How is execution recorded (OQ-18)? | Tracked `finalize` event plus indexed tables. | Cache-only from run data; no E/V. | Maintainer via /askme 2026-10-26. | no |
| D-4 | Token, cost, time granularity and currency (OQ-20)? | Turn tracked, step cached, item self-reported; exact amounts with currency, convert on display. | Cache only; every step tracked; stored conversions; USD only. | Maintainer via /askme 2026-10-26. | no |
| D-5 | How much run data is indexed (OQ-21)? | All structured data, no text bodies. | Including text; minimum only. | Maintainer via /askme 2026-10-26. | yes |

### Scope and evidence

Explicit re-review of spec `4sd62s`, already `reviewed`, at baseline `d88fef004` (decisions OQ-17 to
OQ-21 recorded and committed before editing; earlier baseline `45ba268c1`). Reviewer:
opencode/its_direct/pt3-claude-opus-5.5-1m-us. Triggered by maintainer questions on the entity
diagrams. Earlier rounds are preserved unchanged. No code, test or plan was written.

Measurements (2026-10-26, this machine): 598 run directories, about 2.3 GB (sessions 1.9 GB,
`manifest.json` 225 MB, `state.json` 58 MB, `events.jsonl` 31 MB, prompts 25 MB, telemetry 9 MB,
outcomes 8 MB); 3,752 recorded attempts, tokens on 3,291, cost on 2,220, verify tokens on 981; one
Antigravity execute session had 2,164 steps, 679 with usage; OpenCode `step_finish` records
per-step tokens and cost; no step records an E-* or V-* id.

### Final validation

```text
aw specs check <spec>: all specs conform. 1 specs checked.
git diff --check <spec>: exit 0
Diagram/prose column cross-check: tables 31 mismatches 0
mermaid-cli 12.0.0: Found 12 mermaid charts in Markdown input; 12 rendered (one sequence-note
semicolon was corrected before the successful run)
```

## Round 16

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-911 | high | IN-SCOPE | B/D: finalize source | 4.2 `op: finalize` "Taken from the merged diff"; `runner_shared` merge-conflict prompt "the plan was already finalized on the lane" | Finalize runs in the lane before integration, so no merged diff exists when the event is written; a hand finalize has no merge. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | `changed_paths` is the git diff from the begin-receipt base to the finalize tip, excluding the plan file and its log; integration never rewrites it. AC-35, diagram 2 and OQ-18 (dated correction) aligned. |
| SR-912 | high | IN-SCOPE | D/F: turn event placement | 4.2 "appended by the driver when the turn ends" vs 4.9.3 "Finalize adds the finalize event and its turn events" | Contradictory writers; a main-checkout append would conflict with the lane on every run. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Maintainer decision OQ-23 plus crash import: lane copy as each turn ends, main checkout for an attempt that does not merge, idempotent importer, one-copy rule, post-finalize turns accepted by the executed-plan hook. |
| SR-913 | high | UNDER-SCOPE | B: same-append rules unverifiable | 4.2 replay, 4.4 readiness/approval rules, finalize | The log carried no write grouping, so no "same append" rule could be checked by the loader. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | Maintainer decision OQ-24: `append` key on every event; LOADER VALIDATION and AC-39. |
| SR-914 | high | IN-SCOPE | D: short-description migration | `_extract_detail` cascade measured: 1,402 sources over 300 characters, mostly terminal records | Round 15's refuse-until-shortened rule would block the cutover permanently. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | fixed | Maintainer decision OQ-22: a cheap model writes every description through a reusable gitignored description journal (dry run generates; reuse by source digest; resume). C8, 5.2 step 0, 3c, AC-36, diagram 4.9.6 aligned. |
| SR-915 | high | IN-SCOPE | B/D: event-owned fields | 4.2 replay "Generic set/unset cannot write ... any EVENT-OWNED field" vs 4.4/AC-15 requiring `set approval` and `unset readiness` in owning appends | The replay rule forbade writes that 4.4 and the ACs require; `readiness` had two encodings. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | One rule: an event-owned `set`/`unset` is valid only inside its owner's append; `readiness`/`review_depth` only from the gate review payload. 4.4, AC-15, AC-39 aligned. |
| SR-916 | high | IN-SCOPE | F: run-index exclusions | AC-38(1) "every field ... appears" vs AC-38(3) no session id/argv/absolute path; `state.json` carries `session_id`, `argv`, absolute `repo`, `worktree`, `log` | Self-contradicting criteria. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | fixed | 4.5b EXCLUDED CLASSES named; AC-38(1) excepts them; `payload_json` and `extra_json` follow the same rule. |
| SR-917 | high | IN-SCOPE | A: run tables vs real data | `state.json` has no top-level host/outcome/terminal; `driver` is `{id, path, sha256, loaded_code}`; `git` is `{aw_version, commit, dirty}`; attempts have no `ace`/`outcome`/`variant`/`requested_model`; outcome files carry no attempt number; question status vocabulary is `open`, `answered` or `stale` | `runs`, `attempts`, `run_outcomes`, `run_questions` and diagram notes named columns and values with no source. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | Columns and notes re-derived from measured data and `question_inbox.VALID_QUESTION_STATUSES`; source-key renames stated; derived columns (`host`, `terminal`) named. |
| SR-918 | medium | IN-SCOPE | D: turn identity | `turn_steps` PK and `turns` lacked a turn ordinal and item position; session `log_suffix` values include hook-refusal, audit, set-correction-N, review-step-NN | Two correction turns collided; turns could not be joined to steps; the role list omitted real turn kinds. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | `turn_index` and `item_position` added; `turn_role` vocabulary derived from `log_suffix`. |
| SR-919 | medium | IN-SCOPE | D: path history coverage and drift | archive moves (`plans_archive.apply_shard_moves`), research moves; AC-26 hand `git mv` | Path-bearing list missed archive moves; no drift rule between discovered and logged path; `by_human: false` contradicted the `by_human` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `archive` verb; research shelf moves are path-bearing transitions; 4.6 `path-drift` row; repair completes journaled moves with no event or appends a confirmed rename. |
| SR-920 | medium | IN-SCOPE | D: scope_result migration | `ipd_lifecycle._format_scope_exceeded_value` writes `path (reason)` only for accepted out-of-scope paths | "within when false" had no source; reasons were dropped; widened paths are unrecoverable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | Absent bullet means unknown; reasons kept; `scope_exceeded_raw` for the round trip; `legacy_scope_exceptions` table. |
| SR-921 | medium | IN-SCOPE | B: stale prose across sections | section 0 terms, C7/AC-6, O5, N2, N4, 3c C2 limit, 4.5a rule 4, META rebuild rule, AC-7, AC-13, AC-23, AC-24, AC-25, AC-31, AC-32, 4.4, 4.8, 5.4, 6, 7, 9 | Many statements predated round 15 (one added event line, basenames, no tracked run data, AC table lists, missing writers and docs, phase B could not hold new events). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Each location rewritten; phase B/C rule added for which writers start at the cutover; module-direction note; 4.9.3, 4.9.6, 4.9.8 and ER notes aligned. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Where are turn events written (OQ-23)? | Lane; main only for an unmerged attempt; idempotent crash import. | Finalize only; main always. | Maintainer via /askme 2026-10-26, with the crash-import addition. | no |
| D-2 | How is a write grouped (OQ-24)? | `append` key. | Infer from at+actor; writer-only. | Maintainer via /askme 2026-10-26. | no |
| D-3 | How are short descriptions filled (OQ-22)? | Model-generated for every record through a reusable description journal; dry run generates. | Cascade fallback; truncate; generate at apply only. | Maintainer via /askme 2026-10-26 (design of the journal is the maintainer's). | yes |
| D-4 | How does `changed_paths` get its diff (SR-911)? | Begin-receipt base to finalize tip. | Merged diff (unavailable); agent report. | 4.2 finalize runs in the lane (`runner_shared`); preserves OQ-18's decision. | yes |
| D-5 | Per-V-item verifier verdict source (SR-917)? | Copy the attempt verdict to each V-item until the verifier reports per item; plan decides the change. | Require per-item verifier output now. | Today's verifier writes one verdict per attempt (`*-verification.json`). | yes |

### Scope and evidence

Internal-consistency review requested by the maintainer after round 15, at baseline `d1c411677`
(decisions OQ-22 to OQ-24 recorded in `8b7b85244` and `a321957d8` before editing). Reviewer:
opencode/its_direct/pt3-claude-opus-5.5-1m-us, with two independent full-text consistency passes.
Measurements (2026-10-26): 596 run directories; 96 distinct `events.jsonl` event types (median 15,
max 34 per run); queue actions execute, review, plan, orchestrate, skip; attempt
`worktree_disposition` created, attempt-scoped, adopted; `model_source` options or absent;
`integration_signal` verifier, driver-run-suite, suite-failed, verifier-declined; verification
verdicts VERIFIED, BLOCKED, CORRECTION_REQUIRED; session `log_suffix` values from `runner_shared`;
`ipd_schema.EXEC_STATES` and `VALIDATION_RESULTS`; `question_inbox.VALID_QUESTION_STATUSES`;
`_extract_detail` sources Scope 1,726, Summary 1,305, title 76, Concern 1, none 7, 1,402 over 300.

### Final validation

```text
aw specs check <spec>: all specs conform. 1 specs checked.
git diff --check <spec>: exit 0
Diagram/prose column cross-check: tables 32 mismatches 0
Op list (4.2): checkpoint, coverage, create, finalize, legacy, note, rename, review, set, transition, turn, unset
mermaid-cli 12.0.0: Found 12 mermaid charts in Markdown input; 12 rendered
aw check all: errors 13, warnings 0, info 54 (unchanged)
aw sanitize --agent: clean
```
