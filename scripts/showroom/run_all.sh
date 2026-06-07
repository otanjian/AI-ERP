#!/usr/bin/env bash
# Run manufacturing showroom setup on ERPNext site (data/config only — no app code changes).
set -euo pipefail

BENCH_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SITE="${SITE:-west.bosofts.com}"

cd "$BENCH_DIR"

run_module() {
	local module="$1"
	echo "==> ${module}"
	SITE="${SITE}" "${BENCH_DIR}/env/bin/python" "${BENCH_DIR}/scripts/showroom/cli.py" "${module}"
}

case "${1:-all}" in
  backup)
    bench --site "$SITE" backup
    ;;
  coa)
    run_module setup_coa
    ;;
  settings)
    run_module setup_settings
    ;;
  masters)
    run_module setup_masters
    ;;
  flow)
    run_module run_flow
    ;;
  verify)
    run_module verify
    ;;
  accounts)
    run_module account_defaults
    ;;
  cancel)
    run_module cancel_flow
    ;;
  check_gl)
    run_module check_gl
    ;;
  reopen)
    run_module account_defaults
    run_module cancel_flow
    run_module run_flow
    run_module verify
    run_module check_gl
    ;;
  all)
    run_module setup_coa
    run_module setup_settings
    run_module setup_masters
    run_module run_flow
    run_module verify
    run_module check_gl
    bench --site "$SITE" clear-cache
    ;;
  *)
    echo "Usage: $0 [backup|coa|settings|masters|accounts|cancel|flow|verify|check_gl|reopen|all]"
    exit 1
    ;;
esac
