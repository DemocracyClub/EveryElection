import pprint
import re
from urllib.parse import urlparse

import lxml.html
import requests
from django.core import serializers
from organisations.boundaries.boundary_bot.code_matcher import CodeMatcher
from organisations.boundaries.boundary_bot.common import (
    BASE_URL,
    GITHUB_ISSUE_ONLY_API_KEY,
    REQUEST_HEADERS,
    SLACK_WEBHOOK_URL,
    START_PAGE,
)
from organisations.boundaries.boundary_bot.github import (
    GitHubIssueHelper,
    GitHubSyncHelper,
)
from organisations.boundaries.boundary_bot.slack import SlackHelper
from organisations.boundaries.boundary_bot.spider import (
    LgbceSpider,
    SpiderWrapper,
)
from organisations.boundaries.constants import LGBCE_SLUG_TO_ORG_SLUG
from organisations.models import Organisation, OrganisationBoundaryReview
from organisations.models.divisions import EditStatus, ReviewStatus

AMBIGUOUS_ID_MAP = {
    "SHE": 504,  # Folkestone & Hythe
}


class ScraperException(Exception):
    pass


def record_as_string(record):
    rec_str = f"{record['slug']}"
    if record["legislation_title"]:
        rec_str += f" ({record['legislation_title']})"
    if record["latest_event"]:
        rec_str += f" ({record['latest_event']})"

    return rec_str


