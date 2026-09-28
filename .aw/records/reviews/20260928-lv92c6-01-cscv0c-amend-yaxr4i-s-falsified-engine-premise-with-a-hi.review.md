# Review findings: plan cscv0c

- Subject-Id: cscv0c
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5a1f20e3` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `"outcome":"clean"`, `findings: 0`) and `--phase
review-finalize --agent` conforms after revision with `findings: 0`. No pre-review snapshot was owed:
`git status --short` reported the tree clean with the plan committed and unmodified.
`check_engine.evaluate_durable_carrier` returned ZERO drifts, and `aw check` reports 2 repository
errors, NEITHER naming this plan or its Set.

EVERY AUTHORED FINDING WAS RE-DERIVED INDEPENDENTLY AND ALL TEN REPRODUCED, several to the digit.
F-01: the quoted sentence is at `yaxr4i` line 103, verbatim as quoted. F-02: `z8ddk0` is `executed`,
`term.should_color` is the single originating definition, `runner_shared.should_color`'s body is
`return term.should_color(stream)`, and `pwatch` calls `term.should_color` directly - and only TWO
`def should_color` remain package-wide, one of them the sanctioned delegation. F-03: the direct call
gives 0 findings with `_citation_anchor_applies` False, and 11 with the date substituted, including
`Diagnostic(line=103, ..., "citation 'term.py:74-98' has no durable anchor")`. F-05: `aw ipd set
executed yaxr4i --dry-run` refuses with `AW-LIFECYCLE-ROLE-001` and leaves `git status --short` empty.
F-06: 387 of 797 executed plans carry a `file.py:NN` citation. F-09: the sentence is at 103, not the
item's 97. F-10: `term.should_color` is at line 330 and lines 74 to 98 hold `is_zero_width`,
`visible_width` and `_ZERO_WIDTH_CATEGORIES`, unrelated display-width code, so the offset points at a
different subject entirely. F-08: `aw ipd note` is an invalid choice while `aw backlog note` and
`aw specs note` both exist. Both OQ measurements also hold: zero `docs/` mentions of `aw ipd lint`'s
`--all`, `--legacy` or `--detail`, and `isg0kg` is `graduated` carrying the same false sentence.

THE PLAN'S CENTRAL JUDGEMENT IS RIGHT AND TWO CHOICES DESERVE NAMING. It correctly identifies that the
item's PREFERRED option 1 ("amend when `yaxr4i` next changes for another reason") is not merely less
attractive but UNAVAILABLE, because an executed plan has no next change and the tooled route is refused
before any write - and it measured that rather than asserting it. And it correctly declines to build a
new checker, recognizing that the sentence's checkable half is its CITATION and that the shipped
`IPD-C801` already flags it exactly. That reframing is what turns a vague "prose accuracy checker may
not be feasible" into a bounded change.

WHAT REVIEW FOUND IS THAT THE BOUNDED CHANGE WAS AIMED AT THE WRONG SUPPRESSOR, AND WOULD HAVE SHIPPED
A FLAG THAT DOES NOTHING FOR THIS PLAN'S OWN TARGET.

**THERE ARE TWO SUPPRESSORS, NOT ONE (PR-501, BLOCKER).** F-03 concluded the advisory is "SILENCED
ONLY BY A DATE", and E-03 was specified on that premise, with an Expected outcome promising the line-103
advisory from `aw ipd lint <flag> <yaxr4i>`. That premise is true of a DIRECT call to
`check_citation_anchors` and FALSE of the `aw ipd lint` path E-03 must actually change. `lint_text`
returns `LintResult(S.DISPOSITION_LEGACY, [])` for any file under a terminal directory, at a branch
sitting ABOVE every `check_*` call, so `check_citation_anchors` is unreachable through
`lint_file`/`lint_text` for an `executed/` plan regardless of its date. Measured three ways:
`lint_file(yaxr4i)` gives `legacy/not evaluated` with `advisories: 0`; monkeypatching
`CITATION_ANCHOR_CUTOVER_DATE` to `20200101`, which defeats the date fence ALONE, STILL gives
`legacy/not evaluated`, `advisories: 0`, `IPD-C801` count 0; only with that patch AND `legacy=True` do
the 11 findings appear. `yaxr4i` is under `executed/`. So an executor building exactly what E-03
described would produce ZERO advisories on the single file the plan promises to surface, and would have
no way to tell from the spec that they had failed.

WORSE, THE TEST PLAN WOULD HAVE PASSED ANYWAY. E-04's four properties all used a synthetic fixture
whose directory was unspecified; on a `pending/`-shaped fixture every one of them passes for a
date-fence-only flag. So the suite would have been green on a flag that does not work for the case that
motivated it - which is the same shape of failure as the deleted-pin problem the plan's own test-policy
paragraph warns about.

THE OBVIOUS WORKAROUND IS ALSO WRONG, and worth recording because an executor would reach for it. The
existing `--legacy` flag does get past the terminal short-circuit, but on `yaxr4i` it exits **1** with
disposition `error` and `IPD-S404: status 'executed' is incompatible with checkpoint 'author'`, against
`exit 0` for the default. Composing the new flag with `--legacy` would therefore make asking an advisory
question redden a run - precisely the harm E-03's own constraint (2) forbids, and the one way this
E-item could do real damage.

A CLEAN ROUTE DOES EXIST, which is why this is a repairable blocker and not a replan.
`check_citation_anchors` is public, takes only `(doc, text)`, is gated internally by
`_citation_anchor_applies` alone, and its source references neither `directory` nor terminal-dir state,
so the flag path can invoke it directly on the parsed document. That keeps `lint_text`'s branch
structure byte-identical, leaves the grandfathering intact, and cannot move a disposition because it
never touches `diags`.

**THE APPEND ROUTE WAS VERIFIED END TO END RATHER THAN LEFT TO E-02 (PR-502).** Since E-02's whole
purpose is to discover whether a hand edit under `executed/` survives the gates, and since a refusal
would be a finding about the gates rather than about this plan, I exercised it: a probe note inserted as
the first history record and STAGED, `python3 -m agent_workflows ipd-executed-gate` exit 0,
`ipd-status-untooled-gate` exit 0, `git diff --cached --numstat` reading `1 0`, then fully reverted
(`git restore --staged` then `git restore`, `git status --short` empty, zero matches for the probe
string). So the route works and E-02 should CONFIRM rather than discover, which is worth stating in the
plan so an executor is not braced for a refusal that will not come.

One further item: the gate was strong on honesty and commit safety but missing a declared scope fence,
the shared-checkout staged-set verification, and any statement of the `Blocks-Release: next` gate this
plan inherits from `lv92c6` (PR-503).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-501 | BLOCKER | IN-SCOPE | A. Correctness / E. Testing (a spec whose stated outcome is unreachable, with a test plan that would pass anyway) | F-03 as authored: "SILENCED ONLY BY A DATE"; E-03's Expected outcome promising the line-103 advisory from `aw ipd lint <flag> <yaxr4i path>`; `ipd_lint.lint_text`'s branch `if _is_terminal_dir(directory) and not legacy and checkpoint != "post-transition": ... return LintResult(S.DISPOSITION_LEGACY, [])`, which precedes every `check_*` call and the `advisories` assembly; measured: `lint_file(yaxr4i)` -> `legacy/not evaluated`, `advisories: 0`; with `CITATION_ANCHOR_CUTOVER_DATE` patched to `20200101` -> STILL `legacy/not evaluated`, `advisories: 0`, `IPD-C801` count `0`; with that patch AND `legacy=True` -> `error`, `IPD-C801` count `11` incl. line 103; `yaxr4i` resides in `.aw/records/plans/executed/` | **E-03's STATED OUTCOME IS UNREACHABLE BY THE MECHANISM E-03 SPECIFIES, AND E-04 WOULD HAVE GONE GREEN ANYWAY.** The date fence is not the only suppressor: the terminal-directory short-circuit silences the advisory for every `executed/` plan independent of date, and this plan's own demonstration target is such a plan. An executor implementing the authored spec produces zero advisories on `yaxr4i` while E-04's four properties, on a fixture whose directory was unspecified, all pass. That is a flag that does not work shipped behind a green suite. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-03 now names BOTH suppressors with the three measurements, refuses the `--legacy` composition with its measured exit-1/`IPD-S404` reason, and specifies the direct-call route (public, pure, internally gated only by `_citation_anchor_applies`, referencing no directory state) with `lint_text`'s branch to be left byte-identical. Expected outcome now requires the exit code to equal the measured default `0` and forbids both `--legacy` and editing the short-circuit, with a STOP-and-report clause if neither is possible. New F-11 (the second suppressor, three measurements), F-12 (why `--legacy` is not advisory-safe) and F-13 (the viable route, verified) added. E-04 gains properties 5 (a TERMINAL-directory pre-cutover fixture must produce the advisory) and 6 (the grandfathering proven still in force). V-03 requires the unmodified branch pasted plus a `lint_file` call showing the legacy disposition intact; V-04 requires property 5 shown RED under the date-fence-only mutation while 1 to 4 still pass. Goal and Proposed change 3 corrected. |
| PR-502 | LOW | IN-SCOPE | C. Operability / G. executability (a verifiable precondition left unverified) | E-02 as authored: "Both were READ at authoring ... each exemption is conditional and the conditions are what must be confirmed"; gate logic read at the symbol (`same_plan_at_head`, `moved_into_executed`, `gained_executed`, and `check_status_untooled`'s `/executed/` skip); measured at review with a probe note actually STAGED: `ipd-executed-gate` exit `0`, `ipd-status-untooled-gate` exit `0`, `git diff --cached --numstat` -> `1 0`; probe then reverted, `git status --short` empty, 0 matches for the probe string | E-02 correctly refused to assume the gates exempt the append, but the question is cheaply ANSWERABLE at review rather than at execution, and the answer changes the executor's posture: the plan's gate warns at length about the `--no-verify` reflex for a refusal that does not in fact occur. Leaving it open also leaves a small chance the whole task-group-1 mechanism is infeasible, which a reviewer should not hand to an executor unresolved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now records the review-measured end-to-end probe (both gates exit 0, `numstat 1 0`, fully reverted) and states that E-02 is expected to CONFIRM rather than discover, so a refusal would be genuinely surprising and genuinely worth escalating. E-02 itself is left in place unchanged, because confirming against the executor's own staged diff is still the right check. |
| PR-503 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: path-scoped `aw commit`, no-push, no-`git add -A`, no-`--no-verify`, separate-commits guidance and the post-gate finalize ownership all PRESENT; ABSENT: any scope-fence declaration with the make-and-justify disposition, the shared-checkout `git diff --cached --name-only` verification, and any statement of the inherited release gate; plan front matter carries `- Blocks-Release: next` and `- From-Backlog: lv92c6`, and `lv92c6` carries `- Work-Kind: bug` with `- Blocks-Release: next` | Three required elements missing. The release-gate omission matters most: this plan is the CARRIER of a bug's release gate, so an executor who cleared or ignored it would break the handoff that lets `lv92c6` close legitimately. The shared-checkout verification matters unusually here because the plan edits a file under `.aw/records/plans/executed/` and the two gates in E-02 are exactly the hooks whose rejection can leave foreign paths staged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a DECLARATION-style scope fence with the make-and-justify disposition (naming `--scope-reason`/`--scope-ack`) and an explicit note that its two STOP directives are narrow safety conditions rather than scope questions; the shared-checkout staged-set verification with the re-verify-after-failed-commit rule; the inherited `Blocks-Release: next` statement with the do-not-clear instruction and the close-legitimacy link to `lv92c6`; and a three-item "what the human is approving" summary. `aw check` added to Required tests as the proof the gate and handoff link resolve. Scope check's over-scope paragraph now records that the E-03 reshape needs no new path and adds a negative constraint inside a declared file. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-501: E-03's mechanism cannot reach its stated outcome. REPLAN the item, drop task group 2, or respecify the mechanism with the second suppressor named? | RESPECIFY IN PLACE, naming both suppressors and the direct-call route, and strengthen E-04 to pin the terminal-directory case. | (a) REPLAN: rejected. The plan's diagnosis (the shipped check already catches it; only suppression hides it) is CORRECT and is the valuable part; what was wrong is a factual claim about how many suppressors exist, which is a bounded correction. (b) Drop task group 2 and ship only the history append: rejected, that abandons the general class the backlog item names and leaves the next stale citation equally unreported. (c) Permit the `--legacy` composition: rejected on measurement - it exits 1 with `IPD-S404` on the target file, so it converts an advisory question into a red run, violating E-03's own constraint (2). (d) Edit `lint_text`'s terminal short-circuit: rejected, that changes behavior for every terminal-directory plan to serve one advisory, and the grandfathering is a considered design choice the plan itself argues must not be reverted by default. | Read `lint_text`'s branch order at the symbol; measured the three-way experiment (default / date-fence-defeated / date-fence-plus-legacy); measured `aw ipd lint --legacy <yaxr4i>` -> exit 1, `IPD-S404`; verified `check_citation_anchors` is public, takes `(doc, text)`, references no `directory` or terminal state in its source, and is gated only by `_citation_anchor_applies`. | yes |
| D-2 | PR-502: should the reviewer exercise the executed-plan append against the real gates, or leave it to E-02 as authored? | EXERCISE IT, then revert, and record the result in the plan. | Leave it to E-02: rejected. The feasibility of task group 1's ONLY mechanism was an open empirical question whose answer a reviewer can get in one minute, and the workflow's HOW-question standard is to demonstrate rather than describe. Had the gates refused, this would have been a finding about the gates contradicting `AGENTS.md` and a far larger matter than this plan. | Staged a probe note and ran both gates: exit 0 and exit 0, `numstat 1 0`. Reverted with `git restore --staged` then `git restore`; `git status --short` empty and 0 matches for the probe string afterwards, so no repository state was left changed. | yes |
| D-3 | OQ-02 resolved that no `docs/` entry is needed. Accept, or require one? | ACCEPT, independently re-measured. | Require a `docs/` entry: rejected on the observed convention rather than on preference. Adding documentation for one new advisory flag while three shipped flags have none would be inconsistent, and the `--help` text is where this repository puts them. | Re-measured at review: `grep` for `ipd lint --all`, `--legacy` or `--detail` across `docs/` returns ZERO hits; the only `docs/` mention of any `aw ipd lint` flag is `--phase` inside a worked example in `docs/artifact-lifecycles.md`. | yes |
| D-4 | OQ-01 resolved to defer the identical false sentence in `isg0kg` to a follow-up carried by `lv92c6`. Accept, or fold it in? | ACCEPT the deferral. | Fold `isg0kg` into this plan: rejected on mechanism, which is the plan's own stated reason and it holds. `isg0kg` is `graduated` (live) so it takes a TOOLED `aw backlog note`; `yaxr4i` is executed and admits only an untooled hand-appended history line. Pairing a tooled backlog write with an untooled plan edit in one commit for one sentence mixes two record types and two mechanisms for no gain. | Verified `isg0kg` is `- Status: graduated` and carries "`term.should_color()` (`term.py:74-98`) already implements the wanted semantics"; verified `aw backlog note` exists and `aw ipd note` does not; the row carries `- Carrier: lv92c6`, and `evaluate_durable_carrier` returns zero drifts. | yes |
| D-5 | Is the plan's tree-wide census claim (the false sentence never reached `docs/`) true, and does it license leaving `docs/` out of scope? | YES, independently confirmed. | Widen scope to `docs/`: rejected, there is nothing there to fix. | Re-ran the census: the phrase appears in `yaxr4i`, `isg0kg`, backlog `lv92c6`, this plan, and three records that correctly report it as FALSE (`nyz8dt`, `pow5sj`, `z8ddk0`), plus two review records. No `docs/` file carries it. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. Both of the plan's open questions were already `resolved` at authoring and both were
independently re-measured and upheld (D-3, D-4), so the plan carries no open question.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0` BEFORE any
  edit; `--phase review-finalize --agent` -> exit 0, `"findings":0` after all edits.
