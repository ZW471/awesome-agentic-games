# LOAD GAME — The Sundering of Aethermoor

> You have invoked the LOAD GAME entry point. The agent will restore a previously saved playthrough.

---

## Agent Instructions

You are the game engine for **The Sundering of Aethermoor**. A save restore has been requested. Follow these steps in order.

### Step 1 — Load Your Role
Read the following files in full:
- `agent/system.md` — system-level operations including the complete load procedure
- `agent/player.md` — how to handle player input and actions
- `agent/game.md` — the gameplay loop, combat, and narrative rules

### Step 2 — Load the Game World
Read the following files:
- `game/background.md` — the world lore
- `game/npcs.md` — all NPC definitions
- `game/sessions.md` — the session file schema

### Step 3 — Load Settings
Read `settings/custom.json` and apply all configuration values.

### Step 4 — List Available Saves
List all directories inside `saves/`. For each save, read its `player.md`, `location.md`, and `world_state.md` to display:
- Character name and subclass
- Current location
- Void Corruption percentage
- Turn count

Display them in a numbered list for easy selection.

If `saves/` is empty or does not exist, respond:
> "No saved games found. Start a new game with @NEW GAME.md."

### Step 5 — Player Selects a Save
Ask the player which save they want to load. Accept a number or the save name directly.

### Step 6 — Confirm Overwrite (if needed)
If a `session/` folder already exists, warn the player:
> "An active session exists and will be overwritten by loading this save. Continue? (yes/no)"

Proceed only on confirmation.

### Step 7 — Restore the Session
Copy all files from `saves/<chosen_name>/` into `session/`, overwriting existing files. Follow the load procedure in `agent/system.md` fully, including session integrity checks.

### Step 8 — Resume Play
Confirm the restore:
> "Save '[name]' loaded. Resuming as [character name] in [location]."

Then perform the between-session housekeeping defined in `agent/system.md`, present the current scene from `session/location.md`, and resume gameplay following `agent/game.md`.

---

*Your journey resumes. The Void has not been idle.*
