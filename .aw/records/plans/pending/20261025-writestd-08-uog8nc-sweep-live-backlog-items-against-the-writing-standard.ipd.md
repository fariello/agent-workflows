# IPD: Sweep live backlog items against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 and MD-5 require a one-time proofread of every live backlog item against the writing standard, parked items included, with diagrams where requirement 12 applies (`ecmw83` R-04). Each swept item must get one history line, and no status, priority, gate, release-gate, identity, or provenance field may change. Measured at review (2026-11-06, context only; E-01 re-derives the set): 49 live items (28 open, 6 graduated, 15 parked; no `blocked/` directory), about 143 KB, the largest 32 KB; item `qph7c5` is among them.
- Scope: Proofread every backlog item whose status is `open`, `blocked`, `graduated`, or `parked` at execution time; add diagrams per requirement 12; append one `aw backlog note` history line to every swept item; write the sweep walkthrough; file one backlog carrier for any `Unresolved` annotation. EXCLUDES `done` items (`ecmw83` N3); any change to an item's title line or metadata fields (`Status`, `Priority`, `Work-Kind`, `Gate-*`, `Blocks-Release`, `Release-Exempt-*`, `Id`, `Set`, `Summary`, `Graduated-To`, and every other `- Key:` field before the first `## ` heading); any change to a heading, a stable ID, an inline code span, a number, a fenced block that is not a Mermaid diagram, a `## Workflow history` record, or text that another tracked file quotes.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/backlog/graduated/, .aw/records/backlog/parked/, .aw/records/walkthroughs/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3
- Status: to-review
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 8
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: uog8nc

## Workflow history
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; round 2 PR-101..PR-104 FIXED; review record .aw/records/reviews/20261025-writestd-08-uog8nc-sweep-live-backlog-items-against-the-writing-standard.review.md
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261025-writestd-08-uog8nc-sweep-live-backlog-items-against-the-writing-standard.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live backlog item up to the writing standard once, without changing what any item asks for, and prove mechanically that no protected element changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Definitions used by every item below:

- BASE is the commit that E-01 records. Every comparison in this plan is against BASE.
- The guard is the script in `## Required tests / validation`. Save it once as `.aw/state/uog8nc/backlog_guard.py` (gitignored, inside the workspace) and run it from the repository root. With no item arguments it checks every item that was live at BASE; with item paths it checks only those.
- An item unit is the work for ONE backlog item, done in this order: (1) proofread the item per the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md` and its numbered requirements, checking in particular that the item states a bounded outcome and how acceptance is shown; (2) apply requirement 12: add a Mermaid diagram only where its criteria apply and none covers that content, and correct an existing diagram that disagrees with the text; (3) where a passage's meaning cannot be established, keep the original text and add an adjacent block-quote line `> **Unresolved (BW-NN):** <the ambiguity>. Decision needed: <what must be decided>.`, numbering `BW-01` upward across the whole sweep (`ecmw83` R-11); (4) run `aw backlog note <item path> --message "proofread per the technical writing standard (spec ecmw83 R-08); meaning unchanged"`, appending `; N Unresolved annotations` when step 3 added any; (5) run the guard on that item and fix every reported problem by restoring the original text; (6) commit the item alone with `aw commit uog8nc -m "sweep(writestd): proofread backlog <id6> (uog8nc)" -- <item path>`.
- Do not change, in any item unit: the title line and the metadata fields (every `- Key:` line before the first `## ` heading, with its indented continuation lines, which includes `- Summary:`); any heading text; any stable ID such as `R-08`, `AC-06`, `OQ-01`, a decision number such as `D140`, or an id6 such as `25kzda`; any inline code span (file and line citations live there); any number (measured values); any fenced block that is not a Mermaid diagram (pasted output, quoted commands); any `## Workflow history` record; any text that another tracked file quotes; any `must`, `should`, `may`, `shall`, or `never`, with or without a following `not` (do not swap, drop, or negate one). The guard enforces each of these. Prose paragraphs before the first `## ` heading are not metadata; proofread them like any other prose. Where you would improve `- Summary:` or the guard blocks another fix you judge necessary, keep the original and list the case and the suggested wording in the walkthrough.
- Dashes: the `AGENTS.md` execution contract exempts backlog items from the dash rule, and the shipped standard adds no dash rule of its own (maintainer ruling, `g4719s` OQ-02). Spec `ecmw83` AC-06 still requires that no swept item carries a `backlog.prose-dash` advisory outside quotations and recorded evidence, so reword a prose em or en dash that the advisory reports, unless the guard protects the text. Live items held no em or en dash at review.

