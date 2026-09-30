- Id: ma8aig
- Status: open
- Set: defpass
- Priority: low
- Work-Kind: chore
- Summary: Four stale oc_runipd/agy_runipd line citations survive in runner_shared comments, four past EOF

## Workflow history
- 2026-09-30 created (aw backlog): Four stale oc_runipd/agy_runipd line citations survive in runner_shared comments, four past EOF

MEASURED 2026-09-30 at review of IPD gyam7x (F-08), every offset re-resolved independently against the host files at HEAD `f2326296`.

THE DEFECT CLASS. `agent_workflows/runner_shared.py` carries five `<host>.py:<line>` citations in comments and docstrings. A line offset expires as soon as the cited file changes, and four of these have. `oc_runipd.py` is 5278 lines and `agy_runipd.py` is 4162, measured at review.

  runner_shared:16935 -> oc_runipd.py:274    resolves, but to the bare line ')'
  runner_shared:19430 -> oc_runipd.py:6993   PAST EOF
  runner_shared:19430 -> oc_runipd.py:7031   PAST EOF
  runner_shared:22124 -> oc_runipd.py:6645   PAST EOF
  runner_shared:29366 -> oc_runipd.py:6120   PAST EOF  (owned by gyam7x, FIXED there)
  runner_shared:37112 -> oc_runipd.py:2979   resolves, but to the bare line '#'
  runner_shared:37112 -> agy_runipd.py:2094  resolves to an unrelated comment about closures

SCOPE OF THIS ITEM: the four citations gyam7x does NOT fix, namely the two in the comment beginning 'The pre-`pgq326` dispatch branch', the one in `SET_RETIREMENT_DONE_STATUS`'s comment area at :22124, the one at :16935, and the two at :37112. gyam7x fixes only the :29366 one, because that is the sentence its subject matter lives in; the rest are a different sentence each with no shared fix, which is why they were filed rather than swept.

WHY EACH NEEDS ITS OWN WORK. A past-EOF offset is provably wrong but does not say where the code WENT, so each fix requires locating the construct the comment meant (most of it moved into `runner_shared` itself when the host bodies were collapsed) and rewriting the citation by SYMBOL or by a quoted content string, which is what the repository's citation convention requires (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`).

THE OPEN DESIGN QUESTION CARRIED HERE, from gyam7x OQ-01, which deferred it to this item deliberately: should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source? The cheap half is decidable with no judgement (a line beyond the file's length is wrong), and four of the seven resolutions above would have been caught by it. The expensive half is not mechanically decidable at all: the two citations that DO resolve land on ')' and '#', which are wrong in the way that actually misleads a reader and which no length check can see. So the question is whether the cheap half alone is worth a repo-wide rule. Decide it with this sample in hand rather than in the abstract. Note the existing advisory `IPD-C801` covers IPD PROSE only; nothing checks offsets inside Python comments.
