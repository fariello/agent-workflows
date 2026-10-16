# Review findings: plan qk0ew6

- Subject-Id: qk0ew6
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `817e7ba85`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` was clean before edits.

### Evidence verified

- `ipd_lifecycle.checkout_control_root`, `is_main_checkout` (`checkout_control_root(root_path).parent`), `_runtime_dir`, `receipt_dir`, `_run_record_committed_paths` (`checkout_control_root(repo_root) / "records" / "runs"`) resolve as cited.
- `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"`, `allocate_worktree` (`repo_root / WORKTREES_SUBDIR / name`), `_owner_record_path` (function-local import, total fallback) resolve as cited.
- `lanes_cli` `wt_base = repo / ".aw" / "worktrees"` and the `repo / ".aw" / "worktrees" / lane_id` fallback, `oc_runipd._apply_execution_profile` sibling scan, `work_cmd._WORK_STATE_SUBDIR`, `checkup.CHECKUP_STATE_REL`, `runner_shared.SUITE_BASELINE_SUBDIR`, `runner_shared.lane_worktree_display` (`parent == "worktrees"` reconstruction), `render_stream._relativize_path`, `attention._resolve_runs_repo_root` all resolve.
- `fnnwj3` (dependency) is pending and reviewed; it defines `home_configured_root` and the lane identity anchor this plan relies on.

### Probes (temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME`, `AW_NO_REEXEC=1`)

- Both `completely-clean-target` and `local-only` installs store `delivery_mode: clean-delta`, `records_backend: home`; `local.json` has no `state_root`.
- With no git identity the installer STAGED 356 paths and committed nothing; deleting `.aw/` left 357 status entries; `git reset` + `git clean -fdxq` left 0.
- Linked worktree with `.aw/.gitignore` = `*` plus scratch: `git status --porcelain` empty; `git status --porcelain --untracked-files=all --ignored=traditional` lists `!! .aw/.gitignore`, `!! .aw/lane-scratch/y`, `!! .aw/state/x`; the main tree stays empty.
- In-repo lane at `<repo>/.aw/worktrees/abc` with no ignore rule: target shows `?? .aw/` while live; empty after `git worktree remove`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness | `project_context.py:1239` `merged_local_binding.get("state_root")`; `:1255` `RecordsBackend.COMPANION`; E-02 expected outcome | The E-02 equalities `control/"state" == logical_roots["state"]` and run-record root `== state_root` hold only when the records backend is `home` and no `state_root` is bound. Stated unconditionally, they are false for a clean-delta companion repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 expected outcome now conditions the equalities on the stored binding the presets write (measured, F-09); the companion/`state_root` case is recorded in Deferred as pre-existing and fail-closed. |
| PR-002 | MEDIUM | IN-SCOPE | E. Reachability | `runner_profiles.py:1520` "[no CLI flag exists]"; `oc_runipd._apply_execution_profile` reads `options["execution_profile"]` | E-07 expected outcome demanded `--execution-profile hardened` exit with a refusal. No such flag exists, so the demand was unreachable; and on a host without Landlock the call raises `HardModeUnavailableError` before any clean-delta check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07(3) and V-07 now drive `_apply_execution_profile` in-process with a frozen `state["host_capabilities"]` descriptor (read by `runner_shared.ensure_frozen_host_capabilities`), refuse before creating lane scratch, and name the real request path. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness | `lane_containment.LANE_INVENTORY_STATUS_ARGS` (`--ignored=traditional`); `LaneInventory.unknown` excludes `unknown_ignored` (amended R5.5); probe above | E-05 adds a new file to every clean-delta lane but did not consider the retention inventory or `inspect_lane` classification, which could have made lanes unretirable or `HOLDS_WORK`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Verified by probe it is reported ignored and does not block; E-05 now states this and E-08(d)/V-05 assert `inspect_lane` `LANE_EMPTY` and the `inventory_lane` result. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | `worktree_lease.allocate_worktree` `DISPOSITION_ADOPTED` early return | E-05 wrote the ignore file only after `git worktree add`, so an adopted pre-existing empty clean-delta lane would lack it and its scratch would be snapshot-committed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now writes it at both return sites through one total helper; E-08(d)/V-05 cover the adopted case. |
| PR-005 | LOW | IN-SCOPE | C. Architecture | E-04 "when the checkout is clean-delta", E-06 "for a clean-delta checkout", E-07(2)/(3) | The mode test was left implicit in four places, inviting four re-derivations (and four git spawns). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds `ipd_lifecycle.clean_delta_control_root` (total, memoized with the control root) and E-04/E-05/E-06/E-07 use it. |
| PR-006 | LOW | UNDER-SCOPE | B. Privacy / leak | `checkup.run_checkup_cli` `rel_record.relative_to(runs_repo_root(repo_root))` with `except Exception: pass` | After E-06, the clean-delta checkup record lies outside the repo, so `Saved record:` prints an absolute `AW_HOME` path, which `aw sanitize` flags. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 relativizes it to `<project home>/...`; E-08(e) and V-06 assert it in-process with `perform_checkup` stubbed (the real one calls `gh`). |
| PR-007 | MEDIUM | IN-SCOPE | E. Test fixture validity | probe above (357 entries after deleting `.aw/` only); `fnnwj3` review PR-002 (committed variant) | "remove in-target residue ... commit nothing" was ambiguous; the installer stages (or, with an identity, commits) 356 paths, so the acceptance bar (h) would fail or pass for the wrong reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 and E-01 now use `git reset --hard <pre-install sha>` + `git clean -fdxq` (correct for both variants) and assert an empty baseline before the cases run. |
| PR-008 | LOW | IN-SCOPE | Evidence | `ipd_lifecycle.maybe_emit_lane_nudge` | E-03 and F-04 cited `maybe_print_lane_nudge`, which does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed to `maybe_emit_lane_nudge`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan route `_run_record_committed_paths` through `state_root` to cover companion clean-delta repos? | No; document it as pre-existing and fail-closed, carried by `kvwwt0` | Route it now (changes finalize attribution for every mode, out of this plan's concern) | `_run_record_committed_paths` returns `anchored=False` on a missing corpus; tracked companion repos diverge identically today; both clean presets store `home` (probe) | yes |
| D-2 | How should the hardened refusal be demonstrated without a CLI flag or Landlock? | In-process call with a frozen capabilities descriptor | Subprocess `aw oc run` with a runner profile (needs a live host and Landlock) | `runner_shared.ensure_frozen_host_capabilities` reads `state["host_capabilities"]["descriptor"]` first | yes |
| D-3 | Where does the clean-delta mode test live? | One `ipd_lifecycle.clean_delta_control_root` | Re-derive in each module | `dh0uno` one-accessor convention cited in the plan's Step 0 | yes |
