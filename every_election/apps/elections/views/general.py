from django.views.generic import ListView, DetailView

from elections.forms import NoticeOfElectionForm
from elections.models import ElectionType, Election, Document


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


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

            e = Election.objects.get(election_id=kwargs['election_id'])
            e.notice = doc
            e.save()

        return self.get(*args, **kwargs)
