from django import forms

from organisations.models import Organisation

from .models import ElectionType, ElectionSubType

from dc_theme import forms as dc_forms


#
# Forms:
#   ElectionDateForm
#   ElectionTypeForm
#   ElectionOrganisationForm


class ElectionDateForm(forms.Form):
    date = dc_forms.DCDateField(help_text="The date that polls open")


class ElectionTypeForm(forms.Form):
    election_type = forms.ModelChoiceField(
        queryset=ElectionType.objects.exclude(organisation=None),
        widget=forms.RadioSelect,
        to_field_name='election_type',
        empty_label=None)


class ElectionSubTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election_type = kwargs.pop('election_type', None)
        super().__init__(*args, **kwargs)
        if election_type:
            qs = self.fields['election_subtype'].queryset
            qs = qs.filter(
                election_type__election_type=election_type)
            self.fields['election_subtype'].queryset = qs

    election_subtype = forms.ModelMultipleChoiceField(
        queryset=ElectionSubType.objects.all(),
        widget=forms.CheckboxSelectMultiple)


class ElectionOrganisationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election_type = kwargs.pop('election_type', None)
        super().__init__(*args, **kwargs)
        if election_type:
            qs = self.fields['election_organisation'].queryset
            qs = qs.filter(
                election_types__election_type=election_type)
            self.fields['election_organisation'].queryset = qs

    election_organisation = forms.ModelMultipleChoiceField(
        queryset=Organisation.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        )
