# IPD: Count waiting aw inbox drops in aw attention by listing the directory only so a forgotten drop is visible without any file being opened

- Date: 2026-09-08
- Kind: child
- Concern: `.aw/inbox/` is deliberately invisible to every records view, and the cost of that correct default is that a file dropped there and forgotten stays forgotten. `aw attention` is this repository's answer to "what needs attention?", and it cannot see the queue at all: `grep -rn "inbox" agent_workflows/attention.py agent_workflows/attention_contract.py` returns ZERO hits. So the one surface that exists to stop work being forgotten is blind to a whole class of waiting work.
  THE INVISIBILITY IS INTENTIONAL AND MUST NOT BE UNDONE. The inbox sits OUTSIDE `.aw/records/` so the `other` catch-all sweep cannot enumerate a drop as an artifact, and `.aw/.gitignore:20-28` documents exactly why in its own comment: because a stray `- Id: <id6>` in a dropped file, "even one merely QUOTED inside an external report", would be "harvested as an identity claim that can collide with a real artifact's id6". The ask here is a plain COUNT, not visibility as records.
  THE HARD CONSTRAINT IS THE WHOLE POINT OF THE ITEM, and I reproduced the hazard rather than repeating it: `selectors._ID_RE` is `(?m)^- Id:\s*([0-9a-z]{6})\s*$` (`selectors.py:111`), applied with `.search()` over a whole body, so it is position-unanchored. Given a body whose line 5 is a `- Id:` line inside prose explicitly labelled as a quoted example, it MATCHED and returned that id6. So LISTING a directory cannot forge an identity but PARSING a drop can, and the implementation may read directory ENTRIES ONLY (names, and at most size/mtime), never opening a file. That distinction must be explicit in the code and its comment.
  THIS IS FULLY LIVE. Not one line exists, no plan carries `- From-Backlog: plbkp5`, and the sibling item in the same Set (`lsztiu`, the `aw adopt` verb, now plan `lznpv6`) covers adoption only: grepping that plan for attention, count, waiting or nudge yields one incidental hit and no E-item.
- Scope: Add a derived, read-only count of waiting `.aw/inbox/` entries and surface it as one advisory line in the `aw attention` human board, computed by listing the directory only and never opening a file. A missing directory means zero and prints nothing. The count must NOT enter the ready/active/blocked/done/parked classification, must NOT invent a status for inbox items, and must NOT affect the exit code. EXCLUDES `aw adopt` (plan `lznpv6`), any change to what `.aw/inbox/` is or its gitignore status, any change to `selectors._ID_RE` (plan `76w6mq`), and any typed inventory of inbox contents.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: none
- Status: to-review
- Set: awinbox
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 9iiqmm
- From-Backlog: plbkp5

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `plbkp5`. The item carries no `- Blocks-Release:` so none is inherited or invented. FULLY LIVE: nothing implemented, nothing claimed.
  I REPRODUCED THE ITEM'S JUSTIFYING HAZARD INSTEAD OF CITING IT. The item's hard constraint rests on `selectors._ID_RE` harvesting a body-quoted `- Id:` line. I ran it: the pattern is `(?m)^- Id:\s*([0-9a-z]{6})\s*$` at `selectors.py:111`, applied via `.search()`, and against a body whose line 5 was a `- Id:` inside prose labelled as a quoted example it MATCHED and returned that id6. So the listing-only rule is justified by measured behavior, and E-04 requires the test PROVE non-reading mechanically rather than asserting it in a comment.
  THE ITEM'S PREMISE HAS ONE ENVIRONMENTAL CORRECTION THAT IS LOAD-BEARING. The item and the sibling plan `lznpv6` both describe a non-empty inbox (`lznpv6:6` measured "10-plus files"), but `.aw/inbox/` DOES NOT EXIST in this worktree: `ls .aw/inbox` returns No such file or directory. That is expected, because the directory is gitignored and therefore per-checkout, and it makes "absent means zero, silently" a first-class requirement rather than an edge case. A naive implementation would raise or print `inbox: 0 files waiting` on most fresh checkouts.
  TWO IMPLEMENTATION TRAPS I FOUND BY READING THE RENDERER, neither in the item. FIRST, the footer is an `if/elif/elif` CHAIN (`attention.py:2940-2948`), so exactly ONE footer line ever prints; appending with `elif` would make the inbox nudge invisible on any repo where setup is needed, which is precisely a fresh checkout. E-02 requires an independent `if`. SECOND, `render_json`'s object (`:1070`) is pinned by a `schema_version` assertion in `tests/test_attention.py`, and `SCHEMA_VERSION = 3` (`:33`), so adding a top-level JSON key is a schema bump with a test to update. OQ-01 resolves that by keeping the count out of the JSON in this plan.
  THE RIGHT PRECEDENT ALREADY EXISTS AND I FOLLOW IT RATHER THAN INVENTING ONE. `setup_needed(repo_root)` (`attention.py:1405`) is a derived, read-only, exception-swallowing boolean that produces a footer nudge and touches neither the item list nor the exit code, and its docstring stresses it "NEVER creates anything". An `inbox` counter is its structural twin. The advisory sections `gate_warnings` and `order_notices` (`:2905`, `:2922`) are the precedent for "human view only; NEVER affect the exit code", which is exactly the item's `--check` recommendation, and their comments say so in as many words.

