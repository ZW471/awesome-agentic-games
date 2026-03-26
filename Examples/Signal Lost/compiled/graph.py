"""
Signal Lost — LangGraph StateGraph

The compiled game engine as a LangGraph graph.

Flow: input_gate → resolver (LLM + tools) → state_writer → world_ticker
      → trace_checker → consequence → [END or loop back]
"""

from __future__ import annotations

import copy
import json
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from state import GameState, append_conversation, empty_turn_delta, save_session_file
from tools import ALL_TOOLS
from game_data import (
    TRACE_CONDITIONS,
    ENDINGS,
    TIME_PERIODS,
    TURNS_PER_PERIOD,
    _trace_discovered,
    _count_discovered_traces,
)
from prompts import build_full_prompt
from reducer import reduce_turn_messages, apply_sliding_window


# ---------------------------------------------------------------------------
# LLM factory (provider-agnostic)
# ---------------------------------------------------------------------------

_llm_instance = None


def get_llm():
    """Get or create the LLM instance. Configured at runtime via run.py."""
    global _llm_instance
    if _llm_instance is None:
        raise RuntimeError(
            "LLM not configured. Call set_llm() before running the graph."
        )
    return _llm_instance


def set_llm(llm):
    """Set the LLM instance to use. Called by run.py."""
    global _llm_instance
    _llm_instance = llm


# ---------------------------------------------------------------------------
# Node: input_gate
# Pure Python. Loads state, builds dynamic prompt, prepares messages.
# ---------------------------------------------------------------------------

def _read_language_setting(session_dir: str) -> str:
    """Read language from settings/custom.json, falling back to 'en'."""
    import os as _os
    game_root = _os.path.abspath(_os.path.join(session_dir, ".."))
    custom_path = _os.path.join(game_root, "settings", "custom.json")
    try:
        with open(custom_path, "r", encoding="utf-8") as f:
            import json as _json
            settings = _json.load(f)
        return settings.get("language", {}).get("display", "en")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "en"


def input_gate(state: GameState) -> dict:
    """Prepare the LLM context for this turn."""
    # Read language from settings
    language = _read_language_setting(state["session_dir"])

    # Build the full system prompt with dynamic context
    system_prompt = build_full_prompt(state, language)

    # Apply sliding window to keep context manageable
    messages = apply_sliding_window(state["messages"])

    # Ensure system prompt is first message
    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = SystemMessage(content=system_prompt)
    else:
        messages = [SystemMessage(content=system_prompt)] + messages

    return {
        "messages": messages,
        "turn_delta": empty_turn_delta(),
        "narrative": "",
    }


# ---------------------------------------------------------------------------
# Node: resolver
# The single LLM node. Calls the model with tools bound.
# ---------------------------------------------------------------------------

def resolver(state: GameState) -> dict:
    """Call the LLM to process the player's action."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Node: tool_executor
# Executes tool calls from the resolver via LangGraph ToolNode.
# ---------------------------------------------------------------------------

tool_executor = ToolNode(ALL_TOOLS)


# ---------------------------------------------------------------------------
# Routing: should we continue tool calling or move to state_writer?
# ---------------------------------------------------------------------------

def should_continue_tools(state: GameState) -> Literal["tool_executor", "state_writer"]:
    """Check if the last message has tool calls that need execution."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_executor"
    return "state_writer"


def after_tools(state: GameState) -> Literal["resolver", "state_writer"]:
    """After tool execution, route back to resolver for more tool calls or proceed."""
    # Check if the resolver needs to process tool results
    # Look at the message before the tool messages — if it had tool_calls,
    # the resolver needs to see the results
    return "resolver"


# ---------------------------------------------------------------------------
# Node: state_writer
# Pure Python. Applies state mutations from tool call results to game state.
# ---------------------------------------------------------------------------

