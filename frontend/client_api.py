import requests

# عدّل هذا الرابط إلى رابط تطبيقك الفعلي على Render بعد النشر
BASE_URL = "https://YOUR-RENDER-APP.onrender.com"

TIMEOUT = 15


def lookup_vehicle(plate_number: str) -> dict:
    resp = requests.get(f"{BASE_URL}/api/vehicle/{plate_number}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def register_vehicle(plate_number: str, car_type: str = None, color: str = None) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/vehicle",
        json={"plate_number": plate_number, "car_type": car_type, "color": color},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def create_driver(name: str, plate_number: str = None) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/driver",
        json={"name": name, "plate_number": plate_number},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_wells() -> list:
    resp = requests.get(f"{BASE_URL}/api/wells", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def create_well(name: str) -> dict:
    resp = requests.post(f"{BASE_URL}/api/wells", json={"name": name}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def create_trip(plate_number: str, driver_name: str, well_name: str, quantity_bbl: float) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/internal_trip",
        json={
            "plate_number": plate_number,
            "driver_name": driver_name,
            "well_name": well_name,
            "quantity_bbl": quantity_bbl,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def create_external_trip(
    plate_number: str,
    driver_name: str,
    task_number: str,
    loading_location: str,
    weight_before: float,
    weight_after: float,
    net_weight: float,
    quantity_bbl: float = None,
) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/external_trip",
        json={
            "plate_number": plate_number,
            "driver_name": driver_name,
            "task_number": task_number,
            "loading_location": loading_location,
            "weight_before": weight_before,
            "weight_after": weight_after,
            "net_weight": net_weight,
            "quantity_bbl": quantity_bbl,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_kpis() -> dict:
    resp = requests.get(f"{BASE_URL}/api/kpi", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()