## Goal

Make a forgotten inbox drop visible in the one place a human or agent asks "what needs attention?", as a plain nudge that never interprets a drop as a record, never classifies it, and never fails a check.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the counter, which may list but never read

- [ ] E-01 ADD A DERIVED, READ-ONLY COUNTER THAT LISTS `<repo>/.aw/inbox/` AND OPENS NOTHING.
  MODEL IT ON `setup_needed` (`attention.py:1405`), which is the house pattern for exactly this: derived on demand, read-only, swallows its own exceptions, never creates anything, and feeds a footer nudge. Do not invent a second shape.
  A MISSING DIRECTORY MEANS ZERO AND MUST BE SILENT. `.aw/inbox/` is gitignored and therefore per-checkout; it does not exist in a fresh worktree (verified). Absent must not raise, and must not print a zero line either: a nudge that fires when there is nothing to nudge about is noise that trains readers to ignore it.
  LIST ONLY, NEVER OPEN. This is the item's hard constraint and its justification is measured (see the history note): parsing a drop lets that drop's CONTENT assert an identity via `selectors._ID_RE` and collide with a real artifact. Use a directory scan that yields names, and at most size or mtime, with no read of any file's contents. `os.scandir` gives exactly that.
  RESOLVE `<repo>/.aw/inbox/` EXACTLY. Never search recursively for directories named `inbox`: `.aw/records/comms/shared/inbox/` is a TRACKED, unrelated inter-agent comms lane, and `.aw/.gitignore:25-27` records that an unanchored `inbox/` pattern once threatened exactly that path and would break `aw install` on a fresh repo. One anchored path, nothing else.
  COUNT ANYTHING WAITING, not a typed inventory. The item is explicit: hidden files, non-`.md` drops, and nested directories all count as "something is waiting". The point is a nudge. Decide and STATE whether a nested directory counts as one entry or is walked; either is defensible, but it must be deliberate and documented, not incidental.
  WRITE THE REASON IN THE CODE, not only in this plan. The comment must state that inbox items are VISIBLE AS FILES and never INTERPRETED AS RECORDS, and why, because the next person to touch this function will otherwise "improve" it by reading front matter.
  - Depends on: none
  - Expected outcome: a derived counter resolving exactly `<repo>/.aw/inbox/`, returning zero for a missing directory without raising, opening no file, counting hidden and non-`.md` entries, with the listing-not-parsing rule and its reason stated in a comment; nothing is created or written.
  - Execution state: pending

### Task group 2: surface it without contaminating the model

