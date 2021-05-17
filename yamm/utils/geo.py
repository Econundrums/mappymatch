from typing import Tuple

import geopandas as gpd
import numpy as np
from pyproj import Transformer
from rtree import index
from shapely.ops import cascaded_union, transform

from yamm.constructs.coordinate import Coordinate
from yamm.constructs.geofence import Geofence
from yamm.constructs.road import Road
from yamm.constructs.trace import Trace
from yamm.maps.map_interface import MapInterface
from yamm.utils.crs import XY_CRS, LATLON_CRS


def build_rtree(road_map: MapInterface):
    """
    builds an rtree index from a map connection.
    """
    items = []

    for i, road in enumerate(road_map.roads):
        rid = road.road_id
        segment = list(road.geom.coords)
        box = road.geom.bounds
        items.append((i, box, (rid, segment)))
    return index.Index(items)


def xy_to_latlon(x: float, y: float) -> Tuple[float, float]:
    transformer = Transformer.from_crs(XY_CRS, LATLON_CRS)
    lat, lon = transformer.transform(x, y)

    return lat, lon


def latlon_to_xy(lat: float, lon: float) -> Tuple[float, float]:
    transformer = Transformer.from_crs(LATLON_CRS, XY_CRS)
    x, y = transformer.transform(lat, lon)

    return x, y


def geofence_from_trace(trace: Trace, padding: float = 0, xy: bool = False, buffer_res: int = 16) -> Geofence:
    """
    computes a bounding box surrounding a trace by taking the minimum and maximum x and y

    :param trace: the trace to compute the bounding box for
    :param padding: how much padding (in meters) to add to the box
    :param xy: should the geofence be projected to xy?
    :param buffer_res: should the geofence be projected to xy?

    :return: the computed bounding box
    """

    if trace.crs != XY_CRS:
        trace = trace.to_crs(XY_CRS)

    coords_df = gpd.GeoSeries([c.geom for c in trace.coords])

    polygon = cascaded_union(coords_df.buffer(padding, buffer_res))

    if xy:
        return Geofence(crs=XY_CRS, geometry=polygon)

    project = Transformer.from_crs(XY_CRS, LATLON_CRS, always_xy=True).transform
    polygon = transform(project, polygon)

    return Geofence(crs=LATLON_CRS, geometry=polygon)


def road_to_coord_dist(road: Road, coord: Coordinate) -> float:
    """
    helper function to compute the distance between a coordinate and a road

    :param road: the road object
    :param coord: the coordinate object

    :return: the distance
    """

    dist = coord.geom.distance(road.geom)

    return dist


def coord_to_coord_dist(a: Coordinate, b: Coordinate):
    """
    helper function to compute the distance between to coordinates

    :param a: coordinate a
    :param b: coordinate b

    :return: the distance
    """
    dist = a.geom.distance(b.geom)

    return dist
