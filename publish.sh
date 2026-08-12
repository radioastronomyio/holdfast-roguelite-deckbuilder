#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR
readonly PRODUCTION_SOURCE="${SCRIPT_DIR}/game/dist"
readonly PRODUCTION_TARGET="/opt/agents/www/holdfast"

source_dir="${PRODUCTION_SOURCE}"
target_dir="${PRODUCTION_TARGET}"
deploy_only=0

fail() {
  printf 'publish.sh: %s\n' "$1" >&2
  exit 1
}

while (($# > 0)); do
  case "$1" in
    --deploy-only)
      deploy_only=1
      shift
      ;;
    --source)
      (($# >= 2)) || fail "--source requires a path"
      source_dir="$2"
      shift 2
      ;;
    --target)
      (($# >= 2)) || fail "--target requires a path"
      target_dir="$2"
      shift 2
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

source_dir="$(realpath -m -- "${source_dir}")"
target_dir="$(realpath -m -- "${target_dir}")"

if [[ "${HOLDFAST_PUBLISH_TEST:-0}" == "1" ]]; then
  test_root="${HOLDFAST_PUBLISH_TEST_ROOT:-}"
  [[ -n "${test_root}" ]] || fail "HOLDFAST_PUBLISH_TEST_ROOT is required in test mode"
  test_root="$(realpath -e -- "${test_root}")"
  [[ -d "${test_root}" && ! -L "${test_root}" ]] || fail "invalid HOLDFAST_PUBLISH_TEST_ROOT"
  case "${source_dir}" in
    "${test_root}"/*) ;;
    *) fail "source is outside HOLDFAST_PUBLISH_TEST_ROOT" ;;
  esac
  case "${target_dir}" in
    "${test_root}"/*) ;;
    *) fail "target is outside HOLDFAST_PUBLISH_TEST_ROOT" ;;
  esac
else
  [[ "${source_dir}" == "${PRODUCTION_SOURCE}" ]] || fail "production source must be ${PRODUCTION_SOURCE}"
  [[ "${target_dir}" == "${PRODUCTION_TARGET}" ]] || fail "production target must be ${PRODUCTION_TARGET}"
  ((deploy_only == 0)) || fail "--deploy-only is available only in test mode"
fi

if ((deploy_only == 0)); then
  (
    cd -- "${SCRIPT_DIR}/game"
    npm run build
  )
fi

[[ -d "${source_dir}" && ! -L "${source_dir}" ]] || fail "build source is missing or is a symbolic link: ${source_dir}"
if find -P "${source_dir}" -type l -print -quit | grep -q .; then
  fail "build source contains a symbolic link"
fi

mkdir -p -- "${target_dir}"
[[ -d "${target_dir}" && ! -L "${target_dir}" ]] || fail "publish target is not a real directory: ${target_dir}"
if find -P "${target_dir}" -type l -print -quit | grep -q .; then
  fail "publish target contains a symbolic link"
fi

rsync -a --delete --itemize-changes -- "${source_dir}/" "${target_dir}/"
diff -r -- "${source_dir}/" "${target_dir}/"

printf 'Published Holdfast to %s\n' "${target_dir}"
