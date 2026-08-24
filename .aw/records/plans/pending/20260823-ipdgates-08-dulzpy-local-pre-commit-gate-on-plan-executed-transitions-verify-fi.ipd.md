# IPD: Local pre-commit gate on plan executed-transitions (verify finalize receipt, no CI enforcement)

- Date: 2026-08-23
- Kind: child
- Concern: Order 07 makes the CLI path safe by DELEGATING `aw set executed` into `aw ipd finalize`, but it cannot cover the path where an agent NEVER touches the CLI: hand-editing a plan's `- Status:` to `executed` in an editor, or `git mv`-ing a plan into `executed/`, and then committing it with a raw `git commit`. That commit never runs finalize, so no receipt/scope-check/attribution happened - the exact p7dqwz-class bypass, just via the editor instead of the CLI. There is no gate on the COMMIT itself. This IPD adds a local pre-commit hook as defense-in-depth for that residual path.
- Scope: Add a LOCAL pre-commit hook (in the existing `.pre-commit-config.yaml` `repo: local` pattern, invoking a packaged `agent_workflows` entry point) that inspects the staged change and, when it detects a PLAN gaining `- Status: executed` (or its `done` alias) OR being moved into an `executed/` directory, verifies a matching consumed/complete finalize receipt exists in `.aw/state/` (the receipt Orders 03/04 produce); if absent/stale, REFUSE the commit with an actionable message pointing to `aw ipd finalize`. Touch: `.pre-commit-config.yaml`, a new `agent_workflows` hook entry point (e.g. `agent_workflows/hooks/executed_transition_gate.py` or a `cli` subcommand the hook calls), the installer/setup-repo path that writes `.pre-commit-config.yaml` (so fresh installs get the hook), and tests. Explicitly NO GitHub Actions / remote CI enforcement (human decision): this is LOCAL prevention only; the deterministic backstop is the LOCAL `proclint` detector (`79li67`) run via `aw check`/`aw doctor`, not a remote gate that fails after push.
- Status: draft
- Set: ipdgates
- Order: 8
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: dulzpy

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created at maintainer direction - a local pre-commit gate so an agent that "forgets" `aw ipd finalize` and hand-commits an executed-transition is still caught locally. Human decision: LOCAL only, NO remote CI.

## Goal

Add a local, best-effort pre-commit hook that refuses to commit a raw (non-finalize) plan-to-`executed` transition, so bypassing the finalize gate by hand-editing status / `git mv` + `git commit` is caught at commit time on the acting machine. The hook detects, in the STAGED diff, a plan file that (a) gained a `- Status: executed`/`done` line it did not have, or (b) moved into an `executed/` disposition directory; for each such plan it requires a matching finalize receipt in `.aw/state/` marked consumed/complete (proving `aw ipd finalize` ran and did the receipt-validation + scope reconciliation + attribution for THIS transition). Finalize's OWN lifecycle commit passes (its receipt is present/consumed); a raw hand-edited transition is REFUSED with `run 'aw ipd finalize <plan>' instead`. Honest framing: git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`, so this is a prevention layer, not an absolute gate; the deterministic local backstop is the `proclint` detector (`79li67`). There is deliberately NO remote/CI enforcement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The staged-diff detector + receipt check

