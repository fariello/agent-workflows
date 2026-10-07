# Review: Escape Markdown metacharacters in the attention board's detail line

- Subject-Id: qpw45x
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits and `--phase review-finalize` was clean after.

Re-verified in this lane:

- F-1/F-2/F-3 reproduce: the F-1 and F-3 values reach `_render_item_row` (both branches) and `_render_table_row` verbatim, including raw `\x1b[31m` and `\x07`; `A.is_safe_descriptive("red \x1b[31m")` is `False`.
- F-5: `attention --no-color --details` and `--format markdown --details` are byte-identical (308369 bytes each); `attention.py` contains no `markdown` string; `fmt` is read once (`fmt = getattr(args, "format", None)`).
- F-6: `FORCE_COLOR=1 ... --format markdown --details` has 1072 lines containing ESC, byte-identical (428501 bytes) to the forced-color default board.
- F-8: `render_json` uses `ensure_ascii=True`. F-9: `--agent --fields data` emits no item payload. F-10: `_AGENT_ESCAPES` is as quoted.
- No Markdown library importable (`import markdown` raises `ModuleNotFoundError`).
- A6 spot-check: `--format markdown --details` sha256 identical under `TZ=UTC` and `TZ=Asia/Tokyo` with `LANG=C`.
- Carriers `tapqf2` and `3jez8u` exist (graduated). Sibling `ynhst5` is executed.
- Live corpus: 3191 extracted details (authoring measured 2820), 0 with C0/C1 controls.
- Adjacent suites green: `tests/test_attention.py tests/test_attention_contract.py tests/test_backlog.py tests/test_term.py` -> `169 passed in 16.92s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Coverage; Section 8.8 | `agent_workflows/attention.py` `format_plan_detail_line` ("Format the detail line for a plan identically to `aw att -d`"); caller `runner_shared.execute_item_core` `attention.format_plan_detail_line(plan_path, term=term)` | A fourth site emits the same untrusted detail raw (colored and plain) to the run banner. Unfixed, it keeps a raw-control-character emission path and breaks its own "identically" contract once the board escapes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to Scope, E-03 (with a single shared helper), E-05, V-03, F-17; fix stays inside `attention.py`. |
| PR-002 | HIGH | IN-SCOPE | Correctness of mechanism (A/G) | E-04 "forcing `colored` false"; `attention.render_board` `colored = bool(getattr(term, "color", False))` | Forcing only the local flag still passes a color-on Term into `render_board`, which re-derives color and emits ANSI. Measured: `render_board(..., term=T.Term(stream=io.StringIO(), color=True))` contains ESC. E-04 as written would not meet its own expected outcome. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now builds the Term with `color=False` when `fmt == "markdown"` (same as `--no-color`); V-04 demands the diff hunk at Term construction; F-18 added. |
| PR-003 | MEDIUM | IN-SCOPE | Spec sync / honesty | spec A14 "a Markdown-table-breaking string ... each fails as a stable named violation"; plan OQ-02 | OQ-02 decides metacharacters are escaped, never violations, which contradicts A14; E-06 forbade touching A14 and claimed E-05 satisfies it, a false conformance claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 amend only A14's table-breaking clause, other clauses byte-identical; E-05 wording updated; F-19 added. |
| PR-004 | MEDIUM | IN-SCOPE | Project convention | E-06 "appending a dated amendment note in the body style"; spec history records for `8njbv5`/`0ta5vg`/`pr5b0t` written by `aw specs note` | Hand-editing a spec's history contradicts the tooled path the spec's prior amendments used. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 require `aw specs note` with pasted output. |
| PR-005 | MEDIUM | IN-SCOPE | Validation strength; live-artifact criteria | V-04 `\| head -12`; F-11 counts; E-06 "three deliberately-unescaped" vs E-02's five | `head -12` cannot prove zero ESC bytes; authoring corpus counts are live (3191 vs 2820) and were being used as the recorded bar; E-02 leaves five characters unescaped but E-06 recorded only three. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 uses a whole-output `grep -c $'\x1b'` count; E-06 records all five with execution-time counts and command. |
| PR-006 | LOW | IN-SCOPE | Execution contract (G) | gate paragraph; Required tests addopts quote `-m 'not slow'` vs `pyproject.toml` `-m 'not slow and not livecorpus'` | Gate lacked scope-fence wording and conditional finalize ownership; addopts misquoted; suite bar was an `N passed` count. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with execution contract and post-gate lifecycle; suite compared by failing node-id set; quote corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Include `format_plan_detail_line` in this plan? | Yes, inside `attention.py` only | Separate backlog item (leaves a raw-control path and an "identically" contract broken by this plan) | F-17; spec Section 8.8 "The renderers never emit raw control characters" | yes |
| D-2 | Amend A14 or keep it and make metacharacters a violation? | Amend only A14's table-breaking clause | Keep A14 and reverse OQ-02 (fails a clean checkout per F-11); leave contradiction (false conformance claim) | OQ-02 evidence; spec is `implemented` and amendable via declared Scope-Paths per AGENTS.md | yes |
| D-3 | How to make `--format markdown` color-free? | `color=False` at Term construction | Local `colored` flag only (measured to still emit ANSI) | F-18 measurement | yes |

## Round 2

Re-review on 2026-10-07 by opencode/its_direct/pt3-claude-opus-5.5-1m-us (verdict APPROVE WITH REVISIONS APPLIED) in lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `ca03f0c56`. The plan was committed and byte-identical to the sealed lane input (rev-6); commit `8c460a9a1` had reset it to `to-review` and removed `- Readiness:`. `aw ipd lint --phase author` clean before edits.

Re-verified: F-1 and F-3 reproduce through `_render_item_row` (pipes, link, image, raw `\x1b[31m` and `\x07` all verbatim); the four emission sites (`_render_item_row` both branches, `_render_table_row`, `format_plan_detail_line`) still interpolate raw; sole caller of `format_plan_detail_line` is `runner_shared` run banner; `render_board` re-derives `colored` from `term.color`; `--no-color --details` and `--format markdown --details` byte-identical; `FORCE_COLOR=1 ... --format markdown --details` emits 916 lines with ESC; `T.Term(stream=io.StringIO(), color=None).color` is True under `FORCE_COLOR=1`; `import markdown` fails; `tests/test_attention_output_safety.py` absent; Section 8.8 Markdown bullet and A14 text unchanged from what E-06 amends.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-007 | MEDIUM | IN-SCOPE | Evidence staleness / D invariants | `agent_workflows/attention_contract.py:653` `_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")`; executed plan `0obt4k` (commit `551c76a82`); spec Section 8.8 "AMENDED by plan 0obt4k" | E-01 quoted the pre-widening regex and argued bidi controls are out of reach; OQ-05 (deferred) and the bidi Deferred row with carrier `3jez8u` (now `done`) described a gap already closed. An executor following E-01 literally would mis-describe the regex and E-05 would omit the bidi case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 quotes the current regex and expects bidi neutralization; V-01 and E-05 add a `\u202e` case; OQ-05 resolved citing `0obt4k`; Deferred row marked superseded; Under-scope reconciled. |
| PR-008 | LOW | IN-SCOPE | E testing / executability | E-05 "via `monkeypatch.setenv`/`delenv`"; `tests/test_attention.py` uses `unittest` and `mock`, no `monkeypatch` | pytest fixtures cannot be injected into a `unittest.TestCase` method. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now prescribes `mock.patch.dict(os.environ, ...)` with an explicit `NO_COLOR` pop. |
| PR-009 | LOW | IN-SCOPE | G live-artifact count | V-04 "(review measured 1072)" vs 916 at `ca03f0c56` | Live board line count drifts; must be context, not a bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 labels both measurements as context and requires an execution-HEAD before count. |
| PR-010 | LOW | IN-SCOPE | Record integrity | Round 1 PR-005 row, review record line 33, parsed as 10 cells (`REV-P001`) | The malformed row made the whole record unparseable, so `check.review-finding-unescalated` failed `review-finalize` lint and no gate could read severities. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Escaped the one pipe (syntax only; see the repair note below). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-3 | Should the neutralizer still deliberately exclude bidi controls now that the shared regex covers them? | No: reuse the shared regex as-is, so bidi controls are neutralized | Write a narrower C0/C1-only class (recreates the checker/renderer divergence E-01 itself forbids) | `attention_contract._CONTROL_CHAR_RE`; executed plan `0obt4k`; spec Section 8.8 amendment | yes |

Record repair (syntax only, no wording change): Round 1's PR-005 row contained an unescaped `|` inside a code span (`V-04 \| head -12`), which split it into 10 cells and made the whole record unparseable (`REV-P001` at line 33), which in turn made `check.review-finding-unescalated` fail `aw ipd lint --phase review-finalize`. Round 2 escaped that single pipe; no Round 1 finding text, severity or decision was changed.