def state_writer(state: GameState) -> dict:
    """Process tool results and apply state changes to session files."""
    session_dir = state["session_dir"]
    player = copy.deepcopy(state["player"])
    knowledge = copy.deepcopy(state["knowledge"])
    traces = copy.deepcopy(state["traces"])
    location = copy.deepcopy(state["location"])
    inventory = copy.deepcopy(state["inventory"])
    npcs = copy.deepcopy(state["npcs"])
    world_state = copy.deepcopy(state["world_state"])
    log = copy.deepcopy(state["log"])

    # Extract narrative from the last AI message
    narrative = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            narrative = msg.content
            break

    # Process tool results for state mutations
    for msg in state["messages"]:
        if not isinstance(msg, ToolMessage):
            continue

        try:
            result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(result, dict) or "type" not in result:
            continue

        mutation_type = result["type"]

        if mutation_type == "update_player":
            changes = result.get("changes", {})
            for k, v in changes.items():
                if k in ("turn", "time"):
                    continue  # Handled by world_ticker
                player[k] = v

        elif mutation_type == "add_knowledge":
            entry_type = result.get("entry_type", "")
            entry = result.get("entry", {})
            entry["turn"] = player.get("turn", 1)
            # Add hidden layer tag
            layer_val = entry.pop("_layer_value", 1)
            entry["_layer"] = {"hidden": True, "value": layer_val}

            type_map = {
                "fact": "facts",
                "rumor": "rumors",
                "evidence": "evidence",
                "theory": "theories",
                "connection": "connections",
            }
            key = type_map.get(entry_type, entry_type + "s")
            if key not in knowledge:
                knowledge[key] = []
            knowledge[key].append(entry)

        elif mutation_type == "update_npc":
            npc_name = result.get("name", "")
            changes = result.get("changes", {})
            npc_list = npcs.get("npcs", [])
            found = False
            for npc in npc_list:
                if npc.get("name", "").lower() == npc_name.lower():
                    npc.update(changes)
                    found = True
                    break
            if not found:
                new_npc = {"name": npc_name}
                new_npc.update(changes)
                npc_list.append(new_npc)
                npcs["npcs"] = npc_list

        elif mutation_type == "update_location":
            location = result.get("data", location)

        elif mutation_type == "update_inventory":
            action = result.get("action", "")
            if action == "add":
                item = result.get("item", {})
                items = inventory.get("items", [])
                items.append(item)
                inventory["items"] = items
                inventory["slots"] = inventory.get("slots", {})
                inventory["slots"]["used"] = len(items)
            elif action == "remove":
                item_spec = result.get("item", {})
                items = inventory.get("items", [])
                # Remove by slot or name
                slot = item_spec.get("slot")
                name = item_spec.get("name", "")
                inventory["items"] = [
                    i for i in items
                    if not (
                        (slot and i.get("slot") == slot)
                        or (name and name.lower() in (i.get("name", "") + i.get("item", "")).lower())
                    )
                ]
                inventory["slots"] = inventory.get("slots", {})
                inventory["slots"]["used"] = len(inventory["items"])
            elif action == "update_credits":
                amount = result.get("amount", 0)
                inventory["credits"] = inventory.get("credits", 0) + amount
                player["credits"] = inventory["credits"]

        elif mutation_type == "update_world_state":
            changes = result.get("changes", {})
            if "nexus_alert_delta" in changes:
                alert = world_state.get("nexus_alert", {})
                if isinstance(alert, dict):
                    current = alert.get("current", 0)
                    alert["current"] = max(0, min(100, current + changes["nexus_alert_delta"]))
                    # Update status text
                    val = alert["current"]
                    if val <= 20:
                        alert["status"] = "Calm"
                    elif val <= 40:
                        alert["status"] = "Watchful"
                    elif val <= 60:
                        alert["status"] = "Alert"
                    elif val <= 80:
                        alert["status"] = "Manhunt"
                    else:
                        alert["status"] = "Lockdown"
                    world_state["nexus_alert"] = alert

            if "fragment_decay_delta" in changes:
                decay = world_state.get("fragment_decay", {})
                if isinstance(decay, dict):
                    current = decay.get("current", 0)
                    decay["current"] = max(0, min(100, current + changes["fragment_decay_delta"]))
                    val = decay["current"]
                    if val < 25:
                        decay["status"] = "Stable"
                    elif val < 50:
                        decay["status"] = "Fading"
                    elif val < 75:
                        decay["status"] = "Critical"
                    else:
                        decay["status"] = "Terminal"
                    world_state["fragment_decay"] = decay

            if "discover_district" in changes:
                district_name = changes["discover_district"]
                registry = world_state.get("_district_registry", {})
                undiscovered = registry.get("undiscovered", [])
                for i, d in enumerate(undiscovered):
                    if d.get("name") == district_name:
                        visible_entry = {
                            "name": d["name"],
                            "name_zh": d.get("name_zh", ""),
                            "status": d.get("status", "Open"),
                        }
                        if "notes" in d:
                            visible_entry["notes"] = d["notes"]
                        access = world_state.get("district_access", [])
                        access.append(visible_entry)
                        world_state["district_access"] = access
                        undiscovered.pop(i)
                        break

            if "add_event" in changes:
                events = world_state.get("global_events", [])
                events.append(changes["add_event"])
                world_state["global_events"] = events

        elif mutation_type == "add_log_entry":
            entries = log.get("entries", [])
            entries.append({
                "turn": player.get("turn", 1),
                "title": result.get("title", "Event"),
                "tag": result.get("tag", "system"),
                "text": result.get("text", ""),
            })
            # Keep max 30 entries
            if len(entries) > 30:
                entries = entries[-30:]
            log["entries"] = entries

    # Write changed files
    save_session_file(session_dir, "player", player)
    save_session_file(session_dir, "knowledge", knowledge)
    save_session_file(session_dir, "location", location)
    save_session_file(session_dir, "inventory", inventory)
    save_session_file(session_dir, "npcs", npcs)
    save_session_file(session_dir, "world_state", world_state)
    save_session_file(session_dir, "log", log)

    # Log conversation
    turn = player.get("turn", 1)
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            append_conversation(session_dir, "user", str(msg.content), turn)
    if narrative:
        append_conversation(session_dir, "assistant", narrative, turn)

    # Reduce messages — collapse tool call noise
    reduced = reduce_turn_messages(state["messages"])

    return {
        "player": player,
        "knowledge": knowledge,
        "traces": traces,
        "location": location,
        "inventory": inventory,
        "npcs": npcs,
        "world_state": world_state,
        "log": log,
        "narrative": narrative,
        "messages": reduced,
    }


