# Review findings: plan qhay6a

- Subject-Id: qhay6a
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `093211481` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-250-qhay6a-inventory-the-docs-surface-and-start-the-cutover-docs-patch.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` with 0 errors, 0 warnings and 2 `IPD-C802` infos (em dashes in the validation preamble). After edits it returned `conforming` with 0 findings. Every measurement was taken read-only in the lane worktree; the one write probe (`tools/_qhay6a_probe.py`, printing `agent_workflows.__file__` and `sys.path[0]`) was removed, and `git status --short` was empty afterwards.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 | "39 files at review"; owner named per row without a rule; "verbatim" | 39 at split, 47 at review; owner as `<id6> E-<nn>` by the F-03 owner rule; `UNASSIGNED` rows listed, never given to a part whose E-item does not cover them | PR-004, PR-006. |
| Conventions | Four bullets | Adds the F-03 owner rule, applied per passage | PR-004. |
| E-02 | `python3 tools/regen_agents_block.py`; outcome `rg -n '^- (Status\|...):'`; commands named without an existence check | Module form plus `--check`; quoted-pattern baseline and after counts; `aw <command> --help` exit code per named command, `a5ijjx` dependency, Order 13 deliverable wording; `aw index plans` post-cutover meaning; `Kind` sentence left to `ngc2a2` | PR-001, PR-002, PR-003, PR-006. |
| E-03 outcome | "lists only the managed-block files" | Adds that no cache path is captured (`__pycache__/` ignored, `.pytest_cache` self-ignoring) | PR-005. |
| Findings | F-01..F-03 | Adds F-04..F-07 with review evidence, and a Mermaid `flowchart TD` of the scratch, patch and sibling chain (rendered with `@mermaid-js/mermaid-cli`) | Technical writing standard requirement 12; PR-007. |
| Deferred | Four carriers | Adds `UNASSIGNED` F-03 rows, Carrier `y1zihp` | PR-004. |
| Scope check | Under-scope "none" | States how uncovered inventory rows are handed off | PR-004. |
| Validation preamble | Two em dashes (`IPD-C802`) | Commas | PR-007. |
| V-01, V-02, V-03 | Owner per row; `^- ` grep; test-name binding; stat only | Owner rule check and `UNASSIGNED` list; before and after quoted counts, `--help` exit codes, regen and `--check` output, module `N passed`; `git apply --check` exit 0 and the exact file list | PR-001..PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The managed block produced by `engine.agents_pointer_prose` is installed into every target repository, so its text is a published contract.
2. No. No security boundary; the patch is documentation only.
3. No. Three `E-*` items.
4. No. Both `- Scope-Paths:` entries are explicit files.
5. Yes. The F-03 table is consumed by `a49djh`, `y1zihp`, `ngc2a2` and `90iqr1` E-09 (a test holding the `rewrite` list as data), and the patch lands in the attended cutover commit `cxxmyv`.

AW-TIER: complex

### Step R1

- Checked: spec `4sd62s` 5.4 (the rewrite list and "A document must not describe a command that does not exist"), 4.3 (`aw index plans` becomes an alias of `aw index rebuild`; `--check` deleted), 5.2 step 4a (executed-plan rule amendment), C10a; `engine.agents_pointer_prose`; `tools/regen_agents_block.py` (`main`, `--check`, `--dir`); `tests/test_agents_section_records.py::test_live_agents_md_section_records_are_current` (remedy string `python3 -m tools.regen_agents_block`); `manifest.resolve_manifest_path`; `.aw/.gitignore` `/state/`; `aw <command> --help` for every command E-02 names.
- Found PR-001: the script form of the regen tool imported `agent_workflows` from the main checkout in a worktree (probe: `sys.path[0]` = `tools`, package from the main checkout); the module form imported the worktree copy.
- Found PR-003: `aw check meta` prints `unknown artifact type 'meta'` (exit 2), and `aw meta repair --help` exits 2. `aw ipd set`, `aw specs set`, `aw backlog set`, `aw set` and `aw show --history` exist with the needed flags.

### Step R2

- Checked: `E-*`/`V-*` bijection (3/3); runtime reachability (all `V-*` demand diffs, file content, command output or a test result); dependency `executed:9o83cr` and the transitive path to `a5ijjx` (`a5ijjx` -> `ffceq0` -> `9o83cr`).
- Found PR-002: the E-02 outcome check `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):' AGENTS.md` already returns nothing (exit 1) on the unedited file, because AGENTS.md quotes field syntax in backticks (16 quoted hits; 12 in `engine.py`). The check could not fail.
- Found PR-006: V-02 bound on a test function name, and V-01 had no rule to judge an owner against.

