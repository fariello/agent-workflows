# Review: Correct the three shipped HANDOFF prose sites to state the ALL-carrier rule

- Subject-Id: jf3j4q
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (its sha256 matched the sealed lane input), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `c31cb89b1`:

- `check_engine.evaluate_blocking_close` HANDOFF returns only under `if same_gate_carriers and all(_carrier_eval(_c) for _c in same_gate_carriers)`.
- The plan's grep returns exactly `cli.py:627`, `engine.py:5598` and `engine.py:5614`.
- The hook docstring still reads `(it does not today; ...)`.
- `backlog-blocking-close-gate --help` renders the singular parenthetical and exits 0.
- The two engine strings carry identical comment regions.
- `2o5wka` is in `executed/`.
- PyYAML 6.0.3 is available.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Project rule (AGENTS.md "TEST OUTCOMES" rule 3, P16) | AGENTS.md: "NEVER assert that specific text, docstrings, or comment banners remain unchanged"; `cli._DESCRIPTIONS["backlog-blocking-close-gate"]` is what `--help` renders | E-03 case (4) asserts on the hook module's `__doc__`. That docstring reaches no operator surface, so the assertion is the explicitly forbidden docstring pin and not an output test. OQ-01 itself invited a reviewer to overrule this and named the fallback. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (4) dropped. The E-05 correction is now verified by V-05 observational evidence. OQ-01 was rewritten as overruled, with the author's original reasoning kept. Case counts were swept to three everywhere. |
| PR-002 | MEDIUM | IN-SCOPE | Test robustness (E) | measured `cli.main(['backlog-blocking-close-gate','--help'])` at default width renders `DE-\nGATED` | Argparse wraps the description and breaks on hyphens. A co-location assertion on `EVERY` plus `From-Backlog`, or an absence check on the singular wording, can therefore split across lines, fail spuriously, or pass vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 case (3) now sets a large `COLUMNS` and normalizes whitespace and hyphen-newline before asserting. V-06 quotes this. |
| PR-003 | LOW | UNDER-SCOPE | Execution contract (Step 4) | plan `## Approval and execution gate` | The gate had no declarative scope fence with the `--scope-reason`/`--scope-ack` route. It also ordered `aw ipd finalize` unconditionally, with no runner-ownership condition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both. The E-01/E-02 premise stops are kept, since they are not scope questions. |
| PR-004 | MEDIUM | IN-SCOPE | Validation honesty (E) | plan E-07 "Re-capture the baseline ... first", placed after E-04..E-06 | The suite baseline was to be captured in E-07, after the prose edits, so it was not a baseline at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The baseline capture moved into E-01, before any edit. E-07, V-07 and Required tests now compare against it. F-07 is kept as context. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the hook module `__doc__` be pinned by a test? | No. Drop the case and verify it by V-05 evidence | Keep case (4) (forbidden by AGENTS.md rule 3) | AGENTS.md TEST OUTCOMES (3); OQ-01's named fallback | yes |
| D-2 | Should `cli.py` site (iii) stay in scope? | Keep it in scope | Split it to its own plan | Same defect, found by the same grep, on a `--help` surface (F-05) | yes |
