# Review findings: plan 1vfqdu

- Subject-Id: 1vfqdu
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran at HEAD `01c564538` in the non-interactive runner review-sweep lane `review-sweep-run-20261114T011656Z-594596`. The tracked plan was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 errors, 0 warnings, 2 `IPD-C802` em-dash advisories on the validation preamble). After all edits (including `E-05`/`V-05`, `- Highest E allocated: 05`), `aw ipd lint --phase author --agent` and `aw ipd lint --phase review-finalize --agent` both returned `clean` with 0 findings. No prior review record existed for this plan; earlier rounds were recorded only in the plan's workflow history.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, E-01, F-01 | Cited `cli.build_parser` | Cites `cli._build_parser` (the only parser builder) | PR-010 |
| Scope | Attributed the chain and stamp to `vxevph` and the `--describe-*` options to `odeo9z` | Chain and stamp `g8na48`; preflight and journal `vxevph`; `--describe-*` `ya4ee4`; names the one `chain.py` addition | PR-006 |
| E-01 | Metadata leaf dispatch unspecified; completion edit asserted | Dispatch through `Migration.run`; leaf not phase-gated; completion is introspection-driven | PR-003, PR-004 |
| E-02 | Layout step through `MigrationManager.execute_migration`; metadata through `m0001_metadata_v2.run`; five cases | Layout through `cli._run_migrate_layout`, `--commit` forward, clean-tree check, distinct `dest` names, `Migration.run`, seven cases | PR-001, PR-002, PR-003, PR-009 |
| E-03 | Raw terminal test; no command printed after a no; fixed prompt text; stamp value unexplained | `term.is_interactive`; command printed after a no; per-migration prompt; stamp-value rationale; phase-A no-offer outcome | PR-001, PR-008 |
| E-04 | Pseudo-terminal with patched constant; edit to top-level completion assertion | In-process calls with `--interactive`; nested completion assertion; three more existing modules | PR-004, PR-005, PR-008 |
| E-05 (new), V-05 (new) | `pending_migrations` folded into E-02 as optional | Own item with four direct cases | PR-001, PR-011 |
| Step 0 | Root declaration assumed accepted | Measured: no root declared today; conformance suites listed; commit policy, phase A and terminal predicate recorded | PR-002, PR-005 |
| Findings | F-04 claimed top-level expectation changes | F-04 corrected; F-05 to F-07 added | PR-002, PR-003, PR-004, PR-001 |
| Proposed changes | No diagram | Mermaid `flowchart TD` of the bare runner (requirement 12 b) | PR-010 |
| Deferred | One carrier `vxevph` for chain, stamp, preflight, journal | Two entries: `g8na48`, `vxevph` | PR-006 |
| Spec / documentation sync | "user documentation lands with `90iqr1`" | States no plan carries it, with measurement; points at OQ-08 | PR-007 |
| OQ-07 | Cited `g5hpbb` E-06 | Cites `bv4kkj` E-01 (carried from `g5hpbb` E-06) | PR-006 |
| Validation preamble | Two em dashes | Commas | PR-010 (`IPD-C802`) |
| V-01 to V-05 | Five bare cases, four modules, AC-28 without printed command | Seven bare cases, seven modules, printed command, phase-A case, V-05 | PR-002, PR-005, PR-008, PR-011 |
| Approval gate | "All open questions are resolved." | Blocking questions resolved, OQ-08 non-blocking; stop on an absent prerequisite symbol | PR-003, PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| I-01 | Spec / documentation sync, OQ-08 | Which plan documents the `aw migrate` family for users | Maintainer scope decision | Add it to the `y1zihp` cutover docs patch; keep `--help` here | medium |

### Step T

1. Yes. It adds the public `aw migrate` group, `aw migrate metadata`, `aw migrate layout`, bare `aw migrate`, and `aw install`/`aw setup` `--migrate`, and adds `chain.pending_migrations`, which E-03 and later plans rely on.
2. Yes. The bare runner's layout step commits through `cli._report_and_commit_migration`, and the install path can start a migration that rewrites the records tree; it does not edit the commit helper, lock or sandbox modules themselves.
3. Yes. Five `E-*` items in three task groups across `cli.py`, `command_surface.py`, `migrations/chain.py`, `engine.py`, and three test modules.
4. Yes. `- Scope-Paths:` lists every file, including `completion.py`, which may stay unmodified (acknowledge at finalize).
5. Yes. Offering `m0001` through `aw install` before the cutover would convert user repositories to a format phase-A code cannot read (PR-001).

AW-TIER: complex

### Step R1

