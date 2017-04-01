from django.conf.urls import url
from .views import (SnoopedElectionView, )


urlpatterns = [
    url(r'^$',
        SnoopedElectionView.as_view(),
        name='snooped_election_view'),
]
