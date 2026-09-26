- Id: x1za6u
- Status: done
- Blocks-Release: next
- Set: specsread
- Priority: medium
- Work-Kind: bug
- Summary: aw specs check sees ZERO specs in an UNREGISTERED repo, even a flat one, and reports conformance

## Workflow history
- 2026-09-26 done (aw set): DONE: already fixed by 6f59cb53 (y4bdoz, specs._spec_files appends the literal .aw/records/specs root); regression test test_unregistered_flat_repo_is_checked_not_vacuous added in 4b3bafee (fails on 6f59cb53^).
- 2026-09-23 created (aw backlog): Found while executing IPD y4bdoz (specdirs Order 01).

MEASURED 2026-09-23 while executing IPD `y4bdoz`, in a throwaway git repo with NO `.aw/config/project.json` and ONE nonconforming spec at the FLAT root `.aw/records/specs/`: `aw specs check` printed `all specs conform` with unpiped exit 0, `--json` reported `{'checked': 0, 'violations': 0}`, and `check_engine._iter_type_files` returned 1 on the same tree.

THIS IS A SECOND, INDEPENDENT DEFECT from the one `y4bdoz` fixed, and it survives that fix. `y4bdoz` made `specs._spec_files` recursive and ignored-path-aware, which cures a spec hidden by a SUBDIRECTORY. This one needs no subdirectory at all: the root itself is wrong. `_spec_files` resolves its roots through `record_producers.resolve_record_read_paths('specs', target_repo=...)`, and for an UNREGISTERED repo that returns a path under the machine's `AW_HOME` (observed: `<AW_HOME>/projects/<name>-<hash>/records/specs`) rather than the repo's own `.aw/records/specs`. So the reader walks a directory belonging to another project, finds nothing, and the verb reports conformance over zero files.

WHY IT MATTERS BEYOND THE FIXTURE: this is the same fail-in-the-dangerous-direction shape as `y4bdoz`, where a clean verdict is indistinguishable from a genuinely clean tree, and it hits precisely the repos least likely to notice (a fresh clone, a target repo before `aw setup-repo`, any CI checkout that does not carry `.aw/config/`). It also silently weakened `y4bdoz`'s OWN test fixtures until diagnosed: a fixture missing `project.json` returned 0 even WITH the recursive fix, which reads as the fix having failed.

THE CONTRAST POINTS AT THE FIX: `check_engine._type_dirs` adds the LITERAL `.aw/records/<type>` (plus the legacy `.agents/<type>`) alongside whatever the resolver returns, which is exactly why it is correct here. The specs reader should do the same, i.e. include the in-repo literal root unconditionally and keep de-duplicating by resolved path, rather than trusting the resolver alone.

DO NOT FIX THIS BY WIDENING `y4bdoz`: that plan declares `agent_workflows/specs.py` for a READER-RECURSION change and its scope check explicitly forbids opportunistic additions. A cross-reader root-resolution fix needs its own before/after evidence on an unregistered fixture.
