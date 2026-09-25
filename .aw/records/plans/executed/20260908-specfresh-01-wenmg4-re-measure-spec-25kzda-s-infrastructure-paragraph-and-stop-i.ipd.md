# IPD: Re-measure spec 25kzda's infrastructure paragraph and stop it going stale a third time

- Date: 2026-09-08
- Kind: child
- Concern: SPEC `25kzda`'s "STILL NET-NEW and to be built" ENUMERATION HAS GONE STALE TWICE AND IS STALE AGAIN NOW, and its whole function is to stop a graduating Set from rebuilding shipped machinery. The paragraph (`:22-31`) was itself a CORRECTION, added in `a59f2c5` on 2026-08-30 because the original text "declared ALL of the below net-new and nonexistent, which is no longer true and would mislead a graduating Set into rebuilding shipped machinery". RE-MEASURED AT HEAD, item by item, and the paragraph is unchanged since the item was filed:
  1. `From-Spec` "(absent from `ipd_schema.META_RECOGNIZED`)" is FALSE. Measured: `META_FROM_SPEC in META_RECOGNIZED` is `True`. Shipped with `check.from-spec-dangling`.
  2. `AW-Run:`/`AW-Item:` trailers "(the ledger is built but UNWIRED)" HOLDS. Measured over the WHOLE history rather than a window: zero of 2936 commits across all refs carry an `AW-Run` trailer (the scan is proven non-vacuous by a control key, `Co-authored-by` -> 20 in the last 400). Note the WRITER machinery exists (`git_commit_helper`), so the honest wording is that the trailers are built and unpassed, which is what plan `wao266` (from `a8eufb`) now addresses.
  3. prompt `Run contract` block HOLDS. Measured: zero occurrences of "Run contract" in either host driver.
  4. per-host capability descriptor is MORE STALE THAN THE ITEM SAYS, and this is the finding that most changes the fix. The item calls it "MISLEADING rather than false" because `hostcap-01` (`mjx7ne`) was then PENDING and scoped to EXTEND. `mjx7ne` HAS SINCE EXECUTED. `HostSandboxCapabilities` now carries THIRTEEN fields including the three runner-safety ones the item said "genuinely does not exist" (`supports_commit_gateway`, `supports_deny_push`, `supports_fresh_verifier_session`). So the descriptor is not partially shipped; it is shipped, and the correct statement is that two of its fields are declared-and-never-probed by deliberate decision.
  5. `aw hooks install` "(no such verb today)" HOLDS. Measured: the verb does not resolve.
  SO TWO OF FIVE ARE NOW WRONG, one in each direction of harm: item 1 would send a Set to add a SECOND `From-Spec` recognition path, and item 4 would send it to CREATE a capability module that exists, which is precisely the defect that killed `a54m79` and forced `hostcap-01` to be written in the first place.
  THE DEEPER PROBLEM IS THE ONE THE ITEM NAMES AND THIS PLAN MUST DECIDE, not the two wrong entries. A spec paragraph that enumerates "what is not built yet" acquires a maintenance burden nothing enforces, and it has now decayed twice in nine days. The item offers three options and its own audit supplies the evidence for choosing: (a) keep correcting it, (b) delete the enumeration and let plans measure current state themselves, "which is what every recent plan review actually does", or (c) keep it but mark it explicitly as a point-in-time snapshot with its measurement date and commit. The audit's finding that reviews re-measure regardless means the list's real function is to WARN, not to inform.
  THE AUDIT HALF IS CLOSED FOR ITS OWN QUESTION AND MUST NOT BE REDONE, but its CONCLUSION is narrower than "only this spec is affected". Re-measured at HEAD `fc67605d`: the corpus is 29 spec files, not 24 or 28 (`_iter_type_files(repo_root, "specs", include_retired=True)` -> 29; the 13 that `aw check specs` reports is the NON-RETIRED subset, and the two numbers are different questions, not a discrepancy). Grepping the item's own phrase set across all 29 gives `25kzda` 4 and `7ckptx` 4, with `release-record-and-blocker-gate` 2, `kw5y2s` 1, `aw-project-layout` 1 and `ipd-structure-and-linting` 1. `7ckptx`'s four and `release-record`'s two are ordinary prose about nonexistent PATHS and dangling references, not existence claims about tooling, so the item's real conclusion holds. `kw5y2s` (`approved`, `:123`) is the one that does NOT: it states "`aw check reviews` currently fails with `unknown artifact type 'reviews'`", and at HEAD that verb SUCCEEDS (`152 reviews checked`, exit 0) because `reviews` is in `ARTIFACT_TYPES`. So a SECOND live approved spec now carries a stale existence claim. That is OUT OF SCOPE for this plan (see Deferred) and is reported rather than fixed, but the item's "confined to one spec, no spec family inherited it" must not be repeated as still-true.
- Scope: Correct the two factually wrong entries in `25kzda`'s infrastructure paragraph, and decide what stops it decaying a third time. This is a FACTUAL-STATUS correction plus a durability decision; it changes NO design and the spec stays `approved`, on the `a59f2c5` precedent. EXCLUDES re-running the 24-spec audit (closed), and excludes building any of the five enumerated items.
- Scope-Paths: .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: specfresh
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wenmg4
- From-Backlog: sd2wz5

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: wenmg4 verified (set specfresh, attempt 1).
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-901..PR-907 all FIXED, no deferrals. Re-measured all five enumerated claims independently at HEAD fc67605d and the plan's measurements are correct, including its stronger-than-the-item item 4 correction; both cited shas resolve. PR-901 (HIGH): a SECOND paragraph in the same preamble, four lines from the edited text, is stale the same way - the Section 2.1 grammar paragraph says run unverifiable/--allow-unverifiable/--unverifiable-ok 'all grep to zero' while both flags are REGISTERED argparse options on start and resume on BOTH hosts (implemented=True, runner_shared.py:1938-1960), landed 08aab7ed on 2026-09-05, the paragraph's own measurement date; added as E-05/V-05 inside the already-declared file, so no new scope path. PR-903: E-03's durability decision would have covered one point-in-time paragraph of four, two of them now measured stale, so it now must govern all four. PR-902 (HIGH): the suite baseline was wrong in both halves and named a test that passes - real state 1 failed, 5958 passed at test_reporting_contract.py ParityTests, caused by another party's gitignored opencode-recovery/ tree, with a do-not-clean-up prohibition and node-id comparison replacing the count comparison. PR-904: three of four byte-pinned spec regions were unnamed (4.1 abort table, 2.1 fenced grammar, 2.5a fenced blocks); verified the preamble edit cannot reach any (no fence, no RUN- row; those three files 261 passed). PR-906: three verdicts rest on a zero, so E-01 now requires a whole-history scan (0 of 2936) plus a non-vacuity control. PR-907: forbids inventing a test/check enforcement mechanism. PR-905: the item's 'confined to one spec' is no longer true - kw5y2s (approved) claims aw check reviews fails with unknown artifact type reviews while that verb now succeeds (152 reviews checked, exit 0); reported as F-15, NOT fixed (undeclared spec), raised to the maintainer as non-blocking OQ-04. Four decisions recorded (D-1..D-4), all reversible. E/V go 4->5 each, bijection intact; aw ipd lint --phase review-finalize conforming. Readiness go-pending-approval: OQ-01 remains open by design and is non-blocking, and no unfixed BLOCKER/HIGH remains.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sd2wz5`. All five enumerated claims were re-measured at HEAD rather than trusted, and the paragraph is unchanged since filing. FOUR OF FIVE MATCH THE ITEM EXACTLY: `From-Spec` is recognized (item 1 stale, as filed); trailers still unpassed (item 2 holds, 0 in 400 commits); no `Run contract` block (item 3 holds, 0 hits in both drivers); `aw hooks install` absent (item 5 holds). ITEM 4 IS MORE STALE THAN THE ITEM RECORDS, which changes the fix: the item calls the capability descriptor "MISLEADING rather than false" on the basis that `mjx7ne` was PENDING and would EXTEND it. `mjx7ne` HAS EXECUTED, and `HostSandboxCapabilities` now carries 13 fields including all three runner-safety fields the item said "genuinely does not exist", two of which are declared-and-never-probed by deliberate decision. So the honest correction for item 4 is stronger than the item's suggested rewording. THE AUDIT HALF IS CLOSED and is explicitly not redone: 28 specs now (was 24), hits still confined to `25kzda`. This plan carries no `Blocks-Release` because the item carries none; it is `Work-Kind: chore` and the maintainer did not gate it.

## Goal

Make a paragraph whose only job is preventing duplicated work stop causing it, and decide whether a hand-maintained "not built yet" list should exist at all.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before editing a spec

- [x] E-01 RE-MEASURE ALL FIVE ENUMERATED ITEMS AT YOUR HEAD AND WRITE THE RESULTS DOWN, because this paragraph's whole failure mode is being edited from a stale reading. Do not trust this plan's measurements; they will themselves be days old.
  THE FIVE, WITH THE EXACT CHECK FOR EACH: `From-Spec` -> `ipd_schema.META_FROM_SPEC in ipd_schema.META_RECOGNIZED`; the trailers -> `git log --all --format='%(trailers:key=AW-Run,valueonly)' | grep -c .` over the WHOLE history (not a 400-commit window, which cannot distinguish "never used" from "not used lately"); the prompt `Run contract` block -> grep both host drivers; the capability descriptor -> enumerate `HostSandboxCapabilities`'s dataclass fields and check `mjx7ne`'s lifecycle directory; `aw hooks install` -> attempt the verb and read its exit.
  A ZERO RESULT MUST BE PROVEN NON-VACUOUS, because the three items that HOLD all rest on a count of zero and a zero is equally the signature of a broken command. For the trailer scan, run the identical command with a key that DOES exist (`Co-authored-by` -> 20 in the last 400 at authoring) and paste BOTH. For each grep, paste the command including its path arguments so a reader can see the files were actually read; `grep -c PATTERN <file1> <file2>` printing a per-file `0` is adequate proof, a bare unqualified `0` is not.
  AUTHORING BASELINE, for comparison only: item 1 STALE (recognized), item 2 HOLDS (0 of 2936 across all refs), item 3 HOLDS (0 hits in each driver), item 4 STALE AND STRONGER (13 fields, `mjx7ne` executed), item 5 HOLDS (verb absent, exit 2, and note the failure text names the whole verb vocabulary, which is itself the proof).
  IF AN ENTRY HAS MOVED AGAIN, THAT IS THE POINT, NOT AN OBSTACLE. Record it and correct it in E-02. A third decay between this plan's authoring and its execution is the strongest possible argument for E-03's durability decision, so report it prominently rather than quietly folding it in.
  - Depends on: none
  - Expected outcome: a per-item measured verdict at your HEAD with the command used for each, and an explicit note of any entry that moved since this plan was authored.
  - Execution state: performed

