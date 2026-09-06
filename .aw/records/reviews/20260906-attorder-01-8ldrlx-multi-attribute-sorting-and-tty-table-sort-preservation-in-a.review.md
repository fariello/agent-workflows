# Review: Multi-attribute sorting and TTY table sort preservation in aw attention

- Subject-Id: 8ldrlx
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: antigravity/gemini-2.5-pro
- Verdict: REVIEWED

## Round 1

Reviewed at HEAD `7c7f18c2`; the plan was committed and unchanged, so no pre-review snapshot was needed. Author-phase `aw ipd lint` returned clean and verified, and so did the `review-finalize` checkpoint after revisions.

The plan addresses a critical defect in `aw attention` / `aw next` interactive terminal usage: `render_table()` was silently clobbering user-specified `--order-by` flags by unconditionally re-sorting rows with a hardcoded sort key. Expanding the vocabulary to cover table columns (`readiness`, `oqs`, `rqs`) and filesystem timestamps (`ctime`, `mtime`), along with comma-separated multi-attribute sorting, makes the sort feature complete and intuitive.

Five findings were identified and repaired in place:
1. Handling non-existent files gracefully in `ctime`/`mtime` sort key resolution (PR-001).
2. Argparse validation for comma-separated tokens in `cli.py` (PR-002).
3. Explicit direction semantics for all attributes (PR-003).
4. Default behavior preservation in `render_table()` when `order_by` is default `class` (PR-004).
5. Explicit execution contract in the approval gate (PR-005).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing and verification | `tests/test_next_ordering.py:228-234` | **`test_all_four_names_agree_under_order_by` iterates over `A.ORDER_KEYS` and will crash on synthetic test items lacking files on disk.** Calling `Path.stat()` without handling missing files causes `FileNotFoundError`/`OSError`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-06. E-03 and F-6 updated to require `try...except OSError` returning `(_ABSENT, 0)`. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `agent_workflows/cli.py:3374` | **`cli.py` restricts `--order-by` via `choices=_attention_order_keys()`, which rejects comma-separated composite keys before execution.** | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | FIXED 2026-09-06. E-02 updated to specify a custom parser/validator in `cli.py` verifying each token against `_attention_order_keys()`. |
| PR-003 | MEDIUM | IN-SCOPE | F. KISS, principles, and UX | `agent_workflows/attention.py:502-537` | **Sort direction semantics were unspecified for new attributes.** Ascending vs descending order must be defined deterministically. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-06. E-03 updated to specify exact direction semantics per attribute. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture and operability | `agent_workflows/attention.py:1625-1633` | **`render_table()` sort bypass condition was ambiguous regarding the default `class` order.** | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-06. E-01 clarified to preserve default table sorting when `order_by` is absent or `A.ORDER_CLASS`. |
| PR-005 | LOW | UNDER-SCOPE | G. Plan executability | `.aw/records/plans/pending/20260906-attorder-01-8ldrlx...ipd.md:130-134` | **Approval and execution gate lacked the standard explicit execution contract.** | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXED 2026-09-06. Added the complete standard execution contract to the Approval and Execution Gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `--order-by` handle missing files during `ctime`/`mtime` stat lookups? | Catch `OSError` and return `(_ABSENT, 0)` so missing files sort last without error. | Let `OSError` propagate (rejected: crashes in synthetic tests or on dangling records). Pre-filter existing files (rejected: filtering violates "ordering never filters"). | `attention.py:496-501` absent-sorts-last rule | yes |
| D-2 | Should `--order-by` support custom ascending/descending prefixes (e.g. `priority:asc`)? | No. Keep standard defaults per attribute and accept simple comma-separated tokens. | Add `:asc`/`:desc` modifiers (rejected: overcomplicates CLI and parser; can be added later if needed). | Rubric F (KISS) | yes |
| D-3 | Should `render_table` re-sort when `order_by` is `class` (default)? | Yes. Preserve the existing default table sort `(type, blocking, priority, name)` when no explicit sort flag is passed. | Never sort in `render_table` (rejected: changes the default table layout when unflagged). | Historical `render_table` contract `attention.py:1589` | yes |

No `Reversible: no` decision was taken in this round. All five findings are `FIXED`, so no finding escalation is required.
