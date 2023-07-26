from datetime import datetime

from .base import BaseSnooper
from election_snooper.models import SnoopedElection


class ALDCScraper(BaseSnooper):
    snooper_name = "ALDC"
    base_url = "https://www.aldc.org/"

    def get_all(self):
        url = "{}category/forthcoming-by-elections/".format(self.base_url)
        print(url)
        soup = self.get_soup(url)
        for tile in soup.find_all("article"):
            title = tile.find("h2").text.strip()
            detail_url = url + "#" + tile["id"]
            date = tile.find("date").text.strip()
            content = tile.find("div", {"class": ""}).find_all("p")

            if content and content[0].text.lower().count("cause") == 1:
                seat_control, cause = content[0].text.lower().split("cause")
                cause = cause.split("\n")[0].strip(": .")
            else:
                cause = "unknown"
            data = {
                "title": title,
                "source": url,
                "cause": cause,
                "detail": "\n".join([x.text for x in content]),
                "snooper_name": self.snooper_name,
            }
            try:
                data["date"] = datetime.strptime(date, "%B %d, %Y")

            item, created = SnoopedElection.objects.update_or_create(
                snooper_name=self.snooper_name,
                detail_url=detail_url,
                defaults=data,
            )
            if created:
                self.post_to_slack(item)
