# Review: Unify every artifact history date onto the UTC clock (spec 2vev8j 4.4), filenames local per D55

- Subject-Id: 5ivkdh
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean beforehand. `--phase review-finalize` was clean afterwards.

### Defect reproduction (lane HEAD `4cfca3ecf`, in-process `cli.main`, tmp repo under `/tmp/opencode`)

I ran this at 2026-10-02 19:52 UTC under `TZ=Pacific/Kiritimati`, where local was `2026-10-03` and UTC was `2026-10-02`:

- `backlog set <path> --status open --message m` -> `- 2026-10-03 same-status (aw backlog): m`
- `backlog set open aa0002 --message m --yes` -> `- 2026-10-02 same-status (aw set): m`
- `specs new ... --apply` -> filename `20261003-...`, `- Date: 2026-10-03`, `- 2026-10-03 created (aw specs): s`

At that same instant `TZ=Pacific/Honolulu` was NOT skewed (local was `2026-10-02`, equal to UTC). That is the basis for PR-001.

### Claims checked

- Spec `2vev8j` 4.4 text: verified.
- The spec is `approved`: verified.
- `DECISIONS.md` D55: verified, including its scope.
- Every cited writer site: verified, namely `backlog._render_item` (x2), `backlog._reattach_history`, `backlog.run_note`, `backlog.run_new`, `specs._today` (4 callers), `specs.run_new` (one value, two roles), `releases.render_new_release`, `readiness_recheck.run_recheck_readiness`, and `status_set.apply_status_change` (UTC).
- `readiness_recheck` has no `artifact_core` import: verified.
- Both test masks: verified.
- `tests/test_specs_date_containment.py::test_non_regression_omitted_date_defaults_today` globs the LOCAL date: verified.
- `set_records.close_on_answer` delegates to `_reattach_history`: verified.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Validation feasibility (E, G) | plan V-02 "under `TZ=Pacific/Honolulu`", F-01 reproduction line; review probe at 19:52 UTC: Honolulu local == UTC | Every single-timezone demonstration was pinned to Honolulu. Honolulu is skewed only while the UTC hour is before 10:00, so outside that window V-02 and the manual reproduction would not demonstrate the bug, and they would pass trivially. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SKEW-WINDOW RULE: print both zones, then use whichever zone is skewed. V-02/V-03/V-04 and the manual reproduction now cite it. |
| PR-002 | HIGH | UNDER-SCOPE | Correctness of the audit (A, G) | `agent_workflows/ipd_authoring.py:40` `_SECTION_BODY[S.H_WORKFLOW_HISTORY] = "- {date} draft ({author}): created."`; `ipd_authoring.run_scaffold` `when = date.today()...` feeds it | E-05 classified `ipd_authoring` as "`- Date:` and filename (D55, leave)". The same `when` also stamps the `draft` HISTORY record, so a history writer was misclassified. That makes the "every writer" goal false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reclassified as HISTORY. Conversion is attributed to pending `9wcei0`/`rfyrvp`, which declare that path. The Goal and the E-05/V-05 bars now say "converted here or attributed to its owner". A Deferred entry was added. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence accuracy / design (C) | E-05 and Deferred "sidecar ... unobservable"; pending `dmrbqa` measured `aw record-history` rendering the stamped date; `dmrbqa` Item-Dependencies `executed:5ivkdh` | The plan declared the sidecar unobservable. A sibling plan measured it as user-visible and depends on this plan's helper. The conditional compact variant also left `dmrbqa` with no guaranteed helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reclassified as HISTORY and owned by `dmrbqa`. The compact variant was dropped in favor of deriving it with `.replace("-", "")`, following the `specs.run_new` precedent. V-01 must name the helper symbol. |
| PR-004 | MEDIUM | IN-SCOPE | Anti-regression (D) | `agent_workflows/attention.py` `_age_marker` `(date.today() - date(y, m, d))` on `last_history_at`; pending `840y6i` | The deferral reasoned "stored dates stay local". However, `_age_marker` reads HISTORY dates, which this plan moves to UTC, so this plan introduces a mixed-clock comparison there. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The deferral now states the residual skew (at most 1 day on a 30-day threshold) and names `840y6i` as owner (carrier `doe2fo`). The archive readers correctly stay local. |
| PR-005 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | E-01 expected outcome and V-01 "equal to the `4405 passed, 2 skipped` baseline" | The bar was a test count from authoring time, while the suite drifts. Sibling lanes measured pre-existing failures on 2026-10-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The executor now records the baseline at its own HEAD and compares failure sets by name. 4405 is kept as context. |
| PR-006 | MEDIUM | UNDER-SCOPE | Test hygiene (E) | `tests/test_history_label_parity.py` module docstring and `_normalize_history_record` point 2; `tests/test_backlog.py` comment "2. Date: ..."; pending `ayhveg` E-04 prescribes the same unmasking; review probe: `specs new --apply --dir <tmp>` with no `.aw/records/specs/` wrote under `~/.aw/projects/` | Removing the masks without updating the comments that describe them leaves those comments false. The `ayhveg` overlap was not noted. The TZ guidance lacked a restore and a subprocess option. A fixture without the records dir writes outside the tmp tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now requires the comment and docstring updates, notes that `ayhveg` E-04 will be overtaken, prefers a subprocess or a restoring context manager, and requires the fixture records dir. |
| PR-007 | LOW | UNDER-SCOPE | Execution contract (G) | plan `## Approval and execution gate` "move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition"; `7qvs1c` already `graduated` | The gate was missing scope-fence semantics and paste-actual-output, and it did not state conditional finalize ownership. It also claimed the runner would graduate `7qvs1c`, which is already graduated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the scope fence with `--scope-reason`/`--scope-ack`, paste-output, and runner-versus-manual finalize ownership, plus a "never `git mv`" rule. Corrected the `7qvs1c` state in two places. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan absorb the `ipd_authoring` draft record and the sidecar to make "every writer" literally true? | No. Attribute them to the owning sibling plans and reword the goal | Widen Scope-Paths to `ipd_authoring.py`/`record_history.py` (collides with `9wcei0`/`rfyrvp`/`dmrbqa`, which already own those splits and their tests) | sibling plan front matter (`Scope-Paths`, `Item-Dependencies: executed:5ivkdh` on `dmrbqa`) | yes |
| D-2 | Should the plan add a compact UTC helper variant? | No; derive it with `.replace("-", "")` | A conditional second function (leaves dependents unsure; two implementations of one clock, P8) | `specs.run_new` `date_compact = date_iso.replace("-", "")` | yes |
| D-3 | Which timezone should single-zone demonstrations use? | Whichever of Kiritimati/Honolulu is skewed at run time, shown by printing both | Fixed Honolulu (not skewed after 10:00 UTC) | review probe at 19:52 UTC | yes |
