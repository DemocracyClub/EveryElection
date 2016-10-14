from django.http import HttpResponseRedirect
from django import forms
from formtools.wizard.views import NamedUrlSessionWizardView
from django.views.generic import ListView

from .models import ElectionType, ElectedRole
from .utils import IDMaker
from .forms import (
    ElectionDateForm, ElectionTypeForm, ElectionOrganisationForm)


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


FORMS = [("date", ElectionDateForm),
         ("election_type", ElectionTypeForm),
         ("election_organisation", ElectionOrganisationForm),
         ("review", forms.Form),
         ]

TEMPLATES = {
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_organisation": "id_creator/election_organisation.html",
    "review": "id_creator/review.html",
}


def select_organisation(wizard):
    # if not wizard.get_cleaned_data_for_step('election_type'):
    #     return False
    election_type = wizard.get_election_type()
    if not election_type:
        return False
    qs = ElectedRole.objects.filter(election_type=election_type)

    if qs.count() > 1:
        return True
    else:
        wizard.storage.extra_data.update({
            'election_organisation': [qs[0].organisation.slug,]})

        return False


CONDITION_DICT = {
    'election_organisation': select_organisation,
}


class IDCreatorWizard(NamedUrlSessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_election_type(self):
        if self.get_cleaned_data_for_step('election_type'):
            return self.get_cleaned_data_for_step(
                'election_type').get('election_type')

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        all_data = self.get_all_cleaned_data()
        if not all_data.get('election_organisation'):
            all_data.update(self.storage.extra_data)
        context['all_data'] = all_data
        all_ids = []
        for organisation in all_data.get('election_organisation', []):
            all_ids.append(
                IDMaker(
                all_data['election_type'],
                all_data['date'],
                organisation=organisation,
                )
            )
        context['all_ids'] = all_ids
        return context


    def get_form_kwargs(self, step):
        if step == "election_organisation":
            election_type = self.get_election_type()
            qs = ElectedRole.objects.filter(election_type=election_type)

            return {
                'election_types': [election_type.election_type]
            }
        return {}

    def done(self, form_list, **kwargs):
        return HttpResponseRedirect('/')
        ...
