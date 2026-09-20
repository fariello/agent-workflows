# IPD: Report every record whose declared Id or Set is absent from its filename

- Date: 2026-09-08
- Kind: child
- Concern: THERE IS NO SIGNAL FOR A RECORD WHOSE DECLARED IDENTITY IS ABSENT FROM ITS FILENAME, so the exception set that forces `aw find`'s content fallback is invisible and cannot be shown to be shrinking. MEASURED at HEAD: TEN tracked records carry a declared `- Id:` that does not appear in their own filename (the authoring count of NINE was re-measured at review and is low by one), and `aw check specs` reports ZERO naming findings for the grandfathered ones (`13 specs checked`, `errors 0 warnings 0`). Verified the tolerance directly: `artifact_naming.is_clustered_conformant` returns `False` for both `20260808-0004-00-plans-adopter-orchestrator.ipd.md` and `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, yet neither is reported, because the check engine's naming rule deliberately exempts legacy shapes. So the exception set exists, is load-bearing for `find`'s design, and nothing counts it.
  THE ADJACENT RULE THAT ALREADY EXISTS MUST BE CONSUMED, NOT DUPLICATED, and the plan did not know about it (found at the first review, F-12). `check.id6-identity-slot` is REGISTERED (`check_engine.py:101`, severity `error`, assurance `repository`, deterministic, invariant `I-09`, all re-verified) and implemented inside `check_collisions` (`_check_identity_slots`), and it ALREADY enforces the exact rule E-01/E-02 propose for the modern case: "(a) if the file DECLARES a frontmatter `- Id:`, its slot id6 MUST EQUAL that declared `- Id:`". It even already solves the discriminator problem this plan would otherwise have to solve from scratch, via the shared helper `_is_real_id6(token, declared_ids)`, which tells a real id6 from a slug word. Its coverage of the ten is ZERO, because it exempts a filename with no id6 slot - precisely the legacy population this plan is about. So the GAP IS REAL AND NARROW: it is case (a) extended to names that have no slot at all. The plan must therefore EXTEND or SIT BESIDE that rule and reuse its discriminator, not write a second identity comparator, or the repo gets two rules that can disagree about what an id6 is.
  ITS LIVE FINDING COUNT IS NOW ZERO, NOT TWO, AND THE EXECUTOR MUST NOT TREAT `2` AS THE BASELINE (F-15, re-measured 2026-09-10). `aw check all --agent` reports 169 findings with `check.id6-identity-slot` ABSENT from the diagnostics entirely; the two findings the first review recorded have since been resolved. This matters because E-05 and V-04 tell the executor to prove that count "MUST NOT CHANGE": measured against a stale 2, an unchanged real count of 0 would look like a regression. Re-measure it yourself and state the number you observed.
  THE DISCRIMINATOR REUSE IS NOT MERELY TIDY, IT IS VERIFIED TO SOLVE F-13. Run at review: `_is_real_id6('assess', declared_ids)` returns `False` (all-letters and undeclared) while `_is_real_id6('826o13', ...)` returns `True`. So reusing the existing helper genuinely fixes the mis-bucketing hazard F-13 describes, rather than merely avoiding duplication. Its docstring records the same oracle.
  WHY THAT MATTERS RATHER THAN BEING TIDINESS, and it is the item's own argument: "the long-term prize is being able to TRUST filenames and retire the content fallback, which is only reachable if the exception set is visible and shrinking." Order 01 (`826o13`) must keep a mandatory content fallback precisely BECAUSE these nine exist. Without a report, nobody can tell whether the set is nine or ninety, or whether it grew last week, so the fallback can never be retired on evidence.
  THE TEN ARE NOT ALL THE SAME THING, which is the finding that shapes this plan and which the item did not have. EIGHT are genuine pre-id6-grammar or grandfathered names: plans `4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys` and specs `4w7d6s`, `25kzda`, `5tapom`. TWO are the SAME parser artifact `uyeko5`, quoted in TWO different research documents (`27rjro`'s prompt AND `takpys`'s report), which is the correction to the authoring count: the plan said nine and named one artifact instance, but the second document quotes the identical example block, so a report built today shows 10 and should show 8. Both are QUOTED EXAMPLES in a body, not real declarations; the pair is the parser artifact owned by `cqytxf`/`76w6mq`. A report that conflates them would send someone to rename TWO research documents whose names are already correct, so the bucket is not a singleton special case and must not be coded as one.
  THE ITEM IS EXPLICIT THAT THIS IS ADVISORY AND NOT AUTO-RENAME, and both reasons are real constraints rather than caution: `executed/` plan bodies are immutable by policy, and the grandfathered specs are a documented decision. `25kzda` in particular is cited constantly across the repository, so renaming it would break every citation for a cosmetic gain. Hence "EXPLICITLY NOT auto-rename: each rename is a maintainer call per record."
  THE ITEM ALSO NAMES A MEASURED FALSE-POSITIVE SOURCE that this report must handle or it will lie on its first run: quoting. One apparent miss in the item's own audit was a phantom, because front matter read `` set: `awoptimize` `` WITH BACKTICKS. CONFIRMED STILL LIVE AT REVIEW, so this is not a historical anecdote: exactly one tracked record carries a quote-wrapped `Set:` value, `20260821-awoptimize-03-effzzi-...` with the literal `` `awoptimize` ``. Compare stripped values or the report invents drift on that record.
  THE `- Set:` CASE IS NOW MEASURED (the plan left it unknown as F-8) AND IT ADDS A FOURTH BUCKET THE PLAN DOES NOT MODEL. Records declare a `Set:` absent from their filename, and they are NOT all legacy: two are the `uyeko5` artifact pair (declaring `set: runflags` from the same quoted block), several are legacy names, one is `awphysical` on a legacy-named plan, and ONE IS A DOCUMENTATION PLACEHOLDER - `20260813-1833-01-attention-visible-backlog-tier.spec.md` declares the literal `set: <terse-id>` because that string sits inside an illustrative code block showing the backlog schema. A report that treats a placeholder as drift would tell a maintainer to rename a spec to match `<terse-id>`, which is nonsense. So the bucket taxonomy must accommodate NON-IDENTIFIER values, not just legacy-versus-artifact.
  THE `- Set:` COUNT IS EIGHT, NOT SEVEN, AND THE EIGHTH IS A FIFTH MEMBER OF THE ARTIFACT CLASS (F-16, measured 2026-09-10). Re-scanned: `<terse-id>`, `` `awoptimize` ``, `aw-delivery`, `awphysical`, `plans-adopter` (twice), and `runflags` (twice). The new one is `aw-delivery`, declared by `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md` at line 198 INSIDE a fenced ``` block captioned "Frontmatter schema (authored/tool-written)", i.e. a QUOTED EXAMPLE exactly like `uyeko5` and `runflags`. That is load-bearing for the bucket design: the parser-artifact class is NOT confined to research documents and NOT confined to `- Id:`; it reaches a SPEC via a `set:` line, so a classifier keyed on type or on field would miss it. The seven-versus-eight difference is not a scan error to reconcile but a NEW member, and it confirms E-02's instruction to code bucket (b) as a CLASS rather than a hardcoded exception.
- Scope: Add an ADVISORY report naming every record whose declared `- Id:` or `- Set:` is absent from its filename, with the exact `aw rename` that would fix each, and with the quoting normalization that stops phantom findings. It EXTENDS or SITS BESIDE the existing `check.id6-identity-slot` rule and reuses its real-id6 discriminator rather than writing a second identity comparator. EXPLICITLY EXCLUDES auto-renaming anything, changing the check engine's legacy exemption into an error, and the resolver work in Order 01.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_name_identity_report.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Priority: medium
- Work-Kind: feature
- Set: findtier
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3i6rso
- From-Backlog: f8m2z2

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 3i6rso verified (set findtier, attempt 1). [Scope reconciliation - out-of-scope tests/test_check_engine.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL; PR-201..PR-205, all FIXED, no open questions (OQ-01/02/03 all resolved and all three survive re-measurement). `aw ipd lint` CONFORMING at `--phase author` before semantic review and at `--phase review-finalize` after. PROVENANCE THIS ROUND MUST RECORD: a ROUND 1 review was committed in `6cb837ad` and then REVERSED in `77384e9c`, which rolled `reviewed` back to `to-review`, stripped the Readiness attestation, and DELETED the 111-line typed review record; that commit's own message records it was done at the maintainer's explicit instruction after being flagged, judging the changes orphaned. Round 1's findings survive in this plan's body and are re-verified here rather than trusted; the deleted record remains recoverable at `6cb837ad`. THE PLAN'S CORE DESIGN RE-VERIFIED SOUND AND IS THE STRONGER HALF OF THE SET. Its central Round 1 insight holds on re-measurement: `check.id6-identity-slot` is registered exactly as described (severity `error`, assurance `repository`, deterministic, invariant `I-09`, all four read from `RULE_REGISTRY`), its rule (a) is already E-01/E-02's comparator for the modern case, and its discriminator is a NAMED SHARED HELPER, `_is_real_id6(token, declared_ids)`, whose docstring records the same `assess`/`agents` oracle. That E-06 must reuse rather than reimplement is now VERIFIED rather than argued: `_is_real_id6('assess', declared_ids)` returns False and `_is_real_id6('826o13', ...)` True, so the reuse genuinely fixes F-13's mis-bucketing hazard. The `- Id:` count of TEN reproduced exactly, and the warning-severity precedent reproduced exactly (6 warning, 24 error, 2 info, all six named rules confirmed). THE FINDING THAT MOST CHANGES THE PLAN IS A NEW ARTIFACT MEMBER THAT BREAKS THE BUCKET'S ASSUMED SHAPE (PR-201, F-16): the `- Set:` case is EIGHT, not seven, and the eighth is `aw-delivery` declared at `specs/20260730-2152-01-agents-artifact-organization.spec.md:198` INSIDE a fenced "Frontmatter schema" code block. That is the same quoted-example class as `uyeko5`, but in a SPEC and via the `set:` field, so the parser-artifact class has FIVE members across TWO fields and THREE types and is NOT research-only. A classifier keyed on record type or on field would have missed it and told a maintainer to rename an `implemented` spec to match a string from its own illustrative block; E-01/E-02 now require POSITIONAL detection and the execution contract names the third file. FOUR RECORDED FACTS HAD GONE STALE IN THE 24 HOURS SINCE ROUND 1, which is itself the lesson (PR-202, F-15): `check.id6-identity-slot` now emits ZERO findings, not 2, and E-05/V-04 tell the executor to prove that count "MUST NOT CHANGE", so a stale baseline of 2 would read a correct 0 as a regression; `aw check` total moved 170 -> 169; `check.setid-collision` 86 -> 38, with `check.scope-drift` now dominant at 110; and the suite moved `5929` -> `5958 passed`. Every count-bearing instruction now says to measure your own and states that these have already drifted once. ALSO FIXED: the sibling paragraph cited numbers no review produced (PR-203, F-17) - it claimed 12% and "54ms of 456ms" and a benchmark returning "ZERO results", where the measured figures are ~42.5ms of ~450ms with only ~12.8ms removable, and the sharper true statement is that the benchmark compares a filename search returning ZERO files against an `aw find` correctly returning ONE; the paragraph's conclusion survives and now also records that Order 01 is `no-go` with a blocking OQ-03. The concurrent-edit list was stale and understated (PR-204, F-18): twelve pending plans declare `check_engine.py`, not four, `dw7i3m` is not among them, and `76w6mq` - whose bounded reader E-02 wants to consume - is. And the window ambiguity that makes this plan say TEN while sibling `826o13` says NINE is now explained in both directions rather than left to look like an error (PR-205): a bounded 4096-byte header read finds nine, a full-body read finds ten, and `check_collisions` reads full bodies, so both are right. `Priority: medium` and `Work-Kind: feature` added from source item `f8m2z2`. Verified sound and unchanged: the premise (`is_clustered_conformant` False for both legacy names while `aw check specs` reports `13 specs checked, errors 0 warnings 0`), the advisory decision and both reasons, `aw check all` exiting 1 unpiped so F-7's vacuity finding stands, the no-auto-rename refusal (now with `25kzda` cited in 455 files, up from 425, so the argument strengthens over time), `aw rename --to-id6`'s existence, the fixtures-not-live-records rule, and per-rule comparison. No product code was modified by this review.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `f8m2z2` as Order 02, covering the item's second added requirement ("RAISE non-conforming filenames"). The item's premise was verified rather than trusted: `is_clustered_conformant` returns False for both a legacy plan name and a legacy spec name, while `aw check specs` reports ZERO naming findings, so the tolerance is real and the exception set is genuinely invisible. THE COUNT IS NINE, NOT THE ITEM'S EIGHT, AND THE NINTH IS NOT A NAMING PROBLEM: `uyeko5` is a QUOTED EXAMPLE in research prompt `27rjro`'s body, the parser artifact owned by `cqytxf`/`76w6mq`, so a report built today would show 9 and should show 8. That distinction is now E-02's explicit job, because conflating them would send someone to rename a correctly-named research prompt. Split from Order 01 because this is a reporting surface with its own test bed, and because it is what makes Order 01's mandatory content fallback retirable on evidence rather than permanently assumed.

## Goal

Make the set of records whose filename cannot be trusted countable, so the content fallback can eventually be retired on evidence instead of assumed forever.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the real set before reporting on it

- [x] E-01 ENUMERATE THE EXCEPTION SET AT YOUR HEAD AND CLASSIFY EVERY MEMBER, before writing any report. The count is the deliverable's whole point, so it must be established rather than inherited.
  SCAN EVERY TRACKED RECORD, not just plans: compare each file's declared `- Id:` and `- Set:` against its own filename. RE-MEASURED AT THE SECOND REVIEW (2026-09-10), so these are the numbers to reproduce and explain rather than to discover: the `- Id:` case is TEN (reproduced exactly; not the authoring count of nine) and the `- Set:` case is EIGHT (the first review said seven; an eighth member was found, see F-16). READ BOTH DIALECTS when scanning: the bullet form `- Id:` and the YAML form `id:`, since research records use YAML front matter and two of the ten are research documents.
  SCAN FULL BODIES, AND KNOW THAT THE WINDOW DECIDES THE COUNT. A bounded 4096-byte header scan finds NINE for the `- Id:` case; a FULL-BODY scan finds TEN, the tenth being the second `uyeko5` quotation, which sits beyond the header window. Order 01 (`826o13`) legitimately says nine because the RESOLVER only ever reads `_HEADER_BYTES` (`selectors.py:317`); this plan says ten because a REPORT reads whole files, and the existing `check_collisions` it extends reads whole files too (`p.read_text()`, no bound). So the two siblings' counts differ by design, not by error: do NOT "reconcile" them, and state your window whenever you cite a count.
  CLASSIFY EACH INTO ONE OF FOUR BUCKETS, because the remedies differ completely and the fourth was found at review: (a) LEGACY GRAMMAR, a pre-id6 or grandfathered name whose rename is a maintainer call (the eight: plans `4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`, specs `4w7d6s`, `25kzda`, `5tapom`); (b) PARSER ARTIFACT, where the declared value comes from a QUOTED EXAMPLE in the body rather than front matter - measured at the second review, this class has FIVE members across BOTH fields and THREE types, not a research-only pair: `uyeko5` quoted in `27rjro`'s prompt and `takpys`'s report, `runflags` from the same two quoted blocks, and `aw-delivery` quoted in a SPEC's fenced frontmatter-schema example (`20260730-2152-01-agents-artifact-organization.spec.md:198`); owned by `cqytxf`/`76w6mq`; (c) GENUINE DRIFT, a modern-grammar file whose name and metadata simply disagree, which would be a real defect; (d) NON-IDENTIFIER VALUE, a declared value that is not an identifier at all - measured: `20260813-1833-01-attention-visible-backlog-tier.spec.md` declares `set: <terse-id>`, a placeholder inside an illustrative code block. Bucket (d) must never produce a rename suggestion, because there is no name that would satisfy it.
  BUCKET (b) MUST BE DETECTED BY POSITION, NOT BY TYPE OR FIELD, and the `aw-delivery` case is why. A classifier keyed on "research documents" or on "the `- Id:` field" would have caught `uyeko5` and missed `aw-delivery` entirely, then told a maintainer to rename an `implemented` spec to match a string from its own illustrative code block. The structural test is whether the declaration sits inside a fenced block or otherwise outside the metadata region, which is exactly what `76w6mq` bounds; if it has not landed, implement the fenced-block exclusion here and say so in the report's output.
  IF BUCKET (c) IS NON-EMPTY, REPORT IT PROMINENTLY. None was found at authoring or at review, and a genuine drift case would be a live naming defect rather than a grandfathering question, so it deserves its own attention rather than being folded into an advisory count.
  RE-MEASURE AFTER CHECKING WHETHER `76w6mq` HAS LANDED. Its status is now `reviewed` (advanced from `to-review` since the first review) but it is still in `pending/`, so it has NOT landed and bucket (b) is NON-empty with five members across both fields. If it lands before you execute, bucket (b) should be EMPTY, the `- Id:` count should be eight, and the `- Set:` count six. Say which state you observed and re-check rather than trusting either figure.
  - Depends on: none
  - Expected outcome: the exception set enumerated at your HEAD with every member classified into legacy / parser-artifact / genuine-drift / non-identifier, the `- Set:` case measured separately, both front-matter dialects read, full bodies scanned with the window stated, and `76w6mq`'s status stated.
  - Execution state: performed

- [x] E-06 READ THE EXISTING IDENTITY RULE AND DECIDE EXTEND-VERSUS-ADD BEFORE WRITING ANY COMPARATOR. This item did not exist at authoring and is now the plan's first real design decision, because the plan proposed building from scratch something that is half-built already.
  WHAT IS ALREADY THERE, re-verified at the second review: `check.id6-identity-slot` is registered at `check_engine.py:101` (severity `error`, assurance `repository`, deterministic, invariant `I-09`, all four confirmed by reading `RULE_REGISTRY`) and implemented in `_check_identity_slots`, called from `check_collisions`. Its documented rule ALREADY states case (a): a file that declares a frontmatter `- Id:` must carry that same id6 in its filename slot. IT PRODUCES ZERO FINDINGS TODAY, not the 2 the first review recorded (F-15); the tree now reports 169 findings and this rule is absent from them. Take your own count.
  WHY IT DOES NOT COVER THE TEN, which is the narrow gap this plan actually fills: it only examines "a filename whose slot PARSES as a real id6 via the naming authority", so a legacy `YYYYMMDD-HHMM-NN-<slug>` name with no slot at all is exempt by construction. Verified: zero of the ten are flagged by it.
  REUSE ITS DISCRIMINATOR RATHER THAN INVENTING ONE, AND IT IS A NAMED SHARED HELPER YOU CAN CALL DIRECTLY: `check_engine._is_real_id6(token, declared_ids)`. `_check_identity_slots` builds `declared_ids` from every file's frontmatter and passes it in; the helper returns True iff the token is some file's declared Id OR visibly mixes digits and letters, whose docstring records the same `assess`/`agents` oracle this plan's F-13 describes. That matters concretely here, and it was VERIFIED at the second review rather than assumed: `_is_real_id6('assess', declared_ids)` returns `False` and `_is_real_id6('826o13', ...)` returns `True`, so calling the existing helper genuinely fixes F-13's mis-bucketing. `parse_clustered` reports the legacy name `20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md` as CONFORMANT with `id6='assess'`, and `ID6_RE` accepts `assess`, so a second comparator that skipped the helper would silently mis-bucket that record, which is one of the ten.
  STATE THE CHOICE AND ITS REASON IN THE CODE. Either extend the existing rule to cover slot-less names under a distinct advisory code, or add a sibling rule that imports the same discriminator. Do NOT copy the id6-detection logic; two definitions of "is this a real id6" that can drift is exactly the defect `check.id6-identity-slot` was written to avoid.
  - Depends on: E-01
  - Expected outcome: a recorded extend-versus-add decision with its reason, the existing rule's coverage measured (2 findings, 0 of the ten), and the real-id6 discriminator reused rather than reimplemented.
  - Execution state: performed

- [x] E-02 MAKE THE REPORT DISTINGUISH THE FOUR BUCKETS RATHER THAN EMITTING ONE COUNT, because a single number would be actively misleading on its first run.
  THE PARSER-ARTIFACT BUCKET MUST NOT BE REPORTED AS A NAMING PROBLEM, AND IT HOLDS TWO FILES. `27rjro`'s and `takpys`'s filenames are both CORRECT; their declared-`- Id:` readings are the same reader bug that `76w6mq` fixes. Reporting either as "rename this file" would send an operator to damage a correct name, and the item's own instruction for that document (via `cqytxf`) is that "the fix is in the reader, not the doc." Code the bucket as a CLASS, not as a hardcoded `27rjro` exception, since review measured two members and a third quotation could appear at any time.
  THE NON-IDENTIFIER BUCKET MUST NOT PRODUCE A REMEDY EITHER. `set: <terse-id>` is a documentation placeholder; no rename satisfies it. Detect it structurally (a value that is not a legal setid/id6 token, e.g. containing `<`, `>`, or whitespace) rather than by name, and emit it - if at all - as a distinct informational note saying the declaration is not an identifier.
  THE CLEANEST IMPLEMENTATION IS TO READ IDENTITY THE WAY THE FIXED READER WILL. If `76w6mq` has landed, consume its metadata-region-bounded reader and bucket (b) disappears by construction. If it has NOT landed (its status is now `reviewed` but it remains in `pending/`, so today it has not), the report must EXCLUDE body-quoted declarations explicitly and say why in its own output, so it does not carry a known-false finding. Note `76w6mq` also declares `check_engine.py`, so if it lands first you are editing a file it changed and must re-read it (F-18).
  NORMALIZE QUOTING, and note the case is LIVE rather than historical: exactly one tracked record carries `` set: `awoptimize` `` with backticks (`20260821-awoptimize-03-effzzi-...`), so an un-normalized comparison produces a real phantom on the first run. Compare stripped values.
  - Depends on: E-01, E-06
  - Expected outcome: a report that separates legacy-grammar records from parser artifacts, genuine drift and non-identifier values, never reporting a correctly-named file as needing a rename, with quoting normalized and the artifact bucket coded as a class rather than a named exception.
  - Execution state: performed

### Task group 2: make it advisory and actionable

- [x] E-03 EMIT IT AS AN ADVISORY WITH THE EXACT REMEDY PER RECORD, and do NOT promote the legacy exemption to an error.
  ADVISORY IS THE ITEM'S EXPLICIT REQUIREMENT and the reason is measured: `executed/` plan bodies are immutable by policy and the grandfathered specs are a documented decision, so an error-severity rule would fail the tree for states the maintainer deliberately chose. `check_engine`'s own precedent is the same shape: its review-escalation rule keeps the ABSENT case SILENT because a fail-closed absent case "would mass-fail the entire corpus on day one".
  NAME THE EXACT `aw rename` PER RECORD, which is what makes the report actionable rather than a lament. The item asks for "the exact `aw rename` that would fix it". Note the verb differs by type (`aw rename plans` versus `aw rename specs`) and that `--to-id6` exists for adopting the id6 grammar; get the per-record command right, because a wrong suggested command is worse than none.
  DO NOT TOUCH THE EXISTING LEGACY EXEMPTION. `check_engine`'s naming rule deliberately exempts legacy shapes, and the spec-name cutover deliberately grandfathers pre-cutover specs. This plan ADDS a report; it does not reclassify what is already tolerated.
  RESPECT THE SPEC CUTOVER RULE. Specs adopted the id6 grammar going forward with pre-cutover names grandfathered, so a pre-cutover spec appearing in this report is EXPECTED and its remedy line should say the rename is optional and a maintainer call, not overdue.
  - Depends on: E-02
  - Expected outcome: an advisory-severity report with a correct per-record `aw rename` suggestion, no change to the existing exemption, and pre-cutover specs described as optional rather than overdue.
  - Execution state: performed

- [x] E-04 DECIDE WHERE THE REPORT SURFACES, and choose a place that cannot mass-fail CI.
  THE CANDIDATES: a new advisory `check.*` rule in the full sweep; a dedicated flag on `aw check`; or `aw doctor` only. Each has a different blast radius.
  THE PLAN'S CENTRAL TEST RESTS ON A FALSE PREMISE AND MUST BE RESTATED, measured at review: `aw check all` ALREADY exits 1 today, with 170 findings on the live tree. So "prove the exit code is unchanged" is trivially satisfiable and proves nothing - the code is 1 before and 1 after no matter what this plan does. THE REAL PROPERTY to prove is the one the plan meant: that the new code carries `warning` severity and that NO ERROR-severity finding is added, so the advisory could not turn an otherwise-green tree red. Prove it as a SEVERITY assertion (paste the `RuleSpec` and assert the new code's severity is `warning`) plus a fixture-tree assertion: on a synthetic tree whose ONLY finding is this new code, `aw check` must exit 0. A live-tree exit-code comparison is NOT acceptable evidence for this item.
  THE WARNING PRECEDENT IS REAL AND NAMED, so the registration has a template rather than a guess: six codes already carry `warning` severity (`check.orphaned-live-blocker`, `check.review-dangling`, `check.review-decision-unescalated`, `check.system-layout-missing`, `check.system-layout-drift`, `check.stale-index-stale`), against 24 `error` and 2 `info`. Follow one of the six.
  MEASURE THE FINDING COUNT BEFORE CHOOSING, and state it. Ten for the `- Id:` case plus eight for `- Set:` (eighteen combined, against a tree already reporting 169) is small enough that a sweep rule is defensible; if your own scan turns up materially more, a flag or doctor-only becomes the better answer, and OQ-01 says so explicitly.
  IF A NEW RULE CODE IS ADDED IT MUST BE REGISTERED. `check_engine`'s `RuleSpec` table assigns severity, assurance class and determinism; an unregistered code carries no contract. Register it as a warning with the catalog id the adjacent naming rules use (`I-09`), matching the advisory decision.
  - Depends on: E-03
  - Expected outcome: a chosen surface with the finding count that justified it, a registered `warning`-severity rule code following one of the six existing warning precedents, and the no-error-added property proven by a severity assertion plus a synthetic-tree exit-0 test rather than by a live-tree exit-code comparison.
  - Execution state: performed

### Task group 3: prove it counts the right things

- [x] E-05 PROVE THE REPORT IS CORRECT ON ALL FOUR BUCKETS AND COSTS NOTHING ELSE.
  SEVEN ASSERTIONS MINIMUM, from fixtures (raised from five at review to cover the two cases the plan did not model): a legacy-named record IS reported with the right `aw rename`; a conformant modern record is NOT reported; a record whose declared value appears only in a QUOTED body block is NOT reported as a naming problem; a backtick-quoted front-matter value produces NO phantom finding; a genuine-drift record (modern grammar, mismatched metadata) IS reported and distinguished from legacy; a NON-IDENTIFIER declared value (`set: <terse-id>`) produces NO rename suggestion; and A LEGACY NAME WHOSE SLUG'S FIRST WORD IS SIX ALPHANUMERIC CHARACTERS is bucketed as legacy rather than as drift. That last one is not hypothetical: `20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md` parses as "conformant" with `id6='assess'`, which `ID6_RE` accepts, so a comparator that trusts the parsed slot mis-buckets a real member of the ten.
  BUILD FIXTURES, NOT LIVE-TREE ASSERTIONS. The live records will change: `76w6mq` removes two, and several agents are authoring concurrently. Use the live tree only for the count in evidence.
  ASSERT THE LIVE COUNT AS EVIDENCE, SEPARATELY, and name every member for BOTH the `- Id:` case (TEN full-body at the second review) and the `- Set:` case (EIGHT). STATE THE READ WINDOW with each, since a bounded header scan yields nine for the `- Id:` case and sibling `826o13` legitimately reports that number. That count is the artifact a future reader compares against to see whether the set is shrinking, which is the item's stated long-term prize.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. THE PLAN'S ORIGINAL BASELINE WAS WRONG AND ITS NAMED FAILURE DOES NOT EXIST; re-measured again at the second review and the totals moved AGAIN, which is the point: `1 failed, 5958 passed, 3 skipped, 2 xfailed in 56.85s` (the first review measured 5929 passed). The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, ENVIRONMENTAL and machine-specific: it globs the tree and trips over the gitignored local `opencode-recovery/` dump (1746 files; `.gitignore:49`), so it will not reproduce on a clean checkout. The claimed `tests/test_orchestrator_retirement.py` failure DOES NOT EXIST: that module is `112 passed` in isolation. Measure YOUR OWN baseline and compare NODE IDS, never totals; every recorded total here has already gone stale once.
  COMPARE `aw check` PER RULE, never by total, since several counts drift for unrelated reasons. Live baseline re-measured at the second review: 169 findings, of which `check.scope-drift` is 110, `check.setid-collision` is 38, `check.lifecycle-transition-invalid` 15, `check.name-nonconformant` 3, and `check.id6-identity-slot` is ZERO (absent from the diagnostics). The first review recorded 170 total, `setid-collision` 86 and `id6-identity-slot` 2, so all three moved: do NOT assert against those figures. The `check.id6-identity-slot` count must not change FROM WHATEVER YOU MEASURE unless E-06 chose to extend that rule, in which case state the new count and why (F-15).
  - Depends on: E-04
  - Expected outcome: seven fixture assertions passing, both live counts recorded with members named, per-rule comparison showing only the new code appearing (and `check.id6-identity-slot` unchanged unless deliberately extended), and an empty bare-suite delta judged by node id.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE TOLERANCE IS REAL AND MEASURED: `is_clustered_conformant` returns `False` for a legacy plan name and a legacy spec name, while `aw check specs` reports ZERO naming findings (`13 specs checked`, `errors 0 warnings 0`), because the naming rule deliberately exempts legacy shapes.
- AN ADJACENT RULE ALREADY EXISTS AND MUST BE CONSUMED: `check.id6-identity-slot` (`check_engine.py:101`, implemented in `_check_identity_slots`) already enforces declared-Id-equals-slot-id6 for names that HAVE an id6 slot, and already owns the real-id6-versus-slug discriminator via the SHARED HELPER `_is_real_id6(token, declared_ids)`. It exempts slot-less legacy names, which is exactly this plan's gap. Its live finding count is ZERO, not the 2 first recorded (F-15).
- THE EXCEPTION SET IS TEN FOR THE `- Id:` CASE (full-body scan; NINE on a bounded header read, which is why Order 01 says nine) and EIGHT FOR THE `- Set:` CASE, re-measured 2026-09-10. Of the ten, EIGHT are legacy/grandfathered and TWO are the same parser artifact.
- BOTH FRONT-MATTER DIALECTS MUST BE READ: the bullet form `- Id:` and the YAML form `id:`, since two of the ten are research documents using YAML.
- THE PARSER-ARTIFACT CLASS HAS FIVE MEMBERS ACROSS TWO FIELDS AND THREE TYPES, not a research-only pair: `uyeko5` quoted in `27rjro` and `takpys`, `runflags` from the same two blocks, and `aw-delivery` quoted in a SPEC's fenced frontmatter-schema example (F-16). `cqytxf`'s instruction is that "the fix is in the reader, not the doc", and `76w6mq` (now `reviewed`, still in `pending/`) implements it. Detect the class by POSITION, never by type or field.
- A FOURTH BUCKET EXISTS: a declared value that is not an identifier at all. `20260813-1833-01-attention-visible-backlog-tier.spec.md` declares `set: <terse-id>`, a placeholder inside an illustrative code block, and no rename can satisfy it.
- A LEGACY SLUG WORD CAN IMPERSONATE AN id6: `parse_clustered` reports `20260817-1357-01-assess-bugs-...` as conformant with `id6='assess'`, which `ID6_RE` accepts. Trusting the parsed slot mis-buckets a real member of the ten.
- `aw check` IS ALREADY RED: `aw check all` exits 1 (verified unpiped) with 169 findings, so an exit-code comparison on the live tree cannot prove an advisory is harmless.
- SIX RULES ALREADY CARRY `warning` SEVERITY (against 24 `error`, 2 `info`), re-verified by reading `RULE_REGISTRY` at the second review, so the advisory registration has a template: `check.orphaned-live-blocker`, `check.review-dangling`, `check.review-decision-unescalated`, `check.system-layout-missing`, `check.system-layout-drift`, `check.stale-index-stale`.
- THE LIVE PER-RULE COUNTS HAVE ALREADY DRIFTED ONCE: 169 total now versus 170 at the first review, `check.setid-collision` 38 versus 86, `check.id6-identity-slot` 0 versus 2, with `check.scope-drift` now dominant at 110. Assert against counts YOU measure, never against a figure recorded in this plan.
- SPECS GRANDFATHER PRE-CUTOVER NAMES by documented decision, adopting the id6 grammar GOING FORWARD, so a pre-cutover spec in this report is expected rather than overdue.
- `executed/` PLANS ARE NOT TO BE RE-COMMITTED, per the contributor contract at `AGENTS.md:63` and the `ipd-executed-gate` hook (a contract plus a local hook, not a filesystem immutability). That is half the reason the item forbids auto-rename.
- `25kzda` IS CITED IN 455 TRACKED RECORD FILES (re-counted at the second review; 425 at the first, so the citation base is GROWING), which makes renaming it progressively more expensive for a cosmetic gain; that is the other half, and the number is the argument.
- `check_engine` HAS AN ADVISORY PRECEDENT: its review-escalation rule keeps the absent case SILENT because a fail-closed absent case "would mass-fail the entire corpus on day one".
- RULE CODES ARE CONTRACTS: severity, assurance class and determinism come from `check_engine`'s `RuleSpec` table; an unregistered code carries none.
- `aw check` IS FAIL-CLOSED IN CI, so even an advisory must be proven not to change the exit code.
- QUOTING CAUSED A PHANTOM MISS ONCE: a backtick-quoted `` set: `awoptimize` ``.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | there is genuinely no signal today | `is_clustered_conformant` is False for a legacy plan and a legacy spec name, yet `aw check specs` reports ZERO naming findings. The exception set is invisible. | both measured at HEAD |
| F-2 | HIGH | the count is TEN on a full-body scan, not the plan's nine nor the item's eight | Ten tracked records declare an `- Id:` absent from their filename at HEAD (reproduced exactly at the second review); the plan said nine and the item said 8 of 751. The extra one is a second instance of the same artifact. A BOUNDED 4096-byte header scan finds NINE, which is why sibling `826o13` legitimately says nine: the resolver reads `_HEADER_BYTES` while this report reads whole files, as `check_collisions` already does. | re-scan of all tracked records at both reviews, reading BOTH the `- Id:` and YAML `id:` dialects, at both windows |
| F-3 | HIGH | the parser artifact is a CLASS with five members, not a pair and not research-only | `uyeko5` is a QUOTED EXAMPLE in TWO documents' bodies (`27rjro`'s prompt, `takpys`'s report); the same two blocks also yield `runflags` for the `- Set:` case; and `aw-delivery` is quoted in a SPEC's fenced frontmatter-schema block (F-16). All five filenames are CORRECT. Reporting any as a rename target would damage a correct name. Owned by `cqytxf`/`76w6mq`. So the bucket must be coded as a POSITIONAL class test, never a hardcoded `27rjro` exception nor a type/field filter. | all documents read at the two reviews; `cqytxf`'s "fix is in the reader" |
| F-4 | HIGH | this is what makes Order 01's fallback retirable | Order 01 must keep a mandatory content fallback BECAUSE these records exist; without a count, the fallback can never be retired on evidence. | the item's stated long-term prize; Order 01's scope |
| F-5 | MEDIUM | auto-rename is forbidden for two real reasons | `executed/` bodies are immutable by policy and grandfathered specs are a documented decision; `25kzda` is cited constantly so a rename breaks citations. | the item; the spec cutover decision |
| F-6 | MEDIUM | advisory has an in-repo precedent | `check_engine`'s review-escalation rule keeps the absent case silent to avoid mass-failing the corpus on day one. | that rule's docstring |
| F-7 | MEDIUM | THE EXIT-CODE TEST AS WRITTEN PROVES NOTHING, because the tree is ALREADY RED | `aw check all` exits 1 today with 170 findings, so "the exit code is unchanged" is satisfied no matter what this plan does. The property actually wanted is that no ERROR-severity finding is added, which must be proven by a severity assertion plus a synthetic-tree exit-0 test. | `aw check all >/dev/null 2>&1; echo $?` -> 1; 170 findings at review |
| F-8 | MEDIUM | RESOLVED AT REVIEW: the `- Set:` case contains a bucket the plan does not model (count corrected to EIGHT by F-16) | Records declaring a `Set:` absent from their filename include two artifact members (`set: runflags`), legacy names (incl. `awphysical`, `plans-adopter` x2), the backtick `` `awoptimize` ``, a third artifact (`aw-delivery`, F-16), and ONE DOCUMENTATION PLACEHOLDER - `20260813-1833-01-attention-visible-backlog-tier.spec.md` declares the literal `set: <terse-id>` from an illustrative code block. No rename can satisfy a placeholder. | measured at both reviews over all tracked records |
| F-9 | LOW | the quoting phantom is LIVE, not historical | Exactly one tracked record carries a quote-wrapped Set value today: `20260821-awoptimize-03-effzzi-...` with the literal `` `awoptimize` ``. An un-normalized comparison produces a real phantom on the first run. | measured at review |
| F-10 | LOW | the remedy differs by type | `aw rename plans` versus `aw rename specs`, and `--to-id6` exists for adopting the grammar (confirmed in `aw rename --help`); a wrong suggested command is worse than none. | `aw rename --help` read at review |
| F-11 | LOW | the no-rename argument is stronger than stated | `25kzda` is cited in 425 tracked files, so renaming it would rewrite references across a large fraction of the records tree for a cosmetic gain. The plan's instinct is right and now has a number. | `grep -rc 25kzda .aw/records/` -> 425 files |
| F-12 | HIGH | AN ADJACENT RULE ALREADY IMPLEMENTS HALF OF THIS AND THE PLAN DOES NOT MENTION IT | `check.id6-identity-slot` is registered (`check_engine.py:101`) and implemented in `_check_identity_slots` (`:923-1000`); its documented rule (a) already requires a declared `- Id:` to equal the filename slot id6, and it already solves the real-id6-versus-slug discriminator using the global `declared_ids` set (`:930-932`). It produces 2 findings and covers ZERO of the ten, because it exempts names with no id6 slot - exactly the legacy population. So the gap is narrow and the plan must extend or reuse rather than write a second comparator. | rule read and `check_collisions` run at review |
| F-13 | HIGH | THE NAIVE DISCRIMINATOR SILENTLY MIS-BUCKETS A REAL MEMBER | `parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")` returns CONFORMANT with `id6='assess'`, and `ID6_RE.match("assess")` is True, because `assess` is six lowercase alphanumerics. A comparator that trusts the parsed slot treats this legacy record (declared Id `wvlk84`) as modern, mis-bucketing one of the ten. This is why E-06 must reuse the existing rule's `declared_ids` discriminator. | both calls run at review |
| F-14 | LOW | the immutability premise is a CONTRIBUTOR CONTRACT, not a filesystem policy | `AGENTS.md:63` says "Do NOT add commits to a plan already in `.aw/records/plans/executed/`; close a post-execution gap with a new corrective IPD", enforced by the `ipd-executed-gate` pre-commit hook. The conclusion (no auto-rename) is correct; the plan's phrasing "immutable by policy" overstates it as an absolute, and a renamer would additionally have to rewrite references. | `AGENTS.md:63`; `engine.py:4631` |
| F-15 | MEDIUM | `check.id6-identity-slot`'s LIVE COUNT IS NOW ZERO, NOT TWO, AND THE PLAN'S "MUST NOT CHANGE" TEST WOULD READ IT AS A REGRESSION | `aw check all --agent` reports 169 findings with `check.id6-identity-slot` ABSENT from the diagnostics; the 2 findings the first review recorded have been resolved since. E-05 and V-04 instruct the executor to prove that count unchanged, so a stale baseline of 2 would make a correct 0 look like a regression. Per-rule counts also moved: `check.setid-collision` 86 -> 38, total 170 -> 169, and `check.scope-drift` is now the dominant rule at 110. | `aw check all --agent` parsed per rule at the second review |
| F-16 | HIGH | THE `- Set:` CASE IS EIGHT, NOT SEVEN, AND THE EIGHTH PROVES THE ARTIFACT BUCKET IS NOT RESEARCH-ONLY | Re-scanned: `<terse-id>`, `` `awoptimize` ``, `aw-delivery`, `awphysical`, `plans-adopter` x2, `runflags` x2. The new member `aw-delivery` is declared at `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md:198`, INSIDE a fenced "Frontmatter schema" code block, i.e. the SAME quoted-example class as `uyeko5`/`runflags` but in a SPEC and via the `set:` field. So bucket (b) has five members across two fields and three types; a classifier keyed on type or field would miss it and suggest renaming an `implemented` spec. Detect by POSITION (fenced/outside the metadata region). | full-body re-scan and the spec read at the second review |
| F-17 | MEDIUM | THE SIBLING PARAGRAPH'S CITED NUMBERS ARE NOT THE ONES THE SIBLING'S REVIEW RECORDED | This plan's gate says Order 01's resolver is "12% of `aw find`'s end-to-end cost (54ms of 456ms)" and that its benchmark "times a filename search that returns ZERO results". Both are wrong at HEAD: measured, the resolver is ~42.5ms of ~450ms (~9%), and `find .aw/records -iname '*lus9ou*'` returns ZERO files while `aw find plans lus9ou` correctly returns ONE, so the benchmark compares a miss against a hit, which is a sharper criticism than "zero results" and is the accurate statement. The paragraph's CONCLUSION (Order 01's value is under an open maintainer decision, this plan is independent) is correct and survives. | timed and run at the second review |
| F-18 | LOW | the concurrent-edit list is stale and larger | The plan names four other pending plans editing `check_engine.py` (`rnkqrc`, `k9awrq`, `sk7ggr`, `dw7i3m`). Re-scanned: twelve others declare it (`rnkqrc`, `b7xarm`, `jxxec8`, `sk7ggr`, `76w6mq`, `k9awrq`, `wmnmei`, `bwgyum`, `y4bdoz`, `1bdxcp`, `lkexaw`, `216rgg`), and `dw7i3m` is NOT among them. `76w6mq`, whose reader this plan wants to consume, is one of them. | `Scope-Paths` re-scan at the second review |

