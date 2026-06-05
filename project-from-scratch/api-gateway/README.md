# API Gateway Setup

This project uses an AWS API Gateway HTTP API in front of Lambda functions.

Every application route is protected by a Cognito JWT authorizer.

## Routes

See `routes.json`.

Core routes:

```text
POST   /upload/prepare
POST   /upload/complete
POST   /upload
GET    /files
POST   /files/delete
POST   /query/by-tags
POST   /query/by-species
POST   /query/by-thumbnail
POST   /query/by-file
POST   /tags/bulk-edit
GET    /notifications/subscriptions
POST   /notifications/subscriptions
DELETE /notifications/subscriptions
PUT    /notifications/settings
```

## Required Values

From `.env`:

```text
AWS_REGION
AWS_ACCOUNT_ID
API_NAME
COGNITO_USER_POOL_ID
COGNITO_APP_CLIENT_ID
CORS_ORIGIN
```

## Create API

Make sure Lambdas already exist, then run:

```bash
set -a
source ../.env
set +a
./setup-http-api.sh
```

The script prints:

```text
API_ID=...
API_BASE_URL=https://...
```

Copy `API_BASE_URL` into the frontend `.env`.

## CORS

The script configures CORS for:

```text
http://localhost:5173
```

For deployed frontend hosting, add your production domain as another allowed origin.

## Authorizer

Issuer:

```text
https://cognito-idp.${AWS_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}
```

Audience:

```text
${COGNITO_APP_CLIENT_ID}
```

## Test

Unauthenticated request should return `401`:

```bash
curl -i "${API_BASE_URL}/files"
```

Authenticated requests must include:

```text
Authorization: Bearer <Cognito ID token>
```

