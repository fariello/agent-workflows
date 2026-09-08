# IPD: Teach the selector both front-matter dialects so research metadata is matchable

- Date: 2026-09-08
- Kind: child
- Concern: `selectors.py` is the ONE selector-to-file resolver for every verb and understands only the BULLET front-matter dialect (`- Id:`, `- Status:`, `- Set:`). Research docs use YAML front matter instead, so for research the three content-derived rules MATCH_ID6 / MATCH_SETID / MATCH_STATUS never fire at all, and every research query silently falls through to MATCH_SUBSTRING, the explicit last-resort FILENAME rule. The failure is silent and plausible-looking rather than an error: `aw find research reference` returns 5 files matched by filename while 52 research docs actually carry `status: reference`, and nothing in the output signals that the metadata was never consulted.
- Scope: Make the resolver's three front-matter readers understand the YAML dialect in addition to the bullet dialect, so research id6/setid/status become matchable, and ACCEPT the resulting contract change deliberately (`aw find research reference` goes from 5 results to 52). Reuse `research_contract.parse_frontmatter` rather than writing a second YAML reader. Preserve the documented precedence chain, the bounded header read, the artifacts-not-mentions rule, and byte-for-byte identical behavior for every non-research type. Replace the test that pins today's filename-only behavior with one that pins the new behavior, and record the change in the changelog because it is user-visible.
- Scope-Paths: agent_workflows/selectors.py, tests/test_selector_zero_open.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Set: selfmdialect
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xo3244
- From-Backlog: 05aqbj
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `05aqbj`, inheriting its `Blocks-Release: next` gate. THE ITEM ASKS THE AUTHOR TO PICK ONE OF THREE OPTIONS; this plan picks OPTION 1 (teach the resolver both dialects), which the item itself calls the recommended shape, and states the 5 -> 52 consequence as an accepted contract change rather than a side effect. OQ-01 hands that acceptance to the maintainer explicitly, because it is theirs to make and not the executor's. Every measurement in the item was RE-VERIFIED at HEAD `44d4950d` and all of it reproduces, with the counts slightly moved by the corpus growing since 2026-09-01: `aw find research reference` returns 5 lines today, while parsing front matter over the same tree gives `reference: 52, archive: 31, todo: 21, active: 1` across 105 YAML-parsable docs. TWO NEW MEASUREMENTS THAT MATERIALLY DE-RISK THE WORK, both of which the item could not have known. FIRST, the blast radius outside research is provably ZERO: I enumerated every candidate the resolver walks for all eight status-carrying types and counted how many begin with a `---` fence, giving `plans 0/527, specs 0/28, backlog 0/158, releases 0/1, reviews 0/69, prompts 0/16, walkthroughs 0/17, research 105/107`. No non-research record can take the new branch, so this cannot perturb `aw find plans` or any mutating verb's resolution. SECOND, the item's warning to NORMALIZE QUOTING (a `set:` value reading `` `awoptimize` `` with backticks) does NOT reproduce anywhere in the current corpus: I checked every parsed value for backticks and for stray quotes and found zero anomalies. E-04 still normalizes, because the warning came from a real observation and a defensive strip is nearly free, but it is now a guard rather than a fix for a live defect, and the plan says so instead of claiming a bug it cannot demonstrate.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a research status or id6 query answer the question the user asked. The specific harm being removed is silent under-reporting: a reader cannot tell a genuine 5-file answer from a 52-file answer whose metadata was never read, so two records with identical metadata resolve differently based only on which dialect their type happens to use.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read the second dialect

- [ ] E-01 Add a YAML-dialect fallback to the three internal front-matter readers `_read_id` (`selectors.py:246-248`), `_read_status` (`:251-253`) and `_read_setid` (`:305-310`), so each tries its existing bullet regex FIRST and, only on a miss, consults the YAML block. Keep the bullet path first and unchanged so no currently-matching record changes its answer. DELEGATE THE YAML PARSE to `research_contract.parse_frontmatter` (`research_contract.py:518-543`); do NOT write a second YAML reader, or the two will drift about what counts as valid front matter. Note the import direction: `selectors.py` currently imports the naming authority and `layout`, and its module docstring records that the naming authority never imports it; check that adding a `research_contract` import creates no cycle, and if it does, import it lazily inside the function rather than restructuring either module.
  - Depends on: none
  - Expected outcome: given the text of a research doc, `_read_id` returns its `id:`, `_read_status` its `status:`, and `_read_setid` its `set:` first token; given the text of a plan, all three return exactly what they return at HEAD `44d4950d`.
  - Execution state: pending