## Proposed changes (ordered, validatable)

1. Enumerate the exception set and classify every member into legacy / parser-artifact / genuine-drift / non-identifier, reading both front-matter dialects and measuring the `- Set:` case separately (E-01).
2. Read the existing `check.id6-identity-slot` rule and decide extend-versus-add, reusing its real-id6 discriminator rather than writing a second comparator (E-06).
3. Make the report distinguish the four buckets so a correctly-named file is never reported as needing a rename, with the artifact bucket coded as a class (E-02).
4. Emit it advisory with the exact per-record `aw rename`, without touching the existing exemption (E-03).
5. Choose a surface, measure the count that justified it, register a `warning` rule code, and prove no ERROR finding is added via a severity assertion plus a synthetic-tree exit-0 test (E-04).
6. Prove all seven bucket cases from fixtures and record both live counts with members named (E-05).

## Deferred / out of scope (with reason)

- AUTO-RENAMING ANY RECORD. Explicitly forbidden by the item, for two measured reasons: `executed/` bodies are immutable by policy and the grandfathered specs are a documented decision. `25kzda` alone is cited constantly enough that a rename would break more than it fixes.
- PROMOTING THE LEGACY EXEMPTION TO AN ERROR. This plan adds a report; reclassifying what the naming rule already tolerates would fail the tree for states the maintainer deliberately chose, and is a separate decision.
- THE RESOLVER AND ITS FILENAME TIER. Order 01 (`826o13`) owns it. This plan produces the COUNT that tells a future maintainer whether Order 01's mandatory fallback can ever be dropped.
- FIXING THE `27rjro` PARSER ARTIFACT. Owned by `cqytxf`/`76w6mq`. This plan must EXCLUDE it from the naming report, not fix it.
- RENAMING THE PRE-CUTOVER SPECS. Grandfathered by documented decision; the report describes their rename as optional and a maintainer call.
- A `--fix` OR BULK-RENAME MODE. The item's per-record maintainer-call requirement rules it out, and a bulk rename across `executed/` would violate the immutability policy at scale.
- THE RESEARCH YAML DIALECT. `05aqbj`/`xo3244` own it; this plan consumes whatever reader exists and, if `76w6mq` has not landed, excludes body-quoted declarations explicitly.

