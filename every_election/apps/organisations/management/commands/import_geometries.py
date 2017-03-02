import os
import json
import time

import requests
import glob2

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.gis import geos
from django.contrib.gis.gdal import DataSource, GDALException


from organisations.models import (
    OrganisationDivision,
    DivisionGeography,
    Organisation,
)
from organisations.utils import create_geom_from_curie_list
from organisations.constants import (
    POLICE_AREA_NAME_TO_GSS, COMBINED_AUTHORITY_SLUG_TO_GSS)


class Command(BaseCommand):
    def handle(self, **options):
        self.import_boundary_line(
            os.path.join(
            settings.BOUNADY_PATH,
            "official_boundaries/**/*.shp"
        ))

        self.import_from_mapit()
        self.import_from_dgu()
        self.create_police_areas()
        self.create_combined_authority_areas()
        self.create_uk_areas()

    def import_boundary_line(self, base_path):
        LAYERS_BY_GSS = {}
        LAYERS_BY_UNIT_ID = {}

        for file_path in glob2.glob(base_path):
            print(file_path)
            ignore = [
                'high_water_polyline.shp',
                'parish_region.shp',
            ]
            if file_path.split('/')[-1] in ignore:
                continue

            try:
                ds = DataSource(file_path)
            except GDALException:
                # This is very strange – sometimes the above will fail the
                # first time, but not the second. Seen on OS X with GDAL
                # 2.2.0
                ds = DataSource(file_path)

            for layer in ds[0]:
                code = None
                if b'WardCode' in layer.fields:
                    code = str(layer['WardCode'])
                if b'PC_ID' in layer.fields:
                    code = str(layer['PC_ID'])
                if b'CODE' in layer.fields:
                    code = str(layer['CODE'])

                if code:
                    LAYERS_BY_GSS[str(code)] = layer

                if b'UNIT_ID' in layer.fields:
                    LAYERS_BY_UNIT_ID[str(layer['UNIT_ID'])] = layer


        def _process_qs(qs, obj_type="division"):
            for obj in qs:
                if obj_type == "organisation":
                    code_type, code = ('gss', obj.gss)
                else:
                    code_type, code = obj.geography_curie.split(':')
                code = str(code)
                if code_type in ["gss", "unit_id"]:
                    try:
                        if code in LAYERS_BY_GSS:
                            layer = LAYERS_BY_GSS[code]
                        elif code in LAYERS_BY_UNIT_ID:
                            layer = LAYERS_BY_UNIT_ID[code]
                        else:
                            raise KeyError

                        poly = self.clean_poly(layer.geom.geos)
                        kwargs = {
                            'geography': poly,
                            obj_type: obj
                        }
                        DivisionGeography.objects.create(**kwargs)
                    except KeyError:
                        pass
        _process_qs(OrganisationDivision.objects.filter(geography=None))
        _process_qs(Organisation.objects.filter(
            geography=None), obj_type="organisation")

    def clean_poly(self, poly, srid=27700):
        if not poly.srid:
            poly.set_srid(srid)
        poly = poly.transform(4326, clone=True)
        if isinstance(poly, geos.Polygon):
            poly = geos.MultiPolygon(poly)
        return poly

    def import_from_mapit(self):

        def _process_qs(qs, obj_type="division"):
            import ipdb; ipdb.set_trace()
            count = qs.count()
            for i, obj in enumerate(qs):
                print("{} of {}: {} ({})".format(
                    i,
                    count,
                    obj.name,
                    getattr(
                        obj, 'geography_curie', obj.format_geography_link())
                ))

                initial_req = requests.get(obj.format_geography_link())

                geo_json_url = "{}.geojson".format(initial_req.url)
                req = requests.get(geo_json_url)
                if req.status_code != 200:
                    print("Not found in MaPit: {}".format(initial_req.url))
                    continue
                json_data = req.text

                poly = self.clean_poly(geos.GEOSGeometry(json_data))
                kwargs = {
                    'geography': poly,
                    obj_type: obj,
                }
                DivisionGeography.objects.create(**kwargs)

                time.sleep(1)
        _process_qs(OrganisationDivision.objects.filter(
            geography=None).exclude(mapit_generation_high=None))
        _process_qs(Organisation.objects.filter(
            geography=None,).exclude(gss=None), obj_type="organisation")


    def import_from_dgu(self):
        def _process_qs(qs, obj_type="division"):
            count = qs.count()
            for i, obj in enumerate(qs):
                print("{} of {}: {} ({})".format(
                    i,
                    count,
                    obj.name,
                    getattr(
                        obj, 'geography_curie', obj.format_geography_link())
                ))

                if obj_type == "organisation":
                    code_type, code = ('gss', obj.gss)
                else:
                    code_type, code = obj.geography_curie.split(':')
                code = str(code)
                if code_type == "gss":
                    geo_json_url = "{}/{}.json".format(
                        "http://statistics.data.gov.uk/boundaries",
                        code
                    )
                    json_data = requests.get(geo_json_url).json()['geometry']
                    json_data = json.dumps(json_data)

                    poly = self.clean_poly(geos.GEOSGeometry(json_data))

                    kwargs = {
                        'geography': poly,
                        obj_type: obj,
                    }
                    DivisionGeography.objects.create(**kwargs)

                    time.sleep(1)

        _process_qs(OrganisationDivision.objects.filter(
            geography=None).exclude(mapit_generation_high=None))
        _process_qs(Organisation.objects.filter(
            geography=None,).exclude(gss=""), obj_type="organisation")

    def create_police_areas(self):
        for force_name, codes in POLICE_AREA_NAME_TO_GSS.items():
            codes = ["gss:{}".format(x) for x in codes]
            poly = self.clean_poly(create_geom_from_curie_list(codes))
            print(force_name)
            org = Organisation.objects.get(
                slug=force_name, organisation_type="police_area")

            if hasattr(org, 'geography'):
                org.geography.geography = poly
                org.geography.save()
            else:
                geog = DivisionGeography.objects.create(
                    organisation=org,
                    geography=poly
                )

    def create_combined_authority_areas(self):
        for ca_name, codes in COMBINED_AUTHORITY_SLUG_TO_GSS.items():
            codes = ["gss:{}".format(x) for x in codes]
            poly = self.clean_poly(create_geom_from_curie_list(codes))
            print(ca_name)
            org = Organisation.objects.get(
                slug=ca_name, organisation_type="combined-authority")

            if hasattr(org, 'geography'):
                org.geography.geography = poly
                org.geography.save()
            else:
                geog = DivisionGeography.objects.create(
                    organisation=org,
                    geography=poly
                )

    def create_uk_areas(self):
        # GB
        data_file = open(os.path.join(
            os.path.abspath('ad_hoc_boundaries'),
            "GB.geojson")).read()
        try:
            GB_geojson = DataSource(data_file)
        except:
            GB_geojson = DataSource(data_file)

        poly = self.clean_poly(GB_geojson[0][0].geom.geos)

        org = Organisation.objects.get(slug="parl")

        if hasattr(org, 'geography'):
            org.geography.geography = poly
            org.geography.save()
        else:
            geog = DivisionGeography.objects.create(
                organisation=org,
                geography=poly
            )

        # Scotland
        data_file = open(os.path.join(
            os.path.abspath('ad_hoc_boundaries'),
            "Scotland.geojson")).read()
        try:
            Scotland_geojson = DataSource(data_file)
        except:
            Scotland_geojson = DataSource(data_file)

        poly = self.clean_poly(Scotland_geojson[0][0].geom.geos)

        org = Organisation.objects.get(slug="sp")

        if hasattr(org, 'geography'):
            org.geography.geography = poly
            org.geography.save()
        else:
            geog = DivisionGeography.objects.create(
                organisation=org,
                geography=poly
            )

        # London
        org = Organisation.objects.get(slug="gla", organisation_type="gla")

        london = Organisation.objects.get(slug="london")
        if hasattr(london, 'geography'):
            london.geography.geography = org.geography.geography
            london.geography.save()
        else:
            geog = DivisionGeography.objects.create(
                organisation=london,
                geography=org.geography.geography
            )
