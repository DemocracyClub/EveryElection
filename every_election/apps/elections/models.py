import tempfile
import urllib.request

from datetime import date, timedelta

from django.db import models, transaction
from django.core.files import File
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.fields import JSONField
from django_markdown.models import MarkdownField

from storages.backends.s3boto3 import S3Boto3Storage
from suggested_content.models import SuggestedByPublicMixin
from .managers import PublicElectionsManager, PrivateElectionsManager, ElectionQuerySet


class ElectionType(models.Model):

    name = models.CharField(blank=True, max_length=100)
    election_type = models.CharField(blank=True, max_length=100, unique=True)
    default_voting_system = models.ForeignKey(
        'elections.VotingSystem', null=True)

    def __str__(self):
        return self.name


class ElectionSubType(models.Model):

    name = models.CharField(blank=True, max_length=100)
    election_type = models.ForeignKey('ElectionType', related_name="subtype")
    election_subtype = models.CharField(blank=True, max_length=100)
    ValidationError = ValueError

    def __str__(self):
        return "{} ({})".format(self.name, self.election_type)


class ElectedRole(models.Model):
    """
    M2M through table between Organisation <-> ElectionType that defines
    the role of the job that the elected person will have. e.g:
    "Councillor for Trumpton" or "Mayor of London"
    """
    election_type = models.ForeignKey('ElectionType')
    organisation = models.ForeignKey('organisations.Organisation', related_name='electedrole')
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
    division_geography = models.ForeignKey('organisations.DivisionGeography',
        null=True, blank=True)
    organisation_geography = models.ForeignKey('organisations.OrganisationGeography',
        null=True, blank=True)
    seats_contested = models.IntegerField(blank=True, null=True)
    seats_total = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey('Election', null=True, related_name="children")
    group_type = models.CharField(blank=True, max_length=100, null=True)
    voting_system = models.ForeignKey('elections.VotingSystem', null=True)
    explanation = models.ForeignKey('elections.Explanation',
        null=True, blank=True, on_delete=models.SET_NULL)
    metadata = models.ForeignKey('elections.MetaData',
        null=True, blank=True, on_delete=models.SET_NULL)
    current = models.NullBooleanField()

    # where did we hear about this election
    # (not necessarily the Notice of Election)
    source = models.CharField(blank=True, max_length=1000)

    # Notice of Election document
    notice = models.ForeignKey('elections.Document',
        null=True, blank=True, on_delete=models.SET_NULL)

    # optional FK to a SnoopedElection record
    snooped_election = models.ForeignKey('election_snooper.SnoopedElection',
        null=True, blank=True, on_delete=models.SET_NULL)


    public_objects = PublicElectionsManager.from_queryset(ElectionQuerySet)()
    private_objects = PrivateElectionsManager.from_queryset(ElectionQuerySet)()

    class Meta:
        ordering = ('election_id',)

    def get_absolute_url(self):
        return reverse("single_election_view", args=(self.election_id,))

    @property
    def get_current(self):
        model_current = getattr(self, 'current', None)
        if model_current is None:
            # We've not explicetly set current
            recent_past = date.today() - timedelta(days=20)
            return self.poll_open_date > recent_past
        return model_current

    # TODO:
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

    @property
    def geography(self):
        if not self.group_type and self.division:
            return self.division_geography
        return self.organisation_geography

    def get_division_geography(self):
        if self.division_geography:
            return self.division_geography

        try:
            # if the election is a 'ballot'
            if not self.group_type:
                # attach geography by division if possible
                if self.division:
                    return self.division.geography
        except ObjectDoesNotExist:
            pass
        return None

    @property
    def ynr_link(self):
        if self.group_type == 'organisation':
            return 'https://candidates.democracyclub.org.uk/election/{}/constituencies'.format(
                self.election_id)
        return None

    @property
    def whocivf_link(self):
        if self.group_type == 'organisation':
            return 'https://whocanivotefor.co.uk/elections/{id}/{type}'.format(
                id=self.election_id, type=slugify(self.election_type))
        return None

    def get_organisation_geography(self):
        if self.organisation_geography:
            return self.organisation_geography

        try:
            # if the election is a 'ballot'
            if not self.group_type:

                if self.division:
                    return None

                # Try to attach geography by organisation
                # (e.g: for Mayors, PCCs etc)
                if not self.division and self.organisation:
                    return self.organisation.get_geography(self.poll_open_date)

            # if the election is an 'organisation group'
            # attach geography by organisation
            if self.group_type == "organisation" and not self.division:
                return self.organisation.get_geography(self.poll_open_date)

        except ObjectDoesNotExist:
            pass
        return None

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.division_geography = self.get_division_geography()
        self.organisation_geography = self.get_organisation_geography()

        if not self.group_id and self.group:
            try:
                group_model = Election.private_objects.get(election_id=self.group.election_id)
            except Election.DoesNotExist:
                group_model = self.group.save(*args, **kwargs)
            self.group = group_model

        return super().save(*args, **kwargs)


class VotingSystem(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(blank=True, max_length=100)
    wikipedia_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    uses_party_lists = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Explanation(models.Model):
    description = models.CharField(blank=False, max_length=100)
    explanation = MarkdownField(blank=False)

    def __str__(self):
        return self.description


class MetaData(models.Model):
    description = models.CharField(blank=False, max_length=100)
    data = JSONField()

    class Meta:
        verbose_name_plural = "MetaData"

    def __str__(self):
        return self.description


class PdfS3Storage(S3Boto3Storage):
    default_content_type = 'application/pdf'
    default_acl = 'public-read'


class Document(models.Model):
    source_url = models.URLField(max_length=1000)
    uploaded_file = models.FileField(
        max_length=1000,
        upload_to='',
        storage=PdfS3Storage())

    def archive_document(self, url, election_id):
        # copy a notice of election document to our s3 bucket
        # because it won't stay on the council website forever

        filename = url.split('/')[-1]
        if filename == '':
            filename = 'Notice_of_Election'
        with tempfile.NamedTemporaryFile() as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            self.uploaded_file.save(
                "%s/%s" % (election_id, filename), File(tmp))
        return self.uploaded_file
