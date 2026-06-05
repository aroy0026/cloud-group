import os
import tempfile
from pathlib import Path

from common.core import (
    checksum_table,
    detect_tags_with_processor,
    infer_tags_from_name,
    media_table,
    now_iso,
    response,
    s3,
    s3_key_from_event,
    s3_sha256,
    s3_url,
    sns,
)


def handler(event, context):
    processed = []
    for record in event.get("Records", []):
        bucket, key = s3_key_from_event(record)
        if key.startswith(("thumbnails/", "frames/")):
            continue
        checksum = s3_sha256(bucket, key)
        owner_id, media_id, name = parse_upload_key(key)
        existing = media_table().get_item(Key={"ownerId": owner_id, "id": media_id}).get("Item") or {}
        tags = infer_tags_from_name(name)
        media_type = "video" if name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")) else "image"
        thumbnail = existing.get("thumbnail") or ""
        frame_prefix = existing.get("framePrefix") or ""
        frame_s3_uris = existing.get("frameS3Uris") or []
        frame_count = int(existing.get("frameCount") or 0)
        if media_type == "image":
            thumbnail_key = thumbnail_key_for(key, name)
            source_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
            tags = detect_tags_with_processor(source_bytes, existing.get("mimeType") or content_type_for(name)) or tags
            create_image_thumbnail(bucket, key, thumbnail_key, source_bytes)
            thumbnail = s3_url(bucket, thumbnail_key)
        else:
            video_result = process_video(bucket, key, owner_id, media_id, name)
            thumbnail = video_result["thumbnail"]
            frame_prefix = video_result["framePrefix"]
            frame_s3_uris = video_result["frameS3Uris"]
            frame_count = video_result["frameCount"]
            tags = video_result.get("tags") or tags
        item = {
            "ownerId": owner_id,
            "id": media_id,
            "name": name,
            "type": media_type,
            "mimeType": existing.get("mimeType") or content_type_for(name),
            "size": existing.get("size"),
            "checksum": checksum,
            "bucket": bucket,
            "key": key,
            "fullUrl": s3_url(bucket, key),
            "thumbnail": thumbnail,
            "framePrefix": frame_prefix,
            "frameS3Uris": frame_s3_uris,
            "frameCount": frame_count,
            "tags": tags,
            "status": "READY",
            "createdAt": existing.get("createdAt") or now_iso(),
            "updatedAt": now_iso(),
        }
        media_table().put_item(Item=item)
        if checksum:
            checksum_table().put_item(
                Item={"checksum": checksum, "ownerId": owner_id, "mediaId": media_id, "status": "ACTIVE"},
            )
        publish_tag_notifications(item)
        processed.append({"ownerId": owner_id, "mediaId": media_id})
    return response(200, {"processed": processed})


def parse_upload_key(key):
    parts = key.split("/", 3)
    if len(parts) < 4 or parts[0] != "uploads":
        raise ValueError(f"Unexpected upload key: {key}")
    return parts[1], parts[2], parts[3].rsplit("/", 1)[-1]


def thumbnail_key_for(source_key, name):
    source = Path(source_key)
    stem = Path(name).stem or source.stem or "thumbnail"
    parts = source_key.split("/", 3)
    return f"thumbnails/{parts[1]}/{parts[2]}/{stem}.jpg"


def frame_prefix_for(owner_id, media_id):
    return f"frames/{owner_id}/{media_id}"


def create_image_thumbnail(bucket, source_key, thumbnail_key, source_bytes=None):
    if source_bytes is None:
        source = s3.get_object(Bucket=bucket, Key=source_key)
        source_bytes = source["Body"].read()
    thumbnail_bytes = resize_with_opencv(source_bytes)
    s3.put_object(
        Bucket=bucket,
        Key=thumbnail_key,
        Body=thumbnail_bytes,
        ContentType="image/jpeg",
        Metadata={"generated-by": "ecolens-media-processor", "source-key": source_key},
    )