- `check_engine.evaluate_durable_carrier` on this plan -> `drifts: 0`. `aw check` -> 2 repository
  errors, neither naming this plan or its Set. All four cited carriers resolve: `lv92c6` (graduated),
  `ikxtkj` (open), `p0a5kr` (open), `xelvyi` (done).
- Suite baseline measured BARE: `2935 passed, 2 skipped, 3 warnings in 42.30s`. No code, test,
  configuration, spec or doc file was modified by this review.
- **F-01 confirmed verbatim.** `grep -n "already correct and complete"` on the `yaxr4i` file -> `103:`
  followed by the sentence exactly as the plan quotes it, inside `## Project conventions discovered`.
- **F-02 confirmed.** `aw find plans z8ddk0` -> `✓ executed z8ddk0 lifeglyph`. `grep -rn "def
  should_color" agent_workflows/*.py` -> exactly TWO, `term.py:330` and `runner_shared.py:314`, the
  latter documented as "A SANCTIONED ONE-LINE DELEGATION to `agent_workflows.term.should_color`, which
  is the single ORIGINATING definition of this decision package-wide (plan `z8ddk0`...)" with body
  `return term.should_color(stream)`. `pwatch.py` -> `color_enabled = not args.no_color and
  term.should_color(sys.stdout)`.
