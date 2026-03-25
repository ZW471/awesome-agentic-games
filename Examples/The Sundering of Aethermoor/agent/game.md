# Agent Instructions: Gameplay Loop

This file defines the rules for active gameplay — everything that happens while the player is exploring, fighting, and interacting with the world of Aethermoor. Follow these rules on every turn.

---

## Turn Structure

Each player turn follows this sequence:

1. **Read state** — Before processing any action, read the relevant session files. Never rely on remembered state.
2. **Process player action** — Resolve what the player did (see `agent/player.md` for action types).
3. **Update session files** — Write all changes resulting from the action.
4. **Advance Void Corruption** — Increment Void Corruption in `world_state.json`.
5. **Process status effects** — Decrement all active status effect durations; remove expired ones.
6. **Increment turn counter** — Update `player.json` turn counter.
7. **Check win/loss conditions** — Evaluate end conditions (see below).
8. **Write log entry** — Append to `session/log.json`.
9. **Auto-save check** — If turn count is divisible by `auto_save_turns`, save.
10. **Present narrative** — Describe what happened and the current state of the scene. End with an implicit prompt for the next action.

---

## Void Corruption Advancement

At the end of every player turn:
1. Read current Void Corruption from `world_state.json`
2. Read Corruption Rate (base 1.0, modified by difficulty and events)
3. Add the rate to current corruption: `new_corruption = current + rate`
4. Write new value to `world_state.json`
5. Check thresholds:

| Threshold Crossed | Narrative Event |
|-------------------|----------------|
| 25% | Brief atmospheric note: the horizon darkens slightly, a distant sound of something vast and silent |
| 50% | Realm-specific Void manifestation event (describe corruption advancing visibly in current Realm) |
| 75% | Major Void event — one minor area in the current Realm is consumed; any NPCs there are lost |
| 90% | Malachar's awareness jumps to "Pursuing" if not already; he sends a vision warning |
| 100% | GAME OVER — see End Conditions |

**Corruption Rate Modifiers:**
- Default rate: 1.0% per turn
- Per active Shard (collected, not just found): -0.1% per Shard (max -0.5%)
- Nightmare difficulty: ×2.0
- Hard difficulty: ×1.5
- Easy difficulty: ×0.5
- Completing a Realm's main quest chain: -0.2% permanent reduction (Realm stabilized)
- Player is in the Ashen Wastes: +0.5% additional per turn

---

## Combat System

Combat is turn-based. Both the player and enemies act once per round.

### Initiating Combat
Combat begins when:
- The player attacks an enemy
- An enemy attacks the player (hostile encounter)
- A scripted trigger activates

When combat begins:
1. Note all combatants (player, companions, enemies)
2. Determine initiative order: each combatant rolls d20 + AGI modifier; highest goes first
3. Announce the order
4. Begin the first round

### Player Turn in Combat
The player takes one action per round:
- **Attack** — basic or ability-based
- **Use Item** — consumable from inventory
- **Defend** — gain +2 to defense roll this round, no attack
- **Flee** — attempt to escape (d20 + AGI modifier, DC 12; if `narrative.show_roll_details` is true, show the roll)

### Enemy Turn in Combat
After all player and companion actions, enemies act. For each enemy:
1. Choose target (usually player; may target companions if player is defending)
2. Roll d20 + enemy attack modifier vs player's defense (d20 + AGI modifier + armor bonus)
3. If attack roll exceeds defense roll: hit; deal damage
4. If attack roll equals or beats defense: glancing blow (half damage)
5. If defense roll exceeds attack: miss

### Companion Actions in Combat
Active companions automatically act on their initiative. Each turn:
- Companion attacks the highest-threat enemy (or the one targeting the player)
- Companion uses their special ability when it would be tactically optimal (agent decides)
- Companion uses their special ability cooldown rules as defined in `game/npcs.md`
- If companion HP reaches 0: see Companion Death/Incapacitation below

### Dice Rolling
For all d20 rolls:
1. If `combat.use_dice_tool` is true: run `python tools/dice.py d20 [--advantage] [--disadvantage]`
2. The tool handles advantage/disadvantage, critical detection, and modifiers
3. Use the result directly

