# Review findings: plan fo08zx

- Subject-Id: fo08zx
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane after `3aa97a6ad`. The plan was committed (last touched by `7562cf9de`, the dated cross-reference added by the `xc8nae` review), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean (one pre-existing info `IPD-Z602`). `placement_switch.py` does not exist yet, so its `6u755v`/`xvlemm` contracts were checked from those plans' text.

Re-verified: `storage.attach_companion` -> `create_companion_identity`, `write_local_attachment_record`, `materialize_companion_storage` (mkdirs `.aw/config`, `.aw/state/durable`, `.aw/records`, writes or appends `.gitignore`); `storage.detach_companion` only unlinks the record; `materialize_companion_storage` `ignore_content`; `cli._run_install` companion create/init; `6u755v` rollback steps (1) delete `new_config_paths`, (2) restore `saved_config/` with `git reset`, fault-point set, frozen-plan resume; `ozr356` E-02 "before the companion attach (not reachable for a relocation, `companion-unsupported` blocks it)"; `ozr356` E-05 case (7); `y1e2m9` E-01 gates the attach block; `y1e2m9` depends on this plan. A fresh companion install's identity file (probe in the `xc8nae` review) held `"git_common_dir_hash": "<scratch>/comp/.git"`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A/D. Reachability and interim safety | `xc8nae` E-02 keeps `companion-unsupported`; `6u755v` refuses any blocker; `ozr356` E-02 attach-block comment; `y1e2m9` E-01 | As written every companion plan carries `companion-unsupported`, so `execute_placement_switch` refuses all of E-05's cases. Lifting it unconditionally here instead would open `aw install --relocate` to a companion switch followed by the un-gated fresh-install attach, and would break `ozr356` case (7), because the gating lives in `y1e2m9`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 adds a keyword-only `allow_companion=True` opt-in; E-05 case (0) proves the default still refuses; OQ-03; `y1e2m9` owns removal (dated cross-reference there; `xc8nae` and `aqun5z` texts reconciled). |
| PR-002 | HIGH | IN-SCOPE | B. Leak containment (D92) | `storage.attach_companion` `git_common_dir_hash=comp_git_common`; probe value an absolute `.git` path | E-02 staged `<companion>/.aw/companion_identity.json`, which carries an absolute machine-local path, into the private companion's index. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 no longer stages it (matches a fresh install, `xc8nae` F-04); F-06; E-05 and V-02 assert it is not staged. |
| PR-003 | MEDIUM | IN-SCOPE | A. Rollback completeness | `storage.materialize_companion_storage` mkdirs and `.gitignore` write | Directories and the `.gitignore` written by `attach_companion` were not journaled, so rolling back pair (d) left them and broke E-05 case (3)'s byte-identical companion claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 journals their prior existence; E-04 removes them (empty dirs deepest first); F-08; E-05 case (3) adds `after-attach`/`mid-companion-stage` and checks for leftovers; V-04 updated. |
| PR-004 | MEDIUM | IN-SCOPE | A. Rollback ordering | `6u755v` E-05 steps (1)/(2) | E-04 inserted its undo after step (1) but before (2), and E-02 never journaled the in-place config in `new_config_paths`/`saved_config/`, so an in-place rollback could delete `project.json` without restoring it, or `git reset` it before restoration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 journals both in-place files in `saved_config/` and `new_config_paths`; E-04 runs after step (2); E-05 case (3) asserts the (a) `project.json` bytes and index entry. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where is `companion-unsupported` lifted? | Library opt-in here (E-06); default-path removal in `y1e2m9` | Lift here unconditionally (unsafe CLI interim); tests monkeypatch the blocker away (tests a plan the planner never produces) | `ozr356` E-02/E-05 (7); `y1e2m9` E-01 and `- Item-Dependencies:` | yes |
| D-2 | Stage the companion identity file? | No | Stage it (D92 leak); fix `create_companion_identity` to drop the path (out of scope, `storage.py` not in Scope-Paths) | F-06; `xc8nae` F-04 | yes |
