# Review findings: plan mj18mi

- Subject-Id: mj18mi
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4d086716` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --short` clean) and the lane-input copy at `.aw/state/lane-inputs/rev-12/`
is byte-identical to the tracked file (`diff` reported no difference). `aw sanitize --agent` clean.

THIS IS THE BEST-EVIDENCED PLAN IN THIS SWEEP AND FOURTEEN OF ITS FIFTEEN FINDINGS REPRODUCE EXACTLY.
Its central argument is correct and non-obvious: the document is wrong in TWO independent ways
(a presence-test for cancelling, a non-emptiness test for forcing), the two compound, and the fix must
be documentary because an approved release-gating spec has already ruled the code is the authority.
Its sharpest authoring insight is F-03, which the backlog item missed: a corrected table containing
only the five monochrome cells would be satisfied by the OPPOSITE wrong belief (that a falsey value
suppresses), so the discriminating row `FORCE_COLOR=0` on a TTY, measured COLORED, is what makes the
tri-state unambiguous. That reasoning is sound and I verified every cell of it.

WHAT REVIEW FOUND IS THAT THE PLAN'S OWN DURABLE DELIVERABLE, THE TABLE-DRIVEN GUARD, PASSES VACUOUSLY
AS SPECIFIED, AND THAT THE SAFEGUARDS THE PLAN ADDED AGAINST EXACTLY THAT DO NOT CATCH IT.

**THE GUARD TESTS NOTHING UNLESS IT STRIPS THE MARKDOWN BACKTICKS (PR-301, HIGH).** E-03(a) says to
derive the environment from the invocation text, where "leading `VAR=value` tokens become
environment". The cell text in the file is a BACKTICKED string (`` `FORCE_COLOR=0 aw <cmd> \| cat` ``),
so a leading-`VAR=value` anchor applied to the raw cell matches the EMPTY STRING: the backtick is
character one. Measured directly, `re.match(r'^((?:[A-Z_]+=\S*\s+)*)', cell)` returns `''` on the
backticked cell and `'FORCE_COLOR=0 '` after stripping. The consequence over E-01's own six new rows
is that FIVE PASS WHILE SETTING NO ENVIRONMENT AT ALL, because four documented-monochrome rows are
monochrome anyway on a pipe and `FORCE_COLOR=0` on a TTY is colored anyway by plain detection. Exactly
one row (`NO_COLOR=1 FORCE_COLOR=0` on a TTY) goes red, and that single red row is WORSE than all-red:
it tells the executor the DOCUMENT is wrong when the PARSER is. What makes this a real finding rather
than a nitpick is that the plan ALREADY anticipated vacuity and guarded against it in E-03(d) with a
row floor and a named-row subset, and NEITHER catches this, because both inspect row TEXT rather than
what was extracted from it. So the plan's own safeguard reasoning was right and its implementation of
that reasoning was one level too shallow. E-03 now carries (a1) with the measurement and a mandatory
per-row env-extraction assertion, and V-03 requires the extracted environment pasted per row and
rejects a V-item that pastes only invocations and results.

**THE DOCUMENTED ROWS NEED A CAPABLE `TERM` SET, NOT INHERITED (PR-302, MEDIUM).** The table says
nothing about `TERM`, but rung 3 disables color for `TERM=dumb` or an unset `TERM`, and several rows
document `colored`. A guard inheriting the runner's `TERM` is therefore machine-dependent and would
fail where `TERM` is unset. This is the file's own convention already (the shipped grid test applies
`TERM="xterm-256color"` per case) and my own table probe needed it to reproduce 5 of 5, so it is
cheap to state and easy to omit. Added to E-03(c) as an explicit requirement and recorded as F-17.

