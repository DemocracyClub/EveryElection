import requests
from bs4 import BeautifulSoup
from election_snooper.helpers import post_to_slack


class BaseSnooper:
    def get_page(self, url):
        return requests.get(url)

    def get_soup(self, url):
        req = self.get_page(url)
        return BeautifulSoup(req.content, "html.parser")

    def post_to_slack(self, item):
        message = """
        Possible new election found: {}\n
        <https://elections.democracyclub.org.uk{}>\n
        Please go and investigate!
        """.format(item.title, item.get_absolute_url())

        post_to_slack(message)
