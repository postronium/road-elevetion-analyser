import psycopg2
import pyproj
from shapely import wkt
from shapely.geometry import LineString, Point
import matplotlib.pyplot as plt
from shapely import wkt
from shapely.geometry import LineString
from elevation_map import ElevationMap
import numpy as np
import math
import os
from dotenv import load_dotenv

# Define the source (current) and target coordinate systems
source_crs = pyproj.CRS("EPSG:3857")  # Web Mercator
target_crs = pyproj.CRS("EPSG:4326")  # WGS84

transformer = pyproj.Transformer.from_crs(source_crs, target_crs)

class RoadProperty:

    def __init__(self, osm_id: int):
        self.osm_id = osm_id
        self.total_curviness = 0
        self.c_a = 0
        self.c_b = 0
        self.c_c = 0
        self.c_d = 0
        self.c_e = 0
        self.c_f = 0
        self.length = -1
        self.total_elevation = -1

class Road:

    def __init__(self, osm_id: int):
        self.osm_id = osm_id
        self.highway: str = ''
        self.oneway: str = ''
        self.bridge: str = ''
        self.bicycle: str = ''
        self.motorcar: str = ''
        self.public_transport: str = ''
        self.surface: str = ''
        self.tunnel: str = ''
        self.name: str = ''
        self.geometry = None
        self.geometry_wkt = None
    
    def get_wkt_geometry(self):
        if self.geometry_wkt is None:
            self.geometry_wkt = wkt.loads(self.geometry)
        return self.geometry_wkt
    
    def get_length(self) -> float:
        return self.get_wkt_geometry().length
    
    def get_coords(self) -> list:
        return self.get_wkt_geometry().coords

    def get_start_coord(self) -> tuple:
        return self.get_wkt_geometry().coords[0]

    def get_end_coord(self) -> tuple:
        return self.get_wkt_geometry().coords[-1]

    def get_bbox(self):
        coords = self.get_coords()
        if self.min_lat is None:
            self.min_lat = min(coord[0] for coord in coords)
            self.max_lat = max(coord[0] for coord in coords)
            self.min_lon = min(coord[1] for coord in coords)
            self.max_lon = max(coord[1] for coord in coords)

        return (self.min_lat, self.max_lat, self.min_lon, self.max_lon)


class RoadDAO:
    def __init__(self, db_name: str, user: str, password: str, host: str = "localhost"):
        self.db_connection = psycopg2.connect(database=db_name, user=user, password=password, host=host)

    def get_all_skatable_roads(self):
        cur = self.db_connection.cursor()

        cur.execute("""
            SELECT 
                osm_id, 
                highway, 
                oneway, 
                bridge, 
                bicycle, 
                motorcar, 
                public_transport, 
                surface, 
                tunnel, 
                name, 
                ST_AsText(way) as geometry
            FROM 
                skatable_roads;
        """)
        
        roads = cur.fetchall()

        cur.close()

        return [RoadDAO.road_from_database(road) for road in roads]
    
    def insert_road_properties(self, properties: list):
        cursor = self.db_connection.cursor()

        insert_query = """
            INSERT INTO properties (osm_id, total_curviness, c_a, c_b, c_c, c_d, c_e, c_f, length, total_elevation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        for property in properties:
            cursor.execute(insert_query, (
                property.osm_id, 
                property.total_curviness, 
                property.c_a, 
                property.c_b, 
                property.c_c, 
                property.c_d, 
                property.c_e, 
                property.c_f, 
                property.length, 
                property.total_elevation))
        self.db_connection.commit()

        cursor.close()

    
    def insert_road_property(self, property: RoadProperty):
        cursor = self.db_connection.cursor()

        insert_query = """
            INSERT INTO properties (osm_id, total_curviness, c_a, c_b, c_c, c_d, c_e, c_f, length)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

        cursor.execute(insert_query, (
            property.osm_id, 
            property.total_curviness, 
            property.c_a, 
            property.c_b, 
            property.c_c, 
            property.c_d, 
            property.c_e, 
            property.c_f, 
            property.length))
        self.db_connection.commit()

        cursor.close()

    def close_connection(self):
        self.db_connection.cancel()

    @staticmethod
    def road_from_database(db_entry: tuple):
        road = Road(db_entry[0])
        road.highway = db_entry[1]
        road.oneway = db_entry[2]
        road.bridge = db_entry[3]
        road.bicycle = db_entry[4]
        road.motorcar = db_entry[5]
        road.public_transport = db_entry[6]
        road.surface = db_entry[7]
        road.tunnel = db_entry[8]
        road.name = db_entry[9]
        road.geometry = db_entry[10]
        return road

        

