from datetime import datetime

from organisations.models import Organisation, OrganisationDivision
from elections.models import ElectionType, ElectedRole
from elections.utils import create_ids_for_each_ballot_paper


class BaseElectionCreatorMixIn():
    def setUp(self):
        super().setUp()
        self._create_models()

    def tearDown(self):
        super().tearDown()
        self.base_data = None


    def _create_models(self):
        self.date = datetime.today()
        self.date_str = self.date.strftime("%Y-%m-%d")

        self.election_type1 = ElectionType.objects.get(
            election_type='local',
        )
        self.org1 = Organisation.objects.create(
            official_identifier='TEST1',
            organisation_type='local-authority',
            official_name="Test Council",
            gss="X00000001",
            slug="test",
            territory_code="ENG",
            election_name="Test Council Local Elections",
        )

        self.elected_role1 = ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=self.org1,
            elected_title="Local Councillor",
            elected_role_name="Councillor for Test Council",
        )
        self.org_div_1 = OrganisationDivision.objects.create(
            organisation=self.org1,
            name="Test Div 1",
            slug="test-div"
        )
        self.org_div_2 = OrganisationDivision.objects.create(
            organisation=self.org1,
            name="Test Div 2",
            slug="test-div-2"
        )

        self.base_data = {
            'election_organisation': [self.org1, ],
            'election_type': self.election_type1,
            'date': self.date,
        }

    def make_div_id(self, org=None, div=None):
        if not org:
            org = self.org1

        if not div:
            div = self.org_div_1

        return "__".join(map(str, [org.pk, div.pk]))

    def create_ids(self, all_data, save_model=True):
        all_ids = create_ids_for_each_ballot_paper(all_data)
        if save_model:
            [e_id.save_model() for e_id in all_ids]

