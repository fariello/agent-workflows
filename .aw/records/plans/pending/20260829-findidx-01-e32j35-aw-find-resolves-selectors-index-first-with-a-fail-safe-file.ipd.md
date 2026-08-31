# IPD: aw find resolves selectors index-first with a fail-safe filesystem fallback, so it stops reading record bodies

- Date: 2026-08-29
- Kind: child
- Concern: `aw find` reads record file bodies to resolve selectors, which is both the wrong division of labour and part of its remaining cost. Per their own help, `aw find` resolves 'by selector (id6, status, Set, filename fragment)' while `aw search` searches 'for matching content (regex-enabled)' - yet find's `selectors._iter_files` opens every candidate record to regex out three front-matter bullets (`- Id:`, `- Status:`, `- Set:`) for the MATCH_ID6/MATCH_SETID/MATCH_STATUS rules (selectors.py:411-418). The awfindperf pass (a3954ed) cut generic find from 7.47s to ~0.8s by bounding those reads to a 4KB header and pruning excluded directories, but that mitigates the architecture rather than fixing it: the RESOLVER still stats and opens hundreds of files to answer a question the index already answers. `.aw/records/plans/INDEX.json` carries exactly the needed fields per entry (`plan_id`, `set_id`, `status`, `path`; 394 entries as measured 2026-08-29), so the id6/setid/status rules are an index lookup with ZERO file reads. SCOPE HONESTY (added in review, PR-001): the CLI's display layer is a SECOND, larger reader that this plan does NOT fix - `cli._find_type_records` calls `plans_index.scan_plans` (cli.py:6590), whose `p.read_text()` is an UNBOUNDED full-file read of every plan (plans_index.py:100). Measured: `aw find plans e32j35` opens 394 distinct record files, 788 open() calls in total, because the resolver and the display layer each scan the tree independently. This plan owns the RESOLVER half only; see Deferred for the display half.
- Scope: Make selector resolution INDEX-FIRST with a FAIL-SAFE FILESYSTEM FALLBACK, never index-only, for the PLANS type (the one indexed type whose index is semantically parity-capable; see Deferred for research). Resolve MATCH_ID6/MATCH_SETID/MATCH_STATUS from the index when it is trustworthy; if the index is missing, unparseable, or judged stale, fall back to today's bounded-header filesystem scan and still return the correct answer. MATCH_PATH/MATCH_STEM/MATCH_SUBSTRING already need no file contents (they match on the path/filename) and must stop being fed file text at all. Add the staleness signal the index currently lacks so 'is the index trustworthy?' is a cheap deterministic check rather than a guess. Out of scope: changing what `aw find` MATCHES (precedence and semantics are frozen, and PARITY between the index path and the fallback path is the hard invariant), changing `aw search`, the CLI display layer's own re-scan, and building indexes for the eight types that do not have one.
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/plans_index.py, tests/, .aw/records/plans/README.md, .gitignore, .aw/records/backlog/open/
- Item-Dependencies: none
- Status: approved
- Set: findidx
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: e32j35
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007 (5 blockers) fixed in place; OQ-03 open (blocking, maintainer scope call)
- 2026-08-29 to-review (aw set): Authored review-ready: aw find should resolve id6/setid/status from the per-type index when fresh, with a non-removable filesystem fallback. Index-only is explicitly rejected: aw check plans reported a stale index TWICE on 2026-08-29, so index-only would have been blind to two real plans.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Stop the SELECTOR RESOLVER from reading record bodies for the plans type: resolve id6/setid/status from the plans index when it is provably trustworthy, fall back to the filesystem scan when it is not, so resolution becomes an index lookup without ever going blind to a record an agent forgot to index, and without changing a single match. The measured prize is architectural (find resolves, search reads) plus zero resolver-side file opens; it is NOT a large wall-clock win, and the CLI display layer's own full scan remains a known, deferred second half.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make index trust checkable

- [ ] E-01 Add a staleness signal for the plans index as an UNTRACKED SIDECAR, NOT inside `INDEX.json`. `.aw/records/plans/INDEX.json` has no generated-at, hash, or count marker, so nothing can tell a current index from one written before three plans were added. CONSTRAINT PROVEN IN REVIEW (PR-002): the marker MUST NOT go inside `INDEX.json`, because `check_drift` establishes staleness by rebuilding the file in memory and BYTE-COMPARING it to disk (plans_index.py:271-280, `jp.read_text() != want_json`). A generated-at timestamp inside that payload makes `want != disk` on every single run, so `aw check plans` would report `stale-index` permanently and every `aw index plans` would dirty a tracked file. Verified: `build_index_json` is currently byte-stable (rebuild == disk is True), and two successive builds carrying a timestamp are NOT byte-identical. Therefore: write the marker to a sidecar `.aw/records/plans/.index-fingerprint.json` that is GITIGNORED (it is machine-local derived state, and a tracked one would conflict between concurrent agents in this shared checkout), leaving `INDEX.json` byte-for-byte unchanged. The sidecar carries the generating tool version, a generated-at timestamp, the record count, and the directory fingerprint from E-02. Back-compat: a MISSING or unparseable sidecar is UNKNOWN-freshness (not trusted), never fresh, so an existing checkout keeps working with zero migration.
  - Depends on: none
  - Expected outcome: `aw index plans` writes the sidecar; `INDEX.json` bytes are unchanged (assert a rebuild still byte-equals disk, so `aw check plans` stays clean); the sidecar is gitignored; a missing sidecar reads as UNKNOWN.
  - Execution state: pending

