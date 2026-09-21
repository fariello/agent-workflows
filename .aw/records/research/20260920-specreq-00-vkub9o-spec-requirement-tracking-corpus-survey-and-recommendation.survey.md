---
id: vkub9o
created: 20260920
set: specreq
order: 00
topic: [specs, requirements, attention, tracking]
model:
kind: survey
status: active
outcome: none-yet
summary: Measured survey of the 36-spec corpus requirement-id conventions, the retrofit cost by lifecycle state, four costed options, and a recommendation on whether spec requirements get machine-readable tracking
consumed-by: [si24ia]
---

# Should spec requirements get machine-readable tracking? A measured survey and a recommendation

Produced by plan `si24ia` (`- From-Backlog: f1sw71`), which deliberately DECIDES nothing and BUILDS
nothing. The maintainer's question was filed with an explicit non-commitment ("I'm not sure if having a
spec is sufficient, since we're not really going back to them for 'hey, what's in the specs that we still
need to address'. Maybe that should be a thing? Definitely not sure."), so the deliverable is a
measurement plus a recommendation the maintainer accepts or rejects.

- Measured at HEAD `96e93f8cc89514260cc729b8f32408ef6f5217d0`, 2026-09-20.
- Corpus at that HEAD: **36 specs**. Every number below is reproducible with the commands given.
- Nothing in `agent_workflows/` was changed. No spec was edited. No requirement id was retrofitted.

## 0. The headline, for a reader who stops here

**RECOMMENDED: option B-minus (a documented convention for NEW specs, no check rule, no parser, no
attention view), plus ONE cheap deterministic `aw check` rule that is NOT about requirement ids at all:
flag a plan graduated from a spec that omits `- From-Spec:`.** The measurement says the expensive part of
option C is not the parser and not the retrofit: it is the MISSING JOIN EDGE. 418 requirement ids already
exist across the corpus, but the link from plan to spec is absent on exactly the specs whose partial
implementation caused the maintainer's pain.

The decisive number is not the retrofit count. It is this: for spec `7ckptx`, where the link exists,
**42 of 42 requirements are already attributable to executed plans today, with no new mechanism at all**.
For `c4gd2h` and `6kwd2e`, which have 25 and 52 requirement ids respectively, **zero plans carry
`- From-Spec:`**, so no mechanism however good could compute their coverage. The gap is the edge, not
the ids.

## 1. Method, and why the method is itself a finding

The plan that commissioned this survey ran one grep per PRE-GUESSED requirement form and got the corpus
wrong in both directions: all six of its greps were anchored on a leading `- ` bullet, so a spec stating
requirements as bare line-start ids was invisible to every one of them, and the tree's most systematically
id'd spec was filed as prose-only. A fixed grep list cannot measure convention diversity, which is the one
thing this question turns on.

So the convention list here is DERIVED FROM THE FILES. Pass one takes the FIRST TOKEN of every non-blank
line of every spec (after stripping at most one leading bullet, table pipe, or heading marker), keeps the
tokens containing a digit, generalizes digit runs to `<n>`, and counts the resulting shapes. The
convention list falls out of that census rather than being guessed.

```
$ python3 derive_shapes.py | head -20
# specs enumerated: 36
  531  26specs  BARE <n>.
  322  33specs  HEAD <n>.
  259  25specs  HEAD <n>.<n>
  107  36specs  BULLET <n>-<n>-<n>
   62   2specs  BULLET **A<n>**
   53   3specs  TABLE <n>
   46   7specs  BULLET G<n>
   38   6specs  BULLET A<n>
   36  15specs  HEAD OQ-<n>:
   35   1specs  BARE R<n>.<n>
   35   1specs  BULLET **R<n>.<n>**
   32   5specs  BULLET F<n>
   32   5specs  BULLET OQ<n>
   30   2specs  BULLET A<n>.
   29   1specs  BARE <n>.<n>
   25   5specs  BULLET R<n>
   23   1specs  BULLET R<n>.
   23   2specs  BULLET **A-<n>**
   21   2specs  BULLET R-<n>
   17   3specs  BARE R-<n>.
```

The enumeration is RECURSIVE, because the `specdirs` Set (`1bdxcp`) proposes moving every spec into a
status subdirectory, which would make a flat glob go blind and a path-keyed table stale on arrival:

```
$ find .aw/records/specs -name '*.spec.md' | wc -l
36
```

Every table row below is therefore keyed by **id6 or filename stem**, never by path.

### 1.1 The three forms that actually exist

Three distinct addressing FORMS are in use, and the third is not a requirement id at all but is
nonetheless a working citation handle:

- **FORM A: letter-prefixed numbered id at a declaration site**, at any marker. Sub-forms vary only in
  prefix letter, dash, bold, table-cell placement, heading placement, and depth: `- R3 ...`,
  `R1.1 For an isolated turn...`, `| I-07 | ... |`, `- **R-12** ...`, `### R4. Layered enforcement`,
  `- G5 \`[Must]\` ...`, `- C1 \`[Must]\` ...`. **This is one convention with many spellings, not seven
  incompatible conventions.** That reframing matters for the cost, and it is the survey's second
  methodological finding: the earlier count of "six incompatible conventions" (later "seven") counted
  SPELLINGS of a single scheme.
- **FORM B: bare dotted-number paragraph ids**, e.g. `1.1 There is ONE universal artifact selector...`
  with no bullet. `z7nbn1` states every normative clause this way, 31 of them. This form is invisible to
  any letter-anchored grep and was missed by every prior count.
