import json
import boto3
import uuid
import urllib.request
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')
s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)

TABLE_NAME = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'
GCP_ML_URL = 'https://ecolens-ml-service-810236742778.australia-southeast2.run.app/tag'

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
    """Generate a presigned URL handling both path-style and virtual-hosted S3 URLs"""
    try:
        # Strip query params first
        clean_url = s3_url.split('?')[0]
        
        virtual_prefix = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/'
        path_prefix = f'https://s3.ap-southeast-4.amazonaws.com/{BUCKET_NAME}/'
        
        if clean_url.startswith(virtual_prefix):
            key = clean_url[len(virtual_prefix):]
        elif clean_url.startswith(path_prefix):
            key = clean_url[len(path_prefix):]
        else:
            print(f"Unknown URL format: {clean_url}")
            return s3_url

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


def run_ml_on_temp_file(s3_key):
    try:
        temp_file_id = f'DO-NOT-SAVE-{str(uuid.uuid4())}'
        payload = json.dumps({
            'file_id': temp_file_id,
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
            return result.get('tags', {})

    except Exception as e:
        print(f"ML error: {str(e)}")
        return {}


def search_by_tags(tags):
    if not tags:
        return []

    normalized_search = {k.lower(): int(v) for k, v in tags.items()}

    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    all_items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        all_items.extend(response.get('Items', []))

    matching_items = []
    for item in all_items:
        item_tags = item.get('tags', {})
        if not item_tags:
            continue
        normalized_item_tags = {k.lower(): int(v) for k, v in item_tags.items()}
        for species in normalized_search.keys():
            if species in normalized_item_tags:
                matching_items.append(normalize_item(item))
                break

    return matching_items


def lambda_handler(event, context):
    try:
        print("EVENT keys:", list(event.keys()))

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

        s3_key = body.get('s3Key')

        if not s3_key:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 's3Key is required'})
            }

        print(f"Running ML on: {s3_key}")

        # Run ML tagging
        detected_tags = run_ml_on_temp_file(s3_key)
        print(f"Detected tags: {detected_tags}")

        # Search DynamoDB
        matching_items = search_by_tags(detected_tags)
        print(f"Found {len(matching_items)} matching files")

        # Clean up temp file
        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            print(f"Temp file deleted: {s3_key}")
        except Exception as e:
            print(f"Failed to delete temp file: {str(e)}")

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'detectedTags': detected_tags,
                'results': matching_items,
                'count': len(matching_items)
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
