# Frontend Deployment — S3 + CloudFront
## EcoLens — Day 1 Patch (Frontend Deployment)

---

## Deployment Config Reference

```
S3 Bucket:           ecolens-frontend-savio-melbourne
S3 Region:           ap-southeast-4
CloudFront ID:       E1DNPE5W6SVY2F
CloudFront URL:      https://d2djf0hsofgar8.cloudfront.net
Local Dev URL:       http://localhost:5173
```

---

## Why CloudFront?

```
S3 static hosting → HTTP only → Cognito rejects HTTP callback URLs
S3 + CloudFront   → HTTPS    → Cognito accepts HTTPS callback URLs ✅
```

---

## Step 1 — Create S3 Bucket for Frontend

```powershell
aws s3api create-bucket `
  --bucket ecolens-frontend-savio-melbourne `
  --region ap-southeast-4 `
  --create-bucket-configuration LocationConstraint=ap-southeast-4

aws s3api put-public-access-block `
  --bucket ecolens-frontend-savio-melbourne `
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

[System.IO.File]::WriteAllText("$env:TEMP\frontend-policy.json", '{"Version":"2012-10-17","Statement":[{"Sid":"PublicReadGetObject","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::ecolens-frontend-savio-melbourne/*"}]}')

aws s3api put-bucket-policy `
  --bucket ecolens-frontend-savio-melbourne `
  --policy file://$env:TEMP/frontend-policy.json

aws s3 website s3://ecolens-frontend-savio-melbourne `
  --index-document index.html `
  --error-document index.html
```

---

## Step 2 — Create CloudFront Distribution

```powershell
[System.IO.File]::WriteAllText("$env:TEMP\cf-config.json", '{"CallerReference":"ecolens-frontend-2026","Origins":{"Quantity":1,"Items":[{"Id":"ecolens-frontend-origin","DomainName":"ecolens-frontend-savio-melbourne.s3-website.ap-southeast-4.amazonaws.com","CustomOriginConfig":{"HTTPPort":80,"HTTPSPort":443,"OriginProtocolPolicy":"http-only"}}]},"DefaultCacheBehavior":{"TargetOriginId":"ecolens-frontend-origin","ViewerProtocolPolicy":"redirect-to-https","CachePolicyId":"658327ea-f89d-4fab-a63d-7e88639e58f6","AllowedMethods":{"Quantity":2,"Items":["GET","HEAD"]}},"Comment":"EcoLens Frontend","Enabled":true,"DefaultRootObject":"index.html","CustomErrorResponses":{"Quantity":2,"Items":[{"ErrorCode":403,"ResponsePagePath":"/index.html","ResponseCode":"200","ErrorCachingMinTTL":0},{"ErrorCode":404,"ResponsePagePath":"/index.html","ResponseCode":"200","ErrorCachingMinTTL":0}]}}')

aws cloudfront create-distribution `
  --distribution-config file://$env:TEMP/cf-config.json
```

> Note: S3 website endpoint format for ap-southeast-4:
> `bucket-name.s3-website.ap-southeast-4.amazonaws.com`
> (dot before region, not hyphen)

---

## Step 3 — Update Cognito Callback URLs

```powershell
aws cognito-idp update-user-pool-client `
  --user-pool-id ap-southeast-4_W2HOAT28m `
  --client-id 3pn6vklcfh4rk7v3ga52fp6egv `
  --callback-urls "http://localhost:5173" "https://d2djf0hsofgar8.cloudfront.net" `
  --logout-urls "http://localhost:5173" "https://d2djf0hsofgar8.cloudfront.net" `
  --region ap-southeast-4
```

---

## Step 4 — Build and Deploy

```powershell
cd ecolens/frontend

pnpm run build

aws s3 sync dist/ s3://ecolens-frontend-savio-melbourne --delete
```

---

## Step 5 — Invalidate CloudFront Cache

After every redeployment, invalidate cache so users get the latest version:

```powershell
aws cloudfront create-invalidation `
  --distribution-id E1DNPE5W6SVY2F `
  --paths "/*"
```

---

## Verification

**Test 1 — CloudFront URL loads**
```
https://d2djf0hsofgar8.cloudfront.net
```
Expected: Login page loads with HTTPS ✅

**Test 2 — HTTP redirects to HTTPS**
```
http://d2djf0hsofgar8.cloudfront.net
```
Expected: Automatically redirects to HTTPS ✅

**Test 3 — React Router works on refresh**
1. Log in and navigate to dashboard
2. Refresh the page
3. Expected: Dashboard loads (not 403) ✅

---

## Redeployment Steps

Whenever you make frontend changes:

```powershell
cd ecolens/frontend

pnpm run build

aws s3 sync dist/ s3://ecolens-frontend-savio-melbourne --delete

aws cloudfront create-invalidation `
  --distribution-id E1DNPE5W6SVY2F `
  --paths "/*"
```

---

## Checklist

```
☑ S3 bucket created (ecolens-frontend-savio-melbourne)
☑ Public access enabled
☑ Bucket policy attached (public read)
☑ Static website hosting enabled
☑ CloudFront distribution created (E1DNPE5W6SVY2F)
☑ Origin set to S3 website endpoint
☑ HTTPS redirect enabled
☑ Custom error responses (403+404 → index.html)
☑ Cognito callback URLs updated
☑ Frontend built and deployed
☑ CloudFront URL loading correctly
```
