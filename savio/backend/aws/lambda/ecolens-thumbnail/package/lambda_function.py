import json
import boto3
import io
import os
import urllib.parse
from PIL import Image

s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')

BUCKET_NAME = 'ecolens-media-savio-melbourne'
TABLE_NAME = 'ecolens-media'
THUMBNAIL_SIZE = (300, 300)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


def generate_thumbnail(image_bytes, content_type):
    """Generate a thumbnail from image bytes"""
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if needed (handles PNG with transparency)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')

    # Resize maintaining aspect ratio then crop to square
    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    return output.getvalue()


def find_dynamodb_record(s3_key):
    """Find DynamoDB record by s3_key"""
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan(
        FilterExpression='s3_key = :key',
        ExpressionAttributeValues={':key': s3_key}
    )
    items = response.get('Items', [])
    return items[0] if items else None


def lambda_handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        # Handle S3 trigger event
        if 'Records' in event:
            for record in event['Records']:
                if record.get('eventSource') != 'aws:s3':
                    continue

                # Get the S3 key from the event
                s3_key = urllib.parse.unquote_plus(
                    record['s3']['object']['key']
                )

                # Only process files in uploads/ folder
                if not s3_key.startswith('uploads/'):
                    print(f"Skipping non-upload file: {s3_key}")
                    continue

                # Only process images
                lower_key = s3_key.lower()
                if not any(lower_key.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    print(f"Skipping non-image file: {s3_key}")
                    continue

                print(f"Generating thumbnail for: {s3_key}")

                # Download original image from S3
                response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                image_bytes = response['Body'].read()
                content_type = response.get('ContentType', 'image/jpeg')

                # Generate thumbnail
                thumbnail_bytes = generate_thumbnail(image_bytes, content_type)

                # Build thumbnail S3 key
                filename = os.path.basename(s3_key)
                thumbnail_key = f'thumbnails/{filename}'

                # Upload thumbnail to S3
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=thumbnail_key,
                    Body=thumbnail_bytes,
                    ContentType='image/jpeg'
                )

                thumbnail_url = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/{thumbnail_key}'
                print(f"Thumbnail uploaded: {thumbnail_url}")

                # Find and update DynamoDB record
                record_item = find_dynamodb_record(s3_key)
                if record_item:
                    table = dynamodb.Table(TABLE_NAME)
                    table.update_item(
                        Key={'file_id': record_item['file_id']},
                        UpdateExpression='SET thumbnail_url = :t',
                        ExpressionAttributeValues={':t': thumbnail_url}
                    )
                    print(f"DynamoDB updated with thumbnail_url for file_id: {record_item['file_id']}")
                else:
                    print(f"No DynamoDB record found for s3_key: {s3_key}")

            return {'statusCode': 200, 'body': json.dumps({'message': 'Thumbnails generated'})}

        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': 'Invalid event — expected S3 trigger'})
        }

    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