- **F-03 reproduced exactly.** `_citation_anchor_applies(doc)` -> `False`;
  `CITATION_ANCHOR_CUTOVER_DATE` -> `20260923`; plan `- Date:` -> `2026-09-08`; direct
  `check_citation_anchors` -> 0 findings. With the date substituted to `2026-09-28` in memory -> 11
  findings, enumerated in full in the plan's amended F-03, including `line=103, IPD-C801, "citation
  'term.py:74-98' has no durable anchor"`.
- **PR-501 / F-11 measured three ways**, as recorded in the findings table. The branch was read at the
  symbol in `lint_text` and confirmed to precede `check_metadata` and every other `check_*` call, with
  `advisories` assembled only after it.
- **PR-501 / F-12 measured.** `aw ipd lint <yaxr4i>` -> exit `0`, `legacy/not evaluated`. `aw ipd lint
  --legacy <yaxr4i>` -> exit `1`, disposition `error`, `IPD-S404: status 'executed' is incompatible
  with checkpoint 'author'`.
- **PR-501 / F-13 verified.** `check_citation_anchors` is public and callable; `inspect.getsource`
  shows no `directory` and no `terminal` reference; its only gate is `if not
  _citation_anchor_applies(doc):`; its docstring states the advisory-only contract the plan quotes.