- [ ] E-02 SURFACE THE COUNT AS ONE ADVISORY LINE IN THE HUMAN BOARD, USING AN INDEPENDENT `if`, NOT THE EXISTING `elif` CHAIN.
  THE TRAP, and the reason this is its own item: the footer at `attention.py:2940-2948` is `if needs_setup and has_hidden / elif needs_setup / elif has_hidden and colored`, so exactly ONE line ever prints. Appending another `elif` would hide the inbox nudge whenever setup is needed, which is the state of a fresh checkout, which is exactly where a forgotten drop is most likely. Add an independent `if` so the nudge composes with whatever else the footer says.
  FOLLOW THE ADVISORY-SECTION PRECEDENT for placement and tone: `gate_warnings` (`:2905`) and `order_notices` (`:2922`) are both rendered as advisory blocks whose comments state they are "human view only; NEVER affect the exit code". A single line in the footer is the whole feature; do not build a section with a header for one number.
  SAY WHAT TO DO NEXT, since a bare count is a nudge without a remedy. The sibling plan `lznpv6` adds `aw adopt` to clear a drop; if it has landed, naming it makes the line actionable. If it has NOT landed, do NOT advertise a verb that does not exist: state the count alone. Check and state which.
  DO NOT INVENT A STATUS AND DO NOT ENTER THE CLASSIFICATION. Inbox items have no id6, no status and no lifecycle. They must not appear as an `Item`, must not be counted in ready/active/blocked/done/parked, and must not reach `TRACKED_TREES` or `CLASS_MAPS`. If a change to `attention_contract.py` seems necessary, the design has drifted into classification: stop and reconsider.
  RESPECT `--all` SEMANTICS DELIBERATELY. `--all` reveals hidden done/parked artifacts. An inbox count is not hidden work of that kind, so decide and state whether it shows always or only under `--all`; the item's intent is a nudge, which argues for always.
  - Depends on: E-01
  - Expected outcome: one advisory footer line added under an independent `if`, composing with the existing footer rather than replacing it; no new `Item`, no new status, no change to `attention_contract.py`; the follow-up verb named only if it exists.
  - Execution state: pending

- [ ] E-03 KEEP THE EXIT CODE AND THE `--check` PATH UNTOUCHED, so a gitignored box-local file can never fail CI.
  NEVER CONSTRUCT A `Drift` FOR A WAITING DROP. The exit code is owned solely by the drift set: `return core.drift_exit_code(drift)` on both the check path (`:2715`) and the board path (`:2956`). A `Drift` here would make `aw attention --check` fail on the presence of a local, gitignored file that no other machine can even see, which the item recommends against and which would be wrong: a waiting drop is not a repository defect.
  THE TWO EXISTING ADVISORY SECTIONS ARE THE PRECEDENT and their comments already state this rule, so cite them rather than arguing it afresh.
  DECIDE WHETHER `--check` PRINTS THE LINE AT ALL. `--check` is a validity gate, so the defensible answer is that it stays silent, but state the choice rather than leaving it to fall out of the code path.
  - Depends on: E-02
  - Expected outcome: no `Drift` is ever constructed for inbox entries; `aw attention` and `aw attention --check` exit codes are provably unchanged with a non-empty inbox; the `--check` display choice stated.
  - Execution state: pending

### Task group 3: prove the constraint mechanically

- [ ] E-04 PROVE NON-READING MECHANICALLY, because "we only listed" is the plan's central safety claim and a comment cannot prove it.
  THE STRONGEST AVAILABLE PROOF is to make opening a file FAIL during the count and assert the count still succeeds: patch the open path (`Path.read_text`, `Path.open`, `builtins.open`) to raise, then assert the counter returns the right number. A test that merely checks the count is right would pass on an implementation that parses every drop.
  BUILD EVERY CASE IN A TEMPORARY REPO AND NEVER READ THE REAL `.aw/inbox/`. It is gitignored, machine-specific, absent in this worktree, and will empty as drops are adopted; a test pinned to it passes on one machine and fails on another. `tests/test_attention.py` already builds temp repos via `_mk_repo` (`:25`) and drives the CLI with an `argparse.Namespace` plus `att.run` under `redirect_stdout` (`:146-150`). Reuse that.
  THE REQUIRED CASES: a MISSING directory counts zero and prints nothing; N files count N; a hidden file counts; a non-`.md` file counts; a nested directory behaves as E-01 documented; a non-empty inbox leaves `aw attention --check` at exit 0; no `Item` gains an inbox status and the class tally is unchanged; and the footer line appears ALONGSIDE the setup-needed line rather than replacing it (the E-02 trap, which is only caught by a test that sets both conditions).
  PUT THE NO-WRITE ASSERTION BESIDE ITS EXISTING TWIN. `tests/test_attention.py` already has `test_scan_does_not_stamp_aw_and_setup_needed_derives` (`:67`) and `test_writes_nothing` (`:255`), which exist because write-on-read was a real defect here. An inbox counter must not create `.aw/inbox/` by looking for it.
  - Depends on: E-03
  - Expected outcome: all listed cases covered in temporary repos, including a patched-open test proving no file is opened and a both-conditions test proving footer composition; no test reads the real `.aw/inbox/`; the counter provably creates nothing.
  - Execution state: pending