### Task group 2: correct the facts

- [x] E-02 AMEND ONLY THE FACTUALLY WRONG ENTRIES, and change no design. This is the same class of edit as `a59f2c5` itself, which is the precedent that keeps the spec `approved`.
  MOVE `From-Spec` OUT OF "STILL NET-NEW" and into the already-shipped list, citing the commit that landed it together with `check.from-spec-dangling`. The item names `8c437188` (merged `b0eb74e6`); VERIFY that sha resolves at your HEAD before citing it, since a cited sha that does not resolve is worse than no citation.
  REWORD THE CAPABILITY DESCRIPTOR ENTRY TO MATCH WHAT SHIPPED, which is stronger than the item's suggestion. It is not "partially shipped": `mjx7ne` executed and the descriptor now carries all three runner-safety fields. The honest statement is that the descriptor EXISTS and must be EXTENDED not created, that `host_sandbox_profile.py` owns it, and that `supports_commit_gateway`/`supports_deny_push` are DECLARED AND NEVER PROBED by deliberate decision so they fail closed. Naming that last part matters, because a Set reading "exists" might otherwise assume those two are usable.
  LEAVE ITEMS 2, 3 AND 5 ALONE if E-01 confirms they hold. Do not "improve" wording that is still true; every touch of this paragraph is a chance to introduce a new inaccuracy.
  SHARPEN ITEM 2 ONLY IF E-01 SUPPORTS IT: the trailers' WRITER machinery exists while nothing passes them, and plan `wao266` (from `a8eufb`) now owns the wiring. If that is still true, saying "built but never passed, owned by `wao266`" is more useful than "built but UNWIRED" and is still a factual-status edit rather than a design change.
  - Depends on: E-01
  - Expected outcome: exactly the wrong entries amended with resolving citations; items that still hold are untouched; no design text changed; the spec remains `approved`.
  - Execution state: performed

- [x] E-05 AMEND THE FOURTH PREAMBLE PARAGRAPH TOO, because it makes the same class of claim, is stale in the same direction, and sits four lines from the text E-02 edits. Discovered in review, not by the item.
  WHAT IS WRONG. The paragraph beginning "LIKEWISE, SEVERAL COMMANDS IN SECTION 2.1's GRAMMAR DO NOT EXIST as written (measured 2026-09-05)" asserts that "the interactive phrase `run unverifiable`, `--allow-unverifiable` and `--unverifiable-ok` all grep to zero". At authoring-review HEAD `fc67605d` all three EXIST: `--allow-unverifiable` and `--unverifiable-ok` are REGISTERED argparse options on the `start` and `resume` subcommands of BOTH hosts, declared with `implemented=True` in `runner_shared.RunPolicyFlag` (`:1938-1960`), and the phrase `run unverifiable` occurs in seven places under `agent_workflows/`. They landed in `08aab7ed` (2026-09-05, "wire spec 2.1's run flag surface onto both hosts"), the SAME DAY the paragraph was measured, which is exactly how a point-in-time snapshot decays.
  WHY THIS IS IN SCOPE WHEN THE OTHER SPECS ARE NOT. This is the same file, the same preamble, the same defect class, and the same declared `Scope-Paths` entry, so fixing it needs no new scope. It also directly serves E-03: whatever durability decision is made must apply to EVERY point-in-time paragraph in this preamble, and a decision applied to one of four while the neighbor keeps decaying is not a fix. Leaving it would also make the plan's own claim to have de-staled this spec false.
  RE-MEASURE FIRST, DO NOT TRUST THE ABOVE. Check registration through the parser rather than by grep, since a grep hit in a help string is not a registered flag: build each host's parser, walk the `start` and `resume` subparsers' `option_strings`, and paste the result. Then correct only the false clause, leaving the `--json`, `--resume`, `aw runs verify` and `aw <host> prompt` clauses alone if they still hold (measured at authoring-review: `--json` is on `status` but not `start`/`resume`; `resume` is still a positional subcommand; `aw runs verify` and `aw oc prompt` both exit 2).
  DO NOT WIDEN INTO SECTION 2.1 ITSELF. `tests/test_run_flag_surface.py:115-120` parses the fenced `text` block under the `### 2.1 Command grammar` heading and binds it bidirectionally to the registered flags, so an edit THERE is a code-contract change and can fail the suite. This item edits the PREAMBLE's description of 2.1, never 2.1's own grammar block.
  - Depends on: E-01
  - Expected outcome: the false "all grep to zero" clause corrected to record that both flags are registered on `start`/`resume` on both hosts and to cite `08aab7ed`, with parser-derived evidence; the clauses that still hold left untouched; Section 2.1's own grammar block unmodified; no design text changed.
  - Execution state: performed

- [x] E-03 DECIDE WHAT STOPS THE THIRD DECAY, and implement that decision in the same edit. This is the item's real question and the reason it is worth a plan rather than a one-line correction.
  THE THREE OPTIONS, with the evidence the item's own audit supplies. (a) KEEP CORRECTING IT: rejected by track record, since it has decayed twice in nine days and nothing enforces the maintenance. (b) DELETE THE ENUMERATION and let plans measure current state, which the audit observes "is what every recent plan review actually does"; the cost is losing the WARNING that stopped `a54m79`'s duplication class. (c) KEEP IT AS AN EXPLICIT POINT-IN-TIME SNAPSHOT carrying its measurement date and commit, so a reader knows to re-verify.
  (c) IS THE DEFENSIBLE DEFAULT AND (b) IS THE HONEST RUNNER-UP. (c) preserves the warning function while making the staleness self-evident rather than invisible, and it costs one sentence. (b) is genuinely attractive because it removes the burden entirely, but it deletes the only text that tells a graduating Set "consume, do not rebuild", and that text has demonstrably prevented at least one duplication. Whichever is chosen, the choice must be RECORDED IN THE SPEC, not just in this plan, or the next reader re-litigates it.
  IF (c): the snapshot must carry a DATE AND A COMMIT and must say "re-verify before relying on this", so the paragraph's own instruction defeats its staleness. State plainly that a Set MUST measure rather than trust it.
  IF (b): the deletion must be replaced by a one-line instruction to measure current state, or the spec loses the warning entirely and this plan reintroduces the `a54m79` risk it exists to prevent.
  APPLY THE DECISION TO ALL FOUR POINT-IN-TIME PREAMBLE PARAGRAPHS, not only the infrastructure one. The preamble carries FOUR paragraphs of the same kind, and three of them ALREADY carry a measurement date while the infrastructure paragraph carries only a correction date: the infrastructure paragraph (`:21-33`), the Section 4.2 finding-code paragraph ("measured 2026-09-05"), the Section 2.1 grammar paragraph ("measured 2026-09-05", the one E-05 corrects), and note that two of the four have now been measured stale. A durability convention stated over one paragraph while three neighbors keep decaying is not a fix, it is a fourth thing to maintain. So state the convention ONCE, in a form that governs the whole preamble, and make each paragraph carry its own date and commit under it. This is the cheapest version of the decision, not a scope increase: it is the same sentence, placed where it covers all four.
  DO NOT INVENT AN ENFORCEMENT MECHANISM. A test or `aw check` rule that verifies these claims is explicitly OUT OF SCOPE (see Deferred) and would be a code change this plan has no mandate to make. The decision here is about the spec's own PROSE, whose defeat mechanism is a reader instruction, not a gate. If you conclude prose is insufficient, that is a finding to report, not scope to take.
  - Depends on: E-02
  - Expected outcome: one of the three options implemented in the spec text with its reasoning recorded there, and under (c) or (b) the warning function preserved rather than dropped.
  - Execution state: performed

### Task group 3: record it the tooled way and prove nothing else moved

- [x] E-04 APPEND THE CORRECTION VIA `aw specs note`, NOT BY HAND, and prove the spec's status and design are untouched.
  USE THE TOOLED VERB: `aw specs note <path> --message ...` appends a workflow-history record WITHOUT changing status, which is exactly this edit's shape. The precedent is in the same spec: its `2026-09-07 note (aw specs)` entry records a maintainer-ruled amendment at length. Do not hand-append a history line; the setter owns that format.
  DO NOT CHANGE `- Status:`. The spec is `approved` and a factual-status correction is not a design change, on the `a59f2c5` precedent. An agent may not set a spec `approved` or `implemented` in any case, so touching status here would be both wrong and forbidden.
  PROVE THE DESIGN TEXT IS UNCHANGED. Paste a diff scoped to the spec showing only the two preamble paragraphs and the history region moved. In particular, DO NOT touch Section 4.2's finding-code table: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so an incidental edit there IS a code change and would fail the suite.
  KNOW EVERY BYTE-PINNED REGION OF THIS SPEC, not just Section 4.2, because the plan originally named only one of four and a reader could infer the rest are free. THREE test files read this spec AS A FILE and will fail on an edit inside their anchors: `tests/test_run_evidence_completion.py:1024-1075` parses Section 4.2's `| \`RUN-` table rows AND Section 4.1's `#### Exhaustive \`ABORT RUN\` set` table; `tests/test_run_flag_surface.py:44-120` parses the fenced block under `### 2.1 Command grammar`; `tests/test_run_selection_policy.py:806-817` parses the fenced `text` blocks of `### 2.5a Draft admission gate` and asserts them character for character. VERIFIED SAFE: the preamble this plan edits (lines 1-56, above `## 1. Executive summary`) contains no fenced block and no `| \`RUN-` table row, and all three files pass at review HEAD (`261 passed`). Stay above `## 1.` and none of them can see your edit.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. THE PLAN'S ORIGINAL BASELINE WAS WRONG IN BOTH HALVES and was corrected in review; re-measured on main at `fc67605d`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`. The failure is NOT `tests/test_orchestrator_retirement.py`, which passes in isolation (`112 passed`); it is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, and its cause is the GITIGNORED `opencode-recovery/` tree of another party's session transcripts, which the test scans regardless of ignore status. It is pre-existing, is nothing to do with this plan, and MUST NOT be "fixed": deleting or editing that tree is another party's work under the shared-checkout rule. Criterion: AFTER minus BEFORE is EMPTY, compared by NODE ID rather than by count, since counts drift as other agents land tests. A spec-text edit should move nothing, so any new node id is a signal that a byte-pinned region was touched.
  - Depends on: E-03, E-05
  - Expected outcome: the correction recorded via `aw specs note`; status unchanged at `approved`; a scoped diff proving only the two preamble paragraphs and the history region changed; every byte-pinned region untouched; bare-suite failure-set delta empty by node id.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PARAGRAPH IS ITSELF A CORRECTION. `a59f2c5` (2026-08-30) added it precisely because the original claimed everything was net-new and "would mislead a graduating Set into rebuilding shipped machinery". That is the precedent for a factual-status edit keeping the spec `approved`.
