# IPD: Verification / evidence layer (proof, not prose)

- Date: 2026-07-04
- Concern: trustworthiness (the single highest-leverage enterprise-grade gap)
- Scope: a new `verify` workflow + a helper that runs repo-native checks and captures
  real results; wiring so `release-review` and relevant `assess` lenses CITE that
  evidence instead of relying on LLM self-report.
- Status: EXECUTED 2026-07-04. See DECISIONS.md D33.

## Goal

Convert the toolkit from "the agent says the tests pass / it is secure" to "here is
machine-checkable evidence." Today the only deterministic tools are `scan_secrets.py`
(a real evidence-producing backstop for the secrets concern) and `setup-repo`'s
`setup_tools.py` (which detects/installs dev tools, i.e. it supports setup rather than
producing review evidence). Every review/assess claim about tests, coverage, lint,
build, type-check, or accessibility rests on the LLM's self-report. For enterprise
trust, claims that can be checked deterministically should be.

## Why this is the priority

An enterprise reviewer will not accept "the agent reviewed it and it is fine." The
value of `release-review`'s GO recommendation, and of most `assess` verdicts, is only
as strong as the evidence behind it. A verification layer is what makes the rest of the
toolkit credible.

## Proposed design

1. **A `verify` workflow + `tools/run_checks.py` helper** (extends the `scan_secrets.py`
   precedent: deterministic, read-only-by-default, honest about what it could not run).
   The helper:
   - **Discovers repo-native checks** rather than inventing them: test/lint/build/
     type-check commands from `package.json` scripts, `Makefile`, `pyproject.toml`/`tox`,
     CI workflow files, `justfile`, etc. (the same "use documented commands" discipline
     release-review already states).
   - **Runs the ones the user approves** and captures real output, exit codes, and
     (where available) coverage numbers into the run record as evidence.
   - **Is honest:** records what it ran, what it skipped and why (no test setup, needs
     services/credentials, unsafe), and never claims a check passed that it did not run.
2. **Safety (running untrusted repo commands is the core hazard):**
   - Do not run arbitrary commands silently. Present the discovered commands and get
     confirmation before executing (or a `--yes` for CI). Never run
     network/deploy/publish steps.
   - Time-bound and resource-bound; capture but do not act on failures.
   - Prefer read-only/`--dry-run` variants; clearly separate "ran it" from "would run
     it."
3. **Evidence format:** a structured record (`verify-results.json` + a readable summary)
   under the run record: per-check command, exit code, duration, key metrics
   (pass/fail counts, coverage %), and a truncated log excerpt.
4. **Wiring into existing workflows:** `release-review`'s validation and `assess-testing`
   (and where relevant others) should RUN `verify` (or cite its results) rather than
   self-reporting. The GO/CONDITIONAL-GO recommendation must reference actual evidence,
   and say so explicitly when a claimed check could not be verified.

## Scope check

- Over-scope: not a CI system, not a test runner of its own, not deployment. It runs the
  repo's OWN checks and records results. It does not write or fix tests (that stays with
  assess-testing / release-review implementation).
- Under-scope: the honesty requirement - "could not verify X" must be as prominent as
  "verified Y"; a partial run must never read as a full green.

## Dependencies / sequencing

- Prioritized first among the roadmap IPDs (trust-critical).
- Composes with the framework self-tests IPD (dogfood: the toolkit should verify itself).
- `assess-all` (the self-tests/assess-all IPD) rollup should incorporate verify evidence.

## Required validation

- On a repo with tests: `verify` discovers and runs them (with consent), records real
  pass/fail + coverage; a deliberately-broken test makes the evidence show failure.
- On a repo with no tests: `verify` records "no runnable checks found" honestly and does
  not imply success.
- Safety: no network/deploy commands run; confirmation required before execution;
  bounded runtime.
- release-review cites the evidence and downgrades its recommendation when checks are
  unverifiable.

## Open questions

1. Default interactivity: confirm-before-each-check (safe) vs. a `--yes` batch mode for
   CI. Probably both, defaulting to confirm.
2. How aggressively to auto-discover check commands vs. asking the user to name them.
3. Whether `verify` is its own command or a mode of `release-review`; leaning its own
   command so `assess-*` and CI can reuse it.

## Approval and execution gate

Proposal only, and the design has real safety surface (running repo commands) - it
should be plan-reviewed carefully before execution. Approve/reorder first.

## Execution record (2026-07-04)

Open questions resolved by the human:
- Q3 (shape): its own `/verify` command + reusable `verify/tools/run_checks.py`.
- Q1 (interactivity): confirm-before-each-check by default, plus a `--yes` "yes to all"
  batch mode; interactive default declines on no input.
- Q2 (discovery): auto-discover from package.json/Makefile/pyproject/tox/justfile/CI,
  propose, then confirm; `--add`/`--only` to override.
- Safety: allowlist (test/lint/build/typecheck) + hard denylist (network/deploy/publish/
  install/push/...) never run even under `--yes`; unclassified never auto-run; bounded.
- Deps: stdlib-only, matching scan_secrets.py.

Changes: `verify/tools/run_checks.py` (discovery, classify/deny, consent, bounded run,
metrics scrape, json/csv/text, `--version`/`--list`); `verify/verify.md` (protocol,
safety, run record, honesty); `index.md` `verify` row; release-review Section 03 and 08
(evidence-not-self-report + evidence gate on GO); assess testing lens (evidence, not
self-report); README + DECISIONS D33. Verified: discovery/denylist/pass/fail/no-checks/
interactive-decline all behave correctly; metric scraping hardened against banner false
positives; fresh install -> 8 shims/tool + `run_checks.py` copied; `--version` from the
installed copy. Dogfooded on this repo. Scope held (not a CI/test runner; no deploy; does
not write tests).
