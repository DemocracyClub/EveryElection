from django.conf.urls import url

from .views import (ElectionTypesView, AllElectionsView,
                    IDCreatorWizard, FORMS, CONDITION_DICT)


id_creator_wizard = IDCreatorWizard.as_view(
    FORMS,
    url_name='id_creator_step',
    done_step_name='home',
    condition_dict=CONDITION_DICT)


urlpatterns = [
    url(r'^election_types$',
        ElectionTypesView.as_view(),
        name='election_types_view'),
    url(r'^elections$',
        AllElectionsView.as_view(),
        name='elections_view'),

    url(r'^id_creator/(?P<step>.+)/$', id_creator_wizard, name='id_creator_step'),
    url(r'^id_creator/$', id_creator_wizard, name='id_creator'),
]