- IT HAS NOW DECAYED TWICE IN NINE DAYS, which is the argument against option (a).
- `aw specs note` IS THE TOOLED SURFACE for exactly this: it appends a workflow-history record WITHOUT changing status. The same spec already carries a long `2026-09-07 note (aw specs)` entry as precedent.
- AN AGENT MAY NOT SET A SPEC `approved` OR `implemented`. Status must not be touched here, which aligns with the edit being factual rather than design.
- FOUR REGIONS OF THIS SPEC ARE BYTE-PINNED by tests that read it AS A FILE, not one: Section 4.2's `RUN-*` table and Section 4.1's abort-class table (`tests/test_run_evidence_completion.py:1024-1075`), Section 2.1's fenced grammar block (`tests/test_run_flag_surface.py:44-120`), and Section 2.5a's fenced blocks (`tests/test_run_selection_policy.py:806-817`). The PREAMBLE this plan edits contains no fenced block and no table row, so it is safe; all three files pass at review HEAD (`261 passed`).
- THE AUDIT HALF IS CLOSED for its own question (29 specs at HEAD; the item said 24, the plan said 28). Its conclusion is narrower than stated: the `detrun` defect class is confined to `25kzda`, but `kw5y2s` carries a stale existence claim of its own. Do not re-run the audit; do not repeat "confined to one spec" either.
- THE PREAMBLE CARRIES FOUR POINT-IN-TIME PARAGRAPHS, two of them now measured stale. Any durability convention has to govern all four or it is a fourth thing to maintain.
- THE SUITE'S ONE FAILURE IS ANOTHER PARTY'S GITIGNORED TRANSCRIPT TREE (`opencode-recovery/`, `.gitignore:49`) tripping `tests/test_reporting_contract.py`. Pre-existing, not yours, and under the shared-checkout rule must not be cleaned up.
- ITEM 4 MOVED SINCE FILING: `mjx7ne` executed, so `HostSandboxCapabilities` carries 13 fields including the three runner-safety ones, two of them declared-and-never-probed by deliberate decision.
- ITEM 2's OWNER NOW EXISTS: plan `wao266` (from `a8eufb`) owns passing the trailers at the one shared commit call site.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | item 1 is FALSE | `From-Spec` is listed as "absent from `ipd_schema.META_RECOGNIZED`". Measured `True`. A Set reading this could add a SECOND recognition path. | `META_FROM_SPEC in META_RECOGNIZED` -> True |
| F-2 | HIGH | item 4 is FALSE AND MORE STALE THAN THE ITEM RECORDS | The item calls it "MISLEADING" because `mjx7ne` was PENDING. `mjx7ne` has EXECUTED and the descriptor carries 13 fields including all three runner-safety ones the item said do not exist. Reading it as net-new invites creating a parallel module, the exact defect that killed `a54m79`. | `dataclasses.fields(HostSandboxCapabilities)` -> 13; `mjx7ne` in `executed/` |
| F-3 | MEDIUM | item 2 HOLDS, with a sharper truth available | Zero `AW-Run` trailers in the last 400 commits across all refs. The WRITER exists (`git_commit_helper`) and nothing passes it; plan `wao266` now owns the wiring. | trailer scan; `wao266`'s scope |
| F-4 | MEDIUM | item 3 HOLDS | Zero occurrences of "Run contract" in `oc_runipd.py` and `agy_runipd.py`. | grep both drivers |
| F-5 | MEDIUM | item 5 HOLDS | `aw hooks install` does not resolve. | verb attempted |
| F-6 | HIGH | the paragraph's function is anti-duplication | Its own preamble says the original text "would mislead a graduating Set into rebuilding shipped machinery", so a stale entry causes exactly the harm the paragraph exists to prevent. | spec `:22-24` |
| F-7 | MEDIUM | nothing enforces the maintenance | Two decays in nine days, and no test, check or gate reads this paragraph. That is why E-03 is a durability decision rather than another correction. | `a59f2c5` then this item |
| F-8 | MEDIUM | reviews re-measure anyway | The item's audit observes that letting plans measure current state "is what every recent plan review actually does", so the list's real function is to WARN rather than to inform. | the item's own audit conclusion |
| F-9 | LOW | the audit half is closed for its own question, but its conclusion is NARROWER than "only this spec" | Corpus is 29 spec files at HEAD (not 24 or 28); `aw check specs`'s 13 is the non-retired subset, a different question. `25kzda` 4 and `7ckptx` 4 on the item's phrase set, but `7ckptx`'s are prose about nonexistent paths, not existence claims about tooling. So the item's real conclusion survives, and its stated one does not. | `_iter_type_files("specs", include_retired=True)` -> 29; `aw check specs` -> 13; grep by file |
| F-10 | LOW | a cited sha must be verified | The item cites `8c437188` (merged `b0eb74e6`) for `From-Spec`. E-02 must confirm it resolves before writing it into an approved spec. VERIFIED in review: both resolve at HEAD. | `git log -1 8c437188` -> "feat(schema,check): recognize From-Spec and flag dangling spec links" |
| F-11 | HIGH | A NEIGHBORING PREAMBLE PARAGRAPH IN THE SAME FILE IS STALE THE SAME WAY, and the plan did not look at it | The Section 2.1 grammar paragraph asserts `run unverifiable`, `--allow-unverifiable` and `--unverifiable-ok` "all grep to zero". All three EXIST: both flags are registered argparse options on `start` and `resume` on BOTH hosts with `implemented=True`, and the phrase occurs 7 times. They landed in `08aab7ed` on 2026-09-05, the same day the paragraph was measured. A plan whose whole purpose is de-staling this preamble would have left a second false paragraph four lines away. | parser walk -> `['--allow-unverifiable','--no-allow-unverifiable','--no-unverifiable-ok','--unverifiable-ok']` on `oc start`, `oc resume`, `agy start`, `agy resume`; `runner_shared.py:1938-1960` `implemented=True`; `git log -1 08aab7ed` |
| F-12 | HIGH | THE SUITE BASELINE IS WRONG IN BOTH HALVES and misnames the failing test | Plan cites `1 failed, 5648 passed` blaming `tests/test_orchestrator_retirement.py`, which PASSES (`112 passed`). Real state: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by the gitignored `opencode-recovery/` tree of ANOTHER party's transcripts. An executor told to expect a different failure could mistake this for their own regression, or worse, "fix" a co-worker's files. | bare `python3 -m pytest` at `fc67605d`; `tests/test_orchestrator_retirement.py` -> `112 passed`; `.gitignore:49` |
| F-13 | MEDIUM | THREE BYTE-PINNED REGIONS WERE UNNAMED, not one | The plan names only Section 4.2. Also pinned by file-reading tests: Section 4.1's abort-class table (`test_run_evidence_completion.py:1058-1059`), Section 2.1's fenced grammar block (`test_run_flag_surface.py:115-120`), and Section 2.5a's fenced blocks asserted character for character (`test_run_selection_policy.py:806-817`). Naming one of four invites the inference that the others are free. VERIFIED SAFE: the preamble has no fenced block and no `RUN-` table row, so the declared edit cannot reach any of them. | the three test files; preamble scan -> no fence, no `RUN-` row; the three files -> `261 passed` |
| F-14 | MEDIUM | E-03's DECISION WOULD HAVE COVERED ONE PARAGRAPH OF FOUR | The preamble carries four point-in-time paragraphs of the same class, TWO of which are now measured stale (infrastructure, and the 2.1 grammar one). A durability convention written over one while three neighbors decay is a fourth thing to maintain, not a fix. | spec `:21-56`; F-1, F-2, F-11 |
| F-15 | LOW | A SECOND LIVE APPROVED SPEC now carries a stale existence claim, out of scope but must not be reported as absent | `kw5y2s:123` (`approved`) says "`aw check reviews` currently fails with `unknown artifact type 'reviews'`". At HEAD that verb SUCCEEDS: `152 reviews checked`, exit 0, and `reviews` is in `ARTIFACT_TYPES`. Fixing it is a different spec and out of this plan's declared scope; concealing it would repeat the item's own error. | `aw check reviews` -> exit 0, `152 reviews checked`; `'reviews' in artifact_types.ARTIFACT_TYPES` -> True |

## Proposed changes (ordered, validatable)

1. Re-measure all five entries at HEAD, with a non-vacuity control for every zero, and record any that moved again (E-01).
2. Amend only the wrong entries in the infrastructure paragraph, with verified citations, leaving true entries untouched (E-02).
3. Correct the neighboring Section 2.1 grammar paragraph's false "all grep to zero" clause, with parser-derived evidence (E-05).
4. Implement a durability decision governing all four point-in-time preamble paragraphs, so none can decay invisibly again (E-03).
5. Record the correction via `aw specs note`, prove status and design unchanged, keep every byte-pinned region untouched (E-04).

## Deferred / out of scope (with reason)

