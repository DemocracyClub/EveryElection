import sys
import tempfile
from io import BytesIO

import boto3
import botocore
import requests


class S3Wrapper:
    """
    A wrapper class for interacting with AWS S3 buckets using boto3.
    """

    def __init__(self, bucket_name):
        self.client = boto3.client("s3")
        self.bucket_name = bucket_name
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            if (
                e.response["Error"]["Code"] == "404"
                or e.response["Error"]["Code"] == "NoSuchBucket"
            ):
                raise ValueError(
                    f"S3 bucket '{bucket_name}' does not exist."
                ) from e
            raise

    def get_file(self, filepath: str):
        tmp = tempfile.NamedTemporaryFile()  # noqa: SIM115
        self.client.download_file(self.bucket_name, filepath, tmp.name)
        return tmp

    def check_s3_obj_exists(self, key: str):
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # The key does not exist.
                return False

            if e.response["Error"]["Code"] == 403:
                # Unauthorized
                sys.stderr.write(
                    "Access denied. Do you have the correct permissions?"
                )
                raise
            # Something else has gone wrong.
            raise

    def upload_obj_from_url(self, url: str, key: str):
        response = requests.get(url)
        response.raise_for_status()
        self.client.put_object(
            Bucket=self.bucket_name, Key=key, Body=BytesIO(response.content)
        )

    def upload_file_from_bytes(self, body: bytes, key: str):
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=body)

    def upload_file_from_fp(self, fp: str, key: str):
        self.client.upload_file(fp, Bucket=self.bucket_name, Key=key)

    def delete_object(self, key: str):
        self.client.delete_object(Bucket=self.bucket_name, Key=key)

    def list_object_keys(self, prefix: str = ""):
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name, Prefix=prefix
        )
        keys = []
        for page in page_iterator:
            keys.extend([obj["Key"] for obj in page.get("Contents", [])])
        return keys
