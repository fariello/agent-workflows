# Review findings: ipd 9ifwdx

- Subject-Id: 9ifwdx
- Subject-Type: ipd
- Reviewed-At: 2026-11-22
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `591a7c3ee87d85d9448759677ee5e6bbcd0305b4` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261122-rereviewux-01-9ifwdx-clear-review-staleness-on-human-approval-and-add-aw-show-sta.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is the only plan in Set `rereviewux`, and the Set has no orchestrator. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0; info only: `IPD-Z602` on E-02 and `IPD-C802` x2 on the scaffold validation-rule boilerplate). `aw attention --check` returned exit 0, and mypy on the six originally scoped modules reported success.

AW-TIER: complex

### Step T

1. Yes: the plan changes a spec-defined contract (the ipd-spec "Review staleness advisory" baseline, which today is "the newest git commit ... whose commit subject begins with `plan-review:`") and the `25kzda` 2.9 basis-record deletion rule. It also adds public CLI surface (`aw show stale-reviews`, `aw att --stale-review`, and a new `aw set` flag).
2. Yes: it changes what a human-approval attestation (`--by-human`) means, since that attestation now clears a review-staleness signal, and it deletes local state files under `.aw/state/review-basis/`.
3. Yes: after review the plan has 8 E-items and 10 work Scope-Paths across 8 modules, past the `IPD-Z603` followability guidance (5 and 8).
4. No: the original `- Scope-Paths:` missed `agent_workflows/ipd_lint.py`, `agent_workflows/command_surface.py`, both governing specs, and `CHANGELOG.md`. All are added now.
5. Yes: a wrong baseline either hides real post-review edits from every staleness surface, or never clears them. A bulk guard that `--yes` satisfies would let an agent clear staleness on edits nobody read.

`AW-TIER: complex`

### Step R1

- Checked: `agent_workflows/plan_readiness.py` (`review_staleness_index` at 1459-1602, with its single `git log --format=%x01%H%x00%s --name-only` subject filter `subject.startswith("plan-review:")` at 1540 and its single `git cat-file --batch`; `review_staleness_from_texts` at 1365; `_STALENESS_CACHE` at 1451). Also `agent_workflows/review_basis.py` (`basis_dir` 34, `contract_digest` 40, `record_basis` 56 where empty targets unlinks, `StaleBasis` 47, `stale_bases(prune=True)` 161, `_format_rereview_command` 281, `report_stale_bases` 415; no `clear_basis` exists). `agent_workflows/status_set.py`: same-status tag and default message at 1527-1531; `--by-human` actor suffix at 1664-1665; stale warning with the hardcoded `aw oc review` at 1641; `_write_history_anyway` and `should_write_history` at 1883-1888; the pure no-op return at 2040-2046; `_offer_self_commit` subject `chore({label}): set status {target_status}` at 2546; `yes` at 3787; the interactive refusal prompt at 3800-3826; the agent/json `--yes` gate at 3888. Hint sites: `check_engine.py:4072` (`check_ipd_review_stale` 4031) and `ipd_lint.py:3022` (`_review_stale_advisory` 2973). Host config: `runner_profiles.load()` 1253 and `default_runner` 571. `.aw/config/project.json` holds only `enabled_hosts` (opencode, claude, antigravity). Both host drivers accept `--yes` (`oc_runipd.py:5124`, `agy_runipd.py:4319`). For `aw show` I checked the `cli.py:4945` parser (one positional `action_ref`), `_run_show` at 14064, and the `command_surface.py` `show` declaration at ~221. The attention legend is at `attention.py:3967-3970` and prints only when colored. Spec text: ipd-spec line 46 and `25kzda` lines 660-663. Backlog `i8dc07` OQ-02 is resolved as Option A.
- Found F1: the plan's baseline wording ("human-attested approval commit") cannot be implemented on the subject filter it extends. Real approval commits carry `chore(plans): set status approved` (`git log` shows `fd12f9abc`, `f64594372`) or arbitrary subjects, so a subject match would almost never fire. Fixed in E-01: the match is now on blob content, and the commit set is bounded to commits newer than the last `plan-review:` commit.
- Found F4: the plan named only one of three hardcoded hint sites, and "repo/user configuration" named no real source. Fixed with E-07.
- Found F2: two specs are contradicted by the plan, yet the plan said "No separate specification requires revision". Fixed with E-08.

### Step R2

