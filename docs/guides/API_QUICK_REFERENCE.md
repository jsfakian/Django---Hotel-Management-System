# NEPHELE HMS - REST API Quick Reference Guide

**Generated:** February 19, 2026  
**API Version:** v1  
**Status:** Core Infrastructure Ready (ViewSets Implementation Pending)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /path/to/Django---Hotel-Management-System
pip install -r requirements.txt
```

### 2. Environment Setup
Create `.env` file in project root:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.sqlite3  # or postgresql for production
DB_NAME=db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Run Migrations
```bash
cd HMS
python manage.py migrate
```

### 4. Start Development Server
```bash
python manage.py runserver
```

### 5. Access API Documentation
Open browser: `http://localhost:8000/api/v1/docs/swagger/`

---

## 📊 API Architecture

```
Base URL: http://localhost:8000/api/v1/

Structure:
├── /auth/              - Authentication endpoints
├── /users/             - User management
├── /properties/        - Hotel properties
├── /rooms/             - Room management
├── /bookings/          - Booking management
├── /guests/            - Guest information
├── /payments/          - Payment processing
├── /invoices/          - Invoice management
├── /contracts/         - Contract management
├── /pricing/           - Pricing & demand data
├── /tasks/             - Task management
├── /notifications/     - Notification system
└── /schema/            - OpenAPI schema
```

---

## 🔐 Authentication

### Get Access Token
```bash
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "strongpassword123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Token Lifespan
- **Access Token:** 1 hour
- **Refresh Token:** 30 days

### Refresh Token
```bash
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}

