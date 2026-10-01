- Id: kinyxf
- Status: open
- Blocks-Release: next
- Set: brokenpipe
- Priority: low
- Work-Kind: bug
- Summary: aw find, aw paths and human output dump a BrokenPipeError traceback on a closed pipe, contradicting the output contract's clean-exit promise

## Workflow history
- 2026-10-01 created (aw backlog): aw find, aw paths and human output dump a BrokenPipeError traceback on a closed pipe, contradicting the output contract's clean-exit promise

MEASURED 2026-10-01 at HEAD 74b301435 while authoring plan okiso1 from backlog item wdazvp.

docs/cli-output-contract.md Section 7 promises: 'Broken Pipes: All handlers catch BrokenPipeError / EPIPE when writing to stdout and exit cleanly without dumping Python stack traces.' Three of aw find's four surfaces break that promise, and so does aw doctor and aw search --paths.

MEASURED, each piped into head -2 with stderr captured:

    python3 -m agent_workflows find plans --agent  -> exit 120, 1050 bytes of stderr, 2 BrokenPipeError lines
    python3 -m agent_workflows find plans --paths   -> exit 120, 1050 bytes of stderr, 2 BrokenPipeError lines
    python3 -m agent_workflows find plans           -> exit 120, 1241 bytes of stderr, 2 BrokenPipeError lines
    python3 -m agent_workflows find plans --json    -> exit 0, no stderr, no traceback
    python3 -m agent_workflows doctor               -> exit 120, 2 BrokenPipeError lines
    python3 -m agent_workflows search plans Scope-Paths --paths -> exit 120, 1 BrokenPipeError line

The traceback terminates at cli._run_find's bare 'print(p)' inside the bare-path loop. The --json case is clean because renderers.BaseRenderer.emit wraps its write in 'except (BrokenPipeError, OSError): pass'; every surface that prints directly rather than through a renderer is exposed.

WHY IT IS A BUG AND NOT A CHORE: the harm is user-perceptible and the contract is explicit. 'aw find plans | head' and 'aw doctor | less' are the exact invocations a human types, and they produce a Python traceback plus exit 120 instead of a clean exit. Per AGENTS.md a live bug gates the next release, hence Blocks-Release: next.

SCOPE NOTE, so this is not confused with a sibling: plan okiso1 incidentally fixes the --agent case ONLY, as a side effect of routing that surface through BaseRenderer.emit, and it explicitly declines to touch the other surfaces because each bare print loop carries its own byte-identity bar. This item therefore covers find --paths, find's human path, doctor, and search --paths, which okiso1 leaves as found.

THE FIX IS NOT ONE LINE AND THE DECISION IS WHERE IT LIVES. Candidates: (a) a shared guarded line-writer every bare print loop calls, which is the honest fix and requires finding every such loop (a census, not a grep for one symbol); (b) a top-level handler in cli.main that catches BrokenPipeError and exits 0 after the conventional 'os.dup2(os.open(os.devnull, O_WRONLY), sys.stdout.fileno())' dance, which is cheap and uniform but swallows the distinction between a closed pipe and a genuine write failure; (c) wrap each loop individually, which leaves the next loop exposed. Related: wdazvp (the token-control defect on the same branch) and plan okiso1.
