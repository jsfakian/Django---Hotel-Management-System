# Business Intelligence & Reporting API Reference

## Overview

The Analytics API provides comprehensive business intelligence, reporting, and dashboard capabilities for the NEPHELE Hotel Management System.

**Base URL:** `/api/v1/analytics/`  
**Authentication:** JWT Bearer Token (required)  
**Response Format:** JSON

---

## Executive Dashboard

**Purpose:** Strategic overview for hotel managers and executives  
**Update Frequency:** Daily (nightly batch)  
**Audience:** Property owners, general managers, executives

### List Executive Metrics

```
GET /analytics/executive-dashboard/
```

**Query Parameters:**
- `property_id` (required): Integer - Property ID to filter metrics
- `metric_date__gte` (optional): Date - From date (YYYY-MM-DD)
- `metric_date__lte` (optional): Date - To date (YYYY-MM-DD)

**Response:**
```json
{
  "count": 90,
  "next": "http://api.nephele.io/api/v1/analytics/executive-dashboard/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "property": 1,
      "property_name": "Acropolis Hotel",
      "metric_date": "2026-02-19",
      "total_revenue": 5000.00,
      "avg_daily_rate": 150.00,
      "occupancy_rate": 85.00,
      "revpar": 127.50,
      "booking_count": 42,
      "revenue_trend_30d": {
        "2026-01-21": 4500.00,
        "2026-01-22": 4750.00,
        "2026-02-19": 5000.00
      },
      "occupancy_trend_30d": {
        "2026-01-21": 80.00,
        "2026-01-22": 82.00,
        "2026-02-19": 85.00
      },
      "adr_trend_30d": {
        "2026-01-21": 145.00,
        "2026-01-22": 148.00,
        "2026-02-19": 150.00
      },
      "yoy_revenue_change": 12.50,
      "yoy_occupancy_change": 8.75,
      "created_at": "2026-02-19T02:00:00Z",
      "updated_at": "2026-02-19T02:30:00Z"
    }
  ]
}
```

**Permissions:** `view_analytics`

### Get Latest Executive Metrics

```
GET /analytics/executive-dashboard/current/
```

**Query Parameters:**
- `property_id` (required): Integer

**Response:**
```json
{
  "id": 1,
  "property": 1,
  "property_name": "Acropolis Hotel",
  "metric_date": "2026-02-19",
  "total_revenue": 5000.00,
  "avg_daily_rate": 150.00,
  "occupancy_rate": 85.00,
  "revpar": 127.50,
  "booking_count": 42,
  ...
}
```

**Permissions:** `view_analytics`

### Get Metric Trends

```
GET /analytics/executive-dashboard/trend/
```

**Query Parameters:**
- `property_id` (required): Integer
- `metric` (optional): String - Metric name (default: `total_revenue`)
  - Options: `total_revenue`, `occupancy_rate`, `avg_daily_rate`, `revpar`
- `days` (optional): Integer - Number of days to retrieve (default: 90)

**Response:**
```json
{
  "metric": "total_revenue",
  "period_days": 30,
  "data": [
    {
      "metric_date": "2026-01-21",
      "total_revenue": 4500.00
    },
    {
      "metric_date": "2026-01-22",
      "total_revenue": 4750.00
    },
    {
      "metric_date": "2026-02-19",
      "total_revenue": 5000.00
    }
  ]
}
```

**Permissions:** `view_analytics`

---

## Operational Dashboard

**Purpose:** Real-time operations overview for hotel staff  
**Update Frequency:** Real-time (on-demand)  
**Audience:** Front desk, housekeeping, operations managers

### Get Current Operational Status

```
GET /analytics/operational-dashboard/current/
```

**Query Parameters:**
- `property_id` (required): Integer

**Response:**
```json
{
  "id": 42,
  "property": 1,
  "property_name": "Acropolis Hotel",
  "status_date": "2026-02-19",
  "status_time": "2026-02-19T14:30:00Z",
  "occupied_count": 42,
  "vacant_count": 8,
  "cleaning_count": 0,
  "maintenance_count": 0,
  "blocked_count": 0,
  "total_rooms": 50,
  "occupancy_percentage": 84.00,
  "checkouts_scheduled": 8,
  "checkins_scheduled": 10,
  "housekeeping_tasks_pending": 2,
  "housekeeping_tasks_in_progress": 1,
  "maintenance_tickets_pending": 1,
  "active_guests_count": 42,
  "guests_with_special_requests": 3,
  "created_at": "2026-02-19T14:30:00Z"
}
```

**Permissions:** `view_operational_dashboard`

---

## Revenue Analytics

**Purpose:** Financial performance and revenue management  
**Update Frequency:** Daily (midnight)  
**Audience:** Revenue managers, finance team, executives

### List Revenue Metrics

```
GET /analytics/revenue-analytics/
```

**Query Parameters:**
- `property_id` (optional): Integer
- `from_date` (optional): Date (YYYY-MM-DD)
- `to_date` (optional): Date (YYYY-MM-DD)