Two smaller items: both suite baselines were unnumbered (PR-303), now measured at `2935 passed,
2 skipped` bare and `23 passed` for `tests/test_term.py`, with the note that BOTH totals must RISE
since E-03 and E-04 add cases, so an unchanged `test_term.py` count means one of them added nothing;
and the gate had no scope fence, no out-of-scope-edit disposition and an unconditional finalize
instruction (PR-304), all corrected per the 2026-09-01 ruling, keeping a stop directive only for the
inverted-premise case (a measured color cell moving), which is a genuinely unsafe condition.

I also flag one pleasant non-finding, because it is the kind of thing a reviewer should confirm rather
than assume: E-03(b1)'s hazard does NOT currently bite. `--no-color` does not contain `--color` as a
substring, so a naive substring test in the natural order happens to be correct today. I still added
the token-matching requirement, because the property is accidental and a later refactor could lose it,
but I record that the plan was not wrong here.

ALL THREE PRE-EXISTING OPEN QUESTIONS WERE RESOLVED BY THE AUTHOR AND ALL THREE RESOLUTIONS HOLD, which
is worth stating explicitly because a reviewer's job includes checking self-resolved questions rather
than accepting them. OQ-01 (`bug` and the release gate): the item is `- Work-Kind: bug` carrying
`- Blocks-Release: next`, `next` resolves to the single `planned` release `f33nrj`, and the repository's
own perceptibility test is satisfied on the plan's own terms (the affected reader is a script author
choosing how to suppress color, the affected user is one who set `NO_COLOR`, and
`_force_color_is_forcing`'s docstring calls getting that wrong "strictly worse"). The plan's honest
recording of the alternative (a maintainer could call it a chore) is the right treatment. OQ-02
(admissibility of a doc-parsing test): the `xelvyi` ruling's recorded words are "no tests that try to
prevent text or code from changing", and its note explicitly reclassifies toward "a BEHAVIORAL test
only where real behavior is at stake", which is what E-03 is; the plan's mitigation of the one real
risk (vacuity) is exactly the risk PR-301 then found a hole in, which strengthens rather than
undermines the reasoning. OQ-03 (one table, guide points at it): confirmed by F-07, whose measured
drift is precisely what a second copy produces.

