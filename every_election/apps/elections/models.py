import tempfile
import urllib.request
from datetime import date, timedelta
from enum import Enum, unique

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db.models.functions import Distance
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.db import models, transaction
from django.db.models import JSONField, Q
from django.db.models.fields.related_descriptors import (
    create_reverse_many_to_one_manager,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from storages.backends.s3boto3 import S3Boto3Storage
from uk_election_ids.datapackage import ID_REQUIREMENTS, VOTING_SYSTEMS
from uk_election_timetables.calendars import Country
from uk_election_timetables.election_ids import (
    NoSuchElectionTypeError,
    from_election_id,
)
from uk_geo_utils.models import Onspd

from .managers import PrivateElectionsManager, PublicElectionsManager


class ElectionCancellationReason(models.TextChoices):
    NO_CANDIDATES = "NO_CANDIDATES", "No candidates"
    EQUAL_CANDIDATES = "EQUAL_CANDIDATES", "Equal candidates to seats"
    UNDER_CONTESTED = "UNDER_CONTESTED", "Fewer candidates than seats"
    CANDIDATE_DEATH = "CANDIDATE_DEATH", "Death of a candidate"


class ElectionType(models.Model):
    name = models.CharField(blank=True, max_length=100)
    election_type = models.CharField(blank=True, max_length=100, unique=True)

    def __str__(self):
        return self.name


class ElectionSubType(models.Model):
    name = models.CharField(blank=True, max_length=100)
    election_type = models.ForeignKey(
        "ElectionType", related_name="subtype", on_delete=models.CASCADE
    )
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

    election_type = models.ForeignKey("ElectionType", on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        "organisations.Organisation",
        related_name="electedrole",
        on_delete=models.CASCADE,
    )
    elected_title = models.CharField(blank=True, max_length=255)
    elected_role_name = models.CharField(blank=True, max_length=255)

    def __str__(self):
        return "{} ({})".format(self.elected_title, self.organisation)


@unique
class ModerationStatuses(Enum):
    suggested = "Suggested"
    rejected = "Rejected"
    approved = "Approved"
    deleted = "Deleted"


class ModerationStatus(models.Model):
    short_label = models.CharField(
        blank=False,
        max_length=32,
        primary_key=True,
        choices=[(x, x.value) for x in ModerationStatuses],
    )
    long_label = models.CharField(blank=False, max_length=100)

    def __str__(self):
        return self.short_label


DEFAULT_STATUS = ModerationStatuses.suggested.value


class Election(TimeStampedModel):
    """
    An election.
    This model should contain everything needed to make the election ID,
    plus extra information about this election.
    """

    election_id = models.CharField(
        blank=True, null=True, max_length=250, unique=True
    )
    tmp_election_id = models.CharField(blank=True, null=True, max_length=250)
    election_title = models.CharField(blank=True, max_length=255)
    election_type = models.ForeignKey(ElectionType, on_delete=models.CASCADE)
    election_subtype = models.ForeignKey(
        ElectionSubType, null=True, on_delete=models.CASCADE
    )
    poll_open_date = models.DateField(blank=True, null=True)
    organisation = models.ForeignKey(
        "organisations.Organisation", null=True, on_delete=models.CASCADE
    )
    elected_role = models.ForeignKey(
        ElectedRole, null=True, on_delete=models.CASCADE
    )
    division = models.ForeignKey(
        "organisations.OrganisationDivision",
        null=True,
        on_delete=models.CASCADE,
    )
    division_geography = models.ForeignKey(
        "organisations.DivisionGeography",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    organisation_geography = models.ForeignKey(
        "organisations.OrganisationGeography",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    seats_contested = models.IntegerField(blank=True, null=True)
    seats_total = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey(
        "Election",
        null=True,
        related_name="_children_qs",
        on_delete=models.CASCADE,
        verbose_name="Parent",
    )
    requires_voter_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=[
            *[(None, "No ID Required")],
            *[(req, ID_REQUIREMENTS[req]["name"]) for req in ID_REQUIREMENTS],
        ],
    )

    def _get_manager_obj(self, manager):
        for m in self._meta.managers:
            if m.name == manager or m == manager:
                return m
        raise ValueError("Unknown manager {}".format(manager))

    def get_children(self, manager):
        """
        This method allows us to call with a manger instance or a string
        i.e both: obj.get_children('private_objects') and
        obj.get_children(Election.public_objects)
        are supported.

        This will return a 'children' RelatedManager
        with the relevant private/public filters applied.
        """
        manager = self._get_manager_obj(manager)
        child_manager_cls = create_reverse_many_to_one_manager(
            manager.__class__, self._meta.get_field("_children_qs")
        )
        return child_manager_cls(self)

    def get_descendents(self, manager, inclusive=False):
        """
        This method allows us to call with a manger instance or a string
        i.e both: obj.get_children('private_objects') and
        obj.get_children(Election.public_objects)
        are supported.

        This will return a Queryset of all descendents
        (children, and children's children)

        with the relevant private/public filters applied.

        inclusive=True/False determines whether to include
        the root node in the QuerySet.
        """
        manager = self._get_manager_obj(manager)

        queryset = (
            manager.all() if inclusive else manager.filter(~Q(pk=self.pk))
        )

        id_parts = self.election_id.split(".")
        head = id_parts[:-1]
        date_ = id_parts.pop(-1)

        prefix = f"{'.'.join(head)}."

        return queryset.filter(
            Q(election_id__startswith=prefix) & Q(poll_open_date=date_)
        )

    group_type = models.CharField(
        blank=True, max_length=100, null=True, db_index=True
    )
    voting_system = models.CharField(
        max_length=100,
        null=True,
        choices=[(vs, VOTING_SYSTEMS[vs]["name"]) for vs in VOTING_SYSTEMS],
    )
    explanation = models.ForeignKey(
        "elections.Explanation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    metadata = models.ForeignKey(
        "elections.MetaData", null=True, blank=True, on_delete=models.SET_NULL
    )
    current = models.BooleanField(null=True, db_index=True)

    """
    ## Statuses
    
    Elections can have various statuses. 
    
    We track these in `ModerationStatus`. Using this model we can 
    get the moderation history of each object, including the current 
    status.
    
    However this query is somewhat slow, and most of the time (e.g 
    for public use) we want to filter on the current status.
    
    Because of this, we denormalize the current status into a 
    `current_status` field.
    
    election.moderation_statuses.all() is not a terribly useful call
    to reference directly because it just gives us a list of all the
    statuses an election object has ever been assigned
    (but not when they were assigned or or which is the most recent).

    `ModerationHistory.objects.all().filter(election=self).latest().status` 
    will get the latest status, but this should always be the same as 
    `self.current_status`.
    """
    moderation_statuses = models.ManyToManyField(
        ModerationStatus, through="ModerationHistory"
    )
    # Don't modify this field directly. Add a ModerationStatus event and save it
    # to change this value.
    current_status = models.CharField(
        blank=False,
        max_length=32,
        choices=[(x, x.value) for x in ModerationStatuses],
        default=DEFAULT_STATUS,
        db_index=True,
    )

    # where did we hear about this election
    # (not necessarily the Notice of Election)
    source = models.CharField(blank=True, max_length=1000)

    # Notice of Election document
    notice = models.ForeignKey(
        "elections.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notice_election_set",
    )

    # optional FK to a SnoopedElection record
    snooped_election = models.ForeignKey(
        "election_snooper.SnoopedElection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    cancelled = models.BooleanField(default=False)
    cancellation_notice = models.ForeignKey(
        "elections.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cancellation_election_set",
    )
    cancellation_reason = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=ElectionCancellationReason.choices,
        default=None,
    )
    replaces = models.ForeignKey(
        "Election",
        null=True,
        blank=True,
        related_name="_replaced_by",
        on_delete=models.CASCADE,
    )
    tags = JSONField(default=dict, blank=True)

    @property
    def replaced_by(self):
        if len(self._replaced_by.all()) == 0:
            return None
        if len(self._replaced_by.all()) == 1:
            return self._replaced_by.all()[0]
        raise AttributeError("Election should only have one replacement")

    """
    Note that order is significant here.
    The first manager we define is the default. See:
    https://docs.djangoproject.com/en/1.11/topics/db/managers/#modifying-a-manager-s-initial-queryset

    public_objects might seem like the 'safe' default here, but there are a
    number of places where Django implicitly uses the default manager
    (e.g: /admin, dumpdata, etc).
    Using public_objects as the default can lead to some strange bugs.

    For the most part, not having a .objects forces us to make a choice
    about what we are exposing when we query the model but there are
    some places where django/DRF/etc are "clever" and silently uses the default.
    We need to be careful about this. e.g:

    class ElectionListView(ListView):
        model = Election

    and ensure we override get_queryset().
    """
    private_objects = PrivateElectionsManager()
    public_objects = PublicElectionsManager()

    class Meta:
        ordering = ("election_id",)
        get_latest_by = "modified"

    def get_absolute_url(self):
        return reverse("single_election_view", args=(self.election_id,))

    @property
    def get_current(self):
        model_current = getattr(self, "current", None)
        if model_current is not None:
            return model_current

        recent_past = date.today() - timedelta(days=settings.CURRENT_PAST_DAYS)
        return self.poll_open_date >= recent_past

    def get_ballots(self):
        """
        If self has a group_type this returns all ballots that are descended from self.
        If self doesn't have a group_type (i.e. is a 'ballot') it returns itself.
        """
        if self.group_type:
            group, date = self.election_id.rsplit(".", 1)
            return Election.public_objects.filter(
                election_id__startswith=group + ".",
                election_id__endswith=date,
                group_type=None,
            )
        return None

    @property
    def group_seats_contested(self):
        """
        Returns the sum of the seats_contested property on all ballots that are
        descended from the election, unless self is a ballot, in which case
        self.seats_contested is returned.
        It's likely there are election groups where not every ballot has had
        seats_contested filled in, so treat with care.
        """
        if self.group_type:
            return (
                self.get_ballots()
                .aggregate(models.Sum("seats_contested"))
                .get("seats_contested__sum")
            )
        return self.seats_contested

    def __str__(self):
        return self.get_id()

    def get_example_postcode(self):
        if not self.group_type and self.geography:
            return (
                Onspd.objects.filter(location__within=self.geography.geography)
                .filter(
                    location__dwithin=(self.geography.geography.centroid, 0.08)
                )
                .annotate(
                    distance=Distance(
                        "location", self.geography.geography.centroid
                    )
                )
                .order_by("distance")
                .first()
            )
        return None

    @property
    def get_timetable(self):
        country_map = {
            "WLS": Country.WALES,
            "ENG": Country.ENGLAND,
            "NIR": Country.NORTHERN_IRELAND,
            "SCT": Country.SCOTLAND,
            "GBN": None,
        }
        area = self.division or self.organisation
        if not area:
            return None

        territory_code = area.territory_code or self.organisation.territory_code
        if not territory_code:
            return None

        try:
            timetable = from_election_id(
                self.election_id, country=country_map[territory_code]
            ).timetable
        except NoSuchElectionTypeError:
            timetable = None

        return timetable

    def get_id(self):
        if self.election_id:
            return self.election_id
        return self.tmp_election_id

    @property
    def geography(self):
        if self.identifier_type == "ballot" and self.division:
            return self.division_geography
        return self.organisation_geography

    @property
    def identifier_type(self):
        if not self.group_type:
            return "ballot"
        return self.group_type

    def get_division_geography(self):
        if self.division_geography:
            return self.division_geography

        if self.identifier_type == "ballot" and self.division:
            # attach geography by division if possible
            try:
                return self.division.geography
            except ObjectDoesNotExist:
                pass
        return None

    @property
    def ynr_link(self):
        if self.identifier_type in ["organisation", "ballot"]:
            return (
                "https://candidates.democracyclub.org.uk/elections/{}".format(
                    self.election_id
                )
            )
        return None

    @property
    def whocivf_link(self):
        if self.identifier_type in ["organisation", "ballot"]:
            return "https://whocanivotefor.co.uk/elections/{}".format(
                self.election_id
            )
        return None

    def get_organisation_geography(self):
        if self.organisation_geography:
            return self.organisation_geography

        try:
            if self.identifier_type == "ballot":
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

    def get_admin_url(self):
        """
        Build URL to the election in the admin
        """
        viewname = (
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change"
        )
        return reverse(viewname=viewname, kwargs={"object_id": self.pk})

    def clean(self):
        if not self.identifier_type == "ballot" and self.cancelled:
            raise ValidationError(
                "Can't set a group to cancelled. Only a ballot can be cancelled"
            )
        if not self.cancelled and self.cancellation_notice:
            raise ValidationError(
                "Only a cancelled election can have a cancellation notice"
            )
        if not self.cancelled and self.cancellation_reason:
            raise ValidationError(
                "Only a cancelled election can have a cancellation reason"
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        # used later to determine if we should look for ballots
        created = not self.pk

        status = kwargs.pop("status", None)
        user = kwargs.pop("user", None)
        notes = kwargs.pop("notes", "")[:255]

        self.division_geography = self.get_division_geography()
        self.organisation_geography = self.get_organisation_geography()

        if not self.group_id and self.group:
            try:
                group_model = Election.private_objects.get(
                    election_id=self.group.election_id
                )
            except Election.DoesNotExist:
                group_model = self.group.save(*args, **kwargs)
            self.group = group_model

        super().save(*args, **kwargs)
        if (
            status
            and status != DEFAULT_STATUS
            and status != self.current_status
        ):
            event = ModerationHistory(
                election=self, status_id=status, user=user, notes=notes
            )
            event.save()

        # if the object was created return here to save on unnecessary
        # db queries
        if created:
            return

        # otherwise check if we have related ballots
        ballots = self.get_ballots()
        if ballots:
            # if so update the modified date on them so that we import
            # the changes made on the parent election
            ballots.update(modified=self.modified)


@receiver(post_save, sender=Election, dispatch_uid="init_status_history")
def init_status_history(sender, instance, **kwargs):
    if not ModerationHistory.objects.all().filter(election=instance).exists():
        event = ModerationHistory(election=instance, status_id=DEFAULT_STATUS)
        event.save(initial_status=True)


class ModerationHistory(TimeStampedModel):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    status = models.ForeignKey(ModerationStatus, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    notes = models.CharField(blank=True, max_length=255)

    def save(self, **kwargs):
        # if this is the initial status no need to update the related election
        # so return early. This is because the default status is identical on
        # both this model and the Election model
        if kwargs.pop("initial_status", False):
            return super().save(**kwargs)

        # save the related election to update the modified timestamp so that it
        # is found by the importer looking for recent changes
        if self.election.current_status != self.status.short_label:
            self.election.current_status = self.status.short_label
            self.election.save()
        super().save(**kwargs)
        return None

    class Meta:
        verbose_name_plural = "Moderation History"
        get_latest_by = "modified"
        ordering = ("election", "-modified")


class Explanation(models.Model):
    description = models.CharField(blank=False, max_length=100)
    explanation = models.TextField()

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
    default_content_type = "application/pdf"
    default_acl = "public-read"


class Document(models.Model):
    source_url = models.URLField(max_length=1000)
    uploaded_file = models.FileField(
        max_length=1000, upload_to="", storage=PdfS3Storage()
    )

    def archive_document(self, url, election_id):
        # copy a notice of election document to our s3 bucket
        # because it won't stay on the council website forever

        filename = url.split("/")[-1]
        if filename == "":
            filename = "Notice_of_Election"
        with tempfile.NamedTemporaryFile() as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            self.uploaded_file.save(
                "%s/%s" % (election_id, filename), File(tmp)
            )
        return self.uploaded_file