- [ ] E-02 Define the directory fingerprint so it detects the drift that actually happens here, then implement `index_freshness(repo_root, record_type) -> Literal["fresh","stale","unknown","absent"]` as a pure, cheap, non-raising predicate: `absent` when there is no index, `unknown` when the sidecar is missing/unparseable, `stale` when the recomputed fingerprint differs, `fresh` otherwise. FINGERPRINT CORRECTION (PR-003, measured in review): the originally proposed "count of `*.md` per disposition dir plus max mtime" is PROVABLY BLIND to two drift modes this repo produces routinely. (a) A RENAME leaves count and max-mtime identical, yet `aw rename plans` / `aw group plans` rename files in place via `git_mv` (artifact_rename.py:590) and change the `path` column every index entry is keyed by. (b) An IN-PLACE EDIT that preserves mtime (`git checkout`, `git stash pop`, `tar -x`, `rsync -t`) changes a `Status:` with no count or mtime change; verified experimentally that such an edit is invisible to count+max-mtime. So the fingerprint MUST include the sorted RELATIVE-PATH SET (a hash of it, not the paths themselves) and each file's `(size, mtime_ns)`, which catches rename, add, delete, and same-mtime content edits, and still costs one `stat` per file with ZERO file opens. It MUST NOT read record bodies and MUST NOT raise (any error degrades to `unknown`).
  - Depends on: none
  - Expected outcome: the predicate returns the right verdict for all four states and never raises; a rename, a delete, an add, and a mtime-preserving in-place `Status:` edit are each reported `stale`; cost is O(stat per file), no file opened.
  - Execution state: pending

### Task group 2: index-first resolution with fallback

- [ ] E-03 Establish and TEST the STATUS-SEMANTICS PARITY the index-backed path requires, BEFORE switching any resolution to the index. PARITY DEFECT FOUND IN REVIEW (PR-004): the two readers do not agree on `Status:`. The selector uses `^- Status:\s*(\S+)\s*$` (selectors.py:89), which requires the whole value to be ONE token and therefore returns None for a multi-word value; the index uses `^- Status:\s*(.+?)\s*$` (plans_index.py:37), which captures the whole line. Measured on this repo: 24 of 394 plans carry a multi-word Status (e.g. `EXECUTED (approved by maintainer 2026-06-30; ...)`), and the two regexes DIVERGE on exactly those 24 files. So naively reading the index's `status` column would make `aw find plans EXECUTED` start matching records the filesystem path deliberately does not match - a silent behavior change to a frozen contract. Fix: the index-backed resolver MUST reproduce the SELECTOR's semantics, by applying the selector's own single-token rule to the index's stored value (a stored value with whitespace yields no status match, exactly as the file scan does). Do NOT "fix" the selector regex here; that is a separate behavior decision, and this plan's invariant is byte-identical results. (`set_id` was verified parity-clean: `set_terse_id` and `_read_setid` agree on all 394 plans, 0 divergences.)
  - Depends on: none
  - Expected outcome: a documented parity table for id6/setid/status, and a test proving the index-backed status rule returns the IDENTICAL path set as the file scan for all 394 plans including the 24 multi-word-Status ones.
  - Execution state: pending

- [ ] E-04 In `selectors.py`, add an index-backed resolver for the three content-derived rules (MATCH_ID6, MATCH_SETID, MATCH_STATUS) that reads `plan_id`/`set_id`/`status`/`path` from the index entries, applying E-03's parity rules. Use it ONLY when `index_freshness` is `fresh`; on `stale`/`unknown`/`absent` fall through to the existing bounded-header filesystem scan. The fallback is the correctness guarantee and MUST NOT be removable by configuration. Also handle the MULTI-DIRECTORY case honestly: `record_dirs` can return several roots (the project-context read paths plus the literal `.aw/records/<type>` and legacy `.agents/<type>`), while the index covers only its OWN root; if `record_dirs` yields any root the index does not cover, the type is NOT index-resolvable for that invocation and MUST take the fallback. (Verified in this repo `record_dirs('plans')` returns exactly one dir and the index path set equals the scan path set - 0 files on either side only - but the code must not assume the single-root case.)
  - Depends on: E-02, E-03
  - Expected outcome: with a fresh index, resolving an id6 opens ZERO record files (assert via an open() counter); with a stale/absent index the same query still returns the identical result via the fallback; a second unindexed record root forces the fallback.
  - Execution state: pending

