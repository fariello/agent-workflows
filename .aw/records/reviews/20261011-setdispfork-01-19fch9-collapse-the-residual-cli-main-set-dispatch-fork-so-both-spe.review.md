# Review findings: plan 19fch9

- Subject-Id: 19fch9
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b`. The plan was committed (`f769c5fb6`) and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision (two advisory `IPD-Z602` info diagnostics on E-02/E-03, judged single-concern:
each touches one function pair with constraints, not two deliverables). Not an orchestrator (`- Kind: child`), so
S407/S408 do not apply.

Verified at `b1b2fab2b`: `cli.main` `backlog_cmd == "set"` and `specs_cmd == "set"` branches still fork on
`if getattr(args, "status", None) is None:` (F-01 holds); `backlog.run_set` and `specs.run_set` default `actor` and
`_verb_label` unconditionally; `specs.run_set` derives `repo_root` via `_repo_root_of(Path(selectors[0]))`;
`status_set.run_set_command` resolves `repo_root` via `resolve_verb_repo_root(args.dir)` when none is passed;
`--actor` is a `common` parent flag so `args.actor` is `None` unless passed. Probes driving `cli.main` in scratch
repos built with `tests/test_set_dispatch_parity.py` helpers:

- Adapter reached? `patch.object(<module>, "run_set", wrapper)`: backlog flag True, backlog positional False, specs
  flag True, specs positional False (so E-04 case (1) is feasible and fails at base as claimed).
- Case (b) id6 from `<repo>/.aw`: rc 0 all four, same destination, identical sidecar records.
- Case (c) absolute selector from an unrelated cwd: rc 0 all four, same destination; specs flag writes
  `.aw/records/history.jsonl` in the fixture repo, specs positional writes NO sidecar; backlog writes none on either.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (anti-regression), evidence accuracy | `specs.run_set` (`repo_root = _repo_root_of(Path(selectors[0]))`) vs `status_set.run_set_command` (`resolve_verb_repo_root(getattr(args, "dir", None) ...)`); review probe case (c) above | The plan claims all four surfaces are identical and demands E-02..E-04 reproduce E-01 "byte-for-byte", but specs case (c) already diverges: the positional spelling silently skips the spec `wy9aru` 4.3 sidecar record. Fixing F-03 as written necessarily changes that cell, so the byte-for-byte bar was unsatisfiable and would push an executor to either fail the plan or preserve the defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06 (measured); E-01/E-02/E-04/V-02/V-03 now name it as the single permitted changed cell and pin it (E-04 case 3 asserts the sidecar record); Scope, Proposed changes, spec note and Spec/doc sync updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric C/D (repo-root derivation) | E-02 prescribed `_repo_root_of(Path(<first selector>))`; `specs._repo_root_of` resolves against cwd, accepts `.git`/`.agents` ancestors and falls back to the path's parent | For a positional id6/setid selector, `_repo_root_of(Path("sp0001"))` resolves against the cwd and differs from the engine's `resolve_verb_repo_root(None)` rule, so E-02 as written could retarget a positional call that works today (from a subdirectory or a non-`.aw` git repo). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now uses `_repo_root_of` only when the selector names an existing path, else `resolve_verb_repo_root(None)`; the `--status` branch stays byte-identical; backlog's derivation untouched; V-02 checks case (b). |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric G/E (scope, user-visible change) | Plan "No CHANGELOG entry: no user-visible behavior changes"; F-06 | Once F-06 converges, there IS one user-visible change; the plan declared none and `CHANGELOG.md` was not in `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 adds one CHANGELOG line; `CHANGELOG.md` added to `- Scope-Paths:`; V-05 demands its diff. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric D; E-03 dead-code claim | `cli.py` `p_backlog_set`/`p_specs_set` `"args", nargs="+"`; hand-built `Namespace(path=..., status=...)` callers in `tests/test_backlog_set_adapter.py`, `tests/test_spec_review_attestation.py` `_set_args`, `tests/test_blocks_release_reader_bounding.py` | E-03 said "confirm and drop it if dead" without distinguishing the `cli.main` normalization (dead: `args.args` is always non-empty) from the adapters' `elif path:` fallback (live for hand-built callers). An executor dropping the latter breaks those suites. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now deletes only the `cli.main` normalization and forbids removing the adapter fallback; E-04 case (4) pins the `Namespace(path=...)` shape; adapter-caller suites added to Required tests and V-04. |
| PR-005 | LOW | IN-SCOPE | Rubric E (evidence feasibility) | Lane notice "invoked in checkout ... but imported agent_workflows from <main checkout>" on every `aw` call | V-04's base-commit failure demonstration in a scratch worktree can silently import a different checkout's `agent_workflows`, proving nothing; and E-05 carried a placeholder date `2026-10-xx`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-04 require running the new test file with `python3 -m pytest` from the scratch root and pasting `agent_workflows.__file__`; E-05 date made an explicit execution-date slot. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract) | "Approval and execution gate" paragraph | Gate lacked the paste-actual-output rule, the staged-set check, scope-fence-as-declaration wording, and conditional finalize ownership (it implied a hand move to `executed/`); OQ-01 `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements and `aw ipd finalize` ownership; OQ-01 owner set to plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the specs positional out-of-repo sidecar divergence be converged or preserved? | Converge onto the flag spelling (write the sidecar). | Preserve the gap byte-for-byte (rejected: keeps a live fork and contradicts `wy9aru` 4.3, which rules the engine appends the sidecar for `specs`); defer to a new backlog item (rejected: the reroute itself changes the cell, so it cannot be deferred without a contorted adapter). | `wy9aru` 4.3 ("the shared engine appends one advisory record for `backlog` and `specs`"); `fcnz1r` Summary; review probe case (c). | yes |
| D-2 | Which repo-root rule for a positional non-path selector? | The engine's `resolve_verb_repo_root(None)`, so positional behavior is unchanged. | `_repo_root_of(Path(sel))` as the plan wrote (rejected: resolves an id6 against cwd); switch the flag spelling too (rejected: out of the no-behavior-change bar). | `status_set.run_set_command` repo_root branch; `specs._repo_root_of` body; `wy9aru` C4. | yes |
| D-3 | Keep OQ-01 (actor stays `aw set` on positional)? | Keep, as the author resolved it. | Unify to `aw specs`/`aw backlog` (rejected: `jbipfa` and `wy9aru` 4.6 rule it deliberate). | `tests/test_history_label_parity.py` docstring "Actor: '(aw backlog)' vs '(aw set)' ... is deliberate"; `wy9aru` 4.6. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
