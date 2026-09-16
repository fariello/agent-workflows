# Review findings: plan 3dki3o

- Subject-Id: 3dki3o
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `6a3a671c`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the LAST of the
nine `rununify` children and the fifth and final split child.

EVERY NUMBER REPRODUCES AND THE INFERENCE INVERTS, exactly as it did for sibling `s16omw`. Verified: 297
oc source lines and 205 agy; 133/111 AST-normalized lines with docstrings stripped; exactly 46 differing
lines; exactly 8 bearing a host token; SequenceMatcher similarity 0.8115, the middle of the five. But a
host TOKEN is the wrong discriminator here, and this is the whole point. Classified BY CAUSE, the 46 lines
are 19 host CAPABILITY, 10 host LABEL, and 17 drift; and 12 of the 17 are one two-line style difference
(`hint = render_continuation_hint(...)` then `print(hint)` versus an inline `print`) repeated twice, plus a
block reordering that changes nothing. THE REAL DRIFT IS ABOUT FIVE LINES OUT OF 133. The 19 capability
lines are oc's entire `as <profile>` grammar (`extract_profile_clause`, `ProfileClauseError`, the
resume-refusal, `print_launch_identity`) plus its `--verify-with`/`--validate`/`--variant` resume handling,
against agy's single `--agy-executable`. So `main` is the most CAPABILITY-divergent of the five, and the
Concern's boilerplate "mostly drift" sentence is false for it while the plan's own F-1 is right.

I MEASURED THE FLAG SURFACE THE RESUME BRANCH READS, because for an entry point the unit of divergence is
a flag one host owns. On `resume`, oc has 8 flags agy lacks (`--audit`, `--no-audit`, `--no-validate`,
`--no-verify`, `--validate`, `--variant`, `--verify`, `--verify-with`) and agy has 2 oc lacks (`--agy`,
`--agy-executable`). Measured on the built parsers, `validate`, `variant` and `verify_with` resolve to NO
option string at all on agy, so the three `getattr(args, ...)` blocks oc's `main` runs are unreachable
there by construction, not by omission.

THE SHARPEST FINDING IS ONE NO SIBLING REVIEW LOOKED FOR, AND IT FAILS SILENTLY. `main` is not merely
SOURCE-pinned (four pins, F-8, which is the obstacle three sibling reviews found); it is
MONKEYPATCH-pinned. 26 `mock.patch.object(<host module>, "<name>")` sites across four test files replace
names `main` resolves at MODULE level: `run_queue` 7x, `locked_run` 6x, `build_parser` 3x,
`resolve_run_dir` 3x, `install_stop_triggers` 2x, `emit_shutdown_report` 2x, `load_state` 2x,
`initialize_run` 1x. A function living in `runner_shared` resolves those as ITS OWN globals, so patching
the host module does not reach it. I proved the mechanism by construction in a scratch probe rather than
asserting it: an import-time-frozen descriptor returned the REAL object while a call-time reference
honored the patch, so whether any given seam survives depends on a design detail the plan never specifies.
WHY THIS MATTERS MORE THAN THE SOURCE PINS: a broken source pin fails loudly at its assertion, but a lost
patch seam makes the test execute the REAL `run_queue`, the REAL `locked_run` and the REAL `initialize_run`
against a temp repo, and it may still pass while asserting nothing it claims to. `tests/test_oc_runipd.py:4123`'s
`_parse_argv` helper is built entirely on that seam and backs 12 launch-profile grammar assertions.

I ALSO PROVED THE EXIT-CODE HAZARD, AND IT IS NOT THE ONE F-2 NAMES. F-2 warns against renumbering an exit
code, which is the kind of mistake a reviewer catches. The real mechanism is invisible: `oc.EmptyStatusSelection`
and `agy.EmptyStatusSelection` are DISTINCT classes, both direct subclasses of the SHARED
`runner_shared.DriverError`, and neither subclasses the other (`issubclass(agy.ESS, oc.ESS)` is False).
Both hosts order `except EmptyStatusSelection` before `except DriverError` precisely because of that
relationship. A shared core resolving that name against ONE host therefore lets the other host's instance
fall through to the `DriverError` arm and return 2 where spec `25kzda` 2.4a property 3 requires 0. In my
probe the same core returned 0 for the matching class and 2 for the sibling class, printing the wrong
message. THE GOOD NEWS, recorded because it changes the risk rather than the design:
`tests/test_run_flag_surface.py:1787` and `tests/test_agy_runipd_cli.py:1200` already assert exit 0 through
`main` on both hosts, so this break would be caught loudly. E-03 adds the structural half neither asserts.

