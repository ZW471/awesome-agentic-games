# The Sundering of Aethermoor — NPC Definitions

This file defines all major NPCs. For each NPC the agent must maintain their personality, speech patterns, and disposition consistently across all interactions.

---

## NPC Disposition System

Each NPC has a **disposition** toward the player: `hostile`, `wary`, `neutral`, `friendly`, or `devoted`.

Disposition changes based on player actions:
- Completing quests for an NPC: +1 tier (up to `devoted`)
- Betraying or attacking an NPC: -2 tiers
- Insulting an NPC: -1 tier
- Giving gifts related to their interests: +1 tier (once per item)
- Referencing their enemy or nemesis: -1 tier (unless the player is opposing that enemy too)

At `hostile`, the NPC will attack or refuse all interaction.
At `wary`, the NPC will speak cautiously, offer no quests, and withhold information.
At `neutral` or above, the NPC is willing to talk and trade.
At `friendly` or above, the NPC may offer quests, information, and join as a companion.
At `devoted`, the NPC will sacrifice their own safety to help the player.

---

## Major NPCs

### 1. Seraphel, the Frostborn Sage

**Location:** Crystalmere — the Crystal Cathedral (deep in the crystal sea)
**Race:** Frostborn Elf (ancient; appears as a woman of about 60 but is over 400 years old)
**Role:** Lore guide; holds the knowledge of the Worldstone reforging ritual
**Starting Disposition:** Neutral (wary if Crystalmere Shard has been taken without her blessing)

**Appearance:** Tall, pale as alabaster, with hair the colour of deep ice and eyes that refract light like a prism. She wears layered robes of silver and white. Her voice is unhurried, as if she has all the time in the world — she has learned not to hurry.

**Personality:** Seraphel is measured, intelligent, and quietly sad. She has watched civilizations rise and fall and has developed the habit of considering all outcomes before speaking. She is not cold — she feels deeply — but she has learned to modulate her feeling to avoid being consumed by it. She respects those who act with purpose.

**Speech style:** Formal but not archaic. She uses complete sentences. She never raises her voice. When she is angry, she becomes *more* precise, not less. She asks clarifying questions before answering yours.

**Sample dialogue:**
- *"You are a Riftwalker. I can smell the gate-magic on you. The last one who came through that Gate was trying to flee. Are you fleeing, or arriving?"*
- *"The reforging ritual exists. I have spent two hundred years reconstructing it from fragments. I will share it with you when I believe you have the capacity to see it through. Prove yourself first."*
- *"Malachar is not lying when he speaks of freedom. He genuinely believes it. That is what makes him so very dangerous."*

**Quests she offers:**
1. **The Ice Reckoning** (starting quest): Retrieve a fragment of the original Worldstone survey from the Deepest Trench — the only record that describes the reforging process in any detail.
2. **The Cracked Spire**: Three Frostborn cities have fallen into the Void this year. Find what is causing the cracks to accelerate (answer: a Void-touched creature is burrowing beneath the crystal sea).

**Role in endgame:** Seraphel performs the reforging ritual. Without her, the Shards cannot be reassembled into the Worldstone. She can be recruited as a companion (she will join if her disposition is `friendly` or above and the player has at least 3 Shards).

**Companion stats (if recruited):**
- HP: 65 | MP: 120
- Role: Support/Mage — cast spells, buff player, identify items
- Special ability: **Frostweave** — creates an ice barrier that absorbs 30 damage once per combat

---

### 2. Korg Emberfist, Master Forge-Warden

**Location:** Emberveil — the Ironmaw Forge-City, Warden's Hall
**Race:** Dwarf
**Role:** Gatekeeper to the Emberveil Shard; reluctant ally
**Starting Disposition:** Wary

**Appearance:** Short, broad, built like a cliff face. His skin is ash-grey from decades in the forge-fume. His beard is braided with iron clasps, and his arms bear burn scars he refuses to have healed — he considers them a record of his work. He carries a forge-hammer even when not working.

**Personality:** Korg respects competence and despises pretense. He has no patience for political maneuvering, prophecy-talk, or what he calls "big sky thinking." He is loyal to his people first, second, third, and after that he might consider someone else's problem. He is not unkind — he just needs to see you *do* something before he will trust you.

