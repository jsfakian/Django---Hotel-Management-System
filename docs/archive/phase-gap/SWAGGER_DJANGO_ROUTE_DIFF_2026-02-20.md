# Swagger vs Django Route Diff (Task 4)

Date: 2026-02-20

## Scope

Compare `swagger.yaml` to currently wired Django API routes under:
- `HMS/HMS/api_urls.py`
- `HMS/analytics/urls.py`
- `HMS/bookings/urls.py`

Status legend:
- **MATCHED**: implemented with compatible semantics
- **PARTIAL**: endpoint exists but path/method/payload differs
- **MISSING**: no implemented route

## Global Base Path Drift

- Swagger mixes unversioned paths (`/bookings`, `/analytics/...`) and versioned paths (`/api/v1/analytics/...`, `/api/analytics/...`).
- Django implementation is consistently under `/api/v1/`.

### Required decision

Choose one:
1) Normalize Swagger to `/api/v1/*` everywhere (recommended).
2) Add compatibility aliases in Django for unversioned and `/api/analytics/*` paths.

---

## Authentication

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| POST `/auth/login` | POST `/api/v1/auth/login/` | PARTIAL | Add alias path or update Swagger base path. Align payload/response keys with contract (`email/password`, `access_token/refresh_token`). |
| POST `/auth/logout` | Not implemented | MISSING | Add API endpoint to blacklist JWT refresh token / invalidate session token. |
| POST `/auth/refresh` | POST `/api/v1/auth/refresh/` | PARTIAL | Add alias or normalize Swagger path. Align request key (`refresh_token` vs SimpleJWT default `refresh`). |
| POST `/auth/register` | Not implemented (only legacy HTML view) | MISSING | Add DRF endpoint for user creation + role assignment. |
| POST `/auth/forgot-password` | Not implemented | MISSING | Add DRF endpoint for reset initiation flow. |

## Bookings

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET/POST `/bookings` | GET/POST `/api/v1/bookings/` | PARTIAL | Add alias or normalize Swagger path. |
| GET/PUT/DELETE `/bookings/{booking_id}` | GET/PUT/PATCH/DELETE `/api/v1/bookings/{id}/` | PARTIAL | Alias path parameter name and ensure PUT contract fields map cleanly. |
| GET `/bookings/{booking_id}/timeline` | Not implemented | MISSING | Add `@action(detail=True, methods=['get'], url_path='timeline')` on `BookingViewSet`. |

## Rooms

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET `/rooms` | GET `/api/v1/rooms/` | PARTIAL | Add alias or normalize Swagger path. |
| GET `/rooms/{room_id}/availability` | Not implemented | MISSING | Add `@action(detail=True, methods=['get'], url_path='availability')` in `RoomViewSet`. |
| GET `/rooms/{room_id}/pricing-history` | Not implemented | MISSING | Add `@action(detail=True, methods=['get'], url_path='pricing-history')` and query `PricingHistory`. |
| PUT `/rooms/{room_id}/pricing` | Not implemented | MISSING | Add `@action(detail=True, methods=['put'], url_path='pricing')` to update base/derived prices. |

## Guests

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET/POST `/guests` | GET/POST `/api/v1/guests/` | PARTIAL | Add alias or normalize Swagger path. |
| GET `/guests/{guest_id}` | GET `/api/v1/guests/{id}/` | PARTIAL | Alias param naming or normalize Swagger path. |
| PUT `/guests/{guest_id}/preferences` | Not implemented | MISSING | Add `@action(detail=True, methods=['put'], url_path='preferences')` in `GuestViewSet`. |

## Payments / Invoices

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET `/invoices` | GET `/api/v1/invoices/` (read-only) | PARTIAL | Add alias or normalize Swagger path. |
| POST `/invoices/{invoice_id}/pay` | Not implemented | MISSING | Add custom action on `InvoiceViewSet` or dedicated payment endpoint. |
| GET `/invoices/{invoice_id}/payment-status` | Not implemented | MISSING | Add custom action returning payment state and timestamps. |

## Reports (non-analytics)

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET `/reports/occupancy` | Not implemented | MISSING | Add dedicated report endpoint (aggregated occupancy output). |
| GET `/reports/revenue` | Not implemented | MISSING | Add dedicated revenue reporting endpoint with aggregation param. |
| GET `/reports/performance` | Not implemented | MISSING | Add KPI performance endpoint. |

