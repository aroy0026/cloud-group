#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
COGNITO_USER_POOL_NAME="${COGNITO_USER_POOL_NAME:-ecolens-users}"
COGNITO_APP_CLIENT_NAME="${COGNITO_APP_CLIENT_NAME:-ecolens-spa}"

USER_POOL_ID="$(
  aws cognito-idp create-user-pool \
    --region "${AWS_REGION}" \
    --pool-name "${COGNITO_USER_POOL_NAME}" \
    --username-attributes email \
    --auto-verified-attributes email \
    --policies 'PasswordPolicy={MinimumLength=8,RequireUppercase=false,RequireLowercase=false,RequireNumbers=true,RequireSymbols=false,TemporaryPasswordValidityDays=7}' \
    --schema \
      Name=email,AttributeDataType=String,Required=true,Mutable=true \
      Name=given_name,AttributeDataType=String,Required=true,Mutable=true \
      Name=family_name,AttributeDataType=String,Required=true,Mutable=true \
    --query 'UserPool.Id' \
    --output text
)"

APP_CLIENT_ID="$(
  aws cognito-idp create-user-pool-client \
    --region "${AWS_REGION}" \
    --user-pool-id "${USER_POOL_ID}" \
    --client-name "${COGNITO_APP_CLIENT_NAME}" \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --supported-identity-providers COGNITO \
    --access-token-validity 60 \
    --id-token-validity 60 \
    --refresh-token-validity 5 \
    --token-validity-units AccessToken=minutes,IdToken=minutes,RefreshToken=days \
    --query 'UserPoolClient.ClientId' \
    --output text
)"

echo "COGNITO_USER_POOL_ID=${USER_POOL_ID}"
echo "COGNITO_APP_CLIENT_ID=${APP_CLIENT_ID}"

