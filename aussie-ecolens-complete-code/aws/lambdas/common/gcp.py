import json
import os
from functools import lru_cache

import boto3
from google.cloud import firestore, pubsub_v1, storage
from google.oauth2 import service_account


@lru_cache(maxsize=1)
def service_account_info():
    secret_id = os.environ["GCP_SECRET_ID"]
    secret = boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)
    return json.loads(secret["SecretString"])


@lru_cache(maxsize=1)
def credentials():
    return service_account.Credentials.from_service_account_info(service_account_info())


def project_id():
    return os.environ.get("GCP_PROJECT_ID") or service_account_info()["project_id"]


@lru_cache(maxsize=1)
def firestore_client():
    return firestore.Client(project=project_id(), credentials=credentials())


@lru_cache(maxsize=1)
def storage_client():
    return storage.Client(project=project_id(), credentials=credentials())


@lru_cache(maxsize=1)
def publisher_client():
    return pubsub_v1.PublisherClient(credentials=credentials())


def server_timestamp():
    return firestore.SERVER_TIMESTAMP

