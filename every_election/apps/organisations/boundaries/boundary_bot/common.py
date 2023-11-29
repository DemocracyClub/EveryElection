import os

import requests

BASE_URL = "http://www.lgbce.org.uk"
START_PAGE = BASE_URL + "/all-reviews"
REQUEST_HEADERS = {"Cache-Control": "max-age=20000"}

try:
    SLACK_WEBHOOK_URL = os.environ["BOUNDARY_BOT_SLACK_WEBHOOK_URL"]
except KeyError:
    SLACK_WEBHOOK_URL = None

try:
    GITHUB_ISSUE_ONLY_API_KEY = os.environ["GITHUB_ISSUE_ONLY_API_KEY"]
except KeyError:
    GITHUB_ISSUE_ONLY_API_KEY = None

try:
    GITHUB_API_KEY = os.environ["GITHUB_API_KEY"]
except KeyError:
    GITHUB_API_KEY = None


class SlackClient:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def post_message(self, message):
        requests.post(self.webhook_url, json={"text": message})

    def post_messages(self, messages):
        for message in messages:
            self.post_message(message)


class GitHubClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def raise_issue(self, owner, repo, title, body):
        url = "https://api.github.com/repos/%s/%s/issues" % (owner, repo)
        requests.post(
            url,
            json={"title": title, "body": body},
            headers={"Authorization": "token %s" % (self.api_key)},
        )


def is_eco(event):
    return "electoral change" in event.lower()
