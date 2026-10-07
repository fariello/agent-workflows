# Review findings: plan vhiqo6

- Subject-Id: vhiqo6
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `072b6f640`. Plan committed and byte-identical to the
sealed lane input (`diff`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`;
`--phase review-finalize --agent` after revision: `clean`. Not an orchestrator.

Measurements (scratch git repos in the system temp dir, lane package pinned with `PYTHONPATH` and
`AW_NO_REEXEC=1`, `--no-commit`):

- `backlog set aaa111 --status done --message m` -> rc 0; porcelain `D .../open/<item> | ?? .../done/ |
  ?? .aw/records/history.jsonl`; history `- 2026-10-07 done (aw backlog): m`.
- `backlog set done aaa111 --message m --yes` -> rc 0; porcelain `D .../open/<item> | ?? .../done/`
  (no sidecar); history `- 2026-10-07 done (aw set): m`.
- `--message 'a\nb'`: `--status` rc 2 `aw backlog set: --message must not contain embedded newlines`;
  positional rc 2 `FAIL aw set: --message ...`; neither wrote.
- `--status ... --agent` without `--yes` -> rc 0, written.
- Two items sharing setid `sharedset`: `--status` spelling rc 0 moves only `aaa111`; positional rc 0
  moves both.
- `status_set.run_set_command(["done","aaa111"], scoped_type="backlog", args=Namespace(work_kind="bogus"))`
  -> rc 0, writes `- Work-Kind: bogus`; same for `priority="bogus"`.
- Code: `status_set.run_set_command` refuses unsafe `--message`/`--gate-ref`/... for all types ("IPD
  4gwgo3 E-02, E-03"); `backlog.run_set` uses `core.utc_history_date()` and `label=`;
  `runner_shared.close_backlog_item` argv includes `--lane-carrier-ref`/`--lane-carrier-path`, which
  `status_set` never reads.
- Records: `19lmbe`, `r74211`, `t1gbwg`, `mbjuv5`, `68sur3` `done`; `fnb8pl`, `lq2w86` `graduated`;
  `2wae2x` `open` (Blocks-Release next); `jbipfa` executed; `m94eht` `reviewed`, pending.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (unreachable evidence) / honest docs | Porcelain probe above; `status_set._offer_self_commit` `git reset --quiet HEAD -- <paths>` | E-04 (1), V-04 and the CHANGELOG text claimed a single `R` rename on both spellings. Under `--no-commit` both spellings already show delete plus untracked, so the evidence could not be produced and the CHANGELOG would have been false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote E-04 (1), E-05, E-06, V-04 and F-02 to the observable agreement; added F-09; E-06 files a backlog item for the AC-5 gap; Deferred entry added. |
| PR-002 | HIGH | UNDER-SCOPE | D (unexplained behavior change) | Actor `(aw backlog)` vs `(aw set)`, 52 pinned assertions in 12 modules; prefix pinned in `tests/test_status_set_descriptive_safety.py`; `--agent` rc 0 vs 2 | Delegation would silently change the actor, a pinned refusal prefix, and the confirmation behavior, none named. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Added spike E-07 + V-07 (actor preserved via `actor="aw backlog"`, refusal table, confirmation gate, sidecar); E-04 and E-06 consume it. |
| PR-003 | HIGH | UNDER-SCOPE | C / F-04 runner dependency | `runner_shared.close_backlog_item` argv `--lane-carrier-ref`/`--lane-carrier-path`; `backlog.run_set` paired-flag check; `status_set` reads neither | E-03 carried `--gate-dir` only; delegation would drop the lane-carrier override the runner's isolated-turn close uses. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now carries the lane-carrier pair with its paired-flag refusal; V-03 and E-05 drive it. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence (stale premises) | `status_set` 4gwgo3 loop; `backlog.run_set` `utc_history_date()`/`label=`/`same_status_message_is_duplicate`; setid probe | E-01 said the engine validates neither unsafe field (false); E-04 (2) said clock, label and dedup flip (all already agree); E-04 (3) and F-05 said the engine refuses ambiguity (a setid acts on all matches). | Overall:Low | FIXED | E-01 is confirm-only; E-04 (2)/(3), F-05, F-07, F-08, Scope and V-items rewritten to measured behavior. |
| PR-005 | MEDIUM | IN-SCOPE | Release-gate rules | Carrier statuses above | E-06 planned closes on carriers that are already `done` or `graduated` to other plans, and treated `2wae2x` as partial when `5ivkdh` fixed its stated scope. | Overall:Low | FIXED | E-06 closes nothing; records statuses unchanged; gives a `2wae2x` verdict naming `5ivkdh` for the maintainer; OQ-02 resolved as moot. |
| PR-006 | LOW | IN-SCOPE | G (OQ answerable; contract) | `runner_shared.close_backlog_item` argv single id6; gate lacked scope fence and conditional finalize | OQ-01 answerable from code; gate missing elements. | Overall:Low | FIXED | OQ-01 resolved; scope-fence and runner/executor finalize ownership added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Preserve `(aw backlog)` or adopt `(aw set)`? | Preserve via `actor`. | Adopt `(aw set)`. REJECTED: rewrites 52 pinned assertions; `jbipfa` declined actor unification. | `wy9aru` 4.6; sibling `m94eht` D-1. | yes |
| D-2 | Close `2wae2x` from this plan? | No; record verdict, leave to maintainer. | Close via SATISFIED citing `5ivkdh`. REJECTED: not this plan's work. | `2wae2x` body scope; commit `3c55295a3`. | yes |
| D-3 | Fix the `_offer_self_commit` reset here? | No; file a backlog item. | Fix in this plan. REJECTED: changes the self-commit contract for every type; `wy9aru` S5. | F-09 probe. | yes |
| D-4 | OQ-01 first-match reliance? | None in-tree; resolved. | Leave for executor. REJECTED: the code answers it. | `runner_shared.close_backlog_item` argv. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
