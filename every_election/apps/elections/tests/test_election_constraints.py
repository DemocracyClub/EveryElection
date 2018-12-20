from django.test import TestCase
from elections.tests.factories import (
    ElectionFactory,
    ElectionWithStatusFactory,
    ModerationHistoryFactory,
    ModerationStatusFactory,
    related_status,
)
from elections.constraints import (
    has_approved_child,
    has_approved_parents,
    has_related_status,
)


class TestElectionModel(TestCase):
    def test_has_related_status(self):
        self.assertFalse(has_related_status(ElectionFactory()))
        self.assertTrue(has_related_status(ElectionWithStatusFactory()))

    def test_has_approved_parents_two_level(self):
        org_group = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Suggested")
        )
        ballot = ElectionWithStatusFactory(
            group=org_group, moderation_status=related_status("Approved")
        )
        self.assertFalse(has_approved_parents(ballot))
        ModerationHistoryFactory(
            election=org_group, status=ModerationStatusFactory(short_label="Approved")
        )
        self.assertTrue(has_approved_parents(ballot))

    def test_has_approved_parents_three_level(self):
        election_group = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Suggested")
        )
        org_group = ElectionWithStatusFactory(
            group=election_group, moderation_status=related_status("Suggested")
        )
        ballot = ElectionWithStatusFactory(group=org_group)
        self.assertFalse(has_approved_parents(ballot))

        ModerationHistoryFactory(
            election=election_group,
            status=ModerationStatusFactory(short_label="Approved"),
        )
        # still false because only one of our 2 parents is approved
        self.assertFalse(has_approved_parents(ballot))

        ModerationHistoryFactory(
            election=org_group, status=ModerationStatusFactory(short_label="Approved")
        )
        # now both parents are approved
        self.assertTrue(has_approved_parents(ballot))

    def test_has_approved_child(self):
        org_group = ElectionWithStatusFactory(group=None)
        ballots = [
            ElectionWithStatusFactory(
                group=org_group, moderation_status=related_status("Suggested")
            ),
            ElectionWithStatusFactory(
                group=org_group, moderation_status=related_status("Suggested")
            ),
        ]
        self.assertFalse(has_approved_child(org_group))

        # approve one of the 2 child ballots
        ModerationHistoryFactory(
            election=ballots[0], status=ModerationStatusFactory(short_label="Approved")
        )
        self.assertTrue(has_approved_child(org_group))
