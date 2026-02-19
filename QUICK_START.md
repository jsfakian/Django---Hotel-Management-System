# Quick Start Guide - New Features

## 🚀 Getting Started

### 1. Apply Migrations
```bash
cd HMS
python manage.py migrate
```

### 2. Create Initial Data

#### Create Payment Methods
```python
python manage.py shell

from payments.models import PaymentMethod

PaymentMethod.objects.bulk_create([
    PaymentMethod(name='Credit Card', payment_type='card', is_active=True, requires_verification=True),
    PaymentMethod(name='Debit Card', payment_type='card', is_active=True, requires_verification=True),
    PaymentMethod(name='Cash', payment_type='cash', is_active=True, requires_verification=False),
    PaymentMethod(name='Bank Transfer', payment_type='bank_transfer', is_active=True, requires_verification=False),
])
```

#### Create Notification Types
```python
from notifications.models import NotificationType

NotificationType.objects.bulk_create([
    NotificationType(code='booking_created', name='Booking Created'),
    NotificationType(code='booking_confirmed', name='Booking Confirmed'),
    NotificationType(code='booking_cancelled', name='Booking Cancelled'),
    NotificationType(code='payment_received', name='Payment Received'),
    NotificationType(code='payment_failed', name='Payment Failed'),
    NotificationType(code='payment_verified', name='Payment Verified'),
    NotificationType(code='refund_processed', name='Refund Processed'),
    NotificationType(code='room_service_request', name='Room Service Request'),
    NotificationType(code='room_service_completed', name='Room Service Completed'),
    NotificationType(code='checkin_reminder', name='Check-in Reminder'),
    NotificationType(code='checkout_reminder', name='Check-out Reminder'),
    NotificationType(code='invoice_generated', name='Invoice Generated'),
])
```

### 3. Test the System

#### Create a Property
```python
from properties.models import Property

property = Property.objects.create(
    name='Grand Hotel',
    location='Downtown',
    address='123 Main St',
    city='Paris',
    postal_code='75001',
    country='France',
    phone_number='+33123456789',
    email='hotel@example.com',
    total_rooms=50,
    star_rating=5
)
```

#### Send a Test Notification
```python
from notifications.services import NotificationService
from django.contrib.auth.models import User

user = User.objects.first()  # Get any user

NotificationService.send_notification(
    user=user,
    notification_type_code='booking_created',
    title='Welcome!',
    message='Your booking has been created successfully.',
    priority='high',
    icon='📅'
)
```

---

## 📍 Access New Features

### Properties Management
- **URL**: `/properties/`
- **Roles**: Admin, Manager, Receptionist, Staff, Guest
- **Admin Panel**: Django Admin → Properties → Property

### Payment Processing
- **URL**: `/payments/process/`
- **Payment History**: `/payments/history/`
- **Invoices**: `/payments/invoices/`
- **Admin Panel**: Django Admin → Payments → Payment

### Notifications
- **URL**: `/notifications/`
- **Preferences**: `/notifications/preferences/`
- **Admin Panel**: Django Admin → Notifications → Notification

---

## 🔐 Role-Based Access Examples

### Using Decorators
```python
from accounts.permissions import require_role, require_permission

@require_role('admin', 'manager')
def my_view(request):
    # Only admin or manager can access
    pass

@require_permission('manage_properties')
def another_view(request):
    # Only users with 'manage_properties' permission
    pass
```

### Checking in Views
```python
from accounts.permissions import has_role, has_permission, get_user_role

def my_view(request):
    role = get_user_role(request.user)
    
    if has_role(request.user, 'admin', 'manager'):
        # Show admin/manager options
        pass
    
    if has_permission(request.user, 'manage_bookings'):
        # Show booking management
        pass
```

### In Templates
```html
{% if user_role == 'admin' %}
    <a href="/admin/">Admin Panel</a>
{% endif %}

{% if 'manage_properties' in user_permissions %}
    <a href="/properties/create/">Create Property</a>
{% endif %}
```

