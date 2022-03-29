import django_filters
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now

from elections.models import Election
from organisations.models import OrganisationGeography


class ElectionFilter(django_filters.FilterSet):
    def election_intersects_local_authority_filter(self, queryset, name, value):

        og_qs = OrganisationGeography.objects.filter(
            organisation__official_identifier=value,
            organisation__organisation_type="local-authority",
        ).select_related("organisation")

        if not og_qs.exists():
            raise ValidationError(
                """Only local authorities supported""",
                code="invalid",
            )

        if self.data.get("future", False):
            og_qs = og_qs.filter(Q(end_date__gt=now()) | Q(end_date=None)).filter(
                Q(start_date__lt=now()) | Q(start_date=None)
            )

        if "poll_open_date" in self.data and self.data["poll_open_date"]:
            og_qs = og_qs.filter(
                Q(start_date__lte=self.data["poll_open_date"]) | Q(start_date=None)
            )

        if (
            "organisation_start_date" in self.data
            and self.data["organisation_start_date"]
        ):
            og_qs = og_qs.filter(
                Q(start_date__lte=self.data["organisation_start_date"])
                | Q(start_date=None)
            )

        try:
            og_qs.get()
        except OrganisationGeography.MultipleObjectsReturned:
            raise ValidationError(
                """Organisation has more than one geography,
                please specify a `poll_open_date` or organisation_start_date""",
                code="invalid",
            )
        except OrganisationGeography.DoesNotExist:
            return og_qs

        return queryset.filter(
            Q(division_geography__geography__bboverlaps=og_qs.get().geography)
            | Q(organisation_geography__geography__bboverlaps=og_qs.get().geography)
        )

    organisation_identifier = django_filters.CharFilter(
        field_name="organisation__official_identifier",
        lookup_expr="exact",
    )
    organisation_type = django_filters.CharFilter(
        field_name="organisation__organisation_type",
        lookup_expr="exact",
    )
    election_intersects_local_authority = django_filters.CharFilter(
        label="Election intersects local authority",
        method="election_intersects_local_authority_filter",
    )
    organisation_start_date = django_filters.DateFilter(
        field_name="organisation__start_date",
        lookup_expr="exact",
    )
    election_id_regex = django_filters.CharFilter(
        label="Filter elections by their election id using a regular expression",
        field_name="election_id",
        lookup_expr="regex",
        max_length="20",
    )
    exclude_election_id_regex = django_filters.CharFilter(
        label="Exclude elections by their election id using a regular expression",
        field_name="election_id",
        lookup_expr="regex",
        exclude=True,
        max_length="20",
    )
    modified = django_filters.IsoDateTimeFilter(
        field_name="modified",
        lookup_expr="gt",
        help_text="An ISO datetime",
    )

    class Meta:
        model = Election
        fields = {
            "group_type": ["exact"],
            "poll_open_date": ["exact", "gte", "lte"],
        }
