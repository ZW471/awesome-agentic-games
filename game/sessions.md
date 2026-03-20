# The Sundering of Aethermoor — Session File Schema

This document defines the required and optional files in the `session/` folder, their formats, and the rules for when and how to update them.

The agent must maintain these files as the authoritative record of game state. When in doubt about any game state, read the relevant session file — do not rely on memory.

---

## Required Session Files

### `session/player.md`

The player character's complete state. Update after every event that changes any value.

**Format:**
```markdown
# Player: [CHARACTER NAME]

## Identity
- **Name:** [name]
- **Class:** Riftwalker ([subclass: Battlemage | Arcanist | Shadowweave])
- **Save Name:** [save name]

## Core Stats
| Stat | Base | Current |
|------|------|---------|
| HP   | [max_hp] | [current_hp] |
| MP   | [max_mp] | [current_mp] |
| STR  | [str] | [str] |
| INT  | [int] | [int] |
| AGI  | [agi] | [agi] |

**Rift Points:** [current] / [max]

## Shards Collected
- [ ] Emberveil Shard — *Flamestrike*
- [ ] Thornwood Shard — *Barkskin*
- [ ] Crystalmere Shard — *Frostbind*
- [ ] Ashen Shard — *Wraithform*
- [ ] Skyreach Shard — *Stormcall*

## Active Abilities
- **Rift Step** (passive): Can open Rift Gates between known Realms. Costs 1 Rift Point.
- **Rift Sense** (passive): Can detect Shard energy and Void corruption nearby.
- [Subclass abilities listed here]
- [Shard abilities listed here as they are collected]

## Status Effects
[List active buffs/debuffs with duration, or "None"]

## Turn Counter
**Turns Elapsed:** [number]
```

**Update rules:**
- Update HP/MP after every combat action or healing event
- Update Rift Points after every Rift Gate use or restoration event
- Add Shard abilities when a Shard is collected
- Update status effects at the start of each turn (decrement durations)
- Increment Turns Elapsed at the end of every player turn

---

### `session/world_state.md`

The global state of Aethermoor. Update when Void Corruption changes, Shards are collected, or Realm conditions change.

**Format:**
```markdown
# World State

## Void Corruption
**Current Corruption:** [0-100]%
**Corruption Rate:** [X]% per turn (base: 1.0, modified by difficulty and events)
**Status:** [Stable | Creeping | Critical | Catastrophic]

> Corruption Thresholds:
> - 0-25%: Stable — the Void is present but contained
> - 26-50%: Creeping — Realm edges are dissolving; NPCs grow fearful
> - 51-75%: Critical — Realm areas begin disappearing; some NPCs lost
> - 76-99%: Catastrophic — Multiple Realms partially consumed; time is running out
> - 100%: GAME OVER — Aethermoor ceases to exist

## Realm Status
| Realm | Status | Notes |
|-------|--------|-------|
| Emberveil | [Intact/Damaged/Critical/Lost] | [brief note] |
| Thornwood | [Intact/Damaged/Critical/Lost] | [brief note] |
| Crystalmere | [Intact/Damaged/Critical/Lost] | [brief note] |
| Ashen Wastes | Damaged | 60% consumed at game start |
| Skyreach | [Intact/Damaged/Critical/Lost] | [brief note] |

## Shards Status
| Shard | Location | Status |
|-------|----------|--------|
| Emberveil Shard | Ironmaw Volcano deep chamber | [Not Found/Found/Collected] |
| Thornwood Shard | Heartroot, Thornwood center | [Not Found/Found/Collected] |
| Crystalmere Shard | Crystal Sea deepest trench | [Not Found/Found/Collected] |
| Ashen Shard | Obsidian Citadel Shard Chamber | [Not Found/Found/Collected] |
| Skyreach Shard | With Zephyra Windfall | [Not Found/Found/Collected] |

## Malachar's Awareness
**Level:** [Dormant | Watching | Active | Pursuing]

> Awareness increases when:
> - Each Shard is collected (+1 tier)
> - Player reaches the Ashen Wastes (+1 tier)
> - Player attempts to contact Seraphel about the reforging (+1 tier)
>
> At "Active": Malachar begins sending agents to obstruct the player
> At "Pursuing": Malachar personally intervenes with vision warnings and traps

## Known Rift Gate Locations
[List of Realms the player has visited and can Rift to directly]
```

**Update rules:**
- Increase Void Corruption by the Corruption Rate at the end of every player turn
- Update Realm Status when the player witnesses significant Void events
- Update Shard Status when player finds or collects a Shard
- Update Malachar's Awareness when trigger conditions are met

---

### `session/location.md`

The player's current location. Update every time the player moves.

**Format:**
```markdown
# Current Location

**Realm:** [Realm name]
**Area:** [Area name]
**Zone:** [Specific zone within area, if relevant]

## Description
[2-4 sentences describing the current location. Tone: dark, epic, atmospheric. Include sensory details — what the player sees, hears, smells.]

## Exits & Paths
- **[Direction/Path name]:** leads to [destination] ([difficulty hint if relevant])
- ...

## Points of Interest
- **[Object/Feature]:** [brief description, hint at interaction]
- ...

## NPCs Present
[List NPCs currently in this zone, or "None"]

## Rift Gate
[Present / Not Present — if Present: Condition (Stable/Unstable/Dormant)]

## Void Presence
[None / Faint / Strong / Overwhelming — describes how much Void corruption is visible here]
```

