# wtiso state taxonomy (frozen)

This document FREEZES the classification of every `.aw` state and run path the runner
constructs today. It is the Phase 0 baseline for the wtiso migration (research
`.aw/records/research/20260828-wtiso-00-x03wgn-worktree-isolation-state-model.gpt56.research-report.md`,
Section 2). Every later phase relocates or repairs the paths below; this table says WHICH
phase owns each move, so no artifact can be relocated without a named owner.

Freeze means: the class, namespace, canonical writer, retention class, and migration owner
of each row are fixed as of 2026-08-29 and are checked mechanically by
`tests/test_wtiso_taxonomy_freeze.py`. Changing a row is a deliberate act that must update
that test in the same change.

Line numbers in the Evidence column were verified against the working tree on 2026-08-29.
Treat the SYMBOL NAME as the durable anchor and the line number as a hint: Phases 1 through 6
edit these same modules, so re-verify with `grep -n '<symbol>'` before relying on a number.

## Column vocabularies (closed enums)

The freeze test rejects any value outside these sets.

Class (x03wgn Section 2, five classes):

| Class | Meaning |
|---|---|
| `product` | Versioned repository content. Isolated in a lane, reconciled through Git. |
| `control-authority` | Receipts, lifecycle state, locks, ledgers, integration records, authoritative decisions. Canonical, centrally discoverable, driver-written. |
| `transaction` | Recoverable record for an in-flight mutation. Central, namespaced to the exact attempt, records phase before cleanup. |
| `lane-evidence` | Agent-produced output, proposals, logs, completion claims. Untrusted until imported or independently reproduced. |
| `reconstructible-cache` | Safe to delete and regenerate. |

Namespace (identity scope):

| Namespace | Meaning |
|---|---|
| `project` | One logical project, across clones. |
| `checkout` | One git common directory (all linked worktrees agree). |
| `run` | One driver run. |
| `lane` | One lane within a run. |
| `attempt` | One attempt of one lane. |
| `transaction` | One in-flight mutation transaction. |

Canonical writer:

| Writer | Meaning |
|---|---|
| `driver` | The run driver or a coordinator service it owns. |
| `worker` | The in-lane agent process. |
| `user` | A human, outside any run. |
| `tool` | A third-party tool process (build system, package manager). |

Retention class (x03wgn Section 2, retention table):

| Retention | Meaning |
|---|---|
| `tracked-publish` | Reaches the product or publication candidate and is committed through Git. |
| `local-retain` | Copied to a local artifact store with verified digest and provenance. |
| `secret-local` | Never tracked, never in ordinary logs or bundles. |
| `discardable` | Known cache, temp, or build output covered by an explicit producer rule. |
| `unknown` | Unclassified. Blocks teardown until reclassified. |

Migration owner is the wtiso child id6 that relocates or repairs the row:

| Owner | Phase |
|---|---|
| `8zgybk` | Phase 0, this freeze plus characterization and adversarial tests (no relocation) |
| `qcqhj7` | Phase 1, stop the deadlock and the silent loss (in-lane paths, input manifest, watchdogs) |
| `rchpms` | Phase 2, driver-owned lifecycle authority (driver-created receipts, worker-role refusal, OBSERVED from git) |
| `7p9n2v` | Phase 3, one typed ExecutionContext and PathResolver keyed by git-common-dir |
| `58ha43` | Phase 4, relocate runtime machine state out of the repository |
| `2c122z` | Phase 5, real candidate-merge integration and full crash recovery |
| `1o4eif` | Phase 6, optional OS-sandbox hard enforcement profile |

## Frozen classification table

