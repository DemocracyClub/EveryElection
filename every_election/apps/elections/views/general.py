from collections import OrderedDict
from django.views.generic import ListView, DetailView, TemplateView

from elections.constants import ELECTION_TYPES
from elections.forms import NoticeOfElectionForm
from elections.models import ElectionType, Election, Document


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
        for et_key, et_record in OrderedDict(sorted(ELECTION_TYPES.items())).items():

            # for the moment leave 'ref' and 'eu' types out of the docs
            # because our spec for these is incomplete
            if et_key == 'eu' or et_key == 'ref':
                continue

            et_record['slug'] = et_key
            et_record['subtype'] = None

            if et_record['subtypes']:
                # if we've got subtypes, duplicate the
                # election type data for each subtype
                for s_record in et_record['subtypes']:
                    table_rec = et_record.copy()
                    table_rec['subtype'] = s_record
                    # subtype data takes precedence if it exists
                    if 'can_have_orgs' in s_record:
                        table_rec['can_have_orgs'] = s_record['can_have_orgs']
                    if 'can_have_divs' in s_record:
                        table_rec['can_have_divs'] = s_record['can_have_divs']
                    election_types_table.append(table_rec)
            else:
                # otherwise just shove it in the list
                election_types_table.append(et_record)

        context['election_types'] = election_types_table
        return context

class AllElectionsView(ListView):
    template_name = "elections/elections.html"
    model = Election
    paginate_by = 50


class SingleElection(DetailView):
    model = Election
    slug_url_kwarg = 'election_id'
    slug_field = 'election_id'

    def get_context_data(self, **kwargs):
        if self.request.POST:
            form = NoticeOfElectionForm(self.request.POST)
        else:
            form = NoticeOfElectionForm()
        context = super().get_context_data(**kwargs)
        context['form'] = form
        return context

    def post(self, *args, **kwargs):
        form = NoticeOfElectionForm(self.request.POST)
        if form.is_valid():
            document_url = form.cleaned_data['document']

            doc = Document()
            doc.source_url = document_url
            doc.archive_document(document_url, kwargs['election_id'])
            doc.save()

            e = Election.public_objects.get(election_id=kwargs['election_id'])
            e.notice = doc
            e.save()

        return self.get(*args, **kwargs)