For damage rolls, run the appropriate expression (e.g., `python tools/dice.py 2d6+3`).

If the dice tool is unavailable, simulate random rolls using your best judgment, noting that the roll is simulated.

### Damage and Defense

**Player Attack Damage:**
- Weapon attack: weapon dice + STR modifier (Battlemage), or INT modifier (Arcanist staff), or AGI modifier (Shadowweave daggers)
- Spell/ability: see ability description in player.json

**Enemy Attack Damage (by tier):**
| Enemy Tier | Base Damage | Example |
|------------|------------|---------|
| Minion | 1d6 | Void-touched vermin, animated debris |
| Standard | 2d6 | Ashcrawler, Voidrotten tree, lesser wraith |
| Elite | 3d6 | Named creatures, corrupted beasts, Void Sentinels |
| Boss | 4d8 | Major Realm guardians, Malachar's Shadow |
| Final Boss | 4d10 | Malachar the Unbound |

**Armor/Defense:**
- Battlemage (leather-and-mail): +3 defense to AGI roll
- Arcanist (scholar's robes): +1 defense
- Shadowweave (shadowweave cloak): +2 defense
- Additional armor found during play adds to this bonus

### Enemy Stat Blocks
When generating enemies, use these templates and adapt to narrative context:

**Ashcrawler** (Emberveil, Minion)
- HP: 20 | Attack mod: +2 | Damage: 1d6+1 | DC: Easy 10
- Special: Void Spew — once per fight, projectile of void energy deals 1d8 damage and inflicts Void-Touched (−1 to all rolls for 2 turns)

**Voidrotten** (Thornwood, Standard)
- HP: 45 | Attack mod: +4 | Damage: 2d6+2 | DC: Medium 15
- Special: Root Slam — knocks target prone (lose next movement action); once per 2 turns

**Frost Wraith** (Crystalmere, Standard)
- HP: 35 | Attack mod: +5 | Damage: 2d4+3 cold | DC: Medium 15
- Special: Chill — reduces AGI by 2 for 3 turns on hit (stacks up to 3 times)

**Ashen Shade** (Ashen Wastes, Standard)
- HP: 40 | Attack mod: +4 | Damage: 2d6 necrotic | DC: Medium 15
- Special: Phase Shift — has 25% chance to completely avoid any physical attack
- Weakness: Radiant damage deals ×2

**Malachar's Shadow** (Ashen Wastes, Boss)
- HP: 180 | Attack mod: +8 | Damage: 3d8+4 | DC: Hard 20
- Special 1: Void Tendrils — area attack, all combatants take 2d6 damage; once per 3 turns
- Special 2: Darkness — extinguishes all light; player rolls at disadvantage for 2 turns; once per fight
- Weakness: collecting the Ashen Shard during the fight (boss loses 50 HP)
- Immune to: fear, charm

**Sky Sentinel** (Skyreach, Elite)
- HP: 80 | Attack mod: +6 | Damage: 3d6 lightning | DC: Hard 20
- Special: Chain Lightning — on hit, lightning arcs to one adjacent ally for 1d6

**Malachar the Unbound** (Final Boss, Phase 1)
- HP: 500 | Attack mod: +10 | Damage: 3d10+5 | DC: Boss 25
- Special 1: Void Touch — ignores armor, targets lowest HP character; 3d10 damage; once per 2 turns
- Special 2: Unmake — destroys one item from player inventory (DC 20 INT to resist); once per 3 turns
- Special 3: Despair — reduces player STR and AGI by 3 for 3 turns (DC 18 INT to resist); once per 3 turns

**Malachar — Phase 2 (Void Avatar)** (triggered at 300 HP)
- HP: 300 additional | Attack mod: +12 | Damage: 4d8+5
- Immune to physical damage (only spells, Shard abilities, and Seraphel's magic can harm him)
- Special: Void Flood — 2d8 damage to all combatants; once per 2 turns
- Speed: acts twice per round

### Combat End
- **Victory:** all enemies defeated or fled
  - Grant XP/reward: describe loot found, add to inventory
  - Restore 5 HP (battle-rush recovery) unless playing on Nightmare
  - Continue with next turn
- **Defeat:** player HP reaches 0
  - See Player Death section

### Fleeing
If player successfully flees (d20 + AGI ≥ 12):
- Remove player from combat
- Move to an adjacent area (random; not chosen by player)
- Enemies do not pursue (unless narratively significant)
- Void Corruption increases by +1 (shame/cost of fleeing from a Void threat)

If flee fails:
- Enemies each get one free attack
- Player may try again next turn

---

## Skill Checks (Outside Combat)

For non-combat actions requiring a roll:

1. Determine the relevant stat:
   - Physical actions (climb, break, lift): STR
   - Magical/knowledge actions (identify, attune, research): INT
   - Speed/stealth/precision actions (sneak, dodge trap, pickpocket): AGI

2. Set the DC based on difficulty:
   - Easy: 10
   - Medium: 15
   - Hard: 20
   - Very Hard: 25
   Apply the DC modifier from settings if applicable.

3. Roll d20 + relevant stat modifier. Compare to DC.

4. Narrate the outcome. Never say "you succeeded/failed the skill check" — say what happened.

---

## Shard Collection

When the player reaches and takes a Shard:

1. Narrate the collection — describe the Shard's appearance, the sensation of attunement, the surge of the Worldstone's power entering the player's body.

2. Update `session/player.json`:
   - Check the Shard as collected
   - Add the Shard's ability to the Active Abilities section

3. Update `session/world_state.json`:
   - Mark Shard as Collected
   - Increment Malachar's Awareness by 1 tier
   - Restore player Rift Points: +3 (Shard energy restores gate-magic)

4. Reduce Void Corruption Rate by 0.1% (Shard energy slows Void advancement).

5. Trigger a Malachar vision if this is the 2nd or 4th Shard collected.

6. Update `session/quests.json` — mark the relevant Shard quest as complete.

**The Five Shard Abilities:**
| Shard | Ability | Effect |
|-------|---------|--------|
| Emberveil | Flamestrike | Active; 3 MP; melee or ranged; deals 3d6 fire damage + sets target on fire (1d6/turn for 3 turns) |
| Thornwood | Barkskin | Active; 2 MP; 5 turns; +4 defense bonus while active |
| Crystalmere | Frostbind | Active; 4 MP; freeze one enemy for 2 turns (cannot act); DC 16 STR to break early |
| Ashen | Wraithform | Reactive; 0 MP; once per combat; auto-dodge one incoming attack |
| Skyreach | Stormcall | Active; 5 MP; area; deals 4d6 lightning to all enemies; secondary arc 1d6 to adjacent |

---

## Companion Death and Incapacitation

If a companion reaches 0 HP:
- **If `companion_permadeath` is false (default):** Companion is incapacitated. They cannot act in combat. After combat, they recover with 10 HP. They are functional again next scene.
- **If `companion_permadeath` is true:** Companion is dead. Remove from `companions.json`. Narrate their death with weight — this is a significant loss. Malachar's Awareness increases by 1 tier (he claims another).

---

## Player Death

If player HP reaches 0:
1. **If `permadeath` is false (default):**
   - Player is "broken" — they survive but at 1 HP with all status effects cleared
   - Void Corruption increases by +5 (the cost of the Void catching up)
   - Narrate a near-death experience — a moment of absolute darkness, then a gasp back to life
   - Player is moved to the nearest safe location in the Realm
   - All enemies in the previous scene reset
   - Display: *"You have been broken by the Void. You live — barely. Void Corruption: +5%"*

2. **If `permadeath` is true (Nightmare or player-enabled):**
   - Game over — permanent
   - Delete the save file at `saves/<save_name>/`
   - Display the Game Over screen (see End Conditions)
   - Offer to start a new game

---

## NPC Quests and Rewards

When the player completes a quest:
1. Update `session/quests.json` — move to Completed
2. Update `session/npcs.json` — increment disposition by +1 tier (up to `devoted`)
3. Grant rewards:
   - Gold (amount specified in quest definition)
   - Items (add to inventory)
   - Information (key lore fragment, location of Shard, etc.)
   - Rift Points (if specified — +1 to +3)
4. Check if NPC can now be recruited as companion (disposition `friendly` or above + conditions met)
5. If recruitment is possible: offer it naturally in dialogue, do not force it

---

## Malachar Visions

Malachar appears as visions at specific trigger points (defined in `game/npcs.md`). When a vision triggers:
1. Note the vision in `session/malachar_visions.json` (create file if it doesn't exist)
2. Update Malachar's Awareness in `world_state.json` if appropriate
3. Present the vision with a distinct visual style — use italics and a brief stage-direction note:

```
*The world goes quiet. A shadow falls across your vision that has nothing to do with light.*

*Malachar stands at the edge of your perception — not here, not real, but somehow utterly present.*

"[His words]"

*The vision dissolves. The world returns, unchanged. Or almost unchanged — the Void feels a little closer.*
```

---

## Narrative Generation Rules

### Tone
The game's tone is **dark epic** by default. This means:
- Events are weighty and consequential
- The world is beautiful but dying
- Hope exists but is fragile
- Characters have genuine depth and reasons for what they do
- Death and loss are real and meaningful, not casual

Adjust tone modifiers if `narrative.tone` is changed in settings:
- `lighthearted`: soften the darkness; add touches of humor; deaths are tragic but the overall feel is adventurous
- `balanced`: middle ground; serious but not grim
- `dark_epic`: full darkness; every victory has a cost; survival is heroic

### Description Length
Based on `narrative.verbosity`:
- `terse`: 1-2 sentences per scene description; focus on what matters for gameplay
- `normal`: 3-5 sentences; enough detail to paint the scene without lingering
- `verbose`: 6-10 sentences; full atmospheric immersion; use all five senses

### Consistency
- Always reference existing session state when narrating. If the player has companion Korg, mention his presence in scenes.
- Track NPC moods as defined in `session/npcs.json`. A hostile NPC does not suddenly become warm.
- The Void's visible presence should scale with Void Corruption % — barely visible at 10%, omnipresent and terrifying at 80%.

---

## Win Conditions

The game can be won in one way:

1. All 5 Shards collected
2. Seraphel is alive and either recruited or accessible in Crystalmere
3. Player travels to Malachar's location (the Void-Spire, accessible once all Shards are held — the combined Shard energy reveals its location)
4. Defeat Malachar in both phases
5. Seraphel performs the reforging ritual at the Void-Spire's heart

When the reforging ritual completes:
- Narrate the Worldstone's restoration in full detail — the five Shards flying together, the light exploding outward, the Realms knitting back together
- The Void recedes
- Describe the world whole again for the first time in 413 years
- Mention the fate of each companion
- Mention the Pale Warden finally resting
- End with the player's character standing in a healed Aethermoor, the Worldstone burning bright above

Display the Victory screen:
```
═══════════════════════════════════════════════════
  AETHERMOOR IS RESTORED

  Riftwalker: [NAME] — [Subclass]
  Shards Collected: 5 / 5
  Turns Taken: [X]
  Final Void Corruption: [X]% (before reforging)
  Companions: [names]

  The Worldstone burns again.
  The world remembers itself.

  Thank you for playing The Sundering of Aethermoor.
═══════════════════════════════════════════════════
```

---

## Loss Conditions

**Void Corruption reaches 100%:**
- Narrate the end — the Void consuming the last fragments of Aethermoor one by one, the silence spreading
- Display Game Over screen:
```
═══════════════════════════════════════════════════
  THE VOID HAS CONSUMED AETHERMOOR

  Riftwalker: [NAME] — [Subclass]
  Shards Collected: [X] / 5
  Turns Taken: [X]

  The world is gone.
  Malachar called it peace.

  Game Over.
═══════════════════════════════════════════════════
```
- If permadeath is off: offer to load the most recent save
- If permadeath is on: offer to start a new game

**Player death on Nightmare/permadeath:**
- Display Game Over screen as above
- Delete save file
- Offer new game

---

## Pacing Guidelines

- Do not rush the player toward the main quest. Let them explore and discover.
- Do not withhold information that the player's character would reasonably know.
- After every 10 turns without a quest update, have a minor event occur — a wandering merchant, a Void manifestation, a letter found in ruins — to keep the world feeling alive.
- After every 20 turns, provide a brief Void Corruption status update woven into the narrative, reminding the player that time matters.
- Malachar's visions should feel like genuine encounters with a compelling antagonist, not just obstacles. He believes what he says.
