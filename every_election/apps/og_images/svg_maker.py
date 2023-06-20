from django.db import connection

from elections.models import Election


class SVGGenerator:
    def __init__(self, ballot: Election):
        if ballot.group_type:
            raise ValueError(
                f"Can only make a SVG for a ballot not {ballot.group_type=}"
            )
        self.ballot = ballot
        if self.ballot.division:
            self.geography_object_type = "organisations_divisiongeography"
            self.area_object = self.ballot.division
        else:
            self.geography_object_type = "organisations_organisationeography"
            self.area_object = self.ballot.organisation

        self.divisionset_id = self.area_object.divisionset_id

        self.cursor = connection.cursor()
        self.bounding_box = self.get_bounding_box_geom()

        self.svg_layers = []

        self.object_svg = self.get_object_svg()
        self.svg_layers.append(self.style_division(self.object_svg))

        self.touching_svg = self.get_touching_svg()
        self.svg_layers.insert(0, self.style_touching(self.touching_svg))
        self.svg_layers += self.get_buildings()
        self.svg_layers += self.get_roads()
        self.svg_layers += self.get_roundabout()
        self.svg_layers += self.get_surface_water()
        self.svg_layers += self.get_tidal()
        self.svg_layers += self.get_greenspace()
        self.svg_layers += self.get_railway()
        self.svg_layers += self.get_railway_tunnel()
        self.svg_layers += self.get_stations()

    def style_touching(self, touching):
        return "\n".join(
            [
                f"""<path d="{path}" fill="#FFF" style="stroke-width:{{width}};stroke:#403F41;stroke-opacity:0.2" />"""
                for path in touching
            ]
        )

    def style_division(self, division):
        return "\n".join(
            [
                f"""<path d="{path}" fill="#EEE" style="stroke-width:{{width}};stroke:#E6007C;stroke-opacity:1" filter="url(#sofGlow)" />"""
                for path in division
            ]
        )

    def get_viewbox(self):
        self.cursor.execute(
            """
        select 
            ST_XMin(extent) ,
            -ST_YMax(extent) ,
            ST_XMax(extent) - ST_XMin(extent) as w, 
            ST_YMax(extent) - ST_YMin(extent) as h
        FROM (
            SELECT ST_Extent(ST_TRansform(%s::geometry, 27700)
        ) AS extent) 
        AS bounding_box
        
        """,
            [self.bounding_box],
        )

        extent = self.cursor.fetchone()
        self.width = extent[2]
        return " ".join([str(x) for x in extent])

    def svg(self):
        viewbox = self.get_viewbox()
        paths = "\n".join(
            path.format(width=self.width * 0.001) for path in self.svg_layers
        )
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="background-color:#99ccff" height="800" width="800" viewBox="{viewbox}">
        	<defs>

	<filter id="sofGlow" height="300%" width="300%" x="-75%" y="-75%">
		<!-- Thicken out the original shape -->
		<feMorphology operator="dilate" radius="15" in="SourceAlpha" result="thicken" />

		<!-- Use a gaussian blur to create the soft blurriness of the glow -->
		<feGaussianBlur in="thicken" stdDeviation="15" result="blurred" />

		<!-- Change the colour -->
		<feFlood flood-color="rgba(230,0,124,0.3)" result="glowColor" />

		<!-- Color in the glows -->
		<feComposite in="glowColor" in2="blurred" operator="in" result="softGlow_colored" />

		<!--	Layer the effects together -->
		<feMerge>
			<feMergeNode in="softGlow_colored"/>
			<feMergeNode in="SourceGraphic"/>
		</feMerge>

	</filter>

