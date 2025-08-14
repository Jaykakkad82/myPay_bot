from typing import List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from .config import OPENAI_MODEL, VERBOSE
from .prompts import SYSTEM
from .lc_tools import (
    make_spend_summary_tool,
    make_spend_by_category_tool,
    make_search_transactions_tool,
    make_get_customer_tool,
    make_make_payment_tool,
    make_get_balance_tool,
    make_list_accounts_tool,
    make_get_transaction_detail_tool,
)

def build_agent() -> AgentExecutor:
    tools = [
        make_spend_summary_tool(),
        make_spend_by_category_tool(),
        make_search_transactions_tool(),
        # Add more MCP tools below
        make_get_customer_tool(),
        make_make_payment_tool(),
        make_get_balance_tool(),
        make_list_accounts_tool(),
        make_get_transaction_detail_tool(),
        # Add any additional tools as needed
    ]

    prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=VERBOSE)
