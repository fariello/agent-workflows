# Review findings: plan ypnk56

- Subject-Id: ypnk56
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ec7f0068` in a lane worktree. Structural preflight `aw ipd lint --phase author` reported
`conforming` with ZERO diagnostics; after revision `--phase review-finalize` reports `conforming` (exit 0)
with TWO `IPD-Z602` density advisories (E-03, E-04), both introduced by this review's own added prose and
both examined on merits in the gate rather than deferred to, since the linter's own contract is that a
passing count check does not clear conceptual density. No pre-review snapshot was owed: the plan was
committed and unmodified, and the lane-input copy under `.aw/state/lane-inputs/rev-41/` is byte-identical
(verified by `diff`). NO PRODUCTION FILE OR TEST WAS MODIFIED by this review; every measurement was a read
or an in-process probe against a freshly built parser whose mutations died with the interpreter. One
BACKLOG ITEM was created (`uip0z6`, see PR-404), which is a record and not a code change.

THIS PLAN IS WELL MEASURED AND MOST OF IT REPRODUCES EXACTLY. Confirmed at review HEAD: the test fails
naming precisely the eight strings the plan records, in that order; `config unset` measures `desc_len=71`
against `help_len=88` and the six `upgrade-test` leaves all measure `description=None` with help lengths
47/42/24/39/48/32 for `list`/`new`/`sandboxes`/`probe`/`env`/`clean`; `sa.choices["config"] is
sa.choices["conf"]` is `True`; the walk makes `283` name visits over `173` distinct parser objects; all 94
table keys resolve to a real path; the parser-adjacent trio reports `41 passed in 9.92s`; the bare suite
reports `3246 passed, 2 skipped in 48.96s`; the slow set reports `3 failed, 199 passed in 37.16s` naming
exactly the three expected node ids; and `64859728` (2026-09-26, plan `8ud1is`) is confirmed as the commit
that added the six leaves with `help=` and no `description=`. F-6 also reproduces in full, including that
`config get` on a recognized-but-unset key exits 0 while only an unrecognized key exits 2, and F-7's seven
`--agent` `ImportError` crashes reproduce with `config exclude list` exiting 0 on its different route.

THREE FINDINGS CHANGE WHAT THE PLAN WILL DO, and all three are about the fix's mechanism rather than its
goal. The goal itself is sound and the defect is real.

PR-401 REVERSES OQ-01. The plan chose the `_DESCRIPTIONS` table and gave "PRECEDENCE SAFETY" as its first
and load-bearing reason: an inline-only fix "would be SILENTLY OVERRIDDEN by any table key that later
claims the path". That is not what the code does. `cli._apply_descriptions` assigns under
`desc = _DESCRIPTIONS.get(path)` guarded by `if desc:`, so for a path the table does NOT claim it does
nothing whatsoever. Measured: an inline sentinel on `upgrade-test list` SURVIVES a verbatim re-run of
`_apply_descriptions` (`INLINE SENTINEL for an unclaimed path`), while the same sentinel on the claimed
`config exclude list` is replaced. So the hazard the resolution invoked requires a future author to ADD a
table key, which is exactly as hypothetical as the mirror hazard on the other side. I then drove BOTH
routes end to end against the unmodified failing test, seven strings each for the same seven paths, and
BOTH reported `Ran 2 tests ... OK`, `failures 0`. With the deciding argument gone the remaining
considerations favour inline, and two of them the plan had backwards: the census it read as "table 94,
inline 183" means inline is the MAJORITY convention for a leaf (the table serves mostly parents), and
inside `config` itself SIX leaves are inline against five `exclude`-family table keys, so `config unset` is
ALREADY inline and the table route would have DELETED accurate prose from one mechanism to re-add it in
another. Locality decides the rest: `8ud1is` omitted six descriptions in one contiguous `add_parser` block,
which is precisely where a table 1700 lines away is not looked at.

PR-402 IS THE MOST CONSEQUENTIAL TEST FINDING. E-05 property (2) asserted the `config`/`conf` alias
identity and equality, naming as its motive "the thing a future author would most plausibly break by
adding a `conf unset` key". That assertion cannot catch that regression, and it also passes on the
UNFIXED tree. One parser object cannot hold two descriptions, so injecting a `_DESCRIPTIONS["conf unset"]`
key makes the alias prose overwrite the canonical for BOTH spellings: measured identity `True`, equality
`True`, and the canonical phrase's presence on `config unset` going `True` -> `False`. A guard that passes
both before the fix and after the regression guards nothing. Only a CONTENT anchor distinguishes them, so
the property is rewritten as one and V-05 now demands the injection experiment as a second sensitivity
check that reverting cannot produce.

PR-403 WOULD HAVE MADE A CORRECT FIX LOOK BROKEN. E-05 property (3) required ANSI stripping and named
Python 3.14 colorization as the reason, which is real (reproduced: `\x1b[1;34musage: ` and colorized text
inside the description region under `FORCE_COLOR=1`). But argparse also WRAPS the description to the
terminal width, so a phrase of more than a few words is split by a newline plus indentation. Measured with
a probe description applied: `"deletes nothing until you pass -y" in stripped_help` is `False`, while the
same phrase in `" ".join(stripped_help.split())` is `True`, and the straddle occurs at `COLUMNS=60` and at
the default 80 alike. As specified the test would have been red on a working fix, which is the worst
failure mode for a guard because it invites weakening the fix.

I ALSO CHECKED THE PLAN'S NEGATIVE CLAIMS, since most of its scope reasoning rests on them, and they hold.
`completion.py` contains no `.description` reference at all (F-8 confirmed by an exhaustive grep, exit 1),
so a description-only change cannot alter a generated completion script. `command_surface.py` already
declares `upgrade-test` plus all six leaves and `CommandDeclaration` has no description field, so it
genuinely needs no change. `docs/` and `README.md` contain zero `upgrade-test` matches, so the CHANGELOG
line is the correct and only user-facing record. `tools/aw_upgrade_test.py` is a 35-line re-exporting shim
with no `build_parser` of its own, so the plan's deferral reasoning about it is right in substance though
wrong in detail (the parser it declines to fix lives in `upgrade_rehearsal.build_parser`, not in the shim);
that parser is genuinely not reached by `cli._build_parser` and not walked by the test, and its six leaves
do measure `description=None`, so declining it is correct. I confirmed `tests/test_cli_parser_conflict_policy.py`
invokes `upgrade_rehearsal.build_parser` but asserts only on conflict handlers, so nothing pins those
descriptions either way.

ONE INCIDENTAL DEFECT WAS FOUND AND FILED RATHER THAN ABSORBED (PR-404). It deserves emphasis because of
the irony: the plan's own draft asserted that `config get` "exits nonzero for an unset variable", caught it
by driving, and recorded the near-miss as F-6 with the lesson that a plausible sentence must be driven.
That exact sentence is ALREADY SHIPPED on the sibling `config get` parser, three lines above the code the
executor will edit. Driven: every recognized-but-unset key exits 0 with empty output, pinned by the
repository's own `tests/test_config.py` assertion, so the help text tells a script to branch on an exit
code that never arrives. It escapes the contract test because it is 335 characters against a 76-character
help, i.e. long enough to satisfy a LENGTH contract while being false, which is a limit of that contract
worth recording. Filed as `uip0z6` (`bug`, `Blocks-Release: next` per the live-bug gate) and carried in the
deferred section rather than absorbed, so the fence stays the seven reported paths.

WHAT I DELIBERATELY DID NOT FLAG. The four `Carrier-Declined` entries are each sound on inspection: the
`dtq6jr` crash is a handler bug in a plan that touches no handler; the CI flip is provably not this plan's
(and I confirmed the surviving two failures are named by TWO items, not one, which makes the point
stronger); the whole-surface audit is genuinely already covered by the census test that must pass; and the
`upgrade_rehearsal` parser is outside the contract. The plan's refusal to re-mark `tests/test_cli.py` as
default-visible is a defensible judgement rather than a dodge, and it discharges the part it owns by making
its own guard default-visible. E-01's STOP condition is correct and must not be removed: a differing report
set or a false alias identity genuinely invalidates the seven-strings arithmetic, which is an unsafe
condition and not a scope question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | C (architecture, canonical mechanism) / G (executability) | plan OQ-01, E-02, E-03, E-04, F-3; `cli._apply_descriptions` (`desc = _DESCRIPTIONS.get(path)` under `if desc:`); `cli._build_parser` `p_config_unset`, `p_upg_list`..`p_upg_clean` | OQ-01'S DECIDING ARGUMENT IS FALSE AND THE ANSWER FLIPS. It claimed an inline `description=` fix "would be SILENTLY OVERRIDDEN by any table key that later claims the path"; `_apply_descriptions` assigns ONLY for a claimed path, so an inline description on an unclaimed path is untouched. Measured both ways. With that gone, three of the plan's own facts favour inline and two were read backwards: the 183-vs-94 census makes inline the MAJORITY convention for a leaf; six `config` leaves are inline against five `exclude` table keys, so `config unset` is already inline and the table route would DELETE accurate prose to re-add it elsewhere; and the defect's actual cause was locality (six omissions in one `add_parser` block). Left as written, the plan would have moved one string between mechanisms and put six new ones 1700 lines from the registrations, reproducing the drift that caused the bug | C:Low; U:Low; S:Low; F:Low (both routes measured green, so no functional risk either way); Overall:Low | FIXED | OQ-01 rewritten with the refuting measurement, BOTH routes driven green (`Ran 2 tests ... OK` each), and the answer changed to inline with locality, majority convention, and single-edit-site as the reasons, plus the honest mirror cost stated. E-02 repurposed from "confirm the table is authoritative" to a two-sentinel check plus a membership check that none of the seven paths is table-claimed (with a STOP if one is). E-03 rewritten as an EXTENSION IN PLACE of the existing inline string. E-04 rewritten to add six inline kwargs at named registration variables. F-3 corrected. Scope, conventions, Proposed changes, Scope-Paths justification, V-02, V-03, V-04 and the gate all swept for the superseded "table entry" wording |
| PR-402 | HIGH | IN-SCOPE | E (testing) / D (anti-regression) | plan E-05 property (2); measured: identity `True` and equality `True` on the UNFIXED tree AND under an injected `_DESCRIPTIONS["conf unset"]` key, while the canonical phrase on `config unset` goes `True` -> `False` | THE ALIAS GUARD IS VACUOUS IN BOTH DIRECTIONS. Asserting `config is conf` and description equality passes BEFORE the fix (the objects are already identical, the descriptions already equal) and STILL PASSES under the exact regression the item names as its motive, because one parser object cannot hold two descriptions, so an added alias key silently overwrites the canonical for both spellings. The plan would have shipped a guard that cannot fail for the reason it exists, and V-05's sensitivity check ("all three cases FAIL when reverted") would have quietly not held for this case | C:Low; U:Low; S:Low; F:Medium (a guard that cannot detect its own stated regression is worse than none, because it licenses the belief that the hazard is covered); Overall:Medium | FIXED | Property (2) rewritten as a CONTENT anchor on `conf unset`'s rendered help, with the identity and equality forms explicitly forbidden and the measurement that condemns them quoted. V-05 now requires a SECOND sensitivity check that reverting cannot produce (inject the alias key over the completed fix and show the case failing), and states that a PASS on the reverted tree means the vacuous form was used. E-05's Expected outcome and the Required-tests entry carry the same condition. New F-11 |
| PR-403 | MEDIUM | IN-SCOPE | E (testing) | plan E-05 property (3); measured with a probe description: phrase `in help` `False`, `in ansi_stripped` `False`, `in " ".join(stripped.split())` `True`; straddle reproduced at `COLUMNS=60` and 80 | STRIPPING ANSI IS NOT SUFFICIENT AND THE TEST AS SPECIFIED WOULD FAIL ON A CORRECT FIX. argparse wraps the description to the terminal width, so any caveat phrase longer than a few words is broken by a newline plus indentation and `assertIn` fails even when the description is exactly right. The plan named only the colorization hazard. A guard that is red on a working fix is the worst kind, because the obvious response is to weaken the description | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Property (3) now requires whitespace normalization ALONGSIDE the ANSI strip, with both measurements and both reasons stated separately, and permits the alternative of a phrase short enough that no wrap can split it provided the executor says which it chose. V-05 requires the statement. New F-12 |
| PR-404 | MEDIUM | OVER-SCOPE (recorded and carried, not absorbed) | B/F (honest documentation of a shipped contract) | `cli._build_parser` `p_config_get` `description=` ("Exits nonzero when the variable is not set"); `cli._run_config_get` (`elif val is None: print("")` then `return 0`); `tests/test_config.py::InstallPolicyDefaultsConfigTests::test_clearing_and_unset_removes_keys`; driven: four recognized keys all `exit=0 out=''`, only `no.such.key` -> `exit=2` | A SHIPPED `--help` STRING STATES SOMETHING FALSE, AND IT IS THE SAME FALSE CLAIM THIS PLAN CAUGHT IN ITS OWN DRAFT (F-6). `config get` promises a nonzero exit for an unset variable; there is none, and the repository's own test pins the exit 0. So the help invites a script to branch on an exit code that never arrives. It is invisible to the contract test because it is 335 characters against a 76-character help: long enough to pass a LENGTH check while being wrong. Found while re-driving F-6, three lines from the code the executor will edit | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded and CARRIED rather than repaired here. Filed backlog `uip0z6` at review (`bug`, `Blocks-Release: next`, with the driven evidence, the pinning test, and a warning that any replacement must be driven). Added F-10; added a Deferred entry with `- Carrier: uip0z6` explaining why proximity is not a reason to absorb it; E-03 and the gate's scope fence both name it as deliberately untouched, and V-03 and V-06 require the executor to confirm it was left alone |
| PR-405 | LOW | IN-SCOPE | F (honest documentation) / D | plan F-5, E-06(e), the `continue-on-error` deferral, and the `- Concern:` field; `.aw/records/backlog/graduated/20260918-4vfkl1-...` and `...-57dwkc-...` each naming the same two node ids | THE TWO SURVIVING SLOW FAILURES ARE OWNED BY TWO ITEMS, NOT ONE. The plan attributes both to `4vfkl1` alone; `57dwkc` names the identical pair. This understates the distance to the CI flip (the plan is not even the penultimate closer) and could send an executor to the wrong owner. The authoring slow-set counts are also now review-stale as printed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5, the `- Concern:` field, E-06(e), the deferral entry, V-06 and the Required-tests entry all now name BOTH owners. E-06's Expected outcome and the Required-tests entry restate the bar as failing-node-id SET equality with the counts as re-measured review context (`3 failed, 199 passed` at `ec7f0068`) rather than as the criterion, per the live-artifact re-derivation convention |
| PR-406 | LOW | UNDER-SCOPE | G (execution contract) | plan gate as authored: "move this plan to `.aw/records/plans/executed/` with the tooled lifecycle transition (`aw ipd set executed`)"; `ipd_lifecycle.finalize` checks `worker_role_active` itself (verified), and `aw ipd set executed` delegates into that same transaction; no scope fence | THE GATE'S LIFECYCLE INSTRUCTION IS UNCONDITIONAL AND NAMES A VERB THAT IS REFUSED IN A MANAGED LANE. `AW-LIFECYCLE-ROLE-001` is enforced inside the finalize transaction, so `aw ipd set executed` is refused for a worker-role process exactly as `aw ipd finalize` is; an agent told to run it in a lane spends its terminal output on a refusal that is the expected path. The gate also carried no scope fence, so finalize reconciliation had nothing declared to reconcile against beyond `- Scope-Paths:` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now separates the UNCONDITIONAL finalize obligation from the CONDITIONAL owner (runner in a managed lane, executor by hand with the full `aw ipd finalize ... --apply` invocation), cites the verified enforcement site, and forbids both a hand-rolled `git mv` and a hand-edited `- Status:`. A per-path SCOPE FENCE was added as a DECLARATION (not a stop directive, per the 2026-09-01 ruling) naming the eight things not to touch, each with its carrier where one exists, and stating that a necessary out-of-scope edit is made and then justified with `--scope-reason` |
| PR-407 | LOW | UNDER-SCOPE | G (approval gate) | plan gate as authored: three lines, `Cohesion rationale: not required`, no statement of what approval means | NO STATEMENT OF WHAT A HUMAN WOULD BE APPROVING. The gate asserted that approval is required without saying what the change does, what it deliberately declines, or which judgement is the contestable one, which for this plan is the mechanism the review reversed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a one-paragraph "WHAT A HUMAN WOULD BE APPROVING" that names the three files, states that no command behavior changes, identifies the reversed mechanism decision as the thing to scrutinise, notes its reversibility, and names the two carried declines (`4vfkl1`/`57dwkc` for the CI flip, `uip0z6` for the false sibling claim). `Cohesion rationale: not required` left as-is, correct at six items |
| PR-408 | LOW | IN-SCOPE | G (right-sizing) / stale cross-reference | `aw ipd lint --phase review-finalize` `IPD-Z602` on E-03 and E-04; plan lines citing `E-04's default-visible guard`, `E-04 discharges`, `E-05 reports this`, `E-05's one CHANGELOG line` | TWO DENSITY ADVISORIES UNADDRESSED, AND FOUR STALE E-ITEM CROSS-REFERENCES. The advisories (introduced by this review's own added prose) would leave a reader unable to tell whether density was examined or missed. Separately, four places cite the wrong item: the guard is E-05 not E-04, the CHANGELOG line is E-06 not E-05, and the CI report is E-06(e) not E-05 | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now records a reasoned density decision for each advisory: E-03 is one string on one parser whose advisory fires on grounding and negative-constraint prose inseparable from the edit; E-04 is six strings but ONE act over ONE verification surface (six sibling leaves, one handler module, one V-04 walk), whose advisory fires on the three mandatory safety caveats, which are its substance. All four stale cross-references corrected |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). The two HIGH findings are both FIXED in place.
No BLOCKER was found: the plan's goal, its defect characterization, and every premise-level measurement are
correct, and all three mechanism findings were repairable with bounded edits to items nobody has executed.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | OQ-01 was already `resolved` in favour of the `_DESCRIPTIONS` table, on an argument measurement refutes. Reverse the answer, or reopen the question for the human? | Reverse it to the inline `description=` kwarg, keeping the question `resolved`, and record the refuting measurement in the resolution | Reopening as `- Blocking: yes`, rejected because the repository ANSWERS this from evidence (the guard clause in `_apply_descriptions`, the 183-vs-94 census, the six inline `config` leaves) and both routes were driven green, so no human judgement is needed and a blocking question would stall a correct plan over a mechanism choice; ALSO rejected: keeping the table and merely deleting the false reason, because the remaining reasons (alias comment locality, family locality) both point the other way once the census is read correctly | `cli._apply_descriptions`' `desc = _DESCRIPTIONS.get(path)` under `if desc:`; sentinel survival on the unclaimed `upgrade-test list` vs replacement on the claimed `config exclude list`; both routes driving `SubcommandDescriptionTests` to `Ran 2 tests ... OK`; census `tabled 94 / inline-only 183 / none 6`; `config` family six inline leaves vs five table keys | yes |
| D-2 | E-05's alias property is vacuous. Rewrite it as a content anchor, or drop property (2) as unguardable? | Rewrite as a content anchor on `conf unset`'s rendered help | Dropping it, rejected because the regression is REAL and reachable (an added `conf unset` key silently steals the canonical description for both spellings) and is exactly the mistake a future author extending the table would make, so the hazard deserves a guard rather than none; keeping the identity assertion alongside, rejected because it asserts something no code path can violate and would read as coverage | measured: identity and equality both `True` on the unfixed tree AND under the injected alias key, while the canonical phrase's presence goes `True` -> `False`; GUIDING_PRINCIPLES P16 (assert observable behavior, and verify sensitivity by mutation) | yes |
| D-3 | The false `config get` help claim sits three lines from the code the executor edits. Absorb it, or carry it? | Carry it on a new backlog item `uip0z6` and fence it out explicitly | Absorbing it, rejected on two grounds: the plan's validation bar is that the SEVEN reported paths clear, and an eighth edited string makes `git diff agent_workflows/cli.py` no longer answer that question; and the execution contract forbids opportunistic widening even when the edit is adjacent and small. Filing nothing, rejected outright because the contract test provably cannot catch it (335 chars vs 76-char help), so without an item it is lost | driven: four recognized-but-unset keys all `exit=0 out=''`, only an unrecognized key `exit=2`; `_run_config_get`'s `return 0` after `print("")`; `tests/test_config.py::InstallPolicyDefaultsConfigTests::test_clearing_and_unset_removes_keys` pinning that exit 0; the repository live-bug gate requiring `Blocks-Release:` on a live `bug` | yes |
| D-4 | Should the review widen scope to the six `upgrade_rehearsal.build_parser` leaves, which also carry `help=` with no `description=`? | No; leave the plan's declining of it intact, correcting only its wrong detail about where that parser lives | Widening, rejected because that parser is not built by `cli._build_parser`, is not walked by the contract test, and is reached only by `python3 tools/aw_upgrade_test.py`; its six leaves document the same commands this plan documents, so the user-facing gap is closed by the `aw` path either way. Filing an item for it, rejected as backlog noise for a compatibility shim's standalone parser with no demonstrated user | verified: `tools/aw_upgrade_test.py` is a 35-line re-exporting shim with no parser of its own; `upgrade_rehearsal.build_parser`'s six leaves measure `description=None`; `tests/test_cli_parser_conflict_policy.py` invokes it but asserts only on conflict handlers | yes |
| D-5 | The two `IPD-Z602` density advisories were introduced by this review's own added prose. Split E-03 or E-04, or keep them whole? | Keep both whole, recording the rationale in the gate | Splitting E-04 into six per-leaf items, rejected because they are one act over one verification surface (six sibling leaves of one family, all authored from handlers in one module, all verified by V-04's single walk) and splitting would multiply the `cli.py` diff and the re-measurement sixfold for no added signal; splitting E-03's grounding prose from its edit, rejected because it would separate a negative constraint from the edit it constrains, which is how the constraint gets ignored | the rubric's own density diagnostics applied per item: one concern each, one test-surface each, one focused pass each; the advisories fire on grounding and caveat prose, not on multiple deliverables | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
