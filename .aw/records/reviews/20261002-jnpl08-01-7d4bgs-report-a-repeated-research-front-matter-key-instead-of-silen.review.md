# Review findings: plan 7d4bgs

- Subject-Id: 7d4bgs
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `64d8ed261` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified (scratch fixture under gitignored `.aw/state/`, deleted after):
- `research_contract.parse_frontmatter("---\na: 1\na: 2\n---\n")` -> `{'a': '2'}`; boundary rules as the plan states.
- Census using `parse_frontmatter`'s boundary: `fenced 127 repeated [] nofence ['conformance-results-template.md', 'plan-review/20260712-0156-14-chatgpt-modular-report-template.md']`.
- Fixture via the real writers: `id: aaaaaa` then `id: m8zg5y` -> `entries 1 scan-drift []`; `status: bogus` then `status: todo` -> `entries 1 scan-drift []`;
  `blocks-release: -` then `Blocks-Release: next` -> `entries 1 scan-drift []`; `status: todo` then `status: bogus` ->
  `entries 0 ["frontmatter-invalid:status: status must be one of [...]"]`.
- `attention.py` and `releases.py` both read the `blocks-release`/`blocks_release`/`Blocks-Release` `or` chain.
- `check_engine.check_content` research branch: `if dirs and include_retired:` -> `_ridx.check_drift`.
- `backlog.metadata-bullet-repeated` registered `error`; the `duplicate`/`graduation` registry guard exists in
  `tests/test_check_engine_spec_criteria.py`; `doctor.build_remediation` has a `"summary-unsafe" in rule` arm.
- `DocEntry` has no text field, so `check_drift` holds no raw text after `_scan_docs`.
- Carriers resolve: `deftzy` (Set `7w6zsl`) and `xnogdl` (from `cvxbbu`) are both pending.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Executability | `research_index.DocEntry` (no text field); E-02 "For each doc the scan already visited, walk the RAW TEXT"; F-10 "text the scan has already loaded" | `check_drift` receives only `DocEntry` values and `Drift`, so the raw text is not available to it. The plan implied reuse of loaded text, which leaves the executor to choose between re-reading and refactoring `_scan_docs`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says to re-read `research_root / e.path` for each indexed entry; F-10, OQ-01 and D-1 prose reconciled. |
| PR-002 | MEDIUM | UNDER-SCOPE | A. Correctness / E. Testing | Probe: `status: todo` then `status: bogus` -> `entries 0`, `frontmatter-invalid` | A repeat whose LAST value is schema-invalid drops the doc before `check_drift` sees it, so the new rule cannot fire. The plan did not state this boundary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 records the boundary and the convergence argument (fixing the invalid line makes the doc an entry, then the rule fires); added to E-02's expected outcome. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification feasibility | E-05/V-05 "plant a repeated `status:` ... gains EXACTLY the new rule id" | Planting a DISAGREEING valid value changes the collapsed status, so `check.stale-index-stale` joins the delta; an invalid value yields `frontmatter-invalid`. Either way "exactly the new rule id" would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05, V-05 and Required tests now require an AGREEING plant (the doc's own value), with the mechanical reason. |
| PR-004 | LOW | UNDER-SCOPE | E. Testing | OQ-03 "a reviewer wanting the agreeing case pinned explicitly can ask for a ninth case" | The agreeing-pair decision was unpinned, and E-05 now depends on that shape. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added case (9), agreeing `status:` pair flagged once; counts updated to nine everywhere. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | Approval gate "do not move this plan to `.aw/records/plans/executed/` until ..." | The gate lacked the paste-actual-output rule as a hard MUST, the `aw ipd begin` / conditional runner-or-executor finalize ownership, and the scope-justification wording. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Contract extended with all three plus the inherited `Blocks-Release: next`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the rule also fire on a doc `_doc_entry` rejected as `frontmatter-invalid`? | No: judge indexed entries only | Walk every file `_scan_docs` visits (would double-report one file with two causes, which E-02 already forbids for `frontmatter-missing`) | Probe `entries 0` + `frontmatter-invalid`; E-02's own one-file-one-cause rule | yes |
| D-2 | How does `check_drift` obtain raw text? | Re-read `research_root / e.path` per entry | Widen `DocEntry` or `_scan_docs`'s return to carry text (changes INDEX.json shape via `_asdict()` or a shared signature) | `DocEntry` has no text field; F-10 re-read cost ~5ms | yes |
| D-3 | What shape does E-05's real-tree plant use? | An agreeing duplicate of the doc's own `status:` | A disagreeing valid value (adds `check.stale-index-stale`); an invalid value (yields `frontmatter-invalid`) | Probes above; `check_drift`'s in-memory manifest comparison | yes |
