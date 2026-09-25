# IPD: Make every aw doctor remediation command runnable as printed or explicitly advisory

- Date: 2026-09-25
- Kind: child
- Concern: `aw doctor` presents remediation commands as the fix, but several cannot succeed as printed: `aw rename <type> <path>` exits 2 (no mutation argument), and with `--slug` it only previews and exits 0 having written nothing, which reads as success; the `blocks-release-dangling` command exits 2 too.
- Scope: `agent_workflows/doctor.py` `build_remediation` branches that return a non-None `command`, plus the `resolve_next_actions` consumer; regression tests in `tests/test_doctor.py`. No change to `aw rename`, `aw group`, or `aw set` themselves.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 9yf5u9
- Blocks-Release: next
- Set: doctorhint
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6k7xot

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 9yf5u9; re-measured both rename failure modes plus the group and blocks-release commands in a throwaway repo against current code.

## Goal

Every `Remediation.command` that `aw doctor` emits (and that `resolve_next_actions` promotes to a next action) either succeeds exactly as printed or is `None`, with the required shape and the human judgement it needs carried in `summary_fix`/`detailed_fix`. That removes the false-completion path where an agent runs the recommended fix, gets exit 0, and nothing changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: honest remediations

- [ ] E-01 Make the `name-nonconformant` branch of `doctor.build_remediation` advisory: `command=None`; `summary_fix` and `detailed_fix` name the required shape `aw rename <type> <path> --slug <corrected-slug> --apply` and state that the corrected slug is a human decision (a truncated slug cannot be derived). This follows the `id6-identity-slot` branch, which already returns `command=None` for a judgement call.
  - Depends on: none
  - Expected outcome: `build_remediation(Drift(<backlog path>, "check.name-nonconformant", ...)).command is None`, and its `detailed_fix` contains both `--slug <corrected-slug>` and `--apply`.
  - Execution state: pending

- [ ] E-02 Make the `setid-collision` branch advisory in the same way: `command=None`, with `detailed_fix` naming `aw group <type> <path> --set <new-set-id> --apply`. It currently emits `aw group ... --set <new-set-id>`, which carries a placeholder and omits `--apply` (measured: `aw group backlog <f> --set newset` prints `--- would set metadata Set: newset ...`, exit 0, file unchanged).
  - Depends on: none
  - Expected outcome: `command is None`; `detailed_fix` contains `--apply`.
  - Execution state: pending

- [ ] E-03 Fix the `blocks-release-dangling` branch. It emits `aw {target_type} set {loc} --blocks-release next`, which exits 2 with `FAIL aw set: at least one target selector (id6, setid, or filename) is required.` (measured for both `backlog` and `specs`), because the setter needs a status. Make it advisory (`command=None`) with `detailed_fix` naming `aw <type> set <path> --status <current-status> --blocks-release next`. Do not auto-fill the current status: backlog `hg2oop` records that a same-status `aw backlog set` damages history, so a generated command must not route through that path.
  - Depends on: none
  - Expected outcome: `command is None`; `detailed_fix` contains `--status` and `--blocks-release next`.
  - Execution state: pending

- [ ] E-04 Add a family guard in `tests/test_doctor.py`: for a representative drift of every rule `build_remediation` handles, assert that any non-None `command` contains no `<`...`>` placeholder, and that any command starting with `aw rename` or `aw group` contains `--apply`. Also assert that `resolve_next_actions` returns no action for a drift set made only of the three rules above. Add per-branch tests for E-01..E-03. Remaining placeholder-bearing branches that the guard flags (`status-untooled` `aw set <status> <id6>` when the id6 is known from the filename, and the `git-dirty`/`git-staged` fallback `git commit -m "<msg>" -- <paths>`) are either given a concrete value when the drift supplies one, or set to `command=None` when it does not, so the guard passes.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the new tests pass with the fix and fail on the unfixed `doctor.py`.
  - Execution state: pending

