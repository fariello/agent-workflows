# Review findings: plan juu1rj

- Subject-Id: juu1rj
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ad22ff70a`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
Baseline: `python3 -m pytest -o addopts="" -n auto tests/test_orchestrator_readiness.py tests/test_status_set.py
tests/test_orchestrator_status_gate.py tests/test_plan_priority_required.py` -> `165 passed in 85.38s`.

Verified: `render_human` hardcodes `Orchestrator {id6} is not ready for review:` (`orchestrator_readiness.py`
`render_human`); `status_set.run_set_command` calls `render_human(r)` with no target or term; the child-lint
finding's `detail` is the joined raw diagnostics (`review_readiness`, `CODE_CHILD_LINT` branch); backward-move
human output names no plan; terminal-reopen human output is one long paragraph; `validate_transition_allowed`
joins approval refusals with `"; "`; `_blocking_question_ids` returns only ids.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C/F; approved spec `uonrjg` | `.aw/records/specs/approved/20260913-uonrjg-...spec.md` 9.1, 9.2, R10.3 ("status setters ... MUST consume the shared resolver. Local `_STATUS_COLOR_256` lifecycle tables MUST be removed"); `term.resolve_lifecycle`, `Term.format_lifecycle_compact`, `Term.style_lifecycle_text` | E-01 prescribed "bold cyan/yellow" for id6s/setids and OQ-01 "ANSI 256 colors", i.e. a hand-picked palette, contradicting an approved spec that governs exactly this surface; the plan's spec-sync said N/A. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Styling split into E-07, which must use the shared resolver (demonstrated at review, output pasted in OQ-01); setid bold only; spec-sync now cites `uonrjg` as the governing contract. |
| PR-002 | HIGH | IN-SCOPE | Rubric D (anti-regression) | `orchestrator_readiness.run_coverage` (`print(render_human(r))`); `runner_shared` continue-handoff builder (`rendered = _orch_readiness.render_human(readiness)` into an agent prompt); `tests/test_orchestrator_status_gate.py` (`assertIn("not ready for review", ...)`) | Plan did not name `render_human`'s other two callers or say what their output becomes; one embeds it in an agent prompt where ANSI would be corruption, and a test pins the current wording for `to-review`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires keyword-only optional params, unchanged header for `None`/`to-review`, byte-identical default output; E-02 forbids touching the other callers; E-05 item 2 and V-01 pin byte-identity; V-02 checks `aw ipd coverage` output unchanged. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric C (architecture), right-sizing | OQ-02 ("A lightweight helper can extract..."); `render_human(result)` receives only `ReviewReadiness`, which has no child paths | Plan left ambiguous whether the renderer reads child files; it cannot without a new data path, and I/O in a renderer would make printing have side effects. E-01 also bundled three concerns (wording, extraction, styling). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Extraction moved to `review_readiness` (new E-06) on a defaulted `Finding.questions` field; E-01 is wording only; OQ-02 rewritten with demonstration. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric D; output contract | `validate_transition_allowed` return string becomes `Diagnostic.detail` (`run_set_command`, `status.invalid_transition`); `specs.run_set` prints `approval_refusals` reasons line by line | E-03 asked for "styled id6 and target status" inside strings that feed agent/JSON output and a second surface; ANSI there corrupts machine output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and the gate's invariant (4) require plain strings from those functions, styling only at the `term` write; E-05/V-02 assert no `\x1b` in agent output. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric D; test-coupled phrases | `tests/test_review_record_classifier.py` ("states a verdict that does not clear this plan", 5 sites); `tests/test_plan_priority_required.py` ("refusing to set approved"); `tests/test_status_set.py` ("Refusing before making changes"; terminal-reopen asserts id6 and `--allow-terminal-reopen`) | Rewording refusals without naming the phrases existing tests match would either break them or invite weakening the tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/E-04 name each phrase to preserve; V-03 requires those two suites pass. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric E/G (evidence strength, P16) | V-02 ("paste `git diff` ... in line 3019"); V-01/V-03/V-04 "test output"; V-06/V-07 `TODO` | V-02 accepted a diff (structural, line-pinned) as proof; others did not specify the run or the observable; new V-06/V-07 were skeletons. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every V-* now demands pasted CLI/session output with exit codes on a temp repo, the agent-mode contract check, and V-05 an after-minus-before failing-node-ID comparison of the bare suite; line numbers replaced by symbol/string anchors. |
| PR-007 | MEDIUM | IN-SCOPE | Release gate (AGENTS.md "Every live bug gates the next release") | Plan `- Work-Kind: bug`, no `- Blocks-Release:`; backlog `hf5cc4` `- Blocks-Release: next` | A live bug plan graduated from a gated item must carry the gate; without it the release blocker set loses this work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `--blocks-release next` through `aw ipd set reviewed ... --blocks-release next`. |
| PR-008 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Plan "Approval and execution gate" (one paragraph) | Gate lacked the paste-actual-output rule, the scope fence as declaration with `--scope-reason`, never-push/staged-set verification, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all four plus an explicit invariants list. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which palette styles id6/status? | Shared lifecycle resolver; setid bold only. | Plan's bold cyan/yellow. REJECTED: violates `uonrjg` R10.3/9.1. | `uonrjg` 9.1, 9.2, R10.3; demo in OQ-01. | yes |
| D-2 | Should `to-review` keep the old header? | Yes, and the default output stays byte-identical. | Change all headers. REJECTED: the old wording is accurate for to-review, a test pins it, and two callers embed it. | `tests/test_orchestrator_status_gate.py`; `run_coverage`; `runner_shared` continue-handoff. | yes |
| D-3 | Where is the question title extracted? | In `review_readiness`, carried on defaulted `Finding.questions`. | In `render_human` (plan's OQ-02 wording). REJECTED: renderer has no paths; I/O in printing. | `render_human` signature; `CODE_CHILD_LINT` branch has `child.path`; demo in OQ-02. | yes |
| D-4 | Does the plan inherit `Blocks-Release: next`? | Yes. | Leave ungated. REJECTED: AGENTS.md live-bug rule and graduation inheritance clause. | backlog `hf5cc4` line 3; plan `- Work-Kind: bug`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
