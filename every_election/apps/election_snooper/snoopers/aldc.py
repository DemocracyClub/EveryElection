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
        wrapper = soup.find('section', {'class': 'mod-tile-wrap'})
        for tile in wrapper.find_all('div', {'class': 'tile'}):

            title = tile.find(
                'div', {'class': 'election-heading'}).text.strip()
            detail_url = tile.find(
                'div', {'class': 'election-heading'}).a['href'].strip()
            content = tile.find(
                'div', {'class': 'election-content'}).find_all('p')
            date = datetime.strptime(content[0].strong.text, "%B %d, %Y")

            # print(content[0].text)
            seat_control, cause = content[1].text.lower().split('cause')
            cause = cause.split('\n')[0].strip(": .")
            data = {
                'title': title,
                'source': url,
                'date': date,
                'cause': cause,
                'detail': "\n".join([x.text for x in content]),
                'snooper_name': self.snooper_name,
                'status': 'new',
            }
            item, created = SnoopedElection.objects.update_or_create(
                snooper_name=self.snooper_name,
                detail_url=detail_url,
                defaults=data
            )
            if created:
                self.post_to_slack(item)
