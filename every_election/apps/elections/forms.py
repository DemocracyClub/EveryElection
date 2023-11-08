from typing import Union, List

from dc_utils import forms as dc_forms
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from organisations.models.divisions import DivisionManager

from .models import ElectionSubType, ElectionType

#
# Forms:
#   ElectionDateForm
#   ElectionTypeForm
#   ElectionOrganisationForm


class ElectionSourceForm(forms.Form):
    source = forms.CharField(
        required=True,
        max_length=1000,
        label="Where did you find out about this election?",
    )
    document = forms.URLField(
        required=False,
        max_length=1000,
        label="Link to 'Notice of Election' Document",
    )


class ElectionDateForm(forms.Form):
    date = dc_forms.DCDateField(help_text="The date that polls open")


class ElectionTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        date = kwargs.pop("date", None)
        super().__init__(*args, **kwargs)
        if date:
            qs = self.fields["election_type"].queryset
            qs = (
                qs.filter(organisation__start_date__lte=date)
                .filter(
                    Q(organisation__end_date__gte=date)
                    | Q(organisation__end_date=None)
                )
                .distinct()
            )
            self.fields["election_type"].queryset = qs

    election_type = forms.ModelChoiceField(
        queryset=ElectionType.objects.exclude(organisation=None),
        widget=forms.RadioSelect,
        to_field_name="election_type",
        empty_label=None,
    )


class ElectionSubTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election_type = kwargs.pop("election_type", None)
        kwargs.pop("election_date", None)
        super().__init__(*args, **kwargs)
        if election_type:
            qs = self.fields["election_subtype"].queryset
            qs = qs.filter(election_type__election_type=election_type)
            self.fields["election_subtype"].queryset = qs

    election_subtype = forms.ModelMultipleChoiceField(
        queryset=ElectionSubType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )


class ElectionOrganisationField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class ElectionOrganisationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election_type = kwargs.pop("election_type", None)
        election_date = kwargs.pop("election_date", None)
        super().__init__(*args, **kwargs)
        if election_type:
            qs = self.fields["election_organisation"].queryset
            qs = qs.filter(
                election_types__election_type=election_type
            ).filter_by_date(election_date)

            if len(qs) == 0:
                self.fields["election_organisation"] = forms.CharField(
                    widget=forms.TextInput(attrs={"class": "hide"}),
                    required=False,
                    label="No organisations available for this poll date.",
                )
            else:
                self.fields["election_organisation"].queryset = qs

    election_organisation = ElectionOrganisationField(
        queryset=Organisation.objects.all(), widget=forms.CheckboxSelectMultiple
    )


class ElectionOrganisationDivisionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.division: OrganisationDivision = kwargs.pop("division", None)
        super().__init__(*args, **kwargs)
        if not self.division:
            return
        self.fields["seats_contested"] = forms.IntegerField(
            max_value=self.division.seats_total,
            min_value=0,
            help_text=f"Up to {self.division.seats_total} seats total",
            required=False,
        )
        self.fields["division_id"] = forms.CharField(
            initial=self.division.pk, required=False, widget=forms.HiddenInput
        )

        self.fields["division_name"] = forms.CharField(
            initial=self.division.name, required=False, widget=forms.HiddenInput
        )

    division_name = forms.CharField()
    seats_contested = forms.CharField()
    ballot_type = forms.ChoiceField(
        choices=(
            ("no_seats", "No Election"),
            ("seats_contested", "Scheduled"),
            ("by_election", "By-election"),
        ),
        widget=forms.RadioSelect,
        required=False,
    )

    def clean(self):
        if (
            self.cleaned_data["ballot_type"]
            and self.cleaned_data["ballot_type"] != "no_seats"
        ):
            if not self.cleaned_data["seats_contested"]:
                raise ValidationError("Seats contested required")


