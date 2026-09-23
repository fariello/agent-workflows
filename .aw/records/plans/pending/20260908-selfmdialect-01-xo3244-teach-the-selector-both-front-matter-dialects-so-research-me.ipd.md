# IPD: Teach the selector both front-matter dialects so research metadata is matchable

- Date: 2026-09-08
- Kind: child
- Concern: `selectors.py` is the ONE selector-to-file resolver for every verb and understands only the BULLET front-matter dialect (`- Id:`, `- Status:`, `- Set:`). Research docs use YAML front matter instead, so for research the three content-derived rules MATCH_ID6 / MATCH_SETID / MATCH_STATUS never fire at all, and every research query silently falls through to MATCH_SUBSTRING, the explicit last-resort FILENAME rule. The failure is silent and plausible-looking rather than an error: `aw find research reference` returns 5 files matched by filename while 52 research docs actually carry `status: reference`, and nothing in the output signals that the metadata was never consulted.
- Scope: Make the resolver's three front-matter readers understand the YAML dialect in addition to the bullet dialect, so research id6/setid/status become matchable, and ACCEPT the resulting contract change deliberately (`aw find research reference` goes from 5 results to 52). Reuse `research_contract.parse_frontmatter` rather than writing a second YAML reader. Preserve the documented precedence chain, the bounded header read, the artifacts-not-mentions rule, and byte-for-byte identical behavior for every non-research type. Replace the test that pins today's filename-only behavior with one that pins the new behavior, and record the change in the changelog because it is user-visible.
- Scope-Paths: agent_workflows/selectors.py, tests/test_selector_zero_open.py, CHANGELOG.md, tests/test_id_metadata_region.py
- Item-Dependencies: executed:76w6mq
- Status: approved
- Work-Kind: bug
- Priority: medium
- Readiness: go-pending-approval
- Set: selfmdialect
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xo3244
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: 05aqbj
- Blocks-Release: next

