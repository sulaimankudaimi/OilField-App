from typing import List, Optional
from pydantic import BaseModel


class TripCreate(BaseModel):
    plate_number: str
    driver_name: str
    well_name: str
    quantity_bbl: float


class ExternalTripCreate(BaseModel):
    plate_number: str
    driver_name: str
    task_number: Optional[str] = None
    loading_location: Optional[str] = None
    weight_before: float
    weight_after: float
    net_weight: float
    quantity_bbl: Optional[float] = None


class VehicleInfoResponse(BaseModel):
    found: bool
    plate_number: Optional[str] = None
    car_type: Optional[str] = None
    color: Optional[str] = None
    drivers: List[str] = []
    suggestion: Optional[str] = None


class VehicleUpsert(BaseModel):
    plate_number: str
    car_type: Optional[str] = None
    color: Optional[str] = None


class DriverCreate(BaseModel):
    name: str
    plate_number: Optional[str] = None  # إن أُرسل، يُربط السائق بهذه السيارة مباشرة


class WellCreate(BaseModel):
    name: str
