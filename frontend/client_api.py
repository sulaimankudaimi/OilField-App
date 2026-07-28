import requests

# عدّل هذا الرابط إلى رابط تطبيقك الفعلي على Render بعد النشر
BASE_URL = "https://YOUR-RENDER-APP.onrender.com"


def create_trip(plate_number: str, driver_name: str, well_name: str, quantity_bbl: float) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/internal_trip",
        json={
            "plate_number": plate_number,
            "driver_name": driver_name,
            "well_name": well_name,
            "quantity_bbl": quantity_bbl,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_kpis() -> dict:
    resp = requests.get(f"{BASE_URL}/api/kpi", timeout=15)
    resp.raise_for_status()
    return resp.json()
