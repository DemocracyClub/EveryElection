from django.http import HttpResponseRedirect
from django import forms
from formtools.wizard.views import NamedUrlSessionWizardView
from django.views.generic import ListView

from .models import ElectionType, ElectedRole, ElectionSubType
from .utils import IDMaker
from .forms import (
    ElectionDateForm,
    ElectionTypeForm,
    ElectionSubTypeForm,
    ElectionOrganisationForm
    )


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


FORMS = [("date", ElectionDateForm),
         ("election_type", ElectionTypeForm),
         ("election_subtype", ElectionSubTypeForm),
         ("election_organisation", ElectionOrganisationForm),
         ("review", forms.Form),
         ]

TEMPLATES = {
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_subtype": "id_creator/election_subtype.html",
    "election_organisation": "id_creator/election_organisation.html",
    "review": "id_creator/review.html",
}


def select_organisation(wizard):
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

def select_subtype(wizard):
    election_type = wizard.get_election_type()
    if not election_type:
        return False
    subtypes = ElectionSubType.objects.filter(election_type=election_type)

    if subtypes.count() > 1:
        return True


CONDITION_DICT = {
    'election_organisation': select_organisation,
    'election_subtype': select_subtype,
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
            if all_data.get('election_subtype'):
                for subtype in all_data['election_subtype']:
                    all_ids.append(
                        IDMaker(
                        all_data['election_type'],
                        all_data['date'],
                        organisation=organisation,
                        subtype=subtype,
                        )
                    )
            else:
                all_ids.append(
                    IDMaker(
                    all_data['election_type'],
                    all_data['date'],
                    organisation=organisation,
                    subtype=None,
                    )
                )

        context['all_ids'] = all_ids
        return context

    def get_form_kwargs(self, step):
        if step in ["election_organisation", "election_subtype"]:
            election_type = self.get_election_type()
            qs = ElectedRole.objects.filter(election_type=election_type)

            return {
                'election_type': election_type.election_type
            }
        return {}

    def done(self, form_list, **kwargs):
        return HttpResponseRedirect('/')
        ...
