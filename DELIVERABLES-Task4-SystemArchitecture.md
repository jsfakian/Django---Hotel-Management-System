# NEPHELE Hotel Management System - System Architecture & Design Report
## Deliverable: ПА.04-01

**Document ID:** ПА.04-01  
**Project:** NEPHELE Hotel Management System  
**Phase:** Phase 2 - Design & Development  
**Date:** February 20, 2026  
**Status:** COMPLETED (Validated against implementation)  
**Prepared by:** Architecture & Technical Design Team  

---

## EXECUTIVE SUMMARY

### Design Objective
Define the complete technical architecture for NEPHELE, transforming business requirements from Phase 1 research into detailed technical blueprints and specifications. This document serves as the foundation for development teams in Phase 2 (Task 5).

### Key Design Decisions

#### Architectural Approach
- **Pattern:** Monolithic architecture (Phase 2) with microservices migration path (Year 3+)
- **Deployment:** Cloud-native SaaS with containerization (Docker)
- **Scalability:** Horizontal scaling for stateless services; PostgreSQL replication for data layer
- **Technology Stack Validation:** Django + PostgreSQL + React validated as optimal for SMB market

#### System Composition
The system consists of 4 primary layers:
1. **Presentation Layer** - REST APIs, Web Frontend, Admin Console
2. **Application Layer** - Core services and business logic
3. **Data Layer** - PostgreSQL, Redis caching, file storage
4. **Integration Layer** - External APIs, payment gateways, email services

#### Design Highlights
✅ **Security-First Design:** Role-based access control (RBAC), encryption at rest/transit, audit logging  
✅ **API-First Architecture:** REST APIs with OpenAPI/Swagger documentation  
✅ **Performance Optimized:** Multi-level caching (Redis), indexed database queries, async processing  
✅ **Scalability Ready:** Load balancing, database replication, horizontal service scaling  
✅ **GDPR Compliant:** Data privacy controls, encryption, audit trails, right-to-deletion  

### Key Deliverables (This Document)

| Deliverable | Status | Description |
|-------------|--------|-------------|
| System Architecture Design | ✅ Complete | High-level system structure and components |
| Data Model & Schema Design | ✅ Complete | Complete database schema with relationships |
| API Specifications | ✅ Complete | REST API endpoints and contract definitions |
| Security Architecture | ✅ Complete | Authentication, authorization, encryption, compliance |
| Integration Architecture | ✅ Complete | External systems, payment gateways, email, notifications |
| Automated Reporting & Scheduling | ✅ Complete | Scheduled reports, email delivery, report generation |
| Deployment Architecture | ✅ Complete | Cloud infrastructure, containerization, CI/CD pipeline |
| Scalability & Performance Design | ✅ Complete | Caching strategy, optimization, capacity planning |

### Recommendations for Development Team

1. **Code Generation:** Use Django model-driven development and OpenAPI code generation
2. **Database Migrations:** Implement strict version control for schema changes with Django migrations
3. **API Documentation:** Auto-generate from OpenAPI/Swagger specs; maintain 100% API coverage
4. **Testing Strategy:** Unit tests (80%+ coverage), integration tests for all services, API contract tests
5. **Performance Baseline:** Establish metrics: API response <200ms (p95), database <100ms (p95)

### Implementation Validation Addendum (February 20, 2026)

Architecture-to-code conformance validation and closure actions completed:

1. **API-first architecture completed**
  - Central API router now exposes core domains: properties, travel agencies, rooms, bookings, contracts, payments, invoices, refunds, notifications, analytics.
  - JWT auth and OpenAPI schema remain active under `/api/v1/`.

2. **Contract subsystem corrected and connected**
  - Contract API endpoints aligned with actual data model fields.
  - Signing workflow mapped to property and agency signatures using model methods.
  - Contract routes mounted in root URL configuration.

3. **Analytics platform startup blockers removed**
  - Forecast serializer field definitions corrected.
  - Forecasting model references fixed to use canonical booking model.
  - Role checks aligned to Django group-based RBAC.

4. **Task 3 pricing training pipeline repaired**
  - Feature engineering now guarantees `available_binary` availability.
  - Trainer handles absent optional numeric features with safe defaults.
  - Smoke test confirms feature-preparation path executes successfully.

5. **Current residual technical debt (non-blocking for Task 4 acceptance)**
  - Django emits `DEFAULT_AUTO_FIELD` warnings across legacy models.
  - Standardization task is queued for a dedicated migration cycle.

---

## 1. SYSTEM ARCHITECTURE DESIGN

### 1.1 Architectural Overview

#### System Layers

```
┌────────────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web UI     │  │  Mobile API  │  │  Admin       │         │
│  │  (React)     │  │  (REST)      │  │  Console     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────┬────────────────────────────────────────────┬──────────┘
         │                                            │
┌────────▼────────────────────────────────────────────▼──────────┐
│          API GATEWAY & LOAD BALANCING                          │
│  (Nginx/HAProxy - Request routing, rate limiting, SSL)         │
└────────┬────────────────────────────────────────────┬──────────┘
         │                                            │
┌────────▼──────────────────────────────────────────────▼────────┐
│           APPLICATION SERVICES LAYER (Django)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Authentication Service  │  Contract Management Service    │  │
│  │ Booking Service         │  Pricing Service (ML Engine)    │  │
│  │ Payment Processing      │  Notification Service           │  │
│  │ Guest Management        │  Analytics & BI Engine          │  │
│  │ Reporting Service       │  Integration Service            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Async Processing Layer (Celery)                         │  │
│  │  - Price optimization jobs                               │  │
│  │  - Email/notification dispatch                           │  │
│  │  - Report generation                                     │  │
│  │  - Data synchronization                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬──────────────────────────────────────────────┬────────┘
         │                                              │
┌────────▼──────────────────┬─────────────────────────▼────────┐
│      DATA LAYER           │    INTEGRATION LAYER              │
│ ┌──────────────────────┐  │ ┌──────────────────────────────┐ │
│ │ PostgreSQL           │  │ │ Payment Gateways (Stripe)    │ │
│ │ (Primary Database)   │  │ │ Email Service (SendGrid)     │ │
│ │                      │  │ │ SMS Service (Twilio)         │ │
│ │ Redis Cache          │  │ │ OTA Integration APIs         │ │
│ │ (Performance Layer)   │  │ │ Analytics Platforms          │ │
│ │                      │  │ │ Accounting Systems           │ │
│ │ S3/Cloud Storage     │  │ │ (QuickBooks/Odoo)           │ │
│ │ (Documents/Media)    │  │ │ Office 365/Google Workspace │ │
│ └──────────────────────┘  │ └──────────────────────────────┘ │
└────────────────────────────┴──────────────────────────────────┘
```

#### Architectural Characteristics

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Architecture Pattern** | Monolithic (Layer-based) | Simpler deployment, sufficient for Phase 2 (<1000 customers) |
| **Deployment Model** | Cloud SaaS (Multi-tenant) | Cost-effective, auto-scaling, automatic updates |
| **Database Model** | Relational (PostgreSQL) | ACID compliance, complex queries, data integrity critical |
| **API Style** | REST (OpenAPI) | Industry standard, easy integration, well-tooled |
| **Communication** | HTTP/HTTPS + WebSockets | REST for stateless operations, WebSockets for real-time updates |
| **Async Processing** | Celery + Redis | Decouples long-running tasks, improves API responsiveness |
| **Caching Strategy** | Multi-level caching | API response caching, query result caching, session caching |
| **File Storage** | Cloud S3-compatible | Scalable, secure document management, automatic backups |

### 1.2 Component Architecture

#### Core Service Components

| Service | Technology | Purpose | Key Responsibilities | Scaling |
|---------|-----------|---------|----------------------|---------|
| **API Server** | Django REST Framework | REST API endpoints for all operations | Request routing, validation, authorization | Horizontal (stateless) |
| **Authentication** | Django Auth + JWT | User identity and session management | Login, token generation, session validation | Horizontal |
| **Booking Service** | Django ORM + PostgreSQL | Reservation management and occupancy | Booking CRUD, availability checking, calendar management | Horizontal |
| **Pricing Engine** | Python/TensorFlow | ML-based dynamic pricing | Price optimization, competitor analysis, demand forecasting | Vertical initially, Horizontal (Year 3) |
| **Payment Service** | Stripe/PayPal integration | Payment processing and reconciliation | Payment processing, invoicing, reconciliation, refunds | Horizontal |
| **Notification Service** | Celery + SendGrid | Email/SMS notifications | Email dispatch, SMS delivery, notification history | Horizontal |
| **Contract Manager** | Django ORM | Travel agency contracts | Contract CRUD, validity checking, commission calculations | Horizontal |
| **Reporting Engine** | Metabase + Python | BI dashboards and reports | Report generation, data aggregation, analytics | Horizontal |
| **File Manager** | S3 SDK | Document and media storage | Upload, download, archival, virus scanning | Scalable object storage |
| **Integration Hub** | API clients library | External system integration | OTA integration, accounting system sync, data import/export | Horizontal |

#### Service Dependencies

```
Booking Service ──→ Pricing Engine
       │               │
       ├──→ Payment Service
       │               │
       └──→ Notification Service
              │
              └──→ Contract Manager

Guest Management ──→ Notification Service
       │
       └──→ File Manager

Reporting Engine ←─ All Services (aggregates data)
```

---

## 2. DATA MODEL & DATABASE SCHEMA

### 2.1 Entity Relationship Diagram

#### Core Data Entities

