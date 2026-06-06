import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-4')

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


def normalize_s3_url(url):
    """Normalize S3 URL to virtual-hosted style without query params"""
    clean_url = url.split('?')[0]
    virtual_prefix = f'https://{BUCKET_NAME}.s3.ap-southeast-4.amazonaws.com/'
    path_prefix = f'https://s3.ap-southeast-4.amazonaws.com/{BUCKET_NAME}/'
    if clean_url.startswith(virtual_prefix):
        return clean_url
    if clean_url.startswith(path_prefix):
        key = clean_url[len(path_prefix):]
        return f'{virtual_prefix}{key}'
    return clean_url


def find_record_by_url(table, url):
    """Find a DynamoDB record by file_url or thumbnail_url"""
    normalized = normalize_s3_url(url)
    response = table.scan(
        FilterExpression='file_url = :url OR thumbnail_url = :url',
        ExpressionAttributeValues={':url': normalized}
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
        tags = body.get('tags', [])
        operation = int(body.get('operation', 1))  # 1 = add, 0 = remove

        if not urls:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'urls field is required'})
            }

        if not tags:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'tags field is required'})
            }

        print(f"Operation: {'add' if operation == 1 else 'remove'}, URLs: {len(urls)}, Tags: {tags}")

        table = dynamodb.Table(TABLE_NAME)
        updated = 0
        failed = []

        for url in urls:
            try:
                record = find_record_by_url(table, url)
                if not record:
                    print(f"No record found for URL: {url}")
                    failed.append({'url': url, 'reason': 'Record not found'})
                    continue

                file_id = record['file_id']
                current_tags = record.get('tags', {})

                if operation == 1:
                    # Add tags — increment count if exists, set to 1 if new
                    for tag in tags:
                        current_count = int(current_tags.get(tag, 0))
                        current_tags[tag] = current_count + 1
                else:
                    # Remove tags
                    for tag in tags:
                        if tag in current_tags:
                            del current_tags[tag]

                # Update DynamoDB
                table.update_item(
                    Key={'file_id': file_id},
                    UpdateExpression='SET tags = :t',
                    ExpressionAttributeValues={':t': current_tags}
                )
                updated += 1
                print(f"Updated tags for file_id: {file_id}")

            except Exception as e:
                print(f"Error processing URL {url}: {str(e)}")
                failed.append({'url': url, 'reason': str(e)})

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': f"{'Added' if operation == 1 else 'Removed'} tags for {updated} file(s)",
                'updated': updated,
                'failed': failed
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
