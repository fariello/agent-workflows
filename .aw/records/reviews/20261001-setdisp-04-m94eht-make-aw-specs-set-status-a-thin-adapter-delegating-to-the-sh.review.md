# Review findings: plan m94eht

- Subject-Id: m94eht
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `427b569c7`. The plan was committed and byte-identical to the
sealed lane input (manifest `source_sha256` matched by `diff`), so no pre-review snapshot.
`aw ipd lint --phase author --agent`: `clean`; `--phase review-finalize --agent` after revision: `clean`
(`conforming`). Not an orchestrator, so `IPD-S407`/`IPD-S408` do not apply.

Measurements (scratch repos under the system temp dir, lane package pinned with `PYTHONPATH` and
`AW_NO_REEXEC=1`):

- `specs set <path> --status to-review --message m --no-commit` -> rc 0, history `(aw specs): m`;
  `specs set to-review abc123 ... --yes` -> rc 0, history `(aw set): m`.
- `specs set <path> --status to-review ... --agent` (no `--yes`) -> rc 0, written;
  `specs set to-review abc123 ... --agent` -> rc 2 `confirmation required`.
- `--message 'a\nb'`: `--status` spelling rc 1 `aw specs set: --message must not contain embedded
  newlines`; positional rc 2 `FAIL aw set: --message ...`.
- Bare `s.md` in a non-repo temp dir (the `tests/test_specs_verbs.py` `SetTests._mk` shape): `--status`
  spelling rc 0; positional rc 2 `No specs artifact matched`.
- `status_set.run_set_command([...], scoped_type="specs", repo_root=<tmp repo>, args=Namespace(actor="aw specs", ...))`
  -> rc 0, `- 2026-10-07 to-review (aw specs): m`; with `repo_root` defaulted to cwd ->
  `ValueError ... is not in the subpath of` from `apply_status_change`.
- `attention_contract.actor_refusal("aw specs")` -> `None`.
- `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q -k blast_radius` ->
  `1 passed, 15 deselected in 5.28s` with this plan's `state:spec:` edge present.
- Code: `specs.run_set` `date = getattr(args, "date", None) or core.utc_history_date()`;
  `status_set.apply_status_change` `today = _core.utc_history_date()`; commit `3c55295a3` (`5ivkdh`)
  moved every writer to UTC; `specs._today()` is used only by `run_new`.
- Records: `wy9aru` `to-review`, OQ-1 `Blocking: yes`; `ulepef` `approved`, pending; `m1jlwm` `reviewed`,
  pending; `68sur3` `done`; `pyhq6s`, `fnb8pl`, `lq2w86` `graduated`; `2wae2x` `open`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D (unexplained behavior change) / G | E-04 outcome "every existing hand-built-Namespace caller still works unchanged"; scratch probes above; `apply_status_change` `rec.path.relative_to(repo_root)`; `tests/test_specs_verbs.py` `SetTests._mk` | Delegation as written cannot keep the bare-file fixture shape working (rc 2 or a `ValueError`), and the plan did not name this. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added spike E-07 (a) to measure each direct-caller shape and choose a single-engine fix (resolver accepts an explicit file path, adapter passes `repo_root` from the path, or the fixture moves into a records tree); a fallback to the old code is forbidden. V-07 added. |
| PR-002 | HIGH | UNDER-SCOPE | D / E | `specs.run_set` actor `(aw specs)`; engine `actor = getattr(args, "actor", None) or "aw set"`; 36 `(aw specs` assertions in nine test modules; `--message` rc 1 vs rc 2 and prefix `aw specs set:` vs `aw set:`; pinned in `tests/test_specs_releases_descriptive_safety.py`, `tests/test_set_dispatch_dedup.py`, `tests/test_releases_line_writers.py` | The plan said it would "measure what the actor becomes" but did not see that delegation silently rewrites the actor and changes refusal exit codes and prefixes that tests pin. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-07 (b) builds a refusal table with each row `preserved` or `changed`; E-07 (c) preserves `(aw specs)` through the engine's existing `actor` parameter (measured to work). E-04 and E-06 consume these decisions; the Deferred actor note is corrected; the conditional test paths are named in Scope check. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence (stale claim) | `specs.run_set` `core.utc_history_date()`; commit `3c55295a3` | E-02, E-06, F-05, V-02, V-06 and a Deferred entry claimed delegation moves the specs path from local clock to UTC. That was fixed by `5ivkdh` before review, so an executor would record an unreproducible clock consequence. | Overall:Low | FIXED | Every clock claim is rewritten: E-02 is the `--date` pass-through only, F-05 corrected to LOW, V-02 asserts UTC agreement under a skewed `TZ` and unchanged clock carriers, E-06/V-06 make no clock claim. |
| PR-004 | MEDIUM | IN-SCOPE | G (sequencing enforcement) | Gate prose "Plan `ulepef` must also have landed"; F-02; `- Item-Dependencies:` lacked it; `ulepef` `approved` with `- Item-Dependencies: none` | The `ulepef`-first ordering E-03 relies on was prose only, so the runner could dispatch this plan first. | Overall:Low | FIXED | Added `executed:ulepef` to `- Item-Dependencies:`; F-02 updated. |
| PR-005 | LOW | IN-SCOPE | G (open question answerable from repo) | OQ-02 `Status: open`; tree search: `runner_shared` names only the positional spelling, `engine.py` advertises `--status ... --by-human` without `--agent`, only `tests/test_completion.py` pairs the flags | OQ-02 was answerable now. | Overall:Low | FIXED | OQ-02 resolved with the search cited; E-04 re-runs it at execution; CHANGELOG still names the `--yes` requirement for out-of-tree callers. |
| PR-006 | LOW | IN-SCOPE | G (execution contract) / evidence drift | Gate lacked scope-fence wording and conditional finalize ownership; F-09 HIGH no longer reproduces; `68sur3` described as dead branch but `done`; five direct-caller modules listed, six exist (`tests/test_specs_date_containment.py`) | Contract gaps and stale evidence. | Overall:Low | FIXED | Added a declaration-style scope fence with `--scope-reason`/`--scope-ack`, runner-or-executor finalize ownership, and a no-hand-`git mv` rule; F-09 downgraded with the re-measurement; `68sur3` and the six-module list corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the adapter preserve the `(aw specs)` actor or adopt the engine's `(aw set)`? | Preserve via `args.actor="aw specs"` when none given. | Adopt `(aw set)`. REJECTED: it rewrites 36 pinned assertions and would be an actor decision `jbipfa` declined to make. | `wy9aru` 4.6; `jbipfa` Deferred; scratch probe writing `(aw specs)`; `actor_refusal("aw specs")` is `None`. | yes |
| D-2 | Resolve the fixture-shape break now, or spike it? | Spike in E-07 with a constrained choice; forbid an old-code fallback. | Pick the resolver change now. REJECTED: the cheaper fix depends on how many shapes fail, which is measured at execution. | Scratch probes; HOW-question rule (demonstrate or spike). | yes |
| D-3 | Enforce `ulepef`-first by dependency edge or leave as prose? | Dependency edge `executed:ulepef`. | Prose. REJECTED: prose is not read by the runner. | F-02; `wy9aru` Section 6 item 2 "MUST land first". | yes |
| D-4 | OQ-02: does any in-tree caller use `--status` with `--agent`/`--json`? | No; resolved, re-checked at execution. | Leave open for the executor. REJECTED: the repository answers it. | Tree search cited in OQ-02. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. The plan's existing gate on
`wy9aru` OQ-1 (BLOCKING, maintainer) is unchanged and is enforced by `state:spec:approved:wy9aru`.
