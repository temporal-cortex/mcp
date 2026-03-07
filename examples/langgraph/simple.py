#!/usr/bin/env python3
"""
Temporal Cortex + LangGraph: Minimal ReAct Agent

Connects to Temporal Cortex via stdio transport and builds a ReAct agent
that auto-discovers all 15 calendar tools. The agent follows a deterministic
workflow: orient in time, resolve datetimes, discover calendars, check
availability, and book conflict-free meetings.

Prerequisites:
  pip install -r requirements.txt
  npx @temporal-cortex/cortex-mcp auth google   # authenticate once

Usage:
  cp .env.example .env   # add your API key and calendar credentials
  python simple.py
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ChatAnthropic is the default. To use OpenAI instead:
#   from langchain_openai import ChatOpenAI
#   model = ChatOpenAI(model="gpt-4o")
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
    async with MultiServerMCPClient(
        {
            "temporal-cortex": {
                "command": "npx",
                "args": ["-y", "@temporal-cortex/cortex-mcp"],
                "env": {
                    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                    "TIMEZONE": os.getenv("TIMEZONE", ""),
                },
                "transport": "stdio",
            }
        }
    ) as client:
        tools = client.get_tools()
        agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

        result = await agent.ainvoke(
            {"messages": [("user", "Schedule a 30-minute Team Sync for next Tuesday at 2pm.")]}
        )

        # Print the final assistant message
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(msg.content)
                break


if __name__ == "__main__":
    asyncio.run(main())
