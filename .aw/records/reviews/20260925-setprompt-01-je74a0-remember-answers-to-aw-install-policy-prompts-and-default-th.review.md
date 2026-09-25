# Review: Remember answers to aw install policy prompts and default the layout migration to yes

- Subject-Id: je74a0
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

All claims verified at HEAD `d84334f8`. The plan cites `0c2e7970`, an ancestor; both were checked and
the measurements agree. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review. At `--phase review-finalize` it now reports exit 1 with exactly
two `IPD-Q501` errors, which are the two BLOCKING open questions this review added ON PURPOSE; every
`IPD-C801` citation advisory raised by the revisions was resolved by re-anchoring each citation to a
symbol or a quoted string. No structural defect remains.

THE PLAN'S OWN THREE FINDINGS ARE ALL TRUE AND I REPRODUCED EACH. `install --yes` on a scratch legacy
repo prints `continuing in compatibility mode` and leaves `.aw/system` absent (F-1). `config set
defaults.migrate_layout true` exits 2 with `Unknown config key`, and so does `defaults.leftovers`
(F-2). `cli._confirm`'s third parameter is `assume_yes` and its `[y/N]` is hardcoded in the `input()`
call, so a yes-default genuinely needs a new helper (F-3). The feature the plan designs is the right
one and the maintainer's two rulings are correctly recorded.

PR-B01 IS THE FINDING THAT CHANGES WHAT THIS PLAN IS. The migration this plan makes the unattended
DEFAULT is currently BROKEN for the repositories it targets. `layout_inventory.classify_item` falls
through to `block-unknown` for `.agents/skills`, the inventory raises one `unknown-owner` error per
path, and `execute_migration` raises `PreflightGateError`. That is already filed as backlog `72qlya`
(`open`, `Work-Kind: bug`, `Blocks-Release: next`), which the plan never mentions. I did not infer the
consequence, I MEASURED it: I patched a yes-default into `cli._handle_legacy_migration` in the
worktree, ran `install --yes` against two fixtures, and got a clean migration for the repo WITHOUT
`.agents/skills` and exit 1 with a `PreflightGateError` traceback for the same repo WITH it, `.aw/system`
never created. I then reverted the patch and confirmed `git diff` was empty. So the net effect of
landing this plan alone is that a command which today SUCCEEDS while printing a deprecation warning
instead CRASHES and installs nothing.

WHAT MAKES THAT A BLOCKER RATHER THAN AN EDGE CASE IS WHO IS IN THE CRASHING SHAPE. `.agents/skills` is
the intended skills directory for BOTH layouts (`engine.SKILLS_DIR`, and `engine.resolve_skills_dir`
returns it for either layout), which `tests/test_doctor.py` independently records as the reason
`.agents/` is a PERMANENT resident of a correctly migrated repo. I then checked the thing that decides
the blast radius: today's own keep-legacy `install --yes` on a bare legacy repo CREATES
`.agents/skills` (and `.aw/.gitignore`). So the tool manufactures the crashing shape itself, and the
very next install under the new default is the crashing case. This is why the plan now declares
`- Item-Dependencies: state:backlog:done:72qlya`, which a runner re-checks at dispatch, rather than
merely noting the bug in prose.

PR-B02 IS THE FINDING THAT MAKES THE CRASH WORSE THAN A FAILED MIGRATION. Nothing catches
`PreflightGateError` anywhere outside `layout_migration.py`, and the three install-time call sites
(two in `cli._handle_legacy_migration`, one in `cli._split_brain_guard`) call `execute_migration` bare.
I drove the fleet case because a single-repo test cannot show it: `install all --to-aw --yes` over two
configured repos, the FIRST holding `.agents/skills` and the second healthy, exited 1 with the traceback
and the SECOND repo was never installed at all. I verified that second repo installs fine when named
alone, which is what proves the stranding is caused by the escaping exception and not by the repo. One
bad repo therefore takes down an entire fleet update. E-04 was added to make all three sites fail soft,
sequenced BEFORE the default flips, and V-04 demands both halves of this evidence.

PR-B03 IS A DEFECT IN THE PLAN'S OWN DESIGN THAT I FOUND BY IMPLEMENTING IT. E-01 said to add both keys
to the allowlist, `CONFIG_SCHEMA` and `normalize`. I widened the allowlist and schema exactly as written
and then called the setter: `defaults.migrate_layout` persisted, and `defaults.leftovers` returned
`None` with NOTHING written to disk. The cause is that `config.normalize` filters `defaults` through
`isinstance(defaults.get(k), bool)`, so a string subkey is dropped AFTER the setter validated it, and
`set_config_value` then re-reads the normalized config and cheerfully reports `None` as success. The
failure is silent and the command exits 0, which is the worst shape: a user sets a preference, is told
`OK`, and the preference is not there. E-01 now requires a schema-driven widening of that filter, and
V-01 requires pasting the `defaults` mapping FROM DISK rather than the setter's own echo, because the
echo is precisely what lied.

