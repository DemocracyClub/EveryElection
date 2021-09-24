import django_filters

from elections.models import Election


class ElectionFilter(django_filters.FilterSet):

    organisation_identifier = django_filters.CharFilter(
        field_name="organisation__official_identifier",
        lookup_expr="exact",
    )
    organisation_type = django_filters.CharFilter(
        field_name="organisation__organisation_type",
        lookup_expr="exact",
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

    class Meta:
        model = Election
        fields = {
            "group_type": ["exact"],
            "poll_open_date": ["exact", "gte", "lte"],
        }
