from unittest.mock import MagicMock

import mock
from django.test import TestCase
from elections import admin
from elections.models import ModerationHistory


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
        election_1 = MagicMock()
        election_2 = MagicMock()
        queryset = [election_1, election_2]
        request = MagicMock(user="michael")

        with mock.patch.object(ModerationHistory.objects, "create"):
            admin.soft_delete(
                modeladmin=MagicMock(), queryset=queryset, request=request
            )
            calls = [
                mock.call(
                    status_id="Deleted",
                    election=election_1,
                    user="michael",
                    notes="Bulk deleted via admin action",
                ),
                mock.call(
                    status_id="Deleted",
                    election=election_2,
                    user="michael",
                    notes="Bulk deleted via admin action",
                ),
            ]
            ModerationHistory.objects.create.assert_has_calls(calls)
