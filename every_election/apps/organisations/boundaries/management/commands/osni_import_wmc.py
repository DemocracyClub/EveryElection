from organisations.boundaries.management.base import BaseOsniCommand
from organisations.boundaries.osni import OsniLayer
from organisations.models import OrganisationDivision


class Command(BaseOsniCommand):
    def handle(self, *args, **options):
        url = "http://osni-spatial-ni.opendata.arcgis.com/datasets/563dc2ec3d9943428e3fe68966d40deb_3.geojson"
        self.layer = OsniLayer(url, "PC_ID", "PC_NAME")

        for feature in self.layer.features:
            if "gss" in feature:
                record = OrganisationDivision.objects.all().get(
                    official_identifier="gss:{}".format(feature["gss"])
                )
                self.import_boundary(record, feature)
            else:
                raise Exception("Expected GSS code")

        self.stdout.write("...done!")
