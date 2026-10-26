---
id: ear8qy
created: 20261025
set: specflow
order: 18
topic: []
model: 
kind: assessment
status: active
outcome: adopted
summary: Repository evidence and CLI design rationale for the independent synthesis candidate
consumed-by: [1tx9t8]
---

# Repository evidence for the independent synthesis candidate

This assessment supports candidate spec `1tx9t8`, created from prompt `g1k32q`. It records inspected implementation, design decisions and authoring validation. It is not an external-model comparison or a `/spec-review` attestation.

## Baseline and method

Inspected branch `main`, baseline commit `933b94b74c2c0f8cb2507cd93c56c3601afc7c6a`. During authoring another writer advanced main to `f99c99baba8e5c0ab921665f7333edc7f480af3d`. A name-only diff showed only the other writer's research assessment changed; none of the inspected implementation sources changed. That work was not staged or edited by this author.

Bounded passes: repository and owner-tool discovery; comparison of artifact-noun, shared-process and run-integrated grammars; detailed configuration, execution, evidence and naming contracts; diagrams/inventories/acceptance mapping; final consistency and local owner checks. No model subagents, live model calls, proposed workflow dispatch or spec review were run. No preferred model catalog or provider configuration was inspected, so availability remains unknown.

## Evidence and consequences

All links pin the baseline above. Symbols and sections identify the inspected behavior.

