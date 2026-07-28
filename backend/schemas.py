from pydantic import BaseModel


class TripCreate(BaseModel):
    plate_number: str
    driver_name: str
    well_name: str
    quantity_bbl: float
