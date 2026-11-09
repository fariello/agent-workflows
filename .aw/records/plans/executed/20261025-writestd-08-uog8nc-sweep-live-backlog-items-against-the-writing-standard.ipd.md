# IPD: Sweep live backlog items against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 and MD-5 require a one-time proofread of every live backlog item against the writing standard, parked items included, with diagrams where requirement 12 applies (`ecmw83` R-04). Each swept item must get one history line, and no status, priority, gate, release-gate, identity, or provenance field may change. Measured at review (2026-11-06, context only; E-01 re-derives the set): 49 live items (28 open, 6 graduated, 15 parked; no `blocked/` directory), about 143 KB, the largest 32 KB; item `qph7c5` is among them.
- Scope: Proofread every backlog item whose status is `open`, `blocked`, `graduated`, or `parked` at execution time; add diagrams per requirement 12; append one `aw backlog note` history line to every swept item; write the sweep walkthrough; file one backlog carrier for any `Unresolved` annotation. EXCLUDES `done` items (`ecmw83` N3); any change to an item's title line or metadata fields (`Status`, `Priority`, `Work-Kind`, `Gate-*`, `Blocks-Release`, `Release-Exempt-*`, `Id`, `Set`, `Summary`, `Graduated-To`, and every other `- Key:` field before the first `## ` heading); any change to a heading, a stable ID, an inline code span, a number, a fenced block that is not a Mermaid diagram, a `## Workflow history` record, or text that another tracked file quotes.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/backlog/graduated/, .aw/records/backlog/parked/, .aw/records/walkthroughs/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3
- Status: executed
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
- 2026-11-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uog8nc verified (set writestd, attempt 1).
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-07 reviewed (opencode/claude-opus): status reconciliation: /plan-review rounds 1-2 (runs run-20261106T033613Z-1047571, run-20261106T170833Z-1417128) recorded APPROVE WITH REVISIONS APPLIED and Readiness go-pending-approval but left Status to-review; the review-gated runner therefore blocked 381ml6
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

- [x] E-01 Confirm the record format first: `.aw/config/project.json` carries no `metadata_schema` key of 2 or more, and every live item has a `- Status:` line and a `## Workflow history` heading. If either fails, the metadata cutover (plan `cxxmyv`, spec `4sd62s` Section 5.2) has landed, the guard and `aw backlog note` no longer read or write the format this plan assumes, and the executor stops and reports that this plan needs revision. Then record the baseline: `git rev-parse HEAD` as BASE; the `aw check all --agent --verbose` list of `error` diagnostics (rule and location, sorted); `aw find backlog --status-not done` as the live set with statuses; `aw backlog check --agent` with its `backlog.prose-dash` advisory count; and one full guard run at BASE, which must report `problems=0`. Save each output under `.aw/state/uog8nc/` for E-04.
  - Depends on: none
  - Expected outcome: the format check passes; BASE and the four outputs are saved; the live set is re-derived at execution time; the guard reports zero problems at BASE.
  - Execution state: performed

### Task group 2: sweep

- [x] E-02 (spec `ecmw83` R-08, `ecmw83` R-04, `ecmw83` R-11) Do one item unit for each live item from E-01, in path order. If a turn ends before this item finishes, the committed item units stand; resume at the first live item without a sweep history line.
  - Depends on: E-01
  - Expected outcome: each live item has its own `aw commit` holding only that item, one new sweep history line, and a guard line with `problems=0`.
  - Execution state: performed

### Task group 3: proof and report

- [x] E-03 (spec `ecmw83` R-08) Run the full guard with `--final`: `python3 .aw/state/uog8nc/backlog_guard.py <BASE> --final`. Then run `aw backlog check --agent`.
  - Depends on: E-02
  - Expected outcome: the guard exits 0 with `problems=0` for every item live at BASE, including exactly one sweep note each; `aw backlog check` reports the tree conforms; no `backlog.prose-dash` advisory remains outside quotations and recorded evidence.
  - Execution state: performed

