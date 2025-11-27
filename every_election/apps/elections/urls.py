from django.urls import re_path

from .views import (
    CONDITION_DICT,
    FORMS,
    AllElectionsView,
    BallotsCsv,
    ElectionTypesView,
    IDCreatorWizard,
    ReferenceDefinitionView,
    SingleElection,
)

id_creator_wizard = IDCreatorWizard.as_view(
    FORMS,
    url_name="id_creator_step",
    done_step_name="home",
    condition_dict=CONDITION_DICT,
)


urlpatterns = [
    re_path(
        r"^election_types/$",
        ElectionTypesView.as_view(),
        name="election_types_view",
    ),
    re_path(
        r"^reference_definition/$",
        ReferenceDefinitionView.as_view(),
        name="reference_definition_view",
    ),
    re_path(r"^elections/$", AllElectionsView.as_view(), name="elections_view"),
    re_path(
        r"^elections/(?P<election_id>[^/]+)/$",
        SingleElection.as_view(),
        name="single_election_view",
    ),
    re_path(
        r"^elections/(?P<election_id>[^/]+)/ballots_csv/$",
        BallotsCsv.as_view(),
        name="ballots_csv_view",
    ),
    re_path(
        r"^id_creator/(?P<step>[^/]+)/$",
        id_creator_wizard,
        name="id_creator_step",
    ),
    re_path(r"^id_creator/$", id_creator_wizard, name="id_creator"),
]
