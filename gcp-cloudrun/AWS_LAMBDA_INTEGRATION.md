# AWS Lambda Integration

AWS Lambda calls the private Cloud Run `/query-file` endpoint for ML tagging.

## Live Cloud Run Endpoint

```text
https://aussie-ecolens-processor-665098755528.australia-southeast1.run.app/query-file
```

## Required Lambda Environment Variables

Set these on Lambda functions that call Cloud Run, especially:

- `ecolens-query-by-file`
- `ecolens-media-processor`

```text
QUERY_FILE_PROCESSOR_URL=https://aussie-ecolens-processor-665098755528.australia-southeast1.run.app/query-file
QUERY_FILE_PROCESSOR_TIMEOUT=120
CLOUD_RUN_AUDIENCE=https://aussie-ecolens-processor-665098755528.australia-southeast1.run.app
GCP_WIF_CREDENTIAL_CONFIG_SECRET=ecolens-gcp-wif-credential-config
GCP_SERVICE_ACCOUNT_EMAIL=aws-ecolens-invoker@project-b70b0656-b022-41bd-bc6.iam.gserviceaccount.com
```

## Workload Identity Federation

The deployed setup uses GCP Workload Identity Federation so Cloud Run can stay private.

AWS identity:

```text
arn:aws:iam::397450412956:role/ecolens-lambda-execution-role
```

GCP service account:

```text
aws-ecolens-invoker@project-b70b0656-b022-41bd-bc6.iam.gserviceaccount.com
```

GCP resources:

```text
Pool: aws-lambda-pool
Provider: aws-provider
```

AWS Secrets Manager secret:

```text
ecolens-gcp-wif-credential-config
```

The Lambda role needs `secretsmanager:GetSecretValue` on that secret.

## Cloud Run IAM

The GCP service account above needs:

```text
roles/run.invoker
```

on the Cloud Run service.

Do not make Cloud Run public unless explicitly choosing a simplified demo-only setup.

