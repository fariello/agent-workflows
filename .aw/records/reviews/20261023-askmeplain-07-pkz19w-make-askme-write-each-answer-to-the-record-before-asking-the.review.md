# Review findings: plan pkz19w

- Subject-Id: pkz19w
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was committed and byte-identical to the sealed lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0 findings; after
revisions `--phase review-finalize`: clean apart from the info advisory `IPD-Z602`. Not an orchestrator.

Verified at review:
- `askme.md` sections `## Ask and wait`, `## Record project decisions` (bullet "Record the answer
  before asking the next question."), `## Finish` ("After the answers are recorded, report the
  decisions") exist as the plan describes.
- Findings `auwidn`: Claude Code T05/T12 quote "All three open questions on plan `m4rcyy` are now
  answered. Recording the decisions in the plan now."; Claude Code T06 note "each answer WAS recorded
  before the next question"; OpenCode + gem T12 "question, edit, question, edit, question, edit";
  Antigravity T12 "an `edit_file` writing each resolution before the next `ask_question`".
- Probe: `engine.install_into_repo` into a temp repo installed `.aw/system/workflows/askme/` =
  `README.md`, `askme.md`, `rationale.md`; installed `askme.md` byte-identical to source.
  `rationale.md` contains no id6.
- `python3 -m pytest -o addopts="" -q --durations=3 tests/test_askme_command_delivery.py`:
  `3 passed in 3.28s`; the installer test took 3.08s, is `@pytest.mark.slow` and listed in
  `tests/slow_allowlist.txt`; slow report threshold 2.0s (`conftest.py`).
- Sibling plans `lf4j52` and `l5f2hg` (same Set) also edit `askme.md`, `rationale.md`, the test file
  and CHANGELOG; `l5f2hg` adds a sentence to `## Ask and wait`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing | plan E-02 "the INSTALLED `askme.md` contains the E-01 ordering paragraph's operative phrase"; V-02 "failing against the pre-change body" | The test's asserted phrase was undefined, so E-01 and E-02 could drift apart, and nothing ordered the test before the edit, so the "fails before" evidence V-02 demands had no step producing it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 fixes the exact sentence; E-02 writes the test first and keeps its FAILED output; V-02 demands it fail on its assertion. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Testing | tests/test_askme_command_delivery.py `test_installer_delivers_and_preserves_askme_shims` (`@pytest.mark.slow`, 3.08s); `tests/slow_allowlist.txt`; conftest.py slow report | A new full-install test takes about 3s, so unmarked it would trip the slow-test report; marked slow it would be deselected by the default `-m 'not slow'`, and E-03's "new test by path" would silently not run it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 marks it slow and adds an allowlist line (`tests/slow_allowlist.txt` added to Scope-Paths); E-03/V-03 run with `-o addopts=""` and check the slow report. |
| PR-003 | MEDIUM | IN-SCOPE | Domain invariant | `.aw/system/workflows/askme/rationale.md` (no id6 anywhere); F-5 probe shows it is installed into target repos | E-01 told the executor to cite `lkn1zt` `auwidn` in `rationale.md`, a file shipped to other repositories where those ids resolve to nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 forbids the ids there and requires the existing dated-incident style; V-01 greps added lines for them. |
| PR-004 | MEDIUM | IN-SCOPE | C. Coordination | plans `l5f2hg` E-02 (sentence in `## Ask and wait`), `lf4j52` (same files) | Three plans of this Set edit the same section and files; "add a short paragraph" with no anchor invites a placement that conflicts or reads wrongly after the siblings land. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 anchors the paragraph after the "If the user both makes an unambiguous choice" paragraph. Merge order is the runner's concern. |
| PR-005 | LOW | IN-SCOPE | G. Executability | plan gate | The gate lacked the honesty rule, a scope-fence declaration, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the full execution contract. |
| PR-006 | LOW | IN-SCOPE | Evidence | plan F-3 "OpenCode + gem T12, Antigravity T12 tool sequences" vs Concern "OpenCode + gem T04, Antigravity T04" | Findings and Concern cited the per-answer evidence under different trial ids, and F-3 did not quote it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 now quotes each T12 row (which records the T04-derived evidence); F-5 and F-6 added for the review probes. |
| PR-007 | LOW | UNDER-SCOPE | D. Invariants | plan "Required tests / validation" | No invariant was named, and the limit of a text-presence test (it cannot show hosts change behavior) was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section names the invariant, its test, and points to the deferred live re-run; spec-sync explains why no spec applies. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which exact sentence should the test pin? | "Write each definite answer to its record before you compose or ask the next question." | Leave phrase to the executor; assert on the existing bullet (already present, so no fail-first) | plan E-02 requires fail-before/pass-after; existing bullet in `## Record project decisions` | yes |
| D-2 | Cite the trial ids in `rationale.md`? | No; dated-incident prose only | Cite ids (original plan) | rationale.md has no id6; installed into targets (review probe); sibling `l5f2hg` E-02 made the same call | yes |
| D-3 | Mark the new test slow? | Yes, plus allowlist line | Unmarked (slow report warning); mark core (adds ~3s to the 30s core budget) | sibling test marked slow and allowlisted; conftest slow report | yes |
