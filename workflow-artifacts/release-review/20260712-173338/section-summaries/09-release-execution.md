# 09-release-execution per-phase report (rung C, full release)

- Prep: CHANGELOG.md + DECISIONS D74 (first-PyPI-is-1.2.0 rationale + registered maintainer
  protestation); committed 5a00c00.
- Validation on the release commit: full suite 215 passed; gitleaks 239 commits, no leaks.
- Push: origin/main 1995207..5a00c00 (fast-forward). CI verified GREEN on 5a00c00 (all 9 matrix
  jobs unittest 3.9/3.13 x 3 OS + wheel build x 3 OS + secret-scan). The A5 fix confirmed: `build`
  now installed in the unittest job so the packaging gate runs.
- Tag: annotated v1.2.0 on 5a00c00; pushed to origin (8ff327d). Resolver now reports exactly 1.2.0.
- Build: wheel + sdist from the clean tag -> agent_workflows-1.2.0 (not devN); twine check PASSED;
  wheel embeds 1.2.0, bundles workflows, NO dev/meta leak.
- GitHub Release: created as a DRAFT for v1.2.0 with both artifacts attached (isDraft=true). The
  human publishes the draft (D71 default: never auto-publish a GitHub Release).
- STOPPED before PyPI: twine upload is irreversible + credentialed; handed off to the maintainer
  (their explicit choice). Exact command provided.
- Not done: PyPI publish (handed off); publishing the GitHub Release draft (human action).
