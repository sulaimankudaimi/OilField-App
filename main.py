import flet as ft

def main(page: ft.Page):
    # إعدادات الصفحة الأساسية
    page.title = "نظام حقل العمر"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True # تفعيل دعم اللغة العربية من اليمين لليسار
    page.window_width = 400
    page.window_height = 800

    # دالة زر الحفظ
    def save_data(e):
        if plate_input.value == "":
            page.snack_bar = ft.SnackBar(ft.Text("يرجى إدخال رقم اللوحة!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
        else:
            # هنا سيتم لاحقاً إرسال البيانات عبر API
            page.snack_bar = ft.SnackBar(ft.Text(f"تم حفظ بيانات اللوحة: {plate_input.value}"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
        page.update()

    # مكونات الواجهة
    title = ft.Text("📊 لوحة قياس الأداء اليومي", size=24, weight=ft.FontWeight.BOLD)
    
    # بطاقة مؤشر أداء (KPI)
    kpi_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("إجمالي النقل اليوم", size=16),
                ft.Text("1,250 برميل", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=300,
        )
    )

    plate_input = ft.TextField(label="رقم اللوحة", width=300, text_align=ft.TextAlign.RIGHT)
    save_btn = ft.ElevatedButton("💾 حفظ السجل", on_click=save_data, width=300)

    # ترتيب المكونات في الشاشة
    page.add(
        ft.Column([
            title,
            ft.Divider(),
            kpi_card,
            ft.Divider(),
            ft.Text("تسجيل رحلة جديدة:", size=18),
            plate_input,
            save_btn
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

# تشغيل التطبيق
ft.app(target=main)