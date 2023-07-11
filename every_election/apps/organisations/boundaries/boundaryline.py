import sys

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
    def __init__(self, filename, show_picker=False):
        ds = DataSource(filename)
        if len(ds) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(ds)))
        self.layer = ds[0]
        self.show_picker = show_picker

    def merge_features(self, features):
        polygons = []
        for feat in features:
            if isinstance(feat.geom.geos, MultiPolygon):
                multipoly = feat.geom.geos
                polygons = polygons + [poly for poly in multipoly]
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

        overlap = overlap_percent(OGRGeometry(div.geography.geography.ewkt), match.geom)
        if overlap >= SANITY_CHECK_TOLERANCE:
            # close enough
            return None

        warning = (
            "Found {code} as potential match for {div} "
            + "but BoundaryLine shape for {code} only covers {percent:.2f}% "
            + "of {div}'s area. Manual review required."
        )
        warning = warning.format(
            code=self.get_code_from_feature(match),
            div=div.official_identifier,
            percent=overlap,
        )
        return warning

    def get_overlaps(self, div, features):
        # builds a list of (code, overlap %) tuples.
        # We don't use a dict ({code: overlap %}), because boundaryline splits multipolygons into separate features
        overlaps = []
        max_overlap = 0
        best_match = None
        for feature in features:
            intersection_area = (
                div.geography.geography.transform(27700, clone=True)
                .intersection(feature.geom.geos)
                .area
            )
            code = self.get_code_from_feature(feature)
            div_area = div.geography.geography.transform(27700, clone=True).area
            percent_overlap = intersection_area / div_area * 100
            if percent_overlap > max_overlap:
                max_overlap = percent_overlap
                best_match = feature
            overlaps.append((code, percent_overlap))

        return best_match, overlaps

    def evaluate_overlaps(self, div, best_match, overlaps):
        significant_overlaps = [
            (code, overlap)
            for code, overlap in overlaps
            if overlap >= SANITY_CHECK_TOLERANCE
        ]
        if len(significant_overlaps) > 1:
            raise MultipleObjectsReturned(
                "Found >1 possible matches for division {div} with significant overlap: {codes}".format(
                    div=div.official_identifier,
                    overlaps=overlaps,
                )
            )
        elif len(significant_overlaps) == 1:
            print(
                f"Matching {best_match.get('name')} ({self.get_code_from_feature(best_match)}) to {div.official_identifier} based on geom overlap"
            )
            return [best_match]
        else:
            raise ObjectDoesNotExist(
                f"Found 0 matches for division {div.official_identifier}. Check territory_code and/or division_type"
            )

    def get_division_code(self, div, org):
        filter_geom = OGRGeometry(org.geography.ewkt).transform(27700, clone=True)
        self.layer.spatial_filter = filter_geom
        # slugging names to compare them
        # will help reduce some ambiguity
        # e.g: St Helen's vs St. Helens
        division_name = normalize_name_for_matching(div.name)

        matches = []
        for feature in self.layer:
            if normalize_name_for_matching(feature.get("name")) == division_name:
                matches.append(feature)
            matched_codes = set(self.get_code_from_feature(match) for match in matches)
            if len(matched_codes) > 1:
                # ...but we also need to be a little bit careful
                best_match, overlaps = self.get_overlaps(div, matches)
                matches = self.evaluate_overlaps(div, best_match, overlaps)

        if len(matches) == 0:
            best_match, overlaps = self.get_overlaps(div, self.layer)
            matches = self.evaluate_overlaps(div, best_match, overlaps)

        warning = self.get_match_warning(div, matches[0])
        if warning:
            if self.show_picker:
                sys.stdout.write(
                    f"""{warning}
                Do you want to match {matches[0].get('name')} ({matches[0].get('code')}) to {div.official_identifier}?
                """
                )
                choice = input("enter 'y' to accept, or 'n' not to: ")
                if choice.lower() in ("y", "yes"):
                    return self.get_code_from_feature(matches[0])

            raise ObjectDoesNotExist(warning)

        return self.get_code_from_feature(matches[0])
