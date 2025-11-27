from django.contrib.auth import get_user_model
from django.test import TestCase
from elections.models import Election
from elections.tests.factories import ElectionWithStatusFactory, related_status


class TestSingleElectionView(TestCase):
    def test_election_status(self):
        # 4 ballots with different moderation statuses
        approved = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Approved")
        )
        suggested = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Suggested")
        )
        rejected = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Rejected")
        )
        deleted = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Deleted")
        )

        # approved elections shoud be visible via the DetailView
        resp = self.client.get("/elections/{}/".format(approved.election_id))
        self.assertEqual(200, resp.status_code)

        # we shouldn't be able to access elections which are
        # suggsted, rejected or deleted via the DetailView
        resp = self.client.get(
            "/api/elections/{}/".format(rejected.election_id)
        )
        self.assertEqual(404, resp.status_code)
        resp = self.client.get(
            "/api/elections/{}/".format(suggested.election_id)
        )
        self.assertEqual(404, resp.status_code)
        resp = self.client.get("/api/elections/{}/".format(deleted.election_id))
        self.assertEqual(404, resp.status_code)

    def test_child_election_status(self):
        # 4 ballots in the same group with different moderation statuses
        group = ElectionWithStatusFactory(
            group_type="election", moderation_status=related_status("Approved")
        )
        approved = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Approved")
        )
        suggested = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Suggested")
        )
        rejected = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Rejected")
        )
        deleted = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Deleted")
        )

        # DetailView should only show approved child elections
        resp = self.client.get("/elections/{}/".format(group.election_id))
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, approved.election_id, html=True)
        self.assertNotContains(resp, suggested.election_id, html=True)
        self.assertNotContains(resp, rejected.election_id, html=True)
        self.assertNotContains(resp, deleted.election_id, html=True)

    def test_edit_in_admin_link_not_displayed(self):
        election = ElectionWithStatusFactory()
        response = self.client.get(election.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Edit in admin")

        # logged in non-superuser
        user = get_user_model().objects.create(is_superuser=False)
        self.client.force_login(user=user)
        response = self.client.get(election.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Edit in admin")

    def test_edit_in_admin_is_displayed_for_superuser(self):
        election = ElectionWithStatusFactory()
        user = get_user_model().objects.create(is_superuser=True)
        self.client.force_login(user=user)
        response = self.client.get(election.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit in admin")


class TestBallotsCsv(TestCase):
    def setUp(self):
        super().setUp()
        Election.private_objects.all().delete()

        self.election_group = ElectionWithStatusFactory(
            group=None,
            group_type="election",
            moderation_status=related_status("Approved"),
            election_id="local.2017-03-23",
        )
        self.org_group = ElectionWithStatusFactory(
            group=self.election_group,
            group_type="organisation",
            moderation_status=related_status("Approved"),
            election_id="local.org.2017-03-23",
        )
        self.ballot1 = ElectionWithStatusFactory(
            group=self.org_group,
            moderation_status=related_status("Approved"),
            election_id="local.org.div1.2017-03-23",
        )
        self.ballot2 = ElectionWithStatusFactory(
            group=self.org_group,
            moderation_status=related_status("Approved"),
            election_id="local.org.div2.2017-03-23",
        )

    def test_invalid_election_id(self):
        resp = self.client.get("/elections/does-not-exist/ballots_csv/")
        self.assertEqual(404, resp.status_code)

    def test_election_id_is_ballot(self):
        resp = self.client.get(
            f"/elections/{self.ballot1.election_id}/ballots_csv/"
        )
        self.assertEqual(404, resp.status_code)

    def test_valid_csv(self):
        resp = self.client.get(
            f"/elections/{self.election_group.election_id}/ballots_csv/"
        )
        self.assertEqual(200, resp.status_code)

        content = resp.content.decode()
        self.assertEqual(3, content.count("\n"))
