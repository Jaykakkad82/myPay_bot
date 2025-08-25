# agent_multi/tools_registry.py
from typing import List
from agent.lc_tools import (
    make_spend_summary_tool,
    make_spend_by_category_tool,
    make_search_transactions_tool,
    make_get_customer_tool,
    make_get_transaction_detail_tool,
    make_get_payment_tool,
    make_create_customer_tool,
    make_create_transaction_tool,
    make_make_payment_tool,
)

def build_read_only_tools() -> List:
    """Safe, read-only analytics + getters."""
    return [
        make_spend_summary_tool(),
        make_spend_by_category_tool(),
        make_search_transactions_tool(),
        make_get_customer_tool(),
        make_get_transaction_detail_tool(),
        make_get_payment_tool(),
    ]

def build_write_tools() -> List:
    """State-changing / sensitive tools. Keep minimal + guarded."""
    return [
        make_create_customer_tool(),
        make_create_transaction_tool(),
        make_make_payment_tool(),
    ]

def all_tools() -> List:
    return build_read_only_tools() + build_write_tools()