- RE-RUNNING THE FULL SPEC AUDIT. Closed by the item and re-confirmed in review at 29 spec files: no OTHER spec carries the false-premise pattern in the form that destroyed the `detrun` Set. Re-running it would be work whose answer is already recorded. The one exception found is recorded immediately below rather than silently absorbed.
- FIXING `kw5y2s`'s STALE CLAIM (F-15). `kw5y2s:123` (`approved`) asserts `aw check reviews` fails with `unknown artifact type 'reviews'`, and at HEAD that verb succeeds. That is a genuine instance of this plan's own defect class in a DIFFERENT approved spec, and it is deliberately NOT fixed here: the file is not in `Scope-Paths`, editing a second approved spec doubles the review surface, and the runners announce declared spec edits at run start, so an undeclared one is exactly the drift that declaration requirement exists to catch. Report it; do not fix it. A follow-up item is the maintainer's call (see OQ-04). CARRIER AT EXECUTION: re-verified at HEAD `007d05e1` (the claim is at `:124`, and `aw check reviews` exits 0 with `findings 0`) and filed as backlog `ddon4j` (`chore`), taking OQ-04's own recommendation, so the obligation does not vanish when this plan reaches `executed`.
- ADDING A TEST OR `aw check` RULE THAT VERIFIES THESE CLAIMS. The tempting "real" fix for a paragraph nothing enforces is to enforce it, and it is out of scope twice over: it is a CODE change in a plan whose `Scope-Paths` declares one spec file, and it is a design decision (what a spec is allowed to assert, and what a check may fail on) that belongs to a maintainer and its own plan. E-03 says so explicitly so an executor does not helpfully build one.
- BUILDING ANY OF THE FIVE ENUMERATED ITEMS. This plan corrects a STATUS description. The trailers are `wao266`'s (from `a8eufb`); `aw hooks install` and the prompt `Run contract` block have no owner yet and are NOT filed by this plan, because inventing scope for them from a spec paragraph is how the false-premise problem started.
- CHANGING ANY DESIGN TEXT IN `25kzda`. Factual-status only, on the `a59f2c5` precedent, which is also what keeps it `approved`.
- TOUCHING SECTION 4.2's FINDING-CODE TABLE. Byte-pinned into `run_evidence.RUN_FINDING_CODES`; an incidental edit is a code change.
- CHANGING THE SPEC'S STATUS. It stays `approved`. An agent may not set `approved` or `implemented` regardless.
- FILING ITEMS FOR THE STILL-UNBUILT ENTRIES. Tempting and out of scope: items 3 and 5 genuinely do not exist, but whether they are WANTED is a design question this plan has no mandate to answer, and a spec listing something is not by itself a decision to build it.
- AUDITING WHETHER OTHER SPECS ENUMERATE "not built yet" IN FUTURE. E-03's decision may imply a general convention, but generalizing it across 28 specs is a separate change with its own review surface.

## Scope check

