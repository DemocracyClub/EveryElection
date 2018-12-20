from django.test import TestCase

from elections.utils import ElectionBuilder

from .base_tests import BaseElectionCreatorMixIn
from elections.models import ElectedRole
from organisations.tests.factories import OrganisationFactory


class TestElectoralSystems(BaseElectionCreatorMixIn, TestCase):
    def test_scotland_local_stv(self):
        """
        Scottish local elections have the type of `local` but unlike the
        rest of the UK that uses FPTP, it uses STV
        """

        # "Normal" UK local election is FPTP
        election_id = ElectionBuilder("local", "2017-05-04").build_election_group()
        assert election_id.voting_system.slug == "FPTP"

        scot_org = OrganisationFactory(territory_code="SCT")

        ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=scot_org,
            elected_title="MSP",
            elected_role_name="MSP for Foo Town",
        )

        # Scotish local elections are STV
        scot_id = (
            ElectionBuilder("local", "2017-05-04")
            .with_organisation(scot_org)
            .build_organisation_group(None)
        )
        assert scot_id.voting_system.slug == "STV"
