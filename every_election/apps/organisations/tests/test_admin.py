import os
from datetime import date

import boto3
from botocore.exceptions import ClientError
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from elections.tests.factories import ElectedRoleFactory
from mock.mock import Mock, patch
from moto import mock_aws
from organisations.models import (
    DivisionProblem,
    OrganisationGeographyProblem,
    OrganisationProblem,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
    OrganisationGeographyFactory,
)


class OrganisationProblemTests(TestCase):
    def test_no_geography(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertTrue(problem.no_geography)
        self.assertFalse(problem.no_divisionset)
        self.assertFalse(problem.no_electedrole)
        self.assertEqual(
            "No associated OrganisationGeography", problem.problem_text
        )

    def test_no_divisionset(self):
        org = OrganisationFactory()
        OrganisationGeographyFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.no_divisionset)
        self.assertFalse(problem.no_electedrole)
        self.assertEqual("No associated DivisionSet", problem.problem_text)

    def test_no_electedrole(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        OrganisationGeographyFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.no_divisionset)
        self.assertTrue(problem.no_electedrole)
        self.assertEqual("No associated ElectedRole", problem.problem_text)

    def test_all_ok(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        OrganisationGeographyFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 0)

    def test_all_broken(self):
        OrganisationFactory()

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.no_divisionset)
        self.assertTrue(problem.no_electedrole)
        self.assertEqual(
            "No associated OrganisationGeography", problem.problem_text
        )


