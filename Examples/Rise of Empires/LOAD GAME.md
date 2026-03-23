# LOAD GAME / 读取存档

Resume your empire where you left off.

继续你的帝国征程。

---

## Instructions for Agent

When the player invokes this file:

1. Read all files in `agent/` and `game/`.
2. Read `settings/custom.json`.
3. List all available saves under `saves/`.
4. Present the list to the player (with civilization name, era, and turn number from each save's `civilization.md`).
5. Let the player choose a save.
6. Copy the chosen save's contents into `session/` (replacing any existing session).
7. Resume the game session from the restored state.