- **FORM C: numbered SECTIONS** used as the citation handle. Not a requirement id, but demonstrably a
  working addressing scheme: this repository cites `25kzda` by section in prose and IN CODE COMMENTS
  (`run_recovery.py:64` reads "spec 2.1's 0..10 bound"). 33 of 36 specs carry 5 or more numbered
  sections.

### 1.2 Distinguishing a requirement id from a non-requirement id

The prefix letter carries the meaning, and the mapping was read off the corpus rather than assumed:
`R`/`F`/`G`/`I`/`N`/`C`/`P`/`T`/`B`/`H` label normative requirements (goals, functional requirements,
invariants, criteria, non-functional notes); `A`/`AC` label ACCEPTANCE CRITERIA, `D` DECISIONS,
`OQ` OPEN QUESTIONS, `E` EVIDENCE, `PR` plan-review findings, `V` validation items. Counting `A*` as
requirements would roughly double the apparent id population while measuring the wrong thing, since an
acceptance criterion is a test of a requirement and not the requirement.

## 2. E-01: the per-spec table

Mechanical classification, one row per spec, all 36, keyed by id6-or-stem. `FORM A ids` counts DISTINCT
requirement ids at declaration sites; `T` marks a terminal spec (`implemented`/`superseded`/`parked`).

```
id6/stem-key	status	terminal	req-id families (FORM A)	FORM A ids	FORM B ids	sections	MUSTs	class
20260706-0000-01-pip-distribution-	implemented	T	(none)	0	0	0	3	needs-ids-invented
20260715-1722-01-agent-comms-conve	implemented	T	(none)	0	0	0	2	needs-ids-invented
20260725-0957-01-external-delivery	deferred	live	TABLE T<n>=4; BULLET R<n>=3	7	0	8	5	needs-reconciliation
20260726-1239-01-clean-delta-and-t	deferred	live	BULLET T<n>=3	3	0	12	1	parsable-as-is
20260726-1340-01-ipd-spec	implemented	T	(none)	0	0	0	5	needs-ids-invented
20260730-2152-01-agents-artifact-o	implemented	T	BULLET C<n>=6; BULLET F<n>=6; BULLET B<n>=3; BULLET G<n>=3; BULLET H<n>=3	21	0	30	2	needs-reconciliation
20260802-1904-01-ipd-structure-and	implemented	T	(none)	0	0	44	119	needs-ids-invented
20260808-0004-01-artifact-organiza	implemented	T	(none)	0	0	17	1	needs-ids-invented
20260808-1945-01-attention-registr	implemented	T	BULLET F<n>=13; BULLET G<n>=8; BULLET N<n>=6	27	0	25	25	needs-reconciliation
20260808-1958-01-prompt-purity-lin	approved	live	BULLET G<n>=6; BULLET P<n>=5; BULLET F<n>=5; BULLET R<n>=3; BULLET N<n>=1	20	0	13	0	needs-reconciliation
20260809-2211-01-aw-project-layout	superseded	T	(none)	0	0	64	68	needs-ids-invented
20260810-1447-01-physical-aw-hiera	implemented	T	(none)	0	0	20	25	needs-ids-invented
20260813-1833-01-attention-visible	implemented	T	BULLET G<n>=7; BULLET F<n>=5; BULLET N<n>=1	13	0	16	5	needs-reconciliation
20260815-0151-01-honest-human-appr	implemented	T	BULLET G<n>=7; BULLET F<n>=5; BULLET N<n>=1	13	0	12	2	needs-reconciliation
20260817-2124-01-records-taxonomy-	implemented	T	BULLET G<n>=7	7	0	9	2	parsable-as-is
20260817-2147-01-uniform-artifact-	implemented	T	BULLET G<n>=8	8	0	10	1	parsable-as-is
20260818-1525-01-command-surface-r	implemented	T	BULLET R<n>=7; BULLET G<n>=6	13	0	13	9	needs-reconciliation
20260818-1525-02-sidecar-metadata-	implemented	T	BULLET R<n>=6; BULLET G<n>=5	11	0	9	9	needs-reconciliation
20260818-1525-03-release-record-an	implemented	T	BULLET R<n>=6; BULLET G<n>=5	11	0	9	9	needs-reconciliation
5tapom	approved	live	BULLET B<n>=2; BULLET H<n>=1	3	0	10	0	needs-reconciliation
25kzda	approved	live	BARE R-<n>=1	1	0	57	17	parsable-as-is
4w7d6s	superseded	T	BULLET G<n>=7; BULLET I<n>=4	11	0	7	11	needs-reconciliation
pqsx96	draft	live	TABLE I-<n>=16; BARE I-<n>=3	19	0	14	4	needs-reconciliation
c4gd2h	implementing	live	BULLET R<n>=23; BULLET R<n>.<n>=2	25	0	15	8	needs-reconciliation
7ckptx	approved	live	BARE R<n>.<n>=42; HEAD R<n>=6	48	0	10	86	needs-reconciliation
kw5y2s	approved	live	(none)	0	0	24	10	needs-ids-invented
6m4kow	approved	live	BULLET R-<n>=16; TABLE R-<n>=11; BARE R-<n>=2	29	0	12	21	needs-reconciliation
77tr3o	approved	live	BULLET R-<n>=12	12	0	11	18	parsable-as-is
2vev8j	approved	live	BULLET C<n>=8; BULLET N<n>=5; BARE C<n>=1	14	0	19	4	needs-reconciliation
2lcqno	approved	live	BULLET N<n>=7	7	0	8	9	parsable-as-is
6kwd2e	approved	live	BULLET R<n>.<n>=42; HEAD R<n>=10	52	0	12	89	needs-reconciliation
w15vzb	approved	live	BULLET R-<n>=9; BARE R-<n>=1	10	0	16	2	needs-reconciliation
uonrjg	approved	live	HEAD R<n>.<n>=4	4	0	42	55	parsable-as-is
z7nbn1	to-review	live	(none)	0	31	9	9	parsable-as-is(form-B)
r07vma	approved	live	BARE R<n>=12	12	0	8	5	parsable-as-is
i4gpto	draft	live	BARE R-<n>=17	17	0	10	10	parsable-as-is

TOTAL specs: 36
  needs-ids-invented: 8 (live 1, terminal 7)
  needs-reconciliation: 18 (live 10, terminal 8)
  parsable-as-is: 9 (live 7, terminal 2)
  parsable-as-is(form-B): 1 (live 1, terminal 0)
  sum check: 36
TOTAL FORM A requirement ids: 418
TOTAL FORM B numbered-paragraph ids: 31
specs with NO '- Id:': 19 (live: 3)
specs with numbered sections (FORM C >= 5): 33
status tally: {'implemented': 15, 'deferred': 2, 'approved': 13, 'superseded': 2, 'draft': 2, 'implementing': 1, 'to-review': 1}
```

