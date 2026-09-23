- Id: knvpiv
- Status: open
- Set: gradtravers
- Priority: medium
- Work-Kind: chore
- Summary: Unify the two independent traversals of the source-to-Set graduation edge (reverse index vs check_graduated_to)

## Why this exists

ONE RELATIONSHIP IS WALKED TWICE, BY TWO SETS THAT NEVER MET. Orchestrator `y9s4vm`'s CID-7 required
that after BOTH the `graduate` Set and `setidhard`'s `bwgyum` landed, "there is exactly ONE mechanism
answering 'which plans belong to this source' and one answering 'which Set did this source become',
and the second consumes the first rather than re-walking the tree." Measured while executing plan
`yv4tb1`, both have landed and the second does NOT consume the first:

* REVERSE (`graduate` child `jxxec8`): `check_engine.build_graduation_reverse_index` walks
  `_iter_plan_ipds` + `_iter_spec_records`, keying `(kind, id6) -> [GraduationArtifact]`.
* FORWARD (`setidhard` `bwgyum`): `releases.check_graduated_to` builds its OWN `known_setids` with a
  SECOND `_iter_plan_ipds` pass, then `rglob("*.md")`s `backlog`/`specs`/`plans` itself.

Introspection at HEAD `0823163b`: neither `build_graduation_reverse_index` nor `graduation_cluster`
appears in `check_graduated_to`'s source, and `Graduated-To`/`parse_graduated_to` appear nowhere in
`build_graduation_reverse_index`'s.

THE ORDERING MAKES IT A MISSED OBLIGATION RATHER THAN A RACE. `jxxec8` finalized 2026-09-21T23:53:32
(`fe664b70`) and `bwgyum` finalized 2026-09-23T01:30:52 (`55a99b5c`), so `bwgyum` was the second to
land and the obligation fell on it. `build_graduation_reverse_index` was already present in
`check_engine.py` at `bwgyum`'s own finalize commit (verified: `git show 55a99b5c:...` contains its
`def`). `bwgyum`'s E-04 DID re-check the `graduate` Set as instructed, but checked the wrong signal:
its V-04 evidence records "`aw graduate` still does not exist (the `graduate` Set's plans
`y9s4vm`/`jxxec8`/`iuxtjy` remain in `pending/`)", which was stale for `jxxec8` and was in any case a
question about a VERB rather than about the reverse INDEX it was obliged to consume.

## Why this is NOT urgent, and why it is not a bug

NO OPERATOR CAN OBSERVE A WRONG ANSWER TODAY, so this is a `chore` and not a `bug` under the
user-perceptible-impact test. Measured on the live corpus: ZERO records declare `- Graduated-To:`
(only `backlog/README.md` mentions the string, as documentation), so `check_graduated_to` returns 0
findings and the two mechanisms share NO live input. The divergence is therefore latent. On a fixture
carrying one source with both directions the two AGREE (`forward=['fixset']`,
`reverse=['fixset']`), and the forward check correctly flags a dangling `nosuchset`.

## The design constraint any fix must respect

THE REVERSE INDEX CANNOT SIMPLY BECOME THE FORWARD CHECK'S RESOLUTION TARGET, which is the obvious
"fix" and is wrong. Measured: `build_graduation_reverse_index` sees 124 setids (it indexes only
artifacts that CARRY a `From-*` bullet), while `check_graduated_to`'s `known_setids` sees 328 setids
over 712 plan files. Substituting the index would make 204 legitimate setids read as dangling on an
`error`-severity rule. `check_graduated_to`'s own docstring also pins its resolution semantics
deliberately ("ANY setid carried by at least one plan file in ANY lifecycle directory"). So the
sharable unit is the underlying PLAN-SETID ENUMERATION (or a shared corpus pass), not the reverse
index's keyed output.

## Suggested shape

Factor the `_iter_plan_ipds` + `_parse_setid` sweep into ONE shared helper both consume, or let the
forward check accept an injected `known_setids`/index the way `graduation_cluster` already accepts an
optional `index`. Add a test asserting the forward and reverse directions agree for one source.

## Provenance

Found by plan `yv4tb1` (Set `graduate`, Order 03) discharging orchestrator `y9s4vm`'s E-02/CID-7.
`yv4tb1` is a verification plan and deliberately did NOT fix this: it declares no product-code
`Scope-Paths`, and a verification plan editing the code it verifies would put the fix and its only
check in one unreviewed change.

## Workflow history
- 2026-09-23 created (aw backlog): Filed by plan yv4tb1 (graduate Order 03) while verifying orchestrator y9s4vm's CID-7.