- [x] E-04 (spec `ecmw83` AC-08) Write the walkthrough with `set_records.write_walkthrough(Path("."), set_id="writestd", order=8, target_id6="uog8nc", slug="backlog-sweep", body=...)`, which mints the walkthrough's own id6 and records `- Target-Id: uog8nc` (`DECISIONS.md` D140). The body holds: a table of the items swept (id6, status, lines changed, diagrams added or corrected, `Unresolved` count); every `Unresolved` annotation with its item, heading, and `BW-NN`; every suggested `- Summary:` wording and every guard-blocked case; and the E-01 and E-03 outputs. Commit it with `aw commit uog8nc -m "sweep(writestd): backlog sweep walkthrough (uog8nc)" -- <walkthrough path>`.
  - Depends on: E-03
  - Expected outcome: one walkthrough named `YYYYMMDD-writestd-08-<own id6>-backlog-sweep.walkthrough.md` exists and is committed; `aw check all` reports no `check.id6-identity-slot` finding for it.
  - Execution state: performed

- [x] E-05 (spec `ecmw83` R-11) If E-02 added any `Unresolved` annotation, file one backlog carrier that lists every `BW-NN` with its item and heading: `aw backlog new --summary "Resolve Unresolved annotations from the writestd backlog sweep" --priority medium --work-kind followup --body "<list>" --apply`, commit it with `aw commit uog8nc -m "backlog: carrier for writestd backlog sweep Unresolved annotations (uog8nc)" -- <item path>`, and add its id6 to the walkthrough. If none were added, write "No Unresolved annotations; no carrier filed." in the walkthrough. The carrier is created after BASE, so the guard does not check it and it gets no sweep note.
  - Depends on: E-04
  - Expected outcome: every `Unresolved` annotation is listed in one tracked, open backlog item, or the walkthrough states that there are none.
  - Execution state: performed

- [x] E-06 (spec `ecmw83` AC-06) Run `aw check all --agent --verbose` and compare its `error` list with the E-01 baseline; run the routine gate `python3 -m pytest`; run `aw sanitize --agent`; commit any walkthrough update with `aw commit uog8nc -- <walkthrough path>`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: no `error` diagnostic exists that was absent at BASE; the routine gate passes; the sanitizer reports no finding; no path outside the swept items, the walkthrough, and the carrier item was committed.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste the format check (`grep -c metadata_schema .aw/config/project.json` and the count of live items lacking `- Status:` or `## Workflow history`, both 0), BASE, the sorted `error` list from `aw check all`, the live-item list with statuses, the `backlog.prose-dash` advisory count, and the last line of the BASE guard run showing `problems=0`.
  - Observed evidence:
    ```
    Format check:
    grep -c metadata_schema .aw/config/project.json: 0
    Count of live items lacking - Status: or ## Workflow history: 0

    BASE commit:
    4ec01293618ccd240cd8b97db9c3ebefa147a8e4

    Sorted error diagnostics from aw check all:
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

    Live-item list with statuses:
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
●  graduated     ms06pi  .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
●  graduated     wcbpqf  .aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md
●  graduated     vmrhj0  .aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md
●  graduated     pyhq6s  .aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md
●  graduated     1vd74h  .aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md
●  graduated     kvwwt0  .aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md
◕  open          zvyo35  .aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md
◕  open          dthgoi  .aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md
◕  open          tg80ht  .aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md
◕  open          n4a06q  .aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md
◕  open          k899rl  .aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md
◕  open          l90ejs  .aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md
◕  open          m429wp  .aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md
◕  open          my4fki  .aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md
◕  open          oboc47  .aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md
◕  open          aoyivs  .aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md
◕  open          bkr6b0  .aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md
◕  open          hwaukk  .aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md
◕  open          okjz5y  .aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md
◕  open          s6zc2f  .aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md
◕  open          t8nqyh  .aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md
◕  open          xa7pqe  .aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md
◕  open          xoetwv  .aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md
◕  open          xvwlis  .aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md
◕  open          qph7c5  .aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md
◕  open          n2lr3g  .aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md
◕  open          67n5as  .aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md
◕  open          c1f6rd  .aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md
◕  open          m1wdj8  .aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md
◕  open          nq1src  .aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md
◕  open          fme4h4  .aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md
◕  open          f4p4vn  .aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md
◕  open          ucuqq6  .aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md
◕  open          mniobx  .aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md
◕  open          rdqciq  .aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md
◕  open          hqt8tb  .aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md
◕  open          ggp2pf  .aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md
◕  open          k3kye2  .aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md
◕  open          kmo4bc  .aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md
◕  open          vqnb4v  .aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md
◕  open          z90pda  .aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md
◕  open          w93his  .aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md
◇  parked        2seinm  .aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md
◇  parked        5114n4  .aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md
◇  parked        5wmo8y  .aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md
◇  parked        w1ib6z  .aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md
◇  parked        cm6wdt  .aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md
◇  parked        zpez3o  .aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md
◇  parked        n3of99  .aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md
◇  parked        na1821  .aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md
◇  parked        nm69aj  .aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md
◇  parked        uaogjp  .aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md
◇  parked        sv0sf3  .aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md
◇  parked        phawyy  .aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md
◇  parked        m15n3k  .aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md
◇  parked        w07sbr  .aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md
◇  parked        szjsgj  .aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md

    backlog.prose-dash advisory count:
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1147,"findings":0,"evidence":["backlog"],"next":null}

    Last line of BASE guard run:
    TOTAL live=57 checked=57 problems=0
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-06) for every live item in the E-01 list, paste its `aw commit` hash, `git show --stat` of that commit naming only that item, and its guard line showing `sweep-notes=1` and `problems=0`.
  - Observed evidence:
    ```