The three classes sum to the total: 8 + 18 + (9 + 1) = **36**. Confirmed by the `sum check` line.

### 2.1 The retrofit cost, split by lifecycle state, with the live figure as the headline

Nobody retrofits requirement ids into a spec whose work is finished, so a raw count overstates the cost.

| Retrofit class | All 36 | LIVE (the decisive figure) | Terminal (not retrofit work) |
|---|---|---|---|
| needs-ids-invented (prose MUST only) | 8 | **1** | 7 |
| needs-reconciliation (ids exist, >1 namespace) | 18 | 10 | 8 |
| parsable-as-is (one namespace, or FORM B) | 10 | 8 | 2 |
| **total** | **36** | **19** | **17** |

**The decisive number is 1, not 13 and not 6.** Exactly ONE live spec (`kw5y2s`) has no requirement-level
id of any form. The plan that commissioned this survey stated 13 of 28 specs "need ids INVENTED"; its
review corrected that to 6 live; the corrected measurement is **1 live**. The earlier figures were
inflated because they (a) counted terminal specs, (b) counted the bullet-anchored greps' misses as
prose-only, and (c) did not recognize FORM B or the `G*`/`C*`/`N*`/`I*` spellings of FORM A as
requirement ids at all.

The `needs-reconciliation` class is also softer than its name suggests. It is triggered by a spec using
MORE THAN ONE requirement namespace, which is usually a deliberate and meaningful split rather than an
inconsistency: `20260815-0151-01` carries `G*` goals AND `F*` functional requirements AND `N*`
non-functional notes, which is a coherent three-tier scheme, not drift. If a chosen convention admitted
prefixed families (`R`/`G`/`F`/`N`/`C`/`I`) rather than mandating a single letter, most of this class
would be parsable as-is.

### 2.2 Section-addressable specs (FORM C)

33 of 36 specs carry 5 or more numbered sections. The extreme cases are `25kzda` (57 numbered sections,
routinely cited as "`25kzda` 2.9" in prose and as "spec 2.1's 0..10 bound" in `run_recovery.py:64`),
`20260809-2211-01` (64), and `20260802-1904-01` (44). For a section-structured spec, "retrofit" may mean
DECLARING AN EXISTING SCHEME CANONICAL rather than minting parallel ids. Adopting what the corpus already
does is materially cheaper than asking anything to adopt something new.

### 2.3 Specs with no `- Id:`

```
specs with NO '- Id:': 19 (live: 3)
```

**19 of 36** carry no `- Id:` at all; **3 of those are live** (one `approved`
`20260808-1958-01-prompt-purity-lint`, and both `deferred` specs). The three live ones are what block a
`<spec-id6>.<req-id>` join key TODAY and are the immediate prerequisite for option C. The whole-corpus
figure of 19 is what answers whether an id6-keyed requirement scheme could ever address the HISTORICAL
corpus; it could not, without minting 19 ids, which is a records change the maintainer must authorize.
Pre-cutover legacy spec names are grandfathered, so this is not a defect of those files.

## 3. E-02: the harm that tracking would actually have prevented

### 3.1 The strongest case, and it is NOT one the plan named

**`7ckptx` is `approved` while all 42 of its requirements are already implemented by 8 executed plans.**
This is a live, measurable instance of exactly the drift the item describes, and it is stronger than any
case the item or the plan identified, because it is a spec whose implementation is COMPLETE and whose
status still says the work has not started.

```
$ python3 coverage_probe.py 7ckptx
spec 7ckptx: 20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
  spec Status: - Status: approved
  DECLARED requirement ids: 42
  plans carrying From-Spec: 7ckptx: 8
  ids cited by EXECUTED plans: 42
  ids cited by NON-executed plans only: 0
  DECLARED ids cited by NO plan at all: 0
```

The Set is complete and its own verification plan says so in writing. Plan `4fodkt`
(`20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.ipd.md`) V-09
records: "all 31 live acceptance criteria PASS with pasted output at HEAD `e299a9a5` ... all six children
are in `.aw/records/plans/executed/`" and "THE EXPLICIT SET VERDICT: the Set IS demonstrably complete
against spec `7ckptx` Section 4". It correctly did NOT set the spec `implemented`, because an agent may
not. So the spec has sat at `approved` since, and `aw attention` reports it as `ready`, i.e. as work
waiting to start.

