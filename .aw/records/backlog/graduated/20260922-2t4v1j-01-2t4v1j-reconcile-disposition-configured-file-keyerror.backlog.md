- Id: 2t4v1j
- Status: graduated
- Graduated-To: recovone
- Blocks-Release: next
- Set: 2t4v1j
- Priority: high
- Work-Kind: bug
- Summary: oc_runipd.reconcile_disposition raises KeyError('configured_file') where agy and the shared copy return cleanly, on the deliberate-stop path

## Workflow history
- 2026-09-25 graduated (aw set): folded into recovone plan cdxcbh (reconcile_disposition single definition)
- 2026-09-22 created (aw backlog): oc_runipd.reconcile_disposition raises KeyError('configured_file') where agy and the shared copy return cleanly, on the deliberate-stop path

MEASURED 2026-09-23 at HEAD 2d04ef8b while executing IPD gqo6if (runresidue 01). Reported rather than fixed, per that plan's OQ-02: it is an extraction plan whose validation rests on 'no behavior changed', so reconciling a behavioral divergence inside it would make the move unverifiable.

THE DIVERGENCE, reproduced directly:

    item = {'id6': 'abc123', 'position': 1, 'action': 'execute'}   # no 'configured_file' key
    oc_runipd.reconcile_disposition(repo, item, run_dir, 0)   -> KeyError('configured_file')
    agy_runipd.reconcile_disposition(repo, item, run_dir, 0)  -> ('partial', None)
    runner_shared.reconcile_disposition(repo, item, run_dir, 0) -> ('partial', None)

The oc copy indexes `item['configured_file']` directly; agy and the shared copy both use
`item.get('configured_file', '')`. The two host bodies are otherwise 40 ast.unparse lines each at
0.976 host-token-normalised similarity, and the ONLY code differences are these two subscripts.

WHY IT MATTERS, and why it is filed as a bug rather than a tidy-up. The raise is NOT in the
review branch (that one is wrapped in a broad `except Exception`); it is on the main path, which
has no `try`. `runner_shared.dispatch_turn` calls it from inside the deliberate-stop handlers
(`except runner_stop.StopNowForce` and `except runner_stop.StopAtCheckpoint`, both
`item['status'], _ = reconcile_disposition(repo, item, run_dir, 1)` immediately before a bare
`raise`), so on the oc host an item missing that key turns an ORDERLY OPERATOR STOP into a
KeyError escaping the stop handler. That is the same failure SHAPE, on the same field, that
runrecon-02 (`fduoj4`) E-01 already fixed once in `reconcile_interrupted`, whose recorded
finding was that oc 'raised KeyError past an except DriverError that does not catch it and
abandoned the whole crashed queue before save_state, while agy reconciled it'. The fix there was
to share the symbol; the same class of defect survived in its sibling.

A THIRD COPY EXISTS AND IS DEAD. `runner_shared.reconcile_disposition` is a full implementation
that neither host reaches: `dispatch_turn` binds `getattr(driver_module, 'reconcile_disposition',
globals().get(...))`, so the host copy always wins. `python3 tools/runner_fork_scan.py --triples`
names it. So there are three bodies to keep in step, the shared one is unreachable, and it is
NOT equal to the copies in use.

SUGGESTED FIX: make both hosts thin wrappers over the shared implementation (the sanctioned
`818uru` OQ-02 form), after first reconciling the shared body against the two live ones, since it
has drifted further than the subscript (it routes through `read_recorded_outcome` and
`outcome_precedence_disposition` where the host copies inline that logic). That reconciliation is
a behavior question about which body is correct, which is why it needs its own plan and a
maintainer decision rather than being absorbed into an extraction.
