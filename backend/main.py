from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine, Base
from models import TripRecord
from schemas import TripCreate

# إنشاء الجداول تلقائياً عند إقلاع الخادم إن لم تكن موجودة
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OilField Internal Trips API")

# مطلوب حتى يستطيع تطبيق الجوال (Flet) الاتصال بالخادم من نطاق مختلف
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
