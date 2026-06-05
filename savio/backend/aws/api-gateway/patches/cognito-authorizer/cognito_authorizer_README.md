# Patch — Cognito JWT Authorizer
## EcoLens — API Gateway Security Patch

---

## What This Patch Does

Attaches AWS Cognito as an authorizer to all API Gateway endpoints.
Without this patch all endpoints are publicly accessible — anyone who
knows the API URL can call them without logging in. With this patch
every request must include a valid Cognito JWT token in the
Authorization header otherwise API Gateway returns 401 before the
Lambda is even invoked.

### Marks Impact
```
Section 1.2 — Access Control
Without patch:  Endpoints publicly accessible → partial marks
With patch:     All endpoints protected by Cognito JWT → full marks
```

---

## Authorizer Config

```
Authorizer ID:   nhocjw
Authorizer Name: CognitoAuthorizer
Type:            COGNITO_USER_POOLS
User Pool ARN:   arn:aws:cognito-idp:ap-southeast-4:686112929724:userpool/ap-southeast-4_W2HOAT28m
Identity Source: method.request.header.Authorization
API ID:          g4raf95x4b
```

---

## Step 1 — Create Cognito Authorizer

```powershell
aws apigateway create-authorizer `
  --rest-api-id g4raf95x4b `
  --name CognitoAuthorizer `
  --type COGNITO_USER_POOLS `
  --provider-arns "arn:aws:cognito-idp:ap-southeast-4:686112929724:userpool/ap-southeast-4_W2HOAT28m" `
  --identity-source "method.request.header.Authorization" `
  --region ap-southeast-4
```

---

## Step 2 — Attach to All POST Endpoints

```powershell
$resources = @(
    @{id="wsr5ar"; path="/upload/presign"},
    @{id="45338n"; path="/upload/confirm"},
    @{id="x0yile"; path="/query/tags"},
    @{id="ywk7uq"; path="/query/thumbnail"},
    @{id="pvwrcf"; path="/query/file"},
    @{id="8xk7ab"; path="/query/file/presign"},
    @{id="onlhs0"; path="/tags"},
    @{id="745qcn"; path="/delete"},
    @{id="u25rrr"; path="/notify"}
)

foreach ($resource in $resources) {
    aws apigateway update-method `
      --rest-api-id g4raf95x4b `
      --resource-id $resource.id `
      --http-method POST `
      --patch-operations op=replace,path=/authorizationType,value=COGNITO_USER_POOLS op=replace,path=/authorizerId,value=nhocjw `
      --region ap-southeast-4
    Write-Host "Authorizer attached to: $($resource.path)"
}
```

---

## Step 3 — Attach to GET /media

```powershell
aws apigateway update-method `
  --rest-api-id g4raf95x4b `
  --resource-id or0hwx `
  --http-method GET `
  --patch-operations op=replace,path=/authorizationType,value=COGNITO_USER_POOLS op=replace,path=/authorizerId,value=nhocjw `
  --region ap-southeast-4
```

---

## Step 4 — Redeploy API

```powershell
aws apigateway create-deployment `
  --rest-api-id g4raf95x4b `
  --stage-name dev `
  --region ap-southeast-4
```

---

## Frontend — No Changes Required

The frontend already sends the Cognito ID token on every request:

```typescript
// In api.ts request() function
const token = await cognitoGetCurrentIdToken();
if (token) headers.set("Authorization", `Bearer ${token}`);
```

API Gateway accepts the `Bearer {token}` format automatically.

---

## Verification

**Test 1 — Unauthenticated request blocked:**
```powershell
Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/media" `
  -Method GET
```
Expected: `{"message":"Unauthorized"}` with 401 status ✅

**Test 2 — Authenticated frontend works:**
1. Sign in at `http://localhost:5173`
2. Dashboard loads with media
3. All features work correctly ✅

---

## Checklist

```
☑ CognitoAuthorizer created (ID: nhocjw)
☑ Linked to user pool: ap-southeast-4_W2HOAT28m
☑ Token source: Authorization header
☑ POST /upload/presign → authorizer attached
☑ POST /upload/confirm → authorizer attached
☑ POST /query/tags → authorizer attached
☑ POST /query/thumbnail → authorizer attached
☑ POST /query/file → authorizer attached
☑ POST /query/file/presign → authorizer attached
☑ POST /tags → authorizer attached
☑ POST /delete → authorizer attached
☑ POST /notify → authorizer attached
☑ GET /media → authorizer attached
☑ API redeployed to dev stage
☑ Unauthenticated requests return 401
☑ Frontend still works correctly
```
