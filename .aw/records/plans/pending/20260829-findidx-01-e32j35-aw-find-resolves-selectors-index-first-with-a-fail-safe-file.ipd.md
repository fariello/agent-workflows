# IPD: aw find resolves selectors index-first with a fail-safe filesystem fallback, so it stops reading record bodies

- Date: 2026-08-29
- Kind: child
- Concern: `aw find` reads record file bodies to resolve selectors, which is both the wrong division of labour and its remaining cost. Per their own help, `aw find` resolves 'by selector (id6, status, Set, filename fragment)' while `aw search` searches 'for matching content (regex-enabled)' - yet find's `selectors._iter_files` opens every candidate record to regex out three front-matter bullets (`- Id:`, `- Status:`, `- Set:`) for the MATCH_ID6/MATCH_SETID/MATCH_STATUS rules. The awfindperf pass (a3954ed) cut generic find from 7.47s to ~0.8s by bounding those reads to a 4KB header and pruning excluded directories, but that mitigates the architecture rather than fixing it: find still stats and opens hundreds of files to answer a question the index already answers. `.aw/records/plans/INDEX.json` carries exactly the needed fields per entry (`plan_id`, `set_id`, `status`, `path`; 390 entries), so the id6/setid/status rules are an index lookup with ZERO file reads.
- Scope: Make selector resolution INDEX-FIRST with a FAIL-SAFE FILESYSTEM FALLBACK, never index-only. For a type that has an index, resolve MATCH_ID6/MATCH_SETID/MATCH_STATUS from the index; if the index is missing, unparseable, or judged stale, fall back to today's bounded-header filesystem scan and still return the correct answer. MATCH_PATH/MATCH_STEM/MATCH_SUBSTRING already need no file contents (they match on the path/filename) and must stop being fed file text at all. Add the staleness signal the index currently lacks so 'is the index trustworthy?' is a cheap deterministic check rather than a guess. Out of scope: changing what `aw find` MATCHES (precedence and semantics are frozen), changing `aw search`, and building indexes for the eight types that do not have one.
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/plans_index.py, agent_workflows/research_index.py, tests/
- Item-Dependencies: none
- Status: to-review
- Set: findidx
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: e32j35

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready: aw find should resolve id6/setid/status from the per-type index when fresh, with a non-removable filesystem fallback. Index-only is explicitly rejected: aw check plans reported a stale index TWICE on 2026-08-29, so index-only would have been blind to two real plans.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Stop `aw find` from reading record bodies: resolve id6/setid/status selectors from the per-type index when it is trustworthy, fall back to the filesystem scan when it is not, so find becomes an index lookup without ever going blind to a record an agent forgot to index.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make index trust checkable

- [ ] E-01 Add a staleness signal to the generated index so trustworthiness is a cheap deterministic check. `.aw/records/plans/INDEX.json` is currently a bare JSON LIST of entries with NO generated-at, hash, or count marker, so nothing can tell a current index from one written before three plans were added. Add a sidecar or wrapper carrying at minimum: the generating tool version, a generated-at timestamp, and the record-count + a cheap directory fingerprint (e.g. count of `*.md` per disposition dir plus max mtime) that can be recomputed without reading any record. Preserve backward compatibility: an index lacking the marker is treated as UNKNOWN-freshness (i.e. not trusted), never as fresh.
  - Depends on: none
  - Expected outcome: `aw index plans` writes the marker; a reader can decide fresh/stale/unknown from the marker plus a directory fingerprint, with no record file opened; an old marker-less index is reported UNKNOWN.
  - Execution state: pending

- [ ] E-02 Implement `index_freshness(repo_root, record_type) -> Literal["fresh","stale","unknown","absent"]` as a pure, cheap predicate: `absent` when there is no index, `unknown` when the marker is missing/unparseable, `stale` when the recomputed fingerprint differs, `fresh` otherwise. It MUST NOT read record bodies and MUST NOT raise (any error degrades to `unknown`).
  - Depends on: E-01
  - Expected outcome: the predicate returns the right verdict for each of the four states and never raises; cost is O(dir entries), not O(records read).
  - Execution state: pending