# ---------------------------------------------------------------------------
# Node: world_ticker
# Pure Python. Advances turn, time, alert decay, fragment decay.
# ---------------------------------------------------------------------------

def world_ticker(state: GameState) -> dict:
    """Advance world state: turn counter, time, passive alert/decay changes."""
    player = copy.deepcopy(state["player"])
    world_state = copy.deepcopy(state["world_state"])
    session_dir = state["session_dir"]

    # Increment turn
    turn = player.get("turn", 1)
    player["turn"] = turn + 1

    # Advance time every TURNS_PER_PERIOD turns
    if turn % TURNS_PER_PERIOD == 0:
        current_time = player.get("time", "Morning")
        # Handle bilingual time strings
        for i, period in enumerate(TIME_PERIODS):
            if period.lower() in current_time.lower():
                next_idx = (i + 1) % len(TIME_PERIODS)
                player["time"] = TIME_PERIODS[next_idx]

                # Update world_state time
                time_data = world_state.get("time", {})
                time_data["period"] = TIME_PERIODS[next_idx]
                if next_idx == 0:  # New day
                    time_data["day"] = time_data.get("day", 1) + 1
                world_state["time"] = time_data
                break

    # Passive NEXUS alert decay (-1% per day cycle = every 9 turns)
    if turn % 9 == 0:
        alert = world_state.get("nexus_alert", {})
        if isinstance(alert, dict):
            alert["current"] = max(0, alert.get("current", 0) - 1)
            world_state["nexus_alert"] = alert

    save_session_file(session_dir, "player", player)
    save_session_file(session_dir, "world_state", world_state)

    return {
        "player": player,
        "world_state": world_state,
    }