```
┌─────────────────┐
│      Users      │ (Authentication & Authorization)
├─────────────────┤
│ id (PK)         │
│ email (unique)  │
│ password_hash   │
│ first_name      │
│ last_name       │
│ role            │◄──┐
│ is_active       │   │
│ created_at      │   │
└─────────────────┘   │
        ▲             │ (1:M)
        │             │
        │ (1:M)       │
        │             ▼
┌─────────────────┐  ┌──────────────────┐
│   Employees     │  │  Roles            │
├─────────────────┤  ├──────────────────┤
│ id (PK)         │  │ id (PK)           │
│ user_id (FK)    │  │ name              │
│ property_id (FK)│  │ permissions (JSON)│
│ position        │  │ description       │
│ hire_date       │  └──────────────────┘
│ status          │
└─────────────────┘
        ▲
        │ (1:M)

┌─────────────────────┐
│    Properties       │ (Hotels/Accommodations)
├─────────────────────┤
│ id (PK)             │
│ name                │
│ description         │
│ address             │
│ city                │
│ country             │
│ phone               │
│ email               │
│ website             │
│ rooms_count         │
│ manager_id (FK)     │◄──────┐
│ created_at          │       │ (1:M)
└─────────────────────┘       │
        ▲                      │
        │ (1:M)               │
        │                     │
┌───────┴──────────────┐  ┌──────────────┐
│        Rooms         │  │  TravelAgency│
├──────────────────────┤  ├──────────────┤
│ id (PK)              │  │ id (PK)      │
│ property_id (FK)     │  │ name         │
│ room_number          │  │ contact_name │
│ floor                │  │ email        │
│ room_type            │  │ phone        │
│ capacity             │  │ address      │
│ amenities (JSON)     │  │ city         │
│ status               │  │ commission % │
│ created_at           │  │ created_at   │
└───────┬──────────────┘  └──────────────┘
        ▲                       ▲
        │ (1:M)                 │ (1:M)
        │                       │
        │         ┌─────────────┤
        │         │             │
        │    ┌────▼──────────────┴─┐
        │    │    Bookings        │
        │    ├────────────────────┤
        │    │ id (PK)            │
        │    │ room_id (FK)       │
        │    │ guest_id (FK)      │
        │    │ travel_agency_id (FK)
        │    │ check_in           │
        │    │ check_out          │
        │    │ status             │
        │    │ price              │
        │    │ number_of_guests   │
        │    │ notes              │
        │    │ created_at         │
        │    └────────────────────┘
        │            ▲
        └────────────┤ (M:1)
                     │
            ┌────────┴─────────┐
            │                  │
        ┌───▼────────┐  ┌──────▼──────┐
        │   Guests   │  │  Invoices   │
        ├────────────┤  ├─────────────┤
        │ id (PK)    │  │ id (PK)     │
        │ email      │  │ booking_id  │
        │ first_name │  │ date        │
        │ last_name  │  │ amount      │
        │ phone      │  │ status      │
        │ address    │  │ paid_date   │
        │ preferences│  │ created_at  │
        │ created_at │  └─────────────┘
        └────────────┘
             ▲
             │ (1:M)
             │
        ┌────┴─────────┐
        │              │
    ┌───▼────────┐  ┌──▼────────────┐
    │  Payments  │  │ Contracts      │
    ├────────────┤  ├────────────────┤
    │ id (PK)    │  │ id (PK)        │
    │invoice_id  │  │ agency_id (FK) │
    │ method     │  │ property_id(FK)│
    │ amount     │  │ start_date     │
    │ status     │  │ end_date       │
    │ ref_number │  │ terms (JSON)   │
    │ date       │  │ commission_%   │
    │ created_at │  │ status         │
    └────────────┘  │ created_at     │
                    └────────────────┘

┌─────────────────────────┐
│   PricingHistory        │ (For ML Algorithm)
├─────────────────────────┤
│ id (PK)                 │
│ room_id (FK)            │
│ date                    │
│ base_price              │
│ dynamic_price           │
│ competitor_price        │
│ occupancy_rate          │
│ demand_score            │
│ season                  │
│ weekday                 │
│ created_at              │
└─────────────────────────┘

┌─────────────────────────┐
│   Notifications         │
├─────────────────────────┤
│ id (PK)                 │
│ recipient_id (FK)       │
│ type (email/SMS)        │
│ subject                 │
│ body                    │
│ status (pending/sent)   │
│ sent_at                 │
│ created_at              │
└─────────────────────────┘
```

### 2.2 Database Schema Details

#### Key Tables & Indexes

**Users Table**
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL REFERENCES roles(name),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Bookings Table**
```sql
CREATE TABLE bookings (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms(id),
    guest_id BIGINT NOT NULL REFERENCES guests(id),
    travel_agency_id BIGINT REFERENCES travel_agencies(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    base_price DECIMAL(10,2) NOT NULL,
    actual_price DECIMAL(10,2),
    number_of_guests INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bookings_room_id ON bookings(room_id);
CREATE INDEX idx_bookings_guest_id ON bookings(guest_id);
CREATE INDEX idx_bookings_check_in_out ON bookings(check_in, check_out);
CREATE INDEX idx_bookings_status ON bookings(status);
```

**PricingHistory Table** (For ML Algorithm)
```sql
CREATE TABLE pricing_history (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms(id),
    date DATE NOT NULL,
    base_price DECIMAL(10,2),
    dynamic_price DECIMAL(10,2),
    competitor_price DECIMAL(10,2),
    occupancy_rate DECIMAL(5,2),
    demand_score DECIMAL(5,2),
    season VARCHAR(20),
    weekday INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_pricing_history_room_date ON pricing_history(room_id, date);
CREATE INDEX idx_pricing_history_date ON pricing_history(date);
```

### 2.3 Data Integrity & Constraints

- **Referential Integrity:** Foreign key constraints enforced at database level
- **Check Constraints:** Price > 0, check_out > check_in, valid status values
- **Unique Constraints:** Email (users), room_number per property, contact email (agencies)
- **Not Null Constraints:** Essential fields (email, property name, room number, etc.)

---

## 3. API DESIGN SPECIFICATIONS

### 3.1 API Architecture

#### Principles
- **RESTful Design:** Standard HTTP methods (GET, POST, PUT, DELETE)
- **Stateless:** All state information in requests/responses
- **OpenAPI Compliant:** Machine-readable API contracts
- **Versioning:** URI-based versioning (/api/v1/, /api/v2/)
- **Pagination:** Offset/limit for all list endpoints
- **Error Handling:** Consistent error response format with codes

#### Base URL Structure
```
Production:    https://api.nephele.io/api/v1/
Staging:       https://staging-api.nephele.io/api/v1/
Development:   http://localhost:8000/api/v1/
```

### 3.2 Core API Endpoints

#### Authentication Endpoints

```
POST   /auth/login
  Request: { email, password }
  Response: { access_token, refresh_token, expires_in }

POST   /auth/logout
  Headers: Authorization: Bearer <token>

POST   /auth/refresh
  Request: { refresh_token }
  Response: { access_token, expires_in }

POST   /auth/register
  Request: { email, password, first_name, last_name, role }
  Response: { user_id, email, role }

POST   /auth/forgot-password
  Request: { email }
  Response: { message: "Password reset email sent" }
```

#### Booking Management Endpoints

```
GET    /bookings
  Query: ?property_id=1&status=confirmed&check_in_from=2026-03-01
  Response: { count, next, previous, results: [booking] }

POST   /bookings
  Request: { room_id, guest_id, check_in, check_out, ... }
  Response: { id, status, confirmation_number, ... }

GET    /bookings/{booking_id}
  Response: { id, room, guest, payment_status, ... }

PUT    /bookings/{booking_id}
  Request: { status, notes, ... }
  Response: { id, updated_at, ... }

DELETE /bookings/{booking_id}
  Response: { message: "Booking cancelled" }

GET    /bookings/{booking_id}/timeline
  Response: { events: [{ timestamp, event_type, description }] }
```

#### Room & Availability Endpoints

```
GET    /rooms
  Query: ?property_id=1&room_type=double
  Response: { count, results: [room] }

GET    /rooms/{room_id}/availability
  Query: ?check_in=2026-03-01&check_out=2026-03-05&occupancy=2
  Response: { is_available, current_price, competitor_price, ... }

GET    /rooms/{room_id}/pricing-history
  Query: ?days=30
  Response: { history: [{ date, base_price, dynamic_price, ... }] }

PUT    /rooms/{room_id}/pricing
  Request: { base_price, seasonal_multipliers: { ... } }
  Response: { base_price, updated_at }
```

#### Guest Management Endpoints

```
GET    /guests
  Query: ?email=example@email.com
  Response: { count, results: [guest] }

POST   /guests
  Request: { email, first_name, last_name, phone, address }
  Response: { id, email, created_at }

GET    /guests/{guest_id}
  Response: { id, email, bookings_history, preferences, ... }

PUT    /guests/{guest_id}/preferences
  Request: { room_type: "suite", floor: "high", ... }
  Response: { preferences_updated_at, ... }
```

#### Payment Endpoints

```
GET    /invoices
  Query: ?status=paid&date_from=2026-01-01
  Response: { count, results: [invoice] }

POST   /invoices/{invoice_id}/pay
  Request: { payment_method, amount }
  Response: { payment_id, status, receipt_number }

GET    /invoices/{invoice_id}/payment-status
  Response: { status, amount_paid, balance_due, ... }
```

#### Reporting Endpoints

```
GET    /reports/occupancy
  Query: ?property_id=1&date_from=2026-01-01&date_to=2026-12-31
  Response: { occupancy_by_date: [...], summary: {...} }

GET    /reports/revenue
  Query: ?date_from=2026-01-01&aggregation=monthly
  Response: { revenue_by_period: [...], total: ... }

GET    /reports/performance
  Query: ?property_id=1&metrics=occupancy,revenue,adr
  Response: { metrics: {...}, trends: {...} }
```

### 3.3 Response Format Standard

```json
// Success Response (HTTP 200)
{
  "data": {
    "id": 123,
    "name": "Standard Room",
    ...
  },
  "meta": {
    "timestamp": "2026-02-19T10:30:00Z",
    "request_id": "req_abc123"
  }
}

// List Response (HTTP 200)
{
  "data": [
    { "id": 1, ... },
    { "id": 2, ... }
  ],
  "pagination": {
    "count": 100,
    "next_page": 2,
    "previous_page": null,
    "page_size": 50
  },
  "meta": { ... }
}

// Error Response (HTTP 4xx/5xx)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  },
  "meta": { ... }
}
```

### 3.4 Authentication & Authorization

#### JWT Token Structure
```
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Token Contents:
{
  "sub": "user_123",           // Subject (user ID)
  "email": "user@hotel.com",   // User email
  "role": "hotel_manager",     // User role
  "properties": [1, 2, 3],     // Accessible property IDs
  "exp": 1645195200,           // Expiration time
  "iat": 1645108800            // Issued at
}
```

#### Authorization Model (RBAC)
```
Role: admin
  - Permissions: All system operations
  
Role: hotel_manager
  - Permissions: Property management, staff management, pricing, reports
  - Scope: Own properties only
  
Role: receptionist
  - Permissions: Booking management, guest check-in/out, reservation queries
  - Scope: Assigned property only
  
Role: travel_agent
  - Permissions: Booking creation, contract viewing, commission tracking
  - Scope: Contracted properties only
  
Role: guest
  - Permissions: View own bookings, guest services
  - Scope: Own reservations only
```

---

## 4. SECURITY ARCHITECTURE

### 4.1 Security Design Principles

1. **Defense in Depth:** Multiple layers of security
2. **Least Privilege:** Users get minimum required permissions
3. **Encryption Everywhere:** Data at rest and in transit
4. **Audit Trail:** All operations logged and auditable
5. **Regular Assessment:** Security testing and vulnerability scanning

### 4.2 Authentication Security

#### Password Security
- **Hashing:** PBKDF2 with SHA256 (minimum 100,000 iterations)
- **Complexity:** Enforce 12+ characters, mixed case, numbers, symbols
- **Expiration:** Password reset every 90 days
- **History:** Prevent reuse of last 5 passwords
- **Multi-Factor Authentication (MFA):** TOTP-based optional for admins (mandatory Year 2)

