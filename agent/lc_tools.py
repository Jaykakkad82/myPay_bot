from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from langchain.tools import StructuredTool
from .mcp_bridge import MCPBridge
from .config import MCP_URL, MCP_API_KEY

# ---------- Pydantic Schemas (inputs to tools) ----------

class SpendSummaryIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    customerId: int = Field(..., ge=1)
    from_: str = Field(..., alias="from", validation_alias=AliasChoices("from", "from_"))  # ISO timestamp
    to: str
    fxBase: str = "USD"

class SpendByCategoryIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    customerId: int = Field(..., ge=1)
    from_: str = Field(..., alias="from", validation_alias=AliasChoices("from", "from_"))
    to: str

class SearchTransactionsIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    customerId: Optional[int] = None
    status: Optional[str] = None
    category: Optional[str] = None
    currency: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from", validation_alias=AliasChoices("from", "from_"))
    to: Optional[str] = None
    page: int = 0
    size: int = 20
    sort: str = "createdAt,desc"

def _headers() -> Optional[dict]:
    return {"x-mcp-api-key": MCP_API_KEY} if MCP_API_KEY else None

# ---------- MCP -> LangChain tool factories ----------

def make_spend_summary_tool():
    async def _run(**kwargs):
        data = SpendSummaryIn.model_validate(kwargs)  # validate kwargs into model
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("spend_summary", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="spend_summary",
        description="Get spending summary. Use keys exactly: customerId, from, to, fxBase.",
        args_schema=SpendSummaryIn,
    )

def make_spend_by_category_tool():
    async def _run(**kwargs):
        data = SpendByCategoryIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("spend_by_category", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="spend_by_category",
        description="Category-wise totals. Use keys: customerId, from, to.",
        args_schema=SpendByCategoryIn,
    )

def make_search_transactions_tool():
    async def _run(**kwargs):
        data = SearchTransactionsIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("search_transactions", data.model_dump(by_alias=True, exclude_none=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="search_transactions",
        description="Search transactions by filters (customerId/status/category/currency, from/to, page/size).",
        args_schema=SearchTransactionsIn,
    )

class GetCustomerIn(BaseModel):
    customerId: int = Field(..., ge=1)

def make_get_customer_tool():
    async def _run(**kwargs):
        data = GetCustomerIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("get_customer", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="get_customer",
        description="Get customer details by customerId.",
        args_schema=GetCustomerIn,
    )

class MakePaymentIn(BaseModel):
    fromAccountId: int = Field(..., ge=1)
    toAccountId: int = Field(..., ge=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(...)

def make_make_payment_tool():
    async def _run(**kwargs):
        data = MakePaymentIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("make_payment", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="make_payment",
        description="Make a payment from one account to another. Use keys: fromAccountId, toAccountId, amount, currency.",
        args_schema=MakePaymentIn,
    )

class GetBalanceIn(BaseModel):
    accountId: int = Field(..., ge=1)

def make_get_balance_tool():
    async def _run(**kwargs):
        data = GetBalanceIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("get_balance", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="get_balance",
        description="Get account balance by accountId.",
        args_schema=GetBalanceIn,
    )

class ListAccountsIn(BaseModel):
    customerId: int = Field(..., ge=1)

def make_list_accounts_tool():
    async def _run(**kwargs):
        data = ListAccountsIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("list_accounts", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="list_accounts",
        description="List all accounts for a customerId.",
        args_schema=ListAccountsIn,
    )

class GetTransactionDetailIn(BaseModel):
    transactionId: int = Field(..., ge=1)

def make_get_transaction_detail_tool():
    async def _run(**kwargs):
        data = GetTransactionDetailIn.model_validate(kwargs)
        async with MCPBridge(MCP_URL) as mcp:
            return await mcp.call("get_transaction_detail", data.model_dump(by_alias=True), headers=_headers())
    return StructuredTool.from_function(
        coroutine=_run,
        name="get_transaction_detail",
        description="Get details for a transaction by transactionId.",
        args_schema=GetTransactionDetailIn,
    )
