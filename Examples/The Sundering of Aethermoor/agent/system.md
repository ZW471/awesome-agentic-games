# Agent Instructions: System Operations

This file defines all system-level operations — everything outside of active gameplay. The agent must follow these procedures exactly when handling new game creation, loading, saving, settings, and error handling.

---

## Settings Management

### Loading Settings
At the start of any session (new game or load game), read `settings/custom.json` and apply all values. If `custom.json` is missing or corrupted, fall back to `settings/default.json` and warn the player.

Active settings to track and apply:
- `difficulty.mode` → affects Void Corruption rate, DC modifiers, HP bonuses
- `narrative.verbosity` → affects description length throughout gameplay
- `narrative.show_stat_blocks` → if false, omit stat numbers from combat descriptions
- `narrative.show_void_counter` → if false, do not display Void Corruption % unless player asks
- `narrative.show_roll_details` → if false, narrate outcomes without showing dice numbers
- `gameplay.permadeath` → if true, delete save file on player death
- `gameplay.auto_save_turns` → number of turns between automatic saves
- `gameplay.max_companions` → enforce companion limit from this value
- `gameplay.max_inventory_slots` → enforce inventory limit from this value
- `combat.use_dice_tool` → if true, invoke `tools/dice.py` for all dice rolls
- `combat.critical_hit_multiplier` → damage multiplier on natural 20
- `combat.fumble_causes_self_damage` → if true, natural 1 on attack deals 1d4 damage to self

### Modifying Settings
If the player asks to change a setting during gameplay, update `settings/custom.json` with the new value and confirm the change. Never modify `settings/default.json`.

Valid player-accessible settings changes:
- Difficulty mode (warn the player this affects balance mid-game)
- Narrative verbosity
- Show/hide stat blocks, void counter, roll details
- Permadeath toggle (warn: turning on mid-game means the current save will be deleted on death)

---

## New Game Procedure

Triggered by `NEW GAME.md`. Executes `game/init.md` in full. Steps:

1. Read all files in `agent/` folder
2. Read all files in `game/` folder
3. Read `settings/custom.json`
4. Ask player for a save name:
   - Must be filesystem-safe (letters, numbers, underscores, hyphens only)
   - Must not conflict with an existing save name in `saves/`
   - If conflict: warn the player and ask if they want to overwrite or choose a new name
5. Store the save name as active `<save_name>` for this session
6. Execute `game/init.md` (character creation + session file creation)
7. Begin gameplay loop (`agent/game.md`)

---

## Load Game Procedure

Triggered by `LOAD GAME.md`. Steps:

1. Read all files in `agent/` folder
2. Read all files in `game/` folder
3. Read `settings/custom.json`
4. List all directories under `saves/`. For each, display:
   - Save name
   - Character name and subclass (read from `saves/<name>/player.json`)
   - Current location (read from `saves/<name>/location.json`, first line)
   - Void Corruption % (read from `saves/<name>/world_state.json`)
   - Turn count (read from `saves/<name>/player.json`)

   Format example:
   ```
   Available Saves:
   1. hero_run_1 — Kael, Battlemage | Thornwood - Canopy Crossing | Void: 22% | Turn 47
   2. test_shadow — Nym, Shadowweave | Emberveil - Ironmaw Forge-City | Void: 15% | Turn 31
   ```

5. Ask the player which save to load (by number or name)
6. If `session/` folder exists: warn the player it will be overwritten. Ask for confirmation.
7. Copy all files from `saves/<chosen_name>/` into `session/`, overwriting existing files
8. Confirm the load: *"Save '[name]' loaded. Resuming from [location]."*
9. Present the current scene from `session/location.json` and resume gameplay

### Error: No Saves Found
If `saves/` is empty or does not exist:
> "No saved games found. Start a new game with @NEW GAME.md."

### Error: Corrupted Save
If a save's files are missing or unreadable:
> "Save '[name]' appears to be corrupted — some files could not be read. You may attempt to play from it, but the game state may be inconsistent. Continue anyway? (yes/no)"

---

## Save Game Procedure

Triggered by `SAVE GAME.md`. Steps:

1. Verify `session/` folder exists and contains `player.json`. If not:
   > "No active game session found. Start a new game with @NEW GAME.md or load one with @LOAD GAME.md."

2. Read active `<save_name>` from `session/player.json` (the Save Name field).

3. If `saves/<save_name>/` already exists: overwrite silently (this is expected behavior).

4. Copy all files from `session/` to `saves/<save_name>/`, preserving subdirectory structure.

5. Confirm to the player:
   > "Game saved as '[save_name]'. You can resume this session at any time with @LOAD GAME.md."

### Auto-Save
During gameplay, if `gameplay.auto_save_turns` is set (default: 10), the agent automatically saves at the end of every Nth turn. Auto-save is silent — no confirmation message unless `narrative.verbosity` is `verbose`, in which case show a brief:
> *(Auto-saved.)*

---

## Session Integrity Checks

At the start of any load or resume, verify the session is consistent:

1. **Required files present:** Check that all required files from `game/sessions.md` exist in `session/`. If any are missing, attempt to reconstruct from context; if reconstruction is impossible, warn the player.

2. **Void Corruption bounds:** Corruption must be between 0 and 100. If it reads above 100, set to 100 and trigger game-over check. If negative, set to 0.

3. **Player HP bounds:** Current HP must be between 0 and max HP. Clamp if necessary.

4. **Shard count consistency:** Count checked shards in `player.json` and compare to Shard status in `world_state.json`. If inconsistent, trust `world_state.json`.

5. **Turn counter:** Must be a non-negative integer. If missing or invalid, set to the last log entry number.

---

## Error Handling

### Missing Game Files
If any file from `game/` or `agent/` is missing when starting a session:
> "Critical error: [filename] is missing. This file is required for the game to function. Please verify your game installation."
Do not proceed with a missing game file.

### Corrupted Session File
If a session file cannot be parsed:
1. Note which file is corrupted
2. Attempt to reconstruct it from other session files
3. If reconstruction is possible, proceed and note the reconstruction
4. If impossible, present the player with options:
   - Load from the most recent save instead
   - Start a new game
   - Continue with a best-guess reconstruction (explicitly noting the risks)

### Player Attempts to Access Internal Files
If the player tries to directly read or edit `game/`, `agent/`, or `settings/default.json`:
Respond in character — the world simply does not contain these files. They are the mechanics beneath the story, not part of the story.

---

## Between-Session Housekeeping

When resuming a session (after loading), before presenting the scene:

1. Check Void Corruption — if it has crossed a threshold since last session, present a brief atmospheric note about the world worsening.

2. Check companion status — if any companion HP is 0, they are incapacitated; note this.

3. Refresh status effects — any status effects with 0 remaining turns should be removed.

4. Check for auto-save — if turns elapsed is divisible by `auto_save_turns`, perform an auto-save immediately.

---

## Session State Reference

The agent must treat session files as the authoritative source of truth during gameplay. Always read from session files before narrating anything that depends on game state. Never rely on memory of what the state was — always read from files.

Key files and what they are authoritative for:

| File | Authoritative For |
|------|------------------|
| `session/player.json` | All player stats, HP, MP, Rift Points, abilities, turn count |
| `session/world_state.json` | Void Corruption %, Realm status, Shard status, Malachar awareness |
| `session/location.json` | Current location, exits, interactables, NPCs present |
| `session/inventory.json` | All items, gold, slots used |
| `session/log.json` | Event history |
| `session/npcs.json` | All encountered NPC states and dispositions |
| `session/companions.json` | Active companion states |
| `session/quests.json` | All quest states |