- **PR-502 measured, then fully reverted.** Probe note inserted as the FIRST record under `yaxr4i`'s
  `## Workflow history` and `git add`ed. `git diff --cached --numstat` -> `1	0`. `python3 -m
  agent_workflows ipd-executed-gate` -> exit `0`. `python3 -m agent_workflows
  ipd-status-untooled-gate` -> exit `0`. Then `git restore --staged` and `git restore`; `git status
  --short` empty; `grep -c "PROBE ONLY"` -> `0`. No repository state left changed.
- **F-04 confirmed at the symbol.** `executed_transition_gate` documents "An ORDINARY EDIT to a plan
  already in `executed/` under the same `- Id:` is NOT a transition and is NOT reported", and binds the
  exemption to `same_plan_at_head` as well as path, with `moved_into_executed` and `gained_executed`
  both required false - matching the plan's reading and matching the measured exit 0.
- **F-05 reproduced exactly.** `aw ipd set executed yaxr4i --dry-run --actor 'opencode/probe' --message
  probe` -> `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role
  process must not run them (refused: terminal finalize transaction)`, `worker-role`, and `git status
  --short` empty afterwards.
- **F-06 reproduced exactly.** `grep -rlE '`[a-z_]+\.py:[0-9]+' .aw/records/plans/executed/ | wc -l` ->
  `387`; `ls .aw/records/plans/executed/*.ipd.md | wc -l` -> `797`.
