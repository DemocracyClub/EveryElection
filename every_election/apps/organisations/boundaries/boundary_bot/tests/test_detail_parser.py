import os
import unittest
from scrapy.http import TextResponse, Request
from boundary_bot.spider import LgbceSpider


def mock_response(file_name, url):
    request = Request(url=url)
    dirname = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(os.path.join(dirname, file_name))

    file_content = bytes(open(file_path, "r").read(), "utf-8")

    response = TextResponse(url=url, request=request, body=file_content)
    return response


class DetailParserTest(unittest.TestCase):
    def test_no_eco(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/no_eco.html",
            "http://www.lgbce.org.uk/current-reviews/eastern/suffolk/babergh",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("babergh", result[0]["slug"])
        self.assertEqual(
            "Consultation on draft recommendations", result[0]["latest_event"]
        )
        self.assertIsNone(result[0]["eco"])
        self.assertEqual(0, result[0]["eco_made"])
        self.assertIsNone(result[0]["shapefiles"])

    def test_with_eco_and_shapefiles(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/with_eco_and_shapefiles.html",
            "http://www.lgbce.org.uk/current-reviews/south-west/gloucestershire/tewkesbury",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("tewkesbury", result[0]["slug"])
        self.assertEqual(
            "The Tewkesbury (Electoral Changes) Order 2018 (Draft)",
            result[0]["latest_event"],
        )
        self.assertIsNone(result[0]["eco"])
        self.assertEqual(0, result[0]["eco_made"])
        self.assertEqual(
            "http://s3-eu-west-2.amazonaws.com/lgbce/__data/assets/file/0005/35906/Tewkesbury_final_proposals.zip",
            result[0]["shapefiles"],
        )

    def test_made_eco(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/made_eco.html",
            "http://www.lgbce.org.uk/current-reviews/yorkshire-and-the-humber/west-yorkshire/leeds",
        )
        result = list(spider.parse(fixture))
        self.assertEqual(1, len(result))
        self.assertEqual("leeds", result[0]["slug"])
        self.assertEqual(
            "The Leeds (Electoral Changes) Order 2017",
            result[0]["latest_event"],
        )
        self.assertEqual(
            "http://www.legislation.gov.uk/uksi/2017/1077/contents/made",
            result[0]["eco"],
        )
        self.assertEqual(1, result[0]["eco_made"])
        self.assertIsNone(result[0]["shapefiles"])

    def test_no_matches(self):
        spider = LgbceSpider()
        fixture = mock_response(
            "fixtures/detail/no_matches.html",
            "http://www.lgbce.org.uk/current-reviews/yorkshire-and-the-humber/west-yorkshire",
        )
        result = list(spider.parse(fixture))
        # response contains nothing we are looking for
        self.assertEqual(0, len(result))
