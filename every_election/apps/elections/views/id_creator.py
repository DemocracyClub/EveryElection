import datetime

from core.helpers import user_is_moderator
from django import forms
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from election_snooper.helpers import post_to_slack
from election_snooper.models import SnoopedElection
from elections.forms import (
    DivFormSet,
    ElectionDateForm,
    ElectionOrganisationForm,
    ElectionSourceForm,
    ElectionSubTypeForm,
    ElectionTypeForm,
)
from elections.models import (
    Document,
    ElectedRole,
    ElectionSubType,
    ModerationStatuses,
)
from elections.utils import (
    create_ids_for_each_ballot_paper,
    get_notice_directory,
    get_voter_id_requirement,
)
from formtools.wizard.views import NamedUrlSessionWizardView
from organisations.models import Organisation

FORMS = [
    ("source", ElectionSourceForm),
    ("date", ElectionDateForm),
    ("election_type", ElectionTypeForm),
    ("election_subtype", ElectionSubTypeForm),
    ("election_organisation", ElectionOrganisationForm),
    ("election_organisation_division", DivFormSet),
    ("review", forms.Form),
]

TEMPLATES = {
    "source": "id_creator/source.html",
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_subtype": "id_creator/election_subtype.html",
    "election_organisation": "id_creator/election_organisation.html",
    "election_organisation_division": "id_creator/election_organisation_division.html",
    "review": "id_creator/review.html",
}


def show_source_step(wizard):
    # if we've got a radar_id in the URL, we want to show the source form
    radar_id = wizard.request.GET.get("radar_id", False)
    if radar_id:
        return True

    # if a source is already set, we want to show the source form
    data = wizard.get_cleaned_data_for_step("source")
    if isinstance(data, dict) and "source" in data:
        return True

    # otherwise, hide it
    return False


def date_known(wizard):
    return True


def select_organisation(wizard):
    election_type = wizard.get_election_type
    if not election_type:
        return False

    qs = ElectedRole.objects.filter(election_type=election_type)

    if qs.count() > 1:
        return True
    wizard.storage.extra_data.update(
        {"election_organisation": [qs[0].organisation.slug]}
    )

    return False


def select_subtype(wizard):
    election_type = wizard.get_election_type
    if not election_type:
        return False
    subtypes = ElectionSubType.objects.filter(election_type=election_type)
    return subtypes.count() > 1


def select_organisation_division(wizard):
    election_type = wizard.get_election_type
    if not election_type:
        return False
    if wizard.get_election_type.election_type in ["mayor", "pcc"]:
        return False
    return True


CONDITION_DICT = {
    "source": show_source_step,
    "date": date_known,
    "election_organisation": select_organisation,
    "election_organisation_division": select_organisation_division,
    "election_subtype": select_subtype,
}


