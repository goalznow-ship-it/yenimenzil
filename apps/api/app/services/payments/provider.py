"""Payment provider abstraction.

IdealEv.az never trusts payment success reported by the frontend.
Every provider must be confirmed server-side via webhook or admin action.

Providers:
- mock: local development. Payments created as pending; a simulated
  webhook can confirm them. No real money, no external dependency.
- stripe: optional production provider, enabled only when configured.
- manual: default fallback; confirmation happens through the admin panel.
"""

from __future__ import annotations

import hmac
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.core.config import get_settings

settings = get_settings()


class ProviderError(Exception):
    """Raised when a provider rejects or fails a payment operation."""


@dataclass
class ProviderResult:
    provider_payment_id: str | None = None
    checkout_url: str | None = None


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    name: str = "base"

    @abstractmethod
    async def create_payment(
        self,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ProviderResult:
        """Create a payment intent with the provider."""

    @abstractmethod
    async def refund_payment(self, provider_payment_id: str) -> None:
        """Refund an already paid payment."""

    def verify_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        """Verify and parse an incoming webhook.

        Returns the parsed payload dict. Raises ProviderError on invalid
        signature or malformed payload.
        """
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Local development provider with simulated webhooks.

    No real money is moved. Confirmations happen through the simulated
    webhook endpoint or the admin panel.
    """

    name = "mock"

    def __init__(self) -> None:
        self._secret = settings.MOCK_PAYMENT_WEBHOOK_SECRET or "mock-dev-secret"

    async def create_payment(
        self,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ProviderResult:
        payment_id = f"mock_{sha256(idempotency_key.encode()).hexdigest()[:24]}"
        return ProviderResult(provider_payment_id=payment_id)

    async def refund_payment(self, provider_payment_id: str) -> None:
        return None

    def verify_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        expected = hmac.new(self._secret.encode(), payload, sha256).hexdigest()
        if not signature or not hmac.compare_digest(expected, signature):
            raise ProviderError("Invalid webhook signature")
        return json.loads(payload.decode("utf-8"))


class StripePaymentProvider(PaymentProvider):
    """Optional production provider using the Stripe API.

    Only instantiated when STRIPE_SECRET_KEY is configured. Keys are never
    committed to the repository; they come from the environment.
    """

    name = "stripe"

    def __init__(self) -> None:
        if not settings.STRIPE_SECRET_KEY:
            raise ProviderError("STRIPE_SECRET_KEY is not configured")
        import stripe  # type: ignore[import-not-found]

        self._stripe = stripe
        self._stripe.api_key = settings.STRIPE_SECRET_KEY
        self._webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_payment(
        self,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ProviderResult:
        intent = self._stripe.PaymentIntent.create(
            amount=amount,
            currency=currency.lower(),
            description=description,
            automatic_payment_methods={"enabled": True},
            idempotency_key=idempotency_key,
        )
        return ProviderResult(
            provider_payment_id=intent.id,
            checkout_url=intent.client_secret,
        )

    async def refund_payment(self, provider_payment_id: str) -> None:
        self._stripe.Refund.create(payment_intent=provider_payment_id)

    def verify_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        if not self._webhook_secret or not signature:
            raise ProviderError("Stripe webhook secret not configured")
        event = self._stripe.Webhook.construct_event(
            payload, signature, self._webhook_secret
        )
        return {
            "event_type": event["type"],
            "object": event["data"]["object"],
        }


class ManualPaymentProvider(PaymentProvider):
    """Manual (offline) provider. Confirmed by admins only."""

    name = "manual"

    async def create_payment(
        self,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ProviderResult:
        return ProviderResult(provider_payment_id=None)

    async def refund_payment(self, provider_payment_id: str) -> None:
        return None

    def verify_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        raise ProviderError("Manual provider has no webhooks")


_PROVIDERS: dict[str, PaymentProvider] = {}


def get_payment_provider() -> PaymentProvider:
    """Return the configured provider (lazily, cached)."""
    provider_name = settings.PAYMENT_PROVIDER
    if provider_name not in _PROVIDERS:
        if provider_name == "stripe":
            _PROVIDERS[provider_name] = StripePaymentProvider()
        elif provider_name == "mock":
            if (
                settings.APP_ENV == "production"
                and not settings.ALLOW_MOCK_PAYMENTS_IN_PROD
            ):
                raise RuntimeError(
                    "Mock payments are forbidden in production "
                    "(set ALLOW_MOCK_PAYMENTS_IN_PROD=true only for staging)"
                )
            _PROVIDERS[provider_name] = MockPaymentProvider()
        else:
            _PROVIDERS[provider_name] = ManualPaymentProvider()
    return _PROVIDERS[provider_name]


def provider_supports_webhooks(provider: PaymentProvider) -> bool:
    return provider.name in ("mock", "stripe")
