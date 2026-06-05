# AWS IAM Setup

The Lambda functions need one execution role with scoped access to:

- CloudWatch Logs
- S3 upload bucket
- DynamoDB tables
- SNS topic create/subscribe/publish
- AWS Secrets Manager WIF config secret

## Create Role

```bash
set -a
source ../.env
set +a
./create-lambda-role.sh
```

The script prints:

```text
LAMBDA_ROLE_ARN=...
```

Copy it into `.env`.

## Policies Included

- `lambda-trust-policy.json`: lets AWS Lambda assume the role.
- `lambda-execution-policy.json`: runtime access for the app.

The policy uses the current table names, bucket name, account id, and region from `.env`.

## Notes

For a production system, split this into per-function roles. For the assignment, one scoped role is simpler to explain and operate.

