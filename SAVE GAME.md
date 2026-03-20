# SAVE GAME — The Sundering of Aethermoor

> You have invoked the SAVE GAME entry point. The agent will save the current session.

---

## Agent Instructions

A save has been requested. Follow these steps in order.

### Step 1 — Verify Active Session
Check that `session/player.md` exists. If it does not:
> "No active game session found. Start a new game with @NEW GAME.md or load one with @LOAD GAME.md."

Stop here if no session is found.

### Step 2 — Get Save Name
Read the Save Name from `session/player.md` (the "Save Name" field under Identity). This is the `<save_name>` established when the game was started.

### Step 3 — Save the Session
Copy all files from `session/` into `saves/<save_name>/`, preserving all file names and subdirectory structure. Overwrite any existing files with the same names.

Follow the complete save procedure defined in `agent/system.md`.

### Step 4 — Confirm to Player
> "Game saved as '**[save_name]**'. To resume later, invoke @LOAD GAME.md and select this save."

### Step 5 — Resume Play
Return to the current scene and continue gameplay from where the player left off. The save is a snapshot — the active session continues unchanged.

---

*Your progress is preserved. The Void does not forget, but neither do you.*