- [ ] E-05 SHOW THE FEATURE WORKING END TO END AND SHOW THE JSON SHAPE UNCHANGED.
  DEMONSTRATE IT, do not only unit-test it: create a temporary repo, drop several files including a hidden one and a non-`.md` one, run the real `aw attention`, and paste the board showing the line. Then remove the directory and paste the board showing no line.
  PROVE THE JSON DID NOT MOVE. `render_json` (`:1070`) emits `schema_version`, `mapping_version`, `valid`, `items`, `violations`, and `tests/test_attention.py` asserts `schema_version == 3` (`SCHEMA_VERSION` at `:33`). Since OQ-01 keeps the count out of the JSON, paste the key list before and after showing it IDENTICAL and the version unbumped. If a later decision adds the key, that is a schema bump plus a test update, and it is not this plan.
  RUN THE ADJACENT SUITES, since attention has many test files: `tests/test_attention.py`, `test_attention_contract.py`, `test_attention_notices.py`, `test_attention_priority_blocker.py`, `test_attention_compact.py`, `test_attention_stem.py`. `test_attention_contract.py` is the tripwire: if it fails, the design leaked into classification.
  - Depends on: E-04
  - Expected outcome: pasted real board output with and without a populated inbox; the JSON top-level key list and `schema_version` proven unchanged; every attention suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `setup_needed` (`attention.py:1405`) IS THE EXACT PRECEDENT: derived read-only, swallows exceptions, "NEVER creates anything", feeds a footer nudge, touches neither items nor exit code.