class LgbceScraper:
    """
    Scraper for The Local Government Boundary Commission for England's website

    By scraping the LGBCE website we can:
    - Discover boundary reviews
    - Detect when the status of a review has been updated
    - Send Slack messages and raise GitHub issues
      based on events in the boundary review process
    """

    TABLE_NAME = "lgbce_reviews"

    def __init__(self, BOOTSTRAP_MODE, SEND_NOTIFICATIONS):
        self.data = {}
        self.code_matcher = CodeMatcher()
        self.slack_helper = SlackHelper()
        self.github_helper = GitHubIssueHelper()
        self.BOOTSTRAP_MODE = BOOTSTRAP_MODE
        self.SEND_NOTIFICATIONS = SEND_NOTIFICATIONS
        self.ignore = [
            # orgs that break our pipeline can be ignored here
            "plymouth",  # https://www.lgbce.org.uk/all-reviews/plymouth is a breaking edge case that because of devolution atm so we'll ignore it for now
        ]

    def scrape_index(self):
        headers = REQUEST_HEADERS
        r = requests.get(START_PAGE, headers=headers)
        return r.text

    def parse_index(self, html):
        expected_letters = list("ABCDEFGHIKLMNOPRSTUVWY")

        root = lxml.html.fromstring(html)
        letter_sections = root.cssselect("div.letter_section")
        found_letters = [
            ls.find("h3").text for ls in letter_sections if ls is not None
        ]
        if expected_letters != found_letters:
            raise ScraperException(
                "Unexpected headings: Found %s, expected %s"
                % (str(found_letters), str(expected_letters))
            )

        for letter_section in letter_sections:
            review_divs = letter_section.cssselect("div")
            # iterate over boundary reviews:
            for review in review_divs:
                link = review.find(".//a")
                url = link.get("href")
                if not url.startswith("http"):
                    url = BASE_URL + url
                lgbce_slug = url.split("/")[-1]
                try:
                    slug = LGBCE_SLUG_TO_ORG_SLUG[lgbce_slug]
                except KeyError:
                    print(f'"{lgbce_slug}":"{lgbce_slug}",')
                    # raise ScraperException(
                    #     f"LGBCE slug: {lgbce_slug} ({url}) not found in LGBCE_SLUG_TO_ORG_SLUG"
                    # )
                self.data[slug] = {
                    "slug": slug,
                    "name": link.text.strip(),
                    "register_code": None,
                    "consultation_url": url,
                    "status": None,
                    "latest_event": None,
                    "boundaries_url": None,
                    "legislation_url": None,
                    "legislation_made": 0,
                    "legislation_title": None,
                }

    def attach_spider_data(self):
        wrapper = SpiderWrapper(LgbceSpider)

        review_details = wrapper.run_spider()
        for area in review_details:
            if area["slug"] not in self.data:
                raise ScraperException(
                    "Unexpected slug: Found '%s', expected %s"
                    % (area["slug"], str(list(self.data)))
                )
            self.data[area["slug"]].update(area)

            if area["slug"] in self.ignore:
                print(
                    f"Deleting scraped data for {area['slug']} because it breaks our pipeline"
                )
                del self.data[area["slug"]]

    def attach_register_codes(self):
        codes_not_found = []
        for key, record in self.data.items():
            code, *_ = self.code_matcher.get_register_code(record["name"])
            if not code:
                codes_not_found.append(key)
            record["register_code"] = code

        for key in codes_not_found:
            print(f"Deleting scraped data for {key} because no code found")
            del self.data[key]

    def get_org_from_reg_code(self, register_code):
        try:
            org = Organisation.objects.get(official_identifier=register_code)

        except Organisation.MultipleObjectsReturned:
            if org_pk := AMBIGUOUS_ID_MAP.get(register_code):
                org = Organisation.objects.get(pk=org_pk)
            else:
                raise

        return org

    def get_review_from_db(self, record):
        if record["legislation_url"]:
            legislation_year = self.get_legislation_year(
                record["legislation_url"]
            )

            try:
                result = OrganisationBoundaryReview.objects.filter(
                    legislation_url__contains=f"/{legislation_year}/",
                    slug=record["slug"],
                )
                if len(result) == 1:
                    return result
                if len(result) > 1:
                    raise ScraperException(
                        f"More than one review found for {record['slug']} with year {legislation_year}",
                    )
            except OrganisationBoundaryReview.DoesNotExist:
                pass

        org = self.get_org_from_reg_code(record["register_code"])

        return OrganisationBoundaryReview.objects.filter(
            organisation=org, slug=record["slug"]
        ).exclude(status=ReviewStatus.COMPLETED)

    def clean_legislation_url(self, url):
        url = url.replace("/id/", "/")
        url = re.search(
            r"(?:www\.)?legislation.gov.uk/(wsi|ukdsi|uksi|ssi|ukpga)/\d+/\d+",
            url,
        ).group()
        return f"https://{url}"

    def get_legislation_year(self, url):
        try:
            cleaned_url = self.clean_legislation_url(url)
        except AttributeError:
            raise ScraperException(f"Failed to clean legislation URL: {url}")

        urlparse_result = urlparse(cleaned_url)
        path = urlparse_result.path
        return path.split("/")[2]

    def validate(self):
        # perform some consistency checks
        # and raise an error if unexpected things have happened
        for key, record in self.data.items():
            if self.BOOTSTRAP_MODE:
                # skip all the checks if we are initializing an empty DB
                return True
            result = self.get_review_from_db(record)

            if len(result) == 0 and record["status"] == ReviewStatus.COMPLETED:
                # we shouldn't have found a record for the first time when it is completed
                # we should find it under review and then it should move to completed
                raise ScraperException(
                    "New record found but status is '%s':\n%s"
                    % (ReviewStatus.COMPLETED, str(record))
                )

            if (
                len(result) == 1
                and record["latest_event"] is None
                and result[0].latest_event != ""
            ):
                # the review isn't brand new and we've failed to scrape the latest review event
                raise ScraperException(
                    "Failed to populate 'latest_event' field:\n%s"
                    % (str(record))
                )

            if (
                len(result) == 1
                and record["status"] == ReviewStatus.CURRENT
                and result[0].status == ReviewStatus.COMPLETED
            ):
                # reviews shouldn't move backwards from completed to current
                raise ScraperException(
                    "Record status has changed from '%s' to '%s':\n%s"
                    % (
                        ReviewStatus.COMPLETED,
                        ReviewStatus.CURRENT,
                        str(record),
                    )
                )

            if (
                len(result) == 1
                and record["legislation_made"] == 0
                and result[0].legislation_made == 1
            ):
                # reviews shouldn't move backwards from made to not made
                raise ScraperException(
                    "'legislation_made' field has changed from 1 to 0:\n%s"
                    % (str(record))
                )

            if len(result) > 1:
                # society has collapsed :(
                raise ScraperException(
                    "Human sacrifice, dogs and cats living together, mass hysteria!"
                )
        return True

    def pre_process(self):
        for key, record in self.data.items():
            if record["latest_event"] is None:
                record["latest_event"] = ""

    def make_notifications(self):
        for key, record in self.data.items():
            result = self.get_review_from_db(record)
            if len(result) == 0:
                # we've not seen this boundary review before
                self.slack_helper.append_new_review_message(record)

            if len(result) == 1:
                # we've already got our eye on this one
                if (
                    record["status"] == ReviewStatus.COMPLETED
                    and result[0].status != ReviewStatus.COMPLETED
                    and result[0].edit_status == EditStatus.UNLOCKED
                ):
                    self.slack_helper.append_completed_review_message(record)
                    self.github_helper.append_completed_review_issue(record)

                if (
                    result[0].latest_event != record["latest_event"]
                    and result[0].edit_status == EditStatus.UNLOCKED
                ):
                    self.slack_helper.append_event_message(record)

    def save(self):
        field_names = [f.name for f in OrganisationBoundaryReview._meta.fields]
        for key, record in self.data.items():
            result = self.get_review_from_db(record)
            if len(result) == 0:
                print(
                    f"Creating a new boundary review object for {record_as_string(record)}"
                )
                record["organisation"] = self.get_org_from_reg_code(
                    record["register_code"]
                )
                OrganisationBoundaryReview.objects.create(
                    **{
                        k: v
                        for k, v in record.items()
                        if k in field_names and v
                    }
                )

            if (
                len(result) == 1
                and result[0].edit_status == EditStatus.UNLOCKED
            ):
                update_fields = {
                    k: v for k, v in record.items() if k in field_names and v
                }
                for field, value in update_fields.items():
                    if value and getattr(result[0], field) != value:
                        print(
                            f"Updating {result[0]} with {record_as_string(record)}"
                        )
                        result.update(**update_fields)
                        break

    def send_notifications(self):
        # write the notifications we've generated to
        # send to the console as well for debug purposes
        pp = pprint.PrettyPrinter(indent=2)
        print("Slack messages:")
        print("----")
        pp.pprint(self.slack_helper.messages)
        print("Github issues:")
        print("----")
        pp.pprint(self.github_helper.issues)

        if not self.SEND_NOTIFICATIONS:
            return

        if SLACK_WEBHOOK_URL:
            self.slack_helper.post_messages()
        if GITHUB_ISSUE_ONLY_API_KEY:
            self.github_helper.raise_issues()

    def dump_table_to_json(self):
        records = OrganisationBoundaryReview.objects.all().order_by("slug")
        return serializers.serialize("json", records, indent=4)

    def sync_db_to_github(self):
        if GITHUB_ISSUE_ONLY_API_KEY:
            content = self.dump_table_to_json()
            g = GitHubSyncHelper()
            g.sync_file_to_github("lgbce.json", content)

    def scrape(self):
        self.parse_index(self.scrape_index())
        self.attach_spider_data()
        self.attach_register_codes()
        self.validate()
        self.pre_process()
        self.make_notifications()
        self.save()
        self.send_notifications()
        self.sync_db_to_github()
