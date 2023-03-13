from typing import List

from django.core.management.base import BaseCommand

from organisations.models import Organisation, OrganisationDivision

GSS_TO_NATION = {
    "W": "WLS",
    "E": "ENG",
    "N": "NIR",
    "S": "SCT",
}


class Command(BaseCommand):
    help = """
    
    Sets the `territory_code` value for any division that doesn't have one.
    
    Uses UK parliamentary constituencies as the "parent" and looks for any division 
    (from any divisionset) that is fully covered by the parent.
    
    This is chosen over `overlaps` to catch two cases:
    
    1. Where a division actually does span two UK nations. This is currently thought 
       never to happen, but if it ever did this script would create a race condition 
       that would confuse everyone
       
    2. More likely, when a boundary has minor errors that cause it to cross the boarder.
       This could also create race conditions where we wrongly assign a division to a 
       nation depending on the order we loop over the constituencies.  
    """

    def handle(self, *args, **options):
        # Step 1: Set all CEDs to ENG, as CEDs are only ever in England
        self.stdout.write("Updating from CEDs")
        OrganisationDivision.objects.filter(division_type="CED").filter(
            territory_code=""
        ).update(territory_code="ENG")

        # Step 2: Guess from GSS codes
        self.stdout.write("Guessing from GSS codes")
        self.guess_from_gss()

        # Step 3: Use constituencies as parents. This catches a load of divisions
        # without using too much CPU to find them
        self.stdout.write("Assigning form parl constituencies")
        parl = Organisation.objects.get(slug="parl")
        constituencies: List[OrganisationDivision] = (
            parl.divisionset.get(start_date="2010-05-06")
            .divisions.all()
            .select_related("geography")
        )
        for constituency in constituencies:
            self.assign_territory_code(constituency)

        # Step 4: Loop over all remaining divisions and find a parent with a known code
        self.stdout.write("Assigning from parents")
        self.assign_from_parents()

        # Step 5: Loop over all remaining divisions and find a parent by the centre
        # of the geography
        self.stdout.write("Assigning from parents by centres")
        self.assign_by_centre()

        divisions_missing_territory_code = OrganisationDivision.objects.filter(
            territory_code=""
        )
        if divisions_missing_territory_code.exists():
            missing_count = divisions_missing_territory_code.count()
            self.stdout.write(
                f"WARNING: {missing_count} are STILL missing a territory_code "
            )
        else:
            self.stdout.write("GOOD NEWS! All divisions have a territory code.")

    def guess_from_gss(self):
        divisions = OrganisationDivision.objects.filter(
            territory_code__in=["", None]
        ).filter(official_identifier__startswith="gss:")

        for division in divisions:
            gss_prefix = division.official_identifier.split(":")[1][0]
            division.territory_code = GSS_TO_NATION[gss_prefix]
            division.save()

    def assign_territory_code(self, parent: OrganisationDivision):
        if not parent.territory_code:
            raise ValueError(f"{parent} doesn't have a territory_code!")

        return (
            OrganisationDivision.objects.filter(
                geography__geography__coveredby=parent.geography.geography
            )
            .filter(territory_code="")
            .update(territory_code=parent.territory_code)
        )

    def assign_from_parents(self):
        divisions_missing_territory_code = OrganisationDivision.objects.filter(
            territory_code__in=["", None]
        ).select_related("geography")

        for division in divisions_missing_territory_code:
            parents = (
                OrganisationDivision.objects.exclude(territory_code__in=["", None])
                .filter(geography__geography__intersects=division.geography.geography)
                .filter(divisionset__organisation__slug__in=["parl", "europarl"])
            )
            if not parents.exists():
                self.stdout.write(f"WARNING: No parents for {division}")
                print(
                    OrganisationDivision.objects.exclude(
                        territory_code__in=["", None]
                    ).filter(geography__geography__covers=division.geography.geography)
                )

                continue

            division.territory_code = parents.first().territory_code
            division.save()

    def assign_by_centre(self):
        divisions_missing_territory_code = OrganisationDivision.objects.filter(
            territory_code__in=["", None]
        ).select_related("geography")

        for division in divisions_missing_territory_code:
            centre = division.geography.geography.centroid
            parents = (
                OrganisationDivision.objects.exclude(territory_code__in=["", None])
                .filter(geography__geography__contains=centre)
                .filter(divisionset__organisation__slug__in=["parl", "europarl"])
            )
            codes = set([parent.territory_code for parent in parents])
            if len(codes) > 1:
                self.stdout.write(
                    f"WARNING: {division} has more than one territory: {parents} / {codes}"
                )
                continue
            division.territory_code = parents.first().territory_code
            division.save()
