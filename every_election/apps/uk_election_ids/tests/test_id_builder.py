from datetime import date
from unittest import TestCase
from uk_election_ids.election_ids import IdBuilder


class TestIdBuilder(TestCase):

    def test_invalid_election_type(self):
        with self.assertRaises(ValueError):
            IdBuilder('foo', date(2018, 5, 3))

    def test_invalid_dates(self):
        with self.assertRaises(ValueError):
            IdBuilder('parl', 'not a date')
        with self.assertRaises(ValueError):
            IdBuilder('parl', '2017-02-31')  # 31st Feb is not a date

    def test_string_date(self):
        id = IdBuilder('parl', '2018-05-03')
        election_id = id.election_group_id
        self.assertEqual('parl.2018-05-03', election_id)

    def test_naw_sp_without_subtype(self):
        for election_type in ('naw', 'sp'):
            id = IdBuilder(election_type, date(2018, 5, 3))\
                .with_division('test-division')
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            with self.assertRaises(ValueError):
                id.subtype_group_id
            with self.assertRaises(ValueError):
                id.organisation_group_id
            with self.assertRaises(ValueError):
                id.ballot_id
            self.assertEqual(["%s.2018-05-03" % (election_type)], id.ids)

    def test_naw_sp_invalid_subtype(self):
        for election_type in ('naw', 'sp'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_subtype('x')

    def test_naw_sp_valid_subtype_no_division(self):
        for election_type in ('naw', 'sp'):
            id = IdBuilder(election_type, date(2018, 5, 3))\
                .with_subtype('c')
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            subtype_id = id.subtype_group_id
            self.assertEqual("%s.c.2018-05-03" % (election_type), subtype_id)
            with self.assertRaises(ValueError):
                id.organisation_group_id
            with self.assertRaises(ValueError):
                id.ballot_id
            self.assertEqual([
                "%s.2018-05-03" % (election_type),
                "%s.c.2018-05-03" % (election_type),
            ], id.ids)

    def test_naw_sp_with_org(self):
        for election_type in ('naw', 'sp'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_organisation('test-org')

    def test_naw_sp_with_division(self):
        for election_type in ('naw', 'sp'):
            id = IdBuilder(election_type, date(2018, 5, 3))\
                .with_subtype('r')\
                .with_division('test-division')
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            subtype_id = id.subtype_group_id
            self.assertEqual("%s.r.2018-05-03" % (election_type), subtype_id)
            with self.assertRaises(ValueError):
                id.organisation_group_id
            ballot_id = id.ballot_id
            self.assertEqual("%s.r.test-division.2018-05-03" % (election_type), ballot_id)
            self.assertEqual([
                "%s.2018-05-03" % (election_type),
                "%s.r.2018-05-03" % (election_type),
                "%s.r.test-division.2018-05-03" % (election_type)
            ], id.ids)

    def test_nia_parl_with_org(self):
        for election_type in ('nia', 'parl'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_organisation('test-org')

    def test_nia_parl_with_subtype(self):
        for election_type in ('nia', 'parl'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_subtype('x')

    def test_nia_parl_no_div(self):
        for election_type in ('nia', 'parl'):
            id = IdBuilder(election_type, date(2018, 5, 3))
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            with self.assertRaises(ValueError):
                id.subtype_group_id
            with self.assertRaises(ValueError):
                id.organisation_group_id
            with self.assertRaises(ValueError):
                id.ballot_id
            self.assertEqual(["%s.2018-05-03" % (election_type)], id.ids)

    def test_nia_parl_with_div(self):
        for election_type in ('nia', 'parl'):
            id = IdBuilder(election_type, date(2018, 5, 3))\
                .with_division('test-division')
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            with self.assertRaises(ValueError):
                id.subtype_group_id
            with self.assertRaises(ValueError):
                id.organisation_group_id
            ballot_id = id.ballot_id
            self.assertEqual("%s.test-division.2018-05-03" % (election_type), ballot_id)
            self.assertEqual([
                "%s.2018-05-03" % (election_type),
                "%s.test-division.2018-05-03" % (election_type)
            ], id.ids)

    def test_local_with_subtype(self):
        with self.assertRaises(ValueError):
            IdBuilder('local', date(2018, 5, 3))\
                .with_subtype('x')

    def test_local_no_org_with_div(self):
        id = IdBuilder('local', date(2018, 5, 3))\
            .with_division('test-division')
        with self.assertRaises(ValueError):
            id.election_group_id
        with self.assertRaises(ValueError):
            id.subtype_group_id
        with self.assertRaises(ValueError):
            id.organisation_group_id
        with self.assertRaises(ValueError):
            id.ballot_id
        self.assertEqual([], id.ids)

    def test_local_no_org_no_div(self):
        id = IdBuilder('local', date(2018, 5, 3))
        election_id = id.election_group_id
        self.assertEqual("local.2018-05-03", election_id)
        with self.assertRaises(ValueError):
            id.subtype_group_id
        with self.assertRaises(ValueError):
            id.organisation_group_id
        with self.assertRaises(ValueError):
            id.ballot_id
        self.assertEqual(["local.2018-05-03"], id.ids)

    def test_local_with_org_no_div(self):
        id = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')
        election_id = id.election_group_id
        self.assertEqual("local.2018-05-03", election_id)
        with self.assertRaises(ValueError):
            id.subtype_group_id
        organisation_id = id.organisation_group_id
        self.assertEqual("local.test-org.2018-05-03", organisation_id)
        with self.assertRaises(ValueError):
            id.ballot_id
        self.assertEqual([
            "local.2018-05-03",
            "local.test-org.2018-05-03"
        ], id.ids)

    def test_local_with_org_with_div(self):
        id = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')
        election_id = id.election_group_id
        self.assertEqual("local.2018-05-03", election_id)
        with self.assertRaises(ValueError):
            id.subtype_group_id
        organisation_id = id.organisation_group_id
        self.assertEqual("local.test-org.2018-05-03", organisation_id)
        ballot_id = id.ballot_id
        self.assertEqual("local.test-org.test-division.2018-05-03", ballot_id)
        self.assertEqual([
            "local.2018-05-03",
            "local.test-org.2018-05-03",
            "local.test-org.test-division.2018-05-03"
        ], id.ids)

    def test_pcc_mayor_with_subtype(self):
        for election_type in ('pcc', 'mayor'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_subtype('x')

    def test_pcc_mayor_with_division(self):
        for election_type in ('pcc', 'mayor'):
            with self.assertRaises(ValueError):
                IdBuilder(election_type, date(2018, 5, 3))\
                    .with_division('test-division')

    def test_pcc_mayor_with_org(self):
        for election_type in ('pcc', 'mayor'):
            id = IdBuilder(election_type, date(2018, 5, 3))\
                .with_organisation('test-org')
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            with self.assertRaises(ValueError):
                id.subtype_group_id
            organisation_id = id.organisation_group_id
            ballot_id = id.ballot_id
            self.assertEqual("%s.test-org.2018-05-03" % (election_type), ballot_id)
            self.assertEqual(organisation_id, ballot_id)
            self.assertEqual([
                "%s.2018-05-03" % (election_type),
                "%s.test-org.2018-05-03" % (election_type)
            ], id.ids)

    def test_pcc_mayor_no_org(self):
        for election_type in ('pcc', 'mayor'):
            id = IdBuilder(election_type, date(2018, 5, 3))
            election_id = id.election_group_id
            self.assertEqual("%s.2018-05-03" % (election_type), election_id)
            with self.assertRaises(ValueError):
                id.subtype_group_id
            with self.assertRaises(ValueError):
                id.organisation_group_id
            with self.assertRaises(ValueError):
                id.ballot_id
            self.assertEqual([
                "%s.2018-05-03" % (election_type)
            ], id.ids)

    def test_gla_with_invalid_subtype(self):
        with self.assertRaises(ValueError):
            IdBuilder('gla', date(2018, 5, 3))\
                .with_subtype('x')

    def test_gla_without_subtype(self):
        id = IdBuilder('gla', date(2018, 5, 3))
        election_id = id.election_group_id
        self.assertEqual('gla.2018-05-03', election_id)
        with self.assertRaises(ValueError):
            id.subtype_group_id
        with self.assertRaises(ValueError):
            id.organisation_group_id
        with self.assertRaises(ValueError):
            id.ballot_id

    def test_gla_with_org(self):
        for subtype in ('a', 'c'):
            with self.assertRaises(ValueError):
                IdBuilder('gla', date(2018, 5, 3))\
                    .with_subtype(subtype)\
                    .with_organisation('test-org')

    def test_gla_additional_with_division(self):
        with self.assertRaises(ValueError):
            IdBuilder('gla', date(2018, 5, 3))\
                .with_subtype('a')\
                .with_division('test-div')

    def test_gla_unknown_subtype_with_division(self):
        with self.assertRaises(ValueError):
            IdBuilder('gla', date(2018, 5, 3))\
                .with_division('test-div')

    def test_gla_additional(self):
        id = IdBuilder('gla', date(2018, 5, 3))\
            .with_subtype('a')
        election_id = id.election_group_id
        self.assertEqual("gla.2018-05-03", election_id)
        subtype_id = id.subtype_group_id
        self.assertEqual("gla.a.2018-05-03", subtype_id)
        with self.assertRaises(ValueError):
            id.organisation_group_id
        ballot_id = id.ballot_id
        self.assertEqual("gla.a.2018-05-03", ballot_id)
        self.assertEqual([
            "gla.2018-05-03",
            "gla.a.2018-05-03"
        ], id.ids)

    def test_gla_constituency_with_division(self):
        id = IdBuilder('gla', date(2018, 5, 3))\
            .with_subtype('c')\
            .with_division('test-div')
        election_id = id.election_group_id
        self.assertEqual("gla.2018-05-03", election_id)
        subtype_id = id.subtype_group_id
        self.assertEqual("gla.c.2018-05-03", subtype_id)
        with self.assertRaises(ValueError):
            id.organisation_group_id
        ballot_id = id.ballot_id
        self.assertEqual("gla.c.test-div.2018-05-03", ballot_id)
        self.assertEqual([
            "gla.2018-05-03",
            "gla.c.2018-05-03",
            "gla.c.test-div.2018-05-03"
        ], id.ids)

    def test_by_elections(self):
        for contest_type in ('by', 'BY', 'bY-elEction', 'by eLECTion'):
            id = IdBuilder('local', date(2018, 5, 3))\
                .with_organisation('test-org')\
                .with_division('test-division')\
                .with_contest_type(contest_type)
            election_id = id.election_group_id
            self.assertEqual("local.2018-05-03", election_id)
            organisation_id = id.organisation_group_id
            self.assertEqual("local.test-org.2018-05-03", organisation_id)
            ballot_id = id.ballot_id
            self.assertEqual("local.test-org.test-division.by.2018-05-03", ballot_id)
            self.assertEqual([
                "local.2018-05-03",
                "local.test-org.2018-05-03",
                "local.test-org.test-division.by.2018-05-03"
            ], id.ids)

    def test_explicit_contest_type(self):
        for contest_type in ('election', 'ELECTION'):
            id = IdBuilder('local', date(2018, 5, 3))\
                .with_organisation('test-org')\
                .with_division('test-division')\
                .with_contest_type(contest_type)
            election_id = id.election_group_id
            self.assertEqual("local.2018-05-03", election_id)
            organisation_id = id.organisation_group_id
            self.assertEqual("local.test-org.2018-05-03", organisation_id)
            ballot_id = id.ballot_id
            self.assertEqual("local.test-org.test-division.2018-05-03", ballot_id)
            self.assertEqual([
                "local.2018-05-03",
                "local.test-org.2018-05-03",
                "local.test-org.test-division.2018-05-03"
            ], id.ids)

    def test_invalid_contest_type(self):
        with self.assertRaises(ValueError):
            IdBuilder('local', date(2018, 5, 3))\
                .with_contest_type('foo')

    def test_eq_equal(self):
        obj1 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')
        obj2 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')
        self.assertEqual(obj1, obj2)

    def test_eq_not_equal(self):
        obj1 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')
        obj2 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')
        self.assertNotEqual(obj1, obj2)

    def test_eq_different_types(self):
        obj1 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')
        obj2 = 7
        self.assertNotEqual(obj1, obj2)

    def test_ref(self):
        with self.assertRaises(NotImplementedError):
            IdBuilder('ref', date(2018, 5, 3))

    def test_eu(self):
        with self.assertRaises(NotImplementedError):
            IdBuilder('eu', date(2018, 5, 3))

    def test_none(self):
        id = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division(None)
        self.assertEqual([
            "local.2018-05-03",
            "local.test-org.2018-05-03"
        ], id.ids)

    def test_empty(self):
        id = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('')
        self.assertEqual([
            "local.2018-05-03",
            "local.test-org.2018-05-03"
        ], id.ids)

    def test_slugger(self):
        id1 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('Test Org')\
            .with_division('Test Division')\
            .ballot_id
        id2 = IdBuilder('local', date(2018, 5, 3))\
            .with_organisation('test-org')\
            .with_division('test-division')\
            .ballot_id
        self.assertEqual(id1, id2)