#### Session Management
- **Token Lifespan:** Access tokens 1 hour, refresh tokens 30 days
- **Token Revocation:** Immediate logout effectiveness
- **Concurrent Sessions:** Limit 5 active sessions per user
- **IP Whitelisting:** Optional for corporate accounts

### 4.3 Data Encryption

#### Encryption at Rest
```
- Database: AES-256 encryption for sensitive fields
  - credit_card_tokens
  - bank_account_data
  - tax_ids
- File Storage: Server-side encryption (S3 KMS keys)
- Backup: Encrypted snapshots with separate key management
```

#### Encryption in Transit
```
- TLS 1.2+ for all communications
- Certificate pinning for mobile apps
- HTTPS enforcement with HSTS headers
- Secure WebSocket (WSS) for real-time connections
```

### 4.4 API Security

#### Rate Limiting
```
- Authentication endpoints: 5 requests/minute per IP
- Public APIs: 100 requests/minute per API key
- Authenticated APIs: 1000 requests/minute per user
- Dynamic pricing: 10 requests/minute (computation overhead)
```

#### Input Validation & Sanitization
```
- SQL injection prevention: Parameterized queries (Django ORM)
- XSS prevention: HTML entity encoding, Content Security Policy
- CSRF protection: Double-submit cookies, SameSite attribute
- File upload validation: Type checking, size limits, malware scanning
```

#### API Key Management
```
- Keys signed with HMAC-SHA256
- Automatic rotation every 90 days
- Scope-based permissions per key
- Real-time revocation capability
```

### 4.5 Database Security

- **Network Isolation:** Database only accessible from application servers
- **Connection Security:** SSL/TLS for all database connections
- **User Isolation:** Role-based database users with minimal privileges
- **Backup Encryption:** All backups encrypted with KMS keys
- **Point-in-time Recovery:** 7-day retention with cryptographic integrity

### 4.6 Audit Logging

#### Logged Events
```
- Authentication: login, logout, password changes, MFA events
- Data Access: booking views, sensitive field access, exports
- Data Modifications: create, update, delete operations
- Administrative: role changes, permission grants, system configuration
- Security: failed auth attempts, IP changes, permission denials
```

#### Audit Trail Storage
```
- Database: PostgreSQL audit schema with immutable logs
- Retention: 7 years for financial records, 3 years default
- Tamper Detection: HMAC-based integrity verification
- Export: Monthly compliance reports
```

### 4.7 GDPR Compliance

#### Data Privacy Controls
1. **Consent Management:** Explicit opt-in for marketing/analytics
2. **Data Access:** Audit trail of who accessed which guest data
3. **Data Portability:** Export user data in standardized format
4. **Right to Deletion:** Automated anonymization after 90 days inactivity (configurable)
5. **Data Minimization:** Only collect necessary data fields
6. **Retention Policies:** Automatic deletion after retention period

#### GDPR Compliance Features
```
- Privacy Policy: Linked from login, acceptance required
- Data Processing Agreements: Standard agreements with partners
- Third-party Management: Vendor security assessment
- Breach Notification: Automated alert system (72-hour requirement)
- Privacy by Design: Data protection in all new features
```

---

## 5. INTEGRATION ARCHITECTURE

### 5.1 External System Integration Points

#### Payment Integration

**Stripe (Primary)**
```
Integration Points:
- Payment processing (cards, bank transfers)
- Subscription billing
- Webhook event handling (payment confirmation, refunds)
- PCI compliance delegation

Flow:
1. User initiates payment in NEPHELE
2. Token created via Stripe.js (no card data on NEPHELE servers)
3. NEPHELE sends token + amount to Stripe API
4. Stripe processes, sends webhook confirmation
5. NEPHELE updates invoice status
```

#### Email & Notifications

**SendGrid (Email)**
```
Integration Points:
- Transactional email (confirmations, receipts)
- Marketing email (newsletters, promotions)
- Bounce/complaint handling
- Delivery tracking

Templates:
- Booking confirmation
- Payment receipt
- Cancellation notice
- Reminder (24-hour pre-arrival)
```

**Twilio (SMS)**
```
Integration Points:
- SMS notifications (confirmations, reminders)
- Two-factor authentication
- Opt-in/opt-out management

SMS Types:
- Booking confirmation
- Check-in reminder
- Payment confirmation
```

#### OTA Integration

**Booking.com, Airbnb, etc.**
```
Sync Points:
- Room inventory
- Availability calendar
- Occupancy rates
- Reviews and ratings

Implementation:
- iCal protocol for calendar sync
- REST APIs for inventory updates
- Webhook for booking notifications
```

#### Accounting Integration

**QuickBooks Online / Odoo**
```
Sync Points:
- Invoice creation
- Payment recording
- Revenue recognition
- Expense tracking

Implementation:
- Monthly batch sync
- Real-time invoice creation
- Reconciliation reports
```

### 5.2 Integration Reliability

#### Error Handling
```
- Retry Logic: Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Circuit Breaker: Fail fast if external service down
- Deadletter Queue: Store failed events for manual retry
- Monitoring: Alert on integration failures >5%
```

#### Data Consistency
```
- Idempotency Keys: Prevent duplicate processing
- Transaction Logging: Track all integration operations
- Reconciliation: Daily automated reconciliation with external systems
- Audit Trail: Full history of integration operations
```

---

## 5.3 Business Intelligence & Reporting Architecture

### 5.3.1 BI System Overview

#### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│  (Bookings, Payments, Guests, Properties, PricingHistory)   │
└────────────┬────────────────────────────────────┬───────────┘
             │                                    │
             ▼                                    ▼
    ┌─────────────────┐              ┌──────────────────┐
    │  PostgreSQL     │              │   Data Warehouse │
    │  (OLTP)         │              │   (PostgreSQL)   │
    │                 │              │                  │
    │ - Bookings      │◄───ETL───►   │ - fact_sales     │
    │ - Payments      │   Process    │ - dim_time       │
    │ - Guests        │              │ - dim_property   │
    │ - Properties    │              │ - dim_guest      │
    │ - Pricing       │              │ - dim_date       │
    └─────────────────┘              └──────────────────┘
                                             │
                        ┌────────────────────┼────────────────────┬──────────────────┐
                        ▼                    ▼                    ▼                  ▼
                  ┌───────────┐        ┌──────────────┐      ┌──────────────┐  ┌─────────────┐
                  │ Metabase  │        │ Custom Python│      │ Report Gen.  │  │ API Layer   │
                  │ (BI Tool) │        │ Analytics    │      │ (Celery)     │  │ (REST)      │
                  │           │        │ Engine       │      │              │  │             │
                  │ Dashboards│        │ (Algorithms) │      │ PDF/Excel    │  │ /analytics/ │
                  │ + Queries │        │              │      │ Export       │  │ /dashboards/│
                  └───────────┘        └──────────────┘      └──────────────┘  └─────────────┘
                        │                   │                       │                │
                        │                   │                       │                │
                        └───────────────────┴───────────────────────┴────────────────┘
                                            │
                                ┌───────────▼──────────────┐
                                │   Presentation Layer     │
                                │                          │
                                │ Executive Dashboard      │
                                │ Operational Dashboard    │
                                │ Revenue Analytics        │
                                │ Guest Analytics          │
                                │ Custom Reports           │
                                └──────────────────────────┘
```

#### Technology Stack

| Component | Technology | Purpose | Rationale |
|-----------|-----------|---------|-----------|
| **Data Source** | PostgreSQL (OLTP) | Transactional data | Primary application database |
| **Data Warehouse** | PostgreSQL + Materialized Views | Analytical data aggregation | ACID compliance, sufficient for growth phase |
| **ETL Pipeline** | Python (pandas, SQLAlchemy) | Data extraction and transformation | Flexible, integrated with Django ecosystem |
| **BI Dashboard** | Metabase (open-source) | Self-service analytics tool | Zero licensing cost, intuitive UI, embeddable |
| **Analytics Engine** | Python (NumPy, pandas, SciPy) | Advanced analytics calculations | Statistical analysis, custom metrics |
| **Report Generator** | Celery + ReportLab/WeasyPrint | Async report generation | Background processing, supports PDF/Excel export |
| **API Layer** | Django REST Framework | REST endpoints for analytics data | Consistent with platform architecture |

### 5.3.2 Dashboard Architecture

#### Executive Dashboard

**Purpose:** Strategic overview for hotel managers and executives  
**Update Frequency:** Daily (overnight batch)  
**Audience:** Property owners, general managers, executives

**Key Metrics:**
```
Overview Section:
- Total Revenue (YTD, MTD, WTD)
- Average Daily Rate (ADR)
- Occupancy Rate (%)
- Revenue per Available Room (RevPAR)
- Total Bookings (count)

Trends Section:
- Revenue trend (30-day line chart)
- Occupancy trend (30-day line chart)
- ADR trend (30-day line chart)
- Year-over-year comparison

Performance Section:
- Top 5 room types by revenue
- Top 5 room types by occupancy
- Booking source breakdown (direct vs. OTA)
- Guest satisfaction scores (5.0-star avg)

Forecasting Section:
- Revenue forecast (next 30/90 days)
- Occupancy forecast
- Demand seasonality indicators
```

**Data Schema:**
```sql
CREATE TABLE dashboard_executive_metrics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    metric_date DATE NOT NULL,
    
    -- Executive KPIs
    total_revenue DECIMAL(12,2),
    avg_daily_rate DECIMAL(10,2),
    occupancy_rate DECIMAL(5,2),
    revpar DECIMAL(10,2),
    booking_count INTEGER,
    
    -- Trends
    revenue_trend_30d JSONB,  -- {date: value, ...}
    occupancy_trend_30d JSONB,
    adr_trend_30d JSONB,
    
    -- Comparisons
    yoy_revenue_change DECIMAL(5,2),
    yoy_occupancy_change DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, metric_date),
    INDEX idx_property_date (property_id, metric_date)
);
```

#### Operational Dashboard

**Purpose:** Day-to-day operations and staff management  
**Update Frequency:** Real-time (on-demand)  
**Audience:** Front desk staff, housekeeping, operations managers

**Key Metrics:**
```
Today's Operations:
- Checkouts today (count)
- Check-ins today (count)
- Current occupancy (% and room count)
- Tasks pending (housekeeping, maintenance)
- Active reservations by status

Room Status:
- Rooms by status (occupied, vacant, cleaning, maintenance, blocked)
- Housekeeping queue (priority level)
- Maintenance requests (status, age)
- Room assignments for today

Guest Management:
- Current guests (check-in time, room, duration)
- Special requests (list)
- Loyalty status breakdown
- Guest preferences (room type, amenities, diet)

