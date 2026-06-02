from elections.models import (
    Election,
    ElectionSubType,
    ElectionType,
    ModerationStatuses,
)
from organisations.models import (
    DivisionGeography,
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


class OrganisationCurrentDivisionSetSerializer(serializers.ModelSerializer):
    division_count = serializers.SerializerMethodField()

    def get_division_count(self, obj):
        return obj.divisions.count()

    class Meta:
        model = OrganisationDivisionSet
        fields = (
            "start_date",
            "end_date",
            "short_title",
            "legislation_url",
            "consultation_url",
            "notes",
            "division_count",
        )


class OrganisationDetailSerializer(OrganisationSerializer):
    """Extends OrganisationSerializer with divisionset fields. Use prefetch_related("divisionset")
    on the queryset to avoid N+1 queries when listing multiple organisations."""

    current_divisionset = serializers.SerializerMethodField()
    divisionsets_url = serializers.SerializerMethodField()

    def get_current_divisionset(self, obj):
        # Iterates the prefetch cache when available instead of issuing a new query.
        active = [ds for ds in obj.divisionset.all() if ds.end_date is None]
        if len(active) != 1:
            return None
        return OrganisationCurrentDivisionSetSerializer(active[0]).data

    def get_divisionsets_url(self, obj):
        request = self.context.get("request")
        url = reverse("api:division-list")
        full_url = f"{url}?org_slug={obj.slug}"
        if request:
            return request.build_absolute_uri(full_url)
        return full_url

    class Meta(OrganisationSerializer.Meta):
        fields = org_fields + ("current_divisionset", "divisionsets_url")


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
    """Base division serializer — used when a division is nested inside an election."""

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
            "created",
            "modified",
        )


class DivisionOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = (
            "official_identifier",
            "organisation_type",
            "slug",
        )


class FlatDivisionSerializer(OrganisationDivisionSerializer):
    """Division serializer for the flat /api/divisions/ endpoint — includes parent organisation."""

    organisation = DivisionOrganisationSerializer(source="divisionset.organisation")

    class Meta(OrganisationDivisionSerializer.Meta):
        fields = (
            "divisionset",
            "organisation",
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


class DivisionGeoSerializer(GeoFeatureModelSerializer):
    geography_model = GeometrySerializerMethodField()

    def get_geography_model(self, obj):
        try:
            return obj.geography.geography
        except DivisionGeography.DoesNotExist:
            return None

    class Meta:
        model = OrganisationDivision
        geo_field = "geography_model"
        fields = (
            "name",
            "official_identifier",
            "slug",
            "division_type",
            "division_subtype",
            "seats_total",
            "territory_code",
        )


class DivisionForDivisionSetSerializer(serializers.ModelSerializer):
    geo_url = serializers.SerializerMethodField()
    geography_url = serializers.SerializerMethodField()

    def get_geo_url(self, obj):
        request = self.context.get("request")
        url = reverse("api:division-geo", args=[obj.pk])
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_geography_url(self, obj):
        return obj.format_geography_link()

    class Meta:
        model = OrganisationDivision
        fields = (
            "name",
            "official_identifier",
            "slug",
            "division_type",
            "division_subtype",
            "division_election_sub_type",
            "seats_total",
            "territory_code",
            "geo_url",
            "geography_url",
        )


class DivisionSetOrganisationSerializer(serializers.ModelSerializer):
    url = OrganisationHyperlinkedIdentityField(
        view_name="api:organisation-detail", read_only=True
    )

    class Meta:
        model = Organisation
        fields = (
            "url",
            "official_identifier",
            "organisation_type",
            "slug",
        )


class DivisionSetSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="api:divisionset-detail", read_only=True
    )
    organisation = DivisionSetOrganisationSerializer()
    divisions = serializers.SerializerMethodField()

    def get_divisions(self, obj):
        return DivisionForDivisionSetSerializer(
            obj.divisions.all(), many=True, context=self.context
        ).data

    class Meta:
        model = OrganisationDivisionSet
        fields = (
            "url",
            "organisation",
            "start_date",
            "end_date",
            "short_title",
            "legislation_url",
            "consultation_url",
            "notes",
            "divisions",
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
    tags = serializers.JSONField()

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
