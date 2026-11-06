# Review findings: plan 59aiyh

- Subject-Id: 59aiyh
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This round was reviewed at HEAD `4a7499289` in a runner review-sweep lane worktree, a non-interactive run. The lane-input
copy (revision 6) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean before the edits, and
`--phase review-finalize` reported clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Item-Dependencies, OQ-02, gate | `executed:tve77h` was called sufficient | `executed:tve77h, executed:xexn45`, with the reason and no critical-path cost | PR-001. |
| E-01 | The builder renders the legacy format itself "exactly as today's writers do" | The builder writes through `artifact_meta.create`/`append` (`write_legacy`) and `render_legacy_text`, has no renderer of its own, and writes reviews through `review_findings.write_review` | PR-001. |
| E-01, batch rule, F-08 | Every field is validated, so a deliberately invalid input cannot be built | `raw_fields=` escape; new `invalid-input` reason class | PR-002. |
| F-03, E-03 to E-09, Scope | Six batches; G1 to G7 counts that did not sum to the file total (G6 99, G7 11) | Seven batches, a first-match partition with re-measured counts, an EXCLUDED list, re-derivation at execution time | PR-003. |
| E-02, V-02, F-09 | Byte equality "before E-01 and after it"; a 3 s bound on a module that runs `aw attention` | E-13 captures a golden file before any edit; a 10 s bound from measurement, with a fallback; a parity test against the production creating commands | PR-004, PR-005. |
| E-10, V-10, F-05, Scope-Paths | 40 fixtures carry metadata; review-pilot plans are converted | 26 carry `- Id:`/`- Status:`; the review-pilot corpus stays literal because `tools/review_pilot.py` reads it; `support.CONFORMING_ORCHESTRATOR` consumers are named | PR-006. |
| Batch rule, E-12, V-12 | `-q` twice, no `-m ""`, an identical multiset that the new test module makes impossible, randomized order under xdist | One deterministic command (`-m "" -p no:randomly -n 0 -rA`), saved under `.aw/state/59aiyh/`; the new node ids are allowed | PR-007. |
| E-13 (new), V-13 | Baselines "before E-03" or "before E-01" with no item that captures them | One baseline item before any edit | PR-004. |
| E-11 | "so no test can bypass the switch" | The switch test proves that no BUILDER path bypasses it; the F-06 census is the evidence for tests | PR-008. |
| Gate | Partial execution contract | Full contract | PR-009. |
| E-03, E-06, E-08, OQ-01 | One split seam (G6) | Pre-measured seams for G1, G4 and G6 | PR-010. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. It creates the shared test interface (`tests/record_builder.py`, `RECORD_FORMAT`) that Orders 11 and 13 depend on (`9o83cr` E-02 and E-13; `cxxmyv` E-07).
2. No guard module is edited. It rewrites the test data of commit, lane and merge tests (G5).
3. Yes. It has 13 E-items in 5 task groups and touches about 300 test modules.
4. Yes, through globs (`tests/test_*.py`), which `aw ipd finalize` treats as directory-bounded entries.
5. Yes. A data rewrite that silently changes what a test exercises weakens the suite unnoticed. The identical outcome list per batch is the guard.

AW-TIER: complex

### Step R1

- Checked: `support.ready_plan_text` exists, with "BUILT FROM THE REAL GENERATOR"; 15 files reference it and there are 30 call expressions (plan: 14 and 29; this is drift only). `ipd_authoring.build_skeleton`, `artifact_naming.build_clustered_name` and `parse_clustered`, `review_findings.render_review`, `tests/repo_template.py::copy_template_repo` and `tests/slow_allowlist.txt` exist, and `tests/conftest.py` is absent, all as claimed. Every module named in E-05, E-08, E-09 and E-10 exists.
- F-01 re-measured: 311 files and 6,657 lines (plan: 309 and 6,638; drift only). The helper pattern gives 89 matches (plan: 88). There are 10,498 collected tests (plan: 10,469). There are 7 `aw-prompt` modules, and 58 `lint_text` calls in 10 modules, as claimed.
- F-03 did not reproduce. The authored per-group counts sum to 309 files, but G6 at 99 files and G7 at 11 files cannot both hold for the stated patterns: the patterns give G6 69 and leave 44 unmatched (PR-003).
- F-05 was inaccurate. 40 is the count of ALL tracked fixture `.md` files; 26 carry `^- (Id|Status):`, at both `0cbfcc706` and HEAD (PR-006).
- The `tve77h` interface names are used as defined. `validate_event` is the registry checker; `validate_new_events` is the writer-side check (`tve77h` E-03).

