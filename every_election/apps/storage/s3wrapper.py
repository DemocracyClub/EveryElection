import boto3
import tempfile
from django.conf import settings

class S3Wrapper:

    def __init__(self, bucket_name):
        resource = boto3.resource(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = resource.Bucket(bucket_name)

    def get_file(self, filepath):
        tmp = tempfile.NamedTemporaryFile()
        self.bucket.download_file(filepath, tmp.name)
        return tmp
