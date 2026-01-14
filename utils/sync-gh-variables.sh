#!/usr/bin/env bash
set -euo pipefail

# Sync GitHub Actions VARIABLES across repos under a personal account.
# Requires: gh (https://cli.github.com/), jq
# Usage examples:
#   bash sync-gh-variables.sh --owner tjsullivan1 --env-file ./vars.env --dry-run
#   bash sync-gh-variables.sh --owner tjsullivan1 --from-repo template-azure-app
#   bash sync-gh-variables.sh --owner tjsullivan1 --from-repo template-azure-app --include '^(app-|api-)'
#   bash sync-gh-variables.sh --owner tjsullivan1 --env-file ./vars.env --exclude 'legacy-repo,playground'

OWNER=""
ENV_FILE=""
FROM_REPO=""
INCLUDE_REGEX=".*"      # match all by default
EXCLUDES=""             # comma-separated repo names
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner) OWNER="$2"; shift 2;;
    --env-file) ENV_FILE="$2"; shift 2;;
    --from-repo) FROM_REPO="$2"; shift 2;;
    --include) INCLUDE_REGEX="$2"; shift 2;;
    --exclude) EXCLUDES="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help)
      echo "Usage: $0 --owner <user> [--env-file path.env | --from-repo <repo>]"
      echo "            [--include <regex>] [--exclude <comma,list>] [--dry-run]"
      exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$OWNER" ]]; then
  echo "ERROR: --owner is required"; exit 1
fi
if [[ -z "$ENV_FILE" && -z "$FROM_REPO" ]]; then
  echo "ERROR: Provide one of --env-file or --from-repo"; exit 1
fi
if [[ -n "$ENV_FILE" && -n "$FROM_REPO" ]]; then
  echo "ERROR: Use either --env-file or --from-repo (not both)"; exit 1
fi

command -v gh >/dev/null || { echo "ERROR: gh CLI not found"; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq not found"; exit 1; }

# Build exclude set
declare -A EXCLUDE_SET
IFS=',' read -ra EX_ARR <<< "${EXCLUDES}"
for r in "${EX_ARR[@]}"; do
  [[ -n "$r" ]] && EXCLUDE_SET["$r"]=1
done

# Load source variables into an array of KEY=VALUE pairs
declare -a VARS

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: env file not found: $ENV_FILE"; exit 1
  fi
  # Accept simple KEY=VALUE lines (skip comments/blank)
  while IFS= read -r line; do
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    VARS+=("$line")
  done < "$ENV_FILE"
else
  # Pull variable NAMES from the source repo, then get each value
  SRC_REPO_FULL="$OWNER/$FROM_REPO"
  echo "Reading variables from $SRC_REPO_FULL ..."
  NAMES=$(gh variable list --repo "$SRC_REPO_FULL" --json name --jq '.[].name')
  while read -r NAME; do
    [[ -z "$NAME" ]] && continue
    VALUE=$(gh variable get "$NAME" --repo "$SRC_REPO_FULL" --json value --jq '.value')
    VARS+=("$NAME=$VALUE")
  done <<< "$NAMES"
fi

# Get all repos for the owner (source-only, excludes forks/archived by default)
REPOS_JSON=$(gh repo list "$OWNER" --limit 200 --json name,isArchived,isFork,visibility)
TARGETS=$(echo "$REPOS_JSON" | jq -r \
  --arg re "$INCLUDE_REGEX" '
  .[]
  | select(.isArchived==false and .isFork==false)
  | select(.name|test($re))
  | .name
')

apply_vars_to_repo () {
  local repo="$1"
  # Skip excluded
  if [[ -n "${EXCLUDE_SET[$repo]+x}" ]]; then
    echo "Skipping (excluded): $repo"
    return
  fi
  echo "==> $OWNER/$repo"
  for kv in "${VARS[@]}"; do
    KEY="${kv%%=*}"
    VAL="${kv#*=}"
    if [[ "$DRY_RUN" == true ]]; then
      echo "  DRY-RUN gh variable set $KEY --repo $OWNER/$repo  (value length: ${#VAL})"
    else
      gh variable set "$KEY" --repo "$OWNER/$repo" --body "$VAL"
    fi
  done
}

# Apply to each target repo
while read -r REPO; do
  [[ -z "$REPO" ]] && continue
  apply_vars_to_repo "$REPO"
done <<< "$TARGETS"

echo "Done."
if [[ "$DRY_RUN" == true ]]; then
  echo "DRY-RUN only. Re-run without --dry-run to apply."
fi
