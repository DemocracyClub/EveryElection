import os
from io import StringIO
from unittest.mock import Mock, patch

import boto3
from botocore.exceptions import ClientError
from django.test import TestCase, override_settings
from moto import mock_s3
from organisations.boundaries.lgbce_review_helper import (
    LGBCEReviewHelper,
    check_s3_obj_exists,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationFactory,
    UnprocessedOrganisationBoundaryReviewFactory,
)

TEST_LGBCE_MIRROR_BUCKET = "test-lgbce-mirror"


def get_content_length(s3_client, bucket, key):
    response = s3_client.head_object(Bucket=bucket, Key=key)
    return int(response["ResponseMetadata"]["HTTPHeaders"]["content-length"])


@mock_s3
class TestLGBCEReviewHelper(TestCase):
    def setUp(self):
        # Don't do anything unintended
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"

        # Set up s3 client
        self.s3 = boto3.client("s3", region_name="eu-west-2")

        # Create mock bucket
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=TEST_LGBCE_MIRROR_BUCKET)

        # Create fixture objects
        self.unprocessed_review = UnprocessedOrganisationBoundaryReviewFactory(
            organisation=OrganisationFactory(official_identifier="FOO")
        )
        self.processed_review = CompletedOrganisationBoundaryReviewFactory(
            boundaries_url="path/to/processed_review_polys.zip"
        )
        self.incomplete_review = IncompleteOrganisationBoundaryReviewFactory()

        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=self.processed_review.s3_boundaries_key,
            Body=bytes("polygons!", encoding="utf-8"),
        )
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.processed_review.s3_directory_key}/end_date.csv",
            Body=bytes(
                "org,start_date,end_date\norg_identifier,2023-05-04,2023-05-03\n",
                encoding="utf-8",
            ),
        )

    def test_check_s3_obj_exists_exists(self):
        self.assertTrue(
            check_s3_obj_exists(
                self.s3,
                TEST_LGBCE_MIRROR_BUCKET,
                self.processed_review.s3_boundaries_key,
            )
        )

    def test_check_s3_obj_exists_not_exists(self):
        self.assertFalse(
            check_s3_obj_exists(
                self.s3,
                TEST_LGBCE_MIRROR_BUCKET,
                "foobar",
            )
        )

    def test_check_s3_obj_exists_no_bucket(self):
        with self.assertRaises(ClientError) as e:
            check_s3_obj_exists(
                self.s3, "this-bucket-doesnt-exist-450928236839", "foobar"
            )
        self.assertEqual(e.exception.response["Error"]["Code"], "NoSuchBucket")

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    def test_upload_boundaries_to_s3_already_exists(self):
        buffer = StringIO()
        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer)
        lgbce_review_helper.upload_boundaries_to_s3(self.processed_review)
        self.assertEqual(
            f"{self.processed_review.slug}/The {self.processed_review.organisation.common_name} (Electoral Changes) "
            f"Order 2023/processed_review_polys.zip already exists. Perhaps you meant to initialise with "
            f"'overwrite=True'?",
            buffer.getvalue(),
        )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    @patch("requests.get")
    def test_upload_boundaries_to_s3(self, mock_get):
        # This is mocking the boundaries that are downloaded from the lgbce site
        mock_get.return_value = mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Some polygons!!"

        buffer = StringIO()
        with self.assertRaises(ClientError) as e:
            get_content_length(
                self.s3,
                bucket=TEST_LGBCE_MIRROR_BUCKET,
                key=self.unprocessed_review.s3_boundaries_key,
            )
            self.assertEqual(e.exception.response["Code"], 404)

        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer, overwrite=True)
        lgbce_review_helper.upload_boundaries_to_s3(self.processed_review)
        self.assertEqual(
            f"Uploading {self.processed_review.boundaries_url} to s3://{TEST_LGBCE_MIRROR_BUCKET}/{self.processed_review.s3_boundaries_key}",
            buffer.getvalue(),
        )
        mock_get.assert_called_once_with(
            "https://www.lgbce.org.uk/path/to/processed_review_polys.zip"
        )
        self.assertEqual(
            15,
            get_content_length(
                self.s3,
                bucket=TEST_LGBCE_MIRROR_BUCKET,
                key=self.processed_review.s3_boundaries_key,
            ),
        )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    @patch("requests.get")
    def test_upload_boundaries_to_s3_already_exists_overwrite(self, mock_get):
        # This is mocking the boundaries that are downloaded from the lgbce site
        mock_get.return_value = mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Some different polygons"

        buffer = StringIO()
        self.assertEqual(
            9,
            get_content_length(
                self.s3,
                bucket=TEST_LGBCE_MIRROR_BUCKET,
                key=self.processed_review.s3_boundaries_key,
            ),
        )
        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer, overwrite=True)
        lgbce_review_helper.upload_boundaries_to_s3(self.processed_review)
        self.assertEqual(
            f"Uploading {self.processed_review.boundaries_url} to s3://{TEST_LGBCE_MIRROR_BUCKET}/{self.processed_review.s3_boundaries_key}",
            buffer.getvalue(),
        )
        mock_get.assert_called_once_with(
            "https://www.lgbce.org.uk/path/to/processed_review_polys.zip"
        )
        self.assertEqual(
            23,
            get_content_length(
                self.s3,
                bucket=TEST_LGBCE_MIRROR_BUCKET,
                key=self.processed_review.s3_boundaries_key,
            ),
        )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    def test_upload_end_date_csv_to_s3_already_exists(self):
        buffer = StringIO()
        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer)
        lgbce_review_helper.upload_end_date_csv_to_s3(
            self.processed_review, "2024-05-02"
        )
        self.assertEqual(
            f"{self.processed_review.s3_directory_key}/end_date.csv already exists. Perhaps you meant to initialise "
            f"with 'overwrite=True'?",
            buffer.getvalue(),
        )

    def test_make_end_date_rows(self):
        buffer = StringIO()
        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer)
        rows = lgbce_review_helper.make_end_date_rows(
            self.unprocessed_review, "2024-05-02"
        )
        self.assertEqual(2, len(rows))
        self.assertListEqual(
            ["org", "start_date", "end_date"],
            rows[0],
        )
        self.assertListEqual(
            [
                "FOO",
                "2024-05-02",
                "2024-05-01",
            ],
            rows[1],
        )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    def test_upload_end_date_csv_to_s3(self):
        with self.assertRaises(ClientError) as e:
            get_content_length(
                self.s3,
                bucket=TEST_LGBCE_MIRROR_BUCKET,
                key=f"{self.unprocessed_review.s3_directory_key}/end_date.csv",
            )
            self.assertEqual(e.exception.response["Code"], 404)

        buffer = StringIO()
        lgbce_review_helper = LGBCEReviewHelper(stdout=buffer)
        lgbce_review_helper.upload_end_date_csv_to_s3(
            self.unprocessed_review, "2024-05-02"
        )

        self.assertEqual(
            f"Uploading end_date_csv to "
            f"s3://{TEST_LGBCE_MIRROR_BUCKET}/{self.unprocessed_review.s3_directory_key}/end_date.csv",
            buffer.getvalue(),
        )
        csv_body = self.s3.get_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.unprocessed_review.s3_directory_key}/end_date.csv",
        )["Body"].read()
        self.assertEqual(
            f"org,start_date,end_date\n"
            f"{self.unprocessed_review.organisation.official_identifier},2024-05-02,2024-05-01\n",
            csv_body.decode("utf-8"),
        )

    def test_get_xml_link_from_eco_url_a(self):
        def get_responses(link, **kwargs):
            """
            The method being tested 'heads' the links generated to determine if they
            return a 200. So we need to mock some respnses
            """
            mock = Mock()
            tail = "/".join(link.split("/")[6:])
            match tail:
                case "schedule/1/made/data.xml":
                    mock.status_code = 200
                    return mock
                case "schedule/made/data.xml":
                    mock.status_code = 404
                    return mock
                case "schedules/made/data.xml":
                    mock.status_code = 404
                    return mock
                case _:
                    mock.status_code = 404
                    return mock

        with patch("requests.head", side_effect=get_responses) as mock_head:
            mock_head.return_value = Mock(side_effect=get_responses)
            lgbce_review_helper = LGBCEReviewHelper()
            self.assertEqual(
                "https://www.legislation.gov.uk/uksi/2017/1315/schedule/1/made/data.xml",
                lgbce_review_helper.get_xml_link_from_eco_url(
                    "https://www.legislation.gov.uk/uksi/2017/1315"
                ),
            )

    def test_get_xml_link_from_eco_url_b(self):
        def get_responses(link, **kwargs):
            """
            The method being tested 'heads' the links generated to determine if they
            return a 200. So we need to mock some responses.
            """
            mock = Mock()
            tail = "/".join(link.split("/")[6:])
            match tail:
                case "schedule/1/made/data.xml":
                    mock.status_code = 404
                    return mock
                case "schedule/made/data.xml":
                    mock.status_code = 200
                    return mock
                case "schedules/made/data.xml":
                    mock.status_code = 404
                    return mock
                case _:
                    mock.status_code = 404
                    return mock

        with patch("requests.head", side_effect=get_responses) as mock_head:
            mock_head.return_value = Mock(side_effect=get_responses)
            lgbce_review_helper = LGBCEReviewHelper()
            self.assertEqual(
                "https://www.legislation.gov.uk/uksi/2021/1053/schedule/made/data.xml",
                lgbce_review_helper.get_xml_link_from_eco_url(
                    "https://www.legislation.gov.uk/uksi/2021/1053"
                ),
            )

    def test_get_xml_link_from_eco_url_c(self):
        def get_responses(link, **kwargs):
            """
            The method being tested 'heads' the links generated to determine if they
            return a 200. So we need to mock some responses.
            """
            mock = Mock()
            tail = "/".join(link.split("/")[6:])
            match tail:
                case "schedule/1/made/data.xml":
                    mock.status_code = 404
                    return mock
                case "schedule/made/data.xml":
                    mock.status_code = 404
                    return mock
                case "schedules/made/data.xml":
                    mock.status_code = 200
                    return mock
                case _:
                    mock.status_code = 404
                    return mock

        with patch("requests.head", side_effect=get_responses) as mock_head:
            mock_head.return_value = Mock(side_effect=get_responses)
            lgbce_review_helper = LGBCEReviewHelper()
            self.assertEqual(
                "https://www.legislation.gov.uk/uksi/2021/417/schedules/made/data.xml",
                lgbce_review_helper.get_xml_link_from_eco_url(
                    "https://www.legislation.gov.uk/uksi/2021/417"
                ),
            )

    @patch("eco_parser.parser.EcoParser.get_data")
    def test_parse_eco_xml(self, get_data_mock):
        with open(
            "every_election/apps/organisations/boundaries/fixtures/buckinghamshire-eco-data.xml"
        ) as f:
            bucks_xml = f.read()
        get_data_mock.return_value = bucks_xml
        lgbce_review_helper = LGBCEReviewHelper()
        expected = [
            (
                "(1) Name of Ward",
                "(2) Number of councillors",
            ),
            ("Abbey", "2"),
            ("Amersham & Chesham Bois", "3"),
            ("Aston Clinton & Weston Turville", "2"),
            ("Aylesbury East", "2"),
            ("Aylesbury North", "2"),
            ("Aylesbury North West", "2"),
            ("Aylesbury South East", "2"),
            ("Aylesbury South West", "2"),
            ("Aylesbury West", "2"),
            ("Beaconsfield", "2"),
            ("Berryfields, Buckingham Park & Watermead", "2"),
            ("Bierton, Kingsbrook & Wing", "2"),
            ("Booker & Cressex", "1"),
            ("Buckingham", "3"),
            ("Burnham", "3"),
            ("Castlefield & Oakridge", "2"),
            ("Chalfont St Giles & Little Chalfont", "3"),
            ("Chalfont St Peter", "2"),
            ("Chesham North", "3"),
            ("Chesham South", "2"),
            ("Chiltern Villages", "1"),
            ("Disraeli", "1"),
            ("Downley", "1"),
            ("Farnhams & Stoke Poges", "3"),
            ("Flackwell Heath & The Wooburns", "3"),
            ("Gerrards Cross & Denham", "3"),
            ("Grendon Underwood & The Claydons", "2"),
            ("Haddenham & Stone", "2"),
            ("Hazlemere", "2"),
            ("Horwood", "1"),
            ("Iver", "2"),
            ("Ivinghoe", "2"),
            ("Long Crendon", "1"),
            ("Marlow", "3"),
            ("Marsh & Micklefield", "2"),
            ("Newton Longville", "2"),
            ("Penn, Tylers Green & Loudwater", "2"),
            ("Princes Risborough", "2"),
            ("Quainton", "1"),
            ("Ridgeway East", "2"),
            ("Ridgeway West", "2"),
            ("Sands", "1"),
            ("Terriers & Amersham Hill", "2"),
            ("The Missendens", "3"),
            ("Totteridge & Bowerdean", "2"),
            ("Waddesdon", "1"),
            ("Wendover, Halton & Stoke Mandeville", "2"),
            ("West Wycombe & Lane End", "1"),
            ("Winslow", "1"),
        ]

        self.assertEqual(
            expected,
            lgbce_review_helper.parse_eco_xml(
                "https://www.legislation.gov.uk/uksi/2023/1205/schedule/1/made/data.xml"
            ),
        )

    @patch("eco_parser.parser.EcoParser.get_data")
    @patch("requests.head")
    def test_make_eco_csv(self, requests_head_mock, get_data_mock):
        with open(
            "every_election/apps/organisations/boundaries/fixtures/west-suffolk-eco.xml"
        ) as f:
            wsk_xml = f.read()
        get_data_mock.return_value = wsk_xml
        requests_head_mock.return_value = mocked_head_response = Mock()
        mocked_head_response.status_code = 200

        lgbce_review_helper = LGBCEReviewHelper()

        wsk_review = CompletedOrganisationBoundaryReviewFactory(
            **{
                "organisation": OrganisationFactory(official_identifier="WSK"),
                "legislation_title": "The West Suffolk (Electoral Changes) Order 2018",
                "slug": "west-suffolk",
                "consultation_url": "http://www.lgbce.org.uk/all-reviews/west-suffolk",
                "boundaries_url": "",
                "status": "Completed",
                "latest_event": "Effective date",
                "legislation_url": "http://www.legislation.gov.uk/uksi/2018/1375/contents/made",
                "legislation_made": True,
            }
        )

        with open(
            f"{os.path.dirname(os.path.realpath(__file__))}/../fixtures/west_suffolk_eco.csv"
        ) as f:
            expected_value = f.read()

        self.assertEqual(
            expected_value,
            lgbce_review_helper.make_eco_csv(wsk_review).decode("utf-8"),
        )