- THE FOOTER IS AN `elif` CHAIN (`attention.py:2940-2948`), so only ONE line prints. This is the single most important implementation detail and the item does not mention it.
- ADVISORY SECTIONS NEVER AFFECT THE EXIT CODE, and the code says so at `:2889-2891` and `:2922-2925`. The exit code is owned by `core.drift_exit_code(drift)` (`:2715`, `:2956`).
- `.aw/inbox/` IS GITIGNORED AND PER-CHECKOUT (`.aw/.gitignore:28`, `/inbox/`), and is ABSENT in this worktree. Absent must mean zero, silently.
- THE `/inbox/` PATTERN IS ANCHORED ON PURPOSE, because an unanchored `inbox/` would swallow the TRACKED comms lane `records/comms/shared/inbox/` and break `aw install` (`.aw/.gitignore:25-27`). Resolve one exact path; never search for directories named `inbox`.
- TWO DIFFERENT INBOXES EXIST. `.aw/inbox/` is the raw-drop lane (this plan). `.aw/records/comms/*/inbox/` is inter-agent comms, tracked in the `shared` case, and unrelated. There is no existing reader for the former; this plan writes the first one.
- `selectors._ID_RE` (`selectors.py:111`) IS POSITION-UNANCHORED AND HARVESTS A BODY-QUOTED `- Id:`. Reproduced. This is why listing-only is a hard constraint. Plan `76w6mq` will bound identity extraction to the metadata region; even after it lands, listing-only stays correct as defense in depth.
- `render_json` PINS A SCHEMA: `SCHEMA_VERSION = 3` (`:33`) with a test assertion. A new top-level key is a bump plus a test update.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | N/A | `attention.py`, `attention_contract.py` | ATTENTION IS TOTALLY BLIND TO THE INBOX: `grep -rn "inbox"` over both modules returns ZERO hits. The one `inbox` hit in `cli.py` is the comms help text. Fully live. | grep |
| F-2 | HIGH | `agent_workflows/selectors.py:111` | THE HARD CONSTRAINT IS JUSTIFIED BY MEASURED BEHAVIOR, not theory: `_ID_RE` is `(?m)^- Id:\s*([0-9a-z]{6})\s*$` used with `.search()`, and I fed it a body whose line 5 was a `- Id:` inside prose labelled a quoted example. It MATCHED and returned that id6. Listing cannot forge an identity; parsing can. | ran it |
| F-3 | HIGH | `agent_workflows/attention.py:2940-2948` | THE FOOTER IS AN `elif` CHAIN, so exactly one line prints. An `elif` addition would hide the nudge whenever setup is needed, i.e. on a fresh checkout, which is where a forgotten drop is likeliest. Not mentioned by the item. | source read |
| F-4 | MED | `.aw/inbox/` | THE DIRECTORY DOES NOT EXIST in this worktree, though the item and sibling plan `lznpv6:6` describe it as holding 10-plus files. It is gitignored and therefore per-checkout, making "absent means zero, silently" a first-class requirement. | `ls` |
| F-5 | N/A | `attention.py:1405` | THE PRECEDENT EXISTS: `setup_needed` is a derived read-only boolean feeding a footer nudge whose docstring stresses it "NEVER creates anything". An inbox counter is its structural twin. | source read |
| F-6 | N/A | `attention.py:2889-2891`, `:2922-2925`, `:2715`, `:2956` | ADVISORY OUTPUT NEVER AFFECTS THE EXIT CODE, stated in the code itself, and the exit code is owned solely by the drift set. This is the authority for the item's `--check` recommendation. | source read |
| F-7 | MED | `attention.py:1070`, `:33` | A NEW TOP-LEVEL JSON KEY IS A SCHEMA BUMP: `render_json` emits five keys and `SCHEMA_VERSION = 3` is asserted in `tests/test_attention.py`. Resolved by OQ-01 keeping the count out of the JSON here. | source read |
| F-8 | MED | `.aw/.gitignore:25-27` | THE `/inbox/` PATTERN IS ANCHORED TO PROTECT A TRACKED PATH: an unanchored `inbox/` would swallow `records/comms/shared/inbox/` and break `aw install` on a fresh repo. So the counter must resolve one exact path, never search by name. | source read |
| F-9 | N/A | pending plan `lznpv6` | THE SIBLING PLAN DOES NOT COVER THIS: it adds `aw adopt` only; grepping it for attention, count, waiting or nudge yields one incidental hit and no E-item. It independently reinforces the never-adopt-a-body-id6 rule. | that plan's text |
| F-10 | LOW | `attention.py:2507-2508` | A duplicated `return 3` sits in `run`, harmless dead code. Noted so it is not replicated by copy-paste; not fixed here (out of scope). | source read |

## Proposed changes (ordered, validatable)

1. E-01 adds a derived counter listing exactly `<repo>/.aw/inbox/`, silent and zero when absent, opening no file, with the listing-not-parsing rule stated in a comment.
2. E-02 renders one advisory footer line under an independent `if` so it composes with the existing chain, inventing no status and entering no classification.
3. E-03 keeps the exit code and `--check` untouched by never constructing a `Drift`.
4. E-04 proves non-reading mechanically with a patched-open test, plus the missing-directory, hidden-file, non-`.md`, nested, and footer-composition cases in temporary repos.
5. E-05 demonstrates the board end to end and proves the JSON shape and `schema_version` unchanged.

## Deferred / out of scope (with reason)

