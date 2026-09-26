RETIRED 2026-09-26: maintainer decided against any prompt-purity gate (phrase lists miss new wordings and flag innocent text; existing instructions already prevent the problem, 0 violations in the 7 prompts written since 2026-08-20); no replacement.

# IPD: Implement aw prompts check, the prompt-purity lint of approved spec 20260808-1958-01

- Date: 2026-09-26
- Kind: child
- Concern: Approved spec `20260808-1958-01-prompt-purity-lint` specifies `aw prompts check`, a deterministic lint that fails a staged prompt containing anything but the prompt itself; it is unimplemented (`aw prompts check` is an invalid choice), and `aw check prompts` covers only the metadata comment, so nothing mechanically guards prompt purity.
- Scope: IN: `agent_workflows/prompts_lint.py` with R1/R2/R3, the `aw prompts check` verb and its command-surface declaration, the same rules inside `aw check prompts`, outcome tests for spec A1-A6, docs sync (managed AGENTS.md block via `engine.py`, prompts README, shipped template, research-prompt workflow), the spec's stale-path amendment and its move to `implementing`. OUT: `.aw/records/prompt-library/` (spec OQ4), a scaffold/--fix verb (OQ5), a separate pre-commit hook, setting the spec `implemented`.
- Scope-Paths: agent_workflows/prompts_lint.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/command_surface.py, agent_workflows/prompts.py, agent_workflows/engine.py, AGENTS.md, tests/test_prompts_check.py, .aw/records/prompts/README.md, .aw/system/workflows/templates/prompts-README.md, .aw/system/workflows/research-prompt/research-prompt.md, .aw/records/specs/approved/20260808-1958-01-prompt-purity-lint.spec.md, .aw/records/specs/implementing/20260808-1958-01-prompt-purity-lint.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: not-executed
- Work-Kind: feature
- Priority: medium
- From-Backlog: kkzgrk
- Set: promptlint
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: mi4s9f

## Workflow history
- 2026-09-26 not-executed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Retired 2026-09-26 by maintainer decision: no prompt-purity gate. A phrase-list lint misses new wordings and falsely flags innocent text; the existing instructions (AGENTS.md, /research-prompt, aw prompts new) already prevent the problem, with zero violations in the 7 prompts written since 2026-08-20.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog kkzgrk: implement aw prompts check (spec 20260808-1958-01 R1-R3) with OQ1/OQ2 left open at the spec's defaults.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Implement `aw prompts check`, the deterministic prompt-purity lint approved spec `20260808-1958-01-prompt-purity-lint` specifies (rules R1-R3, `--agent` output, exit 0/1/2), so a staged prompt that carries operator instructions, delimiter markers, or non-comment content above its body is caught mechanically instead of by a maintainer re-reading it. Document the convention in the managed AGENTS.md block and the prompts README, and hand the spec to `implementing` with evidence ready for a human to mark it `implemented`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: outcome tests

- [ ] E-01 Add `tests/test_prompts_check.py`: a tmp repo with `.aw/records/prompts/{pending,executed,untracked}/` and fixture prompts, driving `cli.main(["prompts", "check", "--dir", tmp])` (and `--agent`) and asserting exit codes and reported `(location, rule)` pairs only. Cases, mapped to the spec's acceptance criteria: A1 a prompt whose body has a line `Operator note (do not upload this section)` -> exit 1 with an R2 finding naming that line, and, because that line is a heading placed before the body starts, an R1 finding too when it precedes the first body line; A2 a line `=== BEGIN UPLOAD-READY PROMPT ===` -> R3; A3 a file starting with YAML `---` front matter -> R1, and the same content with the metadata moved into a leading `<!-- aw-prompt: ... -->` comment -> exit 0; A4 a verbatim copy of the tracked `executed/20260808-1948-01-attention-registry-spec-external-review.prompt.md` -> exit 0 (its metadata comment itself contains the phrase `not part of the prompt`, so this also proves the comment line is exempt from R2); A5 a body line `Return your answer as a DOWNLOADABLE markdown (.md) file.` -> exit 0; A6 `--agent` stdout has one tab-separated `location<TAB>rule<TAB>detail` record per finding and exit 1, and a clean tree exits 0; exclusions: a violating file under `untracked/` and a violating `README.md` produce no findings; a second `<!-- aw-prompt: ... -->` line anywhere after line 1 -> R1. Tests assert OUTCOMES only (exit code, rule id, file:line), never the phrase-list contents, source text, or message wording.
  - Depends on: none
  - Expected outcome: every case fails at HEAD with `invalid choice: 'check'` (exit 2).
  - Execution state: pending

