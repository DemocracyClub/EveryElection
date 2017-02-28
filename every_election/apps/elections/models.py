from django.db import models
from django.core.urlresolvers import reverse

from suggested_content.models import SuggestedByPublicMixin


class ElectionType(models.Model):
    """
    As defined at https://democracyclub.org.uk/projects/election-ids/reference/
    """

    name = models.CharField(blank=True, max_length=100)
    election_type = models.CharField(blank=True, max_length=100, unique=True)
    default_voting_system = models.ForeignKey(
        'elections.VotingSystem', null=True)

    def __str__(self):
        return self.name


class ElectionSubType(models.Model):
    """
    As defined at https://democracyclub.org.uk/projects/election-ids/reference/
    """

    name = models.CharField(blank=True, max_length=100)
    election_type = models.ForeignKey('ElectionType', related_name="subtype")
    election_subtype = models.CharField(blank=True, max_length=100)

    def __str__(self):
        return "{} ({})".format(self.name, self.election_type)


class ElectedRole(models.Model):
    """
    M2M through table between Organisation <-> ElectionType that defines
    the role of the job that the elected person will have. e.g:
    "Councillor for Trumpton" or "Mayor of London"
    """
    election_type = models.ForeignKey('ElectionType')
    organisation = models.ForeignKey('organisations.Organisation')
    elected_title = models.CharField(blank=True, max_length=255)
    elected_role_name = models.CharField(blank=True, max_length=255)

    def __str__(self):
        return "{} ({})".format(self.elected_title, self.organisation)


class Election(SuggestedByPublicMixin, models.Model):
    """
    An election.
    This model should contain everything needed to make the election ID,
    plus extra information about this election.
    """
    election_id = models.CharField(
        blank=True, null=True, max_length=250, unique=True)
    tmp_election_id = models.CharField(blank=True, null=True, max_length=250)
    election_title = models.CharField(blank=True, max_length=255)
    election_type = models.ForeignKey(ElectionType)
    election_subtype = models.ForeignKey(ElectionSubType, null=True)
    poll_open_date = models.DateField(blank=True, null=True)
    organisation = models.ForeignKey('organisations.Organisation', null=True)
    elected_role = models.ForeignKey(ElectedRole, null=True)
    division = models.ForeignKey('organisations.OrganisationDivision', null=True)
    seats_contested = models.IntegerField(blank=False, null=True)
    seats_total = models.IntegerField(blank=False, null=True)
    group = models.ForeignKey('Election', null=True, related_name="children")
    group_type = models.CharField(blank=True, max_length=100, null=True)
    voting_system = models.ForeignKey('elections.VotingSystem', null=True)

    def get_absolute_url(self):
        return reverse("single_election_view", args=(self.election_id,))


    # TODO:
    # Notice of election
    # Reason for election
    # Link to legislation
    # hashtags? Other names?
    # Discription

    def __str__(self):
        return self.get_id()

    def get_id(self):
        if self.election_id:
            return self.election_id
        else:
            return self.tmp_election_id


class VotingSystem(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(blank=True, max_length=100)
    wikipedia_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    uses_party_lists = models.BooleanField(default=False)

    def __str__(self):
        return self.name