**Response:**
```json
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "property": 1,
      "property_name": "Acropolis Hotel",
      "metric_date": "2026-02-19",
      "total_revenue": 5000.00,
      "revenue_direct": 2500.00,
      "revenue_ota": 1500.00,
      "revenue_agency": 1000.00,
      "avg_daily_rate": 150.00,
      "revpar": 127.50,
      "dynamic_pricing_uplift": 8.33,
      "occupancy_rate": 85.00,
      "occupancy_count": 42,
      "booking_count": 42,
      "cancellation_count": 2,
      "cancellation_rate": 4.76,
      "noshow_count": 1,
      "revenue_forecast_30d": 150000.00,
      "occupancy_forecast_30d": 82.50,
      "metrics_by_source": {
        "direct": {
          "count": 20,
          "revenue": 2500.00,
          "adr": 125.00
        },
        "ota": {
          "count": 15,
          "revenue": 1500.00,
          "adr": 100.00
        },
        "agency": {
          "count": 7,
          "revenue": 1000.00,
          "adr": 142.86
        }
      },
      "created_at": "2026-02-19T02:00:00Z",
      "updated_at": "2026-02-19T02:30:00Z"
    }
  ]
}
```

**Permissions:** `view_revenue_analytics`

### Get Revenue Summary

```
GET /analytics/revenue-analytics/summary/
```

**Query Parameters:**
- `property_id` (required): Integer
- `from_date` (optional): Date
- `to_date` (optional): Date

**Response:**
```json
{
  "total_revenue": 150000.00,
  "avg_adr": 148.50,
  "avg_revpar": 126.25,
  "avg_occupancy": 84.75,
  "total_bookings": 1000,
  "total_cancellations": 50
}
```

**Permissions:** `view_revenue_analytics`

### Get Revenue by Source

```
GET /analytics/revenue-analytics/by_source/
```

**Query Parameters:**
- `property_id` (required): Integer
- `period` (optional): String - `day|week|month|quarter|year` (default: `month`)

**Response:**
```json
{
  "property_id": 1,
  "period": "month",
  "breakdown": [
    {
      "revenue_direct": 2500.00,
      "revenue_ota": 1500.00,
      "revenue_agency": 1000.00
    }
  ]
}
```

**Permissions:** `view_revenue_analytics`

---

## Guest Analytics

**Purpose:** Guest insights, segmentation, and personalization  
**Update Frequency:** Daily (midnight)  
**Audience:** Marketing team, personalization engine, customer success

### List Guest Analytics

```
GET /analytics/guest-analytics/
```

**Query Parameters:**
- `property_id` (required): Integer
- `from_date` (optional): Date
- `to_date` (optional): Date

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "property": 1,
      "property_name": "Acropolis Hotel",
      "analytics_date": "2026-02-19",
      "total_unique_guests": 42,
      "new_guests": 10,
      "returning_guests": 32,
      "repeat_booking_rate": 76.19,
      "avg_booking_lead_days": 14,
      "avg_length_of_stay": 3.5,
      "avg_review_score": 4.5,
      "avg_nps": 72,
      "review_rate": 85.71,
      "complaint_count": 2,
      "complaint_resolution_rate": 100.00,
      "retention_rate": 95.24,
      "churn_rate": 4.76,
      "at_risk_guests": 2,
      "recommendations_generated": 42,
      "recommendations_accepted": 29,
      "upsell_conversions": 5,
      "cross_sell_conversions": 3,
      "personalization_revenue_uplift": 5.50,
      "guest_segments": {
        "leisure": 65.0,
        "business": 30.0,
        "family": 5.0
      },
      "geographic_breakdown": {
        "Greece": 60,
        "Germany": 15,
        "UK": 10,
        "Other": 15
      },
      "created_at": "2026-02-19T02:00:00Z"
    }
  ]
}
```

**Permissions:** `view_guest_analytics`

### Get Guest Segments

```
GET /analytics/guest-analytics/segments/
```

**Query Parameters:**
- `property_id` (required): Integer

**Response:**
```json
{
  "property_id": 1,
  "segments": {
    "leisure": {
      "percentage": 65.0,
      "count": 27,
      "avg_spend": 175.00,
      "avg_los": 3.8,
      "satisfaction": 4.6
    },
    "business": {
      "percentage": 30.0,
      "count": 13,
      "avg_spend": 200.00,
      "avg_los": 2.1,
      "satisfaction": 4.3
    },
    "family": {
      "percentage": 5.0,
      "count": 2,
      "avg_spend": 350.00,
      "avg_los": 4.5,
      "satisfaction": 4.8
    }
  }
}
```

**Permissions:** `view_guest_analytics`

### Get Churn Analysis

```
GET /analytics/guest-analytics/churn/
```

**Query Parameters:**
- `property_id` (required): Integer

**Response:**
```json
{
  "property_id": 1,
  "churn_data": [
    {
      "analytics_date": "2026-02-19",
      "retention_rate": 95.24,
      "churn_rate": 4.76,
      "at_risk_guests": 2
    },
    {
      "analytics_date": "2026-02-18",
      "retention_rate": 93.50,
      "churn_rate": 6.50,
      "at_risk_guests": 3
    }
  ]
}
```

**Permissions:** `view_guest_analytics`

---

## Custom Reports

**Purpose:** User-defined reports for analytics export  
**Update Frequency:** On-demand  
**Audience:** All authorized users

### List Custom Reports

```
GET /analytics/custom-reports/
```

**Query Parameters:**
- `property_id` (optional): Integer - Filter by property

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "property": 1,
      "property_name": "Acropolis Hotel",
      "created_by": 10,
      "created_by_name": "John Manager",
      "name": "February 2026 Revenue Report",
      "description": "Comprehensive revenue analysis for February",
      "report_type": "revenue",
      "from_date": "2026-02-01",
      "to_date": "2026-02-28",
      "include_charts": true,
      "include_summary": true,
      "include_detailed_data": true,
      "export_format": "pdf",
      "file_path": "/reports/20260219_revenue_report.pdf",
      "status": "generated",
      "error_message": "",
      "generated_at": "2026-02-19T03:15:00Z",
      "created_at": "2026-02-18T10:30:00Z",
      "updated_at": "2026-02-19T03:15:00Z"
    }
  ]
}
```

