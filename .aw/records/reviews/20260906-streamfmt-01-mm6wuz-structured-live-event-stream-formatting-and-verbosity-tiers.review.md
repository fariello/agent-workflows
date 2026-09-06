# Review: structured live event stream formatting and verbosity tiers (child mm6wuz, Set streamfmt)

- Subject-Id: mm6wuz
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `fcdf1134`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review; `--phase review-finalize` conformed after the revisions.

METHOD, because it is what produced every finding. This plan makes claims about the SHAPE OF A DATA
STREAM (which fields exist on which event, how often, with what types) and about GLYPH WIDTHS. Both are
empirically checkable, so rather than reading the plan's prose I measured the corpus the plan is about:
380 real session logs under `.aw/records/runs/*/sessions/*.jsonl`, 98,401 events, 27,673 `tool_use`
calls, 4,685 `filediff` occurrences, 984 `todowrite` events, 2,110 `read` events. That tree is
GITIGNORED (`.aw/.gitignore:14`, zero tracked files), so it is legitimate local evidence but cannot
become a test fixture; the plan now says so.

Three of the plan's central factual claims turned out to be FALSE, and each would have produced a
specific, visible defect rather than a stylistic imperfection: a write-event format reading a field that
does not exist, an alignment guarantee that breaks on four of nine glyphs, and a flag that cannot be
added the way described because its short spelling is already reserved by the argument shim. A fourth
claim (the flood-control rationale) is contradicted by its own subject matter by roughly an order of
magnitude in the wrong direction.

