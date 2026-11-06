# Review findings: plan ffceq0

- Subject-Id: ffceq0
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `d962920be` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 10) is byte-identical to the tracked plan. The tracked plan was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them. `agent_workflows/artifact_meta.py` and `agent_workflows/meta_cli.py` do not exist yet; they are created by `tve77h` and `1ajqaa`, which run first, so interface names were checked against those plans' text.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Pin-first rule, E-01, E-04 to E-07, E-09, V-01 to V-09, V-14 | Baselines in `/tmp` and compared by summary-line pass counts | Outcome lists and checkout baselines under the gitignored `.aw/state/ffceq0/`, one deterministic command, full sorted outcome lists diffed | PR-001. |
| E-03, E-05, V-03, V-05 | Bars "1,635 paths", "3,096 items and 1 violation" | Equality with baselines saved in E-01; authoring counts kept as context | PR-002. |
| D-1, E-03, V-03 | Normalized status matching for every type | Plans only; other types keep exact matching; `aw find backlog open` and `aw find specs implemented` counts are checked unchanged | PR-003. |
| D-2, E-02, V-02 | "the legacy loader grammar accepts `^-[ \t]*`" | The loader is strict (`tve77h` E-11); `read_text` returns strict and loose values; public readers use loose and the cache uses strict | PR-004. |
| D-1 test-edit list | One test edit named | Also names `test_single_token_status_contract_survives`'s `_read_status(multi)` assertion and keeps its other assertions | PR-005. |
| E-07 | `_read_setid` | `_parse_setid` (the real symbol in `check_engine`) | PR-006. |
| E-08, V-08, D-5 | Three `_SKIP_NAMES` copies and `iter_scan_files` consulting the skip list | All copies named (`specs`, `releases`, `ipd_lint` too); `iter_scan_files` excludes only `meta/` because its callers scan `README.md` (0u0ako); D-5 added | PR-007. |
| OQ-03, E-02, Scope-Paths, spec sync | "No spec change" while adding an interface function | Spec `4sd62s` 4.3 gains `read_text`; declared in Scope-Paths and spec sync with its reason | PR-008. |
| E-10, V-10 | `aw check meta` CLI placement unstated | `meta` is a reserved word of `aw check`'s type positional, excluded from `aw check all` in phase B | PR-009. |
| E-11, V-11 | Synthetic log fixture construction unstated | Written from `encode_event` lines in its own git repository, not through phase-B `append` | PR-010. |
| E-12, V-12 | No legacy `.agents/` root case; "under 5 s" for a CLI-spawning matrix | `.agents/` root fixture added; wall time pasted against the core budget | PR-011. |
| Gate, E-14 | Partial execution contract | Honesty rule, `git add -A` ban, declaration wording of the fence, conditional finalize ownership, dash rule for user-facing prose | PR-012. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan adds `aw check meta` and `aw meta repair`, changes what `aw find plans <status>` matches (D-1), adds `artifact_meta.read_text`, and (after this review) amends spec `4sd62s` 4.3.
2. No. It touches no guard module.
3. Yes. It has 14 E-items in 5 task groups across about 12 modules.
4. Yes. It declares Scope-Paths.
5. Yes. Every search, attention, check and lint read moves; a silent change would mislead every later gate.

AW-TIER: complex

### Step R1

- Checked: every module and symbol named in Scope and E-01 to E-11 by import and `hasattr` at HEAD. All resolve except `check_engine._read_setid`; the real symbol is `check_engine._parse_setid` (PR-006). Every existing test module named exists; `test_readers_selectors_find` and `test_check_meta` are absent, as expected.
- `selectors` "PARITY CONSTRAINT" comment above `_STATUS_RE` exists and says what Step 0 says.
- `plans.normalize_status` maps `open`, `implemented`, `active`, `planned`, `graduated` to `legacy/unknown` (measured), so D-1 as written would break non-plan status matching (PR-003).
- `tve77h` E-11 says "one strict `- Field: value` grammar"; D-2 claimed the loader accepts `^-[ \t]*` (PR-004).
- `ipd_lint.lint_text` currently has `checkpoint`, `directory`, `legacy`, `doc`, `citation_anchors`, `path`; adding `state` is additive. 58 `lint_text(` test call sites confirmed.
- `_SKIP_NAMES` is defined in exactly the three modules named; the same three names are also inlined in `specs`, `releases` and `ipd_lint` (PR-007). `artifact_core.iter_scan_files` has no skip list today; its callers scan `README.md` (`artifact_refs` comment, 0u0ako).
- Live re-measure: `aw find plans executed` 1,611 and `--status executed` 1,636 (plan: 1,610 and 1,635); `aw attention --all` 3,102 items, 1 violation (plan: 3,096). The counts drift, which PR-002 addresses. `aw find plans zzzzzz` exits 2. `vfa1tl` is the only upper-case `EXECUTED` match, as F-03 says. `pyproject.toml` `dependencies = ["filelock>=3"]`. `0cbfcc706` resolves.
- `aw check --help` lists no `meta` type; `aw check meta` exits 2 today, matching F-10.
- The spec's 4.4 "Gate `IPD-S405`" bullet, the 4.4 last bullet (one exclusion list) and the 4.6 table all exist as cited.

