import json
import boto3
from decimal import Decimal

s3 = boto3.client(
    's3',
    region_name='ap-southeast-4',
    endpoint_url='https://s3.ap-southeast-4.amazonaws.com'
)
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')

TABLE_NAME = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


def url_to_s3_key(url):
    """Extract S3 key from a full S3 URL"""
    clean_url = url.split('?')[0]
    prefix = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/'
    if clean_url.startswith(prefix):
        return clean_url[len(prefix):]
    return None


def find_record_by_url(table, url):
    """Find a DynamoDB record by file_url"""
    clean_url = url.split('?')[0]
    response = table.scan(
        FilterExpression='file_url = :url',
        ExpressionAttributeValues={':url': clean_url}
    )
    items = response.get('Items', [])
    return items[0] if items else None


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

        urls = body.get('urls', [])

        if not urls:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'urls field is required'})
            }

        print(f"Deleting {len(urls)} file(s)")

        table = dynamodb.Table(TABLE_NAME)
        deleted = 0
        failed = []

        for url in urls:
            try:
                # Find DynamoDB record
                record = find_record_by_url(table, url)
                if not record:
                    print(f"No record found for URL: {url}")
                    failed.append({'url': url, 'reason': 'Record not found'})
                    continue

                file_id = record['file_id']
                file_url = record.get('file_url', '')
                thumbnail_url = record.get('thumbnail_url', '')

                # Delete original file from S3
                if file_url:
                    s3_key = url_to_s3_key(file_url)
                    if s3_key:
                        try:
                            s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
                            print(f"Deleted S3 file: {s3_key}")
                        except Exception as e:
                            print(f"Failed to delete S3 file {s3_key}: {str(e)}")

                # Delete thumbnail from S3
                if thumbnail_url:
                    thumb_key = url_to_s3_key(thumbnail_url)
                    if thumb_key:
                        try:
                            s3.delete_object(Bucket=BUCKET_NAME, Key=thumb_key)
                            print(f"Deleted thumbnail: {thumb_key}")
                        except Exception as e:
                            print(f"Failed to delete thumbnail {thumb_key}: {str(e)}")

                # Delete DynamoDB record
                table.delete_item(Key={'file_id': file_id})
                print(f"Deleted DynamoDB record: {file_id}")

                deleted += 1

            except Exception as e:
                print(f"Error deleting URL {url}: {str(e)}")
                failed.append({'url': url, 'reason': str(e)})

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': f"Deleted {deleted} file(s)",
                'deleted': deleted,
                'failed': failed
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
