from django import forms
from django.db import models

from organisations.models import Organisation
from organisations.models import OrganisationDivisionSet

from .models import ElectionType, ElectionSubType

from dc_theme import forms as dc_forms


#
# Forms:
#   ElectionDateForm
#   ElectionTypeForm
#   ElectionOrganisationForm


class ElectionSourceForm(forms.Form):
    source = forms.CharField(required=True, max_length=1000,
        label="Where did you find out about this election?")
    document = forms.URLField(required=False, max_length=1000,
        label="Link to 'Notice of Election' Document")


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
        kwargs.pop('election_date', None)
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
        election_date = kwargs.pop('election_date', None)
        super().__init__(*args, **kwargs)
        if election_type:
            qs = self.fields['election_organisation'].queryset
            qs = qs\
                .filter(election_types__election_type=election_type)\
                .filter(
                    start_date__lte=election_date
                ).filter(
                    models.Q(end_date__gte=election_date)
                    | models.Q(end_date=None)
                )

            if len(qs) == 0:
                self.fields['election_organisation'] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={'class': 'hide',}
                    ),
                    required=False,
                    label="No organisations available for this poll date."
                )
            else:
                self.fields['election_organisation'].queryset = qs

    election_organisation = forms.ModelMultipleChoiceField(
        queryset=Organisation.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        )


class ElectionOrganisationDivisionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        organisations = kwargs.pop('organisations', None)
        election_subtype = kwargs.pop('election_subtype', None)
        election_date = kwargs.pop('election_date', None)
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


            div_set = OrganisationDivisionSet.objects.filter(
                organisation=organisation,
                start_date__lte=election_date
                ).filter(
                    models.Q(end_date__gte=election_date)
                    | models.Q(end_date=None)
                ).order_by('-start_date').first()
            if not div_set:
                # There is no active division set for this organisation
                # on this date
                no_divs_field = forms.CharField(
                    widget=forms.TextInput(
                        attrs={'class': 'hide',}
                    ),
                    required=False,
                    label="""
                        There are no active divisions for this organisation.
                        This is normally because we know a boundary change
                        is about to happen but it's not final yet.
                        Please try again in future, or contact us if you think
                        it's a mistake.
                    """
                )
                self.fields[
                        "{}_no_divs".format(organisation.pk)] = no_divs_field
                continue


            if election_subtype:
                for subtype in election_subtype:
                    # TODO Get Div Set by election date
                    div_qs = div_set.divisions.filter(
                        division_election_sub_type=subtype.election_subtype
                    )
                    div_qs = div_qs.order_by('name')
                    if div_qs:
                        self.fields[subtype.pk] = dc_forms.DCHeaderField(
                            label=subtype.name)
                    for div in div_qs:
                        self.add_single_field(organisation, div, subtype=subtype.election_subtype)
            else:
                div_qs = div_set.divisions.all()
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


class NoticeOfElectionForm(forms.Form):
    document = forms.URLField(required=True, max_length=1000,
        label="Link to 'Notice of Election' Document")

    def clean_document(self):
        document = self.cleaned_data['document']
        """
        TODO: do we want to do any additional validation checks here?
        Notice of Election URLs are not gauranteed to end in .pdf
        and aren't always hosted on a .gov.uk domain.

        Examples:
        https://www.tewkesbury.gov.uk/voting-and-elections
        http://doncaster.gov.uk/services/the-council-democracy/notice-of-elections
        """
        return document