- Checked: the E/V bijection after `aw ipd sync --apply` (E-01..E-08 to V-01..V-08, `Highest E allocated: 08`), the dependency order (E-01 before E-02, then E-06, E-03, E-04, E-07, E-05, and E-08; every `Depends on` names an earlier item), Scope-Paths completeness, and V-item evidence specificity.
- Found F3: E-02(d) gated non-interactive bulk approval on `--yes`, but agent and json callers already need `--yes` for every mutation (`status_set.py:3888`), so the guard confirmed nothing. Fixed: E-06 adds a dedicated `--accept-stale` flag with a defined trigger, refusal rule, exit code, and recording.
- Found F6: E-02 and E-04 each bundled two concerns in different files (E-02 also lacked the no-op mechanics). Fixed: split into E-02/E-06 and E-04/E-07, with `aw ipd sync`-assigned ids.
- Found F8: V-05 cited `aw sanitize` without `--agent`. V-01..V-05 named no units. The original V-02 and V-04 each validated two unrelated behaviors. Fixed: each V-item now names its units and demands falsifiable pasted evidence.
- Found F7: the gate lacked a scope-fence declaration, the honesty rule, never-push, the hand-`git mv` prohibition, and conditional lifecycle ownership. Fixed in the gate section; the fence is worded as a declaration with `--scope-reason`/`--scope-ack`, not as a STOP directive.

### Step R3

- Checked (full form): attestation integrity, local state deletion, and output leakage. Matching `--by-human` in committed blob content, not in the commit subject or the working tree, keeps the baseline tied to a committed attested record. It is still an author-asserted attestation, as it is everywhere `--by-human` is honored, so this plan widens what that attestation does without weakening how it is written. The bulk guard (E-06) is the control against an agent clearing staleness for many plans through one Set selector. Requiring a flag distinct from `--yes`, and recording it in the history actor, makes any override visible afterwards. `clear_basis` deletes only `basis_dir(repo)/<id6>.json`, where the id6 comes from a resolved record, so a crafted path cannot escape. The read-only view must use `stale_bases(prune=False)`, because the default prune deletes files; F5 made this explicit. `rereview_host` reads a user-local store that may hold institution-specific model ids, but it emits only the canonical `oc`/`agy` token.
- No separate security finding beyond F3 and F5.

### Step R4

- Checked: correctness (the baseline cannot regress to "no baseline", because a path with no `plan-review:` commit stays silent; the `same_status_message_is_duplicate` suppression is defeated only by a differing SHA clause, so a second re-affirmation after a later edit still writes), performance, operability, and tests. Measured: an unscoped `git log -G` over the 131 pending plans took about 4.5s, against 0.49s for the plain log. E-01 therefore keeps today's one-`git log` and one-`cat-file --batch` model and examines only commits newer than each path's last review. Tests: the conftest pops `AW_CONFIG_DIR` around each test, so the host tests must set it inside the test (E-05 group 6). The legend prints only when colored, so its test needs `--color` (F10). The `legacy_flags`-versus-parser tests (`tests/test_group_verb_policy.py:1042` and its siblings) require the new flags to be declared in `command_surface.py`.
- Found F9: the "Under-scope: none" claim was wrong (see F2, F4, F5). Corrected.
- Found F10: no cross-reference to approved plan `t4gl15`, which ports `review_staleness_index` onto `artifact_meta.read_at`. Added to the Scope check.

### Step R5

- Checked as maintainer, as a newcomer, and as an executing agent. A newcomer could not tell from the original Goal what "basis-stale" means; it is now defined in the Goal. An executor could not implement "requires `--yes` / explicit confirmation" or "derive the host from repo/user configuration" without guessing; both are now concrete (E-06, E-07). A maintainer would want to know whether an uncommitted approval clears the marker; decision D2 now states that it does not.

### Step R6

- Checked: whether to split into a Set. All eight items deliver one user-visible feature, and E-02, E-03, E-05, E-06, and E-08 depend on E-01's baseline rule, so a Set would add coordination overhead without independent deliverables. The followability advisory (`IPD-Z603`: 8 E-items, 10 work Scope-Paths) is answered in the gate's cohesion rationale rather than by splitting. No split is recommended.

### Step R7

