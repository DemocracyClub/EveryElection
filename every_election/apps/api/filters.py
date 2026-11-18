import datetime

import django_filters
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now
from elections.models import Election
from organisations.models import (
    Organisation,
    OrganisationDivisionSet,
    OrganisationGeography,
)


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
            og_qs = og_qs.filter(
                Q(end_date__gt=now()) | Q(end_date=None)
            ).filter(Q(start_date__lt=now()) | Q(start_date=None))

        if "poll_open_date" in self.data and self.data["poll_open_date"]:
            og_qs = og_qs.filter(
                Q(start_date__lte=self.data["poll_open_date"])
                | Q(start_date=None)
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
            | Q(
                organisation_geography__geography__bboverlaps=og_qs.get().geography
            )
        ).prefetch_related("_children_qs")

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
        max_length="200",
    )
    exclude_election_id_regex = django_filters.CharFilter(
        label="Exclude elections by their election id using a regular expression",
        field_name="election_id",
        lookup_expr="regex",
        exclude=True,
        max_length="200",
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


class FlagWidget(forms.HiddenInput):
    """
    This leaves the flag widgets out of the form on the browesable api.
    The browesable page isn't available on prod, so is only a convenience locally.
    This is equivalent to `current` and `future` in the /elections/ endpoint

    TSubclasses HiddenInput so that the form doesn't render a label.
    """

    def render(self, name, value, attrs=None, renderer=None):
        return ""


class FlagField(forms.Field):
    """
    A query parameter that turns a filter on by being present.

    `?active` and `?active=` will work, but any value on
    the right raises a ValidationError.
    """

    widget = FlagWidget

    def to_python(self, value):
        if value is None:
            # flag field not included
            return None
        if value == "":
            # flag field included
            return True
        raise ValidationError(
            "This filter doesn't take a value. To apply it, include the parameter on its own.",
            code="invalid",
        )


class FlagFilter(django_filters.Filter):
    field_class = FlagField


class DivisionSetFilterForm(forms.Form):
    MUTUALLY_EXCLUSIVE = ("date", "active", "future")

    def clean(self):
        """
        `date`, `active` and `future` each restrict division sets by
        date, so at most one of them may be supplied. This applies even
        when a combination could be satisfied (date=<today>&active)
        so that the rule is easy to describe.

        This checks cleaned values, not the raw query string, because
        an empty `date` is ignored but an empty `active` or `future`
        turns that flag on.
        """
        cleaned_data = super().clean()
        supplied = [
            name for name in self.MUTUALLY_EXCLUSIVE if cleaned_data.get(name)
        ]
        if len(supplied) > 1:
            raise ValidationError(
                "Only one of 'date', 'active' and 'future' can be used "
                f"in a request, but this request has {len(supplied)}: "
                + ", ".join(f"'{name}'" for name in supplied),
                code="mutually_exclusive",
            )
        return cleaned_data


class DivisionSetFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        method="date_filter",
        label="Only division sets active on this date (yyyy-mm-dd)",
    )
    active = FlagFilter(
        method="active_filter",
        label="Only division sets active today",
    )
    future = FlagFilter(
        method="future_filter",
        label="Only division sets with start_date > today",
    )
    organisation_type = django_filters.ChoiceFilter(
        field_name="organisation__organisation_type",
        lookup_expr="exact",
        choices=Organisation.ORGTYPES,
    )

    def date_filter(self, queryset, name, value):
        return queryset.filter_by_date(value)

    def active_filter(self, queryset, name, value):
        return queryset.filter_by_date(datetime.date.today())

    def future_filter(self, queryset, name, value):
        return queryset.filter(start_date__gt=datetime.date.today())

    class Meta:
        model = OrganisationDivisionSet
        form = DivisionSetFilterForm
        fields = []
