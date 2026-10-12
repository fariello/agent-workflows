# Review findings: plan hinpcf

- Subject-Id: hinpcf
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `e98d697ba`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot commit was needed. `aw ipd lint --phase author` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

The cited symbols resolve: `attention._age_marker` (UTC, `today` seam), `plans_archive._age_days` / `_resolve_plan_date`, `research_archive._age_days` (LOCAL `date.today()`, `today` seam), `workflow_artifacts_prune._calculate_run_age` (caller passes `datetime.date.today()`), and `artifact_core.utc_history_date`. Spec 4.4 sits at the "### 4.4 One timezone for every writer" heading, and the heading text is quoted by three test modules. Precedent `ulepef` exists, as does executed `840y6i` with its F-02/F-07. The zones `EAST_TZ`/`WEST_TZ` are in `tests/test_scaffold_history_clock.py`.

A scratch probe was run under both zones and then deleted. Its results are recorded as plan F-06.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (test discrimination) | `agent_workflows/attention.py:2490` `_age_marker` returns `'!'` only when `age_days > 30`. Probe: a fresh date gives `''` with either clock, while a boundary date gives `''`/`'!'` east and `'!'`/`''` west | Case (a), a fresh `utc_history_date()` read back as `''`, passes even if the reader is switched to a LOCAL today, so the UTC reader's clock is not actually pinned. The negative control was hand arithmetic, not a call into the reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (a) now adds a boundary date per zone, and case (d) routes every mixed pairing through the readers' own `today` seams. |
| PR-002 | MEDIUM | IN-SCOPE | E (feasibility) | Probe: `aw ipd scaffold` refused in turn without `--kind/--order`, then `--author`, then `--priority/--work-kind`, and has no `--slug` | The case (b) invocation as written exits 2. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now spells out the full, measured argv. |
| PR-003 | MEDIUM | IN-SCOPE | E / B (isolation) | Probe: `aw research new --apply` in a temp repo wrote `<HOME>/.aw/projects/repo-<hash>/records/research/...`; `tests/test_research_date_containment.py` isolates `HOME`/`XDG_CONFIG_HOME` | Case (c) would write into the real user home and then fail to find the doc inside the temp repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires HOME and XDG isolation and locating the doc from `wrote <path>`. V-02 demands evidence that the doc landed under the temp HOME. |
| PR-004 | LOW | IN-SCOPE | Honest documentation | `DECISIONS.md` D55 covers NAMES (filenames, RUN_IDs); the scaffold test docstring records `- Date:` as LOCAL beside the name | The draft amendment text said D55 "rules LOCAL" the `- Date:` and `created` front matter, which D55 does not state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded: the front-matter dates are LOCAL because the same writers stamp them beside D55-ruled names, which matches the probe's `created: <local date>`. |
| PR-005 | LOW | IN-SCOPE | G (execution contract) | Original gate; V-04 required "plus this plan" while Scope-Paths omitted it; OQ-01 claimed `Owner: maintainer` for an author recommendation; OQ-02 had `Owner: none` | The gate had no scope declaration or finalize ownership, Scope-Paths was inconsistent with V-04, and the owners were inaccurate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate, added the plan to Scope-Paths, and set both owners to `plan author` (OQ-01 records that the maintainer ratifies it by approval). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Keep recording the spec edit with `aw specs note` rather than a fresh `--by-human` approval? | Keep `aw specs note`. | Require `aw specs set approved --by-human` as `ulepef` did. | AGENTS.md "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD"; the executor will not hold a fresh human attestation for the spec, and plan approval is the ruling. | yes |
| D-2 | Is OQ-01 (whether to amend at all) a blocking human decision? | Non-blocking; plan approval is the ruling, and declining means retiring the plan. | Raise it as `Blocking: yes`. | The plan's own gate states approval is the ruling, the change is one appended paragraph (reversible), and no code changes (F-03, re-measured by F-06). | yes |