Service Issues:
- Open complaints/issues
- Maintenance tickets (overdue, pending, in-progress)
- Guest requests (priority)
- Staff task assignments
```

**Data Schema:**
```sql
CREATE TABLE dashboard_operational_status (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    status_date DATE NOT NULL,
    status_time TIMESTAMP NOT NULL,
    
    -- Room Status
    occupied_count INTEGER,
    vacant_count INTEGER,
    cleaning_count INTEGER,
    maintenance_count INTEGER,
    blocked_count INTEGER,
    
    -- Check-in/Check-out
    checkouts_scheduled INTEGER,
    checkins_scheduled INTEGER,
    
    -- Task Status
    housekeeping_tasks_pending INTEGER,
    housekeeping_tasks_in_progress INTEGER,
    maintenance_tickets_pending INTEGER,
    
    -- Guest-related
    active_guests_count INTEGER,
    guests_with_special_requests INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_property_datetime (property_id, status_date, status_time)
);
```

#### Revenue Analytics Dashboard

**Purpose:** Financial performance and revenue management  
**Update Frequency:** Daily (midnight)  
**Audience:** Revenue managers, finance team, executives

**Key Metrics:**
```
Revenue Overview:
- Total Revenue (by day, week, month, quarter, year)
- Revenue by room type
- Revenue by source (direct, OTA, travel agency)
- Average Daily Rate (ADR) by room type
- Revenue per available room (RevPAR)

Pricing Analysis:
- Dynamic pricing impact (uplift %)
- Competitor pricing comparison
- Rate optimization recommendations
- Price variance by date and room type

Booking Source Analysis:
- Direct bookings (count, revenue, ADR)
- OTA bookings (count, revenue, ADR, commission)
- Travel agency bookings (count, revenue, ADR, commission)
- Channel comparison

Occupancy & Demand:
- Occupancy rate by date, room type, source
- Cancellation rate
- No-show rate
- Length of stay distribution
- Demand patterns (peak vs. off-season)

Payment Analysis:
- Revenue by payment method
- Payment status breakdown (paid, pending, failed)
- Payment timing (pre-arrival, at-arrival, post-arrival)
- Refund/credit analysis
- Average booking value

Forecasting:
- Revenue forecast (30/90/180 days ahead)
- Occupancy forecast
- Pricing recommendations
- Demand seasonality
```

**Data Schema:**
```sql
CREATE TABLE dashboard_revenue_metrics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    metric_date DATE NOT NULL,
    
    -- Revenue
    total_revenue DECIMAL(12,2),
    revenue_direct DECIMAL(12,2),
    revenue_ota DECIMAL(12,2),
    revenue_agency DECIMAL(12,2),
    
    -- Pricing
    avg_daily_rate DECIMAL(10,2),
    revpar DECIMAL(10,2),
    dynamic_pricing_uplift DECIMAL(5,2),
    
    -- Occupancy
    occupancy_rate DECIMAL(5,2),
    occupancy_count INTEGER,
    
    -- Bookings
    booking_count INTEGER,
    cancellation_count INTEGER,
    cancellation_rate DECIMAL(5,2),
    noshow_count INTEGER,
    
    -- Forecast
    revenue_forecast_30d DECIMAL(12,2),
    occupancy_forecast_30d DECIMAL(5,2),
    
    metrics_by_source JSONB,  -- {direct: {...}, ota: {...}, agency: {...}}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, metric_date),
    INDEX idx_property_date (property_id, metric_date)
);
```

#### Guest Analytics Dashboard

**Purpose:** Guest insights and personalization data  
**Update Frequency:** Daily (midnight)  
**Audience:** Marketing team, personalization engine, customer success

**Key Metrics:**
```
Guest Segmentation:
- New vs. returning guest ratio
- Repeat booking rate
- Guest satisfaction score (NPS, review scores)
- Loyalty segment distribution

Guest Behavior:
- Average booking lead time
- Average length of stay
- Peak booking days/times
- Channel preference
- Amenity preference analysis

Guest Profile:
- Geographic distribution (country, region)
- Guest type (business, leisure, family)
- Group size distribution
- Special requests frequency

Churn & Retention:
- Guest retention rate
- Churn rate (guests who haven't booked within 12 months)
- Reason for churn (if available)
- At-risk guests (low satisfaction scores)

Personalization:
- Generated recommendations (count, acceptance rate)
- Upsell opportunities (count, conversion rate)
- Cross-sell suggestions (count, conversion rate)
- Personalization impact on revenue uplift

Guest Satisfaction:
- Average review score
- Review frequency (% of guests)
- Common feedback themes (positive/negative)
- Complaint resolution rate
- Guest satisfaction trend
```

**Data Schema:**
```sql
CREATE TABLE dashboard_guest_analytics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    analytics_date DATE NOT NULL,
    
    -- Guest counts
    total_unique_guests INTEGER,
    new_guests INTEGER,
    returning_guests INTEGER,
    repeat_booking_rate DECIMAL(5,2),
    
    -- Behavior
    avg_booking_lead_days INTEGER,
    avg_length_of_stay DECIMAL(5,2),
    
    -- Satisfaction
    avg_review_score DECIMAL(3,2),
    avg_nps INTEGER,
    review_rate DECIMAL(5,2),
    complaint_count INTEGER,
    complaint_resolution_rate DECIMAL(5,2),
    
    -- Churn
    retention_rate DECIMAL(5,2),
    churn_rate DECIMAL(5,2),
    at_risk_guests INTEGER,
    
    -- Personalization
    recommendations_generated INTEGER,
    recommendations_accepted INTEGER,
    upsell_conversions INTEGER,
    cross_sell_conversions INTEGER,
    personalization_revenue_uplift DECIMAL(5,2),
    
    guest_segments JSONB,  -- {leisure: %, business: %, family: %, ...}
    geographic_breakdown JSONB,  -- {country: count, ...}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_property_date (property_id, analytics_date)
);
```

### 5.3.3 Analytics API Endpoints

#### Dashboard Data Endpoints

```
GET    /analytics/executive-dashboard
  Query: ?property_id=1&period=month  (period: day|week|month|quarter|year)
  Response: { metrics, trends, forecasts, comparisons }
  Permission: manager:view_analytics

GET    /analytics/operational-dashboard
  Query: ?property_id=1&date=2026-02-19
  Response: { room_status, checkins, checkouts, tasks, guests }
  Permission: staff:view_operational_dashboard

GET    /analytics/revenue-analytics
  Query: ?property_id=1&from_date=2026-01-01&to_date=2026-02-19&granularity=day
  Response: { revenue_metrics, pricing_analysis, occupancy, forecasts }
  Permission: manager:view_revenue_analytics

GET    /analytics/guest-analytics
  Query: ?property_id=1&from_date=2026-01-01&to_date=2026-02-19
  Response: { guest_segments, churn, satisfaction, personalization_impact }
  Permission: manager:view_guest_analytics

GET    /analytics/reports
  Query: ?property_id=1&type=monthly|custom&report_id=123
  Response: { status, url, generated_at, format }
  Permission: manager:view_reports

GET    /analytics/custom-reports/{report_id}
  Response: { report_definition, data, generated_at }
  Permission: user (by report visibility settings)
```

#### Analytics Data Aggregation Endpoints

```
POST   /analytics/aggregate-metrics
  Request: { property_id, metric_type, from_date, to_date, grouping }
  Response: { aggregated_data, summary_statistics }
  Permission: manager:generate_analytics

GET    /analytics/comparison
  Query: ?property_ids=1,2,3&metric=revenue&period=month
  Response: { comparison_data, trends, best_performer }
  Permission: manager:view_analytics

GET    /analytics/forecast
  Query: ?property_id=1&metric=occupancy|revenue&days_ahead=30
  Response: { forecast_values, confidence_interval, methodology }
  Permission: manager:view_analytics

GET    /analytics/export
  Query: ?report_type=excel|csv|pdf&property_id=1&from_date=2026-01-01
  Response: File download (xlsx, csv, or PDF)
  Permission: manager:export_analytics
```

### 5.3.4 ETL & Data Warehouse Pipeline

#### ETL Jobs

```python
# Daily ETL Process (runs at 2 AM UTC)

Jobs:
1. Extract OLTP Data (bookings, payments, guests, properties)
   - Extract: Read from PostgreSQL
   - Transform: Aggregations, calculations, data validation
   - Load: Write to data warehouse schema
   
2. Generate Dimensions
   - dim_time: Date hierarchy (year, quarter, month, week, day)
   - dim_property: Property details with hierarchy
   - dim_guest: Guest profile and segmentation
   - dim_date: Calendar table with season/holiday flags
   
3. Build Fact Tables
   - fact_bookings: Booking details with related dimensions
   - fact_revenue: Daily revenue by property/room type/source
   - fact_occupancy: Daily occupancy metrics
   - fact_pricing: Pricing changes and effective rates
   
4. Calculate Dashboard Metrics
   - Executive KPIs (revenue, occupancy, ADR, RevPAR)
   - Operational status (room counts by status)
   - Revenue analytics (by source, room type, date)
   - Guest analytics (segments, churn, satisfaction)
   
5. Generate Forecasts
   - Occupancy forecasting (time-series model)
   - Revenue forecasting (demand-based model)
   - Pricing recommendations
   
6. Data Quality Checks
   - Completeness: All expected records present
   - Accuracy: Values within expected ranges
   - Consistency: Cross-table validation
   - Freshness: All tables updated within SLA
```

#### ETL Implementation

**Technology:** Celery (async jobs) + pandas (data processing) + SQLAlchemy (ORM)

```python
@periodic_task(run_every=crontab(hour=2, minute=0))
def nightly_etl_pipeline():
    """Run full ETL pipeline nightly"""
    
    try:
        # 1. Extract OLTP data
        extract_bookings_to_warehouse()
        extract_payments_to_warehouse()
        extract_guests_to_warehouse()
        
        # 2. Generate dimensions
        build_time_dimensions()
        build_property_dimensions()
        build_guest_dimensions()
        
        # 3. Build fact tables
        build_fact_bookings()
        build_fact_revenue()
        build_fact_occupancy()
        
        # 4. Calculate metrics
        calculate_executive_metrics()
        calculate_operational_status()
        calculate_revenue_metrics()
        calculate_guest_analytics()
        
        # 5. Generate forecasts
        generate_occupancy_forecast()
        generate_revenue_forecast()
        
        # 6. Data quality validation
        validate_etl_completeness()
        validate_data_ranges()
        
        logging.info("ETL pipeline completed successfully")
        
    except Exception as e:
        logging.error(f"ETL pipeline failed: {str(e)}")
        alert_operations_team(f"ETL Failure: {str(e)}")
```

### 5.3.5 Analytics Calculations & Algorithms

#### Key Metric Definitions

```
Occupancy Rate = (Occupied Rooms / Total Rooms) × 100
Average Daily Rate (ADR) = Total Revenue / Number of Bookings
Revenue per Available Room (RevPAR) = Total Revenue / Total Rooms

