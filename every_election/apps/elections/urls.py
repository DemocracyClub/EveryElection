from django.conf.urls import url

from .views import ElectionTypesView

urlpatterns = [
    url(
        r'^$',
        ElectionTypesView.as_view(),
        name='election_types_view'),
]
