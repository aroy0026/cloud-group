# SNS Tag Notification Setup

SNS provides tag-based email notifications.

## How It Works

1. User subscribes to a tag from the React UI.
2. `ecolens-notifications-subscriptions` stores the watched tag in DynamoDB.
3. The Lambda creates or reuses an SNS topic:

```text
${SNS_TOPIC_PREFIX}${tag}
```

Example:

```text
ecolens-dingo
```

4. The Lambda subscribes the user's Cognito email to the topic.
5. User must confirm the SNS email subscription.
6. When new media is processed, `ecolens-media-processor` publishes to matching tag topics.

## Required Env Var

```text
SNS_TOPIC_PREFIX=ecolens-
```

## Required IAM

The Lambda execution role needs:

```text
sns:CreateTopic
sns:Subscribe
sns:Publish
```

on:

```text
arn:aws:sns:${AWS_REGION}:${AWS_ACCOUNT_ID}:ecolens-*
```

## Confirm Email

SNS email subscriptions do not become active until the user clicks the confirmation link emailed by AWS.

For demo:

1. Add subscription in UI.
2. Open email inbox.
3. Click "Confirm subscription".
4. Upload matching media.
5. Show the notification email.

## Optional Manual Topic Test

```bash
aws sns create-topic --name ecolens-dingo --region ap-southeast-2
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-southeast-2:<account-id>:ecolens-dingo \
  --protocol email \
  --notification-endpoint you@example.com \
  --region ap-southeast-2
```