## Scope check

- Over-scope: none. One advisory report and its tests.
- Scope-Paths justification: `agent_workflows/check_engine.py` holds the naming rule, the `RuleSpec` severity table, `_iter_type_files` (`:503`) and the EXISTING `check.id6-identity-slot` implementation (`_check_identity_slots`, `:923-1000`) whose discriminator E-06 must reuse, so the scan, the bucket classification, the extend-versus-add decision and the rule registration all land there (E-02, E-03, E-04, E-06); `tests/test_name_identity_report.py` is new and carries the seven fixture cases plus the live-count evidence. `agent_workflows/artifact_naming.py` is deliberately NOT declared: the report CONSUMES `is_clustered_conformant` and the parse helpers read-only, and changing the naming authority would alter what every type considers conformant - note F-13 means the executor may WANT to change it (the `id6='assess'` mis-parse) and must NOT: work around it via the `declared_ids` discriminator instead, and file the parse behavior separately if it looks wrong. `agent_workflows/selectors.py` is likewise not declared even though Order 01 edits it, so the two children cannot collide at the finalize scope gate.
- CONCURRENT-EDIT NOTE, re-scanned at the second review and LARGER than first recorded (F-18): TWELVE other pending plans declare `check_engine.py` (`rnkqrc`, `b7xarm`, `jxxec8`, `sk7ggr`, `76w6mq`, `k9awrq`, `wmnmei`, `bwgyum`, `y4bdoz`, `1bdxcp`, `lkexaw`, `216rgg`); `dw7i3m`, named in the first review, is NOT among them. `sk7ggr` touches the id6/setid collision machinery this plan extends and `76w6mq` owns the bounded reader E-02 wants to consume, so whichever lands last must re-read the others rather than assuming `_check_identity_slots` is as this plan describes.
- Under-scope, stated rather than left as `none`: this plan renames nothing, does not promote the exemption to an error, does not touch the resolver, does not fix the parser artifact, does not fix the `id6='assess'` parse, adds no `--fix` mode, and does not teach any reader a second dialect (it READS both, which is different from teaching the shared resolver). Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. THE PLAN'S ORIGINAL BASELINE WAS WRONG AND ITS NAMED FAILURE DOES NOT EXIST, and the corrected figure has ITSELF gone stale: `1 failed, 5929 passed` at the first review, `1 failed, 5958 passed, 3 skipped, 2 xfailed in 56.85s` at the second. The single failure is the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (the gitignored local `opencode-recovery/` dump, `.gitignore:49`), and the claimed `test_orchestrator_retirement.py` failure does not exist (that module is `112 passed` alone). Measure your OWN baseline; criterion: AFTER minus BEFORE is EMPTY, compared by NODE ID, never an absolute count.
- SEVEN FIXTURE CASES (E-05): legacy reported with the right command; conformant not reported; body-quoted declaration NOT reported as a naming problem; backtick-quoted value producing no phantom; genuine drift reported and distinguished; NON-IDENTIFIER value (`set: <terse-id>`) producing no rename suggestion; and a legacy name whose slug begins with a six-alphanumeric word (`assess`) bucketed as legacy rather than modern.
- BOTH LIVE COUNTS recorded as evidence with every member NAMED, and the READ WINDOW stated: the `- Id:` case (TEN full-body, NINE bounded-header) and the `- Set:` case (EIGHT), since those counts are what a future reader compares against.
- `aw check all --agent` PER-RULE counts before and after, showing only the new code appearing and no existing rule's count changing FROM WHAT YOU MEASURE. Live baseline at the second review: 169 findings total, `check.scope-drift` 110, `check.setid-collision` 38, `check.lifecycle-transition-invalid` 15, `check.name-nonconformant` 3, `check.id6-identity-slot` ZERO. These moved from the first review's 170/86/2 (F-15), so treat them as a snapshot, not a contract. State the `check.id6-identity-slot` count explicitly, since E-06 may deliberately extend it.
- THE NO-ERROR-ADDED PROPERTY, proven the way F-7 requires: paste the new code's `RuleSpec` showing `warning` severity, AND a synthetic-tree test where the only finding is the new code and `aw check` exits 0. Do NOT offer a live-tree exit-code comparison as evidence: `aw check all` already exits 1 with 170 findings, so that comparison is vacuous.
- THE SUGGESTED COMMAND VERIFIED for at least one record of each type: run it in `--dry-run` (or equivalent) and show it resolves, since a wrong suggestion is worse than none. Confirmed available at review: `aw rename <type> ... --to-id6` exists for the legacy-grammar conversion.
- `76w6mq`'s STATUS stated, and the report's behavior under both states (landed / not landed) described. Now `reviewed` but still in `pending/` at the second review, so the not-landed branch is the one an executor will hit today; re-check rather than trusting this.
- THE FIFTH ARTIFACT MEMBER COVERED EXPLICITLY: `aw-delivery`, quoted in `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md:198` inside a fenced frontmatter-schema block, must NOT be reported as a rename candidate (F-16). It is the case that proves the bucket test must be positional rather than keyed on record type or field.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

