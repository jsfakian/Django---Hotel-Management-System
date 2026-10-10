"""Payment gateway adapters (Viva Wallet default, Stripe alternate)."""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentGatewayError(Exception):
    pass


class PaymentGateway(ABC):
    name = "base"

    @abstractmethod
    def create_payment(
        self,
        *,
        amount: Decimal,
        currency: str = "EUR",
        description: str = "",
        customer_email: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        return_url: str = "",
    ) -> Dict[str, Any]:
        """Return {payment_id, redirect_url?, status}."""

    @abstractmethod
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Return {payment_id, status, paid: bool}."""


class VivaWalletGateway(PaymentGateway):
    """Greek Viva Wallet / Smart Checkout adapter."""

    name = "viva"

    def __init__(self):
        self.merchant_id = getattr(settings, "VIVA_MERCHANT_ID", "")
        self.api_key = getattr(settings, "VIVA_API_KEY", "")
        self.source_code = getattr(settings, "VIVA_SOURCE_CODE", "")
        self.api_base = getattr(
            settings, "VIVA_API_BASE", "https://demo-api.vivapayments.com"
        )

    def _auth(self):
        return (self.merchant_id, self.api_key)

    def create_payment(
        self,
        *,
        amount: Decimal,
        currency: str = "EUR",
        description: str = "",
        customer_email: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        return_url: str = "",
    ) -> Dict[str, Any]:
        if not self.merchant_id or not self.api_key:
            # Dev/demo path without credentials
            pid = f"viva-demo-{uuid.uuid4().hex[:12]}"
            return {
                "payment_id": pid,
                "status": "pending",
                "redirect_url": return_url or f"/payment-success?ref={pid}",
                "gateway": self.name,
                "demo": True,
            }

        # Amount in cents for Viva; SCA/3DS handled by Smart Checkout redirect
        amount_cents = int((amount * 100).quantize(Decimal("1")))
        meta = metadata or {}
        payload = {
            "amount": amount_cents,
            "customerTrns": description[:2048],
            "customer": {"email": customer_email},
            "sourceCode": self.source_code,
            "merchantTrns": str(meta.get("booking_id", "")),
            # Strong Customer Authentication — Smart Checkout collects 3DS challenge
            "paymentTimeout": int(meta.get("payment_timeout", 1800)),
            "preauth": bool(meta.get("preauth", False)),
            "allowRecurring": False,
        }
        if return_url:
            payload["successUrl"] = return_url
            payload["failureUrl"] = meta.get("failure_url") or return_url
        try:
            resp = requests.post(
                f"{self.api_base}/checkout/v2/orders",
                json=payload,
                auth=self._auth(),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise PaymentGatewayError(f"Viva error: {resp.status_code} {resp.text}")
            data = resp.json()
            order_code = data.get("orderCode") or data.get("OrderCode")
            checkout_host = (
                "www.vivapayments.com"
                if "demo" not in self.api_base
                else "demo.vivapayments.com"
            )
            return {
                "payment_id": str(order_code),
                "status": "pending",
                "redirect_url": f"https://{checkout_host}/web/checkout?ref={order_code}",
                "sca_required": True,
                "gateway": self.name,
                "raw": data,
            }
        except PaymentGatewayError:
            raise
        except Exception as exc:
            raise PaymentGatewayError(str(exc)) from exc

    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        if str(payment_id).startswith("viva-demo-"):
            return {"payment_id": payment_id, "status": "paid", "paid": True}
        if not self.merchant_id or not self.api_key:
            return {"payment_id": payment_id, "status": "unknown", "paid": False}
        try:
            resp = requests.get(
                f"{self.api_base}/checkout/v2/transactions/{payment_id}",
                auth=self._auth(),
                timeout=30,
            )
            data = resp.json() if resp.content else {}
            status_val = str(data.get("statusId") or data.get("status") or "").lower()
            paid = status_val in ("f", "finished", "paid", "captured", "1")
            return {
                "payment_id": payment_id,
                "status": "paid" if paid else status_val or "pending",
                "paid": paid,
                "raw": data,
            }
        except Exception as exc:
            raise PaymentGatewayError(str(exc)) from exc


class StripeGateway(PaymentGateway):
    name = "stripe"

    def create_payment(
        self,
        *,
        amount: Decimal,
        currency: str = "EUR",
        description: str = "",
        customer_email: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        return_url: str = "",
    ) -> Dict[str, Any]:
        secret = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not secret:
            pid = f"stripe-demo-{uuid.uuid4().hex[:12]}"
            return {
                "payment_id": pid,
                "status": "pending",
                "redirect_url": return_url or f"/payment-success?ref={pid}",
                "gateway": self.name,
                "demo": True,
            }
        try:
            import stripe

            stripe.api_key = secret
            intent = stripe.PaymentIntent.create(
                amount=int((amount * 100).quantize(Decimal("1"))),
                currency=currency.lower(),
                description=description,
                receipt_email=customer_email or None,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            return {
                "payment_id": intent.id,
                "status": intent.status,
                "client_secret": intent.client_secret,
                "gateway": self.name,
            }
        except Exception as exc:
            raise PaymentGatewayError(str(exc)) from exc

    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        if str(payment_id).startswith("stripe-demo-"):
            return {"payment_id": payment_id, "status": "paid", "paid": True}
        secret = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not secret:
            return {"payment_id": payment_id, "status": "unknown", "paid": False}
        import stripe

        stripe.api_key = secret
        intent = stripe.PaymentIntent.retrieve(payment_id)
        paid = intent.status == "succeeded"
        return {
            "payment_id": payment_id,
            "status": intent.status,
            "paid": paid,
        }


def get_payment_gateway(name: Optional[str] = None) -> PaymentGateway:
    chosen = (name or getattr(settings, "DEFAULT_PAYMENT_GATEWAY", "viva")).lower()
    if chosen == "stripe":
        return StripeGateway()
    return VivaWalletGateway()
