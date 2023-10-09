import rasterio
import numpy as np
from scipy.interpolate import RectBivariateSpline
import math
import os
from rasterio.plot import show

class ElevationMap:
    class ElevationMapTile:
        def __init__(self, lat: int, lon: int, filename: str):
            self.filename = filename
            self.lat = lat
            self.lon = lon
            self.load_tile()
        
        def load_tile(self):
            img = rasterio.open(self.filename)
            elevation_data = img.read(1)
            transform = img.transform

            print(self.filename)
            #show(elevation_data, cmap='terrain', origin='lower')

            self.shape = elevation_data.shape
            self.spline_interpolator = RectBivariateSpline(np.arange(elevation_data.shape[0]), np.arange(elevation_data.shape[1]), elevation_data)

            # Calculate the bounds manually
            self.bounds = {}
            self.bounds['left'] = transform.c
            self.bounds['top'] = transform.f
            self.bounds['right'] = self.bounds['left'] + elevation_data.shape[1] * transform.a
            self.bounds['bottom'] = self.bounds['top'] + elevation_data.shape[0] * transform.e

        def get_elevations(self, coords: np.array) -> float:
            lats_on_tile = coords[:,0] - self.lat
            lons_on_tile = coords[:,1] - self.lon

            coord_on_tile_y = [self.shape[1] - (self.shape[1] * lats_on_tile)]
            coord_on_tile_x = [self.shape[0] * lons_on_tile]

            elevation_interpolated = self.spline_interpolator(coord_on_tile_x, coord_on_tile_y)

            return elevation_interpolated


        def get_elevation(self, lat: float, lon: float):
            lat_on_tile = lat - self.lat
            lon_on_tile = lon - self.lon

            coord_on_tile_y = [self.shape[1] - (self.shape[1] * lat_on_tile)]
            coord_on_tile_x = [self.shape[0] * lon_on_tile]

            elevation_interpolated = self.spline_interpolator(coord_on_tile_y, coord_on_tile_x)

            return elevation_interpolated[0][0]

    def __init__(self, path: str):
        self.path = path
        self.lat_from = 49
        self.lat_to = 51
        self.lon_from = 5
        self.lon_to = 8
        self.load_tiles()
        pass

    def is_on_map(self, lat: float, lon: float):
        if lat < self.lat_from or lat > self.lat_to + 1:
            return False
        elif lon < self.lon_from or lon > self.lon_to + 1:
            return False
        return True

    def get_elevation(self, lat: float, lon: float) -> float:
        if self.is_on_map(lat, lon):
            return self.tiles[math.floor(lat)][math.floor(lon)].get_elevation(lat, lon)
        return 0
    
    def get_elevations(self, coords: np.array, tile_lat: int, tile_lon: int) -> list:
        if self.is_on_map(tile_lat, tile_lon):
            raise Exception("Tile %i, %i is not loaded" % (tile_lat, tile_lon))
        return self.tiles[math.floor(tile_lat)][math.floor(tile_lon)].get_elevations(coords)
    
    def get_elevation_file(self, lat: float, lon: float):
        return os.path.join(self.path, 'lat-%i-lon-%i.tif' % (lat, lon))

    def load_tiles(self):
        self.tiles = {}
        for lat in range(self.lat_from, self.lat_to + 1):
            if lat not in self.tiles:
                self.tiles[lat] = {}
            for lon in range(self.lon_from, self.lon_to + 1):
                filename = self.get_elevation_file(lat, lon)
                self.tiles[lat][lon] = ElevationMap.ElevationMapTile(lat, lon, filename)