The plan's genuine strengths, stated plainly because they are why this is a revisions verdict and not a
replan: the module boundaries are right (one shared renderer, two thin host call sites), the ANSI-padding
hazard was correctly identified before any code was written (`render_stream.py:70-93`), the golden-test
coupling was correctly anticipated, and the E/V structure was already a clean bijection. The findings
below are corrections and additions inside a sound design, not a redesign.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | F. UX; D. anti-regression; evidence accuracy | plan "Project conventions" (original line 81); `unicodedata.east_asian_width` | The conventions section asserted "all chosen glyphs (`◀`, `▶`, `✎`, `⌕`, `☑`, `◇`, `◈`, `↳`, `❯`) are 1 character in width", and the whole alignment guarantee rests on it. FALSE for four of nine: `◀` U+25C0, `▶` U+25B6, `◇` U+25C7 and `◈` U+25C8 are East Asian Width `"A"` (AMBIGUOUS), which a terminal MAY render double-width; only `✎`, `⌕`, `☑`, `↳`, `❯` are `"N"`. The affected prefixes are exactly `read`, `write`, `diag` and `reason`, so on such a terminal those four lines shift by one column and the feature's single deliverable is lost. Worse, the false claim was written as a settled convention, so an executor would have had no reason to question it | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now states an explicit WIDTH POLICY (padding is by codepoint, exact only for narrow glyphs) and forbids restating the false claim; new E-09 adds a narrow-glyph fallback reusing the `use_unicode` switch the statusline already has (`render_stream.py:351`, `:476-483`); V-01 requires the limitation quoted from the code and V-09 requires both tables rendered. Added F-7. A true `wcwidth` helper is explicitly DEFERRED with reason (none exists in the repo: zero `east_asian_width`/`wcwidth`/`display_width` occurrences) |
| PR-002 | HIGH | IN-SCOPE | A. correctness; G. executability | plan E-03 (original); measured 480 completed `write` events | E-03 required rendering `▶ write: <path> (new file, <lines> lines)` from "`filediff` ... for `edit` and `write` tool events". `filediff` DOES NOT EXIST ON `write`. Measured over every dict-valued `filediff` in the corpus (4,685 instances): 4,663 on `edit` and ZERO on any other tool; `write` metadata keys are exactly `{diagnostics, filepath, exists, truncated}` and `metadata.filediff` was `None` in 480 of 480 completed writes. So the required line had NO SOURCE FIELD, and an executor following it literally would either render an empty/zero stat or invent a number. The `(new file, ...)` wording is also wrong for 15 of 480 writes, which overwrite an existing file (`metadata.exists` True) | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 rewritten: `filediff` is `edit`-only (with the measured int types for `additions`/`deletions`, 4,685 of 4,685), the write count is derived from `state.input.content`, the new-versus-overwrite word comes from `metadata.exists` (465 False / 15 True), and an absent `content` degrades to a path with no count rather than guessing. V-03 requires a `write` fixture with NO `filediff` at all to prove no code path reads it. Added F-8 |
| PR-003 | HIGH | IN-SCOPE | G. executability; C. architecture | `oc_runipd.py:7774`; `agy_runipd.py:4688`; `tests/test_runner_stop_triggers.py:1018-1029` | E-05 described adding `-v` as an ordinary `action="count"` flag. It cannot be. `"-v"` is a MEMBER OF THE IMPLICIT-START `subcommands` SET in both drivers, so a leading `-v` is treated as a subcommand and never gets `start` prepended. Measured at HEAD: `aw oc run -v somesetid` -> `error: argument command: invalid choice: 'somesetid'`; `aw oc run -vv somesetid` -> `error: unrecognized arguments: -vv`. The two spellings therefore fail DIFFERENTLY and neither reaches `start`, so the plan's own acceptance sentence ("`aw oc run <target> -v` ... control streaming detail") was unachievable as written. Compounding it, the set entry guards a `--version` that NEITHER driver registers (measured `parse_args(["--version"])` -> exit 2), and the set is STRUCTURALLY PINNED: `tests/test_runner_stop_triggers.py:994-1009` regexes it out of both source files and `:1018-1029` re-declares it inline, while `oc_runipd.py:7768-7770` forbids hoisting it into a constant | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now requires resolving the collision FIRST, naming both options and the parity constraint; new E-12 updates the structural test and the stale inline copy and pins whichever leading-flag behavior is chosen; `tests/test_runner_stop_triggers.py` added to `Scope-Paths`; V-05 requires the BEFORE and AFTER of the two exact failing commands, in leading AND trailing position, for `start` and `resume`, and through the `aw oc run` wrapper. Added F-9 and gate warning FOURTH |
| PR-004 | MEDIUM | UNDER-SCOPE | A. correctness; D. anti-regression | `oc_runipd.py:6899`, `:7051`, `:7133` | E-02 and E-03 add per-turn state (`tracker.todos`, `tracker.modified_files`) to `StreamTracker`, but the tracker is constructed ONCE PER INVOCATION and passed to every queue item and to the end-of-run summary. So item 2's first `todowrite` would be diffed against item 1's FINAL list and render a nonsense transition, and `modified_files` would silently mean "this run" while reading like "this plan". This only manifests on a multi-item queue, which is the normal case for `aw oc run all`, so it would have escaped single-plan testing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires a per-turn reset (or session keying) with a test; E-08 requires the accumulation scope of `modified_files` to be stated; V-02 requires a cross-item reset case as pasted evidence. Added F-15 and gate warning FIFTH |
| PR-005 | MEDIUM | IN-SCOPE | E. testing; G. executability | `pyproject.toml:154`; `tools/ipdrunner/test_runagy.py:18-101` | V-07's bare `python3 -m pytest` was the only validation for E-06, but a SECOND pinned renderer test exists outside the collected tree: `AgyEventRenderTests` asserts on `render_agy_event` output through the `runagy.py` re-export shim, and `testpaths = ["tests"]` means a bare run never collects `tools/` (measured: zero items). E-06 changes that function's output, so four assertions would have broken invisibly while V-07 reported green. Separately, ten of that module's twenty tests are ALREADY RED at HEAD (measured `10 failed, 10 passed`) for reasons unrelated to rendering, so a naive whole-module run cannot distinguish a new regression from inherited failure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-11 requires the explicit `-o addopts="" -k AgyEventRender` run (baseline `4 passed`, measured), `tools/ipdrunner/test_runagy.py` added to `Scope-Paths`, V-11 requires before/after plus confirmation the pre-existing failure count is UNCHANGED at 10, and fixing those ten is explicitly OUT of scope. Added F-14 and gate warning THIRD |
| PR-006 | MEDIUM | IN-SCOPE | Evidence accuracy; F. KISS | plan E-04 (original); measured 380 sessions | The default tier suppresses `read` and `find` "to avoid terminal flooding". The data contradicts the stated reason by roughly an order of magnitude: `read`+`grep`+`glob` are 7.9% of tool calls (median 3 per session, mean 5.7, max 53) while `bash`, which the tier KEEPS, is 69.7% (median 28, max 219), and `text` narration is 41.7% of all 47,498 would-be rendered lines. Hiding 7.9% while keeping 69.7% is not flood control. A wrong rationale is not cosmetic here: the next person tuning the tiers would reason from it and reach the wrong conclusion (for example suppressing `read` harder, or adding `bash` to the same bucket) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The volume rationale is removed and replaced with the defensible one (a read or a glob does not MUTATE the repository, so it is low-signal for an operator watching for effects), with the measured counts recorded so the reasoning is checkable. Added F-11 |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness; F. prevent silent failure | `render_stream.py:153-203` | E-04's `quiet` tier promises "IPD banners, heartbeats, and fatal errors only", but `render_event` HAS NO `error` BRANCH: a real `{"type":"error","error":{"name":"UnknownError","data":{"message":"The operation timed out."}}}` event (observed in the corpus) returns `None` and the operator sees nothing at ANY tier. So the one thing `quiet` exists to show is the one thing the renderer discards. Related: `quiet` is not a renderer level at all, it is implemented by NOT CALLING `render_event` (`oc_runipd.py:5651-5657`), so specifying it as a `render_event` tier would have produced a redundant second suppression path | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-04 now requires an `error` branch rendering at every tier (or an explicit citation of the layer that reports it), and states that `quiet` is owned by the call site with the `:5651-5657` citation. V-04 requires an `error` row in the per-tier matrix. Added F-13 |
| PR-008 | MEDIUM | OVER-SCOPE | G. executability; honest documentation | plan E-01/E-04 (original `◈ reason:`); measured event vocabulary | The prefix table includes `◈ reason:` and the `-vv` tier promises "`reason` (thinking/thought snippets)", but NO SUCH EVENT EXISTS. The complete `type` vocabulary over 98,401 events is exactly `text`, `tool_use`, `step_start`, `step_finish`, `error`; every `"reasoning"` string in the logs is the integer token-count field `"reasoning":0` inside `step_finish`. So `-vv` would have shipped documented help text for an effect that cannot occur, which is precisely the silent-failure shape the repo's own principles reject | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires either dropping the prefix or marking it reserved-and-unreachable in code, and forbids advertising the thinking tier; the `-vv` tier is re-pointed at `filediff.patch` hunks and `diagnostics`, both of which DO exist (patch on 4,685 edits, diagnostics non-empty on 3,160 of 5,165). The reason line is added to Deferred with the condition under which it becomes real. Added F-12 |
| PR-009 | MEDIUM | IN-SCOPE | Evidence accuracy; A. correctness | plan E-02 (original); measured 984 `todowrite` events | E-02 named no source field for the todo list and its format assumed a single active task. Measured: `state.title` is only ever `"<N> todos"` (which is exactly the uninformative thing the plan is fixing), the real list is `metadata.todos` with keys `{content, status, priority}` (`metadata.truncated` False in 982 of 982); statuses include `cancelled` (4 occurrences) which the plan did not mention and which must not count as done; and the number of `in_progress` items is NOT always 1 (1 x797, 0 x169, 2 x10, 3 x4, 4 x2), so the proposed `completed "<t>" -> active "<t>"` form is wrong or raises for 185 of 984 events | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now names `metadata.todos` with an `input.todos` fallback (0 length mismatches in 981 paired samples), and requires stating what renders for zero and for multiple active items and handling `cancelled`. V-02 demands seven distinct pasted cases |
| PR-010 | LOW | IN-SCOPE | F. KISS; evidence accuracy | plan E-01/E-04 (original); measured prefix lengths | The prefix table does not fit its own 13-column claim cleanly. `↳ subagent:` is 11 chars; `◇ diagost:` is a MISSPELLING of `diagnostic`, and the correctly spelled `◇ diagnostic:` is EXACTLY 13, leaving zero separator before the payload at a 13-pad. Also E-04 promised `read` line "byte sizes" which do not exist anywhere in the read payload (measured zero `bytes`/`size`/`byteSize` fields over 2,110 reads), and treated `find` as one shape when `grep` reports `metadata.matches` and `glob` reports `metadata.count` under DIFFERENT names, so a single lookup renders nothing for one of them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Label shortened to `◇ diag:`; the pad is now required to be DERIVED in code from `max(len(p)) + 1` rather than hardcoded to 13, with V-01 explicitly rejecting a test that only compares against the literal; byte sizes replaced by the line range actually present (`display.lineStart`/`lineEnd`/`totalLines` on 2,103 of 2,103); the two distinct find field names are named. Added F-10 |
| PR-011 | LOW | UNDER-SCOPE | E. testing; D. anti-regression | plan "Required tests" (original); `tests/test_render_stream.py:242-248` | The plan's own conventions section identifies ANSI-versus-padding as the failure mode, but the only test required for it was a golden transcript, which pins ONE sample and would let a future tenth prefix break alignment silently. There was also no test that the pad is derived rather than hardcoded, which is the property that actually prevents drift | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-10 requires an invariant test over ALL nine prefixes with color on and off, extending the existing `test_colored_transcript_strips_back_to_plain` pattern, and V-10 requires DEMONSTRATING IT BITES (paste the failure with a deliberately wrong pad, then the restored pass) rather than only a green run |
| PR-012 | LOW | UNDER-SCOPE | G. executability; spec/doc sync | plan "Spec / documentation sync" (original); `tests/test_render_stream.py:179-248`; `CONTRIBUTING.md:142` | Three gaps. (a) Doc sync named only CLI help strings, omitting the `CHANGELOG.md` entry that a user-visible output change plus two new operator flags warrants, and omitting the `subcommands`-set source comment (`oc_runipd.py:7768-7770`) that E-05 makes stale. (b) E-07 treated the golden as one assertion; `_GOLDEN_EVENTS` feeds THREE tests, one of which (`:229-240`) compares driver output against module output and must keep that property rather than being re-pinned to a literal. (c) The plan never decided whether the new type prefix keeps, replaces, or merges with the EXISTING per-status glyph (`✓`/`✗`/`…`/`•`, `:171-178`), which E-07 cannot re-pin without answering | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Doc sync now covers CHANGELOG (in user-facing prose, no em/en dashes) and the stale comment, and records that no spec governs stream rendering with the paths-checked requirement; E-07 enumerates all three golden tests and requires the re-export property preserved; OQ-01 raises the status-glyph question with an evidence-based resolution and `- Blocking: no` |

