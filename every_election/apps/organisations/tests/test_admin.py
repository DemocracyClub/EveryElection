from django.test import TestCase

from organisations.models import (
    DivisionProblem,
    OrganisationProblem,
    OrganisationGeographyProblem,
)

from organisations.tests.factories import (
    DivisionGeographyFactory,
    OrganisationFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationGeographyFactory,
)
from elections.tests.factories import ElectedRoleFactory


class OrganisationProblemTests(TestCase):
    def test_no_geography(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertTrue(problem.no_geography)
        self.assertFalse(problem.no_divisionset)
        self.assertFalse(problem.no_electedrole)
        self.assertEqual("No associated OrganisationGeography", problem.problem_text)

    def test_no_divisionset(self):
        org = OrganisationFactory()
        OrganisationGeographyFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.no_divisionset)
        self.assertFalse(problem.no_electedrole)
        self.assertEqual("No associated DivisionSet", problem.problem_text)

    def test_no_electedrole(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        OrganisationGeographyFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.no_divisionset)
        self.assertTrue(problem.no_electedrole)
        self.assertEqual("No associated ElectedRole", problem.problem_text)

    def test_all_ok(self):
        org = OrganisationFactory()
        OrganisationDivisionSetFactory(organisation=org)
        OrganisationGeographyFactory(organisation=org)
        ElectedRoleFactory(organisation=org)

        self.assertEqual(len(OrganisationProblem.objects.all()), 0)

    def test_all_broken(self):
        OrganisationFactory()

        self.assertEqual(len(OrganisationProblem.objects.all()), 1)
        problem = OrganisationProblem.objects.all()[0]
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.no_divisionset)
        self.assertTrue(problem.no_electedrole)
        self.assertEqual("No associated OrganisationGeography", problem.problem_text)


class OrganisationGeographyProblemTests(TestCase):
    def test_no_gss_code(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.gss = ""
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)

    def test_no_geography(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.geography = None
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("Geography field is NULL", problem.problem_text)

    def test_invalid_source(self):
        og = OrganisationGeographyFactory()
        og.source = "unknown"
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Boundary source is invalid", problem.problem_text)

    def test_all_ok(self):
        og = OrganisationGeographyFactory()
        og.source = "this is totally fine"
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 0)

    def test_all_broken(self):
        og = OrganisationGeographyFactory()
        og.source = ""
        og.gss = ""
        og.geography = None
        og.save()
        self.assertEqual(len(OrganisationGeographyProblem.objects.all()), 1)
        problem = OrganisationGeographyProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Geography field is NULL", problem.problem_text)


class DivisionProblemTests(TestCase):
    def test_no_gss_code(self):
        div = OrganisationDivisionFactory()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "this is totally fine"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertFalse(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)

    def test_invalid_source(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "unknown"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertFalse(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("Boundary source is invalid", problem.problem_text)

    def test_no_geography(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertFalse(problem.no_gss_code)
        self.assertTrue(problem.no_geography)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("No associated DivisionGeography", problem.problem_text)

    def test_all_ok(self):
        div = OrganisationDivisionFactory()
        div.official_identifier = "gss:X01000001"
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = "this is totally fine"
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 0)

    def test_all_broken(self):
        div = OrganisationDivisionFactory()
        div.save()
        dg = DivisionGeographyFactory(division=div)
        dg.source = ""
        dg.save()
        self.assertEqual(len(DivisionProblem.objects.all()), 1)
        problem = DivisionProblem.objects.all()[0]
        self.assertTrue(problem.no_gss_code)
        self.assertTrue(problem.invalid_source)
        self.assertTrue(problem.invalid_source)
        self.assertEqual("No GSS code", problem.problem_text)