### Step R3

- Checked: the scratch worktree path (gitignored `.aw/state/qhay6a/scratch`), the never-`git add -A`-in-the-checkout rule, `--force` worktree removal scope, and leak exposure of the patch (documentation only; `90iqr1` E-10 runs the sanitizer on the patched tree).
- No finding.

### Step R4

- Checked: idempotence (the scratch worktree is recreated from HEAD each run), capture completeness (`git add -A` in scratch includes new files; `__pycache__/` is ignored by `.gitignore:15`, and pytest 8.2.2 writes its own ignore file into `.pytest_cache`), patch applicability on the executing checkout.
- Found PR-005: V-03 checked the file list but not that the patch applies; `90iqr1` E-09 relies on it applying.

### Step R5

- Checked: QA (V-02 now needs a count that can fail), novice executor (why the module form; what to do with a command that does not exist yet), architect (one owner per `rewrite` row so `90iqr1` E-09 does not fail), stakeholder (spec 5.4 "must not describe a command that does not exist").
- Folded into PR-002, PR-003 and PR-004.

### Step R6

- Checked: 3 `E-*` items, 2 `- Scope-Paths:` entries; the `IPD-Z603` advisory raised by an inline owner rule was resolved by moving the rule to the conventions section. No split needed.

### Step R7

- Checked: siblings `a49djh` (E-02 names the review workflows; E-04 is the catch-all "remaining workflow and template files from the `qhay6a` F-03 table owned by this part"), `y1zihp` (E-02 five READMEs, E-03 two docs and `ipd_schema.py`, E-04 reference and `aw-prompt` documents), `ngc2a2` (E-02 `Kind` renames, E-03 `cli.py`, E-04 quickstarts), `90iqr1` E-09 and F-08, `9o83cr` Deferred row (Carrier `90iqr1`, the managed-block `aw index plans` sentence, now carried here), `a5ijjx`.
- Found PR-004: of the 47 rows, `docs/cli-output-contract.md`, `.aw/records/reviews/README.md` and `.aw/records/roadmaps/README.md` match no sibling E-item, and the remaining workflow bodies were covered only by the `a49djh` E-04 catch-all. `GEMINI.md` carries no pattern; the 44 `agent_workflows/*.py` parser modules, `CHANGELOG.md`, `DECISIONS.md` and `tools/gate_drop_audit.py` found by a wider scan are code or history, outside the documentation patch.

### Step S5

- Checked: owner assignment, nonexistent commands, regen invocation, outcome measure.
- Engineering decisions D-1..D-4 were resolved from repository evidence. No question belongs to the maintainer.

### Pass 2

