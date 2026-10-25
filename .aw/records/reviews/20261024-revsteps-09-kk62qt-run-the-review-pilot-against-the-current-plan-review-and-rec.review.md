# Review findings: plan kk62qt

- Subject-Id: kk62qt
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `79804a009` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot.
`aw ipd lint --phase author` clean (one INFO `IPD-Z602` size-density advisory) before and after;
`--phase review-finalize` clean after.

Verified: spec `k3yx72` Sections 13.1 to 13.5, 15 (Order 09 row), OQ-07, OQ-09, OQ-10, AC-17;
`3bwrfx` E-01/E-11/E-12 and its deferred row "Pilot baseline" (`- Carrier: kk62qt`); `uiyoax` E-05
(`--review-mode`, `--review-variant` default `single-12`); `run_analytics_attempts._matches`
(equality, no glob) and `ATTEMPT_FILTER_FIELDS` (has `label`, `review_variant`);
`aw oc run start --help` / `aw agy run start --help` (`--repo`, `--label`, `--review-variant`,
`--unattended`, `--model`, `--variant` on OpenCode, `--effort` on Antigravity);
`check_engine.evaluate_durable_carrier` / `evaluate_carrier_obligation`; `.aw/.gitignore`
`records/runs/`; `.gitignore` `tmp/`; `aw research new --kind findings --set revsteps` preview.

