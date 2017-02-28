from django.test import TestCase

from elections.models import Election

from .base_tests import BaseElectionCreatorMixIn


class TestCreateIds(BaseElectionCreatorMixIn, TestCase):

    def run_test_with_data(self, all_data, expected_ids):
        self.create_ids(all_data)
        print(all_data)
        # self.assertEqual(Election.objects.count(), len(expected_ids))
        for expected_id in expected_ids:
            self.assertTrue(
                Election.objects.filter(election_id=expected_id).exists())

    def test_group_id(self):
        self.run_test_with_data(
            self.base_data,
            ['local.2017-02-24', ]
        )

    def test_creates_div_data_ids(self):
        self.assertEqual(Election.objects.count(), 0)
        all_data = {
            'election_organisation': [self.org1, ],
            'election_type': self.election_type1,
            'date': self.date,
        }
        all_data.update({'1__1': 'contested'})
        expected_ids = [
            'local.2017-02-24',
            'local.test.2017-02-24',
            'local.test.test-div.2017-02-24',
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_div_data_ids_1(self):
        self.assertEqual(Election.objects.count(), 0)
        all_data = {
            'election_organisation': [self.org1, ],
            'election_type': self.election_type1,
            'date': self.date,
        }
        all_data.update({'1__1': 'contested'})
        expected_ids = [
            'local.2017-02-24',
            'local.test.2017-02-24',
            'local.test.test-div.2017-02-24',
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    # def test_creates_div_data_ids_with_blank_div(self):
    #     all_data = self.base_data
    #
    #     all_data.update({
    #         '1__1': 'contested',
    #         # '1__2': ''
    #     })
    #     expected_ids = [
    #         'local.2017-02-24',
    #         'local.test.2017-02-24',
    #         'local.test.test-div.2017-02-24',
    #     ]
    #
    #     self._test_with_data(
    #         all_data,
    #         expected_ids
    #     )
    #
