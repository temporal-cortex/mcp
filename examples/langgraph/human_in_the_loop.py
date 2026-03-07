#!/usr/bin/env python3
"""
Temporal Cortex + LangGraph: Human-in-the-Loop Booking Approval

Demonstrates LangGraph's interrupt() mechanism for gating calendar
booking. Read-only tools (temporal context, calendar queries) run
automatically, but write operations (book_slot) pause for human
approval before execution.

This is the LangGraph-native approval pattern. It maps to the MCP
tool annotations where booking tools have readOnlyHint: false.

Flow:
  1. ReAct agent runs temporal analysis + availability check (auto)
  2. Agent proposes a booking → graph pauses via interrupt()
  3. Human reviews and approves or rejects
  4. Graph resumes → agent books the slot or suggests alternatives

Prerequisites:
  pip install -r requirements.txt
  npx @temporal-cortex/cortex-mcp auth google   # authenticate once

Usage:
  cp .env.example .env   # add your credentials
  python human_in_the_loop.py
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
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

# Tool names that require human approval before execution.
# These map to MCP tool annotations with readOnlyHint: false.
WRITE_TOOLS = {"book_slot", "request_booking"}


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

        # Use MemorySaver to enable interrupt/resume.
        # In production, use PostgresSaver for persistence across restarts.
        checkpointer = MemorySaver()

        agent = create_react_agent(
            model,
            tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            # interrupt_before gates tool execution: the graph pauses
            # before calling any tool in WRITE_TOOLS, giving the human
            # a chance to approve or reject.
            interrupt_before=["tools"],
        )

        config = {"configurable": {"thread_id": "scheduling-session-1"}}

        # Step 1: Start the scheduling workflow
        print("Starting scheduling workflow...\n")
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="Schedule a 30-minute Team Sync for next Tuesday at 2pm.")]},
            config=config,
        )

        # Step 2: The graph pauses before tool calls.
        # Check if the pending tool call is a write operation.
        last_message = result["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            pending_tool = last_message.tool_calls[0]
            tool_name = pending_tool["name"]

            if tool_name in WRITE_TOOLS:
                print(f"Approval required for: {tool_name}")
                print(f"Arguments: {pending_tool['args']}")
                print()

                # In production, wire this to a UI dialog, Slack message,
                # or approval queue. Here we use terminal input.
                approval = input("Approve this booking? (y/n): ").strip().lower()

                if approval == "y":
                    # Resume the graph — the tool call will execute
                    print("\nApproved. Booking...\n")
                    result = await agent.ainvoke(None, config=config)
                else:
                    # Resume with a rejection message — agent will adapt
                    print("\nRejected. Agent will suggest alternatives.\n")
                    result = await agent.ainvoke(
                        {"messages": [HumanMessage(content="Reject this booking. Suggest alternative times.")]},
                        config=config,
                    )
            else:
                # Non-write tool — let the graph continue automatically
                result = await agent.ainvoke(None, config=config)

        # Print the final result
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(msg.content)
                break


if __name__ == "__main__":
    asyncio.run(main())