PR-B04 WOULD HAVE FAILED THE SUITE ON THE FIRST RUN. Three tests in `tests/test_cli.py` pin the OLD
default and none were in the plan's scope or its test list.
`Order15CliTests.test_install_legacy_repo_unattended_defaults_to_keep_legacy` asserts that `--yes`
keeps the legacy layout AND that `.aw/system` does not appear, which is the exact inverse of the
contract this plan establishes. The other two patch `agent_workflows.cli._confirm`, which stops being
the prompt's code path once E-03 routes it through `_ask_policy`; that is the more insidious half,
because a mock that stops intercepting yields a GREEN test that proves nothing. I ran them to establish
the baseline: `5 passed, 59 deselected in 11.30s`. E-07 now owns repairing all three, and V-07 requires
positive evidence that the new patch target is actually reached.

PR-B05 IS THE HALF OF THE BACKLOG ITEM'S OWN REQUIREMENT THE PLAN LEFT UNBUILT. `kapm7y` point 4 says
the saved defaults must be "visible and resettable, or a user who answers once can never change their
mind without editing JSON". E-01 said `aw config set <key> -` "or the existing unset spelling, if one
exists". There is none: the `config` subparsers are show/get/set/add/remove/is/exclude, and I confirmed
the setter rejects `-`, `none`, `unset` and `""` for a bool key with `Invalid boolean value`. So as
authored the feature is write-once. E-02 now owns the clearing path with the distinction that matters
stated explicitly: clearing must REMOVE the subkey, because writing `false` is a real saved answer
meaning "keep the legacy layout" and is a different state from "never asked".