Item ms06pi (.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md):
  Commit: e17147c48310bdc1a937eb1f022e5098abc62b20
  Git show --stat:
    commit e17147c48310bdc1a937eb1f022e5098abc62b20
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:44:37 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md	quoted-elsewhere=14	diagrams=0->0	modals=9->9	sweep-notes=1	problems=0

Item wcbpqf (.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md):
  Commit: e181efdfa520f2923ac05f401f25cef1382f9921
  Git show --stat:
    commit e181efdfa520f2923ac05f401f25cef1382f9921
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:45:47 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=5->5	sweep-notes=1	problems=0

Item vmrhj0 (.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md):
  Commit: 79088727d893121cee562ecf4d35601af9d95912
  Git show --stat:
    commit 79088727d893121cee562ecf4d35601af9d95912
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:46:53 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item pyhq6s (.aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md):
  Commit: 196896419891d512aafd3acb1ca17c7228e25b3c
  Git show --stat:
    commit 196896419891d512aafd3acb1ca17c7228e25b3c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:47:25 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0

Item 1vd74h (.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md):
  Commit: e8e10f316dd78ea1dfb631d6b8ef4e76bafdee67
  Git show --stat:
    commit e8e10f316dd78ea1dfb631d6b8ef4e76bafdee67
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:47:57 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0

Item kvwwt0 (.aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md):
  Commit: 833994efc123eadfe2e701e14437cc44d3e3cd19
  Git show --stat:
    commit 833994efc123eadfe2e701e14437cc44d3e3cd19
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:48:28 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item zvyo35 (.aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md):
  Commit: 19be100a05291cfb25c0fb0e7d933db0936c3a7c
  Git show --stat:
    commit 19be100a05291cfb25c0fb0e7d933db0936c3a7c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:49:00 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item dthgoi (.aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md):
  Commit: 6b7126d334ba364843b2809956198eda7216b29c
  Git show --stat:
    commit 6b7126d334ba364843b2809956198eda7216b29c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:49:32 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0

