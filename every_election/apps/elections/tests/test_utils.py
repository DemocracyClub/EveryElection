import pytest
from elections.utils import get_voter_id_requirement
from elections.tests.factories import ElectionFactory


@pytest.mark.django_db
class TestGetVoterIdRequirements:
    default_election_id = "local.place.2024-01-01"

    @pytest.mark.parametrize(
        "territory_code,expected_result",
        [("ENG", "EA-2022"), ("NIR", "EFA-2002"), ("", None), (None, None)],
    )
    def test_get_voter_id_requirement_expected_territory_codes(
        self, territory_code, expected_result
    ):
        election = ElectionFactory(election_id=self.default_election_id)
        election.division.territory_code = territory_code
        assert get_voter_id_requirement(election) == expected_result

    def test_get_voter_id_requirement_no_division(self):
        election = ElectionFactory(election_id=self.default_election_id)
        election.division = None
        assert get_voter_id_requirement(election) is None

    def test_get_voter_id_requirement_fake_territory(self):
        election = ElectionFactory(election_id=self.default_election_id)
        with pytest.raises(ValueError):
            election.division.territory_code = "BBQ"
            get_voter_id_requirement(election)
