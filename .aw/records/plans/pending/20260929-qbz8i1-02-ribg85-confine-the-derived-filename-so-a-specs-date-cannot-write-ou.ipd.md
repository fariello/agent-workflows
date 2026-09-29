# IPD: Confine the derived filename so a specs date cannot write outside the records tree

- Date: 2026-09-29
- Kind: child
- Concern: `specs.run_new` interpolates `--date` into the derived filename with NO validation, so a traversal in it writes a spec outside the records tree. Measured in this lane: `aw specs new --date ../../../../ESCAPED --apply` exits 0 and creates `ESCAPED-<id6>-01-<id6>-x.spec.md` at the REPOSITORY ROOT, and a deeper traversal creates it outside the repository entirely; `aw specs check` on that repo then reports `"checked":0,"findings":0`, because the record it just wrote is not in the tree the checker walks. The cause is that `build_clustered_name` passes its `date` argument through raw while running `artifact_core.kebab` over the setid and slug, so the date is the ONE filename input that is not sanitized. A non-traversing but malformed `--date 9999-99-99` is equally unvalidated and silently stamps a fabricated date into the filename, the `- Date:` bullet, and the history record.
- Scope: Validate `--date` at `specs.run_new` against the `YYYY-MM-DD` format, using the refusal that `prompts.run_new` already ships for the identical flag, and add a destination-containment assertion so a filename that would resolve outside the resolved records tree is refused rather than written. DELIBERATELY NOT COVERED: `aw research new`, which has the same traversal and is carried separately; the DESCRIPTIVE-value injection vectors, which Order 01 owns; and `build_clustered_name` itself, which is a shared name builder this plan does not change (OQ-02).
- Scope-Paths: agent_workflows/specs.py, tests/test_specs_date_containment.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: qbz8i1
- Blocks-Release: next
- Set: qbz8i1
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ribg85

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `qbz8i1`. This defect is NOT in that item, which reports descriptive-field injection through `--summary`; it was found while measuring the sibling flags on the same verb and is a different class, since `attention_contract.is_safe_descriptive` returns True for a traversal string. Separated from Order 01 for that reason rather than folded in. Also measured that `prompts.run_new` already ships the exact guard `specs.run_new` lacks, and that `research new` has the same hole (carried by `m5csyi`).
- 2026-09-29 draft (opencode): created.

## Goal

Make `aw specs new` refuse a `--date` it cannot safely use, so the verb cannot write a record outside the tree its own checker walks, and cannot silently stamp a fabricated date into a record's identity. The escape is the severe half; the fabricated-date half is the one that has already happened in this repository's history.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: validate the value, then confine the destination

- [ ] E-01 Add a `--date` FORMAT guard to `specs.run_new`, placed immediately after the existing `--title is required` refusal and BEFORE `core.mint_id6`, so a refusal consumes no id6 and touches no filesystem. Refuse with exit 2 and a message naming the flag, the required format, and the received value.
  PORT THE SIBLING VERB'S GUARD RATHER THAN INVENTING ONE. `prompts.run_new` already validates the identical flag with `re.match(r"\A\d{4}-\d{2}-\d{2}\Z", date_iso)` and refuses `aw prompts new: --date must be YYYY-MM-DD (got {date_iso!r})` at exit 2. Use that regex and that message shape with the verb name changed, so the two verbs refuse identically and a user meets one vocabulary. Exit 2 is also `run_new`'s own convention for a bad flag (`--title is required` returns 2).
  THE REGEX IS A FORMAT CHECK, NOT A CALENDAR CHECK, and that limit must be stated in the code comment rather than discovered later: it accepts `9999-99-99`, which F-04 measured as silently stamping a fabricated date. OQ-01 resolves whether to add calendar validation and records why not; do not add `datetime.date.fromisoformat` without reading it, because the sibling verb deliberately does not and divergence between the two is worse than the shared limit.
  - Depends on: none
  - Expected outcome: `aw specs new --date ../../../../ESCAPED --title T --slug x --summary s --apply` exits 2 with the format refusal and writes nothing, where before it exited 0 and created a file outside the records tree. `--date notadate` and `--date 2026-9-9` also exit 2. `--date 2026-09-29` still succeeds unchanged.
  - Execution state: pending