TWO OF THE PLAN'S FIVE FINDINGS ARE FACTUALLY WRONG AND I RETRACTED BOTH IN PLACE. F-5 says oc resolves the
`opencode` binary in `main` and agy resolves via `resolve_agy`: neither host's `main` resolves a binary at
all (`resolve_agy` is called once, at `agy_runipd.py:3010`, in the turn-launch path), so the ONE difference
the plan called genuinely host-specific is not in the symbol. F-3 says each host routes its own verbs: the
two hosts route the IDENTICAL five verbs and `tests/test_runner_stop_triggers.py:1041` asserts their
`subcommands` sets EQUAL, so there is no routing table to parameterize. F-2 additionally cites
`tests/test_exit_codes.py`, WHICH DOES NOT EXIST (the repository's file is `tests/test_json_and_exitcodes.py`,
which tests `cli.main` and never touches a runner), and paraphrases the spec's exit-code table wrongly.

ONE HARD CONSTRAINT ON THE HOOK BOUNDARY THAT THE PLAN COULD NOT HAVE HONORED, because it does not mention
it: `tests/test_runner_stop_triggers.py:1001` and `:1055` REGEX `subcommands = \{(.*?)\}` out of BOTH runner
SOURCE FILES and require the two literals to be equal, and both runners carry a KEEP-THIS-INLINE comment
recording that hoisting the set into a constant makes the guard "silently unmatchable (measured: it fails
with unexpectedly None)". So the implicit-start shim cannot move into a shared core without rewriting the
guard that stops `stop <run-id>` being rewritten to `start stop <run-id>` in one driver only.

WHAT I FIXED AND WHAT I LEFT. I corrected the Concern with the by-cause classification; retracted F-5 and
corrected F-3 and F-2 with citations; added F-6 (the Concern/F-1 contradiction), F-7 (the
`EmptyStatusSelection` mechanism, proven), F-8 (the four source pins), F-9 (the 26 patch seams), F-10 (the
pinned `save_state`/`print_status` call-site census, of which `main` holds 6/5 and 2/2), F-11
(right-sizing) and F-12 (the dependency edge pointing at a `no-go` sibling); added the closure table to the
Goal and the inline-literal constraint plus the corrected runner-to-runner-import fact to Project
conventions; restructured one bundled E-item into six single-concern items; fenced the six existing test
files the change would have to touch; made non-vacuity bidirectional; rewrote the spec section with the two
real couplings; and recorded the suite baseline including a pre-existing failure. I did NOT decide the
route.