class RoadPropertyCalculator:

    def __init__(self):
        self.segment_size = 100
        self.elevation_map = ElevationMap(('.\\1-arc-sec-de-nrw\\'))
        
    def coords_as_lat_lon(self, coords):
        lon, lat = transformer.transform(coords[0], coords[1])
        return (lat, lon)

    def get_road_property(self, road: Road) -> RoadProperty:
        curviness = RoadPropertyCalculator.calc_curviness(road)
        segment_curviness = self.calc_segment_curviness(road)
        curves_classes = RoadPropertyCalculator.curvy_metrics(segment_curviness)
        total_elevation = self.calculate_total_elevation(road)

        properties = RoadProperty(road.osm_id)

        properties.total_curviness = curviness
        properties.c_a = curves_classes[0]
        properties.c_b = curves_classes[1]
        properties.c_c = curves_classes[2]
        properties.c_d = curves_classes[3]
        properties.c_e = curves_classes[4]
        properties.c_f = curves_classes[5]
        properties.length = road.get_length()
        properties.total_elevation = total_elevation

        return properties
    
    def calculate_total_elevation(self, road: Road) -> float:
        start_point = self.coords_as_lat_lon(road.get_start_coord())
        end_point = self.coords_as_lat_lon(road.get_end_coord())
        start_elevation = self.elevation_map.get_elevation(start_point[1], start_point[0])
        end_elevation = self.elevation_map.get_elevation(end_point[1], end_point[0])
        delta_elevation = end_elevation - start_elevation
        return delta_elevation

    @staticmethod
    def calc_curviness(road: Road) -> tuple:
        straight_line = LineString([road.get_start_coord(), road.get_end_coord()])
        straight_length = straight_line.length
        
        if straight_length == 0:
            return 0.0
        curviness = road.get_length() / straight_length - 1
        
        return curviness

    def calc_segment_curviness(self, road: Road) -> list:
        curviness_values = []

        i = 0
        while i + self.segment_size <= road.get_length():
            road_geometry = road.get_wkt_geometry()

            start_point = road_geometry.interpolate(i)
            end_point = road_geometry.interpolate(i + self.segment_size)

            coords = []
            for coord in road.get_coords():
                if i <= road_geometry.project(Point(coord)) <= i + self.segment_size:
                    coords.append(coord)
            coords = [start_point.coords[0]] + coords + [end_point.coords[0]]
            subroad = LineString(coords)
            
            actual_length = subroad.length
            straight_length = LineString([start_point, end_point]).length
            curviness = actual_length / straight_length - 1
            
            curviness_values.append(curviness)
            
            i += self.segment_size
        
        return curviness_values
    
    @staticmethod
    def curvy_metrics(curviness):
        curv_counter = [0, 0, 0, 0, 0, 0]
        for c in curviness:
            if c < 0.1:
                curv_counter[0] += 1
            elif c < 0.2:
                curv_counter[1] += 1
            elif c < 0.3:
                curv_counter[2] += 1
            elif c < 0.5:
                curv_counter[3] += 1
            elif c < 0.75:
                curv_counter[4] += 1
            else:
                curv_counter[5] += 1

        return curv_counter


if __name__ == "__main__":
    load_dotenv()

    road_dao = RoadDAO(os.getenv('DB_NAME'), os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_HOST'))

    roads = road_dao.get_all_skatable_roads()

    calculator = RoadPropertyCalculator()

    road_properties = [calculator.get_road_property(road) for road in roads]

    road_dao.insert_road_properties(road_properties)

    road_dao.close_connection()