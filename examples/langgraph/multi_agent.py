#!/usr/bin/env python3
"""
Temporal Cortex + LangGraph: Multi-Agent StateGraph

Builds a LangGraph StateGraph with three specialized nodes that mirror
Temporal Cortex's tool layer architecture:

  temporal_analyst  →  calendar_manager  →  booking_coordinator  →  END
  (Layer 1 tools)      (Layer 2 tools)      (Layer 4 tools)

Unlike the OpenAI Agents SDK pattern (Agent-as-Tool, LLM-driven routing),
LangGraph uses explicit graph control flow — the routing is deterministic,
guaranteeing tools are called in the correct order: orient → query → book.

Each node is a ReAct sub-agent scoped to its layer's tools. The graph state
carries structured results between nodes so downstream agents have the
context they need.

Prerequisites:
  pip install -r requirements.txt
  npx @temporal-cortex/cortex-mcp auth google   # authenticate once

Usage:
  cp .env.example .env   # add your credentials
  python multi_agent.py
"""

import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from typing_extensions import TypedDict

load_dotenv()

model = ChatAnthropic(model="claude-sonnet-4-6")

MCP_SERVER_CONFIG = {
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

# For Platform Mode (no Node.js needed), replace MCP_SERVER_CONFIG with:
# MCP_SERVER_CONFIG = {
#     "temporal-cortex": {
#         "url": "https://mcp.temporal-cortex.com/mcp",
#         "headers": {"Authorization": f"Bearer {os.getenv('TEMPORAL_CORTEX_API_KEY', '')}"},
#         "transport": "streamable_http",
#     }
# }


# --- State ---

class SchedulingState(TypedDict):
    """State passed between graph nodes."""

    messages: Annotated[list, add_messages]
    temporal_context: str
    available_slots: str
    booking_result: str


# --- Node functions ---


async def temporal_analyst(state: SchedulingState, client: MultiServerMCPClient) -> dict:
    """Orient in time and resolve datetime expressions (Layer 1 tools)."""
    tools = client.get_tools()
    # Filter to temporal context tools only
    temporal_tools = [t for t in tools if t.name in {
        "get_temporal_context", "resolve_datetime",
        "convert_timezone", "compute_duration", "adjust_timestamp",
    }]

    agent = create_react_agent(
        model,
        temporal_tools,
        prompt=(
            "You are a time-awareness specialist. Your job:\n"
            "1. Call get_temporal_context to learn current time, timezone, and DST status\n"
            "2. Call resolve_datetime to convert the user's datetime expression "
            "into a precise RFC 3339 timestamp\n\n"
            "Always pass format='json' to data tools. Return a summary of "
            "current time and resolved timestamp."
        ),
    )

    result = await agent.ainvoke({"messages": state["messages"]})

    # Extract temporal context from the last AI message
    context = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            context = msg.content
            break

    return {
        "temporal_context": context,
        "messages": [AIMessage(content=f"[Temporal Analyst] {context}")],
    }


async def calendar_manager(state: SchedulingState, client: MultiServerMCPClient) -> dict:
    """Discover calendars and find available slots (Layer 2 tools)."""
    tools = client.get_tools()
    calendar_tools = [t for t in tools if t.name in {
        "list_calendars", "list_events", "find_free_slots",
        "expand_rrule", "check_availability",
    }]

    agent = create_react_agent(
        model,
        calendar_tools,
        prompt=(
            "You are a calendar operations specialist. Your job:\n"
            "1. Call list_calendars to discover connected providers\n"
            "2. Call find_free_slots to find available time windows on the target date\n\n"
            "Always use provider-prefixed calendar IDs (e.g., google/primary).\n"
            "Always pass format='json' to data tools. Return the available slots."
        ),
    )

    # Include temporal context from previous node
    messages = state["messages"] + [
        HumanMessage(content=f"Temporal context: {state['temporal_context']}")
    ]
    result = await agent.ainvoke({"messages": messages})

    slots = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            slots = msg.content
            break

    return {
        "available_slots": slots,
        "messages": [AIMessage(content=f"[Calendar Manager] {slots}")],
    }


async def booking_coordinator(state: SchedulingState, client: MultiServerMCPClient) -> dict:
    """Book the best available slot (Layer 4 tools)."""
    tools = client.get_tools()
    booking_tools = [t for t in tools if t.name in {
        "book_slot", "check_availability",
    }]

    agent = create_react_agent(
        model,
        booking_tools,
        prompt=(
            "You are a booking specialist. Your job:\n"
            "1. Select the best slot from the available options\n"
            "2. Call book_slot with the calendar_id, title, start time, "
            "and duration_minutes\n\n"
            "book_slot uses Two-Phase Commit to prevent double-bookings.\n"
            "Always pass format='json' to data tools."
        ),
    )

    messages = state["messages"] + [
        HumanMessage(
            content=(
                f"Temporal context: {state['temporal_context']}\n"
                f"Available slots: {state['available_slots']}"
            )
        )
    ]
    result = await agent.ainvoke({"messages": messages})

    booking = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            booking = msg.content
            break

    return {
        "booking_result": booking,
        "messages": [AIMessage(content=f"[Booking Coordinator] {booking}")],
    }


# --- Build the graph ---


async def main():
    async with MultiServerMCPClient(MCP_SERVER_CONFIG) as client:
        # Build the scheduling graph
        graph = StateGraph(SchedulingState)

        # Add nodes — each uses the shared MCP client
        graph.add_node("temporal_analyst", lambda state: temporal_analyst(state, client))
        graph.add_node("calendar_manager", lambda state: calendar_manager(state, client))
        graph.add_node("booking_coordinator", lambda state: booking_coordinator(state, client))

        # Deterministic routing: orient → query → book → done
        graph.set_entry_point("temporal_analyst")
        graph.add_edge("temporal_analyst", "calendar_manager")
        graph.add_edge("calendar_manager", "booking_coordinator")
        graph.add_edge("booking_coordinator", END)

        app = graph.compile()

        # Run the scheduling workflow
        result = await app.ainvoke({
            "messages": [
                HumanMessage(content="Schedule a 30-minute Team Sync for next Tuesday at 2pm.")
            ],
            "temporal_context": "",
            "available_slots": "",
            "booking_result": "",
        })

        print("\n" + "=" * 60)
        print("SCHEDULING RESULT")
        print("=" * 60)
        print(result["booking_result"])


if __name__ == "__main__":
    asyncio.run(main())
