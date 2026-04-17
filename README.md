# Yamenshat API - خادم API متقدم

خادم API قوي وآمن لتطبيق Yamenshat Pro مبني باستخدام FastAPI وSQLAlchemy.

## الميزات الرئيسية

### 1. **قاعدة البيانات المحلية (SQLite)**
- ✅ نماذج بيانات كاملة باستخدام SQLAlchemy ORM
- ✅ دعم العلاقات بين الجداول (One-to-Many, Many-to-Many)
- ✅ هجرات البيانات باستخدام Alembic
- ✅ استعلامات محسّنة وفعالة

### 2. **نظام المصادقة الآمن (JWT)**
- ✅ توكنات الوصول والتحديث
- ✅ تشفير كلمات المرور باستخدام bcrypt
- ✅ التحقق من الهوية والصلاحيات
- ✅ إدارة الجلسات الآمنة

### 3. **Firebase للإشعارات الفورية**
- ✅ إرسال إشعارات فورية إلى الأجهزة
- ✅ إشعارات متعددة (Multicast)
- ✅ الاشتراك في المواضيع (Topics)
- ✅ أنواع إشعارات مختلفة (إعجاب، تعليق، رسالة، إلخ)

### 4. **API RESTful متقدم**
- ✅ مسارات كاملة للمستخدمين والمنشورات والإشعارات
- ✅ معالجة الأخطاء الشاملة
- ✅ التحقق من البيانات باستخدام Pydantic
- ✅ توثيق تفاعلي (Swagger UI)

## المتطلبات

- Python 3.8+
- pip أو uv

## التثبيت

### 1. تثبيت المكتبات

```bash
pip install -r requirements.txt
```

أو باستخدام uv:

```bash
uv pip install --system -r requirements.txt
```

### 2. إعداد متغيرات البيئة

انسخ ملف `.env.example` إلى `.env` وعدّل البيانات:

```bash
cp .env.example .env
```

ثم عدّل الملف بإضافة:
- `SECRET_KEY`: مفتاح سري قوي للتطبيق
- بيانات Firebase (اختياري)

### 3. إنشاء قاعدة البيانات

```bash
python -c "from database import init_db; init_db()"
```

## التشغيل

### في بيئة التطوير

```bash
python main.py
```

أو باستخدام uvicorn مباشرة:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### في بيئة الإنتاج

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## التوثيق

بعد تشغيل الخادم، يمكنك الوصول إلى:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## نقاط النهاية الرئيسية (Endpoints)

### المصادقة (Authentication)
- `POST /api/auth/register` - تسجيل مستخدم جديد
- `POST /api/auth/login` - تسجيل الدخول
- `POST /api/auth/refresh` - تحديث التوكن
- `POST /api/auth/change-password` - تغيير كلمة المرور
- `POST /api/auth/reset-password` - إعادة تعيين كلمة المرور
- `POST /api/auth/verify-email` - التحقق من البريد الإلكتروني
- `POST /api/auth/logout` - تسجيل الخروج

### المستخدمين (Users)
- `GET /api/users/me` - الحصول على بيانات المستخدم الحالي
- `GET /api/users/{user_id}` - الحصول على بيانات مستخدم معين
- `GET /api/users` - الحصول على قائمة المستخدمين
- `PUT /api/users/me` - تحديث بيانات المستخدم
- `POST /api/users/friends/{friend_id}` - إضافة صديق
- `DELETE /api/users/friends/{friend_id}` - إزالة صديق
- `GET /api/users/{user_id}/friends` - الحصول على قائمة الأصدقاء
- `GET /api/users/settings/me` - الحصول على إعدادات المستخدم
- `PUT /api/users/settings/me` - تحديث إعدادات المستخدم

