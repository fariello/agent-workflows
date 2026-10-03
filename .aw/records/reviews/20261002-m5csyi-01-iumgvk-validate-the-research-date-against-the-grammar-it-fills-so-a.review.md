# Review: Validate the research date against the grammar it fills

- Subject-Id: iumgvk
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (its sha256 matched the sealed lane input), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `6d48f3f94`:

- `today = date_str or date.today()...` precedes the id6 mint in both `plan_new` and `plan_new_comparison`.
- `_emit_and_write` has exactly two callers, `run_new` and `run_new_comparison`.
- `artifact_adopt` calls `_rc.plan_new(..., date_str=date_str)` and then runs `_R.parse_name`.
- `strptime(..., "%Y%m%d")` refuses `99999999`, `20261332`, `20260230` and `00000101`, and accepts `20260929`.

With HOME isolated in a nested fixture, the following reproduced:

- F-01: `ESC-fa-00-...findings.md` was written at `<tmp>/a/b/c/`.
- F-02: three `ESC-cmp-*` files were written at `<tmp>/a/b/c/`.
- F-09: a newline date under an existing set wrote the clean-named `20260101-inj-01-...`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Security / test safety (B, E) | `agent_workflows/research_contract.py:399` `resolve_research_root` -> `record_producers.resolve_record_path`; review probe output `changes[0].path` = `.aw/projects/repo-7c3bc1/records/research/../../../../ESC-x1-...` | The plan's safety bound (traversal depth bounded to the fixture depth) is NOT sufficient. A scratch git repo with no `.aw/records/research` resolves its research root to `$HOME/.aw/projects/<name>-<hash>/records/research`. A review probe with a fixture-safe depth therefore wrote `$HOME/.aw/ESC-x1-00-dkj15o-x1.findings.md` outside the temp base. This is exactly the collateral damage the plan warns about, in a place the plan's arithmetic did not model. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires three things: a pre-created `<repo>/.aw/records/research`, `HOME`/`XDG_CONFIG_HOME` isolated to the temp base, and the probe target computed from the RESOLVED root, with both the root and the target asserted inside the base. V-04 quotes this, and the gate names it as a third hazard. Re-measured with all three rules: the escape landed inside `<tmp>`. |
| PR-002 | LOW | IN-SCOPE | Input validation (B) | Python 3 `re`: `\d` is Unicode-aware; measured `re.match(r'\A\d{8}\Z', '２０２６０９２９')` -> match, `[0-9]{8}` -> no match | `\A\d{8}\Z` accepts fullwidth digits. Only the calendar check happens to refuse them. | all Low | FIXED | The regex is now `\A[0-9]{8}\Z`, and the fullwidth input was added to E-01 and V-01. |
| PR-003 | MEDIUM | IN-SCOPE | Test design (D, E) | backlog `0ougsh` `- Status: graduated`, `- Graduated-To:` run that produced pending plan `plb8jx` (`From-Backlog: 0ougsh`) | E-05(e) committed a test asserting that the live `set-assign` escape SURVIVES. That test turns red whenever `plb8jx` lands, in either execution order. It also commits a destructive move probe into the suite. | all Low | FIXED | (e) is now V-05 scratch evidence with `0ougsh`/`plb8jx` named, not a committed test. |
| PR-004 | MEDIUM | IN-SCOPE | Validation feasibility (E) | `research_cmd._mint_research_id6` -> `artifact_core.mint_id6` (random) | Non-regression (a) required "the SAME path and bytes" as a HEAD reference. The id6 is random, so that can never match. | all Low | FIXED | The id6 is now pinned by monkeypatch, or normalized, and the executor must state which. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | `grep run_new_from_plan agent_workflows/` -> none; `research_archive.apply_moves` writes via `RF._atomic_write` | The plan names a third `_emit_and_write` caller, `run_new_from_plan`, that does not exist. It also cites `aw research archive` as proof that shard descendants are accepted, but archive never goes through `_emit_and_write`, so that run proves nothing. | all Low | FIXED | Caller counts corrected in E-03 and OQ-02. The archive proof is replaced with a direct `_emit_and_write` call on a shard-nested path (E-03, V-03). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do we make the destructive probes safe? | Pre-create the research dir, isolate HOME, and assert the resolved root and target | Depth arithmetic alone (measured insufficient) | the review probe output in PR-001 | yes |
| D-2 | How do we record the unfixed `set-assign` escape? | As V-05 scratch evidence | A committed test (it breaks when `plb8jx` lands, and it pins a defect) | `plb8jx` pending with `From-Backlog: 0ougsh` | yes |

### Side effect requiring a human

The PR-001 probe wrote `$HOME/.aw/ESC-x1-00-dkj15o-x1.findings.md` (152 bytes) and created `$HOME/.aw/projects/repo-7c3bc1/`. Both are outside this lane's permitted directories, so the reviewer could not delete them. They should be removed by hand.
