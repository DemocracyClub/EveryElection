import csv
import io
from collections import OrderedDict

from core.helpers import user_is_moderator
from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.utils.html import mark_safe
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from elections.forms import NoticeOfElectionForm
from elections.models import ByElectionReason, Document, Election, ElectionType
from uk_election_ids.datapackage import ELECTION_TYPES


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


class ReferenceDefinitionView(TemplateView):
    template_name = "elections/reference_definition.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ELECTION_TYPES is optimised for fast
        # lookups and not duplicating information.
        # We need to transform ELECTION_TYPES into a data structure
        # which is more optimised for generating HTML in a template:
        election_types_table = []
        for et_key, et_record in OrderedDict(
            sorted(ELECTION_TYPES.items())
        ).items():
            et_record["slug"] = et_key
            et_record["subtype"] = None

            if et_record["slug"] == "senedd":
                table_rec = et_record.copy()
                table_rec["name"] += " (2026-05-07 onwards)"
                election_types_table.append(table_rec)
            if et_record["subtypes"]:
                # if we've got subtypes, duplicate the
                # election type data for each subtype
                for s_record in et_record["subtypes"]:
                    table_rec = et_record.copy()
                    if et_record["slug"] == "senedd":
                        table_rec["name"] += " (before 2026-05-07)"
                    table_rec["subtype"] = s_record
                    # subtype data takes precedence if it exists
                    if "can_have_orgs" in s_record:
                        table_rec["can_have_orgs"] = s_record["can_have_orgs"]
                    if "can_have_divs" in s_record:
                        table_rec["can_have_divs"] = s_record["can_have_divs"]
                    election_types_table.append(table_rec)
            else:
                # otherwise just shove it in the list
                election_types_table.append(et_record)

        context["election_types"] = election_types_table
        context["by_election_reasons"] = ByElectionReason.choices
        return context


class AllElectionsView(ListView):
    template_name = "elections/elections.html"
    model = Election
    paginate_by = 50

    def get_queryset(self):
        return Election.public_objects.all()


class SingleElection(AccessMixin, DetailView):
    model = Election
    slug_url_kwarg = "election_id"
    slug_field = "election_id"

    def get_queryset(self):
        return Election.public_objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.children = obj.get_children(Election.public_objects)
        return obj

    def get_document(self, election):
        if election.cancelled and election.cancellation_notice:
            document = election.cancellation_notice
            document_type = "Notice of Cancellation Document"
        else:
            if election.notice:
                document = election.notice
                document_type = "Notice of Election Document"
            elif election.group and election.group.notice:
                document = election.group.notice
                document_type = "Notice of Election Document"
            else:
                document = None
                document_type = None

        return document, document_type

    def get_geography_html(self, election):
        if election.division and election.division.format_geography_link():
            division = election.division
            geography_link = f"<a href={division.format_geography_link()}>{division.official_identifier}</a>"
        else:
            geography_link = "<strong>Missing</strong>"
        return mark_safe(geography_link)

    def get_context_data(self, **kwargs):
        if self.request.POST:
            form = NoticeOfElectionForm(self.request.POST)
        else:
            form = NoticeOfElectionForm()
        context = super().get_context_data(**kwargs)
        context["geography_html"] = self.get_geography_html(context["object"])
        context["api_detail_geo"] = reverse(
            "api:election-geo",
            kwargs={
                "election_id": context["object"].election_id,
                "format": "json",
            },
        )
        context["document"], context["document_type"] = self.get_document(
            context["object"]
        )
        context["form"] = form
        context["user_can_upload_docs"] = user_is_moderator(self.request.user)
        return context

    def post(self, *args, **kwargs):
        if not user_is_moderator(self.request.user):
            return self.handle_no_permission()

        form = NoticeOfElectionForm(self.request.POST)
        if form.is_valid():
            document_url = form.cleaned_data["document"]

            doc = Document()
            doc.source_url = document_url
            doc.archive_document(document_url, kwargs["election_id"])
            doc.save()

            e = Election.public_objects.get(election_id=kwargs["election_id"])
            e.notice = doc
            e.save()

        return self.get(*args, **kwargs)


class BallotsCsv(View):
    def get(self, *args, election_id, **kwargs):
        try:
            group = Election.public_objects.get(election_id=election_id)
        except Election.DoesNotExist:
            raise Http404("Election not found")

        if group.group_type is None:
            raise Http404(f"{election_id} is a ballot")

        ballots = (
            group.get_descendents("public_objects", inclusive=False)
            .filter(group_type__isnull=True)
            .order_by("election_id")
        )

        if ballots.count() == 0:
            raise Http404("No ballots found")

        output = io.StringIO()
        writer = csv.writer(output)

        # header
        writer.writerow(
            ["election_id", "cancelled", "seats_total", "seats_contested"]
        )

        # content
        for b in ballots:
            writer.writerow(
                [
                    b.election_id,
                    b.cancelled,
                    b.seats_total,
                    b.seats_contested,
                ]
            )

        csv_content = output.getvalue()
        output.close()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{election_id}.csv"'
        )
        response.write(csv_content)
        return response
