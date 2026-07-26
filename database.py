# -*- coding: utf-8 -*-
"""
database.py
------------
وحدة إدارة قاعدة البيانات لنظام أتمتة تقارير حقل النفط.
تستخدم SQLite (ملف واحد خفيف، لا يحتاج سيرفر منفصل).

الجداول:
    Vehicles         : السيارات/الصهاريج (المفتاح الأساسي: رقم اللوحة)
    Drivers          : السائقون
    Vehicle_Drivers  : علاقة متعدد-لمتعدد بين السيارات والسائقين
    Wells            : الآبار النفطية
    Internal_Trips   : رحلات النقل الداخلي (من البئر إلى المحطة الرئيسية)
    External_Trips   : رحلات النقل الخارجي (من المحطة الرئيسية إلى المصفاة)
"""

import sqlite3
import os
import difflib
from datetime import date

# مسار قاعدة البيانات: مجلد data/ داخل جذر المشروع
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "oilfield.db")


def get_connection():
    """إرجاع اتصال جديد بقاعدة البيانات مع تفعيل القيود المرجعية (Foreign Keys)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """إنشاء جميع الجداول إذا لم تكن موجودة مسبقًا."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS Vehicles (
        plate_number TEXT PRIMARY KEY,
        car_type     TEXT,
        color        TEXT
    );

    CREATE TABLE IF NOT EXISTS Drivers (
        driver_id   INTEGER PRIMARY KEY AUTOINCREMENT,
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
        trip_id      INTEGER PRIMARY KEY AUTOINCREMENT,
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
        trip_id          INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.close()
    print(f"✅ تم تجهيز قاعدة البيانات في: {DB_PATH}")


# ---------------------------------------------------------------------------
# دوال البيانات الأساسية (Master Data)
# ---------------------------------------------------------------------------

def upsert_vehicle(plate_number: str, car_type: str = None, color: str = None):
    """إضافة سيارة جديدة أو تحديث بياناتها إن كانت موجودة."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO Vehicles (plate_number, car_type, color)
        VALUES (?, ?, ?)
        ON CONFLICT(plate_number) DO UPDATE SET
            car_type = COALESCE(excluded.car_type, Vehicles.car_type),
            color    = COALESCE(excluded.color, Vehicles.color)
    """, (str(plate_number).strip(), car_type, color))
    conn.commit()
    conn.close()


def get_or_create_driver(driver_name: str) -> int:
    """إرجاع معرّف السائق، وإنشاء سجل جديد له إن لم يكن موجودًا."""
    driver_name = driver_name.strip()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT driver_id FROM Drivers WHERE driver_name = ?", (driver_name,))
    row = cur.fetchone()
    if row:
        driver_id = row["driver_id"]
    else:
        cur.execute("INSERT INTO Drivers (driver_name) VALUES (?)", (driver_name,))
        driver_id = cur.lastrowid
        conn.commit()
    conn.close()
    return driver_id


