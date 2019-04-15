from organisations.boundaries.management.base import BaseOsniCommand
from organisations.boundaries.osni import OsniLayer
from organisations.models import OrganisationDivision


class Command(BaseOsniCommand):
    def handle(self, *args, **options):
        url = "http://osni-spatial-ni.opendata.arcgis.com/datasets/d9dfdaf77847401e81efc9471dcd09e1_0.geojson"
        self.layer = OsniLayer(url, "NAME", "NAME")
        gss = "N07000001"

        self.layer.features[0]["gss"] = gss
        record = OrganisationDivision.objects.all().get(
            official_identifier="gss:{}".format(gss)
        )
        self.import_boundary(record, self.layer.features[0])

        self.stdout.write("...done!")
