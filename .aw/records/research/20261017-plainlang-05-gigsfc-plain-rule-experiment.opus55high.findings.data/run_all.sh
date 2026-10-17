#!/bin/bash
cd <experiment-dir>/empty
run_one(){ m=$1; p=$2; k=$3; P=$(cat ../prompts/$p.txt); o=../out/$m-$p-$k.txt
  [ -s "$o" ] && return
  case $m in
   codex) timeout 600 codex exec --skip-git-repo-check -s read-only -m gpt-6.1-sol -c model_reasoning_effort=medium "$P" > $o 2>/dev/null ;;
   opus)  timeout 600 opencode run -m uri/its_direct/pt3-claude-opus-5.5-1m-us --variant high "$P" > $o 2>/dev/null ;;
   gem)   timeout 600 agy -p "$P" --model gemini-3.8-flash-high > $o 2>/dev/null ;;
  esac; }
for m in codex opus gem; do
 ( for p in old-s1 new-s1 old-s2 new-s2 old-s3 new-s3; do for k in 1 2; do run_one $m $p $k; done; done ) &
done; wait; echo ALLDONE
