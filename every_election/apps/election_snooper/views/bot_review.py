import urllib
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

from core.helpers import user_is_moderator
from election_snooper.models import SnoopedElection
from election_snooper.forms import ReviewElectionForm


class SnoopedElectionView(UserPassesTestMixin, TemplateView):
    template_name = "election_snooper/snooped_election_list.html"

    def test_func(self):
        return user_is_moderator(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = SnoopedElection.objects.all().order_by("-date_seen", "id")

        if "status" in self.request.GET:
            queryset = queryset.filter(status=self.request.GET["status"])

        if "pk" in self.request.GET:
            queryset = queryset.filter(pk=self.request.GET["pk"])

        objects = []
        for item in queryset:
            objects.append(ReviewElectionForm(instance=item, prefix=item.pk))

        paginator = Paginator(objects, 25)  # Show 25 records per page
        page = self.request.GET.get("page")
        try:
            context["objects"] = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            context["objects"] = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            context["objects"] = paginator.page(paginator.num_pages)

        return context

    def post(self, request, *args, **kwargs):
        instance = SnoopedElection.objects.get(pk=request.POST.get("pk"))
        form = ReviewElectionForm(
            request.POST, instance=instance, prefix=instance.pk
        )
        if form.is_valid():
            form.save()
        # TODO: if there's an error it's not processed yet

        url = reverse("snooped_election_view")
        if "status" in self.request.GET:
            url = "{}?status={}".format(
                url, urllib.parse.quote_plus(request.GET["status"])
            )
        return HttpResponseRedirect(url)
