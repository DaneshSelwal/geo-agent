import ee


def geojson_to_ee_geometry(
    geojson: dict,
) -> ee.Geometry:
    """
    Convert a GeoJSON geometry object into an
    Earth Engine Geometry.
    """

    return ee.Geometry(geojson)