### Task group 2: the checker

- [ ] E-02 Create `agent_workflows/prompts_lint.py` (stdlib only, Python 3.9) with `check_prompt(path, text) -> List[Drift]` and `run(args) -> int`. The file walk reuses `check_engine._iter_type_files(repo_root, "prompts", include_retired=True)`, which already resolves `.aw/records/prompts` (and legacy `.agents/prompts`), skips `README.md`/`INDEX.md`/`STATUS.md`, skips the gitignored `untracked/` lane through `artifact_core.is_ignored_path`, and sorts deterministically; ALSO skip any path with a `local/` segment explicitly (the retired lane name an older checkout may still carry, per the prompts README). Rules: R1 = line 1 may be a single `<!-- aw-prompt: ... -->` comment; after it (or from line 1 if absent) the first non-blank line must be body text, so a first non-blank line that is `---`, or a `- Key: value` metadata bullet, or any further `<!-- aw-prompt:` comment anywhere, is a violation; R2 = a case-insensitive substring match of `OPERATOR_PHRASES` on every line EXCEPT the leading metadata comment; R3 = a line that, stripped of surrounding `=`/`-`/`#`/`*`/`~`/`_` fence characters and whitespace, reads `BEGIN ... PROMPT`, `END ... PROMPT` or `START ... PROMPT` (the words bounding at most 40 characters). Each finding is an `artifact_core.Drift(location="<repo-rel-path>:<line>", rule="prompt.purity-R1|R2|R3", detail=<offending text truncated to 120 chars + why>)`. Output: `--agent` prints `artifact_core.render_agent_drift`; human mode prints each finding plus ONE remediation line per offending file ("Move pipeline metadata into a leading `<!-- aw-prompt: ... -->` comment and delete user-directed instructions; the file must be pure prompt."); exit `artifact_core.drift_exit_code`, 2 when the prompts root does not exist or cannot be read. An optional positional `dir` scopes the walk to one subtree of the prompts root. No em or en dashes in emitted text (spec N5).
  - Depends on: E-01
  - Expected outcome: `check_prompt` is callable in isolation; nothing wired yet.
  - Execution state: pending

- [ ] E-03 Single-source the R2 phrase list as the module constant `OPERATOR_PHRASES: Tuple[str, ...]` in `prompts_lint`, seeded with exactly the spec's list: "operator note", "do not upload", "upload everything", "upload this", "copy this", "paste below", "paste this", "not part of the prompt", "run this against", "run separately and compare", "save the returned", "move this prompt to". Document the extension mechanism in the constant's comment: append a lowercase phrase; a phrase must be USER-directed (how a human handles the file), never TARGET-AI-directed (what the model returns), and the A5 test is the guard. No `upload`/`download`/`.md` stems are listed, so "return a downloadable .md file" cannot match (spec A5, F2).
  - Depends on: E-02
  - Expected outcome: one constant; no other copy of the list exists.
  - Execution state: pending

- [ ] E-04 Wire the verb. In `cli._build_parser`, add `prompts_sub.add_parser("check", parents=[common], ...)` beside `new` (the `prompts_sub = p_prompts.add_subparsers(dest="prompts_command")` block), with `--dir` and optional positional `dir`, and update the `p_prompts` help/epilog/description to list `check` and exit code 1. In `_dispatch`'s `if args.command in ("prompt", "prompts"):` block route `prompt_cmd == "check"` to `prompts_lint.run(args)` and change the family-help hint to mention both verbs. Add a `CommandDeclaration(command="prompts check", command_class="check", human_recipe="check", agent_record_kind="result", mutation_gate="none", empty_error_renderer="renderer_boundary", legacy_flags=("--agent", "--dir"), exit_contract=(0, 1, 2))` beside `prompts new` in `agent_workflows/command_surface.py`, so `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` stays green. Update the stale sentence in the `prompts.py` module docstring ("Deliberately NOT here: ``aw prompts check`` ... is owned by its own approved spec") to point at `prompts_lint`.
  - Depends on: E-03
  - Expected outcome: E-01 passes; `python3 -m agent_workflows prompts check --help` renders.
  - Execution state: pending