### Task group 2: index-first resolution with fallback

- [ ] E-03 In `selectors.py`, add an index-backed resolver for the three content-derived rules (MATCH_ID6, MATCH_SETID, MATCH_STATUS) that reads `plan_id`/`set_id`/`status`/`path` from the index entries. Use it ONLY when `index_freshness` is `fresh`; on `stale`/`unknown`/`absent` fall through to the existing bounded-header filesystem scan. The fallback is the correctness guarantee and MUST NOT be removable by configuration.
  - Depends on: E-02
  - Expected outcome: with a fresh index, resolving an id6 opens ZERO record files (assert via an open() counter); with a stale/absent index the same query still returns the identical result via the fallback.
  - Execution state: pending

- [ ] E-04 Stop feeding file text to the rules that never needed it: MATCH_PATH, MATCH_STEM, and MATCH_SUBSTRING match on the path/filename only, yet `_hits_for` currently draws them from `_files()`, which pairs every path with header text. Give those rules a text-free path enumeration so a stem/substring query reads no file content in ANY freshness state.
  - Depends on: none
  - Expected outcome: a stem or substring query opens zero record files regardless of index state (assert via the open() counter).
  - Execution state: pending

- [ ] E-05 Apply the same index-first path to `research` (the other type with an index, `.aw/records/research/INDEX.json`), reusing the shared predicate and resolver rather than adding a second implementation. The eight types with no index keep the filesystem scan and are unaffected.
  - Depends on: E-03
  - Expected outcome: research id6/status/setid queries use its index when fresh and fall back otherwise; a grep shows one shared implementation, not per-type copies.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Only TWO of the ten artifact types have an index: `.aw/records/plans/INDEX.json` and `.aw/records/research/INDEX.json`. The other eight (specs, prompts, backlog, walkthroughs, roadmaps, comms, releases, other) have none, so the filesystem scan must remain the general mechanism, not a legacy path.
- The plans index is a bare JSON LIST of entries; each entry carries `date`, `disposition`, `kind`, `order`, `path`, `plan_id`, `set_id`, `status` (390 entries observed). `plan_id`/`set_id`/`status`/`path` are exactly the fields the three content-derived selector rules need.
- There is NO freshness marker anywhere in the index file: no generated-at, no tool version, no count/hash. Trust therefore cannot be established today without recomputing, which is why E-01 precedes the resolver work.
- Selector precedence is a frozen contract: path -> id6 -> setid -> status -> stem -> substring (`_PRECEDENCE` in selectors.py). Only the DATA SOURCE changes here, never the order or the semantics.
- `aw find` vs `aw search` division is documented in their own help text: find resolves by selector, search matches content. Reading bodies in find is a violation of that split, which is the motivating concern.
- The awfindperf pass already added `_read_header` (4KB bounded read) and `_iter_md` (os.walk with pruning); this plan removes the need for the former on the fast path and keeps it as the fallback's reader.

## Findings

- The three rules that force file reads are MATCH_ID6, MATCH_SETID, MATCH_STATUS (via `_read_id`/`_read_setid`/`_read_status`, selectors.py:174-190). Every one of those values is already a column in the index.
- MATCH_PATH/MATCH_STEM/MATCH_SUBSTRING need no content at all, yet they are served from `_files()` which has already paired each path with header text. That is pure waste today and is fixed by E-04 independently of any index work.
- INDEX-ONLY WOULD BE WRONG, and this is the plan's central design constraint. Index drift is not hypothetical: on 2026-08-29 `aw check plans` reported 'Manifest index is missing or out of date' TWICE in one day - once after a plan was created by another agent, once after one was created by this session. An index-only `find` would have been blind to both plans. The fallback is therefore a correctness requirement, not defensive padding.
- Because the index has no freshness marker, 'is it stale?' is currently unanswerable cheaply. E-01 adds that signal; without it, index-first resolution would either be unsafe (trust blindly) or pointless (recompute everything to check).
- Expected win: with a fresh index, an id6 query becomes O(1) index parse + a dict lookup and opens zero record files. MEASURED BUDGET (corrected 2026-08-29 after awfindperf follow-ups ea8c3c2): `aw find` is now ~0.61s total, of which ~0.38s is process startup (bare python 0.05s; `import agent_workflows.cli` 0.33s; `aw --version` 0.38s) and only ~0.2s is search. An earlier draft of this plan claimed the whole residual was import cost; that was WRONG and was disproved by direct measurement, which found ~1.0s of real search work (30 forked `git ls-files` subprocesses at 0.92s, plus 978 redundant `repo_root.resolve()` calls). Those two are now fixed. So the remaining search budget this plan can attack is ~0.2s, not ~0.8s: judge it primarily on FILE OPENS (the zero-open assertions), with wall-clock as a secondary signal.

