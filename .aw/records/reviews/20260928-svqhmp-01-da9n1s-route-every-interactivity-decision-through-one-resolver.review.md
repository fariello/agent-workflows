# Review findings: plan da9n1s

- Subject-Id: da9n1s
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5241e82a` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --short` clean) and the lane-input copy at `.aw/state/lane-inputs/rev-10/`
is byte-identical to the tracked file (`diff` reported no difference). `aw sanitize --agent` clean.

THE PLAN IS UNUSUALLY WELL EVIDENCED AND ITS CENTRAL JUDGEMENT IS CORRECT. The defect is real, the
two-Order sequencing is the item's own and is right (a flag cannot route through a resolver that no
call site consults yet), and the decision to keep the two site-specific extras and the output-mode
condition at their call sites rather than teaching `term.py` about runner namespaces is the right
architectural call. Its measurement discipline is high: F-01's counts reproduce EXACTLY (59 `isatty`
across 17 files, 22 in `cli.py`, all stdin), F-08's parser walk reproduces (all five candidate flag
spellings declared on ZERO leaves), and F-05's two incident comments are verbatim as quoted. Nine of
its eleven authored findings hold unchanged.

WHAT REVIEW FOUND IS THAT THE PLAN'S OWN CITED MODEL WAS DELETED BY THE COMMIT IT ALREADY CITES, THAT
IT IS NOT THE BEHAVIOR-PRESERVING REFACTOR ITS GATE CLAIMS, AND THAT ONE OF ITS MEASURED SETS IS WRONG.

**E-06's MODEL DOES NOT EXIST (PR-201, HIGH).** E-06 said to model the single-originating-definition
guard on `tests/test_term.py::OneOriginatingDefinitionTests`. That class was DELETED by commit
`19313eed` - the same suite trim the plan already cites as F-09 for a different file - along with
`ColorDepthOneDefinitionTests`, and the `is_pure_delegation` predicate it cited from
`tests/test_rununify_run_queue.py` went with that whole file. So the plan's most structurally
demanding item pointed at nothing, and an executor would have searched, failed, and either invented an
unreviewed guard shape or quietly skipped the item. This is the sharpest kind of stale citation because
the plan had already noticed the commit and did not connect it to its own instruction. The fix is
cheap and better than re-invention: the deleted class is recoverable from git history and IS the
reviewed design, so E-06 now says to read `git show 19313eed^:tests/test_term.py` and port its four
load-bearing properties (AST not substring; "originating" not "one `def`"; a pure-delegation test that
does not pin the target module; a walk of every package `*.py`), each with the recorded reason it
exists. V-06 requires the recovery citation and rejects a guard missing the AST property.

**THE GATE'S CENTRAL CLAIM IS FALSE (PR-203, HIGH).** The gate said "No prompt appears or disappears
for an unchanged environment, with ONE deliberate exception" (the `CI` reading). Measured:
`cli._confirm`'s guard with stdin a TTY and stdout a PIPE answers True today, while the stdin+stdout
fence answers False. So routing the 21 live `cli.py` sites through a resolver whose default includes
rung 4 changes what every one of them answers whenever the output stream is not a terminal - an
invocation like `aw <cmd> | tee log` from a terminal STOPS prompting. This is the plan's PURPOSE, not a
regression: it is exactly the fence whose absence caused the 1h49m finalize wedge F-05 records. But
describing it as no change misrepresents the blast radius to the approver and, worse, told the
validation section to produce a table "showing IDENTICAL answers except for the `CI` cells", which an
executor could only satisfy by not testing the case that matters. The gate now declares three deltas
with a checkable invariant (no cell may go False->True except the three `CI` values), and the
validation is reframed as a behavior-DELTA proof that classifies every differing cell.