No finding was DEFERRED, left OPEN, or marked REPLAN. PR-001, PR-002 and PR-003 are HIGH and all three are
FIXED, so no escalation to a `- Blocking: yes` question was required
(`check.review-finding-unescalated` applies only to a HIGH left OPEN or DEFERRED).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: fix the width problem with a real display-width helper, or with a narrow-glyph fallback? | Narrow-glyph fallback (E-09) reusing the existing `use_unicode` switch; a `wcwidth`-style helper is explicitly DEFERRED with reason. | A full codepoint-width table, REJECTED as a general-purpose text-measurement facility rather than a stream-formatting change: the repo has none today (measured zero `east_asian_width`/`wcwidth`/`display_width` occurrences), and introducing one inside a rendering plan would be the largest thing in the plan while serving one caller. Simply dropping the four Ambiguous glyphs, REJECTED because they carry the clearest semantics (`◀` read, `▶` write) and the maintainer chose them. | `render_stream.py:351`, `:476-483` (the `use_unicode` precedent); `unicodedata.east_asian_width` for U+25C0/25B6/25C7/25C8 = `A` | yes |
| D-2 | PR-002: prescribe the write line count, or drop the write stat? | Derive from `state.input.content` and take the new-versus-overwrite word from `metadata.exists`. | Dropping the write stat entirely, REJECTED: `write` is 488 events and knowing a file was CREATED versus OVERWRITTEN is exactly the operator signal the plan exists to add, and both facts are available. Reading `filediff` on write anyway, REJECTED as reading a field measured `None` in 480 of 480 cases. | measured `write` metadata keys `{diagnostics, filepath, exists, truncated}`; `exists` False x465 / True x15; `input` keys `{filePath, content}` | yes |
| D-3 | PR-003: which resolution of the `-v` shim collision should the plan mandate? | NEITHER; the plan names both options, requires the executor to pick one, state it in code, and pin it in E-12. | Mandating removal of `"-v"` from the set, REJECTED as a decision that is arguably the maintainer's: `-v` is conventionally `--version`, and although no `--version` exists today the maintainer may intend one. Mandating `--verbose`-only, REJECTED as quietly abandoning the plan's own stated interface (`aw oc run <target> -v`). Recorded as OQ-02, non-blocking, because either choice is a one-literal edit in two files and fully reversible before release. | `oc_runipd.py:7774`, `:7768-7770`; `agy_runipd.py:4688`; measured `parse_args(["--version"])` -> exit 2 | yes |
| D-4 | PR-005: should this plan also fix the ten already-failing tests in `tools/ipdrunner/test_runagy.py`? | No, and explicitly out of scope; E-11 requires only that their count be reported UNCHANGED. | Fixing them, REJECTED on two grounds: they are unrelated to rendering, and repairing them in the same pass would destroy the executor's ability to tell whether THIS change is clean. Ignoring the module, REJECTED because four of its tests DO pin the function E-06 rewrites. | measured `10 failed, 10 passed` whole-module and `4 passed` for `-k AgyEventRender` at `fcdf1134`; `pyproject.toml:154` | yes |
| D-5 | PR-004/E-03: keep `modified_files` at all? | Keep the item but require a NAMED READER (E-08), with removal as an explicit permitted outcome. | Silently keeping the write-only set, REJECTED: dead accumulating state has no test that can prove it right and is a maintenance cost with no observable behavior. Deleting it outright in review, REJECTED because the maintainer put it there and `render_run_summary_table` is a natural consumer; the choice is the executor's with either outcome acceptable. | `render_stream.py:1047` (summary table), `:597` (statusline, byte-pinned by `tests/test_render_stream.py:402-436`); `oc_runipd.py:6899`, `:7051` | yes |
| D-6 | PR-008: drop the `◈ reason:` prefix, or reserve it? | Either, at the executor's choice, but the `-vv` "thinking snippets" PROMISE is removed and the deferral condition recorded. | Keeping the promise on the theory that some host might emit reasoning, REJECTED: shipping a documented flag whose effect cannot occur is exactly the silent-failure pattern the rubric forbids, and no such event exists in 98,401 measured events. | measured `type` vocabulary = `text`, `tool_use`, `step_start`, `step_finish`, `error`; `"reasoning":0` is a `step_finish` token count | yes |
| D-7 | Should the twelve E-items be split into multiple child plans? | No. One plan, twelve E-items, five task groups, with the cohesion rationale recorded in the gate. | Splitting, REJECTED for a dependency reason and NOT by appeal to the passing size lint: E-12 goes red the moment E-05 lands, E-11 goes red the moment E-06 lands, E-07 cannot re-pin the golden until every format-producing item exists, and E-10's invariant cannot be written before E-01 derives the pad. A split would produce children whose tests fail until a sibling merges. E-08 and E-09 are separable in principle but each attaches directly to one existing item and is a handful of lines. | `plan-review.md:490-496`; the E-05/E-12, E-06/E-11 and E-01/E-10 dependencies | yes |
| D-8 | PR-012: is a `CHANGELOG.md` entry required, and should the file join the fence? | Entry warranted; file deliberately NOT added to `Scope-Paths`, to be justified at finalize with `--scope-reason`. | Adding `CHANGELOG.md` to the fence, REJECTED to keep the fence describing the plan's code surface; the repo's own precedent handles a single intended out-of-fence doc edit through `--scope-reason` (the sibling `7wei1o` plan does exactly this for a spec header). Asserting no entry needed, REJECTED: two new operator-facing flags and changed terminal output are user-visible by definition. | `CONTRIBUTING.md:142`; `.aw/records/plans/pending/...7wei1o...ipd.md` gate (the `--scope-reason` precedent); `plan-review.md:353-360` | yes |
| D-9 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status: reviewed`; no human sign-off recorded). `no-go`, REJECTED: all three HIGH findings are FIXED, both open questions are resolved from repository evidence and carry `- Blocking: no`, and no finding was deferred. | `plan-review.md:531-546` | yes |

No `Reversible: no` decision was taken. Every decision above is undoable by editing the plan before
execution; nothing here publishes an interface, migrates data, or deletes anything.

### Verified claims

Re-measured independently at `fcdf1134`. Where a claim concerns the event stream, the population is 380
session logs, 98,401 events, 27,673 `tool_use` calls.

The plan's claims that HELD:

- `_GOLDEN_EVENTS` pins output byte-for-byte and must be updated (`tests/test_render_stream.py:179-192`).
  Confirmed, and extended: it feeds THREE tests, not one (PR-012).
- `Palette` wraps with ANSI and padding after colorization misaligns (`render_stream.py:70-93`).
  Confirmed; `_strip_ansi` at `:92-93` is the right primitive.
- `_add_output_mode_flags` uses a mutually exclusive group for `--quiet`/`--raw`/default `clean`
  (`oc_runipd.py:7252-7269`). Confirmed, and it is reached by both `start` (`:7514`) and `resume` (`:7572`).
- `render_agy_event` reduces paths to a bare basename (`agy_runipd.py:433-436`). Confirmed.
- Neither runner has `-v`/`--verbose` for stream detail. Confirmed, and the reason is worse than absence
  (PR-003).
- `filediff` carries `additions`/`deletions`. Confirmed FOR `edit`: keys are exactly
  `{file, patch, additions, deletions}` and both counts are `int` in 4,685 of 4,685 cases, so no string
  coercion is needed.
- `todowrite` renders a static count. Confirmed: `state.title` values are `0 todos` x164, `1 todos` x124,
  `4 todos` x110, `5 todos` x98, and so on.

Measurements that produced the findings:

- East Asian Width: `◀` U+25C0 `A`, `▶` U+25B6 `A`, `◇` U+25C7 `A`, `◈` U+25C8 `A`; `✎` U+270E `N`,
  `⌕` U+2315 `N`, `☑` U+2611 `N`, `↳` U+21B3 `N`, `❯` U+276F `N` (PR-001).
- Prefix lengths: `◀ read:` 7, `▶ write:` 8, `✎ edit:` 7, `⌕ find:` 7, `☑ todo:` 7, `◈ reason:` 9,
  `↳ subagent:` 11, `❯ bash:` 7; `◇ diagnostic:` 13 exactly (PR-010).
- `filediff` by tool: 4,663 `edit`, 0 everything else. `write` metadata keys
  `{diagnostics, filepath, exists, truncated}`, `filediff` `None` 480/480, `exists` False 465 / True 15
  (PR-002).
- `todowrite`: item keys `{content, status, priority}`; statuses `completed` 3,438, `pending` 3,246,
  `in_progress` 837, `cancelled` 4; `in_progress` per event 1 x797, 0 x169, 2 x10, 3 x4, 4 x2;
  `metadata.truncated` False 982/982; `input`/`metadata` list length mismatches 0 of 981 (PR-009).
- Tool mix: `bash` 19,289 (69.7%), `edit` 4,721 (17.1%), `read` 2,110 (7.6%), `todowrite` 984 (3.6%),
  `write` 488 (1.8%), `grep` 47, `glob` 21, `task` 11. Per-session `read`+`find` median 3 / mean 5.7 /
  max 53 versus `bash` median 28 / mean 50.8 / max 219; `text` is 41.7% of 47,498 rendered lines
  (PR-006).
- `read` payload: `metadata.display` keys `{type, path, text, lineStart, lineEnd, totalLines, truncated}`
  on 2,103 of 2,103; `input.offset`+`limit` both present on 1,543 of 2,110, neither on 509; ZERO
  `bytes`/`size`/`byteSize` fields anywhere. `grep` -> `metadata.matches` (47), `glob` ->
  `metadata.count` (21) (PR-010).
- Event vocabulary: `text` 39,580 part-events, `tool_use` 27,591, `step_start` 25,522, `step_finish`
  25,500, `error` 1. No reasoning event (PR-008). `render_event` on the real error line returns `None`
  (PR-007).
- Each `callID` appears exactly once: 27,514 of 27,514 single-event calls; status `completed` 27,474 /
  `error` 40. So there is no start/finish pair to correlate (informs OQ-01).
- CLI, measured unpiped: `aw oc run -v somesetid` -> `error: argument command: invalid choice:
  'somesetid'`; `aw oc run -vv somesetid` -> `error: unrecognized arguments: -vv`; the wrapper forwards
  `['-v','somesetid']` verbatim; `parse_args(["--version"])` -> exit 2 in BOTH drivers (PR-003).
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q` -> `10 failed, 10 passed`;
  `-k AgyEventRender` -> `4 passed`; bare collect yields 0 items from `tools/` (PR-005).