- [ ] E-02 Add a DESTINATION-CONTAINMENT assertion after `record_placement.resolve_creation_path` returns `dest` and before `dest.parent.mkdir(...)`, refusing when the RESOLVED `dest` does not lie inside the RESOLVED records directory for the specs type. Refuse with exit 2 and a message naming the computed destination and the tree it escaped.
  THIS IS DEFENCE IN DEPTH AND IS NOT REDUNDANT WITH E-01, which is the reason it is a separate item rather than a line in the first. E-01 guards the one input measured to traverse today; E-02 guards the PROPERTY that matters, namely that this verb only ever writes inside its own tree, and it holds for any future input that reaches the name builder. Both are cheap and the second is what makes a regression in the first non-exploitable.
  USE THE ESTABLISHED IN-REPO IDIOM, not a string comparison on `..`: resolve both paths and call `Path.relative_to`, treating `ValueError` as the escape, exactly as `check_engine.resolve_evidence_artifact` does ("containment: candidate must be inside the repo root (no ../ escape)"). A substring test for `..` is wrong in both directions (it rejects a legitimate directory named `..x` and misses an absolute-path destination) and must not be used.
  DERIVE THE BOUNDARY FROM THE SAME RESOLVER THAT BUILT THE PATH, `record_placement.resolve_type_dir("specs", repo_root=repo_root)`, rather than hard-coding `.aw/records/specs`. That function deliberately falls back to a legacy `.agents/` tree when present, so a hard-coded modern path would make this guard refuse every legitimate write in a legacy-layout repository.
  - Depends on: E-01
  - Expected outcome: with E-01's guard temporarily bypassed in a scratch session, a traversing derived name is refused by E-02 alone at exit 2 and writes nothing; and with both guards in place every conforming `aw specs new` still writes to the same path it wrote before, in BOTH a `.aw/records/` and a legacy `.agents/` layout fixture.
  - Execution state: pending

### Task group 2: pin the escape, the fabrication, and the non-regressions

- [ ] E-03 Add `tests/test_specs_date_containment.py` pinning the ESCAPE as the primary property. The fixture MUST be nested several directories deep inside the temp dir (for example `<tmp>/a/b/repo`) so the traversal lands somewhere WRITABLE, and the test must assert that no file exists anywhere under the temp base outside the repo's records tree, not merely that the command failed.
  THE NESTING IS NOT INCIDENTAL AND MUST CARRY A COMMENT SAYING SO: F-03 measured that the identical traversal against a fixture directly under `/tmp` exits 2 with `[Errno 13] Permission denied` because the escape lands on `/`, which is an accident of filesystem permissions and not a guard. A test written against a shallow fixture PASSES BEFORE THE FIX and therefore validates nothing. This is the single easiest way to get a false green here.
  Cover: a traversal that lands at the repo root, a deeper one that leaves the repository entirely, an absolute-path `--date`, and the conforming converse. Drive at least one case through `cli.main` rather than the runner function alone, following `test_new_requires_title` in `tests/test_spec_id6_filenames.py`.
  - Depends on: E-02
  - Expected outcome: a new module whose escape cases FAIL against pre-E-01 code with the escaped file PRESENT on disk, and PASS after with the temp base containing no file outside the records tree.
  - Execution state: pending

- [ ] E-04 In the same module, pin the FABRICATED-DATE case and the non-regressions. Fabrication: `--date 9999-99-99` must now be REFUSED, and the test must document in its name and a comment that this half of the defect is about record IDENTITY rather than path safety, because a fabricated filename date has already caused real damage in this repository (F-04 cites the committed instance). Also assert `--date notadate` is refused, and that its pre-fix artifact was invisible to `aw specs check` while visible to `aw check specs` as `check.name-nonconformant`, which is the asymmetry F-05 measured.
  Non-regressions: (a) a conforming `--date 2026-09-29` writes the SAME path and bytes as before the change, compared against a HEAD-generated reference; (b) omitting `--date` still defaults to today through `specs._today`; (c) the existing `--title is required` refusal keeps its exit code and message; (d) `specs.run_set` and `specs.run_note`, which also read `--date` and write it into a history record but do NOT derive a filename from it, are UNCHANGED by this plan, asserted by driving each with a malformed date and observing the pre-existing behavior, which documents the deliberate under-scope rather than leaving a reader to wonder.
  - Depends on: E-03
  - Expected outcome: the fabrication cases are refused, the four non-regression groups pass, and (d) records the surviving `run_set`/`run_note` behavior explicitly so the scope boundary is evidence rather than assertion.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE GUARD THIS PLAN ADDS ALREADY SHIPS IN A SIBLING VERB, so this is a port and not new policy. `prompts.run_new` validates `--date` against `\A\d{4}-\d{2}-\d{2}\Z` and refuses at exit 2 before deriving a name. `specs.run_new` is the outlier among the creating verbs, not the pioneer.
