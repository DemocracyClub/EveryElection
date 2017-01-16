from django.conf.urls import url

from .views import SupportedOrganisationsView, OrganisationsView

urlpatterns = [
    url(
        r'^$',
        SupportedOrganisationsView.as_view(),
        name='organisations_view'),
    url(
        r'^(?P<official_identifier>.+)/$',
        OrganisationsView.as_view(),
        name='organisation_view'),
]