**Permissions:** `view_reports` (own reports) or `manage_reports` (all)

### Create Custom Report

```
POST /analytics/custom-reports/
```

**Request Body:**
```json
{
  "property": 1,
  "name": "March 2026 Revenue Report",
  "description": "Comprehensive revenue analysis for March",
  "report_type": "revenue",
  "from_date": "2026-03-01",
  "to_date": "2026-03-31",
  "include_charts": true,
  "include_summary": true,
  "include_detailed_data": true,
  "export_format": "pdf"
}
```

**Response:** (201 Created)
```json
{
  "id": 6,
  "property": 1,
  "property_name": "Acropolis Hotel",
  "created_by": 10,
  "created_by_name": "John Manager",
  "name": "March 2026 Revenue Report",
  "report_type": "revenue",
  "status": "pending",
  "created_at": "2026-02-19T15:00:00Z",
  ...
}
```

**Permissions:** `view_reports` (create own)

### Generate Report

```
POST /analytics/custom-reports/{id}/generate/
```

**Response:**
```json
{
  "message": "Report generation started",
  "status": "pending",
  "report_id": 6
}
```

**Permissions:** `export_analytics`

### Download Report

```
GET /analytics/custom-reports/{id}/download/
```

**Response:**
```json
{
  "download_url": "/media/reports/20260219_revenue_report.pdf",
  "format": "pdf",
  "generated_at": "2026-02-19T03:15:00Z"
}
```

**Permissions:** `view_reports` (own) or `export_analytics`

---

## Combined Dashboard Summary

**Purpose:** Get multiple dashboard data in one request

### Get Dashboard Summary

```
GET /analytics/dashboard/summary/
```

**Query Parameters:**
- `property_id` (required): Integer
- `dashboard_type` (optional): String - `executive|operational|revenue|guest|all` (default: `executive`)

**Response:**
```json
{
  "property_id": 1,
  "dashboard_type": "all",
  "data": {
    "executive": {
      "id": 1,
      "property_name": "Acropolis Hotel",
      "metric_date": "2026-02-19",
      "total_revenue": 5000.00,
      ...
    },
    "operational": {
      "id": 42,
      "property_name": "Acropolis Hotel",
      "status_date": "2026-02-19",
      "occupied_count": 42,
      ...
    },
    "revenue": {
      "id": 1,
      "property_name": "Acropolis Hotel",
      "metric_date": "2026-02-19",
      ...
    },
    "guest": {
      "id": 1,
      "property_name": "Acropolis Hotel",
      "analytics_date": "2026-02-19",
      ...
    }
  }
}
```

**Permissions:** User depends on dashboard_type

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "property_id query parameter required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "message": "No metrics available yet"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred."
}
```

---

## Rate Limiting

Analytics endpoints follow standard rate limiting:
- **Authenticated users:** 1000 requests/minute
- **Analytics export:** 50 requests/minute

---

## Performance Notes

- **Executive/Revenue/Guest Dashboards:** Updated nightly at 2 AM UTC
- **Operational Dashboard:** Real-time data, queries may take 100-200ms
- **Custom Reports:** Generated asynchronously, check status via download endpoint
- **Data Retention:** 3 years of historical data maintained

---

## Integration Examples

### Python (requests library)
```python
import requests

headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}

# Get executive dashboard
response = requests.get(
    'https://api.nephele.io/api/v1/analytics/executive-dashboard/current/',
    params={'property_id': 1},
    headers=headers
)

metrics = response.json()
```

### JavaScript (fetch API)
```javascript
const token = localStorage.getItem('jwt_token');

fetch('/api/v1/analytics/executive-dashboard/current/?property_id=1', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error(err));
```

---

**Last Updated:** February 19, 2026  
**API Version:** 1.0  
**Documentation Version:** 1.0
