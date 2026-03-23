# Player Actions / 玩家操作指南

Defines what the player can do and how to interpret their input.

---

## Available Actions Per Turn

The player may take **2 actions per turn** (unless modified by technology or events). Present these as a numbered menu each turn.

### Core Actions

| # | Action | Command | Description |
|---|--------|---------|-------------|
| 1 | **Build** / 建造 | `build <building>` | Construct a building or improvement in a territory |
| 2 | **Research** / 研究 | `research <tech>` | Begin or continue researching a technology |
| 3 | **Recruit** / 征兵 | `recruit <unit>` | Train a military unit (costs Production) |
| 4 | **Explore** / 探索 | `explore <direction>` | Scout an adjacent unexplored territory |
| 5 | **Expand** / 扩张 | `expand to <territory>` | Settle/claim an adjacent unclaimed explored territory |
| 6 | **Trade** / 贸易 | `trade with <civ>` | Propose a trade agreement |
| 7 | **Diplomacy** / 外交 | `diplomacy <civ>` | Open diplomatic dialogue (alliance, peace, threat, gift) |
| 8 | **Attack** / 进攻 | `attack <target>` | Send military units to attack a territory or civilization |
| 9 | **Move** / 移动 | `move <unit> to <territory>` | Relocate a military unit |
| 10 | **Build Wonder** / 建造奇迹 | `wonder <name>` | Begin constructing a World Wonder |

### Free Actions (don't count toward the 2-action limit)

| Action | Command | Description |
|--------|---------|-------------|
| **View Map** / 查看地图 | `map` | Display the current world map |
| **View Stats** / 查看状态 | `stats` | Show civilization dashboard |
| **View Tech** / 查看科技 | `tech` | Show technology tree and progress |
| **View Military** / 查看军事 | `military` | Show military units and conflicts |
| **View Diplomacy** / 查看外交 | `diplomacy` | Show diplomatic relations overview |
| **Check Score** / 查看分数 | `score` | Show current score breakdown |
| **Help** / 帮助 | `help` | Show available actions |

---

## Input Interpretation Rules

1. **Be flexible**: Accept natural language. "I want to build a library" = `build library`. "让我们研究文字" = `research Writing`.
2. **Bilingual**: Accept commands in English or Chinese regardless of session language.
3. **Clarify ambiguity**: If the player's intent is unclear, ask a brief clarifying question. Never guess destructive actions (like declaring war).
4. **Validate**: Check that the action is legal before executing:
   - Can they afford it? (resources)
   - Do they have the required technology?
   - Is it the right era?
   - Have they used their 2 actions this turn?
5. **Suggest**: If the player seems stuck, offer 2-3 strategic suggestions based on game state.
6. **End turn**: After 2 actions (or if the player says "end turn" / "结束回合"), proceed to the end-of-turn phase.

---

## Restrictions

- The player **cannot** directly edit session files — all changes go through actions.
- The player **cannot** take more than 2 actions per turn (unless a tech/event grants bonus actions).
- The player **cannot** attack an Allied civilization without first breaking the alliance (costs 1 action and -5 disposition with all civs).
- The player **cannot** research technologies from a future era until they have researched at least 4 technologies in the current era.
