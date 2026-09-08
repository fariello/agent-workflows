- Id: ceauac
- Status: open
- Set: fgendet
- Priority: medium
- Work-Kind: feature
- Summary: Decide whether --follow-generated is wanted and how a generated IPD is detected, before it can be planned: the flag refuses and no detection mechanism exists

## Workflow history
- 2026-09-08 created (aw backlog): SPLIT OUT OF x8diyb 2026-09-08 during graduation. x8diyb carried both spec 25kzda 2.1 runner flags; its --with-dependencies half graduated to plan dhycim (depclosure-01) and this half deliberately did NOT, because the mechanism it needs does not exist. Measured at HEAD fac69fbd: recommended_next_action and files_changed appear only in the prompt text SENT to the agent (oc_runipd.py:4898, :4904; agy_runipd.py:2395, :2401) and are never parsed back; generated_manifest_paths (runner_shared.py:309) is about INDEX merge conflicts; the queue is appended to only at build time (oc_runipd.py:2954, agy_runipd.py:1944). So the work is invent detection, then mutate a deliberately frozen queue, then satisfy spec :945's requirement that a generated IPD resolve its own Item-Dependencies before review-readiness. The combined shape was already REJECTED once: superseded kaygwo E-07 promised both flags and drew NEEDS REPLAN, so graduating this half today would produce a plan whose first E-item is 'invent the missing half'. Filed as a DECISION item rather than a build item: a maintainer should decide whether the behavior is wanted at all, and answer the three recorded questions, before anyone plans it. No Blocks-Release is carried: x8diyb's gate went with the half that is actually being built (dhycim), and gating a release on a behavior nobody has designed would be a gate that cannot be satisfied.

/tmp/opencode/fgbody.md
