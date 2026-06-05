import os
import subprocess
import tempfile
from pathlib import Path

from google.cloud import firestore, storage
from PIL import Image

from model_adapter import detect_tags_for_image
from notifier import publish_tag_notifications

db = firestore.Client()
gcs = storage.Client()

GCS_BUCKET = os.environ["GCS_BUCKET"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def process_media(job):
    media_id = job["mediaId"]
    media_ref = db.collection("media").document(media_id)
    media_ref.update({"status": "PROCESSING", "updatedAt": firestore.SERVER_TIMESTAMP})

    try:
        local_path = download_gcs(job["gcsUri"])
        content_type = job.get("contentType", "")
        suffix = local_path.suffix.lower()

        if content_type in IMAGE_TYPES or suffix in IMAGE_EXTS:
            file_kind = "image"
            thumbnail_url = create_thumbnail(local_path, job)
            tags = detect_tags_for_image(local_path)
        elif suffix in VIDEO_EXTS or content_type.startswith("video/"):
            file_kind = "video"
            thumbnail_url = None
            tags = detect_video_tags(local_path)
        else:
            file_kind = "unknown"
            thumbnail_url = None
            tags = {}

        sorted_urls = create_classified_copies(job, tags)
        primary_tag = choose_primary_tag(tags)
        full_url = sorted_urls.get(primary_tag) or job["gcsUri"]
        update = {
            "status": "READY",
            "fileKind": file_kind,
            "primaryTag": primary_tag,
            "thumbnailUrl": thumbnail_url,
            "fullUrl": full_url,
            "sortedUrls": sorted_urls,
            "sortedUrlList": sorted(sorted_urls.values()),
            "tags": tags,
            "tagList": sorted(tags.keys()),
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        media_ref.update(update)

        if thumbnail_url:
            db.collection("thumbnailIndex").document(safe_id(thumbnail_url)).set(
                {
                    "mediaId": media_id,
                    "thumbnailUrl": thumbnail_url,
                    "fullImageUrl": full_url,
                }
            )

        publish_tag_notifications(tags, media_id, full_url)
    except Exception as exc:
        media_ref.update(
            {
                "status": "FAILED",
                "error": str(exc),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        raise


def detect_query_file(raw_bytes):
    suffix = ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw_bytes)
        tmp.flush()
        return detect_tags_for_image(Path(tmp.name))


def download_gcs(gcs_uri):
    bucket_name, blob_name = parse_gcs_uri(gcs_uri)
    suffix = Path(blob_name).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    gcs.bucket(bucket_name).blob(blob_name).download_to_filename(tmp.name)
    return Path(tmp.name)


def create_thumbnail(path, job):
    image = Image.open(path).convert("RGB")
    image.thumbnail((420, 420), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as out:
        image.save(out.name, "JPEG", quality=78, optimize=True)
        blob_name = f"thumbnails/{job['ownerId']}/{job['mediaId']}.jpg"
        gcs.bucket(GCS_BUCKET).blob(blob_name).upload_from_filename(
            out.name, content_type="image/jpeg"
        )
    return f"gs://{GCS_BUCKET}/{blob_name}"


def create_classified_copies(job, tags):
    """Copy the processed object into one species prefix per detected tag."""
    if not tags:
        return {}

    source_bucket_name, source_blob_name = parse_gcs_uri(job["gcsUri"])
    source_bucket = gcs.bucket(source_bucket_name)
    source_blob = source_bucket.blob(source_blob_name)
    original_name = safe_filename(job.get("originalName") or source_blob_name.rsplit("/", 1)[-1])
    destination_bucket = gcs.bucket(GCS_BUCKET)

    sorted_urls = {}
    for tag in sorted(tags.keys()):
        safe_tag = safe_path_part(tag)
        destination_blob_name = (
            f"classified/{safe_tag}/{job['ownerId']}/{job['mediaId']}/{original_name}"
        )
        source_bucket.copy_blob(source_blob, destination_bucket, destination_blob_name)
        sorted_urls[tag] = f"gs://{GCS_BUCKET}/{destination_blob_name}"
    return sorted_urls


def choose_primary_tag(tags):
    if not tags:
        return None
    return max(tags.items(), key=lambda item: (int(item[1]), item[0]))[0]


def detect_video_tags(path):
    frames = extract_video_frames(path)
    totals = {}
    for frame in frames:
        tags = detect_tags_for_image(frame)
        for tag, count in tags.items():
            totals[tag] = totals.get(tag, 0) + int(count)
    return totals


def extract_video_frames(path):
    out_dir = Path(tempfile.mkdtemp())
    pattern = str(out_dir / "frame_%05d.jpg")
    subprocess.run(["ffmpeg", "-i", str(path), "-vf", "fps=1", pattern], check=True)
    return sorted(out_dir.glob("frame_*.jpg"))


def parse_gcs_uri(uri):
    if not uri.startswith("gs://"):
        raise ValueError(f"Expected gs:// URI, got {uri}")
    rest = uri[len("gs://") :]
    bucket, _, blob = rest.partition("/")
    return bucket, blob


def safe_id(value):
    return value.replace("/", "_").replace(":", "_")


def safe_path_part(value):
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in value.lower())


def safe_filename(value):
    cleaned = value.replace("/", "_").replace("\\", "_").strip()
    return cleaned or "media.bin"