### المنشورات (Posts)
- `POST /api/posts` - إنشاء منشور جديد
- `GET /api/posts/{post_id}` - الحصول على منشور معين
- `GET /api/posts` - الحصول على قائمة المنشورات
- `PUT /api/posts/{post_id}` - تحديث منشور
- `DELETE /api/posts/{post_id}` - حذف منشور
- `POST /api/posts/{post_id}/reactions/{reaction_type}` - إضافة تفاعل
- `DELETE /api/posts/{post_id}/reactions/{reaction_type}` - إزالة تفاعل
- `POST /api/posts/{post_id}/comments` - إضافة تعليق
- `GET /api/posts/{post_id}/comments` - الحصول على التعليقات
- `DELETE /api/posts/comments/{comment_id}` - حذف تعليق

### الإشعارات (Notifications)
- `POST /api/notifications` - إنشاء إشعار
- `GET /api/notifications` - الحصول على الإشعارات
- `GET /api/notifications/{notification_id}` - الحصول على إشعار معين
- `PUT /api/notifications/{notification_id}/read` - تحديد الإشعار كمقروء
- `PUT /api/notifications/read-all` - تحديد جميع الإشعارات كمقروءة
- `DELETE /api/notifications/{notification_id}` - حذف إشعار
- `GET /api/notifications/count/unread` - عدد الإشعارات غير المقروءة
- `POST /api/notifications/send/like` - إرسال إشعار إعجاب
- `POST /api/notifications/send/comment` - إرسال إشعار تعليق
- `POST /api/notifications/send/task-assignment` - إرسال إشعار مهمة

## أمثلة الاستخدام

### تسجيل مستخدم جديد

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "أحمد",
    "email": "ahmed@example.com",
    "password": "SecurePassword123",
    "phone_number": "+966501234567"
  }'
```

### تسجيل الدخول

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmed@example.com",
    "password": "SecurePassword123"
  }'
```

### إنشاء منشور

```bash
curl -X POST "http://localhost:8000/api/posts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "مرحباً بالجميع! 👋",
    "post_type": "text"
  }'
```

### إضافة تفاعل على منشور

```bash
curl -X POST "http://localhost:8000/api/posts/{post_id}/reactions/like" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## بنية المشروع

```
YamenshatApi/
├── main.py                 # التطبيق الرئيسي
├── config.py              # الإعدادات
├── models.py              # نماذج قاعدة البيانات
├── database.py            # إعدادات قاعدة البيانات
├── security.py            # نظام الأمان والمصادقة
├── schemas.py             # نماذج Pydantic
├── firebase_service.py    # خدمة Firebase
├── routes_auth.py         # مسارات المصادقة
├── routes_users.py        # مسارات المستخدمين
├── routes_posts.py        # مسارات المنشورات
├── routes_notifications.py # مسارات الإشعارات
├── .env.example           # مثال متغيرات البيئة
└── README.md              # هذا الملف
```

## الأمان

- ✅ تشفير كلمات المرور باستخدام bcrypt
- ✅ توكنات JWT آمنة
- ✅ التحقق من الهوية على كل طلب
- ✅ معالجة الأخطاء الآمنة
- ✅ CORS محسّن
- ✅ التحقق من البيانات الكامل

## الأداء

- ✅ استعلامات محسّنة
- ✅ تخزين مؤقت (Caching) قابل للتوسع
- ✅ معالجة متزامنة (Async)
- ✅ دعم عدة عمال (Workers)

## المساهمة

نرحب بمساهماتك! يرجى:

1. عمل Fork للمشروع
2. إنشاء فرع للميزة الجديدة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add some AmazingFeature'`)
4. Push إلى الفرع (`git push origin feature/AmazingFeature`)
5. فتح Pull Request

## الترخيص

هذا المشروع مرخص تحت MIT License - انظر ملف LICENSE للتفاصيل.

## الدعم

للمساعدة والدعم، يرجى:

- فتح Issue على GitHub
- التواصل عبر البريد الإلكتروني
- مراجعة التوثيق الكاملة

## الشكر والتقدير

شكر خاص لجميع المساهمين والمستخدمين الذين يدعمون هذا المشروع.

---

**تم التطوير بـ ❤️ بواسطة فريق Yamenshat**
