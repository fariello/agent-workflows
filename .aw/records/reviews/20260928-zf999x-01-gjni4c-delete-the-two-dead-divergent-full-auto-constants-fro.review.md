# Review findings: plan gjni4c

- Subject-Id: gjni4c
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `592ca322` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`; `--detail` reported `conforming` with no
`IPD-Z602` advisory) and `--phase review-finalize --agent` conforms after revision with `findings: 0`.
No pre-review snapshot was owed: the plan was committed and unmodified (`git status --short` clean) and
the lane-input copy at `.aw/state/lane-inputs/rev-2/` is byte-identical to the tracked file (`diff`
reported no difference).

THE PLAN IS GOOD AND ITS CENTRAL DESIGN CHOICE IS THE RIGHT ONE. The defect is real, the deletion is
safe, and OQ-02's decision to write a MECHANICAL SWEEP rather than a named-constant test is correct for
the reason the plan gives: a test naming these two constants would pass forever after E-02 deletes
them. Both of the sweep's load-bearing measurements reproduce EXACTLY at this HEAD, which is unusual and
worth recording: 10 `UPPER_CASE` names are co-defined across all three modules, exactly 2 have a shared
value matching neither host (the two being deleted), and 9 of 10 "differ" when compared by unparsed
source text - so F-06's insistence on comparing RESOLVED values is not a stylistic preference but the
difference between a usable guard and one that flags almost everything.

WHAT REVIEW FOUND IS THAT THE PLAN'S STATED SAFETY MECHANISM IS ONE LAYER OFF FROM THE REAL ONE.

**THE MESSAGE DOES NOT ARRIVE BY PARAMETER (PR-101, HIGH).** F-03 says "THE DELETION IS SAFE BECAUSE
THE VALUE ALREADY ARRIVES BY PARAMETER", and E-04 builds its assertion on that: it pins
`inspect.signature(runner_shared.set_plan_approved).parameters["message"].default is
inspect.Parameter.empty`. That is true of the shared function and FALSE of the path the runner takes.
Both HOST wrappers declare `def set_plan_approved(repo, id6, message: str = FULL_AUTO_APPROVAL_MESSAGE)`,
and BOTH live call sites invoke them with two arguments (`set_plan_approved_fn(repo, id6)` in the
queue-build arm, `set_plan_approved(repo, item["id6"])` in the dispatch arm). So no caller ever supplies
a message: it comes from each HOST'S DEFAULT. Measured, `inspect.signature(oc.set_plan_approved)
.parameters["message"].default` is the host message string, not `Parameter.empty`, and the same for agy.
The consequence for the plan is precise: E-04 would have pinned the one signature no live caller uses,
while the defaulted host signature that actually decides what lands in permanent plan history went
unpinned. The deletion's SAFETY is unaffected (the host defaults reference each host's OWN constant, not
the shared one), so this is not a blocker on the deletion; it is a gap in the guard the plan exists to
build, which is why it is HIGH and UNDER-SCOPE rather than BLOCKER.

**AND THE SHARED DOCSTRING E-02 IS TOLD TO AMEND REPEATS THE SAME ERROR (PR-102, MEDIUM).**
`set_plan_approved`'s docstring says `message` "IS ALSO REQUIRED, with no default here, for a narrower
but identical reason". An executor amending that paragraph per E-02 would naturally write that the
caller supplies the message, cementing a false claim in the one comment that survives the deletion.
E-02 now carries an explicit instruction not to.

**THE V-03 EVIDENCE CONTAINS AN ABSOLUTE INTERPRETER PATH (PR-103, MEDIUM).** V-03 requires the captured
argv pasted. Measured: element 0 of that argv is the running interpreter's ABSOLUTE PATH and elements
1-2 are `-P -c` plus a multi-line bootstrap string, because `pinned_module_argv` builds it that way. The
plan lists `aw sanitize --agent` as routine; here it is specifically load-bearing, and the honest
instruction is to redact the prefix and assert on the tokens after `set`.

Three smaller items: E-04's second mutation needed a note that adding a `NamedTuple` default is legal
Python and does not break either `HOST_LABELS` construction, so the assertion flips on the ABSENCE of a
`TypeError` rather than on a construction failure (PR-104); the gate's element inventory was complete
except for the out-of-scope-edit disposition (PR-105); and the baseline the validation compares against
was unstated (PR-106), now pinned at the re-measured `2935 passed, 2 skipped`.

Every other claim in the plan was checked and HELD. F-01, F-02, F-04, F-05, F-06, F-07, F-08, F-09,
F-11, F-12, F-13, F-14 and F-15 all reproduce; the `--triples` report really does list only
`StallWatchdog`; `li44r9`'s review really does contain PR-001 verbatim as quoted; and OQ-01's
resolution-from-evidence is sound (the item's second fix direction IS already shipped, so the two
options were never alternatives).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-101 | HIGH | UNDER-SCOPE | A. Correctness / E. Testing / D. durable-history invariant | `oc_runipd.set_plan_approved` and `agy_runipd.set_plan_approved` both declared `message: str = FULL_AUTO_APPROVAL_MESSAGE`; both live call sites pass two arguments (`set_plan_approved_fn(repo, id6)` in the queue-build arm; `set_plan_approved(repo, item["id6"])` in the dispatch arm); measured `inspect.signature(oc.set_plan_approved).parameters["message"].default` == the host message string, NOT `Parameter.empty`, same for agy; plan F-03 ("THE VALUE ALREADY ARRIVES BY PARAMETER") and E-04's assertion | **THE PLAN PINS A NO-DEFAULT PROPERTY ON THE ONE SIGNATURE NO LIVE CALLER USES, WHILE THE DEFAULT THAT ACTUALLY DECIDES DURABLE HISTORY GOES UNPINNED.** The recorded message comes from each HOST WRAPPER'S DEFAULT, never from a caller. So the mechanism protecting a plan's permanent `## Workflow history` is the two host defaults plus `labels.full_auto_actor`, not a required shared parameter. E-04 as authored would have asserted a true-but-inert property and left the real one uncovered - in a plan whose entire purpose is to replace a comment with an executable guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-05 pins the HOST layer: each host's defaulted `message` asserted against the LITERAL (not against `<host>.FULL_AUTO_APPROVAL_MESSAGE`, which would repeat F-07's self-referential blindness), the default's PRESENCE asserted explicitly, the value asserted to be neither shared string, and both live two-argument call shapes pinned by source read so the premise cannot silently lapse. `Highest E allocated` 04 -> 05; V rebuilt 4 -> 5. E-04 keeps its two assertions and now states its bound. New F-03a records the measurement; F-03 narrowed to the claim that actually holds. |
| PR-102 | MEDIUM | IN-SCOPE | F. Honest documentation | `runner_shared.set_plan_approved` docstring: "`message` IS ALSO REQUIRED, with no default here, for a narrower but identical reason"; E-02's instruction to amend that paragraph | **THE COMMENT E-02 IS TOLD TO AMEND REPEATS PR-101's ERROR, SO THE AMENDMENT WOULD CEMENT IT.** An executor rewriting that paragraph would naturally write that the caller supplies the message; it does not. This is the one comment that survives the deletion, so a false claim there outlives the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now carries an explicit instruction: when amending that paragraph, do NOT write that the message is caller-supplied; write that each HOST binds its own value as its wrapper's default and that E-01's guard plus E-05's assertions keep the shared module from acquiring a third. |
| PR-103 | MEDIUM | UNDER-SCOPE | B. Privacy / leak hygiene | Measured argv element 0 is the running interpreter's absolute path, elements 1-2 are `-P -c` plus a multi-line bootstrap string (`pinned_module_argv`); V-03 requires "the captured argv for each host" pasted; plan's Required tests listed `aw sanitize --agent` only as routine | **THE EVIDENCE THIS PLAN MANDATES PASTING CONTAINS A MACHINE-LOCAL ABSOLUTE PATH.** V-03's pasted argv would carry an absolute interpreter path into a durable validation record, which is exactly what the repository's leak-sanitizer paragraph exists to prevent, and the plan flagged the sanitizer only as a generic pre-commit step. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | V-03 now requires the prefix redacted or elided and assertions made on the tokens after `set`; Required tests states the measurement and that the sanitizer runs BEFORE commit, not after; the gate carries a short evidence-hygiene line. |
| PR-104 | LOW | IN-SCOPE | E. Testing (demonstration feasibility) | `HostLabels._fields[-1] == "full_auto_actor"`; both `HOST_LABELS` constructed by keyword; verified a trailing `NamedTuple` default is legal and leaves keyword construction working; V-04's "temporarily give the `full_auto_actor` field a default and paste that assertion failing" | V-04's second mutation reads as though adding the default would break something; it does not. The field is LAST and both constructions are keyword-based, so the default is legal and both keep working - the assertion flips because no `TypeError` is raised. Without the note an executor may conclude the mutation "did not work" and skip the demonstration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 carries the note, with the measured `TypeError` text for the positive case, and states in one sentence that its two assertions do not cover the recorded message and that V-05 does. |
| PR-105 | LOW | IN-SCOPE | G. Plan executability (scope fence) | Plan gate as authored: path-scoped commit, never-push, paste-actual-output and the lifecycle line all present; no out-of-scope-edit disposition; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate carried every required execution-contract element except what to do about an out-of-scope edit. The correct wording is MAKE-AND-JUSTIFY (finalize refuses without a `--scope-reason`), not stop-and-report. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate states an out-of-scope edit is made then justified with `--scope-reason` and explicitly that it is not a reason to stop. No "STOP and report" wording added. The commit clause also now names this plan beside the two scope paths, matching what `git diff --cached --name-only` will actually show. |
| PR-106 | LOW | IN-SCOPE | E. Testing | Required tests said "compared against a baseline captured before any edit"; no number recorded anywhere in the plan | The one comparison the whole-plan regression check rests on had no value, so an executor could paste any count and call it unchanged. Every other measurement in this plan is numeric. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-measured at review with a BARE run: `2935 passed, 2 skipped, 3 warnings in 42.52s`. V-05 now states the baseline as `2935 passed, 2 skipped` explicitly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The host wrappers default `message` and no live caller passes one (PR-101). Should the plan REMOVE those defaults so the value becomes a caller obligation, or PIN them as they are? | PIN THEM. E-05 asserts the defaulted values and their presence; neither host signature changes. | (a) Remove both defaults and update the two call sites to pass each host's constant: rejected on two grounds. It is a behavior change to the `--full-auto` path, which spec `llbr2b` Section 10 places out of scope while the policy is unsettled ("CHANGING ANY VERB'S CURRENT BEHAVIOR, including `--full-auto`"), and this plan's own second deferral row already rejects exactly that. It would also widen the fence to both host files for no gain in the recorded value. (b) Leave E-04 as authored and file the host-layer gap separately: rejected, the plan's whole deliverable is an executable guard replacing a comment, and shipping it with the real mechanism unguarded would repeat the defect class it exists to close. | Measured host signatures and both live call sites; spec `llbr2b` Section 10's explicit exclusion; the plan's own deferral row prohibiting value changes; both files are outside `- Scope-Paths:` and E-05 needs no edit to them. | yes |
| D-2 | E-05 asserts each host's defaulted message. Compare it against `<host>.FULL_AUTO_APPROVAL_MESSAGE`, or against a literal spelled in the test? | AGAINST A LITERAL spelled in the test. | Read the expected value from the host constant: rejected because that is precisely the self-referential shape F-07 measured on the two shipped tests, which pass for whatever value the name holds and therefore cannot detect a value change. Repeating it in the new test would produce a guard blind to the defect it was written for. | Plan F-07, confirmed by reading both shipped tests (`assertIn(driver.FULL_AUTO_ACTOR, argv)` and the agy twin); the same reasoning the plan already applies to E-03. | yes |
| D-3 | Does PR-101 endanger the DELETION itself, and should the plan's verdict change? | No. The deletion stays exactly as authored. | Treat it as a BLOCKER on E-02: rejected on measurement. Each host's wrapper default references that HOST'S own `FULL_AUTO_APPROVAL_MESSAGE`, not the shared one, so deleting the shared pair changes no default and no recorded value; F-02's census (no executable read of either shared name anywhere) is unaffected. | `inspect.signature` on both hosts showing the defaults resolve to the host message; `rg` census of both shared names showing only assignments, host-name test assertions and prose; F-13/F-14 confirming no fingerprint or export covers them. | yes |
| D-4 | OQ-01 resolved "delete, and it needs no maintainer ruling" from evidence. Does that hold, given it removes a module attribute? | HOLDS. Left resolved and non-blocking. | Escalate it as a public-contract question for the human: rejected because the repository's compatibility surfaces are documented and module attributes are not among them, so the premise the escalation would rest on is measurably false. | `agent_workflows/__init__.py` is 42 lines and imports only `versioning` and `._compat` (re-exports no runner symbol); `rg "^__all__" agent_workflows/runner_shared.py` empty; `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md` name the CLI and the `aw.agent/v1` JSON as the contracts; the premove fingerprint fixture holds 34 symbols and none matching `FULL` or `approv`. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. Both pre-existing open questions (OQ-01, OQ-02) remain `resolved` and non-blocking and
their reasoning survives review intact: OQ-02's mechanical-sweep choice is confirmed by measurement
(F-05/F-06 reproduce exactly), and OQ-01's is confirmed by D-4.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`; `--detail`
  reported `conforming` with no `IPD-Z602` advisory.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (the new E-05, `Highest E allocated` 04 -> 05, V rebuild to 5, `Readiness` written,
  `Status` to `reviewed`). E/V counts confirmed 5 and 5.
