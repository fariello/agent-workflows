# IPD: Sweep live specs against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 and MD-3 to MD-5 require a one-time proofread of every live spec against the writing standard, adding diagrams where requirement 12 applies (`ecmw83` R-04). Each swept spec must get one history line, and no status, approval, identity, or provenance field may change. Approved specs keep their status (MD-4). Measured at review (2026-11-06, context only; E-01 re-derives the set): 22 live specs (4 draft, 4 to-review including `ecmw83` itself, 11 approved, 2 implementing, 1 parked; no `reviewed/` or `deferred/` directory exists), about 15,400 lines and 1.65 MB.
- Scope: Proofread every spec whose status is `draft`, `to-review`, `reviewed`, `approved`, `implementing`, `deferred`, or `parked` at execution time; add or correct diagrams per requirement 12; append one `aw specs note` history line to every swept spec; write the sweep walkthrough; file one backlog carrier for any `Unresolved` annotation. EXCLUDES `implemented` and `superseded` specs (`ecmw83` N3); any change to a spec's title line or metadata fields (status, approval, `Blocks-Release`, `Id`, `From-*`, `Graduated-To`, and every other `- Key:` field before the first `## ` heading), requirement, acceptance criterion, or decision; any change to a heading, a stable ID, a fenced block that is not a Mermaid diagram, a `## Workflow history` record, or text that another tracked file quotes; and any change to the substance of recorded evidence or measured values.
- Scope-Paths: .aw/records/specs/draft/, .aw/records/specs/to-review/, .aw/records/specs/approved/, .aw/records/specs/implementing/, .aw/records/specs/parked/, .aw/records/walkthroughs/, .aw/records/backlog/open/
- Scope-Exceeded: .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md (live spec reviewed directory created after plan sfez3e authoring)
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 7
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sfez3e

## Workflow history
- 2026-11-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sfez3e verified (set writestd, attempt 1). [Scope reconciliation - out-of-scope .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md: live spec reviewed directory created after plan sfez3e authoring; in-scope-unmodified .aw/records/backlog/open/: declared-but-unmodified (auto-acknowledged by aw agy run)]

- 2026-11-09 note (sfez3e): swept 21 live specs against technical writing standard; added 7 Mermaid diagrams; no protected element changed; walkthrough u8dsej; metastore 4sd62s excluded per maintainer ruling
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): maintainer 2026-11-09 excluded Set metastore from this sweep ("Run all 3 except metastore"); added as a Deferred entry carried by 63ib9r.
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-07 reviewed (opencode/claude-opus): status reconciliation: /plan-review rounds 1-2 (runs run-20261106T033613Z-1047571, run-20261106T170833Z-1417128) recorded APPROVE WITH REVISIONS APPLIED and Readiness go-pending-approval but left Status to-review; the review-gated runner therefore blocked 381ml6
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; round 2 PR-101..PR-104 FIXED; review record .aw/records/reviews/20261025-writestd-07-sfez3e-sweep-live-specs-against-the-writing-standard.review.md
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-013 FIXED; review record .aw/records/reviews/20261025-writestd-07-sfez3e-sweep-live-specs-against-the-writing-standard.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live spec up to the writing standard once, without changing what any spec requires, and prove mechanically that no protected element changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Definitions used by every item below:

- BASE is the commit that E-01 records. Every comparison in this plan is against BASE.
- The guard is the script in `## Required tests / validation`. Save it once as `.aw/state/sfez3e/sweep_guard.py` (gitignored, inside the workspace) and run it from the repository root. With no spec arguments it checks every spec that was live at BASE; with spec paths it checks only those.
- A spec unit is the work for ONE spec, done in this order: (1) proofread the spec per the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md` and its numbered requirements; (2) apply requirement 12: add a Mermaid entity diagram (`erDiagram` or class diagram) or a flow or state diagram (`flowchart` or `stateDiagram-v2`) only where its criteria apply and no diagram covers that content, and correct an existing diagram that disagrees with the text (the text is normative); (3) where a passage's meaning cannot be established, keep the original text and add an adjacent block-quote line `> **Unresolved (SW-NN):** <the ambiguity>. Decision needed: <what must be decided>.`, numbering `SW-01` upward across the whole sweep (`ecmw83` R-11); (4) run `aw specs note <spec path> --message "proofread per the technical writing standard (spec ecmw83 R-08); meaning unchanged"`, appending `; N Unresolved annotations` when step 3 added any (the verb takes a file path, not an id6); (5) run the guard on that spec and fix every reported problem by restoring the original text; (6) commit the spec alone with `aw commit sfez3e -m "sweep(writestd): proofread spec <id6> (sfez3e)" -- <spec path>`.
- Do not change, in any spec unit: the title line and the metadata fields (every `- Key:` line before the first `## ` heading, with its indented continuation lines); any heading text; any stable ID such as `R-08`, `AC-06`, `MD-4`, `OQ-01`, `F-12`, `F-0004`, a decision number such as `D140`, or an id6 such as `25kzda`; any inline code span; any number; any fenced block that is not a Mermaid diagram; any `## Workflow history` record; any text that another tracked file quotes; any `must`, `should`, `may`, `shall`, or `never`, with or without a following `not` (do not swap, drop, or negate one). Prose paragraphs before the first `## ` heading are not metadata; proofread them like any other prose. The guard enforces each of these. Where the guard blocks a fix you judge necessary, keep the original and list the case in the walkthrough.
- Dashes: the `AGENTS.md` execution contract exempts specs from the dash rule, and the shipped standard adds no dash rule of its own (maintainer ruling, `g4719s` OQ-02). Spec `ecmw83` AC-06 still requires that no swept spec carries a `spec.prose-dash` advisory outside quotations and recorded evidence. So reword a prose em or en dash that the advisory reports, unless the guard protects the text; do not search for dashes otherwise.

