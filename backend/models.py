from sqlalchemy import Column, Integer, String, Float
from database import Base


class TripRecord(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, nullable=False)
    driver_name = Column(String, nullable=False)
    well_name = Column(String, nullable=False)
    quantity_bbl = Column(Float, nullable=False)