- Lane input identity: `diff .aw/state/lane-inputs/rev-2/plan-20260928-zf999x-01-gjni4c-....ipd.md
  .aw/records/plans/pending/20260928-zf999x-01-gjni4c-....ipd.md` -> no difference; `git status --short`
  clean before editing, so no pre-review snapshot was owed.
- F-01 reproduced exactly, three modules side by side:
  - `FULL_AUTO_ACTOR`: shared `'aw-driver/full-auto'`, oc `'aw oc run --full-auto'`,
    agy `'aw agy run --full-auto'`.
  - `FULL_AUTO_APPROVAL_MESSAGE`: shared `'Auto-approved via --full-auto (review passed all gates)'`,
    oc and agy both `'auto-approved by --full-auto: review readiness cleared (not human approval)'`.
- F-02 confirmed: `rg -n "FULL_AUTO_ACTOR|FULL_AUTO_APPROVAL_MESSAGE"` over `agent_workflows/`,
  `tests/` and `tools/` returns hits only at the 4 assignments (`oc_runipd.py:1077`/`:1078`,
  `agy_runipd.py:1326`/`:1327`, `runner_shared.py:27534`/`:27535`), the 2 host-name test assertions
  (`tests/test_oc_runipd.py:2014`, `tests/test_agy_runipd_cli.py:1297`), the 2 host wrapper DEFAULTS
  (`oc_runipd.py:1084`, `agy_runipd.py:1333`) and prose in comments/docstrings. No executable read of
  either SHARED name exists.