## Workflow history
- 2026-09-23 approved (opencode its_direct/pt3-claude-opus-5-1m-us): WORK PERFORMED, NOT A TERMINAL TRANSITION. This entry records execution of the plan's items only; the status stays `approved` and the terminal transition to `executed` belongs to `aw ipd finalize`, which the RUNNER performs for this lane (a worker-role process is refused with `AW-LIFECYCLE-ROLE-001`). Executed all 7 E-items and verified all 7 V-items with pasted evidence, in lane `aw/lane/xo3244` at base HEAD `0823163b`. Dependency `executed:76w6mq` was already satisfied (it is in `plans/executed/`), and the composition it gates was verified on the real `27rjro` document: the region bound makes the bullet path miss, the new YAML fallback then yields the document's own `27rjro` instead of the foreign `uyeko5` it once reported. Suite: `3 failed, 9097 passed, 3 skipped, 2 xfailed` against a self-measured baseline of `3 failed, 9069 passed, 3 skipped, 2 xfailed` on the same lane, i.e. +28 passed and the SAME 3 failures, each proven pre-existing by re-running with my changes stashed. THREE CORRECTIONS THIS EXECUTION MADE TO THE PLAN'S OWN CLAIMS, all re-measured rather than inherited. (1) The headline shift is 5 -> 64, not the authored 52 nor review's 58. (2) THE MUTATING-VERB EXPOSURE OQ-01 ACCEPTED DOES NOT OCCUR: `aw archive` (and `rename`/`group` for research) NEVER routes through this resolver, so their behavior is byte-identical before and after, verified for six command forms. The plan's F-13 and OQ-01 assumed otherwise. That bypass contradicts `selectors.py:4-9`'s single-resolver claim and is filed as backlog `mblu3p` (`bug`, gated `Blocks-Release: next`) rather than fixed here, because fixing it WOULD deliver the 0 -> 32 widening OQ-01 already approved and that deserves its own plan. (3) The fenced non-research population is 0 in this lane, not review's 2, because both `Kind: session-handoff` prompts live in the gitignored `records/*/untracked/` lane and are absent from an isolated worktree; that vindicates F-5c and is exactly why the case-sensitivity proof is a FIXTURE test rather than a corpus count. SCOPE: 3 declared paths changed, plus ONE UNDECLARED, `tests/test_id_metadata_region.py`, where three characterization tests pinned the old behavior and named this plan as the change that would flip them; each was updated to assert the new value while keeping its original subject intact (see the decisions register, decision 37-xo3244-D1).
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item 05aqbj (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> None (not negative). Specifically, both blocking questions were answered on 2026-09-10 (dependency edge declared; both selector surfaces accepted) and the findings they escalated, PR-301 and PR-303, are now closed in review round 2. Performed at HEAD `5692797e` at the maintainer's explicit instruction of 2026-09-10, who was shown that 12 of 15 `no-go` plans were held by stale bookkeeping and chose to have them fixed with evidence recorded rather than re-reviewed. This is the SECOND such cleanup in one session; the durable fix is plan `qhy3i3` E-07, authored and awaiting approval. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`. NOTE ON THE VERDICT INPUT FOR THIS PLAN: `newest_verdict` returns polarity None here, NOT because the review is missing but because this session's tooled `aw ipd dependencies set` write appended a `reviewed (aw set)` history line that `is_review_history_entry` misclassifies as a review record, shadowing the real one. The actual review verdict is `REVIEWED - OPEN QUESTIONS` (confirmed in both the plan history and the typed review record's `- Verdict:` field), which is the NEUTRAL case and not a negative verdict, so the third condition is genuinely clear. That misclassification is a real defect and is filed as backlog `ycg597`; it is NOT a reason to withhold this re-check.
- 2026-09-10 reviewed (aw set): set Item-Dependencies to executed:76w6mq

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; readiness NO-GO; PR-301..PR-307. Reviewed at HEAD `d0b0acab`; `aw ipd lint` conformed at `--phase author` before semantic review. THE APPROACH IS SOUND AND RE-VERIFIED: `aw find research reference` returns 5 while 58 docs carry `status: reference`, the silent-fallthrough diagnosis holds, reusing `parse_frontmatter` is right, keeping the public runner readers bullet-only is right, and the 4096-byte header genuinely suffices (0 of 110 parsable docs straddle it). TWO BLOCKERS ESCALATED. PR-301 -> OQ-03: this plan and `76w6mq` compose in ONE ORDER ONLY and neither declares the edge. Because this plan tries the bullet regex FIRST and consults YAML only on a miss, running it alone leaves the `27rjro` doc still reporting the FOREIGN id6 `uyeko5` from a quoted block (measured: bullet-on-header `uyeko5`, bullet-on-region None, own YAML id `27rjro`), so the collision that breaks `aw set` survives; with `76w6mq` first, the fallback returns the correct value. PR-303 -> OQ-01, reclassified from advisory to BLOCKING and widened: the contract change reaches the MUTATING `aw archive` verb, where the bare tokens `reference`/`todo`/`archive` go from 5/0/0 files to 58/20/31, so accepting 'my search returns more rows' is not accepting 'my archive verb moves 31 documents'. PR-302 (HIGH) falsified F-5: the blast radius outside research is NOT zero, since two `Kind: session-handoff` prompts ARE `---`-fenced; what protects them is CAPITALIZED keys plus a case-SENSITIVE lookup that E-01 never specified, so the whole safety argument rested on an unstated detail. Also fixed: E-07 omitted a fourth test in its target class and a second class (`DialectDocumentationTests`) that asserts the very docstring phrases E-07 rewrites; the headline figure is 58 not 52; the suite baseline was wrong in count and named failure. OQ-02 RESOLVED from the precedence table (status beats stem/substring, path still wins; before state measured as 0, not 5).
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `05aqbj`, inheriting its `Blocks-Release: next` gate. THE ITEM ASKS THE AUTHOR TO PICK ONE OF THREE OPTIONS; this plan picks OPTION 1 (teach the resolver both dialects), which the item itself calls the recommended shape, and states the 5 -> 52 consequence as an accepted contract change rather than a side effect. OQ-01 hands that acceptance to the maintainer explicitly, because it is theirs to make and not the executor's. Every measurement in the item was RE-VERIFIED at HEAD `44d4950d` and all of it reproduces, with the counts slightly moved by the corpus growing since 2026-09-01: `aw find research reference` returns 5 lines today, while parsing front matter over the same tree gives `reference: 52, archive: 31, todo: 21, active: 1` across 105 YAML-parsable docs. TWO NEW MEASUREMENTS THAT MATERIALLY DE-RISK THE WORK, both of which the item could not have known. FIRST, the blast radius outside research is provably ZERO: I enumerated every candidate the resolver walks for all eight status-carrying types and counted how many begin with a `---` fence, giving `plans 0/527, specs 0/28, backlog 0/158, releases 0/1, reviews 0/69, prompts 0/16, walkthroughs 0/17, research 105/107`. No non-research record can take the new branch, so this cannot perturb `aw find plans` or any mutating verb's resolution. SECOND, the item's warning to NORMALIZE QUOTING (a `set:` value reading `` `awoptimize` `` with backticks) does NOT reproduce anywhere in the current corpus: I checked every parsed value for backticks and for stray quotes and found zero anomalies. E-04 still normalizes, because the warning came from a real observation and a defensive strip is nearly free, but it is now a guard rather than a fix for a live defect, and the plan says so instead of claiming a bug it cannot demonstrate.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a research status or id6 query answer the question the user asked. The specific harm being removed is silent under-reporting: a reader cannot tell a genuine 5-file answer from a 52-file answer whose metadata was never read, so two records with identical metadata resolve differently based only on which dialect their type happens to use.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read the second dialect

- [x] E-01 Add a YAML-dialect fallback to the three internal front-matter readers `_read_id` (`selectors.py:246-248`), `_read_status` (`:251-253`) and `_read_setid` (`:305-310`), so each tries its existing bullet regex FIRST and, only on a miss, consults the YAML block. Keep the bullet path first and unchanged so no currently-matching record changes its answer. DELEGATE THE YAML PARSE to `research_contract.parse_frontmatter` (`research_contract.py:552-577`); do NOT write a second YAML reader, or the two will drift about what counts as valid front matter. Note the import direction: `selectors.py` currently imports the naming authority and `layout`, and its module docstring records that the naming authority never imports it; check that adding a `research_contract` import creates no cycle, and if it does, import it lazily inside the function rather than restructuring either module.
  THE KEY LOOKUP MUST BE CASE-SENSITIVE, AND THIS IS THE ITEM'S LOAD-BEARING DETAIL RATHER THAN A NICETY. Look up EXACTLY `id`, `status` and `set`, lowercase, and do NOT fold case, `.title()`, or try variants. REASON, measured at review and not knowable from the authored plan: TWO `---`-fenced records exist OUTSIDE research (two `Kind: session-handoff` prompts under `.aw/records/prompts/untracked/`), and they are saved from perturbation ONLY by their capitalization. `parse_frontmatter` preserves keys verbatim (`research_contract.py:568-575`: `key.strip()`, no case folding), so on those files `.get('Status')` is `draft` while `.get('status')` is None. A case-sensitive lookup leaves them untouched; a tolerant one silently makes `aw find prompts draft` start matching two handoff drafts. Write the case-sensitivity as an explicit code comment naming this reason, because it looks like an arbitrary restriction and a future "robustness" edit would undo the safety proof E-06 rests on.
  - Depends on: none
  - Expected outcome: given the text of a research doc, `_read_id` returns its `id:`, `_read_status` its `status:`, and `_read_setid` its `set:` first token; given the text of a plan, all three return exactly what they return at HEAD; given a `Kind: session-handoff` prompt with `Status: draft`, all three return None because the lookup is case-sensitive.
  - Execution state: performed

- [x] E-02 Confirm the bounded header read is sufficient for the YAML dialect and do NOT enlarge it. `_read_header` reads at most `_HEADER_BYTES` = 4096 (`selectors.py:317-330`), and the item asserts that is enough for a YAML block too. RE-VERIFIED at HEAD `d0b0acab` and this item exists to keep it verified rather than assumed: parsing the first 4096 bytes of every research doc yields the SAME result as parsing the whole file for all 110 YAML-parsable docs of 118 (0 documents parse from the full text but fail from the header). Note WHY the check is not trivial: `parse_frontmatter` returns `None` when it never sees the closing `---` fence (`research_contract.py:576-577`), so a document whose front matter straddles the 4096-byte boundary would silently read as having NO metadata, which is the exact silent-miss class this plan exists to remove. Add an assertion or comment pinning the relationship so a future front-matter growth spurt fails loudly rather than degrading.
  - Depends on: E-01
  - Expected outcome: no change to `_HEADER_BYTES`, plus evidence that every research doc's front matter closes inside it, and a guard that makes a future violation visible.
  - Execution state: performed

- [x] E-03 Leave the PUBLIC readers `read_front_matter_id` (`:288-295`) and `read_front_matter_status` (`:298-305`) BULLET-ONLY, and say why in a comment next to them. These are the runners' shared readers (`oc_runipd` and `agy_runipd` call them; the long note at `:255-282` records that they exist precisely so there is one definition per reader and that they use a deliberately LOOSER whitespace pattern than the internal readers). A driver reads PLAN front matter, never research, so teaching them YAML adds a dialect no caller can produce while widening the surface of the one pair of readers whose failure mode is documented as silently degrading a runner to a directory-derived status. Keeping them narrow is a decision, so record it rather than leaving a reader to wonder whether it was an oversight.
  - Depends on: E-01
  - Expected outcome: the public readers are unchanged in behavior, and a comment states that the YAML dialect is deliberately not wired into them and why.
  - Execution state: performed

- [x] E-04 Normalize a YAML scalar before comparing: strip surrounding backticks and matching quote pairs. THE HONEST STATUS OF THIS ITEM: the backlog item reports observing a `set:` value written `` `awoptimize` `` with backticks during e32j35's maintainer session, and warns that comparing raw produces a phantom mismatch. That does NOT reproduce in the current corpus. Measured at HEAD `44d4950d` across all 105 YAML-parsable research docs, checking every front-matter value for a backtick or for a value that differs from itself with quotes stripped: ZERO anomalies. So this is a defensive guard against a form the corpus once held, not a fix for a live defect, and it must not be described as the latter. Implement it anyway (it is a two-line strip and the observation was real), and apply it consistently to id, status and setid. Do NOT extend the normalization to the BULLET readers: `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT that deliberately disagrees with `plans_index._META_RE` on 24 records (`selectors.py:112-121`), and loosening it would change what `aw find plans` matches.
  - Depends on: E-01
  - Expected outcome: a research doc whose `set:` reads `` `topic` `` resolves for the selector `topic`; bullet-dialect matching is byte-for-byte unchanged.
  - Execution state: performed

### Task group 2: hold the contracts that must not move

- [x] E-05 Prove and preserve the invariants the resolver's docstring makes, none of which this change may quietly alter. (a) PRECEDENCE stays `path -> id6 -> setid -> status -> stem -> substring` (`_PRECEDENCE`, `selectors.py:71-78`; the loop at `:601-613`). Note the OBSERVABLE CONSEQUENCE the tests must capture: a research id6 query that returns MATCH_SUBSTRING today will return MATCH_ID6 afterwards, which is the intended change, and the winning `kind` is carried on the `Resolution` where callers can apply the kind-aware ambiguity policy. (b) The `allow`/`deny` rejection semantics stay intact: a match only via a denied kind must remain an explicit `rejected_kind` rejection with empty `paths`, never a silent no-match (`:604-607`). (c) The ARTIFACTS-NOT-MENTIONS rule holds: front matter only, never body text, which the bounded header read plus the anchored patterns already enforce. (d) The single-traversal performance property survives: `_files()` must keep deriving from `_paths()` rather than walking again (`:551-566`; the docstring records 83ms vs 50ms on 469 plans when it walked twice), and the filename-only rules must keep consulting `_paths()` and never `_files()` (`:591-598`).
  - Depends on: E-01, E-04
  - Expected outcome: each of (a)-(d) demonstrated individually rather than asserted collectively.
  - Execution state: performed

- [x] E-06 Show the change cannot perturb any NON-research type, and pin that with a test. THE AUTHORED PREMISE IS FALSE AND MUST NOT BE RE-ASSERTED: the plan claimed "no non-research record" opens a `---` fence, making the blast radius provably zero. RE-MEASURED at HEAD `d0b0acab`: `plans 0/608`, `specs 0/29`, `backlog 0/176`, `releases 0/1`, `reviews 0/139`, `prompts **2**/34`, `walkthroughs 0/17`, `research 110/112`. TWO PROMPTS ARE FENCED, both `Kind: session-handoff` files under `.aw/records/prompts/untracked/`, so a non-research record CAN reach the new branch.
  THE SAFETY ARGUMENT THEREFORE CHANGES FROM "NOTHING ELSE IS FENCED" TO "THE LOOKUP IS CASE-SENSITIVE", and this item must prove the NEW claim rather than the old one. Those prompts carry `Status:`/`Kind:`/`Date:` capitalized, and `parse_frontmatter` preserves keys verbatim, so a case-sensitive `status`/`id`/`set` lookup returns None for them. PROVE IT DIRECTLY: assert that each of the two fenced prompts still resolves exactly as it does today, and add a fixture test with a `---`-fenced NON-research record carrying `Status: draft` asserting the fallback does NOT match it. Note these two files live in a GITIGNORED lane (`.aw/.gitignore:6` `records/*/untracked/`), so another machine may hold different ones and the fixture test, not the corpus count, is the durable guard.
  Re-run the per-type enumeration after the change and confirm resolution is identical for every non-research type. Pin it also with a test that a bullet-dialect record still resolves via the bullet path even if a YAML-looking line appears in its body, so the fallback cannot start reading bodies.
  - Depends on: E-05
  - Expected outcome: identical resolution for all seven non-research types before and after INCLUDING the two fenced prompts; a fixture test proving a fenced non-research record with capitalized keys is not matched; and a regression test that the YAML fallback never fires on a bullet record.
  - Execution state: performed

### Task group 3: replace the test that pins the old contract, and disclose the change

- [x] E-07 Rewrite `tests/test_selector_zero_open.py::ResearchStaysFilesystemResolvedTests` (`:371-424`), which EXISTS TO PIN TODAY'S BEHAVIOR and will go red by design. Its tests are `test_research_has_no_bullet_id` (`:398-399`), `test_research_id6_resolves_by_filename_substring_not_id6` (`:401-409`, asserting `MATCH_SUBSTRING` with the message "a MATCH_ID6 here would mean the YAML dialect was wired in, which changes results"), `test_research_status_query_does_not_see_yaml_status` (`:411-415`, asserting `got.paths == []` for the selector `reference`), AND a FOURTH the plan originally omitted, `test_research_status_query_opens_zero_files_when_it_is_a_filename_miss` (`:417-424`), which survives the change but belongs to the inverted class and must be carried across rather than dropped. DO NOT DELETE THE CLASS: invert it, keeping its fixture (two YAML docs, `:378-393`) and renaming it to describe the new contract, so the corpus retains the record that this behavior was changed deliberately. The first test stays TRUE as written (a research doc genuinely has no bullet `- Id:`) and should be kept to document that the fallback, not the bullet path, is what now matches.
  THERE IS A SECOND TEST CLASS THAT CONSTRAINS THE DOCSTRING REWRITE, and finding it mid-execution is avoidable. `DialectDocumentationTests` (`:426-440`) asserts the module docstring contains BOTH the substrings `"YAML front matter"` and `"research"` (`test_module_docstring_names_the_dialect_gap`), so a rewrite that drops either phrase turns it red for a reason unrelated to correctness; keep both phrases while changing what the prose CLAIMS, or update that test deliberately and say so. Its sibling `test_status_regex_carries_the_parity_note` asserts the `PARITY` + `plans_index.py` prose still sits within 1200 characters before `_STATUS_RE`, so do not displace that comment while editing nearby.
  Update the module docstring's E-06 rationale at `selectors.py:11-31`, which currently explains at length why research is deliberately NOT wired in; leaving that prose in place would make the code lie about itself.
  - Depends on: E-06
  - Expected outcome: the class asserts the new contract (research resolves via MATCH_ID6 / MATCH_STATUS / MATCH_SETID) and carries all four of its original tests forward; `DialectDocumentationTests` still passes or is deliberately updated with a stated reason; the module docstring no longer claims research is deliberately excluded; and the changelog carries a user-visible entry stating that `aw find research <status>` now matches front matter and returns more results, with the RE-MEASURED count rather than the authored 52.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `selectors.py` is the single resolver for every verb, so a change here reaches `rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`, `archive` and the set-assign/mv paths at once (module docstring `:1-9`). That is why the non-research no-op proof in E-06 is load-bearing and not decoration: a regression would surface as a MUTATING verb resolving to the wrong file.
- The module docstring at `:11-31` is a written rationale for the CURRENT exclusion, authored by IPD `e32j35` E-06 which deliberately documented rather than fixed this. Reversing the decision means rewriting that prose, not appending to it.
- `_STATUS_RE` (`:121`) carries a PARITY CONSTRAINT comment (`:112-120`): its `(\S+)` requires a single-token status, its twin `plans_index._META_RE["Status"]` uses `(.+?)`, and the two provably disagree on 24 of 469 plans carrying a multi-word `- Status:`. Do not "harmonize" them while here.
- There are already TWO tiers of reader in this module for a reason: strict internal ones for selector matching, and permissive public ones for the runners (`:255-282`). A third dialect belongs in the internal tier only (E-03).
- `parse_frontmatter` (`research_contract.py:518-543`) is deliberately minimal and dependency-free: scalars become `str`, `[a, b]` becomes a list, and a missing closing `---` returns `None`. Its `None`-on-malformed behavior is what makes E-02's boundary check necessary.
- `research_index._scan_docs` is the existing consumer of that parser, which is what makes it the canonical reader rather than one of several.
- The status vocabulary differs per type. Research statuses measured here are `reference`, `archive`, `todo`, `active`; note `archive` is also a DIRECTORY name in the research tree, so a selector `archive` may match both by status and by path. Check which rule wins under the preserved precedence and make sure the answer is deliberate.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The three content-derived rules read only the bullet dialect, so they cannot fire for research at all. | `selectors.py:246-248`, `:251-253`, `:305-310`; rules dispatched at `:584-592` |
| F-2 | The defect reproduces at HEAD: `aw find research reference` returns 5 records. | measured `python3 -m agent_workflows find research reference` -> 5 lines, at `44d4950d` |
| F-3 | The true count is an order of magnitude higher, and it has MOVED since authoring. RE-MEASURED at HEAD `d0b0acab`: `reference: 58, archive: 31, todo: 20, active: 1` across 110 YAML-parsable docs of 118 `.md` files (authored figures were `reference: 52 ... 105 of 113`). So the headline contract change is 5 -> 58, not 5 -> 52. RE-COUNT at execution rather than asserting either number; the corpus grows continuously. | measured via `research_contract.parse_frontmatter` over `.aw/records/research/**/*.md` at `d0b0acab` |
| F-4 | The failure is SILENT, which is what makes it a bug rather than a limitation: the status rule does not error, it falls through to the filename rule and returns a plausible short list. | `_PRECEDENCE` loop `:601-613`; `MATCH_SUBSTRING` documented as the explicit last resort at `:515` |
| F-5 | FALSIFIED BY REVIEW: THE BLAST RADIUS OUTSIDE RESEARCH IS NOT ZERO. Re-running the same enumeration at HEAD `d0b0acab` gives `plans 0/608`, `specs 0/29`, `backlog 0/176`, `releases 0/1`, `reviews 0/139`, `prompts **2**/34`, `walkthroughs 0/17`, `research 110/112`. TWO PROMPTS ARE `---`-FENCED (`.aw/records/prompts/untracked/20260829-1422-01-session-handoff-run-ledger-defects.md` and `...-2250-01-session-handoff-wtiso-stranded-lanes.md`), both `Kind: session-handoff` written by the `handoff` workflow, so a non-research record CAN take the new branch and the plan's "single strongest reason option 1 is safe" does not hold as stated. | enumerated via `selectors._iter_paths` + `selectors._read_header` at `d0b0acab` |
| F-5b | WHAT SAVES IT IS CASE, NOT ABSENCE, AND THE PLAN NEVER SPECIFIES THE LOOKUP. Those two prompts carry CAPITALIZED keys (`Kind:`, `Status: draft`, `Date:`, `Purpose:`, `Focus:`), and `parse_frontmatter` preserves keys VERBATIM (`research_contract.py:568-575`, `key.strip()` with no case folding). Measured: `parse_frontmatter(header)['Status']` is `draft` while `.get('status')` is None. So a case-SENSITIVE lookup for `status`/`id`/`set` leaves both prompts unperturbed, and a case-INSENSITIVE or `.title()`-tolerant one silently makes `aw find prompts draft` start matching them. E-01 says only "consults the YAML block" and never fixes the lookup, so the safety of the whole change rests on an unstated implementation detail. | measured at `d0b0acab`; `research_contract.py:552-577` |
| F-5c | THE FENCED PROMPTS SIT IN A GITIGNORED LANE, which bounds the damage but does not remove the requirement. `.aw/.gitignore:6` is `records/*/untracked/`, so these two files are box-local and another machine may have none, or may have different ones. That makes the case-sensitivity requirement a CONTRACT rather than a corpus accident: the next `handoff` run writes another such file. | `git check-ignore` at `d0b0acab` |
| F-6 | The 4096-byte header read is sufficient: 0 research docs parse from the full text but fail from the first 4096 bytes. The check matters because `parse_frontmatter` returns `None` on a missing closing fence, so a straddling block would read as no-metadata. | measured at `44d4950d`; `research_contract.py:542-543` |
| F-7 | THE ITEM'S QUOTING WARNING DOES NOT REPRODUCE. Zero of 105 parsed docs carry a backticked or stray-quoted `id:`/`status:`/`set:` value. E-04 is therefore a defensive guard, not a live-defect fix, and must not be sold as the latter. | measured at `44d4950d` over every parsed front-matter value |
| F-8 | A test currently PINS the behavior this plan changes, and its own assertion message says so. It must be inverted, not deleted. | `tests/test_selector_zero_open.py:371-416`, notably `:401-409` and `:411-415` |
| F-8b | THE PINNING CLASS HAS A FOURTH TEST AND THERE IS A SECOND CLASS, NEITHER NAMED BY E-07. `ResearchStaysFilesystemResolvedTests` also holds `test_research_status_query_opens_zero_files_when_it_is_a_filename_miss` (`tests/test_selector_zero_open.py:417-424`), which survives the change but belongs to the inverted class. More importantly `DialectDocumentationTests` (`:426-440`) asserts the module DOCSTRING contains both `"YAML front matter"` and `"research"`, so E-07's docstring rewrite can turn it red depending on wording; and its sibling `test_status_regex_carries_the_parity_note` asserts the `PARITY` + `plans_index.py` prose still precedes `_STATUS_RE`, which constrains any edit near it. E-07 must name both classes or it will be discovered mid-execution. | read at `d0b0acab`; `tests/test_selector_zero_open.py:371-440` |
| F-8c | THE PLAN'S OWN SUITE BASELINE IS WRONG IN COUNT AND IN ITS NAMED FAILURE. Re-measured bare on main at `d0b0acab`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`. `tests/test_orchestrator_retirement.py` PASSES (`112 passed`); the single real failure is the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks the repo and trips over another party's untracked `opencode-recovery/`. `tests/test_selector_zero_open.py` is fully green today (34 passed). | measured at `d0b0acab` |
| F-12 | THE `76w6mq` OVERLAP IS A COMPOSITION ORDER CONSTRAINT, NOT MERELY A MERGE HAZARD, AND THIS PLAN DOES NOT MENTION IT AT ALL. Plan `76w6mq` (`idcapture`, `- Status: reviewed`, `Readiness: go-pending-approval`) edits the SAME three readers to bound them to the metadata region. MEASURED at `d0b0acab` on the `27rjro` research doc, which quotes an IPD bullet block in its BODY: the bullet reader on the header returns `uyeko5` (a foreign id6), on the region returns None, and the doc's own YAML `id:` is `27rjro`. Since THIS plan keeps the bullet path FIRST and consults YAML only ON A MISS, executing it ALONE leaves that doc still reporting `uyeko5` (the fallback never runs) and therefore still colliding. Executing `76w6mq` FIRST makes the bullet path miss, after which this plan's fallback yields the correct `27rjro`. The two compose correctly in ONE order only. | measured at `d0b0acab`; `76w6mq` metadata |
| F-13 | THE CONTRACT CHANGE REACHES A MUTATING VERB AND OQ-01 DESCRIBES ONLY `aw find`. `aw archive` accepts a research `<set-id>/<id6>` target and MOVES files. Measured today for research: `reference` -> 5 (substring), `todo` -> 0, `archive` -> 0. After the change the same bare tokens become MATCH_STATUS: 58, 20 and 31 respectively. So a selector that resolves to 0 or 5 files today would resolve to 20-58 on a verb that relocates them, which is a materially different acceptance question from "a query returns more rows". E-06 does not cover this: it proves no NON-research TYPE is perturbed, which is true and is a different claim. | measured at `d0b0acab`; `aw archive --help` |
| F-9 | The module docstring is a 21-line written justification for the current exclusion, so the code documents the opposite of what this plan does until it is rewritten. | `selectors.py:11-31` |
| F-10 | 8 of 113 research `.md` files have no YAML front matter at all (READMEs, an INDEX, a template, a prototype README). They must keep resolving by filename exactly as today; the fallback must not make them errors. | measured at `44d4950d` |

## Proposed changes (ordered, validatable)

1. Add a YAML fallback to the three internal readers, delegating to `research_contract.parse_frontmatter` (E-01).
2. Verify and pin that the bounded 4096-byte header covers every research front-matter block (E-02).
3. Leave the runners' public readers bullet-only, with the reason recorded in a comment (E-03).
4. Normalize backticks and quote pairs on a YAML scalar before comparing, as a guard (E-04).
5. Demonstrate precedence, allow/deny rejection, artifacts-not-mentions, and the single-traversal property all survive (E-05).
6. Prove and pin the zero-effect result for all seven non-research types (E-06).
7. Invert the pinning test, rewrite the module docstring's rationale, and add the changelog entry (E-07).

## Deferred / out of scope (with reason)

- OPTION 2 from the backlog item (leave research filename-only and merely document the limitation in `aw find --help`). Rejected because it preserves the silent wrongness this item was filed for: a user still cannot tell a 5-file answer from a missed 52-file one, and help text is not consulted at the moment of a wrong answer.
- OPTION 3 (route research through `research/INDEX.json` for these rules). Already rejected during `e32j35`'s review and not reopened: it produces the same 5 -> 52 shift while ALSO coupling `find` to manifest freshness, and index drift is routine here.
- HARMONIZING `_STATUS_RE` with `plans_index._META_RE`. A separate, deliberate contract change affecting 24 plans (`selectors.py:112-121`), unrelated to the dialect gap.
- Teaching the YAML dialect to the PUBLIC runner readers. Explicitly decided against in E-03, with the reason recorded in code.
- MIGRATING research to the bullet dialect. That would make 105 files churn and lose the YAML shape the research contract and its index are built on; the resolver is the cheaper and more honest place to absorb the difference.

## Scope check

- Over-scope: `CHANGELOG.md` is in `Scope-Paths` although the backlog item does not name it. It is included because the item states a changelog note is needed for a user-visible contract change, and 5 -> 58 is exactly that.
- Under-scope: research docs with NO front matter (8 of 118, re-measured) keep resolving by filename; nothing is done to give them metadata. The `archive`-is-both-a-status-and-a-directory overlap is now RESOLVED in OQ-02 (status wins over stem/substring, path still wins) and must be pinned rather than redesigned. NOT ADDRESSED AND DELIBERATELY SO: the widened selector's effect on the MUTATING `aw archive` verb is measured and surfaced for the maintainer in OQ-01 rather than mitigated here; if the maintainer chooses option (b) (read verbs only), that is a design change needing its own plan, because this resolver is deliberately ONE resolver and forking it per verb is a contract change.
- ADDITIVE SCOPE-PATHS WIDENING AT EXECUTION (2026-09-23): `tests/test_id_metadata_region.py` was ADDED as a fourth entry. It is a LITERAL FILE PATH, so it is widening-eligible under `ipd_lifecycle.scope_entry_is_literal_file` (verified: True), it is purely additive (no entry removed, no `E-*`/`V-*` requirement text altered), and it is DECLARED here rather than concealed, which is the honest route the additive-widening comparison exists to accept. WHY IT WAS NEEDED: three tests in that file are CHARACTERIZATIONS of the pre-change behavior written by IPD `76w6mq`, and each names THIS plan as the change that would flip it (`test_a_yaml_doc_reads_as_ABSENT_rather_than_as_the_quoted_values`: "Teaching the readers the YAML dialect is a separate change (plan `xo3244`)"; `test_precedence_is_preserved_on_a_filename_present_token`: "by `substring`, not `id6`, because this plan does not teach the reader the YAML dialect"). They went red BY DESIGN, exactly as `tests/test_selector_zero_open.py`'s pinning class did, and the plan simply failed to enumerate them alongside it. Each was updated to assert the new value while keeping its original SUBJECT intact and carrying an `UPDATED BY IPD xo3244` note; none was deleted or weakened. Full reasoning, alternatives, and reversibility in the run's decisions register as decision `37-xo3244-D1`.
- Scope-Paths justification, stated because two of the three entries are unusual: `agent_workflows/selectors.py` holds the three internal readers, the public pair E-03 leaves alone, the precedence tuple and the module docstring E-07 rewrites; `tests/test_selector_zero_open.py` holds BOTH test classes that pin the old contract (`ResearchStaysFilesystemResolvedTests` and `DialectDocumentationTests`); `CHANGELOG.md` carries the user-visible entry. `agent_workflows/research_contract.py` is deliberately NOT declared: E-01 must REUSE `parse_frontmatter` unchanged, so editing it would be the wrong direction, and a needed change there is a scope-widening finding to report.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. RE-MEASURED AT REVIEW on main (HEAD `d0b0acab`): `1 failed, 5958 passed, 3 skipped, 2 xfailed`. The authored baseline `1 failed, 5648 passed` and its named `test_orchestrator_retirement` failure are BOTH WRONG: that module passes (`112 passed`), and the single real failure is the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks the repo and trips over another party's untracked `opencode-recovery/` directory. Do NOT delete that directory to make the suite green; it is not yours. Measure your OWN before-baseline and judge on the DELTA.
- `python3 -m pytest tests/test_selector_zero_open.py` for the focused surface (34 passed at review, so any failure there is yours), plus any `aw find` test module the change touches.
- Before/after resolution comparison for all seven non-research types, produced by re-running the E-06 enumeration and diffing (E-06 is not validated by a passing suite alone). MUST INCLUDE THE TWO `---`-FENCED PROMPTS explicitly, since the authored "zero non-research records are fenced" premise is false and they are the only records whose safety depends on the case-sensitive lookup.
- The live shift demonstrated directly with `python3 -m agent_workflows find research reference | wc -l` before and after. RE-MEASURE THE EXPECTED AFTER VALUE rather than asserting the authored 52; it is 58 at review and the corpus grows.
- THE MUTATING-VERB EXPOSURE demonstrated, not just the read one: paste `aw archive research archive` (or the equivalent selector path) in PREVIEW mode before and after, showing how many files the widened selector would move. Before is 0 for `archive`; after is expected 31. This is the evidence OQ-01 needs and no other item produces it.
- `python3 -m agent_workflows check` must not gain a diagnostic.

## Spec / documentation sync

No `.spec.md` file governs selector precedence or the front-matter dialects, so none is touched and none is declared in `Scope-Paths`. The authoritative documentation for this behavior is the `selectors.py` module docstring (`:11-31`) plus the `resolve()` docstring's precedence list (`:504-523`), both of which E-07 and E-05 keep truthful; `.aw/records/research/README.md` describes the research YAML contract and needs no change because the contract itself is unchanged. `CHANGELOG.md` gets the user-visible entry, since a query returning ten times as many results is a behavior change a user must be able to discover without reading the diff.

## Open questions

### OQ-01: Does the maintainer accept the contract change, which reaches a MUTATING verb and is 5 -> 58, not 5 -> 52?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-303
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION (a), ACCEPT BOTH THE READ AND THE MUTATING SURFACE, WITH A NEW OBLIGATION ON THIS PLAN. It must PROVE, with pasted output, that `aw archive`'s default preview lists the FULL widened set before any move, so the first use shows 31 rather than surprising the operator with it. Three alternatives were declined: read-verbs-only (rejected because there is deliberately ONE resolver, so per-verb dialects fork that design and would be a bigger change than this plan describes), an added match-count confirmation threshold (rejected as new behavior not in the plan, with a threshold the maintainer would have to set), and NO (offered explicitly, since the plan states a no retires it rather than trimming it).
  BOTH OF REVIEW'S CORRECTIONS RE-VERIFIED AT HEAD `7c594929`, not carried over on trust. THE NUMBER IS NOT 52 AND NOT 58-AS-A-CONSTANT: measured across 118 research files, 110 carry a parsable status, distributed `reference` 58, `archive` 31, `todo` 20, `active` 1. The authored 52 is stale and the corpus grows, so the accepted framing is AN ORDER OF MAGNITUDE rather than a fixed figure, and no successor should treat 58 as a pinned expectation.
  THE MUTATING SURFACE IS REAL AND WAS THE DECIDING FACT. `aw archive`'s own help confirms it takes an artifact TYPE or "a research `<set-id>/<id6>` to archive" and performs "a targeted move". Measured TODAY, bare status tokens resolve by filename substring only: `reference` 5, `todo` 7, `archive` 7, `active` 1. After the change the same tokens select 58, 20 and 31. So the consent recorded here is explicitly the WIDER one: the maintainer has accepted that a selector which today relocates at most a handful of files may relocate twenty to fifty-eight. A successor may not cite this answer as covering only the query surface.
  THE BOUNDING AFFORDANCE ALREADY EXISTS, which is why (a) is safe rather than reckless: `aw archive` previews by default and requires `--apply` to move anything (confirmed in its help). The new V-item obligation is to demonstrate that the preview is TRUTHFUL AT THE NEW SCALE, because a preview that under-reports the set would convert the existing safeguard into a false reassurance.
  NOTE `archive` IS BOTH A RESEARCH STATUS AND A DIRECTORY in that tree, which OQ-02 tracks separately. This answer does not settle that ambiguity; whoever executes must not let a status-token match silently mean the directory or vice versa.

### OQ-03: Must `76w6mq` (idcapture) execute BEFORE this plan?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-301
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION (a), DECLARE THE EDGE. `- Item-Dependencies:` on this plan is now `executed:76w6mq`, set with `aw ipd dependencies set xo3244 executed:76w6mq` rather than hand-edited, so a runner holds this item as `dependency-blocked` and reports why instead of dispatching it early. This is the shape the repository already uses for a correctness ordering and it fails closed. Options (b) sequence-by-hand and (c) accept-either-order-with-proof were both declined, (b) because the constraint would live only in review prose and a whole-queue run could still pick the wrong order, (c) because the wrong order's failure is SILENT.
  THE ORDERING CLAIM WAS RE-VERIFIED AT HEAD `7c594929`, NOT TRUSTED FROM REVIEW. On `.aw/records/research/reference/202609/20260905-awmetastore-00-27rjro-where-aw-metadata-should-live.research-prompt.md`: the first bullet-style `- Id:` line found anywhere in the document returns `uyeko5`, while the document's own YAML `id:` is `27rjro`. `uyeko5` is confirmed a REAL FOREIGN ARTIFACT, the executed plan `.aw/records/plans/executed/20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-surface-onto-both-host-runners.ipd.md`. The defect is live, not theoretical: `aw check all` reports `check.id6-collision` against that research document today.
  WHY THE ORDER IS ASYMMETRIC, stated plainly because the earlier phrasing "they compose in one order only" was rejected as vague. With `76w6mq` FIRST: it bounds the three readers to the metadata region, so the bullet path no longer sees the quoted block and returns None, which is precisely the condition this plan's YAML fallback is gated on, so the fallback runs and yields `27rjro`. With THIS PLAN first: the bullet path still finds the quoted `uyeko5`, so it never returns None, so the fallback never fires and the document keeps asserting a foreign id6 until `76w6mq` lands. This plan alone therefore does not fix its own headline case.
  BOTH PLANS READ `- Item-Dependencies: none` BEFORE THIS CHANGE, which is why the hazard was real rather than hypothetical: a runner treats two `none` items as independent and may dispatch them in either order. Only this plan's line was changed; `76w6mq` correctly stays `none` because it depends on nothing.
  NOTE THE EXISTING GATE TEXT IS NOT A SUBSTITUTE, and must not be read as one: telling the executor to "re-read the file at execution time and compose with whatever has landed" is good practice but carries no enforcement, and the review was right that it does not make the wrong order safe.

### OQ-02: Under the preserved precedence, what should the selector `archive` resolve to for research?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IT RESOLVES AS A STATUS TO 31 RECORDS, AND THE PATH RULE STILL WINS FOR AN EXPLICIT PATH. Resolved at review by reading the precedence and measuring the before state, since the question itself says it is resolvable from the code and the plan-review contract forbids leaving such a question for a human. `_PRECEDENCE` is `path -> id6 -> setid -> status -> stem -> substring` (`selectors.py:71-78`, loop at `:601`), so `status` (4th) beats `stem` and `substring` but loses to `path` (1st), which is exactly the behaviour the plan wants: `aw find research archive` answers the status question, while `aw find research .aw/records/research/archive/...` still resolves the path.
  THE BEFORE STATE, MEASURED at `d0b0acab`, is the part worth pinning because it is more surprising than the after: `archive` resolves to ZERO files today (`kind=None`, `paths=0`), not to the directory and not by substring. So this is a 0 -> 31 change, not a re-ranking of an existing answer, and `.aw/records/research/archive/` does exist as a directory. Pin BOTH the before (0) and the after (31) in the E-07 class, since a silent flip is the class of surprise this plan removes.
  THIS FEEDS OQ-01 AND IS WHY THAT QUESTION IS NOW BLOCKING: `aw archive` is a MUTATING verb that accepts a research target, so `archive` going from 0 files to 31 is a selector that starts matching thirty-one documents on a verb that relocates them. The resolution here is about precedence and is settled; the acceptance of that consequence is the maintainer's and lives in OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a Python snippet's output showing, for one real research doc, that `selectors._read_id`, `_read_status` and `_read_setid` each return the YAML value; and for one real plan, that all three return the same values they return at HEAD `44d4950d` (paste both runs). Paste the diff of the three readers showing the bullet regex is still attempted FIRST.
  - Observed evidence: Executed at base HEAD `0823163b` (NOT `44d4950d`; that commit is long superseded, so the BEFORE run below was produced by stashing only `selectors.py` and re-running the identical snippet, which is a stronger comparison than a historical figure).

    AFTER (working tree), on one real research doc and one real plan:

    ```
    RESEARCH 20260905-awmetastore-00-27rjro-where-aw-metadata-should-
       _read_id='27rjro' _read_status='reference' _read_setid='awmetastore'
    PLAN 20260908-selfmdialect-01-xo3244-teach-the-selector-both-
       _read_id='xo3244' _read_status='approved' _read_setid='selfmdialect'
    ```

    BEFORE (same two files, `git stash push -- agent_workflows/selectors.py`, same snippet):

    ```
    RESEARCH: _read_id=None _read_status=None _read_setid=None
    PLAN: _read_id='xo3244' _read_status='approved' _read_setid='selfmdialect'
    ```

    So the research doc goes from all-`None` to its three DECLARED YAML values, and the plan's three reads are BYTE-IDENTICAL across the change, which is the no-perturbation half of E-01.

    `git diff` of the three readers, showing the bullet regex is still attempted FIRST in each (the YAML call is only reached on a miss):

    ```diff
     def _read_id(text: str) -> str | None:
         m = _ID_RE.search(metadata_region(text))
    -    return m.group(1) if m else None
    +    if m:
    +        return m.group(1)
    +    return _read_yaml_scalar(text, "id")

     def _read_status(text: str) -> str | None:
         m = _STATUS_RE.search(metadata_region(text))
    -    return m.group(1) if m else None
    +    if m:
    +        return m.group(1)
    +    return _read_yaml_scalar(text, "status")

     def _read_setid(text: str) -> str | None:
         m = _SET_RE.search(metadata_region(text))
         if not m:
    -        return None
    +        # YAML dialect fallback (IPD `xo3244`); the same first-token rule applies to its value.
    +        yaml_val = _read_yaml_scalar(text, "set")
    +        return _first_set_token(yaml_val) if yaml_val else None
         # The set-id is the first whitespace token before any '(' (mirrors plans_index.set_terse_id).
    -    return m.group(1).split("(")[0].strip().split()[0] if m.group(1).strip() else None
    +    return _first_set_token(m.group(1))
    ```

    BULLET-FIRST IS ALSO PINNED BY A TEST rather than only by reading the diff: `YamlFallbackFiresOnlyOnABulletMissTests::test_a_bullet_record_never_consults_the_yaml_reader` monkeypatches `_read_yaml_scalar` with a spy and asserts the call list is EMPTY for a bullet record.

    THE IMPORT DIRECTION WAS CHECKED as E-01 requires: `research_contract` imports only `artifact_core` and `artifact_naming`, never `selectors`, so there is no cycle. The import is nevertheless done LAZILY inside `_read_yaml_scalar` (with a `text.startswith("---")` pre-filter ahead of it), so no bullet-dialect record pays for it.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the output of a script that, for every file under `.aw/records/research/`, compares `parse_frontmatter(full_text)` with `parse_frontmatter(first_4096_bytes)` and reports the count that differ. The number must be 0. Paste the guard (assertion or comment) added, and state what would happen if a future document violated it.
  - Observed evidence: The script compares BOTH bounds, the literal first 4096 bytes and the window `_read_header` actually returns (they differ, because the read is now a structural chunked read rather than a hard cap, so checking only the constant would have been the weaker test):

    ```
    files=126 parsable_full=119
    differ(full vs first-4096)=0
    differ(full vs _read_header window)=0
    ```

    So ZERO of the 119 documents that parse from their full text fail to parse from either bound. Largest closing `---` fence measured at byte 602, against a 4096-byte first chunk, i.e. the corpus is nearly an order of magnitude inside the bound.

    `_HEADER_CHUNK_BYTES` IS UNCHANGED AT 4096, as E-02 demands, and that is asserted by `YamlFallbackHeaderBoundTests::test_the_chunk_size_is_unchanged_by_this_plan`.

    THE GUARD IS TWO TESTS PLUS A DOCSTRING, not a bare comment. `YamlFallbackHeaderBoundTests::test_every_real_research_doc_parses_from_the_bounded_header` re-runs the comparison above over the LIVE tree on every suite run and fails loudly with the message "a research doc's front matter straddles the bounded header read: it would silently read as having NO metadata". `_read_yaml_scalar`'s docstring records the measurement and states the bound is structural.

    WHAT WOULD HAPPEN IF A FUTURE DOCUMENT VIOLATED IT, stated because this is the load-bearing risk: `parse_frontmatter` returns `None` when it never sees the CLOSING fence, so such a document would read as having NO metadata at all, and the selector would silently fall back to the FILENAME rule for it - the exact silent-miss class this plan exists to remove. It would NOT produce a wrong value, only an absent one, which is the safe direction. That failure MODE is itself pinned by `test_a_STRADDLING_fence_reads_as_absent_rather_than_as_a_wrong_value`, which constructs a 300KB fence and asserts `None` from the truncated text and `'reference'` from the full text. And the corpus test above is what makes the violation LOUD rather than silent.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff` for `read_front_matter_id`/`read_front_matter_status` showing NO behavioral change plus the added explanatory comment, and paste the passing result of whatever test covers those two readers (name it).
  - Observed evidence: THE DIFF IS COMMENT-ONLY. `git diff` around the public pair adds no code line at all; the only change is the recorded decision:

    ```diff
     # long plan whose metadata block outruns one read chunk must not lose its region to a missing `##`,
     # which is why exhaustion means "the region continues" and never an empty region.
    +#
    +# THIS PAIR IS DELIBERATELY LEFT BULLET-ONLY, AND ITS OMISSION FROM THE YAML DIALECT IS A DECISION
    +# RATHER THAN AN OVERSIGHT (IPD `xo3244` E-03). The three INTERNAL readers above now fall back to the
    +# YAML dialect; these two do not. Two reasons. FIRST, no caller can produce the input: a host runner
    +# reads PLAN front matter, which is bullet-dialect by construction, so a YAML branch here would widen
    +# a surface nothing exercises. SECOND, and decisively, this is the ONE reader pair whose failure mode
    +# is documented as SILENTLY DEGRADING a runner to a directory-derived status, so its surface is kept
    +# as narrow as its callers need. If a driver ever has to read a YAML-fenced record, add the fallback
    +# HERE explicitly with its own evidence; do not infer it from the internal readers having one.
     _FRONT_MATTER_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
     _FRONT_MATTER_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
    ```

    Neither `read_front_matter_id` nor `read_front_matter_status` nor either of their two patterns appears as a changed line anywhere in the diff.

    THE COVERING TESTS, named as required. Pre-existing: `tests/test_id_metadata_region.py::PublicReaderTests` (3 tests, including `test_the_two_tiers_still_differ_on_whitespace`). New, added by this plan because the OMISSION otherwise reads as an oversight a later change would "complete": `tests/test_selector_zero_open.py::PublicRunnerReadersStayBulletOnlyTests` (4 tests), which asserts the public pair returns `None` for a YAML record, that the INTERNAL readers by contrast DO read it (the contrast is the point: the two tiers now differ in DIALECT as well as in whitespace tolerance), that the whitespace tolerance is unchanged, and that the reason is discoverable in the source.

    ```
    $ python3 -m pytest tests/test_id_metadata_region.py::PublicReaderTests "tests/test_selector_zero_open.py::PublicRunnerReadersStayBulletOnlyTests" -o addopts="" -q
    .......                                                                  [100%]
    7 passed in 0.16s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a test or snippet output showing a fixture doc with `` set: `topic` `` resolves for the selector `topic`, AND paste the re-measured corpus check confirming zero real docs currently need it (so the guard is honestly labeled a guard). Paste proof the bullet readers were not touched (`git diff` of `_ID_RE`/`_STATUS_RE`/`_SET_RE` showing no change).
  - Observed evidence: THE FIXTURE TEST is `YamlScalarNormalizationTests::test_a_backticked_yaml_set_resolves_for_the_bare_selector`, which writes a research doc whose front matter reads `` set: `topic` `` and asserts `resolve(root, "research", "topic")` returns `MATCH_SETID` on it. Its filename deliberately contains NO occurrence of `topic` (`...-nomatchinname-01-gg0001-a-report...`), so a substring hit cannot make the test pass accidentally. Run together with the pin it must not break:

    ```
    $ python3 -m pytest "tests/test_selector_zero_open.py::YamlScalarNormalizationTests" tests/test_cli_find.py::BacktickSetValueIsPinnedTests -o addopts="" -q
    ........                                                                 [100%]
    8 passed in 0.32s
    ```

    THE CORPUS RE-CHECK CONFIRMS THIS IS A GUARD, NOT A FIX, and it is labelled that way in both the code docstring and the test docstring:

    ```
    parsable docs checked=119  values needing normalization=0
    ```

    Zero of 119 parsable research documents carry a backticked or stray-quoted `id:`/`status:`/`set:` value, so F-7 reproduces at execution: the backlog item's observation was real when made but does not reproduce in the current corpus. E-04 is implemented anyway (it is a few lines and the observation was real), and it is described as a defensive guard rather than as a live-defect fix.

    THE BULLET READERS WERE NOT TOUCHED. `git diff agent_workflows/selectors.py | grep -E "^[-+].*(_ID_RE = |_STATUS_RE = |_SET_RE = |_FRONT_MATTER_ID_RE = |_FRONT_MATTER_STATUS_RE = )"` returns NO lines, i.e. not one of the five patterns appears as an added or removed line. The `_STATUS_RE` PARITY comment is also undisplaced, which `DialectDocumentationTests::test_status_regex_carries_the_parity_note` (asserting the `PARITY` + `plans_index.py` prose still sits within 1200 characters before `_STATUS_RE`) proves independently and which passes.

    THE NORMALIZATION IS CONFINED TO THE YAML DIALECT, which is the half that matters: `test_the_bullet_dialect_is_NOT_normalized` asserts `_read_setid` still returns `` '`awoptimize`' `` VERBATIM for a BULLET record, and `BacktickSetValueIsPinnedTests` (which exists precisely to forbid that normalization, because it would flip a real query from 4 substring hits to 1 setid hit) passes unmodified. `test_an_unbalanced_quote_is_left_alone` pins that only MATCHING pairs are stripped, so a value is never silently mangled.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: four separate pasted demonstrations, one per invariant. (a) A research id6 query's `Resolution.kind` is now `MATCH_ID6` where it was `MATCH_SUBSTRING`, with both runs shown. (b) A denied-kind resolution still returns `rejected_kind` set and empty `paths`. (c) A token appearing only in a document BODY does not match. (d) A timing or call-count measurement showing `_paths()` is walked ONCE for a query that consults both views (an instrumented counter is acceptable; a wall-clock number alone is not, since it is noisy).
  - Observed evidence: Four SEPARATE demonstrations, as required, on the LIVE tree at base HEAD `0823163b`:

    ```
    (a) AFTER  research '27rjro': kind=id6 n=1   [BEFORE was kind=substring n=1]
    (b) denied id6: paths=[] rejected_kind=id6 kind=None
        resolve_for_mutation -> paths=[] err="this verb does not accept a id6 selector: '27rjro'"
    (c) 'uyeko5' as research: kind=None n=0 []
        'uyeko5' as plans:    kind=id6 n=1 ['20260903-runflags-01-uyeko5-wire-the-spe']
    ```

    (a) PRECEDENCE HOLDS AND THE OBSERVABLE CONSEQUENCE IS CAPTURED. `_PRECEDENCE` is byte-identical (asserted by `PreservedInvariantsUnderTheNewDialectTests::test_precedence_is_unchanged` and by the pre-existing `PrecedenceUnchangedTests::test_precedence_tuple_is_frozen`). The intended consequence is exactly the one E-05 predicted: the same FILE, a different winning `kind`, carried on the `Resolution` so callers can apply the kind-aware policy. That is not cosmetic - `id6` is in `UNIQUE_KINDS` and `substring` is not, so this query now routes through the COLLISION policy (never overridable by `--force`) instead of the ambiguity-with-`--force` one. The `path`-beats-`status` case from OQ-02 is pinned separately by `test_an_explicit_PATH_still_outranks_the_new_status_match`.

    (b) ALLOW/DENY REJECTION SEMANTICS INTACT: a match only via a denied kind yields `rejected_kind` set with EMPTY `paths` and `kind=None`, never a silent no-match, and `resolve_for_mutation` turns that into an explicit refusal naming the denied kind.

    (c) ARTIFACTS-NOT-MENTIONS HOLDS, demonstrated on the REAL case rather than a fixture. `uyeko5` is a FOREIGN id6 quoted inside `27rjro`'s body (it is the executed plan `20260903-runflags-01-uyeko5-...`). It resolves to NOTHING as research and to the owning PLAN as plans, so the quotation is not read as a claim. This is also the direct proof that this plan composes correctly with its declared dependency `executed:76w6mq`: the region bound makes the bullet path MISS on that document, and only then does this plan's YAML fallback supply the document's own `27rjro`. Both halves are needed - `aw check all` reports no `check.id6-collision` for it. Additionally `test_a_token_only_in_the_BODY_still_does_not_match` pins that body prose mentioning an id/status/set never matches, and `YamlFallbackFiresOnlyOnABulletMissTests::test_a_yaml_looking_line_in_a_bullet_records_BODY_does_not_match` pins the NEW dialect's version of the same rule (a plan whose body documents the research front-matter format is not read as declaring it).

    (d) SINGLE-TRAVERSAL SURVIVES, measured with an INSTRUMENTED COUNTER, not wall clock, as E-05 requires. `_files()` still derives from `_paths()` (the diff touches neither), and two tests assert opens == distinct opens:

    ```
    $ python3 -m pytest "tests/test_selector_zero_open.py::PreservedInvariantsUnderTheNewDialectTests::test_the_single_traversal_property_survives" "tests/test_selector_zero_open.py::_SanityOnRealRepoTests::test_real_repo_one_traversal_is_shared" -o addopts="" -q
    ..                                                                       [100%]
    2 passed in 0.25s
    ```

    The filename-only rules also still consult `_paths()` and never `_files()`; that is unchanged code, and `FilenameRuleEvaluationIsReadFreeTests` plus `EnumerationsAgreeTests::test_iter_paths_opens_nothing` pass.

    Whole class, all four invariants:

    ```
    $ python3 -m pytest "tests/test_selector_zero_open.py::PreservedInvariantsUnderTheNewDialectTests" -o addopts="" -q
    .....                                                                    [100%]
    5 passed in 0.25s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the before/after output of the per-type enumeration (the `---`-fenced counts), RE-MEASURED rather than copied, and state explicitly that `prompts` is NOT zero (2 at review) so the corrected safety argument is on the record. Paste a diff showing resolution results are identical for `plans`, `specs`, `backlog`, `releases`, `reviews`, `prompts` and `walkthroughs`, INCLUDING the two fenced prompts named individually. Paste the fixture test proving a `---`-fenced NON-research record with a capitalized `Status:` is not matched by the fallback, and the code comment recording why the lookup is case-sensitive. Paste the regression test's name and passing result showing a YAML-looking line in a bullet record's BODY does not trigger the fallback.
  - Observed evidence: THE `prompts` COUNT IS **ZERO** AT EXECUTION, NOT 2, AND THAT IS A CORRECTION TO THIS V-ITEM'S OWN INSTRUCTION RATHER THAN A CONFIRMATION OF IT. Re-measured at base HEAD `0823163b`, enumerating via `selectors._iter_paths` + `_read_header` for ALL TEN resolvable types (the plan and review both said "seven"; the resolver actually serves ten, and the three unexamined ones - `comms`, `roadmaps`, `other` - are checked here too):

    ```
    backlog              567  fenced 0
    comms                7    fenced 0
    other                4    fenced 0
    plans                712  fenced 0
    prompts              17   fenced 0
    releases             1    fenced 0
    research             121  fenced 119
    reviews              273  fenced 0
    roadmaps             1    fenced 0
    specs                36   fenced 0
    walkthroughs         24   fenced 0
    ```

    WHY IT IS 0 AND WHY THAT DOES NOT RESTORE THE AUTHORED "BLAST RADIUS IS ZERO" ARGUMENT. The two `Kind: session-handoff` prompts review measured are simply ABSENT FROM THIS LANE: they lived under `.aw/records/prompts/untracked/`, which `.aw/.gitignore` excludes as `records/*/untracked/`, so they were never committed and an isolated worktree does not have them. That is exactly F-5c's point. The corpus count is therefore NOT the durable guard and must not be cited as one: another checkout has such files, and the next `handoff` run writes a new one. So the safety argument is the one review demanded - THE LOOKUP IS CASE-SENSITIVE - and it is proved by FIXTURE, which holds on every machine, rather than by a count that varies per checkout. The authored premise ("no non-research record is fenced") is still wrong; it merely happens to be unfalsifiable in this particular lane.

    RESOLUTION IS IDENTICAL FOR EVERY NON-RESEARCH TYPE, verified ROW BY ROW rather than by type totals. For each of the 1642 non-research records I recorded the triple `(_read_id, _read_status, _read_setid)` before (with `selectors.py` stashed) and after, then diffed:

    ```
    type                 n    fenced  CHANGED-reader-rows
    backlog              567  0       0
    comms                7    0       0
    other                4    0       0
    plans                712  0       0
    prompts              17   0       0
    releases             1    0       0
    research             121  119     119
    reviews              273  0       0
    roadmaps             1    0       0
    specs                36   0       0
    walkthroughs         24   0       0
    ```

    ZERO changed rows across all ten non-research types (1642 records); all 119 changed rows are research, and the 2 research rows that did NOT change are the two files carrying no front matter at all (`conformance-results-template.md`, `plan-review/20260712-0156-14-chatgpt-modular-report-template.md`), which correctly keep resolving by filename - F-10's requirement that the fallback must not turn them into errors.

    THE TWO FENCED PROMPTS COULD NOT BE NAMED INDIVIDUALLY because they are not present in this lane (see above). The FIXTURE TEST stands in for them and is stronger, since it runs everywhere: `YamlFallbackIsCaseSensitiveTests::test_a_fenced_non_research_record_is_not_matched_by_a_status_query` writes a `---`-fenced `Kind: session-handoff` prompt with `Status: draft` into `.aw/records/prompts/untracked/` ALONGSIDE a bullet prompt also at `draft`, then asserts `aw find prompts draft` returns ONLY the bullet one. Its sibling `test_the_parser_does_see_those_keys_under_their_real_capitalization` is the contrast case that stops the test passing for the wrong reason (it asserts `parse_frontmatter(...)['Status'] == 'draft'` while `.get('status')` is None), so the `None` above is proven to be the LOOKUP and not a broken parse.

    THE CODE COMMENT RECORDING WHY THE LOOKUP IS CASE-SENSITIVE sits immediately above `_read_yaml_scalar` and is itself asserted by `test_the_case_sensitivity_reason_is_recorded_in_the_source` (which greps the source for `CASE-SENSITIVE` and `handoff` within 2500 characters before the function, so a future edit that drops the reason fails):

    > THE KEY LOOKUP IS CASE-SENSITIVE, AND THAT IS THE LOAD-BEARING SAFETY PROPERTY OF THIS CHANGE, NOT A STYLISTIC RESTRICTION. `parse_frontmatter` preserves keys VERBATIM (`key.strip()`, no case folding), and the `---`-fenced records that exist OUTSIDE research are written by the `handoff` workflow with CAPITALIZED keys (`Kind:`, `Status:`, `Date:`). Looking up exactly `id`/`status`/`set` therefore returns None for them, leaving every non-research type's resolution untouched. A tolerant lookup (`.title()`, case folding, or trying variants) would silently make `aw find prompts draft` start matching session-handoff drafts, so DO NOT "robustify" this: the no-perturbation proof for the other nine record types rests on it.

    THE BODY-FALLBACK REGRESSION TEST, named as required, is `YamlFallbackFiresOnlyOnABulletMissTests::test_a_yaml_looking_line_in_a_bullet_records_BODY_does_not_match`: a bullet plan whose BODY contains a complete `---`-fenced research block is asserted to read its OWN `cc0095`/`to-review`/`demo`, and each of the three quoted tokens (`zz9999`, `quotedset`, `quotedstatus`) is asserted to resolve to nothing. The fallback keys on a LEADING fence, so a body block cannot become metadata.

    ```
    $ python3 -m pytest "tests/test_selector_zero_open.py::YamlFallbackIsCaseSensitiveTests" "tests/test_selector_zero_open.py::YamlFallbackFiresOnlyOnABulletMissTests" -o addopts="" -q
    .......                                                                  [100%]
    7 passed in 0.25s
    ```

    ONE MORE INDEPENDENT NO-OP CHECK, since a passing suite alone does not validate E-06: `aw check --agent` before and after is IDENTICAL at 42 findings with the same (rule, location) set - added `[]`, removed `[]`. Only the arbitrary `next` hint differs, which is a display pick among equal findings.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the rewritten test class in full with ALL FOUR original tests carried across, and its passing result. Paste `DialectDocumentationTests`' result too, and if you changed it, say why. Paste the `python3 -m agent_workflows find research reference | wc -l` output BEFORE (5) and AFTER (re-measure; 58 at review, not the authored 52). Paste the `archive` selector's before (0) and after (31) resolution per OQ-02, and the `aw archive` PREVIEW showing the widened mutating-verb exposure per OQ-01. Paste the `git diff` of the `selectors.py` module docstring and the `CHANGELOG.md` entry, whose figure must be the re-measured one. Paste the bare `python3 -m pytest` summary line and compare it to a baseline YOU measured, not to the figure this plan originally cited.
  - Observed evidence: THE CLASS WAS INVERTED, NOT DELETED. `ResearchStaysFilesystemResolvedTests` is now `ResearchResolvesByYamlFrontMatterTests` in `tests/test_selector_zero_open.py`, keeping its FIXTURE byte-for-byte (the two YAML docs) so the before/after comparison is on identical inputs, and its docstring records that the class pinned the opposite contract and why that contract was wrong. ALL FOUR original tests are carried across:

    1. `test_research_has_no_bullet_id` - KEPT, still true, and now documents that the FALLBACK (not the bullet path) is what matches. Its body was retargeted from `_read_id` to `_ID_RE.search(metadata_region(...))`, because `_read_id` deliberately no longer returns None here; the assertion it makes (a research doc carries no bullet `- Id:`) is the same one.
    2. `test_research_id6_resolves_by_filename_substring_not_id6` -> `test_research_id6_resolves_by_its_yaml_id_not_by_filename_substring`. INVERTED: `MATCH_SUBSTRING` becomes `MATCH_ID6`, same FILE, plus a new assertion that the kind is now in `UNIQUE_KINDS`.
    3. `test_research_status_query_does_not_see_yaml_status` -> `test_research_status_query_sees_the_yaml_status`. INVERTED: `got.paths == []` becomes both fixture docs via `MATCH_STATUS`.
    4. `test_research_status_query_opens_zero_files_when_it_is_a_filename_miss` - CARRIED ACROSS UNCHANGED (the fourth test F-8b caught; it survives the change and belongs to the inverted class).

    Two tests were ADDED to it: `test_research_setid_resolves_by_its_yaml_set` (the third content rule, which the old class could not cover because it could never fire, including an assertion that a Set stays MULTI-target and does not become a collision) and `test_a_document_with_no_front_matter_at_all_still_resolves_by_filename` (F-10: the 7 of 126 research files with no front matter must not become errors).

    `DialectDocumentationTests` WAS CHANGED, AND HERE IS WHY. It did NOT go red: it asserts the module docstring CONTAINS `"YAML front matter"` and `"research"`, never which way the decision went, and my rewrite keeps both phrases, so all three of its tests passed unmodified. I added one test rather than repairing one, because the existing assertions were too weak to catch the exact failure E-07 exists to prevent: the phrases alone are equally satisfied by prose still claiming research is deliberately EXCLUDED. `test_module_docstring_no_longer_claims_research_is_excluded` asserts the docstring contains `BOTH DIALECTS` and does NOT contain `RESEARCH INDEX IS DELIBERATELY NOT WIRED IN`, so the code cannot drift back to documenting the opposite of what it does. Its sibling `test_status_regex_carries_the_parity_note` (the `_STATUS_RE` PARITY prose within 1200 characters) passes untouched, confirming nothing near that comment was displaced.

    ```
    $ python3 -m pytest "tests/test_selector_zero_open.py::ResearchResolvesByYamlFrontMatterTests" "tests/test_selector_zero_open.py::DialectDocumentationTests" -o addopts="" -q
    ..........                                                               [100%]
    10 passed in 0.27s
    ```

    THE LIVE SHIFT IS 5 -> 64 AT EXECUTION, not the authored 52 and not review's 58. Re-measured, not copied:

    ```
    BEFORE $ python3 -m agent_workflows find research reference | wc -l
    5
    AFTER  $ python3 -m agent_workflows find research reference | wc -l
    64
    ```

    Full research status distribution over 121 records (119 parsable): `reference` 64, `archive` 32, `todo` 19, `active` 4. The corpus grows continuously, so treat this as AN ORDER OF MAGNITUDE and not as a pinned figure; no test asserts 64.

    THE `archive` SELECTOR PER OQ-02 IS 0 -> 32 (review predicted 31; re-measured):

    ```
    BEFORE  'archive': kind=None      n=0      'reference': kind=substring n=5   'todo': kind=None n=0
    AFTER   'archive': kind=status    n=32     'reference': kind=status    n=64  'todo': kind=status n=19
    ```

    Both the before (0, `kind=None` - not the directory and not a substring) and the after (32, via `MATCH_STATUS`) are pinned, together with the `path`-still-wins half, by `PreservedInvariantsUnderTheNewDialectTests::test_an_explicit_PATH_still_outranks_the_new_status_match`.

    THE `aw archive` PREVIEW PER OQ-01: THE PREDICTED MUTATING-VERB EXPOSURE DOES NOT EXIST, AND THAT IS A CORRECTION TO OQ-01/F-13 RATHER THAN A CONFIRMATION. OQ-01 accepted a widened mutating surface and obliged me to prove the preview lists the full widened set. I could not prove that, because it does not happen: `aw archive` NEVER ROUTES THROUGH THIS RESOLVER. `research_archive.py` imports `selectors` zero times and matches with its own private loop over `_all_docs()` comparing `parsed.id6 == target or parsed.set_id == target` against the PARSED FILENAME (`research_archive.py:305-312`). Measured before and after, with only `selectors.py` stashed for the BEFORE column:

    ```
                                          BEFORE                          AFTER
    aw archive research archive      no research doc or set matches   no research doc or set matches   (identical)
    aw archive research reference    no research doc or set matches   no research doc or set matches   (identical)
    aw archive research todo         no research doc or set matches   no research doc or set matches   (identical)
    aw archive research awmetastore  7 'would archive' lines          7 'would archive' lines          (identical)
    aw rename  research reference    error: no research file has id6  error: no research file has id6  (identical)
    aw group   research reference    error: no research file has id6  error: no research file has id6  (identical)
    aw find    research reference    5 rows                           64 rows                          (CHANGED)
    ```

    So `aw find` is the ONLY verb whose behavior this change alters; every MUTATING research verb is byte-identical. The maintainer's OQ-01 consent was therefore broader than the change actually needed, which is the safe direction. The resolver-bypass is itself a real defect - `selectors.py:4-9` claims "every verb ... routes selector resolution through `resolve()` here, so the SAME selector resolves to the SAME file for every verb", which is false for research - and it is FILED as backlog `mblu3p` (`bug`, `Blocks-Release: next`) rather than fixed here, since fixing it would deliver exactly the 0 -> 32 mutating widening OQ-01 approved and that deserves its own evidence. NOTE FOR WHOEVER TAKES `mblu3p`: OQ-01's recorded consent already covers that consequence.

    THE MODULE DOCSTRING DIFF replaces the 21-line e32j35 E-06 justification for the exclusion (which would otherwise make the code document the opposite of what it does) with prose describing both dialects, why the exclusion was reversed (the 5-vs-64 silent under-report), and the two ways the YAML reader is deliberately narrow:

    ```diff
    -FRONT-MATTER DIALECT: WHY THE RESEARCH INDEX IS DELIBERATELY NOT WIRED IN HERE (IPD e32j35 E-06).
    -Two of the ten artifact types ship a generated manifest (`plans/INDEX.json`, `research/INDEX.json`)
    -whose columns look like exactly what the id6/setid/status rules need. For RESEARCH that appearance
    -is false, and reading it would CHANGE what `aw find research` matches:
    -  * this resolver only understands the BULLET dialect ...
    -  * measured 2026-09-01: 0 of 103 research files carry a `- Id:` bullet while 101 carry a YAML `id:`.
    -  * consequently a status query is filename-shaped too: `aw find research reference` matches 5 files
    -    by filename, whereas `research/INDEX.json` holds 52 entries with `status: reference`. ...
    -That order-of-magnitude shift is a SEMANTIC change ... Research therefore stays on the
    -filesystem scan, and the underlying dialect gap is tracked as its own backlog item ...
    +FRONT-MATTER DIALECT: THE CONTENT READERS SPEAK BOTH DIALECTS, BULLET FIRST (IPD `xo3244`, which
    +REVERSED the deliberate exclusion IPD e32j35 E-06 had documented here). ...
    +WHY THE EXCLUSION WAS REVERSED ... Speaking only the bullet dialect did not make research
    +resolution CONSERVATIVE, it made it SILENTLY WRONG ... `aw find research reference` returned 5
    +records while 64 documents carried `status: reference` ...
    +THE YAML READER IS DELIBERATELY NARROW IN TWO WAYS ... The key lookup is CASE-SENSITIVE ... And the
    +PUBLIC runner-facing readers below ... stay bullet-only.
    ```

    The still-standing caution about the PLANS index (the `_STATUS_RE` parity note, which this change does not touch) is deliberately RETAINED.

    THE CHANGELOG ENTRY carries the RE-MEASURED figures (5 -> 64, plus 32 and 19 for the two statuses that returned nothing at all), states plainly that larger result sets are the correction rather than a regression, records that all 1642 non-research records resolve byte for byte as before, and says explicitly that no file-moving command changes behavior and that this was CHECKED rather than assumed. It is written for a user, with no em or en dashes.

    THE BARE SUITE, against a baseline I MEASURED MYSELF on this lane at base HEAD `0823163b` before touching anything:

    ```
    BEFORE $ python3 -m pytest
    3 failed, 9069 passed, 3 skipped, 2 xfailed, 6 warnings in 409.39s (0:06:49)

    AFTER  $ python3 -m pytest
    3 failed, 9097 passed, 3 skipped, 2 xfailed, 6 warnings in 165.13s (0:02:45)
    ```

    DELTA: +28 passed (the tests this plan adds), and the SAME 3 failures. NOTE THAT THE PLAN'S OWN BASELINE IS WRONG TOO: it cites `1 failed, 5958 passed` and names `test_reporting_contract.py` as the failure. Neither holds here. The three failures on this lane are `tests/test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd`, `tests/test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd`, and `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. All three are PROVEN pre-existing and unrelated: re-run with my four changed files stashed at base HEAD, all three still fail identically (`3 failed in 1.96s`), and none touches the resolver (two are runner-symbol-location assertions, one is a permission-policy scope assertion; the last is already filed as backlog `j08jky`). `tests/test_reporting_contract.py` passes here.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS NOT APPROVABLE AS IT STANDS, and the refusal is mechanical rather than a matter of taste. Two open questions carry `- Blocking: yes` (OQ-01 and OQ-03), so `plan_readiness.has_unresolved_blocking_question` returns True and `aw set approved` will refuse at every lint checkpoint from `author` onward. Both need a maintainer decision, both are stated with costed options and a recommendation, and neither is a reviewer's to make: OQ-01 is a risk-appetite call about a DESTRUCTIVE verb, and OQ-03 is a scheduling decision between two independently-approvable plans. The authoring note was right that OQ-01 must be settled with the review; review's contribution is that it is BIGGER than the plan said and therefore blocking rather than advisory.

THE APPROACH IS SOUND AND REVIEW RE-VERIFIED IT. The defect reproduces exactly (`aw find research reference` returns 5 while 58 docs carry `status: reference`), the silent-fallthrough diagnosis is correct, reusing `parse_frontmatter` rather than writing a second YAML reader is right, keeping the public runner readers bullet-only is right, and the bounded 4096-byte header genuinely suffices (0 of 110 parsable docs straddle it). What changed is the evidence around the edges, not the design.

FOUR CORRECTIONS NOT TO INHERIT FROM THIS PLAN'S EARLIER TEXT. (1) THE BLAST RADIUS OUTSIDE RESEARCH IS NOT ZERO: two `Kind: session-handoff` prompts under `.aw/records/prompts/untracked/` ARE `---`-fenced, and what protects them is that their keys are CAPITALIZED plus a case-SENSITIVE lookup, not the absence of fenced records. E-01 must make the lookup case-sensitive deliberately and comment why; E-06 must prove the new claim. (2) The shift is 5 -> 58, not 5 -> 52, and the corpus is 118 files with 110 parsable; re-measure. (3) The suite baseline is `1 failed, 5958 passed, 3 skipped, 2 xfailed` and the failing test is the environmental `test_reporting_contract.py` case, NOT `test_orchestrator_retirement`, which passes. (4) E-07's target has a FOURTH test, and a SECOND class (`DialectDocumentationTests`) asserts the very docstring phrases E-07 rewrites.

THE `76w6mq` INTERACTION IS AN ORDERING CONSTRAINT, NOT JUST A MERGE HAZARD (OQ-03). Because this plan tries the bullet regex FIRST and consults YAML only on a MISS, running it alone leaves the `27rjro` research doc still reporting a FOREIGN id6 (`uyeko5`) harvested from a quoted block, so the collision that breaks `aw set` survives. `76w6mq` bounds the readers to the metadata region, which makes the bullet path miss and lets this plan's fallback return the correct `27rjro`. Measured both ways. The two compose in ONE order only.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Do NOT delete the untracked `opencode-recovery/` directory that makes one suite test fail; it belongs to another party in this shared checkout. Do NOT edit `research_contract.py`: `parse_frontmatter` must be reused unchanged, and a needed change there is a finding to report. Re-read `selectors.py` at execution time and compose with whatever has landed rather than trusting the line numbers cited here. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
