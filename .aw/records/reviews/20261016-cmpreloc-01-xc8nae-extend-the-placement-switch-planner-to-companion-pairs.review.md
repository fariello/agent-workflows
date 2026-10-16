# Review findings: plan xc8nae

- Subject-Id: xc8nae
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `38d107d18`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` clean after revisions. `agent_workflows/placement_switch.py` does not exist yet (its creator `xvlemm` is `approved`, not executed), so claims about it were checked against `xvlemm`'s E-01/E-02 text.

Re-verified:
- F-01..F-05 reproduced by a scratch probe under `.aw/state/` (deleted): fresh `install --preset public-target-private-companion --companion-dir <s>/comp -y --no-interactive` exit 0; `physical_classes` `config_project: <r>/.aw/config/project.json`, `state_durable: <r>/.aw/state/durable`, `records: <comp>/records`; target `?? .aw/config/`; companion `?? .aw/`, `?? .gitignore`, `?? records/`, no commits; `.aw/state/durable/companion_attachment.json` present.
- `storage.validate_companion_preflight`, `storage.detach_companion` "without deleting companion data", `storage.materialize_companion_storage` `ignore_content`, `cli._run_install` "if getattr(policy, \"create_companion\", False) or not comp_p.exists():" all resolve as cited.
- `xvlemm` E-02 defines `dirty-aw-tree` as `git status --porcelain -- .aw` non-empty; `6u755v` E-03 refuses any plan with a blocker; `ozr356` E-05 case (7) asserts `companion-unsupported`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A/D. Interim safety | `6u755v` E-03 "when the plan has any blocker"; `ozr356` E-05 case (7) "refuses naming `companion-unsupported`" | Removing `companion-unsupported` makes a companion plan blocker-free, so once `6u755v`/`ozr356` exist (they do not depend on this plan) `aw install --relocate` would execute a companion switch with no attach, detach or companion staging, and `ozr356` case (7) would fail in the bare suite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Blocker KEPT beside the full census (Scope, E-02, F-10, OQ-03); Order 02 owns lifting it (Deferred row; dated cross-reference in `fo08zx` history). |
| PR-002 | HIGH | IN-SCOPE | A. Correctness | Probe: `GIT_OPTIONAL_LOCKS=0 git -C r status --porcelain -- .aw` -> `?? .aw/config/` on a fresh companion install | The inherited `dirty-aw-tree` rule fires on every companion source, so pairs (b) and (c) would always be blocked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 excludes exactly the untracked `.aw/config/project.json` for a companion old side (F-07); E-03 tests absence on a fresh install and presence with a stray file. |
| PR-003 | MEDIUM | IN-SCOPE | A. Reachability | `ppu39q` E-02 (a)/(b): label branch compares labels, path branch compares dirs | Two companion policies have equal labels and equal in-tree config dirs, so `config_placement_switch` returns `None` and `not-a-placement-switch` would short-circuit before `companion-to-companion` could fire. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 orders the `companion-to-companion` check before the short-circuit; same-dir case stays `not-a-placement-switch`; E-03 asserts both. |
| PR-004 | MEDIUM | IN-SCOPE | B. Wrong repository | Probe: `git -C parent/comp rev-parse --git-dir` -> `<s>/parent/.git`, exit 0 | `rev-parse --git-dir` succeeds for a plain dir nested in another repo, so records would be staged into the wrong repository. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `companion-not-git` uses `--show-toplevel` equality (F-08); E-03 nested case and mutation M2. |
| PR-005 | MEDIUM | IN-SCOPE | B. Nesting guard | Probe: `validate_companion_preflight(<r>, <r>/nested-comp)` raised `StorageSecurityError` with the dir absent; snapshot unchanged | Calling preflight only when the companion exists skips the nesting check for the `companion_create` path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Preflight runs whether or not the dir exists, with `aw_home` passed (F-09); E-03 nonexistent-nested case. |
| PR-006 | MEDIUM | UNDER-SCOPE | A. Plan completeness | E-01 (c)/(d); F-02 | `config_retrack` and the staging repository of the in-tree `project.json` were unstated for (c)/(d); for (d) a staged `project.json` would diverge from what a fresh companion install leaves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01: `config_retrack=None` for (c)/(d); (d) `config_project` `dest_git=None`; E-03 asserts it. |
| PR-007 | LOW | IN-SCOPE | E. Evidence | V-02, V-03, Required tests | Validation did not demand the new cases (kept blocker on every pair, nested cases, fresh-install dirty exclusion, M2). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02/V-03 and Required tests updated; clean-fixture blocker list is exactly `["companion-unsupported"]`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Remove `companion-unsupported` here or keep it until Order 02? | Keep as an ordinary blocker; Order 02 lifts it | Remove here (unsafe interim, breaks `ozr356` case 7); add `Item-Dependencies` from `6u755v`/`ozr356` on this plan (edits other Sets' approved plans) | `6u755v` E-03; `ozr356` E-05 (7); F-10 | yes |
| D-2 | How to keep `dirty-aw-tree` from blocking every companion source? | Exclude exactly the untracked in-tree `project.json` for a companion old side | Drop the target dirty check for companion sources (loses real protection); track `project.json` (contradicts F-02) | Probe output F-07; F-02 | yes |
| D-3 | Should the new in-tree `project.json` in pair (d) be staged? | No (`dest_git=None`), matching a fresh companion install | Stage it (diverges from fresh-install state, contradicts pair (a) untrack) | F-02; E-01 (a) `config_retrack="untrack"` | yes |
| D-4 | Run preflight on a nonexistent companion dir? | Yes | Only when it exists (misses nesting) | Probe F-09: refuses nested, writes nothing | yes |
