import boto3
from django.test import TestCase
from moto import mock_aws
from storage.s3wrapper import S3Wrapper

TEST_S3_BUCKET = "test-bucket"


@mock_aws
class TestS3Wrapper(TestCase):
    def setUp(self):
        # Set up s3 client
        self.s3_client = boto3.client("s3", region_name="eu-west-2")
        # Create mock bucket
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=TEST_S3_BUCKET)

        self.s3_wrapper = S3Wrapper("test-bucket")

    def test_check_s3_obj_exists_exists(self):
        self.s3_client.put_object(
            Bucket=TEST_S3_BUCKET,
            Key="test-file.txt",
            Body=b"hello world",
        )
        self.assertTrue(self.s3_wrapper.check_s3_obj_exists("test-file.txt"))

    def test_check_s3_obj_exists_not_exists(self):
        self.assertFalse(self.s3_wrapper.check_s3_obj_exists("foobar"))

    def test_bucket_doesnt_exist(self):
        with self.assertRaises(ValueError) as e:
            self.s3_wrapper = S3Wrapper("this-bucket-doesnt-exist-450928236839")
        self.assertEqual(
            str(e.exception),
            "S3 bucket 'this-bucket-doesnt-exist-450928236839' does not exist.",
        )