- [ ] E-01 Implement a packaged `agent_workflows` hook entry point that, given the staged change (from `git diff --cached`), identifies each PLAN that in this commit either gained a `- Status: executed`/`done` line (compare staged vs HEAD) or was renamed into an `executed/` directory, and for each such plan verifies a matching finalize receipt in `.aw/state/` (per Order 03's location, e.g. `.aw/state/ipd-lifecycle/<id6>.receipt.json`) exists and is marked consumed/complete for THIS transition (plan id + digest match). Missing/stale/absent receipt -> exit nonzero with an actionable message naming the plan and `aw ipd finalize <plan>`. A plan carrying `Scope-Paths: grandfathered` (Order 02) or with no finalize machinery yet is handled per OQ-01 (grandfather/advisory), never a hard lock. Discriminate on `record_type == plans` (do NOT fire on prompts which share the `executed` token, nor on non-plan artifacts).
  - Depends on: none
  - Expected outcome: given a staged raw executed-transition with no matching receipt, the entry point exits nonzero and names the fix; given finalize's own transition (receipt present/consumed), it exits zero.
  - Execution state: pending

### Task group 2: Wire it as a local pre-commit hook + install it

- [ ] E-02 Register the entry point as a `repo: local` hook in `.pre-commit-config.yaml` (mirroring the existing local-leaks guard), scoped to the plan record paths, running once per commit; and update the installer/setup-repo path that writes `.pre-commit-config.yaml` so a fresh `aw install`/`setup-repo` includes the hook. Do NOT add any GitHub Actions / CI workflow (human decision: local only). Ensure the hook is a no-op (exit zero fast) when no plan executed-transition is staged, so it does not slow ordinary commits.
  - Depends on: E-01
  - Expected outcome: `git commit` of a raw executed-transition is refused locally; ordinary commits and finalize's own commit pass; fresh installs get the hook; no CI workflow is added.
  - Execution state: pending

### Task group 3: Prove the gate + grandfather + escape honesty

- [ ] E-03 Add tests: a fixture staging a hand-edited plan `- Status: executed` with NO matching receipt is REFUSED (nonzero, names `aw ipd finalize`); a fixture staging finalize's transition WITH a consumed receipt PASSES; a `git mv` of a plan into `executed/` without a receipt is REFUSED; a grandfathered (`Scope-Paths: grandfathered`) plan is NOT locked (per OQ-01); a prompt terminal `executed` transition and a non-plan artifact are NOT falsely gated; an ordinary commit with no plan transition is a fast no-op. Confirm `pytest -n auto` is green. Do NOT add a test that requires network/CI.
  - Depends on: E-01, E-02
  - Expected outcome: the raw-bypass commit is gated locally, finalize's commit passes, grandfathered/prompt/non-plan cases are not falsely gated, and no CI is involved.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `.pre-commit-config.yaml` already uses a `repo: local` hook that invokes the packaged `agent_workflows` (the local-leaks guard: "Scans the whole tracked tree ... via the packaged agent_workflows ... runs once per commit"). This is the exact pattern for a new local hook - reuse it, do not invent a new hook framework.
- The finalize receipt lives in gitignored `.aw/state/` (`.gitignore:52,60`), local-only and never committed. That is FINE for a pre-commit hook (which runs on the acting machine) but means the receipt CANNOT be verified remotely - hence local-only enforcement and no CI (human decision).
- Git hooks are local, not cloned by default, and skippable with `--no-verify`: this is a best-effort PREVENTION layer, not an absolute gate. The deterministic local backstop is the `proclint` detector (`79li67`, `aw check`/`aw doctor`).
- Order 07 delegates the CLI path into finalize; THIS order covers the raw-commit / hand-edit path Order 07 cannot. They are complementary, not duplicative.
- The `ipdgates` Set's own plans (and the other pre-cutoff Sets) are grandfathered (`Scope-Paths: grandfathered`, no receipt); the hook MUST grandfather them or it would lock this very Set from finalizing itself (mirrors Order 07's lockout handling).

## Findings

Order 07 closes the CLI bypass; this closes the COMMIT bypass (editor hand-edit + raw `git commit`), which is the residual path an untrained agent most naturally takes when it "forgets" the tool. Because the receipt is local, the honest reach of this hook is: on the acting machine, at commit time, best-effort. It is NOT unbypassable (`--no-verify`, fresh clone, CI absent by choice), so it is explicitly framed as prevention with the local `proclint` detector as the backstop - never oversold as a hard gate. False-positive avoidance matters: it must not fire on prompts (shared `executed` token), non-plan artifacts, grandfathered plans, or ordinary commits, or it trains people to `--no-verify` habitually (which would defeat it).

## Proposed changes (ordered, validatable)

1. Packaged staged-diff detector + `.aw/state/` receipt check for plan executed-transitions (E-01).
2. Register as a local `repo: local` pre-commit hook + include it in fresh installs; NO CI (E-02).
3. Tests: raw-bypass refused, finalize's commit passes, grandfathered/prompt/non-plan not gated, ordinary commit fast no-op (E-03).

## Deferred / out of scope (with reason)

