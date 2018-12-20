from urllib.parse import urlencode

from django.conf import settings

from .base import BaseSnooper
from election_snooper.models import SnoopedElection


class CustomSearchScraper(BaseSnooper):
    snooper_name = "CustomSearch:NoticeOfElectionPDF"
    base_url = "https://www.googleapis.com/customsearch/v1"

    def get_all(self):
        args = {
            "key": settings.GCS_API_KEY,
            "cx": "018004400196177335143:vyu4hunm_wm",
            "q": '"notice of election"',
            "dateRestrict": "m1",
            "sort": "date",
            "fileType": "pdf",
            "cr": "uk",
        }

        url = "{}?{}".format(self.base_url, urlencode(args))
        print(url)
        req = self.get_page(url)

        for item in req.json()["items"]:
            title = item.get("title", item.get("displayLink"))
            detail_url = item["link"]
            content = item["snippet"]
            data = {
                "title": title,
                "source": url,
                "detail": content,
                "extra": item,
                "snooper_name": self.snooper_name,
            }
            item, created = SnoopedElection.objects.update_or_create(
                snooper_name=self.snooper_name, detail_url=detail_url, defaults=data
            )
            if created:
                self.post_to_slack(item)
