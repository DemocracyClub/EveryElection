from datetime import timedelta, datetime

from organisations.models import (
    OrganisationDivisionSet
)


def add_end_date_to_previous_div_sets(div_set):
    older_div_set = OrganisationDivisionSet.objects.filter(
        organisation=div_set.organisation,
        end_date=None,
        start_date__lt=div_set.start_date
    ).order_by('-start_date').first()
    if older_div_set:
        start_date = datetime.strptime(str(div_set.start_date), "%Y-%m-%d")
        older_div_set.end_date = start_date - timedelta(days=1)
        older_div_set.save()