---

## 📧 Email Configuration

To enable email notifications, configure in `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your email provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

---

## 💳 Payment Flow

1. **Guest initiates payment** → `/payments/process/`
2. **Payment method selected** → PaymentMethod choice
3. **If verification required** → Verification code sent to email
4. **Payment verified** → `/payments/verify/<id>/`
5. **Payment confirmed** → `/payments/success/<id>/`
6. **Invoice auto-generated** → Available at `/payments/invoices/`

---

## 🔔 Notification Flow

1. **Event occurs** (booking, payment, etc.)
2. **Notification service called** → `NotificationService.send_notification()`
3. **User preferences checked** → Delivery channels determined
4. **Notification sent**:
   - In-app notification created immediately
   - Email sent if user has it enabled
   - SMS sent if provider configured
5. **User receives notification** → `/notifications/`

---

## 🗂️ Project Structure

```
HMS/
├── properties/              # NEW: Property management
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── payments/                # NEW: Payment processing
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── services.py
├── notifications/           # NEW: Notification engine
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── services.py
├── accounts/                # ENHANCED: Role-based access
│   ├── permissions.py       # NEW
│   ├── context_processors.py # NEW
│   └── ...
├── room/                    # ENHANCED: Property link added
│   ├── models.py
│   └── ...
└── HMS/
    ├── settings.py          # UPDATED: New apps registered
    ├── urls.py              # UPDATED: New URLs included
    └── ...
```

---

## 🧪 Testing

### Test Payment Creation
```python
from payments.models import Payment, PaymentMethod
from accounts.models import Guest

guest = Guest.objects.first()
method = PaymentMethod.objects.first()

payment = Payment.objects.create(
    guest=guest,
    payment_method=method,
    amount=100.00,
    currency='EUR',
    transaction_id='TXN-TEST-001',
    reference_code='REF-TEST-001'
)
```

### Test Notification
```python
from notifications.models import Notification, NotificationType

notification_type = NotificationType.objects.first()
user = User.objects.first()

notification = Notification.objects.create(
    user=user,
    notification_type=notification_type,
    title='Test',
    message='Test message',
    priority='high'
)
```

---

## 📊 Admin Features

### Properties Admin
- Search by name, city, country
- Filter by star rating, active status
- Bulk operations
- Custom list display with room count

### Payments Admin
- Track payment status in real-time
- View transaction history
- Process refunds
- Monitor verification codes

### Notifications Admin
- View all notifications
- Filter by user, status, type
- Track delivery (email, SMS)
- Monitor notification log

---

## ⚙️ Configuration

### Notification Frequency
- Immediate - Send as soon as event occurs
- Daily - Send daily digest at configured time
- Weekly - Send weekly digest
- Never - Disable notifications

### Quiet Hours
```python
# In notification preferences
quiet_hours_enabled = True
quiet_hours_start = "22:00"  # 10 PM
quiet_hours_end = "08:00"    # 8 AM
```

### Payment Verification
```python
# In PaymentMethod
requires_verification = True  # Sends verification code
requires_verification = False # Instant payment
```

---

## 🐛 Debugging

### Check System
```bash
python manage.py check
```

### Create Migrations
```bash
python manage.py makemigrations
```

### View Database
```bash
python manage.py dbshell
```

### Create Superuser
```bash
python manage.py createsuperuser
```

---

## 📞 Support

For issues or questions:
1. Check Django logs
2. Review model documentation in admin panel
3. Test endpoints with curl or Postman
4. Check notification logs in admin

---

## ✅ Checklist for Deployment

- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Initialize payment methods
- [ ] Initialize notification types
- [ ] Configure email settings
- [ ] Configure SMS provider (optional)
- [ ] Test payment flow
- [ ] Test notifications
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set SECRET_KEY in environment

---

Generated on: February 19, 2026
