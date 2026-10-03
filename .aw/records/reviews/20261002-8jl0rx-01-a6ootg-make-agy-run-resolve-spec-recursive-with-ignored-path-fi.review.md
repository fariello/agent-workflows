# Review: Make agy_run.resolve_spec recursive with ignored-path filtering

- Subject-Id: a6ootg
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `a68215fa6`: `agy_run.resolve_spec` still uses `d.glob("*.md")` over the two roots; `specs._spec_files` is recursive with the ignore filter and skip names; `resolve_mode_and_target` has the two call sites and the `except ScriptError: pass` -> `return "prompt", target_str, ""` fallback; `testpaths = ["tests"]`; CI and `make test` run `pytest tests/`; `tools/test_agy_run.py -o addopts=""` gives `44 passed`; `pqsx96` lives in `draft/`. In process at base: `resolve_mode_and_target(root, parse_args(["--spec","pqsx96"]))` raises `No specification matching 'pqsx96' found.` and `["pqsx96"]` returns `('prompt', 'pqsx96', '')`. With a stub `--agy`, `aw agy exec --no-audit --spec pqsx96` exits 2 and positional `pqsx96` prints `Executing [prompt mode] pqsx96 in Antigravity...`. Carriers `mlcbk9` and `n8adhb` exist. Backlog `8jl0rx` is `graduated`.

Prototype of the revised E-03 shape (delegate, resolve, fence to `root.resolve()`, render ambiguity relative to the resolved root) over a temp git fixture with an isolated `AW_HOME` and over the live tree: `abc123` and its bare filename resolve to `.aw/records/specs/approved/...`; `README`, the `untracked/` spec, a `.git/info/exclude`-only spec and an out-of-repo backend spec all raise `No specification matching ... found.`; `abc12` and `attention` raise `is ambiguous` listing two repo-relative candidates; live `pqsx96` and the flat-looking path resolve to `.aw/records/specs/draft/20260828-pqsx96-...spec.md`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Correctness (A) / Architecture (C) | `agent_workflows/specs.py` `_spec_files` `resolve_record_read_paths("specs", target_repo=...)`; `agent_workflows/agy_run.py` `relative_posix` | `_spec_files` follows the records backend and can return specs outside `root`. Measured with an isolated `AW_HOME`: an out-of-repo spec is returned and `relative_posix` then raises `ValueError`, which is not a `ScriptError`, so it escapes the positional caller as a traceback. A relative root breaks the ambiguity renderer the same way. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 resolves and fences the delegated set to `root.resolve()` and renders ambiguity relative to it; E-02 adds assertion (6); F-10 added; V-03 demands the fence lines quoted; OQ-01 addendum. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (E) | `agent_workflows/artifact_core.py` `is_ignored_path` `"untracked" in rel_parts` | The `untracked/` fixture is rejected by a hardcoded path check, so it cannot prove a real git ignore rule is consulted, which V-02 itself demands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (4) split into 4a (`untracked/`) and 4b (`.git/info/exclude`-only dir, measured excluded); V-02 demands `git check-ignore -v`; F-11 added. |
| PR-003 | MEDIUM | IN-SCOPE | Testing (E) | plan E-02 expected outcome; V-02 expected split | The stated red split was wrong: the gitignored exclusion PASSES at base (the flat glob cannot reach that dir), so an executor would hit an unexplained split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expected outcome and V-02 restated: (1)/(2)/(5) fail at base, exclusions pass vacuously at base and become discriminating after E-03. |
| PR-004 | HIGH | UNDER-SCOPE | Security / Operability (B, C) | `agent_workflows/agy_run.py` `run` calls `run_agy` right after `resolve_mode_and_target`; `agy` is on PATH | Every CLI probe that resolves (all after-fix probes, and the positional before-fix probe) would launch a real Antigravity turn from inside validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 stub rule (`--agy <stub> --no-audit`, read the `Executing [<mode> mode]` line, delete the `tmp/antigravity` log); E-04, V-01, V-03, V-04 and the gate updated; in-process `resolve_mode_and_target` probe added. |
| PR-005 | MEDIUM | IN-SCOPE | Plan executability (G) | plan gate "POST-GATE LIFECYCLE" | Gate lacked the declared scope fence, the conditional finalize owner (runner vs hand), the never-`git mv` rule, and the backlog-status guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | SCOPE FENCE, NEVER LAUNCH A REAL AGENT and conditional `aw ipd finalize` ownership added. |
| PR-006 | LOW | IN-SCOPE | Live-artifact criteria (G) | plan E-04, V-04 "beside the authoring baseline of 44 passed" | A collected test count was used as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now zero failures at the E-01 count; 44 kept as context. Also `Owner: none` on resolved OQs corrected to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should out-of-repo backend specs be resolvable by `--spec`? | No: fence to `root`, preserving today's scope | Accept them and change downstream rendering/prompts to absolute paths (widens a release-gating bugfix into a contract change) | Old loop only searched inside `root`; `relative_posix` and Turn-1 prompt assume repo-relative; prototype run at review | yes |
| D-2 | Keep delegation to `_spec_files` given PR-001? | Keep, with a post-filter | Re-implement the walk locally (second definition of the spec set) | OQ-01 rationale; `spec_citations` and `check_engine` call `_spec_files` cross-module | yes |
| D-3 | How should CLI probes avoid launching a real agent? | `--agy <stub> --no-audit` plus in-process `resolve_mode_and_target` | Probe in process only (loses the end-to-end form the item reports) | `agy_run.resolve_agy` accepts an explicit executable; stub run measured at review | yes |
