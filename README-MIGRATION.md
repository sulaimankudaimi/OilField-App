# تعليمات ترحيل المشروع إلى هيكلة backend / frontend

## 1) شجرة المجلدات النهائية

```
OilField-App/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── main.py
│   ├── client_api.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── assets/
├── .github/
│   └── workflows/
│       └── build-apk.yml
└── README-MIGRATION.md
```

## 2) كيفية رفع التحديث على GitHub

في جذر مستودعك المحلي (بعد استبدال الملفات القديمة بهذه الملفات):

```bash
# احذف الملفات القديمة من الجذر إن كانت main.py / requirements.txt موجودة هناك
git rm -f main.py requirements.txt 2>/dev/null || true
# احذف أي ملف واجهة Streamlit قديم من الجذر إن وُجد (استبدل الاسم الفعلي)
git rm -f app.py 2>/dev/null || true

# انسخ الملفات الجديدة من هذا الحزمة إلى جذر مستودعك بنفس المسارات
# (backend/, frontend/, .github/workflows/build-apk.yml)

git add backend frontend .github
git commit -m "إعادة هيكلة المشروع إلى backend/frontend وتحويل الواجهة من Streamlit إلى Flet"
git push origin main
```

بعد الدفع (push)، سيعمل الـ workflow تلقائياً على أي تعديل داخل `frontend/`، أو يمكنك تشغيله يدوياً من تبويب Actions عبر "Run workflow" (بفضل `workflow_dispatch`).

## 3) ما يجب تغييره في إعدادات Render

من لوحة تحكم Render → اختر خدمتك → **Settings**:

| الإعداد | القيمة الجديدة |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

تأكد أن متغير البيئة `DATABASE_URL` (رابط PostgreSQL) لا يزال مضبوطاً في تبويب **Environment**.

بعد الحفظ، اضغط **Manual Deploy → Deploy latest commit** لتطبيق التغييرات.

## 4) قبل استخدام تطبيق الجوال فعلياً

في ملف `frontend/client_api.py` غيّر:

```python
BASE_URL = "https://YOUR-RENDER-APP.onrender.com"
```

إلى رابط خدمتك الفعلي على Render (يظهر أعلى صفحة الخدمة في لوحة التحكم).

## 5) ملاحظة مهمة حول محتوى الواجهة

ملف `frontend/main.py` المرفق هنا هو **هيكل Flet كامل وقابل للتشغيل فوراً** (نموذج إضافة رحلة + عرض مؤشرات الأداء)، لكنه لا يغطي بالضرورة كل الشاشات التي كانت موجودة في تطبيق Streamlit الأصلي (مثل التقارير PDF عبر reportlab، الرسوم البيانية عبر plotly، أو تصدير Excel عبر openpyxl).

لتحويل تلك الأجزاء بدقة، أرسل لي كود ملف الواجهة الأصلي (Streamlit) وسأحوّله سطراً بسطر إلى مكوّنات Flet المكافئة. أما الحزم الإضافية (plotly, pandas, openpyxl, arabic-reshaper, reportlab) فأضفها إلى `frontend/requirements.txt` فقط إن كانت الواجهة (وليس الخادم) هي من يستخدمها فعلياً.