This case cuts BOTH ways and both directions must be stated. It proves the drift is real and
user-visible. It ALSO proves that the coverage question was ANSWERABLE without any new mechanism: the ids
existed, the plans cited them, and a plan computed the reconciliation by hand and pasted the result. What
failed was not measurement; it was the status transition, which is deliberately reserved to the
maintainer.

### 3.2 The case the item named, re-verified, with its numbers corrected

`c4gd2h` holds up and is worse than filed:

```
$ grep -nE '^- (Date|Status|Blocks-Release|Id):' <c4gd2h>
3:- Date: 2026-08-29
4:- Status: implementing
5:- Id: c4gd2h
8:- Blocks-Release: next
$ grep -cE '^- R[0-9]+' <c4gd2h>
23
```

`implementing` since 2026-08-29, **22 days** at this measurement (the Concern says 9 days, the review
says 11; both are stale, which is itself the point about corpus numbers dating instantly), carrying
`- Blocks-Release: next`, with 23 requirement bullets. Its single workflow-history line records an
AMENDMENT to R12 rather than any implementation progress. And the decisive new datum:

```
$ python3 coverage_probe.py c4gd2h '\bR\d+[a-z]?\b'
  DECLARED requirement ids: 23
  plans carrying From-Spec: c4gd2h: 0
  DECLARED ids cited by NO plan at all: 23
```

**Zero plans carry `- From-Spec: c4gd2h`**, although 37 plans mention the id6 somewhere in prose. So for
the item's own sharpest example, no requirement parser however good could compute coverage: the join edge
does not exist. `6kwd2e` is the same shape and larger: 42 declared `R<n>.<n>` ids, 52 counting its `R<n>`
section headings, and 0 plans carrying `- From-Spec: 6kwd2e`.

That is the survey's single most important structural finding. **The blocker is the missing plan-to-spec
edge, not the missing requirement parser.**

### 3.3 The retry-budget case, and TWO citation errors rather than one

The substance holds, and it has MOVED since the plan was authored, so the plan's own datum is stale:

```
$ rg -n '\b(plan_retry|retry_budget_remaining)\s*\(' --type py -g '!tests/**' -g '!agent_workflows/run_recovery.py'
(no output)
$ rg -n 'validate_retry_budget\(' --type py -g '!tests/**'
agent_workflows/runner_shared.py:6636:            return run_recovery.validate_retry_budget(cli_value)
agent_workflows/runner_shared.py:6646:                return run_recovery.validate_retry_budget(policy_value)
```

One requirement in three implementation states inside one spec: the range check is WIRED, while
`plan_retry` and `retry_budget_remaining` have zero production callers. This is now tracked by TWO
backlog items, `trjfyy` (`graduated` to plan `xipfy1`) and the newer `eh91an` (`open`, filed 2026-09-20
from plan `zzcrlo` OQ-03), the second of which explains WHY the helpers are unreachable: they require a
`run_engine.RunEngine` over a hash-chained `ledger.jsonl` that neither driver has.

**Now the citation errors, and there are two, because the review's correction of the plan was ITSELF
wrong.** The plan cites "`25kzda` 2.1's retry budget" four times. The review's finding PR-305 declares
that wrong on the grounds that §2.1 is "Command grammar", and names §1.1 and line 586 as the correct
anchors. Measured:

```
$ grep -nE '^#{2,4} ' <25kzda> | awk -F: '$1<=211' | tail -3
162:### 1.4 Resolution of the required revisions
172:## 2. Selector resolution and mixed-type policy
174:### 2.1 Command grammar
$ sed -n '211p' <25kzda>
- `--retry-budget` is an integer from 0 through 10 inclusive. It counts automatic correction attempts
  after the initial execution attempt. ...
```

Line 211 IS inside §2.1. The plan's citation was CORRECT and the review's correction of it was wrong.
The 0..10 bound is in fact stated in FOUR different sections:

| Line | Section it falls in |
|---|---|
| 167 | `### 1.4 Resolution of the required revisions` |
| 211 | `### 2.1 Command grammar` |
| 691 | `### 4.1 Message and recovery conventions` |
| 1088 | `### 5.5 Retry policy` |

**This is the single best piece of evidence in the survey, and it argues for the CHEAP option rather than
the expensive one.** A plan about requirement addressability miscited a requirement; its reviewer
"corrected" the citation and introduced a second error; and the code comment says "spec 2.1's 0..10
bound" while the spec states that bound in four places. Three parties disagreed about where one
requirement lives. Note what would and would not have prevented this: a requirement PARSER would not have
helped, because the text carries no requirement id at any of the four sites. A stable ADDRESSING
CONVENTION would have, because there would have been one canonical handle to cite. The failure is an
addressing failure, not a coverage-tracking failure.

### 3.4 The strongest DISCONFIRMING case, stated because it may be the right answer

Three lines of evidence say whole-artifact status has been survivable.

**FIRST, the backlog workaround demonstrably works.** `trjfyy` tracked a split requirement as an ordinary
backlog item and graduated to plan `xipfy1`; when the same divergence recurred it was filed again as
`eh91an` with a fuller diagnosis. Two items, correctly filed, gated and visible in `aw attention`, with
no requirement mechanism involved. Backlog `f1sw71`'s own dependency note says routing obligations to
items and plans "works today", and it says so while ARGUING FOR this feature, which makes it a concession
rather than a claim.

