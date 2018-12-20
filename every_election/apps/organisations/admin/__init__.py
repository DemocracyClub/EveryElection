from django.contrib import admin
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
    OrganisationGeography,
)
from .division_problem import DivisionProblem, DivisionProblemAdmin
from .organisation_problem import OrganisationProblem, OrganisationProblemAdmin
from .organisation_geography_problem import (
    OrganisationGeographyProblem,
    OrganisationGeographyProblemAdmin,
)
from .organisation import OrganisationAdmin
from .organisation_division import OrganisationDivisionAdmin
from .organisation_divisionset import OrganisationDivisionSetAdmin
from .organisation_geography import OrganisationGeographyAdmin


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationDivision, OrganisationDivisionAdmin)
admin.site.register(OrganisationDivisionSet, OrganisationDivisionSetAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
admin.site.register(DivisionProblem, DivisionProblemAdmin)
admin.site.register(OrganisationProblem, OrganisationProblemAdmin)
admin.site.register(OrganisationGeographyProblem, OrganisationGeographyProblemAdmin)
