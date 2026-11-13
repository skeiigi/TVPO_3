#!/usr/bin/env bash
set -euo pipefail

repo="skeiigi/TVPO_3"
app_dir="/home/gitlab-runner/TVPO_3"
state_file="/home/gitlab-runner/.tvpo3-deployed-sha"

sha=$(curl -fsS "https://api.github.com/repos/$repo/commits/main" | python3 -c 'import json,sys; print(json.load(sys.stdin)["sha"])')
if [[ -f "$state_file" ]] && [[ "$(cat "$state_file")" == "$sha" ]]; then
  exit 0
fi

conclusion=$(curl -fsS "https://api.github.com/repos/$repo/actions/runs?head_sha=$sha&status=completed&per_page=10" |
  python3 -c 'import json,sys; runs=json.load(sys.stdin)["workflow_runs"]; print(runs[0]["conclusion"] if runs else "pending")')
if [[ "$conclusion" != "success" ]]; then
  echo "Коммит $sha ещё не прошёл CI: $conclusion"
  exit 0
fi

if [[ ! -d "$app_dir/.git" ]]; then
  git clone "https://github.com/$repo.git" "$app_dir"
else
  git -C "$app_dir" fetch origin main
  git -C "$app_dir" checkout -f main
  git -C "$app_dir" reset --hard origin/main
fi

cd "$app_dir"
CI_COMMIT_SHORT_SHA="${sha:0:7}" bash deploy.sh
printf '%s\n' "$sha" > "$state_file"
