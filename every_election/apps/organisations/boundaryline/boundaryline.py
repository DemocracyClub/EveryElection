from django.contrib.gis.gdal import DataSource, OGRGeometry
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from organisations.boundaryline.helpers import normalize_name_for_matching, overlap_percent


# Percentage overlap required for us to consider 2 divisions
# 'the same' without manual investigation
SANITY_CHECK_TOLERANCE = 97


class BoundaryLine:

    def __init__(self, filename):
        ds = DataSource(filename)
        if len(ds) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(ds)))
        self.layer = ds[0]

    def get_feature_by_field(self, fieldname, code):
        matches = 0
        match = None
        for feature in self.layer:
            if str(feature.get(fieldname)) == code:
                match = feature
                matches = matches + 1

        if matches == 0:
            raise ObjectDoesNotExist(
                "Expected one match for {code}, found 0".format(code=code)
            )
        if matches == 1:
            return match

        raise MultipleObjectsReturned(
            "Expected one match for {code}, found {matches}".format(
                code=code,
                matches=matches
            )
        )

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

    def get_match_warning(self, div, match):
        # return a warning if there is something to warn about
        # or None if everything looks OK

        if not div.geography.geography:
            # If we haven't got a division geography to check against,
            # just assume its fine. Its probably fine.
            return None

        overlap = overlap_percent(
            OGRGeometry(div.geography.geography.ewkt),
            match.geom
        )
        if overlap >= SANITY_CHECK_TOLERANCE:
            # close enough
            return None

        warning = "Found {code} as potential match for {div} " +\
            "but BoundaryLine shape for {code} only covers {percent:.2f}% " +\
            "of {div}'s area. Manual review required."
        warning = warning.format(
            code=self.get_code_from_feature(match),
            div=div.official_identifier,
            percent=overlap
        )
        return warning

    def get_division_code(self, div, org):
        filter_geom = OGRGeometry(org.geography.ewkt).transform(27700, clone=True)
        self.layer.spatial_filter = filter_geom
        # slugging names to compare them
        # will help reduce some ambiguity
        # e.g: St Helen's vs St. Helens
        division_name = normalize_name_for_matching(div.name)

        matches = 0
        match = None
        for feature in self.layer:
            if normalize_name_for_matching(feature.get('name')) == division_name:
                match = feature
                matches = matches + 1
            if matches > 1:
                # ...but we also need to be a little bit careful
                raise MultipleObjectsReturned(
                    'Found >1 matches for division {div}'.format(
                        div=div.official_identifier)
                )

        if matches == 0:
            raise ObjectDoesNotExist(
                'Found 0 matches for division {div}'.format(
                    div=div.official_identifier)
            )

        warning = self.get_match_warning(div, match)
        if warning:
            raise ObjectDoesNotExist(warning)

        return self.get_code_from_feature(match)