# ---------------------------------------------------------------------------
# Node: trace_checker
# Pure Python. THE KEY WIN — deterministic trace checking that never forgets.
# ---------------------------------------------------------------------------

def trace_checker(state: GameState) -> dict:
    """Check all trace conditions against current knowledge. Always runs."""
    traces = copy.deepcopy(state["traces"])
    knowledge = state["knowledge"]
    npcs = state["npcs"]
    player = state["player"]
    world_state = state["world_state"]
    session_dir = state["session_dir"]

    new_discoveries = []

    for tc in TRACE_CONDITIONS:
        trace_id = tc["id"]
        if _trace_discovered(traces, trace_id):
            continue

        try:
            if tc["check"](knowledge, traces, npcs, player, world_state):
                discovery = {
                    "id": trace_id,
                    "description": tc["description"],
                    "turn": player.get("turn", 1),
                }
                if "discovered" not in traces:
                    traces["discovered"] = []
                traces["discovered"].append(discovery)
                new_discoveries.append(trace_id)

                # Update deepest layer in gate system
                gate = traces.get("_gate_system", {})
                if gate:
                    gate["deepest_layer"] = max(
                        gate.get("deepest_layer", 0), tc["layer"]
                    )
        except Exception:
            # Don't let a bad checker crash the game
            pass

    if new_discoveries:
        save_session_file(session_dir, "traces", traces)

    return {"traces": traces}


# ---------------------------------------------------------------------------
# Node: consequence
# Pure Python. Checks death and ending conditions.
# ---------------------------------------------------------------------------

def consequence(state: GameState) -> dict:
    """Check for death conditions and ending triggers."""
    player = state["player"]
    traces = state["traces"]
    world_state = state["world_state"]
    knowledge = state["knowledge"]

    # Death check
    integrity = player.get("integrity", {})
    if isinstance(integrity, dict) and integrity.get("current", 1) <= 0:
        return {"game_over": True, "ending": "death"}

    # Ending checks
    for ending in ENDINGS:
        try:
            if ending["check"](traces, world_state, player, knowledge):
                return {"game_over": True, "ending": ending["id"]}
        except Exception:
            pass

    return {"game_over": False, "ending": None}


# ---------------------------------------------------------------------------
# Routing: after consequence, end or continue
# ---------------------------------------------------------------------------

def after_consequence(state: GameState) -> str:
    """Always end after consequence. The outer game loop handles the next turn."""
    # The graph processes exactly ONE player turn, then returns.
    # The outer loop (run.py / TUI) feeds the next player input.
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct the Signal Lost game engine as a LangGraph StateGraph."""
    graph = StateGraph(GameState)

    # Add nodes
    graph.add_node("input_gate", input_gate)
    graph.add_node("resolver", resolver)
    graph.add_node("tool_executor", tool_executor)
    graph.add_node("state_writer", state_writer)
    graph.add_node("world_ticker", world_ticker)
    graph.add_node("trace_checker", trace_checker)
    graph.add_node("consequence", consequence)

    # Set entry point
    graph.set_entry_point("input_gate")

    # input_gate → resolver
    graph.add_edge("input_gate", "resolver")

    # resolver → tools or state_writer
    graph.add_conditional_edges(
        "resolver",
        should_continue_tools,
        {"tool_executor": "tool_executor", "state_writer": "state_writer"},
    )

    # tool_executor → back to resolver (for multi-step tool use)
    graph.add_edge("tool_executor", "resolver")

    # state_writer → world_ticker → trace_checker → consequence
    graph.add_edge("state_writer", "world_ticker")
    graph.add_edge("world_ticker", "trace_checker")
    graph.add_edge("trace_checker", "consequence")

    # consequence → END (one turn per invocation)
    graph.add_edge("consequence", END)

    return graph


def compile_graph():
    """Build and compile the graph, ready to invoke."""
    graph = build_graph()
    return graph.compile()
