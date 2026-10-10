"""Prometheus metrics for channel sync health."""

from prometheus_client import Counter, Histogram

channel_sync_total = Counter(
    "nephele_channel_sync_total",
    "Channel availability sync attempts",
    ["channel_name", "status"],
)
channel_webhook_total = Counter(
    "nephele_channel_webhook_total",
    "Inbound channel webhooks",
    ["channel_name", "status"],
)
channel_sync_latency = Histogram(
    "nephele_channel_sync_latency_seconds",
    "Channel sync duration",
    ["channel_name"],
)
