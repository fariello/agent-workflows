# Review findings: plan lkn1zt

- Subject-Id: lkn1zt
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `a178320e9`. The plan was committed and unchanged (`dc23b1d93`), so no snapshot was needed. `aw ipd lint --phase author` was clean (one info, `IPD-Z602`, on E-01). `--phase review-finalize` was clean after the revisions.

Re-verified:
- `y0vcm9` "Actual questions produced by agents": 12-row table and judging paragraph quoted correctly.
- `er11a0` is `approved` in `pending/` (not executed). `- Item-Dependencies: executed:er11a0` plus the E-01 preflight STOP gate it correctly. Its deferral row names `- Carrier: jymlaw`.
- `aw research new --kind findings --set askmeplain --slug askme-live-trials ...` dry-run derives `20261014-askmeplain-02-<id6>-askme-live-trials.findings.md`; `records/research/INDEX.*` is gitignored.
- `opencode export [sessionID] --sanitize` exists. `claude --help` has `--disallowedTools` and `-p`. `agy --help` has `-p`, `--conversation`, `--model`, and no question-tool disable flag.
- `lane_containment.LANE_PERMISSION_POLICY` `"question": "deny"`; the env JSON shape is `{"permission": ...}`. The `runner_shared` driver sentence "non-interactive: do not invoke an interactive question tool or wait for human input" is present.
- `~/.config/agent-workflows/runner-profiles.json` has two OpenCode profiles (`opus` default, `gem` = `google/gemini-3.8-flash`).
- `aw ipd scaffold --help` has no `--blocks-release`; `aw ipd set` has it.
- `aw research set-outcome` takes `--to {adopted,informational,rejected,none-yet} --consumed-by ... --apply`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Runner fallback | old gate: "perform E-01 to E-03, mark E-04 to E-08 blocked" | A runner-dispatched run would create the findings doc and a disposable worktree (E-02, E-03) and then block before E-08 removes the worktree, leaving it orphaned outside `.aw/worktrees/` with a half-written doc. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fallback is now read-only E-01 only, with E-02..E-08 blocked. Added an approval note that `aw oc run all` dispatches approved plans. OQ-02 is reconciled. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Model coverage | `runner-profiles.json` profiles `opus`, `gem` | E-01 named only one OpenCode model, so the `gem` profile (a different model family) would go untrialled although "each host/model in use" is the brief. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now enumerates `aw oc profile list`; OQ-01 states each profile is a combination; authoring snapshot updated. |
| PR-003 | MEDIUM | IN-SCOPE | E. Capture location | E-04 "into the gitignored `.aw/state/askme-trials/`"; E-08 removes the worktree | Sessions run in the disposable worktree, so a relative capture path would be deleted with it, and V-04's `ls` could not be satisfied. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 creates the capture dir in the executing checkout; E-04/E-05/E-06 give explicit per-host capture commands and filenames; V-04..V-06 `ls` there. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Trial feasibility | `agy --help` (no question-tool disable flag); E-05/E-06 "the captured transcript file list" | No capture mechanism for Claude Code and Antigravity, and no way to stage "tool unavailable" on Antigravity, so V-05/V-06 asked for evidence nothing produced. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named transcript locations; Antigravity tool-unavailable uses a host mechanism if one exists, else `not-run` with a reason (vocabulary defined in E-02, never for convenience); screen-copy fallback stated. |
| PR-005 | LOW | IN-SCOPE | E. Trial staging | E-04 "after a deliberately unclear question" | The unclear question was not staged reproducibly, so trials 1–2 would vary by tester. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Staging prompt specified against fixture question (b). |
| PR-006 | LOW | IN-SCOPE | A. Trial isolation | E-03 `git worktree add` at `HEAD` | A non-detached worktree creates a branch, and a trial session could commit to it, leaving a stray branch after removal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `--detach`; "trial sessions must not commit or push"; E-08 allows `--force` on that disposable path only. |
| PR-007 | LOW | IN-SCOPE | Tooling accuracy | `aw ipd scaffold --help` (no gate flag); E-08 `set-outcome` without args | E-07 implied scaffold sets `Blocks-Release`; E-08's set-outcome had no value. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 uses `aw ipd set to-review <plan> --blocks-release next`; E-08 gives `--to adopted` (or `informational`) `--consumed-by lkn1zt --apply`; V-08 demands its output. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract / records | gate; Scope-Paths `plans/pending/*`; OQ `Owner: opencode`; history order | The gate lacked an OQ status line and conditional finalize ownership. The Scope-Paths glob was status-specific. The OQ owner was a host name, not a role. The history was oldest-first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate completed (OQ line, hand-executor finalize, runner case, no `git mv`); `plans/**`; `Owner: plan author`; history newest-first. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does each OpenCode runner profile count as a separate host/model combination? | Yes | Default profile only (leaves a shipped profile untested) | `runner-profiles.json` profiles; backlog `jymlaw` "each host/model in use" | yes |
| D-2 | What should a runner-dispatched run do? | E-01 only, the rest blocked | E-01..E-03 (orphans worktree and doc); refuse entirely (loses the cheap preflight) | E-03/E-08 lifecycle | yes |
| D-3 | What if Antigravity cannot stage "tool unavailable"? | `not-run` with a reason | Simulate by instruction (not the same condition; would be a fabricated trial) | `agy --help`; plan honesty rule | yes |
