from pathlib import Path

from kappa.paths import OUTPUT_PATH, KappazunderPath
import typer
from py3dtiles.convert import convert


extract_cli = typer.Typer(
    help="Process data extract from https://www.wien.gv.at/geodatenviewer"
)


@extract_cli.command(name="merge-images")
def merge_image_metadata_into_wfs(wfs_geojson: Path, extract_path: list[Path]):
    """Merge images from data extract into WFS dump."""
    pass


@extract_cli.command(name="merge-lidar")
def merge_lidar_metadata_into_wfs(wfs_geojson: Path, extract_path: list[Path]):
    """Merge lidar from data extract into WFS dump."""
    pass


@extract_cli.command(name="prepare-lidar")
def prepare_lidar_files(data_dir: Path):
    """Rearrange and convert to COPC lidar files."""
    kappa_path = KappazunderPath(data_dir)
    convert(files=kappa_path.get_all_scans(), outfolder=OUTPUT_PATH / '3dtiles', overwrite=True)

@extract_cli.command(name="prepare-images")
def prepare_image_files(data_dir: Path):
    """Rearrange image files for easier consumption."""
    pass


@extract_cli.command(name="upload-images")
def upload_image_files(prepared_dir: Path):
    """Upload prepared image files to S3/R2."""
    pass


@extract_cli.command(name="upload-lidar")
def upload_lidar_files(prepared_dir: Path):
    """Upload prepared lidar files to S3/R2."""
    pass
