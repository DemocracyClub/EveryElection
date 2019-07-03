from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer,
    GeometrySerializerMethodField,
)

from elections.models import (
    Election,
    ElectionType,
    ElectionSubType,
    ModerationStatuses,
    VotingSystem,
)
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)


class OrganisationHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
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


class OrganisationDivisionSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationDivisionSet
        fields = (
            "start_date",
            "end_date",
            "legislation_url",
            "consultation_url",
            "short_title",
            "notes",
        )


class OrganisationDivisionSerializer(serializers.ModelSerializer):
    divisionset = OrganisationDivisionSetSerializer()

    class Meta:
        model = OrganisationDivision
        fields = (
            "divisionset",
            "name",
            "official_identifier",
            "slug",
            "division_type",
            "division_subtype",
            "division_election_sub_type",
            "seats_total",
            "territory_code",
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


class VotingSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingSystem
        fields = ("slug", "name", "uses_party_lists")


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
    "election_type",
    "election_subtype",
    "organisation",
    "group",
    "group_type",
    "children",
    "elected_role",
    "seats_contested",
    "division",
    "voting_system",
    "current",
    "explanation",
    "metadata",
    "deleted",
    "cancelled",
    "replaces",
    "replaced_by",
)


class BaseElectionSerializer(serializers.ModelSerializer):
    election_type = ElectionTypeSerializer()
    election_subtype = ElectionSubTypeSerializer()
    organisation = OrganisationSerializer()
    division = OrganisationDivisionSerializer()
    group = serializers.SlugRelatedField(slug_field="election_id", read_only=True)
    children = serializers.SerializerMethodField()
    elected_role = ElectedRoleField(read_only=True)
    voting_system = serializers.SerializerMethodField()
    explanation = ExplanationSerializer(read_only=True)
    metadata = MetaDataSerializer(read_only=True)
    current = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()
    replaces = serializers.SlugRelatedField(slug_field="election_id", read_only=True)
    replaced_by = serializers.SlugRelatedField(slug_field="election_id", read_only=True)

    def get_deleted(self, obj):
        return obj.moderation_status.short_label == ModerationStatuses.deleted.value

    def get_current(self, obj):
        return obj.get_current

    def get_voting_system(self, obj):
        if (
            obj.group_type == "organisation"
            or obj.group_type == "subtype"
            or not obj.group_type
        ):
            return VotingSystemSerializer(obj.voting_system).data
        return None

    def get_children(self, obj):
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
        extra_kwargs = {"url": {"view_name": "election-geo", "lookup_field": "pk"}}

        geo_field = "geography_model"

        fields = election_fields
        depth = 1
