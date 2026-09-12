# Review: deliver Order 07's run-scratch relocation to the shipped surface, orchestrator re772u (Set wfartifacts)

- Subject-Id: re772u
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `14b09376`. `aw ipd lint --phase author` CONFORMED with zero findings before semantic
review, and `--phase review-finalize` conformed after every revision.

SELF-REVIEW DISCLOSURE: the same agent and model authored this Set minutes earlier, so this is close to
a self-review and is worth less than an independent one. Its value therefore rests on what was
EXECUTED rather than reasoned: every numeric claim in every plan was re-measured against the
repository, which is what produced the findings below.

WHAT WAS RUN, since a review's worth is in what it executed. Both reference greps with and without
`--include` filters and with `-c` versus `-o`; per-file occurrence counts across all 25 files; the four
`engine.py` line citations (`:237`, `:3292`, `:5141`, and the real `mkdir` at `:5168`); the fallback
literal at `:5153`; `_AW_GITIGNORE_TEMPLATE` searched for a `workflow-artifacts` entry; the 29-repo
scan plus `git ls-files workflow-artifacts` in the two affected repos; a byte comparison of
`.aw/records/README.md` against the workflow-artifacts template; `git ls-files .aw/records/reviews | wc -l`;
`ls` + `comm` across both artifact trees per shared workflow; the 42/10 test-reference counts; and the
shipped `agents-README.md` template plus a freshly installed scratch repo.

EVERY LOAD-BEARING CLAIM HELD. 86 bare occurrences and 0 prefixed re-verified EXACTLY. The 29-repo
count and both affected repos' file counts (11 and 3) re-verified exactly. All four `engine.py` citations
resolve. The template genuinely has no entry for the path. `.aw/records/README.md` is byte-identical to
the workflow-artifacts README. `records/reviews/` holds exactly 170 files. The migration tool really
does untrack in place with no caller in `agent_workflows/`.

FOUR FINDINGS, ALL FIXED IN PLACE. Two are counting errors in my own authoring (PR-001), one is a
missing case in the riskiest child (PR-002), one names the specific tests that assert the defect
(PR-003), and one materially NARROWS a child after discovering the shipped template is already correct
(PR-004).

