# Review findings: plan ic4eg0

- Subject-Id: ic4eg0
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `3c7058184` in an isolated review-sweep lane. Child plan. Plan committed and byte-identical to
the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review;
`--phase review-finalize` clean after revisions; `check.ipd-uncarried-obligation` fired on the unrevised plan and is
clear after.

Verified:
- `artifact_core.atomic_write`: `tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")` then `os.replace`,
  no chmod (F-01 holds). `run_analytics_report` comment and `_current_umask` set-and-restore exist (F-03 holds).
- Scratch `private-target` install, umask 022: `aw research new`, `aw adopt`, `aw ipd scaffold`, `aw backlog new` all
  wrote 600; `.aw/system/managed-sections.json` 600; a plan chmodded 640 became 600 after `aw ipd set to-review`.
  This repo: `find .aw/records -type f -perm 600` returns six files written by this review sweep.
- Mechanism sketch (mkstemp + chmod to existing mode or `0o666 & ~umask`, umask read from `/proc/self/status`):
  022 -> 644, 002 -> 664, 077 -> 600, existing 640 -> 640, umask unchanged.
- `aw config set defaults.prune false` under umask 022 wrote `config.json` 600 (reachable PRIVATE control for E-04 g).
- `aw ipd begin` on a scaffolded plan refuses (unresolved `Item-Dependencies`), so it is not a usable test control.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | C Architecture / A | `agent_workflows/run_analytics_report.py:258` `_current_umask` "Racy only against a concurrent umask change"; threads in `runner_shared`, `runner_stop` | E-02 left the umask-read mechanism open ("where possible"). Moving set-and-restore into a writer used by every verb widens its race window. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the mechanism: `/proc/self/status` read with set-and-restore fallback, shared `current_umask`/`replacement_mode` helpers, `run_analytics_report` repointed; demonstrated (F-06). |
| PR-002 | MEDIUM | IN-SCOPE | G / Scope-Paths | `manifest.save`, `leak_sanitizer._atomic_write`, `oc_models._atomic_write` vs Scope-Paths | Scope-Paths listed private-state modules (`work_cmd`, `comms_*`, `runner_shared`, `project_layout`) as expected changes and omitted real tracked writers (`leak_sanitizer`, `oc_models`); `managed-sections.json` measured 600. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 carries a starting classification for every site; Scope-Paths now lists the expected TRACKED-RECORD modules only. |
| PR-003 | MEDIUM | IN-SCOPE | B Security / D | `leak_sanitizer._atomic_write` writes both `resolve_allowlist_path` and `USER_HINTS_FILENAME` | One helper writes a tracked file and a PRIVATE user-hints file; routing it wholesale would widen the hints file. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-03 requires a mode choice in the helper, hints stay 0600. |
| PR-004 | LOW | IN-SCOPE | G | E-03 "PRIVATE sites ... gain a one-line comment" | Adding comments to ~13 untouched modules is churn outside a behavior fix and outside Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Classification is recorded in V-03 evidence; PRIVATE sites get no code change. |
| PR-005 | MEDIUM | IN-SCOPE | E Testing | E-04 "under a forced `umask 022` in a subprocess"; `pyproject.toml` `-n auto` | Test approach unstated; changing the test process umask under xdist is unsafe, and `aw ipd new` in E-01 is not a verb. No PRIVATE control or POSIX guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 gives exact verbs; E-04 uses `sh -c 'umask 022 && exec ...'`, POSIX skip, adds `managed-sections.json` (f) and the `aw config set` PRIVATE control (g). |
| PR-006 | LOW | IN-SCOPE | D | OQ-01 preserve rule; F-05 | Preserving the existing mode means every file this bug already wrote stays 0600 forever; not stated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Consequence stated in OQ-01 and Deferred; remedy one-liner widened to `.aw/system`, excludes `.aw/state`. |
| PR-007 | HIGH | UNDER-SCOPE | Project rule | `check.ipd-uncarried-obligation` on deferred row `Carrier: none (...)`; AGENTS.md live-bug rule | Malformed carrier failed `aw check` at error; live bug lacked `Blocks-Release`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Carrier-Declined:` with reason; `- Blocks-Release: next`. |
| PR-008 | MEDIUM | UNDER-SCOPE | G contract | gate "move the plan to `executed/` with `aw ipd set executed ic4eg0`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the Set's standard contract with `aw ipd finalize`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to read the umask? | `/proc/self/status` first, set-and-restore fallback | set-and-restore only; `os.open(..., 0o666)` own temp name | multi-threaded runner modules; sketch F-06; keeps `mkstemp` naming/O_EXCL | yes |
| D-2 | Is `managed-sections.json` a tracked record? | Yes | PRIVATE | it lives in `.aw/system/` beside tracked installed files; measured 600 | yes |
| D-3 | Comment every PRIVATE site? | No; record in V-03 | Comment each | KISS; avoids out-of-scope churn in ~13 modules | yes |
| D-4 | Fix `project_layout`'s `int(tempfile.mkstemp()[0])` fd leak here? | No; reported | Fix it | unrelated defect class | yes |