### Step R2

- Checked: the E/V bijection is 14/14; each V demands pasted runs, diffs or transcripts.
- Bars counting live artifacts (1,635 plans, 3,096 items) were fixed numbers; now equality with saved baselines (PR-002).
- Baselines under `/tmp` would be lost on lane integration, and summary-line count equality misses a test that swaps from pass to fail (PR-001).
- Reachability: V-10's `aw check meta` and V-11's `aw meta repair` are produced by E-10 and E-11; V-11's synthetic log needed a stated construction, because phase-B `append` writes the legacy format (PR-010). V-05's violation for an `incomplete` record is produced by E-05.
- `- Item-Dependencies: executed:tve77h, executed:xexn45` is correct: `tve77h` supplies the interface and `xexn45` the `short_description` writer. `1ajqaa` (which creates `meta_cli.py`) is not listed; it depends only on `tve77h`, and the Set's queue does not guarantee it runs before this plan. Covered by the E-10 wording "in `meta_cli.py`": if the module does not exist, the executor creates it (within Scope-Paths). Recorded as D-4, no finding.

### Step R3

- Checked: the plan reads metadata and adds two commands. `aw meta repair` previews by default, needs `--apply` to write and `--confirm` for a divergent tail; that matches spec 4.7. The offline test (E-13) proves no network or model use. No secrets, no trust-boundary change.

### Step R4

- A: reads only, except `aw meta repair`, which inherits `tve77h`'s locked write path.
- C: one interface; `read_text` is the one addition and now amends the spec (PR-008). One skip list (PR-007).
- D: pin-first rule with outcome-list diffs (PR-001); behavior changes named in D-1 to D-5. D-1 limited to plans (PR-003); D-2 corrected (PR-004); the missed test edit named (PR-005). The legacy `.agents/` root, which `selectors`, `attention` and `check_engine` read today (measured: a repository with only `.agents/plans/pending/<plan>` is listed by `aw find` and `aw attention`), now has a case in E-12 (PR-011).
- E: each new behavior has a named module. The parity matrix spawns the CLI many times; the fixed "under 5 s" bar was replaced by a pasted wall time against the 30 s core budget (PR-011).
- F: `aw check meta` names the not-applicable rows instead of skipping them.
- Spec sync: "No spec change" was false once `read_text` was added to the spec's C5 interface list (PR-008).

### Step R5

- Checked through the eight personas:
  - QA and regression: deterministic outcome diffs; baselines that survive integration.
  - UI/UX and power user: `aw find plans executed` now agrees with `--status executed`; `aw find backlog open` unchanged.
  - Architect: one reader, one skip list, one spec-listed text entry point.
  - Engineer: real symbol names; the CLI placement of `aw check meta` is stated.
  - Novice: `aw check meta` names legacy not-applicable rows.
  - Stakeholder: AC ownership table is unchanged and consistent with `t4gl15`.

### Step R6

- Checked: 14 E-items in 5 groups. E-07 (`check_engine`) is the densest; OQ-02 records a split at the type boundary if execution finds it too large. Each E-item has one pin set and one V. No split recommended (D-3).

### Step R7

- Checked `tve77h` (interface names, OQ-03 status column, strict E-11 grammar, E-13 `incomplete`), `1ajqaa` (creates `meta_cli.py`; routes `rebuild` before type validation, the model for `aw check meta`), `2xwb9b` OQ-04 and `59aiyh` (do not need `read_text`), `t4gl15` (depends on this plan; uses `read_text`; follows D-1 for `plans_index`), `9o83cr` (deletes `selectors` readers, merges F-12), `cxxmyv` E-05 (takes the logged-path row and `last_history_precision`), and the orchestrator `63ib9r` row 08. Consistent after PR-003, PR-004 and PR-008.

### Step S5