- THE CONTAINMENT IDIOM IS ESTABLISHED: `check_engine.resolve_evidence_artifact` resolves the candidate and calls `relative_to`, treating `ValueError` as the escape, with the comment "containment: candidate must be inside the repo root (no ../ escape)". E-02 reuses that shape rather than inventing a string test.
- ONLY THE DATE SEGMENT IS UNSANITIZED, which is why this plan guards the date and not the other name inputs. `artifact_naming.build_clustered_name` runs `_core.kebab` over BOTH `set_id` and `slug` (`f"{date}-{_core.kebab(set_id)}-{order:02d}-{id6}-{_core.kebab(slug)}{facet}.md"`) and `kebab`'s `_KEBAB_STRIP_RE` is `[^a-z0-9]+`, so a traversal or newline in the slug is flattened. Driven: `core.kebab('../../../etc/passwd')` returns `'etc-passwd'`.
- THE REFUSAL CONVENTION IN THIS FUNCTION IS EXIT 2. `specs.run_new` returns 2 for `--title is required`; `command_surface` declares the repository convention as 0 clean / 1 findings / 2 cannot-run-or-usage. Note that `specs.run_set` uses 1 for its usage refusals, so this module is internally inconsistent; this plan touches only `run_new` and so takes 2 without needing to resolve that.
- A FABRICATED FILENAME DATE IS A KNOWN, ALREADY-REALIZED HARM IN THIS REPOSITORY, which is why E-04 treats the non-traversing malformed case as a real defect rather than a cosmetic one. Open backlog item `tf4jz5` records the executed plan `20260101-instsafe-07-qrokie` carrying a fabricated filename date whose real `20260723` survives only in git, and which propagated the wrong date into `DECISIONS.md` and a spec.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'` (AGENTS.md).

## Findings

All findings were DRIVEN against temporary fixture repositories in this lane at HEAD `f4b00263`, not read off the source.

