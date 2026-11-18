from elections.models import (
    Election,
    ElectionSubType,
    ElectionType,
    ModerationStatuses,
)
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer,
    GeometrySerializerMethodField,
)
from uk_election_ids.datapackage import VOTING_SYSTEMS


class OrganisationHyperlinkedIdentityField(
    serializers.HyperlinkedIdentityField
):
    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        return self.reverse(
            view_name,
            kwargs={
                "organisation_type": obj.organisation_type,
                "official_identifier": obj.official_identifier,
                "date": obj.start_date,
            },
            request=request,
            format=format,
        )


org_fields = (
    "url",
    "official_identifier",
    "organisation_type",
    "organisation_subtype",
    "official_name",
    "common_name",
    "slug",
    "territory_code",
    "election_name",
    "start_date",
    "end_date",
    "created",
    "modified",
)


class OrganisationSerializer(serializers.ModelSerializer):
    url = OrganisationHyperlinkedIdentityField(
        view_name="api:organisation-detail", read_only=True
    )

    class Meta:
        model = Organisation
        fields = org_fields


class OrganisationGeoSerializer(GeoFeatureModelSerializer):
    geography_model = GeometrySerializerMethodField()
    url = OrganisationHyperlinkedIdentityField(
        view_name="api:organisation-geo", read_only=True
    )

    def get_geography_model(self, obj):
        return obj.geographies.latest().geography

    class Meta:
        model = Organisation
        geo_field = "geography_model"
        fields = org_fields


def divisionset_url_kwargs(divisionset: OrganisationDivisionSet) -> dict:
    """
    The URL kwargs that identify a DivisionSet by its natural key:
    the Organisation's type, official identifier and start date,
    followed by the DivisionSet's own start date.
    """
    organisation = divisionset.organisation
    return {
        "organisation_type": organisation.organisation_type,
        "official_identifier": organisation.official_identifier,
        "date": organisation.start_date,
        "divset_date": divisionset.start_date,
    }


class DivisionSetHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        return self.reverse(
            view_name,
            kwargs=divisionset_url_kwargs(obj),
            request=request,
            format=format,
        )


divisionset_summary_fields = (
    "url",
    "start_date",
    "end_date",
    "short_title",
    "legislation_url",
    "consultation_url",
    "notes",
)


class DivisionSetSummarySerializer(serializers.ModelSerializer):
    """
    A division set without its divisions. Used in list responses, and
    nested inside each division in the elections endpoint.
    """

    url = DivisionSetHyperlinkedIdentityField(
        view_name="api:divisionset-detail", read_only=True
    )

    class Meta:
        model = OrganisationDivisionSet
        fields = divisionset_summary_fields


division_fields = (
    "name",
    "official_identifier",
    "slug",
    "division_type",
    "division_subtype",
    "division_election_sub_type",
    "seats_total",
    "territory_code",
    "created",
    "modified",
)


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationDivision
        fields = division_fields


class OrganisationDivisionSerializer(serializers.ModelSerializer):
    divisionset = DivisionSetSummarySerializer()

    class Meta:
        model = OrganisationDivision
        fields = division_fields + ("divisionset",)


class DivisionSetSerializer(DivisionSetSummarySerializer):
    """
    A division set including its divisions. Used in the detail response.

    If the serializer context contains `division_type`, only divisions of
    that type are included in `divisions`.
    """

    divisions = serializers.SerializerMethodField()
    division_types = serializers.SerializerMethodField()
    previous = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()
    pmtiles_url = serializers.SerializerMethodField()

    class Meta:
        model = OrganisationDivisionSet
        fields = divisionset_summary_fields + (
            "division_types",
            "previous",
            "next",
            "pmtiles_url",
            "divisions",
        )

    def get_divisions(self, obj: OrganisationDivisionSet):
        divisions = obj.divisions.all()
        if division_type := self.context.get("division_type"):
            divisions = divisions.filter(division_type=division_type)
        return DivisionSerializer(
            divisions, many=True, context=self.context
        ).data

    def get_division_types(self, obj: OrganisationDivisionSet) -> list[str]:
        # order_by() clears the model's default ordering by name, which
        # would otherwise be added to the SELECT and defeat distinct()
        return sorted(
            obj.divisions.order_by()
            .values_list("division_type", flat=True)
            .distinct()
        )

    def _detail_url(self, divisionset):
        if divisionset is None:
            return None
        return reverse(
            "api:divisionset-detail",
            kwargs=divisionset_url_kwargs(divisionset),
            request=self.context.get("request"),
            format=self.context.get("format"),
        )

    def get_previous(self, obj: OrganisationDivisionSet):
        return self._detail_url(
            obj.organisation.divisionset.filter(start_date__lt=obj.start_date)
            .order_by("-start_date")
            .first()
        )

    def get_next(self, obj: OrganisationDivisionSet):
        return self._detail_url(
            obj.organisation.divisionset.filter(start_date__gt=obj.start_date)
            .order_by("start_date")
            .first()
        )

    def get_pmtiles_url(self, obj: OrganisationDivisionSet):
        # This checks for a stored hash instead of using has_pmtiles_file
        # because has_pmtiles_file makes a request to S3.
        # This means you could get a 404 if the file hasn't been generated.
        if not obj.pmtiles_md5_hash:
            return None
        return reverse(
            "api:divisionset-pmtiles",
            kwargs=divisionset_url_kwargs(obj),
            request=self.context.get("request"),
        )


class ElectionTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ElectionType
        fields = ("name", "election_type")
        depth = 1


class ElectionSubTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionSubType
        fields = ("name", "election_subtype")


class ElectedRoleField(serializers.RelatedField):
    def to_representation(self, value):
        return value.elected_title


class ExplanationSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return value.explanation


class MetaDataSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return value.data


election_fields = (
    "election_id",
    "tmp_election_id",
    "election_title",
    "poll_open_date",
    "timetable",
    "election_type",
    "election_subtype",
    "organisation",
    "group",
    "group_type",
    "identifier_type",
    "children",
    "elected_role",
    "seats_contested",
    "division",
    "voting_system",
    "requires_voter_id",
    "current",
    "explanation",
    "metadata",
    "deleted",
    "cancelled",
    "cancellation_reason",
    "replaces",
    "replaced_by",
    "by_election_reason",
    "tags",
    "created",
    "modified",
)


class BaseElectionSerializer(serializers.ModelSerializer):
    election_type = ElectionTypeSerializer()
    election_subtype = ElectionSubTypeSerializer()
    organisation = OrganisationSerializer()
    division = OrganisationDivisionSerializer()
    group = serializers.SlugRelatedField(
        slug_field="election_id", read_only=True
    )
    children = serializers.SerializerMethodField()
    elected_role = ElectedRoleField(read_only=True)
    voting_system = serializers.SerializerMethodField()
    explanation = ExplanationSerializer(read_only=True)
    metadata = MetaDataSerializer(read_only=True)
    current = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()
    replaces = serializers.SlugRelatedField(
        slug_field="election_id", read_only=True
    )
    replaced_by = serializers.SlugRelatedField(
        slug_field="election_id", read_only=True
    )
    timetable = serializers.SerializerMethodField()
    tags = serializers.JSONField()

    def get_timetable(self, obj: Election):
        return {
            field: getattr(obj, field) for field in Election.TIMETABLE_FIELDS
        }

    def get_deleted(self, obj: Election):
        return obj.current_status == ModerationStatuses.deleted.value

    def get_current(self, obj: Election):
        return obj.get_current

    def get_voting_system(self, obj: Election):
        if (
            obj.group_type == "organisation"
            or obj.group_type == "subtype"
            or not obj.group_type
        ):
            system = VOTING_SYSTEMS.get(obj.voting_system, None)
            if system:
                system["slug"] = obj.voting_system
            return system
        return None

    def get_children(self, obj: Election) -> list[str]:
        if not obj.group_type:
            return []
        if children := getattr(obj, "children", None):
            return [c.election_id for c in children]
        if self.context["request"].query_params.get("deleted", None):
            children = (
                obj.get_children("private_objects")
                .all()
                .filter_by_status(
                    [
                        ModerationStatuses.approved.value,
                        ModerationStatuses.deleted.value,
                    ]
                )
            )
        else:
            children = obj.get_children("public_objects").all()
        return [c.election_id for c in children]


class ElectionSerializer(
    serializers.HyperlinkedModelSerializer, BaseElectionSerializer
):
    class Meta:
        model = Election
        fields = election_fields
        depth = 1


class ElectionGeoSerializer(GeoFeatureModelSerializer, BaseElectionSerializer):
    geography_model = GeometrySerializerMethodField()

    def get_geography_model(self, obj):
        if obj.geography is None:
            return None
        return obj.geography.geography

    class Meta:
        model = Election
        extra_kwargs = {
            "url": {"view_name": "election-geo", "lookup_field": "pk"}
        }

        geo_field = "geography_model"

        fields = election_fields
        depth = 1
