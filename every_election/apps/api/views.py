from collections import OrderedDict

from api import filters
from core.helpers import parse_url_date
from django.conf import settings
from django.db.models import Prefetch
from django.http import Http404, HttpResponseRedirect
from elections.models import (
    Election,
    ElectionSubType,
    ElectionType,
    ModerationStatuses,
)
from elections.query_helpers import PostcodeError
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from uk_election_ids.election_ids import validate

from .serializers import (
    DivisionSetSerializer,
    DivisionSetSummarySerializer,
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
            # needed to build the URL of the ballot's division set
            "division__divisionset__organisation",
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
            if identifier_type and identifier_type != "ballot":
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
        resp = super().retrieve(request, *args, **kwargs)
        if not settings.DEBUG:
            resp["Cache-Control"] = "s-maxage=7200 stale-if-error=86400"
        return resp

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
    queryset = Organisation.public_objects.all()
    serializer_class = OrganisationSerializer
    filterset_fields = ["modified"]

    def get_object(self, **kwargs):
        kwargs["date"] = parse_url_date(kwargs["date"])
        try:
            return self.queryset.get_by_date(**kwargs)
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
                "division__divisionset__organisation",
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
        orgs = self.queryset.filter(**kwargs)

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


class DivisionSetViewSet(viewsets.GenericViewSet):
    """
    Division sets keyed by:
        `(organisation_type, official_identifier, organisation date, divisionset date)`

    This is the organisation natural key + date for the division set. Since there is
    only ever one division set active for each organisation this is also a natural key
    for division sets.

    URLs in responses will always use the start date of the organisation and
    divisionset. But neither date _has_ to be the start date.
    The organisation and division set active on the given dates will be returned.
    """

    # The routes nested under an organisation look it up with
    # Organisation.public_objects, which excludes provisional
    # organisations. The flat list needs the same filter to make sure we
    # don't return their division sets.
    queryset = OrganisationDivisionSet.objects.filter(
        organisation__provisional=False
    ).select_related("organisation")
    serializer_class = DivisionSetSummarySerializer
    # Only used by list(). The routes nested under an organisation don't
    # call filter_queryset().
    filterset_class = filters.DivisionSetFilter

    def list(self, request, **kwargs):
        """
        All division sets, newest first.

        `date`, `active` and `future` can't be combined with each other.
        """
        # Many division sets share a start date, so order by primary key
        # as well to keep the order the same from one page to the next.
        queryset = self.filter_queryset(self.get_queryset()).order_by(
            "-start_date", "pk"
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_organisation(self) -> Organisation:
        try:
            return Organisation.public_objects.get_by_date(
                organisation_type=self.kwargs["organisation_type"],
                official_identifier=self.kwargs["official_identifier"],
                date=parse_url_date(self.kwargs["date"]),
            )
        except Organisation.DoesNotExist:
            raise Http404()

    def get_object(self) -> OrganisationDivisionSet:
        organisation = self.get_organisation()
        try:
            # The related manager sets each division set's `organisation`
            # to this instance, so building its URL doesn't fetch it again.
            return organisation.divisionset.filter_by_date(
                parse_url_date(self.kwargs["divset_date"])
            ).get()
        except OrganisationDivisionSet.DoesNotExist:
            raise Http404()

    def organisation_list(self, request, **kwargs):
        """
        The division sets of one organisation.
        """
        queryset = (
            self.get_queryset()
            .filter(organisation=self.get_organisation())
            .order_by("-start_date")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def organisation_detail(self, request, **kwargs):
        context = self.get_serializer_context()
        context["division_type"] = request.query_params.get("division_type")
        serializer = DivisionSetSerializer(self.get_object(), context=context)
        return Response(serializer.data)

    def pmtiles(self, request, **kwargs):
        """
        Redirect to the PMTiles file containing the geographies of the
        division set's divisions.

        The redirect is temporary because the file name contains a hash
        of the division set's contents so could change.
        """
        divisionset = self.get_object()
        # has_pmtiles_file makes a request to S3 in production. That is
        # fine for one object, but don't call it for each row of a list.
        if not divisionset.has_pmtiles_file:
            raise Http404("This division set has no PMTiles file")
        return HttpResponseRedirect(divisionset.pmtiles_source_url)