Dynamic Pricing Uplift = (Actual ADR - Base ADR) / Base ADR × 100
Cancellation Rate = Cancelled Bookings / Total Bookings × 100
No-Show Rate = No-Show Bookings / Checked-In Bookings × 100

Guest Retention Rate = Returning Guests / Total Previous Guests × 100
Churn Rate = (Total Previous Guests - Returning Guests) / Total Previous Guests × 100
Net Promoter Score (NPS) = (Promoters % - Detractors %) × 100

Forecast Accuracy = 1 - (|Actual - Forecast| / Actual) × 100
```

#### Forecasting Models

**Occupancy Forecasting:**
- Algorithm: Time-series ARIMA or exponential smoothing
- Input: Historical occupancy data, seasonality factors, upcoming events
- Output: Occupancy forecast (30/90/180 days)
- Accuracy Target: 85%+

**Revenue Forecasting:**
- Algorithm: Demand-based regression model
- Input: Historical revenue, occupancy forecast, pricing strategy, seasonality
- Output: Revenue forecast with confidence intervals
- Accuracy Target: 80%+

**Demand Forecasting:**
- Algorithm: Prophet (Facebook) or ARIMA
- Input: Booking history, competitor pricing, events, seasonality
- Output: Expected demand (bookings) for future dates
- Accuracy Target: 75%+

### 5.3.6 Data Visualization Strategy

#### Metabase Integration

```
1. Connection Setup:
   - Connected to PostgreSQL (data warehouse)
   - Auto-discover schemas and tables
   - Create dashboards for each user type

2. Pre-built Dashboards:
   - Executive Dashboard (executive role)
   - Operational Dashboard (staff role)
   - Revenue Dashboard (manager role)
   - Guest Analytics Dashboard (marketing role)

3. Self-Service Capabilities:
   - Users can create custom queries
   - Drag-and-drop visualization builder
   - Saved reports for scheduled delivery
   - Email alerts on metric thresholds

4. Row-Level Security:
   - Users see only their property data
   - Managers see team data
   - Executives see all properties

5. Embeddable Dashboards:
   - Embed dashboards in React frontend
   - Shareable public links (with permissions)
   - Mobile-responsive design
```

#### Custom Analytics Engine

```
For metrics beyond Metabase capabilities, use custom Python analytics:

- Anomaly detection (statistical outliers)
- Cohort analysis (guest lifetime value)
- Attribution modeling (revenue source attribution)
- Prediction models (churn prediction, next booking prediction)
- Simulation models (pricing strategy what-if analysis)
```

### 5.3.7 Automated Reporting & Scheduling

#### Automated Report System Overview

The system provides automated report generation and email delivery for stakeholders, reducing manual reporting work by 40-50 hours/week and ensuring consistent, timely business intelligence distribution.

```
┌─────────────────────────────────────────────────────────────────┐
│           AUTOMATED REPORTING SYSTEM ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Report Scheduler (Celery Beat)                               │
│  ├─ Daily Reports (Operational Dashboard)                     │
│  ├─ Weekly Reports (Revenue Summary)                          │
│  ├─ Monthly Reports (Executive Summary)                       │
│  └─ Ad-hoc Reports (User-triggered)                           │
│         │                                                      │
│         ├──→ Report Generation Service                        │
│         │    ├─ Query data aggregation                        │
│         │    ├─ Calculate KPIs                                │
│         │    ├─ Generate charts/visualizations                │
│         │    └─ Render PDF/Excel/CSV                          │
│         │                                                      │
│         ├──→ Distribution Service                             │
│         │    ├─ Email delivery                                │
│         │    ├─ Archive storage (S3)                          │
│         │    ├─ Dashboard embedding                           │
│         │    └─ Notification delivery                         │
│         │                                                      │
│         └──→ Tracking & Analytics                             │
│              ├─ Report generation logs                        │
│              ├─ Email delivery status                         │
│              ├─ User access tracking                          │
│              └─ Performance metrics                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Scheduled Report Types

| Report Type | Frequency | Recipients | Content | Use Case |
|-------------|-----------|------------|---------|----------|
| **Daily Operational** | Daily 6:00 AM | Property Managers | Room status, check-ins/outs, tasks pending | Monitor daily operations |
| **Daily Finance** | Daily 8:00 AM | Finance Team | Revenue, bookings, payments, refunds | Track cash flow |
| **Weekly Performance** | Monday 8:00 AM | Managers/Executives | Revenue trends, ADR, occupancy, YoY comparison | Monitor KPI trends |
| **Weekly Marketing** | Wednesday 10:00 AM | Marketing Team | Guest analytics, booking sources, conversion rates | Optimize marketing |
| **Monthly Executive** | 1st of month 9:00 AM | C-Suite | Revenue summary, forecasts, strategic metrics, alerts | Strategic planning |
| **Monthly Occupancy** | 2nd of month 9:00 AM | Operations | Occupancy analysis, forecasts, availability | Capacity planning |
| **Compliance Report** | Quarterly | Compliance Officer | GDPR audit, data access logs, security incidents | Regulatory compliance |
| **Custom Reports** | User-defined | Selected users | User-configured metrics and data | Ad-hoc analysis |

#### Report Generation Pipeline

```
1. SCHEDULING LAYER (Celery Beat)
   └─ Cron schedule triggers report generation task
   
2. DATA AGGREGATION LAYER
   ├─ Query dashboard metrics tables
   ├─ Aggregate from multiple sources
   ├─ Apply filters (property, date range)
   └─ Calculate derived metrics
   
3. RENDERING LAYER
   ├─ PDF Rendering (ReportLab)
   │  ├─ Header with branding
   │  ├─ KPIs with color coding
   │  ├─ Charts (matplotlib/plotly)
   │  └─ Detailed data tables
   │
   ├─ Excel Rendering (openpyxl)
   │  ├─ Multiple sheets by category
   │  ├─ Formatted tables
   │  ├─ Embedded charts
   │  └─ Data filters/pivots
   │
   └─ CSV Export
      └─ Raw data export for further analysis
   
4. DISTRIBUTION LAYER
   ├─ Email via SendGrid
   │  ├─ HTML email with embedded visualizations
   │  ├─ PDF attachment
   │  ├─ Direct download links
   │  └─ Delivery tracking
   │
   ├─ File Storage (S3)
   │  ├─ Archive reports
   │  ├─ Generate signed URLs
   │  └─ Retention policy (2 years)
   │
   └─ Dashboard Integration
      ├─ Embed report link in UI
      ├─ Push notification
      └─ Store metadata in

 DB
```

#### Database Schema for Scheduled Reports

```sql
CREATE TABLE scheduled_reports (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    created_by INT NOT NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL,  -- 'daily_operational', 'weekly_performance', 'monthly_executive', etc.
    
    -- Scheduling
    schedule_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'custom'
    schedule_day INT,  -- Day of month for monthly reports
    schedule_dow INT,  -- Day of week for weekly reports (0-6)
    schedule_time TIME NOT NULL,  -- Time to generate report (UTC)
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Recipients
    recipient_emails TEXT[] NOT NULL,  -- Array of email addresses
    include_managers BOOLEAN DEFAULT true,  -- Include property managers
    include_owner BOOLEAN DEFAULT false,  -- Include property owner
    
    -- Configuration
    include_charts BOOLEAN DEFAULT true,
    include_summary BOOLEAN DEFAULT true,
    include_detailed_data BOOLEAN DEFAULT true,
    custom_filters JSONB,  -- Custom filters for report
    metric_selection JSONB,  -- Selected metrics to include
    
    -- Output
    export_formats TEXT[] DEFAULT ARRAY['pdf'],  -- ['pdf', 'excel', 'csv']
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_generated_at TIMESTAMP,
    next_scheduled_at TIMESTAMP,
    consecutive_failures INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, name),
    INDEX idx_property_active (property_id, is_active),
    INDEX idx_next_scheduled (next_scheduled_at)
);

CREATE TABLE report_executions (
    id SERIAL PRIMARY KEY,
    scheduled_report_id INT NOT NULL REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    
    execution_status VARCHAR(20) NOT NULL,  -- 'pending', 'generating', 'generated', 'failed'
    
    -- Files generated
    pdf_file_path VARCHAR(500),
    excel_file_path VARCHAR(500),
    csv_file_path VARCHAR(500),
    
    -- Email delivery
    email_status VARCHAR(20),  -- 'pending', 'sent', 'failed'
    email_sent_at TIMESTAMP,
    email_recipients TEXT[],
    
    -- Metadata
    data_date_from DATE,
    data_date_to DATE,
    metrics_snapshot JSONB,  -- Snapshot of KPIs for this report
    
    execution_time_seconds INT,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scheduled_report (scheduled_report_id),
    INDEX idx_status (execution_status),
    INDEX idx_created (created_at)
);

CREATE TABLE report_delivery_tracking (
    id SERIAL PRIMARY KEY,
    report_execution_id INT NOT NULL REFERENCES report_executions(id) ON DELETE CASCADE,
    
    recipient_email VARCHAR(255) NOT NULL,
    delivery_status VARCHAR(20),  -- 'pending', 'sent', 'bounced', 'opened', 'failed'
    
    opened_at TIMESTAMP,
    click_count INT DEFAULT 0,
    last_clicked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_recipient (recipient_email),
    INDEX idx_execution (report_execution_id),
    INDEX idx_status (delivery_status)
);
```

#### API Endpoints for Report Management

```
POST /api/v1/analytics/scheduled-reports/
  - Create new scheduled report
  - Required: name, report_type, schedule_type, schedule_time, recipient_emails
  - Optional: custom_filters, metric_selection, export_formats
  
GET /api/v1/analytics/scheduled-reports/
  - List all scheduled reports for user's properties
  - Filters: property_id, report_type, is_active
  
GET /api/v1/analytics/scheduled-reports/{id}/
  - Retrieve specific scheduled report configuration
  
PUT /api/v1/analytics/scheduled-reports/{id}/
  - Update scheduled report settings
  - Cannot modify past executions
  
DELETE /api/v1/analytics/scheduled-reports/{id}/
  - Soft-delete and deactivate scheduled report
  
POST /api/v1/analytics/scheduled-reports/{id}/trigger/
  - Manually trigger immediate report generation
  - Returns report_execution_id
  
POST /api/v1/analytics/scheduled-reports/{id}/test/
  - Send test report to current user's email
  - Validates configuration and email delivery
  
GET /api/v1/analytics/scheduled-reports/{id}/executions/
  - List execution history for scheduled report
  - Filters: execution_status, date_from, date_to
  - Pagination: limit=50, offset=0
  
GET /api/v1/analytics/scheduled-reports/{id}/executions/{exec_id}/
  - Retrieve specific report execution
  - Returns status, file paths, metrics snapshot
  
GET /api/v1/analytics/reports/{exec_id}/download/
  - Download generated report file
  - Query param: format (pdf|excel|csv)
  - Returns signed S3 URL or file stream
  
POST /api/v1/analytics/reports/{exec_id}/resend/
  - Resend report email to original recipients
  - Optional: override_recipients
  
GET /api/v1/analytics/delivery-tracking/{exec_id}/
  - Get email delivery status for report
  - Returns per-recipient delivery status and engagement metrics
```

