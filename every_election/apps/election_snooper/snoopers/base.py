from bs4 import BeautifulSoup
import requests


class BaseSnooper:
    def get_page(self, url):
        return requests.get(url)

    def get_soup(self, url):
        req = self.get_page(url)
        soup = BeautifulSoup(req.content, "html.parser")
        return soup
