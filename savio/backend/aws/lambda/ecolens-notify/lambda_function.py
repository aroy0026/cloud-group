import json
import boto3

sns = boto3.client('sns', region_name='ap-southeast-4')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


def get_or_create_topic(tag):
    """Get or create an SNS topic for a species tag"""
    topic_name = 'ecolens-tag-' + tag.replace('_', '-').lower()
    response = sns.create_topic(Name=topic_name)
    return response['TopicArn']


def lambda_handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'OK'})
            }

        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        action = body.get('action', 'subscribe')
        tag = body.get('tag', '').strip()
        email = body.get('email', '').strip()

        # Handle list action
        if action == 'list':
            # List all ecolens SNS topics and their subscriptions
            response = sns.list_topics()
            topics = response.get('Topics', [])

            subscribed_tags = []
            for topic in topics:
                topic_arn = topic['TopicArn']
                topic_name = topic_arn.split(':')[-1]

                if not topic_name.startswith('ecolens-tag-'):
                    continue

                # Extract tag name from topic name
                tag_name = topic_name.replace('ecolens-tag-', '').replace('-', '_')

                # Check subscriptions
                subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
                active_subs = [s for s in subs['Subscriptions']
                               if s['SubscriptionArn'] != 'PendingConfirmation']

                if active_subs:
                    subscribed_tags.append(tag_name)

            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'tags': subscribed_tags})
            }

        # Handle subscribe action
        if action == 'subscribe':
            if not tag:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'message': 'tag is required for subscribe'})
                }
            if not email:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'message': 'email is required for subscribe'})
                }

            topic_arn = get_or_create_topic(tag)

            sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )

            print(f"Subscribed {email} to tag: {tag}")

            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'message': f'Subscription request sent! Check {email} to confirm.',
                    'tag': tag,
                    'email': email
                })
            }

        # Handle unsubscribe action
        if action == 'unsubscribe':
            if not tag:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'message': 'tag is required for unsubscribe'})
                }
            if not email:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'message': 'email is required for unsubscribe'})
                }

            topic_arn = get_or_create_topic(tag)

            # Find and unsubscribe
            subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            unsubscribed = False

            for sub in subs['Subscriptions']:
                if sub['Endpoint'] == email and sub['SubscriptionArn'] != 'PendingConfirmation':
                    sns.unsubscribe(SubscriptionArn=sub['SubscriptionArn'])
                    unsubscribed = True
                    print(f"Unsubscribed {email} from tag: {tag}")
                    break

            if not unsubscribed:
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'message': f'No active subscription found for {email} on tag {tag}'})
                }

            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'message': f'Unsubscribed {email} from {tag}',
                    'tag': tag
                })
            }

        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': f'Unknown action: {action}. Use subscribe, unsubscribe, or list'})
        }

    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': str(e)})
        }