**SECOND, and stronger: adjacent work priced this exact gap and deliberately shipped around it.** Plan
`jxxec8` implements the "minimum useful version" of a graduation guard and declines the
already-implemented verdict precisely because this tracking does not exist. Its own text:

> "The full classifier is NOT chosen because one of its three cases is mechanically unanswerable: there
> is no per-requirement tracking, a spec carries ONE whole-artifact status with no partial-implementation
> state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog
> `f1sw71` ... tracks that"

and it makes that limit part of its OUTPUT, not just its plan file: "ALREADY IMPLEMENTED is NOT
DETECTABLE, because there is no per-requirement tracking." `iuxtjy` and `y9s4vm` (the same Set) take the
same position. Three reviewed plans concluding "advisory is enough" is real evidence of survivability.

**Whether that is sufficiency or accumulated workaround cost is the judgement, and here is the honest
answer: it is BOTH, and which one dominates depends on the edge, not the ids.** `jxxec8` declined the
verdict for a reason that is only HALF true. It cited three gaps (no requirement tracking, no partial
state, no semantic verification). But for `7ckptx` the verdict WAS computable, by exactly the advisory
reverse index `jxxec8` builds, because that spec has the `From-Spec` edge on 8 plans. What made the
verdict unanswerable for `c4gd2h` was the MISSING EDGE, which `jxxec8` did not name as a cause.

### 3.5 Quantified waste

| Case | Cost, measured | Would tracking have prevented it? |
|---|---|---|
| `7ckptx` at `approved` with 42/42 built | A completed spec has been reported as `ready` (not-started) by `aw attention` for 3 days, since `4fodkt` finalized on 2026-09-17 (`git log -1 --date=short` on that plan file) | PARTLY. Coverage was computable; the transition is the maintainer's by design, so no mechanism closes it |
| `c4gd2h` `implementing` 22 days, release-gating | Item `1m3nul` had to caution its implementer to verify which stop levels existed; that verification ran the code and took a full plan turn | NO, not as specified. 0 plans carry `- From-Spec: c4gd2h`, so coverage is uncomputable regardless of the parser |
| retry budget in 3 states | 2 backlog items (`trjfyy`, `eh91an`) and 1 pending plan (`xipfy1`) filed over 15 days for one requirement | NO. The text carries no requirement id at any of its 4 sites; an ADDRESSING convention would have helped, coverage tracking would not |
| the citation error in this plan and its review | 2 wrong citations of one requirement, by an author and a reviewer, plus a third disagreement in a code comment | YES, by a stable addressing convention. NOT by a coverage mechanism |
| `jxxec8`/`iuxtjy`/`y9s4vm` declining the verdict | 3 reviewed plans wrote around the gap; each spent authoring effort explaining why | PARTLY, and the missing edge is the real cause for the specs where it matters |

**Which way does the evidence point? At the CHEAP END, and at a target the item did not name.** Three of
the five cases are ADDRESSING failures that a convention fixes and a coverage mechanism does not. One is
a MISSING-EDGE failure that no requirement mechanism can fix. Only `7ckptx` is a genuine coverage case,
and there the coverage was already computable.

## 4. E-03: the four options, at equal detail

### Option A: DO NOTHING

- **Authoring burden per new spec:** zero. This is the incumbent.
- **Retrofit burden:** zero.
- **Gaps closed:** none of the three. No per-requirement model, no partial state, `implemented` stays
  unverified semantically.
- **What it would have caught in section 3:** nothing, by construction. But note that it DID catch
  four of the five cases through other means: `trjfyy` and `eh91an` are filed items, `xipfy1` is a
  pending plan, `1m3nul` recorded its uncertainty, and `jxxec8` published its own limit. The incumbent
  is not silent; it routes to backlog items and plans, which `f1sw71` concedes "works today".
- **Failure mode:** silent. A spec sits half-built and nobody asks. Concretely: `7ckptx` at `approved`
  with 42/42 implemented, and `c4gd2h` release-gating at 22 days. Neither is visible AS a partial
  implementation; both are visible as long-sitting artifacts, which `aw attention` already shows.
- **Cost of choosing it:** the maintainer's question stays open forever, or is closed as decided.

### Option B-minus: A CONVENTION FOR NEW SPECS, NO CHECK RULE

- **Authoring burden per new spec:** near zero, because 18 of 19 live specs ALREADY do this. It writes
  down what the corpus does rather than asking for anything new.
- **Retrofit burden:** zero by construction (going-forward only). Optionally 1 live spec (`kw5y2s`) if
  the maintainer wants full live coverage.
- **Gaps closed:** gap 1 (no per-requirement model) for everything authored from now on, at the
  ADDRESSING level: a requirement becomes citable by a stable handle. Gaps 2 and 3 untouched.
- **What it would have caught:** the two citation errors in section 3.3, and the code-comment
  disagreement. Those are 3 of the 5 measured cases.
- **Failure mode:** an unenforced convention decays. Mitigation that is already load-bearing here: spec
  STRUCTURE is enforced by review, not by a rule, and `/plan-review` and the newer spec review
  (`6m4kow`) are the enforcement surface. Weaker mitigation than a rule, and honestly weaker.
- **What it does NOT do:** it cannot answer "which requirements are unbuilt", because it adds no
  coverage edge and no view.

### Option B: THE CONVENTION PLUS AN `aw check` RULE

