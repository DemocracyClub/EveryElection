import warnings
import json
import textwrap

from django.conf import settings

from bs4 import BeautifulSoup
import requests


class BaseSnooper:
    def get_page(self, url):
        return requests.get(url)

    def get_soup(self, url):
        req = self.get_page(url)
        soup = BeautifulSoup(req.content, "html.parser")
        return soup

    def post_to_slack(self, item):
        if not hasattr(settings, 'SLACK_WEBHOOK_URL'):
            warnings.warn("settings.SLACK_WEBHOOK_URL is not set")
            return

        text = """
        Possible new election found: {}\n
        <https://elections.democracyclub.org.uk{}>\n
        Please go and investigate!
        """.format(item.title, item.get_absolute_url())

        payload = {
            "icon_emoji": ":satellite_antenna:",
            "username": "Election Radar",
            "text": textwrap.dedent(text),
        }
        url = settings.SLACK_WEBHOOK_URL
        requests.post(url, json.dumps(payload), timeout=2)