MY RECOMMENDATION IS ROUTE (C), share only the error-translation tail (F-4's four `except` arms and the two
message prefixes), because that is the one piece which is genuinely shared, genuinely drifted, closes over
almost none of the nine double-defined symbols, and touches none of the 26 patch seams, which all sit on
the parse/route head. Route (D), do not split `main`, is a stronger fallback here than for any sibling
except `s16omw`: an entry point's job IS to bind one host's CLI to one host's behavior.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | E. testing; D. anti-regression | 26 sites in `tests/test_oc_runipd.py`, `tests/test_oc_runipd_cli.py`, `tests/test_interrupt_menu.py`, `tests/test_run_summary_table.py`; mechanism proven in a scratch probe | **THE SPLIT MAY SILENTLY DISARM 26 MONKEYPATCH SEAMS, AND SILENT IS THE POINT.** `mock.patch.object(<host>, "<name>")` sites replace names `main` resolves at module level (`run_queue` 7x, `locked_run` 6x, `build_parser` 3x, `resolve_run_dir` 3x, `install_stop_triggers` 2x, `emit_shutdown_report` 2x, `load_state` 2x, `initialize_run` 1x). A core in `runner_shared` resolves its OWN globals and sees none of them. Unlike a source pin, this does not fail at an assertion: the test runs the REAL dependency against a temp repo and may pass while asserting nothing it claims. `tests/test_oc_runipd.py:4123`'s `_parse_argv`, which backs 12 launch-profile assertions, is entirely this seam. | C:High; U:Low; S:Low; F:High; Overall:High | OPEN | Added as F-9 with all 26 sites counted by symbol; E-01(c) must re-derive the census and classify each seam LOST versus BROKEN; E-04(c) must give a verdict per seam; four files fenced. Folded into OQ-03. NOT fixed by a plan edit because converting 26 seams to injected-parameter patching is a test-infrastructure rewrite the maintainer must authorize. |
| PR-002 | BLOCKER | IN-SCOPE | A. correctness (a spec-pinned exit code) | measured `issubclass` results; `oc_runipd.py:9338`, `agy_runipd.py:5690`; scratch-probe reproduction | **HARDCODING EITHER HOST'S `EmptyStatusSelection` IN THE SHARED CORE TURNS EXIT 0 INTO EXIT 2 ON THE OTHER HOST.** The two classes are distinct siblings under the shared `runner_shared.DriverError`, neither subclassing the other, and both hosts order `except EmptyStatusSelection` before `except DriverError` because of that. A core resolving the name against one host lets the other's instance reach the `DriverError` arm and return 2, violating spec `25kzda` 2.4a property 3. Reproduced by construction: 0 for the matching class, 2 for the sibling. | C:Medium; U:Medium; S:Low; F:High; Overall:High | OPEN | Added as F-7 with the mechanism and the probe result; E-03 created as its own item to pin BOTH the behavioral and the STRUCTURAL half; V-03(b) requires the `issubclass` results pasted; non-vacuity control (a) requires the break demonstrated. Folded into OQ-03. Existing coverage at `tests/test_run_flag_surface.py:1787` and `tests/test_agy_runipd_cli.py:1200` recorded, so the risk is a loud failure rather than a silent one. |
| PR-003 | BLOCKER | IN-SCOPE | C. architecture; F. KISS | closure measured at HEAD; four pins in two files | **THE PLAN MEASURED BODY DIFFERENCE AND INFERRED LIFTABILITY, the error that reversed siblings `i3d6ml` and `ty3cj6`.** `main` closes over 27 module-level names: 8 resolve in `runner_shared`, 2 have a per-host WRAPPER there (`print_status`, `save_state`, so importing them loses the host label), 5 are one object agy imports from oc, 9 are STILL DEFINED TWICE, and 3 are oc-only. So the promised "relocation with a parameter" is a relocation with ELEVEN parameters that de-duplicates none of them. Four pins additionally read `inspect.getsource(<host>.main)`. | C:High; U:Low; S:Low; F:Medium; Overall:High | OPEN | Closure table added to the Goal with all 27 members named; E-01(a) must re-derive it; F-8 records the four pins with the substring each requires; E-04(a)/(b) must report both; escalated as OQ-03 with four routes and a share-the-error-tail recommendation. |
| PR-004 | HIGH | IN-SCOPE | A. correctness (a false factual claim) | `agy_runipd.py:1929` (definition), `:3010` (its only call); `main`'s 27-name closure | **F-5 IS FALSE AND IT IS THE PLAN'S ONLY "GENUINELY HOST-SPECIFIC" FINDING.** "oc resolves `opencode`, agy resolves via `resolve_agy`" describes neither host's `main`. `resolve_agy` is called once, inside the turn-launch path; oc's `main` mentions `opencode` only as the `driver_label` argument, which is F-6's label. No binary-resolution name appears among the 27 closure names. An executor would have gone looking for a hook that has nothing to hold. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 struck through and retracted in place with both citations and the closure evidence. |
| PR-005 | HIGH | IN-SCOPE | A. correctness (a conclusion contradicting its own finding) | by-cause classification of the 46 lines; similarity 0.8115 | **THE CONCERN'S "MOSTLY DRIFT" SENTENCE IS FALSE HERE AND CONTRADICTS F-1.** It is the boilerplate line shared verbatim with the four sibling split children. Classified by cause the 46 lines are 19 CAPABILITY, 10 LABEL and 17 drift, and 12 of the 17 are one style difference repeated twice plus a reordering, leaving about 5 lines of real drift in 133. F-1 (which calls this the most host-specific reading) is correct. An executor trusting the Concern would hunt for drift and find oc's launch-profile subsystem. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern corrected in place with the classification; F-6 added stating the contradiction and siding with F-1. |
| PR-006 | HIGH | IN-SCOPE | E. testing (a cited guard that does not exist) | repository search; `tests/test_json_and_exitcodes.py`; spec `25kzda:1074-1083` | **F-2 CITES A NONEXISTENT TEST FILE AND MISQUOTES THE SPEC IT RELIES ON.** `tests/test_exit_codes.py` does not exist; the repository's exit-code file tests `cli.main` and never touches a runner. The spec's table is 0/1/2/3/4/130, not "0 ok, 1 findings, 2 cannot-run", and it records at `:1082` that the drivers return only `0`/`2`/`130`/`143` today, citing `oc_runipd.main` by name. So the plan's headline hazard rests on a guard nobody can run. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-2 corrected with the spec's actual table, the `:1082` self-citation, and the FOUR guards that do exist (`test_run_flag_surface.py:1787`, `test_agy_runipd_cli.py:1200`, `test_run_summary_table.py:352/367`, `test_interrupt_menu.py:344/365`). |
| PR-007 | HIGH | IN-SCOPE | A. correctness (a difference that is not one) | `tests/test_runner_stop_triggers.py:1041`; both hosts' `subcommands` literals | **F-3'S "EACH HOST ROUTES ITS OWN VERBS" IS FALSE.** Both hosts route the identical five verbs, and a test asserts their implicit-start `subcommands` sets EQUAL, so there is no per-host routing table to parameterize. What is host-specific is what each branch DOES with `args`, which is F-1's capability difference wearing a different name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 corrected with the equality guard cited and the real locus of divergence named. |
| PR-008 | HIGH | UNDER-SCOPE | G. dependencies; C. architecture | `tests/test_runner_stop_triggers.py:1001`, `:1055`; `oc_runipd.py:9085-9089`; `agy_runipd.py:5533-5535` | **A HARD CONSTRAINT ON THE HOOK BOUNDARY THE PLAN DOES NOT KNOW ABOUT.** Two guards REGEX `subcommands = \{(.*?)\}` out of both runner SOURCE files and require the literals equal, and both runners carry a KEEP-THIS-INLINE comment recording that hoisting the set into a constant makes the guard "silently unmatchable (measured: it fails with unexpectedly None)". So the implicit-start shim cannot move into the core without rewriting the guard that stops `stop <run-id>` being rewritten into `start stop <run-id>` in one driver only. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added to Project conventions with both citations and the measured failure mode; `tests/test_runner_stop_triggers.py` fenced; Required tests item 7 requires it green by name. |
| PR-009 | MEDIUM | UNDER-SCOPE | D. anti-regression (a pinned census) | `tests/test_runner_shared.py:1148`; AST counts at HEAD | **THE SPLIT MOVES PART OF A PINNED CALL-SITE POPULATION.** `test_no_call_site_was_rewritten` expects 38/36 `save_state` and 2/2 `print_status` sites per runner (verified passing). `main` holds SIX of oc's 38 and FIVE of agy's 36, and BOTH `print_status` sites on each host. Moving them drops the counts, and the test's own rule forbids editing the literal: "If a count moves and you cannot name the new call site, the wrapper ruling has been undone". The correct treatment is a documented RELOCATION subtraction, as `RELOCATED_RUN_CHECKED_CALLERS` does. Not mentioned in the plan. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-10 and to Project conventions with the measured per-symbol split; Required tests item 6 and V-06(c) require the test green with its expectations unchanged. |
| PR-010 | MEDIUM | UNDER-SCOPE | C. architecture (a wrapper, not an import) | measured object identity for `print_status` and `save_state` against `runner_shared` | **TWO CLOSURE NAMES EXIST IN `runner_shared` BUT THE HOST OBJECTS DIFFER, so "resolves there" is not the same as "can be imported".** `print_status` and `save_state` are per-host WRAPPERS over the shared definition (`INJECTED` maps them to `driver_label` and `write_report` respectively at `tests/test_runner_shared.py:76-85`). A shared core importing the shared symbol directly would lose the host label and the host's `write_report`. The plan's closure reasoning does not exist, so it could not distinguish these from the 8 free movers. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as its own row in the Goal's closure table ("Name in `runner_shared` but host object DIFFERS"), counted among the eleven injections in E-04(a). |
| PR-011 | MEDIUM | UNDER-SCOPE | G. right-sizing | E-02 as authored | One E-item bundled the relocation of a 297-line entry point, eleven dependency decisions, the exit-code contract and the repair of six test files into one pass, invisible to the count-based lint. A failure midway leaves the package unimportable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-11; restructured into six single-concern items (measure / characterize / exit-code pin / analysis / closure guard / inverse guard); `Highest E allocated` raised to 06; the IPD-Z602 density advisory this raised on the first pass was cleared by splitting E-05. |
| PR-012 | LOW | UNDER-SCOPE | G. dependencies and sequencing | sibling front matter measured at HEAD | **THE DECLARED EDGE POINTS AT A PLAN THAT CANNOT CURRENTLY EXECUTE.** `Item-Dependencies: executed:ty3cj6` names child 08, which its own 2026-09-16 review left `reviewed`/`no-go` and RE-SCOPED to explicitly not perform its split, so `run_queue` will still be double-defined after it runs. Children 09 and 10 are likewise `no-go`. The edge is not wrong, it is INSUFFICIENT, which is what makes route (B) unactionable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-12 with the sibling statuses; E-04(d) must state it; OQ-03 route (B) records that this plan is already Order 11, so the real question is whether the four `no-go` siblings can be unblocked. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan reports 46 differing lines with 8 host tokens and concludes "mostly drift". Accept, or classify? | CLASSIFY BY CAUSE. 19 CAPABILITY, 10 LABEL, 17 drift, and 12 of the 17 are one style difference repeated twice plus a reordering, so real drift is about 5 lines of 133 and the conclusion inverts. | (a) Accept the Concern, rejected: it is boilerplate repeated verbatim across five children and a host-TOKEN count cannot see a capability difference whose lines happen to name no host (oc's `--validate`/`--variant` blocks carry no host token yet exist only because oc has a profile subsystem). (b) Trust F-1 without measuring, rejected: F-1 and the Concern CONTRADICT each other, so measurement was the only way to say which stands. | AST-normalized diff at HEAD `6a3a671c`; per-line classification; SequenceMatcher 0.8115; the resume flag surface measured on both built parsers (8 oc-only, 2 agy-only) | yes |
| D-2 | For an entry point, is the line diff or the closure the right liftability test? | THE CLOSURE, plus two pin populations. 27 names: 8 free, 2 host-wrapped, 5 one-object-via-import, 9 double-defined, 3 oc-only. | (a) Keep to the line diff as this plan and three siblings did, rejected: two sibling reviews (`i3d6ml`, `ty3cj6`) were reversed by exactly that error, and a dispatch/entry symbol's body is almost entirely calls, so its own diff measures how little the wrappers disagree. (b) Closure only, rejected as insufficient here: `main` is uniquely patch-pinned, and a closure table would have shown 27 names without revealing that 26 test seams depend on those names being module globals. | live object-identity resolution of all 27 names against `runner_shared`, oc and agy; `tests/test_runner_shared.py:76-85` for the two wrappers | yes |
| D-3 | `EmptyStatusSelection` is defined twice. Assume a shared core can just reference it, or test it? | TEST IT, by construction. A core resolving one host's class returns 2 for the other host's instance where the spec requires 0. | (a) Assume `except EmptyStatusSelection` is host-neutral because both classes have the same NAME and the same parent, rejected: measured, neither subclasses the other, and a name is not an identity. (b) Reason about it in prose without a probe, rejected: this is precisely the class of claim a reviewer gets wrong, and a ten-line probe settles it; the probe also produced the exact wrong output (`runX: empty` instead of `Nothing awaiting review`) that would appear in production. | `issubclass` results for both directions; MRO of both classes; scratch-probe reproduction returning 0 then 2; spec `25kzda` 2.4a property 3 | yes |
| D-4 | Are the 26 `mock.patch.object` seams a real obstacle, or would a shared core still see them? | REAL, AND DESIGN-DEPENDENT, so it must be escalated rather than assumed either way. Proven that an import-time-frozen reference ignores the patch while a call-time reference honors it. | (a) Assume the seams survive because `mock.patch.object` is standard, rejected: `patch.object(host_module, "run_queue")` rebinds a name in the HOST module's namespace, and a function defined in `runner_shared` never reads that namespace. (b) Assume they all break, rejected as equally unfounded: a core that takes each dependency as a call-time PARAMETER supplied by the host hook would still honor the patch, so the honest finding is that the answer depends on a design detail the plan does not specify, which is exactly why it belongs in front of the maintainer. | scratch-probe comparing an import-time-frozen descriptor against a call-time reference; the 26 sites enumerated by file, line and symbol | yes |
| D-5 | F-5 claims a binary-resolution difference in `main`. Correct it silently, or retract it on the record? | RETRACT ON THE RECORD, struck through, with both citations. | (a) Delete the finding, rejected: a reader comparing this plan to its four siblings would see one fewer host-specific difference and not know whether it was measured away or overlooked. (b) Soften it to "resolution happens elsewhere", rejected: it is not a matter of degree, the claim names a mechanism that is not in the symbol, and the plan called it the one difference that "stays behind the hook", so its removal changes what the hook is for. | `resolve_agy` defined at `agy_runipd.py:1929`, its single call at `:3010`; oc's `main` `opencode` occurrences are both `driver_label`; no binary-resolution name among the 27 closure names | yes |
| D-6 | The plan cites `tests/test_exit_codes.py` for its headline hazard. Assume a rename, or verify? | VERIFY. The file does not exist; the repository's exit-code tests target `cli.main`, and the real guards on `main`'s codes are four other files. | (a) Assume it means `tests/test_json_and_exitcodes.py`, rejected after reading it: that file exercises `cli.main` and never imports either runner, so it would not catch a renumbered driver exit code at all. (b) Leave the citation as harmless, rejected: an executor told a guard exists will not write one, and F-2 is the plan's own nominated highest-value hazard. | repository search for the filename; `tests/test_json_and_exitcodes.py:11` importing only `cli`; the four real guards located and cited | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: Converting 26 monkeypatch seams across four test files from module-name patching to injected-parameter patching is a test-infrastructure rewrite, and one of them (`_parse_argv`) is the foundation of 12 launch-profile grammar assertions. Which seams may be rewritten, and whether the split is worth that rewrite, is the maintainer's call.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, including whether the four test files listed in `Scope-Paths` may be restructured.
  - Consequence if unresolved: nothing breaks; the current state is correct. The risk being held open is an executor performing the split and leaving tests that LOOK green while exercising real dependencies they intended to stub, which is the one failure mode in this Set that no characterization suite detects.
- `PR-002` - `OPEN`:
  - Reason: The two hosts' `EmptyStatusSelection` classes cannot both be the one the shared core catches, and unifying them into a single shared class is a change to the exception hierarchy two runners raise, not a relocation.
  - Remediation Risk: High
  - Axis: functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, specifically whether the class may be lifted to `runner_shared` as ONE class (which is the clean fix) rather than injected.
  - Consequence if unresolved: nothing breaks, and this hazard is already covered by two tests, so a careless split fails loudly rather than shipping. The consequence of ignoring it is a spec-pinned exit code silently changing on one host if those two tests are ever weakened.
- `PR-003` - `OPEN`:
  - Reason: Whether to share an ENTRY POINT whose real drift is about five lines, whose eleven dependencies include two host wrappers and nine still-duplicated symbols, and 19 of whose 46 differing lines implement a subsystem one host does not have, is a design and priority question. Every route changes what this child of the Set delivers.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03 (routes A through D).
  - Consequence if unresolved: `main` stays duplicated, and the duplicated residue is each host's own CLI binding plus about five lines of genuine drift. The dangerous outcome is an eleven-parameter shared core that de-duplicates none of the eleven while disarming 26 test seams.

### Escalation of the irreversible decision

None of this round's six decisions is judged `Reversible: no`. Each is undone by editing this plan or a
test, and none publishes an interface, migrates data, or deletes anything. Stated explicitly rather than
left blank: D-3 and D-4 LOOK like the irreversible ones, because collapsing an exception hierarchy and
rewriting 26 test seams genuinely cannot be cleanly undone, but in both cases the decision I made was to
MEASURE AND ESCALATE rather than to act, which is the fail-closed direction. The irreversible acts they
guard against are escalated instead: PR-001 and PR-002 are raised in the plan as F-9 and F-7 with the
mechanism and the probe result, E-03 pins the exit-code contract structurally, E-06 asserts the four source
pins are still present so a later agent cannot quietly clear the obstacle, and the `Blocking: yes` OQ-03
puts all three in front of the maintainer before any split executes. That is the workflow's prescribed
handling for an irreversible consequence I declined to authorize.

### Why OQ-03 was left OPEN rather than asked

Stated explicitly because the workflow requires asking when a channel exists. THIS RUN HAD NO
INTERACTIVE PROMPT TOOL: the session exposes file, search and shell tools only, and `askme` is a
workflow rather than a CLI verb (`aw askme` is not a valid command, verified). So there was no way to
ask-and-wait for an answer inside the run. The question is therefore raised where the machinery WILL
stop on it: OQ-03 carries `- Blocking: yes` and `- Finding: PR-001, PR-002, PR-003`, which makes
`aw ipd lint` refuse the plan at EVERY checkpoint (confirmed: `IPD-Q501` at the `review-finalize`
checkpoint) and therefore blocks `aw ipd begin`. The four routes, their costs, and a recommendation are
written into the plan so the maintainer can decide from the plan alone. This is the same handling the
four sibling split children received, for the same reason.

### Honest limits of this review

- I DID NOT ATTEMPT THE SPLIT. The 27-name closure, the four source pins and the 26 patch seams come from
  AST extraction, live object-identity resolution and regex census, not from having built a shared core.
  E-01 re-derives all three at execution HEAD rather than inheriting my numbers.
- MY PATCH-SEAM CENSUS IS A REGEX OVER `mock.patch.object` AND `monkeypatch.setattr` with a bounded set of
  target spellings (`oc_runipd`, `agy_runipd`, `module`, `mod`, `driver`, `_MODULES[...]`). A seam reached
  another way (a fixture that patches by string path, a helper taking a module argument under a different
  parameter name, `patch("agent_workflows.oc_runipd.run_queue")`) would NOT have appeared, so 26 is a FLOOR
  and E-01(c) is asked to confirm it independently. I did not search for the string-path `mock.patch(...)`
  form at all.
- I PROVED THE TWO MECHANISMS IN SCRATCH PROBES OUTSIDE THE REPOSITORY, not by modifying the runners. The
  probes establish that the failure modes are real in Python; they do not establish that any particular
  shared-core design would hit them, which is precisely why D-4 is escalated rather than decided.
- I RAN A FULL SUITE AND IT IS NOT CLEAN AT HEAD. `python3 -m pytest` at `6a3a671c` with a clean tree:
  `1 failed, 7308 passed, 3 skipped, 2 xfailed in 96.93s`. The failure varied BETWEEN MY TWO RUNS, which is
  itself the finding: a targeted run failed
  `tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`
  (reproducible in isolation), while the full run failed
  `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`
  on a 30-second subprocess TimeoutExpired. Both exercise `main`'s signal paths, both are load-dependent,
  and NEITHER is caused by this review, which changed no code. An executor must take its own baseline; I
  named the first one in the plan and record here that the second exists.
- I DID NOT VERIFY THE PLAN'S CLAIM THAT `runner_shared` COULD HOST THE CORE WITHOUT A CYCLE. I confirmed
  `runner_shared` imports no runner (the AST-based rule at `tests/test_runner_shared.py:955`), but I did not
  check whether the eleven injected dependencies could be threaded without one of them re-introducing an
  import cycle through a third module.
- I DID NOT DECIDE THE ROUTE (OQ-03), and my share-the-error-tail recommendation is a recommendation. I also
  did not estimate the cost of route (C) concretely: I established that the error tail closes over few of
  the nine double-defined symbols and none of the patch-seam names, but I did not extract it to confirm.