- [ ] E-05 Fold the rules into `aw check prompts` so the existing CI/`aw check all` path sees them: in `check_engine.check_types`' `elif record_type == "prompts":` branch (which calls `validate_prompt_content`), also extend with `prompts_lint.check_prompt(p, text)` for each file. Leave `SUPPORTED["prompts"] = ("names", "content")` unchanged: the purity rules are content rules. Register the three rule ids in `RULE_REGISTRY` at severity `error`, `ASSURANCE_REPOSITORY`, `DET_DETERMINISTIC`, invariant `""`, so `enrich_drift` does not fall back to the conservative default silently.
  - Depends on: E-04
  - Expected outcome: `aw check prompts --all` reports the same findings as `aw prompts check` on a violating fixture (one E-01 case extended to assert this, still an outcome assertion).
  - Execution state: pending

### Task group 3: docs sync (spec F4)

- [ ] E-06 AGENTS.md prompt section is a MANAGED block generated from `engine.py` (`agents_pointer_prose`, the `"### Writing prompts for another AI (research/handoff prompts)\n"` string). Add to that paragraph: the single leading `<!-- aw-prompt: ... -->` HTML comment is the ONLY permitted non-prompt content (no YAML front matter, no metadata bullets), and `aw prompts check` is the gate. Then regenerate `AGENTS.md` through the installer's merge path (`engine.merge_aw_block` with the manifest from `.aw/system/managed-sections.json`, `file_key="AGENTS.md"`, `target_layout="aw"`; the layout this repo renders with, measured: `agents_managed_block(target_layout="aw")` is the only layout whose output appears verbatim in `AGENTS.md`), and confirm the new sentence is on disk. Measured at authoring: a sentinel appended to the pointer section DID land (`action='refreshed'`, sentinel present), so the manifest drift-preserve trap y9vpvv E-07 hit is not armed today; if it is armed at execution, re-record only a section proven byte-equal to the generator, as y9vpvv E-07 did, and commit `.aw/system/managed-sections.json` separately with a `--scope-reason`. No em or en dashes (user-facing).
  - Depends on: E-04
  - Expected outcome: `AGENTS.md` carries the new sentence inside `<!-- aw:pointer -->`; `engine.py` and `AGENTS.md` agree.
  - Execution state: pending

- [ ] E-07 `.aw/records/prompts/README.md`: the metadata-comment convention is already documented ("Pipeline metadata lives in a SINGLE leading HTML comment ... YAML front-matter is NOT permitted"); ADD one paragraph stating the purity contract as three checkable rules (R1 structure, R2 no user-directed instructions, R3 no region-delimiter markers), naming `aw prompts check` as the gate and `OPERATOR_PHRASES` in `agent_workflows/prompts_lint.py` as the one place the phrase list lives. Mirror the same paragraph into the shipped template `.aw/system/workflows/templates/prompts-README.md`, which installs this README into other repos, and add one line to the memory kernel of `.aw/system/workflows/research-prompt/research-prompt.md` (item 1, "AGENTS.md Prompt-Purity Contract") telling the producer to run `aw prompts check` on the minted file before concluding (spec G4 author-time reminder).
  - Depends on: E-04
  - Expected outcome: three doc surfaces name the gate; none contradicts the code.
  - Execution state: pending