## Proposed changes (ordered, validatable)

1. Index writers (`plans_index.py`, `research_index.py`): emit a freshness marker (tool version, generated-at, record count + cheap directory fingerprint).
2. New shared `index_freshness()` predicate: fresh / stale / unknown / absent, cheap and non-raising.
3. `selectors.py`: index-backed resolution for id6/setid/status when fresh; existing bounded-header scan otherwise.
4. `selectors.py`: text-free enumeration for path/stem/substring rules.
5. Research wired through the same shared code path.
6. Tests: zero-open assertions, stale/absent fallback equivalence, precedence unchanged, output contracts unchanged.

## Deferred / out of scope (with reason)

- Building indexes for the eight types that lack one: much larger scope, and unnecessary - they keep the filesystem scan, which is correct if slower.
- Auto-refreshing a stale index during `find`: deliberately NOT done. `find` is a read verb; silently rewriting a manifest as a side effect of a query would surprise callers and could race concurrent agents. Detecting stale and falling back is the safe behavior; refreshing stays an explicit `aw index <type>`.
- Changing selector precedence or matching semantics: frozen contract.
- The <100ms wall-clock target for generic `aw find`: NOT reachable by this plan, but for a measured reason rather than the wrong one first recorded. Of the current ~0.61s, ~0.38s is process startup (interpreter + the `agent_workflows.cli` import graph) which no index change can touch; the ~0.2s search remainder is what this plan addresses. Getting under 100ms would additionally require attacking import cost (lazy imports, a trimmed import graph, or a persistent daemon), which is a separate concern and deliberately out of scope here.
- `aw search`: unchanged; content search is legitimately its job.

## Scope check

- Over-scope: none.
- Under-scope: none. Index writer + freshness predicate + both index-backed types + the text-free path rules + fallback tests is the complete change; omitting the freshness marker would force unsafe trust, and omitting the fallback would reintroduce the drift blindness that motivated the design.

## Required tests / validation

- ZERO RECORD OPENS with a fresh index for id6/setid/status; and for stem/substring in every state.
- FALLBACK EQUIVALENCE: identical results with index fresh / stale / absent.
- DRIFT SAFETY (the point of the design): a record on disk but missing from a stale index is STILL FOUND. This is the assertion that forbids index-only.
- FRESHNESS PREDICATE: all four verdicts, and never raises.
- PRECEDENCE UNCHANGED: path -> id6 -> setid -> status -> stem -> substring, exercised per rule.
- OUTPUT CONTRACTS UNCHANGED: human TTY, `--json`, `--agent` JSONL shapes and exit codes.
- The new flags keep working: `--include-ignored` and `--max-depth` must still affect the FALLBACK path (they are traversal controls; state explicitly in the plan whether they are meaningful when the index answers, and assert that documented behavior).
- FULL SUITE green.

Validation command: `python3 -m pytest tests/test_selectors.py tests/test_plans_index.py tests/test_research_index.py -q` plus the new freshness/zero-open tests, and a full default suite `python3 -m pytest -p no:randomly` (paste ACTUAL output; never claim success unrun).

