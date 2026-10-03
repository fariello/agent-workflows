# Review findings: plan e6w056

- Subject-Id: e6w056
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `7bd4f92bb`. The plan was committed and byte-identical to the lane input. `aw ipd lint
--phase author` was clean before review and `--phase review-finalize` clean after.

Re-driven at review:
- (a) `hasattr(hsp,'CAP_DENY_PUSH')` False; push-named fields `[]`.
- (b) `RUN-NO-PUSH` absent; codes naming `Push attempt` `[]`; `'Push attempt' in ABORT_CLASSES` True. Both are tuples, and `RunFindingCode` is a NamedTuple, so V-02's `_replace`-and-rebind falsification is feasible.
- (c) `hook_preserving_commit` in `UNREPRESENTED_SPEC_CAPABILITIES` (a dict, so V-02's delete-and-restore is feasible); no field under either spelling; `RUNNER_SAFETY_CAPABILITIES` = `('supports_commit_gateway','supports_fresh_verifier_session')`.
- (d) `host capabilities opencode --json` `data.unrepresented_spec_capabilities` lists the six keys including `hook_preserving_commit`.
- E-05: `isolated_worktree`, `path_policy` and `timeout_cancel` are all unrepresented keys and none is a field. `gqy7yd` is `open`, `Work-Kind: bug`, `Blocks-Release: next`.
- Spec 5.2 rows 1-5 are verbatim as quoted (row 2 already amended); `grep -rn "Push attempt\|hook_preserving" tests/` returns nothing.
- Set `netnsfilter`: all five plans in `pending/`; `wn956n` is `to-review`.
- The three test files report `54 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `aw backlog --help` subcommands `{new,set,note,check}` | V-05 demanded `aw backlog show gqy7yd`, a verb that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now read from the item file or `aw find backlog gqy7yd` (verified). |
| PR-002 | MEDIUM | IN-SCOPE | G. Scope fence vs mechanism | Scope-Paths `.aw/records/backlog/open`; setters relocate on status change | E-05's corrective branch allowed `aw backlog set`, which moves the file out of the declared directory. Its re-file branch did not say where the new file lands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrections now use `aw backlog note` only. A re-file uses `aw backlog new` with the gate flags and must land under `open/`; anything else is justified with `--scope-reason`. |
| PR-003 | LOW | IN-SCOPE | G. Live count as bar | measured `54 passed` vs plan's `51 passed` | A stale authoring count was offered as the comparison point. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Kept as an orientation pointer only. The bar is now that the tests pass and include E-02's class. |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | plan LIFECYCLE paragraph | Begin/finalize ownership by runner versus hand executor, and the expected `--scope-ack` for the normally untouched backlog directory, were not stated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How may E-05 correct `gqy7yd` without leaving declared scope? | `aw backlog note` only; re-file via `aw backlog new` into `open/` | Widen Scope-Paths to all of `.aw/records/backlog` | `.aw/records/specs/README.md` relocation rule applies to backlog setters too; plan's own fence | yes |
