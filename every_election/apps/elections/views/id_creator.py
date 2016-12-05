from django.http import HttpResponseRedirect
from django import forms
from formtools.wizard.views import NamedUrlSessionWizardView

from organisations.models import Organisation, OrganisationDivision
from elections.models import ElectedRole, ElectionSubType, Election
from elections.utils import IDMaker
from elections.forms import (
    ElectionDateForm,
    ElectionTypeForm,
    ElectionSubTypeForm,
    ElectionOrganisationForm,
    ElectionOrganisationDivisionForm
    )


FORMS = [("date", ElectionDateForm),
         ("election_type", ElectionTypeForm),
         ("election_subtype", ElectionSubTypeForm),
         ("election_organisation", ElectionOrganisationForm),
         ("election_organisation_division", ElectionOrganisationDivisionForm),
         ("review", forms.Form),
         ]

TEMPLATES = {
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_subtype": "id_creator/election_subtype.html",
    "election_organisation": "id_creator/election_organisation.html",
    "election_organisation_division":
        "id_creator/election_organisation_division.html",
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
            'election_organisation': [qs[0].organisation.slug, ]})

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
            return context
        if not all_data.get('election_organisation'):
            all_data.update(self.storage.extra_data)
        context['all_data'] = all_data
        all_ids = []
        for organisation in all_data.get('election_organisation', []):
            if type(organisation) == str:
                organisation = Organisation.objects.get(
                    organisation_type=organisation)
            pk = str(organisation.pk)

            div_data = {
                k: v for k, v
                in all_data.items()
                if str(k).startswith(pk)
                and '__' in str(k)
                and v != "no_seats"
            }

            by_elections = {
                k: v for k, v
                in div_data.items()
                if v == "by_election"
            }

            only_by_election = by_elections == div_data

            args = [all_data['election_type'], all_data['date']]
            kwargs = {
                'organisation': organisation,
            }

            if self.get_election_subtypes():
                for subtype in all_data.get('election_subtype', []):
                    by_elections = {
                        k: v for k, v
                        in div_data.items()
                        if v == "by_election"
                        and k.endswith(subtype.election_subtype)
                    }
                    only_by_election = by_elections == div_data
                    if only_by_election:
                        for div in by_elections:
                            org_div = OrganisationDivision.objects.get(
                                pk=div.split('__')[1]
                            )

                            all_ids.append(IDMaker(
                                *args,
                                subtype=subtype,
                                division=org_div,
                                **kwargs))
                    else:
                        all_ids.append(
                            IDMaker(*args, subtype=subtype, **kwargs))
            else:
                if only_by_election:
                    for div in by_elections:
                        org_div = OrganisationDivision.objects.get(
                            pk=div.split('__')[1]
                        )
                        all_ids.append(IDMaker(
                            *args,
                            division=org_div,
                            **kwargs
                            ))
                else:
                    all_ids.append(IDMaker(*args, **kwargs))


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
            Election.objects.update_or_create(
                    election_id=election_data.to_id(),
                    poll_open_date=election_data.date,
                    election_type=election_data.election_type,
                    election_subtype=election_data.subtype,
                    organisation=election_data.organisation,
            )


        return HttpResponseRedirect('/')
        ...