- Not needed under `steps/s6-rereview.md` rule 1: no `E-*` or `V-*` item was added or removed, and `- Scope-Paths:` and `- Item-Dependencies:` are unchanged. A re-read of every item against the revised E-01 and E-02 found no stale quotation of the old outcome check or the script-form regen command. Lint `conforming`, 0 findings.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / E-02 | `tools/regen_agents_block.py` run as a script: `sys.path[0]` = `tools`, `agent_workflows` imported from the main checkout; `tests/test_agents_section_records.py` remedy `python3 -m tools.regen_agents_block` | In the scratch worktree the script form could regenerate the block from the unedited generator, so the patch would carry stale hashes or text. | Low | FIXED | `python3 -m tools.regen_agents_block` from the scratch root, then `--check` printing `Up to date`; F-05. |
| PR-002 | HIGH | IN-SCOPE | R2 / E-02, V-02 | `rg -n '^- (Status\|Readiness\|Blocks-Release\|From-Backlog):' AGENTS.md`: no output, exit 1, on the unedited file; quoted form: 16 in AGENTS.md, 12 in `engine.py` | The only outcome check could not fail. | Low | FIXED | Baseline and after counts of the backtick-quoted pattern; remaining hits identified as marked legacy quotations; F-06. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / E-02 | `aw check meta`: `unknown artifact type 'meta'`, exit 2; `aw meta repair --help`: exit 2; spec `4sd62s` 5.4 "A document must not describe a command that does not exist" | E-02 named commands that `a5ijjx` has not built yet. | Low | FIXED | `aw <command> --help` exit code recorded per named command; a missing one is named only as an Order 13 deliverable; dependency path stated; F-07. |
| PR-004 | MEDIUM | UNDER-SCOPE | R7 / E-01, Deferred | 47-file `rg -l` list; `a49djh` E-02/E-04, `y1zihp` E-02..E-04, `ngc2a2` E-02..E-04; `90iqr1` E-09 "asserts that the patch touches every file the `qhay6a` F-03 table marks `rewrite`" | Some `rewrite` candidates had no owning E-item, so `90iqr1` E-09 would fail or a row would be silently dropped. | Low | FIXED | F-03 owner rule in conventions; `UNASSIGNED` rows listed in V-01 and handed to `y1zihp` (Deferred); F-04. |
| PR-005 | MEDIUM | IN-SCOPE | R4 / E-03, V-03 | V-03 demanded only `git apply --stat` | Nothing proved the patch applies to the checkout it was cut from, nor that no cache file was captured. | Low | FIXED | `git apply --check` exit 0, exact file list, cache-path note in the E-03 outcome. |
| PR-006 | LOW | IN-SCOPE | R2 / V-01, V-02 | V-02 "showing `test_live_agents_md_section_records_are_current` PASSED"; V-01 "an owning part" | Evidence bound to a function name and to an unstated rule. | Low | FIXED | Module `N passed` line; owners as `<id6> E-<nn>` checked against the rule; `Kind` sentence assigned to `ngc2a2`. |
| PR-007 | LOW | IN-SCOPE | Proofreading / preamble, Findings | `IPD-C802` x2; no diagram; "39 files at review" | Em dashes, no diagram for a five-part chain, a stale count. | Low | FIXED | Commas; Mermaid flowchart; 39 at split and 47 at review. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is the regen tool invoked in the scratch worktree? | `python3 -m tools.regen_agents_block` from the scratch root, then `--check` | `python3 tools/regen_agents_block.py --dir <scratch>` (imports the wrong package) | Import probe at review; the test's remedy string | yes |
| D-2 | What does E-02 do with a command that does not exist yet? | Check `--help` at execution; name a missing command only as an Order 13 deliverable | Add `a5ijjx` to `- Item-Dependencies:` (already transitive through `9o83cr`); drop the commands from the text | Spec `4sd62s` 5.4; `a49djh` E-03 precedent for `aw reviews record` | yes |
| D-3 | Who owns an F-03 `rewrite` row no sibling E-item covers? | `UNASSIGNED`, handed to `y1zihp` through Deferred | Rewrite it here (exceeds the managed-block scope); assign it to `a49djh` E-04 regardless of path (outside its workflow scope) | `90iqr1` E-09 asserts every `rewrite` file is touched; `y1zihp` owns READMEs and docs | yes |
| D-4 | Keep `- Item-Dependencies: executed:9o83cr` and both `- Scope-Paths:` entries? | Keep | Add `executed:a5ijjx` (redundant: `9o83cr` -> `ffceq0` -> `a5ijjx`) | `ffceq0` and `9o83cr` `- Item-Dependencies:` lines | yes |