- Zero agy `step_update` events exist in the corpus (every log is OpenCode), so E-06's format has no
  local sample to validate against; recorded in E-06 rather than left implicit.
- `.aw/records/runs/` is gitignored (`.aw/.gitignore:14`) with 0 tracked files, and the payloads contain
  absolute maintainer paths, so it is measurement evidence only and not fixture material.

### Right-sizing and conceptual density

Twelve E-items, five task groups, three product modules (one renderer, two host drivers) and four test
modules. I evaluated splitting per `plan-review.md:490-496` and kept one plan for the dependency reason
recorded in D-7, not because the count lint passes. Each E-item names one deliverable in one region:
E-01 the pad derivation, E-02 the todo diff, E-03 the two file-event formats, E-08 one consumer decision,
E-04 the tier predicate, E-09 one fallback table, E-05 one driver's flag, E-06 the other driver's
renderer, E-10 one invariant test, E-07 the golden, E-11 one out-of-tree module, E-12 one structural
test. Each maps to exactly one V-item demanding pasted evidence. E-03 is the densest (two event shapes)
and was kept together because both write the same `modified_files` set and share the path-relativization
helper.

### Not verified, and stated as such

I implemented nothing and changed no product code; every claim above is a read of a named `path:line` at
`fcdf1134`, a read-only CLI invocation, or an aggregation over gitignored local session logs.
Specifically NOT established: how the four Ambiguous-width glyphs actually render in the maintainer's
terminal (that is a property of their terminal configuration, not of this repo, which is precisely why
E-09 exists rather than a verification step); whether the agy format changes in E-06 are correct against
a real Antigravity stream, since no agy event exists in the corpus to compare against; and whether the
bare suite stays green after the change, which requires the code to exist and is what V-07 forces.
