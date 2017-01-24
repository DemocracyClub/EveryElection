from rest_framework import serializers

from elections.models import (
    Election, ElectionType, ElectionSubType, ElectedRole)
from organisations.models import (Organisation, OrganisationDivision,
                                  OrganisationDivisionSet)



class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = (
            'official_identifier',
            'organisation_type',
            'organisation_subtype',
            'official_name',
            'common_name',
            'gss',
            'slug',
            'territory_code',
            'election_name'
        )


class OrganisationDivisionSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationDivisionSet
        fields = (
            'start_date',
            'end_date',
            'legislation_url',
            'consultation_url',
            'short_title',
            'mapit_generation_id',
            'notes',
        )




class OrganisationDivisionSerializer(serializers.ModelSerializer):
    divisionset = OrganisationDivisionSetSerializer()
    class Meta:
        model = OrganisationDivision
        fields = (
            'divisionset',
            'name',
            'official_identifier',
            'geography_curie',
            'slug',
            'division_type',
            'division_subtype',
            'division_election_sub_type',
            'seats_total',
            'mapit_generation_low',
            'mapit_generation_high',
        )


class ElectionTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ElectionType
        fields = ('name', 'election_type')
        depth = 1


class ElectionSubTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionSubType
        fields = ('name', 'election_subtype')


class ElectedRoleField(serializers.RelatedField):
    def to_representation(self, value):
        return value.elected_title


class ElectionSerializer(serializers.HyperlinkedModelSerializer):
    election_type = ElectionTypeSerializer()
    election_subtype = ElectionSubTypeSerializer()
    organisation = OrganisationSerializer()
    division = OrganisationDivisionSerializer()
    group = serializers.SlugRelatedField(
        slug_field='election_id',
        read_only=True
        )
    children = serializers.SlugRelatedField(
        slug_field='election_id',
        read_only=True,
        many=True
    )
    elected_role = ElectedRoleField(read_only=True)


    class Meta:
        model = Election
        fields = (
            'election_id',
            'tmp_election_id',
            'election_title',
            'poll_open_date',
            'election_type',
            'election_subtype',
            'organisation',
            'group',
            'group_type',
            'children',
            'elected_role',
            'division',
        )
        depth = 1

