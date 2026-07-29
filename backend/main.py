import difflib

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine, Base
from models import TripRecord, ExternalTripRecord, Vehicle, Driver, Well
from schemas import (
    TripCreate,
    ExternalTripCreate,
    VehicleInfoResponse,
    VehicleUpsert,
    DriverCreate,
    WellCreate,
)

# إنشاء الجداول تلقائياً عند إقلاع الخادم إن لم تكن موجودة
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OilField Field Reports API")

# مطلوب حتى يستطيع تطبيق الجوال (Flet) الاتصال بالخادم من نطاق مختلف
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
#  السيارات والسائقين — تكافئ منطق database.py في نسخة Streamlit
# =========================================================
@app.get("/api/vehicle/{plate_number}", response_model=VehicleInfoResponse)
def get_vehicle_info(plate_number: str, db: Session = Depends(get_db)):
    plate_number = plate_number.strip()
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()

    if vehicle:
        return VehicleInfoResponse(
            found=True,
            plate_number=vehicle.plate_number,
            car_type=vehicle.car_type,
            color=vehicle.color,
            drivers=[d.name for d in vehicle.drivers],
        )

    # لم تُوجد اللوحة تماماً — نبحث عن أقرب رقم مشابه لاقتراحه على المستخدم
    all_plates = [v.plate_number for v in db.query(Vehicle.plate_number).all()]
    close = difflib.get_close_matches(plate_number, all_plates, n=1, cutoff=0.6)
    suggestion = close[0] if close else None

    return VehicleInfoResponse(found=False, suggestion=suggestion)


@app.post("/api/vehicle")
def upsert_vehicle(payload: VehicleUpsert, db: Session = Depends(get_db)):
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.plate_number == payload.plate_number).first()
        if vehicle:
            if payload.car_type:
                vehicle.car_type = payload.car_type
            if payload.color:
                vehicle.color = payload.color
        else:
            vehicle = Vehicle(
                plate_number=payload.plate_number,
                car_type=payload.car_type,
                color=payload.color,
            )
            db.add(vehicle)
        db.commit()
        return {"message": "تم حفظ بيانات السيارة", "plate_number": vehicle.plate_number}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/driver")
def get_or_create_driver(payload: DriverCreate, db: Session = Depends(get_db)):
    try:
        driver = db.query(Driver).filter(Driver.name == payload.name).first()
        if not driver:
            driver = Driver(name=payload.name)
            db.add(driver)
            db.commit()
            db.refresh(driver)

        if payload.plate_number:
            vehicle = db.query(Vehicle).filter(Vehicle.plate_number == payload.plate_number).first()
            if not vehicle:
                raise HTTPException(status_code=404, detail="السيارة غير موجودة، سجّلها أولاً")
            if driver not in vehicle.drivers:
                vehicle.drivers.append(driver)
                db.commit()

        return {"message": "تم حفظ السائق", "driver_id": driver.id, "name": driver.name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
#  الآبار
# =========================================================
@app.get("/api/wells")
def get_all_wells(db: Session = Depends(get_db)):
    wells = db.query(Well).order_by(Well.name).all()
    return [w.name for w in wells]


@app.post("/api/wells")
def create_well(payload: WellCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Well).filter(Well.name == payload.name).first()
        if existing:
            return {"message": "البئر موجود مسبقاً", "well_id": existing.id}
        well = Well(name=payload.name)
        db.add(well)
        db.commit()
        db.refresh(well)
        return {"message": "تم إضافة البئر", "well_id": well.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
#  الرحلات الداخلية
# =========================================================
@app.post("/api/internal_trip")
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    try:
        new_trip = TripRecord(
            plate_number=trip.plate_number,
            driver_name=trip.driver_name,
            well_name=trip.well_name,
            quantity_bbl=trip.quantity_bbl,
        )
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        return {"message": "تم حفظ السجل بنجاح", "trip_id": new_trip.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
#  الرحلات الخارجية
# =========================================================
@app.post("/api/external_trip")
def create_external_trip(trip: ExternalTripCreate, db: Session = Depends(get_db)):
    try:
        new_trip = ExternalTripRecord(
            plate_number=trip.plate_number,
            driver_name=trip.driver_name,
            task_number=trip.task_number,
            loading_location=trip.loading_location,
            weight_before=trip.weight_before,
            weight_after=trip.weight_after,
            net_weight=trip.net_weight,
            quantity_bbl=trip.quantity_bbl,
        )
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        return {"message": "تم حفظ السجل بنجاح", "trip_id": new_trip.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
#  مؤشرات الأداء
# =========================================================
@app.get("/api/kpi")
def get_kpis(db: Session = Depends(get_db)):
    try:
        total_trips = db.query(TripRecord).count()
        trips = db.query(TripRecord).all()
        total_barrels = sum(t.quantity_bbl for t in trips)
        return {
            "total_internal_trips": total_trips,
            "total_barrels_internal": total_barrels,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# لتشغيل الخادم من سطر الأوامر أثناء التطوير المحلي فقط
# على Render يتم التشغيل عبر Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
