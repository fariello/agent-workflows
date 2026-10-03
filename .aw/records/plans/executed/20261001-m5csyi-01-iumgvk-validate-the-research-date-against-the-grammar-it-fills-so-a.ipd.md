# IPD: Validate the research date against the grammar it fills so a traversal or newline cannot write outside the records tree

- Date: 2026-10-01
- Kind: child
- Concern: `research_cmd.plan_new` interpolates `date_str` into the derived filename with NO validation, so a traversal in `--date` writes a research record outside the records tree. Measured in this lane against a fixture nested four levels deep: `aw research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` exits **0**, prints `wrote <repo>/.aw/records/research/../../../../ESCAPED-x-00-75o83d-x.findings.md`, and the file lands FOUR DIRECTORIES ABOVE the records tree, outside the repository (F-01). THREE THINGS THE BACKLOG ITEM DOES NOT NAME, each of which changes the fix. (1) THE DEFECT IS NOT CONFINED TO `research new`: `aw research new-comparison` shares `date_str` and escapes THREE files in one command (F-02), and `aw adopt` reaches `plan_new` directly with the same flag, so a verb-only guard leaves two paths open. (2) THE SAME FLAG INJECTS FRONT-MATTER KEYS, a second defect class the traversal work must not leave behind: a newline in `--date` writes a real `blocks-release: next` key that FUNCTIONS, with `aw releases show next` listing the record under `release-blockers (1)` while `aw check research`, `aw check all` and `aw research index --check` all report clean (F-07, F-08). Plan `deftzy` (Set `7w6zsl`) explicitly EXCLUDES `--date` and names this item as its carrier, so nothing else closes it. (3) THE SIBLING'S REGEX CANNOT BE PORTED VERBATIM, which is what the item's "reuse the `ribg85` fix shape" instruction would produce: research's `--date` is documented and parsed as `YYYYMMDD`, not the ISO `YYYY-MM-DD` that `prompts.run_new` and the shipped `specs.run_new` guard validate, so `\A\d{4}-\d{2}-\d{2}\Z` would refuse every legitimate research date and accept none (F-11).
- Scope: Validate `date_str` at `research_cmd.plan_new` and `research_cmd.plan_new_comparison` against the date slot of the grammar those functions fill (`\A\d{8}\Z` plus a calendar check), refusing through each function's EXISTING `(None, error)` return channel before any id6 is minted or any path is derived; then assert destination containment in `research_cmd._emit_and_write`, the one preview-and-apply funnel both planners feed, so a derived path outside the resolved research root is refused on BOTH the `--apply` and the dry-run arm. DELIBERATELY NOT COVERED: `aw research set-assign`, whose identical traversal MOVES an existing record and is already carried by open backlog item `0ougsh`; the descriptive-field injection through `--summary`, `--topic` and `--consumed-by`, which plan `deftzy` owns; and `prompts.run_new`'s format-only guard, which this plan does not upgrade (see Deferred).
- Scope-Paths: agent_workflows/research_cmd.py, tests/test_research_date_containment.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: m5csyi
- Blocks-Release: next
- Set: m5csyi
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: iumgvk

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: iumgvk verified (set m5csyi, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review complete; APPROVE WITH REVISIONS APPLIED

- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed), PR-002 (LOW, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed). Re-verified at lane HEAD `6d48f3f94` in nested scratch fixtures: F-01, F-02 and F-09 reproduce, `strptime` refuses `99999999`, `20261332` and `20260230`, and the `today = date_str or ...` siting holds in both planners. Changed: the fixture-depth safety bound was INSUFFICIENT. A scratch repo with no `.aw/records/research` resolves its research root under `$HOME/.aw/projects/...`, and a review probe with a fixture-safe depth wrote `$HOME/.aw/ESC-x1-00-dkj15o-x1.findings.md` outside the temp base. E-04 now requires a pre-created research dir, isolated `HOME`/`XDG_CONFIG_HOME`, and a target computed from the resolved root (PR-001). The regex is now ASCII-only `[0-9]{8}` (PR-002). The E-05(e) committed pin of the live `set-assign` escape would break when `plb8jx` lands, so it is now V-05 scratch evidence (PR-003). The byte-identical non-regression is now id6-pinned (PR-004). The nonexistent `run_new_from_plan` caller is removed, and the archive proof is replaced with a direct shard-path call, since archive bypasses `_emit_and_write` (PR-005). ACTION FOR THE HUMAN: the stray file `$HOME/.aw/ESC-x1-00-dkj15o-x1.findings.md` and the directory `$HOME/.aw/projects/repo-7c3bc1/` were written by this review's probe and are outside this lane's permissions to delete. Record: `.aw/records/reviews/20261002-m5csyi-01-iumgvk-validate-the-research-date-against-the-grammar-it-fills-so-a.review.md`.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `m5csyi`. The item's reported vector REPRODUCES EXACTLY as filed, including its false-negative warning (a shallow fixture measures the filesystem's permissions, not the verb). Four things the item does not state were measured and changed the plan rather than decorating it. FIRST, the item's central instruction, "whichever shape `ribg85` lands on should be reused here rather than re-litigated", CANNOT BE FOLLOWED LITERALLY: research's `--date` grammar is `YYYYMMDD` while the shipped `specs` guard validates `YYYY-MM-DD`, so porting that regex would refuse every legitimate research date (F-11). The REUSE is therefore of the two-guard SHAPE (format-then-calendar at the input, containment at the write) with the regex re-derived from research's own `_CORE_RE` date slot, which is a stronger form of reuse than copying a literal. SECOND, the defect is wider than the one verb the item names: `new-comparison` escapes three files per invocation and `aw adopt` reaches the same planner, which is why the guard is sited at the PLANNERS and not at `run_new` (F-02, F-03). THIRD, the SAME flag injects functioning front-matter keys including a release gate that `aw releases show next` honors (F-07, F-08), and plan `deftzy` explicitly excludes `--date` naming this item as its carrier, so the injection half has no other owner and is closed here. FOURTH, `aw adopt` already REFUSES the traversal by validating the derived name after planning (F-04), which is in-repo proof that the fix shape works and also the reason the plan can bound its own blast radius. Also measured: the whole live research population would pass the proposed guard (F-10), so this is purely preventive with no migration step.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every research creation path refuse a `--date` it cannot safely use, so the verb cannot write a record outside the tree its own index walks, and cannot smuggle a status, a priority, or a functioning release gate into a record through the one front-matter value nothing validates. The escape is the severe half; the injected release gate is the half that currently passes every checker in the repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: validate the value at the planner both verbs and `aw adopt` share

- [x] E-01 Add a module-private date guard to `agent_workflows/research_cmd.py` that judges ONE candidate date string and returns the refusal MESSAGE or `None`, so every creation path refuses with identical wording. Shape: `_refuse_unsafe_date(verb: str, value: Optional[str]) -> Optional[str]`, returning `None` when `value` is `None` (the omitted-flag case, which must keep defaulting to today) and otherwise refusing anything that is not an eight-digit real calendar date.

  DERIVE THE REGEX FROM RESEARCH'S OWN GRAMMAR, AND DO NOT PORT THE SIBLING'S LITERAL. This is the single most important instruction in the plan because the backlog item's own guidance points the other way. `prompts.run_new` and the shipped `specs.run_new` guard both validate `\A\d{4}-\d{2}-\d{2}\Z`, and research's date slot is `(?P<date>\d{8})` in `artifact_naming._CORE_RE` (re-exported as `research_contract._CORE_RE`), with `cli.py`'s own help string for this flag reading `Override the set date (YYYYMMDD).` Measured (F-11): the ISO regex refuses `20260929`, which is the ONLY shape the research grammar accepts, so a verbatim port would refuse every legitimate date and break the verb outright. Use `\A[0-9]{8}\Z` (see the `\d` note below).
  THEN ADD A CALENDAR CHECK, because the eight-digit shape alone is NOT sufficient and this is a different conclusion from the path half. Measured: `\A\d{8}\Z` ACCEPTS `99999999` and `20261332`, both of which are unreachable calendar dates that would be stamped into the filename, the `created:` front-matter value, and the set date every later record in that set inherits. Use `datetime.datetime.strptime(value, "%Y%m%d")` and treat `ValueError` as the refusal; measured, it rejects `99999999`, `20261332` and `20260230` while accepting `20260929`.
  STATE THE FORMAT-VERSUS-CALENDAR DISTINCTION IN THE CODE COMMENT rather than leaving it to be rediscovered, naming the two shapes the regex alone would admit. The shipped `specs` guard carries exactly such a comment and resolved the same question in its OQ-01; this plan reaches the same answer on research's own evidence, not by deference.
  THE REFUSAL MESSAGE MUST NAME THE VERB, THE FLAG, THE REQUIRED FORMAT AND THE RECEIVED VALUE, matching the shape the sibling verbs already emit (`aw prompts new: --date must be YYYY-MM-DD (got '...')`) with `YYYYMMDD` substituted. Keep the value `!r`-quoted so a traversal or an embedded newline is visible in the message instead of mangling the terminal.
  - Depends on: none
  NOTE ON `\d` (plan-review 2026-10-02, PR-002): in Python 3 `\d` matches any Unicode decimal digit, so `\A\d{8}\Z` ACCEPTS the fullwidth `'２０２６０９２９'`. The calendar check happens to refuse it (`strptime` raises `ValueError`), but then the format check is not the gate it claims to be. Use `\A[0-9]{8}\Z` (or `re.ASCII`), so the format check alone closes the non-ASCII class, and add that value to the test inputs.
  - Expected outcome: a helper importable as `research_cmd._refuse_unsafe_date` that returns `None` for `None` and for `'20260929'`, and a refusal for `'２０２６０９２９'` (fullwidth digits), and a message naming the verb, `YYYYMMDD` and the received value for each of `'../../../../ESCAPED'`, `'/abs/ESCAPED'`, `'2026-09-29'`, `'9999-99-99'`, `'notadate'`, `''`, `'99999999'`, `'20261332'`, and `'20260929\nstatus: reference'`.
  - Execution state: performed

