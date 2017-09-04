from datetime import datetime

from .base import BaseSnooper
from election_snooper.models import SnoopedElection
import re

class LibDemNewbiesScraper(BaseSnooper):
    snooper_name = "LibDemNewbies"
    base_url = "http://libdemnewbies.org.uk/"

    def get_all(self):
        url = "{}elections/forthcoming-by-elections/".format(self.base_url)
        print(url)
        soup = self.get_soup(url)
        wrapper = soup.find('section', {'class': 'av_textblock_section'})

        for index, tile in enumerate(wrapper.find_all('p')):
            title = tile.find('strong')

            if not title:
                title = tile.text.split("\n")[0]
            else:
                title = title.text

            content = tile.text

            if 'cause' in content.lower():
                try:
                    cause = re.match(
                        ".*\n(\S+) seat. [cC]ause: (\S+)\n.*", content).group(2)
                except AttributeError:
                    cause = "unknown"
            else:
                cause = "unknown"

            data = {
                'title': title,
                'source': url,
                'cause': cause,
                'detail': content,
                'snooper_name': self.snooper_name,
            }
            try:
                data['date'] = datetime.strptime(
                    tile.find_previous_sibling('h3').text, "%d/%m/%Y")
                datef = data['date'].strftime('%Y-%m-%d')
            except ValueError:
                datef = tile.find_previous_sibling('h3').text

            specific_url= "%s#%s-%s" % (
                url,
                title.lower().replace(' ','-'),
                datef
            )

            item, created = SnoopedElection.objects.update_or_create(
                snooper_name=self.snooper_name,
                detail_url=specific_url,
                defaults=data
            )

            if created:
                self.post_to_slack(item)