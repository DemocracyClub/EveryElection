from organisations.models import OrganisationDivision, OrganisationDivisionSet
from organisations.models.organisations import Organisation

# Create new divset for NIA
nia = Organisation.objects.get(official_identifier="nia")
new_divset = OrganisationDivisionSet.objects.create(
    organisation=nia,
    start_date="2027-05-06",
    short_title="2027 Boundaries",
    notes="Boundaries copied from 2025 parl boundaries",
)
# get queryset of NI divisions in 2025 parl boundaries
old_divset = OrganisationDivision.objects.filter(
    divisionset_id=755, territory_code="NIR"
)
# copy the divisions
for div in old_divset:
    div.pk = None
    # update seats
    div.seats_total = 5
    div.divisionset = new_divset
    div.save()
# copy the geographies
geographies = [(div.official_identifier, div.geography) for div in old_divset]
for gss, geog in geographies:
    div = OrganisationDivision.objects.get(
        official_identifier=gss, divisionset=new_divset
    )
    geog.pk = None
    geog.division_id = div.id
    geog.save()
    # attach it to the target division
    div.geography = geog
    div.save()
