from django.core.management.base import BaseCommand

from elections.models import ElectionType, ElectionSubType, VotingSystem
from elections import constants


class Command(BaseCommand):
    def handle(self, *args, **options):
        for type_name, info in constants.ELECTION_TYPES.items():
            if info.get("default_voting_system"):
                voting_system, _ = VotingSystem.objects.get_or_create(
                    slug=info["default_voting_system"]
                )
            else:
                voting_system = None

            election_type, _ = ElectionType.objects.update_or_create(
                election_type=type_name,
                defaults={"name": info["name"], "default_voting_system": voting_system},
            )
            for subtype in info["subtypes"]:
                ElectionSubType.objects.update_or_create(
                    election_type=election_type,
                    election_subtype=subtype["election_subtype"],
                    defaults={"name": subtype["name"]},
                )

        for election_type in ElectionType.objects.all():
            missing_vs = election_type.election_set.filter(voting_system=None)
            missing_vs.update(voting_system=election_type.default_voting_system)
