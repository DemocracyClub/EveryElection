from django.contrib.gis import geos

import factory

from organisations.models import (Organisation, OrganisationDivisionSet,
                                  OrganisationDivision, DivisionGeography)


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    official_identifier = factory.Sequence(lambda n: n)
    organisation_type = "local-authority"
    official_name = factory.Sequence(
        lambda n: 'The Organisation %d Council' % n)
    common_name = factory.Sequence(lambda n: 'Organisation %d' % n)
    gss = factory.Sequence(lambda n: 'E00000%d' % n)
    slug = factory.Sequence(lambda n: 'org-%d' % n)
    territory_code = "ENG"
    # election_types
    # election_name


class OrganisationDivisionSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationDivisionSet

    organisation = factory.SubFactory(OrganisationFactory)
    start_date = "2017-05-04"
    end_date = "2025-05-03"
    legislation_url = "https://example.com/the-law"
    consultation_url = "https://example.com/consultation"
    short_title = "Made up boundary changes"
    notes = "This is just for testing."


class OrganisationDivisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationDivision

    organisation = factory.SubFactory(OrganisationFactory)
    divisionset = factory.SubFactory(OrganisationDivisionSetFactory)
    name = factory.Sequence(lambda n: 'Division %d' % n)
    official_identifier = factory.Sequence(lambda n: n)
    geography_curie = factory.Sequence(lambda n: 'test:%d' % n)
    slug = factory.Sequence(lambda n: '%d' % n)
    division_type = "test"
    # division_election_sub_type
    # seats_total
    # mapit_generation_low
    # mapit_generation_high


class DivisionGeographyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DivisionGeography

    division = factory.SubFactory(OrganisationDivisionFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    geography = "MULTIPOLYGON (((-0.142322981070547 51.5068483965321, -0.142175355949697 51.5066383732171, -0.141985552222889 51.5067171320737, -0.141458319648422 51.5061920704584, -0.141458319648422 51.506034550794, -0.140256229378637 51.5048662629532, -0.140720194044168 51.5046824846112, -0.138674531655237 51.5024770866938, -0.130787132341213 51.5057720168099, -0.12956395276845 51.5051025483037, -0.129142166708876 51.5038029637132, -0.129142166708876 51.5034485251196, -0.129669399283343 51.5028577880039, -0.129943560222066 51.5014531156649, -0.141205248012678 51.5002584537182, -0.142850213645014 51.4995889042081, -0.143145463886716 51.4993394616797, -0.143757053673097 51.498367935661, -0.144115571823735 51.4982235178632, -0.145043501154796 51.4983416779137, -0.146941538422877 51.498367935661, -0.147363324482451 51.4989062161487, -0.147974914268832 51.4995889042081, -0.148987200811808 51.5003897367824, -0.149640969204147 51.500849224529, -0.150737612959038 51.5014793716197, -0.151138309715633 51.5017813140128, -0.150948505988825 51.5018994648395, -0.149872951536913 51.5023195541869, -0.149619879901169 51.5025952357166, -0.149640969204147 51.5030153186501, -0.149408986871382 51.5031334662775, -0.147510949603301 51.5040655090422, -0.147004806331813 51.5044724513128, -0.145844894667986 51.505063167497, -0.144537357883308 51.505785143545, -0.142322981070547 51.5068483965321)))"  # noqa
