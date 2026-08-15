from __future__ import annotations

import io
import uuid

from minio import Minio

from app.core.config import get_settings

settings = get_settings()


def _is_minio_endpoint() -> bool:
    """Check if we're using a MinIO-compatible endpoint vs real AWS S3.

    MinIO-compatible: localhost / dev hostnames and custom S3-compatible
    endpoints (e.g. ``http://minio:9000`` inside the docker network).
    Real AWS S3: endpoints on ``amazonaws.com``.
    """
    endpoint = settings.S3_ENDPOINT.lower().strip()
    return "amazonaws.com" not in endpoint and not endpoint.startswith("s3.")


def _minio_client() -> Minio:
    """Build a MinIO client, normalizing the endpoint for the minio SDK.

    minio-python rejects endpoints that carry a scheme; the scheme must be
    expressed via the ``secure`` flag instead.
    """
    endpoint = settings.S3_ENDPOINT.strip()
    secure = settings.S3_SECURE
    if "://" in endpoint:
        scheme, endpoint = endpoint.split("://", 1)
        secure = scheme.lower() == "https"
    return Minio(
        endpoint,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=secure,
    )


def _public_read_policy(bucket: str) -> str:
    """Anonymous read policy so generated public URLs actually serve media."""
    return f"""
{{
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Effect": "Allow",
      "Principal": {{"AWS": ["*"]}},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::{bucket}/*"]
    }}
  ]
}}
"""


def ensure_bucket_exists() -> None:
    """Ensure the bucket exists, create it if not.

    Uses MinIO for local development and AWS S3 for production.
    The bucket is set to anonymous read so the plain public URLs returned by
    upload_file() are actually fetchable by browsers.
    """
    if _is_minio_endpoint():
        # MinIO path
        try:
            minio_client = _minio_client()
            if not minio_client.bucket_exists(settings.S3_BUCKET):
                minio_client.make_bucket(settings.S3_BUCKET)
            minio_client.set_bucket_policy(
                settings.S3_BUCKET, _public_read_policy(settings.S3_BUCKET)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to ensure MinIO bucket exists: {e}") from e
    else:
        # Production AWS S3 path using botocore
        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT if settings.S3_SECURE else None,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
            # Check if bucket exists
            try:
                s3_client.head_bucket(Bucket=settings.S3_BUCKET)
            except Exception:  # noqa: BLE001
                s3_client.create_bucket(Bucket=settings.S3_BUCKET)
            s3_client.put_bucket_policy(
                Bucket=settings.S3_BUCKET,
                Policy=_public_read_policy(settings.S3_BUCKET),
            )
        except ImportError:
            raise RuntimeError(
                "boto3 is required for production S3 support. "
                "Install with: pip install boto3"
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to ensure S3 bucket exists: {e}") from e


def upload_file(
    file_data: bytes,
    file_name: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file to storage (MinIO or AWS S3) and return the public URL.

    Args:
        file_data: The file content as bytes.
        file_name: The name of the file (including extension).
        content_type: The MIME type of the file.

    Returns:
        The public URL of the uploaded file.

    Raises:
        RuntimeError: If the upload fails.
    """
    ensure_bucket_exists()

    # Generate a unique object name to avoid collisions
    object_name = f"{uuid.uuid4()}-{file_name}"

    if _is_minio_endpoint():
        # MinIO path
        try:
            minio_client = _minio_client()
            minio_client.put_object(
                bucket_name=settings.S3_BUCKET,
                object_name=object_name,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to MinIO: {e}") from e
    else:
        # Production AWS S3 path using boto3
        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT if settings.S3_SECURE else None,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=object_name,
                Body=file_data,
                ContentType=content_type,
            )
        except ImportError:
            raise RuntimeError(
                "boto3 is required for production S3 support. "
                "Install with: pip install boto3"
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to S3: {e}") from e

    # Construct the public URL
    if settings.S3_PUBLIC_URL:
        url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{object_name}"
    else:
        # If no public URL is set, construct from the endpoint
        protocol = "https" if settings.S3_SECURE else "http"
        url = f"{protocol}://{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{object_name}"

    return url


def _object_name_from_url(url: str) -> str | None:
    """Extract the object name from a stored public URL."""
    base = settings.S3_PUBLIC_URL or (
        f"{'https' if settings.S3_SECURE else 'http'}://{settings.S3_ENDPOINT}"
    )
    prefix = f"{base}/{settings.S3_BUCKET}/"
    if url.startswith(prefix):
        return url[len(prefix) :]
    return None


def delete_file(url: str) -> None:
    """
    Delete an object from storage (MinIO or AWS S3) by its public URL.

    No-op when the URL cannot be mapped to an object (e.g. external URLs).
    """
    object_name = _object_name_from_url(url)
    if object_name is None:
        return
    if _is_minio_endpoint():
        try:
            minio_client = _minio_client()
            minio_client.remove_object(
                bucket_name=settings.S3_BUCKET, object_name=object_name
            )
        except Exception as e:
            raise RuntimeError(f"Failed to delete file from MinIO: {e}") from e
    else:
        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT if settings.S3_SECURE else None,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
            s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=object_name)
        except ImportError:
            raise RuntimeError(
                "boto3 is required for production S3 support. "
                "Install with: pip install boto3"
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to delete file from S3: {e}") from e
