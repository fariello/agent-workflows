- Id: vlf75p
- Status: graduated
- Blocks-Release: next
- Set: runverdict
- Priority: high
- Work-Kind: bug
- Summary: Run records cannot attribute a turn to a model or price it: state.json records model=null and 0 of 9757 cost-bearing steps carry a modelID, while the rate card that produced the recorded costs lives only in the user's opencode.json outside the repo

## Workflow history
- 2026-09-08 graduated (aw set): PARTIALLY graduated to plan w33lrl (runverdict-07); see the PARTIAL OBSOLESCENCE AND SCOPE HANDOFF section appended to this item. NOT graduated as ALREADY SHIPPED: the record-a-provenance-object half of gap 1, delivered by executed plan 3cm15q (launch_profile_record, present in 33 of 135 runs). NOT graduated as OWNED BY THE PENDING runanalytics SET, owner named per clause: per-turn model capture (5f2h8i E-01/E-02), effective-dated pricing and the recorded-versus-estimated split (aflsz3 E-02), normalized pricing-key facts (8hald1 E-02), the aw runs query surface (mm5p3v), and tests (b), (d), (e). GRADUATED: the producer those plans consume and that does not exist today, namely the resolved host-default model and the four-component rate card frozen per run with a digest, unknowns named rather than omitted, and the recorded card made authoritative. Gaps 2 and 3 held in full on re-measurement (28158 cost-bearing steps, 0 with a model id). Inherits Blocks-Release: next.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

ROOT CAUSE (in-tree, verified): the run record captures per-step COST but neither the MODEL that
incurred it nor the RATE CARD that priced it, so a recorded dollar figure cannot be attributed or
recomputed. Three separate gaps:

1. `state.json` `options.model` is `null` on every run (the runner records the CLI flag, which is
   normally unset because the model comes from the host's own config, not from `aw`).
2. The per-step records in `.aw/records/runs/<run>/sessions/*.jsonl` carry `part.cost` and
   `part.tokens{input,output,reasoning,cache{read,write}}` but NO model id. MEASURED across every
   recorded run: 9757 cost-bearing steps, 0 carrying a `modelID`, 0 distinct model ids.
3. The rate card is not in the repository at all. It lives in the USER's host config
   (`~/.config/opencode/opencode.json`), e.g. for `its_direct/pt3-claude-opus-5-1m-us`:
   `{"input": 5.5, "cache_read": 0.55, "cache_write": 6.875, "output": 27.5}`. That file is mutated by
   `aw oc update-models` (see `oc_models.py`, which syncs pricing from a LiteLLM admin endpoint) and
   currently has four `.bak`/timestamped siblings from recent edits, i.e. it demonstrably changes.

MEASURED (how model attribution has to be done today): asked "how often has validation under Opus 5
caught anything significant", the only way to attribute the 28 verification outcomes to a model was to
grep model strings out of each run directory. Those strings occur 8 times in one session log and EVERY
occurrence is inside a shell command the AGENT typed, e.g.
`... ipd finalize <plan> --actor "opencode its_direct/pt3-claude-opus-5-1m-us" ...`. So per-model
attribution currently rests on agent-authored PROSE, which the framework elsewhere insists is never
authority (research ig9bai: "agent prose and exit status are never completion authority"). One run
shows BOTH `opus-4.8` and `opus-5` strings, so even the reconstruction is ambiguous.

CONSEQUENCE (analysis the record cannot support): (a) per-model quality questions are unanswerable --
"is Opus 5 a better verifier than 4.8" cannot be computed, which is exactly the question that exposed
this; (b) costs are not comparable across time. Research x0spmh documents the concrete trap: the rate
card was corrected mid-history from `input 5.00/output 25.00, cache_read UNPRICED` to
`5.50/27.50/0.55/6.875`, so Aug 24 and Aug 29 dollar totals are NOT comparable and the Aug 24
`cache_read = $0` is a CONFIG ARTIFACT rather than evidence that cache reads were free. Nothing in the
run record lets a future reader detect which regime priced a given run, so a naive pooled analysis
reaches a false conclusion. That study's central finding (cache reads were 74% of a $16.41 turn) depends
on a rate card that the runs themselves do not record.

FIX SKETCH: record, per RUN and per TURN, the resolved model identity (provider + exact model id, since
a gateway alias like `pt3-claude-opus-5-1m-us` is what actually prices) and the resolved rate card
(input/output/cache_read/cache_write) in effect at launch, plus a digest so a later change is detectable.
Resolve them from the host config the runner is about to invoke rather than from the `--model` flag,
which is normally null. Prefer capturing what the host reports per step if it can be made to emit it;
otherwise snapshot at launch and record that it is a launch-time snapshot. Treat an unresolvable model
or rate card as a recorded UNKNOWN rather than silently omitting it. Cross-check: `aw runs` cost views
should read the recorded card, never a hardcoded or current-config price, so historical runs keep
reporting their own regime.

TEST: (a) a run record names the exact model id and the four-component rate card; (b) a cost recomputed
from recorded tokens x recorded card matches the recorded cost to the cent (the x0spmh reconstruction
reproduced $16.41 exactly, so this is achievable); (c) changing the host config after a run does NOT
change that run's reported cost; (d) a run whose model/card cannot be resolved records UNKNOWN and is
excluded from pooled cost aggregates rather than silently averaged in; (e) per-model aggregation over
verification outcomes is computable WITHOUT grepping agent prose.

RELATION: siblings in this Set are wyw936 (verifier gate fails open), rbftpl (verifier evidence never
consumed) and t74o5q (verifier turn dies on a stale plan path; verification skipped 23 times). This item is the OBSERVABILITY instance: the other two concern a gate that cannot reject,
this one concerns a record that cannot attribute or price what it observed. Consumes research x0spmh,
whose session-allocation policy REQUIRES a runtime cache-read/context signal that this gap currently
denies.

## PARTIAL OBSOLESCENCE AND SCOPE HANDOFF, measured 2026-09-08 at HEAD 44d4950d during graduation

GAP 1 IS PARTLY CLOSED BY SHIPPED WORK. This item says `options.model` is null "on every run". Measured
across all 135 run directories: it is SET in 5 of 135 (the runs where an operator passed `--model`), and
more importantly `runprofile` Order 03 (`3cm15q`, EXECUTED) shipped `launch_profile_record`
(`oc_runipd.py:2740`), which freezes a provenance object into 33 of 135 runs carrying `model`, `variant`,
`agent`, `config_source`, `config_present`, `config_digest` and a per-field `provenance` map. So the
RECORD-A-PROVENANCE-OBJECT half of gap 1 is DONE and must not be rebuilt.

WHAT SURVIVES OF GAP 1: in all 33 the provenance reads `{"model": "host-default", ...}` unless `--model`
was passed, and `PROVENANCE_HOST_DEFAULT` is documented as "nothing supplied it; pass no argument"
(`runner_profiles.py:378`). The record now honestly NAMES the gap instead of filling it. Filling that
value is what was graduated.

GAPS 2 AND 3 HELD IN FULL on re-measurement. Gap 2: 28158 cost-bearing steps across every session log,
0 carrying any `modelID`/`modelId`/`model` key, 0 distinct model ids (this item measured 9757 steps; the
corpus tripled and the ratio is still exactly zero). Gap 3: the rate card is not in the repository at
all, and `aw oc update-models` demonstrably mutates the host config from a LiteLLM admin endpoint
(`oc_models.sync_provider`, `:607`).

MOST OF THE FIX SKETCH AND THREE OF THE FIVE TESTS ARE OWNED BY THE PENDING `runanalytics` SET, not by
this item, and are therefore NOT graduated here. That Set is 11 plans (orchestrator `5lxvl3`) and its
children DECLARE the downstream work by name:
- `5f2h8i` (Order 04) E-01/E-02: telemetry "records resolved run/set/IPD/attempt/phase/model/provider/
  variant metadata" per invocation, and "the execution ID, attempt, phase, start/end times, model
  identity, and node pseudonym must be recorded per file and must not be inferred later from a single
  run-level snapshot". That is the PER-TURN capture this item's fix sketch asks for.
- `aflsz3` (Order 06) E-02: "effective-dated pricing", with "price schedules carry provider/model/variant,
  input/output/cache rates, currency, effective interval, and source/version", plus the recorded
  convention "Model prices changed over time. A timeless price map would rewrite history and is
  forbidden". That is the effective-dated card, the recorded-versus-estimated split, and the
  missingness/uncertainty handling.
- `8hald1` (Order 05) E-02: the normalized fact schema carrying "runner/model/variant" and "pricing-key"
  facts.
- `mm5p3v` (Order 08): the `aw runs` query/analyze surface.
SO NOT GRADUATED: the fix-sketch clauses about per-TURN capture, effective-dated schedules,
pooled-aggregate exclusion, and `aw runs` cost views computing from a card; and TESTS (b)
(cost recomputed to the cent), (d) (unknown-card runs excluded from pooled aggregates) and (e)
(per-model aggregation over verification outcomes).

WHAT WAS GRADUATED (plan `w33lrl`, runverdict-07): the ONE thing that Set cannot do for itself. Those
plans CONSUME a model identity and a rate card from the run record, and today the run record contains
NEITHER, so a telemetry integration that "records resolved model" would record `host-default` and a
pricing engine would have no in-repo card to be effective-dated. `w33lrl` is the PRODUCER: resolve and
freeze the host's own default model and the four-component card with a digest, per RUN, with unknowns
named rather than omitted, and make the recorded card authoritative so a later host-config edit cannot
reprice history. Tests (a) and (c) are graduated with it.