- **Authoring burden per new spec:** as B-minus, plus keeping the corpus green.
- **Retrofit burden:** this is where it bites, and the dilemma is unavoidable. A rule over a corpus with
  non-conforming specs must either (i) EXEMPT them, in which case it proves little and a reader cannot
  tell a conforming spec from an exempt one, or (ii) FAIL CLOSED, in which case it **blocks unrelated
  work until the non-conforming specs are fixed**. Measured, option (ii) costs 1 live spec
  (`kw5y2s`) if the rule admits prefixed families, or 11 live specs if it mandates a single namespace.
  The grandfathering precedent exists (`aw check` grandfathers pre-cutover legacy spec names), so (i)
  with an explicit cutover date is the viable shape.
- **Gaps closed:** gap 1 at the addressing level, enforced. Gaps 2 and 3 untouched.
- **What it would have caught:** the same 3 cases as B-minus, more reliably.
- **Failure mode:** a `warning` in `aw check` EXITS NONZERO in this repository (`jxxec8` records this
  explicitly as a misreading to avoid), so a rule firing on legitimate specs would red every run and
  teach readers to ignore it. That is the failure mode that usually decides these questions.
- **Where it would touch:** a rule registers beside `check.from-spec-dangling`
  (`check_engine.py:129-131`, with the predicate at `:3817`). Not touched by this survey.

### Option C: THE FULL MECHANISM

Parsed requirement ids, a plan-side declaration of implemented requirements validated as resolvable, a
"requirements outstanding" view in `aw attention`, and `implemented` computed from coverage.

- **Authoring burden per new spec:** the convention, PLUS a per-plan declaration of which requirements it
  implements, PLUS keeping that declaration accurate as scope changes during execution. That last is the
  real cost and it recurs on every plan, not every spec.
- **Retrofit burden:** 1 live spec needs ids invented, 10 live need namespace reconciliation IF a single
  namespace is mandated, **3 live specs need an `- Id:` minted** before a `<spec-id6>.<req-id>` key can
  reference them at all, and 19 of 36 across the whole corpus. Then the REAL cost: the plan-to-spec edge
  must be added retroactively wherever coverage is wanted. Measured, `c4gd2h` (release-gating) has 37
  plans mentioning it and 0 carrying `- From-Spec:`.
- **Gaps closed:** all three, in principle. Gap 2 requires adding a value to `SPEC_STATUSES`
  (`attention_contract.py:269-281`), a nine-value frozenset pinned by totality tests in
  `tests/test_attention_contract.py`, so it is a CONTRACT change. Gap 3 (`implemented` computed from
  coverage) inverts the `APPROVAL_FLOOR` design, which states in its own words that `aw specs` enforces
  "presence + format + resolvability, NOT semantic verification that the work truly happened".
- **What it would have caught:** `7ckptx` cleanly, and that is one case. NOT `c4gd2h`, NOT the retry
  budget, NOT either citation error, because those fail for reasons a coverage mechanism does not
  address.
- **Failure mode, and it is the worst of the four:** a coverage number that is WRONG is worse than no
  number, because it is trusted. Coverage computed from plan-side declarations measures what plans CLAIM,
  not what shipped, which is the exact class of error `APPROVAL_FLOOR` refuses to make and which
  `jxxec8` refused to build for the same reason. And a `implemented` computed from declarations would let
  a spec reach `implemented` on the strength of plan prose, weakening a gate that today demands a
  resolvable artifact.
- **Where it would touch:** `SPEC_STATUSES` and `_SPEC_MAP` (`attention_contract.py:269-300`),
  `validate_spec` (`specs.py:211`), the `check_engine` rule table, and a new `aw specs` subcommand as a
  sibling of `check` (the surface today is `new`/`scaffold`/`set`/`note`/`check`/`migrate`). None touched.

### 4.1 The item's five questions, answered explicitly

**Q1. Do requirements get stable ids in the spec (`R1`..`Rn` / `G1`..`Gn`), and are they parsed?**
IDS YES, PARSING NO. They already have them: 418 distinct requirement ids exist across the corpus and 18
of 19 live specs carry them. What is missing is that the SPELLING is unstated, so an author invents one
and a citer guesses. Document the convention (admitting prefixed families `R`/`G`/`F`/`N`/`C`/`I`, since
that is what the corpus does) and do not build a parser yet: a parser's output has no consumer until the
join edge exists.

**Q2. Does a plan declare WHICH requirements it implements, and is that validated as resolvable?**
NO, AND THIS IS THE WRONG SECOND STEP. Measured, plans ALREADY cite requirement ids in prose heavily (the
8 `7ckptx` plans cite between 7 and 37 ids each), and that prose citation was enough to compute 42/42
coverage. The thing actually missing is one level up: the `- From-Spec:` bullet itself, absent on every
plan for `c4gd2h` and `6kwd2e`. Validate THAT edge before inventing a requirement-level field.

**Q3. Does `aw attention` gain a "requirements outstanding" view, or is this only an `aw check` rule?**
NEITHER, YET. A view needs coverage data, coverage needs the edge, and the edge is missing exactly where
it matters. Build the edge first; then the view is cheap and ITS value can be measured rather than
assumed.

**Q4. Is `implemented` then computed from requirement coverage rather than asserted?**
NO. Recommended against, on the design's own stated grounds. `APPROVAL_FLOOR` deliberately enforces
"presence + format + resolvability, NOT semantic verification", and coverage computed from plan-side
declarations measures claims rather than shipped behavior. `7ckptx` is the case in point: its coverage is
100 percent and a human still has to decide whether that means `implemented`, which is why plan `4fodkt`
reported rather than transitioned.