- Checked: pending plans citing `review_staleness_index` or `stale-review`. The only other one is `t4gl15` (Set `metastore`, approved), which lists `plan_readiness.review_staleness_index` among the git-blob metadata readers it will port to `artifact_meta.read_at`. Overlap is low; the port must carry E-01's rule, as now noted in the Scope check. Backlog `i8dc07` (verb-first CLI, OQ-02 Option A) is consistent with E-03's reserved view name and owns the escape hatch. Backlog `1iojci` owns selector unification, so `aw show stale-reviews` takes no selectors here (decision D4).

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | 7 work Scope-Paths; Scope prose named one hint site | Added `ipd_lint.py`, `command_surface.py`, `CHANGELOG.md`, and both specs; Scope prose names all three hint sites and the spec sync | F2, F4, F5, F9 |
| Goal and diagram | Used "self-stale" and "basis-stale" without defining them | Defines both signals and where each is computed; diagram edges say "committed" and name the deletion | Requirement: explain terms on first use; F1 |
| E-01 | "recognizes the latest human-attested approval commit" | Blob-content baseline rule, bounded commit set, unchanged batch cost model, uncommitted approvals excluded | F1 |
| E-02 / new E-06 | One item with four sub-steps; `--yes` guard | E-02: `clear_basis` plus re-affirmation mechanics; E-06: `--accept-stale` guard with trigger, refusal, and recording | F3, F6 |
| E-03 | Unspecified dispatch, filters, and prune behavior | Reserved view name per `i8dc07` OQ-02, `review_contract_diff` helper, `stale_bases(prune=False)`, json/agent/empty behavior, `--diff` declared | F5 |
| E-04 / new E-07 | Filter, legend, and host hint in one item; one hint site | E-04: filter and legend; E-07: `review_basis.rereview_host` at all three sites | F4, F6 |
| E-05 | Five test groups | Six groups keyed to E-items, with non-subject approval, uncommitted approval, `--color`, and `AW_CONFIG_DIR` cases | F8, F10 |
| New E-08 | Absent | Spec amendments, `aw specs note`, and CHANGELOG | F2, F9 |
| Spec / documentation sync | "No separate specification requires revision" | Names both specs and says why each must change | F2 |
| Scope check | "Under-scope: none" | Lists the corrected omissions and the `t4gl15` note | F9, F10 |
| Proposed changes, Findings table, Deferred | Referenced the old E split | Renumbered to E-01..E-08; added review decisions D1-D5; deferred the basis text diff with its reason | F6 |
| V-01..V-08 | Unit-free evidence; `aw sanitize` | Each V names its units and demands falsifiable pasted output; `aw sanitize --agent` | F8 |
| Deferred / out of scope | Four rows with no carrier | Rows 1-2 name carriers `i8dc07` and `1iojci`; rows 3-4 carry `Carrier-Declined` with reasons | F11 |
| Approval and execution gate | One sentence | Prerequisite check, resolved-OQ line, declaration-style scope fence, honesty rule, path-scoped commit, never-push, conditional lifecycle ownership, cohesion rationale | F7 |

The two `IPD-C802` em dashes are in the scaffold's validation-rule boilerplate (the same text as `agent_workflows/ipd_authoring.py:98`), not in authored prose, so they were left unchanged.

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step S5

- Checked: OQ-01 (`Blocking: no`, `Status: resolved`). Its condition, that only genuine `--by-human` approvals advance the baseline, is preserved. The resolution now records that the trailer/prefix option is not viable and that E-01 inspects blob content (D1). Review decisions D1-D5 are recorded in the plan and below. Deferred rows now carry `Carrier` or `Carrier-Declined` (F11). No blocking or human-owned question remains, and no finding is left OPEN or DEFERRED, so nothing is escalated.

### Pass 2

