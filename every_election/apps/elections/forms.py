from django import forms

from organisations.models import Organisation

from .models import ElectionType


#
# Forms:
#   ElectionDateForm
#   ElectionTypeForm
#   ElectionOrganisationForm


class ElectionDateForm(forms.Form):
    date = forms.DateField(
        widget=forms.SelectDateWidget(
            empty_label=("Year", "Month", " Day"),
        ),
    )


class ElectionTypeForm(forms.Form):
    election_type = forms.ModelChoiceField(
        queryset=ElectionType.objects.exclude(organisation=None),
        widget=forms.RadioSelect,
        to_field_name='election_type',
        empty_label=None)


class ElectionOrganisationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election_types = kwargs.pop('election_types', None)
        super().__init__(*args, **kwargs)
        if election_types:
            qs = self.fields['election_organisation'].queryset
            qs = qs.filter(
                election_types__election_type__in=election_types)
            self.fields['election_organisation'].queryset = qs

    election_organisation = forms.ModelMultipleChoiceField(
        queryset=Organisation.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        )
