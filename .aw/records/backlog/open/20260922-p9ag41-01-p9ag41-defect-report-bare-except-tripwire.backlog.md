- Id: p9ag41
- Status: open
- Blocks-Release: next
- Set: p9ag41
- Priority: medium
- Work-Kind: bug
- Summary: test_defect_report's bare-except tripwire fails at HEAD: 894d7924 added 'except Exception: pass' inside the defect-report section of runner_shared.py

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan ld8lb3 (finidem). Pre-existing at HEAD 301a1d8f, independent of that plan's Scope-Paths.

MEASURED AT HEAD 301a1d8f, with plan ld8lb3's changes stashed out, so this is NOT caused by that plan:

    $ python3 -m pytest tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code -o addopts=""
    FAILED tests/test_defect_report.py:434: AssertionError

WHAT THE ASSERTION IS. `test_no_bare_except_was_introduced_around_the_new_code` slices
`runner_shared.py` from the marker `# ---- THE DEFECT REPORT` (line 11446) to EOF and refuses
`except Exception:\n        pass` anywhere in that tail. The tripwire exists because that exact
shape is how the spec-edit announcement was once silenced (`st5klo`).

WHERE IT NOW FIRES. `runner_shared.py:16881`, inside `execute_item_core`'s optional
plan-detail banner:

    try:
        from agent_workflows import attention, term as T
        ...
        print(detail_line)
    except Exception:
        pass

Introduced by `894d7924` "Surface plan detail on start, abort on active runs, and display slated
artifacts" (found with `git log -S`). The swallow is plausibly intentional there (a cosmetic
banner must not kill a turn), but it is inside the fenced region, so the guard fires.

WHY IT IS A BUG AND NOT NOISE. A red tripwire that everyone learns to ignore stops being a
tripwire: the next genuine silencing of a defect-report failure will land in a suite that is
already failing this test, and no one will look. Two legitimate fixes exist and the choice is a
judgement call for the owner: (a) replace the swallow with `contextlib.suppress(Exception)`,
which the same file already uses elsewhere for exactly this best-effort intent and which the
AST half of the test permits; or (b) narrow the test's fence so it covers the defect-report code
it names rather than everything to EOF. Do NOT simply delete the assertion.

NOT IN SCOPE FOR ld8lb3: that plan declares `ipd_lifecycle.py`, `oc_runipd.py`,
`agy_runipd.py`, `runner_shared.py` and two test files, and while `runner_shared.py` IS
declared, the swallow is another agent's code serving another purpose, so changing it there
would have been an unrelated opportunistic edit.
