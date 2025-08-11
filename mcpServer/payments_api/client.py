from typing import Any, Dict, Optional
import httpx
from mcpServer.config import MY_PAYMENTS_BASE_URL, MY_PAYMENTS_API_KEY, REQUEST_TIMEOUT_SECS

# This client implementation is used to make API calls to the specified API ( This is where API is wrapped)
class PaymentsApiClient:
    def __init__(self, base_url: str = MY_PAYMENTS_BASE_URL, api_key: str = MY_PAYMENTS_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self._client: Optional[httpx.AsyncClient] = None

    # Asynchronous code defined with async def needs an event loop to run. 
    #The asyncio library provides the necessary infrastructure for managing and executing these coroutines within an event loop.
    async def _ac(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(REQUEST_TIMEOUT_SECS),
                headers=self.headers
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # --- Customers ---
    async def create_customer(self, payload: Dict[str, Any]) -> Dict[str, Any]:     #async def defines a coroutine function
        ac = await self._ac()                                       # await in this line means lazy initialization of the HTTP client
        r = await ac.post("/customers", json=payload)               # await means non-blocking HTTP call; yields to event loop
        r.raise_for_status()
        return r.json()

    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get(f"/customers/{customer_id}")
        r.raise_for_status()
        return r.json()

    async def list_customer_transactions(self, customer_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get(f"/customers/{customer_id}/transactions", params=params)
        r.raise_for_status()
        return r.json()

    # --- Transactions ---
    async def create_transaction(self, payload: Dict[str, Any], idempotency_key: str | None) -> Dict[str, Any]:
        ac = await self._ac()
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        r = await ac.post("/transactions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    async def get_transaction(self, tx_id: int) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get(f"/transactions/{tx_id}")
        r.raise_for_status()
        return r.json()

    async def search_transactions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get("/transactions", params=params)
        r.raise_for_status()
        return r.json()

    async def cancel_transaction(self, tx_id: int, idempotency_key: str | None) -> Dict[str, Any]:
        ac = await self._ac()
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        r = await ac.post(f"/transactions/{tx_id}/cancel", headers=headers)
        r.raise_for_status()
        return r.json()

    # --- Payments ---
    async def make_payment(self, payload: Dict[str, Any], idempotency_key: str | None) -> Dict[str, Any]:
        ac = await self._ac()
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        r = await ac.post("/payments", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    async def get_payment(self, payment_id: int) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get(f"/payments/{payment_id}")
        r.raise_for_status()
        return r.json()

    async def get_payment_by_tx(self, tx_id: int) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get(f"/transactions/{tx_id}/payment")
        r.raise_for_status()
        return r.json()

    async def retry_payment(self, payment_id: int, idempotency_key: str | None) -> Dict[str, Any]:
        ac = await self._ac()
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        r = await ac.post(f"/payments/{payment_id}/retry", headers=headers)
        r.raise_for_status()
        return r.json()

    async def fail_payment(self, payment_id: int, reason_code: str, idempotency_key: str | None) -> Dict[str, Any]:
        ac = await self._ac()
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        r = await ac.post(f"/payments/{payment_id}/fail", params={"reasonCode": reason_code}, headers=headers)
        r.raise_for_status()
        return r.json()

    # --- Analytics ---
    async def spend_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get("/analytics/spend-summary", params=params)
        r.raise_for_status()
        return r.json()

    async def spend_by_category(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get("/analytics/spend-by-category", params=params)
        r.raise_for_status()
        return r.json()

    async def time_series(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ac = await self._ac()
        r = await ac.get("/analytics/time-series", params=params)
        r.raise_for_status()
        return r.json()