PR-B06 IS SMALL BUT IT IS THE DOCUMENT A USER READS. The plan scoped `docs/**` and named no file; I
grepped and `docs/` contains ZERO hits for `compatibility mode`, `keep-legacy` or `migrate-layout`,
while `README.md`'s "Bounded Legacy Compatibility & Deprecation Policy" section describes the old
default twice (migration is "interactively offer[ed]", legacy is kept "when running non-interactively
with `--keep-legacy`"). So the declared scope pointed at nothing and the real document was undeclared.
`README.md` is now in `Scope-Paths` and E-08 names both bullets.

F-7 IS THE LOOSE END I COULD NOT CLOSE AND DELIBERATELY DID NOT HIDE INSIDE THE DEPENDENCY. I isolated
a SECOND trigger for the same refusal using a fixture with no `.agents/skills` at all: a repo carrying
`.aw/.gitignore` fails with the sole error `partial-aw:.gitignore has unknown owner/disposition`.
`.aw/setup-repo-needed.md` behaves the same way, and today's install writes both. Backlog `72qlya`'s
text is specifically about `.agents/skills` and does not mention the `partial-aw` arm, so satisfying
this plan's dependency edge may STILL leave the default-migration path refusing. Folding this into the
dependency would have made the edge assert a safety it does not deliver, so it is OQ-04, `Blocking:
yes`, with the decision (widen `72qlya` or file a second item) left to the maintainer.

ON THE SPEC QUESTION, which I resolved myself and recorded rather than asking. The implemented
physical-layout spec's install-target contract says install MUST detect a legacy layout and OFFER
migration, and MAY keep updating legacy in place if the operator DECLINES. Read closely it constrains
the offer and the decline and says nothing about which way the prompt defaults or what an unattended run
must do, and Section 11.3 states the cutover intent this plan serves. So no amendment is required and
the plan declares no spec edit. I recorded it as OQ-05 anyway because the opposite reading is plausible,
and under that reading the spec is the artifact to change first.

ONE THING I CHECKED AND FOUND CORRECT, because the plan asserted it without evidence: `aw config show`
needs no change. It enumerates `CONFIG_SCHEMA` and renders `None` as `-`, and I confirmed both new keys
appear as `defaults.leftovers = -` and `defaults.migrate_layout = -` once registered. E-01 now records
that so an executor does not go looking for a display site to edit.

Backlog item `kapm7y` carries `- Blocks-Release: next`; the plan correctly inherits it, so the gate is
preserved by the handoff. The gate section now also says plainly that `72qlya` must NOT be closed by
this plan, since it is a bug this plan depends on rather than one it fixes.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | BLOCKER | UNDER-SCOPE | A. Correctness / D. Anti-regression | With a yes-default patched into `cli._handle_legacy_migration` at review: legacy fixture WITHOUT `.agents/skills` -> exit 0, `.aw/system` created; the SAME fixture WITH `.agents/skills/assess/SKILL.md` -> exit 1, `PreflightGateError`, `.aw/system` absent. `--to-aw --yes` fails identically today. Backlog `72qlya` (`open`, `bug`, `Blocks-Release: next`) already describes the cause. Patch reverted, `git diff` empty | THE DEFAULT THIS PLAN FLIPS TO LEADS INTO A SHIPPED CRASH, AND THE PLAN NEVER MENTIONS IT. `.agents/skills` classifies `block-unknown`, so the migration preflight refuses every repo carrying it. `.agents/skills` is the intended skills directory for BOTH layouts (`engine.SKILLS_DIR`, `engine.resolve_skills_dir`), and today's own keep-legacy install CREATES it, so essentially the whole installed base is in the crashing shape. Landing this plan alone converts `aw install --yes` from succeeding-with-a-warning into crashing-and-installing-nothing, which is strictly worse than the defect it fixes | C:Medium; U:High (an unattended install crashes); S:Low; F:High (the 2.0.0 upgrade path is the thing that breaks); Overall:High | OPEN | ESCALATED, not silently fixed. The classifier fix is outside these Scope-Paths and its disposition decision deserves its own review (the same reasoning `z1yefm` recorded when it filed `72qlya`). Plan now declares `- Item-Dependencies: state:backlog:done:72qlya` (lint conforming), Concern and gate state the crash, F-4/F-5/F-6 record the measurements, and OQ-03 is `Blocking: yes` naming this finding so the lint gate refuses the plan until the maintainer chooses between fixing `72qlya` first, relying on E-04's fail-soft, or adding a child plan |
| PR-B02 | BLOCKER | UNDER-SCOPE | A. Correctness / C. Operability | `install all --to-aw --yes` over two configured repos, the first holding `.agents/skills`: exit 1 with an uncaught `PreflightGateError` traceback, first repo unmigrated AND the second, healthy repo never installed; that second repo installs fine when named alone. grep: zero `PreflightGateError` handlers outside `layout_migration.py`; the three call sites are bare | THE CRASH IS UNCAUGHT AND KILLS THE WHOLE RUN, NOT JUST THE MIGRATION. `execute_migration` raises and nothing in `cli.py` catches it, so it escapes `main` as a traceback. In a fleet update one bad repo strands every repo queued after it, which a single-repo reproduction cannot reveal and which no item addressed. This holds independently of `72qlya`: any future preflight refusal has the same consequence | C:Low; U:High (a traceback is the user-facing outcome); S:Low; F:High (a fleet update silently stops partway); Overall:Medium | FIXED | Added E-04, sequenced BEFORE the default flip, to catch `PreflightGateError`/`StaleInputError` at all three sites, report a readable skip, and return the keep-legacy result so the batch continues. V-04 requires BOTH the single-repo traceback-to-skip evidence AND the two-repo fleet case with the second repo's `.aw/system` checked in both states, because the single-repo run cannot show the stranding |
| PR-B03 | HIGH | IN-SCOPE | A. Correctness / E. Testing | Widened `_ALLOWED_DEFAULT_KEYS` and `CONFIG_SCHEMA` exactly as E-01 said, then drove the setter: `set_config_value("defaults.leftovers","remove")` returned `None` and the on-disk `defaults` kept only `{backup, prune}`; `defaults.migrate_layout` persisted in the same run. Cause: `config.normalize`'s `isinstance(defaults.get(k), bool)` filter | E-01 AS WRITTEN CANNOT PERSIST `defaults.leftovers`, AND THE FAILURE IS SILENT. `normalize` drops a non-bool `defaults` subkey after the setter validated it, and `set_config_value` re-reads the normalized config and reports `None` while exiting 0. A user sets a preference, is told `OK`, and the preference does not exist. Found by implementing the item, not by reading it | C:Low; U:Medium (a silent no-op reported as success); S:Low; F:Medium (one of the plan's two keys does not work); Overall:Low | FIXED | E-01 now requires widening the filter per-key from the schema's `type_name`, keeps `normalize`'s documented fail-open direction for an out-of-enum value (as `color_depth` does), and specifies `allowed_values` as the declarative constraint rather than a setter branch. V-01 requires pasting the `defaults` mapping from disk, not the setter's echo, and requires the drop-versus-refuse pair. Recorded as F-8 and as a conventions bullet |
| PR-B04 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `Order15CliTests.test_install_legacy_repo_unattended_defaults_to_keep_legacy` asserts `--yes` keeps legacy and `.aw/system` is absent; `...interactive_decline_keeps_legacy` and `...interactive_accept_migrates_to_aw` patch `agent_workflows.cli._confirm`. Baseline `python3 -m pytest tests/test_cli.py -o addopts="" -q -k legacy` -> `5 passed, 59 deselected in 11.30s` | THREE EXISTING TESTS PIN THE OLD DEFAULT AND `tests/test_cli.py` WAS NOT EVEN IN SCOPE. One asserts the exact inverse of the new contract and fails the moment the default flips. The other two are worse: their patch target stops being the prompt's code path once `_ask_policy` lands, so they keep PASSING while intercepting nothing, which is a green test that proves nothing | C:Low; U:Low; S:Low; F:Medium (a mock that stops intercepting hides a real regression); Overall:Low | FIXED | `tests/test_cli.py` added to `Scope-Paths`; added E-07 to invert the unattended test and repoint the two interactive ones, with an explicit instruction not to weaken them. V-07 requires the baseline line plus, per test, positive evidence the new patch target is reached. Recorded as F-10 |
| PR-B05 | MEDIUM | UNDER-SCOPE | F. KISS and UX / G. Plan executability | `config` subparsers are show/get/set/add/remove/is/exclude (no `unset`); `set_config_value` on a bool key raised `Invalid boolean value` for each of `-`, `none`, `unset`, `""`. Backlog `kapm7y` point 4 requires the saved defaults be "visible and resettable" | THE FEATURE IS WRITE-ONCE AS AUTHORED, WHICH FAILS THE SOURCE ITEM'S OWN REQUIREMENT. E-01 hedged with "or the existing unset spelling, if one exists"; none exists, so nothing can clear a saved answer and a user who answers once cannot change their mind without hand-editing JSON. The hedge is what let the gap through | C:Low; U:Medium (write-once preference); S:Low; F:Low; Overall:Low | FIXED | Added E-02 owning the clearing path, with the load-bearing distinction stated: the clear must REMOVE the subkey, because `false` is a real answer meaning "keep legacy" and is not the same state as "never asked". V-02 requires the unset-versus-`false` evidence and a re-ask. A genuine stop condition covers the case where only writing `false` turns out to be reachable. Recorded as F-9 |
| PR-B06 | LOW | UNDER-SCOPE | G. Plan executability (documentation sync) | grep of `compatibility mode`/`keep-legacy`/`migrate-layout`: ZERO hits under `docs/`; `README.md`'s "Bounded Legacy Compatibility & Deprecation Policy" points 1 and 2 both describe the old default; `CHANGELOG.md` likewise | THE PLAN SCOPED `docs/**`, WHICH CONTAINS NOTHING RELEVANT, AND MISSED THE DOCUMENT THAT DOES. `README.md` tells users migration is offered interactively and that legacy is kept non-interactively with `--keep-legacy`. Shipping the new default without that edit leaves a shipped document contradicting shipped behavior | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `README.md` added to `Scope-Paths`; E-08 names both README bullets and states the zero-`docs/`-hits measurement so a grep returning nothing there is not mistaken for work done. V-08 requires the README diff covering both points. Recorded as F-11 |
| PR-B07 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: four sentences, no scope fence, no stop conditions, an unconditional finalize instruction, and no statement of what approval means beyond restating the ruling. V-02's evidence was "paste the helper's diff"; V-01 named `AW_HOME`, which does not locate the config file (`config.config_dir` reads `XDG_CONFIG_HOME`) | THE GATE CARRIED ONLY THE COMMIT RULE AND TWO VALIDATIONS COULD NOT SUPPORT THEIR CLAIMS. No fence, so finalize could not reconcile scope; unconditional finalize, contradicting runner ownership; a diff cannot demonstrate a precedence chain; and V-01's stated fixture would not have isolated the config file, so a test could have read or written the reviewer's real config | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: an approval paragraph separating the settled ruling from the newly found crash, a per-path scope fence naming `layout_inventory.py`/`layout_migration.py` as OUT and `docs/**` as expected-unmodified, the honesty rule naming the three easily faked claims here, two genuine stop conditions, conditional runner/executor finalize ownership, the `kapm7y` close with its inherited gate, and an explicit instruction not to close `72qlya`. V-03 now demands all three precedence rungs driven plus the save-failure path; every fixture reference switched to `XDG_CONFIG_HOME` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan flips a default into a code path I had not exercised. Trust the plan's scope, or drive the new default end to end? | Drive it: patch a yes-default into the worktree, run it against fixtures with and without `.agents/skills`, then revert. | (a) Review the diff-to-be on reasoning alone - rejected: the defect is in a module the plan does not touch and would not appear in any diff it produces. (b) Trust that `--to-aw` already works, since a flag for it exists - rejected, and this is the trap: `--to-aw --yes` is ALSO broken on the same repos, so an existing flag is no evidence the path works. | fixture without skills -> exit 0 migrated; with skills -> exit 1 `PreflightGateError`; patch reverted with empty `git diff`; backlog `72qlya` describing the same cause | yes |
| D-2 | Is the crash an edge case or the common case? | The common case: measure what today's own install creates. | (a) Treat `.agents/skills` as user-specific content - rejected: `engine.SKILLS_DIR` and `engine.resolve_skills_dir` make it the intended location for BOTH layouts, and `tests/test_doctor.py` records `.agents/` as a permanent resident of a migrated repo. (b) Assume an old repo may not have it - rejected after measuring: a keep-legacy `install --yes` CREATES it, so the tool manufactures the crashing shape. | two-step scratch run: `install --yes` -> `.agents/skills` present; then `install --to-aw --yes` -> `PreflightGateError` | yes |
| D-3 | PR-B01 is a BLOCKER whose fix is out of scope. Fix it here, defer it, or gate the plan? | Gate it: declare a machine-readable dependency edge AND raise a blocking open question. | (a) Fix `layout_inventory.py` here - rejected: outside `Scope-Paths`, and the `preserve`-versus-relocate disposition is a real decision that `z1yefm` already declined to take inside an unrelated plan. (b) Note it in prose only - rejected: prose gates nothing, and the runner would happily dispatch the plan. (c) Choose the sequencing myself - rejected: the three options trade a crash against a silent no-op on the 2.0.0 upgrade path, which is a release-scope judgement. | `aw ipd lint` conforming with `- Item-Dependencies: state:backlog:done:72qlya`; the `25kzda` spec's `state:<type>:<status>:<id6>` grammar; `IPD-Q501` firing on OQ-03 as intended | yes |
| D-4 | E-01 looked implementable as written. Accept it, or implement it to check? | Implement it in a scratch interpreter before accepting. | (a) Accept it - rejected, and it would have been wrong: the item is correct about the allowlist and schema and silently wrong about persistence. (b) Read `normalize` and reason - rejected: reading shows the bool filter, but only driving it reveals that `set_config_value` reports `None` and still exits 0, which is the part that makes the failure invisible. | `set_config_value("defaults.leftovers","remove")` -> `None`, on-disk `defaults` unchanged; the bool key persisting in the same run | yes |
| D-5 | Should the `partial-aw` trigger (F-7) be folded into the `72qlya` dependency? | No: record it as its own blocking question. | (a) Fold it in - rejected: `72qlya`'s text is specific to `.agents/skills`, so the edge would assert a safety it does not deliver and the plan could unblock while still crashing. (b) Report it as advisory - rejected: it can crash the plan's central behavior change, which is the definition of blocking here. | fixture with `.aw/.gitignore` and NO skills -> exit 1, sole error `partial-aw:.gitignore has unknown owner/disposition`; `72qlya`'s text | yes |
| D-6 | Does the implemented layout spec's "OFFER to migrate" forbid an unattended migration? | No: no amendment required, and no spec edit declared. | (a) Treat it as forbidding - rejected: the bullet constrains the offer and the decline, is silent on the prompt's default and on unattended behavior, and Section 11.3 states the cutover intent this plan serves. (b) Amend the spec to be safe - rejected: editing an implemented spec to permit what it never forbade would assert a contract change that did not happen. | the Section 11.3 install-target bullet beginning "When `aw install`/`aw update` runs in a repository that still has a legacy"; Section 11.3's "major-version physical cutover" | yes |
| D-7 | Three existing tests will break. Adjust them myself in the plan, or leave the executor to find them? | Name all three, with what changed and why it is not a weakening. | (a) Leave them - rejected: the executor meets a red suite with no context and the cheapest repair is deleting an assertion. (b) Name only the failing one - rejected, and this is the subtle half: the two `_confirm`-patching tests do NOT fail, they keep passing while intercepting nothing, so an executor fixing only the red test ships two tests that prove nothing. | the three test bodies; `5 passed, 59 deselected in 11.30s`; `_ask_policy` replacing `_confirm` on that path per E-03 | yes |