class OrganisationGeographyProblemTests(TestCase):
    def test_no_gss_code(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.gss = ""
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)

    def test_no_geography(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.geography = None
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("Geography field is NULL", problem.problem_text)

    def test_invalid_source(self):
        og = OrganisationGeographyFactory()
        og.source = "unknown"
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Boundary source is invalid", problem.problem_text)

    def test_all_ok(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 0)

    def test_all_broken(self):
        og = OrganisationGeographyFactory()
        og.source = ""
        og.gss = ""
        og.geography = None
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Geography field is NULL", problem.problem_text)


class DivisionProblemTests(TestCase):
    def test_no_gss_code(self):
        div = OrganisationDivisionFactory()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "this is totally fine"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)

    def test_invalid_source(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "unknown"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Boundary source is invalid", problem.problem_text)

    def test_no_geography(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual(
            "No associated DivisionGeography", problem.problem_text
        )

    def test_all_ok(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "this is totally fine"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 0)

    def test_all_broken(self):
        div = OrganisationDivisionFactory()
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = ""
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertTrue(problem.invalid_source)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)


TEST_LGBCE_MIRROR_BUCKET = "test-lgbce-mirror"


def get_content_length(s3_client, bucket, key):
    response = s3_client.head_object(Bucket=bucket, Key=key)
    return int(response["ResponseMetadata"]["HTTPHeaders"]["content-length"])


@mock_aws
class WriteCSVToS3Tests(TestCase):
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

        org_foo = OrganisationFactory(
            official_identifier="FOO",
            official_name="City of Foobar",
            common_name="Foobar",
            slug="foobar",
        )
        OrganisationDivisionSetFactory(organisation=org_foo, end_date=None)
        self.completed_review = CompletedOrganisationBoundaryReviewFactory(
            organisation=org_foo
        )
        self.completed_review.effective_date = date(2023, 5, 2)
        self.completed_review.save()

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    @patch("requests.get")
    @patch("eco_parser.parser.EcoParser.get_data")
    def test_post_to_s3(self, get_data_mock, mock_get):
        with open(
            "every_election/apps/organisations/boundaries/fixtures/buckinghamshire-eco-data.xml"
        ) as f:
            bucks_xml = f.read()
        get_data_mock.return_value = bucks_xml
        mock_get.return_value = mock_boundaries_response = Mock()
        mock_boundaries_response.status_code = 200
        mock_boundaries_response.content = b"Some polygons!!"

        keys = (
            (self.completed_review.s3_boundaries_key, 15),
            (self.completed_review.s3_eco_key, 9322),
            (self.completed_review.s3_end_date_key, 50),
        )
        for key, length in keys:
            with self.assertRaises(ClientError) as e:
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                )
                self.assertEqual(e.exception.response["Code"], 404)

        user = get_user_model().objects.create(is_staff=True, is_superuser=True)
        self.client.force_login(user=user)
        response = self.client.post(
            reverse(
                "admin:write_csv_to_s3_view",
                kwargs={
                    "object_id": self.completed_review.pk,
                },
            ),
            {"overwrite": "false"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        mock_get.assert_called_once_with(
            "https://www.lgbce.org.uk/sites/default/files/2023-03/polygons.zip"
        )
        print(
            self.s3.get_object(
                Bucket=TEST_LGBCE_MIRROR_BUCKET,
                Key=self.completed_review.s3_eco_key,
            )["Body"]
            .read()
            .decode("utf-8")
        )
        for key, length in keys:
            self.assertEqual(
                length,
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                ),
            )
        self.assertEqual(
            "Start Date,End Date,Name,official_identifier,geography_curie,seats_total,Boundary Commission Consultation URL,Legislation URL,Short Title,Notes,Mapit Generation URI,Organisation ID,"
            "Organisation ID type",
            self.s3.get_object(
                Bucket=TEST_LGBCE_MIRROR_BUCKET,
                Key=self.completed_review.s3_eco_key,
            )["Body"]
            .read()
            .decode("utf-8")
            .split("\n")[0],
        )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    @patch("requests.get")
    @patch("eco_parser.parser.EcoParser.get_data")
    def test_post_to_s3_already_exists_overwrite_false(
        self, get_data_mock, mock_get
    ):
        with open(
            "every_election/apps/organisations/boundaries/fixtures/buckinghamshire-eco-data.xml"
        ) as f:
            bucks_xml = f.read()
        get_data_mock.return_value = bucks_xml
        mock_get.return_value = mock_boundaries_response = Mock()
        mock_boundaries_response.status_code = 200
        mock_boundaries_response.content = b"Some polygons!!"
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=self.completed_review.s3_boundaries_key,
            Body=bytes("polygons!", encoding="utf-8"),
        )
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.completed_review.s3_directory_key}/end_date.csv",
            Body=bytes(
                "org,start_date,end_date\norg_identifier,2017-05-04,2023-05-03\n",
                encoding="utf-8",
            ),
        )
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.completed_review.s3_directory_key}/eco.csv",
            Body=bytes(
                "eco,csv,yeah",
                encoding="utf-8",
            ),
        )
        keys = (
            (self.completed_review.s3_boundaries_key, 9),
            (self.completed_review.s3_eco_key, 12),
            (self.completed_review.s3_end_date_key, 61),
        )
        for key, length in keys:
            self.assertEqual(
                length,
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                ),
            )

        user = get_user_model().objects.create(is_staff=True, is_superuser=True)
        self.client.force_login(user=user)
        response = self.client.post(
            reverse(
                "admin:write_csv_to_s3_view",
                kwargs={
                    "object_id": self.completed_review.pk,
                },
            ),
            {"overwrite": "False"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        for key, length in keys:
            self.assertEqual(
                length,
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                ),
            )

    @override_settings(LGBCE_BUCKET=TEST_LGBCE_MIRROR_BUCKET)
    @patch("requests.get")
    @patch("eco_parser.parser.EcoParser.get_data")
    def test_post_to_s3_already_exists_overwrite_true(
        self, get_data_mock, mock_get
    ):
        with open(
            "every_election/apps/organisations/boundaries/fixtures/buckinghamshire-eco-data.xml"
        ) as f:
            bucks_xml = f.read()
        get_data_mock.return_value = bucks_xml
        mock_get.return_value = mock_boundaries_response = Mock()
        mock_boundaries_response.status_code = 200
        mock_boundaries_response.content = b"Some polygons!!"
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=self.completed_review.s3_boundaries_key,
            Body=bytes("polygons!", encoding="utf-8"),
        )
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.completed_review.s3_directory_key}/end_date.csv",
            Body=bytes(
                "org,start_date,end_date\norg_identifier,2017-05-04,2023-05-03\n",
                encoding="utf-8",
            ),
        )
        # Create processed objects on s3
        self.s3.put_object(
            Bucket=TEST_LGBCE_MIRROR_BUCKET,
            Key=f"{self.completed_review.s3_directory_key}/eco.csv",
            Body=bytes(
                "eco,csv,yeah",
                encoding="utf-8",
            ),
        )
        keys = (
            (self.completed_review.s3_boundaries_key, 9),
            (self.completed_review.s3_eco_key, 12),
            (self.completed_review.s3_end_date_key, 61),
        )
        for key, length in keys:
            self.assertEqual(
                length,
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                ),
            )

        user = get_user_model().objects.create(is_staff=True, is_superuser=True)
        self.client.force_login(user=user)
        response = self.client.post(
            reverse(
                "admin:write_csv_to_s3_view",
                kwargs={
                    "object_id": self.completed_review.pk,
                },
            ),
            {"overwrite": "True"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        keys = (
            (self.completed_review.s3_boundaries_key, 15),
            (self.completed_review.s3_eco_key, 9322),
            (self.completed_review.s3_end_date_key, 50),
        )
        for key, length in keys:
            self.assertEqual(
                length,
                get_content_length(
                    self.s3,
                    bucket=TEST_LGBCE_MIRROR_BUCKET,
                    key=key,
                ),
            )
