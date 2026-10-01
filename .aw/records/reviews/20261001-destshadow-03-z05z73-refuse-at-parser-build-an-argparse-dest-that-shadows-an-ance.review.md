# Review findings: plan z05z73

- Subject-Id: z05z73
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed), PR-907 (LOW, fixed), PR-908 (LOW, fixed), PR-909 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and unmodified before editing
(`git status --porcelain` empty on the whole tree), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with NO advisories of any
kind. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row
check does not apply. No production file, test, document or spec was modified by this review; every
probe ran in-process or against a throwaway synthetic parser tree.

THE DESIGN IS CONFIRMED SOUND AND REVIEW CHANGED NO E-ITEM'S PURPOSE. The two measurements the whole
plan turns on were re-driven independently and both reproduce exactly:

```
NARROW findings: []
parsers visited: 175 actions inspected: 2076            <-- F-02, F-04 counts EXACT

POST-BUILD PASS caught 4 of 4:                          <-- F-05, the design-deciding measurement
    ('synth direct',     'command', ('--direct',))
    ('synth viagroup',   'command', ('--grp',))
    ('synth viamx',      'command', ('--mx',))
    ('synth viaparents', 'command', ('--inherited',))
WRAPPER hits per route: direct=1 parents=0 group=0 mutex=0  TOTAL=1 of 4

per-builder subparsers census (F-02):
  oc_runipd 1 / agy_runipd 1 / upgrade_rehearsal 1 / layout_inventory 0 / oc_models 0 / pwatch 0
  all six are plain ArgumentParser                      <-- supports the Deferred declination

F-06: parser classes {_RunsArgumentParser, _AwArgumentParser}; _RunsArgumentParser subclasses
      _AwArgumentParser = True; root subparsers _parser_class = _AwArgumentParser
      _build_parser defined once (line 907), called once in _dispatch (line 14360)

F-10: total parsers reachable: 175 | viewer_parser prog 'aw runs' | reachable via choices walk: False

F-11: _build_parser lines 5665 | load_config 0 read_text 0 json.load 0 plugin 0 iter_entry_points 0

F-12: command-surface-redesign is `implemented`; occurrences of the word dest in it: 0

PR-901 timing, re-measured:
  median build 85.5 ms | median pass 0.78 ms | pass = 0.91% of build   (authored 48.8 / 0.63 / 1.29%)
  aw --help: 0.327s 0.317s 0.310s  via AW_NO_REEXEC=1 python3 -m agent_workflows
             0.429s 0.435s         via the `aw` shim (pays the re-exec)
  cold-vs-warm: import cli 108.4ms | FIRST build 158.2ms | second build 48.3ms
  => pass is ~0.25% of the command an operator waits on, NOT ~0.03%

PR-903/904 counts, re-measured:
  narrow 0 | chain-broad 1329 over 24 dests | tree-wide broad 1922 over 114 dests
  eight shared flags at 162-163 (help no_color color no_interactive interactive agent json fields)
  narrowed-broad live pairs 33 (dir 16, targets 3, version 1, + 13 singletons; runs 29, release 4)
  default=SUPPRESS leaves dest unchanged: action dest 'command' -> still 'command'

PR-906: add_subparsers() with NO dest -> dest = '==SUPPRESS==' (the default!)
        cli tree: 23 subparsers actions, 0 with dest == SUPPRESS, 0 other actions with that dest

PR-907: name-keyed child registrations 196 | distinct child parser objects 174 | 22 duplicate visits

PR-909: sq1go0 is `graduated` (Graduated-To: destshadow), not `open`
        bare python3 -m pytest -> 3892 passed, 2 skipped, 3 warnings in 77.68s  (ZERO failures)
```

