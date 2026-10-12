# Review findings: plan rq3q7v

- Subject-Id: rq3q7v
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `4dc9b2f82`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
Interfaces were taken from the reviewed text of `g55j1e` (Order 03) and `anzu8q` (Order 06, reviewed earlier in this
sweep); `tools/mutation_probe.py` does not exist at this HEAD yet.

Demonstration (temp dir under `/tmp/opencode`, removed): `python3 -m pytest -o addopts= -q -p no:randomly
--continue-on-collection-errors --junitxml <x> <real nodeid> tests/test_lost_guard_census.py::Nope::test_x`
gave `no tests ran in 0.09s`, exit 4, and a valid junit file with `tests="0"`. The same happened with the missing
nodeid alone.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness (false `unguarded`) | Review demo (F-03); `g55j1e` E-01 `error` only when baseline "could not produce junit XML"; `anzu8q` E-04 nodeids from an earlier HEAD | A narrowed selection with one stale nodeid runs zero tests and writes valid empty junit, so the probe reports `survived`, and with a killing control the property is filed as `unguarded`, a false gap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 step 1 runs a collect-only preflight (exit 0, count equals nodeids), drops missing ids and falls back to the full selection. V-02 demands the preflight line for the `unguarded` row. |
| PR-002 | MEDIUM | IN-SCOPE | A verdict mapping | `g55j1e` E-01 Verdicts "Consumers" bullet; Scope original | `timeout` and `error`, plus survivor `invalid` and control `killed-by-import`, had no mapping. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope maps every probe verdict to one of the four final verdicts. |
| PR-003 | MEDIUM | IN-SCOPE | A same-tree integrity | `g55j1e` E-01 Worktree (tests committed `HEAD`) | Nothing stopped a commit mid-batch, which would silently change the tree under later probes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 forbids commits until E-03; E-02 step 4 checks each JSON's `head` and `checkout_status_changed`. |
| PR-004 | MEDIUM | IN-SCOPE | C operability (index) | `.aw/.gitignore:50-51`; `8d0qsg` F-07 | E-03/V-03 committed the gitignored index and demanded `--check` conform. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Doc-only commit; `aw research find --id` plus no `--check` line naming the doc. |
| PR-005 | LOW | UNDER-SCOPE | G evidence | V-02 original | V-02 sampled two JSONs but did not reconcile all rows with their JSON or the mapping; totals ignored `budget exhausted`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 adds a whole-table `python3 -c` check; E-03/V-03 totals include `budget exhausted`. |
| PR-006 | LOW | IN-SCOPE | Gate / OQ owner | Gate original; OQ-01 `Owner: none` | Gate lacked the paste-actual-output rule, fence wording and prerequisite; OQ owner `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate itemized; owner `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to stop an empty selection reading as `survived`? | Collect-only preflight in this plan's E-02. | Change `g55j1e` to treat zero executed tests as `error`, which is the better long-term fix but belongs to that reviewed plan; noted here as a recommendation for its executor or a follow-up. | F-03 demo. | yes |
| D-2 | Survivor selection when every nodeid is gone? | Full default selection. | Mark `unprovable`, rejected because the full selection still answers the question at higher cost. | `anzu8q` E-03 fallback rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
