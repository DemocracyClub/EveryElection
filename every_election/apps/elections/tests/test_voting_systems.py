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

        # Elections without organisations don't have voting systems
        election_id = ElectionBuilder(
            "local", "2017-05-04"
        ).build_election_group()
        assert election_id.voting_system == None

        # "Normal" UK local election is FPTP
        eng_org = OrganisationFactory(territory_code="ENG")
        ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=eng_org,
            elected_title="Councillor",
            elected_role_name="Councillor for Foo Town",
        )
        election_id = (
            ElectionBuilder("local", "2017-05-04")
            .with_organisation(eng_org)
            .build_election_group()
        )

        assert election_id.voting_system == "FPTP"

        scot_org = OrganisationFactory(territory_code="SCT")

        ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=scot_org,
            elected_title="MSP",
            elected_role_name="MSP for Foo Town",
        )

        # Scottish local elections are STV
        scot_id = (
            ElectionBuilder("local", "2017-05-04")
            .with_organisation(scot_org)
            .build_organisation_group(None)
        )
        assert scot_id.voting_system == "STV"
