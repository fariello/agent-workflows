# Review findings: plan yumxwz

- Subject-Id: yumxwz
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `cedab274` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after.
`IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review snapshot was
owed: `git status --porcelain` was empty at review start.

NO PRODUCTION FILE WAS MODIFIED BY THIS REVIEW. Every measurement was an in-process call against the
installed package plus `tempfile.TemporaryDirectory()` roots, or a read. Nothing was written to `tests/`,
`agent_workflows/`, or the tracked config. `git status --porcelain` showed only the plan and this record
before the commit.

THIS IS A HONEST, WELL-MEASURED PLAN AND ITS CENTRAL CLAIM IS CORRECT. It also does something unusual and
valuable: it refutes a conclusion an EXECUTED plan (`zx9dkq`) recorded as settled, and it does so with the
right measurement rather than by assertion. I re-derived every load-bearing claim. ALL CONFIRMED:

- **The allowlist divergence (F2).** `build_ruleset(REPO_ROOT)` carries 8 `allow_line_substrings`,
  `build_ruleset(<root with no allowlist>)` carries 4. The fail-rule NAMES are identical (8 both ways,
  `sorted(a.fail) == sorted(b.fail)` True), which is exactly why `zx9dkq`'s name-only comparison could
  not see this.
- **The outcome flip (F3).** On `"/ho"+"me/"+handle+"/VC/agent-workflows see hermes-agent-org/hermes"`:
  repo-root ruleset `[]`, allowlist-less ruleset `['home-path', 'private-repo', 'handle']`. Each half of
  the input is independently detectable (`home` alone gives `['home-path','handle']`, the token alone
  gives `['private-repo']`), so the mixed line is a genuine discriminator and not a contrivance.
- **Ordinary reachability (F4).** `resolve_allowlist_path(REPO_ROOT/'tests')` returns
  `tests/.aw/config/local-leaks-allowlist.toml`, which does not exist; `os.chdir('tests')` then
  `build_ruleset(Path.cwd())` yields the 4-substring ruleset inside the real repository.
- **F5's deleted-file account.** `git log --diff-filter=D -- tests/test_run_analytics_spa.py` names
  `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", and `PLANTED_HOME_PATH`,
  `CLEAN_CONTROL_PATH`, `_leaky_repo_path` occur nowhere in the tree outside plan prose.
- **F1's three call sites.** `tests/test_run_analytics.py:986`, `:992`, `:1072`, all
  `ls.build_ruleset(Path.cwd())`; two assert an empty finding list, one is the `fail`-severity control.
- **F6's precedent.** `tests/test_leak_sanitizer.py:46` and `tests/test_local_leaks.py:43` both
  `from tests.support import REPO_ROOT`; `tests/support.py:13` defines it as
  `Path(__file__).resolve().parent.parent`.
- **The refuted claim really is in the executed plan.** `zx9dkq`'s F6 reads "THE RULESET IS NOT
  LOCATION-DEPENDENT AT ALL", justified by "the SAME eight fail-rule names with an EMPTY difference".
  The plan's characterization of what that measurement missed is accurate.
- **The three affected tests currently PASS**, both from the repo root (`3 passed`) and with
  `cwd=tests` (`Ran 3 tests ... OK`), so this is a latent defect and the plan does not claim otherwise.

