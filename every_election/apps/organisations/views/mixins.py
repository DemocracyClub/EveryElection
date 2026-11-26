from core.helpers import parse_url_date
from django.http import Http404
from organisations.models import Organisation, OrganisationDivisionSet


class DivisionSetLookupMixin:
    """
    Finds a division set from the URL kwargs `organisation_type`,
    `official_identifier`, `date` and `divset_date`. Works in Django and
    DRF views.

    Neither date has to be a start date: `date` matches the organisation
    that existed on that date, and `divset_date` matches that
    organisation's division set that was active on that date.

    Override get_organisation_queryset() to choose which organisations
    can be found. The default excludes provisional organisations.
    """

    def get_organisation_queryset(self):
        return Organisation.public_objects.all()

    def get_organisation(self) -> Organisation:
        try:
            return self.get_organisation_queryset().get_by_date(
                organisation_type=self.kwargs["organisation_type"],
                official_identifier=self.kwargs["official_identifier"],
                date=parse_url_date(self.kwargs["date"]),
            )
        except Organisation.DoesNotExist:
            raise Http404()

    def get_divisionset_queryset(self, organisation: Organisation):
        """
        The division sets of `organisation` that get_divisionset()
        chooses from. Override to annotate them.
        """
        # The related manager sets each division set's `organisation`
        # to this instance, so building its URL doesn't fetch it again.
        return organisation.divisionset.all()

    def get_divisionset(self) -> OrganisationDivisionSet:
        organisation = self.get_organisation()
        try:
            return (
                self.get_divisionset_queryset(organisation)
                .filter_by_date(parse_url_date(self.kwargs["divset_date"]))
                .get()
            )
        except OrganisationDivisionSet.DoesNotExist:
            raise Http404()
