- Id: jnpl08
- Status: done
- Graduated-To: jnpl08
- Blocks-Release: next
- Set: jnpl08
- Priority: medium
- Work-Kind: bug
- Summary: research_contract.parse_frontmatter accepts a duplicated YAML key with last-wins semantics, so a record with two status keys parses as valid rather than reporting the duplication; the bullet trees' sibling rule 7ohskw flags a duplicated metadata bullet and the YAML dialect has no equivalent

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 7d4bgs executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-jnpl08-01-7d4bgs-report-a-repeated-research-front-matter-key-instead-of-silen.ipd.md); evidence .aw/records/plans/executed/20261002-jnpl08-01-7d4bgs-report-a-repeated-research-front-matter-key-instead-of-silen.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: 7d4bgs
- 2026-10-01 created (aw backlog): research_contract.parse_frontmatter accepts a duplicated YAML key with last-wins semantics, so a record with two status keys parses as valid rather than reporting the duplication; the bullet trees' sibling rule 7ohskw flags a duplicated metadata bullet and the YAML dialect has no equivalent

FILED WHILE AUTHORING plan `deftzy` (Set `7w6zsl`), which closes the research write paths that can CREATE a duplicate key but deliberately leaves the reader's behavior alone.

MEASURED 2026-10-01 in a lane at HEAD `9e813570a`.

`research_contract.parse_frontmatter` is a hand-written line splitter, not a YAML library (there is no `import yaml` anywhere in this package): it walks lines between the `---` fences doing `key, _, val = line.partition(":")` and assigns into a dict. So a repeated key OVERWRITES silently. Driven directly: `parse_frontmatter("---\na: 1\na: 2\n---\n")` returns `{'a': '2'}`.

WHY THAT MATTERS BEYOND TIDINESS. `build_frontmatter` always emits a legitimate `status:` line, so a duplicate `status:` appearing LATER in the block WINS, and every reader of the dialect then reports the later value: `validate_frontmatter` validates it (and returns `[]` when it is a legal status), `research_index` records it, `attention._research_record` reports it as `native_status`, and `selectors._read_status` resolves it. Driven on a doc whose legitimate line read `status: todo` and whose later injected line read `status: reference`: `parse_frontmatter` returned `reference`, `aw attention --format json` reported `"native_status":"reference","attention_class":"done"`, and both `aw check research` and `aw research index --check` reported clean. The same mechanism makes an injected `blocks-release:` a FUNCTIONING release gate that `aw releases show next` honors.

ONE BOUND WORTH RECORDING, because it shows the reader is not uniformly blind: a duplicated `id:` IS caught, though by a different rule and for a different reason. `research_index._doc_entry` compares the block's `id` against the id6 parsed out of the FILENAME, so an overridden `id` surfaces as `name-frontmatter-mismatch: id aaaaaa != name m8zg5y` at exit 1. Nothing performs the analogous cross-check for `status`, `blocks-release`, `priority`, `outcome` or `kind`, which is the actual gap.

THE SIBLING DIALECT IS GETTING THIS RULE SEPARATELY. Pending plan `7ohskw` adds a duplicated-metadata-bullet finding for the bullet trees. The YAML dialect has no equivalent and this item is that equivalent, so the two should agree on rule id and severity rather than minting two vocabularies for one defect class.

WHY IT IS NOT FOLDED INTO `deftzy`: changing the shared reader's behavior (or adding a checker rule over it) affects every research consumer at once (`research_index`, `research_archive`, `selectors`, `attention`, `releases`), which is a cross-cutting change that does not belong in the same commit as a verb-side input guard. Note also that the two fixes are INDEPENDENT rather than redundant: `deftzy` stops a VERB from creating a duplicate, and this item is what would catch one that arrives by HAND EDIT, which no write-path guard can see.
