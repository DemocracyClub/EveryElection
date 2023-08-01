import abc
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from localflavor.gb.forms import GBPostcodeField
from uk_geo_utils.geocoders import OnspdGeocoder

logger = logging.getLogger(__name__)


class PostcodeError(Exception):
    pass


class BasePostcodeLookup(metaclass=abc.ABCMeta):
    def __init__(self, postcode):
        self.postcode = postcode.replace(" ", "")

    @property
    @abc.abstractmethod
    def point(self):
        pass


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
    validator = GBPostcodeField()
    try:
        postcode = validator.clean(postcode)
    except ValidationError:
        raise PostcodeError("Invalid Postcode")

    methods = [ONSPDPostcodeLookup]
    for method in methods:
        try:
            return method(postcode).point
        except PostcodeError:
            continue
    raise PostcodeError
