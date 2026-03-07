#!/usr/bin/env python3
"""
Publish the Temporal Cortex scheduling agent prompt to LangSmith Hub.

This script pushes a reusable system prompt to smith.langchain.com/hub
at the handle `temporal-cortex/calendar-scheduling-agent`. Consumers
can pull it with:

    from langsmith import hub
    prompt = hub.pull("temporal-cortex/calendar-scheduling-agent")
    agent = create_react_agent(model, tools, prompt=prompt)

Prerequisites:
  pip install langsmith langchain-core
  export LANGSMITH_API_KEY=ls-...   # from smith.langchain.com Settings → API Keys

Usage:
  python publish_hub_prompt.py
"""

import os

from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

# The scheduling agent system prompt — encodes the deterministic workflow
# that prevents date hallucination and ensures correct tool-calling order.
SYSTEM_PROMPT = (
    "You schedule meetings using Temporal Cortex calendar tools.\n\n"
    "Follow this workflow:\n"
    "1. Call get_temporal_context to learn the current time and timezone\n"
    "2. Call resolve_datetime to convert human expressions to RFC 3339 timestamps\n"
    "3. Call list_calendars to discover connected calendars\n"
    "4. Call find_free_slots to check availability on the target date\n"
    "5. Call book_slot to book the meeting (Two-Phase Commit prevents double-bookings)\n\n"
    "Rules:\n"
    "- When calling data tools (list_calendars, list_events, find_free_slots, "
    "expand_rrule, get_availability), pass format='json' for structured output\n"
    "- Always use provider-prefixed calendar IDs (e.g., google/primary, outlook/work)\n"
    "- Never guess dates or times — always use the tools\n"
    "- Never skip the availability check before booking\n"
    "- If booking fails, report the error and suggest alternatives"
)

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}"),
])


def main():
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("Error: LANGSMITH_API_KEY not set.")
        print("Get your API key from smith.langchain.com → Settings → API Keys")
        return

    client = Client(api_key=api_key)

    handle = "temporal-cortex/calendar-scheduling-agent"
    description = (
        "System prompt for a calendar scheduling ReAct agent using "
        "Temporal Cortex MCP tools. Encodes a 5-step deterministic "
        "workflow: orient → resolve → discover → query → book. "
        "Prevents date hallucination and ensures correct tool-calling order."
    )

    url = client.push_prompt(
        handle,
        object=PROMPT_TEMPLATE,
        description=description,
        is_public=True,
    )

    print(f"Published to LangSmith Hub: {url}")
    print(f"\nConsumers can use it with:")
    print(f"  from langsmith import hub")
    print(f'  prompt = hub.pull("{handle}")')
    print(f"  agent = create_react_agent(model, tools, prompt=prompt)")


if __name__ == "__main__":
    main()
