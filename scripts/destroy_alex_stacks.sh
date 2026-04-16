#!/usr/bin/env bash
# Back-compat wrapper — delegates to destroy.sh (twin-style entry point).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" != "--yes" ]]; then
  echo "This removes all Terraform-managed AWS resources for Alex (stacks 8 → 2)."
  echo "Run on the machine that applied Terraform (local state) or use a runner with remote state."
  echo "Usage: $0 --yes"
  exit 1
fi
exec "${DIR}/destroy.sh" demo --yes