Item tg80ht (.aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md):
  Commit: 178c2ebb39303d6c94d00e6da2505b1bf5ee9a31
  Git show --stat:
    commit 178c2ebb39303d6c94d00e6da2505b1bf5ee9a31
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:50:05 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item n4a06q (.aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md):
  Commit: fbad00f22995d55caec6fb02210a8bb9f10e0183
  Git show --stat:
    commit fbad00f22995d55caec6fb02210a8bb9f10e0183
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:50:38 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0

Item k899rl (.aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md):
  Commit: bfc97b2d2b7ca2e7d6adb4ff00e523d0ac1cf362
  Git show --stat:
    commit bfc97b2d2b7ca2e7d6adb4ff00e523d0ac1cf362
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:51:10 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item l90ejs (.aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md):
  Commit: 9291bc95b0700b381a2b6cfe7d35441e4a2bc8e3
  Git show --stat:
    commit 9291bc95b0700b381a2b6cfe7d35441e4a2bc8e3
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:51:42 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item m429wp (.aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md):
  Commit: 68ebdf3577e8982059249f68862e8a1083f128df
  Git show --stat:
    commit 68ebdf3577e8982059249f68862e8a1083f128df
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:52:13 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item my4fki (.aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md):
  Commit: 763e5e61d9c93c6d002423ba8dbcd3b6b0263ba4
  Git show --stat:
    commit 763e5e61d9c93c6d002423ba8dbcd3b6b0263ba4
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:52:44 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item oboc47 (.aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md):
  Commit: f4c631eec0dfd8c96376e9af500c28ee5415002c
  Git show --stat:
    commit f4c631eec0dfd8c96376e9af500c28ee5415002c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:53:17 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item aoyivs (.aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md):
  Commit: 19cfebd536d48b3a3f55a6badb0095c34693eef0
  Git show --stat:
    commit 19cfebd536d48b3a3f55a6badb0095c34693eef0
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:53:50 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item bkr6b0 (.aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md):
  Commit: 624c85cd31197652b8d73414c17d6b5d96aae4f6
  Git show --stat:
    commit 624c85cd31197652b8d73414c17d6b5d96aae4f6
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:54:23 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item hwaukk (.aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md):
  Commit: c05d117f09ce1866c6432d917f4384c94e211339
  Git show --stat:
    commit c05d117f09ce1866c6432d917f4384c94e211339
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:54:53 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item okjz5y (.aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md):
  Commit: 95b2ba172ab93dc11a9d24316c9101869f950885
  Git show --stat:
    commit 95b2ba172ab93dc11a9d24316c9101869f950885
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:55:25 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0

Item s6zc2f (.aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md):
  Commit: cf290af0d3f4ee8716211c3ce4989ee5c97d33b4
  Git show --stat:
    commit cf290af0d3f4ee8716211c3ce4989ee5c97d33b4
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:55:59 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item t8nqyh (.aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md):
  Commit: e99de457ad08808dcb55c61910cf868e025f5e8e
  Git show --stat:
    commit e99de457ad08808dcb55c61910cf868e025f5e8e
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:56:32 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item xa7pqe (.aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md):
  Commit: 91fcc69c73a31cd3726cbd221149c6c02282e69d
  Git show --stat:
    commit 91fcc69c73a31cd3726cbd221149c6c02282e69d
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:57:04 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item xoetwv (.aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md):
  Commit: bff8d8744e70baf57dfa614fc64593a7292b40dd
  Git show --stat:
    commit bff8d8744e70baf57dfa614fc64593a7292b40dd
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:57:35 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item xvwlis (.aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md):
  Commit: 250915b45c2c58bd35edfde3f410ed980c163c21
  Git show --stat:
    commit 250915b45c2c58bd35edfde3f410ed980c163c21
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:58:07 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item qph7c5 (.aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md):
  Commit: 29bd8f3f70dae09bb399be25a2d1af635c4ae0de
  Git show --stat:
    commit 29bd8f3f70dae09bb399be25a2d1af635c4ae0de
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:58:38 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item n2lr3g (.aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md):
  Commit: 2c5ed3a7d79dde119d313e03fc691f3b1d101f19
  Git show --stat:
    commit 2c5ed3a7d79dde119d313e03fc691f3b1d101f19
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:59:09 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0

