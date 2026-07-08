import uuid
from functools import lru_cache

import boto3
from botocore.client import Config

from app.config import get_settings


@lru_cache
def _s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def build_object_key(user_id: uuid.UUID, kind: str, extension: str) -> str:
    return f"users/{user_id}/{kind}/{uuid.uuid4()}.{extension}"


def public_url(key: str) -> str:
    settings = get_settings()
    base = settings.s3_public_base_url.rstrip("/")
    return f"{base}/{key}"


def create_presigned_upload(key: str, content_type: str, expires_in: int = 3600) -> str:
    settings = get_settings()
    client = _s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def download_object(key: str) -> bytes:
    settings = get_settings()
    client = _s3_client()
    response = client.get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()


def upload_object(key: str, data: bytes, content_type: str) -> str:
    settings = get_settings()
    client = _s3_client()
    client.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
    return public_url(key)


def delete_object(key: str) -> None:
    settings = get_settings()
    client = _s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)
