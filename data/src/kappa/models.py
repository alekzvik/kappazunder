from pathlib import Path
from pydantic import BaseModel


class RawImageMeta(BaseModel):
    trajectory_id: int
    sensor_id: int
    id: int
    gps_epoch_s: float
    name: str
    x_m: float
    y_m: float
    z_m: float
    rx_rad: float
    ry_rad: float
    rz_rad: float
    path: Path


class TrajectoryMeta(BaseModel):
    id: int
    epsg: int
    gps_week: int