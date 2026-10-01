# Review findings: plan kfbom1

- Subject-Id: kfbom1
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (HIGH, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (HIGH, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (MEDIUM, fixed), PR-012 (HIGH, fixed)

## Round 1

Reviewed at HEAD `6447fe3e1` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize`
reports `conforming` after revision, with the one transient `IPD-Z602` advisory my own E-06 edit introduced
resolved by trimming that prose. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does
not apply. No production file and no test was modified by this review.

THE PLAN'S CENTRAL CASE IS CORRECT AND I RE-DROVE IT RATHER THAN ACCEPTING IT, at the real lane HEAD rather
than the authoring commit the plan cites. Every headline measurement reproduced exactly. All seven verbs
(`show`, `get`, `set`, `unset`, `add`, `remove`, `is`) exit 1 under `--agent` with 0 bytes on stdout and
`ImportError: cannot import name 'format_agent_json' from 'agent_workflows.term'` on stderr; `config exclude
list --agent` exits 0 with 103 bytes, the negative control holding. The eight import statements sit where
F-01 says, counted by enclosing function, with `_run_config_show` holding two (`grep -c` reports 16, being
8 imports plus 8 call sites). `git log --all -S "def format_agent_json"` returns only plan commits, never a
definition, so F-02's dead-on-arrival claim holds. The thirteen refusal paths reproduce with F-06's exact
per-handler distribution (show 1, and 2 each for the other six), and `config get no.such.key --agent`
writes 247 bytes of HUMAN `FAIL` text to STDOUT at rc 2 with stderr empty, matching F-06 to the byte. F-07's
deciding measurement, the one the whole route decision rests on, reproduced verbatim: a `CommandResult`
carrying `data={"key":"repos.search","value":["~/src"]}` renders to a record with neither key present, in
compact AND `verbose=True` mode alike, and `sanitize_evidence_item` returns the bare `"value"` for a list,
dict, or None while returning `"value:repos.search"` for a scalar. F-12's `--json` witnesses all emit
well-formed JSON at the expected codes. The `command_surface` declarations were read leaf by leaf and all
seven carry `agent_record_kind="result"`, `exit_contract=(0, 1, 2)`, and `legacy_flags=("--json", "--agent")`.

THEN I REBUILT ALL TEN PAYLOADS AND RAN THE REAL VALIDATOR OVER THEM, which is what produced the serious
findings, because this plan's whole premise is that the import is only the first of three stacked defects and
that premise is only as good as its arithmetic.

DEFECT ONE IN THE PLAN, AND THE ONE THAT WOULD HAVE HALTED ITS OWN EXECUTION: the refused count is EIGHT,
not six. The plan enumerated ten payloads, named two valid, listed eight refusals in its own evidence
column, and then wrote `six` in three places including a hard STOP AND REPORT gate keyed on that number. An
executor re-measuring correctly would have found eight, matched it against the gate, and stopped. The
omission is specific and visible in the plan's own text: the two `config_file`-carrying MISS payloads are
described as refused on BOTH defects and then not counted.

DEFECT TWO: THE COUNT IS NOT A STABLE CODE FACT AT ALL, so correcting six to eight would not have been
enough. Six of the eight refusals are the unsanitized-`config_file` class, and F-04 already establishes
that the validator ACCEPTS a `/tmp` path. Re-running the same probe with `config_file` under `/tmp` instead
of the operator's home leaves only two refusals, both on the outcome word. So the total is a function of the
executing operator's `XDG_CONFIG_HOME`, which is precisely the live-artifact-count pattern the review
convention says must be re-derived as a property. E-01 and the gate now demand the two-valid property and
explicitly stop treating a differing total as a stop condition.

DEFECT THREE, AND THE MOST CONSEQUENTIAL, BECAUSE THE PLAN WOULD HAVE SHIPPED A STILL-BROKEN SURFACE:
`config_file` is not the only carrier of an unsanitized home path, and the plan's E-03 named only it plus
the nested `config` mapping. `config-get` with `value=["/home/<realuser>/src"]` is refused at `value[0]`.
`config-add` with a foreign `item` is refused at BOTH `item` and `value[0]`. Those two fields hold USER
INPUT and CONFIG CONTENT respectively, reached by exactly the routes the plan's own OQ-02 argues are real
(a shared or copied `config.json`, a hand-edited entry, an argument typed at the prompt). The failure mode
is quiet and the plan's own test design hides it: an executor fixes the six `config_file` sites, runs E-05's
suite under a temp `XDG_CONFIG_HOME` whose `/tmp` path the validator accepts, sees green, and ships a verb
that raises `ValueError` the first time a real user's config holds a colleague's path. E-03 now states one
record-wide rule verified against `validate_agent_record` rather than a field list, and E-05 gains a fifth
case class driving a foreign path through `value` and through `item`.

DEFECT FOUR: THE `slow`-MARK PREMISE IS HALF FALSE AND IT CARRIED TWO CONCLUSIONS. `tests/test_config.py`
contains zero occurrences of the string `pytest`, carries no `pytestmark`, and collects 31 tests under a
bare run with nothing deselected. Only `tests/test_cli.py:29` is marked, and it reports 64 deselected. The
plan asserted both were `slow` and used it to explain WHY the defect shipped (F-11) and WHY E-05 needs a new
file. The first conclusion is simply wrong and now names the real cause: default-collected coverage of this
family exists, none of it touches `--agent`. The second conclusion survives on a better reason I verified
instead: `test_config.py` is an in-process `unittest.TestCase` suite using `redirect_stdout`, which cannot
observe a real process exit code or an import-time failure, so the harnesses are incompatible regardless of
marks.

DEFECT FIVE: THE PLAN'S OWN RECOMMENDED SANITIZER LEAKS. OQ-03 offered `agent_schema.normalize_repo_path`
as an equal remedy for the echoed argument. Measured, `normalize_repo_path("/home/<realuser>/secret")`
returns `'<realuser>/secret'`, and a record carrying that string passes `validate_agent_record` with `[]`.
So that route converts a loud `ValueError` into a SILENT local-account-name leak onto a machine surface,
invisible to the home-path rule once the `/home/` prefix is stripped, and exactly the class `aw sanitize`
exists to catch. This is a defect introduced BY the fix, in the same shape as the `enygec` defect the plan
is careful not to replicate, and it would have passed every gate the plan specified.

FINALLY, THE PLAN QUOTES A FALSE `--help` EPILOG AS SUPPORTING EVIDENCE. F-10 cited `Agent mode: --agent or
non-TTY piped emits aw.agent/v1 JSONL.` to establish the promised contract. The first clause is true and
the second is false by the 2026-09-10 maintainer ruling (`ttyflags` `yaxr4i` OQ-01) that
`docs/cli-output-contract.md` Section 9 records, and that `result_types.select_output`'s docstring already
reflects. Measured: `aw config show` redirected to a file with no `--agent` exits 0 with human prose. The
string appears at 16 sites in `cli.py`. I checked whether this was already carried: graduated item `zdjhug`
covers the renderer's `Agent output: --agent (automatic when piped)` hint in `renderers.py` plus four
conformance goldens, which is a different string in a different file reached by a different path, so fixing
one does not fix the other. Filed as new backlog `qdd6ey` (bug, medium, `Blocks-Release: next`) and declared
out of scope with that carrier, rather than folded in: `cli.py` is in `- Scope-Paths:` but this plan's fence
is eight branches and thirteen refusal paths in seven handlers, and a repo-wide string sweep would falsify
this plan's own byte-identical-human-output regression witness.

Two things the plan gets right that are worth recording because they are easy to get wrong. Its placeholder
discipline is sound and self-aware: both the leak-sanitizer's `home-path` rule and `agent_schema._HOME_PATH_RE`
allowlist `/home/<...>`, so every quoted example in the plan validates vacuously, and the plan says so and
instructs substitution. I verified both halves and then used a real non-placeholder name throughout my own
probes, which is the only reason the `value`/`item` gap was visible. And its Carrier-Declined rows each
meet the bar: the `--json` branches genuinely are not broken (measured), the `agent_schema` widening
genuinely would invert the fix, and the `result_types` payload-channel question genuinely is a maintainer's
public-contract decision rather than a defect this plan established.

I did NOT run the bare suite as a review baseline, because this review modified no production file or test
and the plan's own E-01 is what must establish the executing baseline. F-13's authored counts are now
labelled context rather than a bar, for the same live-population reason as PR-002.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (executability), E (verification) | Probe over all ten payloads vs `agent_schema.validate_agent_record` at `6447fe3e1`: `refused count = 8`; plan's F-03, Concern, history, E-01 and gate each said `six` | The refused-payload count is EIGHT, not six; the plan's own evidence column lists eight refusals and then states six. This is not arithmetic trivia: the `## Approval and execution gate` made `is not six` a hard STOP AND REPORT condition, so a correctly re-measuring executor would halt the plan on its own true measurement | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 corrected to eight with the two omitted miss payloads named; the Concern, history line, E-01, proposed-change 1, V-01 and the gate all swept; the gate's stop condition re-keyed onto the property per PR-002 |
| PR-002 | MEDIUM | IN-SCOPE | G (live-artifact criteria) | Same probe with `config_file="/tmp/x/agent-workflows/config.json"`: only 2 refusals remain, both on the outcome word. F-04 already records `/tmp` as ACCEPTED | The refused total is a LIVE, machine-dependent figure (six of eight refusals depend on where the operator's config lives), so pinning any number as a gate violates the re-derivation convention. Correcting six to eight alone would have left a gate that fires on a `/tmp` `XDG_CONFIG_HOME` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-03a records the machine-dependence; E-01, V-01 and the gate now require the TWO-VALID PROPERTY (`config-get` and `config-is` hit validate; `config-is` miss refuses on the outcome word alone) and expressly state a differing total is NOT a stop condition |
| PR-003 | LOW | IN-SCOPE | G (consistency) | `- Concern:` and the `to-review` history line both read `six ValueError`s | Two prose sites repeated the superseded count, which is the stale-sibling sweep the review convention requires after a correction | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both updated to eight, the history line marked as corrected at review so the record shows the change rather than hiding it |
| PR-004 | HIGH | IN-SCOPE | E (testing), F (honest documentation) | `tests/test_config.py` contains 0 occurrences of `pytest`; `pytest tests/test_config.py --collect-only -q` -> `tests/test_config.py: 31`; `tests/test_cli.py:29` has `pytestmark = pytest.mark.slow` and reports `64 tests were deselected` | The plan asserts BOTH owning suites are `slow`-marked and deselected. False for `test_config.py`, which is default-collected. Two conclusions rest on it: F-11's account of why the defect shipped, and E-05's justification for a new file. The first is wrong; the second needed a real reason | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions bullet, F-11, E-05 and the E-06/Required-tests `-o addopts=""` rationale all corrected with the measured collect counts; E-05's new-file reason restated as HARNESS INCOMPATIBILITY (in-process `unittest` + `redirect_stdout` cannot see a real exit code or an import-time failure) |
| PR-005 | LOW | IN-SCOPE | E (validation commands) | `pyproject.toml:171` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` | The plan quotes the marker expression as `-m 'not slow'`, omitting `not livecorpus`, so E-05's "keep it out of the deselected set" instruction under-specifies which marks are disqualifying | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and E-05 quote the full expression; E-05 now forbids BOTH marks; E-06 notes that clearing `addopts` also clears `-n auto` so the serial slowdown is expected |
| PR-006 | LOW | IN-SCOPE | G (traceability) | Scope-Paths justification, spec-sync bullet, and the gate each cite `E-06` / `E-06e` / `E-06(f)` for the CHANGELOG line and the `f36de0` report, both owned by E-07 | Three cross-references point at the wrong E-item after the plan grew from six items to seven, so an executor reading the gate looks for the reconciliation instruction in the regression item | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three re-pointed at E-07 |
| PR-007 | LOW | IN-SCOPE | G (size assessment) | Plan has 7 `- [ ] E-` leaves and 7 `V-` items, `- Highest E allocated: 07`; the gate says `Six E-items` | The cohesion rationale miscounts its own checklist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to seven, with the prior value noted so the correction is visible |
| PR-008 | HIGH | UNDER-SCOPE | A (correctness), B (privacy), E (testing) | `config-get` with `value=["/home/<realuser>/src"]` -> refused at `value[0]`; `config-add` with foreign `item` -> refused at BOTH `item` and `value[0]`. F-04: a `/tmp` `config_file` is ACCEPTED | E-03 names only `config_file` and the nested `config` mapping as path carriers. `item` and `value` are independent carriers holding user input and config content. Worse, E-05's temp-`XDG_CONFIG_HOME` design cannot see the gap, so the executor would fix six sites, pass a green suite, and still emit a `ValueError` on a real user's config | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-04a records the measurement; E-03 replaced the field list with ONE record-wide rule verified against `validate_agent_record`, and names `_preserve_home` for own-home vs `normalize_repo_path` for foreign; E-05 gains case class (e) (`config get` exercising `value`, `config is` exercising `item`) and an explicit warning that the temp `/tmp` config hides defect 3; V-03 and V-05 demand the new evidence and a real non-placeholder user name |
| PR-009 | MEDIUM | IN-SCOPE | F (honest documentation) | `docs/cli-output-contract.md` Section 9 (RETRACTED, ttyflags `yaxr4i` OQ-01, 2026-09-10); `result_types.select_output` docstring; `aw config show` redirected to a file -> rc 0, human prose; 16 occurrences of the epilog in `cli.py` | F-10 cites the `--help` epilog `Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.` as the promised contract, but its second clause promises the auto-switch that was retracted and never shipped. Quoting it as a spec risks an executor writing a test asserting the piped case | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10a records the retraction with its citations and forbids treating the epilog as a behavior spec; checked against graduated `zdjhug` and confirmed DISTINCT (that is `renderers.py`'s rendered hint plus four goldens); filed new backlog `qdd6ey` and added a Deferred row carrying it, rather than folding a repo-wide string sweep into a plan whose human-output witness must stay byte-identical |
| PR-010 | LOW | IN-SCOPE | E (evidence precision) | Per-handler counts re-measured by enclosing function: fail/exit-2 paths show 1, get 2, set 2, unset 2, add 2, remove 2, is 2 = 13; imports show 2, others 1 each = 8 | F-01 and F-06's counts are correct but were stated without the measurement method, and `grep -c format_agent_json` returns 16 rather than 8, which an executor re-checking crudely would read as a discrepancy | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01 now states the by-function method, the 16 = 8 imports + 8 call sites decomposition, and the review re-measurement; E-04 records the confirmed thirteen with its distribution |
| PR-011 | MEDIUM | IN-SCOPE | A (correctness), G (scope fence) | `_run_config_remove` and `_run_config_is` each carry one `term.status("warn", ...)` + `return 1`; validator refuses an `error` record at exit 1 (`Error record must carry exit=2, got exit=1`) | E-04 says "every refusal path" emits an exit-2 `error` record and enumerates only the thirteen `fail` sites. The two `warn` + exit-1 miss paths are adjacent, unenumerated, and belong to defect 2 (E-03). An executor sweeping "refusal paths" could convert one and produce a record the validator refuses | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now explicitly excludes the two `warn`/exit-1 paths, states they are E-03's territory, and gives the measured reason (a miss is a legitimate exit-1 finding, and an `error` record at exit 1 is refused); its Expected outcome narrowed to exit 2 only |
| PR-012 | HIGH | IN-SCOPE | B (privacy / data minimization) | `agent_schema.normalize_repo_path("/home/<realuser>/secret")` -> `'<realuser>/secret'`; a record carrying that string passes `validate_agent_record` with `[]` | OQ-03 offers `normalize_repo_path` as an equal remedy for the echoed argument. It satisfies the validator while RETAINING THE USERNAME, so it trades a loud `ValueError` for a silent local-account leak onto a machine surface, invisible to the home-path rule. This is a defect introduced by the fix itself, of the same class as the `enygec` defect the plan is careful not to replicate | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | OQ-03 narrowed: omission recommended, `normalize_repo_path` alone declared insufficient for this field with the measurement quoted, and non-identifying reduction offered as the alternative; E-04 carries the same warning inline; V-04 now requires the record shown free of any local account name, plus pasted `aw sanitize --agent` evidence if that function is used anyway |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's gate stops execution if the refused-payload count is not six, and the true count is eight AND machine-dependent. Correct the number, or replace the number with a property? | Replace it with the two-valid PROPERTY and state explicitly that a differing total is not a stop condition, keeping eight in F-03 as the measured figure | (a) Just correct six to eight: REJECTED, because the probe shows six of the eight refusals vanish under a `/tmp` `XDG_CONFIG_HOME`, so the corrected number would still fire falsely on a legitimate executing environment. (b) Delete the stop condition entirely: REJECTED, because it guards a real premise (that `agent_schema`, `config.load`, or a handler has not moved), and the property preserves that guard | Measured both totals (8 under a home-dir config, 2 under `/tmp`) against `agent_schema.validate_agent_record`; the plan-review convention on live-artifact success criteria requires a property plus re-derivation where a count drifts, and exempts stable code facts, which this is not | yes |
| D-2 | The `--help` epilog's non-TTY clause is false. Fix it in this plan (`cli.py` is already in Scope-Paths), file a carrier, or just record it? | File new backlog `qdd6ey` and declare it out of scope with that carrier | (a) Fix it here: REJECTED, because the string is at 16 sites spanning the whole CLI while this plan's fence is eight branches in seven handlers, and changing human help text would falsify this plan's own byte-identical-human-output regression witness (E-06d, V-03). (b) Attach it to graduated `zdjhug`: REJECTED after checking, because `zdjhug` is `renderers.py`'s rendered result hint plus four conformance goldens, a different string in a different file reached by a different path; fixing one does not fix the other, so folding them would hide one defect behind another's closure. (c) Record only in F-10a: REJECTED, because it is a live `bug`-kind user-visible defect and AGENTS.md requires a live bug to carry a release gate, which only a filed artifact can do | `docs/cli-output-contract.md` Section 9 records the retraction as a maintainer ruling; `result_types.select_output`'s docstring confirms the resolver never consulted `stdout.isatty()`; measured `aw config show` redirected to a file emitting human prose at rc 0; `zdjhug`'s own summary and body name `renderers.py` and the four goldens | yes |
| D-3 | OQ-03 offers two remedies for the echoed argument and `normalize_repo_path` leaks the username while passing the validator. Narrow the question, reopen it for the maintainer, or leave the executor's choice intact? | Narrow it: recommend omission, declare `normalize_repo_path` alone insufficient for this field, and require extra `aw sanitize --agent` evidence if it is used anyway | (a) Leave both remedies equal: REJECTED, because the plan presents them as equally conforming and one of them silently leaks a local account name, so an executor following the plan faithfully could ship the leak. (b) Reopen as `Blocking: yes` for the maintainer: REJECTED, because the repository already answers it; `aw sanitize`'s existence and the `enygec` item establish that a local account name on a public surface is a defect, so this is evidence-resolvable and not a risk-appetite call. (c) Mandate omission outright: NOT taken, because a non-identifying reduction (a basename, a marker) is equally safe and keeps a diagnostic hint, and foreclosing it would be a design choice I have no basis to impose | Measured `normalize_repo_path("/home/<realuser>/secret")` -> `'<realuser>/secret'` validating with `[]`, i.e. validator-clean and leak-dirty; AGENTS.md's leak-sanitizer paragraph makes `aw sanitize` the authority for this class rather than hand-judgement; the plan's own F-09 and the `enygec` carrier establish the class as a defect | yes |
| D-4 | E-03 named `config_file` and the nested `config` mapping as the path carriers, and `item`/`value` are also carriers. Add them to the field list, or restate the rule? | Restate as ONE record-wide rule verified against `validate_agent_record`, and add a test case class for the two newly found carriers | (a) Extend the field list to four names: REJECTED, because a field-by-field audit is exactly what produced the gap, and a fifth carrier added later by an unrelated change would reopen it. (b) Add the cases to E-05 without changing E-03: REJECTED, because the test would then go red with no instruction telling the executor what the fix is | Measured `value[0]` and `item` refusals directly; `agent_schema._check_string_values` recurses every dict and list and reports a dotted path, so the validator itself is field-agnostic and the rule should be too | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Twelve findings, all FIXED in place, none deferred, none left open. No
unfixed finding at or above the `HIGH` gate threshold, so no escalation to a `- Blocking: yes` question is
owed. The plan's three pre-existing open questions all remain `- Blocking: no` and `- Status: resolved`;
OQ-03's resolution was narrowed rather than reopened (D-3). `- Status:` set to `reviewed` and
`- Readiness: go-pending-approval`. Human approval is still required before execution.
