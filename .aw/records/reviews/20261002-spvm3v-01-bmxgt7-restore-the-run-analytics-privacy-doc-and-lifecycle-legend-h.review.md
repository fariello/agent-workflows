# Review: Restore the run-analytics privacy-doc and lifecycle-legend help-reach coverage

- Subject-Id: bmxgt7
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `4a3807d66`:

- `tests/test_docs.py` and both target files are absent.
- No test references `DETECTOR_BLIND_SPOTS`, `LIFECYCLE LEGEND` or `both_forms`.
- I recovered both classes from `19313eed7^:tests/test_docs.py` into gitignored `tmp/bmxrev/`. They give `8 passed` under `-o addopts=""` and also under the bare xdist addopts.
- The set-equality harvest reproduces both code tuples: covered matches, blind matches, 11 names.
- A recursive subparser walk covered 284 `format_help()` calls with 0 placeholder leaks, in 0.6s.
- `docs/cli-human-guide.md` carries both reference strings. `docs/` holds 28 `.md` files.
- `t9lcdu` is `approved`, `y2ge26` is `to-review`, and backlog `spvm3v` is `graduated`.
- Scratch was removed afterwards, and `git status --short` was clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Testing (E) / determinism | `agent_workflows/cli.py` `format_help` uses `Term(color=False)`; `agent_workflows/term.py` `should_unicode` returns False on `AW_ASCII_ONLY`/`FORCE_ASCII`/an ASCII stdout; `Term.format_lifecycle_legend` `if both_forms and self.unicode` | The recovered legend arm depends on the environment. It gives `1 failed, 7 passed` under `AW_ASCII_ONLY=1` and under `PYTHONIOENCODING=ascii -s`. The `both_forms` arm, as written, compares two default-constructed `Term`s, and in an ASCII environment those render identically. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now pins the environment with monkeypatch: it deletes both variables and sets a UTF-8 `sys.stdout`. I demonstrated this passing under the bare, `AW_ASCII_ONLY=1` and `PYTHONIOENCODING=ascii` environments. E-04 now uses an explicit `unicode=True`. V-03 requires a run under `AW_ASCII_ONLY=1`. Added F-12. |
| PR-002 | MEDIUM | IN-SCOPE | Anti-regression (D) | `docs/run-analytics.md` "it catches TWO at fail severity:" / "does NOT look for the other ELEVEN:" | E-02's anchor sentence contains the count word `TWO`. A correct doc update after a ruleset change would break that anchor and produce a misleading "structure changed" failure. The harvest also had no stopping rule at the end of the bullet block. | Low | FIXED | Anchors are now the count-free `at fail severity:` and `does NOT look for the other`. The harvest takes only the first contiguous bullet block. V-01 and V-02 check this. F-06 is annotated. |
| PR-003 | LOW | IN-SCOPE | Validation (E) | V-01 "hard-codes `13`, `11` or `2`" | A bare literal grep for `2` would match unrelated code, so it cannot be satisfied meaningfully. | Low | FIXED | V-01 now targets `len(...)` of the three tuples compared to a literal, plus the words `TWO`/`ELEVEN`. |
| PR-004 | LOW | IN-SCOPE | Validation (E) / plan hygiene | E-05/V-05 "no previously passing test fails"; OQ-01/OQ-02 `Owner: none` | The suite bar did not require stating the failure set as test ids. The resolved open questions named no owner. | Low | FIXED | The bar is now an empty failure-set delta stated as test ids. Owner is `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the legend arms be made environment-independent? | Pin through monkeypatch: delete `AW_ASCII_ONLY`/`FORCE_ASCII` and set a UTF-8 `sys.stdout`. | Assert ASCII-only content (this loses the glyph and `both_forms` coverage); skip under ASCII (silently a no-op) | Probe passing under 3 environments at review | yes |
| D-2 | Which prose should the harvest anchor on? | Count-free `at fail severity:` and `does NOT look for the other` | Count-bearing full sentences (they break on correct doc updates); HTML markers (needs a `docs/` edit, per OQ-01) | `docs/run-analytics.md` lines read at review | yes |
