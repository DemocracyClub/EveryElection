from django.db import transaction
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

from core.helpers import user_is_moderator
from elections.constraints import has_approved_parents, check_constraints
from elections.forms import ModerationHistoryForm
from elections.models import Election, ModerationHistory, ModerationStatuses


def set_election_status(election, status, user):
    event = ModerationHistory(
        election=election,
        status_id=status,
        user=user,
        notes='moderation queue'
    )
    event.save()


class ModerationQueueView(UserPassesTestMixin, TemplateView):
    template_name = "elections/moderation_queue.html"

    def test_func(self):
        return user_is_moderator(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        elections = Election\
            .private_objects\
            .all()\
            .filter_by_status('Suggested')\
            .filter(group_type=None)\
            .order_by('poll_open_date', 'election_id')

        forms = []
        for election in elections:
            mh = election.moderationhistory_set.all().latest()
            forms.append(
                ModerationHistoryForm(instance=mh, prefix=election.pk)
            )

        context['forms'] = forms
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ballot_pk = request.POST.get('election', None)
        ballot = Election.private_objects.get(pk=ballot_pk)
        status = request.POST.get('{}-status'.format(ballot_pk), None)
        set_election_status(ballot, status, request.user)

        if status == ModerationStatuses.approved.value:
            # it doesn't make sense for an approved ballot to have parents
            # which aren't approved, so if this happens we need to approve
            # any parent (and grandparent) election objects
            if ballot.group and not has_approved_parents(ballot):
                set_election_status(ballot.group, status, request.user)
            if ballot.group and ballot.group.group and not has_approved_parents(ballot):
                set_election_status(ballot.group.group, status, request.user)

        # if we've messed something up here, check_constraints()
        # will throw an (unhandled) ViolatedConstraint exception
        # which will roll back the transaction
        check_constraints(ballot)

        url = reverse('election_moderation_queue')
        return HttpResponseRedirect(url)
