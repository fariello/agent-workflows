# Review findings: plan kgv213

- Subject-Id: kgv213
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `211969bb8` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified with read-only probes (nothing written to tracked paths):
- F-01 reproduces at this HEAD on BOTH spellings: `aw backlog set <item> --status open` and `aw backlog set open <item>` with `--message "metadata only"` printed `unchanged`, wrote no column-zero record, and `backlog.validate_item` returned `[]`. The predicate returned True and `_prior_history_records` returned `[]`.
- `status_set._prepare_status_change` computes `is_dup` via `same_status_message_is_duplicate` and `should_write_history = not (is_same_status and is_dup)`, as the plan says. The predicate's other callers are `specs.run_note` and the specs migrate path.
- The proposed rule, implemented as a probe: newest record agrees with the loose reader on all 2464 tracked artifacts with a history heading; records and body equal `_prior_history_records` / `_strip_metadata_and_history` on all 975 tracked backlog items. The loose and strict lists differ on 161 artifacts (plans 155, backlog 3, reviews 2, research 1). The counts in F-02/F-04 have drifted slightly; their conclusions hold.
- `_strip_metadata_and_history` has no production caller. The live body reader on the writer path is `set_records._extract_body` (`close_on_answer`), which the plan had deferred.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Data integrity | `agent_workflows/backlog.py:1725` `_reattach_history` (`prior = _prior_history_records(old_text)`); `agent_workflows/set_records.py:379` `body = _extract_body(text)`; plan E-02 as authored, Deferred `set_records._extract_body` | E-02 moved the prior-record source onto a rule that continues past a wrapped record but left the body boundary on the old strict reader. A review probe on a wrapped-record `close_on_answer` fixture wrote the following records TWICE with the continuation orphaned between them. The new rule also dropped the continuation text itself. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 adds `record_lines` (records with their continuations); E-02 returns `record_lines`; new E-06 moves `_extract_body` onto the shared body; E-04 (e2) round-trips through `close_on_answer`; V-06 added. Probe with the revised shape: each record once, continuation kept. Deferred bullet removed, Scope and Scope-Paths updated, F-06 added. |
| PR-002 | MEDIUM | IN-SCOPE | A. Data integrity | plan E-01 as authored "`body` ... `.strip()`ed" | Stripping the body de-indents a leading blank-separated quotation to column zero, and the next rewrite turns it into a record: the `tk1gqo` defect by another route (probe: 2 records became 3). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now removes only leading blank lines and trailing whitespace, keeping the first line's indentation; E-04 (e)/(e2) assert it; F-07 added. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing | `agent_workflows/specs.py:956` `run_note` calls `same_status_message_is_duplicate` | E-03 changes the predicate for the specs callers too, but no test covered them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (h) drives `aw specs note` on an indented-only spec fixture; spec and status_set test modules added to the validation command. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked the OQ status line, the scope-fence declaration, `aw ipd begin`, the MUST-paste wording, and the statement that the executor must not finalize under a runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added. |
| PR-005 | LOW | IN-SCOPE | G. Live criteria | plan V-02 "the expected count is 0 except where F-04 names the item" | V-02 used a count of live artifacts as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now demands re-derivation and the property (every changed item listed and justified). |
| PR-006 | LOW | IN-SCOPE | Evidence drift | plan F-02/F-04 "2489", "163", "969 tracked backlog items" | Corpus counts drifted (2464 / 161 / 975 at `211969bb8`); conclusions unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded here; F-rows keep their authoring-time context, and the V-items re-derive at execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should `_prior_history_records` return under the shared rule? | `record_lines` (records plus indented continuations) | `.records` (drops wrapped text, duplicates following records on rewrite) | review probe of `_reattach_history` on a wrapped fixture; `backlog.py:1725` | yes |
| D-2 | Migrate `set_records._extract_body` here or leave it deferred? | Migrate here (E-06) | Defer (leaves the duplication route open the moment E-02 lands) | `set_records.py:379-381` feeds `_extract_body` and `_reattach_history` in one assembly | yes |
| D-3 | Should `body` be fully stripped? | No: drop leading blank lines and trailing whitespace only | `.strip()` (forges a record from an indented quotation) | review probe, F-07 | yes |