**Update rules:**
- Rewrite completely whenever the player moves to a new area
- Update "NPCs Present" when NPCs arrive or depart
- Update "Rift Gate" status if the player creates or repairs one

---

### `session/inventory.md`

Everything the player is carrying. Update when items are gained, used, dropped, or traded.

**Format:**
```markdown
# Inventory

**Gold:** [amount]
**Slots Used:** [X] / [max — from settings]

## Weapons
| Item | Damage | Notes |
|------|--------|-------|
| [name] | [dice] | [any special properties] |

## Armor & Accessories
| Item | Defense | Notes |
|------|---------|-------|
| [name] | [value] | [any special properties] |

## Consumables
| Item | Effect | Qty |
|------|--------|-----|
| [name] | [what it does] | [count] |

## Quest Items
| Item | Associated Quest | Notes |
|------|-----------------|-------|
| [name] | [quest name] | [relevant info] |

## Artifacts
| Item | Power | Notes |
|------|-------|-------|
| [name] | [special ability] | [any limitations] |
```

**Update rules:**
- Add items immediately when acquired
- Remove items immediately when used, sold, dropped, or consumed
- Update Gold after every transaction

---

### `session/log.md`

A chronological event log. Keep the last 20 entries. Older entries may be trimmed.

**Format:**
```markdown
# Session Log

## [Turn X] — [Brief event title]
[1-3 sentences describing what happened this turn. Include: player action taken, outcome, any notable consequence.]

---

## [Turn X-1] — [Brief event title]
[...]

---
[...continue for last 20 turns...]
```

**Update rules:**
- Add a new entry at the end of every player turn
- If more than 20 entries exist, remove the oldest ones
- Entries must include the turn number

---

### `session/npcs.md`

The current state of all major NPCs the player has encountered. Update when NPC disposition changes, location changes, or quests are given/completed.

**Format:**
```markdown
# NPC Tracker

## [NPC Name]
- **Location:** [current location]
- **Disposition:** [hostile | wary | neutral | friendly | devoted]
- **Status:** [Active/Recruited as Companion/Deceased/Unknown]
- **Quests Given:** [list quest names, or None]
- **Quests Completed:** [list, or None]
- **Notes:** [any relevant state info]

---
[repeat for each encountered NPC]
```

**Update rules:**
- Add an NPC entry when the player first encounters them
- Update disposition whenever it changes
- Update location if the NPC moves
- Move NPC to "Recruited as Companion" status and update companions.md when they join

---

### `session/companions.md`

The player's active companions. Update when companions join, leave, level up, or take damage.

**Format:**
```markdown
# Active Companions

**Slots Used:** [X] / 3

---

## [Companion Name]
- **Race/Class:** [race and role]
- **HP:** [current] / [max]
- **MP:** [current] / [max]
- **Special Ability:** [name] — [description + cooldown status]
- **Status:** [Active/Injured/Incapacitated]
- **Disposition toward player:** [friendly | devoted]
- **Notes:** [any relevant info, e.g., current cooldown state]

---
[repeat for each companion, up to 3]
```

**Update rules:**
- Add companion entry when they join the party
- Update HP/MP after every combat
- Track special ability cooldowns
- Remove entry if companion leaves or is lost
- Write "No active companions" if party is empty

---

### `session/quests.md`

All quests: active and completed. Update when quests are received, progressed, or completed.

**Format:**
```markdown
# Quest Log

## Active Quests

### [Quest Name]
- **Given by:** [NPC name]
- **Realm:** [where the quest takes place]
- **Objective:** [what needs to be done]
- **Progress:** [current status, steps completed]
- **Reward:** [what the player will receive]

---

## Completed Quests

### [Quest Name] ✓
- **Completed:** Turn [X]
- **Outcome:** [brief description of how it was resolved]
- **Reward received:** [what was given]

---
```

**Update rules:**
- Add quest as soon as it is given by an NPC
- Update Progress whenever a quest step is completed
- Move quest to Completed section and add outcome when finished
- Note if a quest was failed or abandoned

---

## Optional Session Files

These files are created during play if relevant conditions are met.

### `session/map_notes.md`

Created when the player begins keeping notes about discovered areas. Contains player-annotated descriptions of explored zones, secret passages, hidden caches, etc.

### `session/malachar_visions.md`

Created when the player receives their first vision from Malachar. Records each vision with the turn it occurred and its content. Useful for tracking Malachar's awareness level and his stated intentions.

### `session/lore_fragments.md`

Created when the player finds their first lore fragment (books, inscriptions, echoes with information). Records discovered lore for reference.

---

## Session Integrity Rules

1. **Never delete session files** during active gameplay — only update them.
2. **Always read before writing** — check current values before updating to avoid overwriting state you don't intend to change.
3. **Void Corruption is authoritative** in `world_state.md` — if there is ever a discrepancy, trust `world_state.md`.
4. **Player HP reaching 0** triggers the death protocol in `agent/game.md` — do not simply update HP to 0 and continue.
5. **Turn counter** in `player.md` drives the Void Corruption increment — keep it accurate.