def link_driver_to_vehicle(plate_number: str, driver_id: int):
    """ربط سائق بسيارة معينة (لدعم أكثر من سائق لكل لوحة)."""
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO Vehicle_Drivers (plate_number, driver_id)
        VALUES (?, ?)
    """, (str(plate_number).strip(), driver_id))
    conn.commit()
    conn.close()


def upsert_well(well_name: str):
    """إضافة بئر جديد إن لم يكن موجودًا."""
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO Wells (well_name) VALUES (?)", (well_name.strip(),))
    conn.commit()
    conn.close()


def get_all_wells():
    """إرجاع قائمة بجميع أسماء الآبار (لتعبئة القائمة المنسدلة)."""
    conn = get_connection()
    rows = conn.execute("SELECT well_name FROM Wells ORDER BY well_name").fetchall()
    conn.close()
    return [r["well_name"] for r in rows]


def get_all_plate_numbers():
    """إرجاع قائمة بجميع أرقام اللوحات المسجلة (للبحث التقريبي)."""
    conn = get_connection()
    rows = conn.execute("SELECT plate_number FROM Vehicles").fetchall()
    conn.close()
    return [r["plate_number"] for r in rows]


def get_vehicle_info(plate_number: str, fuzzy_threshold: float = 0.8):
    """
    البحث عن بيانات سيارة برقم لوحتها.
    - أولًا: بحث دقيق (Exact Match).
    - إن لم يوجد: بحث تقريبي (Fuzzy Matching) لاقتراح أقرب رقم لوحة مسجّل،
      لتفادي الأخطاء الإملائية البسيطة عند الكتابة اليدوية.

    يُرجع قاموسًا (dict) على الشكل:
    {
        "found": True/False,          # هل وُجدت مطابقة دقيقة؟
        "plate_number": "...",
        "car_type": "...",
        "color": "...",
        "drivers": ["اسم1", "اسم2", ...],
        "suggestion": "..." أو None    # اقتراح بديل في حال عدم التطابق الدقيق
    }
    """
    plate_number = str(plate_number).strip()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM Vehicles WHERE plate_number = ?", (plate_number,))
    row = cur.fetchone()

    if row:
        drivers = cur.execute("""
            SELECT d.driver_name FROM Drivers d
            JOIN Vehicle_Drivers vd ON d.driver_id = vd.driver_id
            WHERE vd.plate_number = ?
            ORDER BY d.driver_name
        """, (plate_number,)).fetchall()
        conn.close()
        return {
            "found": True,
            "plate_number": row["plate_number"],
            "car_type": row["car_type"],
            "color": row["color"],
            "drivers": [d["driver_name"] for d in drivers],
            "suggestion": None,
        }

    # لا يوجد تطابق دقيق -> نبحث عن أقرب رقم لوحة مسجّل (بحث تقريبي)
    all_plates = [r["plate_number"] for r in cur.execute("SELECT plate_number FROM Vehicles").fetchall()]
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
    rows = conn.execute("""
        SELECT d.driver_name FROM Drivers d
        JOIN Vehicle_Drivers vd ON d.driver_id = vd.driver_id
        WHERE vd.plate_number = ?
        ORDER BY d.driver_name
    """, (str(plate_number).strip(),)).fetchall()
    conn.close()
    return [r["driver_name"] for r in rows]


# ---------------------------------------------------------------------------
# دوال إدخال الرحلات اليومية (Transactions)
# ---------------------------------------------------------------------------

def insert_internal_trip(trip_date: str, plate_number: str, driver_name: str,
                          well_name: str, quantity_bbl: float):
    """تسجيل رحلة نقل داخلي جديدة (من بئر إلى المحطة الرئيسية)."""
    driver_id = get_or_create_driver(driver_name) if driver_name else None
    if driver_id:
        link_driver_to_vehicle(plate_number, driver_id)
    if well_name:
        upsert_well(well_name)

    conn = get_connection()
    conn.execute("""
        INSERT INTO Internal_Trips (trip_date, plate_number, driver_id, well_name, quantity_bbl)
        VALUES (?, ?, ?, ?, ?)
    """, (trip_date, str(plate_number).strip(), driver_id, well_name, quantity_bbl))
    conn.commit()
    conn.close()


def insert_external_trip(trip_date: str, plate_number: str, driver_name: str,
                          task_number: str, loading_location: str,
                          weight_before: float, weight_after: float,
                          quantity_bbl: float = None):
    """تسجيل رحلة نقل خارجي جديدة (من المحطة الرئيسية إلى المصفاة)."""
    driver_id = get_or_create_driver(driver_name) if driver_name else None
    if driver_id:
        link_driver_to_vehicle(plate_number, driver_id)

    net_weight = None
    if weight_before is not None and weight_after is not None:
        net_weight = weight_after - weight_before

    conn = get_connection()
    conn.execute("""
        INSERT INTO External_Trips
            (trip_date, plate_number, driver_id, task_number, loading_location,
             weight_before, weight_after, net_weight, quantity_bbl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (trip_date, str(plate_number).strip(), driver_id, task_number, loading_location,
          weight_before, weight_after, net_weight, quantity_bbl))
    conn.commit()
    conn.close()


def get_daily_report(trip_date: str):
    """إرجاع بيانات اليوم كاملة (داخلي وخارجي) لعرضها أو تصديرها."""
    conn = get_connection()
    internal = conn.execute("""
        SELECT it.trip_id, it.trip_date, it.plate_number, v.car_type, v.color,
               d.driver_name, it.well_name, it.quantity_bbl
        FROM Internal_Trips it
        LEFT JOIN Vehicles v ON it.plate_number = v.plate_number
        LEFT JOIN Drivers d ON it.driver_id = d.driver_id
        WHERE it.trip_date = ?
        ORDER BY it.trip_id
    """, (trip_date,)).fetchall()

    external = conn.execute("""
        SELECT et.trip_id, et.trip_date, et.plate_number, v.car_type, v.color,
               d.driver_name, et.task_number, et.loading_location,
               et.weight_before, et.weight_after, et.net_weight, et.quantity_bbl
        FROM External_Trips et
        LEFT JOIN Vehicles v ON et.plate_number = v.plate_number
        LEFT JOIN Drivers d ON et.driver_id = d.driver_id
        WHERE et.trip_date = ?
        ORDER BY et.trip_id
    """, (trip_date,)).fetchall()
    conn.close()

    return {
        "internal": [dict(r) for r in internal],
        "external": [dict(r) for r in external],
    }


if __name__ == "__main__":
    # تشغيل مباشر لهذا الملف: إنشاء قاعدة البيانات فقط (للاختبار السريع)
    init_db()