- Checked: every symbol and record the plan cites, located by symbol or quoted text: `cli._build_parser` (no `build_parser` exists), `cli._run_migrate_layout`, `cli._report_and_commit_migration`, `cli._add_commit_flags`, `cli._show_family_help`, `cli._run_install`, `cli._install_all`, `cli._run_setup`, the install `-y` help "Skip preflight confirmations." and setup "Install without per-repo prompts.", `layout_inventory._default_roots`, `layout_inventory.DEFAULT_ROOTS`, `engine.detect_split_brain_layout`, `layout_migration.MigrationManager.execute_migration` and `_acquire_lock`, `command_surface.discover_parser_leaves`, `discover_parser_roots`, `find_undeclared_leaves`, the `migrate-layout` `CommandDeclaration`, `completion._positional_choices`, `completion.introspect_cli_tree`, `tests/test_completion.py` `with_choices` assertion, `term.is_interactive`, the `common` parent's `--agent`/`--json`; records `4sd62s` (5.1, 5.3, AC-11, AC-28), `g8na48` E-01, `vxevph` E-02 to E-05, `dcerjg` E-15, E-16, OQ-03, `bv4kkj` E-01, `ya4ee4` Scope, `90iqr1`, `qhay6a`, `a49djh`, `y1zihp`, `ngc2a2`.
- Not found: `cli.build_parser` (PR-010); `m0001_metadata_v2.run` in the `vxevph` plan (PR-003); any `aw migrate` documentation carrier (PR-007). Moved: `g5hpbb` E-06 to `bv4kkj` E-01; chain and stamp from `vxevph` to `g8na48` (PR-006). Contradicted: F-04's claim that the top-level completion expectation changes (PR-004).

### Step R2

- Checked: E/V bijection (5/5 after `E-05`/`V-05`), Scope-Paths (every edited file declared; `chain.py` now has a definite change), Item-Dependencies (`g8na48` added because E-01 to E-05 call its contract directly; `vxevph` depends on it, so the edge was transitive but undeclared), concrete evidence in each `V-*`, and no hardcoded record-tree counts.
- Reverse edges: `dcerjg` and `o19353` depend on `executed:1vfqdu`; `ya4ee4` and `bv4kkj`, which add options to and chain into `aw migrate metadata`, depend on `dcerjg`, so they follow this plan transitively.

### Step R3

- Checked: the full security form. No identity, secret or network surface. The material risk is unintended mutation of user repositories: install and bare `aw migrate` reaching `m0001` before the cutover (PR-001), and bare `--apply` committing layout moves (PR-002, which now follows the existing explicit `--commit` convention and never commits silently). `--migrate` adds neither `--force` nor `--force-worktree` (AC-28 case 4). The plan's safety rule keeps every apply on `tmp_path`.

### Step R4

- Checked: A (ordering and partial failure in the bare runner, stop at first refusal, clean-tree precondition for the metadata step), C (reuse of `_run_migrate_layout`, `_add_commit_flags`, `term.is_interactive`, the chain contract; one `pending_migrations` definition), D (invariants: AC-28 "-y never starts a migration", AC-11 "install never stamps a legacy repository", phase A "nothing converts before the cutover", each mapped to a V-03, V-02 or V-05 case), E (in-process calls where the constant is patched), F (empty state "nothing to migrate", recovery hint on an uncommitted layout step), right-sizing (E-02 density reduced by E-05), and documentation sync (PR-007).

### Step R5

- Checked: QA/QC (each new behavior has a case with byte-level assertions); testing (conformance suites over declared commands added); UI/UX (prompt names the migration, a no prints the command); architect (one offered-migration definition, chain contract not module internals); software engineer (argparse `dest` collision, PR-009); power user (`--commit`/`--no-commit` forwarding, `--json` per step); novice (bare `aw migrate` dry run by default; "nothing to migrate"); stakeholder (no user repository converted before the cutover).

### Step R6

- Checked: whether the plan should become a Set. Five items, one concern each after `E-05`; the CLI group, the runner and the install prompt share the chain contract and test fixtures. No split recommended.

### Step R7

- Checked: `metastore` siblings `g8na48`, `vxevph`, `dcerjg`, `bv4kkj`, `ya4ee4`, `o19353`, `90iqr1` and its docs-patch writers, against the orchestrator `63ib9r`.
- Cross-plan gaps outside this plan's ownership, for the owning plans' reviewers: (1) `g8na48` E-01 says `m0001_metadata_v2.run` is "created by `vxevph`", but the `vxevph` plan never names a `run` entry point or its signature; this plan's gate now stops if it is absent. (2) `dcerjg` E-16's CHANGELOG line names `aw migrate metadata`, `aw migrate layout` and `aw install --migrate` but not bare `aw migrate`. (3) No docs plan carries the family (PR-007, OQ-08).

### Step S5

- Checked: OQ-06 and OQ-07 (resolved; OQ-07 reference updated); new OQ-08 from PR-007, left `open`, `Blocking: no`, `Owner: maintainer`, because carrier placement in the Set is a scope decision and the plan's E-items do not depend on it. No finding at or above `HIGH` is left unfixed, so no blocking escalation is required. Decisions D-1 to D-6 below were resolved from repository evidence; all are reversible plan edits.