- **F-03a, the finding that changed the plan.** All three signatures printed side by side:
  - shared: `(repo, id6, message, *, labels, argv_builder, run_checked) -> None` - `message` no default.
  - oc: `(repo, id6, message: str = 'auto-approved by --full-auto: review readiness cleared (not human approval)')`.
  - agy: identical default.
  - `parameters["message"].default is not Parameter.empty` -> True for BOTH hosts.
  - Both live call sites read and confirmed to pass TWO arguments: `set_plan_approved_fn(repo, id6)`
    in the queue-build arm and `set_plan_approved(repo, item["id6"])` in the dispatch arm.
- F-04 confirmed by reading both assignments: `oc_runipd.py:1077` is
  `runner_shared.OC_HOST_LABELS.full_auto_actor` and `agy_runipd.py:1326` is the agy twin; neither
  re-spells a literal.
- **F-05 and F-06 reproduced EXACTLY** by an AST + `getattr` probe over the three source files:
  - 10 names co-defined in all three: `ACTION_CHOICES`, `ACTION_IMPLEMENTED`, `DEFAULT_STALL_TIMEOUT`,
    `EXECUTION_SUCCESS_STATES`, `FULL_AUTO_ACTOR`, `FULL_AUTO_APPROVAL_MESSAGE`, `SUCCESS_STATES`,
    `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES`.
  - differ by SOURCE TEXT: 9 (all but `DEFAULT_STALL_TIMEOUT`).
  - shared value matches NEITHER host: exactly 2, `['FULL_AUTO_ACTOR', 'FULL_AUTO_APPROVAL_MESSAGE']`.
  So the sweep needs no allowlist, and comparing source text instead of resolved values would flag 9.
