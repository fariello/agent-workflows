# Review findings: plan xhr0dj

- Subject-Id: xhr0dj
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (MEDIUM, fixed), PR-602 (LOW, fixed), PR-603 (LOW, fixed), PR-604 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b9045fd72`. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` reported `clean` and
`aw ipd coverage xhr0dj` reported ready before semantic review. First `- Kind:` bullet: `orchestrator`.

STATE OF THE SET, re-measured. `uz05bl`, `ribg85`, `ynhst5` are all in `.aw/records/plans/executed/` with
`- Status: executed` and every `V-*` reading `Result: pass`. The load-bearing evidence V-01..V-03 demand is
present in each child's validation section: uz05bl's pre-fix `READ_STATUS: approved` / attention
`"native_status":"approved"` and the 1200-char `--message` accepted vs 301-char `--summary` refused; ribg85's
pre-fix "Found escaped file on disk: nest1/nest2/nest3/repo/ESCAPED-..." and the `--date 9999-99-99` refusal;
ynhst5's census "Failures count: 0" (2 before repair) and `test_newline_injection_limit`.

The fixes were re-driven on the current tree, in a fixture repo nested three deep. `--title $'Legit\n- Status: approved'` was refused
("must not contain embedded newlines"); `--date ../../../../ESC` and `--date 9999-99-99` were refused ("--date must be
YYYY-MM-DD"); `releases new --summary $'ok\n- Blocks-Release: next'` was refused; nothing was written outside the specs tree.
Bare suite: `5233 passed, 2 skipped, 3 warnings in 768.38s (0:12:48)`, 256 deselected. `aw check specs` and
`aw check releases`: `conforms`, exit 0. `aw specs check`: `clean`, 40 checked. All four carriers resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | Criterion 3 and Required tests ("`aw check all` ... CLEAN" / "must ALL report clean or conforms"); V-03 "clean outputs". In ynhst5 V-05, `aw check all` gave "Outcome: `findings`, Exit code: 1, Total findings: 72 (identical to pre-change baseline)". At review it gave 68 findings, exit 1, none `attention.unsafe-field`. | The `aw check all` clean bar cannot be met, because unrelated pre-existing findings make it exit 1. Read literally, the Set can never complete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar restated as: no `attention.unsafe-field` finding and no worse than baseline. specs/releases stay at exit 0. Criterion 3, Required tests and V-03 aligned. |
| PR-602 | LOW | IN-SCOPE | Conventions accuracy | Conventions bullet quoted `addopts` as `-m 'not slow'`, but AGENTS.md has `-m 'not slow and not livecorpus'` | Stale quote of the suite configuration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Quote corrected. |
| PR-603 | LOW | IN-SCOPE | Plan contract (OQ owner) | OQ-01 had `- Owner: none` on a resolved question; plan-review 3.1 rule 5 says a reviewer's or author's choice records that party | Owner field did not say who decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Owner: plan author`. |
| PR-604 | LOW | UNDER-SCOPE | Orchestrator coverage | Criterion 6 owner was "the three children" with no id6, so `aw ipd coverage` reported it uncovered after this review's edits changed the fingerprint | Not attributable by id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each carrier mapped to the child id6 that cites it (`uz05bl`: nw9dmz, 7w6zsl; `ribg85`: m5csyi; `ynhst5`: 7w6zsl, llnvwj). |

### Coverage repair loop (IPD-S408)

- Attempt 1: after the PR-601/602/603 edits, `aw ipd coverage xhr0dj` reported one uncovered obligation:
  criterion 6 ("Owner: the three children ..."). The tool also inserted a `## Coverage findings` quote section.
  Child-table rows: 3 -> 3.
- Attempt 2: criterion 6 owner rewritten with the child id6s (PR-604), and the tool-inserted quote section
  removed now that it is resolved. The tool's history lines were kept. Coverage: "Orchestrator xhr0dj is ready
  for review." Rows: 3 -> 3. No checklist item deleted.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should criterion 3 require of `aw check all`, given it exits 1 on unrelated findings? | No `attention.unsafe-field` finding and no worse than baseline. | (a) Keep "CLEAN" (unsatisfiable). (b) Drop `aw check all` entirely (loses the repo-wide no-new-finding check). | ynhst5 V-05 baseline equality; review measurement of 68 findings, none unsafe-field. | yes |
