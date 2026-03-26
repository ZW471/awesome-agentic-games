"""
Signal Lost — Message Reducer

Smart context management that collapses tool-call noise while preserving
narrative continuity. This is the key improvement over the CLI-based approach.
"""

from __future__ import annotations

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


def summarize_tool_calls(messages: list[BaseMessage]) -> str:
    """Summarize a sequence of tool calls into a compact one-line description."""
    summaries = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            # Extract the tool name and a brief result summary
            name = msg.name or "tool"
            content = str(msg.content)
            if len(content) > 80:
                content = content[:77] + "..."
            summaries.append(f"{name}: {content}")
        elif isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name", "tool")
                args = tc.get("args", {})
                # Compact representation of key args
                arg_str = ", ".join(f"{k}={v}" for k, v in list(args.items())[:2])
                summaries.append(f"called {name}({arg_str})")

    return " | ".join(summaries) if summaries else ""


def reduce_turn_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Collapse a completed turn's messages into a compact form.

    Keeps:
    - The player's input (HumanMessage)
    - The final narrative (last AIMessage with text content, no tool_calls)
    - A compact SystemMessage summarizing tool calls and state changes

    Removes:
    - All intermediate AIMessage with tool_calls (the LLM's internal reasoning)
    - All ToolMessage objects (raw tool results)
    """
    human_msgs = []
    tool_msgs = []
    final_narrative = None

    for msg in messages:
        if isinstance(msg, HumanMessage):
            human_msgs.append(msg)
        elif isinstance(msg, ToolMessage):
            tool_msgs.append(msg)
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                tool_msgs.append(msg)
            elif msg.content:
                final_narrative = msg

    result = list(human_msgs)

    # Add compact tool summary if there were tool calls
    tool_summary = summarize_tool_calls(tool_msgs)
    if tool_summary:
        result.append(SystemMessage(content=f"[Turn mechanics: {tool_summary}]"))

    if final_narrative:
        result.append(final_narrative)

    return result


def apply_sliding_window(
    messages: list[BaseMessage],
    max_recent_turns: int = 10,
    max_total_messages: int = 60,
) -> list[BaseMessage]:
    """Apply a sliding window to keep context manageable.

    Strategy:
    - Always keep the system message(s) at the start
    - Keep the last `max_recent_turns` turn pairs in full
    - Summarize older turns to one line each
    - Hard cap at `max_total_messages`
    """
    if len(messages) <= max_total_messages:
        return messages

    # Separate system messages from conversation
    system_msgs = []
    conversation = []
    for msg in messages:
        if isinstance(msg, SystemMessage) and not conversation:
            system_msgs.append(msg)
        else:
            conversation.append(msg)

    # Identify turn boundaries (each turn starts with a HumanMessage)
    turns: list[list[BaseMessage]] = []
    current_turn: list[BaseMessage] = []
    for msg in conversation:
        if isinstance(msg, HumanMessage) and current_turn:
            turns.append(current_turn)
            current_turn = []
        current_turn.append(msg)
    if current_turn:
        turns.append(current_turn)

    if len(turns) <= max_recent_turns:
        return messages

    # Summarize older turns
    old_turns = turns[:-max_recent_turns]
    recent_turns = turns[-max_recent_turns:]

    old_summaries = []
    for turn in old_turns:
        # Extract player action and AI response
        player_action = ""
        ai_response = ""
        for msg in turn:
            if isinstance(msg, HumanMessage):
                player_action = str(msg.content)[:60]
            elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                ai_response = str(msg.content)[:60]

        if player_action or ai_response:
            summary = f"Player: {player_action}"
            if ai_response:
                summary += f" → {ai_response}"
            old_summaries.append(summary)

    # Build compressed history
    result = list(system_msgs)
    if old_summaries:
        compressed = "\n".join(f"- {s}" for s in old_summaries)
        result.append(SystemMessage(
            content=f"[Earlier conversation summary ({len(old_turns)} turns):\n{compressed}]"
        ))

    for turn in recent_turns:
        result.extend(turn)

    return result
