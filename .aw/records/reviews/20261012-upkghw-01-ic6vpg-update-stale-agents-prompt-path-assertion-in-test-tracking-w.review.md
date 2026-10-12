# Review findings: plan ic6vpg

- Subject-Id: ic6vpg
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in the isolated review-sweep lane. The pending plan matched the sealed lane input byte for byte and was committed. `- Kind: child`. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` were clean.

Verified at HEAD: `tests/test_installer.py:2577` `self.assertIn(".agents/prompts/untracked/", out_clean)`; `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_tracking_warning_scan` gives `1 failed, 143 deselected`; `engine.warn_tracking_and_scan` builds `prompts_lane = f"{dirs['prompts']}/untracked/"` and `comms_lane = f"{dirs['comms']}/untracked/"` (`agent_workflows/engine.py:3666-3667`); the only other `.agents/prompts/untracked` assertion is the legitimate `--keep-legacy` case at `tests/test_installed_text_current.py:464`. DEMONSTRATED the fix in-process (no tree edit): a fresh install's output contains both `.aw/records/prompts/untracked/` and `.aw/records/comms/untracked/`, and not `.agents/prompts/untracked/`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E/G (verification) | E-02/V-02 "no new failures versus baseline" with no step capturing a baseline | The "no new failures" bar referenced a baseline nothing in the plan produced. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 captures a bare-suite baseline before E-01's edit; V-02 demands both FAILED node-id lists. |
| PR-002 | LOW | IN-SCOPE | G (execution contract) | plan-review Step 4 contract rules; OQ-01 `Owner: none` | The gate lacked a scope declaration, the honesty rule, and runner versus hand finalize ownership; it also suggested committing the plan file through `aw commit`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate; set OQ-01 owner to `plan author`; recorded the review demonstration in Findings. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Also assert the comms lane? | Yes, as the plan proposes. | Only replace the prompts assertion. | `engine.py:3667` prints `comms_lane` in the same sentence; demonstrated present. | yes |