Every other claim verified. F-01 (all five cells monochrome); F-02 (row 2 verbatim); F-03
(`FORCE_COLOR=0` on a TTY COLORED); F-04 (`frozenset({"", "0", "false", "no", "off"})`, both call
sites, and the "six cells" docstring verbatim including "strictly worse"); F-05 (the item's five-row
addition would indeed be satisfiable by the suppress reading); F-06 (`_ENV_VALUES = (None, "", "0",
"1")`, and the word-valued falsey spellings appear exactly once each, inside the `NO_COLOR=None`
loop); F-07 (`--color` beats `NO_COLOR` on both stream kinds and beats `TERM=dumb`, all three
measured True); F-08 (5 of 5 agree under a hermetic probe); F-09 and F-10 (five distinct dangling
files, two hits in the contract, at lines 55 and 91); F-11 (249 leaves, 29 missing both color flags,
all 29 being the host-driver forwarders plus `__complete`; `_dispatch` returns 2 with the documented
message); F-12 (spec A13 verbatim, including "MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW");
F-13 (`xdwa5t` `done`, byte-identical Summary, the quoted history line); F-14 (all eight normalization
spellings); F-15 (only `GUIDING_PRINCIPLES.md` and `DECISIONS.md` besides the two fenced docs, and both
mention `FORCE_COLOR` only as a signal). The carrier `ikxtkj` is live, `open`, and genuinely covers
both the four other citations AND the general-guard idea this plan assigns to it, and it correctly
excludes the line-55 citation as belonging to this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-301 | HIGH | IN-SCOPE | E. Testing / A. Correctness | Measured: `re.match(r'^((?:[A-Z_]+=\S*\s+)*)', cell)` returns `''` on the backticked cell `` `FORCE_COLOR=0 aw <cmd> \| cat` `` and `'FORCE_COLOR=0 '` after `strip` of the backtick; probe over E-01's six planned rows under that bug shows extracted env `{}` for all six, 5 of 6 agreeing with their documented result anyway, and one red row (`NO_COLOR=1 FORCE_COLOR=0` on a TTY); plan E-03(a) "leading `VAR=value` tokens become environment" and E-03(d)'s row floor plus named-row subset | **THE PLAN'S DURABLE DELIVERABLE PASSES VACUOUSLY AS SPECIFIED.** Without a backtick strip the guard sets no environment at all, so five of the six rows that exist to pin falsey `FORCE_COLOR` pass having tested nothing about it. E-03(d)'s anti-vacuity safeguards do NOT catch it, because both inspect row TEXT rather than extraction output. The single resulting red row is worse than all-red: it misdirects the executor to the document. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 gains (a1): strip the backticks, and ASSERT a non-empty extracted environment for every `=`-bearing row, with the measurement recorded and an explicit note that (d) does not cover it. V-03 now requires the extracted environment and override pasted PER ROW and states that a V-03 lacking it must be rejected even when green. New F-16. |
| PR-302 | MEDIUM | IN-SCOPE | E. Testing (portability) | Section 1.1 rung 3 "`TERM=dumb` or an unset `TERM` disables"; several documented rows read `colored`; `ShouldColorGridTests` applies `TERM="xterm-256color"` in every color case; review's own probe required it to reproduce 5 of 5 | The table states nothing about `TERM`, so a guard that inherits the runner's `TERM` is machine-dependent and fails where `TERM` is unset. The plan's hermeticity requirement named `NO_COLOR`/`FORCE_COLOR` and the color override but not `TERM`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03(c) now requires `TERM` set explicitly per row to a capable value, citing the file's existing convention and rung 3. New F-17. |
| PR-303 | LOW | IN-SCOPE | E. Testing | Plan Required tests: "compared against a baseline captured BEFORE any edit" and "pasted both before and after", with no values | Neither baseline had a number, so an executor could paste any value and call it unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured at review: bare `2935 passed, 2 skipped, 3 warnings in 43.80s` (zero failures) and `tests/test_term.py -o addopts=""` -> `23 passed`. Both recorded, with the note that both totals must RISE and that an unchanged `test_term.py` count means E-03 or E-04 added nothing. |
| PR-304 | LOW | IN-SCOPE | G. Plan executability (gate) | Plan gate as authored: path-scoped commit, staged-set verification, never-push, paste-actual-output, the inverted-premise warning and the `Readiness` abstention all present; no named scope fence, no out-of-scope-edit disposition; "Do not move this plan to `executed/` until ..." unconditional; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate named no forbidden paths, carried no disposition for an out-of-scope edit, and stated the lifecycle move without the conditional runner/executor ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming `agent_workflows/term.py`, any `.spec.md` and the four carried citations; make-and-justify wording (`--scope-reason`/`--scope-ack`) with no stop-and-report for the scope case; kept the inverted-premise stop as the one legitimate stop; conditional finalize ownership forbidding a hand-rolled `git mv`. Also added a WHAT REVIEW CHANGED paragraph so an approver sees PR-301, and corrected the `Readiness` sentence, which said the plan carries no such field while review was about to write one. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-301: how should the vacuity hole be closed, given E-03(d) already tried and missed? | REQUIRE THE BACKTICK STRIP *AND* AN ASSERTION ON THE EXTRACTION OUTPUT, and require the extraction pasted in V-03. | (a) Only add "strip the backticks": rejected, it fixes this instance and leaves the CLASS open; any future parse failure (a renamed column, an added flag spelling, a row using `env VAR=x`) would silently return an empty environment again and pass. Asserting on the extraction output catches all of them. (b) Strengthen the row floor instead: rejected, measured, the floor passes under the bug because it counts rows rather than inspecting extraction. (c) Abandon the table-driven guard as too fragile: rejected, it is the plan's whole answer to recurrence and OQ-02's admissibility reasoning is sound; the fragility is in the parse, and it is assertable. | Measured `re.match` behavior before and after stripping; measured 5-of-6 vacuous pass; E-03(d)'s two assertions both passing under the bug. | yes |
| D-2 | Does PR-301 make the plan unsound (REPLAN), or is it a bounded fix? | BOUNDED FIX. Everything else about E-03 (unescaped-pipe splitting, hermetic env, all-mismatches reporting, the mutation demonstrations, the OQ-02 docstring) is correct and unchanged. | REPLAN: rejected. The defect is in one parsing step of one E-item, the plan had already identified the correct risk class, and the repair is two requirements plus a V-item paste. | The rest of E-03 verified correct: unescaped-pipe splitting is genuinely necessary (my first probe reproduced the `cat` truncation class), and the five shipped rows agree 5 of 5 under a correct parse. | yes |
| D-3 | OQ-01 self-resolved `bug` + `Blocks-Release: next` on the author's own authority. Does it stand? | STANDS. Left `resolved`, gate untouched. | Escalate to the maintainer: rejected. The repository's perceptibility test is written down, the plan applies it to a concrete reader and a concrete accessibility case, the backlog item already carried both the kind and the gate, and the plan records the alternative outcome honestly so a maintainer can overrule cheaply. Escalating would hold a correct plan for a question its own evidence answers. | Item `bar5t8`: `- Work-Kind: bug`, `- Blocks-Release: next`; `next` resolves to the single `planned` release `f33nrj`; `AGENTS.md`'s user-perceptible-impact ruling; `_force_color_is_forcing`'s "strictly worse" docstring. | yes |
| D-4 | OQ-02 argues a doc-parsing test survives the 2026-09-26 no-source-pin ruling. Verify or challenge? | VERIFIED. Left `resolved`. | Challenge it: rejected on the ruling's own recorded text, which says "DELETE the source-reading tests (text or AST structure pins) and keep or add a BEHAVIORAL test only where real behavior is at stake". E-03 reads `docs/` prose and decides every row by executing `term.should_color`, so it is behavioral and its subject is repository content. | The `xelvyi` history note quoted verbatim; E-03 asserts no production source text and parses no package module. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. All three pre-existing open questions remain `resolved` and their reasoning survives
review (D-3, D-4, and OQ-03 confirmed by F-07).

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (E-03 (a1)/(b1)/(c) additions, V-03 extraction paste, F-16, F-17, measured
  baselines, gate rewrite, `Status: reviewed`, `Readiness: go-pending-approval`).