| # | Finding | Evidence |
|---|---|---|
| F-01 | `aw specs new --date` TRAVERSES AND WRITES A SPEC AT THE REPOSITORY ROOT, outside the records tree, at exit 0. | Driven through the real CLI in a fixture at `<tmp>/a/b/repo`: `specs new --date ../../../../ESCAPED --apply` printed `wrote <repo>/.aw/records/specs/draft/../../../../ESCAPED-vt2xut-01-vt2xut-x.spec.md` at `rc=0`, and the resulting file was found at `a/b/repo/ESCAPED-vt2xut-01-vt2xut-x.spec.md`, i.e. the repo root. |
| F-02 | A DEEPER TRAVERSAL LEAVES THE REPOSITORY ENTIRELY, and creates intermediate directories to do it, so the blast radius is not confined to the repo. | Driven with `--date ../../../../../OUTSIDE/deep/dir --apply` against a fixture at `<tmp>/repo`: `rc=0`, and the tree under the repo's PARENT afterwards contained `OUTSIDE/deep/dir-cp9lsg-01-cp9lsg-x.spec.md`, created by the `dest.parent.mkdir(parents=True, exist_ok=True)` that precedes the write. |
| F-03 | THE OBVIOUS TEST FOR THIS PASSES BEFORE THE FIX, so E-03's fixture nesting is load-bearing rather than stylistic. The same traversal against a shallow fixture refuses for an unrelated reason. | Driven twice with the SAME command. Against `<tmp>/repo` with five `../`, the escape resolved onto `/` and the run exited 2 with `[Errno 13] Permission denied`. Against `<tmp>/a/b/c/repo` with four `../`, where the escape lands in a writable directory, the same shape exited 0 and wrote the file. So an unnested fixture measures the filesystem's permissions, not the verb's behavior. |
| F-04 | THE NON-TRAVERSING MALFORMED CASE IS ALSO UNVALIDATED AND IS SILENT: `--date 9999-99-99` stamps a fabricated date into the filename, the `- Date:` bullet AND the history record, and every checker passes it. | Driven: `--date 9999-99-99 --apply` exited 0 writing `99999999-vr90e2-01-vr90e2-x.spec.md`, whose body carries `- Date: 9999-99-99` and `- 9999-99-99 created (aw specs): s`; `aw specs check --agent` reported `"outcome":"clean","findings":0`. This class of harm is already realized in this repository: open backlog item `tf4jz5` records executed plan `20260101-instsafe-07-qrokie` carrying a fabricated filename date whose real date survives only in git, and open item `5h8u3z` records that a malformed `- Date:` escapes `aw ipd lint` entirely. |
| F-05 | THE ESCAPED RECORD IS INVISIBLE TO THE TREE CHECKER, so nothing downstream can detect the F-01 write; and the two checkers DISAGREE on the malformed-name case. | Driven: after the F-01 escape, `aw specs check --dir <repo> --agent` reported `"checked":0,"findings":0` on a repository that had just been told it wrote a spec. Separately, for `--date notadate`, `aw specs check` reported 1 finding (`attention.history-missing`) while `aw check specs` reported 3 including `check.name-nonconformant`; so the name defect is caught only by the second command, and the ESCAPE is caught by neither. |
| F-06 | `attention_contract.is_safe_descriptive` CANNOT DETECT THIS, which is why the fix cannot be folded into Order 01's descriptive guard. | Driven: `is_safe_descriptive('../../../../outside/pwned')` returns **True**, and so does `is_safe_descriptive('notadate')`, because both are single bounded control-char-free lines. The defect class is path derivation, not output safety. |
| F-07 | THE SIBLING VERB ALREADY REFUSES THE IDENTICAL INPUT, so the fix shape is settled and `specs` is simply the outlier. | Driven: `aw prompts new --dir <fx> --slug x --date ../../../../../ESCAPED/x --apply` exited **2** with `aw prompts new: --date must be YYYY-MM-DD (got '../../../../../ESCAPED/x')` and wrote nothing. `prompts.run_new` contains that regex check inline. |
| F-08 | `aw research new` HAS THE SAME TRAVERSAL and is NOT fixed here, so the residue is real and owned. | Driven against a fixture at `<tmp>/a/b/c/repo`: `research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` exited **0** and wrote `a/b/c/ESCAPED-x-00-ul54zx-x.findings.md`, three levels above the records tree. Note this ALSO first measured as a false negative on a shallow fixture (`Permission denied` on `/`), exactly as F-03 describes. Carried by `m5csyi`. |
| F-09 | ONLY THE DATE SEGMENT IS EXPOSED; the other user-controlled name inputs are already flattened, so the fix is narrow by construction rather than by choice. | Driven: `core.kebab('../../../etc/passwd')` returns `'etc-passwd'`, `core.kebab('x\n- Blocks-Release: next')` returns `'x-blocks-release-next'`. `build_clustered_name` applies `kebab` to `set_id` and `slug` and interpolates `date` raw. A `--slug` traversal therefore produces an odd filename inside the tree, not an escape. |
| F-10 | THE EXISTING POPULATION IS UNAFFECTED, so this plan is purely preventive with no migration step. | Driven over the whole tree: `aw specs check --agent` reports `"outcome":"clean","checked":38,"findings":0` and `aw check specs --agent` `"outcome":"conforms"`. All 38 committed specs carry conformant or grandfathered names; none sits outside the specs tree. |

## Proposed changes (ordered, validatable)

