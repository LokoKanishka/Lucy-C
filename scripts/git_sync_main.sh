#!/usr/bin/env bash
set -euo pipefail

REMOTE="origin"
BASE_BRANCH="main"
REPO=""
FORCE_PUSH="false"

usage() {
  cat <<'USAGE'
Usage:
  scripts/git_sync_main.sh [--repo PATH] [--base main] [--remote origin] [--force-with-lease]

Examples:
  scripts/git_sync_main.sh
  scripts/git_sync_main.sh --repo "/home/lucy-ubuntu/Escritorio/lucy c demon/fusion/lucy-fusion"
  scripts/git_sync_main.sh --base main --force-with-lease
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --base)
      BASE_BRANCH="${2:-}"
      shift 2
      ;;
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --force-with-lease)
      FORCE_PUSH="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  if REPO_FROM_GIT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    REPO="$REPO_FROM_GIT"
  else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
  fi
fi

if [[ ! -d "$REPO/.git" ]]; then
  echo "Error: '$REPO' is not a git repository (.git missing)." >&2
  exit 1
fi

CURRENT_BRANCH="$(git -C "$REPO" branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  echo "Error: detached HEAD detected; checkout a branch first." >&2
  exit 1
fi

echo "Repo:   $REPO"
echo "Branch: $CURRENT_BRANCH"
echo "Base:   $REMOTE/$BASE_BRANCH"

git -C "$REPO" fetch "$REMOTE"
git -C "$REPO" rebase "$REMOTE/$BASE_BRANCH"

if [[ "$FORCE_PUSH" == "true" ]]; then
  git -C "$REPO" push --force-with-lease "$REMOTE" "$CURRENT_BRANCH"
else
  git -C "$REPO" push -u "$REMOTE" "$CURRENT_BRANCH"
fi

git -C "$REPO" status -sb
