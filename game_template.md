# Agentic Game Template Specification

An **agentic game** is a game defined entirely by `.md` files (and optionally Python helper tools) that is played through interaction with an agentic coding assistant (e.g., Claude Code, Codex, Opencode). The agent acts as the game engine: it reads the game definition, manages state, enforces rules, and presents the game to the player.

---

## Directory Structure Overview

```
<game_root>/
├── NEW GAME.md            # Player entry point: start a new game
├── LOAD GAME.md           # Player entry point: load an existing save
├── SAVE GAME.md           # Player entry point: save the current session
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
├── session/               # Live game state (created at runtime)
│   └── (files defined by sessions.md)
└── saves/                 # Saved snapshots of session/
    └── <save_name>/       # Each save is a named copy of session/
```

---

## Root-Level Entry Points

Root-level `.md` files use **UPPER CASE** names. These are the only files the **player** invokes directly (via `@` mention). The agent must never prompt the player to invoke anything else — these three files are the entire player-facing interface for game lifecycle operations.

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

- **Required files**: files that must always exist in `session/` (e.g., `log.md`, `player.md`).
- **Optional files**: files that may be created during play under certain conditions.
- **File formats**: the structure and expected contents of each session file.
- **Update rules**: when and how each file should be updated during gameplay.

Typical session files include (but are game-specific):

| File | Purpose |
|------|---------|
| `log.md` | Chronological record of events and interactions in the current session |
| `player.md` | Player character state: stats, status effects, health, etc. |
| `inventory.md` | Items the player is carrying |
| `location.md` | Current location description and available exits/interactions |
| `npcs.md` | NPCs currently present near the player and their states |

The exact files are defined per game in `sessions.md` — the above are examples, not requirements.

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

## `tools/` Folder — Python Helper Tools (Optional)

Contains Python scripts that the agent can invoke to support gameplay. This folder is **optional** — simple games may not need any tools.

- Tools are referenced and their usage is described in `agent/` folder `.md` files.
- The agent must only use tools when instructed to by the agent behavior files.
- Example uses: dice rolling, random table lookups, map generation, complex calculations.

---

## `session/` Folder — Live Game State

The runtime state of the current game. This folder:

- Is **created** during `NEW GAME` (via the procedure in `game/init.md`).
- Is **overwritten** during `LOAD GAME` (from a save).
- Is **copied** during `SAVE GAME` (into `saves/<save_name>/`).
- Contains everything the player can see or that affects gameplay during a session.
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

## Conventions Summary

| Convention | Rule |
|-----------|------|
| **UPPER CASE `.md`** | Root-level entry points invoked by the player |
| **lowercase `.md`** | All other files (game definition, agent instructions, session state) |
| **Player invokes** | Only `NEW GAME.md`, `LOAD GAME.md`, `SAVE GAME.md` (via `@`) |
| **Agent invokes** | `game/init.md` and any internal procedures — never directly by player |
| **Read-only during play** | `game/`, `agent/`, `settings/default.json` |
| **Read-write during play** | `session/`, `settings/custom.json` |
| **Tools** | Optional; usage defined in `agent/` files; stored in `tools/` |