def process_video(bucket, source_key, owner_id, media_id, name):
    frame_prefix = frame_prefix_for(owner_id, media_id)
    thumbnail_key = thumbnail_key_for(source_key, name)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        input_path = os.path.join(tmpdir, safe_local_name(name))
        s3.download_file(bucket, source_key, input_path)

        frame_bytes = extract_video_frames(input_path)
        if not frame_bytes:
            raise RuntimeError("Video frame extraction produced no frames")

        thumbnail_bytes = resize_with_opencv(frame_bytes[0])
        s3.put_object(
            Bucket=bucket,
            Key=thumbnail_key,
            Body=thumbnail_bytes,
            ContentType="image/jpeg",
            Metadata={"generated-by": "ecolens-media-processor", "source-key": source_key, "source-frame": "frame_000001.jpg"},
        )
        thumbnail = s3_url(bucket, thumbnail_key)
        save_video_thumbnail_preview(owner_id, media_id, thumbnail, s3_url(bucket, frame_prefix), len(frame_bytes))

        frame_s3_uris = []
        tags = {}
        for index, frame in enumerate(frame_bytes, start=1):
            frame_key = f"{frame_prefix}/frame_{index:06d}.jpg"
            s3.put_object(
                Bucket=bucket,
                Key=frame_key,
                Body=frame,
                ContentType="image/jpeg",
                Metadata={"generated-by": "ecolens-media-processor", "source-key": source_key},
            )
            frame_s3_uris.append(s3_url(bucket, frame_key))
            for tag, count in detect_tags_with_processor(frame, "image/jpeg").items():
                tags[tag] = max(tags.get(tag, 0), int(count))

    return {
        "thumbnail": thumbnail,
        "framePrefix": s3_url(bucket, frame_prefix),
        "frameS3Uris": frame_s3_uris,
        "frameCount": len(frame_s3_uris),
        "tags": tags,
    }


def save_video_thumbnail_preview(owner_id, media_id, thumbnail, frame_prefix, frame_count):
    media_table().update_item(
        Key={"ownerId": owner_id, "id": media_id},
        UpdateExpression=(
            "SET thumbnail = :thumbnail, framePrefix = :framePrefix, frameCount = :frameCount, "
            "#status = :status, updatedAt = :updatedAt"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":thumbnail": thumbnail,
            ":framePrefix": frame_prefix,
            ":frameCount": frame_count,
            ":status": "PROCESSING",
            ":updatedAt": now_iso(),
        },
    )


def resize_with_opencv(source_bytes):
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError("OpenCV is required for media processing. Package opencv-python-headless with media_processor.") from exc

    max_dimension = int(os.environ.get("THUMBNAIL_MAX_DIMENSION", "480"))
    quality = int(os.environ.get("THUMBNAIL_QUALITY", "78"))
    image = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("OpenCV could not decode image bytes")

    height, width = image.shape[:2]
    scale = min(max_dimension / max(width, height), 1.0)
    if scale < 1.0:
        image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

    ok, encoded = cv2.imencode(
        ".jpg",
        image,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality, int(cv2.IMWRITE_JPEG_OPTIMIZE), 1],
    )
    if not ok:
        raise RuntimeError("OpenCV could not encode thumbnail")
    return encoded.tobytes()


def extract_video_frames(video_path):
    try:
        import cv2
    except ModuleNotFoundError as exc:
        raise RuntimeError("OpenCV is required for video frame extraction. Package opencv-python-headless with media_processor.") from exc

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError("OpenCV could not open uploaded video")

    fps = capture.get(cv2.CAP_PROP_FPS) or 1
    frame_interval = max(1, round(fps))
    max_frames = int(os.environ.get("VIDEO_MAX_FRAMES", "0"))
    quality = int(os.environ.get("VIDEO_FRAME_JPEG_QUALITY", "82"))
    frames = []
    frame_number = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_number % frame_interval == 0:
                ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                if ok:
                    frames.append(encoded.tobytes())
                if max_frames > 0 and len(frames) >= max_frames:
                    break
            frame_number += 1
    finally:
        capture.release()
    return frames


def content_type_for(name):
    lowered = name.lower()
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith(".mp4"):
        return "video/mp4"
    if lowered.endswith(".mov"):
        return "video/quicktime"
    return "application/octet-stream"


def safe_local_name(name):
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name) or "video.bin"


def publish_tag_notifications(item):
    prefix = os.environ.get("SNS_TOPIC_PREFIX")
    if not prefix:
        return

    tags = item.get("tags") or {}
    if not tags:
        return

    for tag, count in tags.items():
        topic_arn = topic_for_tag(prefix, tag)
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Aussie EcoLens: new {tag} media",
            Message=(
                f"New wildlife media matched your watched tag: {tag}\n\n"
                f"File: {item.get('name')}\n"
                f"Type: {item.get('type')}\n"
                f"Tag count: {count}\n"
                f"Full media: {item.get('fullUrl')}\n"
                f"Thumbnail: {item.get('thumbnail') or 'N/A'}\n"
            ),
        )


def topic_for_tag(prefix, tag):
    if prefix.startswith("arn:"):
        return f"{prefix}{tag}"
    return sns.create_topic(Name=f"{prefix}{tag}")["TopicArn"]
