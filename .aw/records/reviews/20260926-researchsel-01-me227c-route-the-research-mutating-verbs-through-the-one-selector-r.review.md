# Review: Route the research mutating verbs through the one selector resolver

- Subject-Id: me227c
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `863220b8`. The target plan was committed and unchanged (last touched by
`c781e187`), so the pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and `--phase
review-finalize` reported exit 0 after the revisions.

EVERY ONE OF THE PLAN'S SIX FINDINGS HOLDS, and I re-measured each rather than trusting the numbers.
`aw find research reference` lists 66 rows; `aw archive research reference` prints `no research doc or
set matches 'reference'` at exit 0; `aw rename research reference` prints `error: no research file has
id6 'reference'`; `aw archive research awmetastore` previews exactly 7, and
`resolve_for_mutation(".", "research", "awmetastore")` returns those same 7. The five private loops are
where the plan says they are, `rg` confirms none of the three modules imports `selectors`, and
`p_archive` genuinely has no `--force`. The plan's diagnosis is correct and its F-1..F-6 table is
accurate.

THE REVIEW TURNED ON WHAT HAPPENS IF YOU ACTUALLY DO IT. The plan asserts, in OQ-02 and throughout,
that routing is behavior-preserving for id6 and setid targets. I did not accept that from the two
matching counts on THIS repo; I built temp repos and drove the proposed routing. It is not
behavior-preserving, in two independent ways, and each would have shipped as a regression.

PR-601 IS THE ONE THAT WOULD HAVE BROKEN THE SUITE AND THE VERB TOGETHER. There are TWO independent
authorities for "where does research live", and they disagree. `research_contract.resolve_research_root`
knows the legacy `.agents/docs/research` nesting, and `research_contract.RESEARCH_ROOT` is literally
that string. `selectors.record_dirs` does not: it takes `record_producers.resolve_record_read_paths`
plus the literal `.aw/records/research` and `.agents/research`, and the legacy nesting appears in
neither. On a temp repo holding one conformant document under `R.RESEARCH_ROOT`,
`resolve_research_root` returns the directory, `record_dirs` returns `[]`, and
`resolve_for_mutation(root, "research", "bbbbbb")` answers `no research artifact matched 'bbbbbb'`
while today's `run_archive(target="bbbbbb", apply=True)` archives that document and returns 0. So the
plan's own change would convert a working archive into a silent no-match at exit 0 on any
legacy-layout repo. It is not a hypothetical population: that layout is what EVERY existing research
fixture builds (`tests/test_research_archive.py`, `tests/test_research_cmd_create.py`,
`tests/test_research_index.py` all use `root / R.RESEARCH_ROOT`), so the shipped
`TargetedArchiveTests::test_targeted_archive_moves_to_archive_shard` would have failed and E-11's own
new fixture, which the plan specifies "all under `R.RESEARCH_ROOT`", could not have passed either.
Worth naming precisely: the plan's E-03 predicted "existing `TargetedArchiveTests` ... pass
unchanged", which measurement contradicts.

PR-602 IS THE ONE WITH THE WORSE FAILURE MODE. `selectors._hits_for(MATCH_PATH)` returns any
`is_file()` hit under the repo root and never checks that the hit is a record of the requested type, so
`resolve(repo, "research", "README.md")` returns the repository's own README with `kind='path'`. Fed
through the plan's proposed routing, `research_cmd.plan_set_outcome` planned a 26200-byte rewrite of
`README.md` (635622 bytes for `agent_workflows/cli.py`), and `plan_mv`/`plan_set_assign` raised
`AttributeError: 'NoneType' object has no attribute 'kind'` because `R.parse_name('README.md')` returns
None. `run_set_outcome` would then also raise `ValueError` at `target.relative_to(root)`. This is not a
novel restriction to invent: `selectors.resolve_one` already passes `deny=frozenset({MATCH_PATH})`, and
`cli._resolve_selectors_with_kinds` behind `aw find` denies it too, both for this class of reason. The
plan instead promised the opposite in E-05's expected outcome ("a path selector to a research doc now
works"), which is the one sentence in the plan that, if honored literally, hands a mutating verb an
unbounded target set.

I FIXED BOTH RATHER THAN DEFERRING, because both fixes are bounded and measurable. E-03 adds one
`_add(repo_root / ".agents" / "docs" / "research")` to `_record_dirs_cached`, which I verified leaves
this repo's `record_dirs` byte-identical (it has no `.agents/`) while making the legacy fixture
resolve. E-04 adds ONE confined helper carrying both the `MATCH_PATH` deny and a research-root
containment check, so the confinement exists once instead of three times. Both got guard tests in a new
E-10 that must be shown FAILING with their own guard reverted, because a guard test that passes without
its guard is decoration.