### Pass 2

- Re-reviewed E-01 to E-05 and V-01 to V-05 because `E-05`/`V-05` were added and `- Item-Dependencies:` changed. Swept superseded tokens (`execute_migration` as the bare runner's layout path, "five" cases, `odeo9z`, `g5hpbb` as a live carrier, `cli.build_parser`, "pseudo-terminal", "four modules", "All open questions are resolved"): none remain outside F-05's quoted evidence and OQ-07's provenance note. Lint `clean` at `author` and `review-finalize`.
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4-A, R3 / E-02, E-03 | `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:45` (`m0001.is_pending` ignores `CURRENT_METADATA_SCHEMA`); `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:199` (phase-A code reads only the legacy format) | Install, setup and bare `aw migrate` would offer and, on yes or `--migrate`, run `m0001` on real repositories before the cutover, converting them to a format the installed toolkit cannot read. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | New E-05 `chain.pending_migrations` (pending AND `target_schema <= CURRENT_METADATA_SCHEMA`) used by E-02 and E-03; explicit `aw migrate metadata` left ungated for `dcerjg` E-15; phase-A cases in V-02, V-03, V-05. Recommendation strength: strong. |
| PR-002 | HIGH | IN-SCOPE | R1, R4-A / E-02 | `agent_workflows/cli.py::_run_migrate_layout` ("return _report_and_commit_migration(args, term, mgr, json_out)"); `agent_workflows/cli.py::_report_and_commit_migration` (non-interactive without `--commit`/`--yes` commits nothing); `vxevph` E-02 condition (2) | Bare `--apply` called `MigrationManager.execute_migration` directly, skipping backend, leftovers, rename and commit handling, and its uncommitted moves make the metadata preflight refuse, so "layout then metadata" fails on the normal path. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Layout step goes through `cli._run_migrate_layout` `action="apply"`; bare group registers `cli._add_commit_flags` and forwards them; metadata starts only when the layout step exited 0 and the records root is clean; new case (3). Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1, R7 / E-01, E-02, E-03, front matter | `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:45` (`Migration.run` contract); `rg -n "m0001_metadata_v2.run"` finds no match in the `vxevph` plan | The metadata leaf's dispatch was unspecified, E-02 called the module function rather than the chain contract, the delegate is not named by its creator, and the direct `g8na48` dependency was undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three items call `Migration.run`; `executed:g8na48` added; gate stops on an absent `Migration.run`, `CURRENT_METADATA_SCHEMA` or `m0001_metadata_v2.run`; gap reported in R7. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | R1 / F-04, E-01, E-04 | `tests/test_completion.py` (`with_choices` iterates only top-level subcommands); `agent_workflows/completion.py::_positional_choices` | F-04 claimed the top-level expectation changes and E-01 asked for a hand completion entry; nested choices come from the parser automatically and the top-level list is unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 corrected; E-01 edits `completion.py` only if needed; E-04 adds a nested assertion. Recommendation strength: strong. |
| PR-005 | MEDIUM | UNDER-SCOPE | R2, R4-E / E-04, V-04 | `agent_workflows/command_surface.py::discover_parser_roots` intersected with `get_declared_leaves` is empty; `tests/test_exit_contract_conformance.py` iterates `command_surface.get_declared_leaves()` | Declaring a parser root has no precedent and every declared command feeds the exit-contract and conformance suites, which V-04 did not run; `tests/test_migrate_layout_cli.py` was listed but never validated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 add `tests/test_migrate_layout_cli.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py`. Recommendation strength: strong. |
| PR-006 | MEDIUM | IN-SCOPE | R1, R7 / Scope, Deferred, OQ-07 | `.aw/records/plans/pending/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md:6` (chain moved to `g8na48`); `.aw/records/plans/pending/20261102-metastore-05-ya4ee4-build-the-short-description-journal-and-the-tool-less-saniti.ipd.md:6` (owns `--describe-*`); `.aw/records/plans/pending/20261109-metastore-105-bv4kkj-chain-the-layout-migration-as-stage-one-of-aw-migrate-metada.ipd.md:37` | Stale carriers after the round-3 splits; Scope and Deferred disagreed on the `--describe-*` owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carriers corrected to `g8na48`, `vxevph`, `ya4ee4`, `bv4kkj`. Recommendation strength: very strong. |
| PR-007 | MEDIUM | UNDER-SCOPE | R4 Spec and documentation sync | `README.md` section "Layout Migration" documents only `aw migrate-layout`; `rg -n "migrat"` on the `90iqr1`, `qhay6a`, `a49djh`, `y1zihp`, `ngc2a2` plans finds no `aw migrate` documentation | The plan said user documentation lands with `90iqr1`; no plan carries it. | C:Low; U:Medium-High; S:Low; F:Medium; Overall:Medium-High | OPEN | Raised as non-blocking OQ-08 (`Owner: maintainer`). Usability: documenting `aw migrate metadata` before the cutover invites users to run a migration their phase-A toolkit cannot read, so the carrier and timing are the maintainer's scope call; required decision: which plan carries it; consequence if unresolved: the family ships with `--help` only. Recommendation: `y1zihp` cutover docs patch; strength: medium. |
| PR-008 | MEDIUM | IN-SCOPE | R4-D, R4-E / E-03, E-04 | `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` AC-28 case (1) ("prints the command that runs the migration"); 5.1 ("asks, for each one"); `agent_workflows/term.py::is_interactive` | A terminal no printed no command; the prompt was fixed to `m0001`; the stamp value's departure from 5.3's literal 2 was unexplained; a pseudo-terminal subprocess cannot see a patched constant. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 prints the command after a no, prompts per migration, explains the constant, uses `term.is_interactive`; E-04 runs patched cases in-process with `--interactive`. Recommendation strength: strong. |
| PR-009 | LOW | IN-SCOPE | R4-A / E-02 | `agent_workflows/cli.py::_build_parser` (`migrate-layout` registers its own `--apply`) | A group-level `--apply` sharing a `dest` with the `layout` leaf is overwritten by the leaf's default when argparse merges the subparser namespace. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires distinct `dest` names. Recommendation strength: medium. |
| PR-010 | LOW | IN-SCOPE | R1, Proofreading / Concern, E-01, F-01, Proposed changes, validation preamble | `agent_workflows/cli.py::_build_parser`; `aw ipd lint` `IPD-C802` (two em dashes); technical-writing requirement 12 (b) | Nonexistent `cli.build_parser` citation, two em dashes, and no diagram for a branching process. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citations corrected, dashes replaced, flowchart added. Recommendation strength: strong. |
| PR-011 | MEDIUM | IN-SCOPE | R4 right-sizing / E-02 | `.aw/records/plans/pending/20261107-metastore-16-1vfqdu-add-the-aw-migrate-command-group-bare-aw-migrate-and-the-ins.ipd.md` E-02 after PR-001 and PR-002 | With the phase helper folded in, E-02 named a second file and a second test surface (about 12 units). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `chain.pending_migrations` moved to new `E-05`/`V-05`; E-02 and E-03 depend on it. Recommendation strength: medium. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should install, setup and bare `aw migrate` offer `m0001` before the cutover? | No: offer only migrations with `target_schema <= CURRENT_METADATA_SCHEMA` (`chain.pending_migrations`) | Offer whenever `is_pending` (rejected: converts repositories phase-A code cannot read); gate install only (rejected: bare runner has the same risk, two definitions) | `dcerjg` OQ-03 (phase-A code reads only the legacy format); `g8na48` OQ-03 pattern (constant flips at Order 13, tests patch it); `dcerjg` E-16 ("the migration does not yet run on any repository") | yes |
| D-2 | How does bare `--apply` run the layout step so the metadata step can follow? | Through `cli._run_migrate_layout` `action="apply"` with forwarded `--commit`/`--no-commit`; metadata only on a clean records root | Call `execute_migration` directly (rejected: skips commit and resolution); always auto-commit (rejected: the selfcommit convention never commits non-interactively without `--commit`) | `cli._report_and_commit_migration` docstring; `cli._add_commit_flags` docstring; `vxevph` E-02 condition (2) | yes |
| D-3 | Is the explicit `aw migrate metadata` leaf phase-gated too? | No | Gate it (rejected: `dcerjg` E-15 runs it on a copy before the cutover and expects a census refusal) | `dcerjg` E-15 steps (a), (b), (e) | yes |
| D-4 | What value does install stamp on a repository without legacy records? | `chain.CURRENT_METADATA_SCHEMA` | Literal 2 per 5.3 (rejected: a repository installed in phase A then receives legacy records while stamped 2 and is never offered `m0001`) | `g8na48` E-01 (`CURRENT_METADATA_SCHEMA = 1` until Order 13); `4sd62s` 5.3 holds after the cutover | yes |
| D-5 | What decides "at a terminal" for the install question? | `term.is_interactive()` | Raw `isatty` on stdin and stdout (rejected: ignores `--no-interactive`/`AW_NONINTERACTIVE` and prevents in-process tests with a patched constant) | `agent_workflows/term.py::is_interactive` precedence docstring | yes |
| D-6 | Where does `pending_migrations` live in the checklist? | Its own `E-05`/`V-05` | Keep it inside E-02 (rejected: second file and test surface in one item) | R4 right-sizing diagnostics (a), (b) | yes |