- **F-07 confirmed.** `isg0kg` is `- Status: graduated` and its line 36 reads "`term.should_color()`
  (`term.py:74-98`) already" with the "already-correct engine" phrase at line 39. The tree-wide census
  found the claim in `yaxr4i`, `isg0kg`, backlog `lv92c6`, this plan, and three records that correctly
  report it FALSE (`nyz8dt`, `pow5sj`, `z8ddk0`) - no `docs/` file.
- **F-08 reproduced exactly.** `aw ipd note` -> `invalid choice: 'note' (choose from 'lint',
  'scaffold', 'sync', 'recheck-readiness', 'execute-set', 'board', 'set', 'dependencies', 'begin',
  'finalize')`; `aw backlog note --help` and `aw specs note --help` both render usage.
- **F-09 reproduced.** The sentence is at line 103; backlog `lv92c6` says "line 97" at its own line 16.
- **F-10 reproduced exactly.** `grep -n "^def should_color" agent_workflows/term.py` -> `330`. Lines 74
  to 98 read at review contain `_ZERO_WIDTH_CATEGORIES`, `is_zero_width` and `visible_width` - display
  width code with no relation to the color decision, confirming the plan's "points at a different
  subject entirely".
- **Convention citations verified.** `plan_readiness.extract_newest_history_entry` exists at
  `plan_readiness.py:245`; `.aw/records/plans/README.md` states "the FIRST record is the most recent
  and the last is the oldest" and names that function, including the "a reader that sliced to end of
  file and took the last bullet is the bug that fix replaced" sentence the plan quotes;
  `ipd_lifecycle` holds "The full plan status vocabulary a history line's leading token may
  legitimately be (a STATUS transition)" with "A history line whose token is NOT one of these is a
  workflow NOTE".
- **OQ-02 re-measured (D-3).** Zero `docs/` hits for `ipd lint --all`, `--legacy` or `--detail`; the
  only flag mention anywhere in `docs/` is `--phase` in a worked example.
- **Release gate verified.** Plan carries `- Blocks-Release: next` and `- From-Backlog: lv92c6`;
  `lv92c6` carries `- Work-Kind: bug`, `- Blocks-Release: next`, `- Status: graduated`,
  `- Graduated-To: lv92c6`, so the gate is correctly inherited and the handoff link resolves.
- **Honest-limit claim re-verified.** `aw ipd lint <yaxr4i> --detail` -> `legacy/not evaluated`, exit
  `0`, confirming nothing machine-readable inspects the note's CONTENT and that V-01 is load-bearing.
