import base64
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import urllib.request

try:
    import boto3
    from boto3.dynamodb.conditions import Key
except ModuleNotFoundError:
    boto3 = None
    Key = None

dynamodb = None
s3 = None
sns = None
secretsmanager = None


class LazyAwsClient:
    def __init__(self, factory, service):
        self.factory = factory
        self.service = service
        self.instance = None

    def __getattr__(self, name):
        if boto3 is None:
            raise RuntimeError("boto3 is required for AWS Lambda runtime operations")
        if self.instance is None:
            self.instance = getattr(boto3, self.factory)(self.service)
        return getattr(self.instance, name)


dynamodb = LazyAwsClient("resource", "dynamodb")
s3 = LazyAwsClient("client", "s3")
sns = LazyAwsClient("client", "sns")
secretsmanager = LazyAwsClient("client", "secretsmanager")

DEFAULT_LABELS_PATH = Path(__file__).with_name("labels.txt")
COMMON_SPECIES_WORDS = {
    "antechinus",
    "bandicoot",
    "boar",
    "brushturkey",
    "cassowary",
    "cat",
    "cattle",
    "chough",
    "chowchilla",
    "currawong",
    "deer",
    "dingo",
    "dove",
    "echidna",
    "fowl",
    "fox",
    "goat",
    "hare",
    "human",
    "kangaroo",
    "kookaburra",
    "lyrebird",
    "magpie",
    "monitor",
    "mouse",
    "pademelon",
    "pitta",
    "possum",
    "rabbit",
    "rat",
    "robin",
    "shrikethrush",
    "wallaby",
    "wombat",
}


class BadRequest(Exception):
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps({} if body is None else body, default=to_json),
    }


def handle_options(event):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    return response(204, {}) if method == "OPTIONS" else None


def parse_body(event):
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BadRequest("Request body must be valid JSON") from exc


def raw_body_bytes(event):
    raw = event.get("body") or ""
    return base64.b64decode(raw) if event.get("isBase64Encoded") else raw.encode("utf-8")


def header_value(event, name, default=""):
    headers = event.get("headers") or {}
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return default


def claims(event):
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    return authorizer.get("jwt", {}).get("claims") or authorizer.get("claims") or {}


def current_user(event):
    data = claims(event)
    sub = data.get("sub")
    if not sub:
        raise PermissionError("Missing Cognito authorizer claims")
    return {
        "id": sub,
        "email": data.get("email", ""),
        "firstName": data.get("given_name", ""),
        "lastName": data.get("family_name", ""),
    }


def table(name):
    table_name = os.environ.get(name)
    if not table_name:
        raise RuntimeError(f"Missing environment variable {name}")
    return dynamodb.Table(table_name)


def media_table():
    return table("MEDIA_TABLE")


def checksum_table():
    return table("CHECKSUM_TABLE")


def subscriptions_table():
    return table("SUBSCRIPTIONS_TABLE")


def settings_table():
    return table("SETTINGS_TABLE")


def list_owner_media(owner_id):
    items = media_table().query(KeyConditionExpression=Key("ownerId").eq(owner_id)).get("Items", [])
    visible = [item for item in items if item.get("status") != "RESERVED"]
    return sorted([normalize_media(item) for item in visible], key=lambda item: item.get("createdAt", ""), reverse=True)


def get_media(owner_id, media_id):
    item = media_table().get_item(Key={"ownerId": owner_id, "id": media_id}).get("Item")
    return normalize_media(item) if item else None


def put_media(item):
    media_table().put_item(Item=item)
    return normalize_media(item)


def delete_media(owner_id, media_id):
    media_table().delete_item(Key={"ownerId": owner_id, "id": media_id})


def s3_sha256(bucket, key):
    digest = hashlib.sha256()
    body = s3.get_object(Bucket=bucket, Key=key)["Body"]
    for chunk in body.iter_chunks(chunk_size=1024 * 1024):
        if chunk:
            digest.update(chunk)
    return digest.hexdigest()


def detect_tags_with_processor(payload, content_type="application/octet-stream"):
    processor_url = os.environ.get("QUERY_FILE_PROCESSOR_URL")
    if not processor_url:
        return {}

    headers = {"Content-Type": content_type or "application/octet-stream"}
    token = cloud_run_identity_token(processor_url)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(processor_url, data=payload, headers=headers, method="POST")
    timeout = int(os.environ.get("QUERY_FILE_PROCESSOR_TIMEOUT", "90"))
    with urllib.request.urlopen(request, timeout=timeout) as result:
        payload = json.loads(result.read().decode("utf-8"))
    tags = payload.get("tags") or payload.get("detectedTags") or {}
    return {normalize_tag(name): int(count) for name, count in tags.items() if normalize_tag(name)}


_identity_token_cache = {}


