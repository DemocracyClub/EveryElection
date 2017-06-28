from django.conf.urls import url
from election_snooper import views


urlpatterns = [
    url(r'^$',
        views.SnoopedElectionView.as_view(),
        name='snooped_election_view'),
]
