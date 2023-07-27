from core.models import JsonbSet
from django.db.models import Value
from django.test import TestCase
from elections.models import Election
from elections.tests.factories import ElectionFactory


class TestJsonbSet(TestCase):
    def setUp(self):
        # This would be nice but couldn't make it play: https://code.djangoproject.com/ticket/7835#comment:46
        self.election = ElectionFactory()
        self.election2 = ElectionFactory()

    def test_update(self):
        qs = Election.private_objects.all()
        qs.update(
            tags=JsonbSet(
                "tags", Value('{"BAZ"}'), Value('{"bar": "foo"}'), True
            )
        )
        for election in qs:
            self.assertDictEqual(election.tags, {"BAZ": {"bar": "foo"}})

    def test_set_obj(self):
        self.election.tags = JsonbSet(
            "tags", Value('{"BAZ"}'), Value('{"bar": "foo"}'), True
        )
        self.election.save()
        self.election.refresh_from_db()
        self.assertDictEqual(self.election.tags, {"BAZ": {"bar": "foo"}})

    def test_set_value(self):
        # Test we can set a new value
        self.election.tags = JsonbSet(
            "tags", Value('{"BAZ"}'), Value('"foo"'), True
        )
        self.election.save()
        self.election.refresh_from_db()
        self.assertDictEqual(self.election.tags, {"BAZ": "foo"})

    def test_set_nested(self):
        self.election.tags = JsonbSet(
            "tags", Value('{"BAZ"}'), Value('{"bar": "foo"}'), True
        )
        self.election.save()
        self.election.refresh_from_db()
        self.assertDictEqual(self.election.tags, {"BAZ": {"bar": "foo"}})

        self.election.tags = JsonbSet(
            "tags", Value('{"BAZ","bar"}'), Value('"different_foo"'), True
        )
        self.election.save()
        self.election.refresh_from_db()
        self.assertDictEqual(
            self.election.tags, {"BAZ": {"bar": "different_foo"}}
        )

    def test_dont_create_missing(self):
        self.election.tags = JsonbSet(
            "tags", Value('{"BAZ","bar"}'), Value('"foo"'), False
        )
        self.election.save()
        self.election.refresh_from_db()
        self.assertEqual({}, self.election.tags)
