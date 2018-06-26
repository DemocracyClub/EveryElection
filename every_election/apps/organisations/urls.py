from django.conf.urls import url

from .views import (
    SupportedOrganisationsView,
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
        r'^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
        OrganisationDetailView.as_view(),
        name='organisation_view'),

    # a list of 'generations' of an organisation
    url(
        r'^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/$',
        OrganisationsFilterView.as_view(),
        name='organisations_filter_by_identifier'),

    # list of organisations of a given type
    url(
        r'^(?P<organisation_type>[-\w]+)/$',
        OrganisationsFilterView.as_view(),
        name='organisations_filter_by_type'),
]
