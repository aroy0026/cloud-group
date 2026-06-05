# AWS Cognito Setup

Cognito provides sign-up, email verification, sign-in, sign-out, and JWTs for protected API calls.

## Requirements

Assignment-required user attributes:

- email
- first name, Cognito attribute `given_name`
- last name, Cognito attribute `family_name`
- password

Email verification must be enabled.

## Create User Pool

Run:

```bash
set -a
source ../.env
set +a
./create-cognito.sh
```

The script prints:

```text
COGNITO_USER_POOL_ID=...
COGNITO_APP_CLIENT_ID=...
```

Copy those values into:

- `project-from-scratch/.env`
- `frontend/.env`

## Frontend Env

```text
VITE_AWS_REGION=ap-southeast-2
VITE_COGNITO_USER_POOL_ID=<user-pool-id>
VITE_COGNITO_APP_CLIENT_ID=<app-client-id>
```

## API Gateway Authorizer Values

Issuer:

```text
https://cognito-idp.${AWS_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}
```

Audience:

```text
${COGNITO_APP_CLIENT_ID}
```

## Test User Flow

1. Open frontend `/signup`.
2. Enter first name, last name, email, password.
3. Check email for verification code.
4. Open `/verify-email`.
5. Enter email and code.
6. Sign in.
7. Confirm protected routes load.
8. Sign out.
9. Confirm protected routes redirect to `/signin`.

