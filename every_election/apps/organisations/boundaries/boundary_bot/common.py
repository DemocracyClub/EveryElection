import os


BASE_URL = "http://www.lgbce.org.uk"
START_PAGE = BASE_URL + "/all-reviews"
REQUEST_HEADERS = {"Cache-Control": "max-age=20000"}

try:
    SLACK_WEBHOOK_URL = os.environ["MORPH_BOUNDARY_BOT_SLACK_WEBHOOK_URL"]
except KeyError:
    SLACK_WEBHOOK_URL = None

try:
    GITHUB_API_KEY = os.environ["MORPH_GITHUB_ISSUE_ONLY_API_KEY"]
except KeyError:
    GITHUB_API_KEY = None


def is_eco(event):
    return "electoral change" in event.lower()
