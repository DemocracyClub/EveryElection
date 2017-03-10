from rest_framework import viewsets

from elections.models import Election, ElectionType, ElectionSubType
from organisations.models import Organisation, OrganisationDivision
from .serializers import (ElectionSerializer, ElectionTypeSerializer,
                          ElectionSubTypeSerializer, OrganisationSerializer,
                          OrganisationDivisionSerializer)


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
           queryset = queryset.for_postcode(postcode)

       coords = self.request.query_params.get('coords', None)
       if coords is not None:
           lat, lng = map(float,coords.split(','))
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

class OrganisationDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrganisationDivision.objects.all()
    serializer_class = OrganisationDivisionSerializer