- `aw adopt` AND ANY CLEARING MECHANISM. Item `lsztiu`, now plan `lznpv6`. The two compose (the count says work is waiting, `adopt` clears it) but they are independent, as the item states.
- ADDING THE COUNT TO `--format json`. OQ-01. It would bump `SCHEMA_VERSION` (3 today) and require updating the schema assertion in `tests/test_attention.py`, which is a consumer-contract change out of proportion to a human nudge. Deferred deliberately, not overlooked.
- ANY CHANGE TO `selectors._ID_RE`. Plan `76w6mq` (from item `cqytxf`) bounds identity extraction to the metadata region. This plan's constraint is independent of that fix and stays correct after it lands.
- ANY CHANGE TO WHAT `.aw/inbox/` IS, its location, or its gitignore status. Sited outside `.aw/records/` deliberately; `lznpv6` excludes this too.
- A TYPED INVENTORY OF INBOX CONTENTS (kinds, ages, topics). Would require reading files, which the hard constraint forbids. A count is the whole feature.
- FAILING `--check` ON A NON-EMPTY INBOX. A waiting drop is not a repository defect and the file is local and gitignored, so other machines cannot see it. E-03 makes this structural rather than a matter of taste.
- THE DUPLICATED `return 3` AT `attention.py:2507-2508` (F-10). Harmless dead code, unrelated to this plan; noted so it is not copied.

## Scope check

- Over-scope: none. Both declared paths are modified: `agent_workflows/attention.py` by E-01 through E-03, `tests/test_attention.py` by E-04 and E-05.
- Under-scope: stated rather than left as `none`. Deliberately, `aw attention --format json` gains NOTHING (OQ-01), so a machine consumer still cannot see the inbox after this plan; only the human board can. `attention_contract.py` is untouched by design, and a need to touch it is a signal the design drifted into classification.

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. Then every attention suite explicitly: `tests/test_attention.py`, `test_attention_contract.py`, `test_attention_notices.py`, `test_attention_priority_blocker.py`, `test_attention_compact.py`, `test_attention_stem.py`. `test_attention_contract.py` is the tripwire for design drift: it owns enum totality and the class maps, so if it needs changing, the count has leaked into classification and the design is wrong. The single most important test is the patched-open proof that no inbox file is ever opened; a passing count is NOT evidence of that, since an implementation that parses every drop would also count correctly. Every case must be built in a temporary repo; never read the real `.aw/inbox/`.

## Spec / documentation sync

NO SPEC IS AMENDED. This adds an advisory human-view line and changes no contract: the attention CLASSIFICATION (which the spec corpus does govern) is untouched by design, no status is added, and the JSON schema is deliberately unchanged (OQ-01).
VERIFY THAT RATHER THAN ASSUMING IT, since a wrong answer means a silent contract change. Before executing, check whether the attention-registry spec (`.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`) constrains the attention OUTPUT surface or only the classification and JSON contract. If it specifies the output surface, add that file to `- Scope-Paths:` before the run starts, because both runners announce declared spec edits at run start and the finalize scope gate reconciles declared against actual. My reading is that the classification and JSON contract are what is specified and an advisory footer line falls outside it, exactly as the existing `gate_warnings` and `order_notices` lines do, but the executor must confirm and state the result.
`AGENTS.md` already documents `.aw/inbox/` and is INSTALLED from `agent_workflows/engine.py`, so if the inbox contract needs restating, edit the generator and not `AGENTS.md`. It should not need to: this plan surfaces a count and changes no rule about what an inbox file is.

## Open questions

### OQ-01: Should the count appear in `aw attention --format json`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO for this plan. `render_json` (`attention.py:1070`) emits exactly `schema_version`, `mapping_version`, `valid`, `items`, `violations`, and `tests/test_attention.py` asserts `schema_version == 3`. Adding a top-level key is a consumer-contract change requiring a version bump and a test update, which is out of proportion to a human nudge; and the count must NOT go inside `items`, since inbox entries are not artifacts and would then be classified. The feature's whole purpose is to catch a human's eye, which the human board does. If a machine consumer later needs it, that is a deliberate schema bump with its own justification.

### OQ-02: Does a nested directory count as one entry, or are its contents walked?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because either answer satisfies the item's requirement that a nested directory register as "something is waiting", and E-01 requires the choice be documented. Counting a directory as ONE entry is simpler, cannot recurse unboundedly, and matches the nudge framing; walking it gives a truer file count for a drop that arrives as an extracted archive, which the sibling plan notes is a real shape (`lznpv6` records a `.tgz` in the inbox). Recommend counting top-level entries only, since the number's job is to be nonzero and roughly right rather than exact, and a shallow scan is trivially bounded. State the decision in the comment either way.

