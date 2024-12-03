import typer
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from tqdm import tqdm
import json
import numpy as np
from typing import Dict, List, Tuple, NamedTuple
import pystac
from shapely.geometry import box, mapping
import pandas as pd
import re

app = typer.Typer()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stac-builder')

class TrajectoryInfo(NamedTuple):
    """Store trajectory folder information."""
    gps_week: int
    epsg: int

class STACBuilder:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.image_meta_path = data_dir / "Bild-Meta" / "image_meta.txt"
        self.trajectories_path = data_dir / "Verortung" / "Trajektorien"
        # self.interior_orientation_path = data_dir / "Bild-Meta" / "interior_orientation.txt"
        self.raw_images_dir = data_dir / "Bild-Rohdaten"
        self.stac_dir = data_dir / "stac-catalog"
        
        # GPS epoch start time
        self.gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
        
        # # Cache for trajectory information
        # self.trajectory_info_cache: Dict[int, TrajectoryInfo] = {}
        
        # # Mapping of sensor positions in cubemap
        # self.sensor_positions = {
        #     110030: "front",
        #     110031: "right",
        #     110032: "back",
        #     110033: "left",
        #     110034: "up",
        #     110035: "down"
        # }

    
    @lru_cache
    def get_trajectory_info(self, traj_id: int) -> TrajectoryInfo:
        """Extract GPS week and EPSG code from trajectory folder name."""
        # Check cache first
        if traj_id in self.trajectory_info_cache:
            return self.trajectory_info_cache[traj_id]
            
        # Look for trajectory folder pattern in raw images directory
        traj_folders = list(self.raw_images_dir.glob(f"Trajektorie_{traj_id}*"))
        if not traj_folders:
            raise ValueError(f"Could not find trajectory folder for ID {traj_id}")
        
        # Extract GPS week and EPSG from folder name using regex
        folder_name = traj_folders[0].name
        match = re.search(r'trajectory_\d+_(\d+)_(\d+)', folder_name)
        if not match:
            raise ValueError(f"Could not extract GPS week and EPSG from folder name: {folder_name}")
        
        info = TrajectoryInfo(
            gps_week=int(match.group(1)),
            epsg=int(match.group(2))
        )
        
        # Cache the result
        self.trajectory_info_cache[traj_id] = info
        return info
    
    def gps_to_datetime(self, gps_week: int, seconds_of_week: float) -> datetime:
        """Convert GPS week and seconds to UTC datetime."""
        # Calculate total seconds since GPS epoch
        total_seconds = gps_week * 7 * 24 * 3600 + seconds_of_week
        
        # Add to GPS epoch to get UTC datetime
        return self.gps_epoch + timedelta(seconds=total_seconds)

    def read_image_metadata(self) -> Dict:
        """Read and parse image metadata file."""
        logger.info("Reading image metadata...")
        metadata = {}
        
        try:
            df = pd.read_csv(
                self.image_meta_path, 
                sep='\s+',
                names=['traj_id', 'sensor_id', 'image_id', 'gps_time', 'image_name', 
                      'x', 'y', 'z', 'rx', 'ry', 'rz'],
                comment='#'
            )
            
            # Group by trajectory and base image name
            for (traj_id, base_name), group in df.groupby([
                'traj_id', 
                df['image_name'].str.split('.').str[0]
            ]):
                key = (traj_id, base_name)
                first_row = group.iloc[0]
                
                # Get trajectory info (GPS week and EPSG)
                traj_info = self.get_trajectory_info(traj_id)
                
                # Convert GPS time to UTC datetime
                timestamp = self.gps_to_datetime(traj_info.gps_week, first_row['gps_time'])
                
                metadata[key] = {
                    'trajectory_id': traj_id,
                    'timestamp': timestamp.timestamp(),  # Store as Unix timestamp
                    'position': (first_row['x'], first_row['y'], first_row['z']),
                    'rotation': (first_row['rx'], first_row['ry'], first_row['rz']),
                    'sensors': dict(zip(group['sensor_id'], group['image_name'])),
                    'epsg': traj_info.epsg
                }
                
        except Exception as e:
            logger.error(f"Error reading metadata file: {str(e)}")
            raise
            
        return metadata

    def create_stac_catalog(self, metadata: Dict) -> pystac.Catalog:
        """Create root STAC catalog."""
        logger.info("Creating STAC catalog...")
        
        catalog = pystac.Catalog(
            id="vienna-mobile-mapping",
            description="Vienna Mobile Mapping Cubemap Images",
            title="Vienna Mobile Mapping"
        )
        
        return catalog

    def create_stac_collection(self, metadata: Dict) -> pystac.Collection:
        """Create STAC collection with extent information."""
        logger.info("Creating STAC collection...")
        
        # Calculate spatial and temporal extent
        positions = [m['position'] for m in metadata.values()]
        timestamps = [m['timestamp'] for m in metadata.values()]
        
        min_x = min(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        max_x = max(p[0] for p in positions)
        max_y = max(p[1] for p in positions)
        
        # Create bbox and temporal extent
        bbox = [min_x, min_y, max_x, max_y]
        spatial_extent = pystac.SpatialExtent([bbox])
        
        min_time = datetime.fromtimestamp(min(timestamps), tz=timezone.utc)
        max_time = datetime.fromtimestamp(max(timestamps), tz=timezone.utc)
        temporal_extent = pystac.TemporalExtent([[min_time, max_time]])
        
        # Create collection extent
        extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        
        # Get unique EPSG codes
        epsg_codes = {m['epsg'] for m in metadata.values()}
        
        # Create collection
        collection = pystac.Collection(
            id="vienna-cubemap-images",
            description="Cubemap images from Vienna mobile mapping campaign",
            extent=extent,
            title="Vienna Cubemap Images",
            license="TBD"
        )
        
        # Add CRS information to collection properties
        collection.extra_fields["proj:epsg"] = list(epsg_codes)
        
        return collection

    def create_stac_item(self, key: Tuple[int, str], item_data: Dict) -> pystac.Item:
        """Create STAC item for a single cubemap location."""
        traj_id, base_name = key
        x, y, z = item_data['position']
        timestamp = datetime.fromtimestamp(item_data['timestamp'], tz=timezone.utc)
        
        # Create geometry
        geometry = {
            "type": "Point",
            "coordinates": [x, y]  # We use x,y only for the point
        }
        
        # Create properties
        properties = {
            "trajectory_id": item_data['trajectory_id'],
            "height": z,
            "rotation_x": item_data['rotation'][0],
            "rotation_y": item_data['rotation'][1],
            "rotation_z": item_data['rotation'][2],
            "proj:epsg": item_data['epsg']
        }
        
        # Create item
        item = pystac.Item(
            id=f"cubemap_{base_name}",
            geometry=geometry,
            bbox=[x, y, x, y],  # Point bbox
            datetime=timestamp,
            properties=properties
        )
        
        # Add assets for each sensor/direction
        for sensor_id, image_name in item_data['sensors'].items():
            direction = self.sensor_positions[sensor_id]
            asset_path = f"../../Bild-Rohdaten/Trajektorie_{traj_id}/Sensor_{sensor_id}/{image_name}"
            
            item.add_asset(
                direction,
                pystac.Asset(
                    href=asset_path,
                    media_type=pystac.MediaType.JPEG,
                    roles=["data"],
                    title=f"Cubemap {direction} face"
                )
            )
            
        return item

    def validate_stac(self, catalog: pystac.Catalog):
        """Validate the STAC catalog."""
        logger.info("Validating STAC catalog...")
        try:
            catalog.validate_all()
            logger.info("STAC validation successful!")
        except Exception as e:
            logger.error(f"STAC validation failed: {str(e)}")
            raise

    def build_catalog(self):
        """Build complete STAC catalog."""
        logger.info("Starting STAC catalog build...")
        
        # Create output directory
        self.stac_dir.mkdir(exist_ok=True)
        
        try:
            # Read metadata
            metadata = self.read_image_metadata()
            
            # Create catalog and collection
            catalog = self.create_stac_catalog(metadata)
            collection = self.create_stac_collection(metadata)
            catalog.add_child(collection)
            
            # Create items
            logger.info("Creating STAC items...")
            for key, item_data in tqdm(metadata.items(), desc="Creating STAC items"):
                item = self.create_stac_item(key, item_data)
                collection.add_item(item)
            
            # Validate catalog
            self.validate_stac(catalog)
            
            # Save catalog
            catalog.normalize_and_save(
                str(self.stac_dir),
                catalog_type=pystac.CatalogType.SELF_CONTAINED
            )
            
            logger.info("STAC catalog build completed!")
            
        except Exception as e:
            logger.error(f"Error building STAC catalog: {str(e)}")
            raise

@app.command()
def build_catalog(
    data_dir: Path = typer.Argument(..., help="Path to the data directory containing Bild-Meta and other folders"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Build STAC catalog for Vienna mobile mapping cubemap images."""
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    builder = STACBuilder(data_dir)
    builder.build_catalog()

if __name__ == "__main__":
    app()