### Task group 1: baseline

- [ ] E-01 Confirm the record format first: `.aw/config/project.json` carries no `metadata_schema` key of 2 or more, and every live item has a `- Status:` line and a `## Workflow history` heading. If either fails, the metadata cutover (plan `cxxmyv`, spec `4sd62s` Section 5.2) has landed, the guard and `aw backlog note` no longer read or write the format this plan assumes, and the executor stops and reports that this plan needs revision. Then record the baseline: `git rev-parse HEAD` as BASE; the `aw check all --agent --verbose` list of `error` diagnostics (rule and location, sorted); `aw find backlog --status-not done` as the live set with statuses; `aw backlog check --agent` with its `backlog.prose-dash` advisory count; and one full guard run at BASE, which must report `problems=0`. Save each output under `.aw/state/uog8nc/` for E-04.
  - Depends on: none
  - Expected outcome: the format check passes; BASE and the four outputs are saved; the live set is re-derived at execution time; the guard reports zero problems at BASE.
  - Execution state: pending

### Task group 2: sweep

- [ ] E-02 (spec `ecmw83` R-08, `ecmw83` R-04, `ecmw83` R-11) Do one item unit for each live item from E-01, in path order. If a turn ends before this item finishes, the committed item units stand; resume at the first live item without a sweep history line.
  - Depends on: E-01
  - Expected outcome: each live item has its own `aw commit` holding only that item, one new sweep history line, and a guard line with `problems=0`.
  - Execution state: pending

### Task group 3: proof and report

- [ ] E-03 (spec `ecmw83` R-08) Run the full guard with `--final`: `python3 .aw/state/uog8nc/backlog_guard.py <BASE> --final`. Then run `aw backlog check --agent`.
  - Depends on: E-02
  - Expected outcome: the guard exits 0 with `problems=0` for every item live at BASE, including exactly one sweep note each; `aw backlog check` reports the tree conforms; no `backlog.prose-dash` advisory remains outside quotations and recorded evidence.
  - Execution state: pending

- [ ] E-04 (spec `ecmw83` AC-08) Write the walkthrough with `set_records.write_walkthrough(Path("."), set_id="writestd", order=8, target_id6="uog8nc", slug="backlog-sweep", body=...)`, which mints the walkthrough's own id6 and records `- Target-Id: uog8nc` (`DECISIONS.md` D140). The body holds: a table of the items swept (id6, status, lines changed, diagrams added or corrected, `Unresolved` count); every `Unresolved` annotation with its item, heading, and `BW-NN`; every suggested `- Summary:` wording and every guard-blocked case; and the E-01 and E-03 outputs. Commit it with `aw commit uog8nc -m "sweep(writestd): backlog sweep walkthrough (uog8nc)" -- <walkthrough path>`.
  - Depends on: E-03
  - Expected outcome: one walkthrough named `YYYYMMDD-writestd-08-<own id6>-backlog-sweep.walkthrough.md` exists and is committed; `aw check all` reports no `check.id6-identity-slot` finding for it.
  - Execution state: pending

- [ ] E-05 (spec `ecmw83` R-11) If E-02 added any `Unresolved` annotation, file one backlog carrier that lists every `BW-NN` with its item and heading: `aw backlog new --summary "Resolve Unresolved annotations from the writestd backlog sweep" --priority medium --work-kind followup --body "<list>" --apply`, commit it with `aw commit uog8nc -m "backlog: carrier for writestd backlog sweep Unresolved annotations (uog8nc)" -- <item path>`, and add its id6 to the walkthrough. If none were added, write "No Unresolved annotations; no carrier filed." in the walkthrough. The carrier is created after BASE, so the guard does not check it and it gets no sweep note.
  - Depends on: E-04
  - Expected outcome: every `Unresolved` annotation is listed in one tracked, open backlog item, or the walkthrough states that there are none.
  - Execution state: pending

