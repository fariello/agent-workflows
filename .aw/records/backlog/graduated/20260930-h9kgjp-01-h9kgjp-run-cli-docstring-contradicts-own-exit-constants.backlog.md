- Id: h9kgjp
- Status: graduated
- Graduated-To: runclidoc
- Set: h9kgjp
- Priority: low
- Work-Kind: chore
- Summary: run_cli module docstring contradicts its own exit constants (folds invalid-evidence into 1 while EXIT_INVALID_EVIDENCE is 4; omits 3, 4 and 6)

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: arhzce
- 2026-09-30 created (aw backlog): run_cli module docstring contradicts its own exit constants (folds invalid-evidence into 1 while EXIT_INVALID_EVIDENCE is 4; omits 3, 4 and 6)

`run_cli`'s module docstring Contract block states "exit 1 = incomplete / invalid evidence / unsatisfied requirements", but the constant `EXIT_INVALID_EVIDENCE` declared a few lines below in the SAME module is 4, not 1. The docstring also omits 3 (`EXIT_BLOCKED`), 4 and 6 (`EXIT_OPERATIONAL`) entirely, listing only 0, 1, 2, 5 and 7. So the module disagrees with itself, independently of the two-table divergence tracked by item 858lhj. FOUND BY plan u28vqb (OQ-02) while surveying the exit vocabularies; recorded there as deliberately deferred. WHY NOT FIXED THERE: once u28vqb E-05 documents the run vocabulary in user-facing documentation, the right fix may be to shorten this docstring to a pointer rather than re-transcribe a table, and deciding that is a different question from the one u28vqb answers. Fixing it there would also have widened that plan's Scope-Paths into the one module whose constants it deliberately declined to renumber. LOW RISK: the docstring misleads a code reader only; the adjacent constants are correct and are what every caller imports.
