from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from elections import admin
from elections.models import ModerationHistory, ModerationStatuses
from elections.tests.factories import ElectionFactory


class TestAdminActions(TestCase):
    def test_change_current(self):
        """
        Test that when admin actions to update current flag are
        called, update is called with the relevant value
        """
        modeladmin = MagicMock()
        request = MagicMock()
        admin_actions = [
            (admin.mark_current, True),
            (admin.mark_not_current, False),
            (admin.unset_current, None),
        ]
        for admin_action in admin_actions:
            action = admin_action[0]
            is_current = admin_action[1]
            queryset = MagicMock()
            with self.subTest(msg=action.short_description):
                action(
                    modeladmin=modeladmin, request=request, queryset=queryset
                )
                queryset.update.assert_called_once_with(current=is_current)

    def test_soft_delete(self):
        election_1 = ElectionFactory()
        election_2 = ElectionFactory()
        queryset = [election_1, election_2]
        user = get_user_model().objects.create(is_superuser=True)
        request = MagicMock(user=user)

        admin.soft_delete(
            modeladmin=MagicMock(), queryset=queryset, request=request
        )

        assert (
            len(
                ModerationHistory.objects.filter(
                    election_id__in=[election_1.pk, election_2.pk],
                    status_id=ModerationStatuses.deleted.value,
                )
            )
            == 2
        )
