# Review findings: plan 5apgyn

- Subject-Id: 5apgyn
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`af008a70e`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD:
- `render_stream.render_run_summary_table` ladder: `outcome_str = "BLOCKED"` around line 4244 via `RUN_OUTCOME_CLASS_BY_STATUS` (`blocked`, `dependency-blocked`, `fail-gate`, `fail-begin`, `fail-depend`, `not-run` all `OUTCOME_CLASS_BLOCKED`, lines 3193-3198); `outcome_color` at 4346-4363 with `else c_cyan`; `b_line1` at 4504.
- Probe (pin-free env, `TERM=xterm-256color`): every one of the six blocked-class statuses renders `BLOCKED` with SGR `36`; `failed` -> `31`, `interrupted` -> `33`, `queued` -> `36`; `integration-blocked` renders `FAILED` (not in the BLOCKED producer set, consistent with the plan's six).
- `color = pal.enabled` is at line ~3986, not `bool(pal and getattr(...))` at line 4135 as the plan said.
- NO `c_amber` exists in `render_stream.py`; the only `38;5;208` literals are bold (`\033[1;38;5;208m`) at lines 1422/1428/1446/1891.
- `lifecycle_style.style_for("blocked")` = `color=208, bold=True`.
- `Palette(True).lifecycle(Resolved(blocked), "BLOCKED", bold=False)`: pin 256 `\x1b[38;5;208mBLOCKED\x1b[0m`; pin 16 `\x1b[35mBLOCKED\x1b[0m`; pin none `BLOCKED`.
- Spec `uonrjg` R10.3: lifecycle item or statusline rendering in `render_stream.py` MUST use the shared resolver.
- `tests/test_zero_dispatch_outcome.py` `_extract_sgr_code` regex is `\033\[([0-9;]+)m<word>` (no trailing reset required; the plan quoted a different regex, harmless).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture / domain invariant | spec `uonrjg` R10.3; backlog `y11p5u` maintainer ruling 2026-10-12 "color_depth=none must turn off ALL color"; plan `32fso3` (removes raw literals from this same function) | E-01 adds a raw `"\033[38;5;208m"` literal for a word the plan itself classifies as lifecycle stage `blocked`. That bypasses the shared resolver the spec requires, and it ignores the `color_depth` pin (at pin `none` it still emits 256-color codes), recreating the defect the sibling plan `32fso3` removes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now renders `BLOCKED` with `pal.lifecycle(Resolved(blocked), outcome_str, bold=False)`. The output is identical at depth 256 and correct at 16 and none (demonstrated). Proposed changes were rewritten and OQ-03 added. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence | `render_stream.py` contains no `c_amber`; `grep 38;5;208` finds only bold literals | F-02 and OQ-01 justified the unbolded literal by citing `format_statusline`'s `c_amber = "\033[38;5;208m"` at line 2536, which does not exist. The `color =` citation (line 4135 and its expression) was also wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 and OQ-01 were corrected with an explicit note at review. Unbolded now rests on the sibling banner colors and the `bold=False` resolver call. The `color = pal.enabled` citation was corrected. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Test isolation | `Palette.lifecycle_term` uses `term.resolve_color_depth(override=True)` (pin, then `COLORTERM`/`TERM`) | Once the resolver is used, a `"38;5;208"` assertion depends on the developer's shell `TERM` and config pin, so it could become `"35"`. E-02 also did not cover depths 16 and none. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now pins the depth inside a temporary `XDG_CONFIG_HOME` with the environment saved and restored (`_DepthTestBase` pattern) and uses a fresh `Palette` per depth. It also asserts the results at 16 and none. Required tests add a `TERM=vt100` run. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate named verbs that do not exist (`aw ipd approve`, `aw ipd move`), would have the executor move the plan itself, and had no scope fence or honesty rule. OQ owners were set to an agent name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wrote a full execution contract using `aw ipd set approved --by-human` and conditional runner or executor `aw ipd finalize`. Owners set to `plan author`. V-02 now requires pre-existing failures to be proven on the base commit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Raw `38;5;208` literal or shared lifecycle resolver for `BLOCKED` (OQ-03)? | Resolver, `pal.lifecycle(..., bold=False)` | Raw literal (plan as authored; depth-blind, violates R10.3) | spec `uonrjg` R10.3; `y11p5u` ruling; review probe at pins 256/16/none | yes |
| D-2 | Bold or unbolded (OQ-01)? | Unbolded (`bold=False`), matching sibling banner words | Stage default `bold=True` | `render_stream.py` banner `c_*` constants at 4333-4336 | yes |
| D-3 | Keep Work-Kind `followup` (not `bug`, which would require `Blocks-Release`)? | Keep, inherited from backlog `pyezbc` | Reclassify `bug` | backlog `pyezbc` `Work-Kind: followup`; reclassification is the item owner's call | yes |
