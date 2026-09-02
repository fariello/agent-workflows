#!/usr/bin/env bash
# Install or update popular agentic coding CLIs on Linux.
#
# Base: opencode, codex, agy, claude, kiro-cli, hermes
# Extras: Cursor, Grok, gemini, copilot, aider, goose

set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.opencode/bin:$PATH"

MODE=""
case "${1:-}" in
  "") ;;
  --all) MODE=all ;;
  --base) MODE=base ;;
  --extras) MODE=extras ;;
  -h|--help)
    echo "Usage: $0 [--all|--base|--extras]"
    exit 0
    ;;
  *)
    echo "Unknown option: $1" >&2
    exit 2
    ;;
esac

if [[ "$(uname -s)" != Linux ]]; then
  echo "This script supports Linux only." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required." >&2
  exit 1
fi

failures=()
selected=()

names=(
  "OpenCode"
  "OpenAI Codex CLI"
  "Google Antigravity CLI (agy)"
  "Anthropic Claude Code"
  "Kiro CLI (kiro-cli)"
  "NousResearch Hermes Agent"
  "Cursor CLI (agent)"
  "xAI Grok Build (grok)"
  "Google Gemini CLI"
  "GitHub Copilot CLI"
  "Aider"
  "Goose"
)

show_menu() {
  echo "Agentic coding CLIs:"
  local i
  for i in "${!names[@]}"; do
    if (( i < 6 )); then
      printf '  %2d) %-34s [base]\n' "$((i + 1))" "${names[$i]}"
    else
      printf '  %2d) %-34s [extra]\n' "$((i + 1))" "${names[$i]}"
    fi
  done
}

select_range() {
  local first=$1 last=$2 i
  selected=()
  for ((i = first; i <= last; i++)); do
    selected+=("$i")
  done
}

select_interactively() {
  local i answer
  selected=()
  echo "Answer y or n for each CLI:"
  for i in "${!names[@]}"; do
    while true; do
      if ! read -r -p "Install or update ${names[$i]}? [y/N] " answer; then
        echo >&2
        echo "Input ended before selection was complete." >&2
        return 1
      fi
      case "${answer,,}" in
        y|yes) selected+=("$i"); break ;;
        ""|n|no) break ;;
        *) echo "Please answer y or n." ;;
      esac
    done
  done
}

parse_numbered_list() {
  local input=$1 item
  selected=()
  input=${input//[[:space:]]/}
  [[ $input =~ ^[0-9]+(,[0-9]+)*$ ]] || return 1
  IFS=',' read -r -a items <<< "$input"
  for item in "${items[@]}"; do
    (( item >= 1 && item <= ${#names[@]} )) || return 1
    selected+=("$((item - 1))")
  done
}

choose_tools() {
  local choice
  case "$MODE" in
    all) select_range 0 $((${#names[@]} - 1)); return ;;
    base) select_range 0 5; return ;;
    extras) select_range 6 $((${#names[@]} - 1)); return ;;
  esac

  show_menu
  echo
  while true; do
    if ! read -r -p "Install which? [all/base/extras/3,5,6/interactive] " choice; then
      echo >&2
      echo "No selection received. Use --all, --base, or --extras for unattended use." >&2
      return 1
    fi
    case "${choice,,}" in
      all) select_range 0 $((${#names[@]} - 1)); return ;;
      base) select_range 0 5; return ;;
      extras) select_range 6 $((${#names[@]} - 1)); return ;;
      interactive) select_interactively; return ;;
      *)
        if parse_numbered_list "$choice"; then
          return
        fi
        echo "Enter all, base, extras, interactive, or comma-separated numbers."
        ;;
    esac
  done
}

is_selected() {
  local wanted=$1 item
  for item in "${selected[@]}"; do
    [[ $item == "$wanted" ]] && return 0
  done
  return 1
}

run_step() {
  local name=$1
  shift
  echo
  echo "==> $name"
  if "$@"; then
    echo "OK: $name"
  else
    echo "FAILED: $name" >&2
    failures+=("$name")
  fi
}

run_installer() {
  local url=$1
  shift
  local installer
  installer=$(mktemp "${TMPDIR:-/tmp}/agent-cli-installer.XXXXXX") || return 1
  if ! curl --proto '=https' --tlsv1.2 -fsSL "$url" -o "$installer"; then
    rm -f "$installer"
    return 1
  fi
  bash "$installer" "$@"
  local status=$?
  rm -f "$installer"
  return "$status"
}

install_opencode() {
  run_installer https://opencode.ai/install
}

install_codex() {
  run_installer https://chatgpt.com/codex/install.sh
}

install_agy() {
  run_installer https://antigravity.google/cli/install.sh
}

install_claude() {
  if command -v claude >/dev/null 2>&1; then
    claude update || run_installer https://claude.ai/install.sh
  else
    run_installer https://claude.ai/install.sh
  fi
}

install_kiro() {
  if command -v kiro-cli >/dev/null 2>&1; then
    kiro-cli update --non-interactive || run_installer https://cli.kiro.dev/install
  else
    run_installer https://cli.kiro.dev/install
  fi
}

install_hermes() {
  if command -v hermes >/dev/null 2>&1; then
    hermes update || run_installer https://hermes-agent.nousresearch.com/install.sh
  else
    run_installer https://hermes-agent.nousresearch.com/install.sh
  fi
}

install_cursor() {
  run_installer https://cursor.com/install
}

install_grok() {
  run_installer https://x.ai/cli/install.sh
}

npm_latest() {
  local package=$1
  command -v npm >/dev/null 2>&1 || {
    echo "npm is required for $package" >&2
    return 1
  }
  npm install --global "$package@latest"
}

install_aider() {
  if command -v uv >/dev/null 2>&1; then
    uv tool install --force --upgrade aider-chat
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user --upgrade aider-install &&
      "$HOME/.local/bin/aider-install"
  else
    echo "uv or Python 3 is required for Aider" >&2
    return 1
  fi
}

install_goose() {
  run_installer https://github.com/block/goose/releases/download/stable/download_cli.sh
}

choose_tools || exit 2

((${#selected[@]})) || {
  echo "No CLIs selected."
  exit 0
}

installers=(
  install_opencode
  install_codex
  install_agy
  install_claude
  install_kiro
  install_hermes
  install_cursor
  install_grok
  "npm_latest @google/gemini-cli"
  "npm_latest @github/copilot"
  install_aider
  install_goose
)

for i in "${!names[@]}"; do
  if is_selected "$i"; then
    # The installer table is defined locally above, never from user input.
    read -r -a command_parts <<< "${installers[$i]}"
    run_step "${names[$i]}" "${command_parts[@]}"
  fi
done

echo
echo "==> Installed command versions"
commands=(opencode codex agy claude kiro-cli hermes agent grok gemini copilot aider goose)
for i in "${!commands[@]}"; do
  if is_selected "$i"; then
    cmd=${commands[$i]}
    if command -v "$cmd" >/dev/null 2>&1; then
      printf '%-12s ' "$cmd"
      "$cmd" --version 2>/dev/null | head -n 1 || echo "installed (version unavailable)"
    else
      printf '%-12s %s\n' "$cmd" "not found on current PATH"
    fi
  fi
done

if ((${#failures[@]})); then
  echo
  echo "Completed with failures: ${failures[*]}" >&2
  exit 1
fi

echo
echo "All requested CLIs installed or updated. Authentication is intentionally not performed."
