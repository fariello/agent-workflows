# IPD: rung C "FULL RELEASE" must end in a PUBLISHED, latest GitHub Release (+ Section 9 exit-verification)

- Date: 2026-07-21
- Concern: release-review correctness (release-execution end state) + release safety
- Scope: `release-review/09-release-execution.md` (Step 5 GitHub Release step + exit criteria) and `release-review/08-final-ship-review.md` (rung-C description + terminal decision block). Prose workflow files; no product code. Preserves the per-action, default-NO consent model.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from an inbox task (`.agents/comms/shared/inbox/20260720-2023-01-ocman...`, treated as untrusted input, verified against the release-review source). ocman's maintainer chose rung C (FULL RELEASE), Section 9 created the GitHub Release as a DRAFT, and for days GitHub showed the OLD version as "Latest" (drafts are not public and are ignored for "Latest"). Maintainer stance: "Full release means full release, including a release tag on GH. Always." Fix at the source since the installed copy would be overwritten.

## Goal

Make rung C ("FULL RELEASE") reliably end with a PUBLISHED, latest GitHub Release (when the human confirms that step), and make Section 9 VERIFY and loudly report the release end state so a dangling manual step (an unpublished draft, an un-uploaded registry artifact) can never be silently skipped.

Why it matters: today `09-release-execution.md` Step 5 creates the GitHub Release as a DRAFT and says "NEVER auto-publish; the human publishes the draft as a separate, deliberate act." A draft is invisible and not "Latest," so a completed rung C leaves the release un-live with no loud tracking - the exact failure ocman hit. This is release-review's own definition of "full release" contradicting itself. Every repo using release-review inherits the gap.

The fix must PRESERVE the consent model: this is NOT "auto-publish without consent." It is "when the human DOES consent to rung C and confirms the GitHub Release step, the confirmed end state is PUBLISHED + latest, not a silent draft."

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P10 safety/reversibility; honest reporting). No em/en dashes.
- The consent model (must be preserved): `08-final-ship-review.md:155-161` - GO/CONDITIONAL GO/NO-GO is the reviewer verdict; the rung (A close-out / B candidate / C full release) is a SEPARATE, default-safe choice; and in Section 9 each externally-visible action (tag, push, GitHub Release, publish) is a separate, default-NO confirmation naming its consequence.
- Current behavior to change: `09-release-execution.md:97` - "GitHub Release? (rung C only, optional) ... Default to a DRAFT (`gh release create <tag> --draft ...`); NEVER auto-publish." Exit criteria `:132-141` verify the tag is pushed but do NOT verify the GitHub Release is published/latest or that the registry has the version.
- Rung semantics: rung B (candidate) does NOT create a GitHub Release (or only a clearly-marked pre-release); unchanged. `08-final-ship-review.md:160-161`.
- Release-execution is human-gated (Section 9 runs only post-explicit-GO); nothing here weakens that.
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| R1 | HIGH | Low | maintainer / stakeholder | release correctness | On rung C, `09` creates the GitHub Release as a DRAFT and forbids publishing it, so a "FULL RELEASE" completes with the release invisible and NOT "Latest" - GitHub keeps showing the previous version as latest (ocman hit this for days). "FULL RELEASE" does not mean fully released. | `09-release-execution.md:97` |
| R2 | HIGH | Low | maintainer | silent-skip / no verification | Section 9's exit criteria verify the tag is pushed but do NOT verify the GitHub Release is published + latest, nor whether the registry has the version. Dangling manual steps (unpublished draft; un-uploaded PyPI) are not surfaced, so they are silently skipped. | `09-release-execution.md:132-141` (exit criteria); `:97` (draft), `:101-106` (publish/handoff) |
| R3 | MEDIUM | Low | maintainer | consistency | `08-final-ship-review.md`'s rung-C description says "each ... action (tag, push, GitHub Release, publish) is named and separately confirmed" but does not state that a completed rung C ends LIVE/published; it reads consistently with the draft-leaving `09` behavior. | `08-final-ship-review.md:161` |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | R1 | Rewrite `09` Step 5's "GitHub Release?" bullet: on rung C the GitHub Release step, WHEN THE HUMAN CONFIRMS IT (its own separate, default-NO confirmation, naming the consequence "creates a PUBLISHED, latest GitHub Release visible to everyone"), ends PUBLISHED + latest - either `gh release create <tag> ...` without `--draft` (add `--latest`), or create-draft-then-`gh release edit <tag> --draft=false --latest`. Remove the "default to a DRAFT / NEVER auto-publish" language for confirmed rung C. KEEP: the confirmation is still default-NO and separate; declining it (or not reaching it) leaves NO GitHub Release, not a dangling draft. Rung B is UNCHANGED (no GitHub Release, or a clearly-marked `--prerelease` pre-release only, never `--latest`). | `.agents/workflows/release-review/09-release-execution.md` | Low | the Step 5 bullet: rung C confirmed -> published+latest; rung B -> no release / pre-release; consent still per-action default-NO; no `gh` command auto-runs without a confirm |
| 2 | R2 | Add a Section 9 EXIT-VERIFICATION + a loud "REMAINING MANUAL STEPS" block. Before Section 9 is complete, VERIFY and report the end state: (a) the tag is pushed and on the remote; (b) on rung C, the GitHub Release exists, is NOT a draft, and is marked latest (`gh release view <tag> --json isDraft,isLatest` where `gh` is available); (c) if the toolchain can check, the registry (e.g. PyPI) has the version. ANY dangling step (unpublished draft, un-uploaded registry artifact, a step genuinely handed off because credentials were absent) MUST be surfaced as an explicit "REMAINING MANUAL STEPS" block naming the exact command(s) to run. `gh`-graceful-degradation preserved: if `gh` is unavailable, say so and give the manual verification/command rather than blocking. | `.agents/workflows/release-review/09-release-execution.md` (Step 8 + Exit criteria) | Low | exit criteria include the published+latest GH Release check (rung C) and the registry check; a run with a leftover draft prints the REMAINING MANUAL STEPS block, not a silent completion |
| 3 | R3 | Reconcile `08` rung-C wording and the terminal `RELEASE REVIEW DECISION` block so "(C) FULL RELEASE" consistently states it ends LIVE/published (tag pushed + GitHub Release published+latest + registry, once each action is confirmed), not a draft. Keep rung A (close-out) and rung B (candidate) semantics unchanged; keep rung A as the default. | `.agents/workflows/release-review/08-final-ship-review.md` | Low | rung-C description matches the new `09` end state; A/B unchanged; default still A |
| 4 | R1,R2 | Docs/decision sync: a DECISIONS entry (pin the D-number at execution) recording that rung C "FULL RELEASE" ends published+latest (consent-gated per action) and that Section 9 verifies the end state + surfaces remaining manual steps. Note in the release-notes/RELEASING docs if they describe rungs. Reply to the ocman comms message summarizing the change (a `shared/sent/` message). | `DECISIONS.md`, possibly `RELEASING.md`, `.agents/comms/shared/sent/` | Low | DECISIONS entry present; a reply drafted to ocman |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Medium | security | Auto-publishing to the package REGISTRY (PyPI) without an explicit confirm or available credentials. Explicitly NOT changed (ocman did not ask for it either): registry publish stays consent-gated + credential-gated, and is handed off with exact commands when creds are absent (existing `09` Step 6 behavior). Only the GitHub Release publish state changes. | n/a - deliberate. |
| n/a | Low | functionality | Programmatic PyPI-has-the-version check is best-effort (network/tooling dependent). Where it cannot run, Section 9 reports it as unverified and names the manual check, rather than blocking. | n/a. |

