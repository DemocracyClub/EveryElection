from datetime import datetime
from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import Q
from django.db.models import Manager
from organisations.models import Organisation, OrganisationDivision
from .common import CustomOrganisationChoiceField, INVALID_SOURCES


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
            ) | (
                # if the division has a GSS code,
                # the boundary source should be BoundaryLine/OSNI
                Q(geography__source__in=INVALID_SOURCES) &
                Q(official_identifier__startswith='gss:')
            ) | (
                # once a division is current (or past)
                # it should have a GSS code
                # ... mostly
                ~Q(official_identifier__startswith='gss:') &
                ~Q(division_type='CED') &
                ~Q(division_type='NIE')
            )
        )
        return qs


class DivisionProblem(OrganisationDivision):

    objects = DivisionProblemManager()

    @property
    def no_gss_code(self):
        return self.official_identifier[:4] != 'gss:'

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
        return ''

    class Meta:
        verbose_name_plural = "⚠️ Division Geography Problems"
        proxy = True


class DivisionProblemForm(forms.ModelForm):
    organisation = CustomOrganisationChoiceField(
        queryset=Organisation.objects.all())

    class Meta:
        model = DivisionProblem
        fields = '__all__'


class DivisionProblemAdmin(admin.ModelAdmin):

    actions = None

    ordering = ('organisation', 'divisionset', 'name')
    list_display = (
        'official_identifier',
        'name',
        'organisation',
        'divisionset',
        'problem_text',
    )
    readonly_fields = (
        'problem_text',
        'no_gss_code',
        'invalid_source',
        'no_geography',
    )
    form = DivisionProblemForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).defer('geography')
