import tempfile

import boto3


class S3Wrapper:
    def __init__(self, bucket_name):
        resource = boto3.resource(
            "s3",
        )
        self.bucket = resource.Bucket(bucket_name)

    def get_file(self, filepath):
        tmp = tempfile.NamedTemporaryFile()
        self.bucket.download_file(filepath, tmp.name)
        return tmp