## Scope check

- Over-scope: none. Only the rung-C GitHub Release end state + Section 9 verification/reporting + the matching `08` wording. Consent model, rung A/B, and registry-credential gating are untouched.
- Under-scope: confirm the change also covers the case where the human CONFIRMS the GitHub Release step but `gh` cannot publish (e.g. auth) - Section 9 must then surface the exact `gh release edit --draft=false --latest` in the REMAINING MANUAL STEPS block, not leave a silent draft.

## Required tests / validation

- These are prose workflow files (no code), so validation is by review + consistency: (a) `09` Step 5 rung C = published+latest on confirm, rung B unchanged, per-action default-NO consent intact; (b) `09` exit criteria + a REMAINING-MANUAL-STEPS block verify/surface the end state; (c) `08` rung-C wording matches; (d) no em/en dashes; (e) `aw check-local-leaks .` clean; (f) full suite `python -m pytest -q` stays green (baseline 295 passed, 1 skipped - these are docs, so unchanged) - paste actual output.
- No unit tests (no code changed). If a future `aw`/verify helper checks release end state, it gets tests then.

## Spec / documentation sync

- `09-release-execution.md`, `08-final-ship-review.md` (the behavior spec itself).
- `DECISIONS.md` entry (Step 4); `RELEASING.md` if it describes the rungs.
- A reply to the ocman comms message in `.agents/comms/shared/sent/` (untrusted-input courtesy loop, D81).

## Open questions

- OQ1 (mechanism): `gh release create <tag> --latest` (no `--draft`) in one step, vs create-draft-then-`gh release edit --draft=false --latest`? Lean: single `gh release create ... --latest` on confirm (simpler; the confirm IS the deliberate act); fall back to create+edit only if notes/assets need staging first. Confirm at review or execution.
- OQ2 (this-repo timing): should this fix land BEFORE the imminent 1.3.0 release-review (so 1.3.0's own rung C ends published), or after? Lean: BEFORE - it directly improves the 1.3.0 cut and is low-risk prose. Human's call.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload (this IPD only EDITS the release-review instructions; it performs no release).

Recommended next steps:
1. Review this IPD (optionally `/plan-review`). Resolve OQ1/OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, sync docs, reply to ocman; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