1. E-01: validate `--date` in `specs.run_new` against `\A\d{4}-\d{2}-\d{2}\Z`, ported verbatim from `prompts.run_new`, placed before `mint_id6`, refusing with stderr + exit 2.
2. E-02: assert the resolved `dest` lies inside `record_placement.resolve_type_dir("specs", ...)` before creating directories or writing, using the `relative_to`/`ValueError` idiom from `check_engine.resolve_evidence_artifact`, refusing at exit 2 otherwise.
3. E-03: pin the escape with a DEEPLY NESTED fixture (F-03), asserting on the absence of any file outside the records tree rather than on the exit code alone.
4. E-04: pin the fabricated-date refusal, the two-checker asymmetry F-05 measured, and four non-regression groups including the deliberately untouched `run_set`/`run_note` date paths.

## Deferred / out of scope (with reason)

- `aw research new` HAS THE SAME TRAVERSAL AND IS NOT FIXED HERE. Measured at F-08: it writes a `.findings.md` three directories above the records tree at exit 0. Deferred because it is a different module with a different front-matter dialect, a different name builder call path (`research_refs`/`research_cmd` rather than `specs`), and its own test surface, so fixing both in one commit would mix two modules' behavior changes. The fix shape this plan lands on should be reused there rather than re-derived.
  - Carrier: m5csyi
- THE SIBLING VERB `prompts.run_new` IS LEFT WITH THE WEAKER GUARD and is not upgraded here. After this plan `specs.run_new` validates format AND calendar validity (OQ-01), while `prompts.run_new` validates format only, so `aw prompts new --date 9999-99-99` still stamps a fabricated date. Deliberate: it is another module's verb, its own test surface, and upgrading it is a behavior change to a command this plan is not otherwise touching, which would make the diff span two verbs for one defect. Recorded rather than left silent so a reader does not read the divergence as an oversight.
  - Carrier: m5csyi
- `specs.run_set` AND `specs.run_note` ALSO READ `--date` and write it into a history record, and are NOT guarded here. Deliberate: neither derives a FILENAME from it, so neither can traverse, and a malformed date there produces a malformed history line that `attention_contract.HISTORY_RECORD_RE` is positioned to catch rather than a file outside the tree. E-04(d) pins their current behavior so the boundary is evidence rather than assertion.
  - Carrier-Declined: The obligation is discharged rather than postponed for the defect class this plan exists to close, which is a write outside the records tree: these two functions provably cannot produce one, because they write to an EXISTING resolved path (`args.path`) and never call a name builder. A malformed history date is a distinct concern about history-record conformance, it is already within the history validator's remit, and no measurement here shows it escaping that remit; filing a carrier would schedule work no finding in this plan supports.
- `artifact_naming.build_clustered_name` IS NOT CHANGED to sanitize its `date` argument. See OQ-02: it is a shared pure builder used by every record type, its callers already pass a compacted date they derived themselves, and making it sanitize would silently CHANGE the names other trees derive. The correct boundary is the verb that accepts user input.
  - Carrier-Declined: Nothing is owed because this is a deliberate factoring decision with no defect behind it: the builder's contract is to ASSEMBLE a name from validated parts, and every measured escape enters through a verb that failed to validate its part. Fixing it at the builder would leave the same unvalidated value flowing into the `- Date:` bullet and the history record, which the verb-side guard closes and a builder-side one cannot.

## Scope check

- Over-scope: none. Two guards in one function in one module, plus one new test module. `build_clustered_name`, `record_placement.resolve_creation_path`, `resolve_type_dir`, `specs._render_new_spec`, `specs.run_set`, `specs.run_note`, `prompts.run_new`, every rule id, and every `--agent` envelope stay untouched.
- Under-scope: (a) `aw research new` keeps the identical traversal, carried by `m5csyi`, and is the largest residue; (b) `aw prompts new` keeps its format-only guard, so it still accepts the fabricated `9999-99-99` that this plan refuses for `specs`, also carried by `m5csyi`; (c) `run_set`/`run_note` malformed dates still reach a history record; (d) the two committed artifacts with fabricated dates that motivated F-04 are NOT remediated by this forward-only guard, and remediating them is a separate records-correction concern already filed as backlog item `tf4jz5`; (e) this plan does not address the F-05 asymmetry where `aw specs check` and `aw check specs` disagree about a malformed name, which is a pre-existing checker-coverage question rather than a write-path defect.

## Required tests / validation

