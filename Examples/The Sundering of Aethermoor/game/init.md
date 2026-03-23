# The Sundering of Aethermoor — Initialization Procedure

This file is invoked by the agent when a new game is started (via `NEW GAME.md`). It defines the complete procedure for character creation and initial state setup. Follow every step in order.

---

## Step 1: Apply Difficulty Settings

Read `settings/custom.json` and note the following active values:
- `difficulty.mode` → determines Void Corruption rate and DC modifiers
- `narrative.verbosity` → determines description length
- `narrative.tone` → should be `dark_epic` by default
- `gameplay.starting_rift_points` → usually 10
- `gameplay.max_inventory_slots` → usually 20
- `gameplay.max_companions` → usually 3

Apply difficulty HP bonus to base HP:
- base HP = 100
- Apply `difficulty.player_hp_bonus[mode]` to get starting max HP

---

## Step 2: Display Opening Lore

Present this opening narration to the player. Adjust verbosity based on `narrative.verbosity`:

---

*The world is broken.*

*You remember what it was like before — not personally, you are not that old — but through the fragments, the stories, the ache in your bones that every Riftwalker carries. The Worldstone's absence is not an absence you see. It is one you feel: a cold space behind your sternum where certainty used to live.*

*You are one of the last. Of the hundred Riftwalkers who once maintained the passages between the Five Realms, perhaps a dozen survive. You have been hunted, hidden, survived on luck and stubbornness. But the luck is running out.*

*You stand now at the edge of a dying world, at the threshold of a crumbling Rift Gate. Behind you, the Void presses in. Ahead, the Five Realms wait — each holding a Shard of the Worldstone, each guarded by those who fear what you might do with it.*

*Malachar is still out there. The Void grows every day.*

*Your name is...*

---

## Step 3: Character Creation

Ask the player the following questions in order. Wait for their response before asking the next question. Narrate each choice back to them before proceeding.

### 3a. Name
> "What is your name, Riftwalker?"

Accept any name. Store it as `CHARACTER NAME`.

### 3b. Subclass
Present the three subclasses and ask which one the player chooses:

> "Before the Sundering, Riftwalker training had three paths. Which did you walk?"

**Option 1: Battlemage**
*"You trained your body and your magic together. Where others had to choose between sword and spell, you found the space between them."*
- Stat bonuses: STR +3, INT +2, AGI +1
- Unique abilities:
  - **Arcane Strike** (active, 1 MP): Melee attack enhanced with magical energy. Deals STR-based damage + 1d6 arcane. Always available.
  - **Iron Resolve** (passive): When HP drops below 25%, gain +3 to all dice rolls until healed above 25%.
- Starting equipment: Iron-edge blade (+1d8 slashing), leather-and-mail armor (+3 defense)

**Option 2: Arcanist**
*"You went deep into the theory of Rift magic. You understand it better than anyone alive — how gates work, how Shards resonate, how the Void thinks."*
- Stat bonuses: INT +4, AGI +2
- Unique abilities:
  - **Rift Pulse** (active, 3 MP): Releases a wave of Rift energy. Deals INT-based damage to all enemies in combat. DC 15 AGI for half damage.
  - **Shard Attunement** (passive): When collecting a Shard, restore 5 MP in addition to normal restoration.
  - **Void Reading** (passive): Can sense Void corruption levels and Malachar's awareness tier without checking world_state.md — the agent describes this as a "gut feeling."
- Starting equipment: Riftweave staff (1d6+INT arcane damage), scholar's robes (+1 defense, +10 MP bonus)

**Option 3: Shadowweave**
*"You learned to bend Rift magic into stealth and deception. You survived the Riftwalker purge because no one could ever quite pin down where you were."*
- Stat bonuses: AGI +4, INT +2
- Unique abilities:
  - **Shadow Step** (active, 2 MP): Teleport up to 30 feet in any direction. In combat, gain advantage on next attack roll.
  - **Rift Cloak** (active, 3 MP, 5-turn cooldown): Turn invisible for up to 3 turns. Breaking invisibility (attacking) ends the effect.
  - **Evasion** (passive): When targeted by area attacks, take half damage automatically.
- Starting equipment: Twin Rift-daggers (2x 1d4+AGI slashing), shadowweave cloak (+2 defense, advantage on stealth checks)

### 3c. Stat Distribution

Based on the chosen subclass, set base stats:

**Battlemage:** STR 8, INT 7, AGI 6 (then apply subclass bonuses → STR 11, INT 9, AGI 7)
**Arcanist:** STR 5, INT 9, AGI 7 (then apply subclass bonuses → STR 5, INT 13, AGI 9)
**Shadowweave:** STR 6, INT 7, AGI 9 (then apply subclass bonuses → STR 6, INT 9, AGI 13)

Stat modifier = (stat - 10) / 2, rounded down. Used in d20 rolls.

### 3d. Opening Realm Choice

> "Every Riftwalker begins somewhere. Your last Rift Gate opened to the border of one of three Realms. Which do you step toward?"

Present three options (always the same three starter options; The Ashen Wastes and Skyreach are not available at start):

1. **Emberveil** — *"Heat and smoke and the distant sound of hammering. The volcanic Forge-Cities are nearby."*
2. **Thornwood** — *"The smell of ancient earth and pine. Massive trees loom overhead, their canopy blocking the sky."*
3. **Crystalmere** — *"The cold hits you immediately, a clean dry cold. The frozen ground crunches underfoot."*