| Artifact | Current path (as constructed today) | Class | Namespace | Canonical writer | Retention | Migration owner | Evidence (symbol, verified line) |
|---|---|---|---|---|---|---|---|
| Begin receipt (execution authority token) | `.aw/state/ipd-lifecycle/<id6>.receipt.json` | `control-authority` | `checkout` | `driver` | `local-retain` | `rchpms` | `ipd_lifecycle.receipt_path_for`, `agent_workflows/ipd_lifecycle.py:249-251`; dir at `ipd_lifecycle.receipt_dir`, `:244-246` |
| Receipt COPY inside the lane worktree (defect: two authorities) | `<worktree>/.aw/state/ipd-lifecycle/<id6>.receipt.json` | `lane-evidence` | `lane` | `driver` | `discardable` | `58ha43` | `oc_runipd.sync_receipt_into_worktree`, `agent_workflows/oc_runipd.py:470-484` |
| Run tree (state, events, report, decisions) | `.aw/records/runs/<run-id>/` | `control-authority` | `run` | `driver` | `local-retain` | `58ha43` | `oc_runipd.state_root`, `agent_workflows/oc_runipd.py:1162-1163` |
| Run driver lock | `.aw/records/runs/<run-id>/driver.lock` | `control-authority` | `run` | `driver` | `discardable` | `58ha43` | `agent_workflows/oc_runipd.py:740` |
| Per-item outcome JSON written by the worker | `.aw/records/runs/<run-id>/outcomes/<NN>-<id6>.json` | `lane-evidence` | `attempt` | `worker` | `local-retain` | `qcqhj7` | prompt names the absolute main-run path, `agent_workflows/oc_runipd.py:1471` (built at `build_prompt`, `:1448`) |
| Decisions and questions register | `.aw/records/runs/<run-id>/decisions-and-questions.md` | `control-authority` | `run` | `driver` | `local-retain` | `rchpms` | prompt names the absolute main-run path, `agent_workflows/oc_runipd.py:1470` |
| Execution report | `.aw/records/runs/<run-id>/execution-report.md` | `control-authority` | `run` | `driver` | `local-retain` | `rchpms` | prompt names the absolute main-run path, `agent_workflows/oc_runipd.py:1472` |
| Captured host session streams and events | `.aw/records/runs/<run-id>/sessions/`, `events.jsonl` | `control-authority` | `run` | `driver` | `local-retain` | `58ha43` | run tree at `oc_runipd.state_root`, `agent_workflows/oc_runipd.py:1162-1163` |
| Rendered worker prompt | `.aw/records/runs/<run-id>/prompts/` | `control-authority` | `attempt` | `driver` | `local-retain` | `58ha43` | `oc_runipd.write_prompt`, `agent_workflows/oc_runipd.py:1603` |
| Lane worktree directory | `.aw/worktrees/<id6>` | `product` | `lane` | `worker` | `tracked-publish` | `7p9n2v` | `worktree_lease.WORKTREES_SUBDIR`, `agent_workflows/worktree_lease.py:30-32`; lane docstring `oc_runipd.py:455` |
| Lane branch | `aw/lane/<id6>` | `product` | `lane` | `worker` | `tracked-publish` | `2c122z` | `agent_workflows/oc_runipd.py:455`; `agent_workflows/agy_runipd.py:578` |
| Path lease table (in memory only, lost on crash) | in-process, no path | `control-authority` | `run` | `driver` | `unknown` | `2c122z` | `worktree_lease.LeaseTable`, `agent_workflows/worktree_lease.py:144-192` |
| Run ledger store lock | `<ledger-path>.lock` | `control-authority` | `run` | `driver` | `discardable` | `58ha43` | `RunLedgerStore.writer_lock` and `_lock_path`, `agent_workflows/run_ledger_store.py:236`, `:250` |
| Integration validation result (returns True before the merge exists) | in-process, no path | `control-authority` | `attempt` | `driver` | `unknown` | `2c122z` | `agy_runipd.make_integration_validation_runner`, `agent_workflows/agy_runipd.py:644-655` (bare `return True` at `:653`) |
| Tracked plan file under lifecycle | `.aw/records/plans/<state>/<name>.ipd.md` | `product` | `project` | `driver` | `tracked-publish` | `rchpms` | `ipd_lifecycle.finalize`, `agent_workflows/ipd_lifecycle.py:1237`; terminal destination at `:1429` |
| Untracked or ignored local input required by a task | same repo-relative path inside the lane | `lane-evidence` | `lane` | `driver` | `local-retain` | `qcqhj7` | no input manifest exists today; worker launched with bare `--auto`, `agent_workflows/oc_runipd.py:1719` |
| Ephemeral secret materialized for a task | lane-local ephemeral path | `lane-evidence` | `attempt` | `driver` | `secret-local` | `rchpms` | no secret class exists today |
| Dependency and tool caches inside a lane | lane-local (for example `__pycache__`, build output) | `reconstructible-cache` | `lane` | `tool` | `discardable` | `rchpms` | ignored status alone must never authorize deletion (x03wgn Section 7) |
| Finalize transaction journal | does not exist yet | `transaction` | `transaction` | `driver` | `local-retain` | `2c122z` | x03wgn Section 2 requires an attempt-scoped finalize journal; none present |
| Runtime layout migration journal | does not exist yet | `transaction` | `transaction` | `driver` | `local-retain` | `58ha43` | does not exist yet; x03wgn Section 2 requires one migration coordinator, created by the Phase 4 relocation transaction |
| Host capability and sandbox profile snapshot | does not exist yet | `control-authority` | `checkout` | `driver` | `local-retain` | `1o4eif` | does not exist yet; x03wgn Section 4 host capability contract, Phase 6 |

## Notes on rows that are currently misclassified in code

These are the defects Phase 0 pins with characterization tests. The table above records the
TARGET classification; the code does not yet honor it.

1. The begin receipt is `control-authority` with a `checkout` namespace, but a COPY is placed
   inside the lane (`oc_runipd.sync_receipt_into_worktree`), so two authorities can diverge.
   Pinned by `tests/test_wtiso_characterization.py::test_receipt_is_copied_into_lane`.
   Removed by `58ha43`.
2. The outcome JSON is `lane-evidence`, yet the worker is directed to write it to an ABSOLUTE
   path in the main run tree, outside its lane. Pinned by
   `tests/test_wtiso_characterization.py::test_worker_prompt_names_main_run_paths`. Fixed by
   `qcqhj7`.
3. The path lease table is `control-authority` but exists only in memory, so a crash loses
   ownership and resume cannot reconstruct it. Retention is therefore `unknown` today.
   Fixed by `2c122z`.
4. Integration validation is `control-authority` for an irreversible action, but it returns
   `True` before the merged tree exists. Pinned by
   `tests/test_wtiso_characterization.py::test_integration_validation_returns_true_before_merge`.
   Fixed by `2c122z`.