- Over-scope: none. One spec file, two preamble paragraphs of the same class, one history note. E-05 widens the plan by one paragraph WITHIN the already-declared file and the already-declared preamble: it adds no path, no code, and no new review surface, and it was added because leaving a second false paragraph four lines from the corrected one would defeat the plan's own purpose.
- Scope-Paths justification: `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` is the ONLY file this plan edits. It is declared deliberately and prominently, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles them; a plan amending a spec it never declared is exactly the drift that declaration requirement exists to catch. NO code path is in scope: this plan changes a description of code, not code, and if the executor concludes a code change is needed, that is a scope-widening finding to report rather than to make.
- Under-scope, stated rather than left as `none`: this plan does not re-run the audit, does not build any enumerated item, changes no design text, does not touch any byte-pinned region, does not change the spec's status, files no items for the unbuilt entries, does not fix `kw5y2s`'s parallel stale claim (F-15, reported not fixed), and adds no test or check rule enforcing spec factual claims. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted, counts stated, AND the failing node ids listed for each. Baseline re-measured on main at `fc67605d`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`. That failure is PRE-EXISTING, is caused by the gitignored `opencode-recovery/` tree belonging to another party, and MUST NOT be fixed or cleaned up. Criterion: AFTER minus BEFORE is EMPTY compared BY NODE ID (not by count, which drifts as other agents land tests). A spec-text edit should move NOTHING, so any new node id means a byte-pinned region was touched.
- THE FIVE PER-ITEM MEASUREMENTS (E-01) pasted with the command used for each, plus the non-vacuity control for the trailer scan, and an explicit statement of any entry that moved since this plan was authored.
- THE PARSER-DERIVED FLAG REGISTRATION (E-05) for both hosts' `start` and `resume` subparsers, pasted rather than grepped.
- EVERY CITED SHA VERIFIED to resolve before it is written into the spec (`8c437188`, `b0eb74e6`, `08aab7ed`).
- A SCOPED DIFF of the spec showing ONLY the two preamble paragraphs and the workflow-history region changed.
- PROOF EVERY BYTE-PINNED REGION IS UNTOUCHED: Section 4.2's `RUN-*` table, Section 4.1's abort-class table, Section 2.1's fenced grammar block, Section 2.5a's fenced blocks. All THREE spec-reading test files pasted passing (`tests/test_run_evidence_completion.py`, `tests/test_run_flag_surface.py`, `tests/test_run_selection_policy.py`; `261 passed` at review HEAD).
- THE SPEC'S `- Status:` shown unchanged at `approved` before and after.
- `aw check specs` before and after, per-rule, showing no new finding.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean, and no em or en dash introduced into the spec.

## Spec / documentation sync

THIS PLAN IS ITSELF A SPEC AMENDMENT, which is why `25kzda` is declared in `Scope-Paths` and why that declaration is the plan's most important structural feature. The runners announce declared spec edits at run start and the finalize gate reconciles what was actually changed against what was declared.

WHY THE AMENDMENT IS LEGITIMATE WITHOUT A STATUS CHANGE: `a59f2c5` set the precedent that a factual-status correction to this paragraph is not a design change, and the spec stayed `approved` through it. This plan makes the same class of edit. The `2026-09-07 note (aw specs)` entry in the same spec shows the recording mechanism.

E-03's DECISION MUST BE RECORDED IN THE SPEC ITSELF, not only in this plan's history. If the enumeration survives as a dated snapshot, the spec must say so and must instruct a reader to re-verify; if it is deleted, the spec must retain a one-line instruction to measure current state. Either way the next reader must find the reasoning without reading this plan. The decision must be stated ONCE in a form that governs all four point-in-time preamble paragraphs, not attached to the infrastructure one alone.

TWO PARAGRAPHS OF THE ONE DECLARED SPEC ARE AMENDED, not one, and the second was found in review rather than by the item (F-11, E-05). Both live in the same preamble of the same file already named in `Scope-Paths`, so no declaration changes.

No OTHER spec is amended, and the reason is now narrower than the item's. The audit's conclusion survives for the defect class that destroyed the `detrun` Set, but it is NOT true that no other live spec carries a stale existence claim: `kw5y2s` (`approved`) does (F-15). That correction is owed and is deliberately NOT taken here, because amending an undeclared second approved spec is precisely the drift the `Scope-Paths` declaration requirement exists to catch. It is reported to the maintainer via OQ-04.

## Open questions

### OQ-01: Should the "not built yet" enumeration survive at all?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: GENUINELY THE MAINTAINER'S CALL, but deliberately NON-BLOCKING because the plan delivers value under every answer: E-01 and E-02 correct two false statements regardless, and only E-03's shape depends on this. The evidence is balanced and worth stating. FOR DELETION: the paragraph has decayed twice in nine days, nothing enforces it, and the item's own audit found that plan reviews re-measure current state anyway, so the list informs nobody who was going to check. FOR KEEPING IT AS A DATED SNAPSHOT: its preamble records that the ORIGINAL version's inaccuracy "would mislead a graduating Set into rebuilding shipped machinery", and the `a54m79` duplication it warns about actually happened, so the warning has demonstrated value even when its details rot. The judgement is how much a maintainer wants a hand-maintained fact list in an approved spec, which is a preference about their own review process. E-03 defaults to the dated snapshot as the option that preserves the warning at the lowest cost, and requires the reasoning to be written into the spec either way.

### OQ-02: Should the still-unbuilt entries get backlog items?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, NOT FROM THIS PLAN. Items 3 (`Run contract` block) and 5 (`aw hooks install`) genuinely do not exist, and filing work for them from a spec paragraph would repeat the exact error this plan is fixing: treating an enumeration as a mandate. A spec LISTING something is not a decision to build it, and neither entry has a recorded maintainer decision behind it. Item 2's trailers already have an owner (`wao266`, from `a8eufb`) and item 4 is shipped. So the correct output is an accurate description; whether the two genuine gaps are WANTED is a separate question for a human, and this plan says so rather than manufacturing scope.

### OQ-03: Does correcting an approved spec require re-approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, ON THE `a59f2c5` PRECEDENT, and the item states the rule plainly: "the spec is `approved`, so it stays approved: a factual-status note is not a design change". `a59f2c5` made exactly this class of edit to exactly this paragraph while the spec remained approved. The independent constraint reinforcing this: an agent may not set a spec `approved` at all (that requires an attested human act), so any reading that demanded re-approval would make the correction unperformable by the agent doing it, which cannot be right for a factual fix. The boundary E-02 must respect is that this licence covers FACTS only: the moment an edit changes what the spec REQUIRES, it is a design change and needs the maintainer.

### OQ-04: `kw5y2s` carries the same defect this plan is fixing. Should it get its own correction?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RAISED IN REVIEW, NOT ANSWERED, because it is a scope decision about a DIFFERENT approved spec and therefore the maintainer's. THE FACT: `kw5y2s:123` (`approved`) states "`aw check reviews` currently fails with `unknown artifact type 'reviews'`", presented as current behavior an implementing plan must change. At HEAD the verb SUCCEEDS (`152 reviews checked`, exit 0) and `reviews` is in `ARTIFACT_TYPES`, so a Set graduating from `kw5y2s` could set out to build a CLI type noun that already works, which is the same duplication risk `25kzda`'s paragraph exists to prevent. WHY THIS PLAN DOES NOT JUST FIX IT: `kw5y2s` is not in `Scope-Paths`, the runners announce declared spec edits before a run starts and the finalize gate reconciles them, so an undeclared second approved-spec edit is exactly the drift that machinery catches; and two approved specs in one correction doubles the review surface for a plan whose value is precision. THE OPTIONS ARE a follow-up backlog item, a widening of this plan's scope before approval, or a deliberate decision to leave it (defensible if `kw5y2s`'s implementing Set is imminent and will measure anyway). NON-BLOCKING because every deliverable of this plan is correct and complete without it. RECOMMENDATION: a backlog item, since the same audit-and-correct shape has now recurred twice and an item is the cheapest way to stop it being rediscovered a third time.
- RESOLVED AT EXECUTION (2026-09-20) BY TAKING THE RECOMMENDATION, which is the one option of the three that needed no maintainer ruling: filed backlog `ddon4j` (`chore`, `medium`). The other two options were the maintainer's to choose and are NOT taken, so nothing was decided on their behalf: this plan's scope was not widened (`kw5y2s` was not edited, and remains outside `Scope-Paths`), and the defect was not left unrecorded. THE FACT WAS RE-VERIFIED FIRST rather than trusted from review: at HEAD `007d05e1` the claim sits at `kw5y2s:124` and `aw check reviews` exits 0, reporting `outcome conforms, target reviews, findings 0`, with `'reviews' in artifact_types.ARTIFACT_TYPES` True. Filing it was also required to clear `aw ipd lint`'s `check.ipd-uncarried-obligation` advisory, which correctly warned that an obligation recorded only in a plan's Deferred section vanishes from `aw attention` the moment the plan classes `done`. The FIX ITSELF remains the maintainer's to schedule; `ddon4j` records the shape (a factual-status correction on the `a59f2c53` precedent, ideally adopting the snapshot convention this plan added to `25kzda`) and is filed `chore` rather than `bug` because no shipped behavior is broken, with that classification flagged in the item as disputable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL output for all five measurements with the command used for each: the `META_RECOGNIZED` membership test, the `AW-Run` trailer scan over the WHOLE history with its count and the total commit count it ran against, the `Run contract` grep over both drivers showing the per-file counts, the `HostSandboxCapabilities` field enumeration plus `mjx7ne`'s directory, and the `aw hooks install` attempt with its unpiped exit code. ALSO paste the NON-VACUITY control for the trailer scan (the same command with `Co-authored-by`, which must return nonzero), since three of the five verdicts rest on a zero and an unproven zero is indistinguishable from a broken command. State explicitly whether any entry moved since this plan was authored, and if so say so prominently as evidence for E-03.
  - Observed evidence: ALL FIVE RE-MEASURED at HEAD `007d05e1951aaa8f484824d5236800d7ed4496f0` BEFORE any edit; verdicts and commands below.
    All five re-measured at HEAD `007d05e1951aaa8f484824d5236800d7ed4496f0` BEFORE any edit. VERDICTS: item 1 STALE (as the plan predicted), item 2 HOLDS, item 3 HOLDS, item 4 STALE AND STRONGER (as the plan predicted), item 5 HOLDS. NO ENTRY MOVED since the plan was authored; all five verdicts match its authoring baseline, so there was no third decay in the enumeration itself. TWO NEIGHBORING PARAGRAPHS DID MOVE, which is reported under V-05 (Section 2.1, as the review predicted) and as DECISION 01-wenmg4-D3 (Section 4.2's finding-code paragraph, which the plan did NOT predict and which is the strongest fresh evidence for E-03's convention).

    ITEM 1, `From-Spec` -> STALE, the paragraph's claim "absent from `ipd_schema.META_RECOGNIZED`" is FALSE:
    ```
    $ python3 -c "
    from agent_workflows import ipd_schema
    print('META_FROM_SPEC =', repr(ipd_schema.META_FROM_SPEC))
    print('META_FROM_SPEC in META_RECOGNIZED ->', ipd_schema.META_FROM_SPEC in ipd_schema.META_RECOGNIZED)
    "
    META_FROM_SPEC = 'From-Spec'
    META_FROM_SPEC in META_RECOGNIZED -> True
    ```

    ITEM 2, the `AW-Run:`/`AW-Item:` trailers -> HOLDS. Scanned the WHOLE history across all refs, not a window, so "never used" is distinguished from "not used lately":
    ```
    $ git log --all --format='%(trailers:key=AW-Run,valueonly)' | grep -c .
    0
    $ git rev-list --all --count
    3764
    $ git log --all --format='%(trailers:key=AW-Item,valueonly)' | grep -c .
    0
    ```
    NON-VACUITY CONTROL, the identical command with a key that DOES exist, proving the scan reads trailers rather than silently returning nothing:
    ```
    $ git log --all --format='%(trailers:key=Co-authored-by,valueonly)' | grep -c .
    22
    ```
    So 0 of 3764 commits carry an `AW-Run` trailer while the control returns 22. Note the count differs from the plan's `0 of 2936` only because the history has grown; the verdict is unchanged. The WRITER exists, which is why the spec's wording was sharpened rather than left at "UNWIRED":
    ```
    $ python3 -c "from agent_workflows import git_commit_helper as g; print('has run_item_trailers ->', hasattr(g,'run_item_trailers'))"
    has run_item_trailers -> True
    ```
    And the owner of the wiring resolves: `.aw/records/plans/pending/20260908-runtrailwire-01-wao266-wire-the-run-ownership-trailers-the-runner-already-writes-no.ipd.md`, from backlog `.aw/records/backlog/graduated/20260830-scopeattrib-01-a8eufb-finalize-committed-half-ownership.backlog.md`.

    ITEM 3, the prompt `Run contract` block -> HOLDS. Per-file counts with the paths shown, so a reader can see both files were actually read:
    ```
    $ grep -c 'Run contract' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:0
    agent_workflows/agy_runipd.py:0
    ```
    NON-VACUITY CONTROL, the identical command with a string that DOES exist in both files:
    ```
    $ grep -c 'def main' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:1
    agent_workflows/agy_runipd.py:1
    ```

    ITEM 4, the per-host capability descriptor -> STALE AND STRONGER THAN THE ITEM RECORDED. The descriptor EXISTS with 13 fields including all three runner-safety ones the item said "genuinely does not exist":
    ```
    $ python3 -c "
    import dataclasses
    from agent_workflows.host_sandbox_profile import HostSandboxCapabilities
    f=[x.name for x in dataclasses.fields(HostSandboxCapabilities)]
    print('field count =', len(f))
    for n in f: print(' -', n)
    "
    field count = 13
     - supports_inline_permissions
     - supports_read_only_phase
     - supports_session_resume
     - emits_structured_tool_events
     - emits_child_permission_events
     - supports_process_tree_kill
     - supports_os_sandbox
     - supports_commit_gateway
     - supports_deny_push
     - supports_fresh_verifier_session
     - platform
     - sandbox_mechanism
     - probe_notes
    ```
    `mjx7ne` HAS EXECUTED, which is what makes the item's "MISLEADING rather than false" reading obsolete:
    ```
    $ find .aw/records/plans -name '*mjx7ne*' -print
    .aw/records/plans/executed/20260830-hostcap-01-mjx7ne-extend-the-shipped-sandbox-capability-contract-with-the-runn.ipd.md
    ```
    And the two declared-and-never-probed fields are documented as such in the owning module, which is why the amended entry names that explicitly:
    ```
    $ grep -n 'supports_commit_gateway\|supports_deny_push\|supports_fresh_verifier_session' agent_workflows/host_sandbox_profile.py
    107:  * `supports_fresh_verifier_session` - PROBED by attempt. The probe runs the real
    111:  * `supports_commit_gateway`, `supports_deny_push` - DECLARED AND NEVER PROBED, with the
    226:    supports_commit_gateway: bool = False
    227:    supports_deny_push: bool = False
    228:    supports_fresh_verifier_session: bool = False
    511:CAP_COMMIT_GATEWAY = "supports_commit_gateway"
    512:CAP_DENY_PUSH = "supports_deny_push"
    513:CAP_FRESH_VERIFIER_SESSION = "supports_fresh_verifier_session"
    ```

    ITEM 5, `aw hooks install` -> HOLDS. Exit code taken UNPIPED, and the failure text names the whole verb vocabulary, which is itself the proof that the noun is absent rather than the command being broken:
    ```
    $ aw hooks install >/dev/null 2>&1; echo "exit=$?"
    exit=2
    $ aw hooks install 2>&1 | head -3
    usage: agent-workflows [-h] [--no-color | --color] [--agent] [--json] [-V]
                           <command> ...
    agent-workflows: error: argument <command>: invalid choice: 'hooks' (choose from 'install', 'setup', 'uninstall', 'list-repos', 'status', 'normalize-lanes', 'doctor', 'exclude', 'include', 'ipd', 'work', 'test', 'commit', 'finish', 'workflow', 'run', 'runs', 'research', 'reviews', 'host', 'context', 'path', 'layout', 'project', 'storage', 'config', 'conf', 'show', 'record-history', 'check', 'find', 'search', 'index', 'rename', 'group', 'set', 'migrate-layout', 'next', 'attention', 'att', 'todo', 'oc', 'opencode', 'agy', 'antigravity', 'pwatch', 'backlog', 'releases', 'release', 'specs', 'spec', 'prompts', 'adopt', 'archive', 'check-local-leaks', 'sanitize', 'ipd-executed-gate', 'ipd-status-untooled-gate', 'backlog-blocking-close-gate', 'ipd-dependency-statement-gate', 'precommit-scope-gate', 'prepush-authorization-gate', 'completion', '__complete')
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the amended paragraph in full. Confirm by quoting that `From-Spec` now sits in the shipped list and that the capability-descriptor entry says the descriptor EXISTS, must be extended not created, names `host_sandbox_profile.py`, and states that two fields are declared-and-never-probed. Paste proof the cited sha RESOLVES (`git log -1 <sha>`). Paste a diff showing items that still hold were NOT reworded except where E-01 supported sharpening item 2.
  - Observed evidence: THE AMENDED INFRASTRUCTURE PARAGRAPH, its four required properties confirmed by quotation, and every cited sha resolved.
    THE AMENDED INFRASTRUCTURE PARAGRAPH IN FULL, as committed (spec `:44-64`):
    ```
    Infrastructure status (measured 2026-09-20 at `007d05e1`; corrected 2026-08-30 in `a59f2c53` and
    again 2026-09-20 by plan `wenmg4`, because this paragraph originally declared ALL of the below
    net-new and nonexistent, which would mislead a graduating Set into rebuilding shipped machinery).
    PARTS ALREADY SHIPPED, which a graduating Set must CONSUME, not rebuild:
    `Item-Dependencies` (the field, its grammar, and the shared graph predicate), the
    `aw ipd dependencies` surface, and `aw runs`. These were graduated FROM this spec by the `ipddeps`
    Set (`r7xku3`, `g69y23`, `ovbnyq`, `mp88bl`, all `executed`), whose plans cite this spec and its
    sections 2.7-2.11 by name. ALSO SHIPPED SINCE THE 2026-08-30 CORRECTION: `From-Spec` is RECOGNIZED
    (`ipd_schema.META_FROM_SPEC in META_RECOGNIZED` is True), landed with its dangling-link rule
    `check.from-spec-dangling` in `8c437188` (merged `b0eb74e6`, 2026-08-30); and the PER-HOST CAPABILITY
    DESCRIPTOR EXISTS and must be EXTENDED, NEVER CREATED - `host_sandbox_profile.HostSandboxCapabilities`
    carries 13 fields including the three runner-safety ones (`supports_commit_gateway`,
    `supports_deny_push`, `supports_fresh_verifier_session`) added by plan `mjx7ne` (`executed`), of which
    `supports_commit_gateway` and `supports_deny_push` are DECLARED AND NEVER PROBED by deliberate
    decision so they fail closed (`host_sandbox_profile.py:107-111`). Creating a parallel capability
    module because this paragraph once called the descriptor net-new is the exact defect that destroyed
    `a54m79`. STILL NET-NEW and to be built: the hash-chained run ledger's `AW-Run:`/`AW-Item:` commit
    trailers (the ledger AND the writer are built - `git_commit_helper.run_item_trailers` formats them -
    but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer; plan `wao266`
    from backlog `a8eufb` owns the wiring), the prompt `Run contract` block, and `aw hooks install` (no
    such verb today; the top-level `hooks` noun does not resolve). This overlaps the agentadhere
    policy-engine/atomic-command phases, the bklggrad `From-Backlog` work, and the runner rename.
    Constraints honored: pre-release (no backward-compatibility shims or legacy aliases) and
    design-against-roles (no dependence on current internal filenames).
    ```

    CONFIRMED BY QUOTATION, each of the four required properties:
    1. `From-Spec` NOW SITS IN THE SHIPPED LIST, under a heading that names it as shipped: "ALSO SHIPPED SINCE THE 2026-08-30 CORRECTION: `From-Spec` is RECOGNIZED (`ipd_schema.META_FROM_SPEC in META_RECOGNIZED` is True), landed with its dangling-link rule `check.from-spec-dangling` in `8c437188`". It no longer appears anywhere in the "STILL NET-NEW" sentence.
    2. THE DESCRIPTOR EXISTS AND MUST BE EXTENDED NOT CREATED: "the PER-HOST CAPABILITY DESCRIPTOR EXISTS and must be EXTENDED, NEVER CREATED".
    3. IT NAMES THE OWNING MODULE: "`host_sandbox_profile.HostSandboxCapabilities`" and the citation "(`host_sandbox_profile.py:107-111`)".
    4. IT STATES THE TWO DECLARED-AND-NEVER-PROBED FIELDS: "`supports_commit_gateway` and `supports_deny_push` are DECLARED AND NEVER PROBED by deliberate decision so they fail closed".

    EVERY CITED SHA RESOLVES, verified before being written into the approved spec:
    ```
    $ for s in 8c437188 b0eb74e6 08aab7ed a59f2c5; do git log -1 --format='%H %ad %s' --date=short $s; done
    8c4371888c0fd331fd7a40120417ef268484af83 2026-08-30 feat(schema,check): recognize From-Spec and flag dangling spec links
    b0eb74e657291c06755a64ae7b592d978e1564ad 2026-08-30 Merge lane aw/lane/bmh754_attempt2: recognize From-Spec and flag dangling spec links
    08aab7ed187c47804f0bd4a03af769acbb68a75f 2026-09-05 feat(runners): wire spec 2.1's run flag surface onto both hosts (uyeko5)
    a59f2c536e2338fed9902e5e3a431b535aba8a5d 2026-08-30 spec(25kzda): correct two factual defects (stays approved, no design change)
    ```

    ITEMS THAT STILL HOLD WERE NOT REWORDED, except the one sharpening E-02 explicitly authorized. Items 3 (`Run contract` block) and 5 (`aw hooks install`) retain their original wording verbatim, with only the parenthetical for item 5 extended to state HOW it was measured ("the top-level `hooks` noun does not resolve"). Item 2 is the authorized sharpening: E-02 says to sharpen it "ONLY IF E-01 SUPPORTS IT", and E-01 did (the writer exists, nothing passes the trailers, `wao266` owns the wiring), so "the ledger is built but UNWIRED" became "the ledger AND the writer are built ... but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer; plan `wao266` from backlog `a8eufb` owns the wiring". The overlap sentence and the "Constraints honored" sentence are byte-identical to HEAD.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the PARSER-DERIVED registration proof, not a grep: for each host, the `option_strings` of the `start` and `resume` subparsers showing `--allow-unverifiable` and `--unverifiable-ok` present (four rows total). Paste the amended clause in full and confirm by quoting that it no longer says those spellings grep to zero and that it cites `08aab7ed`. Paste proof that sha resolves. Confirm the clauses left standing were RE-MEASURED, with the output for each (`--json` absent from `start`/`resume`, `resume` still positional, `aw runs verify` and `aw oc prompt` exit codes taken unpiped). Paste a diff proving Section 2.1's own fenced grammar block is byte-identical, and paste `tests/test_run_flag_surface.py` passing.
  - Observed evidence: PARSER-DERIVED registration proof for both hosts' `start` and `resume`, the amended clause, and the re-measured surviving clauses.
    PARSER-DERIVED REGISTRATION PROOF, built by walking each host's real `start`/`resume` subparser `option_strings` rather than by grep, so a help-string hit cannot be mistaken for a registered flag. Four rows, as required:
    ```
    $ python3 - <<'PY'
    import argparse, importlib
    for mod, host in (("agent_workflows.oc_runipd","oc"), ("agent_workflows.agy_runipd","agy")):
        m = importlib.import_module(mod)
        p = m.build_parser()
        subs = [a for a in p._actions if isinstance(a, argparse._SubParsersAction)]
        for sa in subs:
            for name, sp in sa.choices.items():
                if name not in ("start","resume"): continue
                opts = sorted({o for a in sp._actions for o in a.option_strings})
                print(f"{host} {name}: unverifiable opts -> {[o for o in opts if 'unverifiable' in o]}")
                print(f"{host} {name}: --json present -> {'--json' in opts}")
    PY
    oc start: unverifiable opts -> ['--allow-unverifiable', '--no-allow-unverifiable', '--no-unverifiable-ok', '--unverifiable-ok']
    oc start: --json present -> False
    oc resume: unverifiable opts -> ['--allow-unverifiable', '--no-allow-unverifiable', '--no-unverifiable-ok', '--unverifiable-ok']
    oc resume: --json present -> False
    agy start: unverifiable opts -> ['--allow-unverifiable', '--no-allow-unverifiable', '--no-unverifiable-ok', '--unverifiable-ok']
    agy start: --json present -> False
    agy resume: unverifiable opts -> ['--allow-unverifiable', '--no-allow-unverifiable', '--no-unverifiable-ok', '--unverifiable-ok']
    agy resume: --json present -> False
    ```
    Both flags are declared `implemented=True` in `runner_shared.RunPolicyFlag` (`:6335-6357`), which is what makes them real rather than declared-and-unbuilt:
    ```
    $ grep -n 'allow-unverifiable\|unverifiable-ok' agent_workflows/runner_shared.py | head -6
    6336:        flag="--allow-unverifiable",
    6337:        dest="allow_unverifiable",
    6343:            "verification stays 'unavailable'. This is the ADMISSION --unverifiable-ok requires; it "
    6348:        flag="--unverifiable-ok",
    6349:        dest="unverifiable_ok",
    6355:            "code, without relabeling it verified. LEGAL ONLY with --allow-unverifiable (or the "
    ```
    And the interactive phrase exists in three SOURCE modules (`.pyc` matches excluded deliberately):
    ```
    $ grep -rn --include='*.py' 'run unverifiable' agent_workflows/ | cut -d: -f1 | sort | uniq -c
          4 agent_workflows/run_evidence.py
          2 agent_workflows/runner_shared.py
          1 agent_workflows/run_selection_policy.py
    ```

    THE AMENDED CLAUSE IN FULL, as committed (spec `:84-103`):
    ```
    LIKEWISE, SEVERAL COMMANDS IN SECTION 2.1's GRAMMAR DO NOT EXIST as written (re-measured 2026-09-20
    at `007d05e1`; first measured 2026-09-05): `--json` is registered on neither runner's `start` or
    `resume` (it IS on `status`); `--resume <run-id>` ships as the POSITIONAL subcommand
    `run resume <run-id>`, not a flag; the spelling `aw runs verify <run-id>` names no leaf at all (the
    real leaf is `verify-ledger`; AMENDED 2026-09-08 by plan `7wei1o`: that spelling now REFUSES with exit
    2 and a message naming the unresolved token and suggesting `verify-ledger`. It previously absorbed a
    first token matching no leaf as a TARGET and, when that target resolved to nothing, dropped it and
    EXITED 0 having verified nothing - backlog `6kq1lj`); and `aw <host> prompt`
    does not exist (the nearest shipped surface is
    `aw agy exec --prompt/--file`); both spellings exit 2. CORRECTED 2026-09-20 by plan `wenmg4`: this
    paragraph previously claimed the interactive phrase `run unverifiable`, `--allow-unverifiable` and
    `--unverifiable-ok` "all grep to zero", and ALL THREE NOW EXIST. `--allow-unverifiable` and
    `--unverifiable-ok` are REGISTERED argparse options on the `start` AND `resume` subcommands of BOTH
    hosts, declared `implemented=True` in `runner_shared.RunPolicyFlag` and owned by
    `run_evidence.aggregate_run_exit`; the phrase `run unverifiable` occurs in three source modules. They
    landed in `08aab7ed` (2026-09-05, "wire spec 2.1's run flag surface onto both hosts"), the SAME DAY
    this paragraph was measured, which is exactly how a point-in-time snapshot decays. Six shipped
    operator-facing recovery strings in `run_evidence.py` already transcribe the non-existent `--resume`
    spelling verbatim; do not add more. Correct the grammar or the code deliberately, but do not treat
    the spellings still listed above as available.
    ```
    CONFIRMED BY QUOTATION: the paragraph NO LONGER says those spellings grep to zero. The phrase "all grep to zero" now survives only inside an explicit past-tense retraction that attributes the old claim and contradicts it - "this paragraph previously claimed the interactive phrase `run unverifiable`, `--allow-unverifiable` and `--unverifiable-ok` \"all grep to zero\", and ALL THREE NOW EXIST" - and it CITES `08aab7ed`: "They landed in `08aab7ed` (2026-09-05, \"wire spec 2.1's run flag surface onto both hosts\")". The closing instruction was narrowed from "do not treat these spellings as available" to "do not treat the spellings still listed above as available", so it no longer sweeps in the three that now exist. That sha resolves (pasted under V-02).

    THE CLAUSES LEFT STANDING WERE ALL RE-MEASURED, not assumed. `--json` is absent from `start` and `resume` on both hosts and IS on `status` (which is why the clause was sharpened rather than deleted), and `resume` is still a POSITIONAL subcommand rather than a flag:
    ```
    $ python3 - <<'PY'
    ... (walks each host's subparsers)
    PY
    oc: subcommands -> ['audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    oc: 'resume' is a positional subcommand -> True
      oc start: '--resume' registered -> False; '--json' registered -> False
      oc resume: '--resume' registered -> False; '--json' registered -> False
      oc status: '--resume' registered -> False; '--json' registered -> True
    agy: subcommands -> ['audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    agy: 'resume' is a positional subcommand -> True
      agy start: '--resume' registered -> False; '--json' registered -> False
      agy resume: '--resume' registered -> False; '--json' registered -> False
      agy status: '--resume' registered -> False; '--json' registered -> True
    ```
    Exit codes taken UNPIPED, as the plan requires:
    ```
    $ aw runs verify >/dev/null 2>&1; echo "exit=$?"
    exit=2
    $ aw oc prompt >/dev/null 2>&1; echo "exit=$?"
    exit=2
    $ aw agy prompt >/dev/null 2>&1; echo "exit=$?"
    exit=2
    ```

    SECTION 2.1's OWN FENCED GRAMMAR BLOCK IS BYTE-IDENTICAL, proven by sha256 over everything from `## 1. Executive summary` through the history section (which contains Section 2.1 in its entirety), not merely by eye:
    ```
    $ python3 - <<'PY'
    ... compares HEAD:<spec> against the working copy for the region '## 1. Executive summary' .. '## Workflow history'
    PY
    DESIGN BODY (## 1. .. ## Workflow history) byte-identical -> True
      sha old: a1464ac171038ff5331a83342320fa490270f4051765edfac27d3adaa750eda7
      sha new: a1464ac171038ff5331a83342320fa490270f4051765edfac27d3adaa750eda7
    ```
    The edit stayed entirely in the PREAMBLE (all diff hunks fall in lines 21-103, above `## 1.` which now begins at line 107), so the parser in `tests/test_run_flag_surface.py:115-120` cannot see it. That test file passes:
    ```
    $ python3 -m pytest tests/test_run_evidence_completion.py tests/test_run_flag_surface.py tests/test_run_selection_policy.py
    ........................................................................ [ 83%]
    ..........................................                               [100%]
    259 passed in 8.66s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: state which of the three options was implemented and paste the spec text implementing it. If the snapshot survives, quote the date, the commit and the re-verify instruction. If the enumeration was deleted, quote the replacement instruction to measure current state, and confirm in one sentence that the anti-duplication warning was preserved rather than dropped. Confirm the reasoning is recorded IN THE SPEC, not only in this plan. ALSO demonstrate the convention GOVERNS ALL FOUR point-in-time preamble paragraphs by quoting the governing sentence and showing each paragraph carries its own date under it, and confirm no test or check rule was added.
  - Observed evidence: OPTION (c) IMPLEMENTED, the point-in-time snapshot, with the convention stated once so it governs every dated preamble paragraph.
    OPTION IMPLEMENTED: (c), THE EXPLICIT POINT-IN-TIME SNAPSHOT, which E-03 names as the defensible default. Recorded as DECISION 01-wenmg4-D2 with the evidence for rejecting (a) and (b). The enumeration SURVIVES, so the anti-duplication warning is preserved rather than dropped; this run's own measurements are the strongest evidence for keeping it, since two entries would have sent a graduating Set to duplicate shipped machinery.

    THE SPEC TEXT IMPLEMENTING IT, placed at the HEAD of the preamble so it governs every dated paragraph rather than being attached to one (spec `:21-39`):
    ```
    EVERY DATED PARAGRAPH BELOW IS A POINT-IN-TIME SNAPSHOT, NOT A STANDING CLAIM, AND YOU MUST
    RE-MEASURE BEFORE RELYING ON ANY OF IT. This convention governs the whole preamble: the three
    paragraphs that follow (infrastructure status, Section 4.2's finding codes, and Section 2.1's command
    grammar) each describe WHAT WAS SHIPPED ON THE DATE IT CARRIES, and each is stale from the moment the
    next commit lands. Each therefore states its own measurement date and, where one exists, the commit
    that moved it. A SET GRADUATING FROM THIS SPEC MUST MEASURE CURRENT STATE ITSELF and must not treat
    any entry here as current; the entry tells you WHERE TO LOOK and WHAT THE ANSWER WAS, never what the
    answer is. The convention is stated once, here, because it governs all three equally and a rule
    attached to one paragraph while its neighbors decay is a fourth thing to maintain rather than a fix.
    WHY THE SNAPSHOTS SURVIVE AT ALL, rather than being deleted in favor of "measure it yourself": their
    function is to WARN, not to inform. This preamble's infrastructure paragraph was itself written as a
    correction because the original text declared everything net-new and "would mislead a graduating Set
    into rebuilding shipped machinery", and that duplication really happened once (`a54m79`). A reader who
    re-measures loses nothing by their presence; a reader who would have rebuilt shipped machinery is
    stopped by it. NOTHING ENFORCES THIS, which is the honest limit: no test and no `aw check` rule reads
    these paragraphs, so their accuracy rests on whoever next touches them. The re-verify instruction is
    the defeat mechanism for their staleness, deliberately in place of a gate. ALL THREE HAVE NOW BEEN
    MEASURED STALE AT LEAST ONCE, which is the evidence for the convention rather than an argument against
    it: the infrastructure paragraph has been corrected twice (2026-08-30, then 2026-09-20), and the
    Section 2.1 and Section 4.2 paragraphs once each (both 2026-09-20, both found to be false by the same
    re-measurement). So treat a date more than a few days old as probably wrong.
    ```

    THE RE-VERIFY INSTRUCTION, quoted: "EVERY DATED PARAGRAPH BELOW IS A POINT-IN-TIME SNAPSHOT, NOT A STANDING CLAIM, AND YOU MUST RE-MEASURE BEFORE RELYING ON ANY OF IT", reinforced by "A SET GRADUATING FROM THIS SPEC MUST MEASURE CURRENT STATE ITSELF and must not treat any entry here as current; the entry tells you WHERE TO LOOK and WHAT THE ANSWER WAS, never what the answer is". So the paragraph's own instruction defeats its staleness, which is what E-03 asks of option (c).

    THE REASONING IS RECORDED IN THE SPEC, NOT ONLY IN THIS PLAN, so the next reader does not re-litigate it: the passage beginning "WHY THE SNAPSHOTS SURVIVE AT ALL, rather than being deleted in favor of \"measure it yourself\"" states the warn-not-inform rationale and cites `a54m79` as the duplication that actually happened, and the passage beginning "NOTHING ENFORCES THIS, which is the honest limit" records that no test or `aw check` rule reads these paragraphs and that the reader instruction is deliberately in place of a gate.

    THE CONVENTION GOVERNS EVERY POINT-IN-TIME PARAGRAPH, and each carries its own date under it. NOTE A DISCREPANCY IN THIS PLAN, recorded rather than papered over: the plan says FOUR such paragraphs but names only THREE, and measurement finds exactly THREE. The preamble was parsed programmatically rather than eyeballed:
    ```
    $ python3 - <<'PY'   # paragraph-split everything above '## 1. Executive summary'
    --- preamble paragraph 1: lines 1-1 ---      # H1 title
    --- preamble paragraph 2: lines 3-14 ---     # metadata bullets
    --- preamble paragraph 3: lines 16-19 ---    # 'load-bearing design' provenance, undated
    --- preamble paragraph 4: lines 21-33 ---    Infrastructure status (corrected 2026-08-30 ...
    --- preamble paragraph 5: lines 35-43 ---    READ SECTION 4.2's FINDING CODES ... (measured 2026-09-05)
    --- preamble paragraph 6: lines 45-56 ---    LIKEWISE, SEVERAL COMMANDS IN SECTION 2.1's ... (measured 2026-09-05)
    --- preamble paragraph 7: lines 58-58 ---    # the '---' rule
    PY
    $ # date markers in the preamble, confirming there is no fourth dated paragraph:
      line 21: Infrastructure status (corrected 2026-08-30; ...
      line 35: READ SECTION 4.2's FINDING CODES AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR (measured 2026-09-05).
      line 45: LIKEWISE, SEVERAL COMMANDS IN SECTION 2.1's GRAMMAR DO NOT EXIST as written (measured 2026-09-05):
      line 48: real leaf is `verify-ledger`; AMENDED 2026-09-08 by plan `7wei1o`: ...   # INSIDE paragraph 6, not a 4th paragraph
    ```
    The fourth date marker is the `AMENDED 2026-09-08 by plan 7wei1o` clause INSIDE the Section 2.1 paragraph, not a separate paragraph, which is the likeliest origin of the plan's miscount. The governing sentence names all three explicitly ("the three paragraphs that follow (infrastructure status, Section 4.2's finding codes, and Section 2.1's command grammar)"), so its scope is checkable rather than implied, and each now opens with its own date:
    ```
    $ grep -n 'measured 2026\|corrected 2026' <spec> | head -4
    22:RE-MEASURE BEFORE RELYING ON ANY OF IT. This convention governs the whole preamble: ...
    44:Infrastructure status (measured 2026-09-20 at `007d05e1`; corrected 2026-08-30 in `a59f2c53` and
    66:READ SECTION 4.2's FINDING CODES AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR (re-measured 2026-09-20 at
    84:LIKEWISE, SEVERAL COMMANDS IN SECTION 2.1's GRAMMAR DO NOT EXIST as written (re-measured 2026-09-20
    ```
    All three cite the measurement commit `007d05e1`, and the two that previously carried only `measured 2026-09-05` now carry both that first date and the re-measurement, so the decay is readable rather than overwritten.

    NO TEST OR CHECK RULE WAS ADDED, which E-03 and the Deferred section both forbid. Proven two ways: the spec commits touch exactly one file each (`1 file changed` in both `1872e412` and `42236304`, the file being the spec), and the bare-suite failure-set delta is empty by node id with no new tests collected beyond ordinary drift (V-04). The spec states the prohibition's rationale itself ("NOTHING ENFORCES THIS, which is the honest limit"), so a later reader knows the absence of a gate is deliberate rather than an oversight.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `aw specs note` command and its output. Paste the spec's `- Status:` line before and after, both `approved`. Paste a scoped `git diff` of the spec proving only the two preamble paragraphs and the history region changed, and confirm every byte-pinned region is byte-identical: Section 4.2's `RUN-*` table, Section 4.1's abort-class table, Section 2.1's fenced grammar block, and Section 2.5a's fenced blocks. Paste all THREE spec-reading test files passing (`tests/test_run_evidence_completion.py`, `tests/test_run_flag_surface.py`, `tests/test_run_selection_policy.py`), not only the `RUN_FINDING_CODES` case. Paste `aw check specs` before and after with its per-rule counts. THEN paste the BARE `python3 -m pytest` summary lines before and after AND the failing node ids from each, and state the failure-set delta BY NODE ID; a new node id on a spec-text edit means a pinned region was touched. Confirm the pre-existing `test_reporting_contract` failure is present in both runs and was not "fixed".
  - Observed evidence: RECORDED VIA `aw specs note`; status unchanged at `approved`, every byte-pinned region byte-identical, bare-suite delta empty by node id.
    THE TOOLED VERB WAS USED, not a hand-appended history line:
    ```
    $ aw specs note .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md --message "Factual-status correction of all three point-in-time preamble paragraphs by plan `wenmg4` ..."
    aw specs note: appended a history record to .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
    ```
    IT REPORTED SUCCESS AND SILENTLY DESTROYED ALL FOUR PRE-EXISTING HISTORY RECORDS. This is a real defect in `aw specs note`, not a mistake in this execution, and it is filed as backlog `l23v3j` (`bug`, `Blocks-Release: next`) and recorded as DECISION 01-wenmg4-D4. Measured:
    ```
    $ git show HEAD:<spec> | sed -n '/^## Workflow history/,$p' | grep -c '^- 20'
    4
    $ sed -n '/^## Workflow history/,$p' <spec> | grep -c '^- 20'
    1
    ```
    Reproduced minimally in a throwaway fixture (since removed), so the cause is not specific to this spec: a spec with three inline records retained ZERO after one `aw specs note` call. Cause at `specs.py:342-359` (`_append_history`), which REPLACES the section body (`new_section = ["", record]`) rather than appending, deliberately, deferring the full log to `.aw/records/history.jsonl`. That premise is false here: the sidecar is UNTRACKED (`git cat-file -e HEAD:.aw/records/history.jsonl` -> "exists on disk, but not in 'HEAD'") and contained exactly ONE record afterwards, mine, never the four. `aw specs set` shares the same helper and truncates identically (3 in, 0 preserved). ALL FOUR RECORDS WERE RESTORED VERBATIM from the starting HEAD and verified programmatically, so nothing was lost in the committed result:
    ```
    $ python3 - <<'PY'   # compares the working copy against 007d05e1
    pre-existing history records preserved verbatim -> True (before=4, after=5)
    new record added: - 2026-09-20 note (aw specs): Factual-status correction of all three point-in-time preambl
    PY
    ```

    `- Status:` IS UNCHANGED AT `approved`, before and after, as required (an agent may not set a spec `approved` in any case):
    ```
    Status before: ['- Status: approved']
    Status after:  ['- Status: approved']
    ```

    THE SCOPED DIFF SHOWS ONLY THE PREAMBLE AND THE HISTORY REGION CHANGED. Every hunk falls in the preamble (lines 21-103, where `## 1. Executive summary` now begins at line 107) except the final one, which is a pure single-line addition in the history section:
    ```
    $ git diff -U0 -- <spec> | grep '^@@'
    @@ -21,3 +21,24 @@ IPD Set (or Sets) can be graduated from and reviewed against.
    @@ -27,4 +48,14 @@ Set (`r7xku3`, `g69y23`, `ovbnyq`, `mp88bl`, all `executed`), whose plans cite t
    @@ -35,8 +66,16 @@ design-against-roles (no dependence on current internal filenames).
    @@ -45,2 +84,3 @@ shipped enforcer by symbol (for the IPD execution checks that is `ipd_lint` phas
    @@ -51 +91 @@ first token matching no leaf as a TARGET and, when that target resolved to nothi
    @@ -53,4 +93,11 @@ does not exist (the nearest shipped surface is
    @@ -1341,0 +1389 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen
    $ git diff --stat 007d05e1..HEAD
     ...3j-specs-note-destroys-prior-history.backlog.md | 26 ++++++
     ...-01-aw-run-deterministic-run-and-verify.spec.md | 94 +++++++++++++++++-----
     2 files changed, 98 insertions(+), 22 deletions(-)
    ```
    Note this plan amends THREE preamble paragraphs plus the new governing paragraph, not two: Section 4.2's finding-code paragraph was also measured false and is corrected under DECISION 01-wenmg4-D3.

    EVERY BYTE-PINNED REGION IS BYTE-IDENTICAL, proven by sha256 over the whole region that contains all four of them rather than by inspecting each separately. All four pinned regions (Section 4.2's `RUN-*` table, Section 4.1's `#### Exhaustive ABORT RUN set` table, Section 2.1's fenced grammar block, Section 2.5a's fenced blocks) live between `## 1. Executive summary` and `## Workflow history`, and that entire span is unchanged versus the starting HEAD:
    ```
    $ python3 - <<'PY'   # region '## 1. Executive summary' .. '## Workflow history', vs 007d05e1
    vs STARTING HEAD, design body byte-identical -> True
      sha: a1464ac171038ff5331a83342320fa490270f4051765edfac27d3adaa750eda7 == a1464ac171038ff5331a83342320fa490270f4051765edfac27d3adaa750eda7
    PY
    ```
    Independently, the preamble that WAS edited contains no fenced block and no table row at all, so none of the three parsers can see the edit:
    ```
    $ python3 - <<'PY'
    '## 1. Executive summary' now at line 107
    fenced blocks in preamble: 0
    table rows in preamble: 0
    PY
    ```
    ALL THREE SPEC-READING TEST FILES PASS:
    ```
    $ python3 -m pytest tests/test_run_evidence_completion.py tests/test_run_flag_surface.py tests/test_run_selection_policy.py
    ........................................................................ [ 83%]
    ..........................................                               [100%]
    259 passed in 8.66s
    ```

    `aw check specs` BEFORE and AFTER, identical, with no new finding:
    ```
    BEFORE (with the edit stashed, isolating the pre-existing state):
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}
    AFTER:
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}
    ```
    Same outcome (`conforms`), same exit 0, same single finding, same rule. The one finding is `check.collisions-not-checked`, an artifact of running a per-type check rather than a repo-wide one; it was proven pre-existing by re-running with my edit stashed, and it is not mine.

    BARE `python3 -m pytest` BEFORE AND AFTER, with the failing node ids from each and the delta by node id.
    ```
    BEFORE (at 007d05e1, before any edit):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7597 passed, 3 skipped, 2 xfailed, 3 warnings in 130.77s (0:02:10)

    AFTER (at 638a8b82, both spec edits and the backlog item committed):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7597 passed, 3 skipped, 2 xfailed, 3 warnings in 99.32s (0:01:39)

    $ comm -13 <(sorted BEFORE FAILED lines) <(sorted AFTER FAILED lines)
    (empty)
    ```
    FAILURE-SET DELTA BY NODE ID IS EMPTY: the same single node fails before and after, and no new node id appeared, which is the criterion for a spec-text edit having touched no pinned region. Counts are identical too (7597 passed both runs).

    THE PLAN'S PREDICTED BASELINE FAILURE DOES NOT OCCUR IN THIS LANE, and the real one is different. Recorded as DECISION 01-wenmg4-D5 rather than silently substituted. The plan expects `1 failed, 5958 passed` failing at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by a gitignored `opencode-recovery/` tree. In this worktree that tree DOES NOT EXIST (`ls -d opencode-recovery` -> "No such file or directory") and that test file PASSES:
    ```
    $ python3 -m pytest tests/test_reporting_contract.py
    45 passed in 10.76s
    ```
    So the `test_reporting_contract` failure is NOT present in either run, and there was nothing to "fix" or refrain from fixing; the plan's instruction not to touch another party's `opencode-recovery/` tree was moot here and no such tree was touched. The actual failure is environmental and is NOT caused by this plan: the test asserts a non-isolated turn receives no permission-denial policy, and it fails because `OPENCODE_CONFIG_CONTENT` is present in this lane's ambient environment (this turn is itself a contained worker). Proven by running the identical node with that variable unset:
    ```
    $ python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 passed
    ```
    It is pre-existing with respect to this plan (it fails at the untouched starting HEAD), it is not mine to fix, and it was not fixed or masked; the suite was run BARE in both directions as the contract requires. Reported as a finding in the outcome JSON.

    ALSO CLEAN: `aw sanitize --agent` reports zero findings and exit 0, and the spec contains no em or en dash (`grep -c '—\|–'` -> 0).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO `Blocks-Release` because the backlog item carries none: it is `Work-Kind: chore` and the maintainer did not gate it. That is recorded explicitly so a reader does not assume the gate was dropped. The defect's harm is real (a Set could duplicate shipped machinery) but it is a documentation-accuracy problem, not shipped-behavior breakage.

OQ-01 IS OPEN BUT NON-BLOCKING BY DESIGN. E-01 and E-02 correct two false statements under any answer; only E-03's shape depends on the maintainer, and it defaults to the lowest-cost option that preserves the warning.

EXECUTION CONTRACT. Commit only the spec file, path-scoped (`git commit -m msg -- <path>`); never `git add -A` and never push. Use `aw specs note` rather than hand-appending history. Do NOT change the spec's `- Status:`, and do NOT touch Section 4.2's finding-code table, which is byte-pinned into `run_evidence.RUN_FINDING_CODES`. Verify every sha before citing it in an approved spec. Re-locate every symbol by NAME rather than by the line numbers cited here. Write no em or en dashes into the spec. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the five per-item measurements and the scoped diff proving no design text moved.