- [ ] E-02 Confirm the bounded header read is sufficient for the YAML dialect and do NOT enlarge it. `_read_header` reads at most `_HEADER_BYTES` = 4096 (`selectors.py:317-330`), and the item asserts that is enough for a YAML block too. VERIFIED at HEAD `44d4950d` and this item exists to keep it verified rather than assumed: parsing the first 4096 bytes of every research doc yields the SAME result as parsing the whole file for all 105 YAML-parsable docs (0 documents parse from the full text but fail from the header). Note WHY the check is not trivial: `parse_frontmatter` returns `None` when it never sees the closing `---` fence (`research_contract.py:542-543`), so a document whose front matter straddles the 4096-byte boundary would silently read as having NO metadata, which is the exact silent-miss class this plan exists to remove. Add an assertion or comment pinning the relationship so a future front-matter growth spurt fails loudly rather than degrading.
  - Depends on: E-01
  - Expected outcome: no change to `_HEADER_BYTES`, plus evidence that every research doc's front matter closes inside it, and a guard that makes a future violation visible.
  - Execution state: pending

- [ ] E-03 Leave the PUBLIC readers `read_front_matter_id` (`:288-295`) and `read_front_matter_status` (`:298-305`) BULLET-ONLY, and say why in a comment next to them. These are the runners' shared readers (`oc_runipd` and `agy_runipd` call them; the long note at `:255-282` records that they exist precisely so there is one definition per reader and that they use a deliberately LOOSER whitespace pattern than the internal readers). A driver reads PLAN front matter, never research, so teaching them YAML adds a dialect no caller can produce while widening the surface of the one pair of readers whose failure mode is documented as silently degrading a runner to a directory-derived status. Keeping them narrow is a decision, so record it rather than leaving a reader to wonder whether it was an oversight.
  - Depends on: E-01
  - Expected outcome: the public readers are unchanged in behavior, and a comment states that the YAML dialect is deliberately not wired into them and why.
  - Execution state: pending

- [ ] E-04 Normalize a YAML scalar before comparing: strip surrounding backticks and matching quote pairs. THE HONEST STATUS OF THIS ITEM: the backlog item reports observing a `set:` value written `` `awoptimize` `` with backticks during e32j35's maintainer session, and warns that comparing raw produces a phantom mismatch. That does NOT reproduce in the current corpus. Measured at HEAD `44d4950d` across all 105 YAML-parsable research docs, checking every front-matter value for a backtick or for a value that differs from itself with quotes stripped: ZERO anomalies. So this is a defensive guard against a form the corpus once held, not a fix for a live defect, and it must not be described as the latter. Implement it anyway (it is a two-line strip and the observation was real), and apply it consistently to id, status and setid. Do NOT extend the normalization to the BULLET readers: `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT that deliberately disagrees with `plans_index._META_RE` on 24 records (`selectors.py:112-121`), and loosening it would change what `aw find plans` matches.
  - Depends on: E-01
  - Expected outcome: a research doc whose `set:` reads `` `topic` `` resolves for the selector `topic`; bullet-dialect matching is byte-for-byte unchanged.
  - Execution state: pending

### Task group 2: hold the contracts that must not move

- [ ] E-05 Prove and preserve the invariants the resolver's docstring makes, none of which this change may quietly alter. (a) PRECEDENCE stays `path -> id6 -> setid -> status -> stem -> substring` (`_PRECEDENCE`, `selectors.py:71-78`; the loop at `:601-613`). Note the OBSERVABLE CONSEQUENCE the tests must capture: a research id6 query that returns MATCH_SUBSTRING today will return MATCH_ID6 afterwards, which is the intended change, and the winning `kind` is carried on the `Resolution` where callers can apply the kind-aware ambiguity policy. (b) The `allow`/`deny` rejection semantics stay intact: a match only via a denied kind must remain an explicit `rejected_kind` rejection with empty `paths`, never a silent no-match (`:604-607`). (c) The ARTIFACTS-NOT-MENTIONS rule holds: front matter only, never body text, which the bounded header read plus the anchored patterns already enforce. (d) The single-traversal performance property survives: `_files()` must keep deriving from `_paths()` rather than walking again (`:551-566`; the docstring records 83ms vs 50ms on 469 plans when it walked twice), and the filename-only rules must keep consulting `_paths()` and never `_files()` (`:591-598`).
  - Depends on: E-01, E-04
  - Expected outcome: each of (a)-(d) demonstrated individually rather than asserted collectively.
  - Execution state: pending

