# Review findings: plan ucr3h8

- Subject-Id: ucr3h8
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`23863c32a`), so no snapshot was needed.

Gates:

- `aw ipd lint` reported clean at `author` and at `review-finalize` (before and after the edits) and at `pre-transition`.
- `aw ipd coverage ucr3h8` reported "Orchestrator ucr3h8 is ready for review." before and after the edits, so there were no IPD-S407/S408 repair attempts.

Checks:

- All 7 child files exist and match the table: Order, id6, `Item-Dependencies`, `Kind: child`, `From-Backlog: kvwwt0`, and `Blocks-Release: next`.
- `irjoga` is in `superseded/` with a RETIRED header that points at ucr3h8.
- `kvwwt0` is `graduated` and carries `Blocks-Release: next`.
- `or061f` exists.
- `local-only` is `Preset.LOCAL_ONLY`.

Probes:

- `runner_shared.evaluate_backlog_close(repo, 'kvwwt0')` lists the superseded irjoga path under "IPD carrier(s) not executed".
- `check_engine.evaluate_blocking_close(..., 'done')` returns illegitimate without evidence, and `SATISFIED` when given an executed plan as `--evidence`.
- `ivq0nr` is `reviewed` with `Readiness: no-go`, because OQ-01 is `Blocking: yes` and has `Owner: maintainer`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Dependencies / sequencing | Child table row 03 "executed:4gn1ka, executed:ivq0nr"; `20261014-nj13xp-01-ivq0nr-...ipd.md` `- Readiness: no-go`, OQ-01 `Blocking: yes`, `Owner: maintainer` | Order 03 depends on a plan outside the Set that is currently blocked on a maintainer decision. The orchestrator never mentioned this, so a human running `aw oc run cleantgt` would watch Orders 03-07 go dependency-blocked without knowing why. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an EXTERNAL DEPENDENCY note after the child table, plus a pointer in E-03. |
| PR-002 | MEDIUM | UNDER-SCOPE | G. Follow-up / release gate | `runner_shared._classify_backlog_carriers` (`bucket != "executed"` -> unexecuted); superseded irjoga carries `- From-Backlog: kvwwt0` | The HANDOFF close of `kvwwt0` can never succeed, because the superseded `irjoga` is a carrier that will never become executed. Without a stated close route, the item would be left graduated and release-blocking after the Set ships. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Deferred row with `Carrier: kvwwt0` naming the SATISFIED route (`aw backlog set done kvwwt0 --evidence <nwporz executed path>`, verified at review) and forbidding an edit of irjoga. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` (one paragraph) | The gate had no honesty rule, scope fence, path-scoped `aw commit`, by-hand route, or conditional lifecycle (runner retirement vs `aw ipd finalize`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate with all of these and kept "never push or tag". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `kvwwt0` close, given that a superseded carrier blocks HANDOFF? | SATISFIED route with `--evidence` pointing at nwporz's executed path, recorded as a Deferred row | Edit irjoga's `From-Backlog` (rewrites a terminal record); add an E-item to this orchestrator (would be parent-only work that no child covers); `--blocks-release -` (drops the gate) | `check_engine.evaluate_blocking_close` probe (SATISFIED with an executed plan); AGENTS.md rule against changing what a terminal plan records | yes |
| D-2 | Should `ivq0nr` be removed from fnnwj3's dependencies? | No. Document the dependency here; the dependency belongs to fnnwj3 (its E-01 re-measures "after `4gn1ka` and `ivq0nr` landed") | Drop the edge (the child author chose it, and fnnwj3's review owns that call) | `20261015-cleantgt-03-fnnwj3-...ipd.md` line 8 and E-01 | yes |
