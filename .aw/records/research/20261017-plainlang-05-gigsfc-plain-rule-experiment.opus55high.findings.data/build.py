from pathlib import Path
H="""You are a coding agent working in a software repository. The block below is the communication
policy you have been given for talking to the human maintainer. Follow it.

=== COMMUNICATION POLICY ===
{contract}
=== END POLICY ===

You have just finished investigating a problem. Your notes are below. Write your reply to the
maintainer now. Output ONLY the reply text you would send, nothing else. Do not use any tools;
everything you need is in the notes.

{scenario}
"""
for cond in ("old","new"):
    c=Path(f"contract_{cond}.txt").read_text()
    for s in sorted(Path("scen").glob("s*.md")):
        Path("prompts").mkdir(exist_ok=True)
        (Path("prompts")/f"{cond}-{s.stem}.txt").write_text(H.format(contract=c, scenario=s.read_text()))
print(sorted(p.name for p in Path("prompts").iterdir()))
