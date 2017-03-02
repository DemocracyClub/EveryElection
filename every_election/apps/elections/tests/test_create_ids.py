from django.test import TestCase

from elections.models import Election

from .base_tests import BaseElectionCreatorMixIn


class TestCreateIds(BaseElectionCreatorMixIn, TestCase):

    def run_test_with_data(self, all_data, expected_ids):
        self.create_ids(all_data)
        self.assertEqual(Election.objects.count(), len(expected_ids))
        for expected_id in expected_ids:
            self.assertTrue(
                Election.objects.filter(election_id=expected_id).exists())

    def test_group_id(self):
        self.run_test_with_data(
            self.base_data,
            ['local.'+self.date_str, ]
        )

    def test_creates_div_data_ids(self):
        self.assertEqual(Election.objects.count(), 0)
        all_data = self.base_data
        all_data.update({self.make_div_id(): 'contested'})
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_div_data_ids_two_divs(self):
        all_data = self.base_data

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): 'contested',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
            'local.test.test-div-2.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_div_data_ids_blank_divs(self):
        all_data = self.base_data

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): '',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

