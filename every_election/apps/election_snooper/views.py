import urllib
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from election_snooper.models import SnoopedElection
from election_snooper.forms import ReviewElectionForm


class SnoopedElectionView(TemplateView):
    template_name = "election_snooper/snooped_election_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = SnoopedElection.objects.all().order_by('-date_seen', 'id')

        if 'status' in self.request.GET:
            queryset = queryset.filter(status=self.request.GET['status'])

        if 'pk' in self.request.GET:
            queryset = queryset.filter(pk=self.request.GET['pk'])

        object_list = []
        for item in queryset:
            object_list.append(
                ReviewElectionForm(instance=item, prefix=item.pk)
            )
        context['object_list'] = object_list
        return context

    def post(self, request, *args, **kwargs):
        instance = SnoopedElection.objects.get(pk=request.POST.get('pk'))
        form = ReviewElectionForm(
            request.POST, instance=instance, prefix=instance.pk)
        if form.is_valid():
            form.save()
        # TODO: if there's an error it's not processed yet
        return HttpResponseRedirect(
            "%s?status=%s" % (
                reverse('snooped_election_view'),
                urllib.parse.quote_plus(request.GET['status']),
            )
        )

