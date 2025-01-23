from django.utils.text import slugify


def overlap_percent(geom1, geom2):
    # How much of the area of geom2 is also inside geom1
    # (expressed as a percentage)
    g1 = geom1.transform(27700, clone=True)
    g2 = geom2.transform(27700, clone=True)
    intersection = g1.intersection(g2)
    return (intersection.area / g1.area) * 100


def normalize_name_for_matching(name):
    # Slug a name and remove suffixes so we can compare division
    # names within a local authority ignoring minor differences
    # and the suffixes ' Ward' and ' ED' (which are appended to
    # the names of wards and electoral districts in BoundaryLine)
    slug = slugify(name)
    if slug.endswith("-ed"):
        return slug[:-3]
    if slug.endswith("-ward"):
        return slug[:-5]
    if slug.endswith("-county"):
        return slug[:-7]
    return slug


def split_code(code):
    return tuple(code.split(":"))
