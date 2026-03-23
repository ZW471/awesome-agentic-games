# SAVE GAME / 保存游戏

Save your empire's progress.

保存你的帝国进度。

---

## Instructions for Agent

When the player invokes this file:

1. Verify that `session/` exists and contains valid game state.
2. Read `session/civilization.md` to get the save name.
3. Copy the entire `session/` folder into `saves/<save_name>/`.
4. Confirm the save to the player, showing: civilization name, current era, turn number, and score.
