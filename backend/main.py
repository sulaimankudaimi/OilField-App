# -*- coding: utf-8 -*-
import flet as ft
from datetime import date

import client_api as api


def main(page: ft.Page):
    page.title = "نظام أتمتة تقارير حقل العمر"
    page.rtl = True
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # قوائم الرحلات المُضافة لليوم الحالي (تعادل st.session_state في Streamlit)
    internal_entries = []
    external_entries = []

    # ---------------- تاريخ التقرير ----------------
    report_date_picker = ft.DatePicker(value=date.today())
    page.overlay.append(report_date_picker)
    report_date_text = ft.Text(f"📅 تاريخ التقرير: {date.today().strftime('%Y-%m-%d')}", size=16)

    def open_date_picker(e):
        report_date_picker.open = True
        page.update()

    def on_date_change(e):
        if report_date_picker.value:
            report_date_text.value = f"📅 تاريخ التقرير: {report_date_picker.value.strftime('%Y-%m-%d')}"
            page.update()

    report_date_picker.on_change = on_date_change
    change_date_button = ft.TextButton("تغيير التاريخ", icon=ft.icons.CALENDAR_MONTH, on_click=open_date_picker)

    # =========================================================
    #  تبويب: نقل داخلي
    # =========================================================
    int_plate = ft.TextField(label="🔢 رقم اللوحة", text_align=ft.TextAlign.RIGHT)
    int_vehicle_info = ft.Text()
    int_driver_dropdown = ft.Dropdown(label="👤 السائق", visible=False)
    int_new_driver_field = ft.TextField(label="اسم السائق الجديد", visible=False)
    int_suggestion_banner = ft.Container(visible=False)
    int_new_vehicle_panel = ft.Container(visible=False)
    int_new_type = ft.TextField(label="نوع السيارة", hint_text="مثال: مرسيدس")
    int_new_color = ft.TextField(label="اللون", hint_text="مثال: أحمر")
    int_new_driver_fresh = ft.TextField(label="اسم السائق")

    int_well_dropdown = ft.Dropdown(label="🛢️ البئر المصدر")
    int_new_well_field = ft.TextField(label="اسم البئر الجديد", visible=False)
    int_qty = ft.TextField(label="🧪 الكمية (برميل)", keyboard_type=ft.KeyboardType.NUMBER)
    int_status = ft.Text()

    # يخزن آخر بيانات سيارة مؤكدة لهذه الرحلة (تعادل متغيرات smart_vehicle_lookup المُعادة في Streamlit)
    int_current_vehicle = {"plate": None, "car_type": None, "color": None}

    def refresh_wells():
        try:
            wells = api.get_wells()
        except Exception:
            wells = []
        int_well_dropdown.options = [ft.dropdown.Option(w) for w in wells] + [
            ft.dropdown.Option("➕ بئر جديد")
        ]
        int_well_dropdown.value = wells[0] if wells else "➕ بئر جديد"
        page.update()

    def on_int_well_change(e):
        int_new_well_field.visible = int_well_dropdown.value == "➕ بئر جديد"
        page.update()

    int_well_dropdown.on_change = on_int_well_change

    def use_int_suggestion(suggested_plate):
        int_plate.value = suggested_plate
        do_int_vehicle_lookup()

    def on_int_driver_change(e):
        int_new_driver_field.visible = int_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
        page.update()

    int_driver_dropdown.on_change = on_int_driver_change

    def do_int_vehicle_lookup(e=None):
        plate = int_plate.value.strip() if int_plate.value else ""
        int_suggestion_banner.visible = False
        int_new_vehicle_panel.visible = False
        int_driver_dropdown.visible = False
        int_new_driver_field.visible = False
        int_vehicle_info.value = ""
        int_current_vehicle.update(plate=None, car_type=None, color=None)

        if not plate:
            page.update()
            return

        try:
            info = api.lookup_vehicle(plate)
        except Exception as ex:
            int_status.value = f"تعذر الاتصال بالخادم: {ex}"
            int_status.color = ft.colors.RED
            page.update()
            return

        if info.get("found"):
            int_current_vehicle["plate"] = info["plate_number"]
            int_current_vehicle["car_type"] = info.get("car_type")
            int_current_vehicle["color"] = info.get("color")
            int_vehicle_info.value = f"🚗 {info.get('car_type') or '—'} / {info.get('color') or '—'}"
            drivers = info.get("drivers", [])
            int_driver_dropdown.options = [ft.dropdown.Option(d) for d in drivers] + [
                ft.dropdown.Option("➕ سائق جديد لهذه السيارة")
            ]
            int_driver_dropdown.value = drivers[0] if drivers else "➕ سائق جديد لهذه السيارة"
            int_driver_dropdown.visible = True
            int_new_driver_field.visible = int_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
        else:
            if info.get("suggestion"):
                sugg = info["suggestion"]
                int_suggestion_banner.content = ft.Row(
                    [
                        ft.Text(f"⚠️ لا توجد لوحة بهذا الرقم. هل تقصد {sugg}؟"),
                        ft.ElevatedButton("✅ نعم، استخدم هذا الرقم", on_click=lambda e, p=sugg: use_int_suggestion(p)),
                    ]
                )
                int_suggestion_banner.visible = True
            int_new_vehicle_panel.visible = True

        page.update()

    int_plate.on_blur = do_int_vehicle_lookup

    def register_new_int_vehicle(e):
        plate = int_plate.value.strip() if int_plate.value else ""
        driver = int_new_driver_fresh.value.strip() if int_new_driver_fresh.value else ""
        if not plate or not driver:
            int_status.value = "أدخل رقم اللوحة واسم السائق على الأقل."
            int_status.color = ft.colors.RED
            page.update()
            return
        try:
            api.register_vehicle(plate, int_new_type.value or None, int_new_color.value or None)
            api.create_driver(driver, plate)
            int_status.value = "تم تسجيل السيارة. أعد إدخال رقم اللوحة أعلاه لإكمال الرحلة."
            int_status.color = ft.colors.GREEN
            int_new_type.value = int_new_color.value = int_new_driver_fresh.value = ""
        except Exception as ex:
            int_status.value = f"خطأ: {ex}"
            int_status.color = ft.colors.RED
        page.update()

    int_new_vehicle_panel.content = ft.Column(
        [
            ft.Text("🆕 سيارة جديدة — لم يُعثر عليها، سجّلها الآن لمرة واحدة", weight=ft.FontWeight.BOLD),
            int_new_type,
            int_new_color,
            int_new_driver_fresh,
            ft.ElevatedButton("💾 تسجيل السيارة والمتابعة", on_click=register_new_int_vehicle),
        ],
        spacing=10,
    )

    def add_internal_entry(e):
        plate = int_current_vehicle["plate"]
        driver = None
        if int_driver_dropdown.visible:
            driver = (
                int_new_driver_field.value.strip()
                if int_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
                else int_driver_dropdown.value
            )
        well = (
            int_new_well_field.value.strip()
            if int_well_dropdown.value == "➕ بئر جديد"
            else int_well_dropdown.value
        )
        try:
            qty = float(int_qty.value) if int_qty.value else 0.0
        except ValueError:
            qty = 0.0

        if not plate or not driver or not well:
            int_status.value = "الرجاء إكمال جميع البيانات الأساسية."
            int_status.color = ft.colors.RED
            page.update()
            return

        internal_entries.append(
            {
                "رقم اللوحة": plate,
                "النوع": int_current_vehicle.get("car_type"),
                "اللون": int_current_vehicle.get("color"),
                "السائق": driver,
                "البئر": well,
                "الكمية (برميل)": qty,
            }
        )
        int_status.value = "تمت الإضافة إلى قائمة اليوم ✅"
        int_status.color = ft.colors.GREEN
        int_plate.value = ""
        int_qty.value = ""
        int_vehicle_info.value = ""
        int_driver_dropdown.visible = False
        refresh_review()
        page.update()

    internal_tab = ft.Column(
        [
            ft.Text("إضافة رحلة نقل داخلي (من بئر إلى المحطة الرئيسية)", size=18, weight=ft.FontWeight.BOLD),
            int_plate,
            int_vehicle_info,
            int_suggestion_banner,
            int_driver_dropdown,
            int_new_driver_field,
            int_new_vehicle_panel,
            int_well_dropdown,
            int_new_well_field,
            int_qty,
            ft.ElevatedButton("➕ إضافة للقائمة", icon=ft.icons.ADD, on_click=add_internal_entry),
            int_status,
        ],
        spacing=12,
    )

    # =========================================================
    #  تبويب: نقل خارجي
    # =========================================================
    ext_plate = ft.TextField(label="🔢 رقم اللوحة", text_align=ft.TextAlign.RIGHT)
    ext_vehicle_info = ft.Text()
    ext_driver_dropdown = ft.Dropdown(label="👤 السائق", visible=False)
    ext_new_driver_field = ft.TextField(label="اسم السائق الجديد", visible=False)
    ext_suggestion_banner = ft.Container(visible=False)
    ext_new_vehicle_panel = ft.Container(visible=False)
    ext_new_type = ft.TextField(label="نوع السيارة")
    ext_new_color = ft.TextField(label="اللون")
    ext_new_driver_fresh = ft.TextField(label="اسم السائق")

    ext_task = ft.TextField(label="🔖 رقم المهمة")
    ext_loc = ft.TextField(label="📍 موقع التحميل", value="المحطة الرئيسية")
    ext_wb = ft.TextField(label="⚖️ الوزن قبل", keyboard_type=ft.KeyboardType.NUMBER)
    ext_wa = ft.TextField(label="⚖️ الوزن بعد", keyboard_type=ft.KeyboardType.NUMBER)
    ext_qty = ft.TextField(label="🧪 الكمية (برميل)", keyboard_type=ft.KeyboardType.NUMBER)
    ext_status = ft.Text()

    ext_current_vehicle = {"plate": None}

    def use_ext_suggestion(suggested_plate):
        ext_plate.value = suggested_plate
        do_ext_vehicle_lookup()

    def on_ext_driver_change(e):
        ext_new_driver_field.visible = ext_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
        page.update()

    ext_driver_dropdown.on_change = on_ext_driver_change

    def do_ext_vehicle_lookup(e=None):
        plate = ext_plate.value.strip() if ext_plate.value else ""
        ext_suggestion_banner.visible = False
        ext_new_vehicle_panel.visible = False
        ext_driver_dropdown.visible = False
        ext_new_driver_field.visible = False
        ext_vehicle_info.value = ""
        ext_current_vehicle["plate"] = None

        if not plate:
            page.update()
            return

        try:
            info = api.lookup_vehicle(plate)
        except Exception as ex:
            ext_status.value = f"تعذر الاتصال بالخادم: {ex}"
            ext_status.color = ft.colors.RED
            page.update()
            return

        if info.get("found"):
            ext_current_vehicle["plate"] = info["plate_number"]
            ext_vehicle_info.value = f"🚗 {info.get('car_type') or '—'} / {info.get('color') or '—'}"
            drivers = info.get("drivers", [])
            ext_driver_dropdown.options = [ft.dropdown.Option(d) for d in drivers] + [
                ft.dropdown.Option("➕ سائق جديد لهذه السيارة")
            ]
            ext_driver_dropdown.value = drivers[0] if drivers else "➕ سائق جديد لهذه السيارة"
            ext_driver_dropdown.visible = True
            ext_new_driver_field.visible = ext_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
        else:
            if info.get("suggestion"):
                sugg = info["suggestion"]
                ext_suggestion_banner.content = ft.Row(
                    [
                        ft.Text(f"⚠️ لا توجد لوحة بهذا الرقم. هل تقصد {sugg}؟"),
                        ft.ElevatedButton("✅ نعم، استخدم هذا الرقم", on_click=lambda e, p=sugg: use_ext_suggestion(p)),
                    ]
                )
                ext_suggestion_banner.visible = True
            ext_new_vehicle_panel.visible = True

        page.update()

    ext_plate.on_blur = do_ext_vehicle_lookup

    def register_new_ext_vehicle(e):
        plate = ext_plate.value.strip() if ext_plate.value else ""
        driver = ext_new_driver_fresh.value.strip() if ext_new_driver_fresh.value else ""
        if not plate or not driver:
            ext_status.value = "أدخل رقم اللوحة واسم السائق على الأقل."
            ext_status.color = ft.colors.RED
            page.update()
            return
        try:
            api.register_vehicle(plate, ext_new_type.value or None, ext_new_color.value or None)
            api.create_driver(driver, plate)
            ext_status.value = "تم تسجيل السيارة. أعد إدخال رقم اللوحة أعلاه لإكمال الرحلة."
            ext_status.color = ft.colors.GREEN
            ext_new_type.value = ext_new_color.value = ext_new_driver_fresh.value = ""
        except Exception as ex:
            ext_status.value = f"خطأ: {ex}"
            ext_status.color = ft.colors.RED
        page.update()

    ext_new_vehicle_panel.content = ft.Column(
        [
            ft.Text("🆕 سيارة جديدة — لم يُعثر عليها، سجّلها الآن لمرة واحدة", weight=ft.FontWeight.BOLD),
            ext_new_type,
            ext_new_color,
            ext_new_driver_fresh,
            ft.ElevatedButton("💾 تسجيل السيارة والمتابعة", on_click=register_new_ext_vehicle),
        ],
        spacing=10,
    )

    def add_external_entry(e):
        plate = ext_current_vehicle["plate"]
        driver = None
        if ext_driver_dropdown.visible:
            driver = (
                ext_new_driver_field.value.strip()
                if ext_driver_dropdown.value == "➕ سائق جديد لهذه السيارة"
                else ext_driver_dropdown.value
            )

        try:
            wb = float(ext_wb.value) if ext_wb.value else 0.0
            wa = float(ext_wa.value) if ext_wa.value else 0.0
        except ValueError:
            ext_status.value = "الرجاء إدخال أوزان صحيحة."
            ext_status.color = ft.colors.RED
            page.update()
            return

        if wa <= wb:
            ext_status.value = "الوزن بعد يجب أن يكون أكبر من الوزن قبل."
            ext_status.color = ft.colors.RED
            page.update()
            return

        net_weight = wa - wb
        qty = float(ext_qty.value) if ext_qty.value else None

        external_entries.append(
            {
                "رقم اللوحة": plate,
                "السائق": driver,
                "رقم المهمة": ext_task.value,
                "موقع التحميل": ext_loc.value,
                "الوزن قبل": wb,
                "الوزن بعد": wa,
                "الوزن الصافي": net_weight,
                "الكمية (برميل)": qty,
            }
        )
        ext_status.value = "تمت الإضافة إلى قائمة اليوم ✅"
        ext_status.color = ft.colors.GREEN
        ext_plate.value = ext_task.value = ""
        ext_wb.value = ext_wa.value = ext_qty.value = ""
        ext_vehicle_info.value = ""
        ext_driver_dropdown.visible = False
        refresh_review()
        page.update()

    external_tab = ft.Column(
        [
            ft.Text("إضافة رحلة نقل خارجي (من المحطة الرئيسية إلى المصفاة)", size=18, weight=ft.FontWeight.BOLD),
            ext_plate,
            ext_vehicle_info,
            ext_suggestion_banner,
            ext_driver_dropdown,
            ext_new_driver_field,
            ext_new_vehicle_panel,
            ext_task,
            ext_loc,
            ext_wb,
            ext_wa,
            ext_qty,
            ft.ElevatedButton("➕ إضافة للقائمة", icon=ft.icons.ADD, on_click=add_external_entry),
            ext_status,
        ],
        spacing=12,
    )

    # =========================================================
    #  تبويب: مراجعة وحفظ اليوم
    # =========================================================
    internal_review_list = ft.Column()
    external_review_list = ft.Column()
    review_status = ft.Text()

    def refresh_review():
        internal_review_list.controls = [
            ft.Text(f"🚛 {e['رقم اللوحة']} — {e['السائق']} — {e['البئر']} — {e['الكمية (برميل)']} برميل")
            for e in internal_entries
        ] or [ft.Text("لا توجد رحلات داخلية بعد.", italic=True)]

        external_review_list.controls = [
            ft.Text(
                f"🚚 {e['رقم اللوحة']} — {e['السائق']} — مهمة {e['رقم المهمة'] or '—'} — "
                f"صافي الوزن {e['الوزن الصافي']}"
            )
            for e in external_entries
        ] or [ft.Text("لا توجد رحلات خارجية بعد.", italic=True)]

        page.update()

    def save_all_entries(e):
        errors = []
        for entry in list(internal_entries):
            try:
                api.create_trip(entry["رقم اللوحة"], entry["السائق"], entry["البئر"], entry["الكمية (برميل)"])
                internal_entries.remove(entry)
            except Exception as ex:
                errors.append(str(ex))

        for entry in list(external_entries):
            try:
                api.create_external_trip(
                    entry["رقم اللوحة"],
                    entry["السائق"],
                    entry["رقم المهمة"],
                    entry["موقع التحميل"],
                    entry["الوزن قبل"],
                    entry["الوزن بعد"],
                    entry["الوزن الصافي"],
                    entry["الكمية (برميل)"],
                )
                external_entries.remove(entry)
            except Exception as ex:
                errors.append(str(ex))

        if errors:
            review_status.value = "تم الحفظ مع بعض الأخطاء: " + " | ".join(errors)
            review_status.color = ft.colors.RED
        else:
            review_status.value = "تم حفظ جميع رحلات اليوم بنجاح ✅"
            review_status.color = ft.colors.GREEN

        refresh_review()
        page.update()

    review_tab = ft.Column(
        [
            report_date_text,
            change_date_button,
            ft.Divider(),
            ft.Text("🚛 رحلات النقل الداخلي", size=16, weight=ft.FontWeight.BOLD),
            internal_review_list,
            ft.Divider(),
            ft.Text("🚚 رحلات النقل الخارجي", size=16, weight=ft.FontWeight.BOLD),
            external_review_list,
            ft.Divider(),
            ft.ElevatedButton(
                "💾 حفظ كل رحلات اليوم",
                icon=ft.icons.SAVE,
                on_click=save_all_entries,
                bgcolor=ft.colors.GREEN,
                color=ft.colors.WHITE,
            ),
            review_status,
        ],
        spacing=10,
    )

    # =========================================================
    #  التبويبات الرئيسية
    # =========================================================
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="🚛 نقل داخلي", content=ft.Container(internal_tab, padding=15)),
            ft.Tab(text="🚚 نقل خارجي", content=ft.Container(external_tab, padding=15)),
            ft.Tab(text="📋 مراجعة وحفظ اليوم", content=ft.Container(review_tab, padding=15)),
        ],
        expand=True,
    )

    page.add(
        ft.Text("🛢️ نظام أتمتة تقارير حقل العمر", size=24, weight=ft.FontWeight.BOLD),
        tabs,
    )

    refresh_wells()
    refresh_review()


ft.app(target=main)