PR-603 is the consequence of PR-602 that had to be decided rather than papered over. Denying
`MATCH_PATH` makes the plan's "path selector now works" claim false, so I inverted it: a path token is
REFUSED, which is PARITY with `aw find research <path>` (it matches nothing there today either) rather
than a regression. That required editing three separate places where the plan asserted a path token
resolves (E-04's and E-08's expected outcomes, E-11 case 1, V-04's evidence), and E-11 gained case (7)
pinning the refusal. Recorded as OQ-04 and decision D-2 because it is a deliberate narrowing of what
the plan advertised.

PR-604 is a signature problem the plan waved at and would have hit. E-05 said to derive `repo_root`
"from `research_root` via the existing research-root authority", and there is no such authority:
`resolve_research_root` is one-way and no inverse exists. Worse, the two `research_cmd` planners take
`research_root` and not `repo_root` (`_research_root` discards it), and five shipped test call sites in
`tests/test_research_cmd_create.py::SetOutcomeTests` pass it positionally. E-08 and E-09 now name the
threading explicitly and require those tests to stay green.

PR-605 is small but would have let a real omission pass as verified. E-04's expected outcome rested on
`python3 -m pytest tests/test_command_surface*.py` passing. That glob matches exactly one file, whose
only test asserts `find_undeclared_leaves(...) == set()` - parser LEAVES, not flags - and no shipped
test compares `archive`'s `legacy_flags` to its parser (only `prompts new` has one). So the suite would
have gone green whether or not the declaration was updated. V-07 now asserts the tuple contents
directly.

PR-606 and PR-607 are structure. The plan's `Scope-Paths` declared `selectors.py` READ-ONLY and its
Scope check said so twice, which the fixes contradict, so both are corrected and justified. And the
gate was missing a statement of the two shipped behaviors a human is now approving beyond the stated
concern (a shared-resolver change affecting every record type on a legacy repo, and a narrowing of
accepted selectors), plus a genuine stop condition for the case where E-03 turns out not to be
additive. Right-sizing went 8 items to 12; nothing was split for its own sake, and the two new guards
plus their test item are the additions.

TWO THINGS I CHECKED AND FOUND CORRECT, recorded so a later reader does not re-derive them. OQ-02's
parity claim holds for THIS tree on its own terms: 0 of 122 documents have a filename id6 or setid
differing from their declared `id:`/`set:`, so reading the declared field is a no-op here. And OQ-01's
resolution is right: `resolve_for_mutation` returns exactly the refusal the plan quotes for `reference`
(66 candidates) and for `archive` (32), so the widening backlog `mblu3p` warned about genuinely does
require an explicit `--force`. The plan also correctly identified that `cli._run_archive` copies
`vars(args)`, so `--force` needs no dispatch change.

The plan carries `- Work-Kind: bug` and `- Blocks-Release: next`, which the every-live-bug rule
requires, and `- From-Backlog: mblu3p`, so the gate handoff is intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | BLOCKER | UNDER-SCOPE | A. Correctness / D. Anti-regression | Temp repo, one conformant doc under `root / R.RESEARCH_ROOT`: `research_contract.resolve_research_root(root)` -> `.agents/docs/research`; `selectors.record_dirs(root, "research")` -> `[]`; `selectors.resolve_for_mutation(root,"research","bbbbbb")` -> `([], "no research artifact matched 'bbbbbb'")`; while `research_archive.run_archive(target="bbbbbb", apply=True)` -> rc 0, document archived. `record_producers._LEGACY_RECORD_CLASS_SUBPATHS["research"] == "docs/research"`. Fixtures: `tests/test_research_archive.py`, `tests/test_research_cmd_create.py`, `tests/test_research_index.py` all build `root / R.RESEARCH_ROOT` | THE ROUTING IS A SILENT REGRESSION, NOT A FIX, ON THE LEGACY LAYOUT. Two independent authorities answer "where does research live" and they DISAGREE: `resolve_research_root` knows `.agents/docs/research`, `selectors.record_dirs` does not. Routing a verb from the first to the second therefore turns a WORKING `aw archive research <id6>` into `no research doc or set matches` at exit 0 - a silent no-match on a mutating verb, which is the exact defect class this plan exists to remove. The plan assumed the routing was behavior-preserving (OQ-02, and E-03's "existing `TargetedArchiveTests` pass unchanged") and measurement contradicts both: that layout is what every shipped research fixture builds, so the suite would have gone red and E-11's own new fixture could not have passed. | C:Low; U:Low; S:Low; F:High if unfixed; Overall:Low (the fix is one additive `_add` call, proven non-perturbing) | FIXED | Added E-03 teaching `selectors._record_dirs_cached` the legacy research nesting, with `_add`'s no-op-on-missing behavior cited as why it is additive; added E-02(a) to REPRODUCE the disagreement first; added `agent_workflows/selectors.py` to `- Scope-Paths:`; added guard test E-10(a) that must FAIL with the E-03 hunk reverted; V-03 requires the before/after `record_dirs` proof on this repo AND for two non-research types, and notes the `functools` cache. Added F-7. Recorded as OQ-03 and decision D-1. A stop condition in the gate covers the case where the change proves non-additive. |
| PR-602 | BLOCKER | UNDER-SCOPE | B. Security (default-deny, resource-scoped) / A. Correctness | `selectors._hits_for(MATCH_PATH)` returns any `is_file()` hit with no type check. Driven at review on the real tree: `resolve(repo,"research","README.md")` -> `kind='path'`, the repo's own `README.md`, NOT under the research root; fed to `research_cmd.plan_set_outcome` -> planned 26200-byte rewrite (`agent_workflows/cli.py` -> 635622); `R.parse_name('README.md')` -> `(None, "name must include a '.<kind>' suffix before '.md'")` -> `plan_mv`/`plan_set_assign` raise `AttributeError: 'NoneType' object has no attribute 'kind'`; `run_set_outcome` raises `ValueError` at `target.relative_to(root)`. Existing denies: `selectors.resolve_one` (`deny=frozenset({MATCH_PATH})`), `cli._resolve_selectors_with_kinds` | ROUTING WITHOUT A KIND DENY HANDS A MUTATING VERB AN UNBOUNDED TARGET SET. The resolver's `path` kind is deliberately unconfined and every caller confines it itself; the plan routed four research MUTATIONS through it with no deny and no containment check, and then promised in E-05 that "a path selector to a research doc now works". Honoring that literally means `aw research set-outcome README.md` plans a frontmatter rewrite of the repository README, and two other verbs crash with unhandled exceptions instead of refusing. The plan named no confinement anywhere, so this was invisible to its own validation. | C:Low; U:Low; S:High if unfixed (a mutating verb reaching arbitrary repo files); F:Medium; Overall:Low (the deny is one argument the shipped code already uses at two sites) | FIXED | Added E-04: ONE shared `_resolve_research_for_mutation`/`_resolve_one_research` helper carrying BOTH the `MATCH_PATH` deny and a research-root containment plus `parse_name` check, so the confinement exists once rather than three times and survives a later precedence change. E-06/E-08/E-09 now call the HELPER and are told explicitly not to call `resolve_for_mutation` directly. Added E-02(b) to reproduce, guard test E-10(b) that must FAIL with the confinement reverted, and V-04 requiring refusals for `README.md` and `cli.py`. Added F-8. Recorded as OQ-04 and decision D-2. |
| PR-603 | MEDIUM | IN-SCOPE | F. Honest documentation / D. Anti-regression | Plan as authored, E-05 expected outcome: "a path selector to a research doc now works"; E-07 case (1) required path-token parity; `cli._resolve_selectors_with_kinds` denies `MATCH_PATH`, so `aw find research <path>` matches nothing today | THE PLAN ADVERTISED A CAPABILITY THAT CONTRADICTS ITS OWN PARITY GOAL. Its stated goal is that a selector learned from `aw find research` resolves the same way on a mutating verb. `aw find` DENIES the path kind, so making the mutating verbs ACCEPT it creates a NEW divergence in the opposite direction, while also being the mechanism of PR-602. Three separate places asserted the path token resolves, so fixing PR-602 without fixing them would have left the plan internally inconsistent and an executor free to pick either reading. | C:Low; U:Medium (a user could reasonably expect a path to work); S:Low; F:Low; Overall:Low | FIXED | Inverted the claim in all four places (E-04 and E-08 expected outcomes, E-11 case 1, V-04 evidence): a path token is REFUSED, and that is PARITY with `aw find`, not a regression. E-11 gained case (7) pinning the refusal explicitly and stating it passes before AND after for different internal reasons. OQ-04 records the decision and its accepted consequence. |
| PR-604 | MEDIUM | IN-SCOPE | A. Correctness / G. Plan executability | Plan E-05 as authored: "derive `repo_root` from `research_root` via the existing research-root authority". `research_contract.resolve_research_root` is one-way; no inverse exists in the module. `research_cmd._research_root` returns `R.resolve_research_root(...)` and discards `repo_root`. `tests/test_research_cmd_create.py::SetOutcomeTests` calls `C.plan_set_outcome(self.research, ...)` at 5 sites, passing `research_root` positionally | THE PLAN NAMED A NON-EXISTENT AUTHORITY FOR A PARAMETER THREE ITEMS NEED. The resolver requires `repo_root`; `_find_by_id6`, `plan_set_outcome` and `plan_set_priority` all have only `research_root`, and no function inverts one to the other. E-05 offered the derivation FIRST and the threading as an alternative, so an executor following the primary instruction would search for something that is not there. The `research_cmd` pair is worse than `research_refs`: its callers do not hold `repo_root` either, and five shipped test call sites pin the current positional signature. | C:Medium; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-08 now states there is NO inverse and instructs threading from `run_set_assign`/`run_mv` (which hold it via `_repo_root(args)`). E-09 names the harder case explicitly, requires the executor to state WHICH approach it took and why, and requires `tests/test_research_cmd_create.py` green; V-09 demands that run's output. Both items now also name the crash sites the confinement protects (`.kind` access, `relative_to`). |
| PR-605 | LOW | IN-SCOPE | E. Testing and verification | `tests/test_command_surface_declarations.py` holds ONE test asserting `find_undeclared_leaves(parser) == set()`; `find_undeclared_leaves` compares parser LEAVES to declared leaves and never inspects flags; `rg -n legacy_flags tests/` -> `test_prompts_new.py`, `test_workflow_artifacts_prune.py`, `test_installer.py`, `conformance_matrix.py` only; `tests/test_command_surface_declarations.py` passes 1 test in 0.27s untouched | THE NAMED VALIDATION CANNOT DETECT THE OMISSION IT IS SUPPOSED TO GATE. E-04 rested on `pytest tests/test_command_surface*.py` passing to confirm the `legacy_flags` update. That glob matches one file whose only assertion is about undeclared LEAVES, and no shipped test compares `archive`'s declared flags to its parser (only `prompts new` has such a test). The suite therefore goes green whether or not `--force` was added to the declaration, so the step would have been reported verified while undone. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now states what the surface tests do and do not prove, with the mechanism named so a later reader does not re-trust the glob. Its expected outcome and V-07 require a DIRECT `get_declaration("archive").legacy_flags` print showing `--force`. Added F-9 with the measurement. Required tests section updated. |
| PR-606 | LOW | IN-SCOPE | G. Plan executability (scope honesty) | Plan as authored: `- Scope-Paths:` omitted `selectors.py`; Scope check said "Over-scope: none" and "`agent_workflows/selectors.py` is READ and not modified"; Scope said OUT "the resolver's own policy" | THE DECLARED SCOPE CONTRADICTED THE WORK ONCE PR-601 WAS FIXED, and a fence that does not match the edit defeats the finalize reconciliation it exists to feed. The original under-scope note also left the `repo_root` threading as an open speculation ("if E-05 needs the repo root and no existing authority derives it") rather than a decision, which PR-604 shows was the wrong half to leave open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `agent_workflows/selectors.py` and `tests/test_cli_find.py` added to `- Scope-Paths:` with justification; Scope IN rewritten to lead with the two guards; Scope OUT narrowed to the resolver's AMBIGUITY POLICY specifically (consumed, never edited); Scope check rewritten to record that the original READ-ONLY claim was wrong and why, and that the threading is now decided rather than speculative. Gate fence enumerates the `selectors.py` surface as the `_record_dirs_cached` path ONLY. |
| PR-607 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: what-a-human-is-approving paragraph covering only the stated concern; `- Cohesion rationale: not required`; honesty rule referencing V-07; no stop condition | THE GATE DID NOT DISCLOSE THE TWO SHIPPED BEHAVIORS THE REVISED PLAN CHANGES beyond its stated concern: a one-line change to the SHARED resolver that every record type and verb routes through, and a NARROWING of which selectors the research mutating verbs accept. A human approving the original text would not have been approving either. The cohesion rationale was also absent while the item count grew to 12, and there was no stop condition for the one case that would make E-03 unsafe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained a TWO THINGS REVIEW ADDED paragraph naming both behavior changes and why each is required; a cohesion rationale explaining why the two guards are separate items; an updated honesty rule pointing at V-10/V-11 and requiring each guard test to fail with its own guard reverted; an extended never-`--apply` list now including `set-outcome`/`set-priority` with the measured reason; and a genuine STOP CONDITION for `record_dirs` changing on this repo or any non-research type. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The legacy `.agents/docs/research` layout is invisible to `selectors.record_dirs`. Fix it in the shared resolver, or work around it inside the research helper? | Fix it in `selectors._record_dirs_cached` (new E-03), additive, with a before/after non-perturbation proof required. | (a) Work around it inside the new research helper by unioning `resolve_research_root` - rejected: it leaves `aw find research` still blind to the legacy layout, which is the very per-verb divergence this plan exists to remove, and it creates a THIRD root authority. (b) Declare the legacy layout out of scope and accept the regression - rejected: it breaks three shipped test files and silently disables a mutating verb on real repos. (c) Change the research fixtures to the migrated layout instead - rejected: that hides the product defect by editing the tests, and real legacy repos would still break. | `selectors.record_dirs` docstring ("so this works for a bare/unregistered repo too") plus its existing per-type literal fallbacks; `record_producers._LEGACY_RECORD_CLASS_SUBPATHS["research"] == "docs/research"`; `research_contract.RESEARCH_ROOT`; measured `record_dirs(Path('.'),'research')` identical before and after on this repo | yes |
| D-2 | Should the confined research resolver DENY the `path` selector kind, or accept a path that is a research document? | Deny `MATCH_PATH` AND confine resolved paths to the research root (both), inverting the plan's advertised "a path selector now works". | (a) Accept a path when it happens to be a research doc - rejected on measurement: it is the mechanism by which `plan_set_outcome` planned a 26200-byte rewrite of `README.md`, and it creates a NEW divergence from `aw find`, which denies the kind. (b) Deny only, no containment - rejected: the deny is an argument a later edit can drop, while the containment is a property of the research planners themselves (they call `parse_name(...).kind` and `relative_to(research_root)` unguarded). (c) Containment only, no deny - rejected: it would silently accept an in-tree path, diverging from `aw find` for no stated benefit. (d) Ask the maintainer - rejected: the repository already denies this kind at two independent call sites for this class of reason. | `selectors.resolve_one` passes `deny=frozenset({MATCH_PATH})`; `cli._resolve_selectors_with_kinds` does the same behind `aw find`; driven measurement of `plan_set_outcome`, `plan_mv` and `run_set_outcome` on `README.md` and `agent_workflows/cli.py` | yes |
| D-3 | The plan claimed routing is behavior-preserving for id6 and setid. Accept that from the two matching counts on this repo, or drive it? | Drive it on temp repos in both layouts, and re-measure the declared-versus-filename identity population. | (a) Accept the plan's OQ-02 answer - rejected: the two counts (7 = 7, 1 = 1) were measured only on THIS repo in the migrated layout, which is exactly the configuration where the legacy defect is invisible. (b) Read the resolver and reason about it - rejected: reading shows `record_dirs` lacks the legacy path but not that every test fixture uses it, which is the fact that turns a latent gap into a red suite. | Temp repos in both layouts; `A._all_docs` versus `selectors._iter_paths` over the real tree (122 vs 124, the two extras being non-conformant templates); 0 of 122 documents with filename id6 or setid differing from the declared field | yes |
| D-4 | E-04's validation rested on `pytest tests/test_command_surface*.py`. Trust it, or verify what it asserts? | Verify; it cannot detect the omission, so require a direct assertion on the declaration tuple. | (a) Leave the glob as the evidence - rejected on measurement: the one matching file asserts only that no parser LEAF is undeclared, so it passes whether or not the flag was declared, and the step would be reported verified while undone. (b) Add a declared-flags-vs-parser test for `archive` modeled on `prompts new`'s - considered and NOT adopted: it is a new contract test for a surface this plan was not asked to harden, and the direct assertion in V-07 covers this plan's own risk. Worth filing separately. | `tests/test_command_surface_declarations.py` (one test, `find_undeclared_leaves`); `command_surface.find_undeclared_leaves` compares leaves only; `rg -n legacy_flags tests/`; the file passes 1 test untouched | yes |