class IDCreatorWizard(NamedUrlSessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    @cached_property
    def get_election_type(self):
        if self.get_cleaned_data_for_step("election_type"):
            return self.get_cleaned_data_for_step("election_type").get(
                "election_type"
            )
        return None

    @cached_property
    def get_election_subtypes(self):
        if self.get_cleaned_data_for_step("election_subtype"):
            return self.get_cleaned_data_for_step("election_subtype").get(
                "election_subtype"
            )
        return None

    @cached_property
    def get_organisations(self):
        if self.get_cleaned_data_for_step("election_organisation"):
            return self.get_cleaned_data_for_step("election_organisation").get(
                "election_organisation"
            )
        if "election_organisation" in self.storage.extra_data:
            return Organisation.objects.filter(
                electedrole__election_type__election_type__in=self.storage.extra_data[
                    "election_organisation"
                ]
            )
        return None

    def get_election_date(self):
        election_date = self.get_cleaned_data_for_step("date") or {}
        return election_date.get("date", None)

    def get_form_initial(self, step):
        if step == "source":
            # init the 'source' form with details of a SnoopedElection record
            radar_id = self.request.GET.get("radar_id", False)
            if radar_id:
                se = SnoopedElection.objects.get(pk=radar_id)
                if se.snooper_name == "CustomSearch:NoticeOfElectionPDF":
                    # put these in the session - they aren't user-modifiable
                    self.storage.extra_data.update(
                        {"radar_id": se.id, "radar_date": ""}
                    )
                    # auto-populate the form with these to allow editing
                    return {"source": se.detail_url, "document": se.detail_url}
                if (
                    se.snooper_name == "ALDC"
                    or se.snooper_name == "LibDemNewbies"
                ):
                    # put these in the session - they aren't user-modifiable
                    self.storage.extra_data.update(
                        {
                            "radar_id": se.id,
                            "radar_date": [
                                se.date.day,
                                se.date.month,
                                se.date.year,
                            ],
                        }
                    )
                    # auto-populate the form with these to allow editing
                    return {"source": se.source, "document": ""}
                return {}
        # if we've got a date from a SnoopedElection
        # init the date form with that
        if step == "date":
            if isinstance(
                self.storage.extra_data, dict
            ) and self.storage.extra_data.get("radar_date", False):
                radar_date = self.storage.extra_data["radar_date"]
                if isinstance(radar_date, list):
                    return {"date": radar_date}

            return {
                "date": [
                    "",
                    (datetime.date.today() + datetime.timedelta(days=45)).month,
                    datetime.date.today().year,
                ]
            }

        return self.initial_dict.get(step, {})

    def process_step(self, form):
        if self.steps.current == "election_type":
            if "election_type" in self.storage.data["step_data"]:
                del self.storage.data["step_data"]["election_type"]
            if "election_organisation" in self.storage.extra_data:
                del self.storage.extra_data["election_organisation"]
        if self.steps.current == "election_organisation" and (
            "election_organisation_division" in self.storage.data["step_data"]
        ):
            del self.storage.data["step_data"]["election_organisation_division"]
        return self.get_form_step_data(form)

    def get_date(self):
        if "date" in self.storage.data["step_data"]:
            date_data = self.storage.data["step_data"]["date"]
            return "-".join(
                [
                    date_data[key][0]
                    for key in (
                        "date-date_2",
                        "date-date_1",
                        "date-date_0",
                    )
                ]
            )
        return None

    def get_divisions(self):
        if "election_organisation_division" in self.storage.data["step_data"]:
            return self.get_cleaned_data_for_step(
                "election_organisation_division"
            )
        return []

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # all_data = self.get_all_cleaned_data()
        all_data = {}
        all_data["date"] = self.get_date()

        all_data["election_organisation"] = self.get_organisations
        all_data["election_divisions"] = self.get_divisions()
        all_data["election_type"] = self.get_election_type

        if not all_data.get("election_organisation"):
            all_data.update(self.storage.extra_data)
        else:
            all_data["radar_id"] = self.storage.extra_data.get("radar_id", None)

        context["all_data"] = all_data
        if self.kwargs["step"] in ["review", self.done_step_name]:
            all_ids = create_ids_for_each_ballot_paper(
                all_data, self.get_election_subtypes
            )
            context["all_ids"] = all_ids
        context["user_is_moderator"] = user_is_moderator(self.request.user)
        context["election_types_with_subtypes"] = ["sp", "senedd", "gla"]
        return context

    def get_form_kwargs(self, step):
        # if step != self.steps.current:
        #     return {}
        if step in ["election_organisation", "election_subtype"]:
            election_type = self.get_election_type
            if election_type:
                return {
                    "election_type": election_type.election_type,
                    "election_date": self.get_election_date(),
                }
            return {}
        if step == "election_organisation_division":
            organisations = self.get_organisations
            election_subtype = self.get_election_subtypes
            return {
                "organisations": organisations,
                "election_subtype": election_subtype,
                "election_date": self.get_election_date(),
            }

        if step == "election_type":
            return {"date": self.get_election_date()}

        return {}

    @transaction.atomic
    def done(self, form_list, **kwargs):
        # Make the elections

        context = self.get_context_data(form_list)
        all_data = self.get_all_cleaned_data()

        # Attach Notice of Election doc
        if all_data.get("document", False):
            # only sync the Notice of Election doc to S3 once
            # (not once per ballot paper)
            directory = get_notice_directory(context["all_ids"])
            doc = Document()
            doc.source_url = all_data["document"]
            doc.archive_document(all_data["document"], directory)
            doc.save()

            for election in context["all_ids"]:
                # Attach Notice of Election docs to IDs we are creating
                # but only link the document to the individual ballot IDs
                # because we can't make a safe assumption about whether
                # all of the elections in a group are covered by a single
                # Notice of Election document - it will vary
                if not election.group_type:
                    election.notice = doc

        status = ModerationStatuses.suggested.value
        notes = ""
        if user_is_moderator(self.request.user):
            status = ModerationStatuses.approved.value
            notes = "auto approved for user {}".format(self.request.user)

        for election in context["all_ids"]:
            # Mop up and pre-ECO metadata
            if election.group_type == "organisation" and (
                election.metadata
                and election.metadata.description == "Pre-ECO election"
            ):
                election.metadata = None

            election.requires_voter_id = get_voter_id_requirement(election)

            election.save(status=status, user=self.request.user, notes=notes)

        if (
            not user_is_moderator(self.request.user)
            and len(context["all_ids"]) > 0
        ):
            ballots = [e for e in context["all_ids"] if e.group_type is None]
            if len(ballots) == 1:
                message = """
                    New election {} suggested by anonymous user:\n
                    <https://elections.democracyclub.org.uk/election_radar/moderation_queue/>
                """.format(
                    ballots[0].election_id
                )
            else:
                message = """
                    {} New elections suggested by anonymous user:\n
                    <https://elections.democracyclub.org.uk/election_radar/moderation_queue/>
                """.format(
                    len(ballots)
                )
            post_to_slack(message)

        # if this election was created from a radar entry set the status
        # of the radar entry to indicate we have made an id for it
        if isinstance(
            self.storage.extra_data, dict
        ) and self.storage.extra_data.get("radar_id", False):
            se = SnoopedElection.objects.get(
                pk=self.storage.extra_data["radar_id"]
            )
            se.status = "id_created"
            se.save()

        return HttpResponseRedirect("/")

    def get(self, request, *args, **kwargs):
        if "reset" in self.request.GET:
            self.storage.reset()
            return HttpResponseRedirect("/")
        return super().get(self, request, *args, **kwargs)
