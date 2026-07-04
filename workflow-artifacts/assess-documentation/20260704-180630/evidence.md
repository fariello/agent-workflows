# Evidence - assess documentation (20260704-180630)

Read-only assessment. No project files were changed by this run (only this run record
and the IPD were written).

## Files read in full

- `README.md` (225 lines)
- `ARCHITECTURE.md` (375 lines)
- `CONTRIBUTING.md` (75 lines)
- `AGENTS.md` (7 lines)
- `GUIDING_PRINCIPLES.md` (68 lines)
- `.agents/workflows/index.md` (206 lines) - the workflow manifest and by-tool run guide
- `.agents/workflows/assess/assess.md`, `assess/lenses/documentation.md`,
  `assess/templates/{ipd.md,run-report.md,findings.csv}` (workflow being executed)

## Files sampled / heads read

- `prompts/final-release-validation-executable.md`, `prompts/fix-bar.md`,
  `prompts/modular-release-review-instruction-set-generation-prompt.md`,
  `prompts/older-general-qaqc-prompt-library.md` (first 5 lines each, to judge the
  "reusable prompt library" claim and orientation)
- `.agents/workflows/getting-started/getting-started.md` and
  `.agents/workflows/list-workflows/list-workflows.md` (grep for command-form usage;
  both use the correct `/assess <concern>` / `/advise <persona>` forms)

## Commands run (read-only / discovery)

- `git ls-files "*.md"` - documentation surface inventory
- `ls -la`, `ls prompts/`, `ls .agents/plans/` - structure and lifecycle dirs
- `python3 install-workflows.py --help` and `--version` (`20260704-02`) - verified the
  README install-details/versioning section against actual tool output
- `grep -rnE "/(assess|advise)-[a-z]" README.md ARCHITECTURE.md CONTRIBUTING.md
  .agents/workflows/index.md .agents/workflows/getting-started/ .agents/workflows/list-workflows/`
  - located DOC-01 (stale command syntax) precisely at `index.md:87-88`; confirmed
  `/assess-all` is the only legitimate `/assess-*` command form
- Em-dash sweep (`grep -c "\u2014"`) over README, ARCHITECTURE, CONTRIBUTING, AGENTS,
  GUIDING_PRINCIPLES, index.md - all 0
- Counts: `ls assess/lenses/*.md | wc -l` = 29 lenses; `grep -cE "^\| assess-" index.md`
  = 30 (29 lens catalog rows + `assess-all` command); README "Twelve core workflows"
  reconciled against 12 core command rows in the manifest
- `git status --short` - clean before the run

## Notes on sampling

- `prompts/*.md` bodies were not read in full (only enough to classify each file and
  confirm the missing-index gap); their internal prose is out of scope for this run
  (prose style is a separate lens).
- The 29 assess lenses and 7 advise personas were not each opened; the manifest rows and
  spot checks (getting-started/list-workflows) were sufficient to verify command-surface
  documentation accuracy.
