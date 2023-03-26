import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

layers = {
    "openmap-local": {
        "buildings": {"file_glob": "*_Building.shp"},
        "roads": {"file_glob": "*_Road.shp"},
        "surface_water": {"file_glob": "*_SurfaceWater_Area.shp"},
        "tidal": {"file_glob": "*_TidalWater.shp"},
        "stations": {"file_glob": "*_RailwayStation.shp"},
        "railway_track": {"file_glob": "*_RailwayTrack.shp"},
        "railway_tunnel": {"file_glob": "*_RailwayTunnel.shp"},
        "roundabout": {"file_glob": "*_Roundabout.shp"},
    },
    "greenspaces": {"greenspaces": {"file_glob": "*_GreenspaceSite.shp"}},
}


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument(
            "data_dir",
            action="store",
            help="Path to OS Open Map Local data directory",
            type=Path,
        )
        parser.add_argument(
            "--product", default="openmap-local", action="store", choices=layers.keys()
        )

    def handle(self, *args, **options):
        self.cursor = connection.cursor()

        self.data_dir = options["data_dir"]

        for layer, layer_data in layers[options["product"]].items():
            self.create_table(layer, layer_data)

    def table_name_from_layer_name(self, layer):
        return f"og_images_layer_{layer}".replace("-", "_")

    def layer_files(self, layer, layer_data):
        return list(self.data_dir.glob(f"**/{layer_data['file_glob']}"))

    def create_table(self, layer, layer_data):
        """
        Drop the old table
        Generate layer SQL
        Create the new table
        """
        self.cursor.execute(
            f"""
        DROP TABLE IF EXISTS {self.table_name_from_layer_name(layer)} 
        """,
        )
        layer_files = self.layer_files(layer, layer_data)
        result = subprocess.run(
            [
                "shp2pgsql",
                "-p",
                "-I",
                layer_files[0],
                self.table_name_from_layer_name(layer),
            ],
            stdout=subprocess.PIPE,
        )
        self.cursor.execute(result.stdout)

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            for i, filename in enumerate(layer_files):
                result = subprocess.run(
                    [
                        "shp2pgsql",
                        "-D",  # Dump format
                        "-s",  # Transform the SRID
                        "27700:4326",  # From:to
                        "-a",  # Append data, don't create table
                        filename,
                        self.table_name_from_layer_name(layer),
                    ],
                    stdout=subprocess.PIPE,
                )
                temp_path = Path(tmpdir) / f"{i}.dump"
                with open(temp_path, "wb") as f:
                    f.write(result.stdout)
                database = settings.DATABASES["default"]
                connection_string = f"postgresql://{database['USER']}:{database['PASSWORD']}@{database['HOST']}/{database['NAME']}"
                subprocess.run(
                    [
                        "psql",
                        connection_string,
                        "-f",  # File
                        temp_path,
                    ],
                    stdout=subprocess.DEVNULL,
                )
