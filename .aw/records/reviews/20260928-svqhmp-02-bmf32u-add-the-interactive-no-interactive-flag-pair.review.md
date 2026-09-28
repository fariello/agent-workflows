# Review findings: plan bmf32u

- Subject-Id: bmf32u
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `0864e264` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`). After revision, `--phase review-finalize`
reports exit 1 with EXACTLY ONE diagnostic, `IPD-Q501` naming the new blocking OQ-03, which is the
intended fail-closed state for an escalated HIGH finding and not a structural defect. No pre-review
snapshot was owed: the plan was committed and unmodified (`git status --short` clean) and the
lane-input copy at `.aw/state/lane-inputs/rev-11/` is byte-identical to the tracked file.

THE PLAN'S ARCHITECTURE IS RIGHT AND ITS SEQUENCING IS THE ITEM'S OWN. Adding the operator surface
over a resolver rather than checking a flag at 22 sites is correct, the `- Item-Dependencies:
executed:da9n1s` gate is load-bearing rather than preference, and OQ-01's resolution from a published
human-approved contract instead of a fresh maintainer round trip is exactly the right call. Its
measurement discipline is high and most of it reproduces: F-01's parser walk reproduces EXACTLY (all
five candidate spellings on ZERO of 283 subcommands), F-04 reproduces (`rg` for an
`--interactive`-family `add_argument` returns nothing), F-05 and F-06 reproduce precisely (the deleted
guard is recoverable and contains all six constructs the plan names), F-07 reproduces, F-09
reproduces (`--yes` exactly 23 times).

WHAT REVIEW FOUND IS THAT THE PLAN'S TWO CENTRAL MECHANISM CLAIMS ARE BOTH FALSE AGAINST THE TREE,
AND THAT THE LADDER IT WOULD PUBLISH CARRIES A REAL SAFETY HAZARD.

**THERE IS NO PARENT THE FORWARDED LEAVES INHERIT (PR-301, HIGH).** E-01 instructed the executor to
declare the pair on "the parent that the FORWARDED leaves also inherit (the one carrying
`--color`/`--no-color`)". Measured by walking the built tree: `oc run`, `oc runipd`, `oc review`,
`agy view`, `run as`, `run ipd`, `agy sessions` and `agy exec` each expose an EMPTY option-string set.
They inherit NOTHING - not `presentation`, not `common`. So the sentence describes a parser
relationship that does not exist, and an executor trusting it would believe declaration covers the 28
forwarded leaves when consumption is their ONLY mechanism. The plan was misled by a shipped comment
in `_build_parser` asserting "`parents=[common]` IS STILL APPLIED to those leaves, deliberately",
which is false at HEAD and whose two justifications are both spent: the `_dispatch_parsed` fallback
it names is not a symbol in `cli.py` at all, and `tests/test_run_dispatch.py`, cited as independently
asserting the forwarded-route contract, was deleted by the same `19313eed` this plan already tracks.
This is the sharpest finding because the plan's own F-03 had the right shape and the E-item
contradicted it.

**THE ARGPARSE MUTUALLY EXCLUSIVE GROUP IS DEAD CODE AT RUNTIME (PR-302, MEDIUM).** E-01 required
"passing both exits 2 with argparse's own usage error" and V-01 required that message pasted. Measured:
`_consume_presentation_flags` strips both tokens on EVERY path before `parse_args` runs, so the color
group is unreachable through `cli.main` and the refusal always comes from the `_dispatch` hand-check.
`cli.main(["--color","--no-color","check"])` returns 2 emitting `agent-workflows: error: argument
--color: not allowed with argument --no-color` with no `usage:` block and no `Next` line, whereas
`parser.parse_args(["--color","--no-color","check"])` exits 2 emitting argparse's `usage:` block and
the operands REVERSED. The deleted guard's `test_passing_both_flags_exits_two_on_a_parsed_command`
passed only because it called `parse_args` directly, bypassing `_dispatch` - which is precisely how
the group's deadness went unnoticed for a release. The V-item as written was therefore unsatisfiable
as stated, and an executor would either paste the wrong thing or conclude the implementation was
broken.

**A NAIVE FLAG-BEATS-ENV LADDER WOULD RE-OPEN THE WEDGE CLASS THIS SET FENCES (PR-306, HIGH, and the
safety finding of this review).** E-06 specified publishing `flag > AW_NONINTERACTIVE/CI > detection`,
in "the same flag-beats-env-beats-detection shape" as the color axis. That grants `--interactive` the
power to override a CI signal. The repository has ALREADY RULED the other way for the one existing
force escape: `runner_stop.interrupt_menu_is_safe` implements `forced_noninteractive` as an early
return BEFORE its `AW_FORCE_INTERACTIVE_INTERRUPT` check, and its docstring gives the reason in its
own words, that the escape "bypasses conditions 1 and 2 but NOT the forced-noninteractive signals: a
deliberate CI setting must win over a stale force flag, since CI is the environment where an
unbounded wait is least recoverable". That site runs inside a SIGNAL HANDLER calling `readline()` with
no timeout while holding the run lock, and `aw oc run` reaches it IN-PROCESS via `_dispatch`'s
`return oc_runipd.main(...)`, so E-03's process-wide override genuinely arrives there. Publishing the
flat ladder in a normative document would license exactly the "silently re-enable prompting ...
weakening a real fail-safe" outcome backlog item `svqhmp` names as its own motivation. E-05/E-06 are
rewritten for the safe asymmetric ladder and the decision is ESCALATED as blocking OQ-03, because the
answer becomes a published contract and is the maintainer's to make.

**E-03 NAMED NO SYMBOL BECAUSE ORDER 1 FIXES NONE (PR-304, MEDIUM).** E-03 said to publish into "the
resolver's process-wide override" without naming the setter or getter. That is not vagueness the
executor can resolve by guessing: `da9n1s` E-01 specifies only "a process-wide setter/getter" and its
V-01 asks for a round-trip, naming no symbol, so the spelling genuinely does not exist yet. E-03 now
instructs the executor to read the real names out of `term.py` at execution and to STOP if absent,
since their absence means the dependency was not satisfied and the flag would be inert.

Three smaller items: the restored guard's parsed-path mutual-exclusion test must not be ported
unchanged, since it is the very test that masked PR-302 (PR-305); the 28-versus-29 forwarded-leaf
count was internally inconsistent without stating the `__complete` split (PR-303); and the gate
lacked a scope fence entirely while the plan declares six paths, three of which Order 1 also declares
(PR-307).

Every other claim was checked and HELD, and two of the plan's own deferral rows were UPGRADED rather
than corrected: F-05's "CARRIER: none filed" is now superseded, because Order 1's review filed backlog
`p5qx91` covering that exact spec defect and it is committed `open`, so the obligation has a real
owner and the plan's request that "the reviewer file it separately" is already discharged. OQ-02 was
resolvable from repository evidence (the spec citation plus the already-declared scope path both point
at the old filename) and is resolved as decision D-2 rather than left to the executor. The
gate-inheritance claim is correct: item `svqhmp` is `- Work-Kind: feature` with no `- Blocks-Release:`,
and the default `release_gate_work_kinds` is `bug` alone, so no gate is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-301 | HIGH | IN-SCOPE | A. Correctness / G. Executability | Parser walk at HEAD `0864e264`: `oc run`, `oc runipd`, `oc review`, `agy view`, `run as`, `run ipd`, `agy sessions`, `agy exec` each yield `options=[]`; `rg -n _dispatch_parsed agent_workflows/cli.py` returns only the comment referencing it; `git cat-file -e HEAD:tests/test_run_dispatch.py` fails; plan E-01 "Put it on the parent that the FORWARDED leaves also inherit" | **THE PARENT E-01 NAMES DOES NOT EXIST.** The forwarded leaves inherit no argparse parent at all, so declaration reaches only the 254 parsed subcommands and E-02 is the SOLE mechanism for the other 28. The plan was misled by a shipped `_build_parser` comment that is false at HEAD and whose two cited justifications are both gone (`_dispatch_parsed` is not a symbol; `tests/test_run_dispatch.py` was deleted by `19313eed`). An executor trusting E-01 would under-build E-02. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 rewritten: declare on `presentation`, reach stated as the 254 parsed subcommands, with an explicit DO-NOT-believe warning naming the false comment and both spent justifications, and an explicit prohibition on "fixing" it by giving a forwarded leaf `parents=[presentation]` (which would break `argparse.REMAINDER` and contradict published section 1.2). E-02 restated as the ONLY mechanism for the 28. New F-10. V-01 now requires the measured reach with the split. Gate and conventions corrected. |
| PR-302 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing / F. Honest documentation | MEASURED at HEAD `0864e264`: `cli.main(["--color","--no-color","check"])` -> rc 2, stderr exactly `agent-workflows: error: argument --color: not allowed with argument --no-color` (no `usage:`, no `Next` line); `parser.parse_args(["--color","--no-color","check"])` -> SystemExit 2 with argparse's `usage:` block and `argument --no-color: not allowed with argument --color` (operands reversed); `git show 19313eed^:tests/test_flag_surface_uniformity.py` `test_passing_both_flags_exits_two_on_a_parsed_command` calls `parser.parse_args` directly; `term.color_override` docstring claims the refusal is "STRUCTURALLY by argparse's mutually exclusive group" | **THE GROUP IS UNREACHABLE THROUGH `cli.main`, SO E-01's "argparse's own usage error" WAS UNSATISFIABLE AS STATED.** Consumption precedes `parse_args` on every path, so `_dispatch`'s hand-check is the only live refusal for either pair. The plan also asserted the refusal "needs two implementations for one behavior", which is backwards: there is one live implementation and one dead backstop. `term.color_override`'s docstring carries the same false claim. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states what the group actually buys (`--help` honesty and a reordering backstop), pastes the measured contrast, and forbids a validation expecting argparse's wording from `cli.main`. E-02 notes there is only one refusal surface, so no second wording must be matched. V-01/V-02 reworded accordingly. E-06 required not to attribute exit 2 to argparse. New F-11 and F-13; the `term.color_override` docstring fix is explicitly fenced OUT as `p5qx91`'s color-axis work. |
| PR-306 | HIGH | IN-SCOPE | B. Security and safety / D. Anti-regression | `runner_stop.interrupt_menu_is_safe` body: the `forced_noninteractive` early return PRECEDES `if os.environ.get("AW_FORCE_INTERACTIVE_INTERRUPT") == "1"`; its docstring: the escape "bypasses conditions 1 and 2 but NOT the forced-noninteractive signals: a deliberate CI setting must win over a stale force flag, since CI is the environment where an unbounded wait is least recoverable"; `cli._dispatch`'s `return oc_runipd.main(list(argv_list[2:]))` (in-process); plan E-06 "flag > `AW_NONINTERACTIVE`/`CI` > stdin and output-stream detection" | **THE LADDER E-06 WOULD PUBLISH LETS `--interactive` DEFEAT A CI SIGNAL**, at sites including one inside a signal handler with `readline()` and no timeout holding the run lock, reachable in-process from `aw oc run`. That is the "silently re-enable prompting ... weakening a real fail-safe" outcome the backlog item names as its motivation, and the repository already ruled the opposite way for its only existing force escape. Publishing it normatively would make a later plan implement it. | C:Low; U:Medium; S:Medium-High; F:Medium; Overall:Medium-High | OPEN | ESCALATED as blocking OQ-03 (`- Blocking: yes`, `- Owner: maintainer`, `- Finding: PR-306, F-12` - the review-record id is named FIRST because `check.review-finding-unescalated` matches the typed `- Finding:` subfield against the RECORD's ids, not the plan's own F-numbers), which is why `aw ipd lint` now reports `IPD-Q501` and the plan cannot reach `approved` until answered. E-05 and E-06 are rewritten for the SAFE asymmetric ladder (`--no-interactive` > env > `--interactive` > detection) so confirming costs one word; E-05 gains eight required safety cells (`--interactive` x {`CI=1`,`AW_NONINTERACTIVE=1`} x four hardened sites) that must all be False, and V-05 states a True cell blocks the plan rather than being explained away. NOT fixed unilaterally: the answer becomes a published contract. |
| PR-304 | MEDIUM | IN-SCOPE | G. Executability | `da9n1s` E-01 Expected outcome names only "a process-wide setter/getter"; its V-01 asks for a round-trip naming no symbol; `rg -n 'def set_color_override\|def get_color_override' agent_workflows/term.py` for the color analogue; plan E-03 "the resolver's process-wide override" with no symbol | **E-03 COULD NOT NAME ITS TARGET BECAUSE ORDER 1 DOES NOT FIX THE SPELLING.** This is not resolvable by guessing, and a guessed name would silently create a second module global while the resolver read the first - a flag that appears wired and is inert. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now instructs the executor to read the real names from `term.py` at execution (`rg -n 'def set_.*_override\|def get_.*_override'`) and to STOP if absent, since absence means the dependency was unmet. V-03 requires the found names pasted. New F-14. |
| PR-305 | MEDIUM | IN-SCOPE | E. Testing | `git show 19313eed^:tests/test_flag_surface_uniformity.py` `ColorFlagMutualExclusionTests.test_passing_both_flags_exits_two_on_a_parsed_command` calls `parser.parse_args(["attention","--no-color","--color"])`; measured contrast in PR-302 | **THE GUARD E-04 RESTORES CONTAINS THE VERY TEST THAT MASKED PR-302.** Porting it unchanged for both axes would re-ship a test asserting a path no operator can take while appearing to cover the operator path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires that test SPLIT into two honestly named tests per pair - one exercising argparse's group on a directly-built parser and labelled as the backstop, one exercising `cli.main`/`_dispatch` as the operator path - and V-04 requires both pasted with their differing messages. |
| PR-303 | LOW | IN-SCOPE | A. Correctness | Parser walk at HEAD `0864e264`: `--color` and `--no-color` each declared on 254 of 283, missing on 29; the missing set is the 28 forwarded leaves plus `__complete`; plan E-02 says "28 of 283" while F-03's evidence column says "missing on 29 of 283" | The forwarded-leaf count was stated two ways without the reconciling split, so E-04's named-set arithmetic had no stated target. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and F-03 now state the 28-forwarded-plus-1-hidden split explicitly; E-04 requires `len(EXEMPT) + len(FORWARDED)` to equal the measured gap; V-04 and the Required tests demand the split rather than a bare number. |
| PR-307 | LOW | IN-SCOPE | G. Executability (gate) | Plan gate as authored: approval statement, OQ-01 note, dependency note, path-scoped commit, never-push, paste-actual-output and the lint bar all present; no scope fence, no out-of-scope-edit disposition; "leave the terminal lifecycle transition to the runner" stated unconditionally | The gate named no forbidden paths although the plan declares six, three of which Order 1 also declares and one of which (`term.py`) Order 1's own gate treats as its territory; and it stated finalize ownership without the conditional hand-execution case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming the spec prohibition, the `--yes` prohibition, the `runner_stop` precedence prohibition, the forwarded-leaf `parents=` prohibition and the `term.color_override` docstring carve-out to `p5qx91`; make-and-justify wording (`--scope-reason`/`--scope-ack`) with no "stop and report" for the scope case; the two legitimate stops named (E-03's missing setter, V-05's True cell); conditional runner/executor finalize ownership forbidding a hand-rolled `git mv`. Scope check gained the Order-1 collision note. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-301: E-01's named parent does not exist. Repair the E-item, or REPLAN? | REPAIR. The plan's STRATEGY (declare once, consume for the forwarded leaves) is correct and is what the shipped color pair actually does; only its description of the parser tree was wrong. | (a) REPLAN: rejected, nothing structural changes - E-02 already carried the load-bearing half and F-03 already had the right shape, so the repair is corrective prose plus a measured reach statement. (b) Add `parents=[presentation]` to the forwarded leaves so the sentence becomes true: rejected, and explicitly prohibited in the revised plan - it would break `argparse.REMAINDER` capture and contradict `docs/cli-output-contract.md` section 1.2's published contract that those leaves declare no flags so the downstream parser owns every flag and its `--help`. | Parser walk showing `options=[]` on all eight sampled forwarded leaves; `docs/cli-output-contract.md` section 1.2; `cli.py`'s `p_oc_runipd.add_argument("runipd_args", nargs=argparse.REMAINDER, ...)`. | yes |
| D-2 | OQ-02: restore the uniformity guard at the old path, or at a new name covering both axes? | RESTORE AT THE OLD PATH, and make it a required instruction rather than a recommendation. | A new path naming both axes: rejected. Approved spec `uonrjg` cites the old filename BY NAME, so restoring there makes that citation resolve; the old path is ALREADY in this plan's `- Scope-Paths:`, so a new name would additionally require a scope change; and a new name leaves a second records defect behind. | Spec `uonrjg` line citing `tests/test_flag_surface_uniformity.py`; the plan's own `- Scope-Paths:` already declaring that path; the plan's own recommendation already favored it, so this settles rather than overrides the author. | yes |
| D-3 | PR-306: resolve the precedence question from evidence, or escalate it to the maintainer? | ESCALATE as blocking OQ-03, while writing the plan for the safe answer so confirming is cheap. | (a) Resolve it from `runner_stop`'s existing precedence: TEMPTING and nearly sufficient - that site's docstring rules exactly this question for its own escape - but rejected, because the answer becomes a NORMATIVE published ladder in `docs/cli-output-contract.md` that every later plan is reviewed against, and it deliberately breaks symmetry with the color axis, which is a public-contract judgement rather than a code detail. (b) Publish the flat ladder as the plan said: rejected on the measured safety ground. (c) Leave E-06 silent on precedence: rejected, an unstated ladder is how the two axes drift apart, which is the item's stated motivation. | `runner_stop.interrupt_menu_is_safe`'s docstring and body ordering; `cli._dispatch`'s in-process `oc_runipd.main` call proving the override reaches that site; backlog `svqhmp`'s own motivation wording; the 1h49m wedge recorded in two independent code comments; ESCALATED as required, in the plan as OQ-03 carrying `- Blocking: yes`. | no |
| D-4 | F-05 says "CARRIER: none filed; RAISED FOR THE REVIEWER". File a new item, or check whether one exists? | NEITHER: the carrier ALREADY EXISTS and the row is upgraded to name it. | Filing a second backlog item: rejected as a duplicate that would split the obligation. Leaving the row saying none is filed: rejected, it is now false and would invite a future reader to file the duplicate. | `.aw/records/backlog/open/20260928-p5qx91-01-p5qx91-uonrjg-hollow-color-axis-pins.backlog.md` exists with `- Status: open`, committed in `4d086716` ("plan-review: harden da9n1s"), and its Summary names both hollow color-axis pins. | yes |
| D-5 | Does PR-302 warrant fixing `term.color_override`'s false docstring in this plan, since `term.py` IS declared? | NO. Fence it out to `p5qx91` and note it in the commit message. | Fixing it here: rejected. It is a COLOR-axis claim, `p5qx91` already owns that spec's color-axis pins, and sweeping an unrelated correction into a declared path is exactly what the finalize scope gate exists to surface. The honest middle path is to require E-06 not to COPY the false phrasing into the interactivity row. | The plan's own scope boundary; `p5qx91`'s subject; `docs/cli-output-contract.md` section 1.1's own layer-1 row, which states exit 2 WITHOUT attributing it to argparse and is therefore already correct. | yes |

D-3 is `Reversible: no` and is ESCALATED as required by Step 3.1: it is raised in the plan as OQ-03
carrying `- Blocking: yes` and `- Finding: PR-306, F-12`, so `aw ipd lint` refuses the plan at every
checkpoint until a human answers. The `Reversible` cell is the BARE token `no` because
`check.review-decision-unescalated` case (c) reports a qualified value (it first read `no - escalated
as required`) as UNJUDGED rather than as irreversible, which is the safe reading but would have left
the rule reporting; the escalation is recorded in the Basis cell instead. Verified:
`evaluate_review_decision_escalation` returns zero drift after the change. PR-306 is the only finding left `OPEN`; it is at or above the
repository's `HIGH` gate threshold and is escalated exactly as Step 4 requires. Every other finding is
`FIXED`. OQ-01 remains `resolved` as authored; OQ-02 is now `resolved` (D-2); OQ-03 is `open` and
blocking.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 1, `"findings":1`, the single
  diagnostic being `IPD-Q501` at OQ-03: "BLOCKING question is still 'open'". This is the intended
  escalation state, not a structural defect; no other rule fires.
- TWO INTERMEDIATE DIAGNOSTICS WERE HIT AND FIXED DURING THIS ROUND, recorded because each reveals a
  mechanical contract a reviewer can get wrong. FIRST, `check.review-finding-unescalated` fired with
  "review finding PR-306 is high/open ... but no `Blocking: yes` open question names it" even though
  OQ-03 already carried `- Blocking: yes` and `- Finding: F-12`: `_blocking_escalated_finding_ids`
  matches the typed `- Finding:` subfield against the REVIEW RECORD's ids, so the field must name
  `PR-306`, not the plan's own `F-12`. Fixed by writing `- Finding: PR-306, F-12` (the field splits on
  commas, so both are matchable). SECOND, `IPD-M107` fired on `- Readiness: no-go` because
  `check_readiness_attestation`'s `_REVIEW_EVIDENCE_RE` accepts only `/plan-review`, `APPROVE`,
  `NO-GO` or `REJECT` in the history, and a `REVIEWED - OPEN QUESTIONS` verdict matches NONE of them;
  fixed by labelling the record `/plan-review` per the workflow's documented history format. Verified
  independently that the verdict string itself is well formed: `plan_readiness.classify_verdict`
  returns `('REVIEWED - OPEN QUESTIONS', 'neutral')` and `is_review_history_entry` returns True.
- TWO FURTHER DIAGNOSTICS FROM `aw check` WERE HIT AND FIXED, both caused by this round's own new
  content rather than by the plan as authored. `check.review-decision-unescalated` reported D-3 as
  UNJUDGED (case (c)) because its `Reversible` cell read `no - escalated as required`, a qualified
  value the classifier does not recognize; the cell is now the bare `no` with the escalation stated in
  the Basis cell, and `evaluate_review_decision_escalation` returns zero drift. Separately,
  `check.ipd-uncarried-obligation` reported the NEW OQ-03 because a question recording an outstanding
  obligation must carry a durable disposition; OQ-03 now carries a `Carrier-Declined` line explaining
  that the answer is consumed by E-05/E-06/V-05 inside this plan, and naming (without pre-filing) the
  single follow-up item an option-B answer would create. `evaluate_durable_carrier` now returns zero
  drift.
- FINAL STATE: the ONLY diagnostic remaining against this plan anywhere is `IPD-Q501` / the
  `check.ipd-lint-diagnostic` that surfaces it, i.e. the blocking OQ-03 itself. That is the intended
  fail-closed state and it clears when the maintainer answers.
- Post-revision suite re-check: `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 39.45s`,
  the same pass/skip counts as the baseline, confirming this review touched no code (it edited only
  the plan and this record).
- `aw sanitize --agent` -> clean (recorded in the run below).
- Lane input identity: the tracked plan and `.aw/state/lane-inputs/rev-11/` copy match; `git status
  --short` was clean for the plan path before editing, so no pre-review snapshot was owed.
- **F-01 reproduced EXACTLY.** Parser walk at HEAD `0864e264` over 283 subcommands: `--interactive`,
  `--no-interactive`, `--non-interactive`, `--tty`, `--no-tty` each declared on ZERO.
- **PR-301, the measured correction.** Same walk: `--color`/`--no-color` declared on 254 of 283,
  missing on 29. Per-leaf option sets: `oc run` `[]`, `oc runipd` `[]`, `oc review` `[]`, `agy view`
  `[]`, `run as` `[]`, `run ipd` `[]`, `agy sessions` `[]`, `agy exec` `[]`; by contrast `check` and
  `ipd lint` each carry `--color` and `--agent`. `rg -c 'parents=\[presentation\]'` -> 2 (both
  `common` and `common_upgrade`, neither a forwarded leaf). `rg -n _dispatch_parsed
  agent_workflows/cli.py` -> one hit, the comment referencing it. `git cat-file -e
  HEAD:tests/test_run_dispatch.py` -> fatal; `git log --diff-filter=D -1 -- tests/test_run_dispatch.py`
  -> `19313eed`.
- **PR-302, the measured correction.** `cli.main(["--color","--no-color","check"])` -> rc 2, stderr
  exactly `agent-workflows: error: argument --color: not allowed with argument --no-color\n`.
  `cli._build_parser().parse_args(["--color","--no-color","check"])` -> SystemExit 2, stderr
  `usage: agent-workflows [-h] [--no-color | --color] [--agent] [--json] [-V]\n ... \nagent-workflows:
  error: argument --no-color: not allowed with argument --color\nNext  aw --help\n`. Also confirmed
  `_consume_presentation_flags(['--no-color','check'])` -> `(['check'], override=False)`, so the token
  never reaches `parse_args`. `aw check --help` renders `[--no-color | --color]`, confirming the group
  is wired for help purposes.
- **PR-306, the safety measurement.** `runner_stop.interrupt_menu_is_safe` read in full: the
  `forced_noninteractive` comprehension over `("AW_NONINTERACTIVE","CI")` returns False BEFORE the
  `AW_FORCE_INTERACTIVE_INTERRUPT` check, matching its docstring verbatim. `rg -n
  AW_FORCE_INTERACTIVE_INTERRUPT` -> only those two sites, so the precedence exists in exactly one
  place and is undocumented in `docs/`. `cli._dispatch` confirmed to call `oc_runipd.main(...)`
  in-process for `oc`/`opencode` x `runipd`/`run`. `runner_stop`'s call site confirmed as `if
  interrupt_menu_is_safe(stream=stream):`.
- **F-04 reproduced.** `rg -n 'add_argument\(\s*"--[a-z-]*interactive' agent_workflows/` -> NOTHING.
  `agy_runipd`'s `--no-dangerously-skip-permissions` confirmed as a permissions flag whose help reads
  "Require interactive tool permissions in agy".
- **F-02 reproduced and WIDENED to three sites (new F-15).** `rg` for the spellings ->
  `host_capability_registry.py:630` and `:1042` (`--non-interactive`), `host_adapters.py:102`
  (`"kiro": "kiro-cli chat --no-interactive"`), `benchmark_runners.py:299` (`--no-interactive` to
  `kiro-cli`). The plan named two of the three; all are third-party command lines, so the conclusion
  holds and only the inventory was short.
- **F-05 and F-06 reproduced precisely.** `git cat-file -e HEAD:tests/test_flag_surface_uniformity.py`
  -> fatal. `git show 19313eed --stat` -> that file 460 lines deleted. `rg -n
  test_flag_surface_uniformity .aw/records/specs/approved/` -> the `uonrjg` citation at line 508.
  `git show 19313eed^:tests/test_flag_surface_uniformity.py` contains all six constructs the plan
  claims: `EXEMPT_SUBCOMMANDS = frozenset({"__complete"})`, `FORWARDED_SUBCOMMANDS = frozenset(...)`,
  `test_the_walk_sees_a_deep_tree_not_just_top_level_verbs`, both-flags tests on parsed AND forwarded
  paths, `test_tokens_after_a_bare_double_dash_are_left_alone`, and
  `test_an_unlisted_flagless_subcommand_fails_the_gate`.
- **F-07 reproduced.** `cli._confirm` declines with `term.status("warn", ...)` naming `--yes` when
  `not sys.stdin.isatty()`.
- **F-09 reproduced.** `rg -c '"--yes"' agent_workflows/cli.py` -> 23.
- **F-08 reproduced.** `cli.main`'s docstring records the measured xdist flake and the restore of the
  INHERITED value; `_term_mod.set_color_override(_entry_color_override)` confirmed in the `finally`,
  with the capture `_entry_color_override = _term_mod.get_color_override()` before the `try`.
- Conventions confirmed: `tests/__init__.py` reopens stdin on `/dev/null` with the win32 `_NotATty`
  wrapper; the four `isinstance(sys.stdin, io.StringIO)` disjuncts are present at exactly four sites;
  `_AwArgumentParser.__init__` sets `conflict_handler="resolve"` on every parser;
  `tests/test_term.py::CliNeverLeaksTheColorOverrideTests` EXISTS at HEAD with a five-case
  `EARLY_EXIT_PATHS` table and a nested-invocation assertion, so E-03's cited harness is real (unlike
  the sibling classes `19313eed` deleted, which is Order 1's PR-201).
- **D-4 verified.** `.aw/records/backlog/open/20260928-p5qx91-01-p5qx91-uonrjg-hollow-color-axis-pins.backlog.md`
  exists, `- Status: open`, committed in `4d086716`.
- Gate facts: backlog `svqhmp` is `- Work-Kind: feature` with no `- Blocks-Release:`, and the default
  `release_gate_work_kinds` is `bug` alone, so the plan's "inherits NO release gate" claim is correct.
  Order 1 `da9n1s` is `- Status: reviewed`, `- Readiness: go-pending-approval`, so this plan's
  dependency is not yet satisfied and it correctly cannot run first.
- Suite baseline, bare: `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 40.35s`, i.e.
  ZERO failures at HEAD `0864e264`.

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-306 | high | IN-SCOPE | B. Security and safety / D. Anti-regression | `runner_stop.interrupt_menu_is_safe` body: the `forced_noninteractive` early return PRECEDES `if os.environ.get("AW_FORCE_INTERACTIVE_INTERRUPT") == "1"`; its docstring: the escape "bypasses conditions 1 and 2 but NOT the forced-noninteractive signals: a deliberate CI setting must win over a stale force flag, since CI is the environment where an unbounded wait is least recoverable"; `cli._dispatch`'s `return oc_runipd.main(list(argv_list[2:]))` (in-process); plan E-06 "flag > `AW_NONINTERACTIVE`/`CI` > stdin and output-stream detection" | **THE LADDER E-06 WOULD PUBLISH LETS `--interactive` DEFEAT A CI SIGNAL**, at sites including one inside a signal handler with `readline()` and no timeout holding the run lock, reachable in-process from `aw oc run`. That is the "silently re-enable prompting ... weakening a real fail-safe" outcome the backlog item names as its motivation, and the repository already ruled the opposite way for its only existing force escape. Publishing it normatively would make a later plan implement it. | C:Low; U:Medium; S:Medium-High; F:Medium; Overall:Medium-High | fixed | STALE ESCALATION CLOSED 2026-09-28 by agent (aw ipd recheck-readiness). The question this finding was escalated as (OQ-03) is `- Status: resolved`, so the finding it gated on has been answered and the record is caught up. NO FINDING WAS RE-DERIVED and no plan content was re-critiqued: the match was made on the question's declared `- Finding: PR-306` back-reference, not on a judgement about what the question was about. Previous decision: open. |
