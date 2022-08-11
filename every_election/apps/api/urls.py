from django.urls import include, re_path
from rest_framework import routers

from .views import (
    ElectionSubTypeViewSet,
    ElectionTypeViewSet,
    ElectionViewSet,
    OrganisationViewSet,
)


class EERouter(routers.DefaultRouter):
    def get_lookup_regex(self, viewset, lookup_prefix=""):
        # we identify organisations by
        # (organisation_type, official_identifier, start_date)
        # but DRF doesn't do composite keys
        # (much like the rest of django)
        # so it needs a bit of... gentle persuasion
        if viewset == OrganisationViewSet:
            return r"(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<date>\d{4}-\d{2}-\d{2})"
        return super().get_lookup_regex(viewset, lookup_prefix)


router = EERouter()
router.register(r"elections", ElectionViewSet)
router.register(r"election_types", ElectionTypeViewSet)
router.register(r"election_subtypes", ElectionSubTypeViewSet)
router.register(r"organisations", OrganisationViewSet)

routes = router.get_urls()

urlpatterns = [
    re_path(r"^", include(routes)),
    re_path(
        r"^organisations/(?P<organisation_type>[-\w]+)/$",
        OrganisationViewSet.as_view({"get": "filter"}),
    ),
    re_path(
        r"^organisations/(?P<organisation_type>[-\w]+)\.(?P<format>[a-z0-9]+)/?$",
        OrganisationViewSet.as_view({"get": "filter"}),
    ),
    re_path(
        r"^organisations/(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/$",
        OrganisationViewSet.as_view({"get": "filter"}),
    ),
    re_path(
        r"^organisations/(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)\.(?P<format>[a-z0-9]+)/?$",
        OrganisationViewSet.as_view({"get": "filter"}),
    ),
]
