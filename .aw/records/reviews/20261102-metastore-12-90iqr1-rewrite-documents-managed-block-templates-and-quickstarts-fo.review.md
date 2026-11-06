# Review findings: plan 90iqr1

- Subject-Id: 90iqr1
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `817f0ba14` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 13) is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them. Probes used throwaway worktrees and files under the gitignored `.aw/state/`, and each was removed afterwards.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 | Search over workflows, docs, READMEs, `engine.py`, `ipd_schema.py` | Adds AGENTS.md, README.md, CONTRIBUTING.md, `cli.py`, the two ipd-spec documents, `aw-prompt` and `--kind` patterns | PR-001, PR-002, PR-003. |
| E-02, OQ-03 (new), gate | Scratch worktree under `/tmp` | Under the gitignored `.aw/state/90iqr1/` | PR-004. |
| E-08, V-08 | `git diff HEAD` | `git add -A` in scratch, then `git diff --cached --binary HEAD` | PR-005. |
| E-02, V-02, E-09 | Managed block rewritten in `engine.py` only | `tools/regen_agents_block.py` regenerates AGENTS.md and the `managed-sections.json` hashes | PR-006. |
| E-09, V-09 | "against a temporary clone of HEAD" | A temporary index with `git apply --cached --check`; the rewrite list is held as test data; install and packaging tests run | PR-007. |
| E-10, V-10, F-07 (new), Deferred | Sanitizer only on the patched tree | Patched-tree run of the text-asserting tests, with failures handed to `cxxmyv` as F-07 | PR-008. |
| E-05, Deferred | "every `aw` option help text" | Help strings only; option renames are `cxxmyv`'s code change | PR-003. |
| Gate | Partial execution contract | Full contract | S7 contract (folded into PR-004). |
| OQ-02 | No recommendation strength | Strength stated | MD-9. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The patch rewrites the published managed block and the installed workflows. They land only in the cutover commit, but this plan authors them.
2. No. It edits no guard module, and the live tree changes only by a patch file, a test and the plan.
3. Partly. It has 10 E-items in 3 groups, and the patch spans about 40 documentation files.
4. Yes. It declares three Scope-Paths.
5. Low. The live documents do not change. A wrong patch is caught by its test or at `cxxmyv`.

AW-TIER: standard

### Step R1

- Checked: the spec 5.4 bullet list. It names "the ipd-spec reference documents" (`.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`, `20260802-1904-01-ipd-structure-and-linting.spec.md`), which the plan omitted (PR-001).
- Spec 4.1 and OQ-25 change the staged-prompt comment to `aw-managed-prompt`. `aw-prompt` appears in `docs/artifact-lifecycles.md`, `.aw/records/prompts/README.md`, `templates/prompts-README.md` and `research-prompt/research-prompt.md`, and the E-01 search could not find them (PR-002).
- `--kind` exists on `aw ipd scaffold` and `aw research mv` (`cli.py`). Spec 5.4 renames the field in option help text, and the plan's E-05 said "every `aw` option" while its test fence allowed only `cli.py` "help text" (PR-003).
- `engine.agents_pointer_prose` exists. `tools/regen_agents_block.py` is the repository's path for re-recording `managed-sections.json` section hashes, and `tests/test_agents_section_records.py` (core) asserts that they are current (PR-006).
- `cxxmyv` E-08 applies `.aw/system/cutover/metastore-docs.cutover.patch` and deletes it with the test, and `cxxmyv` E-06 builds `aw reviews record` and `aw walkthrough new`. `aw reviews` today has only `decisions`, and `aw walkthrough` does not exist, so documenting them as Order 13 deliverables is correct.
- `nq1src` is the open backlog item `20261105-execrecord-01-nq1src-implement-execution-record`, a valid carrier.
- `pyproject.toml` force-includes `.aw/system` in the wheel and the sdist, so the patch file ships while it exists. `engine.collect_source_members` installs from the descended `.aw/system/workflows/`, so `.aw/system/cutover/` is not installed into targets. Probe: an untracked `.aw/system/cutover/` file produced only `doctor.git-untracked`, which is expected for an uncommitted file.

### Step R2

- Checked: the E/V bijection is 10/10.
- Reachability: V-08's patch comes from E-08, and V-09's corrupted-patch failure comes from the E-09 test.
- E-08's `git diff HEAD` would silently drop the two new quickstart files. Measured: an untracked new file produced 0 diff lines, and after `git add -N` it produced `new file` (PR-005).
- E-09's "temporary clone" adds a clone cost the core tier must absorb. Measured instead: `git read-tree HEAD` into a temporary index plus `git apply --cached --check` took 26 ms (PR-007).
- `- Item-Dependencies: executed:9o83cr` is correct. `9o83cr` hands the `aw index plans` sentence here, and its deletions change what the documents must say.

### Step R3

