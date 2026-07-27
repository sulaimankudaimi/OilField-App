# -*- coding: utf-8 -*-
"""
client_api.py
-------------
ملف وسيط يتم استخدامه في واجهة المستخدم (Streamlit / Flet) 
لإرسال وجلب البيانات من الخادم السحابي على Render بأمان.
"""

import requests

# رابط الخادم السحابي الحي على Render
API_BASE_URL = "https://oilfield-app.onrender.com"

# مفتاح الحماية السري لتجاوز حماية الخادم
HEADERS = {
    "X-API-Key": "Suleiman_Secure_Key_2026",
    "Content-Type": "application/json"
}

def get_dashboard_kpi():
    """دالة لجلب مؤشرات الأداء اليومية من الخادم السحابي"""
    url = f"{API_BASE_URL}/api/kpi"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"خطأ في جلب البيانات: {response.text}")
            return None
    except Exception as e:
        print(f"فشل الاتصال بالخادم: {e}")
        return None

def submit_internal_trip(plate: str, driver: str, well: str, quantity: float):
    """دالة لإرسال وتخزين بيانات رحلة نقل داخلي جديدة سحابياً"""
    url = f"{API_BASE_URL}/api/internal_trip"
    data = {
        "plate_number": plate,
        "driver_name": driver,
        "well_name": well,
        "quantity_bbl": quantity
    }
    try:
        response = requests.post(url, json=data, headers=HEADERS)
        if response.status_code == 200:
            return True, response.json().get("message", "تم الحفظ بنجاح")
        else:
            return False, response.text
    except Exception as e:
        return False, f"فشل الاتصال بالخادم: {e}"

def submit_external_trip(plate: str, driver: str, task: str, location: str, w_before: float, w_after: float, quantity: float = None):
    """دالة لإرسال وتخزين بيانات رحلة نقل خارجي جديدة سحابياً"""
    url = f"{API_BASE_URL}/api/external_trip"
    data = {
        "plate_number": plate,
        "driver_name": driver,
        "task_number": task,
        "loading_location": location,
        "weight_before": w_before,
        "weight_after": w_after,
        "quantity_bbl": quantity
    }
    try:
        response = requests.post(url, json=data, headers=HEADERS)
        if response.status_code == 200:
            return True, response.json().get("message", "تم الحفظ بنجاح")
        else:
            return False, response.text
    except Exception as e:
        return False, f"فشل الاتصال بالخادم: {e}"
