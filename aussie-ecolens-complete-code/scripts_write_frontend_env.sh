#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

: "${VITE_API_BASE_URL:?Set VITE_API_BASE_URL to the API Gateway endpoint.}"

VITE_AWS_REGION="${VITE_AWS_REGION:-ap-southeast-2}"
VITE_COGNITO_USER_POOL_ID="${VITE_COGNITO_USER_POOL_ID:-ap-southeast-2_y1ddoO0pv}"
VITE_COGNITO_CLIENT_ID="${VITE_COGNITO_CLIENT_ID:-22jl47515ubj2b3ib3j8qm2o6i}"

cat > "$ROOT/frontend/.env.local" <<EOF
VITE_AWS_REGION=$VITE_AWS_REGION
VITE_COGNITO_USER_POOL_ID=$VITE_COGNITO_USER_POOL_ID
VITE_COGNITO_CLIENT_ID=$VITE_COGNITO_CLIENT_ID
VITE_API_BASE_URL=$VITE_API_BASE_URL
EOF

echo "Updated frontend/.env.local"

