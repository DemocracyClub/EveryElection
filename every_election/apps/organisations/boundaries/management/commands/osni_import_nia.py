from django.utils.text import slugify
from organisations.boundaries.management.base import BaseOsniCommand
from organisations.boundaries.osni import OsniLayer
from organisations.models import OrganisationDivision


class Command(BaseOsniCommand):
    def handle(self, *args, **options):
        """
        Northern Ireland Assembly constituency names and boundaries
        are the same as the Westminster Constituency names and boundaries
        """
        url = "http://osni-spatial-ni.opendata.arcgis.com/datasets/563dc2ec3d9943428e3fe68966d40deb_3.geojson"
        self.layer = OsniLayer(url, "PC_ID", "PC_NAME")

        for feature in self.layer.features:
            record = OrganisationDivision.objects.all().get(
                official_identifier="osni_oid:NIE-{}".format(
                    feature["OBJECTID"]
                ),
                slug=slugify(feature["name"]),
            )
            self.import_boundary(record, feature)

        self.stdout.write("...done!")