Per-finding against the plan's own Findings table: F-02, F-05, F-06, F-10, F-11 and F-12 REPRODUCE
EXACTLY. F-07's quoted `_AwArgumentParser.__init__` comment reads verbatim, including the `p0l1to`
reference and the `allow_abbrev=False` twin. F-01 reproduces in substance (`8kd4eo` executed, its
OQ-02 `deferred`/`maintainer`/`Carrier: sq1go0`, the detection test present and the refusal test
absent) with its item status drifted. F-03, F-04 and F-08 each carry a figure that did not reproduce.
F-09's risk argument is sound and is confirmed by the single-builder/single-call census.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | A (correctness), F (honest documentation) | three timed `--help` runs at 0.327s / 0.317s / 0.310s; two shim runs at 0.429s / 0.435s; the cold-versus-warm probe (`import cli` 108.4ms, first build 158.2ms, second build 48.3ms) | F-04 records `aw --help` at "2.1 to 2.6 seconds" and derives the pass at "roughly 0.03 percent" of it. Measured: **0.31 seconds**, so the figure is wrong by roughly 7x and the true ratio is about **0.25 percent**, eight times thinner than claimed. This is not a cosmetic drift: that ratio is the load-bearing number in OQ-01's recommendation to the maintainer, so an approver reading the authored figure would be deciding on a number off by an order of magnitude. The conclusion survives (0.25 percent is still far below `AGENTS.md`'s perceptibility threshold) and the build-relative ratio also moved benignly (0.91 percent at review against 1.29 percent authored). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 rewritten with both readings, the corrected wall time, the 7x error named, and the likeliest cause (a cold or shim-re-exec reading) recorded. The Concern, OQ-01's recommendation, the Scope check and V-06 all carry the corrected figure; V-06 now requires the executor to state which interpreter and entry point produced its timing, since the shim and the module differ measurably |
| PR-902 | HIGH | IN-SCOPE | G (executability), A | the gate's closing Backlog-handoff paragraph against OQ-01's own `- Blocking: no` | The gate asserts "Because OQ-01 is `- Blocking: yes` and owned by the maintainer", while OQ-01 reads `- Blocking: no`. The `no` is correct and deliberate, and OQ-01 argues the case at length (this plan's own approval gate IS the decision mechanism, so a blocking flag would stall it behind a question that approving it answers). So the GATE was the error. Left as written it tells an executor or a human reader that a blocking question gates the plan when none does, and the same paragraph also claims the backlog item "moves to `graduated` on authoring" as though owed, when it is already there | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The paragraph now states `- Blocking: no` with the reason, names the contradiction explicitly so a reader of the diff sees which side was wrong, and records `sq1go0` as ALREADY `graduated` (verified) with no transition owed and an explicit prohibition on setting it `done` |
| PR-903 | MEDIUM | IN-SCOPE | G (live-artifact criteria), C | review's narrowed-broad count of 33; `zwv1sa`'s own "29 live pairs"; `zwv1sa` E-02's prohibition on `dest=` changes; the `dest` invariance of `default=SUPPRESS` driven directly | F-08's "16 live pairs" did not reproduce: review measures 33 under its own narrowing, and the sibling that owns the defect claims 29. Three numbers describe one live defect under three narrowings, so none is a usable bar, and the plan's argument for `- Item-Dependencies: none` rested on one of them. A STRICTLY BETTER ARGUMENT EXISTS and review established it: `zwv1sa` E-02 changes only `default=` and explicitly forbids changing "any `dest=`", and a `default=argparse.SUPPRESS` provably leaves an action's `dest` unchanged, so this plan's narrow-rule zero is stable across that sibling in either execution order by MECHANISM rather than by count | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 rewritten: all three counts named as narrowing-dependent and explicitly not bars, with the mechanical stability argument added as the basis for the no-dependency claim. OQ-01's summary of the same point updated |
| PR-904 | MEDIUM | IN-SCOPE | G (live-artifact criteria) | both broad readings re-measured (1329 over 24; 1922 over 114); the per-dest Counter showing eight flags at 162 to 163 | F-03's "1167 occurrences over 23 distinct dests" did not reproduce, and V-02 and the gate both use it as a comparison target. The figure is narrowing-dependent (chain reading versus tree-wide) and it drifts; the plan also lists seven shared flags at 162 where there are eight (`fields` is the eighth and is the likeliest source of the delta). The POINT is invariant and is what matters: the broad rule is three orders of magnitude from zero under every narrowing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 rewritten with both readings, the eighth flag named, and the order-of-magnitude framing made explicit. V-02 no longer compares the broad count to a constant and instead requires the measured value plus the narrowing that produced it; the gate's "DO NOT IMPLEMENT THE BROAD RULE" paragraph carries the same correction |
| PR-905 | MEDIUM | UNDER-SCOPE | G (right-sizing) | the Scope check as authored; `plan-review.md` Section G's four diagnostics | The Scope check carried over-scope and under-scope but no per-E-item right-sizing assessment, which the workflow requires be evaluated in semantic review rather than cleared by a passing count lint. This plan is a genuine case worth assessing, since E-02 carries four prohibitions and E-04 bundles four test routes | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Per-E-item assessment added: the three measurement items kept separate because they answer three different questions and E-05 reconciles against E-07 alone; E-02 kept whole because its prohibitions constrain one deliverable rather than adding deliverables; E-03 correctly separate because it is the item that changes behavior; E-04's four routes kept together because splitting them would let three land without the fourth, which is the exact failure mode F-05 measured in the rejected design |
| PR-906 | LOW | IN-SCOPE | A (correctness) | `add_subparsers()` with no `dest` returning `dest == '==SUPPRESS=='`; the cli tree's 23 subparsers actions with 0 suppressed | E-02's `SUPPRESS` exclusion reads as a defensive clause for an exotic declaration. It is the DEFAULT case: `add_subparsers()` called with no `dest` at all defaults its dest to `SUPPRESS`, so every subparsers action an author forgets to name lands there. The clause is therefore load-bearing for the first future author who adds one, even though 0 of the 23 actions in the tree are affected today | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now records that this is the default route into the case, with the measurement and the present-day zero stated so a reader knows it is prophylactic rather than currently active, and requires comparing against `argparse.SUPPRESS` rather than the raw string. V-02 additionally requires the unnamed-`add_subparsers()` route to be demonstrated, not only the explicit `dest=SUPPRESS` one |
| PR-907 | LOW | IN-SCOPE | E (evidence) | `command_surface.discover_parser_leaves`'s docstring; the 196-versus-174 measurement | E-02 justifies identity deduplication by citing "63 spurious leaves" from `discover_parser_leaves`. That figure is real but measures a DIFFERENT thing (alias leaves surfacing as undeclared in the command inventory), so it is a category error as the cost of a name walk, even though the conclusion is right. The figure that actually measures it here is 196 name-keyed registrations against 174 distinct objects, so 22 duplicate visits | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now cites the 22 with its measurement, names the 63 as measuring something else so a reader does not propagate it, and keeps the `discover_parser_leaves` citation for the identity rule itself (its docstring does say "identity (`is`) is the test"). V-02 carries the 22 as context for the alias demonstration |
| PR-908 | LOW | UNDER-SCOPE | C (architecture), F | `checkout_pin`'s `if os.environ.get("AW_NO_REEXEC") == "1":` and its self-documenting message line | E-03 specifies an `AW_`-prefixed hatch in the right shape but cites no shipped precedent, leaving the truthiness test and the message convention to the executor. A precedent exists for exactly this shape, a build-time refusal with an env escape that warns on stderr and continues, and matching it also avoids the classic defect where `if os.environ.get(VAR):` fires on `VAR=0` and the hatch cannot be turned off once exported | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names `checkout_pin` as the precedent, requires the truthy test on the literal `"1"`, stderr, and the variable named inside the message, and states the `VAR=0` trap as the reason |
| PR-909 | LOW | IN-SCOPE | G, E | `sq1go0`'s front matter; the bare suite at review; `tests/test_backlog.py`'s date normalization | Two stale live facts. F-01 says `sq1go0` is `open`; it is `graduated` with `- Graduated-To: destshadow` (which strengthens the row, since that is the correct state for a handed-off design). And three places (E-07, V-07, Required tests) carry `8kd4eo`'s expected pre-existing failure as though it will recur; the suite is green at `3892 passed, 2 skipped` and that test PASSES, because it now normalizes history dates rather than asserting a literal one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01 corrected with the item's real status and why it strengthens rather than weakens the row. E-07, V-07 and the Required tests section now state an EMPTY expected failure set, require any observed failure to be shown reproducing on an unmodified tree, and record the pass count as context rather than a bar (it moved 3246 to 3312 to 3498 to 3892) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-04's wall-time figure is wrong by ~7x and it is the number OQ-01's recommendation to the maintainer rests on. Does correcting it change the recommendation, change the readiness, or require escalation to the human before approval? | CORRECT THE FIGURE AND KEEP THE RECOMMENDATION, with the thinner margin stated explicitly so the maintainer decides on the real number. Readiness is unaffected. | (a) Escalate as a new blocking question, rejected because the corrected ratio (about 0.25 percent of a 0.31 second command) is still far below `AGENTS.md`'s user-perceptibility threshold and does not change which way the evidence points; the question the maintainer must answer is the one OQ-01 already names (is an import-time crash an acceptable failure mode), and that is untouched by the timing. (b) Set `- Readiness: no-go`, rejected because the finding is a corrected measurement in a Findings row rather than an unfixed defect in the plan's design, and it is FIXED. (c) Quietly update the number, rejected because the margin moved by 8x and an approver who read the old figure deserves to see that it moved; the correction is therefore stated in the Concern, F-04, OQ-01 and V-06 rather than only in the finding. | Three timed `--help` runs at 0.310 to 0.327s against the authored 2.1 to 2.6s; the cold-versus-warm probe locating the likely cause; the pass median at 0.78ms; `AGENTS.md`'s perceptibility test ("measure the END-TO-END command a user actually runs, warm and cold"). Recorded as the PR-901 row and in F-04. | yes |
