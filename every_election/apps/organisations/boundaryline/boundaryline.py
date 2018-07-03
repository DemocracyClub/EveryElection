from django.contrib.gis.gdal import DataSource, OGRGeometry
from django.utils.text import slugify


class BoundaryLine:

    def __init__(self, filename):
        ds = DataSource(filename)
        if len(ds) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(ds)))
        self.layer = ds[0]

    def normalize_name(self, name):
        slug = slugify(name)
        if slug.endswith('-ed'):
            return slug[:-3]
        if slug.endswith('-ward'):
            return slug[:-5]
        return slug

    def get_code_from_feature(self, feature):
        if feature.get('area_code') == 'CED':
            return "unit_id:" + str(feature.get('unit_id'))
        if feature.get('code') == '999999999':
            raise ValueError(
                'Expected GSS code but found {code} for feature: ({type} - {name})'.format(
                    code=feature.get('code'),
                    type=feature.get('area_code'),
                    name=feature.get('name')
                )
            )
        return 'gss:' + feature.get('code')

    def get_division_code(self, div, org):
        filter_geom = OGRGeometry(org.geography.ewkt).transform(27700, clone=True)
        self.layer.spatial_filter = filter_geom
        # slugging names to compare them
        # will help reduce some ambiguity
        # e.g: St Helen's vs St. Helens
        division_name = self.normalize_name(div.name)

        matches = 0
        match = None
        for feature in self.layer:
            if self.normalize_name(feature.get('name')) == division_name:
                match = self.get_code_from_feature(feature)
                matches = matches + 1
            if matches > 1:
                # ...but we also need to be a little bit careful
                print('Found >1 matches for division {div}'.format(
                    div=div.official_identifier))
                return None

        return match
