from django.test import TestCase

# from elections.models import Election
from elections.utils import IDMaker

from .base_tests import BaseElectionCreatorMixIn
from organisations.tests.factories import OrganisationFactory



class TestElectoralSystems(BaseElectionCreatorMixIn, TestCase):
    def test_scotland_local_stv(self):
        """
        Scottish local elections have the type of `local` but unlike the
        rest of the UK that uses FPTP, it uses STV
        """

        # "Normal" UK local election is FPTP
        election_id = IDMaker('local', '2017-05-04')
        assert election_id.voting_system.slug == "FPTP"

        scot_org = OrganisationFactory(
            territory_code="SCT",
            gss="S0000001"
        )

        # Scotish local elections are STV
        scot_id = IDMaker('local', '2017-05-04', organisation=scot_org)
        assert scot_id.voting_system.slug == "STV"
