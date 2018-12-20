from datetime import datetime

from django.views.generic import TemplateView

from elections.models import Election


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        election_qs = Election.public_objects.all()
        election_qs = election_qs.filter(group_type="election")
        election_qs = election_qs.filter(poll_open_date__gte=datetime.today())
        election_qs = election_qs.order_by("poll_open_date", "election_id")[:15]
        context["upcoming_elections"] = election_qs

        return context