</defs>
        
        
        {paths}
        </svg>
        """

    def get_bounding_box_geom(self):
        sql_str = f"""
        SELECT st_transform(
        st_envelope(
            ST_MinimumBoundingCircle(
                st_envelope(
                    ST_Transform(geog_table.geography, 27700)
                )
            )
        )
        , 4326) 
        FROM {self.geography_object_type} geog_table 
        WHERE division_id = %s;
        """

        self.cursor.execute(
            sql_str,
            [
                self.area_object.pk,
            ],
        )
        return self.cursor.fetchone()[0]

    def get_touching_svg(self):
        sql = f"""
        SELECT 
            st_assvg(
              ST_Transform(
                st_intersection(
                  %s::geometry,
                  geom_table.geography)
              , 27700)
            ) AS gg
        FROM {self.geography_object_type} geom_table
        WHERE ST_Overlaps(
                %s::geometry, 
                geom_table.geography
        )
        """
        self.cursor.execute(
            sql,
            [
                self.bounding_box,
                self.bounding_box,
            ],
        )
        svg_list = [row[0] for row in self.cursor.fetchall()]
        return svg_list

    def get_object_svg(self):
        sql_str = f"""
                SELECT 
                    st_assvg(st_transform(geom_table.geography, 27700))
                FROM {self.geography_object_type} geom_table
                WHERE division_id = %s
                """

        self.cursor.execute(sql_str, [self.area_object.pk])
        svg_list = [row[0] for row in self.cursor.fetchall()]
        return svg_list

    def get_buildings(self):
        sql = f"""
        SELECT st_assvg(ST_Transform(geom, 27700))
        FROM og_images_layer_buildings
        WHERE 
        st_coveredby(geom::geometry,
                    %s::geometry) AND
        st_coveredby(
            geom,
            (SELECT geog_table.geography
                FROM {self.geography_object_type} geog_table
                WHERE 
                     
                    division_id = %s)
            )
        """
        self.cursor.execute(
            sql,
            [
                self.bounding_box,
                self.area_object.pk,
            ],
        )
        svg_list = [
            f"""<path d="{row[0]}" fill="black" style="stroke-width:0.00002;stroke:#000;stroke-opacity:1" />"""
            for row in self.cursor.fetchall()
        ]

        return svg_list

    def get_roads(self):
        sql = f"""
        SELECT
            drawlevel, st_assvg(
              ST_Transform(
--                 st_intersection(
--                   %s::geometry,
                  geom
--                   )
              , 27700)
            ) AS gg
        FROM og_images_layer_roads
        WHERE 
        st_intersects(
                geom::geometry,
                %s::geometry 
                
        )
        """
        self.cursor.execute(
            sql,
            [
                self.bounding_box,
                self.bounding_box,
            ],
        )
        svg_list = []
        for row in self.cursor.fetchall():
            scale = int(row[0]) + 1
            scale = pow(scale, 2)
            svg_list.append(
                f"""<path d="{row[1]}" fill="none" style="stroke-width:{5*scale};stroke:#000;stroke-opacity:0.4" />"""
            )
        return svg_list

    def get_surface_water(self):
        attrs = """
        fill="rgba(0,206,209,0.2)" style="stroke-width:0.001;stroke:#000;stroke-opacity:0.9"
        """
        return self.add_bb_layer("surface_water", attrs)

    def get_tidal(self):
        attrs = """
        fill="rgba(0,206,209,0.2)" style="stroke-width:0.001;stroke:#000;stroke-opacity:0.9"
        """
        return self.add_bb_layer("tidal", attrs)

    def get_greenspace(self):
        attrs = """
            fill="rgba(0,100,0,0.2)" 
            style="stroke-width:0.001;stroke:#000;stroke-opacity:0.5" 
        """
        return self.add_bb_layer("greenspaces", attrs)

    def get_railway(self):
        attrs = """
            fill="rgba(0,100,0,0.2)" 
            style="stroke-width:9;stroke:#000;stroke-opacity:0.5" 
        """
        return self.add_bb_layer("railway_track", attrs, covers_func="st_intersects")

    def get_railway_tunnel(self):
        attrs = """
            fill="none" 
            style="stroke-width:11;stroke:#000;stroke-opacity:0.3" 
        """
        return self.add_bb_layer("railway_tunnel", attrs, covers_func="st_intersects")

    def get_stations(self):
        attrs = """r="20" fill="rgba(255,0,0,0.6)" """
        layer = self.add_bb_layer("stations", attrs, tag_name="circle")
        return layer

    def get_roundabout(self):
        attrs = """r="10" fill="rgba(0,0,0,0.8)" """
        layer = self.add_bb_layer("roundabout", attrs, tag_name="circle")
        return layer

    def add_bb_layer(
        self, layer_name, attrs, tag_name="path", covers_func="st_coveredby"
    ):
        """
        Adds a layer that will cover the entire bounding box

        """

        sql = f"""
                SELECT
                    st_assvg(
                      ST_Transform(geom, 27700)
                    ) AS gg
                FROM og_images_layer_{layer_name}
                WHERE {covers_func}(
                    geom::geometry,
                    %s::geometry
                )
                """
        self.cursor.execute(
            sql,
            [
                self.bounding_box,
            ],
        )

        svg_list = []
        for row in self.cursor.fetchall():
            if tag_name == "path":
                data = f"""d="{row[0]}" """
            else:
                data = f"""{row[0]}"""

            svg_list.append(f"""<{tag_name} {data} {attrs} />""")
        return svg_list
