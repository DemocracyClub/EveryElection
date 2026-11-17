from django.urls import include, re_path
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    DivisionSetViewSet,
    ElectionSubTypeViewSet,
    ElectionTypeViewSet,
    ElectionViewSet,
    OrganisationViewSet,
)

ORGANISATION_LOOKUP_REGEX = r"(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<date>\d{4}-\d{2}-\d{2})"


class EERouter(routers.DefaultRouter):
    def get_lookup_regex(self, viewset, lookup_prefix=""):
        # we identify organisations by
        # (organisation_type, official_identifier, start_date)
        # but DRF doesn't do composite keys
        # (much like the rest of django)
        # so it needs a bit of... gentle persuasion
        if viewset == OrganisationViewSet:
            return ORGANISATION_LOOKUP_REGEX
        return super().get_lookup_regex(viewset, lookup_prefix)


router = EERouter()
router.register(r"elections", ElectionViewSet)
router.register(r"election_types", ElectionTypeViewSet)
router.register(r"election_subtypes", ElectionSubTypeViewSet)
router.register(r"organisations", OrganisationViewSet)

routes = router.get_urls()

# Division sets are nested under the organisation they belong to and are
# identified by date, in the same way that organisations are.
# format_suffix_patterns adds a second pattern for each of these so that
# they can be requested with an extension like .json
divisionset_routes = format_suffix_patterns(
    [
        re_path(
            rf"^organisations/{ORGANISATION_LOOKUP_REGEX}/division_sets/(?P<divset_date>\d{{4}}-\d{{2}}-\d{{2}})/$",
            DivisionSetViewSet.as_view({"get": "retrieve"}),
            name="divisionset-detail",
        ),
    ]
)

urlpatterns = [
    re_path(r"^", include(routes)),
    re_path(r"^", include(divisionset_routes)),
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