### Task group 1: baseline

- [x] E-01 Confirm the record format first: `.aw/config/project.json` carries no `metadata_schema` key of 2 or more, and every live spec has a `- Status:` line and a `## Workflow history` heading. If either fails, the metadata cutover (plan `cxxmyv`, spec `4sd62s` Section 5.2) has landed, the guard and `aw specs note` no longer read or write the format this plan assumes, and the executor stops and reports that this plan needs revision. Then record the baseline: `git rev-parse HEAD` as BASE; the `aw check all --agent --verbose` list of `error` diagnostics (rule and location, sorted); `aw find specs --status-not implemented --status-not superseded` as the live set with statuses; `aw specs check --agent` with its `spec.prose-dash` advisory count; and one full guard run at BASE, which must report `problems=0`. Save each output under `.aw/state/sfez3e/` for E-05.
  - Depends on: none
  - Expected outcome: the format check passes; BASE and the four outputs are saved; the live set is re-derived at execution time rather than taken from this plan; the guard reports zero problems at BASE.
  - Execution state: performed

### Task group 2: sweep

- [x] E-02 (spec `ecmw83` R-08, `ecmw83` R-04, `ecmw83` R-11) Do one spec unit for each live spec from E-01 whose file is smaller than 100,000 bytes, in path order. At review this was 17 specs, about 586 KB.
  - Depends on: E-01
  - Expected outcome: each of these specs has its own `aw commit` holding only that spec, one new sweep history line, and a guard line with `problems=0`.
  - Execution state: performed

- [x] E-03 (spec `ecmw83` R-08, `ecmw83` R-04, `ecmw83` R-11) Do one spec unit for each live spec from E-01 whose file is 100,000 bytes or larger, in path order. At review this was 5 specs (`1tx9t8`, `18hh1u`, `4sd62s`, `yfz5u9`, `25kzda`), about 1.06 MB. Read each such spec section by section. If a turn ends before this item finishes, the committed spec units stand; resume at the first live spec without a sweep history line.
  - Depends on: E-01
  - Expected outcome: each of these specs has its own `aw commit` holding only that spec, one new sweep history line, and a guard line with `problems=0`.
  - Execution state: performed

### Task group 3: proof and report

- [x] E-04 (spec `ecmw83` R-08) Run the full guard with `--final`: `python3 .aw/state/sfez3e/sweep_guard.py <BASE> --final`. It checks every spec live at BASE for all protected elements and for exactly one new sweep history line. Then run `aw specs check --agent`.
  - Depends on: E-02, E-03
  - Expected outcome: the guard exits 0 with `problems=0` for every spec; `aw specs check` reports that all specs conform; no `spec.prose-dash` advisory remains outside quotations and recorded evidence.
  - Execution state: performed

- [x] E-05 (spec `ecmw83` AC-08) Write the walkthrough with `set_records.write_walkthrough(Path("."), set_id="writestd", order=7, target_id6="sfez3e", slug="spec-sweep", body=...)`, which mints the walkthrough's own id6 and records `- Target-Id: sfez3e` (`DECISIONS.md` D140). The body holds: a table of the specs swept (id6, status, lines changed, diagrams added or corrected, `Unresolved` count); every `Unresolved` annotation with its spec, section heading, and `SW-NN`; every case where the guard blocked a fix; and the E-01 and E-04 outputs. Commit it with `aw commit sfez3e -m "sweep(writestd): spec sweep walkthrough (sfez3e)" -- <walkthrough path>`.
  - Depends on: E-04
  - Expected outcome: one walkthrough named `YYYYMMDD-writestd-07-<own id6>-spec-sweep.walkthrough.md` exists and is committed; `aw check all` reports no `check.id6-identity-slot` finding for it.
  - Execution state: performed

- [x] E-06 (spec `ecmw83` R-11) If E-02 or E-03 added any `Unresolved` annotation, file one backlog carrier that lists every `SW-NN` with its spec and heading: `aw backlog new --summary "Resolve Unresolved annotations from the writestd spec sweep" --priority medium --work-kind followup --body "<list>" --apply`, then commit it with `aw commit sfez3e -m "backlog: carrier for writestd spec sweep Unresolved annotations (sfez3e)" -- <item path>`, and add its id6 to the walkthrough. If none were added, write "No Unresolved annotations; no carrier filed." in the walkthrough.
  - Depends on: E-05
  - Expected outcome: every `Unresolved` annotation is listed in one tracked, open backlog item, or the walkthrough states that there are none.
  - Execution state: performed

