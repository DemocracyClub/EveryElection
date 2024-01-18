from urllib.parse import urlencode

import django_filters
from django.db.models import BLANK_CHOICE_DASH
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django_filters.widgets import LinkWidget

from .models import OrganisationBoundaryReview, ReviewStatus


class DSLinkWidget(LinkWidget):
    """
    The LinkWidget doesn't allow iterating over choices in the template layer
    to change the HTML wrappig the widget.

    This breaks the way that Django *should* work, so we have to subclass
    and alter the HTML in Python :/

    https://github.com/carltongibson/django-filter/issues/880
    """

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if not hasattr(self, "data"):
            self.data = {}
        if value is None:
            value = ""
        self.build_attrs(self.attrs, extra_attrs=attrs)
        output = []
        options = self.render_options(choices, [value], name)
        if options:
            output.append(options)
        # output.append('</ul>')
        return mark_safe("\n".join(output))

    def render_option(self, name, selected_choices, option_value, option_label):
        option_value = force_str(option_value)
        if option_label == BLANK_CHOICE_DASH[0][1]:
            option_label = "All"
        data = self.data.copy()
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
            "attrs": selected and ' aria-current="true"' or "",
            "query_string": url,
            "label": force_str(option_label),
        }


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