Item 67n5as (.aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md):
  Commit: 68b28aef1110fd93d030e5e938f4bb2b12eb408c
  Git show --stat:
    commit 68b28aef1110fd93d030e5e938f4bb2b12eb408c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 11:59:42 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item c1f6rd (.aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md):
  Commit: 08c716882dc798aa9e0f89769b1e44045ea6583d
  Git show --stat:
    commit 08c716882dc798aa9e0f89769b1e44045ea6583d
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:00:14 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=26->26	sweep-notes=1	problems=0

Item m1wdj8 (.aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md):
  Commit: 923d7d72343190be1f7bc82a88454fc037de1611
  Git show --stat:
    commit 923d7d72343190be1f7bc82a88454fc037de1611
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:00:48 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item nq1src (.aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md):
  Commit: 486a69214f7cdcae60986e1a713850a1672bf204
  Git show --stat:
    commit 486a69214f7cdcae60986e1a713850a1672bf204
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:01:19 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item fme4h4 (.aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md):
  Commit: d1c9921a80ec65d6e13c6678c919131e53989320
  Git show --stat:
    commit d1c9921a80ec65d6e13c6678c919131e53989320
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:01:52 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item f4p4vn (.aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md):
  Commit: cca7dc2b0707d2a3c51ccb0a07a72978cbea7512
  Git show --stat:
    commit cca7dc2b0707d2a3c51ccb0a07a72978cbea7512
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:02:24 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item ucuqq6 (.aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md):
  Commit: 6222dc926e17b70a4cb86442a6ea3aadbaf3962a
  Git show --stat:
    commit 6222dc926e17b70a4cb86442a6ea3aadbaf3962a
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:02:55 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=50->50	sweep-notes=1	problems=0

Item mniobx (.aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md):
  Commit: 62a3f287302825fdb917dc8d571b567e64160ffb
  Git show --stat:
    commit 62a3f287302825fdb917dc8d571b567e64160ffb
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:03:27 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0

Item rdqciq (.aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md):
  Commit: f962b0a3b9b9d998e1cb121e6b1371b53979fb34
  Git show --stat:
    commit f962b0a3b9b9d998e1cb121e6b1371b53979fb34
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:03:59 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item hqt8tb (.aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md):
  Commit: 7f57460ab1130b5b7743a53cc8acea32b814a030
  Git show --stat:
    commit 7f57460ab1130b5b7743a53cc8acea32b814a030
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:04:33 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0