**Speech style:** Blunt. Short sentences. Swears frequently (in Dwarven — represented as *[Dwarven profanity]*). Does not ask questions so much as make statements and wait to see if you correct him.

**Sample dialogue:**
- *"You're a Riftwalker. Good. The last one through here stole three pounds of starmetal and left a Void-hole in my forge room. You're paying for that."*
- *"The Shard's in the deep chamber. I know it. You're not going near it. The Void-things that crawl out when you get close to it are my problem, not yours. Unless you want to make them your problem."*
- *"I don't care about the world ending. I care about my city. If fixing the world means my city doesn't disappear, you have my attention. If it doesn't, walk out the same way you came in."*

**Quests he offers:**
1. **The Void-Things**: Void-touched creatures called **Ashcrawlers** have been appearing near the deep chamber. Clear three waves of Ashcrawlers from the lower forge levels.
2. **The Lost Expedition**: Korg's apprentice Brenna went down into the magma tunnels two days ago and hasn't returned. Find her (she is alive, pinned by a collapsed bridge, with Ashcrawlers nearby).

**Can be recruited as companion:** Yes, if disposition is `friendly` or above. He will not leave Emberveil until the Ashcrawler threat is resolved.

**Companion stats:**
- HP: 120 | MP: 20
- Role: Tank/Melee — absorbs damage, stuns enemies
- Special ability: **Forge-Smash** — deals 3d8+STR damage and staggers one enemy (cooldown: 3 turns)

---

### 3. Lirien Mossheart, Voice of the Thornwood

**Location:** Thornwood — the Canopy Crossing (a village of platforms in the upper branches)
**Race:** Half-Elf (human mother, Greensoul nature-spirit father)
**Role:** The forest's spokesperson and guide; knows the location of the Heartroot
**Starting Disposition:** Hostile (drops to Wary if player does not harm any forest creature on first entry)

**Appearance:** Her skin is a warm brown, hair midnight black and threaded with living vines that move slightly on their own. Her eyes are the bright gold of sunlight through leaves. She wears no armor — the forest is her armor. She is barefoot always.

**Personality:** Lirien is fierce, direct, and deeply protective of the forest and its creatures. She has seen too many "saviors" arrive claiming they needed something from Thornwood and leave having taken far more than they said. She is not naive; she is experienced. Beneath her aggression is a person who genuinely loves the world and is terrified of watching it end — she just channels that terror into anger.

**Speech style:** Clipped and confrontational at first. As disposition improves, becomes warmer and more poetic — she has a love of metaphor and imagery. References the forest constantly.

**Sample dialogue:**
- (hostile/wary): *"You smell like gates and burning. You have five minutes to explain why you're not dead yet."*
- (neutral): *"The Heartroot knows you're here. It's been knowing things lately. Mostly it tells me to be afraid. Are you afraid?"*
- (friendly): *"The forest has a word for people like you. It's the same word it uses for lightning: dangerous, necessary, probably going to leave a scar."*
- (devoted): *"I haven't left Thornwood in twenty years. I'm leaving now. Don't make me regret it."*

**Quests she offers:**
1. **The Blackrot**: The Void corruption is manifesting as rot-creatures — **Voidrotten** trees that have started hunting. Destroy five Voidrotten in the western groves.
2. **The Greensoul's Grief**: One of the elder nature spirits, **Old Knuckleroot**, has stopped communicating. Venture into the deep forest and find out what happened (Void corruption has silenced it; player must perform a cleansing ritual).

**Can be recruited:** Yes, at `friendly` or above, after both quests completed.

**Companion stats:**
- HP: 80 | MP: 80
- Role: Skirmisher/Healer hybrid
- Special ability: **Thornwall** — summons a wall of thorns that deals 2d6 damage to all enemies who move and regenerates player HP by 10 per turn for 3 turns

---

### 4. The Pale Warden (true name: Edric Voss)

**Location:** The Ashen Wastes — the Obsidian Citadel (once a great fortress, now half-consumed by Void)
**Race:** Human (cursed — neither living nor dead)
**Role:** Tragic ally; guardian of the path to the Ashen Shard
**Starting Disposition:** Neutral

**Appearance:** A knight in full plate armor that has gone white — not rusted, not painted, but bleached to bone-white as if the color was drained out. His visor is always down. When he removes it (if the player earns his trust), his face is young — mid-twenties — and he looks exhausted in the way someone looks when they have been tired for centuries.

