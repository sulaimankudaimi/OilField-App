import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime

# 1. إعدادات قاعدة البيانات الديناميكية (تعمل محلياً وسحابياً)
# سيقرأ الخادم الرابط السحابي إذا كان موجوداً، وإلا سيصنع ملف oilfield.db محلي
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./oilfield.db")

# معالجة توافق رابط Neon السحابي (postgres://) مع متطلبات مكتبة SQLAlchemy (postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# إعداد محرك قاعدة البيانات
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. بناء نماذج قاعدة البيانات (Models)
class TripRecord(Base):
    __tablename__ = "internal_trips"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, index=True)
    driver_name = Column(String)
    well_name = Column(String)
    quantity_bbl = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# إنشاء الجداول فوراً إذا لم تكن موجودة
Base.metadata.create_all(bind=engine)

# 3. نماذج التحقق من البيانات (Pydantic Schemas)
class TripCreate(BaseModel):
    plate_number: str
    driver_name: str
    well_name: str
    quantity_bbl: float

# 4. تهيئة تطبيق FastAPI
app = FastAPI(title="AegisPhys API - Oil Field Core")

# إضافة CORS للسماح لتطبيقات خارجية (مثل تطبيق الموبايل) بالاتصال بالخادم
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# دالة الحصول على جلسة قاعدة البيانات بأمان
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. برمجة مسارات (Endpoints) واجهة برمجة التطبيقات

@app.post("/api/internal_trip")
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    try:
        new_trip = TripRecord(
            plate_number=trip.plate_number,
            driver_name=trip.driver_name,
            well_name=trip.well_name,
            quantity_bbl=trip.quantity_bbl
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
        # حساب إجمالي البراميل المنقولة
        trips = db.query(TripRecord).all()
        total_barrels = sum(t.quantity_bbl for t in trips)
        
        return {
            "total_internal_trips": total_trips,
            "total_barrels_internal": total_barrels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# لتشغيل الخادم من سطر الأوامر أثناء التطوير
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
