import os

import boto3
from google.cloud import firestore

db = firestore.Client()


def publish_tag_notifications(tags, media_id, media_url):
    if not tags:
        return
    tag_names = set(tags.keys())
    watches = db.collection("userWatches").where("active", "==", True).stream()
    matching = [w.to_dict() for w in watches if w.to_dict().get("tag") in tag_names]
    if not matching:
        return

    # Option A: publish directly to SNS from Cloud Run using AWS credentials in Secret Manager/env.
    # Option B: call an AWS notification Lambda. Direct SNS is implemented here.
    sns = boto3.client("sns", region_name=os.environ.get("AWS_SNS_REGION", "ap-southeast-2"))
    for watch in matching:
        sns.publish(
            TopicArn=watch["snsTopicArn"],
            Subject=f"Aussie EcoLens: new {watch['tag']} media",
            Message=(
                f"A new media file contains watched tag '{watch['tag']}'.\n"
                f"Media ID: {media_id}\n"
                f"URL: {media_url}\n"
                f"Detected tags: {tags}"
            ),
        )