- Checked: E-10 runs the sanitizer on the patched tree. The scratch worktree is gitignored state and leaks nothing into commits. No trust boundary is involved.

### Step R4

- C: one patch, and one generator path for the managed block (PR-006).
- D: a published-text change can break tests that assert today's text. Those tests are now run on the patched tree, and their failures are handed to `cxxmyv` (PR-008).
- E: the patch-apply test guards against drift until the cutover.
- Spec sync: "No spec change" is true.

### Step R7

- Checked `cxxmyv` E-06 and E-08 (applies and deletes the patch and the test; its Scope-Paths cover `.aw/system/workflows/`, `docs/`, `AGENTS.md`, `agent_workflows/` and `tests/`, but not `.aw/system/managed-sections.json` or `.aw/system/cutover/`; `cxxmyv`'s finalize scope reconciliation will see those two paths, so this is recorded for its review), `xexn45` (hands the two commands), `9o83cr` (hands the managed-block sentence) and `ya4ee4` (owns the description prompt).

### Step S5

- Checked: OQ-01 and OQ-02 are resolved. OQ-03 is a HOW question, resolved by the demonstrations above (D-1). No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Spec 5.4 | Spec 5.4 "5 records READMEs, `docs/artifact-lifecycles.md`, the `ipd_schema.py` section schema, and the ipd-spec reference documents" | The two ipd-spec reference documents were outside the inventory. | Low | FIXED | Added to the E-01 roots and E-05; a spec gets a `rewrite` disposition only where it instructs agents to write field syntax. |
| PR-002 | MEDIUM | UNDER-SCOPE | Spec 4.1 / OQ-25 / AC-40 | `rg -l aw-prompt` finds 4 documentation files | The staged-prompt comment form changes, but the search patterns could not find it. | Low | FIXED | `aw-prompt` pattern added; E-05 rewrites them to `aw-managed-prompt`. |
| PR-003 | MEDIUM | IN-SCOPE | Spec 5.4 / R2 fence | `cli.py` `p_ipd_scaffold.add_argument("--kind", ...)`; E-05 "every `aw` option help text"; E-09 fence "`cli.py` help text" | `cli.py` was not inventoried, and "option" was ambiguous between help text and renaming the option (a CLI contract change). | Low | FIXED | `cli.py` and `--kind` are in E-01; E-05 changes help strings only; option renames are deferred to `cxxmyv`. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / lane workspace | E-02 "`git worktree add /tmp/<scratch> HEAD`" | A runner lane may not write outside its workspace, so the scratch step could not run. | Low | FIXED | `.aw/state/90iqr1/scratch` (gitignored), demonstrated; OQ-03; gate rewritten with the full execution contract. |
| PR-005 | HIGH | IN-SCOPE | R2 evidence | Measured: `git diff HEAD` prints 0 lines for an untracked new file | The two quickstarts (new files) would be missing from the patch, and E-08 and V-08 would not notice. | Low | FIXED | `git add -A` in scratch plus `git diff --cached --binary HEAD`; V-08 checks that both quickstarts appear as new. |
| PR-006 | MEDIUM | UNDER-SCOPE | R4 C | `tests/test_agents_section_records.py::test_live_agents_md_section_records_are_current`; `tools/regen_agents_block.py` | Editing the generator without regenerating AGENTS.md and the manifest hashes leaves a patch that fails a core test once applied. | Low | FIXED | Regenerate in scratch; the patch and the E-09 fence include `managed-sections.json`; V-02 runs the test. |
| PR-007 | LOW | IN-SCOPE | R2 / core budget | E-09 "against a temporary clone of HEAD"; measured 26 ms for the index method | A clone is slower than needed, and the test's source for the `rewrite` list was unstated. | Low | FIXED | Temporary-index apply check; the list is held as test data; install and packaging tests added to V-09. |
| PR-008 | MEDIUM | UNDER-SCOPE | R4 D | Tests that assert published text: `test_agents_section_records`, `test_installed_text_current`, `test_technical_writing_delivery`, `test_askme_command_delivery`, `test_authoring_coverage_guidance` | The patch can break text-asserting tests at the cutover, and nothing identified them in advance. | Low | FIXED | E-10 runs them on the patched tree and records F-07 for `cxxmyv`; Deferred row added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Scratch location and new-file capture | `.aw/state/90iqr1/scratch`; `git add -A` plus `git diff --cached --binary HEAD` | `/tmp` (outside the lane); `git diff HEAD` (drops new files) | Probes at review (1 s worktree, 0 vs `new file`, 26 ms apply) | yes |
| D-2 | Rename `--kind` options in this patch? | No; help text only, renames to `cxxmyv` | Rename in the patch (a CLI contract change in a documentation plan) | Spec 5.4; E-09 fence | yes |
| D-3 | Edit `cxxmyv` Scope-Paths for `managed-sections.json`? | No; recorded for its review | Edit it (outside this ledger) | Step 0.1 ledger rule | yes |
