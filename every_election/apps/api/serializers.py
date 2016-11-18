from rest_framework import serializers

from elections.models import Election, ElectionType, ElectionSubType
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


class ElectionSerializer(serializers.HyperlinkedModelSerializer):
    election_type = ElectionTypeSerializer()
    election_subtype = ElectionSubTypeSerializer()
    organisation = OrganisationSerializer()

    class Meta:
        model = Election
        fields = (
            'election_id',
            'poll_open_date',
            'election_type',
            'election_subtype',
            'organisation',
        )
        depth = 1