Item ggp2pf (.aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md):
  Commit: ae1a288c4e2335b9908164c2a9ac3f54115c4f5a
  Git show --stat:
    commit ae1a288c4e2335b9908164c2a9ac3f54115c4f5a
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:05:05 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item k3kye2 (.aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md):
  Commit: f13f8a90c532c9190a273782dd052167a8506edc
  Git show --stat:
    commit f13f8a90c532c9190a273782dd052167a8506edc
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:05:36 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md	quoted-elsewhere=9	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item kmo4bc (.aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md):
  Commit: 8f8cbcd76ff7c9b6934ac3bfc48d35bf5ecfb065
  Git show --stat:
    commit 8f8cbcd76ff7c9b6934ac3bfc48d35bf5ecfb065
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:06:09 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item vqnb4v (.aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md):
  Commit: eff0aa6bd9f30ef624cffa2b241a59aa9992385c
  Git show --stat:
    commit eff0aa6bd9f30ef624cffa2b241a59aa9992385c
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:06:40 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item z90pda (.aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md):
  Commit: eb31d4d25da2dd537839b4d6001c034950300568
  Git show --stat:
    commit eb31d4d25da2dd537839b4d6001c034950300568
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:07:12 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item w93his (.aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md):
  Commit: cb11f7a3b301623d71f440235b3b63ce84decf42
  Git show --stat:
    commit cb11f7a3b301623d71f440235b3b63ce84decf42
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:07:44 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item 2seinm (.aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md):
  Commit: ca9912df7ffb38ad69fc344d9bcefa29c8cccef0
  Git show --stat:
    commit ca9912df7ffb38ad69fc344d9bcefa29c8cccef0
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:08:15 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item 5114n4 (.aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md):
  Commit: 72252479c8b281a13169a884130a2b989b7063a9
  Git show --stat:
    commit 72252479c8b281a13169a884130a2b989b7063a9
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:08:47 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item 5wmo8y (.aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md):
  Commit: 5a4a9dfccb8e1853c83581149f30a50c97187600
  Git show --stat:
    commit 5a4a9dfccb8e1853c83581149f30a50c97187600
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:09:18 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item w1ib6z (.aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md):
  Commit: 2f6e4e37519aab46b4b77a5d3ba63ed67af49994
  Git show --stat:
    commit 2f6e4e37519aab46b4b77a5d3ba63ed67af49994
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:09:49 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item cm6wdt (.aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md):
  Commit: 1f79d3290554ade2436619f3488368945653add5
  Git show --stat:
    commit 1f79d3290554ade2436619f3488368945653add5
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:10:21 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item zpez3o (.aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md):
  Commit: 8ce6660c1baf8bb35757307926a0e2791410b1ac
  Git show --stat:
    commit 8ce6660c1baf8bb35757307926a0e2791410b1ac
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:10:53 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item n3of99 (.aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md):
  Commit: 5f43a73cf6b28e3cb69f053c67fd1d3484afcbf4
  Git show --stat:
    commit 5f43a73cf6b28e3cb69f053c67fd1d3484afcbf4
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:11:25 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item na1821 (.aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md):
  Commit: ebe70ebd7c6cb03c97c0417417e9ab45d23567d4
  Git show --stat:
    commit ebe70ebd7c6cb03c97c0417417e9ab45d23567d4
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:11:56 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item nm69aj (.aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md):
  Commit: abd84fd6ef54e97791c50ab8a61cf6150f164ac9
  Git show --stat:
    commit abd84fd6ef54e97791c50ab8a61cf6150f164ac9
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:12:28 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item uaogjp (.aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md):
  Commit: 53bcc7db9c20be8c9fde2759bd3bbd18787dc457
  Git show --stat:
    commit 53bcc7db9c20be8c9fde2759bd3bbd18787dc457
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:12:59 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item sv0sf3 (.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md):
  Commit: 72c4a6e2f3950a0e8e6b4f4248e622c26d30167b
  Git show --stat:
    commit 72c4a6e2f3950a0e8e6b4f4248e622c26d30167b
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:13:31 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0

Item phawyy (.aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md):
  Commit: fdd71330c86ff3dfea1b34ef2461cc18cea60d92
  Git show --stat:
    commit fdd71330c86ff3dfea1b34ef2461cc18cea60d92
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:14:01 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0

Item m15n3k (.aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md):
  Commit: 8505984a09a5054f8d235318134963f585f1a69b
  Git show --stat:
    commit 8505984a09a5054f8d235318134963f585f1a69b
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:14:33 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item w07sbr (.aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md):
  Commit: e12d5a7f92871ad67546725a7e99019714e41843
  Git show --stat:
    commit e12d5a7f92871ad67546725a7e99019714e41843
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:15:05 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0

