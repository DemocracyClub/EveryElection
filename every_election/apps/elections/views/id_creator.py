from django.http import HttpResponseRedirect
from django import forms
from formtools.wizard.views import NamedUrlSessionWizardView

from organisations.models import Organisation
from elections.models import ElectedRole, ElectionSubType, Election
from elections.utils import (create_ids_for_each_ballot_paper)
from elections.forms import (
    ElectionDateKnownForm,
    ElectionDateForm,
    ElectionTypeForm,
    ElectionSubTypeForm,
    ElectionOrganisationForm,
    ElectionOrganisationDivisionForm
    )


FORMS = [
         ("date_known", ElectionDateKnownForm),
         ("date", ElectionDateForm),
         ("election_type", ElectionTypeForm),
         ("election_subtype", ElectionSubTypeForm),
         ("election_organisation", ElectionOrganisationForm),
         ("election_organisation_division", ElectionOrganisationDivisionForm),
         ("review", forms.Form),
         ]

TEMPLATES = {
    "date_known": "id_creator/date_known.html",
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_subtype": "id_creator/election_subtype.html",
    "election_organisation": "id_creator/election_organisation.html",
    "election_organisation_division":
        "id_creator/election_organisation_division.html",
    "review": "id_creator/review.html",
}


def date_known(wizard):
    date_known_step_data = wizard.get_cleaned_data_for_step('date_known')
    if date_known_step_data:
        known = date_known_step_data.get('date_known')
        if known == "no":
            return False
    return True

def select_organisation(wizard):
    election_type = wizard.get_election_type()
    if not election_type:
        return False
    qs = ElectedRole.objects.filter(election_type=election_type)

    if qs.count() > 1:
        return True
    else:
        wizard.storage.extra_data.update({
            'election_organisation': [qs[0].organisation.slug, ]})

        return False


def select_subtype(wizard):
    election_type = wizard.get_election_type()
    if not election_type:
        return False
    subtypes = ElectionSubType.objects.filter(election_type=election_type)
    return subtypes.count() > 1

def select_organisation_division(wizard):
    election_type = wizard.get_election_type()
    if not election_type:
        return False
    if wizard.get_election_type().election_type == "mayor":
        return False
    return True



CONDITION_DICT = {
    'date': date_known,
    'election_organisation': select_organisation,
    'election_organisation_division': select_organisation_division,
    'election_subtype': select_subtype,
}


class IDCreatorWizard(NamedUrlSessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_election_type(self):
        if self.get_cleaned_data_for_step('election_type'):
            return self.get_cleaned_data_for_step(
                'election_type').get('election_type')

    def get_election_subtypes(self):
        if self.get_cleaned_data_for_step('election_subtype'):
            return self.get_cleaned_data_for_step(
                'election_subtype').get('election_subtype')

    def get_organisations(self):
        if self.get_cleaned_data_for_step('election_organisation'):
            return self.get_cleaned_data_for_step(
                'election_organisation').get('election_organisation')
        if 'election_organisation' in self.storage.extra_data:
            qs = Organisation.objects.filter(
                electedrole__election_type__election_type__in=\
                    self.storage.extra_data['election_organisation']
            )
            return qs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        all_data = self.get_all_cleaned_data()
        # print("\n".join(str(all_data).split(',')))
        if not 'date' in all_data:
            all_data['date'] = None
        if not all_data.get('election_organisation'):
            all_data.update(self.storage.extra_data)
        context['all_data'] = all_data
        all_ids = create_ids_for_each_ballot_paper(all_data, self.get_election_subtypes())
        # all_ids = create_ids_grouped(all_data, self.get_election_subtypes())
        context['all_ids'] = all_ids
        return context

    def get_form_kwargs(self, step):
        if step in ["election_organisation", "election_subtype"]:
            election_type = self.get_election_type()
            if election_type:
                return {
                    'election_type': election_type.election_type
                }
        if step == "election_organisation_division":
            organisations = self.get_organisations()
            election_subtype = self.get_election_subtypes()
            return {
                'organisations': organisations,
                'election_subtype': election_subtype,
            }
        return {}

    def done(self, form_list, **kwargs):

        # Make the elections
        context = self.get_context_data(form_list)
        for election_data in context['all_ids']:
            election_data.save_model()


        return HttpResponseRedirect('/')
