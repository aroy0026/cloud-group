#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-ap-southeast-2}"

create_table() {
  local name="$1"
  shift
  if aws dynamodb describe-table --table-name "${name}" --region "${REGION}" >/dev/null 2>&1; then
    echo "exists: ${name}"
    return
  fi
  aws dynamodb create-table --table-name "${name}" --region "${REGION}" "$@"
  aws dynamodb wait table-exists --table-name "${name}" --region "${REGION}"
  echo "created: ${name}"
}

create_table ecolens-media \
  --billing-mode PAY_PER_REQUEST \
  --attribute-definitions AttributeName=ownerId,AttributeType=S AttributeName=id,AttributeType=S \
  --key-schema AttributeName=ownerId,KeyType=HASH AttributeName=id,KeyType=RANGE

create_table ecolens-checksums \
  --billing-mode PAY_PER_REQUEST \
  --attribute-definitions AttributeName=checksum,AttributeType=S \
  --key-schema AttributeName=checksum,KeyType=HASH

create_table ecolens-subscriptions \
  --billing-mode PAY_PER_REQUEST \
  --attribute-definitions AttributeName=ownerId,AttributeType=S \
  --key-schema AttributeName=ownerId,KeyType=HASH

create_table ecolens-settings \
  --billing-mode PAY_PER_REQUEST \
  --attribute-definitions AttributeName=ownerId,AttributeType=S \
  --key-schema AttributeName=ownerId,KeyType=HASH

