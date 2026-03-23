# Session Schema / 会话文件结构

Defines the structure of the `session/` folder — the live game state.

---

## Required Files

### `session/civilization.md`
The player's civilization state. Updated every turn.

```markdown
# Civilization: <name>
Save Name: <save_name>
Language: <en|cn>
Turn: <number>
Era: <era_name>

## Resources
| Resource | Amount | Per Turn |
|----------|--------|----------|
| Gold | <n> | +<n> |
| Food | <n> | +<n> |
| Production | <n> | +<n> |
| Science | <n> | +<n> |
| Culture | <n> | +<n> |

## Stats
- Population: <n>
- Happiness: <n>/10
- Military Strength: <n>
- Score: <n>
```

**Update rules**: Update resources, population, and stats at the **end** of each turn based on actions taken and per-turn income.

---

### `session/map.md`
The world map represented as a territory grid. Updated when territories are explored, claimed, or change hands.

```markdown
# World Map

## Territories
| ID | Name | Terrain | Owner | Resources | Improvements | Explored |
|----|------|---------|-------|-----------|--------------|----------|
| A1 | <name> | <type> | <owner/unclaimed> | <resources> | <buildings> | yes/no |
...
```

**Terrain types**: Plains, Forest, Mountain, Desert, Coast, River, Tundra
**Territory count**: Generate a 5x5 grid (25 territories) at game start.
**Update rules**: Update when player explores, settles, conquers, or builds improvements.

---

### `session/technology.md`
Tech tree progress. Updated when research completes.

```markdown
# Technology Tree

## Researched
- <tech_name> (Turn <n>)

## Currently Researching
- <tech_name> — Progress: <n>/<cost> science

## Available to Research
- <tech_name> — Cost: <n> science — Requires: <prereqs> — Effect: <description>
```

The tech tree has ~30 technologies across the 5 eras. See `game/init.md` for the full tech tree.

**Update rules**: Each turn, add accumulated science to current research. When complete, move to Researched and let player choose next research.

---

### `session/diplomacy.md`
Relations with NPC civilizations. Updated when diplomatic events occur.

```markdown
# Diplomacy

## Active Civilizations
| Civilization | Leader | Disposition | Status | Treaties |
|-------------|--------|-------------|--------|----------|
| <name> | <leader> | <-10 to +10> | <status> | <list> |

## Diplomatic Log
- Turn <n>: <event description>
```

**Update rules**: Update disposition after any diplomatic interaction. Log all diplomatic events.

---

### `session/military.md`
Military units and ongoing conflicts. Updated during combat and recruitment.

```markdown
# Military

## Units
| Unit | Type | Strength | Status | Location |
|------|------|----------|--------|----------|
| <name> | <type> | <n> | Ready/Damaged/Recovering | <territory_id> |

## Active Conflicts
- War with <civ>: Started Turn <n>

## Battle Log
- Turn <n>: <battle description and outcome>
```

**Unit types by era**:
- Ancient: Warriors (2), Archers (1+range)
- Classical: Swordsmen (3), Cavalry (4)
- Medieval: Knights (5), Siege Engines (3+siege)
- Renaissance: Musketeers (6), Cannons (5+siege)
- Modern: Infantry (7), Artillery (6+range), Tanks (9)

**Update rules**: Update after recruitment, combat, or unit movement.

---

### `session/log.md`
Chronological game log. Append-only.

```markdown
# Game Log

## Turn <n> — <era_name>
- <event 1>
- <event 2>
- Player action: <action>
- Result: <outcome>
```

**Update rules**: Append events at the end of each turn. Never delete previous entries. Keep entries concise (1-2 lines each).

---

## Optional Files

### `session/events.md`
Created when there are pending or active special events. Deleted when empty.

```markdown
# Active Events
- <event_name>: <description> — Expires: Turn <n>
  - Options: <A> / <B>
```

### `session/wonders.md`
Created when the player begins building a world wonder.

```markdown
# Wonders

## Built
- <wonder_name> (Turn <n>) — Effect: <description>

## In Progress
- <wonder_name> — Progress: <n>/<cost> production

## Available
- <wonder_name> — Cost: <n> production — Era: <era> — Effect: <description>
```
