# IPD: Assess documentation - reconcile forward-facing docs with the post-D47-D50 reality

- Date: 2026-07-11
- Concern: documentation (accuracy/honesty; this project's core value, GUIDING_PRINCIPLES P2)
- Scope: whole project, forward-facing docs (README, ARCHITECTURE, CONTRIBUTING, index.md stamp,
  the `assess` harness example), plus two self-conformance (dogfooding) gaps the assessment
  surfaced. Run before a planned `/release-review`.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Run record: `workflow-artifacts/assess-documentation/20260711-173843/`

## Goal

Bring the forward-facing documentation back into honest agreement with what the code does after
D44-D50 (git-tag versioning + CLI + packaging; the five-state plan lifecycle; the
`YYYYMMDD-HHMM-NN-<slug>` filename convention + the `normalize_plan_names.py` tool; the
self-documenting `.agents/` tree READMEs). No blocker-level false claims were found; the drift is
concentrated in (a) tool-inventory counts that predate D48/D50, (b) two shipped features never
surfaced in README/ARCHITECTURE, (c) a stale example in the assess harness, and (d) this repo not
having re-run its own install/version-bake, so its tree and version stamp under-report reality.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P2 honest-docs is the governing principle for this
  concern; P3 self-documenting; P8 single-source).
- Plan lifecycle + naming: five states (`pending/executed/superseded/not-executed/reusable`, `done/`
  alias) named `YYYYMMDD-HHMM-NN-<slug>.md` (D45/D47/D48). This IPD is named accordingly.
- Ground truth checked against: `engine.py:1970` (`PLAN_LIFECYCLE_SUBDIRS`), DECISIONS D44-D50, the
  actual tool/lens/persona/shim files, `pyproject.toml`, and `git describe` (`v1.0.0-40-gf613346`).
- Framework-is-subject: this repo IS the product; `.agents/workflows/` is assessed as the product
  (explicit-subject exception), not excluded.

## Findings

