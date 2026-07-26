# -*- coding: utf-8 -*-
"""
api.py
------
خادم FastAPI كوسيط آمن بين تطبيق الجوال وقاعدة البيانات سحابياً.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from datetime import date
import database as db

# تهيئة قاعدة البيانات
db.init_db()

app = FastAPI(title="OilField Automation API", version="1.0")

# ---------------------------------------------------------------------------
# إعداد نظام الحماية بواسطة مفتاح API السري
# ---------------------------------------------------------------------------
API_KEY = "Suleiman_Secure_Key_2026"  # يمكن تغيره إلى أي نص سري خاص بك
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(header_key: str = Depends(api_key_header)):
    if header_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="عذراً، مفتاح الوصول غير صحيح أو مفقود!"
        )
    return header_key

# ---------------------------------------------------------------------------
# نماذج البيانات (Pydantic Models)
# ---------------------------------------------------------------------------
class InternalTrip(BaseModel):
    plate_number: str
    driver_name: str
    well_name: str
    quantity_bbl: float

class ExternalTrip(BaseModel):
    plate_number: str
    driver_name: str
    task_number: str
    loading_location: str
    weight_before: float
    weight_after: float
    quantity_bbl: float = None

# ---------------------------------------------------------------------------
# مسارات الـ API (Endpoints)
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "خادم حقل العمر يعمل بنجاح 🚀"}

@app.post("/api/internal_trip", dependencies=[Depends(verify_api_key)])
def add_internal_trip(trip: InternalTrip):
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        db.insert_internal_trip(
            trip_date=today_str,
            plate_number=trip.plate_number,
            driver_name=trip.driver_name,
            well_name=trip.well_name,
            quantity_bbl=trip.quantity_bbl
        )
        return {"status": "success", "message": "تم حفظ رحلة النقل الداخلي بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/external_trip", dependencies=[Depends(verify_api_key)])
def add_external_trip(trip: ExternalTrip):
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        db.insert_external_trip(
            trip_date=today_str,
            plate_number=trip.plate_number,
            driver_name=trip.driver_name,
            task_number=trip.task_number,
            loading_location=trip.loading_location,
            weight_before=trip.weight_before,
            weight_after=trip.weight_after,
            quantity_bbl=trip.quantity_bbl
        )
        return {"status": "success", "message": "تم حفظ رحلة النقل الخارجي بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpi", dependencies=[Depends(verify_api_key)])
def get_daily_kpi():
    """جلب مؤشرات الأداء اليومية لعرضها في الشاشة الرئيسية لتطبيق الجوال"""
    today_str = date.today().strftime("%Y-%m-%d")
    report = db.get_daily_report(today_str)
    
    internal_count = len(report["internal"])
    external_count = len(report["external"])
    
    total_bbl = sum(float(trip[5]) for trip in report["internal"] if trip[5])
    
    return {
        "date": today_str,
        "total_internal_trips": internal_count,
        "total_external_trips": external_count,
        "total_barrels_internal": total_bbl
    }