from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# جدول ربط بين السيارات والسائقين (سيارة واحدة قد يقودها أكثر من سائق)
vehicle_drivers = Table(
    "vehicle_drivers",
    Base.metadata,
    Column("vehicle_plate", String, ForeignKey("vehicles.plate_number"), primary_key=True),
    Column("driver_id", Integer, ForeignKey("drivers.id"), primary_key=True),
)


class Vehicle(Base):
    __tablename__ = "vehicles"

    plate_number = Column(String, primary_key=True, index=True)
    car_type = Column(String, nullable=True)
    color = Column(String, nullable=True)

    drivers = relationship("Driver", secondary=vehicle_drivers, back_populates="vehicles")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    vehicles = relationship("Vehicle", secondary=vehicle_drivers, back_populates="drivers")


class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class TripRecord(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, nullable=False)
    driver_name = Column(String, nullable=False)
    well_name = Column(String, nullable=False)
    quantity_bbl = Column(Float, nullable=False)


class ExternalTripRecord(Base):
    __tablename__ = "external_trips"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, nullable=False)
    driver_name = Column(String, nullable=False)
    task_number = Column(String, nullable=True)
    loading_location = Column(String, nullable=True)
    weight_before = Column(Float, nullable=False)
    weight_after = Column(Float, nullable=False)
    net_weight = Column(Float, nullable=False)
    quantity_bbl = Column(Float, nullable=True)
