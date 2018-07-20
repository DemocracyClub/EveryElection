from django.contrib import admin
from django.contrib.gis.db.models import Q
from organisations.models import OrganisationGeography
from .common import invalid_sources


class OrganisationGeographyProblem(OrganisationGeography):

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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)

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
