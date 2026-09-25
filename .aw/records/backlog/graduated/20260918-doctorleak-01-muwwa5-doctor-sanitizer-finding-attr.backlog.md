- Id: muwwa5
- Status: graduated
- Graduated-To: doctorleak
- Blocks-Release: next
- Set: doctorleak
- Priority: high
- Work-Kind: bug
- Summary: aw doctor never reports a real leak: probe_sanitizer reads Finding.matched, which does not exist

## Workflow history
- 2026-09-25 graduated (aw set): graduated into doctorleak (plan rpqv4q); verified live at 8e74dcac
- 2026-09-18 created (aw backlog): Found while executing plan 216rgg (setidfix Order 01); unrelated to that plan's scope, filed per the defect-report contract. THE DEFECT: agent_workflows/doctor.py:681 builds each leak Drift with f'{f.severity}: {f.matched}', but leak_sanitizer.Finding declares (location, rule, severity, SNIPPET) and has no 'matched' attribute. The AttributeError is raised inside probe_sanitizer's own try/except, which swallows it and replaces the whole probe's output with ONE generic Drift('<sanitizer>', 'doctor.probe-failed', ...). CONSEQUENCE: aw doctor can never report an actual leak finding, and the failure is indistinguishable from a probe that found nothing, because the generic message is what a reader sees. It is invisible on a clean tree (zero findings means the loop never runs), which is why it survived. REPRODUCED in a throwaway git repo with one planted home-path leak: leak_sanitizer.scan_working_tree returned Finding(location='leaky.md:1', rule='home-path', severity='fail', snippet='home path: ...'), and doctor.probe_sanitizer returned exactly one drift, rule 'doctor.probe-failed', detail "'Finding' object has no attribute 'matched'" -- the leak itself never surfaced. FIX: read f.snippet (and consider truncating it, since a snippet is unbounded and this detail string reaches agent output). The repository's own leak gate is the authority here, so a probe that silently cannot report is worth an error-severity fix plus a regression test with a planted finding; nothing currently tests this loop with a nonempty findings list. Also worth deciding whether probe_sanitizer's blanket except should re-raise programming errors rather than reporting them as probe failures, since that is what hid this.
