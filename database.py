# -*- coding: utf-8 -*-
"""
database.py
------------
وحدة إدارة قاعدة البيانات لنظام أتمتة تقارير حقل النفط.
تم التحديث للعمل مع PostgreSQL (Neon) للحفاظ على البيانات سحابياً.
"""

import os
import difflib
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor

# جلب الرابط من إعدادات Render أو استخدام الرابط الخاص بك مباشرة (كبديل احتياطي)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_7EQxra2LMRwY@ep-restless-paper-axc441fe-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

def get_connection():
    """إرجاع اتصال جديد بقاعدة البيانات السحابية."""
    # نستخدم محرك psycopg2 للاتصال بقاعدة PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """إنشاء جميع الجداول إذا لم تكن موجودة مسبقًا (معدلة لـ PostgreSQL)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Vehicles (
        plate_number TEXT PRIMARY KEY,
        car_type     TEXT,
        color        TEXT
    );

    CREATE TABLE IF NOT EXISTS Drivers (
        driver_id   SERIAL PRIMARY KEY,
        driver_name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Vehicle_Drivers (
        plate_number TEXT NOT NULL,
        driver_id    INTEGER NOT NULL,
        PRIMARY KEY (plate_number, driver_id),
        FOREIGN KEY (plate_number) REFERENCES Vehicles(plate_number) ON DELETE CASCADE,
        FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Wells (
        well_name TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS Internal_Trips (
        trip_id      SERIAL PRIMARY KEY,
        trip_date    TEXT NOT NULL,
        plate_number TEXT NOT NULL,
        driver_id    INTEGER,
        well_name    TEXT,
        quantity_bbl REAL,
        FOREIGN KEY (plate_number) REFERENCES Vehicles(plate_number),
        FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id),
        FOREIGN KEY (well_name) REFERENCES Wells(well_name)
    );

    CREATE TABLE IF NOT EXISTS External_Trips (
        trip_id          SERIAL PRIMARY KEY,
        trip_date        TEXT NOT NULL,
        plate_number     TEXT NOT NULL,
        driver_id        INTEGER,
        task_number      TEXT,
        loading_location TEXT,
        weight_before    REAL,
        weight_after     REAL,
        net_weight       REAL,
        quantity_bbl     REAL,
        FOREIGN KEY (plate_number) REFERENCES Vehicles(plate_number),
        FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ تم تجهيز قاعدة بيانات Neon السحابية بنجاح!")


# ---------------------------------------------------------------------------
# دوال البيانات الأساسية (Master Data)
# ---------------------------------------------------------------------------

def upsert_vehicle(plate_number: str, car_type: str = None, color: str = None):
    """إضافة سيارة جديدة أو تحديث بياناتها إن كانت موجودة."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Vehicles (plate_number, car_type, color)
        VALUES (%s, %s, %s)
        ON CONFLICT(plate_number) DO UPDATE SET
            car_type = COALESCE(EXCLUDED.car_type, Vehicles.car_type),
            color    = COALESCE(EXCLUDED.color, Vehicles.color)
    """, (str(plate_number).strip(), car_type, color))
    conn.commit()
    cur.close()
    conn.close()


def get_or_create_driver(driver_name: str) -> int:
    """إرجاع معرّف السائق، وإنشاء سجل جديد له إن لم يكن موجودًا."""
    driver_name = driver_name.strip()
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT driver_id FROM Drivers WHERE driver_name = %s", (driver_name,))
    row = cur.fetchone()
    if row:
        driver_id = row["driver_id"]
    else:
        # في Postgres نستخدم RETURNING للحصول على المعرف فوراً
        cur.execute("INSERT INTO Drivers (driver_name) VALUES (%s) RETURNING driver_id", (driver_name,))
        driver_id = cur.fetchone()["driver_id"]
        conn.commit()
    cur.close()
    conn.close()
    return driver_id


def link_driver_to_vehicle(plate_number: str, driver_id: int):
    """ربط سائق بسيارة معينة."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Vehicle_Drivers (plate_number, driver_id)
        VALUES (%s, %s)
        ON CONFLICT (plate_number, driver_id) DO NOTHING
    """, (str(plate_number).strip(), driver_id))
    conn.commit()
    cur.close()
    conn.close()


def upsert_well(well_name: str):
    """إضافة بئر جديد إن لم يكن موجودًا."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Wells (well_name) VALUES (%s)
        ON CONFLICT (well_name) DO NOTHING
    """, (well_name.strip(),))
    conn.commit()
    cur.close()
    conn.close()


def get_all_wells():
    """إرجاع قائمة بجميع أسماء الآبار."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT well_name FROM Wells ORDER BY well_name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["well_name"] for r in rows]


def get_all_plate_numbers():
    """إرجاع قائمة بجميع أرقام اللوحات المسجلة."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT plate_number FROM Vehicles")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["plate_number"] for r in rows]


