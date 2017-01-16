from django import forms

from organisations.models import Organisation

from .models import ElectionType, ElectionSubType

from dc_theme import forms as dc_forms


#
# Forms:
#   ElectionDateForm
#   ElectionTypeForm
#   ElectionOrganisationForm


class ElectionDateKnownForm(forms.Form):
    date_known = forms.ChoiceField(
        choices=(('yes', 'Yes'), ('no', 'No')),
        widget=forms.RadioSelect,
        label="Do you know the date of the election?")


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


class ElectionOrganisationDivisionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        organisations = kwargs.pop('organisations', None)
        election_subtype = kwargs.pop('election_subtype', None)
        self.field_groups = []

        super().__init__(*args, **kwargs)

        self.choices = (
            ('no_seats',"No Election"),
            ('seats_contested',"Contested seats"),
            ('by_election',"By-election")
        )
        if not organisations:
            return
        for organisation in organisations.all():
            self.fields[organisation.pk] = dc_forms.DCHeaderField(
                label=organisation.common_name)

            if election_subtype:
                for subtype in election_subtype:
                    # TODO Get Div Set by election date
                    div_qs = organisation.divisions.filter(
                        division_election_sub_type=subtype.election_subtype
                    )
                    div_qs = div_qs.order_by('name')
                    if div_qs:
                        self.fields[subtype.pk] = dc_forms.DCHeaderField(
                            label=subtype.name)
                    for div in div_qs:
                        self.add_single_field(organisation, div, subtype=subtype.election_subtype)
            else:
                div_qs = organisation.divisions.all()
                div_qs = div_qs.order_by('name')
                for div in div_qs:
                    self.add_single_field(organisation, div)


    def add_single_field(self, organisation, div, subtype=None):
                field_id = "__".join([
                    str(x) for x in [organisation.pk, div.pk, subtype] if x])
                field = forms.ChoiceField(
                    choices=self.choices,
                    widget=forms.RadioSelect,
                    label=div.name,
                    initial='no_seats',
                    required=False,
                    )
                self.fields[field_id] = field
