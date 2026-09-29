# Review findings: plan 5poaqh

- Subject-Id: 5poaqh
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9504c522` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after
revision (exit 0, `findings: 0`). `IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads
`child`, not `orchestrator`. No pre-review snapshot was owed: the plan was committed at `6b614cc8` and
unmodified, with `git status --short` empty at review start. Bare suite at review HEAD: `3246 passed, 2
skipped, 3 warnings in 47.59s`. `aw sanitize --agent`: `outcome: clean`, exit 0.

NO PRODUCTION FILE OR TEST WAS MODIFIED BY THIS REVIEW. Every measurement was a read, an in-process probe
that restored what it patched, or a driven CLI invocation against purpose-built fixture repositories under
a gitignored `tmp/` path, which was removed afterwards (`git status --short` empty again before commit).

THIS PLAN IS UNUSUALLY WELL MEASURED AND I RE-RAN EVERY LOAD-BEARING CLAIM. ALL SIXTEEN authored findings
REPRODUCE at review HEAD. The ones worth naming individually:

- F-01 reproduces verbatim: `aw ipd set reviewed aaaa03 --actor 'me model=x' -m 'retire note' --no-commit
  --priority high --from-backlog pftva5 --dir <fixture> --json` emits
  `next_actions: [{"command": "aw set reviewed aaaa03 --yes"}]`. Every flag is gone, `ipd set` became `set`.
- F-02's revert is real and the audience claim is correct. `git show fcf76812` is titled `fix(status_set):
  allow direct interactive status mutation and commit prompt without requiring -y`, and measured, a flagless
  `aw ipd set reviewed pl0001 --no-commit --dir <fixture>` exits 0 and writes `- Status: reviewed`, printing
  no hint. The predicate at `status_set.py:2008` reads `(ctx.is_agent or ctx.is_json) and not is_dry_run and
  not yes`.
- F-04 is the most serious and reproduces EXACTLY, including the history line. After `aw ipd set approved
  ex0001 --actor 'me model=x' -m 'why' --no-commit --dir <fixture> --json` on a fixture holding an
  `executed` plan, the second next action was `aw set approved ex0001 --allow-terminal-reopen --yes`;
  re-executing it exited 0, moved the plan back to `pending/`, and wrote
  `- 2026-09-29 approved (aw set, --allow-terminal-reopen): status set to approved` with neither the
  actor nor the message the caller supplied.
- F-05 reproduces and is worse than "under-specified". `aw ipd set executed pl0001 --message "say \"hi\"
  and it's" --json` emits `--message 'say "hi" and it\'s'`; `shlex.split` on it raises `ValueError: No
  closing quotation` and `bash -c` exits 2 with `unexpected EOF while looking for matching '`.
- F-06 reproduces: `aw set reviewed aaaa03 --priority high --from-backlog pftva5 --dir <fixture> --yes`
  exits 2 with `unrecognized arguments: --priority high --from-backlog pftva5`.
- F-07 reproduces: rendering a `NextAction` whose command carries `--dir <home>/checkout` raises
  `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'`, while a
  relative `tmp/x2` and a non-home absolute `/srv/shared/repo` both validate.
- F-08 reproduces: on a fixture where `shared` names one plan and one spec, `aw ipd set reviewed shared
  --json` scopes correctly and emits `aw set reviewed shared --yes`, which then exits 2 with `Selector
  'shared' names artifacts of 2 types (plans, specs), so 'aw set' cannot tell which you meant`.
- F-09 reproduces for all five spellings, alias preserved: `ipd set` -> `command='ipd',
  ipd_command='set'`; `specs set` -> `('specs','set')`; `spec set` -> `command='spec',
  specs_command='set'`; `backlog set` -> `('backlog','set')`; `set` -> `command='set'`. `aw plan set` and
  `aw plans set` are both `invalid choice`, confirming they are not live spellings.
- F-10 reproduces: `argparse.Namespace(dir=..., message=..., yes=True, json=True)` has
  `hasattr(ns, "command")` False and still reaches the terminal-reopen refusal and emits its hint.
- F-11 reproduces and is correctly identified as a PIN rather than a target: `aw set plans reviewed shared
  --json` emits `aw set plans reviewed shared --yes`.
- F-12 reproduces: `grep -c "next_actions\|NextAction\|cmd_str" tests/test_status_set.py` returns 0.
- F-13 reproduces: `aw ipd set` leaves `message=None`, `aw specs set` leaves `message=''`.
- F-15's baselines all reproduce: `3246 passed, 2 skipped` bare; `95 passed` for the three owning modules;
  `79 passed` for `tests/test_status_set.py` alone (measured with `-o addopts=""`, since the configured
  `-q` otherwise suppresses the per-test count).
