"""
Abstract base class for external service connectors.
"""
from abc import ABC, abstractmethod



class BaseConnector(ABC):
    """
    Base interface for external service connectors.
    Each connector (Google Calendar, Fitbit, etc.) implements this interface.
    """

    @abstractmethod
    def connector_type(self) -> str:
        """Return the connector type identifier."""
        ...

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Validate and store authentication credentials."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test that the connection is working."""
        ...

    @abstractmethod
    async def sync(self, full: bool = False) -> dict:
        """
        Sync data from the external service.
        Returns a summary dict with records_fetched, records_created, etc.
        """
        ...

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> dict:
        """Handle an incoming webhook from the external service."""
        ...

    async def disconnect(self) -> None:
        """Clean up resources when disconnecting."""
        pass
