import math


PI = math.pi
AXIS = 6378245.0
EE = 0.00669342162296594323


def _transform_lat(x: float, y: float) -> float:
    ret = (
        -100.0
        + 2.0 * x
        + 3.0 * y
        + 0.2 * y * y
        + 0.1 * x * y
        + 0.2 * math.sqrt(abs(x))
    )

    ret += (
        20.0 * math.sin(6.0 * x * PI)
        + 20.0 * math.sin(2.0 * x * PI)
    ) * 2.0 / 3.0

    ret += (
        20.0 * math.sin(y * PI)
        + 40.0 * math.sin(y / 3.0 * PI)
    ) * 2.0 / 3.0

    ret += (
        160.0 * math.sin(y / 12.0 * PI)
        + 320.0 * math.sin(y * PI / 30.0)
    ) * 2.0 / 3.0

    return ret


def _transform_lon(x: float, y: float) -> float:
    ret = (
        300.0
        + x
        + 2.0 * y
        + 0.1 * x * x
        + 0.1 * x * y
        + 0.1 * math.sqrt(abs(x))
    )

    ret += (
        20.0 * math.sin(6.0 * x * PI)
        + 20.0 * math.sin(2.0 * x * PI)
    ) * 2.0 / 3.0

    ret += (
        20.0 * math.sin(x * PI)
        + 40.0 * math.sin(x / 3.0 * PI)
    ) * 2.0 / 3.0

    ret += (
        150.0 * math.sin(x / 12.0 * PI)
        + 300.0 * math.sin(x / 30.0 * PI)
    ) * 2.0 / 3.0

    return ret


def _out_of_china(
    longitude: float,
    latitude: float,
) -> bool:

    return not (
        72.004 <= longitude <= 137.8347
        and
        0.8293 <= latitude <= 55.8271
    )


def gcj02_to_wgs84(
    longitude: float,
    latitude: float,
) -> tuple[float, float]:

    if _out_of_china(
        longitude,
        latitude,
    ):
        return longitude, latitude

    d_lat = _transform_lat(
        longitude - 105.0,
        latitude - 35.0,
    )

    d_lon = _transform_lon(
        longitude - 105.0,
        latitude - 35.0,
    )

    rad_lat = latitude / 180.0 * PI

    magic = math.sin(rad_lat)

    magic = 1 - EE * magic * magic

    sqrt_magic = math.sqrt(magic)

    d_lat = (
        d_lat * 180.0
        / (
            AXIS
            * (1 - EE)
            / (magic * sqrt_magic)
            * PI
        )
    )

    d_lon = (
        d_lon
        * 180.0
        / (
            AXIS
            / sqrt_magic
            * math.cos(rad_lat)
            * PI
        )
    )

    mg_lat = latitude + d_lat
    mg_lon = longitude + d_lon

    return (
        longitude * 2 - mg_lon,
        latitude * 2 - mg_lat,
    )