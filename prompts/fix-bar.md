# The Fix Bar (decision policy for what to address)

This defines the "fix bar" used by RhodyPACT's IPD reviewer
(`.agents/prompts/reusable/prompt_ipd_reviewer.md`). Paste it to another LLM to
tell it what to address.

---

**Core principle: fix by default. Deferral is the exception that must be justified.**

The executing model is fast, cheap, and efficient, so **the time, effort, or
token cost of a fix is NOT a reason to skip it.** Flip the usual question. Don't
ask "is this important enough to fix?" Ask: **"is there a strong enough reason
NOT to fix this?"**

## The decision rule

> **FIX the finding unless the *Remediation Risk* of fixing it is Medium-High or
> higher.**
> When unsure whether it reaches that bar, **prefer to fix** and note the
> uncertainty (fail-safe).

This means **everything gets addressed by default** — including small bugs,
nits, wording/polish, missing-but-required capabilities, and
over-scoped/gold-plated features (for those, the "fix" is to recommend removing
or deferring them).

## "Remediation Risk" — the only thing that justifies NOT fixing

Remediation Risk = the risk that *applying the fix itself* harms one or more of
these axes, **now or in the future**:

- **Complexity** — the fix adds disproportionate architectural complexity or
  maintenance burden (a real "keep it simple" cost). *This is the main
  counterweight: don't let "it's cheap to add" become an excuse for gold-plating
  or over-engineering. Unjustified complexity is a valid reason to defer.*
- **Usability** — the fix degrades the user experience or makes things less
  intuitive.
- **Security** — the fix opens, weakens, or complicates the security posture.
- **Functionality** — the fix risks breaking current or planned/future behavior.

Rate it **Low / Medium / Medium-High / High**:

- **Low or Medium → FIX NOW.**
- **Medium-High or High → DEFER**, but only with an explicit, recorded
  justification naming *which axis* and *why*. Where possible, **do the safe part
  now and defer only the risky remainder.** Never silently drop a finding.

**Explicitly excluded from Remediation Risk:** effort, time, and token/compute
cost. The only question is whether the change makes the system more complex, less
usable, less secure, or less correct.

## Severity is for reporting, not for deciding

Issues still get labeled by *impact if left alone* — Blocker / High / Medium /
Low — but **severity does not decide whether to fix.** The Remediation-Risk gate
does. So a "Low/cosmetic" finding still gets fixed by default; a "High" finding
is only deferred if its *cure* clears the Medium-High risk bar.

## Scope is checked separately (two directions)

- **Over-scope:** a feature, abstraction, or dependency not traceable to a stated
  requirement → flag it, default action is remove/defer (usually low-risk, so do
  it).
- **Under-scope:** a required capability that's missing → add it by default.

## How to instruct the other LLM (template)

> Apply this fix bar: address **every** issue you find — bugs, gaps,
> ambiguities, polish, missing requirements, and over-engineering — **by
> default.** Do **not** skip something because it's small or because fixing it
> takes effort/time/tokens. The **only** reason to leave something unaddressed is
> if *making the fix* carries **Medium-High or higher risk** to **complexity,
> usability, security, or functionality** (current or future). When in doubt, fix
> it. If you defer anything, state which of those four axes is at risk and why,
> and fix the safe portion now if you can.

---

**Practical caveat:** this bar makes "do everything" the default, so the *active*
discipline becomes guarding against scope creep. The complexity axis is what
keeps a cheap-to-add fix from quietly violating "keep it simple" — that's the one
judgment the other LLM should exercise most carefully.