The new rule's registration in `check_engine`'s table must carry a comment stating WHY it is advisory rather than an error: `executed/` bodies are immutable and the grandfathered specs are a documented decision, so an error would fail the tree for chosen states. Without that, a future tightening pass will promote it and break CI.

The report's own output must say what it is FOR, in one line: this is the exception set that forces `aw find`'s content fallback, and it is expected to shrink. A count with no purpose gets ignored; a count with a stated purpose gets acted on.

The bucket distinction must be documented at the code, especially the parser-artifact exclusion, because the next reader will otherwise "fix" the report by including `27rjro` and send someone to rename a correct filename.

No spec change is expected. The spec-name cutover is already documented in `check_engine`'s SUPPORTED comment (pre-cutover specs grandfathered, id6 required going forward), and this plan HONORS it rather than amending it. If the executor finds spec text requiring every record's filename to carry its id6 unconditionally, that contradicts the grandfathering and must be REPORTED rather than edited.

## Open questions

### OQ-01: Where should the report surface?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM EVIDENCE, as A SWEEP RULE AT `warning` SEVERITY, and RE-CONFIRMED at the second review on re-measured numbers. FIRST, THE COUNT IS SMALL AND BOUNDED: the plan said the sweep option "weakens considerably" if the `- Set:` scan turns up many more than nine; measured, it turns up EIGHT (revised up from seven, F-16), so the combined population is EIGHTEEN findings against a tree that already reports 169. That is roughly an 11% addition to an already-noisy sweep, not a flood, and it remains well inside the precedent set by `check.scope-drift` at 110 and `check.setid-collision` at 38. The revision from seven to eight does not change the answer, which is what makes the resolution robust rather than luck. SECOND, THE FAIL-CLOSED WORRY DISSOLVES ON MEASUREMENT: the plan's premise was that `aw check` is fail-closed in CI so the sweep risks flipping it red, but `aw check all` ALREADY exits 1 today, so no advisory can flip a state that is already failing. The real property (add no ERROR finding) is a severity choice, not a placement choice, and six registered rules already carry `warning` for exactly this reason. The alternatives are rejected on the item's own stated goal: `aw doctor`-only reaches fewer readers, and the item's prize is that the set be VISIBLE and seen shrinking, which argues for the surface agents and CI already run; a flag is "the least likely to be run" by the plan's own admission, which for a count whose purpose is to be watched over time is close to not shipping it. E-04 still measures and states the count that justified this, and still must prove the no-error-added property, so the decision is checkable rather than merely asserted. If an executor's own scan finds materially more than seventeen, that is a reason to re-open this question, and E-04 should say so.

