- Id: fe6aro
- Status: open
- Set: fe6aro
- Priority: medium
- Work-Kind: chore
- Summary: host_runner module docstring claims captured output is masked, but redact_worker_output only detects a leak without masking it

## Workflow history
- 2026-10-02 created (aw backlog): filed from mflqqf plan authoring; measured at HEAD 4fbbc8386

Measured at HEAD 4fbbc8386 while authoring plan gqyold (backlog item mflqqf).

agent_workflows/host_runner.py's module docstring says, of the REDACTION bullet, that all captured stdout/stderr/diff pass through security_hardening.check_evidence_redaction and that 'a planted home-path/secret is masked/blocked'.

Reproducing probe, driving the real function:
  raw = RawWorkerResult(exit_code=0, stdout='token=abc /home/<some-user>/x', stderr='', diff='d',
                        changed_files=('a',), timed_out=False, cancelled=False, duration_ms=1.0)
  red, res = redact_worker_output(raw, repo_root=<repo>)
  -> res.ok is False  (the boundary correctly fails closed)
  -> red.stdout still reads 'token=abc /home/<some-user>/x'  (NOT masked)

Mechanism: RedactionPolicy masks sensitive KEYS, and the planted path is a VALUE under the non-sensitive key 'stdout'. The canonical leak sanitizer stage DETECTS it and drives ok=False, but detection is not masking, so the returned text is unchanged.

THIS MAY NOT BE A CODE DEFECT. The function's own docstring states the contract correctly ('the caller must treat that as a failure to record rather than admitting the raw text'), so the BoundaryResult is the fail-closed signal and the MODULE docstring is arguably the thing that overclaims. The decision needed is which to change:
  (a) correct the module docstring to say detected-and-refused rather than masked, or
  (b) make the function mask what the sanitizer detected, so a caller that ignores ok=False still cannot admit raw text.

Why it matters despite the ambiguity: redact_worker_output has ZERO callers today (measured: rg -ln redact_worker_output over the package matches only its own definition), so the first caller written will be written against whichever statement its author reads. If that author reads the module docstring, they may reasonably skip checking ok and assume the text is safe.

Plan gqyold adds the first test caller and PINS the measured behavior (both halves) so the gap is observable, but deliberately does not change host_runner.py, which is outside its declared Scope-Paths.