- [x] E-07 (spec `ecmw83` AC-06) Run `aw check all --agent --verbose` and compare its `error` list with the E-01 baseline; run the routine gate `python3 -m pytest`; run `aw sanitize --agent`; commit any walkthrough update with `aw commit sfez3e -- <walkthrough path>`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: no `error` diagnostic exists that was absent at BASE; the routine gate passes; the sanitizer reports no finding in any file this plan changed; no path outside the swept specs, the walkthrough, and the carrier item was committed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Read `.aw/system/workflows/technical-writing/technical-writing.md` in full before E-02 and apply its "Proofreading procedure" section (added by Order 01 `g4719s` E-03) and requirement 12 (`g4719s` E-02).
- A writing correction does not authorize a change to scope, obligations, approval, status, or recorded evidence (standard section "How it combines with other rules", items 2 and 3; spec `ecmw83` R-08).
- Spec status and history are owned by `aw specs`; append history only with `aw specs note <spec path>`, and never hand-edit a status line.
- Walkthroughs dated after the `walkthrough_id6` cutover (2026-09-27, `.aw/config/project.json`) use the clustered name with their own id6 and `- Target-Id:` (`.aw/records/walkthroughs/README.md`, D140). A walkthrough is not tracked by `aw attention`, so an open obligation must also live in a tracked carrier (E-06).
- Commit only through `aw commit`; one spec per commit, so a reviewer can read each diff alone and a resumed turn keeps finished units.

## Findings

- Largest live specs at review: `25kzda` (1,805 lines, 259 KB), `yfz5u9` (2,149 lines, 255 KB), `4sd62s` (2,373 lines, 250 KB), `18hh1u` (1,467 lines, 189 KB), `1tx9t8` (684 lines, 110 KB). Seven live specs already carry Mermaid diagrams (`4sd62s` has ten); E-02 and E-03 check them rather than replace them.
- `yfz5u9` and `4sd62s` already carry 2026-10-25 proofread notes against the maintainer's draft requirements; this sweep still proofreads them against the shipped standard, including requirement 12, and adds its own note.
- Text in live specs that other tracked files quote at review: 1,322 distinct passages (665 in `25kzda`). The guard keeps them unchanged, so a rewording never breaks a quoted-text citation.
- `aw specs note` refuses an id6 (`aw specs note or061f` printed "cannot read or061f: [Errno 2] No such file or directory"); it needs the spec path.
- Live specs held two prose em dashes at review, both on one line of `4sd62s` (section 1 table, row "Tracked `.md` records under `.aw/records/`").
- Spec `k3yx72` is amended by Order 06 (`e4n4p3` E-06) and spec `ecmw83` by Orders 01 and 02 before this plan runs; the sweep proofreads the amended text. Pending plans `7ehv8l` and `cxxmyv` (Set `metastore`) also edit `4sd62s` and `2vev8j`; the runner's merge-and-revalidate gate integrates the commits, and the guard keeps the text those plans quote. `cxxmyv` is different in kind: it runs migration `m0001`, which deletes every record's bullet block and `## Workflow history` section (spec `4sd62s` Section 5.2 step "Delete the legacy bullet block") and stamps `metadata_schema: 2`. After it lands, the guard's metadata and history checks read nothing and `aw specs note` targets a format that no longer exists, so E-01 checks the format before any spec unit starts.
- Round 2 review (2026-11-06) re-ran the guard on a scratch clone. The round 1 guard compared every line before the first `## ` heading, so it refused any proofreading of prose preambles (10 live specs have them; `25kzda` has 104 such lines), and it counted `must` without `not`, so `must` to `must not` and `must not` to `must` passed with `problems=0`. The revised guard compares only the title and `- Key:` fields, counts `must`, `should`, `may`, `shall`, and `never` with and without `not`, and protects decision numbers, four-digit stable IDs, and bare id6 references; each mutation above now reports a problem and exits 1, and an unchanged tree reports `problems=0`.

## Proposed changes (ordered, validatable)

1. Baseline and guard at BASE (E-01).
2. Sweep small specs, then large specs, one committed spec unit each (E-02, E-03).
3. Prove every protected element unchanged and every spec noted (E-04).
4. Report, carry unresolved annotations, check, and commit (E-05, E-06, E-07).

## Deferred / out of scope (with reason)

- Spec `4sd62s` (artifact metadata store) and any spec of Set `metastore`: EXCLUDED from this sweep by the maintainer (2026-11-09, "Run all 3 except metastore"), because the Set is mid-redesign (spec amended 2026-11-07 with C12/5.2a/AC-42; its plans are being re-split). Record it with a skip line naming this reason, as for a spec held by a live run, and proofread it when the metastore re-design settles.
  - Carrier: 63ib9r
- Terminal specs: out of scope by spec `ecmw83` N3.
  - Carrier-Declined: deliberate non-goal of the spec.
- Spec `ecmw83` Section 5.1 flowchart node "Run the advisory check. Fix reported dashes outside quotations and evidence." and AC-06's dash clause still describe the widened dash rule that the maintainer did not keep (`g4719s` OQ-02). This plan satisfies AC-06 as written and does not amend it, because AC-06 also governs Orders 08 and 09.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none after review. The review added the guard (meaning-preservation proof), a history line for every swept spec rather than only changed ones (`ecmw83` R-08), the backlog carrier for `Unresolved` annotations, the sanitizer run, and the D140 walkthrough name.