**THE `CI` DIVERGING SET IS WRONG IN FOUR PLACES (PR-202, MEDIUM).** The plan says
`engine.is_interactive_session` reads `CI` by "bare PRESENCE, so ANY value including `0` and the empty
string forces non-interactive". It reads `if os.environ.get("CI")`, which is Python truthiness of the
raw string, and `""` is FALSY. Measured against `leak_gate_is_interactive` with TTY streams: `CI=0`
False/True DIVERGE, `CI=false` DIVERGE, `CI=no` DIVERGE, `CI=""` True/True AGREE, `CI=1` and `CI=true`
AGREE. The finding survives intact (three real diverging values, including the plausible `CI=0` the
item cares about) but the name and the example were wrong, and E-03 told the executor to write a test
asserting `CI=""` is a behavior delta - an assertion that would have failed. Corrected in the Concern,
the history note, F-03, E-03, V-03 and the gate.

**OQ-01 COULD NOT HONESTLY BE LEFT OPEN (PR-204, MEDIUM).** Its alternative branch (delete the four
`io.StringIO` disjuncts, convert the tests to the resolver's override) requires editing
`tests/test_cli.py`, which `- Scope-Paths:` does not declare; measured, that file drives these paths
with `patch("sys.stdin", io.StringIO(...))` at many sites. So an executor choosing that branch would
take an undeclared out-of-scope edit or silently delete interactivity assertions, and F-06 already
records that the second failure mode is invisible. Resolved to PRESERVE (the plan's own
recommendation) on that scope ground, with the requirement that the disjunct sit as an OR beside the
resolver call rather than re-implementing a rung.

**F-09 IS TWO DANGLING CITATIONS, NOT ONE (PR-205, MEDIUM).** Spec `uonrjg` cites BOTH
`tests/test_flag_surface_uniformity.py` (deleted outright) and `tests/test_term.py` (surviving, but its
asserting classes deleted) as pins for the color axis. The second is the more dangerous, since a
path-resolving check passes while the content is gone. Filed as backlog `p5qx91` with the decision it
needs (restore the guards versus amend the spec - these are materially different, one preserving the
guarantee and one withdrawing it, and a 9,136-to-2,000 test trim was a deliberate maintainer act), and
recorded as a new deferral row with that carrier rather than left for a reader to rediscover.

Two smaller items: the unmeasured suite baseline, now pinned at `2935 passed, 2 skipped` with zero
failures so any later failure is attributable (PR-206); and the gate, which had no scope fence, no
out-of-scope-edit disposition and an unconditional finalize instruction (PR-207).

Every other claim was checked and HELD. F-01 (exact reproduction); F-02 (all five predicate bodies
read, stream pairs confirmed); F-04 (`is_interactive_run` honors neither `AW_NONINTERACTIVE` nor `CI`);
F-05 (both comments verbatim, including "wedged a real finalize for 1h49m holding its run lock" and
"STRICTLY MORE DANGEROUS ... inside a SIGNAL HANDLER"); F-06 (all four function names correct, all four
`io.StringIO` line sites confirmed); F-07 (`_confirm`'s docstring says "auto-yes when assume_yes or
non-interactive stdin" while its body declines with a warn); F-08 (zero of 249 leaves declare any of
the five spellings; the plan's 283 is a parent-inclusive count that reconciles at 284 including root);
F-10 (`--no-color` missing on 29); F-11. The Step 0 conventions all hold, including `should_color`'s
nested-invocation reasoning and `tests/__init__.py`'s `/dev/null` stdin harness. The gate-inheritance
claim is correct (item `svqhmp` is `- Work-Kind: feature` with no `- Blocks-Release:`, and the default
gating set is `bug` alone). Order 2 `bmf32u` exists, carries `- Item-Dependencies: executed:da9n1s`,
and declares `tests/test_flag_surface_uniformity.py` in its own `- Scope-Paths:`, so all three of its
carrier rows name a real owner rather than a nominal one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-201 | HIGH | IN-SCOPE | E. Testing / G. Executability | `git show 19313eed -- tests/test_term.py` shows `-class OneOriginatingDefinitionTests` and `-class ColorDepthOneDefinitionTests`; `rg -n "^class " tests/test_term.py` lists neither; `tests/test_rununify_run_queue.py` (source of the cited `is_pure_delegation`) does not exist; plan E-06 "modeled on `tests/test_term.py::OneOriginatingDefinitionTests`" | **E-06's MODEL WAS DELETED BY THE COMMIT THE PLAN ALREADY CITES AS F-09.** The plan's most structurally demanding item pointed at a class that does not exist, so an executor would have invented an unreviewed guard shape or skipped the item - leaving the interactivity axis exactly as unprotected as it is today while reporting success. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now recovers the reviewed design from `git show 19313eed^:tests/test_term.py`, names the four properties to port with the reason each exists, prefers it over the weaker surviving `tests/test_runner_shared.py` model, and requires the recovery citation. V-06 requires the citation and rejects a guard lacking the AST property. New F-09a records the deletion. |
| PR-202 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `engine.is_interactive_session` body: `if os.environ.get("CI"): return False`; measured with TTY streams against `leak_gate_is_interactive`: `CI=0` False/True, `CI=false` False/True, `CI=no` False/True, `CI=""` True/True, `CI=1` False/False, `CI=true` False/False | **THE DIVERGING SET IS `{"0","false","no"}`, NOT "any value including the empty string".** `engine` reads Python truthiness of the raw string, and `""` is falsy, so `CI=""` agrees today. The plan asserted otherwise in four places and instructed a test asserting `CI=""` changes behavior - an assertion that would FAIL. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the Concern, the authoring history note, F-03, E-03, V-03 and the gate. E-03 now names the three changed values and requires `CI=""` asserted as a NO-CHANGE case; V-03 requires it in both before and after tables and rejects a V-item claiming it as a delta. |
| PR-203 | HIGH | IN-SCOPE | A. Correctness / F. Honest documentation / E. Testing | Measured: `cli._confirm`'s stdin-only guard with stdin TTY + stdout PIPE -> True (prompts); the stdin+stdout fence on the same streams -> False (declines); plan gate "No prompt appears or disappears for an unchanged environment, with ONE deliberate exception"; Required tests "showing IDENTICAL answers except for the `CI` cells" | **THIS IS NOT A BEHAVIOR-PRESERVING REFACTOR AND THE GATE SAID IT WAS.** Rung 4 changes what all 21 `cli.py` sites answer whenever the output stream is not a TTY, so `aw <cmd> \| tee log` from a terminal stops prompting. That is the plan's purpose (the fence F-05's wedge justifies), but misdescribing it hides the blast radius from the approver AND told the validation to produce a table that can only be satisfied by not testing the case that matters. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | Gate now declares THREE deltas explicitly with the rung-4 change named first as the plan's purpose, plus a checkable invariant (no cell may go False->True except the three `CI` values). Required tests reframed from "behavior-preservation proof" to a behavior-DELTA proof classifying every differing cell against the three declared classes, with anything else blocking. V-05 requires the stdin-TTY/stdout-pipe `_confirm` case pasted. New F-12. |
| PR-204 | MEDIUM | IN-SCOPE | G. Executability / E. Testing | `rg -n 'patch("sys.stdin", io.StringIO' tests/test_cli.py` -> many sites (783, 796, 811, 852, 882 among them); `- Scope-Paths:` declares `tests/test_stdin_interactive.py` and `tests/test_interactivity_resolver.py` but not `tests/test_cli.py`; plan OQ-01 `Owner: executor`, "EITHER IS ACCEPTABLE" | **OQ-01's ALTERNATIVE BRANCH IS NOT LEGALLY AVAILABLE INSIDE THIS PLAN'S SCOPE**, so offering the executor a free choice invited either an undeclared out-of-scope edit or the silent deletion of interactivity assertions that F-06 itself records as invisible. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 RESOLVED to PRESERVE (decision D-3) with the scope reason stated; owner moved to reviewer; `Carrier-Declined` rewritten. E-05 now instructs PRESERVE and requires the disjunct be an OR beside the resolver call, not a local rung re-implementation. Scope check gained the boundary note. New F-13. |
| PR-205 | MEDIUM | UNDER-SCOPE | D. Anti-regression / records integrity | Spec `uonrjg`: "`tests/test_term.py` asserts the single-originating-definition property" and "pinned by `tests/test_term.py` and `tests/test_flag_surface_uniformity.py`"; `git cat-file -e HEAD:tests/test_flag_surface_uniformity.py` fails; the asserting classes are gone from `tests/test_term.py` | **BOTH of spec `uonrjg`'s color-axis pins are hollow, not one.** F-09 caught the deleted file; it missed that the surviving cited file no longer contains the assertion, which is the worse case because a path-existence check passes. Left unfiled, this stays invisible. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-09 widened (full deletion inventory) and new F-09a added. Filed backlog `p5qx91` naming both citations and the decision needed (restore versus amend, with the note that these differ in whether the guarantee survives). New deferral row carries `p5qx91`. This plan still edits no `.spec.md`, which the Spec sync section already justified. |
| PR-206 | LOW | IN-SCOPE | E. Testing | Plan Required tests: "Establish the baseline on a CLEAN tree BEFORE any edit" with no value recorded | The regression bar had no number, so an executor could paste any baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-measured bare at HEAD `5241e82a`: `2935 passed, 2 skipped, 3 warnings in 44.49s`, i.e. ZERO failures, so any later failure is attributable to this work. Recorded with the note that the total will RISE by the new test files. |
| PR-207 | LOW | IN-SCOPE | G. Executability (gate) | Plan gate as authored: approval statement, Order-2 disclaimer, approval requirement, path-scoped commit, never-push and paste-actual-output all present; no scope fence, no out-of-scope-edit disposition; "leave the terminal lifecycle transition to the runner" stated unconditionally; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate named no forbidden paths despite four test files it must run but not edit, carried no out-of-scope-edit disposition, and stated finalize ownership without the conditional hand-execution case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming the four test files and the spec prohibition, make-and-justify wording (`--scope-reason`/`--scope-ack`) with no "stop and report" for the scope case, the E-03 discovered-dependency stop as the one legitimate stop, and conditional runner/executor finalize ownership forbidding a hand-rolled `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | E-06's cited model class no longer exists (PR-201). Should the executor invent a guard, or should the plan supply a design? | RECOVER THE DELETED DESIGN FROM GIT HISTORY and name the four properties to port. | (a) Let the executor invent one: rejected, this is the plan's most structurally demanding item and an unreviewed shape is how a guard that cannot fail gets shipped - especially bad here, where the property previously HAD a guard and lost it silently. (b) Model on the surviving `tests/test_runner_shared.py`: rejected as weaker; its own docstring records its fingerprint fixture is now unread because "the test harness was deleted in `19313eed`". (c) Drop E-06: rejected, the single-originating-definition property is the plan's durable deliverable. | `git show 19313eed^:tests/test_term.py` contains the full reviewed class with its rationale docstring (AST-not-substring, originating-not-one-def, pure-delegation-without-target-pinning, package-wide walk); `git show 19313eed -- tests/test_term.py` confirms the deletion. | yes |
| D-2 | Is PR-203 a reason to reject the plan, given it changes behavior at 21 sites while claiming not to? | NO. The CHANGE is correct and wanted; only its DESCRIPTION was wrong. Declare it as a delta and keep it. | (a) Narrow the resolver's default to stdin-only for `cli.py` sites to preserve behavior: rejected, that is precisely the shape E-02 forbids and the shape that caused the measured 1h49m wedge; it would make the plan pointless. (b) REPLAN: rejected, the architecture is right and the repair is a gate paragraph plus a reframed validation section. | The two incident comments in `ipd_lifecycle.run_finalize` and `runner_stop.interrupt_menu_is_safe`, which justify rung 4 independently; measured `_confirm` delta confirming the change is real; E-02's own "RUNG 4 IS NOT OPTIONAL" statement, which the plan already got right. | yes |
| D-3 | OQ-01: preserve the four `io.StringIO` disjuncts, or convert the tests to the resolver's override? | PRESERVE, and make it the required branch rather than an executor choice. | Convert the tests: rejected on SCOPE, not on taste. It requires editing `tests/test_cli.py`, which `- Scope-Paths:` does not declare, so the branch cannot be taken legally inside this plan; and F-06 records that a botched conversion silently turns interactive wizard tests into non-interactive ones that still pass. The cleaner mechanism remains available to a later plan that declares the file. | Measured `patch("sys.stdin", io.StringIO(...))` sites in `tests/test_cli.py`; the plan's own `- Scope-Paths:`; the plan's own recommendation already favored PRESERVE, so this settles rather than overrides the author. | yes |
| D-4 | The `uonrjg` spec-pin defect (PR-205) is real and out of scope. File it, or note it and move on? | FILE IT as backlog `p5qx91`, with the decision it needs stated. | (a) Amend `uonrjg` in this plan: rejected, it is a COLOR-axis defect, amending an approved spec changes the contract every other plan is reviewed against, and `Scope-Paths` declares no `.spec.md` - which the plan's Spec sync section already reasoned correctly. (b) Leave it as prose in the plan's findings: rejected, prose in a pending plan is invisible to `aw attention`, and the repository rule is explicit that committed backlog must not live only in prose. | Both citations measured hollow; `AGENTS.md`'s rule that committed backlog belongs in the `records/backlog/` tree rather than prose; the deletion was a deliberate maintainer act (9,136 -> under 2,000 tests), so restore-versus-withdraw is the maintainer's call and not an executor's. | yes |
| D-5 | Does OQ-02 need escalating to `Blocking: yes`? | NO. Left `open`, `Blocking: no`, owner executor. | Escalate: rejected. It asks whether any unattended install path depends on the old `CI` reading; the evidence that it does not is already in-tree (`is_interactive_session` returns False whenever `plan.yes`), E-03 requires the consumers enumerated and the guard verified, and E-03 already routes the one bad branch to a RECORDED FINDING rather than a silent change. Under the 2026-09-10 ruling a non-blocking question does not gate readiness. | `engine.is_interactive_session`'s `if plan.yes: return False` first line, read at review; E-03's explicit "STOP and record it rather than changing it" instruction; V-03 requiring the enumeration pasted. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. OQ-01 is now `resolved` (D-3); OQ-02 remains `open` and non-blocking (D-5).

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (Concern/history/F-03/E-03/V-03 `CI` corrections, E-06 model recovery, gate rewrite,
  OQ-01 resolution, F-09 widening + F-09a, F-12, F-13, new deferral row with carrier `p5qx91`,
  Scope check additions, `Status: reviewed`, `Readiness: go-pending-approval`).
- `aw sanitize --agent` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- Lane input identity: `diff .aw/state/lane-inputs/rev-10/plan-20260928-svqhmp-01-da9n1s-....ipd.md`
  against the tracked plan -> no difference; `git status --short` clean before editing, so no
  pre-review snapshot was owed.
- **F-01 reproduced EXACTLY.** `rg -c isatty agent_workflows/` -> 17 files, 59 total references;
  `rg -c isatty agent_workflows/cli.py` -> 22. All 22 enumerated and confirmed stdin; the one at the
  `_build_parser` site is a comment, leaving 21 live.
- **F-02 reproduced.** All five bodies read: `leak_gate_is_interactive` (stdin+stdout, false-value
  list), `ipd_lifecycle.run_finalize`'s `_is_tty` fence (stdin+stdout, same list, plus the output-mode
  AND), `interrupt_menu_is_safe` (stdin+stderr, same list, plus `AW_FORCE_INTERACTIVE_INTERRUPT`
  documented as bypassing the streams but not the signals), `is_interactive_run` (stdin+stderr,
  `--unattended`/`--full-auto`, no env signals), and the bare `cli.py` stdin checks.
- **PR-202, the measured correction.** `engine.is_interactive_session` versus
  `leak_gate_is_interactive`, TTY streams: `CI='0'` False/True DIVERGE; `CI='false'` False/True
  DIVERGE; `CI='no'` False/True DIVERGE; `CI=''` True/True AGREE; `CI='1'` False/False;
  `CI='true'` False/False.
- **PR-203, the measured correction.** `cli._confirm`'s guard with stdin TTY + stdout PIPE -> True
  (would prompt today); the stdin+stdout fence on identical streams -> False (would decline after).
- **PR-201.** `git show 19313eed -- tests/test_term.py` -> `-class OneOriginatingDefinitionTests`,
  `-class ColorDepthOneDefinitionTests`; surviving `rg -n "^class " tests/test_term.py` lists 20
  classes, neither of them; `ls tests/test_rununify_run_queue.py` -> not found; the recovered class is
  self-contained in `git show 19313eed^:tests/test_term.py`.
- **PR-205.** `git cat-file -e HEAD:tests/test_flag_surface_uniformity.py` -> fatal, does not exist;
  `git show 19313eed --stat` -> that file 460 lines deleted, `test_output_contract.py` 138,
  `test_output_mode.py` 176, `test_run_flag_surface.py` 4863; spec `uonrjg` bullet quoted above.
- **F-05 reproduced verbatim**, both comments, including "wedged a real finalize for 1h49m holding its
  run lock, leaving the plan `approved` in pending/ while the run reported `complete`" and "THIS SITE
  IS STRICTLY MORE DANGEROUS ... the menu runs inside a SIGNAL HANDLER ... `readline()` here has no
  timeout".
- **F-06 reproduced.** The four `io.StringIO` disjuncts resolve to `_ask_policy`, `_confirm_install`,
  `_install_leftover_disposition` and `_run_migrate_layout` - all four names as the plan states.
- **F-07 reproduced verbatim.** `_confirm`'s docstring: "Ask a yes/no question; auto-yes when
  assume_yes or non-interactive stdin." Its body: `if not sys.stdin.isatty():` -> warn "(declining:
  non-interactive; pass --yes to proceed)" -> `return False`.
- **F-08 reproduced.** Parser walk over 249 leaves: `--interactive`, `--no-interactive`,
  `--non-interactive`, `--tty`, `--no-tty` each declared on ZERO. The plan's "283 subcommands" is a
  parent-inclusive count (284 including root), so the figure reconciles rather than conflicting.
- **F-10 reproduced.** `--no-color` missing on 29 of the 249 leaves.
- Step 0 conventions confirmed: `should_color`'s two-level override with `_COLOR_OVERRIDE` and its
  nested-invocation reasoning; `cli.main`'s `finally` restoring the INHERITED value rather than `None`
  (noted in the plan, since copying it as a `None` reset would break nesting);
  `term.stdin_is_interactive`'s win32 `GetConsoleMode` probe and its self-described honest limit;
  `git_commit_helper._is_interactive`'s docstring already naming the divergence this plan closes;
  `tests/__init__.py` reopening stdin on `/dev/null` against a measured 40+ minute hang.
- Set and gate facts: backlog `svqhmp` is `graduated`, `- Work-Kind: feature`, no `- Blocks-Release:`;
  the repository's `release_gate_work_kinds` is the default (`bug` alone), so no gate is owed. Order 2
  `bmf32u` is `pending` with `- Item-Dependencies: executed:da9n1s` and declares
  `tests/test_flag_surface_uniformity.py` in its own `- Scope-Paths:`.
- Suite baseline, bare: `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 44.49s`.
- Filed during review: backlog `p5qx91`
  (`.aw/records/backlog/open/20260928-p5qx91-01-p5qx91-uonrjg-hollow-color-axis-pins.backlog.md`).