#### Report Generation Service Implementation

```python
# Core components

class ReportGenerator:
    """Main report generation orchestrator"""
    
    def generate_report(scheduled_report, data_date_from, data_date_to):
        - Fetch and aggregate data
        - Calculate metrics and KPIs
        - Detect and alert on anomalies
        - Generate visualizations
        - Create PDF/Excel/CSV files
        - Return file paths and metrics snapshot
    
class ReportRenderer:
    """Format-specific rendering"""
    
    def render_pdf(data, template, metrics):
        - Use ReportLab for PDF generation
        - Include charts (matplotlib/plotly)
        - Professional formatting
        - Multi-page support for large reports
    
    def render_excel(data, template, metrics):
        - Use openpyxl for Excel
        - Multiple sheets by category
        - Formatted tables with styles
        - Embedded charts
    
    def render_csv(data):
        - CSV export with proper escaping
        - Flatten nested structures
        - Include metadata in header

class EmailDistributor:
    """Email delivery and tracking"""
    
    def send_report(report_execution, recipients):
        - Build HTML email template
        - Attach PDF/Excel files
        - Include download links
        - Track delivery via SendGrid webhooks
    
    def track_delivery(email_id, event_type, timestamp):
        - Update delivery_status (sent, opened, clicked, bounced)
        - Calculate engagement metrics
        - Alert on delivery failures

class ReportScheduler (Celery Beat):
    """Periodic report scheduling"""
    
    @periodic_task(run_every=crontab(minute=0))  # Every hour
    def check_pending_reports():
        - Query scheduled_reports for next_scheduled_at <= now()
        - Trigger report generation for each
        - Update next_scheduled_at timestamp
    
    @periodic_task(run_every=crontab(minute='*/5'))  # Every 5 minutes
    def monitor_report_health():
        - Check for failed reports
        - Retry failures with exponential backoff
        - Alert on critical failures
        - Clean up old executions (>2 years)
```

#### Anomaly Detection & Alerts

```
Automated anomaly detection alerts users to unusual metrics:

1. Statistical Anomalies:
   - Revenue drops >30% YoY
   - Occupancy falls below threshold
   - ADR increases >50% without explanation
   - Booking cancellation rate increases
   
2. Operational Anomalies:
   - Unusual number of no-shows
   - High complaint volume
   - Low review ratings
   - Payment processing failures
   
3. Alert Delivery:
   - Include in daily operational report
   - Send immediate email for critical alerts
   - Dashboard notification badge
   - SMS for P1 incidents (configurable)
   
4. Alert Configuration UI:
   - Set metric thresholds
   - Choose notification channels
   - Configure alert frequency
   - Suppress false positives
```

#### Performance & Scalability

| Aspect | Specification | Notes |
|--------|-------------|-------|
| **Report Generation Time** | <2 minutes for daily/weekly | Parallel processing for multiple properties |
| **Email Batch Processing** | <5 minutes for 1,000 emails | SendGrid API rate limited to prevent bottlenecks |
| **Storage Efficiency** | Compress PDFs, archive old reports | 2-year retention policy |
| **Database Indexing** | Optimized queries with proper indexes | Scheduled metrics pre-calculated nightly |
| **Concurrent Reports** | Support 50+ simultaneous generations | Queued via Celery worker pool |
| **Delivery Guarantees** | At-least-once delivery guarantee | Retry logic with exponential backoff |

---

### 5.3.8 Predictive Analytics & Forecasting Architecture

#### Forecasting System Overview

NEPHELE implements comprehensive predictive analytics using time-series forecasting (Prophet, SARIMA) and machine learning (XGBoost) to forecast occupancy, revenue, cancellations, and no-shows. These capabilities enable proactive management, revenue optimization, and risk mitigation.

```
┌─────────────────────────────────────────────────────────────────┐
│       PREDICTIVE ANALYTICS & FORECASTING ARCHITECTURE           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ML Model Training Pipeline (Weekly/Daily)                    │
│  ├─ Data Preparation & Feature Engineering                   │
│  ├─ Occupancy Forecasting (Prophet + SARIMA)                 │
│  ├─ Revenue Forecasting (Prophet)                            │
│  ├─ Cancellation Prediction (XGBoost)                        │
│  ├─ No-Show Prediction (XGBoost)                             │
│  └─ Model Evaluation & Monitoring                            │
│         │                                                      │
│         ├──→ Model Storage                                     │
│         │    ├─ Serialized models (pickle/.pkl)               │
│         │    ├─ Model versioning with metadata                │
│         │    ├─ Performance metrics tracking                  │
│         │    └─ Model registry                                │
│         │                                                      │
│         ├──→ Real-Time Prediction Service                     │
│         │    ├─ Load-balanced API endpoints                   │
│         │    ├─ Sub-100ms inference latency                   │
│         │    ├─ Fallback to rule-based predictions           │
│         │    └─ Batch prediction processing                   │
│         │                                                      │
│         ├──→ Prediction Storage                               │
│         │    ├─ OccupancyForecast table                       │
│         │    ├─ RevenueForecast table                         │
│         │    ├─ CancellationPrediction table                  │
│         │    ├─ NoShowPrediction table                        │
│         │    └─ ForecastingModelMetrics table                 │
│         │                                                      │
│         └──→ Forecasting Dashboard & API                      │
│              ├─ Executive dashboard widgets                   │
│              ├─ Alerting for high-risk events                │
│              ├─ REST API for frontend integration             │
│              └─ Historical forecast accuracy tracking         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Forecasting Models Implemented

| Model | Type | Target Variable | Accuracy | Frequency | Use Case |
|-------|------|-----------------|----------|-----------|----------|
| **Prophet** | Time-Series | Occupancy % | MAPE 5-8% | Daily | 7/14/30-day occupancy forecast |
| **SARIMA** | Time-Series | Occupancy % | MAPE 4-6% | Weekly | Short-term occupancy (7-14 days) |
| **Prophet** | Time-Series | Daily Revenue | MAPE 8-10% | Daily | Revenue forecasting & budgeting |
| **XGBoost** | Classification | Cancellation Risk (0-100) | Precision 0.84 | Per booking | Identify cancellation-prone bookings |
| **XGBoost** | Classification | No-Show Risk (0-100) | Precision 0.68 | Per booking | Overbooking optimization |

#### Occupancy Forecasting Model

**Data Pipeline:**
```
Historical Booking Calendar Data
├─ Daily occupancy rates (0-100%)
├─ Booking pace (7, 14, 30 days)
├─ Day-of-week patterns (Mon-Sun)
├─ Seasonal patterns (Q1-Q4)
├─ Holiday/event indicators
└─ Competitor availability (optional)
        │
        ├──→ Prophet Model (Primary)
        │    ├─ Trend component: Long-term trajectory
        │    ├─ Yearly seasonality: Summer peaks, winter lows
        │    ├─ Weekly seasonality: Wed-Sun peaks
        │    ├─ Holiday effects: Christmas, Easter, etc.
        │    └─ Uncertainty intervals (95% CI)
        │
        ├──→ SARIMA Model (Validation)
        │    ├─ Order: SARIMA(1,1,1)x(1,1,1,7)
        │    ├─ Seasonal component: 7-day week
        │    └─ Alternative predictions for comparison
        │
        └──→ Ensemble Forecast
             └─ Average of Prophet + SARIMA for robustness

Output: 30-day occupancy predictions with confidence intervals
```

**Implementation Details:**
- **Training Frequency:** Daily (incorporates new bookings)
- **Data Window:** 365+ days historical data (full seasonal cycle)
- **Forecast Horizon:** 7, 14, 30 days ahead
- **Update Mechanism:** Incremental updates as new data arrives
- **Performance Baseline:** MAE <4%, RMSE <6%, MAPE <8%

#### Revenue Forecasting Model

**Model Architecture:**
```
Daily Revenue Input = Occupancy % × ADR × Number of Rooms
                │
                ├──→ Prophet Time-Series Model
                │    ├─ Captures revenue seasonality
                │    ├─ Adjusts for price changes (dynamic pricing impact)
                │    ├─ Predicts 30-day revenue trend
                │    └─ Confidence intervals for budgeting
                │
                └──→ Output: Revenue forecast $ with bounds
                     ├─ Expected revenue (point estimate)
                     ├─ Lower bound (optimistic scenario)
                     └─ Upper bound (pessimistic scenario)
```

**Business Use:**
- Cash flow forecasting and budget management
- Early warning for revenue shortfalls
- Variance analysis against budget targets
- Revenue optimization recommendations

#### Cancellation Risk Prediction

**Classification Model (XGBoost):**

| Feature Category | Features | Impact |
|-----------------|----------|--------|
| **Booking Behavior** | Lead time, booking channel, payment status, refund policy | ⭐⭐⭐ High |
| **Pricing** | Price per night, discount %, rate changes | ⭐⭐⭐ High |
| **Customer** | Type (business/leisure), repeat guest status, nationality | ⭐⭐ Medium |
| **Temporal** | Day of week, season, holiday proximity | ⭐⭐ Medium |
| **Property** | Location, star rating, occupancy forecast | ⭐ Low-Medium |

**Output:**
- Cancellation Risk Score (0-100%)
- Risk Level (Low <40%, Medium 40-65%, High >65%)
- Recommended Actions (confirmation email, special offer, etc.)

**Intervention Strategy:**
```
High Risk (>65%)
├─ Automated confirmation email
├─ Personalized retention offer
├─ VIP treatment assignment
└─ Overbooking flag

Medium Risk (40-65%)
├─ Standard confirmation
├─ Monitor for cancellation signals
└─ Optional special offer

Low Risk (<40%)
└─ Standard booking handling
```

#### No-Show Risk Prediction

**Classification Model (XGBoost):**

| Risk Indicator | Typical Finding |
|----------------|-----------------|
| Long lead time (>30 days) | 4-6% no-show rate |
| Unpaid deposit | 8-12% no-show rate |
| International guest | 4-5% no-show rate |
| Budget hotel OTA booking | 4-6% no-show rate |
| Confirmed payment | <2% no-show rate |

**Overbooking Strategy Based on Predictions:**
```
Risk Distribution Detection
├─ Low Risk (<20%) bookings: 100% allocation
├─ Medium Risk (20-40%) bookings: 105-110% allocation
└─ High Risk (>40%) bookings: 110-115% allocation

Expected Outcome:
├─ 2-3% additional occupancy rate
├─ Reduced Walk-Away rate: <0.5%
├─ Net revenue increase: 1-2% per property
└─ Slight guest inconvenience: <1% bumped rate
```

#### Forecasting API Endpoints

```
GET /api/analytics/occupancy-forecasts/
├─ Query Parameters: property_id, forecast_date, target_date
├─ Response: List of occupancy forecasts with CI
└─ Pagination: 50 results per page

