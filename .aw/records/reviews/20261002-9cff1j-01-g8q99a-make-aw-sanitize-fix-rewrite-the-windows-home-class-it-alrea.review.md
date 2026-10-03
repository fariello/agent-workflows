# Review: Make aw sanitize --fix rewrite the Windows home class it already detects

- Subject-Id: g8q99a
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

The target plan was committed and unchanged (sha256 matched the sealed lane input), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `2f22724d1`:

- `leak_sanitizer._rewrite_line` applies only `_HOME_ANY_RE` and `_USERS_ANY_RE`. It has one caller, in `fix_working_tree`. Nothing else in the package or tests reads either constant.
- `agent_schema.redact_home_paths` matches F-03. On `C:\Users\<user>\x` it gives `C:\Users\~\x`, and on `c:/Users/<user>/x` it gives `c:/Users/~/x`.
- F-02 reproduces. `fix_working_tree(assume_yes=True)` on a committed `see c:/Users/<user>/proj/a.md` returned `(['a.md'], [])` and wrote `see c:~/proj/a.md`.
- F-04 reproduces. A mixed file came back `real ~/x\ndocumented portable example ~/src/thing\n~/x\n`.
- Baseline: `tests/test_leak_sanitizer.py -o addopts=""` gives `14 passed`.
- Housekeeping: after the review line was added at the top of the plan, the plan's two original 2026-10-01 history lines (written oldest-first) made `check.lifecycle-transition-invalid` read `to-review -> draft`. Their order was swapped to newest-first, as the convention requires, and the rule is clear again. No text was changed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness / anti-regression (A, D) | `agent_workflows/agent_schema.py:163` `_REDACT_POSIX_HOME_RE = re.compile(r"/home/[A-Za-z0-9._-]+")` vs `agent_workflows/leak_sanitizer.py:91` `_HOME_ANY_RE ... (?=/\|\b)` | Delegating the WHOLE line to `redact_home_paths` deletes trailing punctuation. Measured: `_rewrite_line('see /home/<user>.')` gives `'see ~.'` today, while the delegated call gives `'see ~'`, and `'/home/<user>-'` gives `'~-'` versus `'~'`. `fix_working_tree` on `Files live in /home/<user>.` writes `Files live in ~.` today. So E-01 as written would introduce a new silent prose edit on the POSIX class, which is the same kind of defect the plan exists to fix. F-06 missed this because none of the six rows ends a username in punctuation. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now selects spans with the three `_FAIL_PATTERNS` home rules, trims a trailing `._-` run when the span is not followed by a separator, merges overlapping spans, and replaces each span with `agent_schema.redact_home_paths(span)`. A review prototype on 18 inputs preserved `'see ~.'`, gave `c:/Users/~/proj/a.md`, `C:\Users\~\x` and `(~).`, left every placeholder unchanged, and left zero detector matches. E-01's expected outcome, V-01 and E-04 now pin the punctuation case. |
| PR-002 | MEDIUM | IN-SCOPE | Test falsifiability (E) | `agent_workflows/leak_sanitizer.py:858` `if not file_findings: continue`; plan E-04 "a placeholder-only file for E-03" | A placeholder-only file has no findings, so `fix_working_tree` skips it and it is untouched TODAY. Measured: `([], [])` with the bytes unchanged. The row would pass on pre-change code, which contradicts E-04's own claim that it FAILS before the change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with a MIXED row: a real leak plus the documented placeholder line, requiring the placeholder line to be byte-identical. Proposed changes and V-04 were updated to match. |
| PR-003 | MEDIUM | UNDER-SCOPE | Detector parity (D) | `agent_workflows/leak_sanitizer.py:616` `if any(sub in line for sub in ruleset.allow_line_substrings): continue` | E-03 claims to make the rewriter's reach "match the detector's", but it covers only the regex lookaheads. The detector also skips lines that carry an allowlisted substring (built-in or from the repo's allowlist TOML). `_rewrite_line` would still rewrite those lines whenever another line in the same file has a real leak. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds an `allow` parameter, and `fix_working_tree` passes `ruleset.allow_line_substrings` at its one call. A direct test was added in E-04, and V-03 evidence covers it. The scope check and OQ-02 were updated for the one-argument loop edit. |
| PR-004 | LOW | IN-SCOPE | Validation feasibility (E, G) | plan V-04 "stash the `leak_sanitizer.py` changes", "count HIGHER than the HEAD baseline of 14" | `git stash` is unsafe in a shared checkout, because it stashes other parties' work. A collected-test count is an artifact of test organization, so it cannot serve as a V-item bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now copies the file aside, restores it from `git show <pre-edit-sha>:...`, and proves the restore with `git diff --stat`. The bar is that every new row and test passes. The value 14 is kept as context in Required tests. |
| PR-005 | LOW | IN-SCOPE | Plan accuracy | plan OQ-01 "`aw ipd set to-review g8q99a --work-kind bug`"; OQ-02 "Owner: none"; E-05/V-05 monkeypatch reachability | (a) OQ-01's command would demote a reviewed plan back to `to-review` and omits `--blocks-release next`, which a live `bug` must carry. (b) A resolved question needs a real owner. (c) V-05's monkeypatch of `agent_schema.redact_home_paths` reaches `_rewrite_line` only if the function is called by attribute, and it also changes the comparison reference unless that reference is captured first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now uses `aw ipd set reviewed g8q99a --work-kind bug --blocks-release next`. OQ-02's owner is now `plan author`. E-01 requires a module import with an attribute call. E-05 captures the reference and restricts agreement inputs to separator-followed real usernames. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `_rewrite_line` delegate without changing POSIX punctuation behavior? | Rewrite only the spans the detector rules select (trimmed and merged), using `redact_home_paths` on each span | Whole-line delegation (deletes punctuation, PR-001); adding lookaheads to `redact_home_paths` (forbidden by the plan's own scope fence, and it has other callers in `result_types.py`); keeping `_HOME_ANY_RE` and adding a third Windows regex (a second replacement definition) | 18-input review prototype, outputs recorded in PR-001; `agent_workflows/leak_sanitizer.py:67-71` `_FAIL_PATTERNS` | yes |
| D-2 | Should the rewriter also honor the line allowlist? | Yes, through an `allow` parameter fed from `ruleset.allow_line_substrings` | Leave it out (parity stays partial, and E-03's stated goal is not met) | `agent_workflows/leak_sanitizer.py:616` | yes |
| D-3 | Should the reviewer resolve OQ-01 (reclassify to `bug`)? | No. It stays open and non-blocking, owned by the maintainer | Resolve it to `bug` (this would overwrite the maintainer's 2026-09-30 ruling and re-gate the release) | AGENTS.md release-gate section; plan Scope check | yes |