- F-07 confirmed by reading both shipped tests: each asserts
  `assertIn(<its own module>.FULL_AUTO_ACTOR, argv)`, reading the expected value from the same name the
  code under test reads.
- F-08 confirmed: `rg "FULL_AUTO_APPROVAL_MESSAGE" tests/` returns only the agy/oc host-name lines and
  no assertion on the message VALUE; `rg "readiness cleared" tests/` returns nothing.
- F-09 confirmed: the runner's console line reads
  `✓ IPD {id6} auto-approved (review readiness cleared, ...` (`runner_shared.py:33610`), and
  `run_selection_policy.DISPOSITION_REMEDIES`'s preceding comment states "overstating what a remedy
  grants is worse than omitting it" and quotes the shipped provenance string.
- E-03's target behavior verified ACHIEVABLE as specified: calling each host's `set_plan_approved` with
  `run_checked` patched captures one argv per host; the token after `--actor` is
  `'aw oc run --full-auto'` / `'aw agy run --full-auto'` and the token after `-m` is the host message.
  **Also measured: argv element 0 is the running interpreter's ABSOLUTE PATH** and elements 1-2 are
  `-P -c` plus a multi-line bootstrap string - the basis for PR-103.
- E-04's two assertions verified achievable: `HostLabels._fields` has 10 entries, `_field_defaults` is
  `{}`, `HostLabels()` raises `TypeError: HostLabels.__new__() missing 10 required positional
  arguments: ...`, and omitting only `full_auto_actor` raises `TypeError: HostLabels.__new__() missing
  1 required positional argument: 'full_auto_actor'`. Separately confirmed that `full_auto_actor` is
  the LAST field and that a trailing `NamedTuple` default is legal and leaves both keyword-based
  `HOST_LABELS` constructions working - the basis for PR-104.
