#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---dry-run}"
DEFAULT_BRANCH="${2:-master}"

case "$MODE" in
  --dry-run|--apply) ;;
  *) echo "usage: $0 [--dry-run|--apply] [default-branch]" >&2; exit 2 ;;
esac

# Work only from live remote refs; never infer merged state from branch names.
git fetch --prune origin "+refs/heads/*:refs/remotes/origin/*"
DEFAULT_REF="refs/remotes/origin/${DEFAULT_BRANCH}"
git rev-parse --verify "$DEFAULT_REF" >/dev/null

candidates=()
while IFS= read -r branch; do
  [[ -n "$branch" ]] || continue
  [[ "$branch" == "$DEFAULT_BRANCH" ]] && continue
  [[ "$branch" == "HEAD" ]] && continue

  ref="refs/remotes/origin/${branch}"
  if git merge-base --is-ancestor "$ref" "$DEFAULT_REF"; then
    candidates+=("$branch")
  fi
done < <(git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin | LC_ALL=C sort)

if ((${#candidates[@]} == 0)); then
  echo "No merged remote branches to prune."
  exit 0
fi

printf 'Merged branch candidates (%d):\n' "${#candidates[@]}"
printf '  %s\n' "${candidates[@]}"

if [[ "$MODE" == "--dry-run" ]]; then
  echo "Dry run only; no remote refs changed."
  exit 0
fi

for branch in "${candidates[@]}"; do
  # Re-fetch and re-prove immediately before each destructive mutation.
  git fetch --prune origin "+refs/heads/${DEFAULT_BRANCH}:refs/remotes/origin/${DEFAULT_BRANCH}" "+refs/heads/${branch}:refs/remotes/origin/${branch}"
  ref="refs/remotes/origin/${branch}"
  if ! git merge-base --is-ancestor "$ref" "$DEFAULT_REF"; then
    echo "Refusing to delete ${branch}: it is no longer proven merged into ${DEFAULT_BRANCH}." >&2
    exit 1
  fi
  echo "Deleting merged remote branch: ${branch}"
  git push origin --delete "$branch"
done
