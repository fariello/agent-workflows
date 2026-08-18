# IPD: 256-color pretty output across all aw verbs by default on TTY

- Date: 2026-08-18
- Kind: child
- Concern: `aw` output is inconsistently colored: the `Term` class (term.py) already makes a correct color decision (`should_color`, term.py:56-80: honors NO_COLOR/FORCE_COLOR/TERM/isatty) and supports 256-color (`color256`, term.py:100), but roughly a dozen backend modules bypass `Term` entirely with raw `print`/`sys.stdout.write` (backlog.py, specs.py, ipd_lint.py, plans_index.py, plans_refs.py, plans_archive.py, research_*.py, ipd_authoring.py, leak_sanitizer.py) so their output is never colorized. The goal is for ALL `aw` verbs to emit pretty, 256-color output by default on a TTY and to fall back to plain text when NO_COLOR, `--no-color`, or a non-TTY pipe is in effect. Addresses TODO items #21 (colorize all output by default on a TTY) and #34 (make output visually pretty).
- Scope: IN: thread the shared `Term` (or an equivalent color flag) into the `run_*` entrypoints of the raw-print backend modules so every verb routes its output through the central color decision; apply a consistent 256-color style vocabulary (headings, ids, status/severity, paths, de-emphasis) to the main output surfaces. OUT: no change to the `should_color` policy itself (term.py:56-80) or to the existing `--no-color` flag on the shared `common` parent (cli.py:371); no new theming/config system; no change to machine-readable `--json`/`--agent` output (must stay uncolored).
- Status: draft
- Set: awcolor
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: u88tb7

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from TODO item #21/#34; route raw-print backends through Term and apply consistent 256-color styling so all aw verbs colorize on a TTY by default.

## Goal

Make every `aw` verb emit pretty, 256-color output by default on an interactive TTY, and cleanly plain
when NO_COLOR / `--no-color` / a pipe is in effect, by routing the raw-print backend modules through the
existing central `Term` color decision instead of bypassing it with raw `print`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: route all verbs through Term

- [ ] E-01 Thread the shared `Term` (or an equivalent color/style flag derived from it) into the `run_*` entrypoints of the backend modules that currently bypass it with raw `print`/`sys.stdout.write` (backlog.py, specs.py, ipd_lint.py, plans_index.py, plans_refs.py, plans_archive.py, research_*.py, ipd_authoring.py, leak_sanitizer.py) and replace their direct writes with `Term`-mediated output, so the central `should_color` policy (term.py:56-80) governs every verb's human-readable output.
  - Depends on: none
  - Expected outcome: running any of those verbs on a TTY produces colorized output; `--json`/`--agent` output is unchanged (still uncolored); no verb writes raw ANSI directly anymore.
  - Execution state: pending

### Task group 2: consistent 256-color styling + policy test

- [ ] E-02 Define a small, consistent 256-color style vocabulary (headings, ids/handles, status/severity, paths, de-emphasis) on top of `Term.color256` (term.py:100), apply it to the main human-readable output surfaces of the verbs touched in E-01, and add a test asserting that NO_COLOR / `--no-color` / a piped (non-TTY) stdout disables color while a forced TTY (FORCE_COLOR) enables it.
  - Depends on: E-01
  - Expected outcome: verb output is visually consistent and pretty on a TTY; the policy test passes for all four cases (NO_COLOR off, --no-color off, pipe off, FORCE_COLOR on).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Term.should_color` (term.py:56-80) already implements the full policy: `NO_COLOR` off, `FORCE_COLOR` on, else color only when `TERM` is capable AND stdout `isatty()`. This is the single source of truth; do not reimplement it per module.
- `Term.color256` (term.py:100) provides 256-color escapes; the style vocabulary should build on it, not on ad-hoc raw escapes.
- `--no-color` lives on the shared `common` parent parser (cli.py:371), so every verb already accepts it; the gap is that the backends never consult the resulting `Term`.
- Roughly a dozen backend `run_*` functions do not currently take a `term` argument and write with raw `print`/`sys.stdout.write`; threading `Term` in is the mechanical core of E-01.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Color decision + 256-color already exist centrally in `Term`. | No new policy code; the work is plumbing + styling, not decision logic. |
| F2 | ~12 backends bypass `Term` with raw writes. | E-01 is a threading/refactor across those modules; large blast radius but mechanical. |
| F3 | `--no-color` is already parsed on the shared parent. | Correct disable path exists; it just is not honored by the raw-print backends today. |
| F4 | `--json`/`--agent` output must stay machine-clean. | Styling must be gated so structured output is never colorized. |

## Proposed changes (ordered, validatable)

1. Thread `Term` into the raw-print backends and replace direct writes (E-01). 2. Add a shared 256-color style vocabulary on `Term.color256` and apply it to the main surfaces (E-02). 3. Add the on/off policy test covering NO_COLOR / `--no-color` / pipe / FORCE_COLOR (E-02).

## Deferred / out of scope (with reason)

- A user-configurable theme/palette system: out of scope; the goal is a sane default, not configurability.
- Changing `should_color` policy or the `--no-color` flag surface: out of scope; both are already correct.
- Coloring structured `--json`/`--agent` output: explicitly excluded (must remain machine-parseable).

## Scope check

- Over-scope: none - policy and flag are reused, not rebuilt.
- Under-scope: none - E-01 makes every verb colorize-capable; E-02 makes it pretty and proves the disable paths.

## Required tests / validation

The E-02 policy test (NO_COLOR / `--no-color` / pipe / FORCE_COLOR) plus a manual visual spot-check of the styled surfaces, and the full serial suite to confirm no regression in existing output-asserting tests.

## Spec / documentation sync

No spec change required; note the default-on-TTY color behavior in the relevant help text if it is not already implied by `--no-color`. Otherwise N/A.

## Open questions

### OQ-01: should there be an `AW_COLOR=always|auto|never` override in addition to NO_COLOR/`--no-color`?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: rely on the existing NO_COLOR/FORCE_COLOR/`--no-color` triad for this plan and defer a dedicated `AW_COLOR` env var unless a maintainer wants it; adding it later is additive and non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste output of at least three previously-raw-print verbs (e.g. `aw backlog`, `aw specs`, `aw ipd lint`) run on a TTY showing color, plus a grep/inspection confirming those modules no longer call raw `print`/`sys.stdout.write` for human output and instead go through `Term`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the passing policy test run covering the four cases (NO_COLOR disables, `--no-color` disables, piped stdout disables, FORCE_COLOR enables) and a before/after visual sample of a styled surface.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification and commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions the plan into
`executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`.
