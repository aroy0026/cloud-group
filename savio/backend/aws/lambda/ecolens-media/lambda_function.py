import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')
s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)

TABLE_NAME = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)


def generate_presigned_url(s3_url, expiry=3600):
    """Generate a presigned URL for an S3 object"""
    try:
        key = s3_url.replace(
            f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/', ''
        )
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=expiry
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return s3_url


def normalize_item(item):
    """Normalize a DynamoDB item for frontend consumption"""
    file_url = item.get('file_url', '')
    thumbnail_url = item.get('thumbnail_url', '')

    return {
        'mediaId': item.get('file_id'),
        'originalName': item.get('original_name', ''),
        'contentType': item.get('content_type', ''),
        'fileKind': item.get('file_type', 'image'),
        'tags': {k: int(v) for k, v in item.get('tags', {}).items()},
        'fullUrl': generate_presigned_url(file_url) if file_url else '',
        'thumbnailUrl': generate_presigned_url(thumbnail_url) if thumbnail_url else '',
        'status': item.get('status', ''),
        'createdAt': item.get('uploaded_at', ''),
        'size': int(item.get('size', 0)),
    }


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

        # Scan all media from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        all_items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_items.extend(response.get('Items', []))

        # Sort by uploaded_at descending (newest first)
        all_items.sort(
            key=lambda x: x.get('uploaded_at', ''),
            reverse=True
        )

        # Normalize all items
        results = [normalize_item(item) for item in all_items]

        print(f"Returning {len(results)} media items")

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'results': results,
                'count': len(results)
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
