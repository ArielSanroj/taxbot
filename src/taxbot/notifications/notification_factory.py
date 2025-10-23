"""Notification factory for different notification providers."""

from __future__ import annotations

from typing import Protocol

from ..models.concept import Concept


class NotificationProvider(Protocol):
    """Protocol for notification providers."""

    def send_notification(self, concepts: list[Concept], **kwargs) -> bool:
        """Send notification about concepts."""
        ...


class NotificationFactory:
    """Factory for creating notification providers."""

    @staticmethod
    def create_email_provider():
        """Create email notification provider."""
        from .email_service import EmailService
        return EmailService()

    @staticmethod
    def create_slack_provider():
        """Create Slack notification provider (future implementation)."""
        # TODO: Implement Slack provider
        raise NotImplementedError("Slack provider not implemented yet")

    @staticmethod
    def create_webhook_provider():
        """Create webhook notification provider (future implementation)."""
        # TODO: Implement webhook provider
        raise NotImplementedError("Webhook provider not implemented yet")

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available notification providers."""
        return ["email"]  # Add more as they're implemented
