import json
import os
import re

import requests
import scrapy
import tempfile
from scrapy.crawler import CrawlerProcess
from organisations.boundaries.boundary_bot.common import (
    is_eco,
    START_PAGE,
    REQUEST_HEADERS,
)


class LgbceSpider(scrapy.Spider):
    name = "reviews"
    custom_settings = {
        "CONCURRENT_REQUESTS": 5,  # keep the concurrent requests low
        "DOWNLOAD_DELAY": 0.25,  # throttle the crawl speed a bit
        "COOKIES_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
        "FEED_FORMAT": "json",
        "DEFAULT_REQUEST_HEADERS": REQUEST_HEADERS,
    }
    allowed_domains = ["lgbce.org.uk"]
    start_urls = [START_PAGE]

    def get_shapefiles(self, response):
        # find any links to zip files in the page
        zipfiles = response.xpath(
            "/html/body//a[contains(@href,'.zip')]/@href"
        ).extract()

        zipfiles = list(set(zipfiles))
        if len(zipfiles) == 1:
            # if we found exactly one link to a zipfile,
            # assume that's what we're looking for
            return zipfiles[0]

        # Try being more specific
        zipfiles = response.xpath(
            "//a[contains(.,' ')][contains(@href,'inal')]/@href"
        ).extract()

        if len(zipfiles) == 1:
            return zipfiles[0]

        return None

    def get_made_link_from_draft_link(self, draft_link):
        r = requests.get(draft_link)
        rel_link = re.search(
            r"(wsi|uksi)\/\d+\/\d+\/(contents\/)?made", str(r.content)
        )
        if rel_link:
            return "https://www.legislation.gov.uk/{}".format(rel_link.group())
        else:
            return None

    def get_legislation(self, response):
        # find any links to legislation.gov.uk in the pagec
        legislation_links = response.xpath(
            "/html/body//a[contains(@href,'legislation.gov.uk')]/@href"
        ).extract()

        made_links = [
            x for x in list(set(legislation_links)) if x.endswith("/made")
        ]
        draft_links = [x for x in list(set(legislation_links)) if "dsi" in x]
        if len(made_links) == 1:
            # if we found exactly link to a made order,
            # assume that's what we're looking for
            return made_links[0]
        elif len(draft_links) == 1:
            return self.get_made_link_from_draft_link(draft_links[0])
        return None

    def parse(self, response):
        tabs = response.css("div.field--name-field-accordion-title")
        if tabs:
            title = tabs[0].xpath("text()").extract_first().strip()
            rec = {
                "slug": response.url.split("/")[-1],
                "latest_event": title,
                "shapefiles": self.get_shapefiles(response),
                "eco": None,
                "eco_made": 0,
            }

            # try to work out if the ECO is 'made'
            eco_made_text_1 = "have now successfully completed a "
            eco_made_text_2 = "scrutiny and will come into "
            div = (
                response.css("div.field--name-field-accordion-body")
                .extract_first()
                .lower()
                .replace("\xa0", " ")
            )

            if (
                is_eco(title)
                and eco_made_text_1 in div
                and eco_made_text_2 in div
            ):
                rec["eco_made"] = 1

                rec["eco"] = self.get_legislation(response)

            yield rec

        for next_page in response.css("ul > li > div > span > a"):
            if "all-reviews" in next_page.extract():
                yield response.follow(next_page, self.parse)


class SpiderWrapper:
    # Wrapper class that allows us to run a scrapy spider
    # and return the result as a list

    def __init__(self, spider):
        self.spider = spider

    def run_spider(self):
        # Scrapy likes to dump its output to file
        # so we will write it out to a file and read it back in.
        # The 'proper' way to do this is probably to write a custom Exporter
        # but this will do for now

        tmpfile = tempfile.NamedTemporaryFile().name

        process = CrawlerProcess(
            {
                "FEED_URI": tmpfile,
            }
        )
        process.crawl(self.spider)
        process.start()

        results = json.load(open(tmpfile))

        os.remove(tmpfile)

        return results