**Q5. Is the ~36-spec corpus large enough to justify it, and retrofit or going-forward?**
LARGE ENOUGH FOR A CONVENTION, NOT FOR THE MECHANISM. 19 live specs and 418 requirement ids is enough
material that inconsistent addressing already costs real citation errors (3 of 5 measured cases). It is
not enough that a parsed model plus a new status plus a computed `implemented` pays for its authoring
burden on every future spec and plan. GOING FORWARD, with the 1 live prose-only spec left alone; a
convention that demands 19 retroactive `- Id:` mints and a corpus rewrite would be a records change with
a worse cost/benefit than the problem.

## 5. E-04: the recommendation

**RECOMMENDED: option B-minus, plus one cheap deterministic check that is NOT about requirement ids.**

Concretely, and in this order:

1. **Document the requirement-addressing convention for NEW specs** in `.aw/records/specs/README.md`:
   a requirement carries a stable id at a declaration site, drawn from the prefixed families the corpus
   already uses (`R` requirement, `G` goal, `F` functional, `N` non-functional, `C` criterion,
   `I` invariant), and a section-structured spec MAY declare its numbered sections as the canonical
   handles instead (which is what `25kzda` already does in practice). No check rule. No parser. Enforced
   by spec review, exactly as spec structure already is.
2. **Add ONE `aw check` rule on the JOIN EDGE, not on requirement ids:** flag a plan whose Concern or
   Scope cites a spec id6 while the plan carries no `- From-Spec:`. This is the measured blocker, it is
   deterministic, it has an unambiguous fix, and it would make `c4gd2h`'s 37 edge-less plans visible.
   This item is NOT in `f1sw71`'s five questions, which is why it must be offered explicitly rather than
   smuggled in.
3. **Do NOT build:** a requirement parser, a plan-side requirement declaration field, a partial spec
   status, a requirements-outstanding attention view, or `implemented` computed from coverage.
4. **Separately, and independently of this decision:** `7ckptx` is demonstrably complete and sits at
   `approved`; its transition to `implemented` is the maintainer's call and plan `4fodkt` supplies the
   cited evidence. That is a one-command fix that delivers more of the item's stated value than any
   mechanism in this survey.

**Reasoning, tied to the evidence.** Of five measured harm cases, three are ADDRESSING failures that a
convention fixes and no coverage mechanism touches (section 3.3's two citation errors plus the code
comment disagreement). One is a MISSING-EDGE failure that no requirement mechanism can fix, on the
release-gating spec (`c4gd2h`, 0 plans with `- From-Spec:` out of 37 mentioning it). Only one is a
genuine coverage case (`7ckptx`), and there the coverage was ALREADY COMPUTABLE from existing citations
with no new mechanism, which is the strongest possible argument that option C would buy little: it would
have automated a calculation a plan performed by hand and pasted (section 3.1). Meanwhile the cost side
of option C is concrete: a pinned contract change to a frozenset with totality tests, 3 live specs
needing minted ids, 19 across the corpus, an inversion of `APPROVAL_FLOOR`'s explicit refusal to verify
semantically, and a recurring per-plan declaration burden whose accuracy nothing can check.

**The strongest argument AGAINST this recommendation, sourced from the evidence rather than invented for
balance.** `7ckptx` is a real, currently-live instance of the harm the maintainer described, and
B-minus does not fix it. A spec whose every requirement is built has been reported as `ready` (i.e. not
started) by the very tool whose job is to answer "what needs attention". If that pattern is COMMON rather
than singular, option C's cost starts to look proportionate, and this survey measured only one such case
because only one spec in the corpus has both requirement ids and the plan-side edge needed to detect it.
That is a genuine sampling limitation and it should be stated plainly: **the survey may be
under-detecting exactly the harm it is judging, because the detector requires the edge whose absence is
its own main finding.** A maintainer who weights that risk heavily should prefer option B with a
grandfathered cutover, which at least makes the addressing enforceable while the edge work proceeds.

A second, weaker counterargument: B-minus's enforcement is review, and review demonstrably missed a
citation error in this very plan AND introduced a second one while correcting it. An unenforced convention
in a repository that has just demonstrated its review surface is fallible is a weak guarantee.

**THE DECISION IS THE MAINTAINER'S.** This is a cost/benefit and authoring-burden judgement on a feature
its requester was openly unsure about, which places it squarely outside what an agent may settle. This
survey recommends; it does not decide, and it built nothing so that the decision remains fully open.

**If the maintainer accepts a mechanism** (option B or C), backlog `f1sw71` should be set `graduated`,
because the implementation is then a separate plan and the item's substance survives. **If the maintainer
accepts B-minus or option A**, `f1sw71` should be set `done`, because the open question is then answered
and closed; the item carries no `- Blocks-Release:`, so no gate is dropped either way. `f1sw71` is
already `graduated` today.

**Where a follow-on plan would amend a spec.** No spec governs spec AUTHORING today; the requirement-id
convention belongs in `.aw/records/specs/README.md`, not in a spec. A follow-on implementing option B or
C would declare that README (and, for option C, `attention_contract.py` plus its tests) in its
`- Scope-Paths:`. Nothing here amends any spec, and deliberately so: documenting the convention IS
implementing option B, which is not this survey's to do.

## 6. Reproducing this survey

