from urllib.parse import unquote, urlparse

import boto3

from .gcp import storage_client


def parse_s3_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "s3":
        raise ValueError(f"Not an s3 URL: {url}")
    return parsed.netloc, parsed.path.lstrip("/")


def parse_gs_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "gs":
        raise ValueError(f"Not a gs URL: {url}")
    return parsed.netloc, parsed.path.lstrip("/")


def delete_s3_url(url):
    if not url:
        return
    bucket, key = parse_s3_url(url)
    boto3.client("s3").delete_object(Bucket=bucket, Key=key)


def delete_gs_url(url):
    if not url:
        return
    bucket, key = parse_gs_url(url)
    storage_client().bucket(bucket).blob(key).delete()


def signed_gs_url(gs_url, minutes=30):
    import datetime

    bucket_name, key = parse_gs_url(gs_url)
    blob = storage_client().bucket(bucket_name).blob(key)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=minutes),
        method="GET",
    )


def url_lookup_candidates(url):
    """Return stored URL variants for user-supplied gs://, s3://, or signed HTTPS URLs."""
    if not url:
        return []

    candidates = [url]
    parsed = urlparse(url)
    host = parsed.netloc
    path = unquote(parsed.path.lstrip("/"))

    if parsed.scheme == "https" and host == "storage.googleapis.com" and "/" in path:
        bucket, key = path.split("/", 1)
        candidates.append(f"gs://{bucket}/{key}")
    elif parsed.scheme == "https" and host.endswith(".storage.googleapis.com") and path:
        bucket = host[: -len(".storage.googleapis.com")]
        candidates.append(f"gs://{bucket}/{path}")
    elif parsed.scheme == "https" and ".s3." in host and path:
        bucket = host.split(".s3.", 1)[0]
        candidates.append(f"s3://{bucket}/{path}")

    return list(dict.fromkeys(candidates))


def find_media_by_url(db, url, limit=10):
    fields = ["fullUrl", "thumbnailUrl", "gcsUri", "s3Url"]
    for candidate in url_lookup_candidates(url):
        for field in fields:
            docs = list(db.collection("media").where(field, "==", candidate).limit(limit).stream())
            if docs:
                return docs
        docs = list(db.collection("media").where("sortedUrlList", "array_contains", candidate).limit(limit).stream())
        if docs:
            return docs
    return []