| Evidence | Finding | Consequence for the candidate |
| --- | --- | --- |
| [runner_profiles.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/runner_profiles.py), RUNNER_REGISTRY, parse_profile, resolve, ROLE_NAMES | Registered launch hosts are oc and agy. agy supports neither variant nor persona; profile validation refuses them. Roles are closed: write-prose, write-code, write-code-fast, research-online, check-content, verify. | Keep exact launch profiles; synthesis role map references them. Do not claim native Codex support or enforced agy High. |
| [host_adapters.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/host_adapters.py), HOST_NONINTERACTIVE_RUNTIME | Metadata includes codex exec, distinct from runner registration. | Preparation/import is the first-release escape route for unsupported dispatch, without silent substitution. |
| [workflow_profile.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/workflow_profile.py), ALLOWED_PROFILE_KEYS, semantic_view | Transport tuning preserves requirements, validation and permission semantics. | Reuse packet adaptation; reasoning hints are not runtime attestation. |
| [workflow_compiler.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/workflow_compiler.py), compile_workflow, _compile_manifest; [run_engine.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/run_engine.py), RunEngine | Compiled steps/dependencies and a single-writer state engine already exist. | Add typed finite synthesis graphs and dispatcher, not another scheduler or IPD executor. |
| [run_ledger_store.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/run_ledger_store.py), RunLedgerStore; [run_recovery.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/run_recovery.py), plan_retry, UnknownOutcomeError | Ledger has hash-chain and single-writer integrity. Recovery distinguishes interrupted side effects and bounded retries; retry helpers are not all production driver callers. | Explicitly wire synthesis recovery; no blind retry after a possibly charged invocation. |
| [run_cli.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/run_cli.py), module contract, EXIT constants; [output contract 3.1](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/docs/cli-output-contract.md#31-run-execution-exit-vocabulary) | run writes, runs reads; resume inspection is not dispatch. Existing run exits exceed v1 envelope's 0/1/2. | Shared typed synth facade with deliberate error mapping; no renumbering of existing run commands. |
| [specs README](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/.aw/records/specs/README.md), Status and history; [spec-review](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/.aw/system/workflows/spec-review/spec-review.md), Three prohibitions | Owner controls status/history; review requires separate records; no spec Readiness field. | Iteration assessments live in research; final candidate is never self-reviewed/approved. |
| [research README](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/.aw/records/research/README.md), Pipeline position, Companion files | Research pipeline synthesis is derived from body/kind, distinct from shelf status. Native companions move with owner. | Use assessment for checks, explicit completion receipts, companion evidence and existing kinds. |
| [D177](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/DECISIONS.md), attributed artifact filenames; [artifact_naming.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/artifact_naming.py), _CLUSTERED_RE | Type-last facets are decided; nonresearch attributed grammar is not yet supported. Research supports a model facet, not full ACE/model. | Propose owner/parser extension; author this candidate with valid current owner output. |
| [record_producers.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/record_producers.py), resolve_record_path | Record/state paths resolve through project context and physical storage classes. | Never make .aw/records the only physical destination; retain native source evidence with owner companions. |
| [selectors.py](https://github.com/fariello/agent-workflows/blob/933b94b74c2c0f8cb2507cd93c56c3601afc7c6a/agent_workflows/selectors.py), resolve_for_mutation | Unique-ID collisions always refuse; Set matching can intentionally name many. | Single-spec inputs add an exact-one constraint; merge manifests enumerate typed members. |

Additional sources read: README quick-start/completion, GUIDING_PRINCIPLES P2/P4/P5/P6/P11/P16, docs/runner-profiles.md, docs/cli-human-guide.md, docs/cli-agent-protocol.md, spec workflow, research/spec owner helps, run_freeze.py, workflow schema/ledger declarations, and behavioral profile/naming/spec-gate/recovery tests. Existing draft `18hh1u` was discovered during scope search and treated as unapproved parallel work, not normative authority. No compatible implemented synthesis CLI was found in parser discovery. The candidate does not overwrite that draft.

Documentation discrepancies observed: principle P5's stable spec path guidance differs from current status-directory setters; the specs module opening docstring describes an outdated interactive-only approval mechanism; agent-protocol examples omit a mandatory field and retain an older find-limit note. Candidate citations distinguish implementation, current contract and older descriptions.

## Design decisions supported

A shared `aw synth` noun avoids duplicating config/decision/recovery controls under specs/research, while preserving run/runs ownership beneath it. A new process client is justified by typed synthesis semantics, not by a new scheduler. The strongest competing artifact-noun grammar loses on duplicated common controls and confusion with existing research comparison scaffolding.

Quick reduces iterations while retaining the roster and correctness gates. One participant remains useful and must not require fabricated consensus or an extra merge. One synthesizer per run bounds first-release complexity. Native adapters are gated by verified capability, with manual prepare/import retained for unsupported preferences. Frozen inputs and explicit configuration forks preserve auditability without claiming identical future model text.

D177 is fixed. Proposed cross-tree sequence reservations, canonical Set dates and linked overflow Sets solve allocation without widening two-digit NN or treating it as an iteration counter. These are new owner extensions, not claims about current tools. New records keep current valid tool-generated names until those extensions exist.

## Owner-authoring observations

`aw specs new` minted `1tx9t8`; `aw research new` minted `ear8qy` in the existing specflow Set, choosing research order 18 and canonical prefix 20261024. `aw group specs` assigned Set specflow and order 02 but retained prefix 20261025 despite a requested `--date 20261024`. The emitted files remain untouched by manual identity/date renaming. No author facet claims an independently confirmed exact runtime model. Tool-owned status/history are preserved.

## Validation observed

The following are actual command outputs from this authoring pass, not illustrative feature transcripts.

`aw specs check <candidate-path> --agent`:

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
```

`aw sanitize --agent`:

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6170,"findings":0,"evidence":["leak-scan"],"next":null}
```

A local document-validation script parsed JSON with Python's json module, passed the sample result to the actual `agent_schema.validate_agent_record`, checked illustrative name forms against the proposed grammar, checked requirement coverage and fences, and rejected en/em dashes:

```text
Candidate checks: 2 JSON blocks parsed; machine record schema valid; 76 example paths match proposed grammar; 20/20 requirements mapped; fences balanced; no en/em dashes.
```

The checks above do not validate semantic correctness, renderer layout or the future implementation. No feature tests can pass for a feature not implemented. No Mermaid renderer was available on PATH; the diagrams were checked as source by reading only. A full project test suite was not run for these authoring-only records. Owner/index/pre-commit results obtained subsequently are appended below rather than inferred.


Final document validation after schema/detail corrections:

```text
Final document validation: 30 pinned source links exist; JSON/protocol valid; 60 unique cross-tree inventory allocations; 20/20 requirements mapped; fences and punctuation conform.
```

`aw research index` refreshed the ignored local manifests successfully:

```text
up to date   .aw/records/research/INDEX.json, INDEX.md (163 docs)
```

A captured `aw research index --check` run returned exit 1. The capture summary was:

```text
research index --check: exit 1; 426 output lines; 8 lines reference new records
```

Eight diagnostics are the explicitly fictional full filename examples in candidate section 8: IDs x00001, x00002, x00049, x00059, y00001, y00002, y00013 and z00025. Current research_contract.iter_id6_citations does not exclude declared example blocks; EXAMPLE_ID6S contains only k7m2xq and ab12cd. Reusing either ID across distinct inventory records would violate the requested identity demonstration. The candidate therefore documents this compatibility gap rather than changing production code, hiding the examples, or claiming a clean corpus check. The remaining output concerns other records (dangling citations, existing metadata/model/status findings); those records were not modified. No diagnostic names this assessment as defective.

The candidate remains draft, with no review/approval attestation. Its source-protocol checks passed; repository-wide research validation did not. No blocking product decision remains, while live adapter verification and example-aware citation handling remain explicit implementation prerequisites.
