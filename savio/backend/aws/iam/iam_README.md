# AWS IAM Fine-Grained Roles

## EcoLens — Day 1, Phase 3

---

## Role Overview

One minimal role per Lambda function. Each role only has the permissions
it actually needs — nothing more. This replaces the overly permissive
single-role approach used in AWS Academy.

| Role                     | Lambda Function(s)                         | Key Permissions                                      |
| ------------------------ | ------------------------------------------ | ---------------------------------------------------- |
| `ecolens-upload-role`    | ecolens-upload                             | S3 put/get, DynamoDB put/query, SNS publish          |
| `ecolens-thumbnail-role` | ecolens-thumbnail                          | S3 get uploads/, S3 put thumbnails/, DynamoDB update |
| `ecolens-query-role`     | ecolens-query, thumbnail-query, file-query | S3 get, S3 put/delete temp-query/, DynamoDB scan     |
| `ecolens-tags-role`      | ecolens-tags                               | DynamoDB scan/update only                            |
| `ecolens-delete-role`    | ecolens-delete                             | S3 delete uploads+thumbnails, DynamoDB scan/delete   |
| `ecolens-notify-role`    | ecolens-notify                             | SNS create/subscribe only                            |

---

## How Each Role Works

Every role is created in two steps:

1. `create-role` — defines who can use this role (Lambda service)
2. `put-role-policy` — defines what this role can do (permissions)

---

## Role 1 — ecolens-upload-role

```powershell
aws iam create-role `
  --role-name ecolens-upload-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-upload-role `
  --policy-name ecolens-upload-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"S3UploadAccess\",\"Effect\":\"Allow\",\"Action\":[\"s3:PutObject\",\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/*\"},{\"Sid\":\"DynamoDBUploadAccess\",\"Effect\":\"Allow\",\"Action\":[\"dynamodb:PutItem\",\"dynamodb:Query\",\"dynamodb:UpdateItem\",\"dynamodb:GetItem\"],\"Resource\":[\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media\",\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media/index/checksum-index\"]},{\"Sid\":\"SNSNotifyAccess\",\"Effect\":\"Allow\",\"Action\":[\"sns:CreateTopic\",\"sns:Publish\",\"sns:ListSubscriptionsByTopic\"],\"Resource\":\"arn:aws:sns:ap-southeast-4:686112929724:ecolens-tag-*\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-upload*:*\"}]}'
```

---

## Role 2 — ecolens-thumbnail-role

```powershell
aws iam create-role `
  --role-name ecolens-thumbnail-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-thumbnail-role `
  --policy-name ecolens-thumbnail-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"S3ReadUploads\",\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/uploads/*\"},{\"Sid\":\"S3WriteThumbnails\",\"Effect\":\"Allow\",\"Action\":[\"s3:PutObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/thumbnails/*\"},{\"Sid\":\"DynamoDBThumbnailAccess\",\"Effect\":\"Allow\",\"Action\":[\"dynamodb:Scan\",\"dynamodb:UpdateItem\"],\"Resource\":\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-thumbnail:*\"}]}'
```

---

## Role 3 — ecolens-query-role

```powershell
aws iam create-role `
  --role-name ecolens-query-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-query-role `
  --policy-name ecolens-query-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"S3QueryAccess\",\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/*\"},{\"Sid\":\"S3TempFileAccess\",\"Effect\":\"Allow\",\"Action\":[\"s3:PutObject\",\"s3:DeleteObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/temp-query/*\"},{\"Sid\":\"DynamoDBQueryAccess\",\"Effect\":\"Allow\",\"Action\":[\"dynamodb:Scan\"],\"Resource\":\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":[\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-query:*\",\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-thumbnail-query:*\",\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-file-query:*\"]}]}'
```

---

## Role 4 — ecolens-tags-role

```powershell
aws iam create-role `
  --role-name ecolens-tags-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-tags-role `
  --policy-name ecolens-tags-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"DynamoDBTagsAccess\",\"Effect\":\"Allow\",\"Action\":[\"dynamodb:Scan\",\"dynamodb:UpdateItem\"],\"Resource\":\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-tags:*\"}]}'
```

---

## Role 5 — ecolens-delete-role

```powershell
aws iam create-role `
  --role-name ecolens-delete-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-delete-role `
  --policy-name ecolens-delete-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"S3DeleteUploads\",\"Effect\":\"Allow\",\"Action\":[\"s3:DeleteObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/uploads/*\"},{\"Sid\":\"S3DeleteThumbnails\",\"Effect\":\"Allow\",\"Action\":[\"s3:DeleteObject\"],\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/thumbnails/*\"},{\"Sid\":\"DynamoDBDeleteAccess\",\"Effect\":\"Allow\",\"Action\":[\"dynamodb:Scan\",\"dynamodb:DeleteItem\"],\"Resource\":\"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-delete:*\"}]}'
```

---

## Role 6 — ecolens-notify-role

```powershell
aws iam create-role `
  --role-name ecolens-notify-role `
  --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'

aws iam put-role-policy `
  --role-name ecolens-notify-role `
  --policy-name ecolens-notify-policy `
  --policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"SNSSubscribeAccess\",\"Effect\":\"Allow\",\"Action\":[\"sns:CreateTopic\",\"sns:Subscribe\",\"sns:ListSubscriptionsByTopic\"],\"Resource\":\"arn:aws:sns:ap-southeast-4:686112929724:ecolens-tag-*\"},{\"Sid\":\"CloudWatchLogsAccess\",\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-notify:*\"}]}'
```

---

## Verification

```powershell
aws iam list-roles --query "Roles[?starts_with(RoleName, 'ecolens')].RoleName" --output table
```

Expected output:

```
ecolens-delete-role
ecolens-notify-role
ecolens-query-role
ecolens-tags-role
ecolens-thumbnail-role
ecolens-upload-role
```

---

## Checklist

```
☑ ecolens-upload-role created + policy attached
☑ ecolens-thumbnail-role created + policy attached
☑ ecolens-query-role created + policy attached
☑ ecolens-tags-role created + policy attached
☑ ecolens-delete-role created + policy attached
☑ ecolens-notify-role created + policy attached
```