### Step R2

- Checked: the E/V bijection is 13/13 after `aw ipd sync` assigned E-13. Each V item demands pasted diffs, test runs or file listings, so reachability holds by construction. Scope-Paths: `tests/fixtures/review-pilot/**` was removed because that corpus is now kept, and `tests/fixtures/record_builder/**` was added for the golden file. `- Item-Dependencies:` was corrected (PR-001).
- Counts of mutable populations (files per batch, fixtures, helpers, collected tests) are now context; each bar is a re-derived comparison (R2 live-artifact convention).
- The comparison command was not executable as written: it set `-q` on top of the `addopts` `-q`, did not pass `-m ""` for `livecorpus` and `slow` tests outside G5, and required an identical full multiset although E-02 adds tests (PR-007).

### Step R3

- Checked: the change is test-only. Fixture repositories are temporary or gitignored (`tmp/`, `.aw/state/`). `aw sanitize --agent` runs in E-12. Records written through `artifact_meta` pass its leak refusals (`tve77h` E-03), so a builder default such as an author name must be a non-identifying token (`tester`, the current default). No secret or trust-boundary change. No finding.

### Step R4

- Checked: A, C, D, E and F of the engineering rubric.
- C: the authored E-01 duplicated the legacy format in the test tree. That breaks the spec's "writes through `artifact_meta`" requirement and leaves two copies of the format for the cutover to change (PR-001).
- D: the anti-regression guard is the identical per-test outcome list. It needed determinism (`-p no:randomly`, `-n 0`) and full marker coverage (PR-007), and an escape for invalid input so that tests of refusals keep their subject (PR-002).
- E: E-02 gains a parity test against the production creating commands, so builder output is shown to be what the toolkit writes (PR-005).
- Spec sync: there is no spec change, which is truthful. `CONTRIBUTING.md` does not mention `ready_plan_text`. Documenting the builder after the cutover is `90iqr1`'s concern, and its Scope-Paths are a patch file, so this plan correctly makes no claim on it.

### Step R5

- Checked through the eight personas:
  - QA and regression: the outcome-list diff is strong once it is deterministic.
  - Architect: one switch point and no second renderer (PR-001).
  - Engineer: batch boundaries are disjoint and re-derivable (PR-003), and split seams are pre-measured (PR-010).
  - Power user and novice: no user-facing change.
  - Stakeholder: the C10a proof at the cutover depends on E-11 and F-06, which are now honest about what the switch test proves (PR-008).

### Step R6

- Checked: 13 E-items in 5 groups. Each batch E-item is one mechanical concern under one rule, though a large one. G1, G4 and G6 each carry a measured split seam, and splitting all three gives 16 E-items, inside the 18-item limit. No Set split is recommended (D-2).

### Step R7

- Checked: `cxxmyv` E-07 switches `RECORD_FORMAT` to `"log"` and converts the setter-byte assertions, which matches E-01 and F-06. `9o83cr` depends on `executed:59aiyh` and names `tests/record_builder.py` and `RecordBuilder(repo_root)`, which matches. The orchestrator `63ib9r` child table row for Order 10 reads `executed:tve77h` and now diverges from the plan's `executed:tve77h, executed:xexn45`. The runner reads each plan's own `- Item-Dependencies:`, and that row is the orchestrator's own record, outside this review's edit scope, so the row is reported here for the orchestrator's review to reconcile (D-3). `xexn45` E-01 and E-11 define `write_legacy` and `render_legacy_text`, which E-01 now consumes. `ffceq0` and `t4gl15` add new test modules in their own Scope-Paths, and those modules are covered by the batch rule's re-derivation.

### Step S5

