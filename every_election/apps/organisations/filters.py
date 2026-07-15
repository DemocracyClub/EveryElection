import django_filters
from dc_utils.filter_widgets import DSLinkWidget

from .models import OrganisationBoundaryReview, ReviewStatus


class OrganisationBoundaryReviewFilter(django_filters.FilterSet):
    def organisation_filter(self, queryset, name, value):
        """
        Filter queryset by organisation
        """
        return queryset.filter(organisation__common_name__icontains=value)

    def status_filter(self, queryset, name, value):
        """
        Filter queryset by status
        """
        return queryset.filter(status=value)

    organisation = django_filters.CharFilter(
        label="organisation",
        method="organisation_filter",
    )

    status = django_filters.ChoiceFilter(
        label="status",
        widget=DSLinkWidget(),
        choices=ReviewStatus.choices,
    )

    class Meta:
        model = OrganisationBoundaryReview
        fields = [
            "status",
            "organisation",
        ]
