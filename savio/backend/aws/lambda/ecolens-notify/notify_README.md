# ecolens-notify
## EcoLens Lambda Function

---

## What This Does

Manages SNS email subscriptions for species tag alerts. Users can
subscribe to a species tag and receive an email whenever a new file
containing that species is uploaded. Supports subscribe, unsubscribe,
and list actions in a single endpoint.

---

## Trigger

```
API Gateway: POST /notify
```

---

## IAM Role

```
ecolens-notify-role
```

---

## Request Body — Subscribe

```json
{
  "action": "subscribe",
  "tag": "felis_catus",
  "email": "user@example.com"
}
```

## Request Body — Unsubscribe

```json
{
  "action": "unsubscribe",
  "tag": "felis_catus",
  "email": "user@example.com"
}
```

## Request Body — List

```json
{
  "action": "list"
}
```

---

## Response — Subscribe

```json
{
  "message": "Subscription request sent! Check user@example.com to confirm.",
  "tag": "felis_catus",
  "email": "user@example.com"
}
```

## Response — List

```json
{
  "tags": ["felis_catus", "sus_scrofa"]
}
```

---

## Flow

```
Subscribe:
  → Get or create SNS topic ecolens-tag-{tag}
  → Subscribe email to topic
  → User receives confirmation email from AWS SNS
  → User clicks confirm → subscription active
  → Next upload with matching species → email notification sent

Unsubscribe:
  → Find SNS topic for tag
  → Find active subscription matching email
  → Unsubscribe

List:
  → List all ecolens-tag-* SNS topics
  → For each topic with active subscriptions → add tag to list
  → Return subscribed tag names
```

---

## SNS Topic Naming Convention

```
Topic name: ecolens-tag-{tag_with_underscores_replaced_by_hyphens}
Example:    ecolens-tag-felis-catus  (for Felis_catus)
```

---

## Key Config

```python
REGION = 'ap-southeast-4'
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-notify

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-notify `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-notify-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-notify `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /notify
Method:      POST
Type:        AWS_PROXY
Resource ID: u25rrr
API ID:      g4raf95x4b
```

---

## Verification

```powershell
$body = '{"action": "subscribe", "tag": "felis_catus", "email": "your@email.com"}'

Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/notify" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Expected: Confirmation email received from AWS SNS ✅

---

## Checklist

```
☑ Lambda created (ecolens-notify)
☑ Runtime: Python 3.12
☑ Role: ecolens-notify-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /notify connected
☑ Subscribe action working
☑ Confirmation email received and confirmed
☑ Unsubscribe action working
☑ List action working
☑ SNS topics auto-created per species tag
```
