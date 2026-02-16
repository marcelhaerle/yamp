import pytest
import respx
from httpx import Response
from pydantic import HttpUrl

from app.core.prometheus import PrometheusClient, PrometheusClientError


@pytest.fixture
def prometheus_client() -> PrometheusClient:
    return PrometheusClient(base_url=HttpUrl("http://localhost:9090"))


@pytest.mark.asyncio
@respx.mock
async def test_fetch_metric_success(prometheus_client: PrometheusClient) -> None:
    mock_response = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": {"instance": "lxc-01"}, "value": [0, "0.85"]}],
        },
    }
    respx.get("http://localhost:9090/api/v1/query").mock(return_value=Response(200, json=mock_response))

    async with prometheus_client as client:
        results = await client.fetch_metric("up")

    assert len(results) == 1
    assert results[0]["metric"] == {"instance": "lxc-01"}
    assert results[0]["value"] == 0.85


@pytest.mark.asyncio
@respx.mock
async def test_fetch_metric_http_error(prometheus_client: PrometheusClient) -> None:
    respx.get("http://localhost:9090/api/v1/query").mock(return_value=Response(500))

    with pytest.raises(PrometheusClientError, match="Prometheus returned status 500"):
        async with prometheus_client as client:
            await client.fetch_metric("up")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_metric_api_error(prometheus_client: PrometheusClient) -> None:
    mock_response = {"status": "error", "errorType": "bad_data", "error": "test error"}
    respx.get("http://localhost:9090/api/v1/query").mock(return_value=Response(200, json=mock_response))

    with pytest.raises(PrometheusClientError, match="Prometheus API error: test error"):
        async with prometheus_client as client:
            await client.fetch_metric("up")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_metric_no_results(prometheus_client: PrometheusClient) -> None:
    mock_response = {"status": "success", "data": {"resultType": "vector", "result": []}}
    respx.get("http://localhost:9090/api/v1/query").mock(return_value=Response(200, json=mock_response))

    async with prometheus_client as client:
        results = await client.fetch_metric("up")

    assert len(results) == 0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_metric_multiple_results(prometheus_client: PrometheusClient) -> None:
    mock_response = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {"metric": {"instance": "node-1"}, "value": [0, "1"]},
                {"metric": {"instance": "node-2", "device": "eth0"}, "value": [0, "0"]},
            ],
        },
    }
    respx.get("http://localhost:9090/api/v1/query").mock(return_value=Response(200, json=mock_response))

    async with prometheus_client as client:
        results = await client.fetch_metric("up")

    assert len(results) == 2
    assert results[0] == {"metric": {"instance": "node-1"}, "value": 1.0}
    assert results[1] == {"metric": {"instance": "node-2", "device": "eth0"}, "value": 0.0}


@pytest.mark.asyncio
async def test_transform_data_invalid_value(prometheus_client: PrometheusClient) -> None:
    """Ensure malformed data points are skipped."""
    raw_data = {
        "data": {
            "result": [
                {"metric": {"instance": "good"}, "value": [0, "1.23"]},
                {"metric": {"instance": "bad"}, "value": [0, "not-a-float"]},
                {"metric": {"instance": "no-value"}, "value": [0]},
            ]
        }
    }
    # Access the "private" method for this unit test
    results = prometheus_client._transform_data(raw_data)
    assert len(results) == 1
    assert results[0]["metric"]["instance"] == "good"
    assert results[0]["value"] == 1.23


@pytest.mark.asyncio
async def test_client_not_initialized(prometheus_client: PrometheusClient) -> None:
    """Ensure client fails if not used in a context block."""
    with pytest.raises(PrometheusClientError, match="Client not initialized"):
        await prometheus_client.fetch_metric("up")
