from django.db import models


class ElectionType(models.Model):
    """
    As defined at https://democracyclub.org.uk/projects/election-ids/reference/
    """

    name = models.CharField(blank=True, max_length=100)
    election_type = models.CharField(blank=True, max_length=100)

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
        return self.name


class ElectedRole(models.Model):
    """
    M2M through table between Organisation <-> ElectionType that defines
    the role of the job that the elected person will have. e.g:
    "Councillor for Trumpton" or "Mayor of London"
    """
    election_type = models.ForeignKey('ElectionType')
    organisation = models.ForeignKey('organisations.Organisation')
    elected_title = models.CharField(blank=True, max_length=255)


class Election(models.Model):
    """
    An election.
    This model should contain everything needed to make the  election ID,
    plus extra information about this election.
    """
    election_id = models.CharField(blank=True, max_length=100)
    election_type = models.ForeignKey(ElectionType)
    election_subtype = models.ForeignKey(ElectionSubType, null=True)
    poll_open_date = models.DateField()
    organisation = models.ForeignKey('organisations.Organisation')
    divisions = models.ManyToManyField(
        'organisations.OrganisationDivision', through='ElectionDivisions')

    # TODO:
    # Notice of election
    # Reason for election
    # Link to legislation
    # hashtags? Other names?
    # Discription
    # Voting system


class ElectionDivisions(models.Model):
    """
    One of the sub-parts of an election, for example, a ward or constituency.

    Some divisions can have more than one seat contested at a given election.
    """
    election = models.ForeignKey('Election')
    division = models.ForeignKey('organisations.OrganisationDivision')
    seats_contested = models.IntegerField(blank=False, null=False)
    seats_total = models.IntegerField(blank=False, null=False)
