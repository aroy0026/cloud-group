# AWS Cognito Setup
## EcoLens — Day 1, Phase 1

---

## Cognito Config Reference

```
Region:          ap-southeast-4
User Pool Name:  User pool - 1ohuo2
User Pool ID:    ap-southeast-4_W2HOAT28m
User Pool ARN:   arn:aws:cognito-idp:ap-southeast-4:686112929724:userpool/ap-southeast-4_W2HOAT28m
App Client Name: ecolens-spa-client
App Client ID:   3pn6vklcfh4rk7v3ga52fp6egv
Client Secret:   None (SPA client)
```

---

## What This Does

AWS Cognito handles all user authentication — sign-up, sign-in, email verification,
and JWT token generation. The frontend uses the ID token from Cognito to authenticate
all API Gateway requests.

---

## Step 1 — Create User Pool

1. Go to **AWS Console → Cognito → Create user pool**
2. Select **"Traditional web application"**
3. Configure:
   ```
   Application name:        ecolens-app
   Sign-in identifier:      Email
   Self-registration:       Enabled
   Required attributes:     family_name, given_name
   Return URL:              http://localhost:5173
   Client secret:           OFF
   ```
4. Click **"Create user directory"**

> The auto-created app client from this flow has a client secret —
> do NOT use it. Create a new SPA client in Step 2.

---

## Step 2 — Create SPA App Client (No Secret)

1. Go to **Cognito → User Pools → your pool → App clients**
2. Click **"Create app client"**
3. Configure:
   ```
   App type:    Single-page application (SPA)
   Name:        ecolens-spa-client
   Return URL:  http://localhost:5173
   Secret:      None (auto-disabled for SPA)
   ```
4. Click **"Create app client"**
5. Note the **Client ID**: `3pn6vklcfh4rk7v3ga52fp6egv`

---

## Step 3 — Frontend Environment Variables

Create a `.env` file in the `frontend/` root:

```env
VITE_AWS_REGION=ap-southeast-4
VITE_COGNITO_USER_POOL_ID=ap-southeast-4_W2HOAT28m
VITE_COGNITO_APP_CLIENT_ID=3pn6vklcfh4rk7v3ga52fp6egv
VITE_COGNITO_CLIENT_ID=3pn6vklcfh4rk7v3ga52fp6egv
VITE_API_BASE_URL=
```

> `VITE_API_BASE_URL` is filled in after API Gateway is created in Day 2.

---

## Verification

**Test 1 — User Pool exists**
```powershell
aws cognito-idp list-user-pools --max-results 10 --region ap-southeast-4
```
Expected: `ap-southeast-4_W2HOAT28m` appears in the list.

**Test 2 — App client has no secret**
```powershell
aws cognito-idp describe-user-pool-client `
  --user-pool-id ap-southeast-4_W2HOAT28m `
  --client-id 3pn6vklcfh4rk7v3ga52fp6egv `
  --region ap-southeast-4
```
Expected: `"ClientSecret"` field is absent from the response.

---

## Checklist

```
☑ User Pool created (ap-southeast-4_W2HOAT28m)
☑ Sign-in by email only
☑ Self-registration enabled
☑ Required attributes: family_name, given_name
☑ SPA App Client created (no secret)
☑ App Client ID noted (3pn6vklcfh4rk7v3ga52fp6egv)
☑ Frontend .env file created with Cognito values
```
