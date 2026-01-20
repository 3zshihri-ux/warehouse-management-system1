# نظام ادارة المستودع (MVP)

هذه نسخة ويب أساسية لإدارة:
- المستودعات
- الأرفف
- المعدات
- حركات الصرف/التسليم/الاستلام/التأجير/النقل

## أفضل قاعدة بيانات
المشروع مُجهّز للعمل على PostgreSQL تلقائياً عند النشر على Render.

## النشر الأسهل على Render (بدون مبرمج)
1) ارفع هذا المشروع إلى GitHub (مستودع جديد).
2) ادخل Render واختر: **New > Blueprint**
3) اختر مستودع GitHub.
4) اضغط Deploy.

### بيانات الدخول
يتم إنشاء مستخدم مدير تلقائيًا عند أول تشغيل:
- ADMIN_EMAIL (افتراضي: admin@example.com)
- ADMIN_PASSWORD (افتراضي: ChangeMe_12345)

**مهم:** غيّر القيمتين من Render Dashboard > Environment بعد النشر.

## التشغيل محلياً (اختياري)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

ثم افتح:
http://127.0.0.1:8000
