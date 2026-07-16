# Assess bugs - decisions and assumptions

- Concern/scope: bugs/correctness lens over the PRODUCT code (`agent_workflows/` + the workflow tools),
  framework-as-subject. Workflow PROSE was out of scope (this is a code-defect hunt).
- Method: two parallel read-only lanes (D84 dogfood) - lane 1 engine.py+cli.py, lane 2
  comms/plans/versioning/config/discovery/term/pypi_links + tools. Coordinator synthesized and
  INDEPENDENTLY re-verified the three Medium findings (F4 return 0 vs returncode; F5 newly_created omits
  artifacts; F8 except Exception misses SystemExit) against source before writing the IPD. The
  security-critical surfaces (is_filename_safe, payload-blind parser, ACK table, redaction) were checked
  by live execution in lane 2.
- Verdict rationale: no Blocker/High because the install path is no-clobber + backs up + stages-not-commits
  (writes are safe), and no security control was found bypassable (is_filename_safe verified bypass-free).
  The real defects are exit-code honesty, rollback completeness, and batch isolation - Medium.
- Intentionally NOT proposed as required fixes (Remediation Risk none/not-reachable, not effort):
  F7 (latent UnboundLocalError, unreachable), F12 (dead identical if/elif, cosmetic), F4-versioning
  (bare-tag parse, unreachable given the sole caller). Offered as optional tidy-ups only.
- Assumption: F5's ensurer READMEs are already recorded (they append `[install]` to `installed`), so the
  fix records ONLY the create_setup_artifacts set, avoiding double-recording.
- Open questions for the user: (1) F5 record-scope confirmation; (2) bundle F-tools vs split the
  redaction item; (3) include F7/F12 opportunistically or skip. Leans recorded in the IPD.