class DivsFormset(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.organisations = kwargs.pop("organisations", [])
        self.election_subtype = kwargs.pop("election_subtype", None)
        self.election_date = kwargs.pop("election_date", None)
        initial_data = []
        self._form_kwargs = []
        print(self.organisations)
        if self.organisations:
            for organisation in self.organisations:
                div_set: Union[List[OrganisationDivision], DivisionManager] = (
                    OrganisationDivisionSet.objects.filter(
                        organisation=organisation,
                        start_date__lte=self.election_date,
                    )
                    .filter(
                        models.Q(end_date__gte=self.election_date)
                        | models.Q(end_date=None)
                    )
                    .order_by("-start_date")
                    .first()
                )
                for div in div_set.divisions.all().select_related(
                    "divisionset__organisation"
                ):
                    initial_data.append({"division_name": div.name})
                    self._form_kwargs.append({"division": div})
        kwargs["initial"] = initial_data
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        if not self._form_kwargs:
            return {}
        return self._form_kwargs[index]


DivFormSet = forms.formset_factory(
    ElectionOrganisationDivisionForm, formset=DivsFormset, extra=0
)


# class ElectionOrganisationDivisionForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         organisations = kwargs.pop("organisations", None)
#         election_subtype = kwargs.pop("election_subtype", None)
#         election_date = kwargs.pop("election_date", None)
#         self.field_groups = []
#
#         super().__init__(*args, **kwargs)
#
#         self.choices = (
#             ("no_seats", "No Election"),
#             ("seats_contested", "Contested seats"),
#             ("by_election", "By-election"),
#         )
#         if not organisations:
#             return
#         for organisation in organisations.all():
#             self.fields[organisation.pk] = dc_forms.DCHeaderField(
#                 label=organisation.common_name
#             )
#
#             div_set = (
#                 OrganisationDivisionSet.objects.filter(
#                     organisation=organisation, start_date__lte=election_date
#                 )
#                 .filter(models.Q(end_date__gte=election_date) | models.Q(end_date=None))
#                 .order_by("-start_date")
#                 .first()
#             )
#             if not div_set:
#                 # There is no active division set for this organisation
#                 # on this date
#                 no_divs_field = forms.CharField(
#                     widget=forms.TextInput(attrs={"class": "ds-visually-hidden"}),
#                     required=False,
#                     label="""
#                         There are no active divisions for this organisation.
#                         This is normally because we know a boundary change
#                         is about to happen but it's not final yet.
#                         Please try again in future, or contact us if you think
#                         it's a mistake.
#                     """,
#                 )
#                 self.fields["{}_no_divs".format(organisation.pk)] = no_divs_field
#                 continue
#
#             if election_subtype:
#                 for subtype in election_subtype:
#                     # TODO Get Div Set by election date
#                     div_qs = div_set.divisions.filter(
#                         division_election_sub_type=subtype.election_subtype
#                     )
#                     div_qs = div_qs.order_by("name")
#                     if div_qs:
#                         self.fields[subtype.pk] = dc_forms.DCHeaderField(
#                             label=subtype.name
#                         )
#                     for div in div_qs:
#                         self.add_single_field(
#                             organisation, div, subtype=subtype.election_subtype
#                         )
#             else:
#                 div_qs: QuerySet[OrganisationDivision] = div_set.divisions.all()
#                 div_qs = div_qs.order_by("name")
#                 for div in div_qs:
#                     self.add_single_field(organisation, div)
#
#     def add_single_field(
#         self, organisation: Organisation, div: OrganisationDivision, subtype=None
#     ):
#         field_id = "__".join([str(x) for x in [organisation.pk, div.pk, subtype] if x])
#         ballot_type_field = forms.ChoiceField(
#             choices=self.choices,
#             widget=forms.RadioSelect,
#             label=div.name,
#             initial="no_seats",
#             required=False,
#         )
#         ballot_type_field.group = field_id
#         self.fields[field_id] = ballot_type_field
#
#         # Add seats contested
#         seats_contested_field = forms.IntegerField(
#             max_value=div.seats_total, min_value=0, label="Seats Contested", initial=0
#         )
#         seats_contested_field.group = field_id
#         self.fields[f"{field_id}_seats"] = seats_contested_field
#


class NoticeOfElectionForm(forms.Form):
    document = forms.URLField(
        required=True,
        max_length=1000,
        label="Link to 'Notice of Election' Document",
    )

    def clean_document(self):
        """
        TODO: do we want to do any additional validation checks here?
        Notice of Election URLs are not gauranteed to end in .pdf
        and aren't always hosted on a .gov.uk domain.

        Examples:
        https://www.tewkesbury.gov.uk/voting-and-elections
        http://doncaster.gov.uk/services/the-council-democracy/notice-of-elections
        """
        return self.cleaned_data["document"]