- `aw sanitize --agent` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- Lane input identity: `diff` of the `rev-12` lane input against the tracked plan -> no difference;
  `git status --short` clean before editing, so no pre-review snapshot was owed.
- **F-01 reproduced, all five cells**, against `term.should_color` with fake streams and a capable
  `TERM`: `FORCE_COLOR=0 | cat` monochrome; `FORCE_COLOR=off | cat` monochrome;
  `FORCE_COLOR=false | cat` monochrome; `NO_COLOR=1 FORCE_COLOR=0 | cat` monochrome;
  `NO_COLOR=1 FORCE_COLOR=0` on a TTY monochrome.
- **F-03 reproduced**: `FORCE_COLOR=0` on a TTY -> COLORED. This is the discriminating row and it
  confirms the plan's six-row decision over the item's five.
- **F-02 reproduced verbatim**: row 2 reads "`NO_COLOR` (any value, including empty) disables, UNLESS
  `FORCE_COLOR` is set; `FORCE_COLOR` (any non-empty value) enables."
- **F-04 reproduced**: `_FORCE_COLOR_FALSEY == frozenset({'', 'off', 'false', 'no', '0'})`; both call
  sites present (`if "NO_COLOR" in os.environ and not _force_color_is_forcing()` and
  `if _force_color_is_forcing()`); the docstring's six-cell measurement and "strictly worse" wording
  quoted as the plan states.