- [ ] E-06 Show the change cannot perturb any NON-research type, and pin that with a test. This is measurable rather than arguable, and it is the single strongest reason option 1 is safe: a record can only take the new branch if its header opens a `---` fence, and no non-research record does. MEASURED at HEAD `44d4950d` by enumerating the resolver's own candidate list per type and counting `---`-fenced headers: `plans 0/527`, `specs 0/28`, `backlog 0/158`, `releases 0/1`, `reviews 0/69`, `prompts 0/16`, `walkthroughs 0/17`, `research 105/107`. Re-run that enumeration after the change and confirm resolution is identical for the non-research types. Pin it with a test that a bullet-dialect record still resolves via the bullet path even if a YAML-looking line appears in its body, so the fallback cannot start reading bodies.
  - Depends on: E-05
  - Expected outcome: identical resolution for all seven non-research types before and after, plus a regression test that the YAML fallback never fires on a bullet record.
  - Execution state: pending

### Task group 3: replace the test that pins the old contract, and disclose the change

- [ ] E-07 Rewrite `tests/test_selector_zero_open.py::ResearchStaysFilesystemResolvedTests` (`:371-416`), which EXISTS TO PIN TODAY'S BEHAVIOR and will go red by design. Its three tests are `test_research_has_no_bullet_id` (`:398-399`), `test_research_id6_resolves_by_filename_substring_not_id6` (`:401-409`, asserting `MATCH_SUBSTRING` with the message "a MATCH_ID6 here would mean the YAML dialect was wired in, which changes results"), and `test_research_status_query_does_not_see_yaml_status` (`:411-415`, asserting `got.paths == []` for the selector `reference`). DO NOT DELETE THE CLASS: invert it, keeping its fixture (two YAML docs, `:378-393`) and renaming it to describe the new contract, so the corpus retains the record that this behavior was changed deliberately. The first test stays TRUE as written (a research doc genuinely has no bullet `- Id:`) and should be kept to document that the fallback, not the bullet path, is what now matches. Update the module docstring's E-06 rationale at `selectors.py:11-31`, which currently explains at length why research is deliberately NOT wired in; leaving that prose in place would make the code lie about itself.
  - Depends on: E-06
  - Expected outcome: the class asserts the new contract (research resolves via MATCH_ID6 / MATCH_STATUS / MATCH_SETID), the module docstring no longer claims research is deliberately excluded, and the changelog carries a user-visible entry stating that `aw find research <status>` now matches front matter and returns more results.
  - Execution state: pending

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
| F-3 | The true count is an order of magnitude higher: parsing front matter over the same tree gives `reference: 52, archive: 31, todo: 21, active: 1` across 105 YAML-parsable docs of 113 `.md` files. | measured via `research_contract.parse_frontmatter` over `.aw/records/research/**/*.md` at `44d4950d`; `research/INDEX.json` independently holds 105 entries with the same distribution |
| F-4 | The failure is SILENT, which is what makes it a bug rather than a limitation: the status rule does not error, it falls through to the filename rule and returns a plausible short list. | `_PRECEDENCE` loop `:601-613`; `MATCH_SUBSTRING` documented as the explicit last resort at `:515` |
| F-5 | BLAST RADIUS OUTSIDE RESEARCH IS ZERO, measured rather than argued. Candidates whose header opens a `---` fence, per type: `plans 0/527`, `specs 0/28`, `backlog 0/158`, `releases 0/1`, `reviews 0/69`, `prompts 0/16`, `walkthroughs 0/17`, `research 105/107`. | enumerated via `selectors._iter_paths` + `selectors._read_header` at `44d4950d` |
| F-6 | The 4096-byte header read is sufficient: 0 research docs parse from the full text but fail from the first 4096 bytes. The check matters because `parse_frontmatter` returns `None` on a missing closing fence, so a straddling block would read as no-metadata. | measured at `44d4950d`; `research_contract.py:542-543` |
| F-7 | THE ITEM'S QUOTING WARNING DOES NOT REPRODUCE. Zero of 105 parsed docs carry a backticked or stray-quoted `id:`/`status:`/`set:` value. E-04 is therefore a defensive guard, not a live-defect fix, and must not be sold as the latter. | measured at `44d4950d` over every parsed front-matter value |
| F-8 | A test currently PINS the behavior this plan changes, and its own assertion message says so. It must be inverted, not deleted. | `tests/test_selector_zero_open.py:371-416`, notably `:401-409` and `:411-415` |
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