- F-16 reproduces: no spec under `.aw/records/specs/` describes `run_set_command`'s hints or `NextAction`
  content; `docs/cli-output-contract.md:152` describes only the carrier shape and
  `docs/cli-agent-protocol.md:59` only that `next` is "a ready-to-run command". No spec amendment is owed,
  and none is declared in `- Scope-Paths:`, which is consistent.

SIX FINDINGS WERE RAISED AND ALL SIX WERE FIXED IN PLACE. Two of them (PR-001, PR-002) would each have
shipped a command that does not run, which is precisely the failure class this plan exists to eliminate, so
they are recorded as HIGH rather than as polish. A third (PR-003) set an acceptance bar no correct
implementation could meet.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A (correctness); G (executability) | `agent_workflows/cli.py:5836` (`p_specs_set.add_argument("--message", ...)`), `agent_workflows/cli.py:5525` (`p_backlog_set.add_argument("--message", ...)`), plan E-02 | E-02 prescribed echoing `--message/-m`, but `-m` is NOT declared on `aw specs set` or `aw backlog set` (both declare only `--message`, while `aw ipd set` and untyped `aw set` declare both). An echo faithful to the caller's typed spelling therefore emits a command that exits 2 with `unrecognized arguments: -m msg` on two of the four verbs the reconstruction newly makes reachable, and both verbs genuinely reach the confirmation refusal. This is the SAME failure mode the plan's own F-06 identifies for `--priority`, arriving by a different door, and the plan did not notice it. Measured: `aw specs set to-review bbbb04 -m 'retire note' --yes` and `aw backlog set done cccc05 -m 'retire note' --yes` each exit 2; the `--message` form of each exits 0. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now mandates the long `--message` always, with the measurement and the reason it is free of cost (every spelling writes the one dest `args.message`, so the namespace cannot report which alias was typed). Recorded as new finding F-17, as OQ-05 (resolved, owner the reviewer), and in the conventions list. E-06 gained case (h), which drives both spellings and RE-EXECUTES each emission asserting exit 0, because a string-only assertion on the `ipd` path would not catch this. |
| PR-002 | HIGH | IN-SCOPE | Rubric A (correctness); B (privacy) | `agent_workflows/agent_schema.py:63` (`_HOME_PATH_RE`), `agent_workflows/agent_schema.py:337` (`_check_string_values`), plan E-02, plan OQ-01 | The home-path validator keys on the VALUE, not the flag name, so excluding `--dir` alone leaves four more crash routes open: `--evidence`, `--gate-dir`, `--scope-reason` and `--scope-ack` can all carry operator-local absolute paths. E-02's echo list explicitly INCLUDED `--evidence` and `--gate-dir`, so as authored it would have reintroduced the exact `ValueError` OQ-01 was resolved to prevent. Reachability confirmed, not theoretical: `aw backlog set done cccc05 --evidence <abs> --gate-dir <abs> --json` reaches the confirmation refusal at exit 2 with both values home-prefixed in the namespace, and `aw ipd set reviewed aaaa03 --scope-reason <abs>=why --json` likewise. Each raises when rendered: `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now excludes all five path-valued flags and mandates an ALLOW-LIST of non-path flags rather than a deny-list, so a sixth path flag added later is excluded by default. The `normalize_repo_path` non-repair is restated for `--scope-reason` specifically (it would corrupt the `PATH=WHY` pair). Recorded as F-19; OQ-01's resolution widened from `--dir` to the value-keyed rule; E-06(g) and V-02 now require the assertion for `--evidence`/`--gate-dir` and not only `--dir`. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (testing and verification) | plan V-05 (`bash -c 'printf %s ' + <emitted>` exiting 0), `agent_workflows/status_set.py:1491` (the `--actor <agent/model>` placeholder) | V-05's acceptance evidence was UNSATISFIABLE by any correct implementation. The hint deliberately contains the literal `<agent/model>` placeholder and `<` is a bash redirection operator, so bash parses the command and then fails on the redirect. Measured: the `shlex.quote` form exits 1 with `bash: line 1: agent/model: No such file or directory`; the `repr()` form exits 2 with `unexpected EOF while looking for matching '`. An executor would therefore either fail V-05 having done the work correctly, or "fix" it by quoting the placeholder, which reaches exit 0 but corrupts the literal text the caller must substitute. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and V-05 now set the bar at `shlex.split`, which decides the property that actually matters (balanced quoting) exactly: it raises `ValueError: No closing quotation` on the `repr()` form and round-trips the message as one token on the fixed form. The bash comparison is retained but restated as 2 versus 1 with the reason 0 is unreachable, and quoting the placeholder is explicitly forbidden. Recorded as F-18 and threaded into E-06(e). |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric D (anti-regression); G (honest scope) | measured: `aw ipd set reviewed <abs home path to plan> --dir <fixture> --agent` raises at HEAD | A SECOND route to the same `--agent` `ValueError` exists and this plan does not close it: `raw_args` is echoed verbatim after the reconstructed verb, so a caller who names an artifact by absolute path puts that path into the `next` field. Measured at HEAD with NO flags passed, the `--agent` call raises `Unsanitized absolute home path in field 'next'` while the `--json` call exits 2 and prints the path. Unrecorded, this would let a reader conclude from E-06(g) that `--agent` refusals are crash-free after the change, which is false. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Recorded as F-20 and added to `## Deferred / out of scope` with a `Carrier-Declined` rationale, and to the Under-scope line of the scope check. Deliberately NOT fixed here: the crash is in the SELECTOR echo rather than the flag echo, it predates and is unaffected by this plan, and repairing it means deciding how a refusal should name an artifact whose path the record may not carry, which is the same machine-contract question OQ-01's deferral already routes to the maintainer. The fix is bounding the plan's CLAIM, which is done. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` as authored | The gate carried the honesty rule, the path-scoped commit rule and the never-push rule, but was missing two required elements: a SCOPE FENCE declaring what must not be touched, and the LIFECYCLE TRANSITION statement with conditional runner/executor ownership. Its closing line instructed only "do not move this plan to executed/ until lint conforms", which states the gate without naming who performs finalize; the workflow requires the unconditional finalize obligation with the conditional owner, and requires flagging a hand-rolled `git mv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE, worded as a DECLARATION for the runner to reconcile rather than a stop directive (per the 2026-09-01 maintainer ruling), carrying four negative constraints that each close a plausible wrong turn this review actually found: do not add `-m` to two public parsers to avoid emitting a long flag (the wrong fix for PR-001), do not weaken `_HOME_PATH_RE` (the wrong fix for PR-002), do not restore the reverted flagless predicate or alter the terminal-reopen gate itself, and do not weaken any of the existing 79 tests. Added the LIFECYCLE TRANSITION paragraph with conditional ownership, the `AW-LIFECYCLE-ROLE-001` refusal, the `git mv` prohibition, and the instruction not to close backlog `pftva5` or clear its gate. |
| PR-006 | LOW | IN-SCOPE | Rubric E; G (checklist assessment) | plan E-06, V-06, `## Required tests / validation` | Consequential to PR-001 through PR-003: the verification checklist could not catch the two defects above, because no case drove the `specs` or `backlog` spellings at all (so an emitted `-m` was invisible), case (g) asserted only on `--dir` (so an echoed `--evidence` was invisible), and case (e) demanded the unsatisfiable bash exit. The plan's own stated failure modes likewise numbered three and omitted the one that most resembles correctness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 gained case (h) covering both short-alias-less spellings with re-execution; case (g) widened beyond `--dir`; case (e) restated to the `shlex.split` bar. The pre-change failure set became `(a), (b), (d), (e), (h)` in all three places it appears (E-06 expected outcome, `## Required tests / validation`, V-06). V-02 and V-06 gained the corresponding evidence demands. The gate's failure-mode list became FOUR, with the new fourth naming the `-m` trap explicitly as the one that "looks most like correctness". The `79 passed` module baseline was added to F-15 and to the validation section with the `-o addopts=""` caveat. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the emitted retry command reproduce the `-m` alias when the caller typed it, or always spell `--message` in long form? | Always emit the long `--message`. | (a) Echo the alias the caller typed, which is what E-02 implied: REJECTED as measurably broken, since `aw specs set` and `aw backlog set` do not declare `-m` and the emission exits 2. (b) Add `-m` to those two parsers so the faithful echo works: REJECTED as changing two public command surfaces to avoid emitting a longer flag name, and as an edit to `cli.py`, which is outside `- Scope-Paths:`. (c) Echo the alias only on the verbs that declare it: REJECTED as unimplementable, since the namespace records no alias, and as pointless complexity for zero gain. | `agent_workflows/cli.py:5836` and `cli.py:5525` declare only `--message`; `cli.py:4233` and the `ipd set` registration declare `--message, -m`. All four write the single dest `args.message`, measured via a namespace spy, so no information is lost by choosing the long form. Measured: `-m` exits 2 on both, `--message` exits 0 on both. | yes |
| D-2 | Which flags are echo-safe, given that the plan's authored answer (exclude `--dir` only) is incomplete? | Exclude EVERY path-valued flag (`--dir`, `--evidence`, `--gate-dir`, `--scope-reason`, `--scope-ack`) and express the echo as an allow-list of non-path flags. | (a) Exclude `--dir` only, as authored: REJECTED, since the validator is value-keyed and the authored echo list included two other flags that raise. (b) Keep a deny-list of the five known-bad flags: REJECTED because it fails open, so the next path-valued flag added to any `set` spelling would be echoed silently and crash `--agent` again. (c) Sanitize the values through `normalize_repo_path` and echo them: REJECTED because the result is not a valid `--dir` from the caller's cwd and would corrupt `--scope-reason`'s `PATH=WHY` pair, producing a command that runs against the wrong root. | `agent_workflows/agent_schema.py:63` `_HOME_PATH_RE` is applied to every string field by `_check_string_values` at `agent_schema.py:337`, so the check keys on the VALUE. Measured: all five flags raise when home-prefixed, and `aw backlog set ... --evidence <abs> --gate-dir <abs> --json` plus `aw ipd set ... --scope-reason <abs>=why --json` both reach the refusal carrying such values. | yes |
| D-3 | What is the correct parseability bar for the missing-`--actor` hint, given that V-05's `bash -c` exit 0 is unreachable? | `shlex.split` succeeding and round-tripping the message as one token; the bash comparison retained only as exit 2 versus exit 1. | (a) Keep the `bash -c` exit 0 demand: REJECTED as unsatisfiable, since the deliberate `<agent/model>` placeholder is a bash redirect. (b) Quote the placeholder to reach exit 0: REJECTED because it changes the literal text the caller is meant to substitute, defeating the placeholder's purpose, which the surrounding docstring's "never a fabricated actor" principle protects. (c) Drop the placeholder from the hint: REJECTED, as OQ-04 already resolved that the placeholder must remain literal because the flag is by definition absent. | Measured: `shlex.quote` form -> bash exit 1, `agent/model: No such file or directory`; `repr()` form -> bash exit 2, `unexpected EOF while looking for matching '`; `shlex.split` raises `ValueError: No closing quotation` on the `repr()` form and succeeds on the fixed form. The property under test is balanced quoting, which `shlex.split` decides exactly. | yes |
| D-4 | Should the pre-existing `--agent` crash on an absolute-path SELECTOR (F-20) be fixed in this plan, deferred with a carrier, or declined? | Declined with a recorded `Carrier-Declined` rationale, and the plan's claim bounded so it does not overstate what E-06(g) proves. | (a) Fix it here: REJECTED as genuine scope creep into a different mechanism (selector echo, not flag echo) whose repair needs a decision about how a refusal names an artifact the record cannot carry the path of. (b) File a backlog item: REJECTED because it is the same machine-contract question OQ-01's deferral already routes to the maintainer, so filing would duplicate a deferral rather than add information. (c) Say nothing: REJECTED as the actively harmful option, since a reader would take E-06(g) to mean `--agent` refusals are crash-free after the change. | Measured at review HEAD: the crash reproduces with NO flags passed, so it predates this plan and is unaffected by it (the same `raw_args` tokens are echoed before and after). The repository's own `Carrier-Declined` grammar (`ipd_schema.CARRIER_DECLINED_FIELD`) is the sanctioned way to record a deliberate non-carry. | yes |

No `Reversible: no` decision was made, so no escalation under the irreversible-decision rule is owed.
No finding was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question under
`review_findings_gate.block_at` (default `HIGH`) is owed either; the two HIGH findings were both FIXED.

### Checklist assessment (required for an agent-executable IPD)

The plan's CREATOR authored both checklists and both are strong. The execution checklist's six E-items each
name one concern, and the E/V bijection is 1:1 with per-item concrete evidence demands that are unusually
specific (they name the exact commands, the exact expected strings, and in several places require the HEAD
behavior pasted beside the AFTER behavior so a correction is visible as a diff rather than asserted).
Right-sizing per the density diagnostics: no E-item names multiple deliverables (E-01 and E-02 split the
helper into verb reconstruction and flag echo, which is the natural seam), none touches independent code
regions beyond the two declared files, and E-06's several cases are one deliverable (one test class on one
surface) rather than several independent test surfaces. `aw ipd lint` reported no `IPD-Z602` density
advisory at either checkpoint. No split is recommended.

The verification checklist's weakness was COVERAGE, not rigor, and it is the reason PR-006 exists: as
authored it could not have caught PR-001 or PR-002, because no case drove the two spellings where the `-m`
alias is absent and case (g) asserted only on `--dir`. That is now repaired in place (case (h) added, case
(g) widened, case (e) corrected). V-06's demand for a DELIBERATE pre-change failure run is the right
instrument and is retained, with `(h)` added to the set that must fail at HEAD, since F-12 measures that
nothing pins these strings today and a test that passes before and after would pin nothing.

The live-artifact-versus-stable-code-fact convention is satisfied: every count this plan asserts is a
stable code fact (parser-declared flags, routing dests, test-suite totals at a named HEAD) rather than a
drifting live population, so no re-derivation clause is owed.
