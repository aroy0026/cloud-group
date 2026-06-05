# AWS API Gateway Setup
## EcoLens — Day 2, Phase 1

---

## API Gateway Config Reference

```
API Name:     ecolens-api
API ID:       g4raf95x4b
Stage:        dev
Base URL:     https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev
Region:       ap-southeast-4
Type:         REST API (Regional)
```

---

## Endpoint Map

| Method | Path | Lambda | Description |
|---|---|---|---|
| POST | /upload/presign | ecolens-upload-presign | Get presigned S3 URL for upload |
| POST | /upload/confirm | ecolens-upload-confirm | Confirm upload + trigger ML |
| GET | /media | ecolens-media | List all media |
| POST | /query/tags | ecolens-query | Search by species tags |
| POST | /query/thumbnail | ecolens-thumbnail-query | Find original from thumbnail URL |
| POST | /query/file | ecolens-file-query | Search by uploaded file |
| POST | /query/file/presign | ecolens-query-file-presign | Get presigned URL for file query |
| POST | /tags | ecolens-tags | Bulk add/remove tags |
| POST | /delete | ecolens-delete | Delete files |
| POST | /notify | ecolens-notify | Manage SNS subscriptions |

---

## Resource ID Map

```
Root:              uoa9ywl6pa
/upload:           8lv6ys
/upload/presign:   wsr5ar
/upload/confirm:   45338n
/media:            or0hwx
/query:            ellbl3
/query/tags:       x0yile
/query/thumbnail:  ywk7uq
/query/file:       pvwrcf
/query/file/presign: 8xk7ab
/tags:             onlhs0
/delete:           745qcn
/notify:           u25rrr
```

---

## Step 1 — Create REST API

```powershell
aws apigateway create-rest-api `
  --name ecolens-api `
  --description "EcoLens Media Management API" `
  --region ap-southeast-4
```

---

## Step 2 — Create Resources

```powershell
# Root resources
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part upload --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part query --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part tags --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part delete --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part notify --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id uoa9ywl6pa --path-part media --region ap-southeast-4

# Sub-resources under /upload
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id 8lv6ys --path-part presign --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id 8lv6ys --path-part confirm --region ap-southeast-4

# Sub-resources under /query
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id ellbl3 --path-part tags --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id ellbl3 --path-part thumbnail --region ap-southeast-4
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id ellbl3 --path-part file --region ap-southeast-4

# Sub-resource under /query/file
aws apigateway create-resource --rest-api-id g4raf95x4b --parent-id pvwrcf --path-part presign --region ap-southeast-4
```

---

## Step 3 — Enable CORS on All Resources

Use temp JSON files to avoid PowerShell escaping issues:

```powershell
[System.IO.File]::WriteAllText("$env:TEMP\mock.json", '{"application/json": "{\"statusCode\": 200}"}')
[System.IO.File]::WriteAllText("$env:TEMP\method-response.json", '{"method.response.header.Access-Control-Allow-Headers": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Origin": false}')
[System.IO.File]::WriteAllText("$env:TEMP\integration-response.json", '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,Authorization'"'"'", "method.response.header.Access-Control-Allow-Methods": "'"'"'POST,OPTIONS'"'"'", "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}')

$resources = @("wsr5ar", "45338n", "x0yile", "ywk7uq", "pvwrcf", "8xk7ab", "onlhs0", "745qcn", "u25rrr", "or0hwx")

foreach ($resourceId in $resources) {
    aws apigateway put-method --rest-api-id g4raf95x4b --resource-id $resourceId --http-method OPTIONS --authorization-type NONE --region ap-southeast-4
    aws apigateway put-integration --rest-api-id g4raf95x4b --resource-id $resourceId --http-method OPTIONS --type MOCK --request-templates file://$env:TEMP/mock.json --region ap-southeast-4
    aws apigateway put-method-response --rest-api-id g4raf95x4b --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters file://$env:TEMP/method-response.json --region ap-southeast-4
    aws apigateway put-integration-response --rest-api-id g4raf95x4b --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters file://$env:TEMP/integration-response.json --region ap-southeast-4
    Write-Host "CORS enabled for: $resourceId"
}
```

---

## Step 4 — Connect Lambda Integrations

For each endpoint, repeat these 3 commands:

```powershell
# Example for /upload/presign
aws apigateway put-method `
  --rest-api-id g4raf95x4b `
  --resource-id wsr5ar `
  --http-method POST `
  --authorization-type NONE `
  --region ap-southeast-4

aws apigateway put-integration `
  --rest-api-id g4raf95x4b `
  --resource-id wsr5ar `
  --http-method POST `
  --type AWS_PROXY `
  --integration-http-method POST `
  --uri "arn:aws:apigateway:ap-southeast-4:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-southeast-4:686112929724:function:ecolens-upload-presign/invocations" `
  --region ap-southeast-4

aws lambda add-permission `
  --function-name ecolens-upload-presign `
  --statement-id apigateway-invoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --source-arn "arn:aws:execute-api:ap-southeast-4:686112929724:g4raf95x4b/*/POST/upload/presign" `
  --region ap-southeast-4
```

Repeat for all endpoints — see individual Lambda READMEs for their specific resource IDs and URIs.

---

## Step 5 — Enable Binary Media Types

Required for file query (raw binary upload):

```powershell
aws apigateway update-rest-api `
  --rest-api-id g4raf95x4b `
  --patch-operations `
    op=add,path=/binaryMediaTypes/image~1jpeg `
    op=add,path=/binaryMediaTypes/image~1png `
    op=add,path=/binaryMediaTypes/image~1webp `
    op=add,path=/binaryMediaTypes/video~1mp4 `
  --region ap-southeast-4
```

---

## Step 6 — Deploy API

```powershell
aws apigateway create-deployment `
  --rest-api-id g4raf95x4b `
  --stage-name dev `
  --region ap-southeast-4
```

> Run this after every change to methods or integrations.

---

## Security

See `patches/cognito-authorizer/README.md` for attaching Cognito JWT
authorizer to all endpoints.

---

## Checklist

```
☑ REST API created (ecolens-api)
☑ All resources created
☑ CORS OPTIONS methods configured on all resources
☑ All Lambda integrations connected (AWS_PROXY)
☑ Lambda invoke permissions granted
☑ Binary media types enabled (image/jpeg, png, webp, video/mp4)
☑ API deployed to dev stage
☑ Cognito authorizer attached to all endpoints
☑ Base URL: https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev
```
