from datetime import datetime, timedelta

from django.db import models
from django.contrib.gis.geos import Point
from elections.query_helpers import get_point_from_postcode


class ElectionManager(models.QuerySet):

    def for_point(self, point):
        return self.filter(geography__geography__contains=point)

    def for_lat_lng(self, lat, lng):
        point = Point(lng, lat)
        return self.for_point(point)

    def for_postcode(self, postcode):
        point = get_point_from_postcode(postcode)
        return self.for_point(point)

    def current(self):
        """
        For the moment, we'll just define 'current' and any election
        with a poll date greater than 30 days ago.
        # TODO replace this with a current status of the election model
        """
        recent_past = datetime.today() - timedelta(days=30)
        return self.filter(poll_open_date__gt=recent_past)

    def future(self):
        return self.filter(poll_open_date__gte=datetime.today())
