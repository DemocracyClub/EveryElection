import json

from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand
from django.db.models import Value

from core.mixins import ReadFromFileMixin
from core.models import JsonbSet
from elections.models import Election


def get_layer(data, layer_index=0):
    data_source = DataSource(data.name)
    if len(data_source) < layer_index + 1:
        raise ValueError(f"Expected layer at index: {layer_index}, None found")
    return data_source[layer_index]


class Command(ReadFromFileMixin, BaseCommand):
    help = """
    Update tags field on Election model.
    Example usage:
    python manage.py add_tags -u 'https://opendata.arcgis.com/datasets/01fd6b2d7600446d8af768005992f76a_2.geojson' --fields '{"NUTS118NM": "value", "NUTS118CD": "key"}' --tag-name NUTS1
    """

    # TODO: add a flag to make overwriting optional - or at least warn about it.
    # TODO: add some way of filtering which elections to apply it too.
    # TODO: make it possible to get a layer by name.
    def add_arguments(self, parser):
        parser.add_argument(
            "--fields",
            action="store",
            dest="field_map",
            help="A map of fields in the form: {'field name in source':'name to store'}",
            required=True,
        )
        parser.add_argument(
            "--tag-name",
            action="store",
            dest="tag_name",
            help="Name of tag to store",
            required=True,
        )
        parser.add_argument(
            "--layer-index",
            action="store",
            default=0,
            type=int,
            dest="layer_index",
            help="Index of layer in dataset",
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):
        field_map = json.loads(options["field_map"])
        tag_name = options["tag_name"]
        self.stdout.write("Loading data...")
        data = self.load_data(options)
        self.stdout.write("...data loaded.")
        layer = get_layer(data, options["layer_index"])
        self.stdout.write(f"Reading data from {layer.name}")
        for feature in layer:
            tags = {}
            for field in field_map:
                tags[field_map[field]] = feature.get(field)
            self.stdout.write(f"Setting tags: {tag_name} to {tags}...")
            ballots = Election.private_objects.ballots_with_point_in_area(
                feature.geom.geos
            )
            self.stdout.write(f"...for {len(ballots)} ballots...")
            ballots.update(
                tags=JsonbSet(
                    "tags", Value(f"{{{tag_name}}}"), Value(json.dumps(tags)), True
                )
            )
            self.stdout.write("...done.")
