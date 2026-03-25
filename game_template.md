# Agentic Game Template Specification

An **agentic game** is a game defined entirely by `.md` files (and optionally Python helper tools) that is played through interaction with an agentic coding assistant (e.g., Claude Code, Codex, Opencode). The agent acts as the game engine: it reads the game definition, manages state, enforces rules, and presents the game to the player.

---

## Creating a New Game — Agent Workflow

When a player asks an agent to **create a new agentic game**, the agent must follow this workflow. Do not jump straight into file generation — plan first, confirm with the player, then build.

### Step 1: Generate a Draft Plan

Based on the player's initial request (which may be vague, e.g., "make me a space exploration game"), the agent produces a structured plan covering:

- **Genre & premise** — What kind of game is this? What's the core fantasy?
- **Core mechanics** — Turn structure, combat/skill checks, resource systems, progression.
- **World structure** — How many regions/levels/areas? Linear or open?
- **Player character** — Class system? Stats? Abilities? How much customization?
- **NPCs & companions** — Key characters, disposition system, companion mechanics.
- **Win/loss conditions** — How does the game end? Is there permadeath?
- **Session file schema** — What files go in `session/`? What does each track?
- **Tools needed** — Dice roller? Random tables? Map generator?
- **Estimated scope** — How many files need to be created?

### Step 2: Ask the Player for Specifications

Present the draft plan and ask the player to confirm, modify, or expand. Specifically ask about:

1. **Theme & tone** — Dark and gritty? Lighthearted? Comedic? Epic?
2. **Complexity preference** — Simple (few mechanics, fast turns) or deep (many systems, tactical)?
3. **Difficulty settings** — What difficulty modes? What do they change?
4. **Narrative style** — Terse? Verbose? Player's choice?
5. **Any specific mechanics or features** they want included or excluded.
6. **TUI viewer** — Does the player want a Terminal UI dashboard for viewing game state? (See `tui_template.md` for details.) If yes, the agent should generate `tui_viewer.py` alongside the game files, following the template in that document. If unsure, explain what the TUI provides (persistent tabbed overview of all session state, visual HP/MP bars, interactive dice roller) and let the player decide.

### Step 3: Build the Game

Only after the player confirms the plan, generate all game files following the directory structure below. Create files in dependency order:

1. `settings/default.json` and `settings/custom.json` — configuration first, since other files reference it.
2. `game/background.md` — world lore that informs everything else.
3. `game/npcs.md` — NPC definitions.
4. `game/sessions.md` — session file schema (must exist before `game/init.md` references it).
5. `game/init.md` — initialization procedure.
6. `agent/system.md`, `agent/game.md`, `agent/player.md` — agent behavior.
7. `tools/*.py` — helper tools if needed.
8. `NEW GAME.md`, `LOAD GAME.md`, `SAVE GAME.md`, `RESUME.md` — player entry points.
9. **Python environment** — run `uv venv` in the game root, then `uv pip install` any packages needed by `tools/` scripts or the TUI.
10. `tui/tui_viewer.py` — TUI viewer, if the player requested one (follow `tui_template.md`).
11. `README.md` — player-facing documentation (see the `README.md` section below for required content).

---

## Directory Structure Overview

```
<game_root>/
├── README.md              # Game documentation and quick-start guide
├── NEW GAME.md            # Player entry point: start a new game
├── RESUME.md              # Player entry point: resume the current session
├── LOAD GAME.md           # Player entry point: load an existing save
├── SAVE GAME.md           # Player entry point: save the current session
├── .venv/                 # Python virtual environment (created during setup)
├── game/                  # Game definition (read-only during play)
│   ├── init.md
│   ├── background.md
│   ├── npcs.md
│   └── sessions.md
├── agent/                 # Agent behavior instructions
│   ├── player.md
│   ├── system.md
│   └── game.md
├── settings/              # Configuration
│   ├── default.json
│   └── custom.json
├── tools/                 # (Optional) Python helper tools
│   └── *.py
├── tui/                   # (Optional) TUI dashboard — see tui_template.md
│   └── tui_viewer.py
├── session/               # Live game state (created at runtime)
│   └── (files defined by sessions.md)
└── saves/                 # Saved snapshots of session/
    └── <save_name>/       # Each save is a named copy of session/
```

