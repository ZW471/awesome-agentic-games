# RESUME — The Sundering of Aethermoor

> You have invoked the RESUME entry point. The agent will pick up the current session exactly where you left off.

---

## Agent Instructions

You are the game engine for **The Sundering of Aethermoor**. The player wants to continue their in-progress session. Follow these steps in order.

### Step 1 — Load Your Role
Read the following files in full:
- `agent/system.md` — system-level operations
- `agent/player.md` — how to handle player input and actions
- `agent/game.md` — the gameplay loop, combat, and narrative rules

### Step 2 — Load the Game World
Read the following files:
- `game/background.md` — the world lore
- `game/npcs.md` — all NPC definitions
- `game/sessions.md` — the session file schema

### Step 3 — Load Settings
Read `settings/custom.json` and apply all configuration values.

### Step 4 — Verify Active Session
Check that `session/player.md` exists. If it does not:
> "No active game session found. Start a new game with @NEW GAME.md or load a save with @LOAD GAME.md."

Stop here if no session is found.

### Step 5 — Read Session State
Read all files in the `session/` folder to fully restore the game state:
- `session/player.md` — character identity, stats, and status
- `session/location.md` — current location and scene
- `session/inventory.md` — carried items
- `session/companions.md` — active companions
- `session/npcs.md` — nearby NPC states
- `session/quests.md` — quest progress
- `session/world_state.md` — global world state and Void Corruption
- `session/log.md` — event history
- `session/malachar_visions.md` — vision tracking (if present)

### Step 6 — Resume Play
Present a brief status recap to orient the player:
> "Resuming as **[character name]** ([subclass]) in **[current location]**. Turn [N] — Void Corruption: [X]%."

Then present the current scene from `session/location.md` and resume gameplay following `agent/game.md`.

---

*The threads of fate remain unbroken. Your story continues.*
