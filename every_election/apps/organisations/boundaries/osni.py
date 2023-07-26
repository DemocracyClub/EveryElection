import json
import urllib.request
from urllib.error import HTTPError
from retry import retry
from django.contrib.gis.geos import GEOSGeometry
from storage.shapefile import convert_geom_to_multipolygon


class OsniLayer:
    @retry(HTTPError, tries=2, delay=30)
    def get_data_from_url(self, url):
        with urllib.request.urlopen(url, timeout=30) as response:
            """
            When an ArcGIS server can't generate a response
            within X amount of time, it will return a 202 ACCEPTED
            response with a body like
            {
              "processingTime": "27.018 seconds",
              "status": "Processing",
              "generating": {}
            }
            and expects the client to poll it.
            """
            if response.code == 202:
                raise HTTPError(
                    url,
                    response.code,
                    response.msg,
                    response.headers,
                    response.fp,
                )
            data = response.read()
            return data

    def __init__(self, url, gss_field, name_field):
        ds = json.loads(self.get_data_from_url(url).decode("utf-8"))
        self.features = []

        for feature in ds["features"]:
            geom = GEOSGeometry(json.dumps(feature["geometry"]), srid=4326)
            geom = convert_geom_to_multipolygon(geom)
            rec = {
                "geometry": geom,
                "name": feature["properties"][name_field],
                "OBJECTID": feature["properties"]["OBJECTID"],
            }
            if gss_field:
                rec["gss"] = feature["properties"][gss_field]
            self.features.append(rec)
