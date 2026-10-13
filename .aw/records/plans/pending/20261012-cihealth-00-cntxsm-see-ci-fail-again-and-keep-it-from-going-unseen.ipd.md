# IPD: See CI fail again and keep it from going unseen

- Date: 2026-10-12
- Kind: orchestrator
- Concern: GitHub CI (`.github/workflows/tests.yml`) has failed on every push since 2026-09-27: the last green run is `f69ad318a`, and 1,623 first-parent commits have landed on main since (measured 2026-10-12 with `gh run list --workflow tests.yml`). Nothing on this machine reads CI, so nobody saw it. Separately, plan `l85xvi` proposed gating stale spec line pointers in CI, which would add one more check that nobody sees.
- Scope: Coordinates four children. Order 01 makes CI pass again. Order 02 adds a periodic checkup (every N main commits, default 100) that reads CI's result and runs slow checks, shown by `aw attention` and `aw doctor`. Order 03 makes runs refuse to start new work when CI has not passed in N commits, with an override. Order 04 refuses to merge a lane that makes a spec line pointer stale, replacing `l85xvi`'s CI step.
- Scope-Paths: .aw/records/plans/pending/20261012-cihealth-00-cntxsm-see-ci-fail-again-and-keep-it-from-going-unseen.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: dff6b6f0823dd2d14d98fbc6a9842ec515921900e761b8e06bdd5257f43753ea
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 0
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: cntxsm

## Workflow history
- 2026-10-12 coverage pass (aw oc run): fingerprint dff6b6f0823d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 coverage pass (aw oc run): fingerprint 42fdec4fde44, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix, from the maintainer's design ruling of 2026-10-12 (periodic checkup every 100 commits, shown in aw attention/doctor, overridable hard stop, stale pointers gated at the runner merge check).
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

CI passes again, and from then on a failing CI is shown to the maintainer within 100 commits of main without anyone visiting GitHub, and blocks new run work until it is fixed or deliberately overridden.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: children

- [ ] E-01 CONFIRM ezyb4a REACHED executed
  - Depends on: none
  Confirm child 01 (`ezyb4a`, make CI pass again) reached `executed`, with a green `tests.yml` run on main.
  - Expected outcome: `ezyb4a` is under `plans/executed/`; `gh run list --workflow tests.yml` shows a `success` run for a main commit at or after its merge.
  - Execution state: pending

- [ ] E-02 CONFIRM n7xlhm REACHED executed
  - Depends on: E-01
  Confirm child 02 (`n7xlhm`, periodic checkup) reached `executed`.
  - Expected outcome: `n7xlhm` is under `plans/executed/`; `aw attention` prints a checkup line.
  - Execution state: pending

- [ ] E-03 CONFIRM s4z5n8 REACHED executed
  - Depends on: E-02
  Confirm child 03 (`s4z5n8`, hard stop with override) reached `executed`.
  - Expected outcome: `s4z5n8` is under `plans/executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM mnwkqu REACHED executed
  - Depends on: none
  Confirm child 04 (`mnwkqu`, merge-check gate on stale spec pointers) reached `executed`.
  - Expected outcome: `mnwkqu` is under `plans/executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `ezyb4a` | `20261012-cihealth-01-ezyb4a-make-ci-pass-again-on-every-leg.ipd.md` | Fixes the install, test, type-check and records failures so every `tests.yml` job passes. | none |
| 02 | `n7xlhm` | `20261012-cihealth-02-n7xlhm-run-a-periodic-checkup-every-n-commits-and-show-its-result.ipd.md` | Every N main commits, one run reads CI's latest result from GitHub and runs the slow checks; saves it; `aw attention` and `aw doctor` show it. | none |
| 03 | `s4z5n8` | `20261012-cihealth-03-s4z5n8-stop-starting-new-run-work-when-ci-has-not-passed-in-n-commi.ipd.md` | Runs refuse to start new work when CI has not passed in N commits, unless `--allow-red-ci "<why>"`; CI-repair plans always run. | `executed:n7xlhm, executed:ezyb4a` |
| 04 | `mnwkqu` | `20261012-cihealth-04-mnwkqu-refuse-to-merge-a-lane-that-makes-a-spec-line-pointer-stale.ipd.md` | At the runner's merge check, refuses a lane that makes a spec line pointer stale; replaces `l85xvi`. | `executed:fz3i3m` |

Order 04 waits on `fz3i3m` (Set `sbh1o1`), which makes the detector accurate. Order 03 must not ship before Order 01: shipping the hard stop while CI is red would stop every run.

## Completion criteria (the whole Set is done only when)

- CI passes on main. OWNER: `ezyb4a`.
- `aw attention` and `aw doctor` show the last checkup and CI state, refreshed at most every N main commits by exactly one of any number of parallel runs. OWNER: `n7xlhm`.
- A run refuses to start new work when CI has not passed in N commits, records an override reason when given one, and always lets a CI-repair plan run. OWNER: `s4z5n8`.
- A lane that makes a spec line pointer stale is not merged. OWNER: `mnwkqu`.

## Cross-IPD validation

- ONE NUMBER, ONE PLACE. Orders 02 and 03 read the same setting (`ci_checkup_interval_commits` in `.aw/config/project.json`, default 100) and the same saved checkup record. Order 03 does not read GitHub itself. OWNER: `s4z5n8` V-items demonstrate it.
- THE STOP CANNOT BLOCK ITS OWN FIX. Order 03's always-allowed set includes this Set's plans. OWNER: `s4z5n8`.

## Deferred / out of scope (with reason)

- Running the full CI matrix locally: CI is the place for other OSes and Pythons; this Set makes its result visible instead.
  - Carrier-Declined: the checkup reads CI's real result, which is the cross-platform answer.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

NONE OWNED BY THIS PLAN: each child carries its own tests and the bare suite. This plan confirms each child executed (E-01..E-04).

## Spec / documentation sync

N/A here; each child records its own.

## Open questions

### OQ-01: Where should stale spec pointers be gated, given nobody watches CI?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: At the runner's merge check (Order 04), plus the periodic checkup (Order 02) for changes made by hand; not in CI alone (maintainer, 2026-10-12, during /plan-review of Set gradfix). This answers plan `l85xvi` OQ-01, which is retired as superseded by this Set.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the pasted `- Status: executed` line of `ezyb4a` and the `gh run list` row showing `success` for a main commit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted `- Status: executed` line of `n7xlhm` and an `aw attention` excerpt with the checkup line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted `- Status: executed` line of `s4z5n8`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted `- Status: executed` line of `mnwkqu`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Order 01 first; Order 03 after Orders 01 and 02; Order 04 is independent of the others. This plan is retired by the runner once all four children are `executed`.
