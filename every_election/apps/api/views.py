from collections import OrderedDict
from datetime import datetime

from api import filters
from django.db.models import Prefetch
from django.http import Http404
from elections.models import (
    Election,
    ElectionSubType,
    ElectionType,
    ModerationStatuses,
)
from elections.query_helpers import PostcodeError
from organisations.models import Organisation, OrganisationDivision
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from uk_election_ids.election_ids import validate

from .serializers import (
    ElectionGeoSerializer,
    ElectionSerializer,
    ElectionSubTypeSerializer,
    ElectionTypeSerializer,
    OrganisationDivisionSerializer,
    OrganisationGeoSerializer,
    OrganisationSerializer,
)


class APIPostcodeException(APIException):
    status_code = 400
    default_detail = "Invalid postcode"
    default_code = "invalid_postcode"


class APICoordsException(APIException):
    status_code = 400
    default_detail = "Invalid co-ordinates"
    default_code = "invalid_coords"


class APIInvalidElectionIdException(APIException):
    status_code = 400
    default_detail = "Invalid Election ID"
    default_code = "invalid_election_id"


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Election.public_objects.all()
    serializer_class = ElectionSerializer
    lookup_field = "election_id"
    lookup_value_regex = r"(?!\.json$)[^/]+"
    filterset_class = filters.ElectionFilter

    @action(detail=True, url_path="geo")
    def geo(self, request, election_id=None, format=None):
        election = self.get_queryset().get(election_id=election_id)
        return Response(
            ElectionGeoSerializer(election, context={"request": request}).data
        )

    def get_queryset(self):
        select_related = [
            "election_type",
            "election_subtype",
            "organisation",
            "elected_role",
            "division",
            "division__divisionset",
            "group",
            "replaces",
            "metadata",
        ]

        queryset = Election.public_objects.all()
        queryset = queryset.select_related(*select_related).prefetch_related(
            "_replaced_by"
        )

        if self.request.query_params.get("deleted", None) is not None:
            queryset = (
                Election.private_objects.all()
                .select_related(*select_related)
                .filter_by_status("Deleted")
            )
        else:
            identifier_type = self.request.query_params.get(
                "identifier_type", None
            )
            if identifier_type != "ballot":
                queryset = queryset.prefetch_related(
                    Prefetch("_children_qs", Election.public_objects.all())
                )

        postcode = self.request.query_params.get("postcode", None)
        if postcode is not None:
            postcode = postcode.replace(" ", "")
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

        if self.request.query_params.get("current", None) is not None:
            queryset = queryset.current()

        if self.request.query_params.get("future", None) is not None:
            queryset = queryset.future()

        if self.request.query_params.get("metadata", None) is not None:
            queryset = queryset.exclude(metadata=None)

        identifier_type = self.request.query_params.get("identifier_type", None)
        if identifier_type is not None:
            if identifier_type == "ballot":
                queryset = queryset.filter(group_type=None)
            else:
                queryset = queryset.filter(group_type=identifier_type)
        return queryset.order_by_group_type()

    def retrieve(self, request, *args, **kwargs):
        if not validate(kwargs["election_id"]):
            raise APIInvalidElectionIdException()
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Override the base `list` method to remove pagination if we're filtering
        on `current`.

        In reality, we're unlikely to have more than the page size (100) current
        elections, however when paging we cause two duplicate queries: one for
        the count() and one for the data.

        This takes a lot of time, and we're busy people (sometimes).

        Seeing as we're iterating over the data anyawy, we can get the count
        from len(serializer.data) and add that to the page data ourselves.

        """

        queryset = self.filter_queryset(self.get_queryset())
        postcode = self.request.query_params.get("postcode", None)
        coords = self.request.query_params.get("coords", None)
        current = self.request.query_params.get("current", None)
        if (postcode or coords) and current:
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                OrderedDict(
                    [
                        ("count", len(serializer.data)),
                        ("next", None),
                        ("previous", None),
                        ("results", serializer.data),
                    ]
                )
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
    filterset_fields = ["modified"]

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

    @action(detail=True, url_path="elections")
    def elections(self, request, **kwargs):
        kwargs.pop("format", None)
        org: Organisation = self.get_object(**kwargs)
        serializer = ElectionSerializer(
            org.election_set.filter(
                current_status=ModerationStatuses.approved.value
            )
            .select_related(
                "election_type",
                "election_subtype",
                "organisation",
                "division",
                "division__divisionset",
                "elected_role",
                "explanation",
                "metadata",
                "replaces",
                "group",
            )
            .prefetch_related(
                "_replaced_by",
                Prefetch(
                    "_children_qs",
                    Election.public_objects.all(),
                    to_attr="children",
                ),
            ),
            many=True,
            read_only=True,
            context={"request": request},
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
                    page,
                    many=True,
                    read_only=True,
                    context={"request": request},
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
    filterset_fields = ["modified"]
