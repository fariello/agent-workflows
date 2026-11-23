# IPD: Update the INDEX statements in the user documents and the changelog

- Date: 2026-11-09
- Kind: child
- Concern: After Order 220 no `aw` command writes `INDEX.json` or `INDEX.md`, so four user documents that describe INDEX generation as current behavior become wrong; C10a of spec `4sd62s` requires documents and behavior to agree at every commit of the family. This is part 8 of the round-3 split of `q6epwc` (Order 41), carrying the `docs/`, `README.md`, `CONTRIBUTING.md` and `CHANGELOG.md` subset of `q6epwc` E-15.
- Scope: edit the named INDEX sentences of `docs/cli-output-contract.md`, `docs/cli-agent-protocol.md`, `CONTRIBUTING.md` and `README.md`, and add one `CHANGELOG.md` line. EXCLUDES the plans and research READMEs and the installed template (Order 227).
- Scope-Paths: docs/cli-output-contract.md, docs/cli-agent-protocol.md, CONTRIBUTING.md, README.md, CHANGELOG.md, .aw/records/plans/pending/20261109-metastore-226-m8dblq-update-the-index-statements-in-the-user-documents-and-the-ch.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15, executed:tqknnc
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 226
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: m8dblq

> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-23 executed (antigravity): finalize m8dblq after run-20261123T035302Z-2681364 (commits 6d9caaf56/35966fbf3 landed directly on main due to vl3pvt; verified with full pytest suite: 2898 passed, 1 skipped) [Scope attribution - 9 changed path(s) OUTSIDE Scope-Paths were DISREGARDED as not attributable to this execution (evidence: commit-cohesion), so no --scope-reason was demanded for them: .aw/records/backlog/done/20261123-tg3v86-01-tg3v86-statusline-spend-resets-on-restart.backlog.md, .aw/records/backlog/open/20261123-metastore-01-bdimw6-unowned-reader-and-grammar-hits.backlog.md, .aw/records/backlog/open/20261123-metastore-01-gapf1m-plans-cite-deleted-in-metadata-region.backlog.md, agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py (... and 4 more; see disregarded_no_evidence_paths in the finalize evidence)]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED
- 2026-11-14 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED; review record .aw/records/reviews/20261109-metastore-226-m8dblq-update-the-index-statements-in-the-user-documents-and-the-ch.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

After this plan, the four user documents describe `aw index rebuild` and the `aw index <type>` alias instead of INDEX file generation, and `CHANGELOG.md` records the change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`q6epwc` E-15's document list is split across Orders 226 and 227; this plan takes `docs/cli-output-contract.md`, `docs/cli-agent-protocol.md`, `CONTRIBUTING.md`, `README.md` and the `CHANGELOG.md` line. Replacement wording for every edit: "`aw index rebuild` rebuilds the local cache; `aw index <type>` is an alias". Write no em or en dashes in this user-facing prose (repository execution contract).

### Task group 1: one document per item

- [x] E-01 `docs/cli-output-contract.md`: rewrite the `--limit` hot-window sentence and the `index` step-cue example.
  - Depends on: none
  - Expected outcome: `rg -n "INDEX\.(json|md)" docs/cli-output-contract.md` prints only lines that describe the removal.
  - Execution state: performed

- [x] E-02 `docs/cli-agent-protocol.md`: rewrite the `INDEX.md` hot-window sentence (the `--limit` bullet).
  - Depends on: none
  - Expected outcome: `rg -n "INDEX\.(json|md)" docs/cli-agent-protocol.md` prints only removal-describing lines.
  - Execution state: performed

- [x] E-03 `CONTRIBUTING.md`: rewrite the two manifest bullets (Plans Manifest, Research Manifest).
  - Depends on: none
  - Expected outcome: `rg -n "INDEX\.(json|md)" CONTRIBUTING.md` prints only removal-describing lines.
  - Execution state: performed

