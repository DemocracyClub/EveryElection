from django.contrib.gis.gdal import DataSource, OGRGeometry
from django.contrib.gis.geos import MultiPolygon
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from organisations.boundaries.helpers import (
    normalize_name_for_matching,
    overlap_percent,
)

# Percentage overlap required for us to consider 2 divisions
# 'the same' without manual investigation
SANITY_CHECK_TOLERANCE = 97


class BoundaryLine:
    def __init__(self, filename):
        ds = DataSource(filename)
        if len(ds) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(ds)))
        self.layer = ds[0]

    def merge_features(self, features):
        """
        When we have geographies with 'Detached parts', these are
        represented in BoundaryLine as multiple records with the same code.

        For example, an area like this
        https://mapit.mysociety.org/area/12701.html

        is represented as 2 Polygons.

        We just want to represent this as a single MultiPolygon feature,
        so if we've matched >1 records with the same code
        merge them into a single MultiPolygon feature.
        """
        polygons = []
        for feat in features:
            if isinstance(feat.geom.geos, MultiPolygon):
                multipoly = feat.geom.geos
                polygons = polygons + list(multipoly)
            else:
                polygons.append(feat.geom.geos)

        return MultiPolygon(polygons)

    def get_feature_by_field(self, fieldname, code):
        matches = []
        for feature in self.layer:
            if str(feature.get(fieldname)) == code:
                matches.append(feature)

        if len(matches) == 0:
            raise ObjectDoesNotExist(
                "Expected one match for {code}, found 0".format(code=code)
            )
        if len(matches) == 1:
            return matches[0].geom.geos
        # handle 'Detached Parts'
        return self.merge_features(matches)

    def get_feature_by_name_and_county(self, div_slug, org_slug):
        matches = []
        slug_tuple = (div_slug, org_slug)
        for feat in self.layer:
            feat_name = normalize_name_for_matching(feat.get("name"))
            feat_county = normalize_name_for_matching(
                feat.get("file_name").replace("_", "-")
            )
            if (feat_name, feat_county) == slug_tuple:
                matches.append(feat)

        if len(matches) == 0:
            raise ObjectDoesNotExist(
                f"Expected one match for {slug_tuple}, found 0"
            )
        if len(matches) == 1:
            return matches[0].geom.geos
        # handle 'Detached Parts'
        return self.merge_features(matches)

    def get_code_from_feature(self, feature):
        if feature.get("area_code") == "CED":
            return "unit_id:" + str(feature.get("unit_id"))
        if feature.get("code") == "999999999":
            raise ValueError(
                "Expected GSS code but found {code} for feature: ({type} - {name})".format(
                    code=feature.get("code"),
                    type=feature.get("area_code"),
                    name=feature.get("name"),
                )
            )
        return "gss:" + feature.get("code")

    def get_match_warning(self, div, match):
        # return a warning if there is something to warn about
        # or None if everything looks OK

        if not div.geography.geography:
            # If we haven't got a division geography to check against,
            # just assume its fine. Its probably fine.
            return None

        overlap = overlap_percent(
            OGRGeometry(div.geography.geography.ewkt), match.geom
        )
        if overlap >= SANITY_CHECK_TOLERANCE:
            # close enough
            return None

        warning = (
            "Found {code} as potential match for {div} "
            + "but BoundaryLine shape for {code} only covers {percent:.2f}% "
            + "of {div}'s area. Manual review required."
        )
        return warning.format(
            code=self.get_code_from_feature(match),
            div=div.official_identifier,
            percent=overlap,
        )

    def get_division_code(self, div, org):
        filter_geom = OGRGeometry(org.geography.ewkt).transform(
            27700, clone=True
        )
        self.layer.spatial_filter = filter_geom
        # slugging names to compare them
        # will help reduce some ambiguity
        # e.g: St Helen's vs St. Helens
        division_name = normalize_name_for_matching(div.name)

        matches = []
        for feature in self.layer:
            if (
                normalize_name_for_matching(feature.get("name"))
                == division_name
            ):
                matches.append(feature)
            if len(matches) > 1:
                # ...but we also need to be a little bit careful
                raise MultipleObjectsReturned(
                    "Found >1 possible matches for division {div}: {codes}".format(
                        div=div.official_identifier,
                        codes=", ".join(
                            [
                                self.get_code_from_feature(match)
                                for match in matches
                            ]
                        ),
                    )
                )

        if len(matches) == 0:
            raise ObjectDoesNotExist(
                "Found 0 matches for division {div}".format(
                    div=div.official_identifier
                )
            )

        warning = self.get_match_warning(div, matches[0])
        if warning:
            raise ObjectDoesNotExist(warning)

        return self.get_code_from_feature(matches[0])