Severity = documentation-honesty impact; Remediation Risk = the Fix-Bar gate. All fixes here are
Low Remediation Risk (doc edits / re-running the framework's own idempotent tooling).

| ID | Sev | RR | Persona | Area | Finding (evidence) |
|----|-----|----|---------|------|--------------------|
| D-1 | High | Low | novice | accuracy | `README.md:9` front-page says the framework is "plain instruction files plus **two small Python helpers**". Reality: 5 workflow tools (`scan_secrets`, `run_checks`, `bench_env`, `setup_tools`, `normalize_plan_names`) + `install-workflows.py` + the `agent_workflows/` package. Contradicts the same README's own later tool list. Stale since D33/D40/D48. |
| D-2 | Medium | Low | software-engineer | accuracy/completeness | `normalize_plan_names.py` (D48/D50) is absent from every top-level inventory: `README.md` "what's in this repo" (`:243-249`), `ARCHITECTURE.md` file tree (`:46-47`) and tool paragraph ("**four** Python tools", `:382-383`), and `CONTRIBUTING.md`. A whole tool with 8+ flags is invisible unless you open `setup-repo.md`. |
| D-3 | Medium | Low | stakeholder/novice | honesty (dogfooding) | This repo's own `.agents/plans/` has only `pending/ executed/ reusable/` on disk - `superseded/` and `not-executed/` are MISSING (`ls .agents/plans/`), and the Category-1 `.agents/README.md` / `.agents/plans/README.md` / per-bucket READMEs are absent. D47/D49 say `create_setup_artifacts`/`ensure_plans_readmes` scaffold these; this repo never re-ran its own installer since. The framework does not self-conform to its own D47/D49. |
| D-4 | Medium | Low | stakeholder | honesty (dogfooding) | `index.md:3-4` hard-codes `WORKFLOWS-VERSION: 1.0.0` / `Version: 1.0.0`, but HEAD is `v1.0.0-40-gf613346` (40 commits past the tag). This is the exact "stale value masquerading as authoritative" state D44/D50 warn against; `make version-file` has not been re-run since the tag. (The live resolver self-corrects to `1.0.1.devN`, so this is the baked stamp only.) |
| D-5 | Medium | Low | software-engineer | accuracy (self-contradiction) | `assess/assess.md:124-126` "Write the IPD" step still gives the example name `<plans-pending>/YYYY-MM-DD-assess-<concern>.md` (old hyphenated, no HHMM-NN) - contradicting the same file's Step 0 (`:91`) and D48. This is the instruction an agent follows, so it yields non-conforming filenames. |
| D-6 | Medium | Low | novice | accuracy | Python floor mismatch: `pyproject.toml:10` `requires-python = ">=3.8"` while `README.md:17,200` promise "Python 3.9+" and CI provisions only 3.9/3.13 (3.8 "not provisioned", `tests.yml`). pip permits 3.8; docs promise 3.9. Pick one (recommend tighten metadata to `>=3.9`, or soften the docs and keep 3.8 as best-effort - align with the DECISIONS D46 "3.8 floor" wording either way). |
| D-7 | Medium | Low | software-engineer | completeness | `CONTRIBUTING.md:52-65` self-tests section names only `install-workflows.py`, `scan_secrets.py`, `run_checks.py` and describes coverage for installer/scanner/check-runner only. Reality: `tests/` has 14 modules (incl. `test_normalize_plan_names`, `test_cli`, `test_config`, `test_discovery`, `test_term`, `test_versioning`, `test_packaging`, `test_setup_artifacts`, `test_dir_readmes`, `test_bench_env`, `test_setup_tools`). |
| D-8 | Low-Med | Low | novice | completeness | The self-documenting `.agents/` tree feature (D49: a README in every top-level dir) is shipped but not mentioned in README/ARCHITECTURE as a feature of `aw install`. Silent omission, not a false claim. |
| D-9 | Low | Low | novice | consistency | `README.md:98` prose says "Thirteen core workflows ... plus two parameterized commands `/assess` and `/advise`", but the Core-workflows table (`:113-126`) has 14 rows and lists `/advise` as a core workflow. Internal count/inclusion inconsistency. |
| D-10 | Low | Low | software-engineer | consistency | `scaffold.md:87-88` still shows `python3 .../install-workflows.py` examples rather than the preferred `aw` path. Acceptable for a dev/authoring workflow, but slightly behind the D46 `aw`-first guidance. |

Explicitly verified ACCURATE (no change): the five-state lifecycle + retirement convention in
`AGENTS.md`, `assess.md` Step 0, `ipd.md`, `setup-repo.md`, `index.md`; the filename convention at
those sites; the CLI verbs/aliases and pip/pipx/wheel/zero-dep packaging claims vs `pyproject.toml`
and `cli.py`; git-tag semver description; cross-OS CI matrix; the 29 assess concerns, 7 personas,
16 shims; all internal file references resolve. The three-state model is fully gone from
forward-facing docs.

## Proposed changes (ordered, validatable)

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| 1 | D3,D4 | RE-RUN the framework's own tooling to self-conform FIRST (dogfood): `python3 -m agent_workflows install .` (creates the missing `.agents/plans/{superseded,not-executed}/` + the `.agents/` and `.agents/plans/*` READMEs, no-clobber, staged), then `make version-file` on the tagged/decided release commit to refresh `VERSION` + the `index.md` stamp. NOTE: the version stamp fix is entangled with the release decision (bump to v1.0.1?) - if a release is imminent, do the tag+bake as part of that; otherwise refresh the stamp to the resolver's current value so it stops asserting a bare `1.0.0`. | `.agents/plans/*`, `.agents/*README`, `VERSION`, `index.md` | Low | `ls .agents/plans` shows five dirs; `normalize_plan_names.py --check` still clean; version stamp no longer a bare `1.0.0` at +40. |
| 2 | D1 | Fix `README.md:9`: replace "two small Python helpers" with an accurate, count-free phrasing (e.g. "plus a few small dependency-free Python tools and an installer/CLI") that will not re-stale. | README.md | Low | grep: no "two small Python helpers"; matches the later tool list. |
| 3 | D2 | Add `normalize_plan_names.py` to the tool inventories: `README.md` what's-in-this-repo, `ARCHITECTURE.md` file tree (`setup-repo/tools/`) and the tool paragraph (four -> five; name it), and a mention in `CONTRIBUTING.md`. Keep counts accurate or count-free. | README.md, ARCHITECTURE.md, CONTRIBUTING.md | Low | grep: `normalize_plan_names` present in all three; ARCHITECTURE says five tools and lists them. |
| 4 | D5 | Fix the `assess.md` IPD-naming example to `<plans-pending>/YYYYMMDD-HHMM-NN-assess-<concern>.md` (matching its own Step 0 and D48). | assess/assess.md | Low | grep: no `YYYY-MM-DD-assess` example remains; example matches the convention. |
| 5 | D6 | Resolve the Python-floor mismatch: decide 3.8 vs 3.9 and make `pyproject.toml requires-python`, README, and DECISIONS wording agree. (Recommend `>=3.9` in metadata to match CI + README, noting 3.8 best-effort; or explicitly keep `>=3.8` and soften README to "3.8+ best-effort, 3.9+ verified".) | pyproject.toml, README.md, DECISIONS | Low | the three sources state the same floor. |
| 6 | D7 | Update `CONTRIBUTING.md` self-tests section: list the current tool set (or make it count-free) and note the full `tests/` suite (`python3 -m unittest discover -s tests -t .`), not just three tools. | CONTRIBUTING.md | Low | grep: mentions normalize_plan_names + the discover command; no "three tools only" framing. |
| 7 | D8 | Add a short mention of the self-documenting `.agents/` tree (READMEs created on install) to README and/or ARCHITECTURE. | README.md, ARCHITECTURE.md | Low | grep: the feature is described. |
| 8 | D9 | Reconcile `README.md:98` count vs the Core-workflows table (make the prose and table agree on what "core" includes and the number). | README.md | Low | prose count matches the table rows. |
| 9 | D10 | Update `scaffold.md` examples to the `aw` path (or note both). | scaffold/scaffold.md | Low | grep: `aw` path shown. |
| 10 | - | DECISIONS entry (D51) recording this documentation reconciliation + the self-conformance re-run. | DECISIONS.md | Low | entry present, dated, em-dash-free. |

## Deferred / out of scope

- The actual **version bump / release** decision (cut `v1.0.1`, tag, release notes) is a RELEASE
  action, not a doc fix. Step 1's stamp refresh is entangled with it; if you are about to release,
  fold the tag+`make version-file` into that. Recorded as a sequencing note, not a Remediation-Risk
  deferral. (This assessment runs BEFORE `/release-review`, which will address release readiness.)
- No content-rewrite of DECISIONS dated entries or `workflow-artifacts/` (append-only history, P4).

## Scope check

- Over-scope guard: no doc rewrites beyond correcting drift; keep fixes concise/count-free to resist
  re-staling (Complexity axis). Not adding new docs beyond the D8 feature mention.
- Under-scope guard: the dogfooding gaps (D3/D4) are included because "honest docs" for THIS project
  includes the repo self-conforming to its own shipped conventions - leaving them would be the
  dishonesty the concern is about.

## Required tests / validation

- After Step 1: `ls .agents/plans/` shows all five lifecycle dirs; `.agents/README.md` +
  `.agents/plans/README.md` + per-bucket READMEs exist; `normalize_plan_names.py --repo . --check`
  stays clean; `python3 -m unittest discover -s tests -t .` green (169 tests).
- Doc greps for each fixed claim (per-step validation column).
- em-dash sweep = 0 on every changed authored file.
- No behavior/code change beyond re-running the framework's own idempotent install + version bake;
  the suite must remain green.

## Spec / documentation sync

This IPD IS the doc-sync. DECISIONS gains D51 (Step 10). No user-visible workflow behavior changes.

## Open questions

1. Release intent (blocks Step 1's stamp half): cut `v1.0.1` now (tag + `make version-file` +
   release notes) so the stamp becomes an honest `1.0.1`, or just refresh the stamp to the current
   dev-resolver value and defer the release to after `/release-review`?
2. Python floor (D6): tighten `requires-python` to `>=3.9`, or keep `>=3.8` and soften the README to
   "3.9+ verified, 3.8 best-effort"?

## Approval and execution gate

This IPD is a proposal; it MUST be human-approved before execution and is NOT auto-run. On approval:
execute steps 1-10 (Step 1's version-bake half gated on OQ1), run the validation, then move this IPD
to `.agents/plans/executed/`. This assessment does not execute the plan.
