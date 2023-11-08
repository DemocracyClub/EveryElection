import json
import lxml.html
import pprint
import requests
from collections import OrderedDict
from organisations.boundaries.boundary_bot.code_matcher import CodeMatcher
from organisations.boundaries.boundary_bot.common import (
    BASE_URL,
    START_PAGE,
    REQUEST_HEADERS,
    SLACK_WEBHOOK_URL,
    GITHUB_API_KEY,
    is_eco,
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
from organisations.models import OrganisationBoundaryReview


class ScraperException(Exception):
    pass


class LgbceScraper:

    """
    Scraper for The Local Government Boundary Commission for England's website

    By scraping the LGBCE website we can:
    - Discover boundary reviews
    - Detect when the status of a review has been updated
    - Send Slack messages and raise GitHub issues
      based on events in the boundary review process
    """

    CURRENT_LABEL = "Current Reviews"
    COMPLETED_LABEL = "Recent Reviews"
    TABLE_NAME = "lgbce_reviews"

    def __init__(self, BOOTSTRAP_MODE, SEND_NOTIFICATIONS):
        self.data = {}
        self.code_matcher = CodeMatcher()
        self.slack_helper = SlackHelper()
        self.github_helper = GitHubIssueHelper()
        self.BOOTSTRAP_MODE = BOOTSTRAP_MODE
        self.SEND_NOTIFICATIONS = SEND_NOTIFICATIONS

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
                slug = url.split("/")[-1]
                self.data[slug] = {
                    "slug": slug,
                    "name": link.text.strip(),
                    "register_code": None,
                    "url": url,
                    "status": None,
                    "latest_event": None,
                    "shapefiles": None,
                    "eco": None,
                    "eco_made": 0,
                }

    def attach_spider_data(self):
        wrapper = SpiderWrapper(LgbceSpider)
        review_details = wrapper.run_spider()
        for area in review_details:
            if area["slug"] not in self.data:
                raise ScraperException(
                    "Unexpected slug: Found '%s', expected %s"
                    % (area["slug"], str([rec for rec in self.data]))
                )
            self.data[area["slug"]]["latest_event"] = area["latest_event"]
            self.data[area["slug"]]["shapefiles"] = area["shapefiles"]
            self.data[area["slug"]]["eco"] = area["eco"]
            self.data[area["slug"]]["eco_made"] = area["eco_made"]

    def attach_register_codes(self):
        for key, record in self.data.items():
            code, *_ = self.code_matcher.get_register_code(record["name"])
            record["register_code"] = code

    def validate(self):
        # perform some consistency checks
        # and raise an error if unexpected things have happened
        for key, record in self.data.items():
            if self.BOOTSTRAP_MODE:
                # skip all the checks if we are initializing an empty DB
                return True

            result = OrganisationBoundaryReview.objects.filter(
                slug=record["slug"]
            )

            if len(result) == 0 and record["status"] == self.COMPLETED_LABEL:
                # we shouldn't have found a record for the first time when it is completed
                # we should find it under review and then it should move to completed
                raise ScraperException(
                    "New record found but status is '%s':\n%s"
                    % (self.COMPLETED_LABEL, str(record))
                )

            if (
                len(result) == 1
                and record["latest_event"] is None
                and result[0]["latest_event"] != ""
            ):
                # the review isn't brand new and we've failed to scrape the latest review event
                raise ScraperException(
                    "Failed to populate 'latest_event' field:\n%s"
                    % (str(record))
                )

            if (
                len(result) == 1
                and record["status"] == self.CURRENT_LABEL
                and result[0]["status"] == self.COMPLETED_LABEL
            ):
                # reviews shouldn't move backwards from completed to current
                raise ScraperException(
                    "Record status has changed from '%s' to '%s':\n%s"
                    % (self.COMPLETED_LABEL, self.CURRENT_LABEL, str(record))
                )

            if (
                len(result) == 1
                and record["eco_made"] == 0
                and result[0]["eco_made"] == 1
            ):
                # reviews shouldn't move backwards from made to not made
                raise ScraperException(
                    "'eco_made' field has changed from 1 to 0:\n%s"
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
            result = OrganisationBoundaryReview.objects.filter(
                slug=record["slug"]
            )

            if len(result) == 0:
                # we've not seen this boundary review before
                self.slack_helper.append_new_review_message(record)

            if len(result) == 1:
                # we've already got our eye on this one
                if (
                    record["status"] == self.COMPLETED_LABEL
                    and result[0]["status"] != self.COMPLETED_LABEL
                ):
                    self.slack_helper.append_completed_review_message(record)
                    self.github_helper.append_completed_review_issue(record)
                if result[0]["latest_event"] != record["latest_event"]:
                    self.slack_helper.append_event_message(record)

    def save(self):
        for key, record in self.data.items():
            scraperwiki.sqlite.save(
                unique_keys=["slug"], data=record, table_name=self.TABLE_NAME
            )

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
        if GITHUB_API_KEY:
            self.github_helper.raise_issues()

    def cleanup(self):
        # remove any stale records from the DB
        if not self.data:
            return
        placeholders = "(" + ", ".join(["?" for rec in self.data]) + ")"
        result = scraperwiki.sql.execute(
            ("DELETE FROM %s WHERE slug NOT IN " + placeholders)
            % (self.TABLE_NAME),
            [slug for slug in self.data],
        )

    def dump_table_to_json(self):
        records = scraperwiki.sqlite.select(
            " * FROM %s ORDER BY slug;" % (self.TABLE_NAME)
        )
        return json.dumps(
            [OrderedDict(sorted(rec.items())) for rec in records],
            sort_keys=True,
            indent=4,
        )

    def sync_db_to_github(self):
        if GITHUB_API_KEY:
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
        self.cleanup()
        self.sync_db_to_github()
