from datetime import datetime
from django.http import Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from elections.models import Election, ElectionType, ElectionSubType
from elections.query_helpers import PostcodeError
from organisations.models import Organisation, OrganisationDivision
from .serializers import (
    ElectionSerializer,
    ElectionTypeSerializer,
    ElectionSubTypeSerializer,
    OrganisationSerializer,
    OrganisationDivisionSerializer,
    OrganisationGeoSerializer,
    ElectionGeoSerializer,
)


class APIPostcodeException(APIException):
    status_code = 400
    default_detail = "Invalid postcode"
    default_code = "invalid_postcode"


class APICoordsException(APIException):
    status_code = 400
    default_detail = "Invalid co-ordinates"
    default_code = "invalid_coords"


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Election.public_objects.all()
    serializer_class = ElectionSerializer
    lookup_field = "election_id"
    lookup_value_regex = r"(?!\.json$)[^/]+"
    filterset_fields = ("group_type", "poll_open_date")

    @action(detail=True, url_path="geo")
    def geo(self, request, election_id=None, format=None):
        election = self.get_queryset().get(election_id=election_id)
        return Response(
            ElectionGeoSerializer(election, context={"request": request}).data
        )

    def get_queryset(self):
        queryset = Election.public_objects.all()
        if self.request.query_params.get("deleted", None):
            queryset = Election.private_objects.all().filter_by_status("Deleted")

        postcode = self.request.query_params.get("postcode", None)
        if postcode is not None:
            try:
                queryset = queryset.for_postcode(postcode)
            except PostcodeError:
                raise APIPostcodeException()

        coords = self.request.query_params.get("coords", None)
        if coords is not None:
            try:
                lat, lng = map(float, coords.split(","))
            except ValueError:
                raise APICoordsException()
            queryset = queryset.for_lat_lng(lat=lat, lng=lng)

        current = self.request.query_params.get("current", None)
        if current is not None:
            queryset = queryset.current()

        future = self.request.query_params.get("future", None)
        if future is not None:
            queryset = queryset.future()

        with_metadata = self.request.query_params.get("metadata", None)
        if with_metadata is not None:
            queryset = queryset.exclude(metadata=None)

        queryset = queryset.select_related(
            "election_type", "organisation", "elected_role", "division"
        )

        return queryset


class ElectionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectionType.objects.all()
    lookup_field = "election_type"
    serializer_class = ElectionTypeSerializer


class ElectionSubTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectionSubType.objects.all()
    serializer_class = ElectionSubTypeSerializer


class OrganisationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer

    def get_object(self, **kwargs):
        kwargs["date"] = datetime.strptime(kwargs["date"], "%Y-%m-%d").date()
        try:
            return Organisation.objects.all().get_by_date(**kwargs)
        except Organisation.DoesNotExist:
            raise Http404()

    @action(detail=True, url_path="geo")
    def geo(self, request, **kwargs):
        kwargs.pop("format", None)
        org = self.get_object(**kwargs)
        serializer = OrganisationGeoSerializer(
            org, read_only=True, context={"request": request}
        )
        return Response(serializer.data)

    def retrieve(self, request, **kwargs):
        kwargs.pop("format", None)
        org = self.get_object(**kwargs)
        serializer = OrganisationSerializer(
            org, read_only=True, context={"request": request}
        )
        return Response(serializer.data)

    def filter(self, request, **kwargs):
        kwargs.pop("format", None)
        orgs = Organisation.objects.all().filter(**kwargs)

        page = self.paginate_queryset(orgs)
        if page is not None:
            return self.get_paginated_response(
                OrganisationSerializer(
                    page, many=True, read_only=True, context={"request": request}
                ).data
            )

        return Response(
            OrganisationSerializer(
                orgs, many=True, read_only=True, context={"request": request}
            ).data
        )


class OrganisationDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrganisationDivision.objects.all()
    serializer_class = OrganisationDivisionSerializer