def cloud_run_identity_token(audience):
    target_audience = os.environ.get("CLOUD_RUN_AUDIENCE") or audience.rsplit("/", 1)[0]
    cache_key = target_audience
    cached = _identity_token_cache.get(cache_key)
    if cached and cached["expires_at"] > time.time() + 60:
        return cached["token"]

    token = cloud_run_identity_token_from_wif(target_audience) or cloud_run_identity_token_from_service_account_key(target_audience)
    if token:
        _identity_token_cache[cache_key] = {"token": token, "expires_at": time.time() + 3000}
    return token


def cloud_run_identity_token_from_wif(target_audience):
    secret_id = os.environ.get("GCP_WIF_CREDENTIAL_CONFIG_SECRET")
    service_account_email = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL")
    if not secret_id:
        return ""
    if not service_account_email:
        raise RuntimeError("GCP_SERVICE_ACCOUNT_EMAIL is required when GCP_WIF_CREDENTIAL_CONFIG_SECRET is configured")

    try:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession, Request
    except ModuleNotFoundError as exc:
        raise RuntimeError("google-auth and requests are required when GCP_WIF_CREDENTIAL_CONFIG_SECRET is configured") from exc

    credential_config = read_secret_json(secret_id)
    credentials, _ = google.auth.load_credentials_from_dict(
        credential_config,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    session = AuthorizedSession(credentials)
    encoded_email = quote(service_account_email, safe="")
    result = session.post(
        f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{encoded_email}:generateIdToken",
        json={"audience": target_audience, "includeEmail": True},
        timeout=15,
    )
    if result.status_code >= 400:
        raise RuntimeError(f"Could not generate Cloud Run ID token: {result.status_code} {result.text[:500]}")
    return result.json().get("token", "")


def cloud_run_identity_token_from_service_account_key(target_audience):
    secret_id = os.environ.get("GCP_SERVICE_ACCOUNT_SECRET")
    if not secret_id:
        return ""

    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
    except ModuleNotFoundError as exc:
        raise RuntimeError("google-auth is required when GCP_SERVICE_ACCOUNT_SECRET is configured") from exc

    service_account_info = read_secret_json(secret_id)
    credentials = service_account.IDTokenCredentials.from_service_account_info(
        service_account_info,
        target_audience=target_audience,
    )
    credentials.refresh(Request())
    return credentials.token or ""


def read_secret_json(secret_id):
    secret = secretsmanager.get_secret_value(SecretId=secret_id)
    secret_string = secret.get("SecretString") or base64.b64decode(secret.get("SecretBinary", b"")).decode("utf-8")
    return json.loads(secret_string)


def find_media_by_urls(owner_id, urls):
    wanted = set(urls)
    wanted_locations = {location for location in (parse_s3_url(url) for url in wanted) if all(location)}
    return [
        item
        for item in list_owner_media(owner_id)
        if item.get("fullUrl") in wanted
        or item.get("thumbnail") in wanted
        or item.get("thumbnailUrl") in wanted
        or (wanted_locations and parse_s3_url(item.get("fullUrl")) in wanted_locations)
        or (wanted_locations and parse_s3_url(item.get("thumbnail")) in wanted_locations)
        or (wanted_locations and parse_s3_url(item.get("thumbnailUrl")) in wanted_locations)
    ]


def normalize_media(item):
    if not item:
        return None
    tags = item.get("tags") or {}
    if isinstance(tags, dict):
        tag_list = [{"name": name, "count": int(count)} for name, count in tags.items()]
    else:
        tag_list = tags
    media_type = item.get("type") or item.get("fileKind") or infer_type(item.get("mimeType", ""))
    full_storage_url = item.get("fullUrl") or item.get("s3Url") or s3_url(item.get("bucket", ""), item.get("key", ""))
    thumbnail_storage_url = item.get("thumbnail") or item.get("thumbnailUrl") or ""
    if not thumbnail_storage_url and media_type == "video":
        thumbnail_storage_url = full_storage_url
    full_url = browser_s3_url(full_storage_url)
    thumbnail_url = browser_s3_url(thumbnail_storage_url)
    return {
        "id": item.get("id"),
        "name": item.get("name") or item.get("originalName") or "Untitled media",
        "type": media_type,
        "thumbnail": thumbnail_url,
        "thumbnailUrl": thumbnail_url,
        "fullUrl": full_url,
        "s3Uri": full_storage_url,
        "thumbnailS3Uri": thumbnail_storage_url,
        "framePrefix": item.get("framePrefix") or "",
        "frameS3Uris": item.get("frameS3Uris") or [],
        "frameCount": int(item.get("frameCount") or 0),
        "tags": tag_list,
        "checksum": item.get("checksum") or item.get("sha256"),
        "createdAt": item.get("createdAt") or now_iso(),
        "size": int(item.get("size", 0)) if item.get("size") is not None else None,
        "mimeType": item.get("mimeType") or item.get("contentType"),
        "source": "upload",
        "status": item.get("status", "READY"),
    }


def infer_type(mime_type):
    return "video" if (mime_type or "").startswith("video") else "image"


def infer_tags_from_name(name):
    lowered = (name or "").lower()
    exact_tags = {}
    for label in species_labels():
        full_aliases = [alias for alias in label["aliases"] if "_" in alias or " " in alias]
        if any(alias and alias in lowered for alias in full_aliases):
            exact_tags[label["tag"]] = 1
    if exact_tags:
        return exact_tags

    tags = {}
    for label in species_labels():
        broad_aliases = [alias for alias in label["aliases"] if "_" not in alias and " " not in alias]
        if any(alias and alias in lowered for alias in broad_aliases):
            tags[label["tag"]] = 1
    return tags or {"untagged": 1}


def clean_tag(tag):
    return normalize_tag(tag)


def clean_tags(tags):
    return sorted({clean_tag(tag) for tag in tags if clean_tag(tag)})


def s3_url(bucket, key):
    if not bucket or not key:
        return ""
    return f"s3://{bucket}/{key}"


def parse_s3_url(value):
    if not value:
        return None, None
    parsed = urlparse(value)
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = unquote(parsed.path.lstrip("/"))
        return bucket, key
    if parsed.scheme in {"http", "https"}:
        host = parsed.netloc.split(":", 1)[0]
        path = unquote(parsed.path.lstrip("/"))
        if ".s3." in host or host.endswith(".s3.amazonaws.com"):
            bucket = host.split(".s3", 1)[0]
            return bucket, path
        if host.startswith("s3.") or host == "s3.amazonaws.com":
            bucket, _, key = path.partition("/")
            return bucket, key
    return None, None


def browser_s3_url(value):
    bucket, key = parse_s3_url(value)
    if not bucket or not key:
        return value or ""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=int(os.environ.get("GET_URL_EXPIRES", "3600")),
    )


