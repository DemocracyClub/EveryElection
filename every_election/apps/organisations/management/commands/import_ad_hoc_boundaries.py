import os
import json

from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis import geos

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
    DivisionGeography,
)


import unicodedata
def strip_accents(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn')
    s = s.replace("′", "'")
    return s

class Command(BaseCommand):


    def handle(self, **options):
        self.base_path = os.path.abspath('ad_hoc_boundaries')
        # self.import_lgbce()
        self.import_lgbcs()

    def _mk_file_path(self, year, filename):
        return os.path.join(self.base_path, year, filename)

    def _get_div_set(self, official_identifier, date, org_type):
        org = Organisation.objects.get(
            official_identifier=official_identifier,
            organisation_type=org_type
        )
        return OrganisationDivisionSet.objects.get(
            organisation=org, start_date=date)

    def clean_poly(self, poly, srid=27700):
        if not poly.srid:
            poly.set_srid(srid)
        poly = poly.transform(4326, clone=True)
        if isinstance(poly, geos.Polygon):
            poly = geos.MultiPolygon(poly)
        return poly

    def import_lgbcs(self):
        date = "2017-05-04"
        year = "2017"
        divisionset_to_file_map = {
            self._get_div_set('ABE', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Aberdeen_City_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('ABD', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Aberdeenshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('ANS', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Angus_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('EDH', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "City_of_Edinburgh_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('CLK', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Clackmannanshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('DGY', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Dumfries_and_Galloway_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('EAY', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "East_Ayrshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('EDU', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "East_Dunbartonshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('ELN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "East_Lothian_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('ERW', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "East_Renfrewshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('FAL', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Falkirk_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('FIF', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Fife_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('GLG', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Glasgow_City_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('HLD', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Highland_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('IVC', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Inverclyde_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('MLN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Midlothian_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('MRY', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Moray_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('NAY', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "North_Ayrshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('NLK', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "North_Lanarkshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('PKN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Perth_and_Kinross_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('RFW', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Renfrewshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('SAY', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "South_Ayrshire_Council_Area_Final_recommendations"
                ),
            self._get_div_set('SLK', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "South_Lanarkshire_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('STG', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "Stirling_Council_Area_Final_Recommendations"
                ),
            self._get_div_set('WDU', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "West_Dunbartonshire_Council_Area_Final_Recommendations"
                ),


        }
        self.import_from_divisionset_to_file_map(
            divisionset_to_file_map, data_type="shp", name_field="Ward_Name")

    def import_lgbce(self):
        date = "2017-05-04"
        year = "2017"
        divisionset_to_file_map = {

            self._get_div_set('CAM', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Cambridgeshire_final_divisions.geojson"
                ),

            self._get_div_set('DOR', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Dorset_final_divisions.geojson"
                ),

            self._get_div_set('BIR', "2018-05-03", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Birmingham_final_proposals.geojson"
                ),

            self._get_div_set('DEV', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Devon_final_divisions.geojson"
                ),

            self._get_div_set('ECA', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-East_Cambridgeshire_final_proposals.geojson"
                ),

            self._get_div_set('ESX', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-EastSussex_final_divisions.geojson"
                ),

            self._get_div_set('EAS', "2019-05-02", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Eastbourne_final_proposals.geojson"
                ),

            self._get_div_set('EAT', "2018-05-03", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Eastleigh_final_proposals.geojson"
                ),

            self._get_div_set('HAM', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Hampshire_final_divisions.geojson"
                ),

            self._get_div_set('HAS', "2018-05-03", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Hastings_final_proposals.geojson"
                ),

            self._get_div_set('HRT', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Hertfordshire_final_divisions.geojson"
                ),

            self._get_div_set('KEN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Kent_final_divisions.geojson"
                ),

            self._get_div_set('LAN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Lancashire_final_divisions.geojson"
                ),

            self._get_div_set('LEC', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Leicestershire_final_divisions.geojson"
                ),

            self._get_div_set('LEE', "2019-05-02", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Lewes_final_proposals.geojson"
                ),

            self._get_div_set('LIN', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Lincolnshire_final_divisions.geojson"
                ),

            self._get_div_set('SWK', "2018-05-03", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Southwark_final_proposals.geojson"
                ),

            self._get_div_set('NTT', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Nottinghamshire_final_divisions.geojson"
                ),

            self._get_div_set('ROH', "2019-05-02", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Rother_final_proposals.geojson"
                ),

            self._get_div_set('WAR', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Warwickshire_final_divisions.geojson"
                ),

            self._get_div_set('WEA', "2019-05-02", 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-Wealden_final_proposals.geojson"
                ),

            self._get_div_set('WSX', date, 'local-authority'):
                self._mk_file_path(
                    year,
                    "LGBCE-West_Sussex_final_divisions.geojson"
                ),

        }
        self.import_from_divisionset_to_file_map(
            divisionset_to_file_map)


    def check_json(self, div_set, data_path):
        data = json.loads(open(data_path).read())
        # Check some things
        if len(data['features']) != div_set.divisions.count():
            raise ValueError("Features and Division counts don't match")

        data_names = set(
            [x['properties']['Name'] for x in data['features']])
        div_names = set([x.name for x in div_set.divisions.all()])

        assert data_names == div_names, \
            "Names don't match:\n\tdata: {} \n\nvs\n\tdivs: {}".format(
                data_names.difference(div_names),
                div_names.difference(data_names)
            )

    def check_shp(self, div_set, data_path, name_field="Name"):
        try:
            data = DataSource(data_path)
        except:
            data = DataSource(data_path)

        # Check some things
        if len(data[0]) != div_set.divisions.count():
            raise ValueError("Features and Division counts don't match")

        data_names = set(
            [x.get('Ward_Name') for x in data[0]])
        div_names = set([strip_accents(x.name) for x in div_set.divisions.all()])

        assert data_names == div_names, \
            "Names don't match:\n\tdata: {} \n\nvs\n\tdivs: {}".format(
                data_names.difference(div_names),
                div_names.difference(data_names)
            )

    def fix_divisions(self, div_set):
        if div_set.organisation.slug == "east-renfrewshire":
            div_set.divisions.filter(
                name="Newton Means North and Neilston").update(
                    name="Newton Mearns North and Neilston"
                )

        if div_set.organisation.slug == "city-of-edinburgh":
            for div in div_set.divisions.all():
                div.name = div.name.replace(' / ', '/')
                div.save()

        if div_set.organisation.slug == "highland":
            OrganisationDivision.objects.filter(
                slug="eilean-aa2-cha-o").update(name="Eilean a′ Chéo")
            OrganisationDivision.objects.filter(
                slug="eilean-aa2-cha-o").update(slug="eilean-a-cheo")


    def import_from_divisionset_to_file_map(
        self, divisionset_to_file_map, data_type="json", name_field="Name"):
        for div_set, data_path in divisionset_to_file_map.items():
            print(data_path)
            self.fix_divisions(div_set)
            if data_type == "json":
                self.check_json(div_set, data_path)
            if data_type == "shp":
                self.check_shp(div_set, data_path, name_field=name_field)

            try:
                geo_data = DataSource(data_path)
            except:
                geo_data = DataSource(data_path)

            for feat in geo_data[0]:

                name = feat.get(name_field)
                if name == "Eilean a' Cheo":
                    name = "Eilean a′ Chéo"
                div = div_set.divisions.get(name=name)

                try:
                    geog = div.geography
                except DivisionGeography.DoesNotExist:
                    geog = DivisionGeography(division=div)

                new_geog = feat.geom.clone()
                new_geog.coord_dim = 2

                geog.geography = self.clean_poly(new_geog.geos)
                geog.save()
                div.save()



