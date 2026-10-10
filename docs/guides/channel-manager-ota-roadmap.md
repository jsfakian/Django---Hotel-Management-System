# Channel manager OTA roadmap

Nephele’s channel layer is built around a small connector interface
(`push_availability`, `push_rates`, `pull_bookings`, `receive_webhook`) with an
honest stub policy: when an OTA is not certified or `BOOKING_COM_LIVE` is off,
connectors return `status=not_implemented` and never report fake success. iCal
is fully usable for two-way calendar blocking; Booking.com is the first live
HTTP path and activates only when credentials and `BOOKING_COM_LIVE=True` are
set against a configurable `BOOKING_COM_API_BASE`.

Expedia is registered as a thin skeleton (`expedia` in the connector registry)
with the message “next OTA by demand”. Implementation priority should follow
property mix: hotels that already sell heavily on Expedia/Hotels.com justify
EQC or Partner Central Connectivity work next; otherwise keep effort on Booking.com
certification, webhook reliability, and room/rate mapping tooling.

Further OTAs (Airbnb, Agoda, regional portals) should reuse the same registry
and mapping_config shape. Prefer one certified bidirectional connector at a time
over parallel half-stubs so ops can trust sync logs and Prometheus channel
metrics.
