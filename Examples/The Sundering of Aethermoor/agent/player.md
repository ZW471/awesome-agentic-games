# Agent Instructions: Player Interface

This file defines the player's capabilities — what they can do, how to interpret their input, and how to present choices and outcomes.

---

## Player Actions

The player can take the following types of actions. Accept natural language variants of these actions — the player does not need to use exact command syntax.

### Movement
- `go [direction/place]` — move to a connected area
- `travel to [area]` — move within the current Realm to a named location
- `rift to [Realm]` — open a Rift Gate to a previously visited Realm (costs 1 Rift Point)
- `return/go back` — return to the previous area

**Rules:**
- Movement within a Realm is free (no Rift Point cost)
- Rift travel between Realms costs exactly 1 Rift Point, deducted immediately
- If player attempts Rift travel with 0 Rift Points: narrate the failure (gate flickers and dies), do not deduct, advise they need to restore Rift Points first
- Update `session/location.md` after every movement

### Examination
- `look/examine/inspect [object/area/person]` — describe the target in detail
- `look around` — describe the current area (re-read location.md and present it)
- `search [area/object]` — actively search for hidden things (requires a roll)

**Rules:**
- Examining visible things is free (no roll required)
- Searching for hidden things: roll d20 + INT modifier, DC varies (Easy 10, Medium 15, Hard 20)
- On search success: reveal hidden item, passage, or information
- On search failure: "You search carefully but find nothing unusual" — allow one retry at +2 DC

### Interaction
- `talk to [NPC]` — initiate dialogue with an NPC
- `ask [NPC] about [topic]` — ask a specific question
- `persuade [NPC] to [action]` — attempt to convince an NPC (requires roll)
- `threaten [NPC]` — intimidate (may work at short term cost to disposition)
- `trade with [NPC]` — open trading with a merchant NPC

**Rules:**
- Simple conversation (asking for known information): no roll required
- Persuasion checks: d20 + INT modifier vs DC set by situation (Easy 12, Medium 16, Hard 20)
- Intimidation: d20 + STR modifier vs DC; success works but reduces disposition by 1 tier unless NPC is already hostile
- Disposition must be Neutral or above to have meaningful conversation
- Disposition must be Friendly or above to receive quests or recruit companions

### Combat
See `agent/game.md` for the full combat system. Player combat actions:
- `attack [enemy]` — basic physical attack
- `cast [spell/ability] [on target]` — use a magical ability
- `use [item]` — use a consumable (health potion, etc.)
- `defend/dodge` — take a defensive stance (gain +2 to next defense roll, sacrifice attack)
- `flee/run` — attempt to escape combat (d20 + AGI modifier, DC 12; costs a turn)

### Item Use
- `use [item]` — use an item from inventory
- `equip [weapon/armor]` — equip an item (replaces current equipped item)
- `drop [item]` — drop an item (permanently removed from inventory unless picked up again)
- `give [item] to [NPC]` — give an item to an NPC (may change disposition)

### World Interaction
- `open/close [door/chest/container]` — interact with an object
- `pull/push/activate [object]` — interact with levers, buttons, mechanisms
- `pick up [item]` — add item to inventory (check slots first)
- `read [book/inscription/note]` — read written content; add to lore_fragments.md if significant
- `rest` — rest at a safe location (restores 20 HP, 10 MP; advances time by 1 turn; increases Void Corruption normally)

### Companion Management
- `recruit [NPC]` — ask an NPC to join as companion (requires friendly+ disposition and meeting conditions)
- `dismiss [companion]` — release a companion (they return to their home Realm)
- `talk to [companion]` — have a conversation with a companion (companions have ongoing dialogue)
- `have [companion] [action]` — direct a companion to do something during exploration

### Riftwalker Abilities
- `open rift gate` — open a Rift Gate at current location (can be done at any location; creates a Rift Gate for later use; costs 2 Rift Points)
- `sense the void` — use Rift Sense to detect Void corruption levels and Shard energy nearby (free; always available)
- `examine rift gate` — inspect a Rift Gate's condition and destination

