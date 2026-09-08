# Review: sanitized export, explicit submission, and setup wizard controls (child ixis0c, Set runanalytics)

- Subject-Id: ixis0c
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `9b413533`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic review
(exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the nine-item split and the rewritten
V-item bijection.

METHOD, AND IT PRODUCED THE ONLY BLOCKER IN THIS SET SO FAR. This is the plan whose entire purpose is to avoid
making a false privacy guarantee, so the first thing checked was whether the tool it relies on delivers the
guarantee it assumes. It does not, and the gap is not marginal. Every one of the twelve canary categories the
plan's own test section enumerates was fed to `leak_sanitizer.scan_text` individually rather than reasoned about,
and eleven came back empty at fail severity. Four further HIGH findings came from executing the transport,
archive, config and declaration surfaces rather than reading them.

WHAT THE PLAN GETS RIGHT, and on the ethics it is the best-reasoned document in the Set. The three-tier
sensitivity model is genuinely well designed: separating projected metrics from bounded redacted events from raw
artifacts is the right decomposition, and attaching escalating consent to each is correct. Refusing to claim
anonymization unless independently demonstrated is exactly the discipline that keeps a data-sharing feature
honest, and the plan states it unprompted. The enumeration of what submission must never be part of (analyze,
open, export, install, periodic telemetry, cleanup) plus the explicit ban on a background uploader, retry daemon,
tracking pixel, beacon and implicit "improve product" consent is precise and unusually complete. And the
endpoint-contract checklist (operator, TLS, retention, deletion method, contact, duplicate-submission behavior)
is the right list, with the right fallback: if it is not approved, ship export only and make submit report
unavailable. That instinct is what makes the plan salvageable rather than a redesign.

THE BLOCKER IS THAT THE SANITIZER CATCHES ONE OF TWELVE. The plan's required tests demand a bundle contain no
seeded prompt, response, command, path, hostname, username, remote, branch, commit message, environment secret,
high-entropy token, spreadsheet formula or archive-traversal canary, and E-01 asserts the redacted tier "passes
the shared sanitizer". Measured at fail severity: a home path is CAUGHT. The real hostname returns `warn` only.
A git remote, a branch name, a commit message, an `AWS_SECRET_ACCESS_KEY=` assignment, an `sk-proj-` token, a
`=cmd|'/C calc'!A0` formula, a `../../../etc/passwd` traversal, prompt text and a shell command ALL return ZERO
findings. The module's complete fail rule set is `home-path`, `users-path`, `windows-home`, `vc-home`,
`private-repo`, `other-account`, `session-id`, `handle`, plus `ipv4`/`ipv6` which are off unless `ip_enabled`,
and it contains no entropy check, no `AKIA`, no `BEGIN ... KEY`. Secret detection in this repository is
`gitleaks` running in a CI job over git history, which an export code path cannot invoke. So a tier built on that
assertion would be redacted of home paths and nothing else, while telling a user their data was checked. That is
the precise failure this plan exists to prevent, committed by the plan itself, which is why it is a BLOCKER
rather than a HIGH. The fix is not to strengthen the detector (see below) but to invert the design: E-03 now
allowlists event FIELDS structurally and drops everything unnamed, and the shipped sanitizer report must
ENUMERATE the blind spots by name.

A SECOND MEASUREMENT MAKES IT WORSE IN THE PLACE THAT MATTERS MOST. Three of the fail rules (`handle`,
`private-repo`, `other-account`) are compiled from this maintainer's own literal tokens. Verified: another user's
handle and another private repository name both return zero findings, while `home-path` and `session-id` are
generic and do match. So the detector's apparent competence on this box does not transfer to an adopter's, and a
data-sharing feature is weakest exactly where the data is not the maintainer's. The detector is extensible via
repo `fail_patterns` and never-committed user hints, which is the right place to strengthen it, but the shipped
default is narrow and the plan must not present it otherwise.

I DELIBERATELY DID NOT FIX THE DETECTOR, AND THE REASONING IS RECORDED BECAUSE IT IS THE UNCOMFORTABLE CALL.
Adding entropy and secret-shape rules to `leak_sanitizer` would be the tempting remedy, and it is out of scope
here: that module backs `aw sanitize`, an installed pre-commit hook and a CI job, so changing its false-positive
profile is a separate plan with its own risk budget, and doing it inside a feature plan would put a repo-wide
gate change on the critical path of an analytics export. The plan now states this, stops leaning on the detector,
and makes it a STOP-and-raise if structural allowlisting still cannot make a redacted tier defensible.

THE TRANSPORT AS SPECIFIED WOULD HAVE BEEN AN EXFILTRATION PRIMITIVE. The plan promises submit "rejects
unapproved schemes/hosts, redirects outside policy" and names no mechanism. Measured by execution: the stdlib
default opener's handler chain includes `HTTPRedirectHandler`, `FileHandler`, `DataHandler` and `FTPHandler`;
`urlopen("file://<path>")` returned the file's contents and `urlopen("data:text/plain,hello")` returned its
payload. So a scheme check on the CONFIGURED url cannot survive a 302 to `file:///etc/passwd`, and a submit
command becomes a local-file reader. A restricted `OpenerDirector` with only `HTTPSHandler`,
`HTTPDefaultErrorHandler` and `HTTPErrorProcessor` does refuse `file://`, though with a bare `AttributeError`
that must be wrapped. The good news is that two correct precedents already ship: `oc_models._scheme_ok` gates
credential transmission on https with a loopback exception, and `oc_models.http_fetch_json` sends a bearer header
"never echoed anywhere" with a blanket failure path.

THE ARCHIVE DEFENSE CANNOT USE THE OBVIOUS API. `requires-python` is `>=3.9` and CI tests 3.9 through 3.14.
`tarfile` extraction filters (PEP 706) arrived in 3.12 and were backported only to 3.9.17+, so on a 3.9.0-3.9.16
interpreter `tarfile.data_filter` is absent and `extractall` is unsafe by default. And there is no archive
precedent anywhere in the package: the only `zipfile` use is `leak_sanitizer` reading a built wheel, with no
`tarfile` import, no `extractall`, no `make_archive`. Every defense is greenfield and must be feature-detected
with a working fallback.

THE ENDPOINT CONFIGURATION WOULD HAVE SILENTLY VANISHED. The plan says to use the existing user-local config
helpers. Measured by round trip: `config.normalize()` rebuilds its output from `default_config()` against
`_ALLOWED_TOP_KEYS` of exactly `{config_version, repos, defaults, aw_home}`, and an added `analytics_endpoint`
key did not survive. This is the third time this Set has hit that trap (Order 03's review found it for a
telemetry key), and the repository's own documented workaround sits at `review_findings_gate`, read from
`.aw/config/project.json` "and NOT via the XDG user config (which drops unknown keys)". But endpoint and auth are
machine-local rather than committed policy, so the right home is the gitignored `.aw/config/local.json`. There is
a pleasing symmetry worth recording: Order 02 REJECTED that file for its cryptographic salt precisely because it
is "a user-facing configuration surface whose keys the setup wizard manages", and that same reasoning ARGUES FOR
it here, because an endpoint is exactly a user-facing setting a human should see and edit.

ONE FINDING WHERE THE PLAN PROPOSED A PATTERN THIS REPOSITORY DELIBERATELY REMOVED. The plan requires "an
every-time interactive confirmation" for raw export. Spec `20260815-0151-01-honest-human-approval-attestation` is
`Status: implemented` and did the opposite transition for spec approval: it REPLACED a `sys.stdin.isatty()`
requirement plus a typed confirmation with `--by-human`, an explicit non-TTY attestation, reasoning that "an
executing agent has no TTY, so it can NEVER record an approval, even one the human explicitly gave in chat", and
that nothing should require asserting "I am human". A TTY-gated consent model would reintroduce the retired
friction and make the feature unusable from an agent shell, which is how this repository is actually driven. The
consent model is now an attested flag naming tier and destination, with `--yes` explicitly insufficient.

TWO SMALLER CORRECTIONS. The plan's "analytics tooling is installed only when selected if packaging supports
optional feature installation" is incoherent: eighteen `run_analytics_*.py` modules appear across the siblings'
`Scope-Paths`, all inside `agent_workflows/`, the only declared extra is `test`, and no optional-feature
mechanism exists, so the code ships regardless and the wizard can gate ENABLEMENT only. And the two new leaves
need `CommandDeclaration`s while `command_surface.py` was undeclared, the identical gap Order 08's review found,
compounded by the same invisibility: the gate is `pytest.mark.slow` and the bare suite this plan requires
deselects it.

ON SIZING. Three E-items spanning three genuinely distinct trust surfaces, which the Set orchestrator `5lxvl3`'s
own open question already names: "Order 09 spans three different trust surfaces in three items where the
transport and the consent model each deserve their own pass". Local bundle tiers, network transport and
interactive consent share a boundary but nothing else. Ninth sibling split for the same reason, and the ninth
consecutive gate carrying no execution contract.

WHY APPROVE WITH REVISIONS DESPITE A BLOCKER. The Fix Bar turns on Remediation Risk, not severity. The blocker's
remedy is bounded and local: invert E-03 from detector-dependent to structurally allowlisted, and require the
report to publish the blind spots. That is Medium risk with a clear verification path, well below the
Medium-High threshold that would justify deferral, and it does not require a human decision. All four open
questions were settled by measurement or by reading an implemented spec, and each is recorded as a decision with
its rejected alternatives. No finding is left OPEN or DEFERRED, so nothing needs escalation as a blocking
question.

ONE NOTE FOR THE MAINTAINER, spanning plans. The detector's coverage gap is worth its own backlog item
independent of this Set. Right now `aw sanitize` reports clean on a git remote, a branch name, a commit message,
an AWS key assignment and an `sk-proj-` token, and three of its fail rules only work on the maintainer's own
machine. That is fine for its original job (keeping maintainer identity out of tracked files) and is a real gap
for any adopter, and this plan is the first consumer that would have taken it for more than it is.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-103 | BLOCKER | IN-SCOPE | B. security and privacy; E. testing | ran `scan_text` at fail and warn severity over each of the twelve canary categories; enumerated every rule name; grepped for entropy/secret detection | **THE SANITIZER CATCHES ONE OF THE TWELVE CANARY CLASSES THIS PLAN'S OWN TESTS DEMAND.** Home path CAUGHT; hostname `warn` only; git remote, branch, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd\|` formula, `../../../etc/passwd`, prompt text and shell command ALL zero findings. No entropy or secret-shape rule exists; `gitleaks` provides that in CI over git history, uncallable from an export path. A tier asserting "passes the shared sanitizer" ships a false privacy guarantee on the one plan whose purpose is to avoid making one | C:Medium; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-03 inverted to a STRUCTURAL field allowlist dropping everything unnamed, with the detector demoted to corroboration; the shipped sanitizer report must ENUMERATE the blind spots by name; V-03 requires per-canary structural exclusion AND the measured detector coverage pasted; the required-tests section rebuilt around structural assertions; a stop condition forbids the "passes the sanitizer" claim; OQ-01/D-1 records it |
| PR-104 | HIGH | IN-SCOPE | B. security and privacy | scanned a different user's handle, private repo name, session id and home path; read the pattern construction | **THREE FAIL RULES ARE COMPILED FROM THE MAINTAINER'S OWN TOKENS, SO THE GATE IS WEAKEST ON AN ADOPTER'S MACHINE.** `handle`, `private-repo` and `other-account` are literal maintainer identifiers returning zero findings for another user, while `home-path` and `session-id` are generic. The detector's competence here does not transfer, which is backwards for a data-sharing feature | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | A conventions bullet records the measurement and that the detector is extensible via repo patterns and user hints while its SHIPPED default is narrow; E-03's structural allowlist is what makes the tier safe for a non-maintainer; the documentation obligation requires stating what is checked and what is not |
| PR-105 | HIGH | IN-SCOPE | B. security (SSRF/exfiltration) | built the default opener and listed handlers; opened a `file://` and a `data:` url successfully; built a restricted opener and observed the refusal shape | **THE STDLIB DEFAULT OPENER IS AN EXFILTRATION AND SSRF SURFACE AND NO MECHANISM WAS NAMED.** The default chain includes `HTTPRedirectHandler`, `FileHandler`, `DataHandler`, `FTPHandler`; `urlopen("file://<path>")` returned file contents and `urlopen("data:...")` its payload. A scheme check on the configured url cannot survive a 302 to `file:///etc/passwd`, turning submit into a local-file reader | C:Medium; U:Low; S:High; F:Medium; Overall:Medium | FIXED | New E-06 requires a restricted `OpenerDirector` (https only, no file/data/ftp) plus a refusing redirect handler with the bare `AttributeError` wrapped, following the existing `oc_models._scheme_ok` and never-echo-the-token precedents; V-06 requires each hostile target and redirect refused AND the assertion shown failing against a naive `urlopen`; the fence and a stop condition forbid a bare `urlopen` |
| PR-106 | HIGH | UNDER-SCOPE | B. security (archive); C. compatibility | read `requires-python` and the CI matrix; grepped the package for every archive API; confirmed the filter backport history | **ARCHIVE SAFETY CANNOT USE THE OBVIOUS API ON THE DECLARED FLOOR.** `requires-python` is `>=3.9` with CI on 3.9; `tarfile` filters landed in 3.12 and were backported only to 3.9.17+, so `tarfile.data_filter` is ABSENT on 3.9.0-3.9.16 and `extractall` is unsafe by default. There is also NO archive precedent in the package (only `leak_sanitizer` reading a wheel), so every defense is greenfield | C:Medium; U:Low; S:High; F:Medium; Overall:Medium | FIXED | New E-05 requires per-member validation (absolute path, `..`, symlink, hardlink, device, duplicate) BEFORE any write, with `tarfile.data_filter` feature-detected and the fallback implemented; V-05 requires each hostile class refused and the fallback exercised; the fence forbids relying on `filter="data"` |
| PR-107 | HIGH | IN-SCOPE | C. operability; A. data integrity | round-tripped an `analytics_endpoint` key through `normalize()`; read `_ALLOWED_TOP_KEYS` and the `review_findings_gate` comment; confirmed `local.json` is gitignored and schema-parsed | **THE ENDPOINT CONFIGURATION WOULD BE SILENTLY DISCARDED.** `config.normalize()` rebuilds from `default_config()` against a four-key allowlist and the added key did NOT survive, so "use the user-local config helpers" produces a setting that vanishes on save. Third occurrence of this trap in the Set (Order 03 hit it for a telemetry key) | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | E-09 requires persistence in the gitignored `.aw/config/local.json` with the auth SOURCE stored as an environment variable name and never the secret; V-09 requires a surviving round trip AND the same test failing against the XDG config; the fence forbids the XDG location; OQ-03/D-3 records it, noting Order 02's rejection of `local.json` for a salt argues FOR it for a user-facing endpoint |
| PR-108 | MEDIUM | IN-SCOPE | F. UX; Honest documentation | read spec `20260815-0151-01` (status, problem statement, G1-G4); found the fail-closed confirm helper in `cli.py` | **"EVERY-TIME INTERACTIVE CONFIRMATION" IS THE PATTERN THIS REPOSITORY DELIBERATELY REMOVED.** That implemented spec replaced a `sys.stdin.isatty()` plus typed-confirmation floor with `--by-human`, a non-TTY attestation, because an executing agent has no TTY and can never record an approval the human gave in chat, and because nothing should require asserting "I am human". A TTY gate would make the feature unusable from an agent shell | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | New E-08 makes consent an explicit attested flag naming tier and destination, honored regardless of TTY, refused when absent, recorded with provenance, with `--yes` explicitly insufficient; V-08 requires the non-TTY refusal and attribution pasted; a stop condition forbids a TTY gate; OQ-04/D-4 records it |
| PR-109 | MEDIUM | UNDER-SCOPE | G. executability | called `find_undeclared_leaves` on the real parser; counted the gate vocabulary; read the test's `slow` marker | **TWO NEW LEAVES NEED DECLARATIONS AND THE FILE THAT HOLDS THEM WAS UNDECLARED.** 129 declarations exist and `find_undeclared_leaves` is asserted EMPTY by a test that is `pytest.mark.slow`, so the bare suite this plan requires DESELECTS it. Same gap Order 08's review found. Both leaves also MUTATE on a noun documented as the READING half | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-01 owns the declaration contract with a `mutation_gate` drawn from the measured four-value vocabulary; `command_surface.py` and `tests/test_cli_conformance_matrix.py` added to `Scope-Paths`; the five `oc profile *` entries pinned as pre-existing baseline and fenced out; the gate and required tests demand the explicit conformance run |
| PR-110 | MEDIUM | OVER-SCOPE | F. KISS; Honest documentation | collected every analytics module path from the Set; read `[project.optional-dependencies]`; searched the installer for extras handling | **"INSTALLED ONLY WHEN SELECTED IF PACKAGING SUPPORTS OPTIONAL FEATURE INSTALLATION" IS INCOHERENT.** Eighteen `run_analytics_*.py` modules live inside `agent_workflows/`, the only declared extra is `test`, and no optional-feature mechanism exists, so the code ships unconditionally. The conditional phrasing invites building a mechanism that should not exist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 replaces the optional-install claim with an ENABLE/DISABLE claim; a conventions bullet records that all analytics code ships in-package; a stop condition forbids building an optional-install mechanism |
| PR-111 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | orchestrator `5lxvl3` OQ-01 read; item content counted against the workflow's split diagnostics | **MECHANICALLY SIZED ACROSS THREE DISTINCT TRUST SURFACES, WHICH THE SET'S OWN OPEN QUESTION NAMES:** "Order 09 spans three different trust surfaces in three items where the transport and the consent model each deserve their own pass". Local bundle tiers, network transport and interactive consent share a boundary but nothing else. Ninth sibling with this finding | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into NINE items across four groups (surface contract / export tiers / transport / consent and lifecycle); `Highest E allocated` 03 -> 09; V-01..V-09 rewritten to bijection; a right-sizing note quotes the orchestrator; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-112 | LOW | UNDER-SCOPE | G. executability; Presentation | plan read; `grep -o` counts before the fix; bare suite run | The gate carried no execution contract (ninth consecutive sibling). Also 22 escaped backtick pairs rendering as literal backslashes plus two smart quotes, and no recorded baseline | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added with a scope fence naming nine measured prohibitions, a concurrent-edit warning for `cli.py`/`command_surface.py`, a never-commit-a-bundle-or-canary rule, the honesty rule with BOTH plan-specific traps named (the slow-marked gate and the misleading clean sanitizer report), re-measure-every-number, and SIX stop conditions; all 22 backticks and both smart quotes cleared (verified zero); baseline recorded (`2 failed, 5655 passed, 3 skipped, 2 xfailed in 56.63s`) with both node ids attributed pre-existing |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What actually establishes the redaction guarantee, given the detector's measured coverage? | A STRUCTURAL field allowlist that drops everything unnamed, with the detector demoted to corroboration whose blind spots are published | Relying on the detector as the gate, rejected because it catches one of twelve canary classes and would ship a tier redacted only of home paths while telling the user it was checked. Extending `leak_sanitizer` with entropy and secret rules, rejected as out of scope for this plan: it backs `aw sanitize`, an installed pre-commit hook and a CI job, so changing its false-positive profile is a separate plan with its own risk budget, and it must not sit on an analytics feature's critical path. Dropping the `events-redacted` tier, rejected because bounded structured events carry the real research value and an allowlist delivers it honestly | per-canary `scan_text` results at fail and warn severity (1 of 12 caught); the complete ten-rule fail set enumerated; no entropy/`AKIA`/`BEGIN KEY` pattern in the module; `gitleaks` confined to a CI job over git history | yes |
| D-2 | How is the transport built, given the default opener resolves `file://` and follows redirects? | A restricted `OpenerDirector` with only `HTTPSHandler`, `HTTPDefaultErrorHandler` and `HTTPErrorProcessor`, plus a redirect handler refusing an out-of-policy target, with the refusal wrapped in an actionable error | Checking the scheme of the configured url only, as the plan implied, rejected because a 302 to `file:///etc/passwd` is followed by the same opener that just passed the check, turning submit into a local-file exfiltrator. Adding a third-party HTTP client, rejected because `pyproject.toml` declares exactly one runtime dependency and two stdlib https callers already model the correct posture (`oc_models.http_fetch_json`, `versioning.latest_pypi_version`) | executed `urlopen` against `file://` (returned contents) and `data:` (returned payload); listed the default handler chain; built the restricted opener and observed it refuse `file://` with a bare `AttributeError` | yes |
| D-3 | Where does endpoint and auth configuration live so it survives a save? | The gitignored `.aw/config/local.json`, with the auth SOURCE stored as an environment variable name and never the secret | The XDG user config, rejected on measurement: `normalize()` rebuilds from `default_config()` against a four-key allowlist and the added key did not survive. `.aw/config/project.json`, rejected because it is COMMITTED portable policy and an endpoint plus auth source is machine-local, so committing it pushes one user's destination onto every clone. Storing a token in any config file, rejected outright | round-tripped an `analytics_endpoint` key through `normalize()` (did not survive); `_ALLOWED_TOP_KEYS`; the `review_findings_gate` precedent comment; `local.json` confirmed gitignored and schema-parsed by `parse_local_binding`; Order 02's OQ-01 reasoning inverted for a user-facing setting | yes |
| D-4 | Is consent an interactive TTY confirmation or an attestation? | An explicit NON-TTY attestation naming tier and destination, honored regardless of TTY, refused when absent, recorded with attributed provenance | The authored "every-time interactive confirmation", rejected because implemented spec `20260815-0151-01` retired exactly that pattern (a `sys.stdin.isatty()` requirement plus a typed confirmation) on the ground that an executing agent has no TTY and can never record an approval the human gave in chat, and that no surface should require asserting "I am human". Accepting `--yes` as consent, rejected because `--yes` is a broad preauthorization and would make a `raw` export or a submission collateral to an unrelated command | spec `20260815-0151-01` status `implemented`, its problem statement and G1-G4; the fail-closed non-interactive confirm helper in `cli.py` | yes |
| D-5 | Does the plan get `command_surface.py` and `tests/test_cli_conformance_matrix.py` in `Scope-Paths`? | YES, necessarily and minimally | Leaving them out, rejected because a leaf cannot be declared without the first and the finalize scope gate would refuse the run over an undeclared edit mid-execution. Declaring `cli.py` alone and hoping the conformance test tolerates two new leaves, rejected on measurement: it asserts the undeclared set is EMPTY. Fixing the five pre-existing `oc profile *` declarations while in there, rejected and fenced out, because it would make a new regression unattributable | `find_undeclared_leaves` asserted empty by `test_no_undeclared_parser_leaves`; the five-entry baseline measured; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` mechanics | yes |
