#!/usr/bin/env bash
set -euo pipefail

target=/home/gitlab-runner/mortgage-calculator
mkdir -p "$target"
install -m 0644 app.py mortgage.py "$target/"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user restart mortgage-calculator.service
for attempt in 1 2 3 4 5; do
  if curl --fail --silent http://127.0.0.1:8000/health | grep -qx ok; then
    echo "Развёртывание успешно: $(git rev-parse --short HEAD)"
    exit 0
  fi
  sleep 1
done
echo "Сервис не ответил на проверку /health" >&2
exit 1
