import math
from typing import Literal

import geopandas as gpd
import orjson as json
import pandas as pd
import typer
from owslib.wfs import WebFeatureService
from requests import Request
from tqdm import tqdm

from kappa.paths import OUTPUT_PATH
from enum import Enum

WFS_URL = "https://data.wien.gv.at/daten/geo?version=1.1.0&service=WFS"
IMAGE_META_LAYER = "ogdwien:KAPPAZUNDERIMAGEPOGD"

wfs_cli = typer.Typer(help=f"Extract data from WFS server - {WFS_URL}")


class FileFormat(str, Enum):
    geojson = "geojson"
    geoparquet = "geoparquet"


def get_all_features(
    wfs_url: str, layer_name: str, batch_size: int = 50000
) -> gpd.GeoDataFrame:
    wfs = WebFeatureService(url=wfs_url, version="1.1.0", timeout=60)
    resp = wfs.getfeature(layer_name, outputFormat="json", maxfeatures=1)
    data = json.loads(resp.read())
    total = data["totalFeatures"]

    result = gpd.GeoDataFrame()

    for offset in tqdm(
        range(0, total, batch_size),
        desc="Fetching data...",
        total=math.ceil(total / batch_size),
        unit="batch",
    ):
        params = dict(
            service="WFS",
            version="1.1.0",
            request="GetFeature",
            typeName=layer_name,
            outputFormat="json",
            maxFeatures=batch_size,
            startIndex=offset,
            sortby="OBJECTID",
        )
        wfs_request_url = Request("GET", wfs_url, params=params).prepare().url

        gdf = gpd.read_file(wfs_request_url).set_crs("epsg:31256")
        result = pd.concat([result, gdf])
    return result


@wfs_cli.command()
def dump_images(format: FileFormat = FileFormat.geojson):
    """Generate dump of image metadata from WFS server."""

    images_gdf = get_all_features(WFS_URL, IMAGE_META_LAYER).to_crs(4326)
    match format:
        case FileFormat.geojson:
            output_file = OUTPUT_PATH / "json" / "images.geojson"
            output_file.unlink()
            images_gdf.to_file(output_file, driver="geojson")
        case FileFormat.geoparquet:
            images_gdf.to_parquet(OUTPUT_PATH / "parquet" / "images.geoparquet")