- [ ] E-06 (spec `ecmw83` AC-06) Run `aw check all --agent --verbose` and compare its `error` list with the E-01 baseline; run the routine gate `python3 -m pytest`; run `aw sanitize --agent`; commit any walkthrough update with `aw commit uog8nc -- <walkthrough path>`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: no `error` diagnostic exists that was absent at BASE; the routine gate passes; the sanitizer reports no finding; no path outside the swept items, the walkthrough, and the carrier item was committed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Read `.aw/system/workflows/technical-writing/technical-writing.md` in full before E-02 and apply its "Proofreading procedure" section (added by Order 01 `g4719s` E-03) and requirement 12 (`g4719s` E-02).
- A writing correction does not authorize a change to scope, obligations, approval, status, or recorded evidence (standard section "How it combines with other rules", items 2 and 3; spec `ecmw83` R-08).
- Backlog status and history are owned by `aw backlog`; append history only with `aw backlog note`, and never hand-edit a status line.
- `- Summary:` is a one-line identity surface used by duplicate detection; leave it unchanged and record suggested wording in the walkthrough.
- Walkthroughs dated after the `walkthrough_id6` cutover (2026-09-27, `.aw/config/project.json`) use the clustered name with their own id6 and `- Target-Id:` (`.aw/records/walkthroughs/README.md`, D140). A walkthrough is not tracked by `aw attention`, so an open obligation must also live in a tracked carrier (E-05).
- Commit only through `aw commit`; one item per commit, so a reviewer can read each diff alone and a resumed turn keeps finished units.

## Findings

- No `blocked/` directory exists at review; E-01 re-derives the live set, so a blocked item that appears before execution is swept.
- Text in live items that other tracked files quote at review: 159 passages. The guard keeps them unchanged.
- Many items cite code as a path with a line number inside an inline code span (for example item `zvyo35`, section "Problem Statement", step 2). The guard keeps every code span, so the sweep never rewrites a citation it cannot re-verify.
- Order 07 (`sfez3e` E-06) may file a carrier item in `backlog/open/` before this plan runs; it is live at BASE and is swept like any other item.
- Pending plan `cxxmyv` (Set `metastore`, `Attended: required`) runs migration `m0001`, which deletes every record's bullet block and `## Workflow history` section (spec `4sd62s` Section 5.2) and stamps `metadata_schema: 2`. Nothing orders it relative to this plan. After it lands, the guard's metadata and history checks read nothing and `aw backlog note` targets a format that no longer exists, so E-01 checks the format before any item unit starts.
- Round 2 review (2026-11-06) re-ran the guard on a scratch clone. The round 1 guard compared every line before the first `## ` heading, so it refused proofreading of the 42-line prose preamble in item `ms06pi`, and it counted `must` without `not`, so `must` to `must not`, `must not` to `must`, and dropping a `never` passed with `problems=0`. Live items hold 191 bare id6 references and 17 decision numbers outside code spans, which the round 1 `stable_id` pattern did not match. The revised guard compares only the title and `- Key:` fields, counts the modals with and without `not`, and protects decision numbers and bare id6 references; each mutation above now reports a problem and exits 1, and an unchanged tree reports `problems=0`.

## Proposed changes (ordered, validatable)

1. Baseline and guard at BASE (E-01).
2. Sweep every live item, one committed item unit each (E-02).
3. Prove every protected element unchanged and every item noted (E-03).
4. Report, carry unresolved annotations, check, and commit (E-04, E-05, E-06).

## Deferred / out of scope (with reason)

- `done` items: spec `ecmw83` N3.
  - Carrier-Declined: deliberate non-goal of the spec.
- Spec `ecmw83` AC-06's dash clause still describes the widened dash rule that the maintainer did not keep (`g4719s` OQ-02). This plan satisfies AC-06 as written and does not amend it, because AC-06 also governs Orders 07 and 09.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none after review. The review added the guard, a history line for every swept item rather than only changed ones (`ecmw83` R-08), the backlog carrier for `Unresolved` annotations, the sanitizer run, and the D140 walkthrough name.

## Required tests / validation

`aw backlog check`, `aw check all` against the E-01 baseline, the guard below, the routine gate `python3 -m pytest`, and `aw sanitize --agent`.

