import pytest
from django.contrib.auth.models import Group
from elections.models import ElectionSubType, ElectionType, ModerationStatus
from uk_election_ids.datapackage import ELECTION_TYPES


@pytest.fixture(autouse=True)
def core_elections_data():
    """
    A pytest fixture that creates the data made in data migrations.

    This data should be considered 'core' to the application, that is,
    it should always exist in any running version of the application.

    Although there are migrations for this data, we can't always rely on
    them because sometimes pytest calls `flush` on the database.

    """
    # We need a moderators group for some core views
    Group.objects.get_or_create(name="moderators")

    # Set up election types as defined in `uk-election-ids`
    for type_name, info in ELECTION_TYPES.items():
        election_type, _ = ElectionType.objects.get_or_create(
            election_type=type_name, defaults={"name": info["name"]}
        )
        for subtype in info["subtypes"]:
            ElectionSubType.objects.update_or_create(
                election_type=election_type,
                election_subtype=subtype["election_subtype"],
                defaults={"name": subtype["name"]},
            )

    recs = [
        ModerationStatus(
            short_label="Suggested", long_label="Suggested by an anonymous user"
        ),
        ModerationStatus(
            short_label="Rejected", long_label="Rejected by a moderator"
        ),
        ModerationStatus(
            short_label="Approved", long_label="Approved by a moderator"
        ),
        ModerationStatus(
            short_label="Deleted",
            long_label="Deleted (because it was added in error)",
        ),
    ]
    ModerationStatus.objects.bulk_create(recs, ignore_conflicts=True)