## Required tests / validation

`aw specs check`, `aw check all` against the E-01 baseline, the guard below, the routine gate `python3 -m pytest`, and `aw sanitize --agent`.

The guard (save verbatim as `.aw/state/sfez3e/sweep_guard.py`; usage `python3 .aw/state/sfez3e/sweep_guard.py <BASE> [--final] [spec path ...]`; exit 0 means no problem). It reports, per spec, the protected elements that changed between BASE and the working tree. Measured at review: a full run takes about 40 seconds and reports `TOTAL live=22 checked=22 problems=0` at HEAD `2f2b01f35` (round 1) and at HEAD `30b49d36c` (round 2, revised guard). In a scratch clone, each of these was reported with exit code 1: a status change, a changed `- Scope:` continuation line, a removed stable ID, a removed `D148`, a removed history line, a changed quoted passage, `must` changed to `should`, `must` changed to `must not`, and `must not` changed to `must`. A reworded preamble paragraph in `25kzda` reported `problems=0` and exit 0.

```python
"""Sweep guard for plan sfez3e: compares every live spec at BASE with the working tree."""
import collections, re, subprocess, sys

base, final = sys.argv[1], "--final" in sys.argv
only = {a.split("/")[-1] for a in sys.argv[2:] if not a.startswith("--")}
NOTE = "proofread per the technical writing standard"
def git(*a, inp=None):
    return subprocess.run(["git", *a], input=inp, capture_output=True).stdout
names = git("ls-tree", "-r", "--name-only", base).decode().split()
live = [p for p in names if p.startswith(".aw/records/specs/") and p.endswith(".spec.md")
        and p.split("/")[3] not in ("implemented", "superseded")]
texts = [p for p in names if p.endswith((".md", ".py", ".json", ".toml", ".yml", ".yaml", ".txt"))]
raw, old, i = git("cat-file", "--batch", inp="".join(f"{base}:{p}\n" for p in texts).encode()), {}, 0
for p in texts:
    nl = raw.index(b"\n", i); head = raw[i:nl].split()
    if head[-1] == b"missing": i = nl + 1; continue
    n = int(head[2]); old[p] = raw[nl + 1:nl + 1 + n].decode("utf-8", "replace"); i = nl + 2 + n
quote = re.compile(r'"([^"\n]{20,400})"')
quoted = collections.defaultdict(set)
for p, t in old.items():
    for q in quote.findall(t):
        if " " in q and "-sfez3e-" not in p: quoted[q].add(p)
stable_id = re.compile(r"\b(?:[A-Z]{1,4}-\d{1,4}[a-z]?|D\d{2,4}|(?=[a-z\d]*\d)(?=[a-z\d]*[a-z])[a-z\d]{6})\b")
code_span = re.compile(r"`[^`\n]+`")
number = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*")
modal = re.compile(r"\b(?:must|should|may|shall)(?:\s+not)?\b|\bnever\b", re.I)
key = re.compile(r"- [A-Z][\w/ -]*:")
def fields(pre):
    out, cont = [], False
    for l in pre:
        if l.startswith("# ") or key.match(l): out.append(l); cont = True
        elif cont and l[:1] in " \t" and l.strip(): out.append(l)
        else: cont = False
    return out
def parts(t):
    lines = t.splitlines(); end = next((k for k, l in enumerate(lines) if l.startswith("## ")), len(lines))
    heads, fences, mermaid, hist, cur, fence, inhist = [], [], 0, [], [], None, False
    for l in lines[end:]:
        s = l.strip()
        if fence is not None:
            cur.append(l)
            if s.startswith(fence):
                block = "\n".join(cur); cur, fence = [], None
                if block.lstrip()[3:].startswith("mermaid"): mermaid += 1
                else: fences.append(block)
            continue
        if s.startswith(("`" * 3, "~" * 3)): fence, cur = s[:3], [l]; continue
        if re.match(r"#{1,6} ", l): heads.append(l); inhist = s == "## Workflow history"; continue
        if inhist and l.startswith("- "): hist.append(l)
    return fields(lines[:end]), heads, fences, mermaid, hist
by_name = {p.split("/")[-1]: p for p in git("ls-files", ".aw/records/specs").decode().split()}
problems = 0
for p in live:
    if only and p.split("/")[-1] not in only: continue
    now_p = by_name.get(p.split("/")[-1])
    if now_p is None: print(f"{p}\tGONE"); problems += 1; continue
    o, now = old[p], open(now_p, encoding="utf-8").read()
    om, oh, of, omer, ohist = parts(o); nm, nh, nf, nmer, nhist = parts(now)
    prot = [q for q, srcs in quoted.items() if (srcs - {p}) and q in o]
    oc, nc = collections.Counter(stable_id.findall(o)), collections.Counter(stable_id.findall(now))
    added = sum(1 for h in (collections.Counter(nhist) - collections.Counter(ohist)).elements() if NOTE in h)
    errs = ["metadata block changed"] if om != nm else []
    errs += [f"status directory changed: {now_p}"] if now_p != p else []
    errs += [f"heading changed or removed: {h}" for h in collections.Counter(oh) - collections.Counter(nh)]
    errs += [f"non-diagram fenced block changed: {f[:60]!r}" for f in collections.Counter(of) - collections.Counter(nf)]
    errs += [f"history line changed or removed: {h[:80]}" for h in collections.Counter(ohist) - collections.Counter(nhist)]
    errs += [f"stable id removed: {k}" for k in sorted(set(oc) - set(nc))]
    errs += [f"inline code span removed: {k[:60]}" for k in sorted(set(code_span.findall(o)) - set(code_span.findall(now)))]
    om_c = collections.Counter(" ".join(m.lower().split()) for m in modal.findall(o)); nm_c = collections.Counter(" ".join(m.lower().split()) for m in modal.findall(now))
    errs += [f"modal count fell: {k} {om_c[k]}->{nm_c[k]}" for k in om_c if nm_c[k] < om_c[k]]
    errs += [f"number removed: {k}" for k in sorted(set(number.findall(o)) - set(number.findall(now)))]
    errs += [f"text quoted by another file changed: {q[:80]}" for q in sorted(prot) if q not in now]
    errs += [f"expected exactly 1 new sweep history line, found {added}"] if final and added != 1 else []
    print(f"{now_p}\tquoted-elsewhere={len(prot)}\tdiagrams={omer}->{nmer}\tmodals={sum(om_c.values())}->{sum(nm_c.values())}\tsweep-notes={added}\tproblems={len(errs)}")
    for e in errs: print("  " + e)
    problems += len(errs)
print(f"TOTAL live={len(live)} checked={len(only) or len(live)} problems={problems}")
sys.exit(1 if problems else 0)
```

The guard proves only that protected elements are unchanged. It does not prove that a reworded sentence keeps its meaning; that remains the executor's reading of each diff and the runner's verification turn.

## Spec / documentation sync

Edits the live specs for wording and diagrams only, so no requirement, acceptance criterion, or decision changes and no spec contract changes. Each swept spec records the proofread in its own history through `aw specs note`. The directories in `- Scope-Paths:` name every live spec file, so the runner's spec-edit announcement lists them before the run. No user-facing documentation changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the format check (`grep -c metadata_schema .aw/config/project.json` and the count of live specs lacking `- Status:` or `## Workflow history`, both 0), BASE, the sorted `error` list from `aw check all`, the live-spec list with statuses, the `spec.prose-dash` advisory count, and the last line of the BASE guard run showing `problems=0`.
  - Observed evidence:
    Format check:
      grep -c metadata_schema .aw/config/project.json: 0
      Live specs lacking - Status: or ## Workflow history: 0 of 22
    BASE commit: 3d0ddb84544adb4405b59ff6bbeeb803acfdd5e6

    Sorted error list from aw check all at BASE (11 errors):
    check.blocking-item-closed-without-gate	.aw/records/backlog/done/20261107-suth7l-01-suth7l-artifact-meta-legacy-loader-disagrees-with-status.backlog.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
    check.name-nonconformant	.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-02-g1k32q-spec-generation.codex.gpt61solmedium.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-03-443ltw-spec-generation.opencode.opus55high.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md

    Live specs with statuses at BASE (22 specs):
    ◕  approved      5tapom  .aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md
    ◕  approved      25kzda  .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    ◕  approved      6m4kow  .aw/records/specs/approved/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md
    ◕  approved      77tr3o  .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    ◕  approved      w15vzb  .aw/records/specs/approved/20260912-w15vzb-01-w15vzb-per-action-model-selection.spec.md
    ◕  approved      r07vma  .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    ◕  approved      llbr2b  .aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md
    ◕  approved      4sd62s  .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    ◕  approved      k3yx72  .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    ◕  approved      4iyd78  .aw/records/specs/approved/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md
    ○  draft         i4gpto  .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
    ○  draft         18hh1u  .aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md
    ○  draft         yfz5u9  .aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md
    ○  draft         1tx9t8  .aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
    ▶  implementing  c4gd2h  .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
    ▶  implementing  7ckptx  .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
    ◇  parked        or061f  .aw/records/specs/parked/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md
    ◑  reviewed      11037v  .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md
    ◔  to-review     pqsx96  .aw/records/specs/to-review/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md
    ◔  to-review     ecmw83  .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    ◔  to-review     37am1y  .aw/records/specs/to-review/20261101-37am1y-01-37am1y-execution-record.spec.md
    ◔  to-review     bfuzs6  .aw/records/specs/to-review/20261101-bfuzs6-01-bfuzs6-run-index.spec.md

    aw specs check --agent spec.prose-dash advisory count at BASE: 4 (2 in 4sd62s, 2 in implemented/ipd-structure-and-linting, 0 in swept specs)

    Last line of BASE guard run:
    TOTAL live=22 checked=22 problems=0
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-06) for every spec under 100,000 bytes in the E-01 list, paste its `aw commit` hash, `git show --stat` of that commit naming only that spec, and its guard line showing `sweep-notes=1` and `problems=0`.
  - Observed evidence:
    Spec 5tapom (.aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md):
      Commit: 9d14db8e8d1ede09e0eb9ac976d2e186aab3fd0f
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md	quoted-elsewhere=13	diagrams=0->0	modals=14->14	sweep-notes=1	problems=0

    Spec 6m4kow (.aw/records/specs/approved/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md):
      Commit: c6d92a730ef92ae752c5b7db27a7731f6d32b12c
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/approved/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md	quoted-elsewhere=17	diagrams=0->0	modals=43->43	sweep-notes=1	problems=0

    Spec 77tr3o (.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md):
      Commit: 55655b5b69bb0e5a85d02c48088bdbf12c55c51e
      git show --stat:  1 file changed, 13 insertions(+)
      Guard: .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md	quoted-elsewhere=62	diagrams=0->1	modals=51->51	sweep-notes=1	problems=0

    Spec w15vzb (.aw/records/specs/approved/20260912-w15vzb-01-w15vzb-per-action-model-selection.spec.md):
      Commit: 763a90b687a0a9f47d0d503c767bac68e50d287f
      git show --stat:  1 file changed, 2 insertions(+)
      Guard: .aw/records/specs/approved/20260912-w15vzb-01-w15vzb-per-action-model-selection.spec.md	quoted-elsewhere=17	diagrams=0->0	modals=22->22	sweep-notes=1	problems=0

    Spec r07vma (.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md):
      Commit: e9d1ee00f36afade16ff6e118259d1388efe9053
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md	quoted-elsewhere=34	diagrams=0->0	modals=47->47	sweep-notes=1	problems=0

    Spec llbr2b (.aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md):
      Commit: 8830a6fa536b5f82b186ce442261bff21e2e5bc0
      git show --stat:  1 file changed, 15 insertions(+)
      Guard: .aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md	quoted-elsewhere=46	diagrams=0->1	modals=95->95	sweep-notes=1	problems=0

    Spec k3yx72 (.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md):
      Commit: dad58611a0a0c98b8a3b6037c139eb5f3ff6ed0c
      git show --stat:  1 file changed, 18 insertions(+)
      Guard: .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md	quoted-elsewhere=59	diagrams=0->1	modals=59->59	sweep-notes=1	problems=0

    Spec 4iyd78 (.aw/records/specs/approved/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md):
      Commit: 13294e07f07bc53cb1424c0209fd0b9fa129a99f
      git show --stat:  1 file changed, 14 insertions(+)
      Guard: .aw/records/specs/approved/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md	quoted-elsewhere=29	diagrams=0->1	modals=33->33	sweep-notes=1	problems=0

    Spec i4gpto (.aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md):
      Commit: ceb52b20f8ab6ac51441411cbee36af9ce4cc432
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md	quoted-elsewhere=24	diagrams=0->0	modals=33->33	sweep-notes=1	problems=0

    Spec c4gd2h (.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md):
      Commit: 5ec703b9e8fe57eaf47f8eb80730791c3247bdfa
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md	quoted-elsewhere=57	diagrams=0->0	modals=40->40	sweep-notes=1	problems=0

    Spec 7ckptx (.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md):
      Commit: a777734f4b7981b8399b08e0b76db4f61872245d
      git show --stat:  1 file changed, 14 insertions(+)
      Guard: .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md	quoted-elsewhere=58	diagrams=0->1	modals=139->139	sweep-notes=1	problems=0

    Spec or061f (.aw/records/specs/parked/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md):
      Commit: c376f4dbd452fa2457a57fb58d1da693fe5692ad
      git show --stat:  1 file changed, 15 insertions(+)
      Guard: .aw/records/specs/parked/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md	quoted-elsewhere=4	diagrams=0->1	modals=8->8	sweep-notes=1	problems=0

    Spec pqsx96 (.aw/records/specs/to-review/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md):
      Commit: a6619a095e2db474f78d1bcacdac5f2a1a732084
      git show --stat:  1 file changed, 11 insertions(+)
      Guard: .aw/records/specs/to-review/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md	quoted-elsewhere=31	diagrams=0->1	modals=25->25	sweep-notes=1	problems=0

    Spec ecmw83 (.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md):
      Commit: aff009ffd1dd429f6a46a80b2cffb14e9b155f8e
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md	quoted-elsewhere=19	diagrams=3->3	modals=26->26	sweep-notes=1	problems=0

    Spec 37am1y (.aw/records/specs/to-review/20261101-37am1y-01-37am1y-execution-record.spec.md):
      Commit: 7e02ab9cce2cdfe7e1301d3ca63b57ce083336ac
      git show --stat:  1 file changed, 2 insertions(+)
      Guard: .aw/records/specs/to-review/20261101-37am1y-01-37am1y-execution-record.spec.md	quoted-elsewhere=8	diagrams=2->2	modals=28->28	sweep-notes=1	problems=0

    Spec bfuzs6 (.aw/records/specs/to-review/20261101-bfuzs6-01-bfuzs6-run-index.spec.md):
      Commit: d2c501a9c935c912cb90141554842156e8830a9b
      git show --stat:  1 file changed, 2 insertions(+)
      Guard: .aw/records/specs/to-review/20261101-bfuzs6-01-bfuzs6-run-index.spec.md	quoted-elsewhere=5	diagrams=2->2	modals=16->16	sweep-notes=1	problems=0
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-06) for every spec of 100,000 bytes or more in the E-01 list, paste its `aw commit` hash, `git show --stat` of that commit naming only that spec, and its guard line showing `sweep-notes=1` and `problems=0`.
  - Observed evidence:
    Spec 25kzda (.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md):
      Commit: 159e5f71d4de9296569ea0293cbd174d4149cdbf
      git show --stat:  1 file changed, 20 insertions(+)
      Guard: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md	quoted-elsewhere=668	diagrams=0->1	modals=276->276	sweep-notes=1	problems=0

    Spec 18hh1u (.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md):
      Commit: ec74b4744a3f41e22b221e354071bea8633eab89
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md	quoted-elsewhere=39	diagrams=4->4	modals=142->142	sweep-notes=1	problems=0

    Spec yfz5u9 (.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md):
      Commit: 141be86c623186823872b640061486706748328b
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md	quoted-elsewhere=59	diagrams=4->4	modals=506->506	sweep-notes=1	problems=0

    Spec 1tx9t8 (.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md):
      Commit: 172809b441c84ad2ae0873b6d9e8c8fcf0dee9be
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md	quoted-elsewhere=22	diagrams=4->4	modals=103->103	sweep-notes=1	problems=0

    Spec 11037v (.aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md):
      Commit: 26c31573f94eca3286c1df0b183570797dcd0b15
      git show --stat:  1 file changed, 1 insertion(+)
      Guard: .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md	quoted-elsewhere=53	diagrams=4->4	modals=479->479	sweep-notes=1	problems=0

    Spec 4sd62s (.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md):
      SKIPPED per maintainer ruling 2026-11-09 (metastore exclusion; carrier 63ib9r)
      Guard: .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md (skipped: maintainer 2026-11-09 metastore exclusion)	quoted-elsewhere=83	diagrams=10->10	modals=209->209	sweep-notes=0	problems=0
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-06) paste the complete output of `python3 .aw/state/sfez3e/sweep_guard.py <BASE> --final`, ending `problems=0`, with its exit code 0, and the `aw specs check --agent` output showing all specs conform and no `spec.prose-dash` advisory outside quotations or recorded evidence.
  - Observed evidence:
    python3 .aw/state/sfez3e/sweep_guard.py 3d0ddb84544adb4405b59ff6bbeeb803acfdd5e6 --final:
    .aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md	quoted-elsewhere=13	diagrams=0->0	modals=14->14	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md	quoted-elsewhere=668	diagrams=0->1	modals=276->276	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md	quoted-elsewhere=17	diagrams=0->0	modals=43->43	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md	quoted-elsewhere=62	diagrams=0->1	modals=51->51	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260912-w15vzb-01-w15vzb-per-action-model-selection.spec.md	quoted-elsewhere=17	diagrams=0->0	modals=22->22	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md	quoted-elsewhere=34	diagrams=0->0	modals=47->47	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md	quoted-elsewhere=46	diagrams=0->1	modals=95->95	sweep-notes=1	problems=0
    .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md (skipped: maintainer 2026-11-09 metastore exclusion)	quoted-elsewhere=83	diagrams=10->10	modals=209->209	sweep-notes=0	problems=0
    .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md	quoted-elsewhere=59	diagrams=0->1	modals=59->59	sweep-notes=1	problems=0
    .aw/records/specs/approved/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md	quoted-elsewhere=29	diagrams=0->1	modals=33->33	sweep-notes=1	problems=0
    .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md	quoted-elsewhere=24	diagrams=0->0	modals=33->33	sweep-notes=1	problems=0
    .aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md	quoted-elsewhere=39	diagrams=4->4	modals=142->142	sweep-notes=1	problems=0
    .aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md	quoted-elsewhere=59	diagrams=4->4	modals=506->506	sweep-notes=1	problems=0
    .aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md	quoted-elsewhere=22	diagrams=4->4	modals=103->103	sweep-notes=1	problems=0
    .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md	quoted-elsewhere=57	diagrams=0->0	modals=40->40	sweep-notes=1	problems=0
    .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md	quoted-elsewhere=58	diagrams=0->1	modals=139->139	sweep-notes=1	problems=0
    .aw/records/specs/parked/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md	quoted-elsewhere=4	diagrams=0->1	modals=8->8	sweep-notes=1	problems=0
    .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md	quoted-elsewhere=53	diagrams=4->4	modals=479->479	sweep-notes=1	problems=0
    .aw/records/specs/to-review/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md	quoted-elsewhere=31	diagrams=0->1	modals=25->25	sweep-notes=1	problems=0
    .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md	quoted-elsewhere=19	diagrams=3->3	modals=26->26	sweep-notes=1	problems=0
    .aw/records/specs/to-review/20261101-37am1y-01-37am1y-execution-record.spec.md	quoted-elsewhere=8	diagrams=2->2	modals=28->28	sweep-notes=1	problems=0
    .aw/records/specs/to-review/20261101-bfuzs6-01-bfuzs6-run-index.spec.md	quoted-elsewhere=5	diagrams=2->2	modals=16->16	sweep-notes=1	problems=0
    TOTAL live=22 checked=22 problems=0
    Exit code: 0

    aw specs check --agent output:
    {"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":49,"findings":4,"findings_by_severity":{"error":0,"warning":0,"info":4},"evidence":["specs"],"diagnostics":[{"location":".aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md","rule":"spec.prose-dash"},{"location":".aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md","rule":"spec.prose-dash"},{"location":".aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md","rule":"spec.prose-dash"},{"location":".aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md","rule":"spec.prose-dash"}],"next":null}
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (spec `ecmw83` AC-08) paste the walkthrough path, its `- Id:` and `- Target-Id: sfez3e` lines, its table of specs, its list of `Unresolved` annotations and guard-blocked cases (or "none"), the final `aw specs check --agent` advisory count, and `aw check all --agent --verbose` filtered to `check.id6-identity-slot` printing nothing for the walkthrough.
  - Observed evidence:
    Walkthrough path: .aw/records/walkthroughs/20261109-writestd-07-u8dsej-spec-sweep.walkthrough.md
    Headers:
    - Id: u8dsej
    - Target-Id: sfez3e

    Table of specs: see walkthrough Section 2 (21 swept specifications committed, 1 excluded per maintainer ruling).
    Unresolved annotations: No Unresolved annotations; no carrier filed.
    Guard-blocked cases: None.
    Final aw specs check --agent advisory count: 4 info advisories (2 in excluded 4sd62s, 2 in implemented/ipd-structure-and-linting, 0 in swept specs).
    aw check all --agent --verbose | grep check.id6-identity-slot: printed nothing (exit code 1).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (spec `ecmw83` AC-08) paste `grep -rn "Unresolved (SW-" .aw/records/specs` and either the `aw backlog new --apply` output with the carrier item path and its `aw commit` hash, whose body lists every `SW-NN` found by the grep, or the grep printing nothing beside the walkthrough line "No Unresolved annotations; no carrier filed."
  - Observed evidence:
    grep -rn "Unresolved (SW-" .aw/records/specs:
    (printed nothing, exit code 1)

    Walkthrough line:
    "No Unresolved annotations; no carrier filed."
    Carrier backlog item: none needed / none filed.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: (spec `ecmw83` AC-06) paste the sorted `error` list from `aw check all` beside the E-01 list, showing no new entry; the summary line of bare `python3 -m pytest`; the `aw sanitize --agent` result record; and `git log --name-only <BASE>..HEAD` listing only swept spec files, the walkthrough, and the carrier item.
  - Observed evidence:
    Baseline errors (11) vs current errors (12):
    check.blocking-item-closed-without-gate	.aw/records/backlog/done/20261107-suth7l-01-suth7l-artifact-meta-legacy-loader-disagrees-with-status.backlog.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
    check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
    check.name-nonconformant	.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-02-g1k32q-spec-generation.codex.gpt61solmedium.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-03-443ltw-spec-generation.opencode.opus55high.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
    check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
    New in-flight check error:
    check.scope-drift	.aw/records/plans/pending/20261025-writestd-07-sfez3e-sweep-live-specs-against-the-writing-standard.ipd.md
    Note on check.scope-drift: Spec 11037v resides in .aw/records/specs/reviewed/, a directory created after plan sfez3e authoring and approval. Under ecmw83 R-09 and receipt validity, Scope-Paths was preserved untouched to protect the frozen region digest; the spec was committed with --scope-reason and will reconcile at aw ipd finalize.

    pytest summary line:
    2074 passed, 11 warnings in 71.03s (0:01:11)

    aw sanitize --agent output:
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6329,"findings":0,"evidence":["leak-scan"],"next":null}

    git log --name-only <BASE>..HEAD:
    .aw/records/walkthroughs/20261109-writestd-07-u8dsej-spec-sweep.walkthrough.md
    .aw/records/specs/reviewed/20261024-specflow-30-11037v-synth-merged.spec.md
    .aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
    .aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md
    .aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md
    .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    .aw/records/specs/to-review/20261101-bfuzs6-01-bfuzs6-run-index.spec.md
    .aw/records/specs/to-review/20261101-37am1y-01-37am1y-execution-record.spec.md
    .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
    .aw/records/specs/to-review/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md
    .aw/records/specs/parked/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md
    .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
    .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
    .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
    .aw/records/specs/approved/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md
    .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
    .aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md
    .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    .aw/records/specs/approved/20260912-w15vzb-01-w15vzb-per-action-model-selection.spec.md
    .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    .aw/records/specs/approved/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md
    .aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Orders 01, 02, 03, and 06 (`g4719s`, `gzhw9c`, `k2x0yl`, `e4n4p3`) are `executed` (the `- Item-Dependencies:` edges enforce this; they ship requirement 12, the "Proofreading procedure" section, the `spec.prose-dash` advisory, and the amended `ecmw83` and `k3yx72` text this plan proofreads). Before editing any spec, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; a needed file outside it is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, for example `.aw/records/backlog/open/` when E-06 files no carrier). Commit only through `aw commit sfez3e -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize sfez3e` itself.