### OQ-03: Should the line name `aw adopt` as the remedy?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, and the answer depends on execution ORDER rather than on design. `aw adopt` is the sibling plan `lznpv6` in this same Set (`awinbox`) and is `to-review`, so it may or may not have landed when this executes. If it has, naming it turns a bare count into an actionable nudge. If it has NOT, the line must not advertise a verb that does not exist, because a nudge pointing at a nonexistent command is worse than a bare count. Check at execution time and state which was true; do not add an `Item-Dependencies` edge for a purely cosmetic string.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the counter's source, showing the exact single path it resolves (proving it is not a recursive search for directories named `inbox`), the listing call used, and the comment stating the visible-as-files-never-interpreted-as-records rule with its reason. Paste a run against a MISSING directory returning zero without raising, and proof that the call did NOT create `.aw/inbox/` (list the parent before and after). Paste a run against a populated temporary inbox returning the right count. State the nested-directory decision (OQ-02).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered board with a populated inbox showing the line, and with an empty or absent inbox showing NO line. Paste the code showing an independent `if`, not an `elif` appended to the chain. Paste the both-conditions case (setup-needed AND a non-empty inbox) showing BOTH lines present, which is the F-3 trap. Paste the class tally with and without a populated inbox showing it IDENTICAL, proving no `Item` was created. Confirm `attention_contract.py` is unmodified by `git status`. State whether the remedy verb was named and why (OQ-03).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw attention` and `aw attention --check` exit codes with a NON-EMPTY inbox, both matching their values with an empty one (expected 0 on a valid view). Paste a grep of the new code proving no `Drift` is constructed. State whether `--check` prints the line and why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the patched-open test source and its PASSING output, where the file-open path RAISES and the count still succeeds; this is the plan's central safety proof and a correct count alone does not establish it. Paste each required case: missing directory silent zero, N files count N, hidden file counted, non-`.md` counted, nested per OQ-02, `--check` still 0, class tally unchanged, footer composition. Paste proof no test references the real `.aw/inbox/` (a grep of the test file). Paste the no-write assertion beside its existing twins at `tests/test_attention.py:67` and `:255`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste real `aw attention` output from a temporary repo containing several drops including a hidden one and a non-`.md` one, then with the directory removed. Paste the `render_json` top-level key list BEFORE and AFTER showing it identical, and `schema_version` still 3. Paste all six attention suites green. Paste the bare full-suite summary line with the worktree baseline beside it and a node-id comparison. Paste `git diff --cached --name-only` showing only this plan's declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the two paths in `- Scope-Paths:`. Do NOT modify `agent_workflows/attention_contract.py`: a need to is a signal the count leaked into classification. Do NOT add a top-level JSON key or bump `SCHEMA_VERSION` (OQ-01, resolved). Do NOT construct a `Drift` for inbox entries. Do NOT open or parse ANY inbox file, for any reason, including "just to check it is markdown". Do NOT search recursively for directories named `inbox`; resolve `<repo>/.aw/inbox/` exactly, or you may sweep the tracked comms lane. Do NOT change `.aw/inbox/`'s location or gitignore status, and do NOT create the directory. Do NOT change `selectors._ID_RE` (owned by plan `76w6mq`). Do NOT implement `aw adopt` (plan `lznpv6`). Do NOT read the real `.aw/inbox/` from a test. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `attention.py` is nearly 3000 lines and under active change. Find `setup_needed`, `render_json`, `render_board`, `render_table`, `scan`, and `run` by name, and find the footer block by its `TODO: Run \`/aw setup-repo\`` text rather than by line number.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 9iiqmm --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `plbkp5` (carried as `- From-Backlog:`) may be closed `done`: this plan delivers the whole feature the item asks for, since OQ-01's JSON deferral is a deliberate scope decision rather than an unmet requirement. That item carries no release gate, so none is inherited.
