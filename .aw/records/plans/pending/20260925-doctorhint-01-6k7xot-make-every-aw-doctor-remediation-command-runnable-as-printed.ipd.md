# IPD: Make every aw doctor remediation command runnable as printed or explicitly advisory

- Date: 2026-09-25
- Kind: child
- Concern: `aw doctor` presents remediation commands as the fix, but five branches cannot succeed as printed: `aw rename <type> <path>` exits 2 (no mutation argument) and, for `plans`, refuses a path selector outright; `aw group ... --set` previews only and, without `--rename`, trades one finding for another; the `blocks-release-dangling` command exits 2 and can name the non-existent `aw plans`; the `status-untooled` command exits 0 reporting success while leaving the finding in place; and `git-dirty`/`git-staged` emit a runnable raw `git commit` that breaches the repository's `aw commit` contract.
- Scope: `agent_workflows/doctor.py` `build_remediation` branches that return a non-None `command`, their paired `summary_fix` strings, plus the `resolve_next_actions` consumer; regression tests in `tests/test_doctor.py`. No change to `aw rename`, `aw group`, `aw set`, or any checker.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 9yf5u9
- Blocks-Release: next
- Set: doctorhint
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6k7xot

## Workflow history
- 2026-09-25 reviewed (aw set): plan-review: 12 findings (1 BLOCKER, 4 HIGH, 4 MEDIUM, 3 LOW), all FIXED in place; 5 decisions recorded; added E-04/E-05 for two unaddressed branches and corrected four prescribed command shapes that were measured wrong
- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 all FIXED; readiness go-pending-approval; record `.aw/records/reviews/20260925-doctorhint-01-6k7xot-make-every-aw-doctor-remediation-command-runnable-as-printed.review.md`

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 9yf5u9; re-measured both rename failure modes plus the group and blocks-release commands in a throwaway repo against current code.

## Goal

Every `Remediation.command` that `aw doctor` emits (and that `resolve_next_actions` promotes to a next action) either succeeds exactly as printed or is `None`, with the required shape and the human judgement it needs carried in `summary_fix`/`detailed_fix`. That removes the false-completion path where an agent runs the recommended fix, gets exit 0, and nothing changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: honest remediations