- [ ] E-08 Amend the spec in place, because its paths predate the `.aw/` layout (the spec says `.agents/prompts/**/*.md`, `.agents/prompts/README.md`, `.agents/prompts/pending/20260808-1948-01-...`, and `local/`): update Section 1, Section 6, Section 7, F3 and A4 to `.aw/records/prompts/`, the `untracked/` lane (retired name `local/`), and A4's file now at `executed/20260808-1948-01-attention-registry-spec-external-review.prompt.md`; record in Section 11 under OQ1/OQ2 the defaults this plan implements (see Open questions) and that they await maintainer ruling. Then append a history note with `aw specs note` (or `aw specs set ... --status implementing`) and move the spec `approved -> implementing` with `aw specs set implementing <spec> --message "IPD mi4s9f: aw prompts check implemented; awaiting evidence review"`, which the transition table permits an executor (`->implementing`: `who: executor`). Do NOT set `implemented`: that needs an executed-IPD evidence citation that only exists once this plan is finalized; the executor PROPOSES it in the final report with the exact command `aw specs set implemented <spec> --evidence .aw/records/plans/executed/<this plan>` for the maintainer.
  - Depends on: E-05
  - Expected outcome: the spec reads `- Status: implementing`, lives under `.aw/records/specs/implementing/`, and its paths match the tree.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-09 Run `python3 -m agent_workflows prompts check` and `python3 -m agent_workflows prompts check --agent` on THIS repository. Measured at authoring over the 17 tracked prompts with the spec's R2 phrases and an R3 BEGIN/END/START-PROMPT pattern: 0 hits outside the leading metadata comment, and every first visible line is body text, so the expected result is exit 0 with no findings. Then run `python3 -m agent_workflows check prompts --all` and `python3 -m agent_workflows check all`, and show neither gained a finding attributable to the new rules.
  - Depends on: E-08
  - Expected outcome: exit 0, zero findings, on all four commands' prompt-purity portion.
  - Execution state: pending

