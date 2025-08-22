import tempfile

import boto3


class S3Wrapper:
    def __init__(self, bucket_name):
        self.client = boto3.client(
            "s3",
        )
        self.bucket_name = bucket_name

    def get_file(self, filepath: str):
        tmp = tempfile.NamedTemporaryFile()  # noqa: SIM115
        self.client.download_file(self.bucket_name, filepath, tmp.name)
        return tmp
