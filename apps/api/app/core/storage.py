from __future__ import annotations

import uuid

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

settings = get_settings()

# Initialize MinIO client
minio_client = Minio(
    settings.S3_ENDPOINT,
    access_key=settings.S3_ACCESS_KEY,
    secret_key=settings.S3_SECRET_KEY,
    secure=settings.S3_SECURE,
)


def ensure_bucket_exists() -> None:
    """Ensure the bucket exists, create it if not."""
    try:
        if not minio_client.bucket_exists(settings.S3_BUCKET):
            minio_client.make_bucket(settings.S3_BUCKET)
    except S3Error as e:
        # Log the error and re-raise
        raise RuntimeError(f"Failed to ensure bucket exists: {e}") from e


def upload_file(
    file_data: bytes,
    file_name: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file to MinIO and return the public URL.

    Args:
        file_data: The file content as bytes.
        file_name: The name of the file (including extension).
        content_type: The MIME type of the file.

    Returns:
        The public URL of the uploaded file.
    """
    ensure_bucket_exists()

    # Generate a unique object name to avoid collisions
    object_name = f"{uuid.uuid4()}-{file_name}"

    try:
        # Upload the file
        minio_client.put_object(
            bucket_name=settings.S3_BUCKET,
            object_name=object_name,
            data=file_data,
            length=len(file_data),
            content_type=content_type,
        )
    except S3Error as e:
        raise RuntimeError(f"Failed to upload file: {e}") from e

    # Construct the public URL
    if settings.S3_PUBLIC_URL:
        url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{object_name}"
    else:
        # If no public URL is set, construct from the endpoint
        protocol = "https" if settings.S3_SECURE else "http"
        url = f"{protocol}://{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{object_name}"

    return url
