from django.conf.urls import url

from .views import SupportedOrganisationsView

urlpatterns = [
    url(
        r'^$',
        SupportedOrganisationsView.as_view(),
        name='organisations_view'),
]
