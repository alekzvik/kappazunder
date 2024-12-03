import csv
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd
import pyproj
import pystac
import typer
from astropy.time import Time
from tqdm import tqdm

from kappa.models import RawImageMeta, TrajectoryMeta
from kappa.paths import KappazunderPath

stac_cli = typer.Typer(help="Prepare STAC catalog [WIP].")


def get_direction_label(
    sensor_id: int,
) -> Literal["up", "front", "right", "back", "left", "down"]:
    # Can also calculate it, given the trajectory and sensor angles
    last_digit = sensor_id % 10
    MAPPING = {
        0: "up",
        1: "front",
        2: "right",
        3: "back",
        4: "left",
        5: "down",
    }
    return MAPPING[last_digit]


def extract_trajectory_metadata(
    kappa_path: KappazunderPath,
) -> dict[int, TrajectoryMeta]:
    meta_map = {}
    for trajectory_path in kappa_path.trajectories_dir.iterdir():
        match = re.search(
            r"trajectory_(?P<id>\d+)_(?P<gps_week>\d+)_(?P<epsg>\d+)",
            trajectory_path.name,
        )
        metadata = TrajectoryMeta(**match.groupdict())

        meta_map[metadata.id] = metadata

    return meta_map


def extract_image_metadata(kappa_path: KappazunderPath) -> dict[int, RawImageMeta]:
    grouped_images = defaultdict(list)
    image_meta_file = kappa_path.image_metadata
    with image_meta_file.open("r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in tqdm(reader, desc="Reading image metadata..."):
            raw_image = RawImageMeta(
                **row,
                id=row["image_id"],
                name=row["image_name"],
                gps_epoch_s=row["epoch_s"],
                path=kappa_path.get_raw_image(
                    row["trajectory_id"],
                    row["sensor_id"],
                    row["image_name"],
                ),
            )
            grouped_images[raw_image.id].append(raw_image)
    return grouped_images


def skip_keys(d: dict, keys: list) -> dict:
    return {
        k: v
        for k, v in d.items()
        if k not in keys
    }

def flatten_image_group(group: list[RawImageMeta]) -> dict:
    image = group[0]
    return {
        **skip_keys(image.model_dump(), ["label", "path", "rx_rad", "ry_rad", "rz_rad", "name"]),
        "images": [
            {
                "label": get_direction_label(image.sensor_id),
                "href": str(image.path),
                "rx_rad": image.rx_rad,
                "ry_rad": image.ry_rad,
                "rz_rad": image.rz_rad,
            }
            for image in group
        ]
    }
    
    
def images_gdf(kappa_path: KappazunderPath):
    image_groups = extract_image_metadata(kappa_path)
    trajectories = extract_trajectory_metadata(kappa_path)
    trajectory = next(iter(trajectories.values()))
    df = pd.DataFrame.from_records(map(flatten_image_group, image_groups.values()))
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x_m, df.y_m, df.z_m), crs=f"epsg:{trajectory.epsg}").to_crs("epsg:4326")
    return gdf




def gps_time_to_datetime(gps_week: int, gps_seconds: float) -> datetime:
    SECONDS_IN_WEEK = 604800
    time = Time(SECONDS_IN_WEEK * gps_week + gps_seconds, format="gps")
    return time.datetime.replace(tzinfo=timezone.utc)


def create_stac_image_items(
    raw_image_groups: dict[int, list[RawImageMeta]],
    trajectories: dict[int, TrajectoryMeta],
) -> list[pystac.Item]:
    items = []
    for group in tqdm(raw_image_groups.values(), desc="Processing image groups..."):
        image = group[0]
        trajectory = trajectories[image.trajectory_id]
        proj = pyproj.Transformer.from_crs(trajectory.epsg, 4326, always_xy=True)
        x, y, z = proj.transform(image.x_m, image.y_m, image.z_m)
        item = pystac.Item(
            id=str(image.id),
            bbox=[x, y, x, y],
            geometry={
                "type": "Point",
                "coordinates": [x, y, z],
            },
            datetime=gps_time_to_datetime(trajectory.gps_week, image.gps_epoch_s),
            properties={
                "trajectory_id": image.trajectory_id,
                "gps_week": trajectory.gps_week,
                "gps_epoch_s": image.gps_epoch_s,
            },
        )
        # proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        # proj_ext.epsg = trajectory.epsg

        for image in group:
            direction = get_direction_label(image.sensor_id)
            item.add_asset(
                f"{direction} photo",
                pystac.Asset(
                    href=image.path,
                    title=f"{direction.capitalize()} photo",
                    media_type=pystac.MediaType.JPEG,
                    extra_fields={
                        "rx_rad": image.rx_rad,
                        "ry_rad": image.ry_rad,
                        "rz_rad": image.rz_rad,
                    },
                ),
            )
        item.properties["direction"] = item.assets.get("front photo").extra_fields
        item.validate()
        items.append(item)
    return items


@stac_cli.command(name='images')
def images(input_dir: Path, title: str = "Kappazunder data extract") -> None:
    """Create STAC collection from Kappzunder images."""
    print(f"Exists: {input_dir.exists()}")
    kappa_path = KappazunderPath(input_dir)
    trajectories = extract_trajectory_metadata(kappa_path)
    raw_image_groups = extract_image_metadata(kappa_path)

    items = create_stac_image_items(raw_image_groups, trajectories)
    
    spatial_extent = pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]])
    temporal_extent = pystac.TemporalExtent([[datetime(1970, 1, 1), None]])
    collection_extent = pystac.Extent(spatial_extent, temporal_extent)

    collection = pystac.Collection(
        id=title,
        title=title,
        extent=collection_extent,
        license="CC-BY-4.0",
        description="Kappazunder image panorama data. Source: https://www.data.gv.at/katalog/dataset/566c8d52-b6f8-48b9-921e-856ba5be392d#additional-info",
        providers=[
            pystac.Provider(
                name="Vienna City Surveying Department (MA 41)",
                roles=[pystac.ProviderRole.PRODUCER],
            ),
            pystac.Provider(
                name="Vienna Digital Department (MA 01)",
                roles=[pystac.ProviderRole.HOST],
            ),
        ],
    )
    

    collection.add_items(tqdm(items, desc="Constructing STAC collection..."))
    collection.update_extent_from_items()
    collection.normalize_hrefs('./output/stac/images')
    collection.validate_all()
    
    collection.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