- Checked: OQ-01 to OQ-03 are resolved and non-blocking. OQ-03 is extended from evidence (spec 4.3 function list) with the reviewer as decider (D-1 below). No question needs the human: the spec amendment adds a function, changes no rule, and is reversible before the cutover.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R2 / R4 D | V-05 "`/tmp/att_before.json`"; V-06 "`/tmp/check_before.txt`"; V-02 "same pass counts" | Baselines outside the lane workspace are lost on integration; count equality hides a test that flips from pass to fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gitignored `.aw/state/ffceq0/`; one deterministic outcome-list command; diffs. |
| PR-002 | MEDIUM | IN-SCOPE | R2 G live counts | E-03 "the same 1,635 paths"; E-05 "3,096 items"; measured 1,636 and 3,102 at review | Live-artifact counts were the bar and had already drifted. | Low | FIXED | Bars are equality with E-01 baselines; counts kept as context. |
| PR-003 | HIGH | IN-SCOPE | R4 D | D-1 "Both `aw find` paths match `plans.normalize_status`"; `plans.normalize_status("open") == "legacy/unknown"` (measured) | Applied to every type, D-1 would make `aw find backlog open` (27 rows) and `aw find specs implemented` (22 rows) match nothing. | Low | FIXED | D-1 applies to plans only; V-03 checks the two non-plan counts unchanged. |
| PR-004 | HIGH | IN-SCOPE | R1 / R7 | D-2 "the legacy loader grammar accepts `^-[ \t]*`"; `tve77h` E-11 "one strict `- Field: value` grammar"; `tests/test_front_matter_loose_whitespace.py::test_public_readers_tolerate_loose_leading_whitespace` | The public readers' loose-whitespace contract had no source once they answer from a strict loader. | Low | FIXED | `read_text` returns strict and loose values; public readers use loose, cache uses strict; tests added. |
| PR-005 | LOW | IN-SCOPE | R4 D | `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives` asserts `_read_status(multi)` is None | D-1 changes that assertion but the plan named only one test edit. | Low | FIXED | Named, with the assertions that stay. |
| PR-006 | LOW | IN-SCOPE | R1 | E-07 "`_read_setid`"; `check_engine` defines `_parse_setid`, not `_read_setid` | Wrong symbol. | Low | FIXED | Renamed. |
| PR-007 | MEDIUM | UNDER-SCOPE | R4 C / spec 4.4 | `specs.py` "skip_names = {...}"; `releases.py` inline tuple; `ipd_lint._NON_IPD_BASENAMES`; `artifact_refs` "`README.md` is scanned as a citing document (0u0ako)" | Three more copies were missed, and routing the README skip into `iter_scan_files` would stop citation rewrites in records READMEs. | Low | FIXED | All copies use the `layout` constants; `iter_scan_files` excludes only `meta/`; D-5; Scope-Paths extended. |
| PR-008 | MEDIUM | IN-SCOPE | Spec sync | Spec 4.3 "Functions: `read(id6) -> State`, ..., and `read_at(id6, rev)`"; plan spec sync "No spec change" | The plan adds an interface function to the spec's C5 list without amending it. | Low | FIXED | Spec 4.3 amended in E-02; declared in Scope-Paths and spec sync with its reason. |
| PR-009 | LOW | IN-SCOPE | R2 executability | `aw check --help` "type ... or 'all'"; `check_engine.SUPPORTED` has no `meta` | How `aw check meta` is wired, and whether `aw check all` includes it, was unstated; including it would break the E-07 and E-14 rule-id baselines. | Low | FIXED | Reserved word dispatched before type validation; excluded from `all` in phase B. |
| PR-010 | LOW | IN-SCOPE | R2 reachability | E-11 "exercised on synthetic log fixtures"; `1ajqaa` E-04 (b) | In phase B `create`/`append` write the legacy format, so a fixture built through them has no log. | Low | FIXED | Fixture written from `encode_event` lines in its own git repository. |
| PR-011 | MEDIUM | UNDER-SCOPE | R4 D / E | `attention._TREE_TO_SCAN_ROOTS` "`.agents/plans`"; measured `.agents/`-only fixture listed by `aw find` and `aw attention` | No case covered the legacy `.agents/` root, which the moved readers serve today; a fixed 5 s bar was arbitrary for a CLI-spawning matrix. | Low | FIXED | E-12 `.agents/` case (keep rows or record a ledger decision); wall time pasted. |
| PR-012 | MEDIUM | UNDER-SCOPE | S7 contract | Gate text | The gate lacked the honesty rule wording, the `git add -A` ban, the fence-as-declaration wording and conditional finalize ownership. | Low | FIXED | Full gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must `read_text` be added to the spec's interface list? | Yes; amend spec 4.3 in this plan | Leave the spec unamended; move `read_text` into `tve77h` (already reviewed) | Spec 4.3 function list; C5; AGENTS.md "A plan may amend a spec"; reversible because no caller outside phase B depends on it | yes |
| D-2 | Normalize status matching for all types or plans only? | Plans only | All types (breaks backlog and spec matching); none (keeps the F-03 disagreement) | `plans.normalize_status` measured on `open`, `implemented`; D-1 of the plan | yes |
| D-3 | Split E-07 or the plan? | No | Split at OQ-02's type boundary | One pin set per E-item; 14 items in 5 groups | yes |
| D-4 | Add `executed:1ajqaa` to Item-Dependencies for `meta_cli.py`? | No | Add the edge | E-10 creates the module if absent, within Scope-Paths; adding an edge changes Set ordering for one file | yes |