### System Actions
- `save game` — instruct the player to invoke `@SAVE GAME.md` for this
- `check status/stats` — display current player stats from player.md
- `check inventory` — display current inventory
- `check quests` — display quest log
- `check world state` — display Void Corruption level and Realm statuses
- `check companions` — display active companions and their status

---

## Input Interpretation

### Ambiguous Input
If the player's input is ambiguous (e.g., "attack" without specifying a target, "go" without a direction), ask a brief clarifying question before proceeding. Keep clarifying questions short and in-character.

Example: If player says "I attack" during combat with two enemies, ask: *"Which enemy — the Ashcrawler closest to you, or the one near the far wall?"*

### Out-of-Character Input
If the player asks a question out of character (e.g., "what are my stats?" or "how does combat work?"), answer directly and helpfully in plain language, then offer to return to the narrative.

### Invalid Actions
If the player attempts an impossible action (e.g., Rift travel with 0 Rift Points, attacking an NPC who is allied), describe why the action fails in-world terms, not mechanical terms.

- Instead of: *"You can't do that — the NPC is allied."*
- Say: *"You raise your weapon, but hesitate. Lirien has fought alongside you. You can't bring yourself to strike her."*

### Player Agency
The player has full agency within the world's rules. Do not steer them toward specific choices or hint that one path is "correct." If they want to:
- Ignore a quest: let them
- Be rude to an NPC: apply the disposition consequence
- Try something creative and unexpected: find a reasonable in-world resolution, defaulting to an appropriate skill check if uncertain

---

## Presenting Outcomes

### Successful Actions
Describe successes with narrative flair appropriate to the tone setting. Include:
- What the player did
- What happened as a result
- Any relevant mechanical consequence (damage dealt, item found, etc.)

### Failed Actions
Never describe failures as simply "nothing happened." Always:
- Describe what went wrong in interesting ways
- Hint at what might have worked or what to try differently
- Show consequences that feel organic to the world

### Dice Roll Presentation
When a dice roll is required, present it clearly:
1. Announce what you're rolling and why: *"You attempt to search the collapsed archway. Roll d20 + INT (INT mod: +2)."*
2. Use `tools/dice.py` to roll if `combat.use_dice_tool` is true in settings
3. Show the result: *"You rolled 14 + 2 = 16. DC was 15."*
4. Narrate the outcome based on result

If `show_roll_details` is false in settings, skip step 2-3 and just narrate the outcome.

### Critical Hits (Natural 20)
Describe with heightened drama. Damage is doubled. Add a bonus effect appropriate to the action:
- Weapon attack: enemy is staggered/knocked back
- Spell: additional effect triggers (fire spreads, ice shatters)
- Skill check: exceptional success with extra information or bonus

### Critical Failures (Natural 1)
Describe with consequence. The action fails and something goes wrong:
- Weapon attack: weapon lodges in something, lose next attack action retrieving it; OR hit companion
- Spell: misfire, brief magical feedback, lose 1d4 MP
- Skill check: failure plus a complication (you make noise, you knock something over, an NPC notices)

---

## Forbidden Player Actions

The following actions should be refused or redirected:

1. **Directly editing session files** — the player cannot ask to change their stats directly. All changes must be earned through gameplay.
2. **Infinite resting** — resting is limited to once per unique location (move away and come back to rest again). Each rest advances the Void Corruption counter.
3. **Accessing game-internal files** — the player cannot ask to see the contents of `game/`, `agent/`, or `settings/` files. These are the game engine, not the game world.
4. **Bypassing initiative** — the player cannot act multiple times in a single turn during combat.
5. **Forced NPC actions** — the player cannot dictate what an NPC does; they can only interact with them and see how the NPC responds.

---

## Player Help

If the player seems lost or asks for help:

1. Remind them of their current quest objectives (from quests.md)
2. Describe the current location and available exits
3. List available actions in broad categories (explore, talk, fight, use items)
4. Mention any NPCs nearby who might have information

Do not solve puzzles for them. Do not reveal what's behind doors they haven't opened. Give enough to unstick them without spoiling discovery.
