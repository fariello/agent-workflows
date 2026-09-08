# IPD: Sanitized export, explicit submission, and setup wizard controls

- Date: 2026-09-08
- Kind: child
- Concern: Allow useful voluntary data sharing without accidental disclosure, automatic network activity, or ambiguous consent.
- Scope: Implement sensitivity-tiered export bundles, explicit submission to configured endpoints, manifests and previews, local telemetry/report setup choices, retention/deletion controls, and hostile privacy tests.
- Scope-Paths: agent_workflows/run_analytics_export.py, agent_workflows/run_analytics_submit.py, agent_workflows/run_analytics_wizard.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_run_analytics_export.py, tests/test_run_analytics_submit.py, tests/test_run_analytics_wizard.py, tests/test_cli_conformance_matrix.py
- Item-Dependencies: executed:mm5p3v
- Status: approved
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 9
- Highest E allocated: 09
- Author: Codex
- Id: ixis0c
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-103..PR-112, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE ROOT FINDING IS THAT THE SANITIZER THIS PLAN RESTS ON DETECTS ALMOST NONE OF ITS OWN CANARY LIST, AND IT WAS MEASURED CANARY BY CANARY (PR-103, F-1). The required tests demand that a bundle contain no seeded prompt, command, path, hostname, username, remote, branch, commit message, environment secret, high-entropy token, spreadsheet formula or archive-traversal canary. Run against `leak_sanitizer.scan_text` at fail severity, only ONE of twelve is caught: a home path. A git remote, a branch name, a commit message, an `AWS_SECRET_ACCESS_KEY=` assignment, an `sk-proj-` token, a `=cmd|` formula, a `../../../etc/passwd` traversal, prompt text and a shell command ALL return ZERO findings; the real hostname returns only `warn`. The module has NO secret-shaped detection at all (no entropy, no `AKIA`, no `BEGIN ... KEY`), because secret scanning here is `gitleaks` in a CI job over git history, which an export code path cannot call. So a plan asserting "passes the shared sanitizer" would have shipped a redacted tier that is redacted only of home paths. SECOND, THE DETECTOR IS MAINTAINER-SPECIFIC BY CONSTRUCTION (PR-104, F-2): `handle`, `private-repo` and `other-account` are compiled from THIS maintainer's tokens, so on an adopter's machine they match nothing, and the export gate would be weakest exactly where the data is not the maintainer's. THIRD, `urllib`'s DEFAULT OPENER IS AN EXFILTRATION AND SSRF SURFACE (PR-105, F-3): it follows redirects silently and enables `FileHandler`, `DataHandler` and `FTPHandler`, so `file:///etc/passwd` and `data:` both RESOLVE through a plain `urlopen`, and a scheme check on the CONFIGURED url cannot survive a redirect; the plan promised "redirects outside policy" with no mechanism named. FOURTH, ARCHIVE SAFETY CANNOT USE THE OBVIOUS API (PR-106, F-4): `requires-python` is `>=3.9` and CI tests 3.9, where `tarfile.data_filter` does not exist, and the package has no archive precedent at all. FIFTH, THE ENDPOINT CONFIG WOULD BE SILENTLY DROPPED (PR-107, F-5): measured, `config.normalize()` rebuilds from `default_config()` against a four-key allowlist, so an `analytics_endpoint` key vanishes on save; the correct home is the gitignored `.aw/config/local.json`, and Order 02 already REJECTED that file for its salt while scoping wider correlation to THIS plan. ALSO FIXED: "every-time interactive confirmation" contradicts implemented spec `20260815-0151-01`, which reframed TTY-gated consent as dishonest and replaced it with a non-TTY attestation (PR-108, F-6); two new leaves need `CommandDeclaration`s and `command_surface.py` was undeclared, the same gap Order 08's review found (PR-109, F-7); "installed only when selected if packaging supports optional feature installation" is incoherent since every analytics module is in-package stdlib code and no optional-feature mechanism exists (PR-110, F-8); the three E-items were mechanically sized across three distinct trust surfaces, which the Set orchestrator's own OQ-01 names (PR-111, F-9, split to NINE); and the gate carried no execution contract, the ninth sibling in a row, plus 22 escaped backticks and two smart quotes (PR-112, F-10).

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): defined three export tiers, explicit per-submission consent, transport boundaries, and optional wizard integration.

## Goal

Let users create inspectable bundles and, only by an explicit separate command, submit a chosen bundle to an approved endpoint. Installation must not enable sharing or periodic sampling by default, and unattended setup must never infer consent.

THE SANITIZER IS NOT THE PRIVACY BOUNDARY, AND ASSUMING IT WAS IS THIS PLAN'S LARGEST DEFECT. Measured canary by canary, `leak_sanitizer` at fail severity catches ONE of the twelve categories this plan's own tests enumerate (F-1), and three of its fail rules are compiled from the maintainer's own tokens so they match nothing on an adopter's machine (F-2). The write-side ALLOWLIST is the boundary: `metrics` is built by naming what may leave, never by filtering what must not. The detector is a corroborating read-side check with known blind spots that must be stated, not a gate to lean on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. Authored with THREE E-items spanning THREE DISTINCT TRUST SURFACES (local bundle tiers, network transport, interactive consent), which the Set orchestrator `5lxvl3`'s own open question names: "Order 09 spans three different trust surfaces in three items where the transport and the consent model each deserve their own pass". Eight siblings were already split for the identical reason (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9, `6eq3oq` 3->8, `mm5p3v` 3->8). Split into NINE items across four groups (surface contract / export tiers / transport / consent and lifecycle).

### Task group 1: The surface contract

- [ ] E-01 Declare `runs export` and `runs submit` in `command_surface.COMMAND_INVENTORY` and satisfy the conformance matrix.
  MEASURED, AND IT IS THE SAME GAP ORDER 08'S REVIEW FOUND. `COMMAND_INVENTORY` holds 129 declarations; `find_undeclared_leaves(_build_parser())` returns exactly the five pre-existing `oc profile *` entries; `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves` asserts that set is EMPTY, and that file is `pytestmark = pytest.mark.slow`, so the BARE suite this plan requires DESELECTS it. The authored `Scope-Paths` listed `cli.py` but not `command_surface.py`, so two new leaves would have failed a named fail-closed CI job with no in-scope file to fix it in.
  BOTH LEAVES MUTATE, AND BOTH GATES ALREADY EXIST. `aw runs` is documented as the READING half, so `export` (writes a bundle) and `submit` (transmits) are further exceptions after `repair` and Order 08's `analyze`. Measured gate vocabulary in use: `none` 91, `dry_run_default` 21, `confirmation` 10, `auth_floor` 7. `sanitize` and `check-local-leaks` already carry `confirmation`; `run finalize` and the `set` verbs carry `auth_floor`. Choose from that vocabulary rather than inventing one.
  - Depends on: none
  - Expected outcome: both leaves declared with a deliberate `command_class` (`mutation`), `mutation_gate` drawn from the existing four values, and `exit_contract`; `find_undeclared_leaves` returns the SAME five pre-existing entries and no new one; the matrix reports a full scenario row set for both; the `aw runs` description stops claiming a short list of exceptions.
  - Execution state: pending