---

## Root-Level Entry Points

Root-level `.md` files use **UPPER CASE** names. These are the only files the **player** invokes directly (via `@` mention). The agent must never prompt the player to invoke anything else — these four files are the entire player-facing interface for game lifecycle operations.

### `NEW GAME.md`

Invoked by the **player** to start a new game. When called, the agent must:

1. Read the `agent/` folder to understand its role and responsibilities.
2. Read the `game/` folder to understand the game definition.
3. Read `settings/custom.json` to load active configuration.
4. Ask the player for a **save name** (a unique identifier for this playthrough).
5. Execute the initialization procedure defined in `game/init.md` (which creates and populates the `session/` folder).
6. Begin the game session.

### `LOAD GAME.md`

Invoked by the **player** to resume a saved game. When called, the agent must:

1. Read the `agent/` folder and `game/` folder.
2. Read `settings/custom.json`.
3. List available saves under `saves/`.
4. Let the player choose a save.
5. Copy the chosen save's contents into the `session/` folder (replacing any existing session).
6. Resume the game session from the restored state.

### `SAVE GAME.md`

Invoked by the **player** to save the current session. When called, the agent must:

1. Verify an active `session/` folder exists.
2. Copy the entire `session/` folder into `saves/<save_name>/`, where `<save_name>` is the name chosen during `NEW GAME`.
3. Confirm the save to the player.

### `RESUME.md`

Invoked by the **player** to continue the current in-progress session across a new agent conversation. Unlike `LOAD GAME.md` (which restores from a save), `RESUME.md` picks up directly from the existing `session/` folder — no save selection needed. This is the quickest way to get back into a game when the session files are already in place. When called, the agent must:

1. Read the `agent/` folder and `game/` folder.
2. Read `settings/custom.json`.
3. Verify an active `session/` folder exists. If not, direct the player to `NEW GAME.md` or `LOAD GAME.md`.
4. Read all files in `session/` to fully restore the game state.
5. Present a brief status recap (character name, location, turn count) to orient the player.
6. Resume the game session from the current state.

---

## `game/` Folder — Game Definition

Contains the static definition of the game world, rules, and structure. These files are **read-only during play** — the agent reads them to understand the game but does not modify them at runtime.

### `game/init.md`

**Called by the agent only** (never by the player directly). Defines the initialization procedure for a new game:

- What files to create inside `session/` and their initial contents.
- Any randomization, procedural generation, or player-choice-driven setup steps.
- What to present to the player at the start of the game (e.g., intro text, character creation).

### `game/background.md`

The lore, world-building, and narrative context of the game. The agent uses this to:

- Set the tone and style of narration.
- Answer player questions about the world.
- Maintain narrative consistency.

### `game/npcs.md`

Defines all non-player characters in the game:

- NPC names, descriptions, personalities, and behaviors.
- Dialogue patterns or disposition rules.
- NPC locations, schedules, or spawn conditions.
- Relationship mechanics (e.g., how NPCs react to player actions).

### `game/sessions.md`

The **schema and specification** for the `session/` folder. Defines:

- **Required files**: files that must always exist in `session/` (e.g., `log.json`, `player.json`).
- **Optional files**: files that may be created during play under certain conditions.
- **File formats**: all session files use **JSON** format for reliable parsing by the TUI viewer and agent.
- **Update rules**: when and how each file should be updated during gameplay.
- **Hidden fields**: which fields should be marked with `"hidden": true` to prevent the TUI from displaying them to the player (see **Hidden Fields** below).

Typical session files include (but are game-specific):

| File | Purpose |
|------|---------|
| `log.json` | Chronological record of events and interactions in the current session |
| `player.json` | Player character state: stats, status effects, health, etc. |
| `inventory.json` | Items the player is carrying |
| `location.json` | Current location description and available exits/interactions |
| `npcs.json` | NPCs currently present near the player and their states |
| `conversation.jsonl` | Append-only log of all player–agent conversation turns |

The exact files are defined per game in `sessions.md` — the above are examples, not requirements.

### Player-Facing Information Principle

