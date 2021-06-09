from unittest.mock import MagicMock

from elections import admin

from django.test import TestCase


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
                action(modeladmin=modeladmin, request=request, queryset=queryset)
                queryset.update.assert_called_once_with(current=is_current)
