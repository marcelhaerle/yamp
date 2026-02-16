import logging
from types import TracebackType
from typing import Any

import httpx
from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class PrometheusClientError(Exception):
    """Custom exception for errors related to Prometheus API queries."""

    pass


class PrometheusClient:
    """
    An asynchronous client for querying a Prometheus server.

    This client is designed to be used as an async context manager,
    which properly handles the lifecycle of the underlying `httpx.AsyncClient`.

    Args:
        base_url: The base URL of the Prometheus server.
    """

    def __init__(self, base_url: HttpUrl) -> None:
        self.base_url = str(base_url).rstrip("/")
        self.query_url = f"{self.base_url}/api/v1/query"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PrometheusClient":
        """Initializes the asynchronous HTTP client."""
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Ensures the asynchronous HTTP client is closed."""
        if self._client:
            await self._client.aclose()

    async def fetch_metric(self, query: str) -> list[dict[str, Any]]:
        """
        Executes a PromQL query and returns a simplified list of results.

        Args:
            query: The PromQL query string to execute.

        Returns:
            A list of dictionaries, where each dictionary represents a metric
            with its labels and the latest value.

        Raises:
            PrometheusClientError: If the client is not initialized, the request
                fails, or the Prometheus API returns an error.
        """
        if not self._client:
            raise PrometheusClientError("Client not initialized. Use 'async with'")

        try:
            response = await self._client.get(self.query_url, params={"query": query}, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "success":
                error_msg = data.get("error", "Unknown Prometheus API error")
                raise PrometheusClientError(f"Prometheus API error: {error_msg}")

            return self._transform_data(data)

        except httpx.RequestError as e:
            logger.error(f"HTTP request to Prometheus failed: {e}")
            raise PrometheusClientError(f"Connection to Prometheus failed: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Prometheus: {e.response.status_code}, {e.response.text}")
            raise PrometheusClientError(f"Prometheus returned status {e.response.status_code}") from e

    def _transform_data(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extracts the 'result' from a Prometheus vector response.

        This method simplifies the complex structure of a Prometheus vector
        query result into a more straightforward list of dictionaries.

        Example:
            From:
            {
                'metric': {'instance': 'node1', '__name__': 'up'},
                'value': [1645000000, '1.23']
            }
            To:
            {
                'metric': {'instance': 'node1', '__name__': 'up'},
                'value': 1.23
            }
        """
        results = []
        for item in raw_data.get("data", {}).get("result", []):
            try:
                value = float(item.get("value", [0, "0"])[1])
                results.append({"metric": item.get("metric", {}), "value": value})
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse value from metric item: {item}. Error: {e}")
        return results
