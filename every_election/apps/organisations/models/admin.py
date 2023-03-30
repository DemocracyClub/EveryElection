"""
Proxy models

These models exist so that we can present
more than one view of the same DB table in /admin
"""

from datetime import datetime
from django.contrib.gis.db.models import Q
from django.db.models import Manager
from .organisations import Organisation, OrganisationGeography
from .divisions import OrganisationDivision

INVALID_SOURCES = ("unknown", "lgbce", "")


class DivisionProblemManager(Manager):
    def get_queryset(self):
        qs = super().get_queryset()

        # some of these conditions are OK in forward-dated division(set)s
        # they only become an issue once they are current/past
        # so we'll ignore DivisionSets with a future start_date in this report
        qs = qs.filter(divisionset__start_date__lte=datetime.today())

        qs = qs.filter(
            (
                # we always want divisions to have
                # an associated geography record
                Q(geography=None)
            )
            | (
                # if the division has a GSS code,
                # the boundary source should be BoundaryLine/OSNI
                Q(geography__source__in=INVALID_SOURCES)
                & Q(official_identifier__startswith="gss:")
            )
            | (
                # once a division is current (or past)
                # it should have a GSS code
                # ... mostly
                ~Q(official_identifier__startswith="gss:")
                & ~Q(division_type="CED")
                & ~Q(division_type="NIE")
            )
        )
        return qs


class DivisionProblem(OrganisationDivision):
    objects = DivisionProblemManager()

    @property
    def no_gss_code(self):
        return self.official_identifier[:4] != "gss:"

    @property
    def invalid_source(self):
        try:
            return self.geography.source in INVALID_SOURCES
        except OrganisationDivision.geography.RelatedObjectDoesNotExist:
            return True

    @property
    def no_geography(self):
        try:
            return not self.geography
        except OrganisationDivision.geography.RelatedObjectDoesNotExist:
            return True

    @property
    def problem_text(self):
        if self.no_geography:
            return "No associated DivisionGeography"
        if self.no_gss_code:
            return "No GSS code"
        if self.invalid_source:
            return "Boundary source is invalid"
        return ""

    class Meta:
        verbose_name_plural = "⚠️ Division Geography Problems"
        proxy = True


class OrganisationProblemManager(Manager):
    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(
            (
                # we always want Organisations to have at least
                # one related OrganisationGeography record
                Q(geographies=None)
            )
            | (
                # usually if an Organisation has no related
                # DivsionSet records this is a problem
                Q(divisionset=None)
                &
                # although (as always), there are some exceptions to this..
                ~Q(organisation_type="combined-authority")
                & ~Q(organisation_type="police-area")
                & ~(
                    Q(organisation_type="local-authority")
                    & Q(official_name="Greater London Authority")
                )
            )
            | (
                # we always want Organisations to have at least
                # one related ElectedRole record
                Q(electedrole=None)
            )
        )

        return qs


class OrganisationProblem(Organisation):
    objects = OrganisationProblemManager()

    @property
    def no_geography(self):
        return len(self.geographies.all()) == 0

    @property
    def no_divisionset(self):
        return len(self.divisionset.all()) == 0

    @property
    def no_electedrole(self):
        return len(self.electedrole.all()) == 0

    @property
    def problem_text(self):
        if self.no_geography:
            return "No associated OrganisationGeography"
        if self.no_divisionset:
            return "No associated DivisionSet"
        if self.no_electedrole:
            return "No associated ElectedRole"
        return ""

    class Meta:
        verbose_name_plural = "⚠️ Organisation Problems"
        proxy = True


class OrganisationGeographyProblemManager(Manager):
    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(
            (
                # OrganisationGeographies should have a GSS code...mostly
                Q(gss="")
                & ~Q(organisation__organisation_type="police-area")
            )
            | (
                # OrganisationGeography with NULL
                # geography field is always a problem
                Q(geography=None)
            )
            | (
                # so is OrganisationGeography with
                # source != BoundaryLine/OSNI, etc
                Q(source__in=INVALID_SOURCES)
            )
        )

        return qs


class OrganisationGeographyProblem(OrganisationGeography):
    objects = OrganisationGeographyProblemManager()

    @property
    def no_gss_code(self):
        return self.gss == ""

    @property
    def no_geography(self):
        return not self.geography

    @property
    def invalid_source(self):
        return self.source in INVALID_SOURCES

    @property
    def problem_text(self):
        if self.no_geography:
            return "Geography field is NULL"
        if self.invalid_source:
            return "Boundary source is invalid"
        if self.no_gss_code:
            return "No GSS code"
        return ""

    class Meta:
        verbose_name_plural = "⚠️ Organisation Geography Problems"
        proxy = True