- [x] E-04 `README.md`: rewrite the research "`INDEX.json`/`INDEX.md`" mention in the records layout list.
  - Depends on: none
  - Expected outcome: `rg -n "INDEX\.(json|md)" README.md` prints only removal-describing lines.
  - Execution state: performed

- [x] E-05 `CHANGELOG.md`: add one `2.0.0 (pending)` line saying INDEX files are no longer generated and `aw index <type>` is an alias of `aw index rebuild`. Then commit through `aw commit m8dblq -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: one new line under `2.0.0 (pending)`; the commit lists only Scope-Paths files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- User-facing prose (READMEs, CHANGELOG, docs) carries no em or en dashes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "INDEX\.(json|md)|STATUS\.md" README.md CONTRIBUTING.md docs/cli-output-contract.md docs/cli-agent-protocol.md` prints `README.md` 1 line (records layout list), `CONTRIBUTING.md` 2 lines (the two manifest bullets), `docs/cli-agent-protocol.md` 1 line (`--limit`); `docs/cli-output-contract.md` describes the hot window and the `index` step cue without the literal filename, so E-01 finds those by `rg -n "hot.window|aw index" docs/cli-output-contract.md`.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Update docs/cli-output-contract.md"] --> E05["E-05: Update CHANGELOG.md & commit"]
    E02["E-02: Update docs/cli-agent-protocol.md"] --> E05
    E03["E-03: Update CONTRIBUTING.md"] --> E05
    E04["E-04: Update README.md"] --> E05
