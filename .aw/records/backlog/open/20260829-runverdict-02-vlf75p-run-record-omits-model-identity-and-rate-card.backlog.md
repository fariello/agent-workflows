- Id: vlf75p
- Status: open
- Set: runverdict
- Priority: high
- Work-Kind: bug
- Summary: Run records cannot attribute a turn to a model or price it: state.json records model=null and 0 of 9757 cost-bearing steps carry a modelID, while the rate card that produced the recorded costs lives only in the user's opencode.json outside the repo

## Workflow history
- 2026-08-29 created (aw backlog): Found while trying to answer 'how does validation do under Opus 5' from the run record. It is not answerable: per-model attribution had to be reconstructed by grepping model strings that appear only because the agent typed them into an --actor argument.

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