Probes run (scratch repository under `/tmp/opencode/`, removed afterwards): `aw oc run start --repo
<scratch> <executed-plan-copied-to-pending> --action review --prepare-only --unattended` refused with
`RUN-STRUCTURE-PREFLIGHT ... IPD-Q501: OQ Status must be open, resolved, or deferred` for `uyd3lw`
(2026-08-29) and for a 2026-10 copy; the attention view reported `attention.duplicate-id`.
`aw runs query attempts --filter label=nonexistentlabel ...` and with `--dir <scratch>` answered
`CANNOT-RUN no attempt facts are published yet; run aw runs analyze first`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | D invariant / experiment validity | `3bwrfx` deferred row "Pilot baseline" (`Carrier: kk62qt`); `3bwrfx` E-11 rewrites `plan-review.md`; `runner_shared.build_review_prompt` sends `/plan-review <path>` | Every cell is built from the pilot commit, where `plan-review.md` is already the new checklist, so `--review-mode single` would run the proposed review: the pilot would compare the new review with itself and the MD-20 gate would be meaningless. The obligation handed to this plan was not taken up. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-04 item (3) swaps in the baseline `plan-review.md` (commit recorded by `3bwrfx` E-12) for `single` cells and refuses without it; E-11 (c) and V-05 prove it. |
| PR-002 | high | UNDER-SCOPE | B / experiment validity | E-02 "The key is never placed in any review ... worktree"; E-04 `git worktree add` of the E-03 commit, which contains `tests/fixtures/review-pilot/defects.json` | The cell worktree contains the committed defect key, rubric and all fixtures, so a reviewing agent could read the answers. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-04 item (2) deletes `tests/fixtures/review-pilot/` from each cell; E-11 (b) and V-05 check it. |
| PR-003 | high | IN-SCOPE | E evidence feasibility | `run_analytics_attempts._matches` (equality); probe: `aw runs query` CANNOT-RUN before `aw runs analyze` | `--filter label=pilot-*` matches nothing, the budget read would return no cost, and cell runs live in each scratch repository's `.aw/records/runs/`, invisible from this repository; budget stop and V-03/V-07 were unsatisfiable. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | One exact label `pilot-k3yx72`; budget summed from `cells.jsonl`; per-cell `aw runs analyze --dir`; run dirs copied into this repo; V-03/V-07 rewritten. |
| PR-004 | high | IN-SCOPE | A correctness | probe: copied executed plans refused by `RUN-STRUCTURE-PREFLIGHT` `IPD-Q501`; `attention.duplicate-id` | Fixtures kept their source id6 (the source stays in `executed/` in every cell: duplicate id, ambiguous selector), and older executed plans fail preflight after the stated resets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 mints fresh id6s, prefers post-2026-10-01 sources, replaces non-linting sources; E-02 re-lints after planting; V-01 checks id uniqueness. |
| PR-005 | medium | UNDER-SCOPE | experiment validity (blinding) | spec `k3yx72` 13.4 "Judges are not told which method or model"; review outputs carry `/plan-review (<agent/model>)` and `- Reviewer:` | The after files name the reviewing model, so the judges were not blind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-03/E-06 redact agent/model/host/run ids; method-inferable-from-layout limit stated in rubric and report; E-11 (f), V-06 check. |
| PR-006 | medium | IN-SCOPE | G executability | E-06 "driven by `tools/review_pilot.py judge`" with no host mechanism | No launch mechanism, output contract, or failure rule for judge runs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 names `opencode run --format json` / `agy -p --output-format json`, a trailing JSON score object, one re-ask, judge cost in budget. |
| PR-007 | medium | UNDER-SCOPE | E testing | E-04 driver of 84 paid cells with no test | Isolation, baseline swap, resume and budget stop would first be exercised with real money. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New E-11 `tests/test_review_pilot.py` with fake launcher, run before E-05; V-11; Scope-Paths. |
| PR-008 | medium | IN-SCOPE | C operability | `docs/run-analytics.md` "Antigravity cost: tokens are reported; no dollar price"; E-04 `--budget` | A dollar budget cannot bound Gemini cells; unstated. Also `--unattended` absent, so a headless cell could prompt. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-04 item (7), E-05 and OQ-01 state the budget covers OpenCode and judge dollars only; launch argv carries `--unattended`. |
| PR-009 | medium | UNDER-SCOPE | durable record | E-08 report; `cells.jsonl`/`scores.jsonl` under gitignored `tmp/` | The data behind the MD-20 decision would not survive the checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-08 report appendix carries every row; V-08 checks row counts. |
| PR-010 | low | UNDER-SCOPE | durable carrier / execution contract / spec trace | `check.ipd-uncarried-obligation` [ERROR] on 3 deferred rows + OQ-01 + OQ-02; gate lacked finalize ownership; AC-17 unqualified; E-09 default location assumed `review_sequence.py` | Pre-existing check error; gate incomplete; trace token unqualified; `uiyoax` E-05 may put the default in `runner_shared.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `Carrier-Declined` with reasons on conditional rows and OQ-01; OQ-02 resolved (executor's documented choice); gate rewritten; `k3yx72` AC-17 qualified; E-09 names both files, Scope-Paths adds `runner_shared.py`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does a `single` cell run the "current" review after `3bwrfx` rewrites it? | Replace `plan-review.md` in the cell with the baseline commit's copy | Run cells from the baseline commit (lacks steps mode and analytics); skip the comparison | `3bwrfx` deferred "Pilot baseline" row; spec `k3yx72` 13.3 V2 and V4 (same commit) | yes |
| D-2 | Label scheme | One exact label `pilot-k3yx72`; cell key in `cells.jsonl` | Per-cell labels with glob filter (no glob support) | `run_analytics_attempts._matches` | yes |
| D-3 | Budget scope | OpenCode review dollars plus judge dollars; Antigravity tokens reported, not bounded | Convert tokens to dollars with a guessed price (no price table) | `docs/run-analytics.md` Antigravity cost | yes |
| D-4 | Resolve OQ-02 (fixture choice) now? | Resolved: executor chooses at E-01 by stated criteria and records reasons | Ask the maintainer (choice is method-neutral and auditable) | plan E-01 criteria; spec 13.3 V1 | yes |
| D-5 | Carrier for the conditional deferred rows | `Carrier-Declined` with reasons | Pre-file backlog items now (would assert a gate outcome that has not happened) | spec `k3yx72` MD-20, OQ-10 | yes |
| D-6 | Split the plan (IPD-Z602 INFO)? | No | Split driver build from attended run | 11 E-items in 4 groups, one deliverable each; the attended run needs the driver in the same session | yes |