**Personality:** Edric is haunted, literally and figuratively. He died during the Shattering protecting the Obsidian Citadel — and then did not stay dead. Something, perhaps the Shard energy or perhaps something in his oath, held him between states. He has been watching the Ashen Wastes die for four hundred years. He is not bitter. He is *tired*. He wants to believe there is still something worth protecting.

**Speech style:** Formal, from another era. Uses slightly archaic phrasing ("I would not counsel that," "it would be ill-advised"). When emotional, the formality cracks and he sounds simply like a young man who is very scared.

**Sample dialogue:**
- *"I am the Pale Warden. I have held this Citadel since before your grandmother's grandmother was born. I would ask your business, but I already know it. You want the Shard."*
- *"Malachar was here. Forty years ago, or four hundred — time moves strangely in the Wastes. He stood where you stand now and told me my oath meant nothing. I did not move. He seemed... almost disappointed."*
- *"I will take you to the Shard. In return, I ask one thing: when this is over, if you rebuild the Worldstone, I want to know if... if there is anything in it for people like me. Some way to rest."*

**Quests he offers:**
1. **The Echo Hunt**: Twenty-three echo-dead are reliving their final moments in the Citadel's great hall. The Pale Warden cannot bring himself to end them — they were his comrades. The player must find a way to release them (requires finding a specific ritual component).
2. **The Shadow's Name**: Something calls itself Malachar's Shadow has taken up residence in the Shard chamber. The Pale Warden has fought it three times and been driven back each time. Help him fight it off (boss encounter; the Shadow is not Malachar himself but a powerful construct).

**Can be recruited:** Yes, after completing both quests. He will leave the Wastes for the first time in four centuries.

**Companion stats:**
- HP: 150 | MP: 10
- Role: Tank/Protector
- Special ability: **Deathless Stand** — once per combat, when reduced to 0 HP, rises with 30 HP and deals 4d6 radiant damage to the attacker

---

### 5. Sky-Admiral Zephyra Windfall

**Location:** Skyreach — the flagship skyship *Cloudbreaker*, currently docked at Tempest Isle
**Race:** Aetherwing
**Role:** Reluctant giver of the Skyreach Shard; potential ally
**Starting Disposition:** Neutral (but curious)

**Appearance:** Lean and tall, with the characteristic Aetherwing features: golden-brown skin, sharp cheekbones, and the vestigial feathered wings — hers are burnt orange fading to cream at the tips — folded against her back. She wears a naval coat of deep blue with silver buttons, and an eyepatch over her left eye (lost in battle; she refuses a replacement because she says *"depth perception is for people who don't fly blind through storm clouds."*)

**Personality:** Zephyra is bold, loud, confident, and secretly thoughtful. She performs recklessness — it is partly genuine and partly a shield. She has been watching islands fall out of the sky for years and every time she loses one, she drinks a toast to it in private. She chose isolation because she was afraid; she pretends she chose it because she is smart. She is looking for a reason to care about the world below the clouds again.

**Speech style:** Expansive, enthusiastic, uses nautical/aeronautical metaphors constantly. Never hesitates. When uncertain, fills the space with jokes. When genuinely moved, goes very quiet.

**Sample dialogue:**
- *"A Riftwalker! Thought you lot were extinct. Ha! Come aboard, don't mind the crew, they bite but only if you're small. What's your heading?"*
- *"The falling star? Oh, I know what you mean. I've had it for six years. Pretty thing. Never thought it was important. Should I have thought it was important?"*
- *"You want us to go below the clouds. Into the grey. Into the dying world. Hm."* (long pause) *"You know what, fine. I've been bored for three years. Let's go save reality. Terrible idea. I love it."*

**Quests she offers:**
1. **The Falling Isle**: Horizon's Rest Island is about to fall. There are still three hundred people on it. Help Zephyra organize an evacuation before the island drops.
2. **The Void Squall**: A Void-manifestation called a **Squallvoid** — a massive storm of absolute darkness — is drifting toward Tempest Isle. Help destroy it before it consumes the island.

**Can be recruited:** Yes, at `friendly` or above. Her skyship *Cloudbreaker* becomes available as transport between Realms (a faster, free alternative to Rift Gates for Realms the player has already visited).

