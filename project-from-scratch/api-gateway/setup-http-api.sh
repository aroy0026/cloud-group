#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
API_NAME="${API_NAME:-ecolens-api}"
COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:?Set COGNITO_USER_POOL_ID}"
COGNITO_APP_CLIENT_ID="${COGNITO_APP_CLIENT_ID:?Set COGNITO_APP_CLIENT_ID}"
CORS_ORIGIN="${CORS_ORIGIN:-http://localhost:5173}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

API_ID="$(
  aws apigatewayv2 create-api \
    --name "${API_NAME}" \
    --protocol-type HTTP \
    --cors-configuration "AllowOrigins=${CORS_ORIGIN},AllowMethods=GET,POST,PUT,DELETE,OPTIONS,AllowHeaders=authorization,content-type,MaxAge=300" \
    --region "${AWS_REGION}" \
    --query 'ApiId' \
    --output text
)"

ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}"
AUTHORIZER_ID="$(
  aws apigatewayv2 create-authorizer \
    --api-id "${API_ID}" \
    --name CognitoJwtAuthorizer \
    --authorizer-type JWT \
    --identity-source '$request.header.Authorization' \
    --jwt-configuration "Audience=${COGNITO_APP_CLIENT_ID},Issuer=${ISSUER}" \
    --region "${AWS_REGION}" \
    --query 'AuthorizerId' \
    --output text
)"

aws apigatewayv2 create-stage \
  --api-id "${API_ID}" \
  --stage-name '$default' \
  --auto-deploy \
  --region "${AWS_REGION}" >/dev/null

python3 - "$ROOT/routes.json" <<'PY' | while IFS=$'\t' read -r route_key function_name; do
import json
import sys

for route_key, function_name in json.load(open(sys.argv[1])):
    print(f"{route_key}\t{function_name}")
PY
  FUNCTION_ARN="$(
    aws lambda get-function \
      --function-name "${function_name}" \
      --region "${AWS_REGION}" \
      --query 'Configuration.FunctionArn' \
      --output text
  )"

  INTEGRATION_ID="$(
    aws apigatewayv2 create-integration \
      --api-id "${API_ID}" \
      --integration-type AWS_PROXY \
      --integration-uri "${FUNCTION_ARN}" \
      --payload-format-version "2.0" \
      --region "${AWS_REGION}" \
      --query 'IntegrationId' \
      --output text
  )"

  aws apigatewayv2 create-route \
    --api-id "${API_ID}" \
    --route-key "${route_key}" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorization-type JWT \
    --authorizer-id "${AUTHORIZER_ID}" \
    --region "${AWS_REGION}" >/dev/null

  statement_id="AllowApiGateway-${API_ID}-${function_name}-${route_key//[^A-Za-z0-9]/}"
  aws lambda add-permission \
    --function-name "${function_name}" \
    --statement-id "${statement_id:0:100}" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/*" \
    --region "${AWS_REGION}" >/dev/null 2>&1 || true

  echo "route: ${route_key} -> ${function_name}"
done

API_BASE_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
echo "API_ID=${API_ID}"
echo "API_BASE_URL=${API_BASE_URL}"