- Over-scope: `CHANGELOG.md` is in `Scope-Paths` although the backlog item does not name it. It is included because the item states a changelog note is needed for a user-visible contract change, and 5 -> 52 is exactly that.
- Under-scope: research docs with NO front matter (8 of 113) keep resolving by filename; nothing is done to give them metadata. The `archive`-is-both-a-status-and-a-directory overlap noted in Step 0 is analyzed and pinned but not redesigned.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` at authoring time is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_selector_zero_open.py` for the focused surface, plus any `aw find` test module the change touches.
- Before/after resolution comparison for all seven non-research types, produced by re-running the E-06 enumeration and diffing (E-06 is not validated by a passing suite alone).
- The live 5 -> 52 shift demonstrated directly with `python3 -m agent_workflows find research reference | wc -l` before and after.
- `python3 -m agent_workflows check` must not gain a diagnostic.

## Spec / documentation sync

No `.spec.md` file governs selector precedence or the front-matter dialects, so none is touched and none is declared in `Scope-Paths`. The authoritative documentation for this behavior is the `selectors.py` module docstring (`:11-31`) plus the `resolve()` docstring's precedence list (`:504-523`), both of which E-07 and E-05 keep truthful; `.aw/records/research/README.md` describes the research YAML contract and needs no change because the contract itself is unchanged. `CHANGELOG.md` gets the user-visible entry, since a query returning ten times as many results is a behavior change a user must be able to discover without reading the diff.

## Open questions

### OQ-01: Does the maintainer accept the 5 -> 52 contract change on `aw find research <status>`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking authoring, but it IS the decision this plan exists to surface, and the backlog item filed it precisely so the call would be made deliberately rather than as a side effect of a performance change. The plan proceeds on the item's own recommendation (option 1) and makes the shift loud: E-07 puts it in the changelog and inverts the test that pinned the old answer. If the maintainer prefers option 2 (document the limitation instead), this plan should be retired rather than trimmed, because option 2 shares none of its implementation. The evidence for accepting: the current answer is not merely narrower, it answers a different question than the one asked, and gives no signal that it did so.

### OQ-02: Under the preserved precedence, what should the selector `archive` resolve to for research?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY THE EXECUTOR FROM THE CODE, recorded so the answer is deliberate rather than emergent. `archive` is both a research STATUS (31 docs measured) and a DIRECTORY in the research tree, and the preserved precedence puts `status` (4th) ahead of `stem` (5th) and `substring` (6th) but behind `path` (1st). So a bare `archive` token should resolve as a status to the 31 records, while the path rule still wins for an explicit path. Confirm by running it and pin whichever answer is chosen in the E-07 test class, since a silent flip here would be the same class of surprise this plan removes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python snippet's output showing, for one real research doc, that `selectors._read_id`, `_read_status` and `_read_setid` each return the YAML value; and for one real plan, that all three return the same values they return at HEAD `44d4950d` (paste both runs). Paste the diff of the three readers showing the bullet regex is still attempted FIRST.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the output of a script that, for every file under `.aw/records/research/`, compares `parse_frontmatter(full_text)` with `parse_frontmatter(first_4096_bytes)` and reports the count that differ. The number must be 0. Paste the guard (assertion or comment) added, and state what would happen if a future document violated it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff` for `read_front_matter_id`/`read_front_matter_status` showing NO behavioral change plus the added explanatory comment, and paste the passing result of whatever test covers those two readers (name it).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a test or snippet output showing a fixture doc with `` set: `topic` `` resolves for the selector `topic`, AND paste the re-measured corpus check confirming zero real docs currently need it (so the guard is honestly labeled a guard). Paste proof the bullet readers were not touched (`git diff` of `_ID_RE`/`_STATUS_RE`/`_SET_RE` showing no change).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: four separate pasted demonstrations, one per invariant. (a) A research id6 query's `Resolution.kind` is now `MATCH_ID6` where it was `MATCH_SUBSTRING`, with both runs shown. (b) A denied-kind resolution still returns `rejected_kind` set and empty `paths`. (c) A token appearing only in a document BODY does not match. (d) A timing or call-count measurement showing `_paths()` is walked ONCE for a query that consults both views (an instrumented counter is acceptable; a wall-clock number alone is not, since it is noisy).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the before/after output of the per-type enumeration (the `---`-fenced counts) AND a diff showing resolution results are identical for `plans`, `specs`, `backlog`, `releases`, `reviews`, `prompts` and `walkthroughs`. Paste the new regression test's name and passing result showing a YAML-looking line in a bullet record's BODY does not trigger the fallback.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the rewritten test class in full, its passing result, the `python3 -m agent_workflows find research reference | wc -l` output BEFORE (5) and AFTER (expected 52), the `git diff` of the `selectors.py` module docstring, and the `CHANGELOG.md` entry. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. OQ-01 is a maintainer decision that a reviewer should settle at the same time, since a NO on it retires this plan rather than reshaping it.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
