- Id: a48b4m
- Status: done
- Graduated-To: cleantgt
- Blocks-Release: next
- Set: cleantgt
- Priority: medium
- Work-Kind: bug
- Summary: test_clean_target_recognition setUp fails: _strip_in_target_residue commits nothing after zero-delta install

## Workflow history
- 2026-10-17 done (aw backlog): closed by aw oc run: IPD jl0bv0 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-cleantgt-01-jl0bv0-make-clean-target-recognition-setup-tolerate-a-zero-delta-re.ipd.md); evidence .aw/records/plans/executed/20261016-cleantgt-01-jl0bv0-make-clean-target-recognition-setup-tolerate-a-zero-delta-re.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T212837Z-3381978: jl0bv0
- 2026-10-16 created (aw backlog): test_clean_target_recognition setUp fails: _strip_in_target_residue commits nothing after zero-delta install

Measured at HEAD 2e4e4c671 while authoring plan ki6t17 (backlog 4uw2a6): `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py` reports 7 failed, every test erroring in `setUp` at `_strip_in_target_residue`: `git -C <clean_repo> commit -m 'Clean residue'` exits 1 with stdout 'nothing to commit, working tree clean'. Since `3m8aix` the clean-target install writes nothing into the target, so the helper's `git rm -r --cached .` + `git add README.md` leaves no change to commit. The module's recognition coverage (fnnwj3) is therefore not running at all. Fix: make the residue strip tolerate an empty change (for example `commit --allow-empty` or skip the commit when `git diff --cached --quiet`), then confirm the seven tests pass.