- Any GitHub Actions / remote CI enforcement: EXPLICITLY OUT (human decision) - local prevention only; the local `proclint` detector (`79li67`) is the backstop, not a post-push CI failure.
- The finalize command, receipt, reconciliation, rollback, and CLI delegation themselves: Orders 03-07 (dependencies).
- Gating non-`executed` transitions or non-plan artifacts: out of scope; only the plan-to-`executed` commit is gated.
- Making the hook unbypassable: impossible for a local git hook by design; not attempted (honest limit).

## Scope check

- Over-scope: none. One local hook + its detector + install wiring + tests; no CI.
- Under-scope: none for the local commit gate; remote enforcement is deliberately excluded per human decision.

## Required tests / validation

- Tests per E-03 (raw-bypass refused; finalize's commit passes; git-mv-into-executed refused; grandfathered not locked; prompt/non-plan not gated; ordinary commit fast no-op).
- Full suite via `pytest -n auto` (paste actual runner output). No network/CI test.

## Spec / documentation sync

- Document the local hook in the IPD lifecycle spec / `.aw/system/workflows/ipd-lifecycle/` and the installer docs (via managed verbs): the plan-`executed` commit gate is LOCAL prevention, its backstop is `aw check`/`aw doctor` (proclint), and there is intentionally no CI enforcement. Note `--no-verify` bypasses it (honest limit).

## Open questions

### OQ-01: How does the hook treat a plan that has no finalize machinery / is grandfathered, and what exactly counts as a "consumed/complete" receipt?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). Two coupled points: (1) GRANDFATHER - a plan carrying `Scope-Paths: grandfathered` (Order 02) or transitioned before finalize shipped has no receipt; the hook must NOT hard-lock it (that would prevent this very Set, and the other pre-cutoff Sets, from ever finalizing). Options: (A) if the plan is grandfathered, allow the commit with an ADVISORY note (no receipt required); (B) require even grandfathered plans to have run a minimal `aw ipd finalize` that records an honest "no-receipt advisory" per D141's recovery path. (2) RECEIPT PREDICATE - what marks a receipt "consumed/complete for THIS transition": plan id + content digest match + a finalize-completed flag. The executor MUST get a human decision on the grandfather behavior (A vs B) and the exact receipt-consumed predicate before E-01, since together they define what the hook blocks vs allows. (A is likely right for the pre-cutoff grandfathered tree; new plans use B via the normal finalize path.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test drives the entry point on a staged hand-edited `- Status: executed` with NO matching `.aw/state/` receipt and asserts nonzero exit + a message naming `aw ipd finalize`; with a matching consumed receipt it exits zero; a `git mv` into `executed/` with no receipt is refused; discrimination on `record_type == plans` is asserted (a prompt `executed` transition is NOT gated).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the hook is present in `.pre-commit-config.yaml` as a `repo: local` entry scoped to plan paths; a real `git commit` of a raw executed-transition is refused and finalize's own commit passes; a fresh `aw install`/setup-repo writes the hook; NO GitHub Actions/CI workflow file was added (shown by absence); an ordinary commit with no plan transition is a fast no-op.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the full test set (raw-bypass refused, finalize passes, git-mv refused, grandfathered not locked per OQ-01, prompt/non-plan not gated, ordinary-commit no-op) passes; `pytest -n auto` is green (pasted); no network/CI test was introduced.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - a local pre-commit gate on raw plan-to-`executed` commits, verifying the finalize receipt, with no CI enforcement.

### Execution contract

1. Open questions RESOLVED: OQ-01 (grandfather behavior + receipt-consumed predicate) MUST be resolved by a human before E-01.
2. Scope fence: touch ONLY the new hook entry point, `.pre-commit-config.yaml`, the installer/setup-repo path that writes it, the tests, and the lifecycle/installer docs via managed verbs. Do NOT add any GitHub Actions / CI workflow (human decision: local only). Do NOT implement finalize/begin/rollback (Orders 03-06) or the CLI delegation (Order 07). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command. Do NOT claim the hook is unbypassable - it is local best-effort (`--no-verify` bypasses it).
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` (append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit); if the finalizer cannot finalize this plan, STOP and report. (Dogfood note: this plan's OWN finalize commit must pass the very hook it installs - a good end-to-end proof, provided the hook grandfathers this pre-cutoff plan per OQ-01.)
