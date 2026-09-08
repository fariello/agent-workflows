- Id: 8kttqq
- Status: open
- Set: testignore
- Priority: medium
- Work-Kind: bug
- Summary: test_reporting_contract parity test walks GITIGNORED directories, so any local agent dump (e.g. opencode-recovery/) fails the suite on a clean tree

## Workflow history
- 2026-09-08 created (aw backlog): test_reporting_contract parity test walks GITIGNORED directories, so any local agent dump (e.g. opencode-recovery/) fails the suite on a clean tree

FOUND WHILE GRADUATING AN UNRELATED BATCH of backlog items (2026-09-08), when a bare
`python3 -m pytest` on `main` reported `1 failed, 5865 passed` with the failure in a test that has
nothing to do with the change under test. Filed because it costs every future agent the same
investigation and can make an unrelated change look like it broke the suite.

THE FAILING TEST:
`tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`

WHAT IT DOES. It searches for the sentence `"Report to the user concisely."` across the tree and
asserts it appears ONLY in four allowed files (`agent_workflows/reporting_contract.py`, `AGENTS.md`,
`CLAUDE.md`, `GEMINI.md`), so that nobody maintains a fifth independent copy of the reporting contract.
The INTENT is right and the test is valuable.

THE DEFECT. It walks `REPO_ROOT.rglob("*")` and filters with a HARDCODED prefix skip list, at
`tests/test_reporting_contract.py:651-655`:

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in (".py", ".md"):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith((".git/", ".aw/records/", ".aw/worktrees/", "tests/")):
            continue

It NEVER CONSULTS GITIGNORE. So any gitignored local directory containing `.md` or `.py` files that
happen to quote the contract sentence fails the test, even though nothing in the repository is wrong and
nothing is tracked.

THE MEASURED INSTANCE. A local agent-session dump directory `opencode-recovery/` (1746 files, created
2026-09-08 16:51) holds per-session `.prompt.md`, `.restart.md` and `.transcript.md` files. Those
transcripts contain the agent's own system prompt, which INCLUDES the reporting contract, so 189 of them
matched and the assertion listed all 189. `opencode-recovery/` is gitignored at `.gitignore:49` (proven:
`git check-ignore -v opencode-recovery/` -> `.gitignore:49:opencode-recovery/`) and `git ls-files
opencode-recovery` returns ZERO tracked files.

PROOF IT IS ENVIRONMENTAL AND NOT A REPOSITORY DEFECT. With the directory temporarily moved aside,
`python3 -m pytest tests/test_reporting_contract.py -o addopts=""` -> `53 passed in 17.33s`. With it
present, that one test fails. Nothing tracked changed between the two runs. The directory was restored
immediately (1746 files verified back in place); it belongs to another party and was not deleted.

WHY THIS IS WORTH FIXING RATHER THAN TOLERATING. The failure is INHERENTLY MISLEADING: it appears in a
bare suite run, which is the exact command this repository's execution contract tells every agent to run
and to paste, and it names a test about the reporting contract, so an agent will reasonably suspect its
own prose edits. It also scales badly: the dump grows per session, so the assertion output was ~15KB of
paths, burying any real finding. And it is a FALSE NEGATIVE risk in the other direction too, since a
reader who learns to dismiss this test will dismiss a genuine fifth copy.

SUGGESTED FIX (one small change, no behavior change to the contract itself): make the walk respect
gitignore rather than extending the hardcoded prefix list. The repository already shells out to git
elsewhere, so the cheap and correct version is to enumerate candidates from `git ls-files` (tracked
files only), which is precisely the set the test's intent covers: an UNTRACKED local file cannot be "a
new independently maintained copy" of the contract, because it is not in the repository. That also
removes the need for the `.git/`, `.aw/worktrees/` and similar special cases. If enumerating untracked
files matters, use `git check-ignore` to filter instead. Do NOT simply add `opencode-recovery/` to the
skip list: that treats one symptom and the next gitignored dump reintroduces the failure.

CHECK THE SIBLINGS BEFORE CLOSING: `tests/test_reporting_contract.py` may contain other `rglob`-based
parity assertions with the same hardcoded-prefix pattern, and other test files may too. Grep for
`rglob` across `tests/` and fix the pattern rather than the single instance.

NOT A RELEASE BLOCKER: it fails only on a machine that has such a directory, it affects no shipped
behavior, and CI on a clean checkout is unaffected (nothing gitignored exists there). Hence no
`Blocks-Release`.

VERIFY WITH: create a gitignored directory holding a `.md` file containing the sentence
`Report to the user concisely.`, run the test, and confirm it still passes.
