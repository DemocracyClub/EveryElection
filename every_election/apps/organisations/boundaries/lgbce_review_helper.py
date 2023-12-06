import copy
import csv
import sys
from datetime import datetime, timedelta
from io import BytesIO, StringIO

import boto3
import botocore
import requests
from django.conf import settings
from eco_parser import EcoParser, ParseError
from organisations.models import OrganisationBoundaryReview


def check_s3_obj_exists(s3_client: boto3.client, bucket: str, key: str):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
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

        if e.response["Error"]["Code"] == "NoSuchBucket":
            # Bucket doesn't exist
            raise
        # Something else has gone wrong.
        raise


def upload_obj_from_url(
    s3_client: boto3.client, url: str, bucket: str, key: str
):
    response = requests.get(url)
    response.raise_for_status()
    s3_client.put_object(Bucket=bucket, Key=key, Body=BytesIO(response.content))


class MissingLegislationTitleError(ValueError):
    pass


class LGBCEReviewHelper:
    """
    Class to help upload csvs based on boundary reviews to s3
    """

    def __init__(self, overwrite: bool = False, stdout=sys.stdout):
        self.s3_client = boto3.client("s3")
        self.overwrite = overwrite
        self.stdout = stdout
        self.review_bucket = settings.LGBCE_BUCKET

    def get_legislation_title_from_review(
        self, review: OrganisationBoundaryReview
    ):
        if review.legislation_title:
            return review

        raise MissingLegislationTitleError(
            f"{review} is missing Legislation Title"
        )

    def upload_boundaries_to_s3(self, review: OrganisationBoundaryReview):
        if not review.boundaries_url:
            self.stdout.write(f"No boundary_url found for {review}")
            return
        if (
            check_s3_obj_exists(
                self.s3_client, self.review_bucket, review.s3_boundaries_key
            )
            and not self.overwrite
        ):
            self.stdout.write(
                f"{review.s3_boundaries_key} already exists. Perhaps you meant to initialise with 'overwrite=True'?"
            )
            return

        self.stdout.write(
            f"Uploading {review.boundaries_url} to s3://{self.review_bucket}/{review.s3_boundaries_key}"
        )

        boundaries_response = requests.get(review.lgbce_boundary_url)
        boundaries_response.raise_for_status()
        self.s3_client.put_object(
            Bucket=self.review_bucket,
            Key=review.s3_boundaries_key,
            Body=BytesIO(boundaries_response.content),
        )

    def make_end_date_rows(
        self,
        review: OrganisationBoundaryReview,
        start_date: str,
        thursday_start_day: bool = True,
    ):
        def day_before(date_str: str):
            date_object = datetime.strptime(date_str, "%Y-%m-%d")
            previous_day = date_object - timedelta(days=1)
            return previous_day.strftime("%Y-%m-%d")

        def is_first_thursday_in_may(date_str: str):
            date_object = datetime.strptime(date_str, "%Y-%m-%d")
            return date_object.month == 5 and date_object.weekday() == 3

        if not is_first_thursday_in_may(start_date) and not thursday_start_day:
            self.stdout.write(
                f"{start_date} is not the the first Thursday in May. Double check."
            )
            return None

        return [
            ["org", "start_date", "end_date"],
            [
                review.organisation.official_identifier,
                start_date,
                day_before(start_date),
            ],
        ]

    def make_end_date_csv(
        self,
        review: OrganisationBoundaryReview,
        start_date: str,
        thursday_start_day: bool = True,
    ):
        rows = self.make_end_date_rows(
            review, start_date, thursday_start_day=thursday_start_day
        )
        buffer = StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerows(rows)

        return bytes(buffer.getvalue().replace("\r\n", "\n"), encoding="utf-8")

    def upload_end_date_csv_to_s3(
        self,
        review: OrganisationBoundaryReview,
        start_date: str,
        thursday_start_day: bool = True,
    ):
        end_date_s3_key = f"{review.s3_end_date_key}"

        if (
            check_s3_obj_exists(
                self.s3_client, self.review_bucket, end_date_s3_key
            )
            and not self.overwrite
        ):
            self.stdout.write(
                f"{end_date_s3_key} already exists. Perhaps you meant to initialise with 'overwrite=True'?"
            )
            return

        csv_bytes = self.make_end_date_csv(
            review, start_date, thursday_start_day=thursday_start_day
        )
        self.stdout.write(
            f"Uploading end_date_csv to s3://{self.review_bucket}/{review.s3_end_date_key}"
        )
        self.s3_client.put_object(
            Bucket=self.review_bucket,
            Key=end_date_s3_key,
            Body=csv_bytes,
        )

    def get_xml_link_from_eco_url(self, eco_url: str):
        """
        There's an xml data page hiding somewhere
        """

        parts = ["schedule/1", "schedule", "schedules"]
        for part in parts:
            xml_link = f"{eco_url}/{part}/made/data.xml"
            response = requests.head(xml_link, allow_redirects=True)
            if response.status_code == 200:
                return xml_link

        self.stdout.write(f"No xml data link found for {eco_url}")
        return None

    def parse_eco_xml(self, xml_link: str):
        eco_parser = EcoParser(xml_link)
        try:
            return eco_parser.parse()
        except ParseError:
            self.stdout.write(f"Could not parse eco at {xml_link}")
        return None

    def get_seats_total_from_leg_text(self, review: OrganisationBoundaryReview):
        """
        If they all have the same number of seats the count isn't included in the ward data :/
        Here are some examples of what the text looks like

        https://www.legislation.gov.uk/uksi/2021/108/made
            '(4) The number of councillors to be elected for each ward is three. '

        https://www.legislation.gov.uk/uksi/2022/967/made
            '(4) Three councillors are to be elected for each ward. '

        https://www.legislation.gov.uk/uksi/2022/1373/made
            '(4) The number of councillors to be elected for each ward is two. '

        https://www.legislation.gov.uk/uksi/2023/1205/article/3/made
            '(4) The number of councillors to be elected for each ward is the number specified in relation to that ward in the second column of the table in Schedule 1.'

        https://www.legislation.gov.uk/uksi/2015/70/made
            '(4) The number of councillors to be elected for each district ward is the number specified in relation to that ward in the second column of the table in Schedule 1. '
        """
        pass  # ToDo

    def get_base_eco_row(self, review: OrganisationBoundaryReview):
        return {
            "Start Date": "",
            "End Date": "",
            "Name": "",
            "official_identifier": "",
            "geography_curie": "",
            "seats_total": "",
            "Boundary Commission Consultation URL": review.consultation_url,
            "Legislation URL": f"{review.cleaned_legislation_url}/made",
            "Short Title": review.legislation_title,
            "Notes": "",
            "Mapit Generation URI": "",
            "Organisation ID": review.organisation.official_identifier,
            "Organisation ID type": "local-authority-eng",
        }

    def get_eco_csv_rows(self, review: OrganisationBoundaryReview):
        xml_link = self.get_xml_link_from_eco_url(
            review.cleaned_legislation_url
        )
        ward_data = self.parse_eco_xml(xml_link)
        base_eco_row = self.get_base_eco_row(review)
        if ward_data[len(ward_data) // 2] == 1:  # pick one from the middle
            base_eco_row["seats_total"] = self.get_seats_total_from_leg_text(
                review
            )
        wards = []
        for ward in ward_data:
            row = copy.deepcopy(base_eco_row)
            if (
                ward[0].startswith("(1)")
                or ward[0].startswith("Column (")
                or ward[0].startswith("Column 1")
            ):
                continue
            row["Name"] = ward[0]

            if len(ward) >= 2:
                row["seats_total"] = ward[-1]
            wards.append(row)
        return wards

    def make_eco_csv(self, review: OrganisationBoundaryReview):
        ward_rows = self.get_eco_csv_rows(review)
        buffer = StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=ward_rows[0].keys())
        writer.writeheader()
        writer.writerows(ward_rows)
        return bytes(buffer.getvalue().replace("\r\n", "\n"), encoding="utf-8")

    def upload_eco_csv_to_s3(self, review: OrganisationBoundaryReview):
        csv_bytes = self.make_eco_csv(review)
        s3_eco_key = f"{review.s3_eco_key}"
        if (
            check_s3_obj_exists(self.s3_client, self.review_bucket, s3_eco_key)
            and not self.overwrite
        ):
            self.stdout.write(
                f"s3://{self.review_bucket}/{s3_eco_key} already exists. "
                f"Perhaps you meant to initialise with 'overwrite=True'?"
            )
            return

        self.stdout.write(f"Uploading end_date_csv to {s3_eco_key}")
        self.s3_client.put_object(
            Bucket=self.review_bucket,
            Key=f"{review.s3_eco_key}",
            Body=csv_bytes,
        )