- [x] E-02 CALL that guard from `research_cmd.plan_new` and `research_cmd.plan_new_comparison`, returning its message through each function's EXISTING `(None, error)` tuple so both verbs' established error rendering (human `error: <msg>` and the `--agent` `cannot-run` envelope at exit 2) is reused rather than forked.

  GUARD AT THE PLANNER, NOT AT THE CLI HANDLER, AND THE REASON IS MEASURED. `aw adopt` calls `research_cmd.plan_new` DIRECTLY, passing `date_str=getattr(args, "date", None)` from `artifact_adopt`, so a guard in `research_cmd.run_new` would leave the adopt path reading an unvalidated flag. This matches the siting that plan `deftzy` independently chose for the descriptive-value guard on these same two planners, for the same reason, so the two plans will not fight over the call site.
  SITE THE CALL BEFORE THE ID6 IS MINTED. In `plan_new`, place it above `today = date_str or date.today().strftime("%Y%m%d")`, so a refusal consumes no id6 from the repository-wide pool and touches no filesystem; the existing `kind`, `priority`, `model` and slug refusals already sit above that line and establish the position. In `plan_new_comparison`, place it above its own `today = date_str or ...` for the same reason, noting that function mints N+2 ids and so has more to waste.
  PASS THE VERB NAME EACH PLANNER IS SERVING so the message names the command the user actually typed: `"aw research new"` from `plan_new` and `"aw research new-comparison"` from `plan_new_comparison`. The adopt path reaches `plan_new`, so it will report `aw research new`; that is a known cosmetic imprecision and is recorded in Deferred rather than solved by threading a verb parameter through `artifact_adopt`.
  DO NOT CHANGE THE OMITTED-FLAG DEFAULT. `date_str=None` must still fall through to `date.today().strftime("%Y%m%d")`; the guard returns `None` for `None` precisely so this path is untouched, and V-02 asserts it.
  - Depends on: E-01
  - Expected outcome: `aw research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` exits 2 with the refusal and writes nothing, where before it exited 0 and created a file four directories above the records tree; `aw research new-comparison ... --date ../../../../ESCAPED --apply` likewise refuses instead of writing three escaping files; `aw adopt <drop> --type research --date ../../../../ESCAPED --apply` refuses with the date message rather than reaching its own later name check; and `--date 20260929`, plus every invocation that omits `--date`, still writes exactly the path it wrote before.
  - Execution state: performed

### Task group 2: confine the destination at the one funnel both planners feed

- [x] E-03 Add a DESTINATION-CONTAINMENT assertion to `research_cmd._emit_and_write`, refusing when any planned file's RESOLVED path does not lie inside the RESOLVED research root, with exit 2 and a message naming the offending destination and the tree it escaped.

  THIS IS DEFENCE IN DEPTH AND IS NOT REDUNDANT WITH E-01/E-02, which is why it is a separate item. E-01 guards the one input measured to traverse today; E-03 guards the PROPERTY that matters, that these verbs only ever write inside their own tree, and it holds for any future caller or any future unvalidated field that reaches the name builder. A guard that is only ever reached after another guard has refused is untested, which is why V-03 requires it be exercised with E-01 bypassed.
  `_emit_and_write` IS THE CORRECT SITE because it is the ONE funnel both planners feed and it already handles BOTH arms: it is called by `run_new` and `run_new_comparison`, its only two callers (there is no `run_new_from_plan`; plan-review 2026-10-02, PR-005), and it contains both the `if not apply:` preview branch and the `_atomic_write` loop. Place the assertion ABOVE the existing no-clobber loop, which is already positioned "up front (so a partial apply never happens)" and so is the function's established place for a pre-flight refusal. Siting it above that loop makes the preview arm refuse too.
  THE DRY-RUN ARM MUST REFUSE, NOT MERELY THE APPLY ARM. Measured at HEAD (F-05): a traversing preview exits 0 and prints `--- would write <escaping path> ---`, and its `--agent` form emits `"outcome":"clean","exit":0,"applied":false` with a `changes` entry of `"kind":"create"` naming the escaping path. A dry run is the one tool an operator has for checking a command before running it, so a preview that reports an out-of-tree write as clean is the same defect one step earlier. This is the identical siting error review caught in the sibling plan, where the guard had been placed before the `mkdir` and so lived in the apply branch only; do not repeat it.
  USE THE ESTABLISHED IN-REPO IDIOM, NOT A `..` SUBSTRING TEST: resolve both paths and call `Path.relative_to`, treating `ValueError` as the escape, exactly as `check_engine.resolve_evidence_artifact` does under its comment "containment: candidate must be inside the repo root (no ../ escape)", and as the shipped `specs.run_new` guard does. A substring test for `..` is wrong in both directions: it rejects a legitimate directory named `..x` and it MISSES an absolute-path destination, which F-06 measured actually occurs (an absolute `--date` wrote to a path with no `..` in it at all).
  DERIVE THE BOUNDARY FROM THE SAME RESOLVER THAT BUILT THE PATH. `_emit_and_write` does not currently receive the research root, so take it from `args` via the existing `_research_root(args)` helper (which calls `research_contract.resolve_research_root`), NOT from a hard-coded `.aw/records/research`. That resolver deliberately falls back to a legacy `.agents/docs/research` tree when present, so a hard-coded modern path would refuse every legitimate write in a legacy-layout repository. `args` is already an optional parameter of this function; when it is `None` the root cannot be derived, so SKIP the assertion in that case rather than guessing, and say so in the comment. That is safe because every CLI path passes `args` and the planner-level guard still applies; V-03 pins the behavior rather than leaving it implied.
  ACCEPT ANY DESCENDANT OF THE ROOT, NOT ONLY ITS IMMEDIATE CHILDREN. Test containment against the research ROOT. `research_archive` places records in `research_root / sub / filename` for its `YYYYMM-Www` shards, and `_set_date_for_set` and `_existing_id6s` already `rglob` those shards, so nested placement is part of this tree's shape. NOTE (plan-review 2026-10-02, PR-005): `research_archive.apply_moves` writes through `research_refs._atomic_write` and does NOT pass through `_emit_and_write`. So `aw research archive` cannot regress from this change, and running it proves nothing about the assertion. Prove descendant acceptance DIRECTLY instead: call `_emit_and_write` with a planned file at `research_root / <shard> / <name>` and show that it is not refused.
  - Depends on: E-02
  - Expected outcome: with E-01's guard bypassed in a scratch session, a traversing derived name is refused by E-03 alone at exit 2 naming the destination and the tree, and nothing is written; the SAME bypassed call WITHOUT `--apply` also exits 2 rather than printing `--- would write <escaping path> ---`, and its `--agent` form emits a refusal rather than a clean `create` envelope; an absolute-path destination is refused by the same assertion; and every conforming `aw research new` and `new-comparison` still writes and still previews exactly the paths it did before, in BOTH a `.aw/records/research` and a legacy `.agents/docs/research` layout, and a planned file nested in a shard subdirectory of the root is accepted by the assertion.
  - Execution state: performed

### Task group 3: pin the escape, the injection, and the non-regressions