Measured at HEAD `96e93f8cc89514260cc729b8f32408ef6f5217d0`, 2026-09-20. Corpus numbers move fast (27
specs at the item's filing, 28 at plan authoring, 29 at plan review, **36** here, in twelve days), so
re-derive rather than cite.

The four scripts used are small, read-only and stdlib-only, and are reproduced below for a reader who
wants to re-run rather than trust. They were run from the repository root.

- `derive_shapes.py` -- pass one, derives candidate id shapes from the files (section 1).
- `census.py` -- per-spec declaration-site id families with samples (section 1.2).
- `final_survey.py` -- the per-spec table and the class totals (section 2).
- `coverage_probe.py <spec-id6> [id-regex]` -- computes how far coverage is derivable TODAY from existing
  citations (section 3).

```
# corpus enumeration (RECURSIVE: the specdirs Set may move specs into status subdirectories)
find .aw/records/specs -name '*.spec.md' | wc -l

# the shape census that derives the convention list from the files
python3 derive_shapes.py

# the per-spec table plus class totals and the sum check
python3 final_survey.py

# coverage derivable today, per spec
python3 coverage_probe.py 7ckptx
python3 coverage_probe.py 6kwd2e
python3 coverage_probe.py c4gd2h '\bR\d+[a-z]?\b'

# the harm-case evidence
rg -n '\b(plan_retry|retry_budget_remaining)\s*\(' --type py -g '!tests/**' -g '!agent_workflows/run_recovery.py'
rg -n 'validate_retry_budget\(' --type py -g '!tests/**'
rg -l '^- From-Spec: 7ckptx' .aw/records/plans
rg -l '^- From-Spec: c4gd2h' .aw/records/plans     # empty
rg -l -- 'c4gd2h' .aw/records/plans | wc -l        # 37

# the structural claims
wc -l agent_workflows/specs.py                      # 1097
rg -n 'requirement|R[0-9]|partial' agent_workflows/specs.py   # 2 incidental hits, :1079 :1094
rg -n -A16 '^SPEC_STATUSES' agent_workflows/attention_contract.py   # :269-281, nine values
rg -n -A14 '^_SPEC_MAP' agent_workflows/attention_contract.py       # :290-300
rg -n -A10 'APPROVAL_FLOOR = ' agent_workflows/attention_contract.py # :523, the honest-limit text
aw specs --help                                     # new/scaffold/set/note/check/migrate
```

### 6.1 Structural claims, re-verified at this HEAD with the plan's numbers corrected

| Claim | Plan / item said | Measured here |
|---|---|---|
| `specs.py` size | 1066 lines (item: 1006) | **1097** |
| incidental `requirement` hits in `specs.py` | `:1048`, `:1063` | **`:1079`, `:1094`**, both about evidence-artifact resolution |
| `validate_spec` | `:211-326` | `:211` (unchanged start) |
| `SPEC_STATUSES` | `:241-253`, nine values, no partial state | **`:269-281`**, nine values, no partial state. HOLDS |
| `_SPEC_MAP` `approved`->ready, `implementing`->active | `:262-272` | **`:290-300`**. HOLDS |
| `APPROVAL_FLOOR` semantic-verification admission | `:453-463` | **`:523`**. Text verbatim: "aw specs enforces presence + format + resolvability, NOT semantic verification that the work truly happened" |
| `check.from-spec-dangling` is an id6 membership test | `check_engine.py:123-125` | **`:129-131`** (rule spec), predicate `check_from_spec_dangling` at **`:3817`**. HOLDS |
| corpus size / `approved` count | 28/6 authored, 29/7 at review | **36 total, 13 `approved`** |
| specs with no `- Id:` | 3 (plan), 19 of 29 (review) | **19 of 36, 3 live** |
| prose-only specs | 13 of 28 (plan), 14 of 29 with 6 live (review) | **8 of 36, 1 live** |
| `25kzda` retry budget section | plan: §2.1; review: §2.1 is wrong, use §1.1 | **plan was RIGHT**: line 211 is in §2.1. The bound appears in §1.4, §2.1, §4.1, §5.5 |
| `plan_retry`/`retry_budget_remaining` callers | zero outside their module | **zero**. HOLDS, now tracked by `trjfyy` AND `eh91an` |

### 6.2 Honest limits of this survey

- **The prefix-to-meaning mapping is a judgement, not a measurement.** `R`/`G`/`F`/`N`/`C`/`I` were read
  as normative and `A`/`AC`/`D`/`OQ`/`E`/`PR`/`V` as non-normative from reading the corpus. A different
  reading changes the id counts, though not the shape of the conclusion.
- **`needs-reconciliation` is a mechanical verdict and overstates.** It fires when a spec uses more than
  one requirement namespace, which is usually a deliberate goal/functional/non-functional split rather
  than drift. Under a convention admitting prefixed families most of that class is parsable as-is.
- **The coverage probe measures CITATION, not implementation.** `7ckptx`'s 42/42 means 42 ids appear in
  executed plans, which is why section 3.1 corroborates it with `4fodkt`'s pasted verification rather
  than resting on the number.
- **The survey may under-detect its own subject** (stated in section 5 as the counterargument): finding a
  partial-implementation case requires both requirement ids and the plan-side edge, and only one spec in
  the corpus has both.
- **This survey was produced by an agent in the same model family as the plan it executes**, so it is
  close to a self-review of that plan's premises and worth less than an independent measurement. It
  contradicts that plan and its review on four numbers, which is the reason to read the commands rather
  than the conclusions.
