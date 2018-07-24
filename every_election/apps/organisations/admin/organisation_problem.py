from django.contrib import admin
from django.contrib.gis.db.models import Q
from django.db.models import Manager
from organisations.models import Organisation


class OrganisationProblemManager(Manager):

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(
            (
                # we always want Organisations to have at least
                # one related OrganisationGeography record
                Q(geographies=None)
            ) | (
                # usually if an Organisation has no related
                # DivsionSet records this is a problem
                Q(divisionset=None) &
                # although (as always), there are some exceptions to this..
                ~Q(organisation_type='combined-authority') &
                ~Q(organisation_type='police-area') &
                ~(
                    Q(organisation_type='local-authority') &
                    Q(official_name='Greater London Authority')
                )
            ) | (
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
        return ''

    class Meta:
        verbose_name_plural = "⚠️ Organisation Problems"
        proxy = True


class OrganisationProblemAdmin(admin.ModelAdmin):

    actions = None

    ordering = ('organisation_type', 'organisation_subtype', 'official_name', 'start_date')
    list_display = (
        'official_name',
        'start_date',
        'end_date',
        'problem_text',
    )
    readonly_fields = (
        'problem_text',
        'no_geography',
        'no_divisionset',
        'no_electedrole',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
