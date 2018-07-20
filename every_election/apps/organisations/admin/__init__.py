from django.contrib import admin
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationGeography
)
from .organisation import OrganisationAdmin
from .organisation_division import OrganisationDivisionAdmin
from .organisation_geography import OrganisationGeographyAdmin


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationDivision, OrganisationDivisionAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