GET /api/analytics/occupancy-forecasts/next-30-days/
├─ Query Parameters: property_id
├─ Response: 30-day rolling forecast
└─ Use Case: Dashboard widget

GET /api/analytics/revenue-forecasts/next-30-days/
├─ Query Parameters: property_id
├─ Response: Daily revenue forecast with bounds
└─ Use Case: Budget vs forecast comparison

GET /api/analytics/cancellation-predictions/high-risk/
├─ Query Parameters: property_id
├─ Response: High-risk bookings (>65%) with scores
└─ Use Case: Manual intervention list

GET /api/analytics/noshow-predictions/overbooking-recommendations/
├─ Query Parameters: property_id
├─ Response: Recommended overbooking percentages
└─ Use Case: Yield management

GET /api/analytics/forecast-metrics/health-check/
├─ Query Parameters: property_id
├─ Response: Model health status (green/yellow/red)
├─ Metrics: MAPE, precision, recall, F1-score
└─ Use Case: Model monitoring & alerting
```

#### Database Schema for Forecasting

```sql
-- Occupancy Forecasts
CREATE TABLE occupancy_forecasts (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_occupancy DECIMAL(5,2) NOT NULL,
    lower_bound DECIMAL(5,2),
    upper_bound DECIMAL(5,2),
    model_type VARCHAR(20), -- prophet|sarima|ensemble
    actual_occupancy DECIMAL(5,2),
    forecast_error DECIMAL(5,2),
    created_at TIMESTAMP,
    UNIQUE(property_id, forecast_date, target_date, model_type),
    INDEX idx_property_target (property_id, target_date)
);

-- Revenue Forecasts
CREATE TABLE revenue_forecasts (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_revenue DECIMAL(12,2) NOT NULL,
    lower_bound DECIMAL(12,2),
    upper_bound DECIMAL(12,2),
    model_type VARCHAR(20),
    predicted_occupancy DECIMAL(5,2),
    avg_daily_rate DECIMAL(10,2),
    actual_revenue DECIMAL(12,2),
    forecast_error DECIMAL(12,2),
    forecast_error_pct DECIMAL(5,2),
    created_at TIMESTAMP,
    UNIQUE(property_id, forecast_date, target_date, model_type)
);

-- Cancellation Predictions
CREATE TABLE cancellation_predictions (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    booking_id INT,
    prediction_date DATE NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    cancellation_risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20), -- low|medium|high
    lead_time_days INT,
    booking_source VARCHAR(50),
    intervention_flag BOOLEAN DEFAULT false,
    actually_cancelled BOOLEAN,
    cancellation_date DATE,
    created_at TIMESTAMP,
    INDEX idx_property_risk_level (property_id, risk_level),
    INDEX idx_booking (booking_id)
);

-- No-Show Predictions
CREATE TABLE noshow_predictions (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    booking_id INT,
    prediction_date DATE NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    noshow_risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20), -- low|medium|high
    customer_country VARCHAR(100),
    payment_confirmed BOOLEAN,
    overbooking_flag BOOLEAN DEFAULT false,
    overbooking_factor DECIMAL(3,2),
    actually_noshow BOOLEAN,
    created_at TIMESTAMP,
    INDEX idx_property_risk_level (property_id, risk_level),
    INDEX idx_overbooking (overbooking_flag)
);

-- Model Metrics for Monitoring
CREATE TABLE forecasting_model_metrics (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    evaluation_date DATE NOT NULL,
    evaluation_period VARCHAR(20), -- 7day|14day|30day|90day
    mae DECIMAL(12,4),             -- Mean Absolute Error
    rmse DECIMAL(12,4),            -- Root Mean Squared Error
    mape DECIMAL(5,2),             -- Mean Absolute Percentage Error
    r_squared DECIMAL(5,4),        -- R-squared coefficient
    precision DECIMAL(5,4),        -- For classification models
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    roc_auc DECIMAL(5,4),
    predictions_count INT,
    is_acceptable BOOLEAN,
    needs_retraining BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE(property_id, model_name, evaluation_date),
    INDEX idx_health_check (is_acceptable, needs_retraining)
);
```

#### Model Training & Deployment Pipeline

**Training Frequency:**
- **Daily:** Occupancy & Revenue forecasts (use latest bookings)
- **Weekly:** All classification models (sufficient data accumulation)
- **Ad-hoc:** Manual retraining if performance drops >10%

**Deployment Process:**
```
1. Data Collection (Historical + New)
   └─ Aggregate 12-24 months of historical data

2. Feature Engineering
   ├─ Temporal features (day-of-week, season, etc.)
   ├─ Lag features (t-1, t-7, t-30)
   ├─ Rolling statistics
   └─ Custom domain features

3. Model Training
   ├─ Train Prophet occupancy model            (5-10 sec)
   ├─ Train SARIMA occupancy model             (30-60 sec)
   ├─ Train Prophet revenue model              (5-10 sec)
   ├─ Train XGBoost cancellation model         (30-60 sec)
   └─ Train XGBoost no-show model              (30-60 sec)

4. Evaluation
   ├─ Cross-validation (k-fold or time-series split)
   ├─ Calculate metrics (MAE, RMSE, MAPE, etc.)
   ├─ Compare against baseline
   └─ Check threshold acceptance criteria

5. Versioning & Storage
   ├─ Serialize models (pickle/.pkl files)
   ├─ Store metadata (version, training date, metrics)
   ├─ Upload to S3/model registry
   └─ Tag as "production" if metrics acceptable

6. Model Serving
   ├─ Load best model to memory on startup
   ├─ Serve predictions via REST API
   ├─ Log all predictions for monitoring
   └─ Collect actuals for future retraining
```

**Monitoring & Alerting:**
```
Daily Model Health Check
├─ Compare prediction vs actual (when available)
├─ Calculate current accuracy metrics
├─ Detect data drift (unusual patterns in input data)
├─ Detect model drift (accuracy declining beyond threshold)
└─ Alert if:
   ├─ MAPE > 15% (forecasting models)
   ├─ Precision < 0.70 (classification models)
   └─ Any model hasn't been updated in >7 days
```

#### Performance & Scalability

| Aspect | Target | Notes |
|--------|--------|-------|
| **Prediction Latency** | <100ms per booking | Sub-second API response for feature store |
| **Forecast Generation Time** | <5 minutes for all properties | Parallel processing per property |
| **Model Training Time** | <5 minutes | Weekly batch training |
| **Forecast Accuracy** | MAPE <10% (time-series), Precision >0.75 (classification) | Validated on hold-out test set |
| **Data Volume** | 1M+ predictions/month | Efficiently indexed for fast retrieval |
| **Storage Size** | <2GB models storage | Compressed serialization |
| **Concurrent Predictions** | 1,000+ per second | Distributed inference across workers |
| **Model Availability** | 99.9% uptime | Load-balanced prediction service |

---

## 6. DEPLOYMENT ARCHITECTURE

### 6.1 Cloud Infrastructure

#### Cloud Provider: AWS (Multi-region ready)

**Primary Region: EU-West-1 (Ireland)** - GDPR compliance

```
┌──────────────────────────────────────────────┐
│           AWS Region (EU-West-1)              │
├──────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │   Availability Zone 1a               │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ ECS Fargate (API Servers)    │   │   │
│  │  │ (2-10 instances, auto-scale) │   │   │
│  │  └──────────────────────────────┘   │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ ElastiCache Redis            │   │   │
│  │  │ (Cache layer)                │   │   │
│  │  └──────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │   Availability Zone 1b               │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ ECS Fargate (API Servers)    │   │   │
│  │  │ (2-10 instances, auto-scale) │   │   │
│  │  └──────────────────────────────┘   │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ Celery Workers (Async Jobs)  │   │   │
│  │  │ (1-5 instances, auto-scale)  │   │   │
│  │  └──────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │        Shared Services                │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ RDS PostgreSQL (Multi-AZ)    │   │   │
│  │  │ (Primary + Standby)          │   │   │
│  │  └──────────────────────────────┘   │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ S3 Document Storage          │   │   │
│  │  │ (Encrypted, versioned)       │   │   │
│  │  └──────────────────────────────┘   │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │ CloudFront CDN               │   │   │
│  │  │ (Static content, API caching)│   │   │
│  │  └──────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
│                                              │
└──────────────────────────────────────────────┘
```

### 6.2 Containerization Strategy

#### Docker Image Configuration

**Base Image:** `python:3.10-slim`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run gunicorn
CMD ["gunicorn", "--workers=4", "--worker-class=uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000", "HMS.wsgi:application"]
```

#### Container Orchestration: ECS Fargate

```
Task Definition:
  - Image: nephele-api:v1.0.0
  - vCPU: 1.0
  - Memory: 2GB
  - Environment Variables:
    - DATABASE_URL (from Secrets Manager)
    - REDIS_URL (from Secrets Manager)
    - SECRET_KEY (from Secrets Manager)
  - Logging: CloudWatch Logs
  - Port Mapping: 8000:8000

Service Configuration:
  - Desired Count: 2 (minimum)
  - Max Capacity: 10 (auto-scale)
  - Load Balancer: Application Load Balancer (ALB)
  - Target Group: Port 8000, path /
  - Health Check: /health/ endpoint (200 response)
  - Auto-scaling:
    - Min: 2 instances (high availability)
    - Max: 10 instances
    - Target CPU: 70%
    - Target Memory: 80%
```

### 6.3 Load Balancing & Traffic Management

```
Internet
    │
    ▼
┌─────────────────────────────────────┐
│  CloudFront CDN                     │
│  - Cache static assets              │
│  - DDoS protection (AWS Shield)     │
│  - Geographic distribution          │
└────────────────┬────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Application Load   │
        │ Balancer (ALB)     │
        │ - HTTPS/TLS 1.2+   │
        │ - Health checking  │
        │ - Path routing     │
        └────────┬───────────┘
                 │
         ┌───────┴───────┐
         ▼               ▼
    ┌────────┐      ┌────────┐
    │ ECS    │      │ ECS    │
    │ Task   │      │ Task   │
    │ (1a)   │      │ (1b)   │
    └────────┘      └────────┘
```

### 6.4 Database Strategy

#### PostgreSQL Configuration

**Primary Database (RDS Multi-AZ)**
```
Configuration:
  - Engine: PostgreSQL 14+
  - Instance: db.t3.large (2 vCPU, 8GB RAM)
  - Storage: 100GB gp3 SSD (auto-scale)
  - Backup: Daily snapshots, 30-day retention
  - Multi-AZ: Automatic failover to standby
  - Encryption: AES-256 at rest, SSL in transit
  
Performance Tuning:
  - max_connections: 200
  - shared_buffers: 2GB
  - effective_cache_size: 6GB
  - work_mem: 20MB
  - Random Page Cost: 1.1 (for SSD)
  
Indexes:
  - All foreign keys
  - Composite indexes on common filters
  - Partial indexes for status-based queries
```

