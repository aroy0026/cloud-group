# Frontend Environment Setup

The React frontend lives outside this folder in:

```text
../frontend/
```

This folder contains the environment template needed to connect it to a recreated backend.

## Required Env File

Create:

```text
frontend/.env
```

Use `frontend.env.example` as the template.

## Variables

```text
VITE_AWS_REGION=ap-southeast-2
VITE_COGNITO_USER_POOL_ID=<created-user-pool-id>
VITE_COGNITO_APP_CLIENT_ID=<created-app-client-id>
VITE_API_BASE_URL=<api-gateway-base-url>
```

## Run

```bash
cd ../frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Build

```bash
npm run build
```

## Functional Test

1. Sign up.
2. Verify email.
3. Sign in.
4. Upload image and video.
5. Search by tag/species/thumbnail/file.
6. Bulk edit tags.
7. Subscribe to tag.
8. Delete media.
9. Sign out.