```

1. One edit per document (E-01 to E-04).
2. Changelog line and commit (E-05).

## Deferred / out of scope (with reason)

- `.aw/records/plans/README.md`, `.aw/records/research/README.md` and the template: Order 227.
  - Carrier: q6epwc
- Rewording the managed block and quickstarts for log-based commands: the alias keeps those commands working.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 5 work Scope-Paths.

## Required tests / validation

No test module targets these four documents. Commands: the per-document `rg` checks, the dash check, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; this plan IS the documentation sync for `4sd62s` 4.5 in these four files.

## Open questions

### OQ-01: Should the documents mention the cutover that deletes on-disk INDEX files?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. On-disk files are removed by `m0001` at the cutover (`cxxmyv`); these documents say only what the commands do now. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff` hunks of `docs/cli-output-contract.md` and `grep -nP "[\x{2013}\x{2014}]"` over the changed lines printing nothing.
  - Observed evidence: `git diff` of docs/cli-output-contract.md (commit 6d9caaf56) changed three lines: line 318 `--limit` now reads "on the index verbs (`index`, `research index`), it is ignored: INDEX files are no longer generated, `aw index rebuild` rebuilds the local cache, and `aw index <type>` is an alias." (was "for index generation ... it configures the recent-item hot window."); line 454 step-cue example `(e.g. `doctor`, `index`, `check`)` -> `(e.g. `doctor`, `index rebuild`, `check`)`; lines 514-517 the `aw index plans|research|prompts|all` bullet changed from "Unchanged. They still write and check their INDEX files..." to "Aliases of `aw index rebuild`. They rebuild the local cache and print one notice; INDEX files are no longer generated. With `--check`, a type spelling runs that type's content drift rules instead, exiting as `aw check <type> --all` would." (matches `aw index --help`). `rg -n "INDEX\.(json|md)" docs/cli-output-contract.md` prints nothing. Dash check `git diff -U0 | grep '^+' | grep -nP "[\x{2013}\x{2014}]"` printed nothing (exit 1).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk of `docs/cli-agent-protocol.md`, `rg -n "INDEX\.(json|md)" docs/cli-agent-protocol.md` showing only removal-describing lines, and the dash check over the changed lines printing nothing.
  - Observed evidence: `git diff` hunk of docs/cli-agent-protocol.md: `-  and mutating verbs (`group`, `rename`) ignore it. On index-building verbs (`index`, `research index`),` / `-  it configures the recent-item hot-window size for `INDEX.md` rather than bounding output records.` replaced by `+  and mutating verbs (`group`, `rename`) ignore it. On the index verbs (`index`, `research index`),` / `+  it is ignored: INDEX files are no longer generated, `aw index rebuild` rebuilds the local cache,` / `+  and `aw index <type>` is an alias.`. `rg -n "INDEX\.(json|md)" docs/cli-agent-protocol.md` prints nothing. Dash check printed nothing (exit 1).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks of `CONTRIBUTING.md`, `rg -n "INDEX\.(json|md)" CONTRIBUTING.md` output, and the dash check printing nothing.
  - Observed evidence: `git diff` hunks of CONTRIBUTING.md: the two manifest bullets (Plans Manifest `aw index plans` GENERATED, GITIGNORED, LOCAL...; Research Manifest `aw research index`) replaced by one bullet `+- **Plans and Research Manifests**: no longer generated. `aw index` writes no `INDEX.json` or` / `+  `INDEX.md` file. `aw index rebuild` rebuilds the local cache (`.aw/state/index.db`, gitignored,` / `+  never committed); `aw index <type>` (for example `aw index plans`) and `aw research index` are` / `+  aliases of it.`. Also the Generated row of the file-category table dropped `.aw/records/plans/INDEX.*`, `.aw/records/research/INDEX.*` and the `aw index plans`, `aw index research` tools (same stale claim, found by `rg -i "INDEX file|aw index plans"`; see decision D1). `rg -n "INDEX\.(json|md)" CONTRIBUTING.md` prints `55:- **Plans and Research Manifests**: no longer generated. `aw index` writes no `INDEX.json` or` and `56:  `INDEX.md` file. ...`, both removal-describing. Dash check printed nothing.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk of `README.md`, `rg -n "INDEX\.(json|md)" README.md` output, and the dash check printing nothing.
  - Observed evidence: `git diff` hunk of README.md line 405: `research/` - durable research reports `(with `INDEX.json`/`INDEX.md`)` -> `(no INDEX files are generated: `aw index rebuild` rebuilds the local cache; `aw index <type>` is an alias)`. `rg -n "INDEX\.(json|md)" README.md` prints nothing. Dash check printed nothing.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `git diff` hunk of `CHANGELOG.md` showing the one new line under `2.0.0 (pending)`, the dash check printing nothing, and `git show --stat` of the `aw commit m8dblq` commit listing only Scope-Paths files.
  - Observed evidence: `git diff` hunk of CHANGELOG.md adds one line under `## 2.0.0 (pending)`: `+- Changed: `aw index` no longer generates `INDEX.json` or `INDEX.md` files. `aw index rebuild` rebuilds the local cache, and `aw index <type>` (such as `aw index plans`) and `aw research index` are aliases of it; `--limit` is ignored on them.`. Dash check printed nothing. `git show --stat 6d9caaf56` (aw commit m8dblq): `CHANGELOG.md | 1 +`, `CONTRIBUTING.md | 12 +++++-------`, `README.md | 2 +-`, `docs/cli-agent-protocol.md | 5 +++--`, `docs/cli-output-contract.md | 11 ++++++-----`, `5 files changed, 16 insertions(+), 15 deletions(-)`: only Scope-Paths files. Core gate `python3 -m pytest`: `2896 passed, 1 skipped, 11 warnings in 164.49s (0:02:44)`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed (Order 220 first, so the documents change only once the behavior has).

Safety rule: uncommitted changes and untracked files you did not create are not yours; never revert, stage, commit, discard, reformat, or "clean up" another party's work.

Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`).

Honesty rule: paste the ACTUAL outputs; never claim a result you did not run.

Commits: only through `aw commit m8dblq -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize m8dblq` (never a hand git mv), after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When aw oc run or aw agy run executes the plan, the runner performs the finalize; a hand executor runs aw ipd finalize m8dblq itself.