## Analytics Core

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET `/analytics/executive-dashboard` | GET `/api/v1/analytics/executive-dashboard/` | PARTIAL | Add alias or normalize Swagger path. |
| GET `/analytics/operational-dashboard` | GET `/api/v1/analytics/operational-dashboard/` | PARTIAL | Same as above. |
| GET `/analytics/revenue-analytics` | GET `/api/v1/analytics/revenue-analytics/` | PARTIAL | Same as above. |
| GET `/analytics/guest-analytics` | GET `/api/v1/analytics/guest-analytics/` | PARTIAL | Same as above. |
| GET `/analytics/reports` | Not implemented directly | MISSING | Add route that proxies report generation/status summary. |
| GET `/analytics/custom-reports/{report_id}` | GET `/api/v1/analytics/custom-reports/{id}/` | PARTIAL | Alias path or normalize Swagger. |
| POST `/analytics/aggregate-metrics` | Not implemented | MISSING | Add custom aggregate endpoint (metric/date/grouping). |
| GET `/analytics/comparison` | Not implemented | MISSING | Add multi-property comparison endpoint. |
| GET `/analytics/forecast` | Not implemented | MISSING | Add generic forecast endpoint (metric + days). |
| GET `/analytics/export` | Not implemented | MISSING | Add export endpoint for csv/excel/pdf stream. |

## Scheduled Reports

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| `/api/v1/analytics/scheduled-reports/` (GET/POST) | Implemented via `ScheduledReportViewSet` | MATCHED | Keep. |
| `/api/v1/analytics/scheduled-reports/{id}/` (GET/PUT/DELETE) | Implemented | MATCHED | Keep. |
| `/api/v1/analytics/scheduled-reports/{id}/trigger/` | Implemented `trigger` action | MATCHED | Keep. |
| `/api/v1/analytics/scheduled-reports/{id}/test/` | Implemented `test` action | MATCHED | Keep. |
| `/api/v1/analytics/scheduled-reports/{id}/executions/` | Not nested; only `/api/v1/analytics/report-executions/` | PARTIAL | Add nested alias endpoint filtered by `scheduled_report_id`. |
| `/api/v1/analytics/scheduled-reports/{id}/executions/{exec_id}/` | Not implemented as nested route | MISSING | Add nested retrieve alias. |
| `/api/v1/analytics/reports/{exec_id}/download/` | Not implemented | MISSING | Add dedicated download endpoint (format selector). |
| `/api/v1/analytics/reports/{exec_id}/resend/` | Exists as `/api/v1/analytics/report-executions/{id}/resend/` | PARTIAL | Add alias route to existing action. |
| `/api/v1/analytics/delivery-tracking/{exec_id}/` | Exists as `/api/v1/analytics/report-executions/{id}/delivery_status/` | PARTIAL | Add alias route to existing action. |

## Forecasting

| Swagger | Current Django | Status | Action |
|---|---|---|---|
| GET `/api/analytics/occupancy-forecasts/` | GET `/api/v1/analytics/occupancy-forecasts/` | PARTIAL | Add `/api/analytics/` alias or normalize Swagger path to `/api/v1/analytics/`. |
| GET `/api/analytics/occupancy-forecasts/next-30-days/` | Implemented at `/api/v1/analytics/occupancy-forecasts/next_30_days/` (underscore DRF action path) | PARTIAL | Set `url_path='next-30-days'` on action or add alias route. |
| GET `/api/analytics/revenue-forecasts/next-30-days/` | Implemented at `/api/v1/analytics/revenue-forecasts/next_30_days/` | PARTIAL | Same action path normalization. |
| GET `/api/analytics/cancellation-predictions/high-risk/` | Implemented at `/api/v1/analytics/cancellation-predictions/high_risk/` | PARTIAL | Set `url_path='high-risk'` or alias. |
| GET `/api/analytics/noshow-predictions/overbooking-recommendations/` | Implemented at `/api/v1/analytics/noshow-predictions/overbooking_recommendations/` | PARTIAL | Set `url_path='overbooking-recommendations'` or alias. |
| GET `/api/analytics/forecast-metrics/health-check/` | Implemented at `/api/v1/analytics/forecast-metrics/health_check/` | PARTIAL | Set `url_path='health-check'` or alias. |

---

## Recommended Execution Order (Routes)

1. Fix auth contract endpoints (`register`, `logout`, `forgot-password`) and token payload keys.
2. Add missing booking/room/guest/invoice actions.
3. Add report endpoints (`/reports/*`) and analytics aggregate/comparison/forecast/export endpoints.
4. Add route aliases for scheduled-report nested paths.
5. Normalize forecasting action URL paths from underscores to hyphens.
6. Choose and apply one global base-path policy (`/api/v1/*` preferred).

## Important Contract Mismatches Beyond Path Names

1) Login payload/response shape mismatch likely exists versus SimpleJWT defaults.

2) Swagger `Booking` schema includes `confirmation_number`, while current serializer does not expose this field.

3) Swagger’s mixed base paths (`/analytics/*`, `/api/v1/analytics/*`, `/api/analytics/*`) are internally inconsistent and should be unified.
