# agent/session_store.py
from collections import defaultdict

# Each session_id → list of messages
# Messages are LangChain message objects, not plain strings
SESSION_HISTORY = defaultdict(list)