### Task group 2: Export tiers and the real privacy boundary

- [ ] E-02 Build `metrics` from Order 02's write-side ALLOWLIST, never by filtering.
  THE ALLOWLIST IS THE BOUNDARY. Order 02 (`bzz5e6`) E-04 is "the single allowlist-based privacy PROJECTOR that every persisted fact crosses", whose stated outcome is that it is "the only path by which a fact reaches the envelope". `metrics` is therefore a re-emission of already-projected facts plus aggregate metadata, and it must NOT re-derive its own filter. Order 02 also records that this plan owns EXPORT-time sanitization and that a consumer may never treat "cache-projected" as "cleared for release", so `metrics` inherits the projection but must state its own residual risk independently.
  - Depends on: E-01
  - Expected outcome: `metrics` contains only fields an explicit allowlist names, refusing unknown keys by default; no second projector or sanitizer is written; the bundle records which projector version produced it; the label never claims anonymity.
  - Execution state: pending

- [ ] E-03 Implement `events-redacted` with the sanitizer's MEASURED BLIND SPOTS declared, not implied.
  THIS IS THE ITEM THE ROOT FINDING CREATED. Measured at review, `leak_sanitizer.scan_text` at fail severity over each canary this plan's own tests name: home path -> `home-path` (CAUGHT); real hostname -> nothing at fail, `warn` only; git remote `git@github.com:acme/private-repo.git` -> NOTHING; branch name -> NOTHING; commit message -> NOTHING; `AWS_SECRET_ACCESS_KEY=...` -> NOTHING; `sk-proj-...` token -> NOTHING; `=cmd|'/C calc'!A0` formula -> NOTHING; `../../../etc/passwd` -> NOTHING; prompt text -> NOTHING; shell command -> nothing at fail. ONE of twelve is caught. The module's rule set is exactly `home-path`, `users-path`, `windows-home`, `vc-home`, `private-repo`, `other-account`, `session-id`, `handle`, `ipv4`, `ipv6` (the last two OFF unless `ip_enabled`), and it contains NO entropy check, no `AKIA`, no `BEGIN ... KEY`. Secret detection in this repository is `gitleaks` in a CI job over git history, which an export path cannot invoke.
  SO THE REDACTION MUST BE STRUCTURAL, NOT DETECTOR-DRIVEN: allowlist the event FIELDS that may appear and drop every other field wholesale, then run the detector as corroboration. The "sanitizer report" this tier ships must ENUMERATE what the detector does not look for, or it advertises a guarantee it does not provide.
  - Depends on: E-02
  - Expected outcome: field-level allowlisting with everything unnamed dropped; the shipped sanitizer report lists the detector's measured coverage AND its blind spots by name; a test proves each of the eleven uncaught canary classes is excluded STRUCTURALLY rather than by detection; residual risk stated in the bundle itself.
  - Execution state: pending

- [ ] E-04 Implement the `raw` tier's file selection, manifest, checksums and preview.
  `raw` copies selected original run artifacts and may contain prompts, conversations, code, commands, paths and secrets. It is never the default and never carries a safety claim. The preview must list the exact files and their sizes before anything is written, since that listing is the only review a human gets.
  NOTE THE MEASURED SCALE, so the preview is usable rather than a wall of text: the live corpus holds 135 runs with 472 prompt files and 460 session files totalling roughly 238 MB. A `raw` export of everything is not a realistic review artifact, so selection must be explicit and the preview must summarize by category with counts and bytes.
  - Depends on: E-03
  - Expected outcome: deterministic manifest with per-file checksums; a preview naming exact selected files, summarized by category with counts and total bytes; `metrics` remains the default tier; no safety or anonymity label anywhere on `raw`.
  - Execution state: pending

- [ ] E-05 Implement archive creation and any extraction with 3.9-safe traversal and symlink defenses.
  MEASURED CONSTRAINT THAT RULES OUT THE OBVIOUS API. `requires-python` is `>=3.9` and CI tests 3.9 through 3.14. `tarfile` extraction filters (PEP 706) arrived in 3.12 and were backported only to 3.9.17+, so on a 3.9.0-3.9.16 interpreter `tarfile.data_filter` DOES NOT EXIST and `extractall` is unsafe by default. Do not write `filter="data"` and assume it is there; either use `zipfile` with explicit per-member validation, or feature-detect the filter and implement the fallback.
  ALSO MEASURED: THERE IS NO ARCHIVE PRECEDENT IN THIS PACKAGE. The only `zipfile` use is `leak_sanitizer` READING a built wheel; there is no `tarfile` import, no `extractall`, no `make_archive`. So this is greenfield and every defense must be written and tested here rather than inherited.
  - Depends on: E-04
  - Expected outcome: every archive member validated for absolute paths, `..` traversal, symlinks, hardlinks, device files and duplicate names BEFORE any write; behavior identical on an interpreter without `tarfile.data_filter` (feature-detected, with the fallback exercised); a test proving a hostile archive is refused rather than partially extracted.
  - Execution state: pending

### Task group 3: Transport

- [ ] E-06 Build the HTTP client on a restricted opener, because the stdlib default is an exfiltration surface.
  MEASURED, AND THIS IS THE SECURITY FINDING THAT MOST CHANGES THE CODE. `urllib.request.urlopen` uses a default opener that (a) FOLLOWS REDIRECTS silently via `HTTPRedirectHandler` and (b) enables `FileHandler`, `DataHandler` and `FTPHandler`. Verified by execution: `urlopen("file:///<path>")` returned the file's contents and `urlopen("data:text/plain,hello")` returned its payload. So a scheme check on the CONFIGURED url is not sufficient, because a 302 to `file:///etc/passwd` is followed by the same opener that just passed the check. Build an `OpenerDirector` carrying ONLY `HTTPSHandler`, `HTTPDefaultErrorHandler` and `HTTPErrorProcessor` plus a redirect handler that REFUSES a redirect whose target fails policy. Verified: such an opener refuses `file://`, though it does so with a bare `AttributeError`, so wrap it in an actionable error rather than letting that surface.
  REUSE THE EXISTING SCHEME-GATE PRECEDENT rather than inventing one: `oc_models._scheme_ok` already gates credential transmission on https with a loopback exception, and `oc_models.http_fetch_json` already sends a bearer token via a header that is "never echoed anywhere" with a blanket failure path. `versioning.latest_pypi_version` is the second https-only caller. Follow both.
  - Depends on: E-01
  - Expected outcome: an https-only restricted opener with no `file`/`data`/`ftp` handler and an explicit redirect policy, proven by tests that a `file://` target, a `data:` target and a redirect to either are all REFUSED with an actionable message; authentication read from the environment or local config and never written to argv, output, logs, receipt or bundle; no automatic retry and no background upload.
  - Execution state: pending

