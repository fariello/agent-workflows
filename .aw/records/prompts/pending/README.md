# prompts/pending/

Run-once and research prompts that are queued to run, or being iterated on before running.

Named with the uniform artifact grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md`; `aw prompts new`
mints the `<id6>` and derives the name, so never hand-name one. A legacy
`YYYYMMDD-HHMM-NN-<slug>.prompt.md` name predating this repository's `prompt_id6` cutover is still
valid and converts on demand with `aw rename prompts <legacy-name> --to-id6`. When a prompt has been
run and its results filed under `.aw/records/research/<topic>/`, move it to `executed/`. If a prompt is
dropped instead of run, retire it to `superseded/` or `not-executed/` - never leave an abandoned
prompt here.