- **F-06 reproduced**: `_ENV_VALUES = (None, "", "0", "1")`; each of `false`, `no`, `off`, `FALSE`
  appears exactly once in the file, inside the falsey loop that applies `NO_COLOR=None`. So
  `NO_COLOR=1 FORCE_COLOR=off` on a TTY is asserted nowhere.
- **F-07 reproduced**, three measurements: `--color` with `NO_COLOR=1` True on a TTY AND on a pipe;
  `--color` with `TERM=dumb` True. The guide's two target sentences quoted as the plan states.
- **F-08 reproduced**: a hermetic table-extraction probe over the 5 shipped rows reports 5 of 5
  agreeing. (My FIRST probe reported 4 of 5, from my own env leak between rows, which independently
  demonstrates why E-03(c)'s hermeticity requirement is load-bearing.)
- **PR-301, the finding that changed the plan.** Root cause measured:
  `re.match(r'^((?:[A-Z_]+=\S*\s+)*)', '`FORCE_COLOR=0 aw <cmd> | cat`')` -> `''`; after stripping the
  backtick -> `'FORCE_COLOR=0 '`. Over E-01's six planned rows under the bug: extracted env `{}` for
  all six; 5 pass, 1 fails (`NO_COLOR=1 FORCE_COLOR=0` on a TTY, doc monochrome, got colored).
- **PR-302** measured: rung 3 quoted; the shipped grid test's `TERM="xterm-256color"` confirmed; my own
  probe required it.
- **F-09 / F-10 reproduced**: an existence sweep over every `tests/test_*.py` token in `docs/*.md`
  finds 7 hits resolving to 5 distinct missing files, two of them in `docs/cli-output-contract.md`
  (lines 55 and 91).
- **F-11 reproduced**: parser walk gives 249 leaves; exactly 29 declare neither `--color` nor
  `--no-color`; all 29 are the `agy`/`antigravity`/`oc`/`opencode`/`run as`/`run ipd` forwarders plus
  `__complete`. `cli._dispatch(["attention","--color","--no-color"])` -> exit 2 with
  `argument --color: not allowed with argument --no-color`.
- **F-12 reproduced verbatim** from spec `uonrjg` A13, including criterion (c), "the document's wording
  is the stale artifact", "AN IMPLEMENTER MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW" and
  "Filed as a defect against the document, not against this spec".
- **F-13 reproduced**: `xdwa5t` is `done` with a byte-identical Summary and the history line "OBSOLETE
  at 877545fc, closed during graduate-top10 triage: duplicate of bar5t8".
- **F-14 reproduced**, all eight spellings: `' 1 '`, `'TRUE'`, `'On'`, `'2'` all COLORED on a pipe;
  `'OFF'`, `'False'`, `' no '`, `''` all monochrome on a TTY with `NO_COLOR=1`.
- **F-15 reproduced**: tracked non-`.aw/` Markdown citing `FORCE_COLOR` is exactly
  `docs/cli-output-contract.md`, `docs/cli-human-guide.md`, `GUIDING_PRINCIPLES.md` and
  `DECISIONS.md`; both of the latter mention it only as one signal `should_color` honors.
- **V-02's whole probe list verified accurate** ahead of execution: all nine claims the new guide
  sentence will make measure as the plan predicts.
- Gate and carrier facts: item `bar5t8` `graduated`, `- Work-Kind: bug`, `- Blocks-Release: next`;
  `next` resolves to the single `planned` release `f33nrj`. Carrier `ikxtkj` is `open` and covers both
  the four other citations and the general-guard idea, and explicitly excludes line 55 as this plan's.
- Convention check: `tests/test_term.py` uses `addCleanup` plus `addCleanup(T.set_color_override, None)`
  in three classes, as the plan states, and backlog `4znh53` records the module-global cause.
- Suite baselines: bare `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 43.80s`;
  `python3 -m pytest tests/test_term.py -o addopts=""` -> `23 passed`.
