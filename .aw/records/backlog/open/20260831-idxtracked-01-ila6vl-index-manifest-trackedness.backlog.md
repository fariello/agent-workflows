- Id: ila6vl
- Status: open
- Set: idxtracked
- Priority: medium
- Work-Kind: chore
- Summary: DECIDED (maintainer 2026-08-31): stop tracking the four generated INDEX.json/INDEX.md manifests; gitignore and git rm --cached them, then reconcile the measured consumers (stale-index semantics, finalize owned_paths, auto-refresh self-commit, three docs, one test)

## Workflow history
- 2026-08-31 decided (opencode/its_direct/pt3-claude-opus-5-1m-us, on the maintainer's call): MAINTAINER CALLED IT - stop tracking the generated INDEX manifests. Item converted from an open QUESTION into a decided IMPLEMENTATION task; the original framing and its three middle options are kept in the body as the record. Basis, all measured: 328 commits in 14 days, 14 commits changing nothing but an INDEX file, byte-deterministic regeneration, nothing reading the committed copy as an authority, the speed argument removed by e32j35's re-scope, and the main counter-argument DISPROVED (check.stale-index byte-compares against the file on DISK, not against git, so it never needed the file committed). Accepted losses recorded explicitly: no manifest in a fresh clone, no git-host browsing of INDEX.md, no manifest diffs in review. Implementation surface measured and wider than gitignore: stale-index semantics (emitted by plans_index and research_index, consumed by doctor in four places), ipd_lifecycle.py:1630 finalize owned_paths (the sharpest edge, since finalize is a journalled transaction with rollback), status_set auto-refresh self-commit, artifact_rename, three documents, and tests/test_auto_index_on_mutation.py.
- 2026-08-31 created (aw backlog): Decide whether the generated INDEX.json/INDEX.md manifests stay tracked: 328 commits in 14 days, 14 commits existing only to repair drift, byte-deterministic regeneration, and nothing reading the committed copy as an authority


DECIDED BY THE MAINTAINER 2026-08-31: STOP TRACKING the generated INDEX manifests. They become
gitignored, locally-regenerated views. This item is therefore an IMPLEMENTATION task, not an open
question; the question it used to pose is recorded below as the basis so the reasoning survives.

SCOPE, measured. FOUR tracked generated files:
`.aw/records/plans/INDEX.json`, `.aw/records/plans/INDEX.md`,
`.aw/records/research/INDEX.json`, `.aw/records/research/INDEX.md`.

THE BASIS FOR THE DECISION, all measured at HEAD `ee5ef94f`.

1. CHURN. In 14 days, `plans/INDEX.json` was touched by **328** commits and `plans/INDEX.md` by
   **268** (research: 20 and 19). Among the highest-churn files in the repo, and every diff is derived.
2. FOURTEEN COMMITS EXIST ONLY TO REPAIR IT. Of the INDEX-touching commits in the last 30 days, 14
   changed NOTHING ELSE (checked each commit's full file list for any non-INDEX path). Those commits
   carry no information; they exist because the file drifted from its source.
3. REGENERATION IS BYTE-DETERMINISTIC, so the tracked copy carries nothing the tree does not already
   carry. VERIFIED by regenerating twice and byte-comparing: identical.
4. NOTHING READS THE COMMITTED COPY AS AN AUTHORITY. Every `INDEX.json` reference in
   `agent_workflows/*.py` is a writer, a path constant, help text, or the `attention_contract`
   exclusion that deliberately treats manifests as NON-artifacts (`attention_contract.py:165`).
5. THE SPEED ARGUMENT IS GONE. Plan `e32j35`'s review measured a plain filesystem `find -iname`
   answering the common case in **20ms vs 357ms**, and re-scoped that plan away from index-first
   resolution entirely.
6. THE MAIN COUNTER-ARGUMENT DOES NOT HOLD. `check.stale-index` does NOT require the file to be
   COMMITTED: `plans_index.py:270-284` builds the manifest in memory and byte-compares it against the
   file on DISK. An untracked-but-present manifest stays fully checkable.

WHAT IS ACTUALLY LOST, stated plainly so the decision is honest rather than one-sided:

- A fresh clone will have NO manifest until something generates one. Any tool that assumes presence
  must generate lazily or degrade.
- `INDEX.md` will no longer be browsable on a git host (the one benefit a human actually used).
- A manifest change will no longer appear in review diffs.
The maintainer accepted all three.

IMPLEMENTATION, and the surface is wider than "add four gitignore lines". MEASURED consumers that must
be reconciled:

1. `.gitignore`: add the four paths. Then `git rm --cached` them so they stop being tracked WITHOUT
   deleting the working copies.
2. `check.stale-index` SEMANTICS SHIFT and must be decided explicitly. Emitted by BOTH
   `plans_index.py:277,283` and `research_index.py:469,473`. Its meaning changes from "the committed
   view is current" to "the local view is current". Options: keep it as-is (still meaningful locally);
   downgrade absence to informational while keeping a present-but-stale file an error; or drop the rule
   for these files. Note `doctor.py` consumes it in FOUR places (`:838`, `:1028`, `:1361`, `:1439`),
   so whatever is chosen must not break the doctor's aggregation or its remediation hint ("aw index").
3. `ipd_lifecycle.py:1630-1633` puts both INDEX paths into `owned_paths` for the finalize commit. Once
   untracked, committing them becomes a no-op at best and an error at worst; this list must drop them.
   THIS IS THE SHARPEST EDGE: `aw ipd finalize` is a transaction with a journal and rollback, so a
   path that cannot be committed could wedge it.
4. `status_set.py:823-894,1028` auto-refreshes manifests after a mutation and returns their paths for
   the self-commit. Same treatment: refresh yes, commit no.
5. `artifact_rename.py:63` computes the INDEX paths for a rename's self-commit (jgcm68). Same.
6. THREE DOCUMENTS assert or imply the manifests are committed and must be corrected:
   `.aw/records/plans/README.md`, `.aw/records/research/README.md`, `CONTRIBUTING.md`.
7. `tests/test_auto_index_on_mutation.py` exists specifically to assert the refresh-and-commit
   behavior; it must be updated rather than deleted, so the refresh half stays covered.
8. CI: confirm nothing in CI runs `aw index --check` expecting a committed baseline. If it does, that
   check must either generate first or be dropped.

SEQUENCING NOTE: do the `git rm --cached` in the SAME commit as the `.gitignore` addition, or a
concurrent agent's `aw index` auto-refresh will immediately re-stage them and the change will look like
it did not take.

STILL WORTH CONFIRMING BEFORE EXECUTING, and it is the one thing the repository cannot answer itself:
whether anything OUTSIDE this repo consumes the committed manifests (a dashboard, another repo, a
script). The maintainer has called the decision, so this is a check for breakage rather than a
re-litigation; if an external consumer exists, it needs a migration path, not a veto.

RELATED. `hsixiz` is the broader trackedness question (repo-local-but-untracked `.aw/records`) and may
subsume the direction this sets. `e32j35` (findidx) is the plan whose re-scope removed the speed
argument. Research prompt `nilw5h` covers private-records trackedness.

ORIGINAL FRAMING, kept as the record: this item was filed as an open QUESTION ("should the manifests
stay tracked?") with the evidence above and three middle options (untrack the `.json` but keep the
`.md`; keep both but stop committing per-change; keep as-is and accept the churn). The maintainer chose
to untrack outright rather than any middle option.