- `python3 -m pytest tests/test_specs_date_containment.py` for the new module (run bare; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_spec_id6_filenames.py tests/test_specs_verbs.py tests/test_specs_status_dirs.py tests/test_spec_production.py tests/test_prompts_new.py` as the targeted regression set: these own the verb being edited, the filename grammar it derives, and the sibling verb whose guard is being ported (so a copy-paste error in the regex surfaces).
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- `aw specs check --agent` must still report clean and `aw check specs --agent` `"outcome":"conforms"` on the repository tree (F-10), re-deriving the `checked` count at execution rather than trusting 38.
- PRE-FIX FALSIFICATION IS REQUIRED: V-03 must show the escape test FAILING against pre-E-01 code WITH THE ESCAPED FILE PRESENT on disk, not merely a nonzero exit. A run that shows only an exit-code difference has not distinguished the fix from the F-03 permissions accident. Obtain the pre-fix run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/specs.py`, since this checkout is shared and stashing a path can swallow a co-worker's uncommitted edit.

## Spec / documentation sync

N/A with reason. This plan adds input validation to one verb; it changes no rule id, adds no field, and amends no spec, so no `.spec.md` appears in `- Scope-Paths:`. The relevant contract is the uniform artifact-naming grammar (spec `uniform-artifact-naming-grammar`), whose `YYYYMMDD` date slot this plan makes the verb actually honor rather than redefining. The user-facing surface that changes is the verb's refusal text and its `--date` help string, both emitted by the code this plan edits; the help text already says `Override the authored date (YYYY-MM-DD)`, so the guard makes the code match the documentation rather than requiring a documentation change.

## Open questions

### OQ-01: Should `--date` be validated for CALENDAR validity, or only for FORMAT?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: validate BOTH, format first then calendar, but implement calendar validation as an explicit second check rather than by replacing the regex. The tension is real and was nearly resolved the other way. AGAINST calendar validation: the sibling verb this plan ports from (`prompts.run_new`) checks format ONLY, and two verbs refusing different inputs for the same flag is a worse user contract than a shared limit. FOR it, and decisive: F-04 measured that `--date 9999-99-99` passes a format-only guard and stamps a fabricated date into the filename, the `- Date:` bullet and the history record, with every checker reporting clean; and this repository has ALREADY been damaged by exactly that (open backlog item `tf4jz5` records executed plan `20260101-instsafe-07-qrokie` carrying a fabricated filename date whose real `20260723` survives only in git, having propagated the wrong date into `DECISIONS.md` and a spec). A guard that admits the one shape known to have caused real harm here is not worth writing. So E-01 applies the ported regex AND a `datetime.date.fromisoformat` (or equivalent) calendar check, refusing both with the same message shape; the ported regex is kept rather than dropped so the refusal wording stays aligned with the sibling for the common typo cases. NON-BLOCKING because the path-safety half, which is the severe half, is closed by the format regex and by E-02 regardless of how this resolves. CONSEQUENCE FOR THE SIBLING, stated so it is not silently orphaned: `prompts.run_new` now has the WEAKER guard, which is a real divergence this plan deliberately does not fix in another module's verb; it is the kind of tidy-up that belongs with the `m5csyi` sweep, and this resolution is the record that it was seen rather than missed.

### OQ-02: Should `artifact_naming.build_clustered_name` sanitize its `date` argument, so every caller is protected at once?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: no. Three reasons, in decreasing order of force. FIRST, it would not be sufficient: the unvalidated `--date` also flows into the `- Date:` bullet and the `## Workflow history` record (F-04), neither of which passes through the name builder, so a builder-side fix would leave the fabricated-date half of the defect fully open while appearing to have addressed it. SECOND, it would change existing behavior for callers this plan has not measured: the builder is shared by every record type (`specs`, `prompts`, `research`, `plans`, `releases`, `backlog`) and each already derives and compacts its own date before calling, so introducing sanitization there would alter the names those callers produce for inputs they currently pass successfully. THIRD, the builder is a pure assembler whose documented contract is to "Assemble a clustered filename", and validation of user input belongs at the verb that accepts it, which is where `prompts.run_new` already puts it (F-07) and where the sibling `dtg7dz` put the analogous descriptive guard. The residue this leaves is that a FUTURE caller could reintroduce the same defect, which E-02's containment assertion covers for this verb and which `m5csyi` covers for the one other verb measured to have it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual terminal output of these runs against a temp fixture NESTED at least three directories deep (see V-03 for why). (a) `aw specs new --date ../../../../ESCAPED --title T --slug x --summary s --apply` showing exit 2, the refusal naming the flag and the required format, and proof that no `.spec.md` exists anywhere under the temp base. (b) `--date notadate` and `--date 2026-9-9` each exiting 2. (c) `--date 9999-99-99` exiting 2, which is the OQ-01 calendar half and is NOT covered by the ported regex alone, so a run where this one still exits 0 has not implemented E-01 as resolved. (d) `--date 2026-09-29 --apply` still succeeding at exit 0 with the expected filename. (e) the guard's source, showing both the regex and the calendar check, and the code comment stating the format-versus-calendar distinction E-01 requires. (f) the PRE-FIX counterpart of (a): exit 0 and the escaped file's actual path on disk.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste evidence that the containment assertion refuses INDEPENDENTLY of E-01, since defence in depth is the whole point and a guard that is only ever reached after another guard has already refused is untested. Concretely: in a scratch Python session, call `specs.run_new` with the format guard monkeypatched or bypassed (state exactly how) and a traversing date, and show exit 2 with the containment message naming the computed destination and the tree it escaped, plus proof no file and no directory were created outside the tree. Then paste the assertion's source showing it uses `Path.relative_to` with `ValueError` as the escape signal and NOT a `..` substring test, and that it derives its boundary from `record_placement.resolve_type_dir` rather than a hard-coded path. Finally paste a conforming `aw specs new --apply` succeeding in BOTH a `.aw/records/` layout fixture and a legacy `.agents/specs/` layout fixture, proving the boundary derivation did not break the legacy path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full `python3 -m pytest tests/test_specs_date_containment.py` output including the `N passed` line. Then paste the PRE-FIX run showing the escape cases FAILING, and for at least one case show the ESCAPED FILE'S PATH as the test reported it, proving the failure was "a file was written outside the tree" and not merely a nonzero exit code. STATE THE FIXTURE'S DEPTH EXPLICITLY and paste the comment in the test that explains it: F-03 measured that a shallow fixture makes this test pass before the fix via `[Errno 13] Permission denied`, so a pre-fix run showing exit 2 with a permission error is EVIDENCE THE TEST IS WRONG, not evidence the code is right. Also confirm the test asserts on the absence of files under the whole temp base, not just on the exit code.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the test output for the fabrication and non-regression groups, naming each test. Fabrication: show `--date 9999-99-99` and `--date notadate` refused, and paste the pre-fix artifacts' evidence for the F-05 asymmetry, namely `aw specs check --agent` and `aw check specs --agent` outputs on a `notadate` fixture showing the first reporting 1 finding and the second reporting `check.name-nonconformant`. Non-regressions: (a) a byte-level comparison of a conforming `--date 2026-09-29` record against a HEAD-generated reference, showing identical path and identical bytes; (b) the no-`--date` default still producing today's date; (c) the `--title is required` refusal unchanged, quoting the HEAD message compared against; (d) `specs.run_set` and `specs.run_note` driven with a malformed date, with their observed behavior pasted verbatim so the deliberate under-scope is documented by evidence. Then paste the bare full-suite run with its `N passed` line and the repository-tree `aw specs check --agent` / `aw check specs --agent` outputs (F-10), re-deriving the `checked` count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and `- Readiness:` is deliberately ABSENT because that field is an output of `/plan-review`, not of authoring. Execute only the checklist above; commit through `aw commit <this plan> -- <the paths in Scope-Paths>` and never `git add -A`, verifying the staged set before each commit because this checkout is shared. Do not push and do not tag. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd set executed`), never by hand.

INDEPENDENCE: this plan declares `- Item-Dependencies: none` and is independent of its siblings. It edits `specs.run_new`'s date-to-filename derivation; Order 01 edits flag guards in the same function and Order 03 edits `specs.validate_spec` and the rule registry. Order 01 and this plan therefore both touch `specs.run_new`, in different statements; the runner isolates each lane by default and returns changes through the merge-and-revalidate gate, so that is a normal merge rather than a hazard. If an executor runs them sequentially in one worktree, take this one second, since Order 01's guards sit earlier in the function and will already be present.
