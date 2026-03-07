#!/usr/bin/env python3
"""
Temporal Cortex + LangGraph: Platform Mode (HTTP Transport)

Same ReAct agent as simple.py, but connects to the managed Temporal Cortex
Platform instead of running locally. No Node.js or local OAuth credentials
needed — just an API key from app.temporal-cortex.com.

Benefits over Local Mode:
  - No Node.js or npx required
  - No local OAuth credentials to manage
  - Multi-agent coordination with distributed locking
  - Usage metering and content firewall
  - 3 additional Open Scheduling tools (15 total)

Prerequisites:
  pip install -r requirements.txt
  Sign up at app.temporal-cortex.com and generate an API key

Usage:
  cp .env.example .env   # add your API keys
  python simple_platform.py
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

model = ChatAnthropic(model="claude-sonnet-4-6")

SYSTEM_PROMPT = (
    "You schedule meetings using Temporal Cortex calendar tools.\n\n"
    "Follow this workflow:\n"
    "1. Call get_temporal_context to learn the current time and timezone\n"
    "2. Call resolve_datetime to convert human expressions to RFC 3339 timestamps\n"
    "3. Call list_calendars to discover connected calendars\n"
    "4. Call find_free_slots to check availability on the target date\n"
    "5. Call book_slot to book the meeting (Two-Phase Commit prevents double-bookings)\n\n"
    "When calling data tools (list_calendars, list_events, find_free_slots, "
    "expand_rrule, get_availability), pass format='json' for structured output.\n"
    "Always use provider-prefixed calendar IDs (e.g., google/primary).\n"
    "Never guess dates or times — always use the tools."
)


async def main():
    # HTTP transport — connects to the managed Temporal Cortex Platform.
    # No local server process, no Node.js required.
    # Get your API key from app.temporal-cortex.com
    async with MultiServerMCPClient(
        {
            "temporal-cortex": {
                "url": "https://mcp.temporal-cortex.com/mcp",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('TEMPORAL_CORTEX_API_KEY', '')}",
                },
                "transport": "streamable_http",
            }
        }
    ) as client:
        tools = client.get_tools()
        # Platform Mode discovers all 15 tools (including Open Scheduling)
        print(f"Discovered {len(tools)} Temporal Cortex tools")

        agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

        result = await agent.ainvoke(
            {"messages": [("user", "Schedule a 30-minute Team Sync for next Tuesday at 2pm.")]}
        )

        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(msg.content)
                break


if __name__ == "__main__":
    asyncio.run(main())