**The player-facing interface (TUI, session files) must never reveal anything the player has not yet discovered through gameplay.** The UI is part of the game world — it should reflect only what the player character knows at any given moment.

This principle applies broadly:

- **Locations/regions**: Only show areas the player has discovered. Undiscovered areas and their unlock requirements must be stored in hidden fields. When the player learns about a new area (an NPC mentions it, they find a map, etc.), move it from the hidden registry to the visible list — but never expose the unlock condition in the visible data. The player should learn how to access areas through gameplay, not from the UI.
- **NPCs**: Only add NPCs to player-visible tracking after the player has encountered or heard about them.
- **Items and collectibles**: Don't show total counts, checklists, or structures that reveal undiscovered content.
- **Progression systems**: Don't reveal layer structures, total milestone counts, or gating logic.
- **Story outcomes**: Don't show ending trajectories, branching paths, or consequence tracking.

This means session data often needs a **two-part structure**: a visible portion (what the player sees) and a hidden portion (what the agent uses internally). The hidden portion uses the `"hidden": true` convention described below.

### Hidden Fields Convention

Some session data is tracked by the agent for internal game logic but **must not be revealed to the player** through the TUI. Examples include ending trajectories, undiscovered content structures, internal AI scoring, and knowledge gate details.

To mark data as hidden, add `"hidden": true` to any JSON object. The TUI viewer **must skip** any object (at any nesting level) that contains this key-value pair.

```json
{
  "public_data": {
    "name": "Player One",
    "hp": 100
  },
  "ending_trajectory": {
    "hidden": true,
    "current": "Neutral",
    "confidence": "Low"
  }
}
```

In this example, the TUI displays `public_data` but ignores `ending_trajectory` entirely.

