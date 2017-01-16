from rest_framework import serializers

from elections.models import (
    Election, ElectionType, ElectionSubType, ElectedRole)
from organisations.models import Organisation



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
        )
        depth = 1

