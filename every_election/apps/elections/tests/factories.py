import factory

from elections.models import Election, ElectionType, ElectedRole
from organisations.tests.factories import (OrganisationFactory,
                                           OrganisationDivisionFactory,
                                           DivisionGeographyFactory)


class ElectionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ElectionType
        django_get_or_create = ('election_type', )

    name = "Local elections"
    election_type = "local"
    # default_voting_system


class ElectedRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ElectedRole
        django_get_or_create = ('election_type', )

    election_type = factory.SubFactory(ElectionTypeFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    elected_title = "Councillor"
    elected_role_name = "Councillor"


class ElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election
        django_get_or_create = ('election_id', )

    election_id = factory.Sequence(
        lambda n: 'local.place-name-%d.2017-03-23' % n)
    election_title = factory.Sequence(lambda n: 'Election %d' % n)
    election_type = factory.SubFactory(ElectionTypeFactory)
    poll_open_date = "2017-03-23"
    organisation = factory.SubFactory(OrganisationFactory)
    elected_role = factory.SubFactory(ElectedRoleFactory)
    division = factory.SubFactory(OrganisationDivisionFactory)
    geography = factory.SubFactory(DivisionGeographyFactory)
    seats_contested = 1
    seats_total = 1
    group = factory.SubFactory(
        'elections.tests.factories.ElectionFactory',
        election_id="local.2017-03-23",
        group=None, group_type="election")
    group_type = None




# class OrganisationDivisionSetFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = OrganisationDivisionSet
#
#     organisation = factory.SubFactory(OrganisationFactory)
#     start_date = "2017-05-04"
#     end_date = "2025-05-03"
#     legislation_url = "https://example.com/the-law"
#     consultation_url = "https://example.com/consultation"
#     short_title = "Made up boundary changes"
#     notes = "This is just for testing."
#
#
# class OrganisationDivisionFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = OrganisationDivision
#
#     organisation = factory.SubFactory(OrganisationFactory)
#     divisionset = factory.SubFactory(OrganisationDivisionSetFactory)
#     name = factory.Sequence(lambda n: 'Division %d' % n)
#     official_identifier = factory.Sequence(lambda n: n)
#     geography_curie = factory.Sequence(lambda n: 'test:%d' % n)
#     slug = factory.Sequence(lambda n: '%d' % n)
#     division_type = "test"
#     # division_election_sub_type
#     # seats_total
#     # mapit_generation_low
#     # mapit_generation_high
#
#
# class DivisionGeographyFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = DivisionGeography
#
#     division = factory.SubFactory(OrganisationDivisionFactory)
#     organisation = factory.SubFactory(OrganisationFactory)
#     geography = "MULTIPOLYGON (((-7.557203359094856 49.76727408865833, -7.557203344046908 49.76727409067937, -7.557203341259608 49.76727408769252, -7.557203342359706 49.76727408662629, -7.557203340853587 49.76727408592865, -7.55720333994566 49.76727408422944, -7.557203337725777 49.7672740835256, -7.557203337508899 49.76727408252273, -7.557203349149426 49.76727408098986, -7.557203351051125 49.76727408069573, -7.557203354058343 49.76727408115904, -7.557203359094856 49.76727408865833)))"  # noqa
