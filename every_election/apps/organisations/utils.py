from datetime import timedelta, datetime

from django.contrib.gis.geos import MultiPolygon, Polygon, GEOSGeometry


from organisations.models import (
    OrganisationDivisionSet, Organisation, OrganisationDivision
)


def add_end_date_to_previous_div_sets(div_set):
    older_div_set = OrganisationDivisionSet.objects.filter(
        organisation=div_set.organisation,
        end_date=None,
        start_date__lt=div_set.start_date
    ).order_by('-start_date').first()
    if older_div_set:
        start_date = datetime.strptime(str(div_set.start_date), "%Y-%m-%d")
        older_div_set.end_date = start_date - timedelta(days=1)
        older_div_set.save()


def create_geom_from_curie_list(curie_list):
    obj_list = []
    gss_list = [x.split(':')[1] for x in curie_list if x.startswith('gss:')]
    obj_list += Organisation.objects.filter(gss__in=gss_list)
    obj_list += OrganisationDivision.objects.filter(
        geography_curie__in=curie_list)
    name = obj_list[0].name
    print(name)
    print("Joining…")

    obj_list = set(obj_list)

    geo_list = [x.geography.geography for x in obj_list]

    mp = GEOSGeometry(geo_list[0])

    for x in geo_list[1:]:
        # print("Adding {}".format(x.name))
        # x = x.buffer(0)
        # print(x.valid)
        # import ipdb; ipdb.set_trace()
        mp = mp.union(x)


    return mp
    # with open('/tmp/kml/{}.kml'.format(name), 'w') as f:
    #     f.write(mp.wkt)


    # print("Writing")
    # with open('/tmp/kml/{}.kml'.format(name), 'w') as f:
    #     f.write(mp.kml)
    # print([x.geography for x in obj_list])
