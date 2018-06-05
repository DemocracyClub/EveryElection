from django.conf.urls import url

from .views import (
    SupportedOrganisationsView,
    OrganisationCompatibilityView,
    OrganisationDetailView,
    OrganisationsFilterView,
)


urlpatterns = [
    url(
        r'^$',
        SupportedOrganisationsView.as_view(),
        name='organisations_view'),

    # canonical URL for a single organisation record
    url(
        r'^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<start_date>\d{4}-\d{2}-\d{2})/$',
        OrganisationDetailView.as_view(),
        name='organisation_view'),

    # a list of 'generations' of an organisation
    url(
        r'^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/$',
        OrganisationsFilterView.as_view(),
        name='organisations_filter_view'),

    # attempt to redirect for backwards-compatibility
    url(
        r'^(?P<official_identifier>[-\w]+)/$',
        OrganisationCompatibilityView.as_view(),
        name='organisation_compatibility_view'),
]
