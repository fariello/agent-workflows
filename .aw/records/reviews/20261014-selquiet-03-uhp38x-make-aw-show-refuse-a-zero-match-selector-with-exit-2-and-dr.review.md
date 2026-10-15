# Review findings: plan uhp38x

- Subject-Id: uhp38x
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review lane. The plan was already committed and unchanged at `d3c6e8a61`, so no pre-review snapshot was needed. `aw ipd lint --phase author` reported conforming before and after the revisions.

Claims I verified at HEAD:
- `aw show zzzzzz --agent` and `aw show prompt-library --agent` both return `outcome:"findings"`, `exit:1`, rule `show.not_found`. `aw show approved` and `aw show f36de0` return `outcome:"clean"`, `exit:0`.
- `aw show f33nrj --json` (the release record) returns `status:"findings"`, `exit_code:1`.
- `command_surface.py` declares `show` with `exit_contract=(0, 1, 2)`. `tests/conformance_matrix.py` `required_scenarios` appends `domain_failure` when `1 in decl.exit_contract` for read verbs.
- `git tag --contains ef55eadb1` and `git tag --contains efd2019ad` both print nothing. Commit `19bd75020` exists.
- `zyj8io` V-08 has the row `| aw show <sel> | 2 | 2 | 2 | 2 | Conforming (25kzda) |`. `aw show zzzzzz --paths` is rejected by argparse.
- `yxsfjc` is in `executed/`. `cli.selector_tokens_naming_no_artifact` and `cli.emit_zero_match_selector_refusal` exist, and `_run_record_history` uses both.
- `selector_tokens_naming_no_artifact(Path("."), ["zzzzzz","prompt-library","f36de0","plans"])` returned `('zzzzzz',)`. `(["f33nrj","README.md"])` returned `()`.
- Predicate timing in this worktree: 1.48s and 1.35s warm for `zzzzzz`. The whole current `aw show zzzzzz` takes 0.98s.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / D. Invariants | `docs/cli-output-contract.md` Section 11.1 "Precedent and Scope": "a selector that names a real artifact with nothing to report is a clean empty answer"; `aw show f33nrj --json` exits 1 today; `selector_tokens_naming_no_artifact(.., ["f33nrj"]) == ()` | E-02 decided refusal on vocabulary membership alone. That would refuse at exit 2 any real artifact in a tree `_run_show` does not search (releases, reviews, comms), telling the operator a real record does not exist. It also diverged from the one shared predicate the contract doc names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now refuses exactly the output of `cli.selector_tokens_naming_no_artifact` and answers exit 0 otherwise. Added the `f33nrj` class to E-01, V-01, V-02, and E-04 case (4). |
| PR-002 | MEDIUM | IN-SCOPE | C. Architecture (one mechanism) | `cli.emit_zero_match_selector_refusal` (shipped by executed `yxsfjc`); old E-02 "if already present in `cli.py` or else" hand-build; old F-6 / Scope "does NOT depend on unexecuted sibling plan `yxsfjc`" | The plan hedged on the shared emitter and specified a second hand-built refusal with different wording (`SCHEMA_ID`, which does not exist; the module has `SCHEMA_VERSION`). `yxsfjc` is executed, so the hedge was stale and invited a duplicate path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 calls the shared emitter unconditionally. Added `executed:yxsfjc` to Item-Dependencies (satisfied). Rewrote F-6 and the conventions. Added a STOP condition if the helpers are absent. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Right-sizing | old E-02 item (4) bundled help-text rewrites into the `_run_show` behavior change | Two independent deliverables with separate test surfaces (runtime behavior vs `--help` text) were in one E-item, and V-02 did not verify the help text. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-06 / V-06 (help text, verified with `show --help`). The old help also named `id@generation` in the `action_ref` help, which E-06 now covers. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability / evidence | `CHANGELOG.md` has no `## [Unreleased]` or `### Changed`, only `## 2.0.0 (pending)` with `- Changed:` bullets; Spec sync cited `.aw/records/specs/20260928-1400-01-25kzda-...spec.md`, which does not exist (real path `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`); `to_agent_record` cited in nonexistent `output_contract.py` (it is in `result_types.py`); `term.empty_result(..., status="ok")` vs the `_run_record_history` precedent `status="clean"` | Wrong anchors would send the executor to sections and files that do not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected every anchor. Line-number hints replaced by symbol anchors. The spec is described as precedent, per Section 11.1's own wording. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Execution contract | old gate: `aw ipd set executed uhp38x` hand transition; no scope fence, STOP conditions, never-push/never-tag, or runner/executor finalize ownership; plan file absent from Scope-Paths | The gate told the executor to self-transition and lacked the required contract elements. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate in the repo's standard form (approval, begin, scope fence as declaration, honesty, commits, runner-owned finalize). Added the plan path to Scope-Paths. |
| PR-006 | LOW | IN-SCOPE | C. Operability (measured cost) | old F-5 "zero extra I/O"; measured predicate 1.35s to 1.48s warm | With PR-001's fix the zero-match path now does real resolution. F-5 claimed it was free. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote F-5 with the measured numbers. Accepted because the cost hits only the error path and keeps one shared predicate. Recorded as D-3. |
| PR-007 | LOW | IN-SCOPE | E. Verification | old V-04 `-v` under configured `addopts`; E-04 case (5) asserted only the declaration; vocab token `prompt-library` hard-coded as a live-tree baseline | Weaker evidence. A live-artifact token could also drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 uses `-o addopts=""` and also runs `tests/test_read_verb_zero_match_refusal.py`. E-04 case (6) checks that the exits observed are members of the declared contract. E-01 now re-derives the token at execution time. |

`aw ipd lint --phase review-finalize` reported conforming after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What decides refusal on `aw show`'s zero-match path? | `cli.selector_tokens_naming_no_artifact` output | Vocabulary membership alone (refuses real non-displayed artifacts); widening `record_types` (positive-match scope change, declined) | `docs/cli-output-contract.md` Section 11.1 "Precedent and Scope"; demo `(["f33nrj","README.md"]) -> ()` | yes |
| D-2 | Does `aw show` drop exit 1 from its exit contract? | Yes, `(0, 2)` | Keep `(0, 1, 2)` and add a synthetic `domain_failure` scenario | `git tag --contains` empty for `ef55eadb1`/`efd2019ad` (unreleased); `tests/conformance_matrix.py` `required_scenarios` | yes |
| D-3 | Is the shared predicate's ~1.4s cost on the zero-match path acceptable? | Yes | A bespoke 4-tree check (~0.9s to 1.06s), which would be a second predicate | Measured in this worktree; cost only on error path | yes |
| D-4 | What `next` does the exit-0 empty answer offer? | `aw find <ref>` | Bare `aw find` (loses the query) | `_run_record_history` precedent offers a query-preserving next | yes |
