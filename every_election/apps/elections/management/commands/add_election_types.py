from django.core.management.base import BaseCommand
from elections.models import ElectionSubType, ElectionType
from uk_election_ids.datapackage import ELECTION_TYPES


class Command(BaseCommand):
    def handle(self, *args, **options):
        for type_name, info in ELECTION_TYPES.items():
            election_type, _ = ElectionType.objects.update_or_create(
                election_type=type_name,
                defaults={"name": info["name"]},
            )
            for subtype in info["subtypes"]:
                ElectionSubType.objects.update_or_create(
                    election_type=election_type,
                    election_subtype=subtype["election_subtype"],
                    defaults={"name": subtype["name"]},
                )