### OQ-02: Should the report include the parser-artifact case?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THIS IS THE PLAN'S MOST IMPORTANT EXCLUSION. `27rjro`'s filename is CORRECT; the apparent mismatch exists only because the reader harvests a `- Id:` from a QUOTED EXAMPLE in its body, which is a reader bug `cqytxf` filed and `76w6mq` fixes, with the explicit instruction that "the fix is in the reader, not the doc". A report that listed it would suggest renaming a correctly-named research prompt, which is worse than reporting nothing: it would manufacture damage while appearing helpful. E-02 therefore requires the exclusion, and the cleanest implementation is to consume `76w6mq`'s bounded reader once it lands, at which point the exclusion becomes structural rather than a special case.

### OQ-03: Should a genuine-drift record be advisory too, or an error?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ADVISORY IN THIS PLAN, WITH THE DISTINCTION RECORDED, and the reasoning is that severity should follow evidence rather than intuition. A modern-grammar file whose name and metadata disagree IS a real defect, unlike a grandfathered name, so it deserves a stronger signal in principle. But NONE was found at authoring, so promoting a class with zero known members would be tuning a rule against no data, and the first real instance might turn out to have a legitimate explanation this plan has not anticipated. E-01 must report prominently if bucket (c) is non-empty, and if it is, the honest next step is a separate decision on severity with real examples in hand rather than a guess encoded now.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the enumerated exception set at your HEAD with EVERY member named and its bucket (legacy / parser-artifact / genuine-drift / non-identifier). Paste the `- Set:` case count separately from the `- Id:` case, and compare both against the review's measured 10 and 7, explaining any divergence rather than restating it. Show that BOTH front-matter dialects were read (name the two research documents, which use YAML). State `76w6mq`'s status. If bucket (c) is non-empty, paste those records prominently as a finding rather than folding them into a count.
  - Observed evidence: HEAD `7f06bb37`, scanning every tracked record of every SUPPORTED type PLUS `research`, reading BOTH dialects (bullet `- Id:`/`- Set:` and YAML `id:`/`set:`), 1227 files.

    RAW FULL-BODY SCAN, which is the plan's measurement and REPRODUCES IT: the `- Id:` case is **TEN** (matching the second review exactly) and the `- Set:` case is **SEVEN** by my scan, or EIGHT counting the backtick record the plan lists separately. Window matters, as E-01 says: a bounded 4096-byte header read yields NINE and FOUR respectively, so sibling `826o13`'s nine is legitimate and the two must not be "reconciled".

    ```
    total files scanned: 1227
    === Id case: 10
      [plans]      lus9ou  .aw/records/plans/executed/20260808-0004-00-plans-adopter-orchestrator.ipd.md
      [plans]      7qx7ys  .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
      [plans]      8q6yr9  .aw/records/plans/executed/20260808-0004-07-plans-scaffold-directives-decisions.ipd.md
      [plans]      4o5lt9  .aw/records/plans/executed/20260815-2156-01-installer-rollback-same-second-backup-collision.ipd.md
      [plans]      wvlk84  .aw/records/plans/executed/20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
      [research]   uyeko5  .aw/records/research/reference/202609/20260905-awmetastore-00-27rjro-...research-prompt.md
      [research]   uyeko5  .aw/records/research/reference/202609/20260905-awmetastore-01-takpys-...research-report.md
      [specs]      5tapom  .aw/records/specs/20260824-2000-01-research-lifecycle-reliability.spec.md
      [specs]      25kzda  .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
      [specs]      4w7d6s  .aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md
    === Set case: 7 (+1 = the backtick record, listed by the plan as a member)
      [plans]    'plans-adopter'  20260808-0004-06-migrate-existing-plans.ipd.md
      [plans]    'plans-adopter'  20260808-0004-07-plans-scaffold-directives-decisions.ipd.md
      [plans]    'awphysical'     20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
      [research] '`awoptimize`'   20260821-awoptimize-03-effzzi-...roadmap.md          <- the backtick phantom
      [research] 'runflags'       20260905-awmetastore-00-27rjro-...research-prompt.md
      [research] 'runflags'       20260905-awmetastore-01-takpys-...research-report.md
      [specs] YAML 'aw-delivery'  20260730-2152-01-agents-artifact-organization.spec.md
      [specs] YAML '<terse-id>'   20260813-1833-01-attention-visible-backlog-tier.spec.md
    ```

    BOTH DIALECTS PROVEN READ: the two research documents named above (`27rjro`, `takpys`) use YAML front matter and both appear, as does `aw-delivery` (YAML `set:` in a spec) and `<terse-id>` (YAML `set:`). A bullet-only scanner would have found neither of the last two.

    `76w6mq`'s STATUS: `- Status: approved` (advanced from `reviewed` since the second review) and STILL IN `pending/` (`.aw/records/plans/pending/20260908-idcapture-01-76w6mq-...ipd.md`). So it has NOT landed, and the not-landed branch is the one this execution took: the bounded metadata-region reader is implemented HERE, with a code note saying to delegate to `76w6mq`'s reader once it lands.

    CLASSIFIED SET AS THE SHIPPED RULE REPORTS IT (`include_retired=True`, i.e. the full historical count), THIRTEEN findings over ELEVEN records:

    ```
    === include_retired=True: 13 findings  {'legacy': 11, 'artifact': 1, 'non-identifier': 1, 'drift': 0}
      legacy          Id: lus9ou         20260808-0004-00-plans-adopter-orchestrator.ipd.md
      legacy          Id: 7qx7ys         20260808-0004-06-migrate-existing-plans.ipd.md
      legacy          Set: plans-adopter 20260808-0004-06-migrate-existing-plans.ipd.md
      legacy          Id: 8q6yr9         20260808-0004-07-plans-scaffold-directives-decisions.ipd.md
      legacy          Set: plans-adopter 20260808-0004-07-plans-scaffold-directives-decisions.ipd.md
      legacy          Id: 4o5lt9         20260815-2156-01-installer-rollback-same-second-backup-collision.ipd.md
      legacy          Id: wvlk84         20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
      legacy          Set: awphysical    20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
      legacy          Id: 5tapom         20260824-2000-01-research-lifecycle-reliability.spec.md
      legacy          Id: 25kzda         20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
      legacy          Id: 4w7d6s         20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md
      artifact        Set: aw-delivery   20260730-2152-01-agents-artifact-organization.spec.md
      non-identifier  Set: <terse-id>    20260813-1833-01-attention-visible-backlog-tier.spec.md
    === include_retired=False (the DEFAULT scope): 2 findings {'legacy': 2}
      legacy          Id: 5tapom         20260824-2000-01-research-lifecycle-reliability.spec.md
      legacy          Id: 25kzda         20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
    ```

    TWO DIVERGENCES FROM THE PLAN'S FIGURES, EXPLAINED RATHER THAN RESTATED, because both are the report working as E-02 specifies rather than a scan error.

    FIRST, THE ARTIFACT BUCKET IS ONE MEMBER, NOT FIVE, AND FOUR OF THE PLAN'S FIVE ARE NOT REPORTED AT ALL. `27rjro` and `takpys` each DECLARE their own `id:` and `set:` CORRECTLY in YAML front matter (`id: 27rjro`, `set: awmetastore`, both present in their filenames); the quoted `- Id: uyeko5` / `- Set: runflags` block at line ~58 is a different record's metadata entirely. Reading identity from the bounded metadata region - which E-02 asks for explicitly - therefore finds each file's OWN correct declaration and emits NOTHING, which is strictly better than emitting an advisory "this is a quoted example, do not rename" note about a file that has no problem. The one remaining artifact member (`aw-delivery`, in the `agents-artifact-organization` spec) IS reported as `artifact`, because that spec declares no `- Set:` of its own anywhere, so the only `set:` in the file is the quoted schema example; the class test still fires, keyed on POSITION. Note this required a real fix found during execution: searching by DIALECT first let the quoted BULLET shadow `27rjro`'s own YAML declaration, so the region is now searched first across both dialects (see `_identity_declared_values`).

    SECOND, `<terse-id>` IS BUCKETED `non-identifier`, NOT `artifact`, DESPITE ALSO BEING INSIDE A FENCED BLOCK. F-8/F-13 model it as a fourth bucket and E-02 requires the non-identifier detection to be structural; since no rename could ever satisfy `<terse-id>` regardless of where it sits, `non-identifier` is the stronger and more actionable statement. The positional fact is APPENDED to that finding rather than replacing it, so nothing is lost.

    BUCKET (c) GENUINE DRIFT IS EMPTY, as at authoring and both reviews: ZERO members, in both scopes. It is nonetheless implemented and proven from a fixture (`test_genuine_drift_on_a_modern_name_is_reported_and_distinguished_from_legacy`), and `LiveCountEvidenceTests` asserts the live bucket stays empty so a first real instance surfaces as a failure rather than silently joining an advisory count.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `check.id6-identity-slot`'s registration and the relevant lines of `_check_identity_slots`, and paste its finding count on your live tree (2 at review) together with proof that ZERO of the ten are covered by it - that is what establishes the gap is real and narrow. State the extend-versus-add decision and paste the code comment recording it. Paste the code showing the real-id6 discriminator is REUSED, plus a grep proving there is no second definition of id6-detection in the file. Paste the F-13 case measured directly: `parse_clustered` on the `assess` legacy name returning `id6='assess'`, `ID6_RE.match('assess')` True, and your classifier nevertheless bucketing that record as legacy.
  - Observed evidence: THE EXISTING RULE, read at HEAD (`check_engine.py:107`, relocated by name as instructed, not by the cited line):

    ```python
    "check.id6-identity-slot": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    ```

    Its rule (a), from `_check_identity_slots` (unchanged by this plan):

    ```python
    for path_str, declared_id, slot_id6 in records:
        if slot_id6 is None:
            continue  # legacy / no identity slot -> exempt
        if declared_id is not None:
            # Rule (a): the slot must equal the file's own declared identity. ...
            if slot_id6 != declared_id:
    ```

    ITS LIVE FINDING COUNT IS **ZERO**, NOT THE 2 THE FIRST REVIEW RECORDED - F-15 predicted exactly this and the re-measurement confirms it, so I state my own number as instructed. From `python3 -m agent_workflows check all --agent` on my HEAD, 324 findings BEFORE and 329 AFTER, with `check.id6-identity-slot` ABSENT from the diagnostics in both runs (per-rule table in V-04 below). It is therefore 0 -> 0, unchanged, and E-06 chose NOT to extend it.

    ZERO OF THE TEN ARE COVERED BY IT, which is what makes the gap real and narrow. Measured directly: `_identity_slot_token()` returns `None` for every one of the ten legacy names, because `parse_clustered` either fails outright or yields a 4-digit HHMM in the set segment:

    ```
    20260808-0004-00-plans-adopter-orchestrator.ipd.md                        parse=None            slot=None
    20260808-0004-06-migrate-existing-plans.ipd.md                            parse=None            slot=None
    20260808-0004-07-plans-scaffold-directives-decisions.ipd.md               parse=None            slot=None
    20260815-2156-01-installer-rollback-same-second-backup-collision.ipd.md   parse=None            slot=None
    20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md              parse=('1357','01','assess','ipd')  slot=None
    20260824-2000-01-research-lifecycle-reliability.spec.md                   parse=None            slot=None
    20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md              parse=None            slot=None
    20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md parse=None          slot=None
    ```

    And as a behavioral rather than structural proof, `test_the_new_rule_sits_beside_the_identity_slot_rule_without_changing_it` builds a tree holding ONLY a legacy `executed/` plan, asserts `check_collisions(..., include_retired=True)` reports `[]` for `check.id6-identity-slot`, and asserts the NEW rule does report it.

    THE DECISION: **ADD A SIBLING**, not extend. Recorded in the code (block comment above `check_name_identity`):

    > DECISION: ADD A SIBLING rather than extend it, for two reasons. (1) SEVERITY: `check.id6-identity-slot` is `error` and must stay so (a foreign id6 in an id6-bearing slot is a real defect); this population is grandfathered and must be `warning`, and one rule id cannot carry two severities without lying to every consumer keyed on it. (2) SUBJECT: that rule compares a filename SLOT against a declaration; this one reports a declaration that appears NOWHERE in the filename, including names that have no slot.

    THE DISCRIMINATOR IS REUSED, NOT REIMPLEMENTED:

    ```python
    m = _naming.parse_uniform_permissive(filename)
    if m is None:
        return False
    if _HHMM_RE.match(m.group("set")):
        return False  # legacy YYYYMMDD-HHMM-NN-<slug>, whose HHMM mimics a setid
    if own_id is not None:
        return True
    return _is_real_id6(m.group("id6"), declared_ids)
    ```

    Grep proving ONE definition (`grep -n "_is_real_id6" agent_workflows/check_engine.py`; `grep -c "def _is_real_id6"` -> `1`):

    ```
    916:def _is_real_id6(token: str, declared_ids: set) -> bool:      <- the ONLY definition
    1060:        if slot_id6 and _is_real_id6(slot_id6, declared_ids):   <- existing rule (b)
    1089:            if not _is_real_id6(slot_id6, declared_ids):        <- existing rule (b)
    1304:    return _is_real_id6(m.group("id6"), declared_ids)           <- THIS plan, calling it
    ```

    `test_the_shared_real_id6_discriminator_is_called_not_reimplemented` pins both facts (the call site string and `src.count("def _is_real_id6") == 1`) so a future copy-paste fails.

    THE F-13 CASE MEASURED DIRECTLY, and it is a live trap rather than a hypothetical:

    ```
    parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")
      -> {'date':'20260817','set':'1357','nn':'01','id6':'assess','slug':'bugs-leftover-remove-dataloss','type':'ipd'}
    is_clustered_conformant(same, expected_type="ipd")  -> True
    _ID6_RE.match("assess")                             -> True
    _is_real_id6("assess", set())                       -> False   <- the discriminator that saves it
    _is_real_id6("826o13", set())                       -> True
    ```

    And my classifier nevertheless buckets that record as **legacy**, both fields, proven by `test_a_legacy_slug_word_of_six_alphanumerics_buckets_as_legacy_not_drift` (which asserts the parse trap AND the bucketing in one test) and by the live output in V-01 (`legacy Id: wvlk84`, `legacy Set: awphysical`).

    ONE FINDING THE PLAN DID NOT FORESEE, and it is a correction to my own first implementation rather than to the plan: consulting `_is_real_id6` ALONE mis-buckets in the OTHER direction too. A MODERN name whose slot holds a typo'd id6 that is nobody's declared id (`...-01-slotaa-a.ipd.md` declaring `- Id: fmbbb1`) got `False` from the helper and was reported as a grandfathered legacy name, when it is precisely `check.id6-identity-slot`'s error case. `_identity_name_is_modern` now takes `own_id` and trusts the slot when the file declares an id6 at all - the same reasoning rule (a) states for itself - and `test_a_modern_names_Id_half_is_left_to_the_identity_slot_rule` pins it. This was found by `tests/test_check_engine.py`'s existing row failing, not by inspection.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the report's ACTUAL output on the live tree and confirm by inspection that NEITHER `27rjro` NOR `takpys` appears as a rename candidate - both, since the artifact is a pair. Quote the code implementing the exclusion, show it is a CLASS test rather than a hardcoded filename, and state whether it works by consuming `76w6mq`'s bounded reader or by an explicit body-quote exclusion. Paste the non-identifier handling and show `set: <terse-id>` produces no rename suggestion. Paste the quoting-normalization code and show the live backtick record (`awoptimize-03 effzzi`) produces no phantom.
  - Observed evidence: THE ACTUAL LIVE OUTPUT with its remedy lines (full scope, the 13 findings enumerated in V-01):

    ```
    legacy          Id: lus9ou (filename: 20260808-0004-00-plans-adopter-orchestrator.ipd.md)
         -> aw rename plans lus9ou --to-id6 --apply
    legacy          Set: plans-adopter (filename: 20260808-0004-06-migrate-existing-plans.ipd.md)
         -> aw rename plans 7qx7ys --to-id6 --apply
    legacy          Id: 25kzda (filename: 20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md)
         -> aw rename specs 25kzda --to-id6 --apply
    artifact        Set: aw-delivery (filename: 20260730-2152-01-agents-artifact-organization.spec.md)
         -> no rename: fix the READER that harvests identity from a quoted block (see `cqytxf` / `76w6mq`), not this document
    non-identifier  Set: <terse-id> (filename: 20260813-1833-01-attention-visible-backlog-tier.spec.md)
         -> no rename is possible: the declared value is not an identifier. If it is a schema example, move it inside a fenced block so it is not read as a declaration
    ```

    NEITHER `27rjro` NOR `takpys` APPEARS AS A RENAME CANDIDATE, AND NEITHER APPEARS AT ALL. Asserted by inspection AND measured mechanically:

    ```
    >>> any(k in Path(x.location).name for x in findings for k in ('awoptimize','27rjro','takpys'))
    False
    ```

    They are absent (rather than present-with-a-do-not-rename-note) because the bounded reader finds each file's OWN correct YAML declaration - `id: 27rjro` / `set: awmetastore`, both in their filenames - so there is nothing to report. That is a stronger outcome than the plan anticipated and is explained in V-01. The pair is still covered as a CLASS by a fixture (`test_a_quoted_declaration_outside_the_name_is_bucketed_artifact_and_never_a_rename`, which reproduces the exact live shape) and by the live property test `test_no_correctly_named_record_is_offered_a_rename`, which fails if ANY `artifact`/`non-identifier` finding ever carries an `aw rename`.

    IT WORKS BY AN EXPLICIT BOUNDED-REGION READ, NOT by consuming `76w6mq`'s reader, because `76w6mq` is `approved` but STILL IN `pending/` (stated in V-01). The code says so and says to delegate once it lands:

    ```python
    def _identity_metadata_region(text: str) -> str:
        """... A record opening with a `---` line is YAML-envelope dialect and its region is that
        envelope ... Otherwise the region runs from the start of the file to the first fenced code
        block or the first `##` heading, whichever comes first.
        ... NOTE the duplication this deliberately accepts: `76w6mq` (pending at authoring) owns a
        bounded identity reader for the RESOLVER. When it lands, this helper should DELEGATE to it."""
        lines = text.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            ...
        ends = [len(text)]
        for rx in (_IDENT_FENCE_RE, _IDENT_H2_RE):
            m = rx.search(text)
            if m is not None:
                ends.append(m.start())
        return text[: min(ends)]
    ```

    IT IS A CLASS TEST, NOT A HARDCODED FILENAME, and the module contains no `27rjro`/`takpys`/`aw-delivery` literal in any predicate: the test is POSITIONAL (`in_region`, derived from `_identity_metadata_region`) and therefore keyed on neither record type nor field, which is the property F-16 demands. Verified over the whole corpus before coding: the bound preserves 1171 of 1173 `Id` declarations and 1141 of 1146 `Set` declarations, and the handful it drops are exactly the quoted-example readings.

    THE NON-IDENTIFIER HANDLING, and its precedence, which is a decision rather than an ordering accident:

    ```python
    _IDENT_TOKEN_RE = _re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")
    ...
    if not _IDENT_TOKEN_RE.match(value):
        bucket = "non-identifier"
        detail = (f"declared `{field}: {value}` is not an identifier (a documentation placeholder or "
                  f"illustrative value), so no filename can satisfy it{quoted_note}")
        recovery = ("no rename is possible: the declared value is not an identifier. ...")
    ```

    `set: <terse-id>` produces NO rename suggestion: the live line above shows the recovery text, and `test_a_non_identifier_declared_value_produces_no_rename_suggestion` asserts `"aw rename" not in recovery`. The detection is structural (`<`/`>`/whitespace fail the token regex), not keyed on the filename.

    THE QUOTING NORMALIZATION:

    ```python
    value = raw.strip("`\"'") or None
    ```

    THE LIVE BACKTICK RECORD PRODUCES NO PHANTOM: `20260821-awoptimize-03-effzzi-...roadmap.md` declares `- Set: \`awoptimize\`` (line 17, confirmed with backticks at HEAD) and is ABSENT from all 13 findings - the mechanical check above covers it (`'awoptimize'` -> False). `test_a_backtick_quoted_front_matter_value_produces_no_phantom` pins the same property from a fixture, so it survives that record changing.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the report's per-record remedy lines and VERIFY at least one per type by running the suggested command in dry-run, showing it resolves. Quote the line describing a pre-cutover spec's rename as optional rather than overdue. Paste proof the existing legacy exemption was NOT changed (a diff over the naming rule).
  - Observed evidence: THE PER-RECORD REMEDY LINES are pasted in V-02 above (all five distinct shapes) and the full 13 are enumerated in V-01.

    VERIFIED IN DRY-RUN, ONE PER TYPE, both resolving (`aw rename`'s default IS the preview; `--apply` was NOT passed, so nothing was renamed):

    ```
    $ python3 -m agent_workflows rename specs 25kzda --to-id6
    --- would rename .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md -> 20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md ---
    --- reuses existing '- Id: 25kzda' (no re-mint) ---

    $ python3 -m agent_workflows rename plans lus9ou --to-id6
    --- would rename 20260808-0004-00-plans-adopter-orchestrator.ipd.md -> 20260808-plans-adopter-00-lus9ou-plans-adopter-orchestrator.ipd.md ---
    --- would rewrite 5x [full-name] '...' in .aw/records/plans/pending/20260908-findtier-02-3i6rso-...ipd.md ---
    ```

    F-10 WAS REAL AND BIT: the FIRST implementation suggested the FILENAME as the selector, and `aw rename plans 20260808-0004-06-migrate-existing-plans.ipd.md --to-id6` REFUSES with `error: no plan has Id '20260808-0004-06-migrate-existing-plans.ipd.md'` (the plans resolver is id-directed). The suggestion now uses the record's own declared id6 wherever it has one, which is why `_identity_rename_hint` exists as a helper with that measurement in its docstring rather than as an f-string. A second F-10 instance: `aw rename roadmaps effzzi` reports `no roadmaps artifact matched`, while `aw rename research effzzi` resolves, so `_IDENT_RENAME_TYPE` maps `roadmaps -> research` with the reason recorded.

    THE PRE-CUTOVER-SPEC LINE, describing the rename as OPTIONAL and a maintainer call rather than overdue (the `legacy` bucket's detail text, which is what a pre-cutover spec receives):

    > `declared \`{field}: {value}\` is absent from this pre-id6-grammar filename, so the record cannot be located by name; the rename is OPTIONAL and a maintainer call (grandfathered, not overdue)`

    THE EXISTING LEGACY EXEMPTION WAS NOT CHANGED. `git diff agent_workflows/check_engine.py` contains exactly THREE hunks, all purely ADDITIVE, and none of them is inside `check_names`, `_spec_requires_id6`, `SPEC_ID6_CUTOVER_DATE`, or `_check_identity_slots`:

    ```
    $ git diff agent_workflows/check_engine.py | grep "^@@"
    @@ -401,6 +401,35 @@ RULE_REGISTRY: Dict[str, RuleSpec] = {          <- the new RuleSpec entry
    @@ -1076,12 +1105,409 @@ def _check_identity_slots(...)                <- the new code, AFTER that function
    @@ -1933,6 +2359,24 @@ def check_types(                              <- the sweep wiring
    ```

    The only appearances of `check.name-nonconformant` in the diff are (a) a comment naming it as a family member and (b) the new rule DEFERRING to it (see V-04's overlap note); `SPEC_ID6_CUTOVER_DATE` appears only inside the new registration comment. Behaviorally confirmed: `check.name-nonconformant`'s live count is 3 -> 3 (V-04 table), and `tests/test_check_engine.py`'s naming and retirement-scope rows pass UNMODIFIED.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: state the chosen surface and the finding count that justified it, and confirm it against OQ-01's resolved answer (sweep rule at `warning`) or justify departing from it. Paste the `RuleSpec` registration showing `warning` severity with its explanatory comment, and name which of the six existing warning rules it follows. Paste the no-error-added proof in the form F-7 requires: the severity assertion AND a synthetic-tree run whose only finding is the new code exiting 0. Paste per-rule counts showing only the new code appeared and `check.id6-identity-slot`'s count stated explicitly. DO NOT offer a live-tree before/after exit code as the proof; `aw check all` already exits 1, so that comparison is vacuous and its presence alone fails this item.
  - Observed evidence: THE CHOSEN SURFACE: a SWEEP RULE at `warning` severity, exactly OQ-01's resolved answer, with NO departure. It rides the once-per-full-sweep seam in `check_types` beside its I-09 family neighbours and is reached by `aw check` / `aw check all`.

    THE COUNT THAT JUSTIFIED IT, measured on my HEAD: 13 findings at full scope (2 at default scope) against a tree already reporting 324. That is ~4% of an already-noisy sweep, well inside OQ-01's threshold ("if an executor's own scan finds materially more than seventeen, that is a reason to re-open this question") - it is FEWER than the eighteen the resolution reasoned about, so the resolution holds a fortiori and I did not re-open it.

    THE REGISTRATION (severity, with its explanatory comment; full comment in the source):

    ```python
    # findtier Order 02 (`3i6rso`) E-04: a record whose declared `- Id:` or `- Set:` is ABSENT from
    # its own filename. ...
    # `warning`, NOT `error`, and the reason is a measured policy constraint rather than caution.
    # Every member on this tree today is grandfathered BY DECISION: eight are pre-id6-grammar names,
    # five of them `executed/` plans whose bodies must not be re-committed (AGENTS.md, enforced by
    # the `ipd-executed-gate` hook), and the rest are pre-cutover specs that `SPEC_ID6_CUTOVER_DATE`
    # above deliberately grandfathers. An `error` would therefore fail the tree for states the
    # maintainer CHOSE ...
    "check.identity-absent-from-name": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    ```

    WHICH OF THE SIX IT FOLLOWS: **`check.review-dangling`** - advisory, whole-tree, deterministic, riding the same full-sweep seam, and consumed by no lifecycle gate. Named in the registration comment and asserted in `test_the_rule_is_registered_as_a_warning_following_the_review_dangling_precedent`, which also re-reads that rule's severity so a change there is noticed here.

    THE NO-ERROR-ADDED PROOF, as a SEVERITY ASSERTION (F-7's form), from `test_no_error_severity_finding_is_added` on a fixture that really produces findings:

    ```python
    self.assertEqual(
        sorted({d.severity for d in drift}),
        ["warning"],
        "every finding this rule emits must be `warning`; a single `error` would let the "
        "advisory fail a tree that was otherwise clean",
    )
    ```

    NO LIVE-TREE EXIT-CODE COMPARISON IS OFFERED AS PROOF, per the explicit instruction. (For completeness only, not as evidence: the tree exits 1 before and after, which proves nothing, exactly as F-7 says.)

    THE SYNTHETIC-TREE "EXITS 0" HALF CANNOT BE SATISFIED BY ANY NON-`info` RULE IN THIS CODEBASE, and I am flagging that rather than fabricating it. `artifact_core.drift_exit_code` is literally `return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, so a `warning`-only tree exits 1 BY DESIGN. Two registered rules state the same fact in their own comments (`check.review-decision-unescalated`: "DO NOT READ `warning` AS 'cannot fail anything' (measured, not assumed)"; `check.stale-index-missing`: "`info` -> the ONLY non-failing severity"), and `tests/test_review_findings.py` says an exit-code argument "would prove nothing (F-13)" for a `warning`. Registering this rule `info` to make the literal assertion pass would ship the WRONG contract, so instead the property is proven three ways and the measurement is pinned: `test_a_synthetic_tree_whose_only_finding_is_this_rule_still_fails_the_gate` asserts `drift_exit_code(drift) == 1` AND `drift_exit_code([d._replace(severity="info") ...]) == 0`, so the claim is measured rather than asserted, and `test_the_rule_gates_no_lifecycle_step` is a source census proving neither `ipd_lint.py` nor `ipd_lifecycle.py` consumes the rule id. Recorded as DECISION 04-3i6rso-D1 with human review requested on the wording.

    PER-RULE COUNTS, BEFORE AND AFTER, via `python3 -m agent_workflows check all --agent` (the installed `aw` shim resolves a different package copy, so the module form is used to exercise THIS workspace's code):

    ```
    BEFORE total=324 exit=1
    AFTER  total=329 exit=1

    rule                                           before   after  delta
    check.from-backlog-dangling                         1       1     +0
    check.from-backlog-gate-mismatch                    2       2     +0
    check.id6-collision                                 1       1     +0
    check.identity-absent-from-name                     0       2     +2   <== NEW (the only new id)
    check.ipd-uncarried-obligation                     86      86     +0
    check.lifecycle-transition-invalid                  3       3     +0
    check.live-bug-ungated                              2       2     +0
    check.name-nonconformant                            3       3     +0
    check.scope-drift                                 225     228     +3
    check.system-layout-missing                         1       1     +0
    ```

    `check.id6-identity-slot`'s COUNT STATED EXPLICITLY: **ZERO before and ZERO after** (absent from the diagnostics in both runs), unchanged, because E-06 chose to ADD a sibling rather than extend it. F-15 warned that a stale baseline of 2 would read a correct 0 as a regression; my own measurement is 0.

    THE ONE OTHER MOVING COUNT IS NOT CAUSED BY THIS RULE, and I checked rather than assuming. `check.scope-drift` +3 is a LOCATION-SET NO-OP: diffing the findings by `(location, rule)` shows the scope-drift location set is IDENTICAL before and after (`only-in-after` and `only-in-before` are both empty for that rule when compared as sets), and the three extra rows belong to OTHER agents' pending plans (`m7gvuz`, `w2y5ac`, `udgilu`) reacting to live receipts in this shared checkout, since my own edits are uncommitted at measurement time. The default scope reports 2 of the 13 because retirement filtering is honored (DECISION 04-3i6rso-D2); `aw check --all` reports the full count.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of all seven fixture cases, QUOTING separately the four false-positive guards: the body-quoted-declaration assertion, the backtick-quoting assertion, the non-identifier assertion, and the six-alphanumeric-slug-word assertion. Paste BOTH live counts with members named as standing evidence. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly by NODE ID, compared against your own measured baseline rather than any figure in this plan.
  - Observed evidence: ALL SEVEN REQUIRED CASES PASS, inside a 20-test module (the seven, plus the E-06 reuse pair, the E-04 registration set, the three scope/overlap boundaries found during execution, and two live-tree evidence tests). ACTUAL output:

    ```
    $ python3 -m pytest tests/test_name_identity_report.py -o addopts="" -v
    collected 20 items
    ScopeAndOverlapTests::test_a_modern_names_Id_half_is_left_to_the_identity_slot_rule PASSED
    ScopeAndOverlapTests::test_retirement_scope_is_honored_rather_than_overridden PASSED
    ScopeAndOverlapTests::test_a_junk_filename_is_left_to_the_name_grammar_rule PASSED
    LiveCountEvidenceTests::test_no_correctly_named_record_is_offered_a_rename PASSED
    LiveCountEvidenceTests::test_the_exception_set_is_small_and_bucketed PASSED
    AdvisoryRegistrationTests::test_no_error_severity_finding_is_added PASSED
    AdvisoryRegistrationTests::test_the_rule_is_registered_as_a_warning_following_the_review_dangling_precedent PASSED
    AdvisoryRegistrationTests::test_a_synthetic_tree_whose_only_finding_is_this_rule_still_fails_the_gate PASSED
    AdvisoryRegistrationTests::test_the_rule_is_reached_by_the_full_sweep PASSED
    AdvisoryRegistrationTests::test_the_rule_gates_no_lifecycle_step PASSED
    FourBucketTests::test_a_conformant_modern_record_is_not_reported PASSED              <- ASSERTION 2
    FourBucketTests::test_a_body_quoted_declaration_is_not_reported_as_a_naming_problem PASSED   <- GUARD 1
    FourBucketTests::test_a_legacy_named_record_is_reported_with_a_resolvable_rename PASSED      <- ASSERTION 1
    FourBucketTests::test_a_non_identifier_declared_value_produces_no_rename_suggestion PASSED   <- GUARD 3
    FourBucketTests::test_a_quoted_declaration_outside_the_name_is_bucketed_artifact_and_never_a_rename PASSED <- GUARD 1b
    FourBucketTests::test_a_backtick_quoted_front_matter_value_produces_no_phantom PASSED        <- GUARD 2
    FourBucketTests::test_genuine_drift_on_a_modern_name_is_reported_and_distinguished_from_legacy PASSED <- ASSERTION 5
    FourBucketTests::test_a_legacy_slug_word_of_six_alphanumerics_buckets_as_legacy_not_drift PASSED <- GUARD 4
    DiscriminatorReuseTests::test_the_shared_real_id6_discriminator_is_called_not_reimplemented PASSED
    DiscriminatorReuseTests::test_the_new_rule_sits_beside_the_identity_slot_rule_without_changing_it PASSED

    ============================== 20 passed in 5.10s ==============================
    ```

    THE FOUR FALSE-POSITIVE GUARDS, QUOTED SEPARATELY as required.

    GUARD 1, body-quoted declaration (a spec whose fenced block holds a second `- Set:`/`- Id:`):

    ```python
    self.assertEqual(
        got, [],
        "the file's OWN declarations are both in its name, and the quoted block must not be "
        f"read as a second declaration; got {got!r}",
    )
    ```

    GUARD 1b, the live shape (declaration quoted AND absent from the name) - must bucket `artifact` and never suggest a rename:

    ```python
    self.assertEqual(bucket, "artifact", ...)
    self.assertNotIn(
        "aw rename", d.recovery,
        "an artifact-bucket finding must never suggest a rename: the filename is correct",
    )
    ```

    GUARD 2, backtick quoting:

    ```python
    self.assertEqual(
        got, [],
        f"a backtick-wrapped value must be compared STRIPPED, producing no finding; got {got!r}",
    )
    ```

    GUARD 3, non-identifier:

    ```python
    self.assertEqual(got, [("non-identifier", "20260101-real-01-abc123-x.spec.md", "Set")], ...)
    self.assertNotIn(
        "aw rename", drift[0].recovery,
        "no rename can satisfy a non-identifier value, so none may be suggested",
    )
    ```

    GUARD 4, the six-alphanumeric slug word (which also asserts WHY it is needed, so the test states the trap rather than only the outcome):

    ```python
    self.assertEqual(m.group("id6"), "assess", "the parsed slot is the SLUG's first word")
    self.assertTrue(ce._ID6_RE.match("assess"), "and it matches the id6 shape")
    ...
    self.assertEqual(
        got, [("legacy", name, "Id"), ("legacy", name, "Set")],
        f"both fields must bucket as `legacy`, never `drift`; got {got!r}",
    )
    ```

    BOTH LIVE COUNTS WITH MEMBERS NAMED are pasted in V-01 (13 at full scope over 11 records; 2 at default scope), and are carried forward as standing evidence by `LiveCountEvidenceTests`, which asserts a BOUND plus an empty `drift` bucket rather than a member list, so the corpus changing (e.g. `76w6mq` landing) is not a false failure.

    THE BARE SUITE, BEFORE AND AFTER. The BEFORE run is a CLEAN CLONE of this workspace at HEAD `7f06bb37` (`git clone --no-hardlinks . tmp/base && git checkout 7f06bb37`), so the baseline is uncontaminated by my edits:

    ```
    BEFORE (clean clone at 7f06bb37):
    7150 passed, 3 skipped, 2 xfailed, 3 warnings in 281.06s (0:04:41)

    AFTER (this workspace):
    7170 passed, 3 skipped, 2 xfailed, 3 warnings in 254.15s (0:04:14)
    ```

    THE FAILURE-SET DELTA BY NODE ID IS **EMPTY**: the baseline failure set is `{}` (ZERO failures) and the after failure set is `{}` (ZERO failures), so `AFTER minus BEFORE` is empty and no node id regressed. The +20 passed is exactly the 20 new tests in `tests/test_name_identity_report.py`.

    MY BASELINE DIFFERS FROM EVERY FIGURE RECORDED IN THIS PLAN, which the plan predicted and instructed me to expect. The plan's second review measured `1 failed, 5958 passed`; I measure `7150 passed` with ZERO failures. The named environmental failure `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` does NOT occur here, because this lane worktree has no gitignored `opencode-recovery/` dump. The claimed `test_orchestrator_retirement.py` failure does not exist either, consistent with the plan's own correction.

    THREE EXISTING TESTS FAILED MID-EXECUTION AND ALL THREE ARE NOW GREEN WITH THE CAUSE UNDERSTOOD, recorded because a passing final suite would otherwise hide real findings: `test_each_entry_point_composes_exactly_its_declared_sub_checks`, `test_is_retired_and_the_default_scope_agree_about_every_artifact`, and `test_one_pass_reports_exactly_the_collisions_present`. They drove DECISION 04-3i6rso-D2 (honor the retirement scope instead of overriding it), D3 (two overlap exclusions so one authoring mistake is not double-reported), and D4 (four fixtures whose declared `- Set:` contradicted their own filename were CORRECTED, while the one row whose fixture is a genuine member of this population gained the new rule id with a rationale). No expectation was loosened to make a failure disappear.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS IS ORDER 02 OF A TWO-CHILD SET AND CARRIES NO DEPENDENCY EDGE, deliberately: it can execute before or after Order 01. The two are complementary rather than sequential, since Order 01 makes lookups cheaper while this one makes the exception set that constrains Order 01 countable. Order 01 edits `selectors.py` and this one edits `check_engine.py`, so they do not overlap by construction.

THIS PLAN IS THE MORE DEFENSIBLE HALF OF THE SET, AND A READER SHOULD KNOW WHY, because the sibling's review changed the picture. Order 01 (`826o13`) was reviewed and its central performance premise did not survive measurement (F-17 corrects the numbers this paragraph originally carried): the resolver it optimizes is ~42.5ms of a ~450ms end-to-end `aw find`, about 9%, and of that only ~12.8ms is actually removable by its filter, roughly 3% of what an operator waits for, while the display layer (~114ms) and interpreter startup (~115ms) each dwarf it. Its headline benchmark also compares a filename search that returns ZERO files against an `aw find` that correctly returns ONE, so it times a miss against a hit. Order 01's OQ-03 is consequently now `Blocking: yes` and its readiness `no-go`, pending a maintainer choice between executing it as narrowed, re-scoping onto the display layer, or deferring.
THIS PLAN DOES NOT DEPEND ON THAT OUTCOME, and the independence is structural rather than asserted: disjoint `Scope-Paths` (`check_engine.py` versus `selectors.py`), no dependency edge, and no shared symbol. Its deliverable is a COUNT, worth having whether or not Order 01 ever executes: it is what would let a future maintainer retire the content fallback on evidence, and it is what tells anyone whether the exception set is growing. If Order 01 is deferred, do NOT infer that this plan should be; if anything the count matters more, because it is then the only part of the Set that ships. Note also that Order 01's review left a standing note that the two plans' counts differ BY DESIGN (nine on a bounded header read, ten on a full-body read), so a reader comparing the siblings should not treat the difference as a defect in either.

ONE HONEST CAVEAT ABOUT THE STATED PRIZE, so nobody over-promises on it. "Retire the content fallback" requires the exception set to reach ZERO, and eight of the ten members are grandfathered-by-decision (`25kzda` alone is cited in 425 files). So the realistic outcome of this report is a WATCHED, STABLE count that prevents the set from growing unnoticed, not a countdown to zero. That is still worth building; it is just a different promise from the one the backlog item implies.

IT CARRIES NO `Blocks-Release`, because backlog `f8m2z2` carries none. It is `Work-Kind: feature` at `Priority: medium` and the maintainer did not gate it; stated so a reader does not assume a gate was dropped.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. RENAME NOTHING: the report is advisory and every rename is a maintainer call per record, and an `executed/` plan must not be re-committed (`AGENTS.md:63`, enforced by the `ipd-executed-gate` hook). Do NOT promote the existing legacy exemption to an error. Do NOT list `27rjro`, `takpys`, OR `20260730-2152-01-agents-artifact-organization.spec.md` as a rename candidate; all three filenames are correct and all three declarations are quoted examples of the same class (F-16). Do NOT write a second id6-detection comparator: call the existing shared helper `check_engine._is_real_id6(token, declared_ids)` (E-06), verified at review to return False for `assess` and True for a real id6. Do NOT "fix" `artifact_naming.parse_clustered`'s `id6='assess'` mis-parse; it is out of scope and undeclared, so work around it and file it separately if it looks wrong. Do NOT offer a live-tree `aw check` exit-code comparison as proof the advisory is harmless; the tree already exits 1. Do NOT assert against any COUNT recorded in this plan: the suite total, `aw check`'s total, `check.setid-collision` and `check.id6-identity-slot` have all already drifted between two reviews (F-15), so measure your own and state it. Build every case from FIXTURES, never from live records, since the live set will change as `76w6mq` lands and several agents author concurrently. Re-locate every symbol by NAME rather than by the line numbers cited here, and re-read the other pending `check_engine.py` edits before starting (twelve declare it: `rnkqrc`, `b7xarm`, `jxxec8`, `sk7ggr`, `76w6mq`, `k9awrq`, `wmnmei`, `bwgyum`, `y4bdoz`, `1bdxcp`, `lkexaw`, `216rgg`), since `sk7ggr` touches the collision machinery this plan extends and `76w6mq` owns the reader it wants to consume. Compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the classified exception set and the unchanged `aw check` exit code.
