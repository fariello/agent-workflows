# Review findings: plan 9epp40

- Subject-Id: 9epp40
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `23863c32a`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Re-measured at HEAD: spec `25kzda` line 148 (step 8) and line 1085 (5.1 ledger bullet) are unamended
(F-1, F-2 MATCH); `rdjka2` OQ-01 records `MAINTAINER RESOLUTION (2026-10-08, ...): OPTION (b)` and
`utb2qr` exists; `grep -nE 'ledger_store|RunLedgerStore|ledger\.jsonl'` on `oc_runipd.py` and
`agy_runipd.py`: no matches; `stale_spec_anchors`: 0; targeted pytest: `64 passed in 5.64s`;
`aw specs check`: exit 0 (40 specs); `aw sanitize --agent`: clean; `aw check --agent`: exit 1 with
`{'error': 19, 'warning': 1, 'info': 90}`, none of the errors at this plan or the spec (the only
diagnostic at this plan is `check.lifecycle-transition-unvalidated` at info). No in-tree test or module
greps for either amended string (F-3 MATCH). `find . -name ledger.jsonl`: 0.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (domain invariant), spec consistency | spec `25kzda` 5.3 intro "The engine stores repository-local, crash-safe run state." (:1290), "A snapshot is a cache; replaying the ledger is authoritative." (:1302), 5.3a "The hash-chained ledger is the run's record and replaying it is authoritative;" (:1312), resume step 1 "verifies the ledger chain before doing anything." (:1337); `runner_shared.append_jsonl`, `runner_shared.load_state`; `oc_runipd.main` resume branch | The same driver-run hash-chain claim the plan corrects in 1.2/5.1 is restated in four 5.3/5.3a sentences. Amending only 1.2/5.1 leaves the spec contradicting itself on the exact question the maintainer decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-03/V-03: four same-line substitutions with dated provenance; resume step 1 wording grounded in `load_state`/`load_json` and `run_cli._run_resume`; F-4 added; Scope, Goal, Scope check updated. |
| PR-002 | MEDIUM | UNDER-SCOPE | Spec/documentation sync | `docs/evidence.md:3` "Every run records tamper-evident evidence in an append-only ledger." | User-facing doc states the claim being retracted; plan said no doc needed updating. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-04/V-04 (no em/en dashes, checked by grep); `docs/evidence.md` added to Scope-Paths; F-5 added; spec-sync section names why `docs/architecture.md` and `docs/recovery.md` are unchanged. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | plan V-03 (pre-review) demanded `aw check` "exiting 0"; measured exit 1 with 19 pre-existing errors unrelated to this plan | Unsatisfiable exit-0 demand would force the executor to fail or misreport. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 captures an `aw check --agent` baseline (count re-derived at execution); E-05/V-05 bar is no new error rule and no warning/error located at the touched paths. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (spec consistency) | spec `25kzda` uses "run ledger" for driver-run records at e.g. :388, :416, :465, :822, :1429 | Many other "run ledger" uses would read as hash-chained after 1.2 scopes the term, but editing them all would collide with transcription-locked 4.2 and `jmogmv`'s 5.5/5.6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 step 8 text gains a terminology clause: "run ledger" of a driver run means its durable run record; chain properties hold only for `ledger.jsonl`. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | plan Project conventions (pre-review) cited `agent_workflows/run_LEDGER_store.py`, `run_cli.py`, `tests/test_run_recovery_cli.py` as the files `rdjka2` corrected; commit `3b84f5c8b` stat | `run_LEDGER_store.py` does not exist; `rdjka2` actually changed `runner_shared.py`, `run_recovery.py`, `docs/recovery.md` (and added the test). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citation corrected to the commit's real file list. |
| PR-006 | LOW | IN-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` (pre-review) | Gate lacked the honesty rule, scope-fence declaration, never-push, and conditional lifecycle ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the repo's standard contract (matches sibling `v47z9u`), with stop conditions limited to genuinely unsafe cases. |
| PR-007 | LOW | IN-SCOPE | Rubric G (verification strength) | plan V-01..V-03 (pre-review) | V items did not pin line-count preservation or forbid edits to 4.2/4.6/5.5/5.6/6.2 concretely; out-of-Set sibling `jmogmv` editing 5.5/5.6 of the same spec was not noted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 and V-05 record `wc -l` before/after; V-02 checks no hunk in excluded sections; `jmogmv` commute note added to Project conventions. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the 5.3/5.3a sentences be amended in this plan or filed as a new backlog item? | Amend here (E-03). | Separate backlog item (REJECTED: leaves the approved spec self-contradictory on the maintainer's decided question in the interim, and the edits are same-line, Low risk, in the same file and Scope-Paths). | `rdjka2` OQ-01 resolution "amend spec 25kzda to say so"; spec :1290, :1302, :1312, :1337. | yes |
| D-2 | How to handle the remaining "run ledger" uses spread across the spec? | One terminology clause in step 8. | Edit each occurrence (REJECTED: 4.2 is byte-for-byte locked by `tests/test_run_finding_spec_transcription.py`; 5.5/5.6 belong to `jmogmv`). | spec :388, :416, :465, :822, :1429; `jmogmv` Deferred section. | yes |
| D-3 | What bar replaces "aw check exits 0"? | No new error rule vs. an E-01 baseline and no warning/error at touched paths. | Keep exit 0 (REJECTED: unsatisfiable, 19 unrelated errors). | measured `aw check --agent` at `23863c32a`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