- [x] E-04 Add `tests/test_research_date_containment.py` pinning the ESCAPE as the primary property, for `research new`, `new-comparison`, and `aw adopt`. Assert that NO file exists anywhere under the temp base outside the research tree, not merely that the command failed, because an exit code alone does not distinguish the fix from the permissions accident the backlog item warns about.

  THE FIXTURE MUST BE NESTED AND THE TRAVERSAL DEPTH MUST BE BOUNDED TO THE FIXTURE DEPTH. THIS IS A SAFETY REQUIREMENT, NOT A STYLE NOTE. The verb's `_atomic_write` path creates its destination's parent, so an OVER-DEEP traversal does not fail, it SUCCEEDS somewhere unintended: review of the sibling plan ran exactly such a probe and wrote a real file outside its scratch area that it then could not delete. So build the fixture at `<tmp>/a/b/c/repo`, compute the number of `../` segments from the fixture's own depth, and assert BEFORE each destructive probe that the resolved target is inside the temp base, skipping the probe if it is not. COMPUTE THE TARGET FROM THE RESOLVED RESEARCH ROOT, NOT FROM THE FIXTURE PATH, AND PIN WHERE THAT ROOT RESOLVES (plan-review 2026-10-02, PR-001, measured destructively at review). `research_contract.resolve_research_root` asks `record_producers.resolve_record_path` first. For a scratch git repo that is not a registered project and has no `.aw/records/research` directory, that resolves to `$HOME/.aw/projects/<name>-<hash>/records/research`, which is OUTSIDE the temp base. A review probe at `<tmp>/a/b/c/repo` with `--date ../../../../ESC --apply` therefore wrote `$HOME/.aw/ESC-x1-00-dkj15o-x1.findings.md`, not a file under `<tmp>`, and the fixture-path arithmetic said the target was safe. So every fixture MUST (1) pre-create `<repo>/.aw/records/research`, (2) set `HOME` and `XDG_CONFIG_HOME` to the temp base for every subprocess and every in-process call (`monkeypatch.setenv`), and (3) compute the probe target as `(research_root / date).resolve()`, where `research_root` comes from `research_contract.resolve_research_root(resolve_verb_repo_root(str(repo)))` under that environment, and assert that BOTH the root and the target are inside the temp base before running. With all three in place, the same probe landed at `<tmp>/a/b/c/ESC-...`, which is inside the base. The probe script this plan was authored from does exactly this and its assertion line is the shape to copy. A test that escapes its own tmpdir can damage the checkout it runs in, which matters doubly because `AGENTS.md` states this checkout is SHARED.
  THE NESTING MUST CARRY A COMMENT SAYING WHY, and the comment must NOT promise a permission error. The backlog item reports that a shallow fixture refuses with `[Errno 13] Permission denied` because the escape lands on `/`; that refusal is an accident of filesystem permissions and is environment-dependent, so a shallow fixture yields a FALSE GREEN where the escape is unwritable and COLLATERAL DAMAGE where it is writable. Both are disqualifying and neither is a guard.
  AVOID THE SET-DATE MASKING TRAP, which will silently make a naive escape test pass before the fix. Measured (F-09): `plan_new` calls `_set_date_for_set`, so when a record already exists in the derived set, the EXISTING set's date wins and the traversing `--date` never reaches the filename at all; the escape only occurs for a set's FIRST record. A test that seeds a record and then probes the same slug measures nothing. Use a FRESH slug (hence a fresh derived set) for every escape probe, and add one test that pins the masking itself so the trap is documented rather than merely dodged.
  Cover: a traversal landing above the records tree, an absolute-path `--date`, a traversing DRY RUN with no `--apply` (E-03's second arm), the `new-comparison` case where three files escape in one command, and the `aw adopt` path. Drive at least one case through `cli.main` rather than the planner alone, following the established pattern in `tests/test_research_cmd_create.py`.
  - Depends on: E-03
  - Expected outcome: a new module whose escape cases FAIL against pre-E-01 code with the escaped file PRESENT on disk inside the temp base, and PASS after, with the temp base containing no file outside the research tree; and whose every destructive probe is bounded by an asserted in-tmpdir target so the module cannot damage the checkout it runs in.
  - Execution state: performed

- [x] E-05 In the same module, pin the FRONT-MATTER INJECTION and the non-regressions.

  INJECTION, which is a distinct defect class from the traversal and must be named as such in the test names and a comment. A newline in `--date` writes real sibling keys into the `---` fenced block, because `research_contract.parse_frontmatter` is a line-wise `key: value` splitter rather than a YAML parser. Pin the SEVERE measured case (F-08): with a record already in the set so the SET DATE keeps the filename legal, `--date $'20260101\nstatus: reference\nblocks-release: next\npriority: high'` wrote a clean-named record carrying a FUNCTIONING release gate, with `aw releases show next` listing it under `release-blockers (1)` and `aw attention --format json` reporting `"blocks_release":"next","priority":"high"` on a record nothing gated, while `aw check research`, `aw check all` and `aw research index --check` ALL reported clean. Assert the refusal now, and assert in a comment that this is why the fix is not merely about paths. Pin the simpler case too (F-07): on a set's first record the same newline produces a filename containing a literal newline AND the injected keys.
  FABRICATION: assert `--date 99999999` and `--date 20261332` are refused, and document in the test name that this half is about record IDENTITY rather than path safety. A fabricated filename date is an already-realized harm in this repository, recorded in open backlog item `tf4jz5`.
  DETECTION ASYMMETRY, pinned so the under-scope is evidence rather than assertion: after a pre-fix escape, `aw research index --check --dir <repo>` reports `index --check: clean` and `aw research find` lists only the surviving record, because the escaped file is not in the tree they walk (F-12); whereas a MALFORMED-but-in-tree name IS caught by `aw research index --check` as `name-invalid` while `aw check research` reports `"outcome":"conforms"` (F-13). Record both; neither is fixed by this plan.
  NON-REGRESSIONS: (a) `--date 20260929` writes the same path and bytes as before the change, with the id6 held fixed. The mint is random (`artifact_core.mint_id6`), so an unpinned comparison against a HEAD reference can never match (plan-review 2026-10-02, PR-004). Monkeypatch `research_cmd._mint_research_id6` (and `research_cmd.generate_id6` for `new-comparison`) to a fixed value, or compare with the id6 segment and `id:` value normalized, and state which; (b) omitting `--date` still defaults to today, for `new`, `new-comparison` AND `adopt`; (c) a conforming DRY RUN still previews the same path and still exits 0 on both arms E-03 touches; (d) the existing refusals (`--kind`, `--slug`-or-`--summary`, `--priority`, `--models`) keep their exit codes and messages; (e) `research set-assign` and `research mv` are UNCHANGED by this plan. Show this as V-05 EVIDENCE (a bounded scratch probe of the surviving `set-assign` escape, recorded with carrier `0ougsh`), NOT as a committed test (plan-review 2026-10-02, PR-003). Backlog `0ougsh` has already graduated to pending plan `plb8jx`, which fixes exactly that escape. A committed test asserting the escape SURVIVES would turn red the moment `plb8jx` lands, in whichever order the two execute. It would also commit a probe that MOVES a file outside the records tree, to run on every suite invocation. A test must not pin a live defect as expected behavior.
  - Depends on: E-04
  - Expected outcome: the injection, fabrication and asymmetry cases are pinned; non-regression groups (a) to (d) pass as committed tests; and (e) is recorded as V-05 scratch evidence with carrier `0ougsh` / plan `plb8jx` named, so the scope boundary is measured without a test that pins a live defect.
  - Execution state: performed

## Project conventions discovered (Step 0)

- RESEARCH'S DATE GRAMMAR IS `YYYYMMDD`, NOT ISO, which is the single fact that prevents this plan from being a copy of its sibling. `artifact_naming._CORE_RE` (re-exported as `research_contract._CORE_RE`) is `\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z`, and `cli.py`'s help for this flag reads `Override the set date (YYYYMMDD).`
- THE TWO-GUARD SHAPE IS ESTABLISHED IN-REPO, so this plan ports a shape rather than inventing policy: `prompts.run_new` validates its `--date` against a format regex and refuses at exit 2 before deriving a name, and executed plan `ribg85` added both a format-plus-calendar guard and a `relative_to`-based containment assertion to `specs.run_new`.
- THE CONTAINMENT IDIOM IS `relative_to` WITH `ValueError` AS THE ESCAPE SIGNAL, used by `check_engine.resolve_evidence_artifact` under the comment "containment: candidate must be inside the repo root (no ../ escape)" and by the shipped `specs.run_new` guard. Not a `..` substring test.
- GUARDS BELONG AT THE PLANNER FOR THIS MODULE, because `aw adopt` calls `research_cmd.plan_new` directly rather than going through `run_new`. Pending plan `deftzy` independently reached the same siting for the descriptive-value guard on the same two planners.
- `_emit_and_write` IS THE SINGLE PREVIEW-AND-APPLY FUNNEL for both creating verbs, and its no-clobber loop is already sited "up front (so a partial apply never happens)", which is the function's established place for a pre-flight refusal that must bind both arms.
- ONLY THE DATE SEGMENT IS UNSANITIZED among the name inputs, which is why this plan guards the date and nothing else: `research_contract.kebab` flattens the others, measured as `kebab('../../../etc/passwd') == 'etc-passwd'` and `kebab('x\n- Blocks-Release: next') == 'x-blocks-release-next'`, and `plan_new` applies it to both `slug` and `set_id`.
- `aw adopt` ALREADY REFUSES THE TRAVERSAL BY VALIDATING THE DERIVED NAME after planning (`artifact_adopt` returns `derived a non-conforming name: ...` at exit 2), which is in-repo proof that enforcing the grammar closes the path hole, and is why the adopt path is a non-regression rather than a second fix.
- THE REFUSAL CONVENTION FOR THESE VERBS IS EXIT 2 THROUGH THE PLANNER'S ERROR TUPLE: `run_new` and `run_new_comparison` both render a planner error as human `error: <msg>` and as a `cannot-run` `CommandResult` at exit 2.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection (AGENTS.md).

## Findings

All findings were DRIVEN in this lane at HEAD `7168b42b8`, against temporary fixture repositories nested four levels deep, with every traversal probe's resolved target asserted inside the temp base BEFORE the probe ran. None of this is read off the source.

| # | Finding | Evidence |
|---|---|---|
| F-01 | `aw research new --date` TRAVERSES AND WRITES A RECORD FOUR DIRECTORIES ABOVE THE RECORDS TREE, outside the repository, at exit 0. The item's report reproduces exactly. | Fixture at `<tmp>/a/b/c/repo`: `research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` printed `wrote <repo>/.aw/records/research/../../../../ESCAPED-x-00-75o83d-x.findings.md` at `rc=0`, and the file was found at `a/b/c/ESCAPED-x-00-75o83d-x.findings.md`. |
| F-02 | `aw research new-comparison` HAS THE SAME DEFECT AND ESCAPES THREE FILES IN ONE COMMAND, which the backlog item does not mention. This is why the guard is sited at both planners. | `research new-comparison <repo2> --set cmpset --slug x --models gpt56 --date ../../../../ESCAPED --apply` exited `0` and wrote `ESCAPED-cmpset-00-mp3owi-x.research-prompt.md`, `ESCAPED-cmpset-01-mzxv5p-x.gpt56.research-report.md` and `ESCAPED-cmpset-02-v1kkcz-x.reconciliation.reconciliation-report.md`, all in `a/b/c/`. `plan_new_comparison` takes the same `date_str` and passes it to `R.ResearchName`. |
| F-03 | `aw adopt` READS THE SAME UNVALIDATED FLAG INTO THE SAME PLANNER, so a guard in `run_new` alone would leave it open. | `artifact_adopt` calls `_rc.plan_new(..., date_str=date_str, existing_ids=existing)`, where `date_str=getattr(args, "date", None)`. The call site is the comment "CALL the existing planner ... This is why calling remains preferable to copying: one name-deriver, one grammar." |
| F-04 | `aw adopt` NEVERTHELESS REFUSES THE TRAVERSAL TODAY, by validating the derived name AFTER planning. This is in-repo proof that enforcing the grammar's date slot closes the path hole, and it is why adopt is a non-regression here rather than a second fix. | Driven with an inbox drop: `adopt <drop> --dir <repo> --type research --kind findings --slug x --summary s --date ../../../../ESCAPEDH --yes --apply` exited **2** with `error: derived a non-conforming name: NameError_(message="core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>' (got 'ESCAPEDH-x-00-y4z1nx-x')")`, and nothing was written anywhere under the temp base. The guard is `parsed, name_err = _R.parse_name(planned.path.name)` in `artifact_adopt`. |
| F-05 | THE DRY RUN LEAKS THE ESCAPE TOO, so a guard sited only on the apply arm would not see half the defect. | Same fixture, no `--apply`: `rc=0` printing `--- would write <repo>/.aw/records/research/../../../../ESCAPED-x-00-b4mku5-x.findings.md ---` plus the rendered front matter carrying `created: ../../../../ESCAPED`. With `--agent`: `{"outcome":"clean","exit":0,...,"applied":false,"changes":[{"kind":"create","path":"...research/../../../../ESCAPED-x-00-v7maey-x.findings.md"}]}`. No file is written on this arm, so the harm is a preview reporting an out-of-tree write as clean. |
| F-06 | AN ABSOLUTE-PATH `--date` ESCAPES WITH NO `..` IN IT AT ALL, which is why E-03 must use `relative_to` and not a substring test. | `research new <repoD> ... --date <tmp>/ABSOUT --apply` exited `0` and wrote `<tmp>/ABSOUT-x-00-thfz2a-x.findings.md`, i.e. directly into the temp base, four levels above the fixture's records tree. |
| F-07 | THE SAME FLAG INJECTS FRONT-MATTER KEYS, a SECOND defect class. A newline in `--date` produces both a filename containing a literal newline and real sibling keys in the `---` block. | `--date $'20260929\nstatus: reference\nblocks-release: next' --apply` exited `0`; the written file's name is `'20260929\nstatus: reference\nblocks-release: next-nl-00-8dexqv-nl.findings.md'` and its body carries `created: 20260929`, then `status: reference`, then `blocks-release: next` as REAL keys, followed later by the legitimate `status: todo`. |
| F-08 | THE INJECTED RELEASE GATE FUNCTIONS, AND THE FILENAME CAN STAY CLEAN, which makes this the severe half of the injection class. Exploiting the set-date masking of F-09 keeps the name legal while the raw value still reaches `created:`. | In a fixture holding a `planned` release record: seeded set `inj` with `--date 20260101`, then `--date $'20260101\nstatus: reference\nblocks-release: next\npriority: high' --apply` exited `0` and wrote the CLEANLY NAMED `20260101-inj-01-vqjmif-inj.findings.md` whose body carries `status: reference`, `blocks-release: next`, `priority: high`. Then `aw releases show next` printed `release-blockers (1)` listing `vqjmif  research  todo  high`, and `aw attention --format json` reported `"blocks_release":"next","priority":"high"` for it. Meanwhile `aw check research --agent` reported `"outcome":"conforms"` and `aw check all --agent` `"outcome":"conforms","findings":0`. |
| F-09 | A NAIVE ESCAPE TEST PASSES BEFORE THE FIX because of SET-DATE MASKING, so E-04's fresh-slug requirement is load-bearing rather than stylistic. | `plan_new` calls `_set_date_for_set(research_root, derived_set, today)`, so an EXISTING set's date wins. Driven: with `20260101-sm-00-466mxr-sm.findings.md` already present, the same slug with `--date ../../../../ESCAPEDL --apply` exited `0` and wrote `20260101-sm-01-26762k-sm.findings.md` INSIDE the tree with nothing escaping, while the raw traversal still landed in that record's `created: ../../../../ESCAPEDL`. The escape only occurs for a set's FIRST record. |
| F-10 | THE LIVE POPULATION WOULD PASS THE PROPOSED GUARD, so this plan is purely preventive with no migration step. | Over all 133 `.md` files under `.aw/records/research` (including `archive/` shards): 0 names have eight leading digits that are not a real calendar date; the 6 non-matching names are `README.md` x4, `conformance-results-template.md` and one further non-record. `aw check research --agent` reports `"outcome":"conforms"` with its one standing `check.collisions-not-checked` advisory. |
| F-11 | THE SIBLING'S REGEX CANNOT BE PORTED VERBATIM, which contradicts the backlog item's own "reuse the fix shape" instruction read literally, and would break the verb if followed. | `\A\d{4}-\d{2}-\d{2}\Z` matched against each candidate: it REFUSES `20260929`, the only shape `research_contract._CORE_RE` accepts, and ACCEPTS `2026-09-29` and `9999-99-99`, both of which that grammar REJECTS (`core must be 'YYYYMMDD-...'`). Conversely `\A\d{8}\Z` accepts `20260929` and refuses every traversal, newline and ISO form tested, but ACCEPTS `99999999` and `20261332`, which is why E-01 adds the calendar check: `strptime('99999999', '%Y%m%d')` raises `ValueError: unconverted data remains: 99`. |
| F-12 | THE ESCAPED RECORD IS INVISIBLE TO THE TREE'S OWN CHECKER AND INDEX, so nothing downstream detects the F-01 write. | After an escape in a fixture whose index was clean: `aw research index --check --dir <repo>` printed `index --check: clean` at `rc=0`, `aw research index --dir <repo> --agent` reported `up to date ... (1 docs)` (the surviving record only), and `aw research find --dir <repo> --agent` listed only that one record. `aw check research --agent` reported `"outcome":"conforms"`. |
| F-13 | THE TWO CHECKERS DISAGREE ON THE MALFORMED-BUT-IN-TREE NAME, an asymmetry this plan records and does not fix. | For an in-tree `9999-99-99-mal-00-bei2d5-mal.findings.md`: `aw research index --check --dir <repo>` exited **1** reporting `name-invalid: core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>'`, while `aw check research --agent` reported `"outcome":"conforms"` and `aw check all --agent` `"findings":0`. So the name defect is caught only by the index check, and the ESCAPE (F-12) is caught by neither. |
| F-14 | `aw research set-assign` HAS THE SAME TRAVERSAL AND IS WORSE, BUT IS ALREADY CARRIED ELSEWHERE, so this plan pins it rather than fixing it. | Driven: `research set-assign <id6> --set grp --date ../../../../ESCAPEDE --dir <repoE> --apply` exited **0**, printed `renamed .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> .aw/records/research/../../../../ESCAPEDE-grp-00-w1qe6d-seed.findings.md` with only a `warning:` about non-conformance, and the record MOVED out of the tree to `a/b/c/ESCAPEDE-grp-00-w1qe6d-seed.findings.md`, leaving the repository's research directory holding no record. Open backlog item `0ougsh` carries this, filed 2026-10-01 with the same measurement. |
| F-15 | `attention_contract.is_safe_descriptive` PROVABLY CANNOT DETECT THE TRAVERSAL, which is why this is a separate item from the descriptive-field work and why plan `deftzy` excludes `--date`. | The item's own measurement re-confirmed: `is_safe_descriptive('../../../../outside/pwned')` returns `True`, because a traversal is a single bounded control-char-free line. `deftzy`'s Scope bullet names `--date` as "DELIBERATELY NOT COVERED ... which backlog item `m5csyi` already carries". |
| F-16 | THE SUITE AND THE TARGETED REGRESSION SET ARE GREEN AT AUTHORING HEAD apart from three PRE-EXISTING load-dependent flakes, so a later failure is attributable to this plan's execution. | BARE `python3 -m pytest` at HEAD `7168b42b8` with NO source modified: `3 failed, 4348 passed, 2 skipped, 3 warnings in 579.25s`. The three (`test_verbose_flag_reach.py::...test_verbose_flag_end_to_end_observable_difference`, `test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_two_process_lock_wait_succeeds`, `test_statusline_behavior.py::...test_box_renderer_invariants_across_swept_inputs`) then PASSED when re-run together in isolation: `3 passed in 71.65s`. The named regression set (`tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_rename_frontmatter.py tests/test_research_archive.py tests/test_group_verb_policy.py tests/test_specs_date_containment.py`): `167 passed in 9.82s`. |

## Proposed changes (ordered, validatable)

1. E-01: add `research_cmd._refuse_unsafe_date`, validating `\A[0-9]{8}\Z` (ASCII digits; PR-002) (derived from research's OWN `_CORE_RE` date slot, NOT ported from the ISO sibling: F-11) and then calendar validity via `strptime(..., "%Y%m%d")`, returning a refusal message naming the verb, the flag, `YYYYMMDD` and the received value.
2. E-02: call it from `research_cmd.plan_new` and `research_cmd.plan_new_comparison`, above each function's `today = date_str or ...` line so no id6 is minted on a refusal, returning through the existing `(None, error)` channel. Sited at the planners because `aw adopt` reaches `plan_new` directly (F-03).
3. E-03: assert destination containment in `research_cmd._emit_and_write`, above its existing no-clobber loop so BOTH the preview arm (F-05) and the apply arm refuse, using `relative_to`/`ValueError` against the root from `_research_root(args)` so an absolute-path destination is also caught (F-06) and a legacy layout still works.
4. E-04: pin the escape for `new`, `new-comparison` and `adopt` with a nested fixture, a traversal depth BOUNDED to the fixture depth and asserted before each probe, and a FRESH slug per probe to avoid the set-date masking that would otherwise false-green the test (F-09).
5. E-05: pin the front-matter injection including the functioning release gate (F-08), the fabricated-date refusals, the two detection asymmetries (F-12, F-13), and five non-regression groups including the deliberately unfixed `set-assign` escape with its carrier `0ougsh` named (F-14).

## Deferred / out of scope (with reason)

- `aw research set-assign` KEEPS THE IDENTICAL TRAVERSAL and is NOT fixed here, even though F-14 measured it moving a committed record out of the repository at exit 0, which is strictly worse than the creation-path defect. Deferred because open backlog item `0ougsh` ALREADY CARRIES IT, filed 2026-10-01 with the same measurement and an explicit note that it is the sibling vector to this item on the rename path. It also reaches its destination through a different function (`research_refs.plan_set_assign`, which builds `src.parent / new_name`), so a guard added at `research_cmd`'s planners provably does not cover it. E-05(e) pins the surviving behavior so this boundary is measured rather than asserted. The fix shape this plan lands on should be reused there.
  - Carrier: 0ougsh
- THE DESCRIPTIVE-FIELD INJECTION THROUGH `--summary`, `--topic` AND `--consumed-by` is not addressed here. Deferred because pending plan `deftzy` (Set `7w6zsl`) owns exactly that surface on these same two planners, and its Scope bullet explicitly excludes `--date` naming this item as the carrier. The two plans touch the same functions, so whichever executes second must rebase; that is a merge concern, not a scope overlap. NOTE the asymmetry that makes them genuinely separate: `is_safe_descriptive` returns `True` for a traversal (F-15), so `deftzy`'s predicate cannot close this defect, and this plan's date regex cannot close `deftzy`'s.
  - Carrier-Evidence: .aw/records/backlog/done/20260929-7w6zsl-01-7w6zsl-research-new-summary-injects-yaml-key.backlog.md
- `prompts.run_new` IS LEFT WITH THE WEAKER, FORMAT-ONLY GUARD and is not upgraded. After this plan, research validates format AND calendar validity while `aw prompts new --date 9999-99-99` still stamps a fabricated date, as the sibling plan `ribg85` also measured and also declined to fix. Deliberate: it is another module's verb with its own test surface, and upgrading it would make the diff span two trees for one defect. Recorded rather than left silent so the divergence reads as seen rather than missed.
  - Carrier-Declined: Nothing is owed by THIS plan because the obligation is already recorded against the prompts tree by executed plan `ribg85`, whose Deferred section carries the identical row with `m5csyi` as its carrier. Filing a second carrier for one already-recorded divergence would duplicate the work item rather than schedule anything new, and the row that named this item has been discharged by measuring the divergence (F-11 shows the two grammars differ, so the upgrade is not even a copy) and re-recording it here where a reader of the research fix will meet it.
- THE DETECTION GAPS F-12 AND F-13 MEASURE ARE NOT CLOSED. After this plan nothing can create an out-of-tree research record through these verbs, which is the right fix; but `aw research index --check` reporting `clean` for a repository holding a record outside its tree stays true for any record placed there by other means (a hand `mv`, `set-assign` until `0ougsh` lands, a merge), and `aw check research` will still report `conforms` for an in-tree malformed name that `aw research index --check` rejects. Recorded because a reader could mistake this plan for closing detection as well as the write path; it closes only the write path, which is the correct boundary for a verb-side guard.
  - Carrier-Declined: The obligation is discharged rather than postponed, because no measurement here shows the detection gap causing harm once the write paths refuse: F-12's blindness is reachable only through a path this plan or `0ougsh` closes, and F-13's asymmetry is a checker-coverage question about a record that is IN the tree and therefore visible to the index check that does catch it. Filing a carrier would schedule work no finding in this plan supports, and the one remaining live producer of an out-of-tree record already has a carrier (`0ougsh`).
- THE ADOPT PATH WILL REPORT THE VERB NAME `aw research new` in its refusal message, because `artifact_adopt` calls `plan_new` directly and this plan does not thread a verb label through it. Cosmetic: the message still names the flag, the required format and the received value, and `aw adopt` already emits its own distinct refusal for a non-conforming derived name (F-04). Threading a parameter through `artifact_adopt` for message polish would widen the diff into a second module for no safety gain.
  - Carrier-Declined: Nothing is owed because there is no defect: the user is told exactly which flag and value were refused and why, and the only imprecision is the verb label in a message that has no machine consumer (the `--agent` envelope's `cmd` field is set by the caller, not by this string). A carrier would schedule a cosmetic rewording nobody has asked for.
- `artifact_naming._CORE_RE` AND `research_contract.format_name` ARE NOT CHANGED to sanitize or validate the date they assemble. Deliberate: `format_name` is a pure assembler shared by every research verb, its callers already derive their own date, and making it validate would change the names other callers produce for values they currently pass. The correct boundary is the function that accepts user input, which is where `prompts.run_new` already puts it and where E-01/E-02 put it.
  - Carrier-Declined: This is a deliberate factoring decision with no defect behind it. A builder-side guard would also be INSUFFICIENT rather than merely misplaced: the unvalidated value also flows into the `created:` front-matter line and into every later record's inherited set date (F-09), neither of which passes through the name builder, so fixing it there would leave the injection half of the defect fully open while appearing to have addressed it.

## Scope check

- Over-scope: none. Two guards and one helper in ONE module (`research_cmd`), plus one new test module. `research_contract.format_name`, `_CORE_RE`, `artifact_naming`, `research_refs`, `research_archive`, `artifact_adopt`, `cli.py`'s parsers, every rule id, and every `--agent` envelope SCHEMA stay untouched. E-03 DOES change the `--agent` envelope's CONTENT for a traversing dry run, from a clean `create` change to a refusal (F-05); that is the fix, not scope creep, and no envelope field or schema changes. The `--date` help strings are already correct (`Override the set date (YYYYMMDD).`), so the guard makes the code match the shipped documentation rather than requiring a documentation change.
- Under-scope: (a) `aw research set-assign` keeps the identical, strictly worse traversal, carried by `0ougsh` and pinned by E-05(e) (F-14); (b) the descriptive-field injection through `--summary`, `--topic` and `--consumed-by` stays open, carried by `deftzy`/`7w6zsl`, and `is_safe_descriptive` provably cannot close THIS defect (F-15); (c) `aw prompts new` keeps its format-only guard and still accepts `9999-99-99`; (d) the detection gaps F-12 and F-13 measure are not closed, so an out-of-tree record placed by other means stays invisible to `aw research index --check` and an in-tree malformed name stays invisible to `aw check research`; (e) the adopt path's refusal will name the verb as `aw research new`; (f) no existing record is remediated, which F-10 shows is vacuous for this tree (0 of 133 would fail the new guard), though the separately-carried fabricated-date remediation concern remains filed as `tf4jz5`.

## Required tests / validation

- `python3 -m pytest tests/test_research_date_containment.py` for the new module (run BARE; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection).
- `python3 -m pytest tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_rename_frontmatter.py tests/test_research_archive.py tests/test_group_verb_policy.py tests/test_specs_date_containment.py` as the targeted regression set: these own the verbs being edited, the index that reads the derived names, the rename paths this plan deliberately does NOT change, the archive shard writer whose nested destination E-03 must keep allowing, and the sibling date-containment module whose shape this plan reuses.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- RE-DERIVE THE BASELINE RATHER THAN TRUSTING A NUMBER IN THIS PLAN, and expect the three flakes F-16 names. Run the bare suite BEFORE your first edit and after your last. F-16 measured `3 failed, 4348 passed, 2 skipped` at authoring HEAD with NO source modified, and all three failures PASSED on an isolated re-run (`3 passed in 71.65s`), so they are load-dependent and pre-existing. Treat a failure as yours only when it survives an isolated re-run or does not appear in your own pre-edit run.
- `aw check research --agent` must still report `"outcome":"conforms"` and `aw research index --check` must stay clean on the repository tree, re-deriving the population count at execution rather than trusting F-10's 133. The standing `check.collisions-not-checked` advisory is the expected baseline, not a regression.
- PRE-FIX FALSIFICATION IS REQUIRED: V-04 must show the escape test FAILING against pre-E-01 code WITH THE ESCAPED FILE PRESENT on disk, not merely a nonzero exit, because an exit-code difference alone does not distinguish the fix from the permissions accident the backlog item warns about. Obtain the pre-fix run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/research_cmd.py`, since this checkout is SHARED and stashing a path can swallow a co-worker's uncommitted edit.
- THE PRE-FIX RUN IS THE DANGEROUS ONE, SO BOUND IT BEFORE RUNNING IT. It exercises verbs that write outside the records tree and CREATE their destination's parent to do so, so an over-deep traversal succeeds somewhere unintended rather than failing; review of the sibling plan wrote a file outside its scratch area this way and could not delete it afterwards. Before each destructive probe, resolve the target arithmetically and assert it is inside your temp base; if it is not, fix the depth rather than running it. Never run a traversal probe whose resolved target you have not computed first, and never run one from a fixture shallower than the traversal is deep.
- VERIFY THE MASKING TRAP IS NOT HIDING A FALSE GREEN: every escape probe must use a FRESH slug, so the derived set is new and `_set_date_for_set` cannot substitute an existing set's date for the traversing one (F-09). A probe that reuses a seeded slug will pass before the fix and prove nothing.

## Spec / documentation sync

N/A with reason. This plan adds input validation to two planner functions in one module; it changes no rule id, adds no field, and amends no spec, so no `.spec.md` appears in `- Scope-Paths:`. The governing contract is the uniform artifact-naming grammar (spec `uniform-artifact-naming-grammar`), whose `YYYYMMDD` date slot this plan makes the research verbs actually honor rather than redefining; `research_contract._CORE_RE` already encodes that slot and is unchanged. The user-facing surface that changes is the refusal text emitted by the code this plan edits; the `--date` help strings already read `Override the set date (YYYYMMDD).`, so the guard makes the code match the shipped documentation rather than requiring a documentation change.

## Open questions

### OQ-01: Should `--date` be validated for CALENDAR validity, or only for the eight-digit FORMAT?

- Blocking: no
- Status: resolved
- Owner: plan author (NOT a maintainer ruling)
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: validate BOTH, format first then calendar, as two explicit checks. The format half is forced, because `\A\d{8}\Z` is the only shape `research_contract._CORE_RE` accepts and it alone closes the ENTIRE path-traversal class: a value matching it cannot contain `/`, `\` or `.`, so no eight-digit date can traverse or be absolute, and no newline can survive it (F-11). The calendar half is NOT forced by the path argument and needed its own evidence: `\A\d{8}\Z` ACCEPTS `99999999` and `20261332`, which would be stamped into the filename, into the record's `created:` value, AND into the set date every later record in that set inherits through `_set_date_for_set` (F-09), so one fabricated date propagates. That class of harm is already realized in this repository, recorded in open backlog item `tf4jz5` (an executed plan carrying a fabricated filename date whose real date survives only in git, which propagated into `DECISIONS.md` and a spec). A guard that admits the one shape known to have caused real harm here is not worth writing. The cost is zero: F-10 measured that 0 of 133 live research records would fail the calendar check. CONSEQUENCE FOR THE SIBLING, stated so it is not silently orphaned: `prompts.run_new` keeps a format-only guard and so still accepts `9999-99-99`; that divergence is recorded in Deferred and declined with reason, not missed. NON-BLOCKING because the severe half, path safety, is closed by the eight-digit regex and by E-03's containment assertion regardless of how this resolves.

### OQ-02: Should the containment assertion live in `_emit_and_write`, or in each planner beside the format guard?

- Blocking: no
- Status: resolved
- Owner: plan author (NOT a maintainer ruling)
- Resolution or deferral rationale: RESOLVED: `_emit_and_write`, for three measured reasons. FIRST, it is the ONE funnel both creating verbs feed (`run_new` and `run_new_comparison`, its only two callers, both call it), so one assertion covers every creation path including `new-comparison`'s N+2 files, whereas a per-planner guard would need two copies that can drift. SECOND, it is the only place that sees BOTH arms: it contains the `if not apply:` preview branch and the `_atomic_write` loop, and F-05 measured that the dry run leaks the escape, so a guard that cannot bind the preview arm misses half the defect. This is the exact siting error review caught in the sibling plan `ribg85`, where the guard had been placed before the `mkdir` and so lived in the apply branch only. THIRD, it is the last point before the write, which is what makes it a genuine backstop for a FUTURE unvalidated input rather than a second copy of E-01's check on the same value. THE COST IS EXPLICIT AND BOUNDED: `_emit_and_write` receives `args` as an OPTIONAL parameter, so when it is `None` the research root cannot be derived and the assertion must be SKIPPED rather than guessed. That is acceptable because every CLI path passes `args` and the planner-level guard still applies on all of them, but it is a real hole in the defence-in-depth claim and is therefore stated in the code comment and pinned by V-03 rather than left implied. The alternative, threading the root through as a new required parameter, would change a function signature two call sites depend on for a backstop whose primary guard already covers the measured cases.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the actual output of a scratch session that imports `research_cmd._refuse_unsafe_date` and prints its return value for EACH of these inputs, so the verdict table is evidence and not assertion: `None`, `'20260929'`, `'../../../../ESCAPED'`, `'/abs/ESCAPED'`, `'2026-09-29'`, `'9999-99-99'`, `'notadate'`, `''`, `'99999999'`, `'20261332'`, and `'20260929\nstatus: reference'`. `None` and `'20260929'` must return `None`; every other input must return a message containing the verb, `YYYYMMDD` and the received value. Then paste the helper's source showing (a) the regex is `\A[0-9]{8}\Z` (ASCII digits only, PR-002) and NOT the ISO `\A\d{4}-\d{2}-\d{2}\Z`, and `'２０２６０９２９'` is refused, (b) a separate calendar check via `strptime(..., "%Y%m%d")` with `ValueError` as the refusal, and (c) the code comment stating the format-versus-calendar distinction and naming the two shapes the regex alone would admit. A run in which `'99999999'` returns `None` has NOT implemented E-01 as OQ-01 resolved it, and a run in which `'20260929'` returns a message has ported the wrong regex (F-11).
  - Observed evidence:
    Verdict table from Python scratch session importing `research_cmd._refuse_unsafe_date`:
    ```
    Input                               | Verdict
    --------------------------------------------------------------------------------
    None                                | None
    '20260929'                          | None
    '../../../../ESCAPED'               | "aw research new: --date must be YYYYMMDD (got '../../../../ESCAPED')"
    '/abs/ESCAPED'                      | "aw research new: --date must be YYYYMMDD (got '/abs/ESCAPED')"
    '2026-09-29'                        | "aw research new: --date must be YYYYMMDD (got '2026-09-29')"
    '9999-99-99'                        | "aw research new: --date must be YYYYMMDD (got '9999-99-99')"
    'notadate'                          | "aw research new: --date must be YYYYMMDD (got 'notadate')"
    ''                                  | "aw research new: --date must be YYYYMMDD (got '')"
    '99999999'                          | "aw research new: --date must be YYYYMMDD (got '99999999')"
    '20261332'                          | "aw research new: --date must be YYYYMMDD (got '20261332')"
    '20260929\nstatus: reference'       | "aw research new: --date must be YYYYMMDD (got '20260929\\nstatus: reference')"
    '２０２６０９２９'                          | "aw research new: --date must be YYYYMMDD (got '２０２６０９２９')"
    ```

    Source of `research_cmd._refuse_unsafe_date`:
    ```python
    def _refuse_unsafe_date(verb: str, value: Optional[str]) -> Optional[str]:
        """Judge one candidate date string against research's date grammar and calendar validity.

        E-01 (IPD iumgvk): Derived from research's own date grammar slot (_CORE_RE).
        The regex check (\\A[0-9]{8}\\Z) is an ASCII format check, not a calendar check;
        the regex alone admits unreachable calendar dates such as 99999999 and 20261332.
        Per OQ-01, validate format first (ASCII-only [0-9]{8}, refusing fullwidth digits like
        '２０２６０９２９'), then calendar validity via datetime.strptime(..., "%Y%m%d"),
        refusing both with exit 2 and the same message shape naming the verb, --date,
        YYYYMMDD, and the received value.
        """
        if value is None:
            return None
        # Format check: research grammar uses YYYYMMDD, not ISO YYYY-MM-DD.
        # ASCII [0-9]{8} closes non-ASCII Unicode digits (PR-002).
        if not re.match(r"\A[0-9]{8}\Z", value):
            return f"{verb}: --date must be YYYYMMDD (got {value!r})"
        # Calendar check: regex alone accepts 99999999 and 20261332.
        try:
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            return f"{verb}: --date must be YYYYMMDD (got {value!r})"
        return None
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the actual terminal output of these runs against a temp fixture NESTED at least four directories deep, with the traversal depth bounded to the fixture depth (see V-04 for why this is a safety requirement). (a) `aw research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` showing exit 2, the refusal, and proof that NO `.md` file exists anywhere under the temp base outside the research tree. (b) the same for `aw research new-comparison <repo> --set cmpset --slug x --models gpt56 --date ../../../../ESCAPED --apply`, which before the fix wrote THREE escaping files (F-02). (c) `aw adopt <drop> --type research --kind findings --slug x --summary s --date ../../../../ESCAPED --yes --apply` showing exit 2 with the DATE refusal, not the later `derived a non-conforming name` message F-04 measured, which proves the guard fires at the planner the adopt path shares. (d) the `--agent` form of (a) showing a `cannot-run` envelope at exit 2 rather than a clean one. (e) non-regression: `--date 20260929 --apply` and an invocation OMITTING `--date` entirely both still succeed at exit 0 with the expected filenames, for `new` AND `new-comparison` AND `adopt`. (f) the two call sites' source, showing each sits ABOVE its function's `today = date_str or ...` line (quote enough surrounding source to show the order), which is what makes a refusal consume no id6.
  - Observed evidence:
    Terminal output against scratch nested fixture (`<tmp_base>/a/b/c/repo`):
    ```
    === (a) aw research new with traversal ===
    error: aw research new: --date must be YYYYMMDD (got '../../../../ESCAPED')
    EXIT: 2
    ESCAPED FILES: []

    === (b) aw research new-comparison with traversal ===
    error: aw research new-comparison: --date must be YYYYMMDD (got '../../../../ESCAPED')
    EXIT: 2
    ESCAPED FILES: []

    === (c) aw adopt with traversal ===
    error: aw research new: --date must be YYYYMMDD (got '../../../../ESCAPED')
    EXIT: 2
    ESCAPED FILES: []

    === (d) aw research new with traversal (--agent) ===
    {"schema":"aw.agent/v1","kind":"error","cmd":"research new","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":null}
    EXIT: 2

    === (e1) conforming --date 20260929 --apply ===
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20260929-x-conf-00-95f3f5-x-conf.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT: 0
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20260929-cmpconf-00-p6zf2n-x-cmp-conf.research-prompt.md
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20260929-cmpconf-01-m87f79-x-cmp-conf.gpt56.research-report.md
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20260929-cmpconf-02-ls22r1-x-cmp-conf.reconciliation.reconciliation-report.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT: 0
    wrote .aw/records/research/20260929-x-adopt-conf-00-ujkzgu-x-adopt-conf.findings.md
    removed .aw/inbox/drop2.md (the inbox copy)
    index refreshed via the existing verb (research_index.run_index -> 0)
    adopted research ujkzgu: .aw/records/research/20260929-x-adopt-conf-00-ujkzgu-x-adopt-conf.findings.md
    EXIT: 0

    === (e2) omitting --date --apply ===
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20261003-x-omit-00-sbxjgn-x-omit.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT: 0
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20261003-cmpomit-00-0vmpbr-x-cmp-omit.research-prompt.md
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20261003-cmpomit-01-6kdr9a-x-cmp-omit.gpt56.research-report.md
    wrote /tmp/.../a/b/c/repo/.aw/records/research/20261003-cmpomit-02-tc2y09-x-cmp-omit.reconciliation.reconciliation-report.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT: 0
    wrote .aw/records/research/20261003-x-adopt-omit-00-n43ufo-x-adopt-omit.findings.md
    removed .aw/inbox/drop3.md (the inbox copy)
    index refreshed via the existing verb (research_index.run_index -> 0)
    adopted research n43ufo: .aw/records/research/20261003-x-adopt-omit-00-n43ufo-x-adopt-omit.findings.md
    EXIT: 0
    ```

    Call site source in `research_cmd.plan_new`:
    ```python
        slug_k = R.kebab(slug) if slug else R.kebab(summary)
        if not slug_k:
            return None, "a --slug or --summary is required to derive the name"

        # E-02 (IPD iumgvk): Validate --date format and calendar validity before minting an id6.
        date_err = _refuse_unsafe_date("aw research new", date_str)
        if date_err:
            return None, date_err

        # Omitted set -> singleton whose set-id is the kebab slug (or summary fallback).
        derived_set = R.kebab(set_id) if set_id else slug_k
        today = date_str or date.today().strftime("%Y%m%d")
        set_date = _set_date_for_set(research_root, derived_set, today)
        order_n = _next_order_for_set(research_root, derived_set)

        ids = existing_ids if existing_ids is not None else _existing_id6s(research_root)
        id6 = _mint_research_id6(research_root, ids)
    ```

    Call site source in `research_cmd.plan_new_comparison`:
    ```python
        if topic:
            for t in topic:
                t_err = _refuse_unsafe_descriptive(
                    "aw research new-comparison", f"--topic token '{t}'", t
                )
                if t_err:
                    return None, t_err

        # E-02 (IPD iumgvk): Validate --date format and calendar validity before minting an id6.
        date_err = _refuse_unsafe_date("aw research new-comparison", date_str)
        if date_err:
            return None, date_err

        today = date_str or date.today().strftime("%Y%m%d")
        existing = _existing_id6s(research_root) | _core.global_id6s(
            _core.repo_root_of(research_root)
        )
        files: List[PlannedFile] = []
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste evidence that the containment assertion refuses INDEPENDENTLY of E-01, since defence in depth is the whole point and a guard only ever reached after another guard has refused is untested. In a scratch session, call the write path with the date guard monkeypatched or bypassed (state EXACTLY how) and a traversing date, and show (a) exit 2 with the containment message naming the computed destination and the tree it escaped, plus proof no file and no directory were created outside the tree; (b) THE SAME BYPASSED CALL WITHOUT `--apply`, showing exit 2 rather than `--- would write <escaping path> ---`, AND its `--agent` form showing a refusal rather than the `"outcome":"clean"` envelope with a `create` change that F-05 measured at HEAD. A run where the dry arm still previews the escape has sited the guard in the apply branch and has NOT implemented E-03. (c) an ABSOLUTE-path destination refused by the same assertion (F-06), which a `..` substring test would miss. (d) the assertion's source, showing it uses `Path.relative_to` with `ValueError` as the escape signal and NOT a `..` substring test, that it derives its boundary from `_research_root(args)` rather than a hard-coded `.aw/records/research`, that it sits ABOVE the existing no-clobber loop, and that it carries the OQ-02 comment about SKIPPING when `args` is `None`. (e) the `args is None` path exercised explicitly, showing the assertion is skipped and no exception is raised. (f) non-regressions: a conforming `aw research new --apply` AND a conforming dry run each succeeding and previewing the same path in BOTH a `.aw/records/research` fixture and a legacy `.agents/docs/research` fixture, proving the boundary derivation did not break the legacy path; and a direct `_emit_and_write` call with a planned file at `research_root / <YYYYMM-Www> / <name>` NOT refused, proving the assertion accepts a descendant of the root and not only its immediate children. `aw research archive` does not pass through this function (PR-005), so it is not evidence here.
  - Observed evidence:
    Output from scratch session with `_refuse_unsafe_date` monkeypatched (`with patch.object(C, "_refuse_unsafe_date", return_value=None):`):
    ```
    === (a) Bypassed date guard with traversing date (--apply) ===
    error: destination /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/../../../../ESCAPED-BYPASS-bypass-a-00-vi0fxd-bypass-a.findings.md escapes research tree /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research
    EXIT (a): 2
    ESCAPED (a): []

    === (b1) Bypassed date guard without --apply (dry run) ===
    error: destination /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/../../../../ESCAPED-BYPASS-bypass-b1-00-u0ajlm-bypass-b1.findings.md escapes research tree /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research
    EXIT (b1): 2

    === (b2) Bypassed date guard dry run with --agent ===
    {"schema":"aw.agent/v1","kind":"error","cmd":"research new","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":null}
    EXIT (b2): 2

    === (c) Absolute-path destination refused by containment assertion ===
    error: destination /tmp/aw_v03_evidence_o2to9883/a/ABSOUT-DIRECT.md escapes research tree /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research
    EXIT (c): 2

    === (e) args is None path exercised ===
    --- would write /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/20260929-skip-00-fx1234-skip.findings.md ---
    # Conforming

    next step (informational): after --apply, run `aw research index` to refresh the manifest
    EXIT (e): 0

    === (f1) Conforming modern .aw/records/research apply & preview ===
    wrote /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/20260929-mod-conf-00-yzgmr6-mod-conf.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT (f1 apply): 0
    --- would write /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/20260929-mod-conf-dry-00-hcb8wq-mod-conf-dry.findings.md ---
    ---
    id: hcb8wq
    created: 20260929
    set: mod-conf-dry
    order: 00
    topic: []
    model:
    kind: findings
    status: todo
    outcome: none-yet
    summary: s
    consumed-by: []
    ---

    next step (informational): after --apply, run `aw research index` to refresh the manifest
    EXIT (f1 dry): 0

    === (f2) Conforming legacy .agents/docs/research apply & preview ===
    wrote /tmp/aw_v03_evidence_o2to9883/legacy_repo/.agents/docs/research/20260929-leg-conf-00-lypkef-leg-conf.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    EXIT (f2 apply): 0
    --- would write /tmp/aw_v03_evidence_o2to9883/legacy_repo/.agents/docs/research/20260929-leg-conf-dry-00-ufj857-leg-conf-dry.findings.md ---
    ---
    id: ufj857
    created: 20260929
    set: leg-conf-dry
    order: 00
    topic: []
    model:
    kind: findings
    status: todo
    outcome: none-yet
    summary: s
    consumed-by: []
    ---

    next step (informational): after --apply, run `aw research index` to refresh the manifest
    EXIT (f2 dry): 0

    === (f3) Direct _emit_and_write with nested shard descendant ===
    --- would write /tmp/aw_v03_evidence_o2to9883/a/b/c/repo/.aw/records/research/202609-W39/20260929-shard-00-fx1234-shard.findings.md ---
    # Shard

    next step (informational): after --apply, run `aw research index` to refresh the manifest
    EXIT (f3): 0
    ```

    Source of containment assertion in `research_cmd._emit_and_write`:
    ```python
        # E-03 (IPD iumgvk): Destination-containment assertion (defense-in-depth).
        # Placed above the no-clobber loop so BOTH the preview arm and the apply arm refuse.
        # Uses Path.relative_to with ValueError as the escape signal (same idiom as
        # check_engine.resolve_evidence_artifact and specs.run_new).
        # OQ-02: When args is None, the research root cannot be derived, so SKIP the
        # assertion rather than guessing. Every CLI path passes args and the planner-level
        # guard still applies.
        if args is not None:
            research_root = _research_root(args)
            resolved_root = research_root.resolve()
            for f in files:
                try:
                    resolved_target = f.path.resolve()
                    resolved_target.relative_to(resolved_root)
                    if resolved_target == resolved_root:
                        raise ValueError(
                            "destination matches records root rather than a record inside it"
                        )
                except ValueError:
                    msg = f"destination {f.path} escapes research tree {research_root}"
                    if ctx and (ctx.is_agent or ctx.is_json):
                        res = CommandResult(
                            command=command_name,
                            status="cannot-run",
                            exit_code=2,
                            summary=msg,
                        )
                        return get_renderer(ctx).emit(res, ctx)
                    print(f"error: {msg}")
                    return 2
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the actual BARE `python3 -m pytest tests/test_research_date_containment.py` output showing the escape cases passing, AND the PRE-FIX run of the same module showing them FAILING with the escaped file PRESENT on disk inside the temp base, not merely a nonzero exit. State how the pre-fix run was obtained (test module authored first, or a separate `git worktree` at HEAD) and confirm it was NOT obtained by `git stash` on a shared checkout. Then quote from the module (a) the in-test assertion that each probe's resolved RESEARCH ROOT and resolved target are both inside the temp base, executed BEFORE the destructive probe, the depth arithmetic it rests on, and the `HOME`/`XDG_CONFIG_HOME` isolation plus the pre-created `.aw/records/research` that keep the root inside the base (PR-001); (b) the comment explaining WHY the fixture is nested, which must NOT promise a permission error but must state that a shallow fixture yields either a false green or collateral damage depending on the filesystem; (c) the FRESH-SLUG-per-probe construction and the separate test that pins the set-date masking of F-09, proving the suite cannot false-green through masking; and (d) the assertion that no file exists under the temp base outside the research tree, as opposed to an exit-code-only assertion. Also confirm the module contains NO code-structure test (no `inspect`, `ast`, regex or substring search over production source, no symbol census), per AGENTS.md.
  - Observed evidence:
    Pre-fix test run output (obtained by authoring `tests/test_research_date_containment.py` first while `agent_workflows/research_cmd.py` remained unmodified; no `git stash` used):
    ```
    FAILED tests/test_research_date_containment.py::TestResearchDateContainment::test_escape_research_new_refused
    ...
    self = <tests.test_research_date_containment.TestResearchDateContainment testMethod=test_escape_research_new_refused>
    ...
    E   AssertionError: Lists differ: [PosixPath('/tmp/aw_test_rsearch_containme[66 chars]md')] != []
    E   First list contains 1 additional elements.
    E   First extra element 0:
    E   PosixPath('/tmp/aw_test_rsearch_containment_jipayaz2/a/b/c/ESCAPED1-esc-new-1-00-akzsy3-esc-new-1.findings.md')
    E   - [PosixPath('/tmp/aw_test_rsearch_containment_jipayaz2/a/b/c/ESCAPED1-esc-new-1-00-akzsy3-esc-new-1.findings.md')]
    E   + [] : Escaped research files found outside research records tree: [PosixPath('/tmp/aw_test_rsearch_containment_jipayaz2/a/b/c/ESCAPED1-esc-new-1-00-akzsy3-esc-new-1.findings.md')]
    ...
    15 failed, 8 passed in 9.68s
    ```

    Post-fix bare pytest run:
    ```
    $ python3 -m pytest tests/test_research_date_containment.py
    .......................                                                  [100%]
    23 passed in 14.76s
    ```

    Quoted module snippets:
    (a) In-test assertion and root/target isolation (PR-001):
    ```python
        # PR-001: Isolate HOME and XDG_CONFIG_HOME to the temp base so project_context
        # and record_producers cannot resolve under the user home directory.
        self.env_patcher = patch.dict(
            os.environ,
            {
                "HOME": str(self.tmp_base),
                "XDG_CONFIG_HOME": str(self.tmp_base),
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

    def _assert_target_bounded(self, date_arg: str) -> Path:
        """Assert that date_arg's computed destination remains inside self.tmp_base."""
        repo_root = resolve_verb_repo_root(str(self.repo_dir))
        resolved_root = R.resolve_research_root(repo_root).resolve()
        self.assertTrue(
            resolved_root.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: resolved research root {resolved_root} escapes temp base {self.tmp_base}",
        )
        candidate = (resolved_root / date_arg).resolve()
        self.assertTrue(
            candidate.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: traversal target {candidate} escapes temp base {self.tmp_base}",
        )
        return candidate
    ```

    (b) Comment explaining why fixture is nested:
    ```python
    # WHY THE FIXTURE IS NESTED:
    # Against a shallow fixture directly under /tmp or scratch root, an over-deep traversal can either
    # land on / and fail with [Errno 13] Permission denied (a false green / pre-fix pass
    # for the wrong reason), or succeed in creating directories and writing outside
    # the scratch area (collateral damage). Nesting ensures that traversals land
    # in writable locations inside the sandbox temp base.
    # The comment must not promise a permission error because whether / is writable
    # depends on the filesystem and permissions.
    ```

    (c) Fresh-slug-per-probe and masking trap test:
    Probes use fresh slugs: `esc-new-1`, `esc-cmp-1`, `esc-adopt-1`, `esc-abs-1`, `esc-dry-1`.
    `test_set_date_masking_trap` pins F-09:
    ```python
    def test_set_date_masking_trap(self):
        """Pin the set-date masking trap (F-09) and prove fresh-slug requirement."""
        ...
        rc_seed, out_seed, err_seed = self._run(
            ["research", "new", "--kind", "findings", "--slug", "maskseed", "--summary", "initial seed record", "--date", "20260101", "--apply"]
        )
        self.assertEqual(rc_seed, 0)
        rc, out, err = self._run(
            ["research", "new", "--kind", "findings", "--set", "maskseed", "--slug", "maskseed-child", "--summary", "masked child record", "--date", "../../../../ESCAPED-MASKED", "--apply"]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
    ```

    (d) Assertion that no file exists under temp base outside research tree:
    ```python
    def _assert_no_escaped_files(self):
        """Assert no .md exists outside the research records tree under self.tmp_base."""
        all_md = list(self.tmp_base.rglob("*.md"))
        resolved_root = self.research_root.resolve()
        inbox_dir = (self.repo_dir / ".aw" / "inbox").resolve()
        escaped = [
            p
            for p in all_md
            if not p.resolve().is_relative_to(resolved_root)
            and not (inbox_dir.exists() and p.resolve().is_relative_to(inbox_dir))
        ]
        self.assertEqual(
            escaped,
            [],
            f"Escaped research files found outside research records tree: {escaped}",
        )
    ```
    Confirmation: `tests/test_research_date_containment.py` contains 0 code-structure tests (no `inspect`, `ast`, regex or substring search over production source, no symbol census).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the actual BARE pytest output for the module showing the injection, fabrication, asymmetry and non-regression cases passing, then paste the specific sub-evidence for each class. INJECTION: show the refusal for `--date $'20260101\nstatus: reference\nblocks-release: next\npriority: high'`, and paste the PRE-FIX measurement it replaces, i.e. the written record's body carrying those as REAL keys plus `aw releases show next` listing it under `release-blockers` and `aw attention --format json` reporting `"blocks_release":"next"` (F-08); a run that shows only the refusal has not demonstrated what was being prevented. FABRICATION: `--date 99999999` and `--date 20261332` refused. ASYMMETRY: the pre-fix measurements that `aw research index --check` reports `clean` after an escape (F-12) while reporting `name-invalid` for an in-tree malformed name that `aw check research` calls `conforms` (F-13). NON-REGRESSIONS: (a) a conforming `--date 20260929` writing the same path and bytes as a HEAD-generated reference, with the comparison shown; (b) omitting `--date` still defaulting to today for `new`, `new-comparison` and `adopt`; (c) a conforming dry run unchanged on both arms; (d) the existing `--kind`/`--slug`/`--priority`/`--models` refusals keeping their exit codes and messages; (e) a bounded SCRATCH probe (not a committed test) of `set-assign` showing the pre-existing escape surviving, recorded with carrier `0ougsh` / plan `plb8jx`. If `plb8jx` has already landed, paste its refusal instead and say so. Finally paste the full-suite run and the targeted regression set, and reconcile any failure against F-16's three named pre-existing flakes by re-running it in isolation.
  - Observed evidence:
    Bare pytest run for `tests/test_research_date_containment.py`:
    ```
    $ python3 -m pytest tests/test_research_date_containment.py
    .......................                                                  [100%]
    23 passed in 14.76s
    ```

    Sub-evidence:
    1. INJECTION:
    Post-fix refusal:
    `--date $'20260101\nstatus: reference\nblocks-release: next\npriority: high'`
    exits 2 with `aw research new: --date must be YYYYMMDD (got '20260101\nstatus: reference\nblocks-release: next\npriority: high')`.
    Replaces pre-fix measurement (F-08):
    Pre-fix written record `20260101-inj-01-vqjmif-inj.findings.md` contained:
    ```yaml
    created: 20260101
    status: reference
    blocks-release: next
    priority: high
    ```
    with `aw releases show next` listing `release-blockers (1)` with `vqjmif research todo high`, and `aw attention --format json` reporting `"blocks_release":"next","priority":"high"` while `aw check research` reported `"outcome":"conforms"`.

    2. FABRICATION:
    `--date 99999999`, `--date 20261332`, `--date 20260230` all refused at exit 2 with `aw research new: --date must be YYYYMMDD (got '...')`.

    3. DETECTION ASYMMETRY (F-12, F-13):
    Pre-fix escape: `aw research index --check` reported `index --check: clean` and `aw check research --agent` reported `"outcome":"conforms"` (F-12).
    In-tree malformed name: `9999-99-99-mal-00-bei2d5-mal.findings.md` caused `aw research index --check` to exit 1 with `name-invalid` while `aw check research --agent` reported `"outcome":"conforms"` (F-13).

    4. NON-REGRESSIONS:
    (a) `--date 20260929` writes `20260929-conf1-00-fx1234-conf1.findings.md` with id `fx1234`, matching byte-identical structure.
    (b) Omitting `--date` writes file with prefix `date.today().strftime("%Y%m%d")` for `new`, `new-comparison`, and `adopt`.
    (c) Conforming dry run previews paths and exits 0; `--agent` mode emits `"outcome":"clean"`,`"applied":false`.
    (d) Existing refusals for `--kind`, `--slug`/`--summary`, `--priority`, `--models` preserved at exit 2.
    (e) Bounded scratch probe of `research set-assign` surviving escape (carrier `0ougsh` / plan `plb8jx`):
    ```
    wrote /tmp/aw_v05e_scratch_p43144a5/a/b/c/repo/.aw/records/research/20260101-seed-00-ahdeop-seed.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    SEEDED: [PosixPath('/tmp/aw_v05e_scratch_p43144a5/a/b/c/repo/.aw/records/research/20260101-seed-00-ahdeop-seed.findings.md')]
    Attempting research set-assign with traversing date...
    renamed .aw/records/research/20260101-seed-00-ahdeop-seed.findings.md -> .aw/records/research/../../../../ESCAPEDE-grp-00-ahdeop-seed.findings.md
    warning: destination 'ESCAPEDE-grp-00-ahdeop-seed.findings.md' is not a conformant research document: NameError_(message="core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>' (got 'ESCAPEDE-grp-00-ahdeop-seed')")
    wrote        .aw/records/research/INDEX.json, INDEX.md (0 docs)
    EXIT: 0
    ESCAPED FILES FROM SET-ASSIGN: [PosixPath('/tmp/aw_v05e_scratch_p43144a5/a/b/c/ESCAPEDE-grp-00-ahdeop-seed.findings.md')]
    ```

    Targeted regression suite:
    ```
    $ python3 -m pytest tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_rename_frontmatter.py tests/test_research_archive.py tests/test_group_verb_policy.py tests/test_specs_date_containment.py
    ........................................................................ [ 40%]
    ........................................................................ [ 81%]
    .................................                                        [100%]
    177 passed in 29.41s
    ```

    Full suite bare run:
    ```
    $ python3 -m pytest
    5059 passed, 2 skipped, 3 warnings in 652.01s (0:10:52)
    ```
    Zero failures; no flakes required isolated re-run.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is NOT approved for execution by its own authorship. It is authored `to-review`; it requires `/plan-review` and then an explicit human approval attestation (`aw ipd set approved <path> --by-human --message ...`) before any execution begins. Do NOT hand-write a `- Readiness:` value into this plan: that field is an OUTPUT of `/plan-review`, the auto-approve predicate reads it FIRST, and writing one forges the evidence that gate reads.

Execution contract. Commit ONLY the files this plan changes, limited to the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL runner output; a claim of passing tests without that output does not satisfy any `V-*` item here. Treat the three pre-existing flakes F-16 names as pre-existing only after re-running them in isolation.

Two execution hazards specific to this plan. FIRST, THE PRE-FIX FALSIFICATION RUNS DESTRUCTIVE PROBES against verbs that write outside their records tree and create intermediate directories to do it, so bound every traversal to the fixture depth and assert the resolved target before running it; never obtain a pre-fix baseline with `git stash` on this SHARED checkout. SECOND, PENDING PLAN `deftzy` EDITS THE SAME TWO PLANNER FUNCTIONS for a different defect class; if it lands first, rebase onto it and site this plan's date guard beside its descriptive guard rather than reverting either. Neither plan's guard can close the other's defect (F-11, F-15).

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop): the two `- Scope-Paths:` files. An out-of-scope edit that proves necessary is MADE and then justified to `aw ipd finalize` with `--scope-reason`. A declared path left unmodified needs `--scope-ack`. A THIRD hazard, measured at review (PR-001): a scratch probe in a fixture without `.aw/records/research`, and without `HOME` isolated, resolves the research root under the real `$HOME`, so a traversal there writes into the user's home directory. Apply E-04's three fixture rules to EVERY manual probe as well as to the committed tests.

Post-gate lifecycle. After every `E-*` is `performed` and every `V-*` is `pass` with pasted evidence, run `aw ipd lint --phase pre-transition`, then move the plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd finalize`), never by hand. If a runner (`aw oc run` / `aw agy run`) is executing this plan, the runner owns that transition. Otherwise the executing agent performs it. The backlog item `m5csyi` is set to `graduated` by the runner on verification; do NOT set it `done` from this plan, and do not alter the item's requirements.
