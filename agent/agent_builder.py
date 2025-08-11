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
)

def build_agent() -> AgentExecutor:
    tools = [
        make_spend_summary_tool(),
        make_spend_by_category_tool(),
        make_search_transactions_tool(),
        # TODO: add the rest of your MCP tools similarly (get_customer, make_payment, etc.)
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