#### Backup & Recovery Strategy

```
Backup Schedule:
  - Hourly snapshots: Last 24 hours
  - Daily snapshots: Last 30 days
  - Weekly snapshots: Last 12 weeks
  - Monthly snapshots: Last 12 months

Recovery Objectives:
  - RTO (Recovery Time Objective): 1 hour
  - RPO (Recovery Point Objective): 1 hour
  
Recovery Procedures:
  - Automated failover to standby: < 2 minutes
  - Restore from snapshot: < 15 minutes
  - Point-in-time recovery: < 30 minutes
```

### 6.5 CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python manage.py test --no-migrations
          coverage report --fail-under=80
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t nephele-api:${{ github.sha }} .
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag nephele-api:${{ github.sha }} $ECR_REGISTRY/nephele-api:latest
          docker push $ECR_REGISTRY/nephele-api:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster nephele-prod --service nephele-api --force-new-deployment
      - name: Run smoke tests
        run: |
          ./tests/smoke_tests.sh
```

---

## 7. SCALABILITY & PERFORMANCE DESIGN

### 7.1 Caching Strategy

#### Multi-Level Caching Architecture

```
Level 1: Browser Cache
  - Static assets (CSS, JavaScript, images): 30 days
  - API responses (GET): 5 minutes
  - Implementation: Cache-Control headers

Level 2: CDN Cache (CloudFront)
  - Static assets: 30 days
  - API responses: 1 minute (select endpoints)
  - Implementation: CloudFront distribution rules

Level 3: Application Cache (Redis)
  - User sessions: 24 hours
  - Pricing lookup: 1 hour (refresh with ML predictions)
  - Property availability: 15 minutes
  - User permissions: 6 hours
  - Exchange rates: 24 hours
  - Implementation: Redis hash/string/set operations

Level 4: Database Query Cache
  - Prepared statements
  - Connection pooling (PgBouncer): 100 connections
  - Implementation: PostgreSQL query optimization
```

#### Cache Invalidation Strategy

```
Manual Invalidation:
  - Booking created/updated: Clear availability cache
  - Pricing updated: Clear pricing lookup cache
  - User role changed: Clear permission cache

Automatic Invalidation:
  - TTL-based: Time-to-live for cached items
  - Event-based: Celery tasks trigger cache clears
  - Dependency-based: Clear dependent caches automatically
```

### 7.2 Database Query Optimization

#### Query Performance Targets

| Query Type | Target Response Time | Acceptable Range |
|-----------|---------------------|-----------------|
| Simple SELECT | 10ms | 5-20ms |
| JOIN queries (2-3 tables) | 50ms | 20-100ms |
| Aggregation queries | 200ms | 100-500ms |
| Report generation | 5 seconds | 1-10 seconds |

#### Optimization Techniques

1. **Indexing Strategy**
   - Index all foreign keys
   - Composite indexes for common filter combinations
   - Partial indexes for status-based queries
   - Analysis: Regular EXPLAIN ANALYZE reviews

2. **Query Optimization**
   - Use Django select_related() for foreign keys
   - Use prefetch_related() for reverse relationships
   - Limit result sets with pagination
   - Use aggregation for summaries

3. **Connection Pooling**
   - PgBouncer: 100-200 connections
   - Transaction pooling mode for efficiency
   - Circuit breaker for connection failures

### 7.3 Horizontal Scalability

#### API Server Scaling

```
Auto-scaling Policy:
  - Minimum instances: 2 (high availability)
  - Maximum instances: 10
  - Target CPU: 70%
  - Target Memory: 80%
  - Scale-up: 1 instance when threshold exceeded
  - Scale-down: Wait 5 minutes then remove 1 instance
  - Cooldown: 3 minutes between scale operations

Load Balancing:
  - Algorithm: Least Outstanding Requests
  - Health checks: Every 30 seconds
  - Sticky sessions: Disabled (stateless design)
```

#### Async Job Scaling

```
Celery Worker Scaling:
  - Minimum workers: 1
  - Maximum workers: 5
  - Queue monitoring: Dynamic scaling based on queue length
  - Job types: Separate queues for priority/speed

Job Types:
  - Pricing calculations: High priority, longer timeout (30min)
  - Email dispatch: Medium priority, 5min timeout
  - Report generation: Low priority, 10min timeout
  - Data sync: Low priority, 1 hour timeout
```

### 7.4 Performance Monitoring

#### Key Metrics

```
Application Metrics:
  - Request latency (p50, p95, p99 percentiles)
  - Throughput (requests/second)
  - Error rate (5xx, 4xx per endpoint)
  - Active connections

Database Metrics:
  - Query execution time
  - Slow queries (>100ms)
  - Connection pool utilization
  - Replication lag (if applicable)

Cache Metrics:
  - Cache hit rate (target: >80%)
  - Cache eviction rate
  - Memory utilization

Infrastructure Metrics:
  - CPU utilization per instance
  - Memory utilization per instance
  - Disk I/O rate
  - Network bandwidth
```

#### Monitoring Tools
- **Prometheus:** Metrics collection
- **Grafana:** Visualization dashboards
- **CloudWatch:** AWS native monitoring
- **DataDog:** Optional third-party APM

#### Alerting Rules

```
Critical Alerts:
  - API error rate > 5% (page on-call)
  - Database replication lag > 10s (page on-call)
  - API response time p99 > 5s (page on-call)
  - Database connection pool >90% (page on-call)

Warning Alerts:
  - API error rate > 1% (Slack notification)
  - API response time p95 > 1s (Slack notification)
  - Cache hit rate < 60% (Slack notification)
  - Disk usage > 80% (Slack notification)
```

---

## 8. IMPLEMENTATION ROADMAP

### Phase 2A: Core Infrastructure (Months 5-6)
- [ ] AWS account setup and VPC configuration
- [ ] Database schema implementation (PostgreSQL)
- [ ] Redis cache infrastructure
- [ ] Docker image creation and ECR setup
- [ ] ECS cluster and task definitions
- [ ] Load balancer and routing configuration
- [ ] Secrets management (AWS Secrets Manager)
- [ ] Monitoring and logging (CloudWatch, Prometheus)
- [ ] CI/CD pipeline setup (GitHub Actions)

### Phase 2B: API Development (Months 6-7)
- [ ] Authentication and authorization systems
- [ ] Core API endpoints (bookings, guests, rooms, payments)
- [ ] Database CRUD operations
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Integration with payment gateway (Stripe)
- [ ] Integration with email service (SendGrid)
- [ ] Error handling and validation
- [ ] Comprehensive API testing

### Phase 2C: Business Logic & Services (Month 8)
- [ ] Pricing service integration with ML engine
- [ ] Contract management system
- [ ] Reporting and BI features
- [ ] Notification service
- [ ] Integration service for OTAs
- [ ] Accounting system integration
- [ ] Performance optimization
- [ ] Security hardening

### Phase 2D: Testing & Launch (Months 8-9)
- [ ] Integration testing
- [ ] Performance testing (load testing)
- [ ] Security testing (penetration testing)
- [ ] User acceptance testing with pilot customers
- [ ] Production deployment
- [ ] Post-launch support

---

## 9. RECOMMENDATIONS & SUCCESS CRITERIA

### Critical Success Factors

1. **API Performance:** Achieve <200ms response time (p95) for all endpoints
2. **System Reliability:** 99.9% uptime SLA (maximum 43 minutes downtime/month)
3. **Data Security:** Zero data breaches, 100% GDPR compliance
4. **Code Quality:** Minimum 80% unit test coverage, zero critical bugs
5. **Scalability:** Support 1000+ concurrent users with consistent performance

### Development Team Guidance

1. **Code Quality**
   - Use Django best practices and patterns
   - Follow PEP 8 style guide
   - Implement comprehensive logging
   - Write testable, modular code

2. **Testing Strategy**
   - Unit tests for all business logic (target: 80% coverage)
   - Integration tests for API endpoints
   - Database migration tests
   - Contract tests for external integrations

3. **Documentation**
   - Auto-generate API docs from OpenAPI specs
   - Maintain architecture decision records (ADR)
   - Document all assumptions and dependencies
   - Keep runbooks for operations

4. **Security Review**
   - Security code review for all PRs
   - Regular dependency updates for vulnerabilities
   - Penetration testing before launch
   - Post-launch security monitoring

---

## 10. APPENDICES

### A. Technology Stack Summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.10+ | Mature, Django ecosystem, ML libraries |
| **Framework** | Django 4.2+ | Battle-tested, security-first, ORM |
| **API** | Django REST Framework | Industry standard, extensive ecosystem |
| **Database** | PostgreSQL 14+ | ACID compliance, JSON support, proven |
| **Cache** | Redis 6+ | Fast, in-memory, supports complex data types |
| **Async Jobs** | Celery + Redis | Distributed task processing, reliable |
| **Frontend** | React 18+ | Component-based, large ecosystem, performance |
| **Containerization** | Docker | Standard industry practice, reproducible builds |
| **Orchestration** | ECS Fargate | Managed Kubernetes alternative, cost-effective |
| **Cloud** | AWS | Mature, GDPR-compliant, extensive services |
| **Monitoring** | Prometheus + Grafana | Open-source, flexible, industry standard |
| **CI/CD** | GitHub Actions | Native GitHub integration, free for public repos |

### B. API Rate Limiting Configuration

```
Tier 1 (Public):
  - 60 requests per minute per IP
  - Used for: Public data queries, guest searches

Tier 2 (Authenticated):
  - 1000 requests per minute per user
  - Used for: All authenticated operations

Tier 3 (ML Pricing):
  - 10 requests per minute per property
  - Used for: Dynamic pricing calculations

Custom Limits:
  - Payment processing: 5 requests per minute (PCI compliance)
  - Authentication: 5 failed attempts before 15-minute lockout
```

### C. SLA & Support Metrics

```
Service Level Agreement (SLA):
  - Uptime: 99.9% (46min/month downtime allowance)
  - API response time p95: <200ms
  - Database query time p95: <100ms
  - Support response time: 1 hour (critical), 4 hours (high)

Support Channels:
  - Email: support@nephele.io
  - In-app messaging: Real-time support
  - Phone: +30-211-XXXXXXX (Greece)
  - Status page: status.nephele.io
```

### D. Data Privacy Officer Contact

- **Name:** [DPO Name]
- **Email:** dpo@nephele.io
- **Phone:** [Phone Number]
- **Availability:** 24/5 (weekdays)

---

**Document Status:** DRAFT FOR PREPARATION  
**Next Review Date:** March 19, 2026  
**Document Owner:** Architecture & Technical Design Team  
**Last Updated:** February 19, 2026
