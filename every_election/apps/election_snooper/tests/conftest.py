import pytest
from django.contrib.auth.models import Group
from election_snooper.models import SnoopedElection


@pytest.fixture
def snooped_election(db):
    return SnoopedElection.objects.create(
        title="Test election",
        snooper_name="TestSnooper",
        status="election",
    )


@pytest.fixture
def logged_in_client(client, django_user_model):
    """A client logged in as a user who is not a moderator."""
    user = django_user_model.objects.create_user(username="nonmoderator")
    client.force_login(user)
    return client


@pytest.fixture
def moderator_client(client, django_user_model):
    """A client logged in as a user in the moderators group."""
    user = django_user_model.objects.create_user(username="moderator")
    # The group is created by a core data migration, but pytest sometimes
    # flushes it away, so don't rely on it already being there.
    group, _ = Group.objects.get_or_create(name="moderators")
    user.groups.add(group)
    client.force_login(user)
    return client
