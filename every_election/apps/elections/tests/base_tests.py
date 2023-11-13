from datetime import date

from elections.models import ElectedRole, ElectionType
from elections.utils import create_ids_for_each_ballot_paper
from organisations.models import Organisation
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)


class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


class BaseElectionCreatorMixIn:
    test_polygon = "MULTIPOLYGON (((-0.142322981070547 51.5068483965321, -0.142175355949697 51.5066383732171, -0.141985552222889 51.5067171320737, -0.141458319648422 51.5061920704584, -0.141458319648422 51.506034550794, -0.140256229378637 51.5048662629532, -0.140720194044168 51.5046824846112, -0.138674531655237 51.5024770866938, -0.130787132341213 51.5057720168099, -0.12956395276845 51.5051025483037, -0.129142166708876 51.5038029637132, -0.129142166708876 51.5034485251196, -0.129669399283343 51.5028577880039, -0.129943560222066 51.5014531156649, -0.141205248012678 51.5002584537182, -0.142850213645014 51.4995889042081, -0.143145463886716 51.4993394616797, -0.143757053673097 51.498367935661, -0.144115571823735 51.4982235178632, -0.145043501154796 51.4983416779137, -0.146941538422877 51.498367935661, -0.147363324482451 51.4989062161487, -0.147974914268832 51.4995889042081, -0.148987200811808 51.5003897367824, -0.149640969204147 51.500849224529, -0.150737612959038 51.5014793716197, -0.151138309715633 51.5017813140128, -0.150948505988825 51.5018994648395, -0.149872951536913 51.5023195541869, -0.149619879901169 51.5025952357166, -0.149640969204147 51.5030153186501, -0.149408986871382 51.5031334662775, -0.147510949603301 51.5040655090422, -0.147004806331813 51.5044724513128, -0.145844894667986 51.505063167497, -0.144537357883308 51.505785143545, -0.142322981070547 51.5068483965321)))"  # noqa

    @classmethod
    def setUpTestData(cls):
        cls.date = date.today()
        cls.date_str = cls.date.strftime("%Y-%m-%d")

        cls.election_type1, _ = ElectionType.objects.get_or_create(
            election_type="local"
        )
        cls.org1 = Organisation.objects.create(
            official_identifier="TEST1",
            organisation_type="local-authority",
            official_name="Test Council",
            slug="test",
            territory_code="ENG",
            election_name="Test Council local elections",
            start_date=date(2016, 10, 1),
        )

        cls.elected_role1 = ElectedRole.objects.create(
            election_type=cls.election_type1,
            organisation=cls.org1,
            elected_title="Local Councillor",
            elected_role_name="Councillor for Test Council",
        )

        cls.div_set = OrganisationDivisionSetFactory(organisation=cls.org1)
        cls.org_div_1 = OrganisationDivisionFactory(
            divisionset=cls.div_set,
            name="Test Div 1",
            slug="test-div",
            seats_total=3,
        )
        cls.org_div_2 = OrganisationDivisionFactory(
            divisionset=cls.div_set, name="Test Div 2", slug="test-div-2"
        )

        cls.base_data = {
            "election_organisation": [cls.org1],
            "election_type": cls.election_type1,
            "date": cls.date,
        }

        cls.testshire_org = Organisation.objects.create(
            official_identifier="TEST1SHIRE",
            organisation_type="local-authority",
            official_name="Testshire County Council",
            slug="testshire",
            territory_code="ENG",
            election_name="Testshire County Council local elections",
            start_date=date(2016, 10, 1),
        )
        ElectedRole.objects.create(
            election_type=cls.election_type1,
            organisation=cls.testshire_org,
            elected_title="Local Councillor",
            elected_role_name="Councillor for Testshire Council",
        )
        cls.testshire_div_set = OrganisationDivisionSetFactory(
            organisation=cls.testshire_org
        )
        cls.testshire_div = OrganisationDivisionFactory(
            divisionset=cls.testshire_div_set,
            name="Testshire Div 1",
            slug="testshire-div",
            seats_total=3,
        )

    def tearDown(self):
        super().tearDown()
        self.base_data = None

    def make_div_id(self, org=None, div=None, subtype=None):
        if not org:
            org = self.org1

        if not div:
            div = self.org_div_1

        return str(div.pk)

    def add_division(
        self, division_id, ballot_type="contested", seats_contested=1
    ):
        return {
            "ballot_type": ballot_type,
            "division_id": division_id,
            "seats_contested": seats_contested,
        }

    def create_ids(self, all_data, save_model=True, **kwargs):
        all_ids = create_ids_for_each_ballot_paper(all_data, **kwargs)
        if save_model:
            [e_id.save() for e_id in all_ids]
