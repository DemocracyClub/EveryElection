from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import Q
from django.db.models import Manager
from organisations.models import Organisation, OrganisationGeography
from .common import CustomOrganisationChoiceField, invalid_sources


class OrganisationGeographyProblemManager(Manager):

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(
            (
                # OrganisationGeographies should have a GSS code...mostly
                Q(gss='') & ~Q(organisation__organisation_type='police-area')
            ) | (
                # OrganisationGeography with NULL
                # geography field is always a problem
                Q(geography=None)
            ) | (
                # so is OrganisationGeography with source != BoundaryLine
                Q(source__in=invalid_sources)
            )
        )

        return qs


class OrganisationGeographyProblem(OrganisationGeography):

    objects = OrganisationGeographyProblemManager()

    @property
    def no_gss_code(self):
        return self.gss == ''

    @property
    def no_geography(self):
        return not self.geography

    @property
    def invalid_source(self):
        return self.source in invalid_sources

    @property
    def problem_text(self):
        if self.no_geography:
            return "Geography field is NULL"
        if self.invalid_source:
            return "Boundary source is invalid"
        if self.no_gss_code:
            return "No GSS code"
        return ''

    class Meta:
        verbose_name_plural = "⚠️ Organisation Geography Problems"
        proxy = True


class OrganisationGeographyProblemAdminForm(forms.ModelForm):
    organisation = CustomOrganisationChoiceField(
        queryset=Organisation.objects.all())

    class Meta:
        model = OrganisationGeographyProblem
        fields = '__all__'


class OrganisationGeographyProblemAdmin(admin.ModelAdmin):

    actions = None

    ordering = ('source', 'gss', 'start_date')
    list_display = (
        '__str__',
        'problem_text',
    )
    readonly_fields = (
        'problem_text',
        'no_gss_code',
        'invalid_source',
        'no_geography',
    )
    exclude = ('geography',)
    form = OrganisationGeographyProblemAdminForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
