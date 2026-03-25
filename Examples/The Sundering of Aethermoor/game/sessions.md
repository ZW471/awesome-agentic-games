# The Sundering of Aethermoor — Session File Schema

This document defines the required and optional files in the `session/` folder, their formats, and the rules for when and how to update them.

The agent must maintain these files as the authoritative record of game state. When in doubt about any game state, read the relevant session file — do not rely on memory.

All session files use JSON format.

---

## Hidden Fields Convention

Any JSON object containing `"hidden": true` must NOT be displayed to the player in the TUI. The TUI's parser applies a `filter_hidden()` function that recursively removes such objects from the data tree before rendering.

**Hidden fields in this game:**

- `world_state.json` > `void_corruption._thresholds` — internal corruption threshold rules and labels
- `world_state.json` > `malachar_awareness._triggers` — internal awareness escalation trigger rules

By convention, hidden field keys are prefixed with an underscore (e.g., `_thresholds`, `_triggers`) to make them visually distinct in the JSON, but the `"hidden": true` property is what controls filtering.

---

## Required Session Files

### `session/player.json`

The player character's complete state. Update after every event that changes any value.

**Format:**
```json
{
  "name": "Character Name",
  "class": "Riftwalker (Subclass)",
  "save_name": "save_name",
  "stats": {
    "HP": {"base": 100, "current": 100},
    "MP": {"base": 60, "current": 60},
    "STR": {"base": 5, "current": 5},
    "INT": {"base": 10, "current": 10},
    "AGI": {"base": 8, "current": 8}
  },
  "rift_points": {"current": 10, "max": 10},
  "shards_collected": [
    {"name": "Emberveil Shard", "ability": "Flamestrike", "collected": false},
    {"name": "Thornwood Shard", "ability": "Barkskin", "collected": false},
    {"name": "Crystalmere Shard", "ability": "Frostbind", "collected": false},
    {"name": "Ashen Shard", "ability": "Wraithform", "collected": false},
    {"name": "Skyreach Shard", "ability": "Stormcall", "collected": false}
  ],
  "active_abilities": [
    {"name": "Rift Step", "type": "passive", "cost": "1 Rift Point", "description": "Can open Rift Gates between known Realms."},
    {"name": "Rift Sense", "type": "passive", "cost": null, "description": "Can detect Shard energy and Void corruption nearby."}
  ],
  "status_effects": [],
  "turns": 0
}
```

**Update rules:**
- Update HP/MP after every combat action or healing event
- Update Rift Points after every Rift Gate use or restoration event
- Add Shard abilities to `active_abilities` and set `collected: true` in `shards_collected` when a Shard is collected
- Update status effects at the start of each turn (decrement durations)
- Increment `turns` at the end of every player turn

---

### `session/world_state.json`

The global state of Aethermoor. Update when Void Corruption changes, Shards are collected, or Realm conditions change.

**Format:**
```json
{
  "void_corruption": {
    "current": 0.0,
    "rate": 1.0,
    "status": "Stable",
    "_thresholds": {
      "hidden": true,
      "values": [
        {"pct": 25, "label": "Stable"},
        {"pct": 50, "label": "Creeping"},
        {"pct": 75, "label": "Critical"},
        {"pct": 100, "label": "Catastrophic — GAME OVER"}
      ]
    }
  },
  "realm_status": [
    {"name": "Emberveil", "status": "Intact", "notes": ""},
    {"name": "Thornwood", "status": "Intact", "notes": ""},
    {"name": "Crystalmere", "status": "Intact", "notes": ""},
    {"name": "Ashen Wastes", "status": "Damaged", "notes": "60% consumed at game start"},
    {"name": "Skyreach", "status": "Intact", "notes": ""}
  ],
  "shards_status": [
    {"shard": "Emberveil Shard", "location": "Ironmaw Volcano deep chamber", "status": "Not Found"},
    {"shard": "Thornwood Shard", "location": "Heartroot, Thornwood center", "status": "Not Found"},
    {"shard": "Crystalmere Shard", "location": "Crystal Sea deepest trench", "status": "Not Found"},
    {"shard": "Ashen Shard", "location": "Obsidian Citadel Shard Chamber", "status": "Not Found"},
    {"shard": "Skyreach Shard", "location": "With Zephyra Windfall", "status": "Not Found"}
  ],
  "malachar_awareness": {
    "level": "Dormant",
    "_triggers": {
      "hidden": true,
      "rules": "Awareness increases when: Each Shard is collected (+1 tier), Player reaches the Ashen Wastes (+1 tier), Player attempts to contact Seraphel about the reforging (+1 tier). At Active: Malachar begins sending agents to obstruct the player. At Pursuing: Malachar personally intervenes."
    }
  },
  "known_rift_gates": [],
  "lore_revelations": []
}
```

**Update rules:**
- Increase Void Corruption by the Corruption Rate at the end of every player turn
- Update Realm Status when the player witnesses significant Void events
- Update Shard Status when player finds or collects a Shard
- Update Malachar's Awareness when trigger conditions are met
- Realm status values: `Intact`, `Damaged`, `Critical`, `Lost`
- Malachar awareness levels: `Dormant`, `Watching`, `Active`, `Pursuing`
- Shard status values: `Not Found`, `Found`, `Collected`

---

### `session/location.json`

The player's current location. Update every time the player moves.

**Format:**
```json
{
  "realm": "Realm Name",
  "area": "Area Name",
  "zone": "Specific Zone",
  "description": "2-4 sentences describing the current location. Tone: dark, epic, atmospheric. Include sensory details.",
  "exits": [
    {"direction": "Direction or Path Name", "destination": "Where it leads"}
  ],
  "npcs_present": ["NPC description 1", "NPC description 2"],
  "rift_gate": "Not Present",
  "void_presence": "None"
}
```