This determines the player's starting location and the first NPC they are likely to meet. Note: the starting Realm is where the first Shard quest will begin.

---

## Step 4: Create Session Files

Create the `session/` folder and all required files with initial contents.

### Create `session/player.md`

Use the template from `game/sessions.md`. Fill in:
- Name: from Step 3a
- Subclass: from Step 3b
- Stats: from Step 3c (base + subclass bonuses)
- Max HP: 100 + difficulty HP bonus
- Current HP: same as Max HP
- Max MP: 50 (Arcanist gets +10 bonus from robes → 60 max)
- Current MP: same as Max MP
- Rift Points: from settings (`gameplay.starting_rift_points`)
- Starting abilities: Rift Step, Rift Sense, plus subclass abilities
- Shards: all unchecked
- Status Effects: None
- Turn Counter: 0

### Create `session/world_state.md`

Use the template from `game/sessions.md`. Fill in:
- Void Corruption: 8% (world starts partially corrupted)
- Corruption Rate: 1.0 × difficulty modifier
- Realm Status:
  - Emberveil: Intact
  - Thornwood: Intact
  - Crystalmere: Intact
  - Ashen Wastes: Damaged (60% consumed — fixed, does not worsen further until player triggers events there)
  - Skyreach: Intact
- All Shards: Not Found
- Malachar's Awareness: Dormant
- Known Rift Gates: player's starting Realm only

### Create `session/location.md`

Use the template from `game/sessions.md`. Set location based on player's starting Realm choice:

**If Emberveil:**
- Realm: Emberveil
- Area: Ironmaw Approach
- Zone: Ash Road (the main road leading toward Ironmaw Forge-City)
- Describe: ash-covered road, distant glow of volcanic fires, smell of sulfur and hot metal, the distant sound of hammering

**If Thornwood:**
- Realm: Thornwood
- Area: Forest Border
- Zone: The First Canopy (where the great trees begin)
- Describe: massive trees overhead, sudden darkness as the canopy closes in, sounds of unseen creatures, faint paths in the undergrowth

**If Crystalmere:**
- Realm: Crystalmere
- Area: Surface Tundra
- Zone: The Frost Approach (the surface wasteland above the crystal sea)
- Describe: howling wind, white stone and grey sky, distant shimmer of crystal below the ice, extreme cold

### Create `session/inventory.md`

Use the template from `game/sessions.md`. Fill in starting inventory based on subclass:

**All characters start with:**
- Gold: 25
- Health Potion × 2 (restores 30 HP each)
- Rift Shard Fragment × 1 (quest item — a tiny fragment of a Shard; glows faintly; Seraphel will want to see this)
- Worn Traveling Cloak (minor protection against elements; no combat bonus)

**Plus subclass-specific equipment:** (listed in Step 3b)

### Create `session/log.md`

Create with first entry:

```markdown
# Session Log

## [Turn 0] — A New Journey Begins
[CHARACTER NAME] steps through the last working Rift Gate and arrives at [starting location]. The gate collapses behind them. The world stretches out, dying and beautiful, in every direction. The hunt for the Shards begins.

---
```

### Create `session/npcs.md`

Create with no entries yet (player has not met anyone):

```markdown
# NPC Tracker

*No NPCs encountered yet.*
```

### Create `session/companions.md`

Create as empty:

```markdown
# Active Companions

**Slots Used:** 0 / 3

*No companions yet.*
```

### Create `session/quests.md`

Create as empty:

```markdown
# Quest Log

## Active Quests

*No active quests yet.*

---

## Completed Quests

*No completed quests yet.*
```

---

## Step 5: Display Character Summary

Present the player's completed character to them in a formatted block:

```
═══════════════════════════════════════
  THE SUNDERING OF AETHERMOOR
  Riftwalker: [NAME] — [Subclass]
═══════════════════════════════════════
  HP: [max] / [max]    MP: [max] / [max]
  STR: [X]  INT: [X]  AGI: [X]
  Rift Points: [X] / [X]

  Starting Location: [Realm — Area]
  Void Corruption: 8%
  Shards Collected: 0 / 5
═══════════════════════════════════════
```

---

## Step 6: Opening Scene

Read `session/location.md` and present a vivid opening scene to the player. Include:

1. The immediate environment (from location.md description)
2. A sense of the Void's presence — slight, distant, but unmistakably there
3. A first possible path or point of interest
4. A brief awareness of the player's own state (alone, Rift Gate gone, the weight of what they're attempting)

End the opening scene with an implied prompt for the player's first action. Do not ask a question — let the scene breathe and wait for the player to act.

Example closing line (adjust to match starting Realm):
- Emberveil: *"The hammering continues somewhere ahead, indifferent to the state of the world. You are on the Ash Road. What do you do?"*
- Thornwood: *"The forest breathes around you. Something in the canopy is watching. You are at the First Canopy edge. What do you do?"*
- Crystalmere: *"The wind cuts through you. Somewhere below, in the crystal dark, a city glimmers. You are on the Frost Approach. What do you do?"*

---

## Initialization Complete

The game is now running. Hand off to the gameplay loop defined in `agent/game.md`.
