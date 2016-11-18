from django.conf.urls import url, include

from rest_framework import routers

from .views import (ElectionViewSet, ElectionTypeViewSet,
                    ElectionSubTypeViewSet, OrganisationViewSet)

router = routers.DefaultRouter()
router.register(r'elections', ElectionViewSet)
router.register(r'election_types', ElectionTypeViewSet)
router.register(r'election_subtypes', ElectionSubTypeViewSet)
router.register(r'organisations', OrganisationViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
