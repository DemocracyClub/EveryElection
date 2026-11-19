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
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer,
    GeometrySerializerMethodField,
)
from uk_election_ids.datapackage import VOTING_SYSTEMS


class NaturalKeyHyperlinkedField(serializers.HyperlinkedRelatedField):
    """
    A link to a model instance that is addressed by natural key rather
    than primary key. The instance's url_kwargs() method supplies the
    URL kwargs.

    For a link to the object being serialized, pass `source="*"`.
    For a link to another object, pass a `source` that returns it, and
    the field will output null when that is None.
    """

    def use_pk_only_optimization(self):
        # Without this, a `source` pointing at a property gets passed to
        # get_url() as a PKOnlyObject, which has no url_kwargs().
        return False

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        return self.reverse(
            view_name,
            kwargs=obj.url_kwargs(),
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
    url = NaturalKeyHyperlinkedField(
        view_name="api:organisation-detail", source="*", read_only=True
    )

    class Meta:
        model = Organisation
        fields = org_fields


class OrganisationGeoSerializer(GeoFeatureModelSerializer):
    geography_model = GeometrySerializerMethodField()
    url = NaturalKeyHyperlinkedField(
        view_name="api:organisation-geo", source="*", read_only=True
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
            "created",
            "modified",
        )


class DivisionSetSummarySerializer(serializers.ModelSerializer):
    """
    A division set without its divisions.
    """

    url = NaturalKeyHyperlinkedField(
        view_name="api:divisionset-detail", source="*", read_only=True
    )

    class Meta:
        model = OrganisationDivisionSet
        fields = (
            "url",
            "start_date",
            "end_date",
            "short_title",
            "legislation_url",
            "consultation_url",
            "notes",
        )


class DivisionSerializer(serializers.ModelSerializer):
    """
    A division without its division set. Used in the division set
    detail response, where the division set is the parent object.
    """

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
            "created",
            "modified",
        )


class DivisionSetSerializer(DivisionSetSummarySerializer):
    """
    A division set including its divisions. Used in the detail response.

    If the serializer context contains `division_type`, only divisions of
    that type are included in `divisions`.
    """

    divisions = serializers.SerializerMethodField()
    division_types = serializers.SerializerMethodField()
    previous = NaturalKeyHyperlinkedField(
        view_name="api:divisionset-detail",
        source="previous_divisionset",
        read_only=True,
    )
    next = NaturalKeyHyperlinkedField(
        view_name="api:divisionset-detail",
        source="next_divisionset",
        read_only=True,
    )

    class Meta(DivisionSetSummarySerializer.Meta):
        fields = DivisionSetSummarySerializer.Meta.fields + (
            "division_types",
            "previous",
            "next",
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
