from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable

OUTPUT_PATH = Path("./output/")


@dataclass
class KappazunderPath:
    base_dir: Path

    @property
    def image_metadata(self) -> Path:
        return self.base_dir / "Bild-Meta" / "image_meta.txt"
    
    @property
    def scan_data_dir(self) -> Path:
        return self.base_dir / 'Scan-Punktwolken'

    @property
    def trajectories_dir(self) -> Path:
        return self.base_dir / "Verortung" / "Trajektorien"
        
    def get_all_scans(self) -> Generator[Path, None, None]:
        return self.scan_data_dir.glob('Trajektorie_*/Sensor_*/*.laz')

    def get_raw_image(
        self, trajectory_id: str, sensor_id: str, image_name: str
    ) -> Path:
        return (
            self.base_dir
            / "Bild-Rohdaten"
            / f"Trajektorie_{trajectory_id}"
            / f"Sensor_{sensor_id}"
            / image_name
        )
