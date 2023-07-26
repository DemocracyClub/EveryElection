from django.urls import re_path
from election_snooper import views


urlpatterns = [
    re_path(
        r"^$", views.SnoopedElectionView.as_view(), name="snooped_election_view"
    ),
    re_path(
        r"^moderation_queue/$",
        views.ModerationQueueView.as_view(),
        name="election_moderation_queue",
    ),
]