- Re-read the revised plan end to end. Every replaced mechanism (baseline rule, `--accept-stale`, `prune=False`, `rereview_host`, spec amendments) appears consistently in Goal, E-items, Proposed changes, Spec sync, and V-items. `aw ipd lint --phase author` is clean; info only: `IPD-Z602`, `IPD-Z603` x2 (8 E-items and 10 work Scope-Paths, answered in the cohesion rationale), and `IPD-C802` x2 (boilerplate).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Correctness | agent_workflows/plan_readiness.py:1540 `subject.startswith("plan-review:")`; agent_workflows/status_set.py:2546 `chore({label}): set status {target_status}`; plan E-01 | The baseline rule "latest human-attested approval commit" had no implementable definition. Approval commits do not carry a fixed subject, so extending the subject filter would almost never fire. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 defines a blob-content rule bounded to commits after the last `plan-review:` commit, keeps the batch cost model, and excludes uncommitted approvals; V-01 tests a non-`plan-review:` subject. |
| F2 | HIGH | UNDER-SCOPE | R1 / Spec sync | .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md:46; .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md:660-663 | The plan changes the spec-defined staleness baseline and adds a basis-record deletion condition, yet said no spec needed revision and did not list the specs in Scope-Paths. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | both specs added to Scope-Paths; E-08 amends them with `aw specs note`; the Spec sync section says why. |
| F3 | MEDIUM | IN-SCOPE | R2 / R3 / Guard design | agent_workflows/status_set.py:3888 agent/json mutation requires `--yes`; plan E-02(d) | The bulk guard's non-interactive confirmation was `--yes`, which every agent or json mutation already passes, so the guard confirmed nothing. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-06 adds `--accept-stale`, with a defined trigger, exit 1 refusal rule `status.bulk_stale_approval_unconfirmed`, a TTY prompt, actor recording, parser and `command_surface` declarations; V-06 tests it. |
| F4 | MEDIUM | UNDER-SCOPE | R1 / Host awareness | agent_workflows/check_engine.py:4072; agent_workflows/ipd_lint.py:3022; agent_workflows/status_set.py:1641; agent_workflows/runner_profiles.py:1253 | Only one of three hardcoded `aw oc review` hint sites was in scope, and "repo/user configuration" named no real source (the project config has no default host). | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-07 adds `review_basis.rereview_host` backed by `default_runner` with an `oc` fallback on absent or broken stores, and applies it at all three sites; `ipd_lint.py` added to Scope-Paths. |
| F5 | MEDIUM | IN-SCOPE | R1 / R3 / CLI design | agent_workflows/cli.py:4960 single positional `action_ref`; agent_workflows/review_basis.py:161 `stale_bases(prune=True)`; backlog i8dc07 OQ-02 | `aw show stale-reviews` had no dispatch rule, no flag declaration, an undefined selector set, and would have deleted basis records via the default prune inside a read-only view. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-03 reserves the view name per OQ-02 Option A, mandates `prune=False`, defines output and exit codes, declares `--diff`, and defers selectors to `1iojci`; `command_surface.py` added to Scope-Paths. |
| F6 | MEDIUM | IN-SCOPE | R2 / Followability | plan E-02 (four sub-steps across two files), E-04 (three concerns across three files); `IPD-Z602` on E-02 | Two E-items each bundled independent concerns, so one item could not be executed or validated as one step. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | split into E-02/E-06 and E-04/E-07 via `aw ipd sync --apply` (watermark 08), with the V mapping rebuilt. |
| F7 | LOW | IN-SCOPE | S7 / Execution contract | plan `## Approval and execution gate` (original line 168) | The gate lacked a scope-fence declaration, the honesty rule, never-push, the hand-`git mv` prohibition, and conditional runner/executor lifecycle ownership. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | full execution contract added, with a declaration-style fence (no STOP for scope). |
| F8 | LOW | IN-SCOPE | R2 / Evidence | plan V-01..V-05 (original lines 138-161) | V-items named no units, two V-items each validated two unrelated behaviors, and V-05 used `aw sanitize` rather than `aw sanitize --agent`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | V-01..V-08 each name their units and demand falsifiable pasted output. |
| F9 | LOW | UNDER-SCOPE | R4 / Scope accuracy | plan `## Scope check` (original line 113); CHANGELOG.md:101 | "Under-scope: none" was false, and the CHANGELOG, which already describes the stale-review advisory, was not updated for four new CLI behaviors. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Scope check corrected; `CHANGELOG.md` in Scope-Paths and E-08. |
| F10 | LOW | IN-SCOPE | R7 / R4 / Cross-plan and tests | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:88-89; agent_workflows/attention.py:3967 colored-only legend; conftest.py:384 pops `AW_CONFIG_DIR` | No cross-reference to `t4gl15`, which ports the same function. The legend test and host test would silently fail to exercise their paths without `--color` and an in-test `AW_CONFIG_DIR`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Scope check notes `t4gl15`; E-05 groups 5 and 6 specify `--color` and in-test `AW_CONFIG_DIR`. |
| F11 | LOW | IN-SCOPE | S5 / Carriers | plan `## Deferred / out of scope` rows 1-4; `aw ipd lint --phase review-finalize` `check.ipd-uncarried-obligation` | The deferred rows named no durable carrier, so once the plan executed they would vanish from `aw attention` with no record. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Rows 1 and 2 carry `- Carrier: i8dc07` and `- Carrier: 1iojci`; rows 3 and 4 carry `- Carrier-Declined:` with the reason (work already done outside the plan; a deliberate, user-visible design limit). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | How is a human-attested approval commit recognized? | By the committed blob: `Status: approved` and newest history record `approved` or `same-status` with `--by-human` in the actor | A commit subject prefix or trailer | `_offer_self_commit` and hand commits use no fixed subject; OQ-01 delegates the mechanism to implementation provided only genuine `--by-human` approvals count | yes |
| D2 | Does an uncommitted approval clear self-staleness? | No; it clears once committed | Read the working tree as a baseline | The ipd-spec defines the advisory from git history; one source of truth | yes |
| D3 | What confirms a stale bulk approval non-interactively? | A new `--accept-stale` flag | `--yes`; `--force` | `--yes` is mandatory for all agent/json mutations, and `--force` already carries other meanings | yes |
| D4 | Does `aw show stale-reviews` accept selectors? | No, in this plan | Positional selectors | Selector unification is owned by `1iojci`; narrowing is available through `aw att -t plan --stale-review <selector>` | yes |
| D5 | Where does the hint host come from? | The user-local `default_runner`, falling back to `oc` | `project.json` `enabled_hosts` | `enabled_hosts` lists three hosts and no default | yes |
