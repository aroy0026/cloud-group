import json
import boto3
import hashlib
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')

BUCKET_NAME = 'ecolens-media-savio-melbourne'
TABLE_NAME = 'ecolens-media'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


def check_duplicate(checksum):
    """Check if a file with this checksum already exists"""
    table = dynamodb.Table(TABLE_NAME)
    response = table.query(
        IndexName='checksum-index',
        KeyConditionExpression=Key('checksum').eq(checksum)
    )
    items = response.get('Items', [])
    return items[0] if items else None


def lambda_handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'OK'})
            }

        # Parse body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        filename = body.get('filename')
        content_type = body.get('contentType', 'application/octet-stream')
        size = body.get('size', 0)
        checksum = body.get('sha256')

        if not filename or not checksum:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'filename and sha256 are required'})
            }

        # Check for duplicate
        existing = check_duplicate(checksum)
        if existing:
            print(f"Duplicate detected: {existing['file_id']}")
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'duplicate': True,
                    'existingMediaId': existing['file_id']
                })
            }

        # Generate file ID and S3 key
        file_id = str(uuid.uuid4())

        if content_type.startswith('video'):
            s3_key = f'uploads/videos/{file_id}_{filename}'
        else:
            s3_key = f'uploads/images/{file_id}_{filename}'

        # Create DynamoDB record with QUEUED status
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'file_id': file_id,
            'checksum': checksum,
            'file_type': 'video' if content_type.startswith('video') else 'image',
            'original_name': filename,
            'content_type': content_type,
            'size': size,
            's3_key': s3_key,
            'file_url': f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/{s3_key}',
            'thumbnail_url': '',
            'tags': {},
            'status': 'QUEUED',
            'uploaded_at': datetime.utcnow().isoformat()
        })

        # Generate presigned URL for direct S3 upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key,
                'ContentType': content_type
            },
            ExpiresIn=3600
        )

        print(f"Presigned URL generated for file_id: {file_id}")

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'duplicate': False,
                'mediaId': file_id,
                'uploadUrl': presigned_url,
                's3Key': s3_key
            })
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
