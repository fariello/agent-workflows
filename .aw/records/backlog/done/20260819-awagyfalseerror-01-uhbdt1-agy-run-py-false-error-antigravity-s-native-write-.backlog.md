- Id: uhbdt1
- Status: done
- Set: awagyfalseerror
- Priority: high
- Kind: bug
- Summary: agy_run.py false-ERROR: Antigravity's native write_to_file tool is sandboxed to its brain dir and rejects target-repo paths, so when Gemini creates a new repo file it (correctly) uses run_command but ALSO attempts write_to_file on the same path, which Antigravity rejects -> the turn ends status ERROR (exit 0) even though the work succeeded + committed. Fix: steer Gemini in the exec/audit prompt to write repo files via run_command ONLY (never write_to_file for target paths), or have agy_run.py treat a write_to_file-artifact-path rejection as non-fatal when the intended write already landed via run_command. Observed executing backlog-medhigh-260819 Orders 01 + 07 (both ERROR-but-complete). Makes agy status untrustworthy as a success signal.

## Workflow history
- 2026-08-23 done (aw set): Closed by highpbacklog0822 Set (all child IPDs executed): uhbdt1
- 2026-08-19 created (aw backlog): agy_run.py false-ERROR: Antigravity's native write_to_file tool is sandboxed to its brain dir and rejects target-repo paths, so when Gemini creates a new repo file it (correctly) uses run_command but ALSO attempts write_to_file on the same path, which Antigravity rejects -> the turn ends status ERROR (exit 0) even though the work succeeded + committed. Fix: steer Gemini in the exec/audit prompt to write repo files via run_command ONLY (never write_to_file for target paths), or have agy_run.py treat a write_to_file-artifact-path rejection as non-fatal when the intended write already landed via run_command. Observed executing backlog-medhigh-260819 Orders 01 + 07 (both ERROR-but-complete). Makes agy status untrustworthy as a success signal.