**When to use `hidden: true`:**
- Ending trajectory or story outcome tracking
- Undiscovered locations, regions, or areas the player hasn't found yet — including their existence and unlock requirements
- Undiscovered content structures (e.g., full lists of collectibles the player hasn't found yet, including total counts and layer assignments that would spoil progression)
- Internal NPC disposition scores that differ from what the player perceives
- Agent-only metadata (e.g., information poisoning flags, false fact tracking)
- Any data whose mere existence or structure would spoil the player's experience

**Guidelines for game creators:**
- The `game/sessions.md` schema should document which fields are hidden and why.
- The `agent/game.md` file should instruct the agent to maintain hidden fields correctly and to promote data from hidden to visible only when the player discovers it through gameplay.
- Hidden objects can contain any valid JSON — the TUI ignores the entire subtree.
- When promoting hidden data to visible (e.g., a newly discovered district), strip any agent-internal fields (like `unlock` conditions) before adding to the visible portion.

### Conversation Log (`session/conversation.jsonl`)

Every game must track the full player–agent conversation in an **append-only** [JSON Lines](https://jsonlines.org/) file at `session/conversation.jsonl`. Each line is a self-contained JSON object representing one conversation turn.

**Format (one JSON object per line):**
```jsonl
{"role": "user", "content": "I walk into the noodle shop and talk to Mira.", "turn": 5, "timestamp": "2026-03-25T14:32:01Z"}
{"role": "assistant", "content": "The steam parts as you push through the bead curtain...", "turn": 5, "timestamp": "2026-03-25T14:32:08Z"}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `role` | `"user"` or `"assistant"` | Who sent this message |
| `content` | string | The full text of the message |
| `turn` | integer | The game turn number at the time of the message |
| `timestamp` | ISO 8601 string | When the message was sent |

**Rules:**
- **Append-only.** The agent must only append new lines to `conversation.jsonl`. It must never modify, delete, or rewrite existing lines. This preserves a tamper-proof record of the entire conversation.
- **Every exchange is logged.** Every player input and every agent response must be appended as separate lines immediately when they occur.
- **Created during initialization.** `game/init.md` must create `session/conversation.jsonl` as an empty file. The first entries are appended when the opening narration is presented and the player responds.
- **Included in saves.** When the session is saved or loaded, `conversation.jsonl` is copied along with all other session files.
- **Displayed in the TUI.** If the game has a TUI viewer, it should include a **Conversations** tab that displays the conversation history, showing player and agent messages in a chat-like format with turn numbers.

---

## `agent/` Folder — Agent Behavior Instructions

Contains instructions that tell the agent **how to behave**. These files define the agent's role and operational rules. Files in this folder may reference tools from the `tools/` folder and instruct the agent when to use them.

### `agent/player.md`

Defines the single human player's capabilities and constraints:

- What actions the player can take (e.g., move, examine, talk, use item, attack).
- What actions are forbidden or restricted.
- How to interpret and validate player input.
- How to present choices and outcomes to the player.

### `agent/system.md`

Defines **system-level operations** — everything outside of active gameplay:

- How to read and apply settings from `settings/custom.json`.
- How to execute the new-game initialization flow (referencing `game/init.md`).
- How to load a save into `session/`.
- How to save `session/` to `saves/`.
- Error handling (e.g., missing save, corrupted session).
- Any housekeeping the agent must perform between turns or sessions.

### `agent/game.md`

Defines the **in-session gameplay loop** — the rules the agent follows while the game is actively being played:

- Turn structure and progression (e.g., what happens each turn, phase order).
- How to read and update files in `session/` in response to player actions.
- Appending every player input and agent response to `session/conversation.jsonl` as part of the turn processing.
- Game mechanics resolution (combat, skill checks, puzzles, etc.).
- Narrative generation rules (tone, pacing, detail level).
- Win/loss/end conditions.
- How to handle player interactions that are gameplay-related (as opposed to system-level requests like saving).

---

## `settings/` Folder — Configuration

### `settings/default.json`

The **baseline configuration** for the game. This file must **never be edited** after initial game creation — it serves as a reference and reset point.

### `settings/custom.json`

The **active configuration** used at runtime. Initially an exact copy of `default.json`. The player or agent edits this file to override defaults.

Settings may include (game-specific):

- Difficulty parameters
- Narrative style preferences (e.g., verbosity, tone)
- Gameplay toggles (e.g., permadeath on/off)
- Agent behavior knobs (e.g., how strictly to enforce rules)

---

## Python Environment Setup

Any game that uses Python tools (`tools/`) or a TUI viewer (`tui/`) must have a virtual environment. The creating agent must set this up as part of game creation using `uv`:

```bash
cd <game_root>
uv venv                        # Creates .venv/ in the game root
```

Then install any dependencies the tools or TUI require:

```bash
uv add textual          # Required if TUI viewer is included
uv add rich          # Required if TUI viewer is included
uv add <other-deps>     # Any packages the tools/ scripts need
```

All tool and TUI invocations must use the venv's Python:

```bash
.venv/bin/python tools/dice.py d20+5
.venv/bin/python tui/tui_viewer.py .
```

The `agent/system.md` file should document which packages are installed and remind the agent to use `.venv/bin/python` when invoking any scripts.

---

## `tools/` Folder — Python Helper Tools (Optional)

Contains Python scripts that the agent can invoke to support gameplay. This folder is **optional** — simple games may not need any tools.

- Tools are referenced and their usage is described in `agent/` folder `.md` files.
- The agent must only use tools when instructed to by the agent behavior files.
- Tools must be run with the game's venv Python (`.venv/bin/python`), not the system Python.
- Example uses: dice rolling, random table lookups, map generation, complex calculations.

---

## `session/` Folder — Live Game State

The runtime state of the current game. All files in this folder use **JSON format** (`.json` extension). This folder:

- Is **created** during `NEW GAME` (via the procedure in `game/init.md`).
- Is **overwritten** during `LOAD GAME` (from a save).
- Is **read in full** during `RESUME` (to restore state in a new agent conversation).
- Is **copied** during `SAVE GAME` (into `saves/<save_name>/`).
- Contains everything the player can see or that affects gameplay during a session, plus hidden agent-only data marked with `"hidden": true`.
- Its structure is defined by `game/sessions.md`.

The agent reads and writes to this folder during gameplay. It is the single source of truth for current game state.

---

## `saves/` Folder — Save Snapshots

Contains named snapshots of the `session/` folder.

- Each save is a subdirectory: `saves/<save_name>/`.
- The `<save_name>` is chosen by the player when starting a new game via `NEW GAME.md`.
- A save is a **literal filesystem copy** of the `session/` folder at the time of saving.
- Saving to an existing `<save_name>` overwrites that save.

---

## TUI Viewer (Optional)

If the player requests a TUI viewer during game creation, generate `tui/tui_viewer.py` following the specification in **`tui_template.md`** (located in the repository root alongside this file).

The TUI is a Textual-based terminal application that provides an interactive split-screen experience for playing the game directly in the terminal. One side embeds a terminal for interacting with the AI agent, while the other displays a tabbed dashboard showing all session state — character stats, inventory, map, quests, and more — updated in real time.

Key points for the creating agent:

- The TUI lives in the `tui/` subfolder to keep the game root clean.
- The TUI's parser must match the session file schema defined in `game/sessions.md`. Every file the game writes to `session/` should have a corresponding parser method and display panel.
- The TUI can invoke tools from `tools/` (e.g., dice roller) for player convenience.
- The player refreshes the TUI (press `r`) after the agent processes each turn to see updated state.
- The TUI includes an embedded pseudo-terminal (PTY) so the player can talk to the agent without leaving the game interface.

See `tui_template.md` for the full specification including parser design, widget conventions, color schemes, and keyboard shortcuts.

---

## `README.md` — Game Documentation

Every game must include a `README.md` at its root that serves as the player's introduction and quick-start guide. The creating agent must generate this file as the final step of game creation.

The README should include:

### Required Sections

1. **Title & tagline** — The game name and a one-line hook.
2. **Background** — A brief, spoiler-light summary of the game's setting, premise, and tone (2–3 paragraphs). Enough to get the player excited without revealing key plot points.
3. **How to Play** — Two subsections:
   - **With the TUI** — How to launch the TUI viewer (`cd` into the game folder, run the TUI command). Mention what the TUI shows and how to refresh it.
   - **With an AI Agent** — How to start a conversation-based game (tell the agent to read `NEW GAME.md`). List compatible agents.
4. **Game Lifecycle** — A table or list of the four entry points (`NEW GAME.md`, `RESUME.md`, `LOAD GAME.md`, `SAVE GAME.md`) and what each does.
5. **Game Features** — Bullet list of key mechanics (e.g., character classes, combat system, companion system, world exploration).
6. **Settings** — Brief note on how to customize difficulty, narrative style, etc. via `settings/custom.json`.

### Tone

Write the README as if it's the back cover of a game box — evocative but concise. Match the game's tone (e.g., dark and dramatic for a dark fantasy, playful for a comedy).

---

## Conventions Summary

| Convention | Rule |
|-----------|------|
| **UPPER CASE `.md`** | Root-level entry points invoked by the player |
| **lowercase `.md`** | Game definition and agent instruction files |
| **`.json` / `.jsonl` for session state** | All files in `session/` and `saves/` use JSON or JSON Lines format for reliable TUI parsing |
| **`conversation.jsonl` is append-only** | The agent must only append new lines to the conversation log — never modify or delete existing entries |
| **Player invokes** | Only `NEW GAME.md`, `LOAD GAME.md`, `SAVE GAME.md`, `RESUME.md` (via `@`) |
| **Agent invokes** | `game/init.md` and any internal procedures — never directly by player |
| **Read-only during play** | `game/`, `agent/`, `settings/default.json` |
| **Read-write during play** | `session/`, `settings/custom.json` |
| **Player-facing info hiding** | The UI must never reveal anything the player hasn't discovered through gameplay — undiscovered locations, unlock requirements, total counts, progression structures, and story outcomes must be hidden |
| **Hidden fields** | JSON objects with `"hidden": true` are tracked by the agent but not displayed by the TUI |
| **Tools** | Optional; usage defined in `agent/` files; stored in `tools/`; run with `.venv/bin/python` |
| **Python environment** | Created with `uv venv`; dependencies installed with `uv pip install`; all scripts use `.venv/bin/python` |
| **TUI viewer** | Optional; created if player requests it; follows `tui_template.md`; requires `textual` in venv |
| **Plan before building** | Always generate a plan, ask the player for specs, then build |
