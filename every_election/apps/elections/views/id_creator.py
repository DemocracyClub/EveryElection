import datetime

from core.helpers import user_is_moderator
from django import forms
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from election_snooper.helpers import post_to_slack
from election_snooper.models import SnoopedElection
from elections.baker import send_event
from elections.forms import (
    DivFormSet,
    ElectionDateForm,
    ElectionOrganisationForm,
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
    reset_cache,
)
from formtools.wizard.views import NamedUrlSessionWizardView
from organisations.models import Organisation

FORMS = [
    ("date", ElectionDateForm),
    ("election_type", ElectionTypeForm),
    ("election_subtype", ElectionSubTypeForm),
    ("election_organisation", ElectionOrganisationForm),
    ("election_organisation_division", DivFormSet),
    ("review", forms.Form),
]

TEMPLATES = {
    "date": "id_creator/date.html",
    "election_type": "id_creator/election_type.html",
    "election_subtype": "id_creator/election_subtype.html",
    "election_organisation": "id_creator/election_organisation.html",
    "election_organisation_division": "id_creator/election_organisation_division.html",
    "review": "id_creator/review.html",
}


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
    if (
        election_type.election_type == "senedd"
        and wizard.get_election_date().date() >= datetime.date(2026, 5, 7)
    ):
        return False
    subtypes = ElectionSubType.objects.filter(election_type=election_type)
    return subtypes.count() > 1


def select_organisation_division(wizard):
    election_type = wizard.get_election_type
    if not election_type:
        return False
    if wizard.get_election_type.election_type in ["mayor", "pcc"]:
        return False
    # special case gla.a as it doesn't have divisions
    return not (
        election_type.election_type == "gla"
        and wizard.get_election_subtypes
        and list(
            wizard.get_election_subtypes.values_list(
                "election_subtype", flat=True
            )
        )
        == ["a"]
    )


CONDITION_DICT = {
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
        # if we've got a date from a SnoopedElection
        # init the date form with that
        if step == "date":
            self.storage.extra_data["radar_id"] = self.request.GET.get(
                "radar_id", None
            )

            if isinstance(self.storage.extra_data, dict):
                if self.storage.extra_data.get("radar_date", False):
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

        all_data["radar_id"] = self.storage.extra_data.get("radar_id", None)
        if all_data["radar_id"]:
            context["radar_obj"] = SnoopedElection.objects.get(
                pk=all_data["radar_id"]
            )

        context["all_data"] = all_data
        if self.kwargs["step"] in ["review", self.done_step_name]:
            all_ids = create_ids_for_each_ballot_paper(
                all_data, self.get_election_subtypes
            )
            context["all_ids"] = all_ids

            ballots_template = "id_creator/elections_group.html"
            if any(e.election_subtype_id is not None for e in all_ids):
                ballots_template = "id_creator/election_subtype_group.html"
            elif all_ids[0].election_type.election_type == "local":
                ballots_template = "id_creator/local_elections.html"
            context["ballots_template"] = ballots_template

        context["user_is_moderator"] = user_is_moderator(self.request.user)
        return context

    def get_form_kwargs(self, step):
        # if step != self.steps.current:
        #     return {}
        if step in ["election_organisation", "election_subtype"]:
            ret = {}
            election_type = self.get_election_type
            if election_type:
                ret = {
                    "election_type": election_type.election_type,
                    "election_date": self.get_election_date(),
                }
            if step == "election_organisation":
                ret["request"] = self.request
            return ret
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

            election.save(
                push_event=False,
                status=status,
                user=self.request.user,
                notes=notes,
            )

        if status == ModerationStatuses.approved.value:
            send_event(
                detail={"description": "Suggested elections approved"},
                detail_type="elections_set_changed",
            )

        if (
            not user_is_moderator(self.request.user)
            and len(context["all_ids"]) > 0
        ):
            ballots = [e for e in context["all_ids"] if e.group_type is None]
            if len(ballots) == 1:
                message = "New election suggested by anonymous user"
            else:
                message = (
                    f"{len(ballots)} new elections suggested by anonymous user"
                )

            fields = [
                {"type": "mrkdwn", "text": f"`{election_id}`"}
                for election_id in ballots
            ]

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message,
                    },
                },
                {"type": "section", "fields": fields},
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Review in moderation queue",
                                "emoji": True,
                            },
                            "url": "https://elections.democracyclub.org.uk/election_radar/moderation_queue/",
                            "style": "primary",
                        }
                    ],
                },
            ]

            post_to_slack(
                username="Election Suggestion",
                icon_emoji=":bulb:",
                blocks=blocks,
            )

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
        # Reset the cache created for this ID creation
        reset_cache()
        return HttpResponseRedirect("/")

    def get(self, request, *args, **kwargs):
        if "reset" in self.request.GET:
            self.storage.reset()
            return HttpResponseRedirect("/")
        return super().get(self, request, *args, **kwargs)
