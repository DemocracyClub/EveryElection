from django.conf.urls import url

from .views import (
    AllElectionsView,
    CONDITION_DICT,
    ElectionTypesView,
    FORMS,
    IDCreatorWizard,
    ModerationQueueView,
    ReferenceDefinitionView,
    SingleElection,
)
from elections.views.sync import get_election_fixture


id_creator_wizard = IDCreatorWizard.as_view(
    FORMS,
    url_name='id_creator_step',
    done_step_name='home',
    condition_dict=CONDITION_DICT)


urlpatterns = [
    url(r'^election_types/$',
        ElectionTypesView.as_view(),
        name='election_types_view'),
    url(r'^reference_definition/$',
        ReferenceDefinitionView.as_view(),
        name='reference_definition_view'),

    url(r'^elections/$',
        AllElectionsView.as_view(),
        name='elections_view'),
    url(r'^elections/(?P<election_id>.+)/$',
        SingleElection.as_view(),
        name='single_election_view'),

    url(r'^id_creator/(?P<step>.+)/$', id_creator_wizard, name='id_creator_step'),
    url(r'^id_creator/$', id_creator_wizard, name='id_creator'),

    url(r'^sync/$', get_election_fixture),

    url(
        r'^moderation_queue/$',
        ModerationQueueView.as_view(),
        name='election_moderation_queue'
    ),
]
