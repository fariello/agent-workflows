#!/bin/bash
cd <experiment-dir>/empty; mkdir -p ../out_rw
rw(){ m=$1; f=$2; o=../out_rw/$(basename $f); [ -s "$o" ] && return
  P=$(python3 -c "import sys;print(open('../rewrite_prompt.txt').read().replace('{draft}',open(sys.argv[1]).read().strip()))" $f)
  case $m in
   codex) timeout 600 codex exec --skip-git-repo-check -s read-only -m gpt-6.1-sol -c model_reasoning_effort=medium "$P" > $o 2>/dev/null ;;
   opus)  timeout 600 opencode run -m uri/its_direct/pt3-claude-opus-5.5-1m-us --variant high "$P" > $o 2>/dev/null ;;
   gem)   timeout 600 agy -p "$P" --model gemini-3.8-flash-high > $o 2>/dev/null ;;
  esac; }
for m in codex opus gem; do ( for f in ../out/$m-old-*.txt; do rw $m $f; done ) & done; wait; echo RWDONE
