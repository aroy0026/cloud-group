import json
import boto3
import urllib.request
import base64

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')
sns = boto3.client('sns', region_name='ap-southeast-4')
s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)

TABLE_NAME = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'
GCP_ML_URL = 'https://ecolens-ml-service-810236742778.australia-southeast2.run.app/tag'


def trigger_ml_tagging(file_id, s3_key):
    """Call GCP ML service and wait for result"""
    print(f"Calling GCP ML for file_id: {file_id}, s3_key: {s3_key}")
    payload = json.dumps({
        'file_id': file_id,
        's3_key': s3_key
    }).encode('utf-8')

    req = urllib.request.Request(
        GCP_ML_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=540) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"ML result: {result}")
        return result


def upload_thumbnail_from_base64(file_id, thumbnail_base64, content_type='image/jpeg'):
    """Upload base64 thumbnail to S3 and return URL"""
    try:
        thumbnail_bytes = base64.b64decode(thumbnail_base64)
        thumbnail_key = f'thumbnails/{file_id}_thumbnail.jpg'

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=thumbnail_key,
            Body=thumbnail_bytes,
            ContentType=content_type
        )

        thumbnail_url = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/{thumbnail_key}'
        print(f"Thumbnail uploaded: {thumbnail_url}")
        return thumbnail_url

    except Exception as e:
        print(f"Thumbnail upload error: {str(e)}")
        return None


def send_sns_notifications(tags, file_url, file_id):
    """Send SNS notifications for each detected species"""
    try:
        for tag in tags.keys():
            topic_name = 'ecolens-tag-' + tag.replace('_', '-').lower()
            try:
                response = sns.create_topic(Name=topic_name)
                topic_arn = response['TopicArn']

                subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
                active_subs = [s for s in subs['Subscriptions']
                               if s['SubscriptionArn'] != 'PendingConfirmation']

                if active_subs:
                    sns.publish(
                        TopicArn=topic_arn,
                        Subject=f'EcoLens Alert: {tag} detected!',
                        Message=f'A new file has been uploaded containing {tag}.\n\nFile ID: {file_id}\nFile URL: {file_url}\n\nLogin to EcoLens to view the file.'
                    )
                    print(f"SNS notification sent for tag: {tag}")

            except Exception as e:
                print(f"SNS error for tag {tag}: {str(e)}")

    except Exception as e:
        print(f"SNS notification error: {str(e)}")


def lambda_handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        file_id = event.get('file_id')
        s3_key = event.get('s3_key')
        file_url = event.get('file_url')

        if not file_id or not s3_key:
            print("ERROR: file_id and s3_key are required")
            return

        table = dynamodb.Table(TABLE_NAME)

        # Call GCP ML service (may take several minutes for videos)
        try:
            ml_result = trigger_ml_tagging(file_id, s3_key)
        except Exception as e:
            print(f"ML tagging failed: {str(e)}")
            # Update status to failed
            table.update_item(
                Key={'file_id': file_id},
                UpdateExpression='SET #s = :s',
                ExpressionAttributeValues={':s': 'failed'},
                ExpressionAttributeNames={'#s': 'status'}
            )
            return

        tags = ml_result.get('tags', {})
        thumbnail_url = None

        # Handle video thumbnail
        if ml_result.get('thumbnail_base64'):
            print("Video thumbnail received — uploading to S3")
            thumbnail_url = upload_thumbnail_from_base64(
                file_id,
                ml_result['thumbnail_base64'],
                ml_result.get('thumbnail_content_type', 'image/jpeg')
            )

        # Update DynamoDB with tags + thumbnail
        update_expr = 'SET tags = :t, #s = :s'
        expr_values = {':t': tags, ':s': 'ready'}

        if thumbnail_url:
            update_expr += ', thumbnail_url = :thumb'
            expr_values[':thumb'] = thumbnail_url

        table.update_item(
            Key={'file_id': file_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames={'#s': 'status'}
        )
        print(f"DynamoDB updated for file_id: {file_id}, tags: {tags}")

        # Send SNS notifications
        if tags and file_url:
            send_sns_notifications(tags, file_url, file_id)

        print(f"ML trigger complete for file_id: {file_id}")

    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
