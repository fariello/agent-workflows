- Id: qtd3lj
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Reconcile benchmark_corpus.load_corpus docstring (claims task_class, seed_id order) with its seed-directory-name order

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T221840Z-2696450: x8p9ek
- 2026-10-23 created (aw backlog): filed by /plan-review of btubm6

benchmark_corpus.load_corpus docstring says 'Returns tasks sorted by (task_class, seed_id) for determinism', but the code sorts corpus_root.iterdir() by p.name (seed directory name). Measured 2026-10-23 at lane HEAD 08a77c338: seeds copied as a_dir (simple_commands) and b_dir (migration) load as task_class order ['simple_commands', 'migration'], not class-sorted. The checked-in fixture corpus names each seed dir after its class, so the two orders coincide there and no current caller can tell them apart. Plan btubm6 pins the CODE's name order as a characterization test. Decide which is the contract: fix the docstring (no behavior change, test stays) or change the sort to (task_class, seed_id) and update btubm6's test. Found by /plan-review of btubm6.