- [ ] E-01 Make the `name-nonconformant` branch of `doctor.build_remediation` advisory: `command=None`; `summary_fix` and `detailed_fix` name the required shape and state that the corrected slug is a human decision (a truncated slug cannot be derived). This follows the `id6-identity-slot` branch, which already returns `command=None` for a judgement call.

  THE ADVISORY SHAPE MUST SELECT BY id6, NOT BY PATH, and this is a correction to the shape this plan was authored with. `aw rename plans` routes to `plans_refs.run_mv` (`artifact_types.backend_name("plans", "rename")`), whose resolver is ID-DIRECTED: it calls `plans_refs._find_plan_by_id` and refuses a path with `error: no plan has Id '<path>'` (`plans_refs.py:504`). Measured 2026-09-25 on a scratch repo, `aw rename plans <relative path> --slug newslug` and the same with an ABSOLUTE path both exit 2, while `aw rename plans <id6> --slug newslug` exits 0 and prints the target name. `backlog` and `specs` route to `artifact_rename.run_rename_generic` instead and DO accept a path, so a single path-shaped hint is correct for two of the three types this branch can emit and refuses for the third. The repository already settled this exact question in `check_engine._identity_rename_hint`, whose docstring states the selector is the declared id6 "wherever one exists" precisely because "a suggested command that refuses is worse than no suggestion". Follow that precedent: prefer the record's declared `- Id:` and fall back to the path only when the record declares no id6.

  Derive the id6 from the filename identity slot when the name carries one (`check_engine._filename_setid`'s sibling `_naming.parse_clustered`), since the drift location is all this function receives; when no id6 can be derived, the hint keeps the path. The `detailed_fix` states the shape `aw rename <type> <id6-or-path> --slug <corrected-slug> --apply`.

  SECOND CORRECTION: `--slug` ALONE DOES NOT ALWAYS RESTORE CONFORMANCE, so the advisory text must not promise that it does. Measured against `check_engine._load_normalizer().is_conformant`: renaming `20260908-demo-01-aaa111-a-truncated-slug-.backlog.md` with `--slug corrected-slug` yields a CONFORMANT name, but a FREE-FORM name (`weird.ipd.md`, `notes.spec.md`) hits `compute_target_name`'s free-form fallback (`artifact_rename.py`, "Free-form filename fallback") and yields a bare `corrected-slug.md`, which is STILL nonconformant. A free-form name needs `--to-id6` (the conversion mode), not `--slug`. So the `detailed_fix` must name `--to-id6 --apply` for a name carrying no id6 and `--slug <corrected-slug> --apply` for a clustered name whose slug is merely wrong, exactly the two-branch distinction `_identity_rename_hint` already draws on its `modern` argument.
  - Depends on: none
  - Expected outcome: `build_remediation(Drift(<backlog path>, "check.name-nonconformant", ...)).command is None`. For a CLUSTERED location the `detailed_fix` names the declared/filename id6 as the selector (not the path) plus `--slug <corrected-slug>` and `--apply`; for a FREE-FORM location it names `--to-id6 --apply`. No emitted `detailed_fix` names `aw rename plans <path>`, the form measured to exit 2.
  - Execution state: pending

- [ ] E-02 Make the `setid-collision` branch advisory in the same way: `command=None`, with a `detailed_fix` naming a shape that actually leaves the repository clean. It currently emits `aw group ... --set <new-set-id>`, which carries a placeholder and omits `--apply` (measured: `aw group backlog <f> --set newset` prints `--- would set metadata Set: newset ...`, exit 0, file unchanged).

  THE SHAPE MUST CARRY `--rename`, NOT ONLY `--apply`, and this is a correction to the shape this plan was authored with. `aw group <type> <path> --set newset --apply` WITHOUT `--rename` rewrites the `- Set:` metadata and LEAVES THE FILENAME'S setid segment untouched, because `run_group_generic` only computes a new name when `rename_files` is set (`artifact_rename.run_group_generic`, `rename_files = bool(getattr(args, "rename", False))`). Measured 2026-09-25 on a two-record scratch repo: the prescribed shape cleared `check.setid-collision` and IMMEDIATELY RAISED `check.identity-absent-from-name` on the same file, so the recommended fix trades one finding for another rather than resolving it. Adding `--rename` renames `20260908-demo-01-aaa111-x.backlog.md` to `20260908-newset-01-aaa111-x.backlog.md` and leaves BOTH rules clean. So the advisory shape is `aw group <type> <selector> --set <new-set-id> --rename --apply`. This matches `check_engine._identity_rename_hint`, which already emits `aw group <type> <selector> --set <setid> --rename --apply` for the `Set` field for exactly this reason.

  APPLY THE E-01 SELECTOR RULE HERE TOO: `aw group plans` routes to `plans_refs.run_set_assign`, the same id-directed backend family, and `aw group plans <path> --set newset` was measured to exit 2 with `no plan has Id '<path>'`. Prefer the id6.
  - Depends on: none
  - Expected outcome: `command is None`; `detailed_fix` contains `--set`, `--rename` and `--apply`, and names an id6 selector rather than a path for the `plans` case.
  - Execution state: pending

- [ ] E-03 Fix the `blocks-release-dangling` branch. It emits `aw {target_type} set {loc} --blocks-release next`, which exits 2 with `FAIL aw set: at least one target selector (id6, setid, or filename) is required.` (measured for both `backlog` and `specs`; the refusal is `status_set.py:1628`, reached because the first positional is consumed as the STATUS and nothing remains as a selector). Make it advisory (`command=None`) with `detailed_fix` naming `aw <type> set <path> --status <current-status> --blocks-release next`.

  `target_type` COMES FROM `_infer_artifact_type` AND CAN BE A TYPE WITH NO `set` VERB, which the current string does not account for. `releases.check_blocks_release` scans `backlog`, `specs` AND `plans`, so a dangling gate on a PLAN emits `aw plans set ...`; measured 2026-09-25, `aw plans ...` exits 2 with `invalid choice: 'plans'`, because the plan spelling is `aw ipd set`. Of the nine types `_infer_artifact_type` can return, only `specs`, `backlog` and `prompts` declare a `set` verb (`command_surface._DECLARATION_INDEX`). So the `detailed_fix` must map `plans` to `aw ipd set <selector> --blocks-release next` (which takes no `--status` and accepts the gate flag directly) and must not invent an `aw <type> set` for a type that has none; fall back to prose naming the field to edit.

  THE `hg2oop` CAUTION THIS PLAN CITES DOES NOT APPLY TO THE SHAPE IT RECOMMENDS, and saying so matters because the plan currently forbids auto-filling the status on that basis. `hg2oop` was CORRECTED ON THE DAY IT WAS FILED (see its own "CORRECTED 2026-09-10" section): the history truncation is a deliberate design, the live defect is that the durable sidecar is gitignored, and the remedy is not a change to this path. Measured 2026-09-25 against current code on a three-record item, the prescribed `aw backlog set <path> --status open --blocks-release next` PRESERVED all three records and prepended a fourth, and it correctly rewrote `- Blocks-Release: nosuchrelease` to `next`, clearing the drift. Keep `command=None` anyway, for the reason that actually holds: `<current-status>` is a value this function cannot read from a `Drift` (which carries only location, rule and detail), so the command still cannot be emitted complete. Replace the `hg2oop` justification with that one rather than repeating a corrected claim.
  - Depends on: none
  - Expected outcome: `command is None`; `detailed_fix` contains `--blocks-release next`, names `--status` for a `backlog`/`specs` location, names `aw ipd set` for a `plans` location, and names no `aw <type> set` for a type that declares no `set` verb.
  - Execution state: pending

- [ ] E-04 Make the `status-untooled` branch advisory. This is a SEPARATE defect from E-01..E-03 and is the one that most directly defeats this plan's Goal, so it gets its own item rather than the passing mention E-04 originally gave it.

  It emits `aw set {status_word} <id6>`. The status word is real (extracted from the detail), so the only placeholder is the id6, and for a clustered filename that id6 IS derivable. The original plan therefore proposed filling it in. THAT IS THE WRONG REMEDY, because the completed command still does not clear the finding. Measured 2026-09-25 end to end on a scratch repo: a plan hand-edited from `to-review` to `approved` and staged raises `check.status-untooled`; running the completed `aw set approved aaa111` exits 0, reports success, writes `- 2026-09-25 same-status (aw set): status unchanged (approved)`, and the drift is STILL PRESENT on re-check. The cause is a genuine disagreement between two shipped components: `status_set.apply_status_change` tags a write whose old status already equals the target as `same-status` (its own docstring says so), while `check_engine._has_matching_history_line` only accepts a line whose status token EQUALS the new status. A hand-edited `- Status:` is by definition already at the target, so the recommended fix can only ever produce the one tag the checker rejects.

  So this branch is the exact false-completion path the Goal names, and completing the command would make it WORSE by turning an obviously-unrunnable placeholder into a plausible command that silently does not work. Set `command=None` and make `detailed_fix` state the two-step recovery the check's own detail implies: revert the hand edit (so the status returns to its previous value), then apply the transition with `aw ipd set <status> <id6>` so a genuine transition record is written. Do NOT attempt to fix `apply_status_change` or `_has_matching_history_line` here; that is a behavior change outside this plan's `Scope-Paths` and is recorded under "Deferred / out of scope" below.
  - Depends on: none
  - Expected outcome: `build_remediation(Drift(<plan path>, "check.status-untooled", "... changed to 'approved' ...")).command is None`; `detailed_fix` names reverting the hand edit AND `aw ipd set`.
  - Execution state: pending

- [ ] E-05 Make the `git-dirty` and `git-staged` branches advisory. Both currently emit a runnable `git commit -m "Update" -- <path>` whenever the drift location is a real path (measured: `doctor.git-dirty` on `some/file.md` yields exactly that), falling back to a placeholder `git commit -m "<msg>" -- <paths>` only for the `<git>` sentinel.

  The concrete form is the more dangerous of the two, because it IS runnable as printed and `resolve_next_actions` promotes it to a `Next` action an agent may execute. Running it violates the repository's execution contract three ways at once: `AGENTS.md` requires committing through `aw commit` and states raw `git commit` obliges an explicit report; the message `Update` is not a conforming commit message; and in a shared checkout a bare commit of a path an agent did not modify sweeps a co-worker's work into its commit, which is the exact loss `AGENTS.md`'s "BEFORE EVERY COMMIT" section exists to prevent. A dirty working tree is also not a defect with a single mechanical remedy: whether to commit, stash or discard is a human decision, which is the same reasoning the neighbouring `git-untracked` and `git-conflict` branches already use to return `command=None`.

  Set `command=None` on both and have `detailed_fix` name `aw commit` as the tooled path, state that the paths must be reviewed first, and keep the existing advice to inspect the changes. This aligns these two branches with their two already-advisory siblings.
  - Depends on: none
  - Expected outcome: `command is None` for both `doctor.git-dirty` and `doctor.git-staged`, for a real path AND for the `<git>` sentinel; no emitted `command` anywhere in the module starts with `git commit`.
  - Execution state: pending

- [ ] E-06 Add the family guard in `tests/test_doctor.py`. For a representative drift of every rule `build_remediation` handles, assert that any non-None `command`: contains no `<`...`>` placeholder; does not start with `git commit`; and, when it starts with `aw rename` or `aw group`, contains `--apply`. Assert that `resolve_next_actions` returns no action for a drift set made only of the five rules made advisory by E-01..E-05. Add per-branch tests for E-01..E-05, including the two-branch `name-nonconformant` case (clustered name gets `--slug`, free-form name gets `--to-id6`) and the `plans` case of `blocks-release-dangling` (names `aw ipd set`, never `aw plans set`).

  Enumerate the rules from a table in the test rather than by scraping `doctor.py`, and include a rule id for every branch listed in this plan's Findings table plus `id6-identity-slot`, `summary-unsafe`, `stale-index`, `setup-needed`, `layout-split-brain`, `pypi-update-available`, `version-`, `leak-`, `git-untracked`, `git-conflict` and the generic fallback. That makes the guard a real family check rather than a check of the branches this plan happened to touch, which is the property that stops the next added branch from reintroducing the defect.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the new tests pass with the fix and fail on the unfixed `doctor.py`.
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: the summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The mutation verbs `aw rename` and `aw group` preview by default and need `--apply` (their `--help` reads "Apply the change (default is a preview)."). `aw index` is the opposite: it writes by default, so this plan does not add `--apply` to the `stale-index` command, which is already runnable.
- `Remediation.command` feeds three surfaces: the human `Fix:` line (via `summary_fix`), `--agent` diagnostics, and `resolve_next_actions`, which skips any remediation whose `command` is falsy. So `command=None` is the established way to say "advisory only".
- ADDED AT REVIEW: `rename`/`group` DO NOT SHARE ONE BACKEND ACROSS TYPES. `artifact_types.backend_name` routes `plans` and `research` to the id-directed `plans_refs`/`research_refs` `run_mv`/`run_set_assign`, and `specs`/`backlog` to the path-tolerant `artifact_rename.run_rename_generic`. Any generated hint must therefore prefer the id6 selector, which works for every type; a path works for only some. `check_engine._identity_rename_hint` is the in-repo precedent and its docstring explains why ("a suggested command that refuses is worse than no suggestion").
- ADDED AT REVIEW: `summary_fix` IS ALSO A USER-FACING SURFACE INDEPENDENT OF `command`. `render_human_report` groups findings by `(title, summary_fix)` and prints `Fix: <summary_fix>`, and `resolve_next_actions` passes `summary_fix` as the `NextAction` description. Three branches currently set `summary_fix = cmd`, so setting `command=None` without also rewriting `summary_fix` would leave the unrunnable string printed as the `Fix:` line. Each of E-01..E-05 must rewrite `summary_fix` as well as `command`.
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

### Added at review, 2026-09-25 (all re-measured against this worktree)

The table above understates the defect in four ways, each verified rather than reasoned:

| # | Rule / shape | Measured behavior |
|---|---|---|
| 1 | `aw rename plans <path> --slug s` | exit 2, `error: no plan has Id '<path>'`. `plans` routes to the id-directed `plans_refs.run_mv`, so the PATH-shaped hint this plan proposed refuses for `plans` while working for `backlog`/`specs`. Same for `aw group plans <path> --set s`. |
| 2 | `aw rename <type> <free-form name> --slug s --apply` | exit 0 and renames, but the result is STILL nonconformant (`weird.ipd.md` -> `corrected-slug.md`): the free-form fallback in `compute_target_name` drops the whole grammar. A free-form name needs `--to-id6`. |
| 3 | `aw group <type> <f> --set new --apply` (no `--rename`) | clears `check.setid-collision` and RAISES `check.identity-absent-from-name` on the same file: metadata moves, filename does not. Adding `--rename` leaves both clean. |
| 4 | `aw set <status> <id6>` for `check.status-untooled` | exit 0, reports success, and the drift REMAINS. The write is tagged `same-status` by `status_set.apply_status_change`, and `check_engine._has_matching_history_line` accepts only a line whose token equals the new status. The completed command can never clear this finding. |
| 5 | `aw backlog set <f> --blocks-release next` for a `plans` location | emits `aw plans set ...`; `aw plans` is not a command (exit 2, `invalid choice: 'plans'`). `releases.check_blocks_release` scans `plans` too, so this is reachable. |
| 6 | `git commit -m "Update" -- <path>` (`git-dirty`/`git-staged`) | runnable exactly as printed, and running it breaches the `aw commit` requirement and risks committing a co-worker's staged work in a shared checkout. |

Finding 4 is the most serious, because it is the only one that reports SUCCESS while leaving the repository in the state the check flagged, which is precisely the false-completion path this plan's Goal names.

## Proposed changes (ordered, validatable)

1. E-01..E-05: make the five defective branches advisory, each with a shape in `detailed_fix` that is correct for every type the branch can emit and that actually leaves the repository clean.
2. E-06: a table-driven family guard over EVERY branch, so a future branch that emits an unrunnable, placeholder-bearing, or contract-violating command fails a test rather than shipping.

## Deferred / out of scope (with reason)

- Adding an "advisory" flag to `NextAction`, so that placeholder commands can be listed without being auto-run (backlog candidate fix 2). `command=None` already achieves the safety property using the existing mechanism.
  - Carrier-Declined: option 1 of the backlog item satisfies the defect and has in-function precedent (`id6-identity-slot`), and a new field would widen the `--agent` JSON contract for no additional correctness.
- `command_surface.py` declares `aw index` as `mutation_gate="dry_run_default"` although it writes by default (noted in the backlog item). That is a separate contract mismatch and changes no doctor output.
  - Carrier-Declined: not a doctor remediation defect; out of this bug's scope, and the item mentions it only as a caution for this fix.
- ADDED AT REVIEW: the `same-status` / `_has_matching_history_line` disagreement that makes the `status-untooled` remediation unable to clear its own finding (Findings row 4). Two shipped components disagree on which history token a re-applied status writes, and no `doctor.py` change can reconcile them.
  - Carrier: mpghjn
  - Carrier note: filed at review 2026-09-25 as a `bug` carrying `Blocks-Release: next`, so the obligation survives this plan reaching `executed`.
  - Deferred with reason: the fix is a behavior change in `status_set.apply_status_change` or `check_engine._has_matching_history_line`, both outside this plan's `Scope-Paths`, and either edit changes a gate other plans are validated against. E-04 removes the FALSE CLAIM (the command that reports success and fixes nothing) which is this plan's actual subject; it does not and should not pretend to fix the underlying disagreement. A user following `aw doctor`'s advice cannot currently clear a `status-untooled` finding by any documented command, which is why the carrier above exists. NOT resolved here, and NOT silently dropped.

## Scope check

- Over-scope: none. E-04 and E-05 were added at review and stay inside the declared `Scope-Paths` (`doctor.py` + its tests); neither changes `aw set`, `aw rename`, `aw group`, or any checker.
- Under-scope: none remaining. Every `cmd =` site in `build_remediation` is now covered by E-01..E-05 or asserted by the E-06 family guard. The underlying `same-status` checker disagreement is explicitly DEFERRED above rather than left unstated.

## Required tests / validation

New tests in `tests/test_doctor.py` (E-01..E-06), shown failing against the unfixed code, then the bare suite.

## Spec / documentation sync

N/A: no spec documents the per-rule remediation strings (confirmed at review: no `.spec.md` in `.aw/records/specs/` mentions `doctor` remediations or `build_remediation`). The `--agent` JSON keeps its shape (`command` was already nullable, and `NextAction.to_dict` omits an absent description), so no consumer contract changes. No `Scope-Paths` entry is a spec file, so this run declares no spec edit.

## Open questions

### OQ-01: May `aw doctor` print a command a human must edit?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: The backlog item defers this as a UX decision. Resolved from repo precedent: `id6-identity-slot` already returns `command=None` for a judgement call, and `resolve_next_actions` treats `None` as advisory. The plan shows the editable shape only in the `Fix:` text and never as a `command`. A maintainer who prefers option 2 can say so at review. CONFIRMED AT REVIEW 2026-09-25: the precedent holds, and `check_engine._identity_rename_hint` is a second instance of the same pattern (it composes an editable `<slug>`/`<setid>` shape as advice, not as an executable command).

### OQ-02: Should the `status-untooled` checker disagreement be fixed here?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Raised at review from Findings row 4. A re-applied status writes a `same-status` history token (`status_set.apply_status_change`) that `check_engine._has_matching_history_line` does not accept, so NO command `aw doctor` can print will clear a `check.status-untooled` finding. Resolved from this plan's own declared scope: both candidate fix sites are outside `Scope-Paths`, and either edit changes a gate other pending plans are validated against, so it is DEFERRED to its own item (recorded under "Deferred / out of scope") rather than absorbed here. E-04 still fixes what is in scope: it stops `aw doctor` claiming a command that cannot work. Non-blocking because this plan's Goal is achieved without it, but the maintainer should expect a follow-up `bug` item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

THE PRE-FIX COMPARISON RECIPE (used by V-01, V-02 and V-06). The method this plan was authored with does NOT work and must not be used: a scratch copy of `doctor.py` on `PYTHONPATH` is shadowed by the repo checkout, because `sys.path[0]` is the working directory and resolves `agent_workflows` to the real package first (measured 2026-09-25: `doctor.__file__` still pointed at the worktree copy). `git stash` remains forbidden in a shared checkout. Use file-location loading instead, which was measured to work:

```sh
cp agent_workflows/doctor.py /tmp/opencode/doctor_prefix.py   # BEFORE applying the fix
# after the fix, load the pre-fix copy by location and print the old value:
python3 -c '
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("doctor_prefix", "/tmp/opencode/doctor_prefix.py")
m = importlib.util.module_from_spec(spec); sys.modules["doctor_prefix"] = m
spec.loader.exec_module(m)
from agent_workflows import artifact_core as core
d = core.Drift(".aw/records/backlog/open/x.backlog.md", "check.name-nonconformant", "nope")
print("PRE-FIX command:", m.build_remediation(d, Path(".")).command)'
```

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -m pytest -o addopts="" tests/test_doctor.py -k name_nonconformant -v`, showing the new tests PASSED. Paste the pre-fix comparison above, showing the old `command` was non-None. Paste the `detailed_fix` for BOTH a clustered location (must contain the id6 as selector, `--slug` and `--apply`, and must NOT contain the path as the `aw rename` selector for a `plans` location) and a free-form location (must contain `--to-id6`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pytest output for the `setid_collision` remediation test, showing it passed, and the `detailed_fix` string itself showing it contains `--set`, `--rename` and `--apply`. Separately, in a throwaway repo, paste before/after `check.setid-collision` AND `check.identity-absent-from-name` findings around running the recommended shape, showing BOTH are clear afterwards (the no-`--rename` shape was measured to leave the second one raised).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pytest output for the `blocks_release_dangling` remediation test, showing it passed, for a `backlog`, a `specs` AND a `plans` location. Show the `plans` case names `aw ipd set` and never `aw plans set`. In a throwaway repo carrying a `planned` release record, paste the output of the recommended `backlog` shape (`aw backlog set <f> --status open --blocks-release next`) and the resulting `- Blocks-Release:` line, showing the dangling value was rewritten and `releases.check_blocks_release` returns no drift.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the pytest output for the `status_untooled` remediation test, showing `command is None` and that `detailed_fix` names both reverting the hand edit and `aw ipd set`. ALSO paste the reproduction that justifies the item: in a throwaway repo, hand-edit a staged plan's `- Status:`, show `check_engine.check_status_untooled` reports it, run the OLD recommended command with the id6 filled in, and show it exits 0 while the drift is STILL reported. That evidence is what proves completing the command would not have worked.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the pytest output for the `git-dirty` and `git-staged` remediation tests, showing `command is None` for a real path AND for the `<git>` sentinel. Paste a grep over `agent_workflows/doctor.py` showing no remaining `cmd` assignment produces a string starting with `git commit`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the pytest output for the family guard, showing it passed, and its FAILING output against the pre-fix module (via the recipe above) naming at least the `aw rename`, `aw group`, `aw set <status>` and `git commit` commands. Paste the guard's rule table from the test source, so a reviewer can confirm it enumerates every branch rather than only the ones this plan touched.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run, showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. Re-assessed at review after growing from 5 to 7 E-items: all seven edit ONE function in ONE file plus its one test module, each item is one branch of one `if` chain, and the E-06 guard must see every branch at once to be a family check. Splitting would create children that each half-populate the same guard.

Execute only after explicit human approval.

Resolved open questions: OQ-01 and OQ-02 are both `resolved` and both non-blocking; no blocking question remains.

Scope fence (a DECLARATION, not a stop instruction): this plan's `Scope-Paths` are `agent_workflows/doctor.py` and `tests/test_doctor.py`. Editing any other path, in particular `agent_workflows/status_set.py` or `agent_workflows/check_engine.py` (see the deferred checker disagreement), is out of scope; if the work genuinely requires it, make the edit and JUSTIFY it at finalize with `--scope-reason <path>=<why>`, and `--scope-ack` any declared path left unmodified.

Honesty rule (hard MUST): when reporting that tests pass, paste the ACTUAL runner output. Never claim a result you did not run, and never fill an `Observed evidence` block from memory.

Commit through `aw commit <this plan> -- agent_workflows/doctor.py tests/test_doctor.py`; never push.

Lifecycle transition: the plan MUST reach `executed/` through the tooled lifecycle, never a hand-rolled `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence. Ownership is conditional: under `aw oc run` / `aw agy run` the RUNNER performs the finalize transaction, so the executing agent does NOT invoke it; for a hand-run execution outside a runner, the executor runs `aw ipd finalize` itself.