THE SET'S SEQUENCING IS SOUND AND IS THE STRONGEST THING ABOUT IT. Order 02 first is not a preference:
Order 03 WRITES the sentence "this is gitignored by default", and writing that before the pattern exists
would reproduce the exact defect being repaired (`assess.md:139` has said it since Order 07 while
nothing enforced it).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing / F. Honest documentation | both greps run with and without `--include`, and with `-c` vs `-o` | THE AUTHORED COUNTS WERE WRONG IN TWO INDEPENDENT WAYS. The FILE count was 27 and is 25: `grep -rl` without `--include` also matched three `assess/tools/__pycache__/scan_secrets.cpython-3*.pyc` binaries (unfiltered total 28), which are build output and not editable bodies. And two per-file figures mixed UNITS: `00-run-protocol.md` is 18 LINES but 20 OCCURRENCES, `README.md` 11 lines but 12, while the aggregate 86 was already occurrences. A line-driven sweep would report itself complete with 3 references left. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to 25 files and 20/12 occurrences in Order 03's Concern, conventions and E-01, and in this orchestrator's F-1. Order 03 E-01 now MANDATES `-o` plus the `--include` filters and V-01 makes a pasted `grep -c` or an unfiltered command a FAILED validation regardless of the number it produced. Recorded as Order 03 F-7/F-8 and F-9 here. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness and data integrity | `ls` + `comm` on both artifact trees, per shared workflow | ORDER 05 DESCRIBED A MOVE WHERE THE REALITY IS A MERGE. Measured in THIS repo: `workflow-artifacts/` holds 5 entries and `.aw/workflow-artifacts/` holds 10, sharing THREE workflow names (`assess-bugs`, `assess-documentation`, `release-review`). The plan's only conflict rule was same-FILE-different-bytes; it never said the destination may already be populated, so an implementation assuming an absent destination would fail on the existing directory or replace it. ZERO `<RUN_ID>`s collide, because run ids are timestamps, so the merge is clean here, but that is luck and not a design. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Order 05 E-01 now requires merging per `<workflow>/<RUN_ID>/` leaf and states the measured populated-destination case; a new Required-tests bullet and V-03 demand a MERGE test proving a pre-existing destination run survives alongside the relocated one; V-01 makes an absent-destination-only implementation a FAILED validation. Recorded as Order 05 F-7 and F-10 here. |
| PR-003 | LOW | IN-SCOPE | G. Plan executability | `tests/test_installer.py:394`, `:406`, `:409-410`; `tests/test_awretrofit_install_selfheal.py:69`, `:78` | ORDER 01 SAID SOME TESTS "ASSERT THE DEFECT" WITHOUT NAMING THEM, leaving the executor to hunt. Verified true and located: `test_installer.py:394` asserts the repo-root README `is_file()`, `:406` asserts its "Git Guidelines" content, `:409-410` asserts a re-run preserves a customized copy, and `test_awretrofit_install_selfheal.py:69`/`:78` exercise `git_add_optional` on the same path (its docstring already cites "Order 07 gitignores workflow-artifacts", so it half-knew). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Order 01 gained F-7 naming all five sites and E-03 now names them inline, flagging `:409` as the subtle one: preserving a user's customized README is CORRECT behavior that should survive at the new path, so it must be re-pointed rather than deleted. |
| PR-004 | HIGH | OVER-SCOPE | C. Architecture / F. Honest documentation | `templates/agents-README.md`; `engine.py:5205`; a fresh scratch install | ORDER 04 TREATED A LOCAL DRIFT AS A SHIPPED DEFECT AND WOULD HAVE EDITED CORRECT PROSE. The wrong `.aw/records/README.md` is real, but the SHIPPED template `agents-README.md` is already correct ("# .aw/records/ / Agent tooling for this repository", describing `plans/` and `workflows/` ownership), `engine.py:5205` emits it, and a freshly installed scratch repo was confirmed to receive the correct text. So no target repo is affected unless it predates the Order 11 migration, and the deliverable is a one-file repair of THIS checkout. Also measured: NO test pins the content (four assertions across two files check existence and path suffix only), so the rewrite is unblocked. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Order 04's Scope and Concern now state this is local drift; E-03 is re-titled to REPAIR this repo's file, is told to start FROM the shipped template, and explicitly forbids editing it; V-03 requires `git diff --stat` proving the template UNCHANGED and treats a modified template as a FAILED validation. F-5 corrected to record that no assertion needs changing, and F-6 added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The maintainer asked mid-review to remember isolated worktrees. Is that a finding, or a contract addition? | A CONTRACT ADDITION to all six plans, not a finding. | Raise it as a finding against each plan (rejected: the plans were not WRONG, they simply omitted a standing operational instruction, and six identical findings would inflate the register without adding information); rely on the runner's default (rejected: correct for `aw oc run`/`aw agy run`, which default `isolate_worktree` True, but this Set is large enough that a hand-run is plausible and the contract is where an executor looks). | `oc_runipd.py:3048`/`:6106` and `agy_runipd.py:2055`/`:3254` confirm the default; maintainer instruction 2026-09-12. | yes |
| D-2 | Should the review re-measure every claim, given the same model authored the plans minutes earlier? | YES, EXHAUSTIVELY, and treat measurement as the review's only real contribution. | Read for coherence and trust the numbers (rejected: a self-review that re-reads its own reasoning finds nothing, and PR-001 and PR-004 were BOTH invisible from the prose and only appeared when commands were run). | The four findings, each produced by a command rather than by reading. | yes |
| D-3 | PR-004 shows one child was over-scoped. Split it, or narrow it? | NARROW IT in place. | Split Order 04 into shipped-template and local-repair children (rejected: after the narrowing there IS no shipped-template work, so a split would create an empty child); leave it and let the executor discover the template is fine (rejected: the plan instructed a rewrite, and an executor following it would replace correct prose). | The template's text, its emission site, and a verified fresh install. | yes |
