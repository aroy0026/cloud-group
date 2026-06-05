import json
import os
import tempfile
from urllib.parse import unquote_plus

import boto3

from common.gcp import firestore_client, publisher_client, server_timestamp, storage_client

s3 = boto3.client("s3")


def handler(event, context):
    db = firestore_client()
    gcs = storage_client()
    publisher = publisher_client()
    gcp_bucket = os.environ["GCP_BUCKET"]
    topic = os.environ["PUBSUB_TOPIC"]

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        head = s3.head_object(Bucket=bucket, Key=key)
        meta = head.get("Metadata", {})
        media_id = meta["media-id"]
        owner_id = meta["owner-id"]
        owner_email = meta.get("owner-email", "")
        sha256 = meta["sha256"].lower()
        content_type = head.get("ContentType", "")

        media_ref = db.collection("media").document(media_id)
        checksum_ref = db.collection("checksums").document(sha256)

        checksum_doc = checksum_ref.get()
        checksum_data = checksum_doc.to_dict() if checksum_doc.exists else {}
        if checksum_doc.exists and checksum_data.get("mediaId") != media_id:
            s3.delete_object(Bucket=bucket, Key=key)
            media_ref.update(
                {
                    "status": "DUPLICATE_REMOVED",
                    "error": "Duplicate checksum detected after upload.",
                    "updatedAt": server_timestamp(),
                }
            )
            continue

        original_name = meta.get("original-name", key.rsplit("/", 1)[-1])
        gcs_key = f"originals/{owner_id}/{media_id}/{original_name}"

        with tempfile.NamedTemporaryFile() as tmp:
            s3.download_fileobj(bucket, key, tmp)
            tmp.flush()
            gcs.bucket(gcp_bucket).blob(gcs_key).upload_from_filename(
                tmp.name, content_type=content_type
            )

        s3_url = f"s3://{bucket}/{key}"
        gcs_uri = f"gs://{gcp_bucket}/{gcs_key}"
        checksum_ref.set(
            {
                "mediaId": media_id,
                "ownerId": owner_id,
                "status": "ACTIVE",
                "s3Url": s3_url,
                "gcsUri": gcs_uri,
                "updatedAt": server_timestamp(),
            },
            merge=True,
        )
        media_ref.update(
            {
                "status": "QUEUED",
                "s3Url": s3_url,
                "gcsUri": gcs_uri,
                "contentType": content_type,
                "updatedAt": server_timestamp(),
            }
        )

        job = {
            "mediaId": media_id,
            "ownerId": owner_id,
            "ownerEmail": owner_email,
            "sha256": sha256,
            "s3Url": s3_url,
            "gcsUri": gcs_uri,
            "contentType": content_type,
            "originalName": original_name,
        }
        publisher.publish(topic, json.dumps(job).encode("utf-8")).result()

    return {"ok": True}
