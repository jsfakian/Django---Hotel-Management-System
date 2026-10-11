# Safe KEY=VALUE loader for Docker-style .env files.
# Does not eval/source values — so SECRET_KEY with '(' ')' etc. is fine.
#
# Usage:  # shellcheck source=scripts/lib/load-dotenv.sh
#         source "$SCRIPT_DIR/lib/load-dotenv.sh"
#         load_dotenv /path/to/.env.prod

load_dotenv() {
  local file="${1:-}"
  [[ -n "$file" && -f "$file" ]] || {
    echo "load_dotenv: file not found: ${file:-}" >&2
    return 1
  }

  local line key val
  while IFS= read -r line || [[ -n "$line" ]]; do
    # trim CR (Windows) and leading/trailing whitespace
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue

    if [[ "$line" =~ ^(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[2]}"
      val="${BASH_REMATCH[3]}"
      # strip matching single/double quotes
      if [[ "$val" == \"*\" ]]; then
        val="${val:1:${#val}-2}"
      elif [[ "$val" == \'*\' ]]; then
        val="${val:1:${#val}-2}"
      fi
      export "$key=$val"
    fi
  done < "$file"
}
