- Id: ila6vl
- Status: open
- Set: idxtracked
- Priority: medium
- Work-Kind: chore
- Summary: Decide whether the generated INDEX.json/INDEX.md manifests stay tracked: 328 commits in 14 days, 14 commits existing only to repair drift, byte-deterministic regeneration, and nothing reading the committed copy as an authority

## Workflow history
- 2026-08-31 created (aw backlog): Decide whether the generated INDEX.json/INDEX.md manifests stay tracked: 328 commits in 14 days, 14 commits existing only to repair drift, byte-deterministic regeneration, and nothing reading the committed copy as an authority

QUESTION: should the generated `INDEX.json` / `INDEX.md` manifests stay TRACKED in git, or become
untracked (gitignored) generated views regenerated on demand?

Carried from the 2026-08-31 ASAP checklist (item 15), where it had been repeatedly deferred. It is
worth settling now because the `e32j35` (findidx) re-scope weakened one of the two arguments for
keeping them tracked (see below), so the balance has actually changed rather than merely being revisited.

SCOPE, measured. FOUR tracked manifest files, all generated:
`.aw/records/plans/INDEX.json`, `.aw/records/plans/INDEX.md`,
`.aw/records/research/INDEX.json`, `.aw/records/research/INDEX.md`.

THE CASE FOR UNTRACKING, all measured at HEAD `f1238b2b`.

1. CHURN. In the last 14 days: `plans/INDEX.json` was touched by **328** commits and
   `plans/INDEX.md` by **268** (research: 20 and 19). The plans manifests are among the
   highest-churn files in the repository, and every one of those diffs is derived content.
2. FOURTEEN COMMITS EXIST ONLY TO REPAIR IT. Of the INDEX-touching commits in the last 30 days,
   **14 changed NOTHING ELSE** (measured by checking each commit's full file list for any non-INDEX
   path). Those commits carry no information; they exist because the file drifted from its source.
3. REGENERATION IS BYTE-DETERMINISTIC, so the tracked copy carries no information the tree does not
   already carry. VERIFIED by regenerating twice and byte-comparing both files: identical each time.
4. NOTHING READS THE COMMITTED COPY AS AN AUTHORITY. Grepped every `INDEX.json` reference in
   `agent_workflows/*.py`: the hits are writers, path constants, help text, and the
   `attention_contract` exclusion list that deliberately treats manifests as NON-artifacts
   (`attention_contract.py:165`). No code consults the committed bytes to answer a question.
5. `aw find` MAY NOT NEED IT AT ALL. This is the argument that changed. Plan `e32j35`'s review
   measured a plain filesystem `find -iname` answering the common case in **20ms vs 357ms** and
   re-scoped that plan away from index-first resolution entirely. So the "we need it committed to
   make lookups fast" rationale is weaker than it was when the manifests were introduced.

THE CASE FOR KEEPING THEM TRACKED.

1. `check.stale-index` WORKS BECAUSE THE EXPECTED OUTPUT IS ON DISK. `plans_index.py:270-284`
   builds the manifest in memory and BYTE-COMPARES it against the file, emitting `stale-index` on a
   mismatch. IMPORTANT NUANCE, and the reason this is not a decisive counter-argument: the check
   compares against the file on DISK, not against git, so it needs the file to EXIST, not to be
   COMMITTED. An untracked-but-present manifest would still be checkable; what would be lost is the
   guarantee that a fresh clone HAS one, and the ability to see a manifest change in review.
2. REVIEWABILITY / OFFLINE READING. A tracked `INDEX.md` is browsable on a git host without running
   anything, which is a real convenience for a human skimming the plan corpus from a phone or a PR view.
3. IT IS A CHEAP CACHE FOR A FRESH CLONE. Whoever clones gets a usable manifest immediately rather
   than having to run `aw index` first.

THE MIDDLE OPTIONS worth considering rather than a binary choice.

- UNTRACK THE `.json`, KEEP THE `.md`. The JSON is the machine view (highest churn, never read as an
  authority) while the MD is the human-browsable one. This kills most of the churn and keeps the one
  benefit a human actually uses.
- KEEP BOTH TRACKED BUT STOP COMMITTING THEM PER-CHANGE. Regenerate on a schedule or at release time
  rather than on every mutation, accepting deliberate staleness between refreshes. Note this would
  make `check.stale-index` fire constantly, so the rule would have to change with it.
- KEEP AS-IS AND ACCEPT THE CHURN, on the grounds that 14 repair commits over 30 days is a low price
  and the auto-refresh on mutation (`status_set.py:842,877,1028-1044`, tested by
  `tests/test_auto_index_on_mutation.py`) already keeps drift mostly at bay.

WHAT TO SOLVE FOR, not prescribed here.

- Does anything OUTSIDE this repo consume the committed manifests (a dashboard, another repo, a
  script)? If so, untracking is a breaking change for that consumer and the answer is probably no.
  This must be checked before deciding, and it is the one question the repository itself cannot answer.
- If untracked, what guarantees a manifest EXISTS when a tool wants one? Options: generate lazily on
  first use, generate in `aw setup`, or have `aw check` treat absence as informational rather than drift.
- What happens to `check.stale-index`? It stays implementable against an untracked file (it compares
  to disk), but its meaning shifts from "the committed view is current" to "the local view is current",
  which is a weaker and arguably less useful claim.
- Does the same answer apply to the RESEARCH manifests? Their churn is an order of magnitude lower
  (20 vs 328 commits), so the cost-benefit differs and a split answer may be correct.

RELATED. `e32j35` (findidx) is the plan whose re-scope weakened argument 5 above and should be read
before deciding. `hsixiz` (records backend variant: repo-local-but-untracked `.aw/records`) is the
broader version of this same trackedness question and may subsume it. There is also a standing research
prompt on private-records trackedness (`nilw5h`) whose result may inform this.

NOTE ON PROVENANCE: this item is the durable home for a question that had been living in a gitignored
scratch checklist, which is exactly the anti-pattern `AGENTS.md` warns about (committed backlog kept in
prose "where the attention view cannot see it").