- [ ] E-07 Implement submission validation, the local receipt, and the unavailable-endpoint path.
  Submission validates manifest, schema, checksums, tier and size, and displays the endpoint and sensitivity before acting. Cancellation, timeout, server rejection, duplicate receipt and interrupted upload must not silently retry.
  IF NO ENDPOINT GOVERNANCE IS APPROVED, THIS IS THE DELIVERABLE. The plan's own gate says to implement submit as a tested unavailable capability rather than a generic uploader, and that is the correct default given no endpoint, operator, retention policy or contact exists in this repository today. An honest `unavailable` status with an actionable message is a complete implementation of this item, not a partial one.
  - Depends on: E-06
  - Expected outcome: every validation failure class returns a documented code and remedy; a local receipt records what was sent, where and when, carrying no secret; with no approved endpoint the command returns an actionable `unavailable` rather than attempting a transmission; no retry daemon, queue or beacon exists anywhere in the code.
  - Execution state: pending

### Task group 4: Consent and lifecycle

- [ ] E-08 Implement consent as a NON-TTY ATTESTATION, because the authored TTY confirmation contradicts an implemented spec.
  THE PLAN'S "every-time interactive confirmation" IS THE PATTERN THIS REPOSITORY DELIBERATELY REMOVED. Spec `20260815-0151-01-honest-human-approval-attestation` is `Status: implemented` and reframed the human-only gate: it REPLACED a `sys.stdin.isatty()` requirement plus a typed confirmation with `--by-human`, an explicit non-TTY attestation, on the reasoning that "an executing agent has no TTY, so it can NEVER record an approval, even one the human explicitly gave in chat", and that nothing should require asserting "I am human". Its G2 is the shape to copy: the action SUCCEEDS iff the explicit flag is passed and is REFUSED with a clear message otherwise, with attributed provenance in a recorded line.
  SO THE CONSENT MODEL IS: an explicit flag naming the tier and the destination, honored regardless of TTY, refused when absent, recorded with provenance. Reuse the fail-closed confirm helper's posture (`cli.py`'s "non-interactive without --yes: refuse to change things silently") for the interactive convenience path, but the attestation is what authorizes, not the TTY.
  - Depends on: E-07
  - Expected outcome: consent is an explicit attested flag with recorded provenance, working in a non-interactive agent shell and REFUSED when absent; no code path asserts the operator is human; a test proves absence refuses and presence records attribution; `--yes` alone never authorizes a `raw` export or a submission.
  - Execution state: pending