- F-11 confirmed: backlog `js1oun` is `- Status: done`, closed 2026-09-25 as "duplicate of zf999x";
  spec `llbr2b` is `- Status: to-review` and its Section 10 reads "D-2 in particular ... is a live trap
  and should be filed and fixed on its own, not folded into a policy rollout", and the same section
  excludes "CHANGING ANY VERB'S CURRENT BEHAVIOR, including `--full-auto`".
- F-12 confirmed verbatim: `li44r9`'s review record PR-001 contains "a verbatim lift of
  `set_plan_approved` records every agy auto-approval as `aw oc run`", classified BLOCKER, resolved via
  maintainer decision on OQ-03.
- F-13 confirmed: `tests/fixtures/runner_shared_premove_fingerprints.json` holds 34 symbols; no name
  matches `FULL` and none matches `approv`.
- F-14 confirmed: `agent_workflows/__init__.py` is 42 lines importing only `versioning` and `._compat`;
  `rg "^__all__" agent_workflows/runner_shared.py` returns nothing.
- F-15 confirmed: both hosts assign the identical message literal independently (`oc_runipd.py:1078`,
  `agy_runipd.py:1327`), and `HostLabels._fields` contains no message field.
- Conventions claim confirmed: `python3 tools/runner_fork_scan.py --triples` reports only
  `StallWatchdog` under "ALSO DEFINED IN runner_shared", so the scanner's census does not cover
  constants.
- Source-of-origin item `zf999x` read: `- Status: graduated`, `- Graduated-To: zf999x`,
  `- Blocks-Release: next`, `- Work-Kind: bug`. The plan's `- From-Backlog: zf999x` and inherited gate
  are both correct.
- Baseline re-measured with a BARE run: `2935 passed, 2 skipped, 3 warnings in 42.52s` (PR-106).
- No code, test, or configuration file was modified by this review. It edited the plan and wrote this
  record. Every probe ran in-process via `python3` heredocs; `set_plan_approved` was exercised only with
  `run_checked` patched to a capturing stub, so no subprocess ran and no repository file was written.
