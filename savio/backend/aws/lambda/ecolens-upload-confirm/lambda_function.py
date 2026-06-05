import json
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')
lambda_client = boto3.client('lambda', region_name='ap-southeast-4')

TABLE_NAME = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)


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

        file_id = body.get('mediaId')
        s3_key = body.get('s3Key')

        if not file_id or not s3_key:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'mediaId and s3Key are required'})
            }

        # Update DynamoDB status to processing
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'file_id': file_id},
            UpdateExpression='SET #s = :s, uploaded_at = :t',
            ExpressionAttributeValues={
                ':s': 'processing',
                ':t': datetime.utcnow().isoformat()
            },
            ExpressionAttributeNames={'#s': 'status'}
        )
        print(f"Status set to processing for file_id: {file_id}")

        file_url = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/{s3_key}'

        # Invoke ml-trigger Lambda ASYNCHRONOUSLY (fire and forget)
        lambda_client.invoke(
            FunctionName='ecolens-ml-trigger',
            InvocationType='Event',  # async — does not wait for result
            Payload=json.dumps({
                'file_id': file_id,
                's3_key': s3_key,
                'file_url': file_url
            })
        )
        print(f"ML trigger invoked async for file_id: {file_id}")

        # Return immediately — frontend polls for status
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'mediaId': file_id,
                'status': 'processing',
                'fileUrl': file_url
            }, cls=DecimalEncoder)
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