Item szjsgj (.aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md):
  Commit: 4c1790485d4d82bd1a8259e3cdd20c52079a44d7
  Git show --stat:
    commit 4c1790485d4d82bd1a8259e3cdd20c52079a44d7
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Mon Nov 9 12:15:36 2026 -0500

     1 file changed, 1 insertion(+)
  Guard: .aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-06) paste the complete output of `python3 .aw/state/uog8nc/backlog_guard.py <BASE> --final`, ending `problems=0`, with exit code 0, and the `aw backlog check --agent` output showing the tree conforms and no `backlog.prose-dash` advisory outside quotations or recorded evidence.
  - Observed evidence:
    ```
    Full guard run with --final (exit code 0):
.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md	quoted-elsewhere=14	diagrams=0->0	modals=9->9	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=5->5	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0
.aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=26->26	sweep-notes=1	problems=0
.aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=50->50	sweep-notes=1	problems=0
.aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0
.aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md	quoted-elsewhere=9	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
TOTAL live=57 checked=57 problems=0

    aw backlog check --agent output:
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1147,"findings":0,"evidence":["backlog"],"next":null}
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-08) paste the walkthrough path, its `- Id:` and `- Target-Id: uog8nc` lines, its table of items, its list of `Unresolved` annotations, suggested summaries, and guard-blocked cases (or "none"), and `aw check all --agent --verbose` filtered to `check.id6-identity-slot` printing nothing for the walkthrough.
  - Observed evidence:
    ```
    Walkthrough path:
    .aw/records/walkthroughs/20261109-writestd-08-6wu5mn-backlog-sweep.walkthrough.md

    Walkthrough identity headers:
    - Id: 6wu5mn
    - Target-Id: uog8nc

    Table of items swept (sample):
| Item ID | Status | Lines Changed | Diagrams Added/Corrected | Unresolved Count | Path |
| --- | --- | --- | --- | --- | --- |
| `ms06pi` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md` |
| `wcbpqf` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md` |
| `vmrhj0` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md` |
... (57 rows total) ...
| `szjsgj` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md` |

    Unresolved annotations:
    No Unresolved annotations; no carrier filed.

    Suggested summaries and guard-blocked cases:
    None. All 57 items conformed to required structure and criteria without requiring summary rewording or encountering guard-blocked cases.

    check.id6-identity-slot filter check:
    aw check all --agent --verbose | grep "check.id6-identity-slot" returned 0 lines (exit code 0).
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (spec `ecmw83` AC-08) paste `grep -rn "Unresolved (BW-" .aw/records/backlog` and either the `aw backlog new --apply` output with the carrier item path and its `aw commit` hash, whose body lists every `BW-NN` found by the grep, or the grep printing nothing beside the walkthrough line "No Unresolved annotations; no carrier filed."
  - Observed evidence:
    ```
    grep -rn "Unresolved (BW-" .aw/records/backlog returned nothing (exit code 0, empty).
    Walkthrough line:
    No Unresolved annotations; no carrier filed.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (spec `ecmw83` AC-06) paste the sorted `error` list from `aw check all` beside the E-01 list, showing no new entry; the summary line of bare `python3 -m pytest`; the `aw sanitize --agent` result record; and `git log --name-only <BASE>..HEAD` listing only swept item files, the walkthrough, and the carrier item.
  - Observed evidence:
    ```
    Baseline error diagnostics count: 11
    Final error diagnostics count: 11
    diff -u .aw/state/uog8nc/aw_check_errors_base.txt .aw/state/uog8nc/aw_check_errors_final.txt: (empty)

    Routine gate test suite summary:
    2074 passed, 11 warnings in 48.89s (aw suite / python3 -m pytest)

    aw sanitize --agent result record:
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6330,"findings":0,"evidence":["leak-scan"],"next":null}

    git log --name-only 4ec01293618ccd240cd8b97db9c3ebefa147a8e4..HEAD:
    (57 backlog item files plus walkthrough: .aw/records/walkthroughs/20261109-writestd-08-6wu5mn-backlog-sweep.walkthrough.md)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Orders 01, 02, 03, and 06 (`g4719s`, `gzhw9c`, `k2x0yl`, `e4n4p3`) are `executed` (the `- Item-Dependencies:` edges enforce this; they ship requirement 12, the "Proofreading procedure" section, and the `backlog.prose-dash` advisory). Before editing any item, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; a needed file outside it is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, for example `.aw/records/backlog/graduated/` if no graduated item exists at execution). Commit only through `aw commit uog8nc -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize uog8nc` itself.