- [ ] E-05 Stop feeding file text to the rules that never needed it: MATCH_PATH, MATCH_STEM, and MATCH_SUBSTRING match on the path/filename only, yet `_hits_for` draws them from `_files()` (selectors.py:420-422), which has already paired every path with header text. Give those rules a text-free path enumeration so a stem/substring query reads no file content in ANY freshness state. This is independent of all index work and is worth doing on its own: measured, the header reads are ~8ms of the ~34ms `_iter_files('plans')` call, and this removes them entirely for these rules.
  - Depends on: none
  - Expected outcome: a stem or substring query opens zero record files regardless of index state (assert via the open() counter).
  - Execution state: pending

- [ ] E-06 Do NOT wire research to the index; instead record the reason in the module docs and keep research on the filesystem scan. RESEARCH DISQUALIFIED IN REVIEW (PR-005): research docs do not use the `- Id:`/`- Status:`/`- Set:` BULLET front matter at all, they use YAML front matter (`id:`, `status:`, `set:` between `---` fences, parsed by `R.parse_frontmatter`, research_index.py:95). Verified: of 98 research files scanned by the selector, ZERO contain a `- Id:` bullet, so `aw find research j2000q` today resolves via MATCH_SUBSTRING (the filename happens to contain the id6), NOT via MATCH_ID6, and `aw find research reference` matches 5 files by filename substring while the index has 52 with `status: reference`. Feeding the research index into the id6/setid/status rules would therefore CHANGE research find results by an order of magnitude (5 -> 52 for one status query), which violates this plan's frozen-semantics invariant. That mismatch is a real defect, but it is a SEMANTIC one about which front-matter dialect selectors should understand; fixing it is a separate decision, not a performance change smuggled in here. So E-06 is documentation-only: state in `selectors.py` that research is deliberately not index-resolvable and why, and file the underlying dialect gap as a backlog item.
  - Depends on: E-04
  - Expected outcome: a comment/docstring naming the YAML-vs-bullet dialect mismatch, a test asserting research still resolves via the filesystem path (unchanged results, no silent 5 -> 52 change), and a new backlog item filed for the dialect gap.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Only TWO of the ten artifact types have an index: `.aw/records/plans/INDEX.json` and `.aw/records/research/INDEX.json`. The other eight (specs, prompts, backlog, walkthroughs, roadmaps, comms, releases, other) have none, so the filesystem scan must remain the general mechanism, not a legacy path.
- The plans index is a bare JSON LIST of entries; each entry carries `date`, `disposition`, `kind`, `order`, `path`, `plan_id`, `set_id`, `status` (394 entries observed 2026-08-29). `plan_id`/`set_id`/`status`/`path` are exactly the fields the three content-derived selector rules need.
- `INDEX.json` is a TRACKED, byte-deterministic artifact and `check_drift` proves freshness by rebuilding it and byte-comparing (plans_index.py:271-280). That makes the file itself the WRONG place for a generated-at marker (E-01), and makes byte-stability of `build_index_json` an invariant this plan must not break.
- There is NO freshness marker anywhere in the index file: no generated-at, no tool version, no count/hash. Trust therefore cannot be established today without recomputing, which is why E-01/E-02 precede the resolver work.
- Selector precedence is a frozen contract: path -> id6 -> setid -> status -> stem -> substring (`_PRECEDENCE` in selectors.py:48-55). Only the DATA SOURCE changes here, never the order or the semantics.
- The two readers DIVERGE on `Status:` parsing (single-token vs whole-line) and AGREE on `Set:`; see E-03. Any index-backed rule must reproduce the SELECTOR's semantics, not the index writer's.
- Research uses YAML front matter, plans use `- Key:` bullets. The selector only understands the bullet dialect, so research selector queries currently resolve by FILENAME SUBSTRING; see E-06.
- `aw find` vs `aw search` division is documented in their own help text: find resolves by selector, search matches content. Reading bodies in find is a violation of that split, which is the motivating concern.
- The awfindperf pass already added `_read_header` (4KB bounded read) and `_iter_md` (os.walk with pruning); this plan removes the need for the former on the fast path and keeps it as the fallback's reader.
- The repo is a SHARED CHECKOUT with concurrent agents (AGENTS.md), which is why the E-01 sidecar is untracked machine-local state rather than a tracked file two agents would fight over.

## Findings

