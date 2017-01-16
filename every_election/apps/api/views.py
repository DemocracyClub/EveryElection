from rest_framework import viewsets

from elections.models import Election, ElectionType, ElectionSubType
from organisations.models import Organisation
from .serializers import (ElectionSerializer, ElectionTypeSerializer,
                          ElectionSubTypeSerializer, OrganisationSerializer)


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    lookup_field = 'election_id'
    lookup_value_regex="(?!\.json$)[^/]+"
    filter_fields = ('group_type', )


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
