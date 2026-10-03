- Id: cn5np0
- Status: done
- Graduated-To: exitcontract
- Set: cn5np0
- Priority: medium
- Work-Kind: chore
- Summary: Nothing validates a command's declared exit_contract against the exit code it actually returns

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD 1mnit8 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-exitcontract-01-1mnit8-make-exit-contract-load-bearing-a-tree-wide-usage-error-floo.ipd.md); evidence .aw/records/plans/executed/20260930-exitcontract-01-1mnit8-make-exit-contract-load-bearing-a-tree-wide-usage-error-floo.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 1mnit8
- 2026-09-29 created (aw backlog): Nothing validates a command's declared exit_contract against the exit code it actually returns

command_surface.CommandDeclaration.exit_contract is described by its own docstring as part of the 'Normative contract declaration for a single CLI command or parser leaf', and every leaf in COMMAND_INVENTORY declares one. NOTHING COMPARES IT TO REALITY. Measured 2026-09-29: exit_contract is referenced in exactly ONE place in the whole test tree, tests/conformance_matrix.py's required_scenarios, and only to decide whether a domain_failure scenario is required ('if 1 in decl.exit_contract and decl.command_class in (read, check, bare)'). Neither test_cli_conformance_matrix.py nor test_cli_quality_gates.py reads it at all. CONSEQUENCE, MEASURED RATHER THAN HYPOTHESIZED: aw ipd board declared (0, 2) while its human no-project path returned 3, and aw next declared (0, 1, 2) while returning the same 3. That divergence survived two plans (rkn8ya, quqyc4) and a backlog round trip (5x195l -> c6vs7y) because no test could see it. THE HARD PART IS NOT THE ASSERTION, IT IS THE COVERAGE: a general gate needs a live-executable invocation per leaf, and the conformance harness explicitly does not have one (it marks mutations, installers and network verbs covered_by='declaration' and never runs them). Eight declarations also legitimately sit outside 0/1/2 (see 858lhj), so a naive subset assertion fails immediately. LIKELY SHAPE: extend LIVE_SAFE_LEAVES coverage so every live-executed scenario asserts its observed exit code is a MEMBER of the leaf's declared exit_contract, which turns the declaration load-bearing for the safe subset without needing to execute mutations. RAISED BY plan rwvzqm, which pinned exactly TWO verbs (next, ipd board) and recorded in its test docstring that the narrow scope is deliberate.
