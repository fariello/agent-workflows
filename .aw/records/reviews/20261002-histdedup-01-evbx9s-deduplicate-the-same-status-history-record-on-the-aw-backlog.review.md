# Review: Deduplicate the same-status history record on the aw backlog set --status path

- Subject-Id: evbx9s
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged (`a07bae46c`), so I skipped the pre-review snapshot. `aw ipd lint --phase author` was clean before my edits and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `bf5c59fa1`. I drove a scratch repo under the gitignored `tmp/` and removed it afterwards. No production file was edited.

- Two `aw backlog set <path> --status open --message "metadata only"` calls left two `same-status (aw backlog): metadata only` records. Two `aw set open <id6> --message "metadata only"` calls left one. F-01 reproduces.
- Two defaulted calls appended two `status -> open` records. `--status parked --message x` followed by an identical repeat appended `same-status (aw backlog): x` above `parked (aw backlog): x`. Cases (c) and (d) reproduce.
- The sidecar `.aw/records/history.jsonl` gained one line per `--status` call.
- `same_status_message_is_duplicate` returns True on a fixture whose only history line is indented four spaces, and `_prior_history_records` returns `[]` on the same fixture (F-03). The predicate also returns True for `same-status`/`x` against a newest `parked ... x` record.
- `_reattach_history` has exactly two callers, `backlog.run_set` and `set_records.close_on_answer`. `specs.run_set` ties `sidecar_msg` to the same predicate branch. `status_set` stamps UTC (`datetime.now(timezone.utc)`), while `_reattach_history` stamps local time (`date.today()`).
- `ulepef` is `approved` and declares `backlog.py`. `vhiqo6` is `to-review`. `wkpcop` is `open`. `jbipfa` is executed.
- `TZ=Etc/GMT-14` gave local `2026-10-03` against UTC `2026-10-02`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (A) | plan E-03 "Guard the existing `if item.id:` block with the same `is_dup`"; E-04 "suppress only when `is_dup and _prior_history_records(text)`" | E-04's fallback writes the inline record when `is_dup` is True and the priors are empty. E-03, however, keys the sidecar on raw `is_dup`, so in that exact F-03 case the sidecar is skipped for a record that was written. That recreates the inline-versus-sidecar disagreement E-03 exists to remove. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now defines ONE `suppress` variable, and both `write_record=` and the sidecar guard read it. The E-03 wording, proposed change 4, the E-04 expected outcome and V-04 are updated to match. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (E) | plan Required tests "once bare and once under `TZ=UTC`"; V-05 "against `git stash`" | Under `TZ=UTC` the local and UTC dates coincide, so the demonstration cannot catch a wrong UTC read. Separately, `git stash` in a shared checkout can swallow a co-worker's edit to `backlog.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The demo now runs under `TZ=Etc/GMT-14` and `TZ=Etc/GMT+12`, which guarantees a local/UTC split at any instant. The base-state run now uses a worktree at a recorded `<base>`. |
| PR-003 | LOW | IN-SCOPE | Execution contract (G) | plan gate "move this plan to `.aw/records/plans/executed/` through the tooled lifecycle" | The gate never said who owns finalize (runner or executor) and had no scope-fence declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize ownership is now conditional: the runner owns it, and a manual executor runs `aw ipd finalize`. Hand `git mv` is forbidden. A non-stop scope fence with `--scope-reason` is added. The `vhiqo6` STOP is kept as a genuinely unsafe condition. |
| PR-004 | LOW | IN-SCOPE | Traceability | plan V-06 "PASTE the id6 of the backlog item filed"; OQ-02 "the executor FILES"; Deferred names `Carrier: wkpcop` | The plan told the executor to file a carrier that authoring had already filed (`wkpcop`, open), which would create a duplicate item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 and OQ-02 now confirm `wkpcop` instead, and the Under-scope wording is aligned. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | In the F-03 fallback, should the sidecar follow `is_dup` or the final suppress decision? | The final `suppress` decision | Raw `is_dup`, as authored (leaves a durable record with no sidecar line) | Plan OQ-01's own rationale: one predicate, one decision for both copies; `specs.run_set` `sidecar_msg` precedent | yes |
| D-2 | Which timezones make the clock demonstration discriminating? | `Etc/GMT-14` and `Etc/GMT+12` | `TZ=UTC` (vacuous); a single non-UTC zone (fails part of the day) | Measured local/UTC dates under `Etc/GMT-14` | yes |
