from datetime import datetime

from .base import BaseSnooper
from election_snooper.models import SnoopedElection
import re

class LibDemNewbiesScraper(BaseSnooper):
    snooper_name = "LibDemNewbies"
    base_url = "http://libdemnewbies.org.uk/"

    def get_all(self):
        url = "{}elections/forthcoming-by-elections/".format(self.base_url)
        soup = self.get_soup(url)
        wrapper = soup.find('section', {'class': 'av_textblock_section'})

        for index, tile in enumerate(wrapper.find_all('p')):
            title = tile.find('strong')

            if not title:
                title = tile.text.split("\n")[0]
            else:
                title = title.text

            content = tile.text
            cause = re.match(".*\n(\S+) seat. [cC]ause: (\S+)\n.*", content).group(2)
            date = datetime.strptime(tile.find_previous_sibling('h3').text, "%d/%m/%Y")

            data = {
                'title': title,
                'source': url,
                'date': date,
                'cause': cause,
                'detail': content,
                'snooper_name': self.snooper_name,
            }

            item, created = SnoopedElection.objects.update_or_create(
                snooper_name=self.snooper_name,
                detail_url=self.base_url,
                defaults=data
            )

            if created:
                self.post_to_slack(item)