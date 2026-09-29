# Review findings: plan t38a4o

- Subject-Id: t38a4o
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2aabfd66` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and after revision `--phase
review-finalize` conforms with ZERO advisories and zero diagnostics. No pre-review snapshot was owed:
the plan was committed and unmodified (`git status --porcelain` showed no entry for it). No production
or test file was modified by this review; every measurement ran either read-only against this tree or
in throwaway `tempfile` git repos, from probe scripts under the gitignored `.aw/state/`.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS CENTRAL DESIGN INSIGHT IS THE RIGHT ONE. F-1 reproduces
verbatim (all four next-generation tokens refused, `gemini4pro` hinted onto the DIFFERENT model
`gemini31pro`). F-2 reproduces exactly, by both routes and with the outage confirmed: a scratch repo
with a known-model control plus one unknown model in frontmatter gave
`frontmatter-invalid: model: unknown model 'gemini4pro'`, exit 1, `INDEX.json exists: False`, and the
filename-facet variant gave `name-invalid` with the same outage, while the control alone wrote
`INDEX.json` with 1 doc. F-5's constraint is real and is the plan's best call: `suggest_metadata` uses
`normalize_model(...).ok` as the facet DETECTOR, measured today as
`some-report.gemini31prohigh.agy.md -> gemini31prohigh` and `some-report.gemini4pro.agy.md -> None`,
so the `recognized` flag rather than flipping `ok` is correct. F-3, F-4, F-6, F-11, F-12, F-13 and
F-15 all reproduce as written; F-11's spec text matches verbatim, and F-13's claim that the suite has
essentially no coverage is confirmed (`test_unknown_model_rejected`'s `assertIn("unknown model", err)`
is the ONLY model-vocabulary assertion in the tree).

WHAT REVIEW FOUND IS THAT THREE ITEMS, AS AUTHORED, WOULD EACH HAVE SHIPPED A DEFECT, and one of them
would have silently undone the plan's own headline fix.

**E-07 WOULD HAVE RESTORED THE F-2 OUTAGE, AND `info` DOES NOT PREVENT IT (PR-701, BLOCKER).** The
plan reasons carefully that `info` is the unique non-failing severity, and that reasoning is correct
for the surface it examined. But `drift_exit_code` governs the `--check` branch ONLY. `run_index`'s
REGENERATE branch, the one that writes `INDEX.json`, tests raw truthiness (`if drift: ... return 1`
under the comment "Refuse to write over invalid input") and never reads severity, while per-doc drift
from `_doc_entry`/`_scan_docs` flows into BOTH branches. Simulated against the shipped code with the
advisory emitted from `_doc_entry`: `drift_exit_code(drift) = 0` so `--check` PASSED, yet
`aw research index` returned `exit: 1` with `INDEX.json written: False`. So an advisory that fails
nothing would have blackholed the manifest exactly as the unfixed bug does. FIXED: E-07 now specifies
emission in `check_drift`, demonstrated to confine it (regenerate `exit: 0`,
`indexed models: ['sonnet5', 'gemini4pro']`; `--check` exit 0 with the advisory still printed), which
also covers `aw check research` since `check_engine` calls the same producer. V-07 now demands the
bare-`index` run as a named regression guard.

**E-05's SYNTAX GATE LEFT A RESIDUAL OUTAGE FOR THE COMMONEST REAL SPELLING (PR-702, HIGH).** E-05
refused any token that is not `[a-z0-9]+` on the strength of F-7. A filename facet is split on `.`, so
a hyphen is legal inside one, and a hyphenated UNKNOWN model has no `MODEL_NORMALIZATIONS` entry
(only known spellings do). Simulated with the exact authored contract, a repo holding one
`gemini-4-pro` doc plus a `sonnet5` control gave
`name-invalid: malformed model token 'gemini-4-pro'` then `exit: 1  INDEX.json written: False`: the
F-2 outage survives the fix. This is not a corner case, because 21 of the 22 `MODEL_NORMALIZATIONS`
KEYS are hyphenated, which is the corpus telling us hyphenated input is how models are written.
FIXED: the gate is `[a-z0-9-]+`, verified arity-safe (`format_name` with `gemini-4-pro` yields a
3-segment stem that `parse_name` round-trips) while a dot, space, underscore and empty still fail.
Hyphen-STRIPPING was considered and rejected: it reproduces only 20 of 22 existing mappings. Raised as
OQ-03 rather than silently applied, because it widens the set of accepted filenames.

**E-02/E-03 PRESUPPOSE A REPO ROOT NOTHING RECEIVES, AND THE OBVIOUS SHORTCUT IS WRONG (PR-703,
HIGH).** E-02 specifies `model_vocab.load(repo_root)` and E-03 a cache "keyed on the resolved repo
root", but `normalize_model(token)`, `parse_name(filename)` and `validate_frontmatter(data)` take no
root, so no item delivers the wiring. The only root-free source is a cwd climb, and measured with cwd
in repo A (blessing `deepseek4`) and `--dir` repo B (blessing nothing),
`project_context.resolve_verb_repo_root` returned A for the climb and B for the verb: `SAME ROOT:
False`. A cwd-climbing loader therefore validates one repository's documents against another's blessed
tokens. FIXED: new E-10 owns the threading, names two acceptable mechanisms, forbids the cwd climb,
requires the no-root default to be the package default alone, and carries the measured call-site
census (4/14/1 production calls) so the cost is known. New V-10 demands the two-repo transcript.

**E-08 WOULD HAVE TURNED THE SUITE RED (PR-704, HIGH).** E-08 says to wire the verb into `cli.py` and
the help table, and names neither `command_surface.COMMAND_INVENTORY` nor the conformance matrix.
Measured by adding a bare `research add-model` leaf to the built parser: `find_undeclared_leaves` went
`[]` -> `['research add-model']` and `build_matrix().undeclared` likewise, so
`test_zero_undeclared_parser_leaves` fails. FIXED: E-08 now requires the declaration (as a
`dry_run_default` mutation matching its `research mv`/`research promote` neighbours),
`command_surface.py` is in `- Scope-Paths:`, and `test_command_surface_declarations.py` joins the
focused suite.

**E-02's TOML-READER BRANCH IS CONDITIONAL ON A SETTLED FACT (PR-705, MEDIUM).** E-02 said to extend
the minimal reader "if that reader cannot express the `from = "to"` pairs", which is an undemonstrated
escape hatch. Measured on the E-01 file shape, `_parse_simple_toml_lists` returns
`{'models': [...]}` and `_parse_simple_toml_bools` returns `{}`: neither reads the pairs, so the
extension is MANDATORY. Also measured and newly recorded: the reader is SECTION-BLIND (two `models =`
keys under different `[section]` headers collapse last-wins), which constrains the E-01 file shape.
FIXED: E-02 states the extension as required, records the section-blindness, and
`leak_sanitizer.py` is in `- Scope-Paths:`.

**THREE MEASURED NUMBERS IN THE PLAN ARE WRONG (PR-706, LOW).** `MODEL_NORMALIZATIONS` has 22 entries,
not the 20 that E-01 and V-01 both assert. F-8's "at least twice per document" over-counts: instrumented
over the live corpus, one `_scan_docs` pass makes 130 calls for 123 indexed docs (1.06 per doc, because a
doc with no model facet skips the `parse_name` call), though the whole-run total of 267 does clear the
"at least 260" bar, so E-03's conclusion survives intact. F-8's 2.7s timing re-measured at
`real 0m1.480s`, and F-14's `3217 passed` baseline is now `3246 passed, 2 skipped, 3 warnings in
50.64s`. FIXED: each corrected in place, and V-01/V-03/V-09 now demand RE-DERIVATION at execution time
instead of comparing against a digit written in the plan, since two of these drifted within a day.

**TWO REASSURING NON-FINDINGS, recorded so an executor does not re-derive them.** Relaxing the model
gate does NOT widen research CITATION recognition: `iter_id6_citations` counts a filename token only
if `parse_name` succeeds, so accepting more tokens could have produced new `dangling-citation` drift,
but simulated over the full 1853-file scan population it produced `files gaining NEW citations: 0` and
`NEW citations that would DANGLE: 0` (new F-25). And F-9's packaging conclusion is confirmed
empirically for the SDIST as well as the wheel: a build from a copy of this tree carrying a probe data
file put `agent_workflows/data/research-models.toml` in both artifacts with no `pyproject.toml` edit
(new F-26), so that path is declared-but-expected-unmodified and needs a `--scope-ack`.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 and OQ-02 both survive review and are upheld, OQ-01 the more strongly because PR-702
demonstrates the very failure mode OQ-01 reasons about (a refusing gate causing the F-2 outage)
actually occurring. New OQ-03 records the hyphen decision as non-blocking and reversible.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | blocker | IN-SCOPE | A. Correctness / C. Architecture | `agent_workflows/research_index.py` `run_index` regenerate branch ("Refuse to write over invalid input", `if drift: return 1`) vs `artifact_core.drift_exit_code`; `_doc_entry`/`_scan_docs` feeding both branches; simulation with the advisory in `_doc_entry` giving `drift_exit_code = 0` while `run_index` gave `exit: 1`, `INDEX.json written: False` | E-07's new `info`-severity advisory, emitted from the per-doc producer, silently RESTORES the F-2 total-index outage that E-06 exists to remove. `info` protects only the `--check` branch; the regenerate branch reads raw truthiness and never consults severity. | C:Low; U:Low; S:Low; F:High; Overall:Medium | fixed | E-07 now specifies emission in `check_drift`, demonstrated to leave regenerate `exit: 0` with the doc indexed and `--check` exit 0; V-07 demands the bare-`index` regression guard; new F-21; the gate now names it as the most dangerous of the three review findings. |
| PR-702 | high | IN-SCOPE | A. Correctness / D. Anti-regression | plan E-05 + F-7; simulation of the authored contract giving `name-invalid: malformed model token 'gemini-4-pro'`, `exit: 1`, `INDEX.json written: False`; 21 of 22 `MODEL_NORMALIZATIONS` keys hyphenated; `format_name`/`parse_name` round-trip on `gemini-4-pro` | The authored `[a-z0-9]+` syntax gate refuses a hyphen, which leaves the F-2 outage intact for a hyphenated unknown model, the commonest real-world spelling. F-7's premise is true of CANONICAL tokens only and does not license refusing hyphenated INPUT. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | fixed | Gate widened to `[a-z0-9-]+` (dot, space, underscore, empty still refused), verified arity-safe; hyphen-stripping rejected on the 20-of-22 mapping measurement; F-7 narrowed; new F-20; raised as OQ-03 because it widens accepted filenames. |
| PR-703 | high | IN-SCOPE | C. Architecture and operability | `normalize_model(token: str)`, `parse_name(filename: str)`, `validate_frontmatter(data: Dict)` signatures (no root); `research_index._roots` resolving via `project_context.resolve_verb_repo_root(args.dir)`; two-repo measurement returning `SAME ROOT: False` | E-02/E-03 presuppose a `repo_root` that no function in the validation chain receives, and no item delivers the wiring. The only root-free mechanism (climbing from cwd) validates repo B's documents against repo A's blessed tokens. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | New E-10 owns the threading with two named mechanisms, forbids the cwd climb, fixes the no-root default to the package default, and carries the call-site census; new V-10 demands the two-repo transcript; E-03 now depends on E-10; new F-22. |
| PR-704 | high | IN-SCOPE | E. Testing and verification | adding a bare `research add-model` leaf to `cli._build_parser()`: `find_undeclared_leaves` `[]` -> `['research add-model']`, `conformance_matrix.build_matrix().undeclared` likewise; `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` | E-08 adds a parser leaf without a `CommandDeclaration`, which is a hard, shipped gate rather than bookkeeping, so the suite goes red. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-08 now requires the declaration with its class and flags specified; `command_surface.py` added to `- Scope-Paths:`; `test_command_surface_declarations.py` added to the focused suite; V-08 demands `find_undeclared_leaves` empty; new F-23. |
| PR-705 | medium | IN-SCOPE | G. Plan executability | `_parse_simple_toml_lists` on the E-01 shape returning `{'models': [...]}` and `_parse_simple_toml_bools` returning `{}`; section-blindness measured as `{'models': ['b']}` for two same-named keys under different headers | E-02's "if that reader cannot express the pairs" is conditional on a fact already settled against it, so the extension is mandatory and an executor could wrongly skip it; and the reader's section-blindness constrains the E-01 file shape but was unrecorded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 states the extension as required with the measurement, records section-blindness and its constraint on E-01; `leak_sanitizer.py` added to `- Scope-Paths:`; V-02 demands the diff and the section-handling statement; new F-24. |
| PR-706 | low | IN-SCOPE | Evidence accuracy | `len(MODEL_NORMALIZATIONS) == 22` against the plan's "20 entries"; instrumented counter giving 130 calls per `_scan_docs` pass over 123 entries (1.06/doc) and 267 per `--check` run; `time aw research index --check` -> `real 0m1.480s`; bare suite -> `3246 passed, 2 skipped` | Four measured digits are wrong or stale: the normalization count (22 not 20), F-8's per-doc call rate (1.06 not 2, though its per-run total holds and its conclusion survives), F-8's 2.7s timing, and F-14's 3217-test baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Each corrected in place with the measurement; E-01/V-01/V-03/V-09 rewritten to demand RE-DERIVATION at execution time rather than comparison against a plan-written digit, since two of the four drifted within a day. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-07's advisory re-blocks the manifest write. Emit it from a check-only producer, or make the regenerate branch severity-aware? | Emit from `research_index.check_drift`, leaving the regenerate branch's refuse-on-invalid-input rule untouched. | (a) Make the regenerate branch call `drift_exit_code` instead of raw truthiness: rejected as out of scope and materially riskier, because it would change the write/refuse decision for EVERY existing drift class at once, reopening the "one bad doc blocks all 130" design question the plan's own Scope check explicitly declines. (b) Emit from `_doc_entry` and filter in the regenerate branch: rejected as a second place the severity convention lives, which is the forked-predicate shape this repo avoids. | `run_index`'s regenerate branch reading raw truthiness while `check_drift` appends its own rule families; demonstration that emission in `check_drift` gives regenerate `exit: 0` with the doc indexed and `--check` exit 0; `check_engine` calling `_ridx.check_drift` so one emission serves both surfaces. | yes |
| D-2 | Should the syntax gate admit a hyphen, widening what filenames this repo accepts? | Admit it (`[a-z0-9-]+`), record the token verbatim. | (a) Keep `[a-z0-9]+`: rejected on the measured residual outage for `gemini-4-pro` plus 21-of-22 hyphenated normalization keys. (b) Strip hyphens and collapse: rejected because it reproduces only 20 of 22 existing mappings and contradicts OQ-02's verbatim rule. (c) Leave it open and blocking: rejected because the repository answers it, but it IS recorded as OQ-03 since it widens a public contract. | Simulation giving `exit: 1  INDEX.json written: False` for a hyphenated unknown model; 21/22 hyphenated keys; `format_name`/`parse_name` round-trip proving arity safety; the 20-of-22 stripping measurement. | yes |
| D-3 | E-02/E-03 need a repo root the functions never receive. Pick the mechanism for the plan, or leave it to the executor? | Add E-10 that FORBIDS the cwd climb and names two acceptable mechanisms, leaving the choice between those two to the executor with V-10 demanding a statement of which. | (a) Mandate the optional-keyword form: rejected as over-prescribing an implementation detail the executor can judge better with the code in front of them, when both forms satisfy the property. (b) Leave E-02/E-03 as written: rejected because the cwd climb is the path of least resistance and is measurably wrong. (c) Raise it blocking: rejected because the correctness property (never infer from cwd) is derivable from repository evidence, and only the mechanism is open. | The three signatures taking no root; `SAME ROOT: False` for cwd-climb vs `--dir`; the measured call-site census bounding the threading cost. | yes |
| D-4 | Four measured digits in the plan are wrong or stale. Correct them, or also change how the plan expresses measured bars? | Correct each in place AND rewrite the affected validation items to demand re-derivation at execution time. | (a) Correct the digits only: rejected because two of the four drifted within one day, so a corrected digit is a defect in waiting; the workflow's own live-artifact convention says a drifting count belongs in prose as context and never as the bar. (b) Delete the numbers: rejected because they are genuinely useful as context for sizing the work. | `len(MODEL_NORMALIZATIONS) == 22` vs "20"; 1.06 calls/doc vs "at least twice"; 1.480s vs 2.7s; 3246 vs 3217 passed. | yes |
