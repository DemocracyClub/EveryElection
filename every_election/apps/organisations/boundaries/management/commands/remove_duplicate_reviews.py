from django.core.management import BaseCommand
from organisations.models import OrganisationBoundaryReview


class Command(BaseCommand):
    help = "One-off command to remove duplicated boundary reviews from database"

    # We have a bunch of duplicated boundary reviews in the database that had been caused by minor changes
    # to legislation titles on the LGCE site that our scraper was seeing as entirely new reviews.
    # This command removes the duplicated reviews that aren't attached to a divisionset because they are redundant,
    # and they causing the updated scraper to fail.
    def handle(self, *args, **options):
        ids = [
            774,
            836,
            904,
            926,
            762,
            767,
            783,
            798,
            818,
            821,
            829,
            846,
            848,
            862,
            864,
            876,
            881,
            887,
            899,
            905,
            820,
            828,
            842,
        ]
        OrganisationBoundaryReview.objects.filter(id__in=ids).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully removed {len(ids)} boundary reviews."
            )
        )
