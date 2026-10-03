# Review: Drop the retracted non-TTY auto-switch clause from 19 cli.py help and docstring sites

- Subject-Id: 79piey
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (`d3b6b4f56`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `e28ab5005`:

- `rg -c "non-TTY piped" agent_workflows/cli.py` = 16, `rg -c "JSONL when piped"` = 3, `rg -c "Agent mode:"` = 16. The shape split is 12 / 2 / 1 / 1 (the `adopt` site sits in a triple-quoted epilog at `cli.py` "Exit codes: 0 adopted/previewed").
- A parser walk with dedup by `id(parser)` covers 175 parsers. It finds 17 surfaces raw and 18 normalized, and `aw agy profile list` is the only difference, so F-03/F-04 reproduce. All 18 surfaces carry both `--agent` and `--json` (F-06).
- `docs/cli-output-contract.md` "## 9. Automatic Non-TTY Migration Policy: RETRACTED" and Section 1.1 "DOES NOT AFFECT THE MODE" are present. `renderers.py` emits `"Agent output: --agent"`.
- The carriers `6bolin`, `8jeh4x`, `bxnhdj` and `wc5c5e` are all `open`.
- `FORCE_COLOR=1` makes `format_help()` emit ANSI escapes (`'\x1b[1;34musage: ...'`). With escapes present the plain-text phrase still matched on `config`, but the color environment can still change the rendered text.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | plan Required tests "MEASURED BASELINE ... 3 failed, 4624 passed"; V-04 "EXACTLY the same three"; carriers 6bolin/8jeh4x/bxnhdj open, wc5c5e load-sensitive | V-04's bar is an exact failed set and pass count measured at authoring. Those are live artifacts with open fix carriers and known load sensitivity, so a correct execution could fail V-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The executor now re-derives `<baseline>` before editing. The bar is "no new failed node vs `<baseline>`", and the authoring numbers are kept as context. |
| PR-002 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | E-01 Expected outcome "still reports 16"; V-01 "must still report `16`" | The `Agent mode:` count is a fixed number on a high-traffic file that concurrent plans may edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records the pre-edit `<modes>`/`<sites>` and requires every site found to be corrected. V-01 compares against `<modes>`. |
| PR-003 | MEDIUM | IN-SCOPE | Testing (E) / anti-regression (D) | E-03 matched only literal wordings, and the plan's own F-02 shows the claim recurred in a third wording | A test that matches only the two literal phrases misses a reworded reintroduction, which is exactly the failure F-02 documents. It also has no positive limb, so deleting the lines would satisfy it. The test also did not strip ANSI, which `tests/test_subparser_descriptions.py` `_normalize` does. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now strips ANSI, normalizes whitespace, and matches the claim shape with a regex. At review that regex hit exactly the 18 surfaces and none of the true `piped`/`redirect` mentions on `aw next`, `aw runs submit` or `aw upgrade-test new`. E-03 also adds a positive `Agent mode:` names `--agent` limb. V-03 adds reworded and deletion negative controls. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract (G) | plan gate "move this plan to `.aw/records/plans/executed/` through the lifecycle tooling" | The gate had no scope-fence declaration and did not say whether the runner or the executor owns finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE declaration (justify with `--scope-reason`/`--scope-ack`, and stop only on an unresolvable concurrent edit). Added a POST-GATE LIFECYCLE MOVE with conditional runner/executor ownership. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy / OQ owner | F-05 `rg -rn` (`-r` is `--replace` in rg); OQ-01 `Owner: none` on a reviewer/author resolution; tests/test_human_renderer_agent_hint.py carries "automatic when piped" | The F-05 command is malformed. OQ-01 had an ownerless resolution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The command is corrected to `rg -n`, and the one negative-assertion test hit is noted. OQ-01 is now `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01's subtractive wording, which adds no positive claim about piping? | Keep it | Positive "piping emits text" wording at all 18 sites | `renderers.py` "Agent output: --agent" precedent; `docs/cli-output-contract.md` Section 9 "does not foreclose a future proposal" | yes |
| D-2 | Should the regression gate match a claim shape or literal phrases? | A claim-shape regex plus a positive limb | Literal phrases only (misses rewording, as F-02 shows) | Review measurement: the regex hits the 18 known surfaces and has 0 false positives across 175 parsers | yes |
| D-3 | Should the suite bar be an exact authoring baseline or a re-derived one? | Re-derived `<baseline>`, with no new failed node allowed | An exact `3 failed` set (live, load-sensitive) | `wc5c5e` open, plus the plan-review rubric G live-artifact convention | yes |
