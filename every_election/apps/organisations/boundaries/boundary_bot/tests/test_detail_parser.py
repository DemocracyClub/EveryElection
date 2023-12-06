import os

from django.test import TestCase
from organisations.boundaries.boundary_bot.spider import LgbceSpider
from scrapy.http import Request, TextResponse


def mock_response(file_name, url):
    request = Request(url=url)
    dirname = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(os.path.join(dirname, file_name))

    with open(file_path, "r") as f:
        file_content = bytes(f.read(), "utf-8")

    return TextResponse(url=url, request=request, body=file_content)


class DetailParserTest(TestCase):
    def test_no_eco_with_shapefiles(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/no_eco.html",
            "https://www.lgbce.org.uk/all-reviews/calderdale",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("calderdale", result[0]["slug"])
        self.assertEqual("Consultation on proposals", result[0]["latest_event"])
        self.assertIsNone(result[0]["legislation_title"])
        self.assertIsNone(result[0]["legislation_url"])
        self.assertEqual(0, result[0]["legislation_made"])
        self.assertEqual(
            "/sites/default/files/2023-10/calderdale_draftrecs.zip",
            result[0]["boundaries_url"],
        )

    def test_with_eco_and_shapefiles(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/with_eco_and_shapefiles.html",
            "https://www.lgbce.org.uk/all-reviews/fareham",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("fareham", result[0]["slug"])
        self.assertEqual(
            "Making our recommendation into law",
            result[0]["latest_event"],
        )
        self.assertEqual(
            "The Fareham (Electoral Changes) Order 2023",
            result[0]["legislation_title"],
        )
        self.assertEqual(
            "http://www.legislation.gov.uk/id/uksi/2023/796",
            result[0]["legislation_url"],
        )
        self.assertEqual(1, result[0]["legislation_made"])
        self.assertEqual(
            "/sites/default/files/2023-02/onedrive_1_06-02-2023.zip",
            result[0]["boundaries_url"],
        )

    def test_made_eco(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/made_eco.html",
            "https://www.lgbce.org.uk/all-reviews/allerdale",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("allerdale", result[0]["slug"])
        self.assertEqual(
            "Effective date",
            result[0]["latest_event"],
        )

        self.assertEqual(
            "The Allerdale (Electoral Changes) Order 2017",
            result[0]["legislation_title"],
        )
        self.assertEqual(
            "https://www.legislation.gov.uk/uksi/2017/1067/contents/made",
            result[0]["legislation_url"],
        )
        self.assertEqual(1, result[0]["legislation_made"])
        self.assertIsNone(result[0]["boundaries_url"])

    def test_no_matches(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/no_matches.html",
            "https://www.lgbce.org.uk/all-reviews/west-yorkshire",
        )
        result = list(spider.parse(fixture))
        # response contains nothing we are looking for
        self.assertEqual(0, len(result))
