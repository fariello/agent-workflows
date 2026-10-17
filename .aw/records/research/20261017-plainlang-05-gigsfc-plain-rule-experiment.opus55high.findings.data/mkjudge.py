import json,sys
bid=sys.argv[1]; key=json.load(open("<experiment-dir>/blind_key.json")); facts=json.load(open("<experiment-dir>/facts.json"))
s=key[bid]["scen"]; scen=open(f"<experiment-dir>/scen/{s}.md").read()
req="\n".join(f"{i}. {x}" for i,x in enumerate(facts[s]["required"]))
msg=open(f"<experiment-dir>/blind/{bid}.txt").read()
print(open("<experiment-dir>/judge_prompt.txt").read().format(facts=scen, msg=msg, required=req))