- [ ] E-10 Run `ruff check` and `ruff format --check` on the edited Python files, then the bare suite `python3 -m pytest`, then add one `Added:` line to the 2.0.0 section of `CHANGELOG.md` describing `aw prompts check` in user terms (no em or en dashes).
  - Depends on: E-09
  - Expected outcome: no ruff findings; suite passes; one changelog line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.Drift` / `render_agent_drift` / `drift_exit_code` is the `--check` convention the spec names (G1, N3); `drift_exit_code` treats only `info` as non-failing.
- `check_engine._iter_type_files` is the walker every `aw check` type uses; for prompts it resolves `.aw/records/prompts` via `record_producers.resolve_record_read_paths` (measured) and yields all 17 tracked prompts with `include_retired=True`.
- `validate_prompt_content` already reads the leading comment (`prompts_index._parse_metadata_comment`) but covers only metadata presence, id/filename agreement and status/bucket agreement, not R1-R3.
- `prompts.render_metadata_comment` ends every minted comment with "... and is not part of the prompt.", so the metadata comment line MUST be exempt from R2 or every minted prompt fails.
- The AGENTS.md prompt rules are rendered from `engine.agents_pointer_prose`; editing `AGENTS.md` by hand would be preserved-as-drift or overwritten, so edit the generator and regenerate.
- A new parser leaf needs a `command_surface.CommandDeclaration` or `tests/test_command_surface_declarations.py` fails.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-verified at HEAD 2026-09-26:

| Id | Evidence | Finding |
|---|---|---|
| F-1 | `cli.py`: `prompts_sub = p_prompts.add_subparsers(dest="prompts_command")` registers only `new`; `_dispatch` routes `new` and `set` | Confirmed; `aw prompts check` is an invalid choice. Note `set` is also dispatched though not in this subparser block; left alone. |
| F-2 | `ls agent_workflows/ \| grep prompt` -> `prompts.py`, `prompts_index.py` | Confirmed: no `prompts_lint.py`. |
| F-3 | `check_engine.SUPPORTED["prompts"] == ("names", "content")`; `validate_prompt_content` emits only `check.prompt-metadata-missing`, `check.prompt-id-mismatch`, `check.prompt-status-mismatch` | Confirmed. The backlog item's `('names',)` is stale; `content` was added by dx0u4s. |
| F-4 | spec Sections 1, 6, 7, F3, A4 use `.agents/prompts/...` and `local/` | Stale paths; E-08 amends them. |
| F-5 | Scan of the 17 tracked prompts, lines after the leading comment, the spec's 12 R2 phrases and a BEGIN/END/START..PROMPT line pattern: 0 hits. The phrase `not part of the prompt` DOES appear 9 times, all inside line-1 metadata comments | Confirms the brief's "0 violations" ONLY IF the metadata comment is exempt from R2; E-02 makes that explicit and A4 tests it. |
| F-6 | 8 of 17 prompts have no metadata comment (6 executed + the 2 superseded, whose first line is a `RETIRED ...` header); `has_metadata_comment` docstring says 6 | The 2 superseded ones start with the AGENTS.md-mandated `RETIRED YYYY-MM-DD: ...` retirement header, which is visible text, not metadata. It passes R1 as written (it is not `---`, a bullet, or a comment) and contains no R2 phrase. Recorded so a future tightening of R1 does not accidentally fail retired prompts. |

## Proposed changes (ordered, validatable)

1. Outcome tests for A1-A6 plus exclusions (E-01).
2. `prompts_lint` with R1-R3 and the single-sourced phrase list (E-02, E-03).
3. CLI verb + command-surface declaration (E-04), and the same rules under `aw check prompts` (E-05).
4. Docs: managed AGENTS.md block via `engine.py`, prompts README + shipped template + research-prompt memory kernel (E-06, E-07).
5. Spec path amendment and `approved -> implementing` (E-08).
6. Live run on this repo, ruff, suite, changelog (E-09, E-10).

## Deferred / out of scope (with reason)

- Purity-checking `.aw/records/prompt-library/` (spec OQ4).
  - Carrier-Declined: the spec's own non-goal and F3 put it out of scope in v1 ("library prompts may document usage"); nothing is owed.
- `aw prompts scaffold` / `--fix` (spec OQ5).
  - Carrier-Declined: `aw prompts new` already mints a pure-by-construction skeleton (IPD jxqdcw), which is what OQ5 asked for.
- Wiring `aw prompts check` into `.pre-commit-config.yaml` (spec G6 `[Should]`).
  - Carrier-Declined: E-05 puts the rules inside `aw check prompts`, which is already the shipped check path; a separate hook would run the same rules twice. A maintainer wanting a hook adds one entry.

## Scope check

- Over-scope: none.
- Under-scope: the shipped template `templates/prompts-README.md` and the `research-prompt` workflow are included because they install/drive prompt authoring in other repos; leaving them would make the gate invisible where prompts are written.

## Required tests / validation

Outcome tests only, per the maintainer's standing rule: `tests/test_prompts_check.py` asserts exit codes and `(location, rule)` pairs from real CLI runs on fixture files, mapped one-to-one to spec acceptance A1-A6 plus the untracked/README exclusions. No test pins the phrase list, message wording, or source text. Live evidence: `aw prompts check` exits 0 on this repository (E-09). Bare suite.

## Spec / documentation sync

- `.aw/records/specs/approved/20260808-1958-01-prompt-purity-lint.spec.md` IS AMENDED (declared in Scope-Paths, together with its post-transition path under `implementing/`): its paths are stale (`.agents/prompts`, `local/`), and leaving them would make the approved contract describe a tree that no longer exists, so every later reviewer would be checking this plan against the wrong paths. The amendment changes locations only, not rules, plus a note recording the OQ1/OQ2 defaults. Its status moves `approved -> implementing`; `implemented` is left to the maintainer with the evidence command stated.
- `agent_workflows/engine.py` + regenerated `AGENTS.md` (spec F4: the prompt section is the managed `aw:pointer` block).
- `.aw/records/prompts/README.md`, `.aw/system/workflows/templates/prompts-README.md`, `.aw/system/workflows/research-prompt/research-prompt.md`.
- `CHANGELOG.md`.

## Open questions

### OQ-01: Should R2 be phrase-list-only, or also structural (spec OQ1)?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: kkzgrk
- Resolution or deferral rationale: NOT answered by the repository and not yet ruled by the maintainer; FLAGGED FOR THE REVIEWER AND MAINTAINER. DEFAULT IMPLEMENTED: phrase-list-only, a single `OPERATOR_PHRASES` constant, following the spec's own leaning (Section 5 "a small, deterministic ruleset (phrase list + structural rules)" where the structural rules are R1/R3, and Section 6 "intentionally conservative to keep false positives low"). A structural second-person-imperative heuristic would be the main false-positive risk the spec names in Section 10, and nothing measured today needs it (0 hits). Changing this later is additive. The carrier is the source backlog item `kkzgrk`, which stays the durable home for the ruling until this plan executes.

### OQ-02: Is an escape hatch needed for a prompt that must quote a banned phrase (spec OQ2)?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: kkzgrk
- Resolution or deferral rationale: NOT answered by the repository and not yet ruled by the maintainer; FLAGGED FOR THE REVIEWER AND MAINTAINER. DEFAULT IMPLEMENTED: no escape hatch (YAGNI, the spec's leaning), because 0 of 17 tracked prompts need one, and an inline `aw-prompt-allow:` comment would itself be a second non-prompt line, which R1/P4 forbid. The one structural exemption that IS implemented is the leading metadata comment, which is required, not an escape hatch. If a real prompt ever needs to quote a phrase, the smallest addition is a fenced-code exemption for R2 only.

### OQ-03: Does anything read prompts' YAML front matter (spec OQ3)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Measured: no tracked prompt has YAML front matter, and every prompt reader (`prompts_index._parse_metadata_comment`, `prompts.read_metadata_id6`, `check_engine.validate_prompt_content`) reads the leading HTML comment only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_prompts_check.py -v` BEFORE E-02, showing every case failing with exit 2 / `invalid choice: 'check'`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a direct call `python3 -c "from pathlib import Path; from agent_workflows import prompts_lint as L; p=Path('<tmp fixture with a --- first line>'); print(L.check_prompt(p, p.read_text()))"` showing one `prompt.purity-R1` Drift with `location` ending in `:1`, and the same call on the A4 copy printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `grep -rn "run separately and compare" agent_workflows/` showing exactly ONE hit, in `prompts_lint.py`'s `OPERATOR_PHRASES`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_prompts_check.py tests/test_command_surface_declarations.py -v` all passing, with the A5 test name visible as PASSED; and pasted `python3 -m agent_workflows prompts check --help` first lines.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted output of `python3 -m agent_workflows check prompts --all --agent --dir <tmp repo with the A2 fixture>` showing a `prompt.purity-R3` diagnostic and exit 1, and the passing test that asserts the two commands agree.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `grep -n "aw prompts check" AGENTS.md agent_workflows/engine.py` showing the sentence in both, the AGENTS.md hit located between `<!-- aw:pointer -->` and `<!-- aw:reporting -->`; plus the pasted `merge_aw_block` action and warnings list from the regeneration (action `refreshed`, no drift warning), and `git diff --stat AGENTS.md` showing only the added lines.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted `grep -n "aw prompts check" .aw/records/prompts/README.md .aw/system/workflows/templates/prompts-README.md .aw/system/workflows/research-prompt/research-prompt.md` with at least one hit per file.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `grep -n "\.agents/prompts\|local/" <new spec path>` returning no stale path (a hit only where the text explains the retired `local/` name is acceptable, and must be quoted); pasted `aw specs check <new spec path>` conforming; pasted spec metadata line `- Status: implementing` and its new path under `.aw/records/specs/implementing/`; and the final report's proposed `aw specs set implemented ... --evidence ...` command quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted `python3 -m agent_workflows prompts check; echo rc=$?` showing no findings and `rc=0`; pasted `--agent` form output (empty record set or a clean result record) with `rc=0`; pasted `check prompts --all` and `check all` outputs showing no `prompt.purity-*` rule id.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted `ruff check` and `ruff format --check` on `agent_workflows/prompts_lint.py agent_workflows/cli.py agent_workflows/check_engine.py agent_workflows/command_surface.py agent_workflows/prompts.py agent_workflows/engine.py tests/test_prompts_check.py` with no findings; the pasted final summary line of bare `python3 -m pytest` showing `N passed` and no failures; pasted `git diff CHANGELOG.md` showing one `Added:` line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A new read-only lint, `aw prompts check`, implementing approved spec `20260808-1958-01-prompt-purity-lint` (R1 structure, R2 user-directed phrases, R3 delimiter markers), also folded into `aw check prompts`. It reports 0 findings on this repository today (measured). Two spec questions are implemented at the spec's own leaning and remain OPEN for the maintainer (OQ-01 phrase-list-only, OQ-02 no escape hatch); neither blocks, and either can be changed additively later. The spec's stale `.agents/` paths are corrected and the spec moves to `implementing`; a human marks it `implemented` with the evidence command the executor supplies.

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`). The one anticipated out-of-fence write is `.aw/system/managed-sections.json`, needed ONLY if the manifest drift-preserve rule blocks the AGENTS.md regeneration (E-06).

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest`. Never set the spec `implemented` yourself.

Commit only the Scope-Paths files via `aw commit mi4s9f -- <paths>`, never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner under `aw oc run`/`aw agy run`).
