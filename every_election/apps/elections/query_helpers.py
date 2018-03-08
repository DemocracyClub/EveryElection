import abc
import requests

from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist

from uk_geo_utils.geocoders import OnspdGeocoder

class PostcodeError(Exception):
    pass


class BasePostcodeLookup(metaclass=abc.ABCMeta):
    def __init__(self, postcode):
        self.postcode = postcode.replace(' ', '')

    @property
    @abc.abstractmethod
    def point(self):
        pass


class BaseMaPitPostcodeLookup(BasePostcodeLookup, metaclass=abc.ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_from_mapit()

    @property
    @abc.abstractmethod
    def mapit_base(self):
        pass

    def fetch_from_mapit(self):
        if hasattr(self, 'mapit_data'):
            return self.mapit_data

        req = requests.get("{}/postcode/{}".format(
            self.mapit_base,
            self.postcode
        ))
        if req.status_code != 200:
            raise PostcodeError
        self.mapit_data = req.json()
        return self.mapit_data

    @property
    def point(self):
        if not 'wgs84_lon' in self.mapit_data:
            raise PostcodeError
        return Point(
            self.mapit_data['wgs84_lon'],
            self.mapit_data['wgs84_lat']
        )


class mySocietyMapitPostcodeLookup(BaseMaPitPostcodeLookup):
    mapit_base = "https://mapit.mysociety.org/"


class ONSPDPostcodeLookup(BasePostcodeLookup):
    def __init__(self, postcode):
        try:
            self.geocoder = OnspdGeocoder(postcode)
        except ObjectDoesNotExist:
            raise PostcodeError("No location information")

    @property
    def point(self):
        centre = self.geocoder.centroid
        if not centre:
            raise PostcodeError("No location information")
        return centre


def get_point_from_postcode(postcode):
    postcode = postcode.upper()
    methods = [
        ONSPDPostcodeLookup,
        mySocietyMapitPostcodeLookup,
    ]
    for method in methods:
        try:
            return method(postcode).point
        except PostcodeError:
            continue
    raise PostcodeError
