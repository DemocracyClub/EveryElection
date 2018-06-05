from django.conf.urls import url, include

from rest_framework import routers

from .views import (ElectionViewSet, ElectionTypeViewSet,
                    ElectionSubTypeViewSet, OrganisationViewSet)


class OrganisationRouter(routers.DefaultRouter):

    include_root_view = False

    def get_lookup_regex(self, viewset, lookup_prefix=''):
        # we identify organisations by
        # (organisation_type, official_identifier, start_date)
        # but DRF doesn't do composite keys
        # (much like the rest of django)
        # so it needs a bit of... gentle persuasion
        return r'(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<start_date>\d{4}-\d{2}-\d{2})'


default_router = routers.DefaultRouter()
default_router.register(r'elections', ElectionViewSet)
default_router.register(r'election_types', ElectionTypeViewSet)
default_router.register(r'election_subtypes', ElectionSubTypeViewSet)
default_router.register(r'organisations', OrganisationViewSet)

org_router = OrganisationRouter()
org_router.register(r'organisations', OrganisationViewSet)

routes = default_router.get_urls() + org_router.get_urls()

urlpatterns = [
    url(r'^', include(routes)),
]
