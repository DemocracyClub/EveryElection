import re

from django.core.management import BaseCommand
from django.db import connection


class SVGGenerator:
    def __init__(self, object_id, object_type="divisiongeography"):
        self.object_type = object_type
        self.object_id = object_id
        self.cursor = connection.cursor()

        self.svg_layers = []

        self.object_svg = self.get_object_svg()
        self.touching_svg = self.get_touching_svg()

        self.svg_layers.append(self.style_touching(self.touching_svg))
        self.svg_layers.append(self.style_division(self.object_svg))
        self.svg_layers += self.get_buildings()
        self.svg_layers += self.get_roads()


    def style_touching(self, touching):
        return "\n".join(
            [
                f"""<path d="{path}" fill="#EEE" style="stroke-width:{{width}};stroke:#CCC;stroke-opacity:1" />"""
                for path in touching
            ]
        )

    def style_division(self, division):
        return "\n".join(
            [
                f"""<path d="{path}" fill="#E6007C" style="stroke-width:{{width}};stroke:#000;stroke-opacity:0.2" />"""
                for path in division
            ]
        )

    def get_viewbox(self):
        def _float_if_float(input):
            try:
                return float(input)
            except ValueError:
                return None

        x_max = -1000
        x_min = 1000
        y_max = -1000
        y_min = 1000
        for svg in self.svg_layers:
            cleaned = re.sub("[A-Za-z]", "", svg)
            cleaned = re.sub("[\s]+", " ", cleaned).strip()
            x_list = []
            y_list = []
            for i, part in enumerate(cleaned.split(" ")):
                floated = _float_if_float(part)
                if not floated:
                    continue
                if i % 2:
                    add_to = y_list
                else:
                    add_to = x_list
                add_to.append(floated)

            x_max = max(
                x_max, max([_float_if_float(x) for x in x_list if
                            _float_if_float(x)])
            )
            x_min = min(
                x_min, min([_float_if_float(x) for x in x_list if
                            _float_if_float(x)])
            )
            y_max = max(
                y_max, max([_float_if_float(x) for x in y_list if
                            _float_if_float(x)])
            )
            y_min = min(
                y_min, min([_float_if_float(x) for x in y_list if
                            _float_if_float(x)])
            )

        # print("-0.38996970653533936 -53.20250701904297 0.2129676789045334 0.2129669189453125")
        self.width = x_max - x_min
        self.height = y_max - y_min
        self.viewport = f"{x_min} {y_min} {self.width} {self.height}"
        # print(viewport)
        return self.viewport
        # import sys
        # sys.exit()
        # return

    def write_svg(self):
        viewbox = self.get_viewbox()
        paths = "\n".join(path.format(width=self.width * 0.004) for path in
                          self.svg_layers)
        print(
            f"""
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="background-color:#99ccff" height="800" width="800" viewBox="{viewbox}">
        {paths}
        </svg>
        """
        )

    def get_buildings(self):
        sql = """ 
        SELECT st_assvg(geom) 
        FROM buildings   
        WHERE st_coveredby(
            geom, 
            (SELECT dg.geography
                FROM organisations_divisiongeography dg 
                WHERE division_id = %s)
            ) 
        """ % (self.object_id, )
        self.cursor.execute(sql)
        svg_list = [
            f"""<path d="{row[0]}" fill="black" style="stroke-width:0.00002;stroke:#000;stroke-opacity:1" />"""
            for row in self.cursor.fetchall()]

        return svg_list

    def get_roads(self):
        sql = """ 
        SELECT st_assvg(geom) 
        FROM roads   
        WHERE st_coveredby(
            geom, 
            (SELECT st_envelope(
                        ST_MinimumBoundingCircle(
                            st_envelope(
                                dg.geography
                            )
                        )
                    ) 
                FROM organisations_divisiongeography dg 
                WHERE division_id = %s)
            ) 
        """ % (self.object_id, )
        self.cursor.execute(sql)
        svg_list = [
            f"""<path d="{row[0]}" fill="none" style="stroke-width:0.00001;stroke:#000;stroke-opacity:1" />"""
            for row in self.cursor.fetchall()]

        return svg_list

    def get_touching_svg(self):
        sql = """
        SELECT 
            st_assvg(st_intersection(
                (
                    SELECT 
                    st_envelope(
                        ST_MinimumBoundingCircle(
                            st_envelope(
                                dg.geography
                            )
                        )
                    ) as gg 
                    FROM organisations_divisiongeography dg 
                    WHERE division_id = %s
                ),
                dg.geography
            )) as gg
        FROM organisations_divisiongeography dg
        WHERE ST_Overlaps(
                (
                    SELECT 
                    st_envelope(
                        ST_MinimumBoundingCircle(
                            st_envelope(
                                dg.geography
                            )
                        )
                    ) as gg 
                    FROM organisations_divisiongeography dg 
                    WHERE division_id = %s
                )
                , 
                dg.geography
                
        )
        """ % (self.object_id, self.object_id)

        self.cursor.execute(sql)
        svg_list = [row[0] for row in self.cursor.fetchall()]
        return svg_list

    def get_object_svg(self):
        sql = """
                SELECT 
                    st_assvg(dg.geography)
                FROM organisations_divisiongeography dg 
                WHERE division_id = %s
                """ % self.object_id

        self.cursor.execute(sql)
        svg_list = [row[0] for row in self.cursor.fetchall()]
        return svg_list


class Command(BaseCommand):
    def handle(self, *args, **options):
        svg = SVGGenerator(21888)
        svg.write_svg()