- The three rules that force file reads are MATCH_ID6, MATCH_SETID, MATCH_STATUS (via `_read_id`/`_read_setid`/`_read_status`, selectors.py:175-190, applied at selectors.py:411-418). Every one of those values is already a column in the index.
- MATCH_PATH/MATCH_STEM/MATCH_SUBSTRING need no content at all, yet they are served from `_files()` which has already paired each path with header text (selectors.py:420-422). That is pure waste today and is fixed by E-05 independently of any index work.
- INDEX-ONLY WOULD BE WRONG, and this is the plan's central design constraint. Index drift is not hypothetical: on 2026-08-29 `aw check plans` reported 'Manifest index is missing or out of date' TWICE in one day - once after a plan was created by another agent, once after one was created by this session. An index-only `find` would have been blind to both plans. The fallback is therefore a correctness requirement, not defensive padding.
- Because the index has no freshness marker, 'is it stale?' is currently unanswerable cheaply. E-01/E-02 add that signal; without it, index-first resolution would either be unsafe (trust blindly) or pointless (recompute everything to check).
- THE MARKER CANNOT LIVE IN `INDEX.json` (PR-002, proven): freshness is currently established by byte-comparing a rebuild against disk, so a timestamp inside the payload would make `aw check plans` report stale forever and dirty a tracked file on every index run. Verified: rebuild currently byte-equals disk (True); two timestamped builds are not byte-identical (False). Hence the untracked sidecar.
- THE PROPOSED FINGERPRINT WAS INSUFFICIENT (PR-003, proven experimentally): count-per-dir + max-mtime does not change under a RENAME (`aw rename plans`/`aw group plans` do exactly this via `git_mv`, artifact_rename.py:590) nor under an mtime-preserving in-place edit (`git checkout`, `rsync -t`), yet both change what the index should say. A path-set hash plus per-file `(size, mtime_ns)` catches all four drift modes at one stat per file. Without this correction the "fresh" verdict would be a false negative precisely when the repo's own rename verbs cause the drift.
- THE TWO READERS DISAGREE ON `Status:` (PR-004, measured): selector `(\S+)` vs index `(.+?)`; 24 of 394 plans have a multi-word Status and the regexes diverge on exactly those 24. An unguarded switch to the index column would silently widen `aw find plans EXECUTED`. `Set:` is parity-clean (0/394 divergences). This is why E-03 (parity) gates E-04 (resolution) rather than following it.
- RESEARCH IS NOT ELIGIBLE (PR-005, measured): 0 of 98 research files carry a `- Id:` bullet because research uses YAML front matter; research selector queries therefore resolve today by filename substring. Wiring in its index would change one status query's result set from 5 to 52 files. The second indexed type is thus deferred to a separate semantic decision (E-06), which shrinks this plan rather than growing it.
- THE RESOLVER IS ONLY HALF THE READS (PR-001, measured): `aw find plans e32j35` opens 394 distinct record files and makes 788 open() calls, because after `resolve_selectors` returns, `cli._find_type_records` independently calls `plans_index.scan_plans` (cli.py:6590) whose `p.read_text()` is UNBOUNDED (plans_index.py:100; 74ms and ~6.7MB across the plans tree versus the resolver's bounded 4KB cap). A zero-open assertion scoped to the resolver can therefore be TRUE while the command still opens every file. The plan now says this plainly, keeps the display layer out of scope, and requires the benchmark to report END-TO-END opens so the improvement cannot be overstated.
- MEASURED BUDGET (corrected 2026-08-29 after awfindperf follow-ups ea8c3c2, re-measured in review): `aw find plans <id6>` is ~0.38s and bare `aw find` (all types) ~0.66s, against a process-startup floor of ~0.20s for `aw --version` on this machine. Resolver-side detail, min of 5 runs: `_iter_files('plans')` ~34ms total = ~1ms enumeration + ~8ms bounded header reads + ~13ms `p.resolve()` per path + ~4ms `record_dirs`; `json.load(INDEX.json)` is ~0.9ms. Across ALL ten types a full scan is ~218ms, of which header reads are ~54ms. So the honest resolver-side prize for the plans type is single-digit milliseconds of READ time (plus the ~13ms of `p.resolve()` the index path also skips), NOT a large wall-clock win: judge this plan primarily on FILE OPENS and on the architectural correctness of the find/search split, and treat wall clock as a secondary, mostly-unmoved signal.

### Maintainer session 2026-08-31: a simpler design, and a semantics correction

MEASURED WITH THE MAINTAINER, and it reframes this plan rather than merely adding to it.

1. `find <records dirs> -iname '*<term>*'` answers the common case in **20ms**, against **357ms** for
   `aw find plans <id6>` today (both measured on this repo, 449 plan files). So the directory listing,
   not the index, is the cheap fast path, and it needs NO freshness primitive at all because it reads
   the filesystem directly. That is a strictly simpler design than E-01/E-02's sidecar.

2. WHAT FILENAME MATCHING CANNOT DO, measured rather than assumed, so the fallback is not optional:
   - STATUS QUERIES ARE IMPOSSIBLE. `Status:` is content, never a filename. `-iname '*approved*'`
     returns 3 files and NONE of them is approved (an `open` backlog item ABOUT the word, a `done`
     item, and a plan literally named `auto-approved` whose status is `executed`), while 16 plans in
     `pending/` actually are `approved`.
   - 8 OF 651 RECORDS (1.2%) carry an `Id` and/or `Set` that is ABSENT from their filename: 5 plans
     (all in `executed/`, pre-id6-grammar legacy names) and 3 specs (grandfathered legacy spec names,
     which `AGENTS.md` explicitly keeps valid). `find -iname '*lus9ou*'` returns ZERO hits;
     `aw find plans lus9ou` finds it. Note `25kzda` is one of the three, i.e. a spec this repo cites
     constantly would become uncitable under filename-only matching.
   - A NAIVE IMPLEMENTATION MUST NORMALIZE QUOTES: one apparent ninth miss (`effzzi`) was a false
     positive caused by front matter reading ``set: `awoptimize` `` with backticks. Strip quoting
     before comparing, or the tool reports phantom drift.

3. THEREFORE THE SHAPE IS TWO-TIER: try the filename listing first (covers 643 of 651 records at
   ~20ms), and fall back to the existing bounded-header content scan ONLY when the listing yields
   nothing, plus always for status queries which filenames cannot express. The fallback then costs
   full price but runs rarely. This preserves correctness for the 8 legacy records while making the
   common case ~18x faster, and it makes E-01/E-02's freshness sidecar unnecessary for the fast path.

4. SEMANTICS, MAINTAINER RULING, and this is a CONTRACT not an optimization: `find` is intended to
   find MATCHING ARTIFACTS, not references. `aw find plans 123abc` must return only the artifact that
   IS `123abc`, never artifacts that MENTION, cite, or concern it. Verified that today's behavior is
   already correct on this point: `aw find plans y6mfgo` returns exactly 1 record while 6 plans
   mention `y6mfgo` in their bodies, and `aw find plans wtiso` returns the 6 `wtiso` plans while
   correctly EXCLUDING the different Set `wtisoland`. Any rewrite MUST preserve that. This is the
   argument against a naive `find | grep`, which conflates the two: the maintainer's own trial of
   `-iname '*wtiso*'` returned `wtisoland` plans, a session-handoff prompt, and a research report.

5. NON-CONFORMING NAMES MUST BE RAISED, NOT SILENTLY TOLERATED (new requirement). The long-term goal
   is to be able to TRUST filenames, which is only reachable if the 8 exceptions are visible and
   shrinking. Verified the gap: both `20260808-0004-00-plans-adopter-orchestrator.ipd.md` and
   `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` return `is_conformant=True` from the
   shipped normalizer, so `check_engine`'s naming rule skips them at `check_engine.py:462` and nothing
   surfaces them. So this is not a check that exists and is being ignored; there is no signal at all.
   REQUIRED: a report (advisory, not an error) naming every record whose `Id`/`Set` is absent from its
   filename, with the exact `aw rename` command that would make it conform, so the set is visible and
   can be driven to zero deliberately. Do NOT auto-rename: `executed/` plan bodies are immutable by
   policy and the grandfathered specs are a documented decision, so the renames are a maintainer call
   per record. Once the count reaches zero the filename fast path could become authoritative and the
   content fallback could be retired, which is the real prize.


## Proposed changes (ordered, validatable)

1. `plans_index.py`: write an UNTRACKED sidecar freshness marker (tool version, generated-at, record count, directory fingerprint), leaving `INDEX.json` bytes untouched; gitignore the sidecar.
2. New `index_freshness()` predicate over a rename/edit-sensitive fingerprint (path-set hash + per-file size/mtime_ns): fresh / stale / unknown / absent, cheap and non-raising.
3. `selectors.py`: prove and pin id6/setid/status PARITY between the index columns and the selector's own regex semantics (the multi-word-Status divergence).
4. `selectors.py`: index-backed resolution for id6/setid/status when fresh; existing bounded-header scan otherwise; multi-root types forced to the fallback.
5. `selectors.py`: text-free enumeration for path/stem/substring rules.
6. Research explicitly NOT wired (documented, tested as unchanged, dialect gap filed to backlog).
7. Tests: zero-open assertions, stale/absent fallback equivalence, drift safety, precedence unchanged, output contracts unchanged, end-to-end open counts reported honestly.

## Deferred / out of scope (with reason)

- THE CLI DISPLAY LAYER'S OWN FULL SCAN (`cli._find_type_records` -> `plans_index.scan_plans`, cli.py:6590, unbounded `read_text` at plans_index.py:100): this is the LARGER half of the reads (394 files, 788 opens, ~74ms and ~6.7MB for one `aw find plans <id6>`), and fixing it means changing how find RENDERS rows, which touches the output contract. Deferred deliberately to keep this plan single-concern and its scope fence honest, NOT because it is unimportant; it should be the follow-on plan in this Set, and until it lands the end-to-end command still opens every plan file. Recorded as a first-class limitation rather than left as an implied win.
- Wiring the RESEARCH index (E-06 documents instead): its YAML front matter means the selector never reads its metadata today, so switching to the index would change results (5 -> 52 on a status query), which is a semantic decision, not a performance one.
- Building indexes for the eight types that lack one: much larger scope, and unnecessary - they keep the filesystem scan, which is correct if slower.
- Auto-refreshing a stale index during `find`: deliberately NOT done. `find` is a read verb; silently rewriting a manifest as a side effect of a query would surprise callers and could race concurrent agents. Detecting stale and falling back is the safe behavior; refreshing stays an explicit `aw index <type>`.
- Changing selector precedence or matching semantics, including "fixing" the single-token `Status:` regex: frozen contract here; byte-identical results are this plan's invariant.
- The <100ms wall-clock target for generic `aw find`: NOT reachable by this plan, and the honest reason is now measured. Bare `aw find` is ~0.66s against a ~0.20s startup floor; the resolver-side read time this plan removes for the plans type is single-digit milliseconds. Getting under 100ms would require attacking import cost (lazy imports, a trimmed import graph, or a persistent daemon) AND the display-layer scan above, both separate concerns.
- `aw search`: unchanged; content search is legitimately its job.

## Scope check

- Over-scope: none. Review REMOVED the research wiring from the build scope (E-06 is now documentation + a backlog filing), because touching it would change user-visible results.
- Under-scope: none for the RESOLVER concern, which is this plan's declared unit. The display-layer scan is a named, quantified, deliberately deferred follow-on (see Deferred), not a silent omission. Freshness sidecar + rename-sensitive fingerprint + parity proof + index-backed resolution + text-free path rules + fallback tests is the complete resolver-side change; omitting the marker would force unsafe trust, omitting the parity proof would silently change matching, and omitting the fallback would reintroduce the drift blindness that motivated the design.

## Required tests / validation

- ZERO RECORD OPENS *IN THE RESOLVER* with a fresh index for id6/setid/status; and for stem/substring in every state. The counter MUST be scoped to `selectors.resolve*` and the assertion MUST be stated as resolver-scoped, because the CLI display layer still opens every file (see Deferred); a test worded as "aw find opens zero files" would be FALSE.
- END-TO-END OPEN COUNT reported honestly before/after for `aw find plans <id6>` (measured today: 394 distinct files, 788 opens), so the residual display-layer reads are visible and the win is not overstated.
- `INDEX.json` BYTE-STABILITY: after `aw index plans`, a rebuild still byte-equals disk and `aw check plans` is clean (this is what forbids putting the marker in the tracked file).
- FALLBACK EQUIVALENCE: identical results with index fresh / stale / absent.
- STATUS PARITY: for all 394 plans, and specifically the 24 with a multi-word `Status:`, the index-backed rule returns the IDENTICAL path set as the file scan (no widening of `aw find plans EXECUTED`).
- FINGERPRINT SENSITIVITY: rename, add, delete, and an mtime-PRESERVING in-place `Status:` edit are each detected as `stale` (the count+max-mtime design failed the rename and preserved-mtime cases; a passing test here is what proves the corrected fingerprint).
- DRIFT SAFETY (the point of the design): a record on disk but missing from a stale index is STILL FOUND. This is the assertion that forbids index-only.
- FRESHNESS PREDICATE: all four verdicts, and never raises.
- PRECEDENCE UNCHANGED: path -> id6 -> setid -> status -> stem -> substring, exercised per rule.
- RESEARCH UNCHANGED: research selector queries return the same results as before (no 5 -> 52 shift).
- OUTPUT CONTRACTS UNCHANGED: human TTY, `--json`, `--agent` JSONL shapes and exit codes.
- The new flags keep working: `--include-ignored` and `--max-depth` must still affect the FALLBACK path, and per OQ-02 passing either one FORCES the fallback; assert that.
- FULL SUITE green.

Validation command: `python3 -m pytest tests/test_selectors.py tests/test_selector_resolver_matrix.py tests/test_selector_resolver_parity.py tests/test_plans_index.py tests/test_research_index.py -q` plus the new freshness/zero-open tests, and a full default suite `python3 -m pytest -p no:randomly` (paste ACTUAL output; never claim success unrun).

Benchmark to report (informational, not a pass/fail gate): record file OPENS before/after, both RESOLVER-scoped and END-TO-END (the primary signal), plus type-scoped latency e.g. `aw find plans <id6>` and `aw find backlog <id6>`. State the startup floor alongside any wall-clock figure (~0.20s for `aw --version`; `aw find plans <id6>` ~0.38s and bare `aw find` ~0.66s as measured 2026-08-29) so a reader can tell search cost from process cost. Expect the wall-clock change to be SMALL (resolver-side reads are ~8ms of ~34ms for plans); do not report a wall-clock win the measurement does not support.

## Spec / documentation sync

- Document the freshness SIDECAR where the index format is described (`.aw/records/plans/README.md` and/or the `plans_index` module docstring): its filename, that it is untracked machine-local derived state, the four-verdict model, that a missing sidecar is UNKNOWN (so no migration is needed), and explicitly WHY it is not inside `INDEX.json` (the byte-compare drift check).
- Document the fingerprint's inputs (path-set hash + per-file size/mtime_ns) and the drift modes it must catch, so a future change does not "simplify" it back to count+mtime and silently reintroduce rename blindness.
- Record the `Status:` parsing parity constraint next to both regexes (selectors.py:89 and plans_index.py:37) as a cross-reference comment, so a future edit to either one is understood to be a matching-behavior change.
- Note in `aw find --help` (or the index docs) that find never rewrites a stale index; refreshing is `aw index <type>`.
- No user-facing behavior changes, so no CHANGELOG entry is required beyond an internal note; if one is written, keep it honest about the resolver/display split (contract item 4).

## Open questions

### OQ-01: When the index is stale, should `find` refresh it, warn, or silently fall back?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: SILENTLY FALL BACK, and do not refresh. Refreshing would make a read verb mutate a tracked manifest as a side effect of a query, which surprises callers and can race concurrent agents in this deliberately parallel repo. Warning on every stale index would be noise, since drift is common mid-session and the fallback already returns the correct answer. The staleness is separately visible through `aw check plans`, which already reports 'Manifest index is missing or out of date' - that is the right surface for the nag. A `--why`/verbose diagnostic MAY expose which path served the query, but the default must be quiet and correct.

### OQ-02: Do `--include-ignored` and `--max-depth` mean anything when the index answers the query?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: They are TRAVERSAL controls, so they only bind the filesystem fallback. Passing either one must therefore FORCE the fallback path rather than be silently ignored by an index hit - otherwise `--include-ignored` would appear to do nothing when an index happens to be fresh. Implement that as an explicit rule and assert it in V-04.

### OQ-03: Given the measured win is small and the display layer still reads every file, does this plan proceed resolver-only, or grow to cover the display layer?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-08-31 with the maintainer, and the answer supersedes
  the question's own framing: NEITHER as-written NOR merely grown. RE-SCOPE to a TWO-TIER filesystem
  design and DROP the index-first premise for the fast path. See "Maintainer session 2026-08-31" in
  Findings for the measurements; the load-bearing ones are that a plain directory listing answers the
  common case in 20ms against this plan's 357ms baseline, and that it needs no freshness sidecar at all
  because it reads the filesystem directly. E-01/E-02's sidecar is therefore unnecessary for the fast
  path, which removes the most fragile part of this plan (its fingerprint could not detect a
  length-preserving edit with a restored mtime; `ctime_ns` closes the realistic case but not a
  same-instant one).
  THE FALLBACK IS NOT OPTIONAL, measured: filenames cannot express a STATUS query at all, and 8 of 651
  records (1.2%) carry an `Id`/`Set` absent from their filename, including spec `25kzda`. So tier 2 is
  the existing bounded-header scan, entered when tier 1 yields nothing and always for status queries.
  TWO REQUIREMENTS WERE ADDED BY THE MAINTAINER RATHER THAN IMPLIED: (1) the CONTRACT that `find`
  returns matching ARTIFACTS and never references, so `123abc` matches only the artifact that IS
  `123abc` (today's behavior already conforms and must be preserved); and (2) an ADVISORY REPORT
  surfacing every non-conforming filename with its suggested `aw rename`, because the long-term goal is
  to trust filenames, which is only reachable if the exception set is visible and shrinking. Verified
  there is no such signal today: the legacy names return `is_conformant=True`, so the naming rule skips
  them.
  CONSEQUENCE: this plan needs re-authoring, not just re-approval. Its E-01/E-02/E-04 rest on the
  index-first premise the maintainer just displaced. Recorded here rather than silently rewritten,
  because a re-scope of that size is authoring and belongs to a fresh plan or a deliberate revision
  pass, not to a question's resolution field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of a named test showing `aw index plans` writes the SIDECAR freshness marker with all four parts (tool version, generated-at, record count, fingerprint), plus a pasted `python3 -c` snippet reading the sidecar and printing it. THE BYTE-STABILITY ASSERTION (this is the one that proves the marker is in the right place): paste evidence that after `aw index plans`, `build_index_json(scan_plans(dir))` byte-equals `INDEX.json` on disk AND that `aw check plans --check` reports clean - run it twice to show the second run does not report `stale-index`. Show the sidecar is gitignored (`git check-ignore -v <sidecar>` output). Include the BACK-COMPAT assertion: with the sidecar absent, freshness is `unknown` (not fresh). Assert the writer opens no record body to compute the fingerprint.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted test output covering ALL FOUR verdicts of `index_freshness`: `absent` (no index file), `unknown` (sidecar missing / malformed JSON / truncated), `stale`, `fresh` (immediately after `aw index`). THE FINGERPRINT SENSITIVITY MATRIX, pasted, with four separate stale cases: (a) a file ADDED, (b) a file DELETED, (c) a file RENAMED with count and max-mtime unchanged, (d) an in-place `Status:` edit with mtime RESTORED via `os.utime` so max-mtime is unchanged. Each MUST report `stale`; a test that only covers (a) does not validate this E-item, because (c) and (d) are exactly what the original count+max-mtime design missed. Plus a non-raising assertion: point it at an unreadable path / a directory / garbage bytes and assert it returns `unknown` rather than raising. Name the test file and functions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: THE STATUS PARITY PROOF, pasted: for every plan in this repo (394 at review time), assert the index-backed status resolution returns the IDENTICAL sorted path set as the filesystem scan, and include a targeted case over the 24 multi-word-`Status:` plans showing `aw find plans EXECUTED` does NOT gain those files. Paste the count of divergences (must be 0). Include the setid parity check too (expected 0 divergences). Cite the two regexes by `path:line` in the test docstring so the constraint is discoverable later.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: THE RESOLVER-SCOPED ZERO-OPEN ASSERTION, pasted: with a FRESH index, resolve an id6 (and separately a setid and a status) while counting record-file opens via a patched `Path.open`/`builtins.open` counter, and assert the count for `.md` record files is EXACTLY 0. State in the test name/docstring that this is RESOLVER-scoped. THEN, separately and honestly, paste the END-TO-END count for `aw find plans <id6>` before and after (baseline measured in review: 394 distinct files / 788 opens) and state plainly whether it changed; do NOT present the resolver-scoped zero as an end-to-end zero. Then THE FALLBACK EQUIVALENCE, also pasted: for the same three queries, compare results with (a) fresh index, (b) index deleted, (c) index made stale - assert all three return the IDENTICAL sorted path set. Then the DRIFT case: a record present on disk but ABSENT from a stale index is still found. Then the MULTI-ROOT case: with a second record root the index does not cover, assert the fallback is taken. Then OQ-02: `--include-ignored` and `--max-depth` each FORCE the fallback.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted test output asserting a MATCH_STEM query and a MATCH_SUBSTRING query each open ZERO record files, in BOTH the fresh-index and no-index states (four assertions), using the same open() counter. This must hold independently of any index, since these rules match on the filename only.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted test output asserting research selector resolution is UNCHANGED by this plan: `aw find research <id6>` and a research status query return the same path sets as before (specifically, the status query must NOT jump from the filename-substring result to the index's 52 `status: reference` docs). Paste the evidence for WHY research is excluded: a snippet counting research files containing a `- Id:` bullet (expected 0 of 98) alongside the YAML `id:` field, plus the `parse_frontmatter` call site (research_index.py:95). Show the new backlog item exists (`aw find backlog <id6>` or the file path) recording the YAML-vs-bullet dialect gap.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (stop the selector resolver reading record bodies by resolving from the plans index when trustworthy); E-items are ordered sub-steps - make trust checkable (E-01/E-02), prove semantic parity (E-03), then use it (E-04), plus one independent cleanup (E-05) and one explicit exclusion with its reason recorded (E-06). Each E-item is one focused pass over one narrow surface; E-05 is separable but too small to warrant its own plan and shares the same test file and open() counter harness.

Approval gate: this plan is `to-review` and carries NO human approval. It MUST NOT be executed until a human sets `Status: approved` via `aw ipd set approved <plan> --by-human`. Review completion is not approval.

Execution contract:

1. Open questions: OQ-01 and OQ-02 resolved from repository evidence; execution still requires explicit human approval (see the gate above).
2. Scope fence: touch ONLY `agent_workflows/selectors.py`, `agent_workflows/plans_index.py`, `tests/`, `.gitignore` (the sidecar ignore line), `.aw/records/plans/README.md` (documenting the sidecar), and the one new backlog file E-06 files. Do NOT modify `agent_workflows/research_index.py` behavior (E-06 is documentation + a backlog filing, deliberately narrowed in review), do NOT touch `cli.py` or the display-layer scan, do NOT build indexes for the eight unindexed types, do NOT change selector precedence or matching semantics (including the single-token `Status:` regex), do NOT modify `aw search`, and do NOT make `find` write or refresh any index. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted output of the named command. A V-item whose test was not run stays `Result: pending`. "Tests pass" is not evidence.
4. NO OVERSTATING THE WIN (HARD MUST): the zero-open claim is RESOLVER-scoped. Any report, walkthrough, or commit message MUST state the end-to-end open count too, and MUST NOT claim `aw find` stopped reading record files while the display-layer scan remains. Wall-clock figures MUST be accompanied by the startup floor.
5. FALLBACK IS NON-NEGOTIABLE: the filesystem scan must remain reachable and must not be disableable by config or flag. If a change makes the zero-open test pass only by removing the fallback, that is a failure. The drift assertion in V-04 (a record on disk but missing from a stale index is still found) is the invariant that forbids index-only; it must fail if the fallback is removed.
6. PARITY BEFORE PERFORMANCE: E-03 must be complete and V-03 verified before E-04 flips any resolution to the index. If parity cannot be achieved for a rule, that rule KEEPS the filesystem scan; silently changing what a selector matches is a failure, not a trade-off.
7. TRACKED-BYTES RULE: `INDEX.json` bytes must not change. If an implementation makes `aw check plans` report `stale-index`, revert it; the marker belongs in the untracked sidecar.
8. Fail-safe rule: `index_freshness` must never raise into a query. Any unreadable/malformed/absent index degrades to `unknown` and therefore to the filesystem scan.
9. Shared checkout: other agents are working in this checkout concurrently. Commit ONLY this plan's own changed files, path-scoped; verify the staged set with `git diff --cached --name-only` before committing; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
10. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`.
