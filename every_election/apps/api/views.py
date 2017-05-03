from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from elections.models import Election, ElectionType, ElectionSubType
from elections.query_helpers import PostcodeError
from organisations.models import Organisation, OrganisationDivision
from .serializers import (ElectionSerializer, ElectionTypeSerializer,
                          ElectionSubTypeSerializer, OrganisationSerializer,
                          OrganisationDivisionSerializer,
                          OrganisationGeoSerializer)


class APIPostcodeException(APIException):
    status_code = 400
    default_detail = 'Invalid postcode'
    default_code = 'invalid_postcode'


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    lookup_field = 'election_id'
    lookup_value_regex="(?!\.json$)[^/]+"
    filter_fields = ('group_type', 'poll_open_date')

    def get_queryset(self):
        queryset = Election.objects.all()
        postcode = self.request.query_params.get('postcode', None)
        if postcode is not None:
            try:
                queryset = queryset.for_postcode(postcode)
            except PostcodeError:
                raise APIPostcodeException()

        coords = self.request.query_params.get('coords', None)
        if coords is not None:
            lat, lng = map(float, coords.split(','))
            queryset = queryset.for_lat_lng(lat=lat, lng=lng)

        current = self.request.query_params.get('current', None)
        if current is not None:
            queryset = queryset.current()

        future = self.request.query_params.get('future', None)
        if future is not None:
            queryset = queryset.future()

        return queryset


class ElectionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectionType.objects.all()
    lookup_field = 'election_type'
    serializer_class = ElectionTypeSerializer


class ElectionSubTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectionSubType.objects.all()
    serializer_class = ElectionSubTypeSerializer


class OrganisationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    lookup_field = 'official_identifier'

    @detail_route(url_path='geo')
    def geo(self, request, official_identifier=None, format=None):
        org = Organisation.objects.get(official_identifier=official_identifier)

        return Response(
            OrganisationGeoSerializer(org, context={'request': request}).data)


class OrganisationDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrganisationDivision.objects.all()
    serializer_class = OrganisationDivisionSerializer
