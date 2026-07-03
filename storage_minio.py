import os
import io
from dotenv import load_dotenv
from minio import Minio

load_dotenv("conf.env")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        if not _client.bucket_exists(MINIO_BUCKET):
            _client.make_bucket(MINIO_BUCKET)
    return _client


def upload_bytes(filename: str, data: bytes):
    client = get_client()
    client.put_object(MINIO_BUCKET, filename, io.BytesIO(data), length=len(data))


def download_bytes(filename: str) -> bytes:
    client = get_client()
    response = client.get_object(MINIO_BUCKET, filename)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def list_files():
    client = get_client()
    return [obj.object_name for obj in client.list_objects(MINIO_BUCKET)]