Response:
{
  "access": "new-access-token"
}
```

### Use in Requests
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 📋 Model-Endpoint Mapping

| Model | Status | Endpoint | Serializers |
|-------|--------|----------|-------------|
| **Property** | Ready | `/properties/` | PropertySerializer, PropertyDetailSerializer |
| **Room** | Ready | `/rooms/` | RoomBasicSerializer, RoomDetailedSerializer |
| **Booking** | Ready | `/bookings/` | BookingSerializer, BookingDetailedSerializer |
| **Guest** | Ready | `/guests/` | GuestSerializer |
| **Employee** | Ready | `/employees/` | EmployeeSerializer |
| **Task** | Ready | `/tasks/` | TaskSerializer |
| **Payment** | Ready | `/payments/` | PaymentSerializer, PaymentDetailedSerializer |
| **Invoice** | Ready | `/invoices/` | InvoiceSerializer |
| **Refund** | Ready | `/refunds/` | RefundRequestSerializer |
| **Contract** | Ready | `/contracts/` | ContractSerializer, ContractDetailedSerializer |
| **TravelAgency** | Ready | `/travel-agencies/` | TravelAgencySerializer |
| **Pricing** | Ready | `/pricing-history/` | PricingHistorySerializer |
| **Forecast** | Ready | `/forecasts/` | DemandForecastSerializer |
| **Notification** | Ready | `/notifications/` | NotificationSerializer |

---

## 🎯 Key Features Implemented

### Per Task 4 System Architecture:

✅ **Security**
- JWT authentication (SimplJWT)
- PBKDF2 password hashing (12+ characters required)
- CORS enabled for frontend integration
- SSL/TLS ready
- GDPR-compliant logging

✅ **API Features**
- REST endpoints with HTTP verbs
- OpenAPI/Swagger documentation
- Pagination (50 items per page)
- Filtering & searching
- Request/response standardization

✅ **Database**
- PostgreSQL support (recommended)
- Proper indexing on frequently queried fields
- Unique constraints for data integrity
- Foreign key relationships
- Migration framework ready

✅ **Error Handling**
- Standardized error response format
- Meaningful error codes
- Detailed error messages
- Request tracking via request_id

✅ **Logging**
- Structured logging to files
- Log rotation (10MB max per file)
- Error tracking integration ready (Sentry)
- Request/response logging

---

## 📝 Response Format Standard

### Success Response (HTTP 200/201)
```json
{
  "data": {
    "id": 1,
    "name": "Room 101",
    "property": 1,
    "...": "..."
  },
  "meta": {
    "timestamp": "2026-02-19T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### List Response (HTTP 200)
```json
{
  "data": [
    {"id": 1, "...": "..."},
    {"id": 2, "...": "..."}
  ],
  "pagination": {
    "count": 100,
    "next_page": 2,
    "previous_page": null,
    "page_size": 50
  },
  "meta": {
    "timestamp": "2026-02-19T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Response (HTTP 4xx/5xx)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  },
  "meta": {
    "timestamp": "2026-02-19T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## 🔗 Role-Based Access Control (RBAC)

### Roles Defined:
- **admin** - Full system access
- **hotel_manager** - Property management, staff, pricing, reports
- **receptionist** - Booking, guest check-in/out
- **travel_agent** - Booking creation, contracts viewing
- **employee** - Basic access based on assignment
- **guest** - Own booking view only

### Implementation:
- JWT payload includes user role
- Permissions stored as JSON in Role model
- Permission checking via decorators/middleware (to be implemented)

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Test a Specific App
```bash
pytest HMS.tests
```

### Test Configuration
- Framework: pytest
- Fixtures: Factory Boy
- Mock Data: Faker
- Target Coverage: 80%+

---

## 📚 Database Schema Highlights

### Key Entities:

**Properties (Hotels)**
- Name, location, address, contact info
- Manager assignment
- Star rating (1-5)
- Available rooms calculation

**Rooms**
- Room number, floor, type, capacity
- Current and base pricing
- Amenities as JSON
- Status tracking

**Bookings**
- Check-in/check-out dates
- Guest and room references
- Travel agency (for commission)
- Pricing (base + actual for dynamic pricing)
- Special requests and notes

**Guests**
- Full profile information
- Preferences as JSON (for personalization)
- Booking statistics
- Contact information

**Pricing Data** (for ML)
- Daily pricing history
- Occupancy rates
- Demand scores
- Competitor pricing
- ML model metadata

**Contracts**
- Property-TravelAgency agreements
- Commission percentage
- Allocation terms (guarantee/allotment)
- Status workflow
- Digital signature support

---

## 🚨 Common Issues & Solutions

### Issue: CORS Error When Calling API from Frontend
**Solution:**
```python
# Check HMS/settings.py - ensure frontend URL in CORS_ALLOWED_ORIGINS:
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React dev server
    'http://localhost:8000',
]
```

### Issue: Database Connection Error
**Solution:**
```bash
# Ensure PostgreSQL is running, or use SQLite for development:
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### Issue: Token Expired Error (401)
**Solution:**
```javascript
// Implement token refresh in frontend:
const response = await fetch('/api/v1/auth/refresh/', {
  method: 'POST',
  body: JSON.stringify({ refresh: refreshToken }),
  headers: { 'Content-Type': 'application/json' }
});
```

### Issue: Serializer Data Not Returning Expected Fields
**Solution:**
- Check model has the field
- Verify serializer includes field in `fields` list
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`

---

## 🎓 Frontend Integration Steps

### 1. Install Frontend Dependencies
```bash
npm install axios
# or
yarn add axios
```

### 2. Create API Client
```javascript
// src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1/',
  timeout: 30000,
});

// Add token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Refresh token and retry
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 3. Create Services for Each Resource
```javascript
// src/api/properties.js
import api from './client';

export const getProperties = () => api.get('/properties/');
export const getProperty = (id) => api.get(`/properties/${id}/`);
export const createProperty = (data) => api.post('/properties/', data);
export const updateProperty = (id, data) => api.put(`/properties/${id}/`, data);
export const deleteProperty = (id) => api.delete(`/properties/${id}/`);
```

### 4. Use in React Components
```javascript
import { useEffect, useState } from 'react';
import { getProperties } from '../api/properties';

function PropertyList() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProperties()
      .then(response => setProperties(response.data.data))
      .catch(error => console.error(error))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  return (
    <ul>
      {properties.map(prop => <li key={prop.id}>{prop.name}</li>)}
    </ul>
  );
}
```

---

## 📞 Support

### Documentation Files:
- `ALIGNMENT_IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `DELIVERABLES-Task4-SystemArchitecture.md` - Architecture specs
- `tasks/phase-2-development/task-5a-backend-core.md` - Development roadmap

### Next Steps:
1. Implement ViewSets for all models
2. Add business logic and validations
3. Integrate with payment gateways
4. Deploy to staging environment
5. Frontend integration testing

---

**Last Updated:** February 19, 2026  
**Status:** Infrastructure Ready ✅  
**Next Phase:** ViewSet Implementation (Task 5a Sprint 5+)
