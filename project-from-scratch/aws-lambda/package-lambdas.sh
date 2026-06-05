#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${ROOT}/source"
DIST="${ROOT}/dist"
BUILD_ROOT="${ROOT}/.build"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

rm -rf "${DIST}" "${BUILD_ROOT}"
mkdir -p "${DIST}" "${BUILD_ROOT}"

copy_source() {
  local function_dir="$1"
  local stage="$2"
  mkdir -p "${stage}/common"
  cp "${SRC}/${function_dir}/handler.py" "${stage}/handler.py"
  cp "${SRC}/common/"*.py "${stage}/common/"
  cp "${SRC}/common/labels.txt" "${stage}/common/labels.txt"
}

zip_stage() {
  local stage="$1"
  local output="$2"
  (cd "${stage}" && zip -qr "${output}" .)
}

package_small() {
  local function_dir="$1"
  local stage="${BUILD_ROOT}/${function_dir}"
  mkdir -p "${stage}"
  copy_source "${function_dir}" "${stage}"
  zip_stage "${stage}" "${DIST}/${function_dir}.zip"
}

package_with_deps() {
  local function_dir="$1"
  local stage="${BUILD_ROOT}/${function_dir}"
  shift
  mkdir -p "${stage}"
  python3 -m pip install \
    --target "${stage}" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version "${PYTHON_VERSION/./}" \
    --only-binary=:all: \
    "$@"
  copy_source "${function_dir}" "${stage}"
  zip_stage "${stage}" "${DIST}/${function_dir}.zip"
}

for fn in \
  files_delete \
  files_list \
  notifications_settings \
  notifications_subscriptions \
  query_by_species \
  query_by_tags \
  query_by_thumbnail \
  tags_bulk_edit \
  upload \
  upload_complete \
  upload_prepare
do
  package_small "${fn}"
done

package_with_deps query_by_file google-auth requests
package_with_deps media_processor opencv-python-headless google-auth requests

ls -lh "${DIST}"