- [ ] E-09 Add wizard choices, retention and precise deletion, storing endpoint configuration where it survives.
  THE AUTHORED CONFIG SURFACE WOULD SILENTLY DISCARD THE SETTING. Measured: `config.normalize()` rebuilds its output from `default_config()` against `_ALLOWED_TOP_KEYS` of exactly `{config_version, repos, defaults, aw_home}`, so an `analytics_endpoint` key added to the XDG user config VANISHES on save (verified by round-tripping one). The repository's own documented workaround is `review_findings_gate`, read from `.aw/config/project.json` "and NOT via the XDG user config (which drops unknown keys)", round-tripping through `project_schema`'s `unknown_fields`. But endpoint and auth are MACHINE-LOCAL, not committed policy, so the right home is `.aw/config/local.json`, which is gitignored and schema-parsed by `parse_local_binding`. Note Order 02 REJECTED that file for its cryptographic salt on the ground that it is "a user-facing configuration surface whose keys the setup wizard manages"; that reasoning ARGUES FOR it here, since an endpoint IS a user-facing setting a human should see and edit.
  DROP THE OPTIONAL-INSTALL CLAIM, WHICH IS INCOHERENT. The authored outcome says "analytics tooling is installed only when selected if packaging supports optional feature installation". Measured: every analytics module in this Set lives inside `agent_workflows/` (eighteen `run_analytics_*.py` files across the siblings' `Scope-Paths`), the only declared extra is `test`, and no optional-feature install mechanism exists. The modules ship with the package unconditionally; what the wizard can gate is whether analytics is ENABLED and whether sampling RUNS, not whether code is present.
  ALSO INHERIT ORDER 02'S DEFERRED DECISION. Its OQ-01 scoped correlation to "ONE BOX AND ONE CACHE GENERATION, and any wider scope is Order 09's explicit opt-in to own". This item owns that opt-in and must default it OFF.
  - Depends on: E-08
  - Expected outcome: endpoint and auth-source configuration persisted where it survives a round trip (proven, not assumed), with secrets referenced by environment variable name rather than stored; conservative defaults with analytics off, sampling a separate question, and unattended mode local and no-submit; the optional-install claim replaced by an enable/disable claim; cross-box correlation defaulted OFF as Order 02 deferred; deletion targeting only tool-owned analytics children and never a source run.
  - Execution state: pending

## Project conventions discovered (Step 0)

- User-local profile/config helpers already exist; use them for preferences and endpoint configuration rather than putting secrets or user choices in repository files. MEASURED CORRECTION: the XDG user config will DROP an unregistered key. `config.normalize()` rebuilds from `default_config()` against `_ALLOWED_TOP_KEYS` = `{config_version, repos, defaults, aw_home}`; a round trip of an `analytics_endpoint` key returned `False` for its survival. Use the gitignored `.aw/config/local.json` (schema-parsed by `parse_local_binding`) for machine-local endpoint settings, and see `review_findings_gate` for the documented precedent of reading a key outside the XDG config.
- THE SANITIZER DETECTS ONE OF THE TWELVE CANARY CLASSES THIS PLAN ENUMERATES. Measured at fail severity: home path CAUGHT; hostname `warn` only; git remote, branch name, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd|` formula, `../../../etc/passwd`, prompt text and shell command ALL uncaught. The full fail rule set is `home-path`, `users-path`, `windows-home`, `vc-home`, `private-repo`, `other-account`, `session-id`, `handle`, plus `ipv4`/`ipv6` only when `ip_enabled`. There is NO entropy or secret-shape detection; `gitleaks` provides that in a CI job over git history and is not callable from an export path.
- THREE OF THE FAIL RULES ARE MAINTAINER-SPECIFIC. `handle`, `private-repo` and `other-account` are compiled from this maintainer's own tokens, so on an adopter's machine they match nothing. Verified: another user's handle and another private repo name both return zero findings, while `home-path` and `session-id` are generic and do match. The detector is extensible via repo `fail_patterns` and never-committed user hints, which is the correct place to strengthen it, but the SHIPPED default is narrow.
- ORDER 02 OWNS THE WRITE-SIDE ALLOWLIST AND THIS PLAN OWNS EXPORT-TIME SANITIZATION. `bzz5e6` E-04 is "the only path by which a fact reaches the envelope", and its own text says a consumer may never treat "cache-projected" as "cleared for release" and that this plan must not build a second sanitizer. So `metrics` re-emits projected facts and states its own residual risk.
- ORDER 02 DEFERRED CROSS-BOX CORRELATION TO THIS PLAN. Its OQ-01 scoped the salt to "ONE BOX AND ONE CACHE GENERATION, and any wider scope is Order 09's explicit opt-in to own". That opt-in is E-09's and defaults OFF.
- `urllib`'s DEFAULT OPENER IS NOT SAFE FOR AN UNTRUSTED URL. Measured by execution: the default handler chain includes `HTTPRedirectHandler`, `FileHandler`, `DataHandler` and `FTPHandler`; `urlopen("file://<path>")` returned file contents and `urlopen("data:text/plain,hello")` returned its payload. A restricted `OpenerDirector` with only `HTTPSHandler`, `HTTPDefaultErrorHandler` and `HTTPErrorProcessor` refuses `file://`, but with a bare `AttributeError` that must be wrapped.
- TWO HTTPS PRECEDENTS EXIST AND BOTH ARE GOOD. `oc_models._scheme_ok` gates credential transmission on https with a loopback exception, and `oc_models.http_fetch_json` sends a bearer header "never echoed anywhere" with a blanket failure path; `versioning.latest_pypi_version` is the second https-only caller. A no-network TEST harness also exists: `lifecycle_fixtures.run_no_network` subclasses `socket.socket` so any `connect` raises. Reuse that to prove zero network calls rather than inventing a mock.
- ARCHIVE HANDLING IS GREENFIELD AND CANNOT USE THE OBVIOUS API. The only `zipfile` use is `leak_sanitizer` reading a built wheel; there is no `tarfile` import, no `extractall`, no `make_archive`. And `requires-python` is `>=3.9` with CI on 3.9, where `tarfile.data_filter` does not exist (PEP 706 landed in 3.12, backported only to 3.9.17+), so extraction filters must be feature-detected with a working fallback.
- A NEW LEAF IS A THREE-FILE CONTRACT. `COMMAND_INVENTORY` holds 129 declarations, `find_undeclared_leaves` is asserted EMPTY by `tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`, and that file is `pytest.mark.slow` so the BARE suite deselects it; it runs in the dedicated `output-conformance` CI job across Python 3.9-3.14. The five `oc profile *` entries are a PRE-EXISTING failure of that assertion and the baseline against which a new one is attributable.
- THE MUTATION-GATE VOCABULARY IS FIXED AND SUFFICIENT. Measured across the 129 declarations: `none` 91, `dry_run_default` 21, `confirmation` 10, `auth_floor` 7. `sanitize` and `check-local-leaks` carry `confirmation`; `run finalize` and the `set` verbs carry `auth_floor`. Choose from these rather than inventing a gate.
- TTY-GATED CONSENT WAS DELIBERATELY REMOVED FROM THIS REPOSITORY. Spec `20260815-0151-01` is `Status: implemented` and replaced a `sys.stdin.isatty()` plus typed-confirmation floor with `--by-human`, an explicit non-TTY attestation, because "an executing agent has no TTY, so it can NEVER record an approval" and because nothing should require asserting "I am human". A fail-closed non-interactive confirm helper also exists in `cli.py` ("non-interactive without --yes: refuse to change things silently").
- Host-level setup interviews are optional and tolerate unavailable components. Analytics prompts must follow that resilience while never swallowing a requested configuration error silently. `install_wizard` is the precedent and its stated invariant is the right one: "Noninteractive first install with incomplete choices or `--yes` alone FAILS CLOSED before writes".
- The local cache and report are minimized but not anonymous. Export UI must not overstate privacy.
- The entire runs tree is disposable, but deletion commands must target exact tool-owned analytics children and preserve source runs unless the user explicitly selects raw run deletion through an existing supported lifecycle. Resolve every path through Order 01's (`xbwq8n`) resolver and `path_is_within_analytics`; never compose the `.aw/records/runs` literal.
- CLI registration shares Order 08's routing-sensitive `aw runs` surface, so this IPD executes afterward and adds fixed leaves only. Both new leaves MUTATE on a noun documented as the READING half, so each is a further declared exception after `repair` and Order 08's `analyze`.
- THE RAW-EXPORT REVIEW SURFACE IS LARGE. The live corpus holds 135 runs with 472 prompt files and 460 session files, roughly 238 MB, so a `raw` preview must summarize by category with counts and bytes rather than listing everything.
- ALL ANALYTICS CODE SHIPS WITH THE PACKAGE. Eighteen `run_analytics_*.py` modules appear across the siblings' `Scope-Paths`, all under `agent_workflows/`; the only declared extra is `test`; no optional-feature install mechanism exists. The wizard can gate ENABLEMENT, not code presence.

## Findings

Sensitivity contract:

| Tier | Contents | Consent |
|---|---|---|
| `metrics` | privacy-projected normalized facts, aggregate metadata, quality, taxonomy/pricing versions, system resource categories/pseudonyms | explicit export command; safe default tier |
| `events-redacted` | bounded structured event facts with content/commands/paths/identity removed by FIELD ALLOWLIST, plus a sanitizer report that names the detector's measured blind spots | explicit tier selection and warning |
| `raw` | selected original run artifacts, potentially including prompts/conversations/code/commands/paths/secrets | explicit attested acknowledgement naming tier and destination (non-TTY, per spec `20260815-0151-01`); never default |

Submission is never part of analyze, open, export, install, periodic telemetry, or cleanup. No background uploader, queued retry daemon, tracking pixel, analytics beacon, or implicit "improve product" consent is permitted.

The endpoint contract must specify operator, URL allowlist/configuration, TLS, authentication source, maximum size, accepted schema/tier, server retention, access, aggregation, deletion request method, contact, response/receipt, and behavior on partial/duplicate submission. If those details are not approved, implement local export only and make submit return an actionable unavailable status. NONE of those details exists in this repository today, so the `unavailable` path is the EXPECTED outcome of E-07, not a fallback.

### Findings (review, measured 2026-09-08 at HEAD `9b413533`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | plan required tests; `leak_sanitizer` rule set | **THE SANITIZER CATCHES ONE OF THE TWELVE CANARY CLASSES THIS PLAN'S OWN TESTS DEMAND.** At fail severity: home path CAUGHT; hostname `warn` only; git remote, branch name, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd\|` formula, `../../../etc/passwd`, prompt text and shell command ALL return ZERO findings. The module has NO entropy or secret-shape detection (no `AKIA`, no `BEGIN ... KEY`); secret scanning here is `gitleaks` in a CI job over git history, uncallable from an export path. A tier asserting "passes the shared sanitizer" would be redacted only of home paths, which is a false privacy guarantee on the one plan whose entire purpose is not to make one | ran `scan_text` at fail and warn severity over each of the twelve canary categories; enumerated every rule name in the module; grepped for entropy/secret detection |
| F-2 | HIGH | `leak_sanitizer._FAIL_PATTERNS` | **THREE FAIL RULES ARE COMPILED FROM THE MAINTAINER'S OWN TOKENS, SO THE GATE IS WEAKEST ON AN ADOPTER'S MACHINE.** `handle`, `private-repo` and `other-account` are literal maintainer identifiers. Verified: another user's handle and another private repo name return zero findings, while `home-path` and `session-id` are generic and do match. So the detector's apparent competence on this box does not transfer, which is exactly backwards for a data-sharing feature whose users are not the maintainer | scanned a different user's handle, private repo name, session id and home path; read the pattern construction |
| F-3 | HIGH | plan E-02's transport; `urllib` default opener | **THE STDLIB DEFAULT OPENER IS AN EXFILTRATION AND SSRF SURFACE AND THE PLAN NAMED NO MECHANISM.** Measured by execution: the default handler chain includes `HTTPRedirectHandler`, `FileHandler`, `DataHandler` and `FTPHandler`; `urlopen("file://<path>")` returned the file's contents and `urlopen("data:text/plain,hello")` returned its payload. So a scheme check on the CONFIGURED url cannot survive a 302 to `file:///etc/passwd`, and "rejects redirects outside policy" needs a restricted `OpenerDirector` plus a refusing redirect handler. A restricted opener does refuse `file://`, but with a bare `AttributeError` | built the default opener and listed its handlers; opened a `file://` and a `data:` url successfully; built a restricted opener and observed the refusal shape |
| F-4 | HIGH | plan's archive-defense test; `requires-python` | **ARCHIVE SAFETY CANNOT USE THE OBVIOUS API ON THE DECLARED FLOOR.** `requires-python` is `>=3.9` and CI tests 3.9; `tarfile` extraction filters landed in 3.12 and were backported only to 3.9.17+, so `tarfile.data_filter` is ABSENT on a 3.9.0-3.9.16 interpreter and `extractall` is unsafe by default. And there is NO archive precedent in the package: the only `zipfile` use is `leak_sanitizer` reading a wheel, with no `tarfile` import, no `extractall`, no `make_archive`. Every defense is greenfield and must be feature-detected | read `requires-python` and the CI matrix; grepped the package for every archive API; confirmed the filter's availability history |
| F-5 | HIGH | plan conventions; `config.normalize` | **THE ENDPOINT CONFIGURATION WOULD BE SILENTLY DISCARDED.** Measured by round trip: `config.normalize()` rebuilds from `default_config()` against `_ALLOWED_TOP_KEYS` of exactly `{config_version, repos, defaults, aw_home}`, and an added `analytics_endpoint` key did NOT survive. The plan says to "use them for preferences and endpoint configuration", which would produce a setting that vanishes on save. The repository's own workaround is documented at `review_findings_gate` (read outside the XDG config because it "drops unknown keys"), and the machine-local home is the gitignored `.aw/config/local.json` | round-tripped an `analytics_endpoint` key through `normalize()`; read `_ALLOWED_TOP_KEYS` and the `review_findings_gate` comment; confirmed `local.json` is gitignored and schema-parsed |
| F-6 | MEDIUM | plan E-01/E-02 consent model; spec `20260815-0151-01` | **"EVERY-TIME INTERACTIVE CONFIRMATION" IS THE PATTERN THIS REPOSITORY DELIBERATELY REMOVED.** That spec is `Status: implemented` and replaced a `sys.stdin.isatty()` plus typed-confirmation floor with `--by-human`, an explicit NON-TTY attestation, reasoning that "an executing agent has no TTY, so it can NEVER record an approval, even one the human explicitly gave in chat" and that nothing should require asserting "I am human". A TTY-gated consent model would reintroduce the exact friction the spec retired and would make the feature unusable from an agent shell | read the spec's status, problem statement and G1-G4; found the fail-closed non-interactive confirm helper in `cli.py` |
| F-7 | MEDIUM | plan `Scope-Paths`; `command_surface.py` | **TWO NEW LEAVES NEED DECLARATIONS AND THE FILE THAT HOLDS THEM WAS UNDECLARED.** `COMMAND_INVENTORY` has 129 entries and `find_undeclared_leaves` is asserted EMPTY by `test_no_undeclared_parser_leaves`, which is `pytest.mark.slow` and therefore DESELECTED by the bare suite this plan requires. Same gap Order 08's review found. Both leaves also MUTATE on a noun documented as the READING half, so each needs a deliberate `mutation_gate` from the existing four-value vocabulary | called `find_undeclared_leaves` on the real parser; counted the gate vocabulary across all declarations; read the test's marker |
| F-8 | MEDIUM | plan E-03's expected outcome | **"INSTALLED ONLY WHEN SELECTED IF PACKAGING SUPPORTS OPTIONAL FEATURE INSTALLATION" IS INCOHERENT HERE.** Measured: eighteen `run_analytics_*.py` modules appear across the siblings' `Scope-Paths`, all inside `agent_workflows/`; the only declared extra is `test`; no optional-feature install mechanism exists. The modules ship unconditionally with the package. The wizard can gate whether analytics is ENABLED and whether sampling RUNS, not whether code is present, and the conditional phrasing invites an executor to build a mechanism that should not exist | collected every analytics module path from the Set; read `[project.optional-dependencies]`; searched the installer for extras handling |
| F-9 | MEDIUM | plan E-01..E-03; orchestrator `5lxvl3` OQ-01 | **MECHANICALLY SIZED ACROSS THREE DISTINCT TRUST SURFACES, WHICH THE SET'S OWN OPEN QUESTION NAMES:** "Order 09 spans three different trust surfaces in three items where the transport and the consent model each deserve their own pass". Local bundle tiers, network transport and interactive consent have nothing in common but sequence. Ninth sibling with this finding | orchestrator plan read; item content counted against the workflow's split diagnostics |
| F-10 | LOW | plan gate; plan source; suite baseline | The gate carried no execution contract (no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions), the ninth consecutive sibling. Also 22 escaped backtick pairs rendering as literal backslashes and two smart quotes, and no recorded baseline: measured `2 failed, 5655 passed, 3 skipped, 2 xfailed in 56.63s`, both failures pre-existing and pinned to the live plan corpus | plan read; `grep -o` counts before the fix; bare suite run at review |

## Proposed changes (ordered, validatable)

1. E-01 declares both leaves and satisfies the conformance matrix.
2. E-02 re-emits Order 02's allowlisted facts as `metrics`; E-03 makes `events-redacted` structurally field-allowlisted with the detector's blind spots declared; E-04 gives `raw` a real manifest and a summarized preview; E-05 adds 3.9-safe archive defenses.
3. E-06 builds the restricted https-only opener with an explicit redirect policy; E-07 adds validation, receipts and the expected `unavailable` path.
4. E-08 makes consent a non-TTY attestation per the implemented spec; E-09 stores endpoint config where it survives, defaults everything off, and deletes precisely.

## Deferred / out of scope (with reason)

- Operating a collection server, choosing an organization endpoint, legal/privacy policy approval, or defining server-side research governance is outside repository implementation. Since NONE of those exists today, E-07's `unavailable` status is the expected deliverable.
- Automatic telemetry submission and automatic price/system data upload are prohibited.
- Claiming anonymization is prohibited unless independently demonstrated. Measured, it cannot be demonstrated with the shipped detector (F-1), so the claim must not appear.
- Installing the analyzer by default is prohibited by the user decision; the wizard may offer it clearly. NOTE the code ships regardless (F-8), so the offer is about ENABLEMENT.
- STRENGTHENING `leak_sanitizer` ITSELF IS OUT OF SCOPE, and that is a deliberate, uncomfortable line. Adding entropy or secret-shape detection would change a shipped gate that `aw sanitize`, a pre-commit hook and a CI job all consume, which is a separate plan with its own false-positive risk budget. This plan must therefore not LEAN on the detector (E-03 allowlists structurally instead) and must state its blind spots. If execution concludes the detector's gaps make a redacted tier indefensible even with structural allowlisting, that is a STOP-and-raise, not a silent detector edit.
- Fixing the five pre-existing `oc profile *` declarations is out of scope; they are the baseline that makes a new undeclared leaf attributable.
- The write-side projector and cache are Order 02 (`bzz5e6`); the resolver and reserved namespace are Order 01 (`xbwq8n`); the analytics engine is Order 06 (`aflsz3`); the report bundle is Order 07 (`6eq3oq`); the `aw runs` routing surface is Order 08 (`mm5p3v`). This plan CONSUMES all of them and reimplements none.

## Scope check

- Over-scope: no source parsing, analysis/statistics, SPA internals, runner lifecycle mechanics, or server implementation. Specifically, and each for a measured reason: do NOT write a second projector or sanitizer (Order 02's E-04 is the single write-side path and its own text forbids a second); do NOT edit `leak_sanitizer` to add detection (it backs `aw sanitize`, a pre-commit hook and a CI job; see the deferred note); do NOT use a bare `urllib.request.urlopen` (its default opener resolves `file://` and `data:` and follows redirects, measured); do NOT call `tarfile.extractall` relying on `filter="data"` (absent on the 3.9 floor); do NOT persist an endpoint key into the XDG user config (`normalize()` drops it, measured); do NOT gate consent on a TTY (spec `20260815-0151-01` retired that pattern); do NOT compose the `.aw/records/runs` literal (Order 01 owns the resolver); do NOT delete or touch a source run directory; and do NOT edit a spec, since none is declared in `Scope-Paths`.
- `command_surface.py` and `tests/test_cli_conformance_matrix.py` ARE now in `Scope-Paths`, necessarily: a leaf cannot be declared without the first, and the pre-existing-baseline assertion may need its known set updated in the second.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
- Under-scope: includes export tiers, manifests, preview, submission boundary, receipts, auth handling, wizard defaults, periodic-sampling consent, retention, deletion, and absent-endpoint behavior. The declaration contract (E-01), the structural field allowlist replacing detector reliance (E-03), the 3.9-safe archive defenses (E-05), the restricted opener (E-06), the attested non-TTY consent (E-08) and the surviving config location (E-09) were all under-scope before review.

## Required tests / validation

Baseline, measured bare at HEAD `9b413533`: `2 failed, 5655 passed, 3 skipped, 2 xfailed in 56.63s`. Both failures (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` and `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) are pinned to the live mutable plan corpus and are PRE-EXISTING. Re-measure in the executing worktree and compare failing NODE IDS; the criterion is an empty delta against your own baseline, never a total.

THE BARE SUITE IS NOT SUFFICIENT. `tests/test_cli_conformance_matrix.py` is `pytest.mark.slow` and `addopts` supplies `-m 'not slow'`, so a bare run DESELECTS the gate proving a leaf is declared and covered. Run it explicitly alongside `tests/test_cli_quality_gates.py`, as the `output-conformance` CI job does, and paste both.

- STRUCTURAL exclusion tests, NOT detector-dependent ones, for every canary class: seeded prompt, response, command, path, hostname, username, remote, branch, commit message, environment secret, high-entropy token, spreadsheet formula and archive-traversal string. Assert each is absent because the field allowlist never named it. Then ALSO run the detector and paste which classes it caught, so the measured one-of-twelve coverage is documented rather than implied.
- A test asserting the sanitizer report shipped in `events-redacted` ENUMERATES the detector's blind spots by name. A report claiming a clean scan without that enumeration is a false guarantee.
- Raw export refuses without the explicit attestation and precisely lists selected files; `metrics` remains the default. Prove `--yes` alone does NOT authorize `raw` or a submission.
- Analyze, report open, wizard, install, and periodic sampling make zero network calls, proven with the EXISTING harness pattern (`lifecycle_fixtures.run_no_network` subclasses `socket.socket` so any `connect` raises) rather than a hand-rolled mock.
- Transport tests: a `file://` target, a `data:` target, an `ftp://` target and a REDIRECT to each are all REFUSED with an actionable message (measured: a bare `urlopen` resolves the first two, so this test must fail against a naive implementation); unapproved scheme or host, invalid TLS, oversized, tampered and unknown-schema bundles, missing auth, unsupported tier. Secrets never appear in argv guidance, output, logs, receipts or bundle.
- Cancellation, timeout, server rejection, duplicate receipt, and interrupted upload do not silently retry. A grep proving no retry loop, queue or daemon exists.
- Archive tests: absolute member path, `..` traversal, symlink, hardlink, device file and duplicate name all refused BEFORE any write; the same behavior on an interpreter WITHOUT `tarfile.data_filter` (feature-detect and exercise the fallback, since the 3.9 floor may lack it).
- Config persistence: an endpoint setting round-trips and SURVIVES (measured, the XDG config drops it), with a test that would fail against the naive location.
- Wizard interactive/unattended/default/reconfigure/disable/delete paths and no-consent assertions; unattended with incomplete choices FAILS CLOSED, per `install_wizard`'s stated invariant.
- Deletion precision: only tool-owned analytics children are removed, resolved through Order 01's containment predicate, and no source run directory is touched.
- No test may reach the network, spawn a browser, spend real time, or parse the live corpus as its assertion source.
- Bare `python3 -m pytest` and `git diff --check`, PLUS the explicit conformance invocation.

## Spec / documentation sync

Order 10 (`9xycbh`) documents local-only defaults, every privacy tier, residual risks, endpoint governance, consent, retention, deletion, and absence of automatic submission. If no endpoint policy is approved, docs must say submission is unavailable rather than imply a future server.

THIS PLAN DECLARES NO `.spec.md` IN `Scope-Paths` AND MUST EDIT NONE. Two implemented specs constrain it and neither is amended: `20260815-0151-01` (honest human-approval attestation) supplies the consent SHAPE, and `20260818-1525-01` (command-surface redesign) supplies the grammar the two new leaves sit inside. If execution concludes either contract must change, that is a STOP-and-raise.

THE DOCUMENTATION MUST CARRY THE DETECTOR'S BLIND SPOTS, and this is the most important documentation obligation in the Set. Measured, the shipped sanitizer catches one of the twelve canary classes this plan enumerates, and three of its fail rules are maintainer-specific so they match nothing on an adopter's machine. Documentation that says a tier "passes the sanitizer" without that boundary tells a user their data was checked for things it was never checked for. State what is structurally excluded (the allowlist), what is detected (the narrow rule set), and what is neither. RE-MEASURE every count here at execution.

## Open questions

"No open questions" was not accurate: the plan required four decisions it specified nowhere. All four are answerable from repository evidence or from measurement rather than by asking, so each is recorded resolved with its basis. Every reviewed sibling in this Set carried the same inaccurate claim.

### OQ-01: What actually establishes the redaction guarantee, given the detector's measured coverage?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT as a STRUCTURAL FIELD ALLOWLIST, with the detector demoted to corroboration whose blind spots must be published. Run canary by canary at fail severity, `leak_sanitizer.scan_text` catches ONE of the twelve classes this plan's own tests enumerate: a home path. A git remote, branch name, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd|` formula, `../../../etc/passwd`, prompt text and shell command all return zero findings, and the hostname returns only `warn`. The module contains no entropy or secret-shape rule; `gitleaks` provides that in CI over git history and cannot be called from an export path. REJECTED: relying on the detector as the gate, because it would ship a "redacted" tier redacted only of home paths, which is a false guarantee on the one plan whose purpose is to avoid making one. Extending `leak_sanitizer` with entropy and secret rules, rejected as out of scope for THIS plan: it backs `aw sanitize`, a pre-commit hook and a CI job, so changing its false-positive profile is a separate plan with its own risk budget; the gate records that if structural allowlisting still cannot make a redacted tier defensible, execution must STOP and raise rather than edit the detector silently. Dropping the `events-redacted` tier, rejected because bounded structured events are the tier with real research value and an allowlist can deliver it honestly.

### OQ-02: How is the transport built, given the stdlib default opener resolves `file://` and follows redirects?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY EXECUTION as a RESTRICTED `OpenerDirector` carrying only `HTTPSHandler`, `HTTPDefaultErrorHandler` and `HTTPErrorProcessor`, plus a redirect handler that refuses a target failing policy, with the refusal wrapped in an actionable error. Measured: the default opener's handler chain includes `HTTPRedirectHandler`, `FileHandler`, `DataHandler` and `FTPHandler`; `urlopen("file://<path>")` returned file contents and `urlopen("data:text/plain,hello")` returned its payload; the restricted opener refuses `file://` but raises a bare `AttributeError`. REJECTED: checking the scheme of the configured url only, as the plan implied, because a 302 to `file:///etc/passwd` is followed by the same opener that just passed the check, turning a submit command into a local-file exfiltrator. Adding a third-party HTTP client, rejected because `pyproject.toml` declares exactly one runtime dependency and two stdlib https callers already exist (`oc_models.http_fetch_json`, `versioning.latest_pypi_version`) whose scheme-gating and never-echo-the-token posture is the right precedent to follow.

### OQ-03: Where does endpoint and auth configuration live so it survives a save?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY ROUND TRIP as the gitignored `.aw/config/local.json`, with the auth SOURCE stored as an environment variable NAME and never the secret itself. Measured: `config.normalize()` rebuilds its output from `default_config()` against `_ALLOWED_TOP_KEYS` of exactly `{config_version, repos, defaults, aw_home}`, and an added `analytics_endpoint` key did not survive the round trip, so the plan's "use the user-local config helpers" would have produced a setting that silently vanishes. REJECTED: the XDG user config, on that measurement. `.aw/config/project.json`, rejected because it is COMMITTED portable policy and an endpoint plus auth source is machine-local, so committing it would push one user's destination onto every clone. Storing a token in any config file, rejected outright; `oc_models` already models the correct pattern by reading a key and sending it in a header that is never echoed. NOTE Order 02 rejected `local.json` for its cryptographic SALT on the ground that it is "a user-facing configuration surface whose keys the setup wizard manages"; that same reasoning ARGUES FOR it here, because an endpoint is precisely a user-facing setting a human should see and edit.

### OQ-04: Is consent an interactive TTY confirmation or an attestation?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW from an implemented spec as an EXPLICIT NON-TTY ATTESTATION naming the tier and destination, honored regardless of TTY, refused when absent, recorded with attributed provenance. Spec `20260815-0151-01-honest-human-approval-attestation` is `Status: implemented` and did exactly this transition for spec approval: it REPLACED a `sys.stdin.isatty()` requirement plus a typed confirmation with `--by-human`, reasoning that "an executing agent has no TTY, so it can NEVER record an approval, even one the human explicitly gave in chat", and that no surface should require asserting "I am human". Its G2 (succeed iff the flag is passed, refuse clearly otherwise) is the shape adopted here. REJECTED: the authored "every-time interactive confirmation", because it reintroduces the friction that spec retired and makes the feature unusable from an agent shell, which is how this repository is actually driven. Accepting `--yes` as consent, rejected because `--yes` is a broad preauthorization for expected mutations and would make a `raw` export or a submission collateral to an unrelated command; the attestation must be specific to the tier and destination.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both `CommandDeclaration`s with their `command_class`, `mutation_gate` (drawn from the measured four-value vocabulary) and `exit_contract`. Paste `find_undeclared_leaves` showing the SAME five pre-existing `oc profile *` entries and no new one. Paste the EXPLICIT run of `tests/test_cli_conformance_matrix.py` (it is `slow`-marked and the bare suite deselects it) showing a full scenario row set for both leaves. Paste the updated `aw runs` description.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the call path proving `metrics` re-emits Order 02's projected facts and adds no second filter (a grep showing no new projector or sanitizer). Paste the allowlist refusing an unknown key. Paste the bundle field recording the projector version. Paste proof no anonymity claim appears in any label or manifest string.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for EACH of the twelve canary classes, that it is absent from the bundle because the field allowlist never named it (structural, not detected). Then paste the detector's result over the same bundle AND over the raw canaries, showing which classes it catches, and re-measure the coverage (one of twelve at review). Paste the shipped sanitizer report ENUMERATING the blind spots by name. A report claiming clean without that enumeration is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a deterministic manifest with per-file checksums, and the preview summarizing selected files by category with counts and bytes (re-measure the corpus scale; 472 prompt and 460 session files, about 238 MB at review). Paste proof `metrics` is the default tier and that `raw` carries no safety or anonymity label.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste each hostile archive member class (absolute path, `..` traversal, symlink, hardlink, device file, duplicate name) REFUSED before any write, with proof nothing was partially extracted. Paste the feature-detection for `tarfile.data_filter` and the FALLBACK path exercised (the 3.9 floor may lack it; CI tests 3.9). State that no archive precedent existed in the package.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the restricted opener's handler list showing no `file`/`data`/`ftp` handler. Paste a `file://` target, a `data:` target and a REDIRECT to each being REFUSED with an actionable message, and show the assertion FAILING against a naive `urlopen` implementation (measured: a bare `urlopen` returns file contents and data payloads). Paste proof the auth token never appears in argv guidance, output, logs, receipt or bundle.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste each validation failure class with its exit code and remedy. Paste the local receipt showing no secret. Paste the `unavailable` status returned when no endpoint governance is configured, which is the EXPECTED outcome today. Paste a grep proving no retry loop, queue or daemon exists. Paste cancellation, timeout, rejection, duplicate and interrupted cases each NOT retrying.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the attestation flag refused when ABSENT and recorded with attribution when present, in a NON-TTY shell. Paste proof no code path requires a TTY or asserts the operator is human, citing spec `20260815-0151-01`. Paste proof `--yes` alone authorizes neither a `raw` export nor a submission.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste an endpoint setting round-tripping and SURVIVING, plus the same test failing against the XDG user config (measured: `normalize()` drops the key). Paste the auth source stored as an environment variable NAME. Paste conservative defaults with analytics off, sampling a separate question, unattended local and no-submit, and unattended-with-incomplete-choices FAILING CLOSED. Paste cross-box correlation defaulted OFF (Order 02's deferred decision). Paste deletion removing only tool-owned analytics children via Order 01's containment predicate, with no source run touched.
  - Observed evidence:
  - Result: pending

Additionally, and NOT as a separate V-item because it validates no single E-item: V-09 must also carry bare `python3 -m pytest`, `git diff --check`, and the explicit conformance invocation (`tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py`), against the baseline the executor measured itself, comparing failing NODE IDS and never totals.

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: export sensitivity, network consent, and wizard defaults are one privacy boundary and must not be implemented independently. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. The three surfaces share a boundary, which is why they belong together; that does not make the declaration contract, the metrics tier, the redacted tier, the raw tier, the archive defenses, the transport, the submission validation, the consent model and the wizard one deliverable, which is why the nine items exist (F-9, and the Set orchestrator's own OQ-01 naming this plan's three trust surfaces).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved ixis0c --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until `mm5p3v` (Order 08) is `executed`. That dependency is load-bearing: Order 08 owns the `aw runs` leaf-registration pattern and the agent envelope these leaves emit through, and beneath it Order 02 owns the write-side projector this plan's `metrics` tier re-emits. Order 10 (`9xycbh`) documents what this plan ships, and its documentation must carry the detector's blind spots.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. `cli.py` and `command_surface.py` are high-traffic shared files and other agents work concurrently in this checkout; if either is being changed under you and the changes cannot be safely combined, STOP and report rather than overwriting.
- NEVER COMMIT A BUNDLE, A RECEIPT, OR ANY PART OF THE LIVE RUN CORPUS. Do not commit a canary as a literal either; generate it at test time or assemble it from fragments, as the detection engine does with its own patterns. Run `aw sanitize --agent` before treating any output as shareable, remembering it checks far less than this plan assumed.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory. TWO TRAPS SPECIFIC TO THIS PLAN: the bare suite DESELECTS the leaf-conformance gate (`pytest.mark.slow`), so a green bare run does not show your leaves are declared; and a clean `aw sanitize` report does NOT mean a bundle is clean, because the detector catches one of twelve canary classes. Never write a privacy claim the tests did not establish.
- RE-MEASURE EVERY NUMBER IN THIS PLAN. Every figure (one-of-twelve detector coverage, the ten fail rules, 129 declarations, the five `oc profile *` entries, the four-key config allowlist, 472 prompt and 460 session files at 238 MB, the 3.9 filter floor) is a review-time snapshot. Re-derive them.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

If endpoint governance remains unspecified, complete export and wizard work but implement submit as a tested unavailable capability, not an arbitrary generic uploader. SIX STOP CONDITIONS. If you are about to write that a tier "passes the sanitizer" as its privacy guarantee, STOP: it catches one of twelve canary classes, so the allowlist is the guarantee and the detector is corroboration. If structural allowlisting still cannot make `events-redacted` defensible, STOP and raise rather than editing `leak_sanitizer`, which backs `aw sanitize`, a pre-commit hook and a CI job. If you reach for a bare `urllib.request.urlopen`, STOP: its default opener resolves `file://` and `data:` and follows redirects, measured. If you gate consent on a TTY, STOP: implemented spec `20260815-0151-01` retired that pattern as dishonest and unusable from an agent shell. If a bare suite is green and you are about to report the leaves conformant, STOP: the gate is `slow`-marked and was not run. And if you find yourself building an optional-install mechanism, STOP: every analytics module ships in-package and the wizard gates enablement, not code presence.