def get_vehicle_info(plate_number: str, fuzzy_threshold: float = 0.8):
    """البحث عن بيانات سيارة برقم لوحتها مع ميزة البحث التقريبي."""
    plate_number = str(plate_number).strip()
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM Vehicles WHERE plate_number = %s", (plate_number,))
    row = cur.fetchone()

    if row:
        cur.execute("""
            SELECT d.driver_name FROM Drivers d
            JOIN Vehicle_Drivers vd ON d.driver_id = vd.driver_id
            WHERE vd.plate_number = %s
            ORDER BY d.driver_name
        """, (plate_number,))
        drivers = cur.fetchall()
        cur.close()
        conn.close()
        return {
            "found": True,
            "plate_number": row["plate_number"],
            "car_type": row["car_type"],
            "color": row["color"],
            "drivers": [d["driver_name"] for d in drivers],
            "suggestion": None,
        }

    cur.execute("SELECT plate_number FROM Vehicles")
    all_plates = [r["plate_number"] for r in cur.fetchall()]
    cur.close()
    conn.close()

    suggestion = None
    if all_plates:
        matches = difflib.get_close_matches(plate_number, all_plates, n=1, cutoff=fuzzy_threshold)
        if matches:
            suggestion = matches[0]

    return {
        "found": False,
        "plate_number": plate_number,
        "car_type": None,
        "color": None,
        "drivers": [],
        "suggestion": suggestion,
    }


def get_drivers_for_vehicle(plate_number: str):
    """إرجاع قائمة أسماء السائقين المرتبطين برقم لوحة معين فقط."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT d.driver_name FROM Drivers d
        JOIN Vehicle_Drivers vd ON d.driver_id = vd.driver_id
        WHERE vd.plate_number = %s
        ORDER BY d.driver_name
    """, (str(plate_number).strip(),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["driver_name"] for r in rows]


# ---------------------------------------------------------------------------
# دوال إدخال الرحلات اليومية (Transactions)
# ---------------------------------------------------------------------------

def insert_internal_trip(trip_date: str, plate_number: str, driver_name: str,
                          well_name: str, quantity_bbl: float):
    """تسجيل رحلة نقل داخلي جديدة."""
    driver_id = get_or_create_driver(driver_name) if driver_name else None
    if driver_id:
        link_driver_to_vehicle(plate_number, driver_id)
    if well_name:
        upsert_well(well_name)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Internal_Trips (trip_date, plate_number, driver_id, well_name, quantity_bbl)
        VALUES (%s, %s, %s, %s, %s)
    """, (trip_date, str(plate_number).strip(), driver_id, well_name, quantity_bbl))
    conn.commit()
    cur.close()
    conn.close()


def insert_external_trip(trip_date: str, plate_number: str, driver_name: str,
                          task_number: str, loading_location: str,
                          weight_before: float, weight_after: float,
                          quantity_bbl: float = None):
    """تسجيل رحلة نقل خارجي جديدة."""
    driver_id = get_or_create_driver(driver_name) if driver_name else None
    if driver_id:
        link_driver_to_vehicle(plate_number, driver_id)

    net_weight = None
    if weight_before is not None and weight_after is not None:
        net_weight = weight_after - weight_before

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO External_Trips
            (trip_date, plate_number, driver_id, task_number, loading_location,
             weight_before, weight_after, net_weight, quantity_bbl)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (trip_date, str(plate_number).strip(), driver_id, task_number, loading_location,
          weight_before, weight_after, net_weight, quantity_bbl))
    conn.commit()
    cur.close()
    conn.close()


def get_daily_report(trip_date: str):
    """إرجاع بيانات اليوم كاملة (داخلي وخارجي)."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT it.trip_id, it.trip_date, it.plate_number, v.car_type, v.color,
               d.driver_name, it.well_name, it.quantity_bbl
        FROM Internal_Trips it
        LEFT JOIN Vehicles v ON it.plate_number = v.plate_number
        LEFT JOIN Drivers d ON it.driver_id = d.driver_id
        WHERE it.trip_date = %s
        ORDER BY it.trip_id
    """, (trip_date,))
    internal = cur.fetchall()

    cur.execute("""
        SELECT et.trip_id, et.trip_date, et.plate_number, v.car_type, v.color,
               d.driver_name, et.task_number, et.loading_location,
               et.weight_before, et.weight_after, et.net_weight, et.quantity_bbl
        FROM External_Trips et
        LEFT JOIN Vehicles v ON et.plate_number = v.plate_number
        LEFT JOIN Drivers d ON et.driver_id = d.driver_id
        WHERE et.trip_date = %s
        ORDER BY et.trip_id
    """, (trip_date,))
    external = cur.fetchall()
    
    cur.close()
    conn.close()

    return {
        "internal": [dict(r) for r in internal],
        "external": [dict(r) for r in external],
    }


if __name__ == "__main__":
    init_db()
