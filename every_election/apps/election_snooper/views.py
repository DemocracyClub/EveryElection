from django.views.generic import ListView

from election_snooper.models import SnoopedElection

class SnoopedElectionView(ListView):
    template_name = "election_snooper/snooped_election_list.html"
    model = SnoopedElection