The guard (save verbatim as `.aw/state/uog8nc/backlog_guard.py`; usage `python3 .aw/state/uog8nc/backlog_guard.py <BASE> [--final] [item path ...]`; exit 0 means no problem). It reports, per item, the protected elements that changed between BASE and the working tree. Measured at review: a full run takes about 9 seconds and reports `TOTAL live=48 checked=48 problems=0` at HEAD `3c7f9c987` (round 1) and `TOTAL live=49 checked=49 problems=0` at HEAD `604e5498f` (round 2, revised guard). In a scratch clone, each of these was reported with exit code 1: a changed `- Priority:`, a changed `- Summary:`, a shortened code-span citation, a changed quoted passage, `should` changed to `may`, `must` changed to `must not`, `must not` changed to `must`, `never` changed to `always`, and an id6 reference removed. A reworded preamble sentence in `ms06pi` reported `problems=0` and exit 0, and after only `aw backlog note`, `--final` reported `sweep-notes=1` and `problems=0`.

```python
"""Sweep guard for plan uog8nc: compares every live backlog item at BASE with the working tree."""
import collections, re, subprocess, sys

base, final = sys.argv[1], "--final" in sys.argv
only = {a.split("/")[-1] for a in sys.argv[2:] if not a.startswith("--")}
NOTE = "proofread per the technical writing standard"
ROOT, SUFFIX, TERMINAL, SELF = ".aw/records/backlog/", ".backlog.md", ("done",), "-uog8nc-"
def git(*a, inp=None):
    return subprocess.run(["git", *a], input=inp, capture_output=True).stdout
names = git("ls-tree", "-r", "--name-only", base).decode().split()
live = [p for p in names if p.startswith(ROOT) and p.endswith(SUFFIX) and p.split("/")[3] not in TERMINAL]
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
        if " " in q and SELF not in p: quoted[q].add(p)
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
by_name = {p.split("/")[-1]: p for p in git("ls-files", ROOT).decode().split()}
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

N/A: backlog items, a walkthrough, and at most one new backlog item only; no spec contract and no user-facing documentation changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the format check (`grep -c metadata_schema .aw/config/project.json` and the count of live items lacking `- Status:` or `## Workflow history`, both 0), BASE, the sorted `error` list from `aw check all`, the live-item list with statuses, the `backlog.prose-dash` advisory count, and the last line of the BASE guard run showing `problems=0`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-06) for every live item in the E-01 list, paste its `aw commit` hash, `git show --stat` of that commit naming only that item, and its guard line showing `sweep-notes=1` and `problems=0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-06) paste the complete output of `python3 .aw/state/uog8nc/backlog_guard.py <BASE> --final`, ending `problems=0`, with exit code 0, and the `aw backlog check --agent` output showing the tree conforms and no `backlog.prose-dash` advisory outside quotations or recorded evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-08) paste the walkthrough path, its `- Id:` and `- Target-Id: uog8nc` lines, its table of items, its list of `Unresolved` annotations, suggested summaries, and guard-blocked cases (or "none"), and `aw check all --agent --verbose` filtered to `check.id6-identity-slot` printing nothing for the walkthrough.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: (spec `ecmw83` AC-08) paste `grep -rn "Unresolved (BW-" .aw/records/backlog` and either the `aw backlog new --apply` output with the carrier item path and its `aw commit` hash, whose body lists every `BW-NN` found by the grep, or the grep printing nothing beside the walkthrough line "No Unresolved annotations; no carrier filed."
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: (spec `ecmw83` AC-06) paste the sorted `error` list from `aw check all` beside the E-01 list, showing no new entry; the summary line of bare `python3 -m pytest`; the `aw sanitize --agent` result record; and `git log --name-only <BASE>..HEAD` listing only swept item files, the walkthrough, and the carrier item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Orders 01, 02, 03, and 06 (`g4719s`, `gzhw9c`, `k2x0yl`, `e4n4p3`) are `executed` (the `- Item-Dependencies:` edges enforce this; they ship requirement 12, the "Proofreading procedure" section, and the `backlog.prose-dash` advisory). Before editing any item, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; a needed file outside it is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, for example `.aw/records/backlog/graduated/` if no graduated item exists at execution). Commit only through `aw commit uog8nc -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize uog8nc` itself.