Benchmark to report (informational, not a pass/fail gate): record file OPENS before/after (the primary signal), plus type-scoped latency e.g. `aw find plans <id6>` and `aw find backlog <id6>`. State the startup floor alongside any wall-clock figure (~0.38s as measured on 2026-08-29) so a reader can tell search cost from process cost and is not misled into judging the change by total wall clock.

## Spec / documentation sync

- Document the index freshness marker where the index format is described (plans/research README or the index module docstring), including that a marker-less index is treated as UNKNOWN.
- Note in `aw find --help` (or the index docs) that find never rewrites a stale index; refreshing is `aw index <type>`.

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
- Resolution or deferral rationale: They are TRAVERSAL controls, so they only bind the filesystem fallback. Passing either one must therefore FORCE the fallback path rather than be silently ignored by an index hit - otherwise `--include-ignored` would appear to do nothing when an index happens to be fresh. Implement that as an explicit rule and assert it in V-04/V-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of a named test showing `aw index plans` writes the freshness marker with all three parts (tool version, generated-at, record count + directory fingerprint), plus a pasted `python3 -c` snippet reading the written index and printing the marker. Include the BACK-COMPAT assertion: an index file WITHOUT the marker is reported UNKNOWN (not fresh) - construct one and show the verdict. Assert the writer opens no record body to compute the fingerprint (see the open() counter in V-03).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted test output covering ALL FOUR verdicts of `index_freshness`: `absent` (no index file), `unknown` (marker missing / malformed JSON / truncated), `stale` (add a record file after indexing, recompute), `fresh` (immediately after `aw index`). Plus a non-raising assertion: point it at an unreadable path / a directory / garbage bytes and assert it returns `unknown` rather than raising. Name the test file and functions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: THE ZERO-OPEN ASSERTION, pasted: with a FRESH index, resolve an id6 (and separately a setid and a status) while counting record-file opens via a patched `Path.open`/`builtins.open` counter, and assert the count for `.md` record files is EXACTLY 0. Then THE FALLBACK EQUIVALENCE, also pasted: for the same three queries, compare results with (a) fresh index, (b) index deleted, (c) index made stale by adding a record afterwards - assert all three return the IDENTICAL sorted path set, proving the fallback is not a degraded answer. Finally assert the drift case explicitly: a record present on disk but ABSENT from a stale index is still found (this is the regression that index-only would cause, and it must fail before the fallback exists).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted test output asserting a MATCH_STEM query and a MATCH_SUBSTRING query each open ZERO record files, in BOTH the fresh-index and no-index states (four assertions), using the same open() counter. This must hold independently of any index, since these rules match on the filename only.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted test output showing a research id6/status/setid query resolves from `.aw/records/research/INDEX.json` when fresh (zero record opens) and falls back correctly when stale/absent. PLUS a grep proving ONE shared implementation: `grep -c "def index_freshness" agent_workflows/*.py` returns 1 total, and both `plans_index` and `research_index` (or selectors) import it rather than defining their own.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (stop find reading record bodies by resolving from the index when trustworthy); E-items are ordered sub-steps - make trust checkable, then use it, then extend to the second indexed type.

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

Execution contract:

1. Open questions: OQ-01 and OQ-02 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/selectors.py`, `agent_workflows/plans_index.py`, `agent_workflows/research_index.py`, and `tests/`. Do NOT build indexes for the eight unindexed types, do NOT change selector precedence or matching semantics, do NOT modify `aw search`, and do NOT make `find` write or refresh any index. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted output of the named command. A V-item whose test was not run stays `Result: pending`. "Tests pass" is not evidence.
4. FALLBACK IS NON-NEGOTIABLE: the filesystem scan must remain reachable and must not be disableable by config or flag. If a change makes the zero-open test pass only by removing the fallback, that is a failure. The drift assertion in V-03 (a record on disk but missing from a stale index is still found) is the invariant that forbids index-only; it must fail if the fallback is removed.
5. Fail-safe rule: `index_freshness` must never raise into a query. Any unreadable/malformed/absent index degrades to `unknown` and therefore to the filesystem scan.
6. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`.
