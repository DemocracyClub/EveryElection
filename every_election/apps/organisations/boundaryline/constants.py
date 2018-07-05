from itertools import groupby


AREA_TYPE_TO_FILE = [
    ('CED', 'county_electoral_division_region.shp'),
    ('UTE', 'unitary_electoral_division_region.shp'),
    ('DIW', 'district_borough_unitary_ward_region.shp'),
    ('LBW', 'district_borough_unitary_ward_region.shp'),
    ('MTW', 'district_borough_unitary_ward_region.shp'),
    ('UTW', 'district_borough_unitary_ward_region.shp'),
    ('CTY', 'county_region.shp'),
    ('GLA', 'county_region.shp'),
    ('UTA', 'district_borough_unitary_region.shp'),
    ('MTD', 'district_borough_unitary_region.shp'),
    ('LBO', 'district_borough_unitary_region.shp'),
    ('DIS', 'district_borough_unitary_region.shp'),
    ('LAC', 'greater_london_const_region.shp'),
    ('SPC', 'scotland_and_wales_const_region.shp'),
    ('WAC', 'scotland_and_wales_const_region.shp'),
    ('SPE', 'scotland_and_wales_region.shp'),
    ('WAE', 'scotland_and_wales_region.shp'),
    ('WMC', 'westminster_const_region.shp'),
]


def get_area_type_lookup(filter=lambda x: True, group=False):

    filtered = [a for a in AREA_TYPE_TO_FILE if filter(a[0])]

    if group == True:
        lookup = {}
        for filename, types in groupby(filtered, lambda x: x[1]):
            lookup[tuple((rec[0] for rec in types))] = filename
        return lookup

    return {
        a[0] : a[1] for a in filtered
    }