ONE THING THE PLAN GETS RIGHT THAT DESERVES NAMING: an outside-home `git clone` does NOT by itself
reproduce the coupling, because the allowlist is TRACKED (`git ls-files --error-unmatch` confirms) and so
travels with any clone. Simulated: a clone-shaped root outside `/home` yields 8 substrings and `[]` on the
mixed input, identical to the repo root. The coupling is driven by the ambient `cwd`, not by the checkout
location, which is precisely what F4 says and why E-02 requires the `cwd` demonstration separately from the
two-location test runs. V-03's two-location requirement is still worth keeping as a portability check; it is
just not the measurement that exposes this defect.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G (plan executability); E (verification) | plan E-01; `leak_sanitizer.run` signature; 11 vs 4 call-site counts in `tests/` | E-01's entry-point set named only `scan_text`, `scan_working_tree`, `build_ruleset`, omitting the top-level dispatcher `run(repo_root, ...)` which takes a root and builds the ruleset internally. Measured in `tests/`: 11 `ls.run`/`ll.run` sites vs 4 direct `build_ruleset` sites, so the sweep would have reported itself COMPLETE while missing the majority of real call sites. The conclusion is unaffected (all 11 pass `REPO_ROOT` or a scratch repo), but a sweep is a method obligation and the method was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names the full entry-point set including `run`; V-01 now requires the per-entry-point call-site counts so an omission is visible. Recorded as F10. |
| PR-002 | LOW | IN-SCOPE | A (correctness of the plan's own claim) | plan F3; scratch-root probe (11 vs 8 fail rules; `SEKRIT-42` -> `repo-pattern-0` vs nothing) | F3 asserted an allowlist absence "can only ever make a clean-side assertion fail, never silently pass". True of THIS repo's config (which sets only `allow_line_substrings`) but NOT of `build_ruleset`, which reads `fail_patterns`, `ip_enabled` and `hostname_fail` from the same resolved path. A wrong root can therefore SUPPRESS a finding. Left uncorrected, a reader concludes the failure mode is always safe-direction, which is the kind of premise that licenses a weakened assertion later. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F3 corrected in place with a pointer to the new F11; E-02 and V-02 gained a required part (d) demonstrating the suppression direction; the gate's FIRST prohibition reworded. |
| PR-003 | LOW | IN-SCOPE | G (plan executability) | plan E-03; `tests/test_run_analytics.py` import block; `grep REPO_ROOT` returning nothing; `tests/support.py:13` | E-03 said to replace `Path.cwd()` with "the module's existing repo-root anchor", but `tests/test_run_analytics.py` imports `tests.support` nowhere and contains no `REPO_ROOT`. The anchor had to be ADDED. An executor meeting this either invents an anchor or reaches for a second file, needlessly threatening the one-path scope fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the import must be added (or a local `Path(__file__)`-derived constant defined), names both precedent import sites, and confirms either choice stays inside the single declared scope path. V-03 now requires the anchor's import/definition be quoted. Recorded as F12. |
| PR-004 | MEDIUM | UNDER-SCOPE | D (anti-regression); E (testing) | `.aw/config/local-leaks-allowlist.toml` comment on the hermes entries; review probe driving the plant from `extra[0]` | E-04 needs a repo-allowlisted substring and its natural spelling hardcodes `hermes-agent-org/hermes`. That entry's own comment describes it as a transient public research citation, i.e. a line that may legitimately be deleted. If it is, the new regression fails pointing at a phantom LEAK rather than at its own stale premise, in a test whose entire purpose is to be a trustworthy location guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires the token be read from `load_repo_allowlist(<repo root>)` with a non-empty precondition assertion; verified at review that driving the plant from `extra[0]` reproduces the flip exactly. V-04 and a new gate prohibition (FIFTH) enforce it. Recorded as F13. |
| PR-005 | LOW | UNDER-SCOPE | G (execution contract) | plan gate, final paragraph as authored | The gate instructed the executor to "move this plan to `executed/` via `aw ipd finalize`" UNCONDITIONALLY. Under a runner the DRIVER owns the terminal transition, so an unconditional instruction tells an agent to do something it must not. The workflow names both the hand-rolled `git mv` and the unconditional finalize instruction as findings to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries a POST-GATE LIFECYCLE paragraph with conditional runner/executor ownership, the never-hand-edit-`Status:`/never-`git mv` prohibition, scope-gate guidance, and the backlog-closure rule (`rd2yh7` stays `graduated`, carries no release gate). |
| PR-006 | LOW | UNDER-SCOPE | C (operability); E (testing) | `build_ruleset` calling `load_user_hints()`; reload probe (8 -> 9 fail rules; clean string acquiring `user-hint-0`) | `build_ruleset` has a SECOND environment input the plan never mentions: `load_user_hints()` reads `<config_dir>/local-leaks-hints.json` (never committed) and registers each token as a `user-hint-N` FAIL rule, independent of `repo_root`. Absent on this machine, so nothing fails today. Unrecorded, an executor meeting a `user-hint-N` failure has no way to know it is not their bug, and the plan could be read as claiming these tests are hermetic against all environment inputs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F15 with the measurement, explicitly NOT filed as a carrier (the file is a deliberate personal escape hatch; a test that ignored it would defeat its purpose), and a SIXTH gate prohibition tells an executor not to chase it into `leak_sanitizer`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is the machine-local hints-file coupling (PR-006) a defect needing a backlog carrier, or a recorded scope note? | Record it as F15 with its measurement and an explicit no-carrier rationale | (a) File a backlog item, REJECTED because nothing is broken: the file is absent here, and `load_user_hints` is a documented, deliberate per-user escape hatch ("the never-committed, per-user layer" per the tracked allowlist's own header), so an `open` item describing intended behavior would be noise in the release-gate view. (b) Widen this plan to neutralize it, REJECTED as it would require editing `leak_sanitizer` or monkeypatching, both outside the one declared scope path and contrary to the plan's own correct position that the sanitizer is behaving properly | Measured: `load_user_hints()` is called unconditionally inside `build_ruleset`; with a hints file declaring `projected-facts` the fail-rule count goes 8 -> 9 and a string the projected-facts test treats as clean acquires `user-hint-0`. The file does not exist at `_config_dir()` on this machine. Follows the repository's established `Carrier-Declined` convention for a decision that leaves nothing broken | yes |
| D-2 | PR-002 shows a wrong root can SUPPRESS findings, not only add them. Does that change the plan's scope or verdict? | No scope change; correct F3 in place and require the demonstration in E-02/V-02 | (a) Treat it as a `leak_sanitizer` defect, REJECTED: reading config from the root you were handed is correct behavior, and the plan's own REVIEW NOTE already draws this fence properly. (b) Leave F3 as written, REJECTED because the overstated direction claim is exactly the premise that would later justify relaxing a clean-side assertion, which the plan elsewhere forbids | Measured on a scratch root declaring `fail_patterns = ["SEKRIT-[0-9]+"]` and `ip_enabled = true`: 11 fail rules vs 8, and `SEKRIT-42` yields `repo-pattern-0` (fail) under the correct root and nothing under the wrong one. This STRENGTHENS the case for E-03 rather than altering it | yes |
| D-3 | Does OQ-01 (`Blocking: no`, already `resolved`) need reopening or a maintainer answer? | No. Left exactly as authored | (a) Reopen to cover `local_leaks`, REJECTED: verified `tests/test_local_leaks.py:43` imports `REPO_ROOT` and `:121` calls `ll.build_ruleset(REPO_ROOT)`, so there is no live defect on that path and a regression there would guard nothing. (b) Mark the plan `NO-GO` for carrying an open question, INAPPLICABLE: it is `resolved`, and even were it open the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01) scopes that condition to an unresolved BLOCKING question | The question's own resolution is correct and independently verified at review; `local_leaks` re-exports the same engine and the coupling is a property of the ARGUMENT, not the alias, so the one E-04 regression covers the failure mode wherever it is reached from | yes |
| D-4 | An outside-home `git clone` does not reproduce this coupling (the allowlist is tracked and travels). Should V-03's two-location requirement be dropped as ineffective? | Keep it; add the explanation to the round narrative rather than weakening the plan | (a) Drop the two-location requirement, REJECTED: it is a genuine portability check, it is what `zx9dkq` used, and removing a validation requirement to save a step is precisely the weakening this plan forbids. (b) Replace it with a cwd-only check, REJECTED: E-02 already requires the cwd demonstration, so the two are complementary and the clone additionally guards against a `Path.home()`-style regression | Simulated a clone-shaped root outside `/home`: 8 allowlist substrings and `[]` on the mixed input, identical to the repo root; `git ls-files --error-unmatch .aw/config/local-leaks-allowlist.toml` confirms the allowlist is tracked. The cwd is the active variable, which is what F4 already states | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or `DEFERRED`,
so no `- Blocking: yes` escalation is owed either.
