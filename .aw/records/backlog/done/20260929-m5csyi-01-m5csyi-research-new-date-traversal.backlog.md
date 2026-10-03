- Id: m5csyi
- Status: done
- Graduated-To: m5csyi
- Blocks-Release: next
- Set: m5csyi
- Priority: medium
- Work-Kind: bug
- Summary: aw research new interpolates an unvalidated --date into the derived filename, so a traversal in it writes a record outside the records tree; prompts new already refuses this and specs is fixed under qbz8i1

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD iumgvk executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-m5csyi-01-iumgvk-validate-the-research-date-against-the-grammar-it-fills-so-a.ipd.md); evidence .aw/records/plans/executed/20261001-m5csyi-01-iumgvk-validate-the-research-date-against-the-grammar-it-fills-so-a.ipd.md
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: iumgvk
- 2026-09-29 created (aw backlog): aw research new interpolates an unvalidated --date into the derived filename, so a traversal in it writes a record outside the records tree; prompts new already refuses this and specs is fixed under qbz8i1

FILED AS THE CARRIER for the research-tree row in plan `ribg85` (Set `qbz8i1`), which fixes the same defect in `aw specs new` only.

MEASURED 2026-09-29 in a lane at HEAD `f4b00263`, against temporary fixture repositories.

`aw research new <repo> --kind findings --slug x --summary s --date ../../../../ESCAPED --apply` exits **0** and writes `<repo>/.aw/records/research/../../../../ESCAPED-x-00-ul54zx-x.findings.md`, which resolves to a file THREE DIRECTORIES ABOVE the repository root, entirely outside the records tree and outside the repo.

THE FIRST ATTEMPT AT THIS MEASUREMENT WAS A FALSE NEGATIVE AND THE REASON MATTERS. With the fixture at `/tmp/<x>/`, the same traversal exited **2** with `research write failed: [Errno 13] Permission denied: '/tmp/<x>/.aw/records/research/../../../../../ESCAPED'`, because the escape landed on `/` which is not writable. That refusal is an accident of filesystem permissions, NOT a guard: re-running with the fixture nested four levels deep (`<tmp>/a/b/c/repo`) so the escape lands in a writable directory produced exit 0 and the escaped file. Anyone verifying this fix must nest the fixture, or they will "confirm" a guard that does not exist.

THE FIX SHAPE ALREADY SHIPS IN A SIBLING VERB. `prompts.run_new` validates `--date` against `\A\d{4}-\d{2}-\d{2}\Z` and refuses with `aw prompts new: --date must be YYYY-MM-DD (got ...)` at exit 2 BEFORE deriving a name; driven with the same traversal, it exits 2 and writes nothing. So format validation at the verb is established here, not new policy. Plan `ribg85` ports it to `specs.run_new` and additionally argues for a destination-containment assertion at the write; whichever shape that plan lands on should be reused here rather than re-litigated.

NOTE `A.is_safe_descriptive` CANNOT DETECT THIS, which is why it is a separate item from the descriptive-field work in `qbz8i1`/`uz05bl`: driven, `is_safe_descriptive('../../../../outside/pwned')` returns **True**, because a traversal is a single bounded control-char-free line. The defect class is path derivation, not output safety.
