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
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
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


def normalize_thumbnail_url(url):
    """Normalize URL by stripping query params (presigned URLs have expiry params)"""
    return url.split('?')[0]


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

        thumbnail_url = body.get('thumbnailUrl')

        if not thumbnail_url:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'thumbnailUrl is required'})
            }

        print(f"Searching for thumbnail URL: {thumbnail_url}")

        # Normalize the search URL (strip query params)
        normalized_search = normalize_thumbnail_url(thumbnail_url)

        # Scan DynamoDB for matching thumbnail_url
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        all_items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_items.extend(response.get('Items', []))

        # Find matching record
        matched_item = None
        for item in all_items:
            stored_thumbnail = item.get('thumbnail_url', '')
            if not stored_thumbnail:
                continue
            # Normalize stored URL and compare
            if normalize_thumbnail_url(stored_thumbnail) == normalized_search:
                matched_item = item
                break

        if not matched_item:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'No file found matching this thumbnail URL'})
            }

        file_url = matched_item.get('file_url', '')
        thumbnail_stored = matched_item.get('thumbnail_url', '')

        print(f"Found matching file: {matched_item.get('file_id')}")

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'fullImageUrl': generate_presigned_url(file_url) if file_url else '',
                'canonicalFullImageUrl': file_url,
                'mediaId': matched_item.get('file_id'),
                'originalName': matched_item.get('original_name', ''),
                'tags': {k: int(v) for k, v in matched_item.get('tags', {}).items()},
                'thumbnailUrl': generate_presigned_url(thumbnail_stored) if thumbnail_stored else '',
                'status': matched_item.get('status', ''),
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