- Checked: OQ-01 was updated with the measured seams and is resolved and non-blocking. OQ-02 was revised by review (D-1), with `Owner` set to the reviewer. No question needs the human. No finding is left open.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4 C / spec trace | `4sd62s` section 7 step 6 "ONE shared record builder that writes through `artifact_meta`"; plan E-01 "renders the legacy format exactly as today's writers do"; `xexn45` E-01 `write_legacy`, E-11 `render_legacy_text`; `tve77h` E-15 `create` is log-format | With only `tve77h`, the builder had to carry its own legacy renderer, which is a second copy of the format in `tests/`. That contradicts the spec, and the cutover would have to change two renderers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Depend on `executed:xexn45`. The builder writes through `artifact_meta.create`/`append` and `render_legacy_text`; reviews go through `review_findings.write_review`. There is no critical-path cost (`9o83cr` already waits on `ffceq0`/`t4gl15`, which wait on `xexn45`). |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 D | `tests/test_releases.py` "`- Status: bogus`"; `tests/test_check_engine.py` "`- Status: EXECUTED`"; 15 such modules | A builder that validates every value cannot build the invalid input that refusal tests need, so those tests would lose their subject or stay hand-built with no recorded reason. | Low | FIXED | `raw_fields=` escape, the `invalid-input` reason class, and F-08. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R2 | F-03 "G6 ... 99, 1,199; G7 ... 11, 124"; Scope "six family batches" | The batch counts were not reproducible and the partition was not disjoint (6 files match two groups). An executor could not tell which files E-09 owned. | Low | FIXED | First-match partition, re-measured counts, an EXCLUDED list, and lists re-derived per batch into `.aw/state/59aiyh/`. |
| PR-004 | MEDIUM | UNDER-SCOPE | R2 G | E-02 "byte equality between `support.ready_plan_text(...)` before E-01 and after it"; E-12 "before E-03 and now" | No item captured the before-state. Once E-01 had changed `support.py`, the "before" bytes and the "before" outcome lists no longer existed. | Low | FIXED | New E-13/V-13 captures every baseline and a golden file before any edit. |
| PR-005 | MEDIUM | IN-SCOPE | R4 E | E-02 "runs under 3 s" with `aw find`, `aw attention`, `aw check` visibility tests; F-09 measured 0.47 s, 2.4 s and 0.9 s | The 3 s bound was unsatisfiable. There was also no proof that builder output equals what the production commands write. | Low | FIXED | 10 s bound with a slow-module fallback, one call per command, and a parity test against six creating commands. |
| PR-006 | MEDIUM | IN-SCOPE | R1 / R4 D | F-05 "40 tracked `.md` fixtures carry bullet metadata"; `tools/review_pilot.py` reads `tests/fixtures/review-pilot/plans` by `manifest.json` filename | 26, not 40, carry metadata. Converting the review-pilot corpus would break a tool outside the test tree. The `CONFORMING_ORCHESTRATOR` consumers were not named. | Low | FIXED | Corrected counts; review-pilot kept literal (carrier `cxxmyv`) and removed from Scope-Paths; consumers named. |
| PR-007 | MEDIUM | IN-SCOPE | R2 G / R4 D | Batch rule `-o addopts="" -p no:randomly -q`; E-12 "identical" full multiset; `pyproject.toml` `addopts` `-m 'not slow and not livecorpus'` | The comparison was not deterministic or complete, and E-12 demanded an identity that E-02's new tests make false. | Low | FIXED | One command with `-m "" -p no:randomly -n 0 -rA` and a fixed filter; E-12 allows only the new node ids. |
| PR-008 | LOW | IN-SCOPE | R4 F honest claims | E-11 "so no test can bypass the switch by building records another way through the builder" | A monkeypatch of `RECORD_FORMAT` proves only that builder paths use the switch. | Low | FIXED | Claim narrowed; F-06 named as the test-side evidence. |
| PR-009 | MEDIUM | UNDER-SCOPE | S7 execution contract | plan gate | The gate lacked the honesty rule, the `git add -A` ban, the declaration wording of the fence, and conditional finalize ownership. | Low | FIXED | Gate rewritten. |
| PR-010 | LOW | IN-SCOPE | R4 right-sizing | E-03 has 1,568 lines in one item; OQ-01 named a seam only for G6 | The densest batch had no pre-measured split seam. | Low | FIXED | Seams for G1, G4 and G6 with measured line counts; OQ-01 updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which Orders must execute before this plan? | `tve77h` and `xexn45` | `tve77h` only, with a builder-local renderer, which duplicates the format and contradicts the spec | `4sd62s` section 7 step 6; `xexn45` E-01/E-11; `9o83cr` Item-Dependencies | yes |
| D-2 | Split the plan into a Set? | No; pre-measured in-plan seams | Split into per-batch child plans | Step R6; 16 E-items worst case | yes |
| D-3 | Edit the orchestrator `63ib9r` child-table row for Order 10? | No; report it for the orchestrator's own review | Edit `63ib9r` in this lane | Review scope ledger is `59aiyh` only; the runner reads each plan's `- Item-Dependencies:` | yes |
| D-4 | Keep the review-pilot plan corpus literal? | Keep it literal | Convert it, which breaks `tools/review_pilot.py`'s filename and quotation contract | `tools/review_pilot.py` reads `manifest.json` and `defects.json` | yes |
