# System Operations / 系统操作

Defines how the agent handles non-gameplay operations.

---

## Settings

Read `settings/custom.json` at game start. Key settings:

- `language`: Default language (`en` or `cn`). Can be overridden by player choice.
- `difficulty`: Controls number of rival civs and their aggression.
  - `easy`: 3 rivals, NPC actions succeed on 5+ (d6), +5 starting disposition
  - `normal`: 4 rivals, NPC actions succeed on 4+ (d6), +0 starting disposition
  - `hard`: 4 rivals, NPC actions succeed on 3+ (d6), -3 starting disposition
- `narrative_style`: `concise` or `detailed` — affects description length.
- `auto_save`: If true, auto-save every 10 turns.

---

## New Game Flow

When `NEW GAME.md` is invoked:

1. Read all `agent/*.md` files.
2. Read all `game/*.md` files.
3. Read `settings/custom.json`.
4. Ask for save name.
5. Execute `game/init.md` step by step.
6. After initialization, display the opening and begin the gameplay loop.

---

## Load Game Flow

When `LOAD GAME.md` is invoked:

1. Read agent and game definitions.
2. List saves: read each `saves/<name>/civilization.md` header for summary info.
3. Present list with: save name, civilization, era, turn number, score.
4. On selection, copy all files from `saves/<name>/` to `session/`.
5. Read session state and resume the gameplay loop from the current turn.

---

## Save Game Flow

When `SAVE GAME.md` is invoked:

1. Verify `session/` exists.
2. Read save name from `session/civilization.md`.
3. Copy all `session/` files to `saves/<save_name>/`.
4. Confirm with: "Game saved: <civ_name>, Turn <n>, <era>."

---

## Error Handling

- **No session exists** when saving/playing: Inform player, suggest `NEW GAME.md` or `LOAD GAME.md`.
- **No saves exist** when loading: Inform player, suggest `NEW GAME.md`.
- **Corrupted session** (missing required files): Attempt to reconstruct from other session files. If impossible, inform player and suggest loading a save.
- **Duplicate save name**: Warn and ask to overwrite or choose a new name.

---

## Auto-Save

If `auto_save` is enabled in settings:
- Every 10 turns, automatically save to `saves/<save_name>/`.
- Notify the player: "Auto-saved at Turn <n>." / "第<n>回合自动存档完成。"

---

## Between Turns

At the transition between turns, before presenting the new turn:
1. Ensure all session files are consistent.
2. Verify resource calculations are correct.
3. Check for victory conditions.
4. Check for era transitions.
