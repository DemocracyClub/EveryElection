from django.utils.text import slugify
from organisations.boundaries.management.base import BaseOsniCommand
from organisations.boundaries.osni import OsniLayer
from organisations.models import OrganisationDivision


class Command(BaseOsniCommand):

    def handle(self, *args, **options):
        url = 'http://osni-spatial-ni.opendata.arcgis.com/datasets/981a83027c0e4790891baadcfaa359a3_4.geojson'
        self.layer = OsniLayer(url, None, 'FinalR_DEA')

        for feature in self.layer.features:
            # OSNI doesn't include the GSS codes (N10xxxxxx) on their
            # District Electoral Areas dataset so we have to match by name.
            # Fortunately they are unique within Northern Ireland
            record = OrganisationDivision.objects.all().get(
                division_type='LGE',
                slug=slugify(feature['name']))
            self.import_boundary(record, feature)

        self.stdout.write("...done!")
