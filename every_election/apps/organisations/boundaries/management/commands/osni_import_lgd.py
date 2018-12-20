from organisations.boundaries.management.base import BaseOsniCommand
from organisations.boundaries.osni import OsniLayer
from organisations.models import OrganisationGeography


class Command(BaseOsniCommand):
    def handle(self, *args, **options):
        url = "http://osni-spatial-ni.opendata.arcgis.com/datasets/a55726475f1b460c927d1816ffde6c72_2.geojson"
        self.layer = OsniLayer(url, "LGDCode", "LGDNAME")

        for feature in self.layer.features:
            if "gss" in feature:
                record = OrganisationGeography.objects.all().get(gss=feature["gss"])
                self.import_boundary(record, feature)
            else:
                raise Exception("Expected GSS code")

        self.stdout.write("...done!")
