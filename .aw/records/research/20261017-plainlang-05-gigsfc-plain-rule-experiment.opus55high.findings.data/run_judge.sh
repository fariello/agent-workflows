#!/bin/bash
cd <experiment-dir>/empty; mkdir -p ../judged
judge(){ jm=$1; bid=$2; o=../judged/$jm-$bid.json; [ -s "$o" ] && return
  P=$(python3 ../mkjudge.py $bid)
  case $jm in
   codex) timeout 600 codex exec --skip-git-repo-check -s read-only -m gpt-6.1-sol -c model_reasoning_effort=medium "$P" > $o 2>/dev/null ;;
   opus)  timeout 600 opencode run -m uri/its_direct/pt3-claude-opus-5.5-1m-us --variant high "$P" > $o 2>/dev/null ;;
   gem)   timeout 600 agy -p "$P" --model gemini-3.8-flash-high > $o 2>/dev/null ;;
  esac; }
for jm in codex opus gem; do ( for f in ../blind/X*.txt; do judge $jm $(basename $f .txt); done ) & done; wait; echo JDONE