- [ ] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: the summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The mutation verbs `aw rename` and `aw group` preview by default and need `--apply` (their `--help` reads "Apply the change (default is a preview)."). `aw index` is the opposite: it writes by default, so this plan does not add `--apply` to the `stale-index` command, which is already runnable.
- `Remediation.command` feeds three surfaces: the human `Fix:` line (via `summary_fix`), `--agent` diagnostics, and `resolve_next_actions`, which skips any remediation whose `command` is falsy. So `command=None` is the established way to say "advisory only".
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Reproduced 2026-09-25 in a throwaway repo (`/tmp/opencode/g3/probe-doctorhint/r`) against this worktree:

| Rule | Emitted command | As printed |
|---|---|---|
| `check.name-nonconformant` | `aw rename backlog <f>` | exit 2, `error: at least one of --slug, --set, or --order is required to rename` |
| same, with `--slug fixed` | | exit 0, `--- would rename ... ---`, file unchanged |
| `check.setid-collision` | `aw group backlog <f> --set <new-set-id>` | placeholder; with a value it previews only, exit 0, unchanged |
| `blocks-release-dangling` | `aw backlog set <f> --blocks-release next` | exit 2, "at least one target selector ... is required" (same for `specs`) |

`aw doctor` on the probe repo printed `Fix: aw rename backlog .aw/records/backlog/open/20260908-demo-01-aaa111-a-truncated-slug-.backlog.md`. The primary checkout currently has zero `name-nonconformant` findings, so the defect is latent here and live for any repository that has one.

## Proposed changes (ordered, validatable)

1. E-01..E-03: make the three branches advisory, each with a complete, correct command shape in `detailed_fix`.
2. E-04: a table-driven guard, so a future branch that emits an unrunnable command fails a test rather than shipping.

## Deferred / out of scope (with reason)

- Adding an "advisory" flag to `NextAction`, so that placeholder commands can be listed without being auto-run (backlog candidate fix 2). `command=None` already achieves the safety property using the existing mechanism.
  - Carrier-Declined: option 1 of the backlog item satisfies the defect and has in-function precedent (`id6-identity-slot`), and a new field would widen the `--agent` JSON contract for no additional correctness.
- `command_surface.py` declares `aw index` as `mutation_gate="dry_run_default"` although it writes by default (noted in the backlog item). That is a separate contract mismatch and changes no doctor output.
  - Carrier-Declined: not a doctor remediation defect; out of this bug's scope, and the item mentions it only as a caution for this fix.

## Scope check

- Over-scope: none.
- Under-scope: none. Every `cmd =` site in `build_remediation` is covered, either by E-01..E-03 or by the E-04 guard.

## Required tests / validation

New tests in `tests/test_doctor.py` (E-01..E-04), shown failing against the unfixed code, then the bare suite.

## Spec / documentation sync

N/A: no spec documents the per-rule remediation strings. The `--agent` JSON keeps its shape (`command` was already nullable).

## Open questions

### OQ-01: May `aw doctor` print a command a human must edit?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: The backlog item defers this as a UX decision. Resolved from repo precedent: `id6-identity-slot` already returns `command=None` for a judgement call, and `resolve_next_actions` treats `None` as advisory. The plan shows the editable shape only in the `Fix:` text and never as a `command`. A maintainer who prefers option 2 can say so at review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -m pytest -o addopts="" tests/test_doctor.py -k name_nonconformant -v`, showing the new test PASSED. Also paste the same command run with `agent_workflows/doctor.py` temporarily reverted (`git stash push agent_workflows/doctor.py` is NOT allowed in a shared checkout, so use a scratch copy of the pre-fix file on `PYTHONPATH`), showing it FAILED on `command is None`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pytest output for the `setid_collision` remediation test, showing it passed, and show that `detailed_fix` contains `--apply`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pytest output for the `blocks_release_dangling` remediation test, showing it passed. In the probe repo, paste the output of running the `detailed_fix` shape with a real status (`aw backlog set <f> --status open --blocks-release next --dry-run`), showing exit 0 and the `[blocking]` preview.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the pytest output for the family guard, showing it passed, and its failing output against the pre-fix `doctor.py` naming at least the `aw rename` and `aw group` commands.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run, showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit through `aw commit <this plan> -- agent_workflows/doctor.py tests/test_doctor.py`; never push. Move the plan to `executed/` via the lifecycle only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
