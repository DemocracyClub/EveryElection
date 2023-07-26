from django.contrib import admin
from organisations.models import (
    DivisionProblem,
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
    OrganisationGeography,
    OrganisationGeographyProblem,
    OrganisationProblem,
)
from organisations.views.admin.division_problem import DivisionProblemAdmin
from organisations.views.admin.organisation_problem import (
    OrganisationProblemAdmin,
)
from organisations.views.admin.organisation_geography_problem import (
    OrganisationGeographyProblemAdmin,
)
from organisations.views.admin.organisation import OrganisationAdmin
from organisations.views.admin.organisation_division import (
    OrganisationDivisionAdmin,
)
from organisations.views.admin.organisation_divisionset import (
    OrganisationDivisionSetAdmin,
)
from organisations.views.admin.organisation_geography import (
    OrganisationGeographyAdmin,
)


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationDivision, OrganisationDivisionAdmin)
admin.site.register(OrganisationDivisionSet, OrganisationDivisionSetAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
admin.site.register(DivisionProblem, DivisionProblemAdmin)
admin.site.register(OrganisationProblem, OrganisationProblemAdmin)
admin.site.register(
    OrganisationGeographyProblem, OrganisationGeographyProblemAdmin
)