**Update rules:**
- Rewrite completely whenever the player moves to a new area
- Update `npcs_present` when NPCs arrive or depart
- Update `rift_gate` if the player creates or repairs one
- Rift gate values: `Not Present`, `Present — Stable`, `Present — Unstable`, `Present — Dormant`
- Void presence values: `None`, `Faint`, `Strong`, `Overwhelming`

---

### `session/inventory.json`

Everything the player is carrying. Update when items are gained, used, dropped, or traded.

**Format:**
```json
{
  "gold": 0,
  "slots_used": 0,
  "slots_max": 20,
  "weapons": [
    {"name": "Item Name", "damage": "1d6+INT arcane", "notes": "Special properties"}
  ],
  "armor": [
    {"name": "Item Name", "defense": "+1 defense", "notes": "Special properties"}
  ],
  "consumables": [
    {"name": "Item Name", "effect": "What it does", "qty": 1}
  ],
  "quest_items": [
    {"name": "Item Name", "quest": "Associated Quest", "notes": "Relevant info"}
  ],
  "artifacts": [
    {"name": "Item Name", "power": "Special ability", "notes": "Limitations"}
  ]
}
```

**Update rules:**
- Add items immediately when acquired
- Remove items immediately when used, sold, dropped, or consumed
- Update Gold after every transaction
- Update `slots_used` to reflect total item count

---

### `session/log.json`

A chronological event log. Keep the last 20 entries. Older entries may be trimmed.

**Format:**
```json
{
  "entries": [
    {"turn": 0, "title": "Brief event title", "text": "1-3 sentences describing what happened."},
    {"turn": 1, "title": "Next event", "text": "Description of this turn's events."}
  ]
}
```

**Update rules:**
- Add a new entry at the end of every player turn
- If more than 20 entries exist, remove the oldest ones
- Entries must include the turn number

---

### `session/npcs.json`

The current state of all major NPCs the player has encountered. Update when NPC disposition changes, location changes, or quests are given/completed.

**Format:**
```json
{
  "npcs": [
    {
      "name": "NPC Name",
      "location": "Current location",
      "disposition": "Neutral",
      "status": "Active",
      "quests_given": "None",
      "quests_completed": "None",
      "notes": "Relevant state info"
    }
  ]
}
```

**Update rules:**
- Add an NPC entry when the player first encounters them
- Update disposition whenever it changes (values: `Hostile`, `Wary`, `Neutral`, `Friendly`, `Devoted`)
- Update location if the NPC moves
- Move NPC to `Recruited as Companion` status and update companions.json when they join

---

### `session/companions.json`

The player's active companions. Update when companions join, leave, level up, or take damage.

**Format:**
```json
{
  "slots_used": 0,
  "slots_max": 3,
  "companions": [
    {
      "name": "Companion Name",
      "race_class": "Race and role",
      "hp": {"current": 50, "max": 50},
      "mp": {"current": 20, "max": 20},
      "ability": "Ability Name — description + cooldown status",
      "status": "Active",
      "disposition": "Friendly",
      "notes": "Relevant info"
    }
  ]
}
```

**Update rules:**
- Add companion entry when they join the party
- Update HP/MP after every combat
- Track special ability cooldowns
- Remove entry if companion leaves or is lost
- Keep `companions` as an empty array if party is empty
- Status values: `Active`, `Injured`, `Incapacitated`

---

### `session/quests.json`

All quests: active and completed. Update when quests are received, progressed, or completed.

**Format:**
```json
{
  "active": [
    {
      "title": "Quest Name",
      "given_by": "NPC Name",
      "realm": "Where the quest takes place",
      "objective": "What needs to be done",
      "progress": "Current status",
      "reward": "What the player will receive"
    }
  ],
  "completed": [
    {
      "title": "Quest Name",
      "completed_turn": "Turn X",
      "outcome": "Brief description of resolution",
      "reward_received": "What was given"
    }
  ]
}
```

**Update rules:**
- Add quest as soon as it is given by an NPC
- Update `progress` whenever a quest step is completed
- Move quest to `completed` array and add outcome when finished
- Note if a quest was failed or abandoned

---

## Optional Session Files

These files are created during play if relevant conditions are met.

### `session/malachar_visions.json`

Created when the player receives their first vision from Malachar. Records each vision with the turn it occurred and its content.

**Format:**
```json
{
  "visions": [
    {
      "id": 1,
      "turn": 9,
      "title": "Vision Title",
      "trigger": "What triggered the vision",
      "content": "Description of what happened in the vision"
    }
  ]
}
```

### `session/map_notes.json`

Created when the player begins keeping notes about discovered areas.

### `session/lore_fragments.json`

Created when the player finds their first lore fragment. Records discovered lore for reference.

---

## Session Integrity Rules

1. **Never delete session files** during active gameplay — only update them.
2. **Always read before writing** — check current values before updating to avoid overwriting state you don't intend to change.
3. **Void Corruption is authoritative** in `world_state.json` — if there is ever a discrepancy, trust `world_state.json`.
4. **Player HP reaching 0** triggers the death protocol in `agent/game.md` — do not simply update HP to 0 and continue.
5. **Turn counter** in `player.json` drives the Void Corruption increment — keep it accurate.
6. **Hidden fields** (objects with `"hidden": true`) contain internal game logic and must not be revealed to the player. They are automatically filtered out by the TUI viewer.
