# Review findings: plan ka0g86

- Subject-Id: ka0g86
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `3a03589f8` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`), depends on `executed:xzlu9b` and `executed:jbnkkh` (both reviewed, not yet executed; the runner enforces the
edges). Plan committed and byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author
--agent` clean before semantic review; `aw ipd lint --phase review-finalize --agent` clean after revisions;
`check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (temp dirs, `AW_NO_REEXEC=1`, temp `HOME`):
- Fresh `aw install <dir> --preset private-target -y --no-interactive` into a package.json-only repo: `AGENTS.md`
  125 lines; grep hits at lines 29 (`records/specs/`), 42 (`oc_runipd.py`), 78 (`RELEASING.md`/`CONTRIBUTING.md`),
  80 (`python3 -m pytest`), 82, 90 (`GUIDING_PRINCIPLES`), 93 (`ipd-spec`). D07 present at review HEAD.
- Token rule now written into E-04, applied to the managed block: dangles `.aw/inbox/`, `CONTRIBUTING.md`,
  `RELEASING.md`, `TODO.md`, `oc_runipd.py`, `pyproject.toml`, `runner_shared.py`; applied to `.aw/records/**/README.md`:
  comms `.agents/docs/specs/`, plans `CONTRIBUTING.md`, research the uninstalled spec path plus `INDEX.json`/`INDEX.md`.
- `--keep-legacy` install with a committed `.agents/workflows/index.md`: block additionally dangles `.aw/inbox/` and
  `.aw/records/plans/pending/` (F-08).
- Same rule over `.aw/system/**/*.md`: 433 hits, 117 distinct (F-09).
- `aw doctor --json --dir <target>` runs on the scratch target and returns a `diagnostics` list with `rule` keys, so
  V-04/E-05(b) filtering by rule id is reachable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `tests/test_suite_instruction_marker_parity.py` `assertIn(marker_expr, prose)` over `engine.agents_pointer_prose(target_layout=layout)` | Moving the suite paragraph out of `agents_pointer_prose` breaks this existing test; the plan neither named it nor declared its path, and the parity guarantee it carries would be lost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 repoints it to this repo's repo-local region and adds a negative assertion; census re-run required at execution; path in Scope-Paths. |
| PR-002 | HIGH | IN-SCOPE | G. Executability / F. KISS | F-07, F-09 measurements; original E-04 "backticked repo-relative paths" | "Repo-relative path" was undefined; a naive rule flags `aw.agent/v1`, `pending/`, `records/<type>/`; the README glob vs bundle scope was unspecified, and the bundle yields 433 unfixable hits. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 specifies the token rule, scan set, relative-to-file resolution and allowlist candidates; bundle deferred with `Carrier-Declined` and reason. |
| PR-003 | MEDIUM | UNDER-SCOPE | C. Operability | `artifact_core.drift_exit_code`; `check_engine._DEFAULT_RULESPEC` is `error` | The probe's severity was unstated; an unregistered rule defaults to `error`, so user README edits would turn `aw doctor` red, contradicting the plan's own "advisory" scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rule registered at `info` (precedent `doctor.artifact-status-location-drift`); `check_engine.py` in Scope-Paths; V-04 pastes `rule_spec(...).severity`. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | F-08; `agents_pointer_prose` literal "`.aw/inbox/` is a GITIGNORED drop zone" and "write a plan under `.aw/records/plans/pending/`" | Legacy layout block hard-codes two `.aw/` paths, so E-03's "every path exists in either layout" was unachievable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 makes the pending path `{plans_dir}/pending/` and emits the inbox paragraph for the aw layout only (matching `xzlu9b`); V-03 pastes the legacy dangling list. |
| PR-005 | MEDIUM | IN-SCOPE | G. Executability | `agents_pointer_prose` "TEST OUTCOMES, NOT CODE STRUCTURE" paragraph | E-02 said "move the AW-only paragraphs" without an exact set; the no-code-pinning, tooled-commit and self-contained-question rules are general and only their P12/P16/RELEASING/CONTRIBUTING citations are AW-only. Moving whole paragraphs would strip valid guidance from targets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 enumerates the exact moved paragraphs and clauses and names what stays. |
| PR-006 | LOW | UNDER-SCOPE | G. Executability | `cli._install_one` calls `engine.print_summary`; original Scope-Paths lacked `cli.py` | The install-advisory call site was unnamed and its file undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the site; `cli.py` added. |
| PR-007 | LOW | IN-SCOPE | E. Verification | original V-02 | "Regenerate with the normal install/update path" was unnamed and "still say everything" had no behavioral check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the command; V-02 asserts `agents_managed_block(...)` is a substring of `AGENTS.md` and the suite line sits after the close marker. |
| PR-008 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-009 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` "move the plan to `executed/` with `aw ipd set executed ka0g86`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's contract shape. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the dangling-reference probe scan the installed workflow bundle? | No; managed block plus records READMEs (and inbox README) | Scan everything with a large allowlist; scan bundle at lower severity | F-09: 433 hits over 117 tokens, all conditional or example names | yes |
| D-2 | Doctor severity for the new rule? | `info` | `warning` (exits 1, turns every customised target red) | `artifact_core.drift_exit_code` exempts only `info`; plan Scope check says advisory; `doctor.probe_artifact_audit` precedent | yes |
| D-3 | Where does the parity test's guarantee live after the move? | This repo's `AGENTS.md` repo-local region | Delete the test; keep the text in the managed block | The AW-only text moves there by E-02; the test's own P16 note treats the instruction text as the artifact | yes |
| D-4 | Emit the inbox paragraph for the legacy layout? | No, aw layout only | Emit with a legacy path | `xzlu9b` E-03 installs the inbox lane for the aw layout only | yes |
