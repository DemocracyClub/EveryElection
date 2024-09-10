from django.core.management import BaseCommand
from organisations.models import OrganisationBoundaryReview


class Command(BaseCommand):
    help = (
        "One-off command to update boundary reviews with bad legislation links"
    )

    def handle(self, *args, **options):
        # The Carlisle (Electoral Changes) Order 2019
        self.update_review(
            653, "https://www.legislation.gov.uk/uksi/2019/280/contents/made"
        )
        # The North Somerset (Electoral Changes) Order 2014
        self.update_review(
            664, "https://www.legislation.gov.uk/uksi/2014/3291/contents/made"
        )

    def update_review(self, review_id, correct_legislation_url):
        review = OrganisationBoundaryReview.objects.get(id=review_id)
        old_link = review.legislation_url
        review.legislation_url = correct_legislation_url
        review.save()
        self.stdout.write(
            f"Updated legislation link for {review.generic_title} from {old_link} to {review.legislation_url}"
        )