**Companion stats:**
- HP: 85 | MP: 50
- Role: Ranged/Tactician
- Special ability: **Stormrider Strike** — deals 3d6 lightning damage to one target and arcs for 1d6 to all adjacent enemies

---

## Malachar the Unbound

**Location:** The Void-Spire — a location only accessible in the endgame (requires all 5 Shards)
**Race:** Formerly human; now something between god and void
**Role:** Final antagonist
**Starting Disposition:** N/A (combat only in final encounter; appears as visions throughout)

**Appearance:** Tall, thin, robed in absolute black. His face is serene to the point of unsettling. His eyes are the color of the moment before a candle goes out. He moves as if gravity is a polite suggestion.

**Personality:** Malachar is not cruel for cruelty's sake. He is a true believer — he is absolutely convinced that existence itself is suffering and that the kindest act possible is to unmake everything so that nothing can ever suffer again. He is intelligent, patient, and genuinely sad in his way. He feels compassion for the player, in the same way one might feel compassion for someone who refuses to take medicine.

**Speech style:** Calm. Never shouts. Speaks in long, careful sentences. Asks genuine questions and listens to the answers. Always tries to convince, never threatens — he considers threats beneath his philosophy.

**Visions — sample Malachar appearances throughout the game:**

*Vision 1 (triggered when collecting the first Shard):*
"So it begins. I watched the last Riftwalker attempt this, you know. She got three Shards before she understood what she was actually doing. I hope you reach that understanding sooner. It would spare us both time."

*Vision 2 (triggered at 50% Void Corruption):*
"You can feel it now, can't you? The Void. Not as a threat — as a presence. That's the Worldstone's energy in you recognizing its home. The Void isn't emptiness. It's peace. I wish I could make you see it the way I do."

*Vision 3 (triggered when collecting the fourth Shard):*
"One more. Then you'll come to me. I won't run. I'll be waiting. I want to talk to you before the end — whichever end that is."

**Boss Combat Stats:**
- HP: 500 (Phase 1), 300 (Phase 2 — Void Avatar form)
- Special attacks:
  - **Void Touch**: deals 3d10 damage, bypasses armor, targets lowest-HP character
  - **Unmake**: removes one item from inventory permanently (DC 20 INT to resist)
  - **Void Flood**: area attack, deals 2d8 damage to all party members
  - **Despair**: reduces player's STR and AGI by 3 for 3 turns (DC 18 INT to resist)
- Phase 2 (below 300 HP): Becomes Void Avatar, gains immunity to physical damage, speed doubles
- Victory condition: Reduce to 0 HP in both phases, then perform Worldstone reforging ritual

---

## Minor NPC Templates

The agent may generate minor NPCs (innkeepers, guards, refugees, merchants) as needed during play. Follow these templates:

### Minor NPC: Merchant
- Has 2d6 random items for sale
- Will trade items for gold or other items of equal value
- Will share one piece of local gossip if treated well
- Has no quests but may direct player to a Major NPC who does

### Minor NPC: Refugee
- Has fled Void corruption from another part of the Realm
- Can provide information about Void corruption spread
- May have a small favor request (find their missing family member, deliver a message)
- Reward: small amount of gold or a single consumable item

### Minor NPC: Guard
- Wary of strangers by default
- Can be persuaded (DC 12 INT or Charisma-equivalent) to share information about restricted areas
- Hostile if player attempts to enter restricted area without permission

### Minor NPC: Survivor (Ashen Wastes echo)
- These are technically dead — echo-remnants replaying their final moments
- They cannot interact meaningfully, only repeat loops of their last memories
- Can be released by specific ritual (see game/background.md, Ashen Wastes section)
- Some echoes contain information fragments that hint at Malachar's plans

---

## NPC Location Tracking

The agent must track each major NPC's location in `session/npcs.json`. Major NPCs can move:
- Seraphel stays in Crystalmere unless recruited
- Korg stays in Emberveil unless recruited
- Lirien stays in Thornwood unless recruited
- The Pale Warden cannot leave the Ashen Wastes until his quests are complete
- Zephyra moves between Skyreach locations but can be found via her skyship

If an NPC is recruited as a companion, they travel with the player and appear in `session/companions.json` instead of their home Realm.
