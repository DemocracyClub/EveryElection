from django.test import TestCase

from io import StringIO
import mock

from .factories import ElectionWithStatusFactory

from elections.models import Election
from elections.management.commands import attach_posts_per_election_from_csv

COMMAND_PATH = \
    "elections.management.commands.attach_posts_per_election_from_csv.Command"


class TestAttachPostsPerWard(TestCase):
    def setUp(self):
        # This will make one more election object as a parent
        ElectionWithStatusFactory.create_batch(5, seats_contested=None)

        self.fake_csv_data = []
        for election in Election.public_objects.filter(group_type=None):
            self.fake_csv_data.append(
                {
                    'created': 'yes',
                    'id': election.election_id,
                    'posts up': 1,
                    'seats_total': 2
                }
            )

        self.default_options = {
            'replace_seats_total': False,
            'skip_unknown': False,
        }

    @mock.patch(COMMAND_PATH + '.load_data')
    def test_set_seats_total(self, fake_load_csv_data):
        fake_load_csv_data.return_value = self.fake_csv_data
        command_class = attach_posts_per_election_from_csv.Command
        command = command_class()
        command.stdout = StringIO(newline=None)

        options = self.default_options
        options['replace_seats_total'] = True
        command.handle(**options)
        self.assertTrue(command.stdout.getvalue().startswith('Taking '))

    @mock.patch(COMMAND_PATH + '.load_data')
    def test_raise_on_seats_total(self, fake_load_csv_data):
        fake_load_csv_data.return_value = self.fake_csv_data
        command_class = attach_posts_per_election_from_csv.Command
        command = command_class()
        command.stdout = StringIO()

        options = self.default_options
        with self.assertRaises(ValueError):
            command.handle(**options)
        self.assertEqual(command.stdout.getvalue(), '')

    @mock.patch(COMMAND_PATH + '.load_data')
    def test_too_many_contested_seats(self, fake_load_csv_data):
        election = ElectionWithStatusFactory(seats_total=1)
        election.division.seats_total = 1
        election.division.save()
        fake_data = [
            {
                'created': 'yes',
                'id': election.election_id,
                'posts up': 200,
                'seats_total': 1
            }
        ]

        fake_load_csv_data.return_value = fake_data
        command_class = attach_posts_per_election_from_csv.Command
        command = command_class()
        command.stdout = StringIO()

        options = self.default_options
        with self.assertRaisesRegexp(ValueError, "seats total less than "):
            command.handle(**options)


    @mock.patch(COMMAND_PATH + '.load_data')
    def test_skip_unknown(self, fake_load_csv_data):
        election = ElectionWithStatusFactory(seats_total=None)
        fake_data = [
            {
                'created': 'yes',
                'id': election.election_id,
                'posts up': None,
                'seats_total': None
            }
        ]

        fake_load_csv_data.return_value = fake_data
        command_class = attach_posts_per_election_from_csv.Command
        command = command_class()
        command.stdout = StringIO()

        options = self.default_options
        with self.assertRaisesRegexp(ValueError, "Seats total not known for"):
            command.handle(**options)

        options['skip_unknown'] = True
        command.handle(**options)
