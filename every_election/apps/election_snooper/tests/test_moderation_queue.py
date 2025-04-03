from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from elections.tests.factories import ElectionWithStatusFactory, related_status


class TestSingleElectionView(TestCase):
    def login(self):
        # fake being logged in as a moderator
        mods = Group.objects.get(name="moderators")
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        mods.user_set.add(user)
        self.client.login(username="testuser", password="12345")

    def test_not_logged_in(self):
        resp = self.client.get("/election_radar/moderation_queue/")
        self.assertRedirects(
            resp, "/accounts/login/?next=/election_radar/moderation_queue/"
        )

    def test_approve(self):
        self.login()
        # 4 ballots with different moderation statuses
        approved = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Approved")
        )
        rejected = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Rejected")
        )
        deleted = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Deleted")
        )

        suggested_parent = ElectionWithStatusFactory(
            group=None,
            group_type="organisation",
            moderation_status=related_status("Suggested"),
        )
        suggested_child = ElectionWithStatusFactory(
            group=suggested_parent,
            moderation_status=related_status("Suggested"),
        )

        resp = self.client.get("/election_radar/moderation_queue/")
        self.assertEqual(200, resp.status_code)

        # only suggested ballot should be shown
        self.assertNotContains(resp, approved.election_id, html=True)
        self.assertNotContains(resp, rejected.election_id, html=True)
        self.assertNotContains(resp, deleted.election_id, html=True)

        # only ballots should be shown
        self.assertContains(resp, suggested_child.election_id, html=True)
        self.assertNotContains(resp, suggested_parent.election_id, html=True)

        with patch("elections.models.push_event_to_queue") as push_mock:
            self.client.post(
                "/election_radar/moderation_queue/",
                {
                    "election": suggested_child.pk,
                    "{}-status".format(suggested_child.pk): "Approved",
                },
            )
        suggested_child.refresh_from_db()
        suggested_parent.refresh_from_db()
        # approving the child should
        # implicitly approve the parent
        # if it is not already approved
        self.assertEqual("Approved", suggested_child.current_status)
        self.assertEqual("Approved", suggested_parent.current_status)

        # we should have only pushed one event
        # even though we approved >1 elections
        assert push_mock.call_count == 1