def s3_key_from_event(record):
    bucket = record["s3"]["bucket"]["name"]
    key = unquote(record["s3"]["object"]["key"].replace("+", " "))
    return bucket, key


def to_json(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


@lru_cache(maxsize=1)
def species_labels():
    labels_path = Path(os.environ.get("LABELS_PATH", DEFAULT_LABELS_PATH))
    if not labels_path.exists():
        return fallback_species_labels()

    labels_by_tag = {}
    with labels_path.open(newline="") as file:
        for row in csv.reader(file, delimiter=";"):
            if len(row) < 7:
                continue
            genus = row[4].strip()
            species = row[5].strip()
            common_name = row[6].strip()
            if not genus and not species and not common_name:
                continue

            scientific = "_".join(part for part in [genus, species] if part).lower()
            common_tag = normalize_tag(common_name) if common_name else scientific
            tag = common_tag or scientific or "unknown_species"
            aliases = {
                tag,
                tag.replace("_", " "),
                scientific,
                scientific.replace("_", " "),
            }
            if common_name:
                aliases.update(
                    word
                    for word in (normalize_tag(part) for part in common_name.split())
                    if word in COMMON_SPECIES_WORDS
                )
            if tag in labels_by_tag:
                labels_by_tag[tag]["aliases"] = sorted(set(labels_by_tag[tag]["aliases"]).union(aliases))
                continue
            labels_by_tag[tag] = {
                    "tag": tag,
                    "commonName": common_name or tag.replace("_", " "),
                    "scientificName": scientific,
                    "aliases": sorted(alias for alias in aliases if alias),
                }
    return list(labels_by_tag.values()) or fallback_species_labels()


def normalize_tag(value):
    tag = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())
    return tag.strip("_")


def fallback_species_labels():
    return [
        {"tag": "dingo", "commonName": "dingo", "scientificName": "canis_dingo", "aliases": ["dingo", "canis_dingo"]},
        {
            "tag": "eastern_gray_kangaroo",
            "commonName": "eastern gray kangaroo",
            "scientificName": "macropus_giganteus",
            "aliases": ["kangaroo", "eastern_gray_kangaroo", "macropus_giganteus"],
        },
        {
            "tag": "common_wombat",
            "commonName": "common wombat",
            "scientificName": "vombatus_ursinus",
            "aliases": ["wombat", "common_wombat", "vombatus_ursinus"],
        },
        {
            "tag": "australian_echidna",
            "commonName": "australian echidna",
            "scientificName": "tachyglossus_aculeatus",
            "aliases": ["echidna", "australian_echidna", "tachyglossus_aculeatus"],
        },
        {
            "tag": "australian_magpie",
            "commonName": "australian magpie",
            "scientificName": "gymnorhina_tibicen",
            "aliases": ["magpie", "australian_magpie", "gymnorhina_tibicen"],
        },
    ]
