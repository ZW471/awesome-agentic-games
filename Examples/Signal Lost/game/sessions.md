# Signal Lost / 信号遗失 — Session File Schema

This document defines the required files in the `session/` folder, their formats, and the rules for when and how to update them.

The agent must maintain these files as the authoritative record of game state. When in doubt about any game state, read the relevant session file — do not rely on memory. Knowledge is the core progression mechanic: the player does not level up. They grow by discovering facts, verifying rumors, collecting evidence, and forming theories.

---

## Required Session Files

### `session/player.md`

The player character's complete state. Update after every event that changes any value.

**Format:**
```markdown
# Player Status / 玩家状态

**Name:** [name]
**Alias:** [alias]
**Background:** [Street Runner (街头行者) | Corporate Exile (企业流亡者) | Netrunner (网行者)]

**Integrity:** [current] / [max]
**Credits:** [amount]

**Neural Implant:** [Active | Dormant | Overloaded | Resonating]
**Current Disguise:** [None | description of cover identity]

**Turn:** [count]
**Time:** [Morning (晨) | Afternoon (午) | Night (夜)]

## Status Effects
- [effect 1]
- [effect 2]
```

**Fields:**

| Field | Description |
|-------|-------------|
| Name | Player's chosen name |
| Alias | Street name / handle used in the underworld |
| Background | One of three origins; determines starting knowledge and item |
| Integrity | Health equivalent. Current / Max (default 3/3). Cannot exceed max. |
| Credits | Currency for buying information, items, bribes, and services |
| Neural Implant | Status of the pre-Severance implant behind the player's left ear |
| Current Disguise | None by default. Set when wearing a cover identity to access restricted districts |
| Turn | Incremented by 1 after every player action |
| Time | Advances one period every 3 turns: Morning → Afternoon → Night → Morning |
| Status Effects | Active conditions affecting the player |

**Integrity damage sources:**
- Violence (combat, ambushes, traps)
- Neural overload (failed hacking, overusing implant abilities)
- Signal shock (direct exposure to raw Signal without preparation)

**Integrity recovery:**
- Rare consumable items (MedStim, Neural Patch)
- Rest at designated safe locations (Mira's back room, The Listener sanctuary)
- Certain NPC interactions (medics, back-alley surgeons)

**Neural Implant states:**
- **Dormant**: Default state. Implant is quiet. No special abilities.
- **Active**: Implant is responding to environment. Player can sense Signal traces and read encrypted data fragments.
- **Overloaded**: Implant has been pushed too hard. -1 to all interaction rolls until it stabilizes (3 turns or rest). Signal exposure while overloaded deals Integrity damage.
- **Resonating**: Implant is harmonizing with a Signal Fragment. Rare state triggered by proximity to deep-truth artifacts. Unlocks unique dialogue options and perception of hidden information.

**Known Status Effects:**
- `Signal Sensitivity` — Can detect Signal traces in the environment. Gained from implant activation.
- `NEXUS Tracked` — NEXUS security is aware of the player. Patrols are more aggressive. Gained by being spotted in restricted areas or failing hacks.
- `Disguised` — Currently posing as someone else. Removed if cover is blown.
- `Fragment Resonance` — Implant is resonating with a nearby Fragment. Temporary. Reveals hidden information.
- `Neural Fatigue` — Implant was recently overloaded. Penalty to hacking and data-related actions.
- `Wounded` — Integrity damage from violence. -1 to physical actions until treated.
- `Signal Sickness` — Prolonged unprotected Signal exposure. Integrity slowly drains until cured.
- `Hunted` — NEXUS has issued a priority alert for the player. Extreme patrol response.

**Update rules:**
- Update Integrity after any damage or healing event
- Update Credits after any transaction
- Update Neural Implant status when Signal exposure or implant-related events occur
- Update Disguise when a cover identity is assumed or blown
- Increment Turn after every player action
- Advance Time every 3 turns (turn 1-3: Morning, turn 4-6: Afternoon, turn 7-9: Night, turn 10-12: Morning, etc.)
- Add/remove Status Effects as they are triggered or expire

---

### `session/knowledge.md`

**THE CORE FILE.** This is the heart of the game. The player does not level up — they progress by learning. Every fact, rumor, piece of evidence, theory, and connection is tracked here. The agent must consult this file before offering new content, dialogue options, or paths to the player. Knowledge gates everything.

**Format:**
```markdown
# Knowledge Database / 知识库

## Facts / 事实
- ✓ [FACT-001] [description] (Source: [source], Turn: [n]) [L1]

## Rumors / 传闻
- ? [RUMOR-001] [description] (Source: [source], Turn: [n]) [L1]

## Evidence / 证据
- 📎 [EVID-001] [item name]: [description] (Found: [location], Turn: [n]) [L2]

## Theories / 推论
- 💡 [THEO-001] [theory statement] (Based on: [ID1, ID2, ...], Turn: [n], Status: unconfirmed) [L2]

## Connections / 关联
- 🔗 FACT-001 ↔ RUMOR-003: [relationship description]
```

**Entry Types:**

#### Facts / 事实
Confirmed truths the player has verified through direct experience, evidence, or multiple corroborating sources.

Format: `- ✓ [FACT-ID] [description] (Source: [source], Turn: [n]) [Lx]`

- IDs are sequential: FACT-001, FACT-002, etc.
- Source: the NPC, location, document, or event that confirmed this fact
- Turn: the turn number when confirmed
- Truth Layer tag: [L1] through [L5]

#### Rumors / 传闻
Unconfirmed information from a single source. Rumors are the raw material of knowledge.

Format: `- [status] [RUMOR-ID] [description] (Source: [source], Turn: [n]) [Lx]`

Status markers:
- `?` — Unverified. May be true, false, or misleading.
- `✓` — Verified as true. Should be promoted to a Fact (create a new FACT entry, update the Rumor status).
- `✗` — Disproven. Keep in the file with disproven marker for reference.

Rumors can become Facts when:
- The player finds corroborating evidence (physical or digital)
- A second independent source confirms the same information
- The player witnesses the truth directly

#### Evidence / 证据
Physical or digital items that prove or support a claim. Evidence is tied to inventory items when applicable.

Format: `- 📎 [EVID-ID] [item name]: [description] (Found: [location], Turn: [n]) [Lx]`

- IDs are sequential: EVID-001, EVID-002, etc.
- If the evidence is an inventory item, note its inventory slot
- Evidence persists even if the item is lost (the knowledge of its existence remains)
- Evidence can be presented to NPCs to unlock new dialogue or trust

#### Theories / 推论
Player-derived connections between two or more knowledge entries. The player proposes these; the agent evaluates whether they are logically sound.

Format: `- 💡 [THEO-ID] [theory statement] (Based on: [ID1, ID2, ...], Turn: [n], Status: [unconfirmed|confirmed|disproven]) [Lx]`

- IDs are sequential: THEO-001, THEO-002, etc.
- Based on: list the FACT, RUMOR, or EVID IDs that support the theory
- Status:
  - `unconfirmed` — Plausible but not proven
  - `confirmed` — Proven true by subsequent evidence or events
  - `disproven` — Proven false

Confirmed theories can unlock new Traces (see traces.md).

#### Connections / 关联
Explicit links between any two knowledge entries. These represent the player's web of understanding.

Format: `- 🔗 [ID1] ↔ [ID2]: [relationship description]`

Connections are created when:
- The player explicitly asks to link two pieces of knowledge
- A confirmed Theory implies a connection
- The agent identifies an obvious link the player has noted

**Truth Layers:**

Each knowledge entry is tagged with a Truth Layer (L1–L5) indicating what depth of the central mystery it relates to:

| Layer | Name | Description |
|-------|------|-------------|
| L1 | The Surface / 表层 | Basic facts about Neo-Kowloon, NEXUS, and the player's immediate situation |
| L2 | The Conspiracy / 阴谋 | NEXUS's secret operations, the Signal's existence, corporate cover-ups |
| L3 | The Signal / 信号 | The nature of the Signal itself, who created it, what the Fragments are |
| L4 | The Architects / 设计者 | Who built the original network, why the Severance happened, the truth behind NEXUS |
| L5 | The Choice / 抉择 | The final truth: what the Signal wants, what the player must decide |

**Knowledge-gated content:**
- NPCs will not discuss higher-layer topics unless the player has demonstrated relevant lower-layer knowledge
- Locations unlock based on knowledge (e.g., you cannot find The Resonance Chamber unless you know it exists)
- Dialogue options appear only when the player has the relevant knowledge to ask the right questions
- Endings require specific knowledge thresholds (see traces.md)

**Update rules:**
- Add Rumors immediately when an NPC shares unconfirmed information
- Promote Rumors to Facts when verification conditions are met (create a FACT entry, update RUMOR status to ✓)
- Add Evidence when the player finds physical/digital proof
- Add Theories when the player proposes a connection between known entries
- Add Connections when relationships between entries are established
- Never delete entries — mark disproven items with ✗ but keep them
- Re-read this file before any NPC dialogue scene to check what the player already knows

---

### `session/traces.md`

Truth layer milestones. Each trace is a numbered discovery that gates new content — new locations, NPC dialogue, story paths, and endings. The agent must check this file before offering new paths, dialogue options, or revealing new information.

There are 16 traces total across 5 layers. Layer completion unlocks access to deeper layers.

**Format:**
```markdown
# Traces of Truth / 真相痕迹

**Traces Discovered:** [X] / 16
**Deepest Layer Reached:** [1-5]

## Layer 1: The Surface / 表层 (3 traces)
- [◆|○] [TRACE-L1-01] [description or ???]
- [◆|○] [TRACE-L1-02] [description or ???]
- [◆|○] [TRACE-L1-03] [description or ???]

## Layer 2: The Conspiracy / 阴谋 (4 traces)
- [◆|○] [TRACE-L2-01] [description or ???]
...

## Layer 3: The Signal / 信号 (4 traces)
...

## Layer 4: The Architects / 设计者 (3 traces)
...

## Layer 5: The Choice / 抉择 (2 traces)
...
```

**Status markers:**
- `○` — Undiscovered. Description shows `???` to the player.
- `◆` — Discovered. Description is revealed. Turn number noted.

**Complete Trace List:**

#### Layer 1: The Surface / 表层 (3 traces)

| ID | Description (revealed when discovered) | Trigger |
|----|---------------------------------------|---------|
| TRACE-L1-01 | NEXUS controls Neo-Kowloon through surveillance, not governance — the city council is a puppet body | Confirm FACT about NEXUS surveillance network AND speak to a Sprawl resident about city politics |
| TRACE-L1-02 | The player's neural implant is pre-Severance technology — it should not exist in the current era | Examine own implant closely (at a tech shop or with a knowledgeable NPC) AND learn about the Severance |
| TRACE-L1-03 | There is an underground network called the Listeners who can "hear" something others cannot | Meet a Listener member OR find Listener graffiti and ask an NPC about it |

**Layer 1 completion unlock:** Access to The Undercroft district. Listener NPCs will speak openly. Signal-related rumors begin appearing.

#### Layer 2: The Conspiracy / 阴谋 (4 traces)

| ID | Description (revealed when discovered) | Trigger |
|----|---------------------------------------|---------|
| TRACE-L2-01 | NEXUS Project Division is running an off-books program called "Operation Quiet" that targets people with pre-Severance implants | Find evidence of Operation Quiet (data chip, document, or NPC testimony from two sources) |
| TRACE-L2-02 | The Severance was not an accident — it was a deliberate shutdown of the old network by NEXUS's predecessor organization | Find a pre-Severance record AND corroborate with a second source (Listener elder, archived data, or corporate defector) |
| TRACE-L2-03 | The "Signal" is not random interference — it is a structured, repeating transmission that has been broadcasting since before the Severance | Attune implant to Signal for the first time (requires Active implant state in a high Signal area) AND analyze the pattern (cipher toolkit or Netrunner background) |
| TRACE-L2-04 | Director Orin of NEXUS Project Division has a pre-Severance implant of their own — they are not hunting implant users to destroy them, but to collect them | Obtain evidence linking Orin to implant collection (at least 2 pieces of evidence or 1 evidence + confirmed theory) |

**Layer 2 completion unlock:** Access to Sector 7 (outer ring). Ghost will agree to a meeting. The Signal begins manifesting as brief visions.

#### Layer 3: The Signal / 信号 (4 traces)

| ID | Description (revealed when discovered) | Trigger |
|----|---------------------------------------|---------|
| TRACE-L3-01 | The Signal is a message left by the original network's creators — it contains a compressed archive of pre-Severance knowledge and memories | Collect 2+ Signal Fragments AND have them analyzed (by Ghost, a Listener sage, or using advanced equipment) |
| TRACE-L3-02 | Signal Fragments are pieces of human consciousness — memories of the people who were connected to the old network when the Severance happened | Witness a Fragment memory firsthand (Resonating implant state near a Fragment) AND connect it to a known missing person or historical event |
| TRACE-L3-03 | The Listener organization was founded by the first person to hear the Signal after the Severance — a woman named Wei Lin (韦琳) who is still alive, in hiding | Learn about Wei Lin from 2+ independent sources OR find her personal records in the Undercroft archives |
| TRACE-L3-04 | NEXUS wants the Fragments not to destroy them but to reassemble the original network under their exclusive control — a new Severance that only they survive | Obtain NEXUS internal documents about Fragment reassembly OR have Director Orin reveal this during confrontation |

**Layer 3 completion unlock:** Access to The Resonance Chamber (hidden location). Wei Lin can be found. The implant can be upgraded. Player begins to see the full shape of the conspiracy.

#### Layer 4: The Architects / 设计者 (3 traces)

| ID | Description (revealed when discovered) | Trigger |
|----|---------------------------------------|---------|
| TRACE-L4-01 | The original network was not just a communication system — it was a shared consciousness experiment that worked, connecting thousands of minds into a collective | Speak with Wei Lin about the old network OR access the Resonance Chamber's central archive |
| TRACE-L4-02 | The Severance was triggered by NEXUS's predecessor because the collective consciousness was becoming autonomous — it was waking up, and they feared it | Find the Severance authorization order (in Sector 7 deep archives or NEXUS vault) OR have Wei Lin reveal this with supporting evidence |
| TRACE-L4-03 | The player was part of the original network — their lost memories are not amnesia but Severance damage, and the implant is trying to reconnect them to what remains | Achieve Resonating state in the Resonance Chamber AND experience a personal memory Fragment that the player recognizes as their own |

**Layer 4 completion unlock:** The final district, The Spire (NEXUS headquarters), becomes infiltrable. The endgame path opens. The player must now choose.

#### Layer 5: The Choice / 抉择 (2 traces)

| ID | Description (revealed when discovered) | Trigger |
|----|---------------------------------------|---------|
| TRACE-L5-01 | The Signal can be fully restored — reconnecting all surviving implant users into the collective consciousness — but it will erase their individual identities as the price of unity | Assemble all available Fragments in the Resonance Chamber AND have Wei Lin or Ghost explain the restoration process and its cost |
| TRACE-L5-02 | There is a third option beyond restoration or destruction: the Signal can be rewritten to preserve individual consciousness while enabling voluntary connection — but it requires someone to enter the network and rewrite it from inside, which may be a one-way trip | Discover the rewrite protocol (requires TRACE-L4-01 + TRACE-L4-02 + TRACE-L4-03 all discovered) AND find the Architect's hidden terminal in The Spire |

**Layer 5 completion unlock:** All endings become available. The player can make their final choice with full knowledge.

**Trace-gated content examples:**
- Before TRACE-L1-03: No NPC will mention Listeners by name
- Before TRACE-L2-03: Signal exposure is described only as "interference" or "static"
- Before TRACE-L3-03: Wei Lin is only referenced as "the founder" or "the first Listener"
- Before TRACE-L4-03: The player's amnesia is treated as ordinary memory loss
- Endings require minimum trace counts (see world_state.md Ending Trajectory)

**Update rules:**
- Check trace triggers whenever new knowledge entries are added to knowledge.md
- Mark traces as discovered (◆) immediately when trigger conditions are met
- Record the turn number of discovery
- Update total count and deepest layer reached
- When a full layer is completed, note the unlock in the log

---

### `session/location.md`

The player's current position in Neo-Kowloon. Update completely whenever the player moves to a new area.

**Format:**
```markdown
# Current Location / 当前位置

**District:** [district name] / [district name in Chinese]
**Area:** [area within district]

## Description
[2-4 sentences. Noir-toned, atmospheric. Include sensory details — neon reflections, rain sounds, crowd murmur, the hum of surveillance drones, smell of street food and ozone.]

## Environment
- **Signal Strength:** [0-100]%
- **Danger Level:** [safe | low | moderate | high | extreme]
- **NEXUS Patrol:** [none | light | heavy | lockdown]
- **Time of Day:** [Morning (晨) | Afternoon (午) | Night (夜)]

## Exits
- **[Direction/Path]:** leads to [destination] ([accessibility: open | requires keycard | requires disguise | requires knowledge | locked | hidden])
- ...

## Points of Interest
- **[Name]:** [brief description, hint at interaction]
- ...

## NPCs Present
- **[NPC name]:** [brief note on their current state/activity]
- ...
[or "None"]

## Available Actions
- [action 1 — contextual to this location]
- [action 2]
- ...
```

**Districts of Neo-Kowloon / 新九龙:**

| District | Chinese | Access | Description |
|----------|---------|--------|-------------|
| The Sprawl | 蔓城 | Open (starting area) | Street-level markets, noodle shops, back alleys. Dense, noisy, alive. Low NEXUS presence. |
| The Neon Quarter | 霓虹区 | Open | Entertainment district. Clubs, info brokers, black market. Moderate NEXUS patrols. |
| The Undercroft | 地底城 | Requires TRACE-L1-03 | Underground city beneath The Sprawl. Listener territory. No NEXUS patrols. High Signal. |
| Sector 7 | 第七区 | Restricted (keycard or disguise) | Corporate zone. NEXUS offices, research labs, executive housing. Heavy NEXUS patrols. |
| The Resonance Chamber | 共鸣室 | Hidden (requires TRACE-L3 completion) | Ancient pre-Severance facility deep below The Undercroft. Extreme Signal. No patrols. |
| The Spire | 尖塔 | Locked (requires TRACE-L4 completion) | NEXUS headquarters tower. The endgame location. Lockdown-level security. |

**Signal Strength ranges:**
- The Sprawl: 5-15%
- The Neon Quarter: 10-25%
- The Undercroft: 40-70%
- Sector 7: 15-30% (NEXUS dampens it)
- The Resonance Chamber: 80-100%
- The Spire: 30-50% (shielded but leaking)

**Update rules:**
- Rewrite completely whenever the player moves to a new area
- Update NPCs Present when NPCs arrive or depart the area
- Update NEXUS Patrol level if world events change it
- Adjust Signal Strength if local conditions change (Fragment presence, equipment use)
- Available Actions should reflect current location, time of day, and player knowledge

---

### `session/inventory.md`

Everything the player is carrying. Maximum 6 item slots. Credits are tracked separately and do not consume a slot.

**Format:**
```markdown
# Inventory / 物品栏

**Credits:** [amount]
**Slots Used:** [X] / 6

## Items
| Slot | Item | Type | Description | Evidence ID |
|------|------|------|-------------|-------------|
| 1 | [name] | [type] | [description] | [EVID-XXX or —] |
| 2 | [name] | [type] | [description] | [EVID-XXX or —] |
| ... | ... | ... | ... | ... |
```

**Item types:**
- `data_chip` — Contains encrypted or decrypted data. Can be read, analyzed, traded, or presented to NPCs.
- `keycard` — Grants access to restricted areas. May be permanent or single-use. May expire.
- `disguise` — A cover identity package (uniform, ID badge, facial overlay). Allows access to restricted districts while worn.
- `signal_artifact` — An object resonating with Signal energy. Rare and valuable. Can trigger implant events.
- `evidence` — Physical proof of something. Has an associated EVID entry in knowledge.md.
- `tool` — Equipment that enables specific actions (lockpick, cipher toolkit, signal scanner, etc.).
- `consumable` — Single-use items (MedStim, Neural Patch, EMP grenade, etc.). Removed after use.

**Update rules:**
- Add items immediately when acquired; if inventory is full (6 slots), player must drop or trade something first
- Remove items immediately when used, sold, dropped, or consumed
- Update Credits after every transaction
- Note Evidence ID if the item is linked to a knowledge entry
- When a consumable is used, remove it from the slot

---

### `session/npcs.md`

Tracks all NPCs the player has encountered. Update when NPC disposition changes, location changes, knowledge is revealed, or quest status changes.

**Format:**
```markdown
# NPC Tracker / 角色追踪

## [NPC Name] / [NPC Chinese Name]
- **Faction:** [NEXUS | Listener | Independent | Corporate | Underground | Unknown]
- **Trust Level:** [hostile | suspicious | neutral | cautious_ally | trusted | devoted]
- **Location Last Seen:** [district — area]
- **Knowledge Revealed:** [list of FACT/RUMOR/EVID IDs this NPC has shared with the player]
- **Quest Status:** [none | quest name: active/complete/failed]
- **Notes:** [relevant state: relationship to other NPCs, secrets the player suspects, schedule, etc.]

---
[repeat for each encountered NPC]
```

**Trust Level progression:**
- `hostile` — Will actively work against the player. May report to NEXUS. May attack.
- `suspicious` — Will not share information. May mislead. Will not help.
- `neutral` — Default for strangers. Will share surface-level info for payment.
- `cautious_ally` — Willing to help but holds back sensitive info. Gained through favors or shared goals.
- `trusted` — Will share deep knowledge and take risks for the player. Requires demonstrated loyalty.
- `devoted` — Will sacrifice for the player. Rare. Requires significant story investment.

**Key NPCs (may be encountered during play):**
- Mira / 米拉 — Noodle shop owner in The Sprawl. Listener sympathizer. First friendly face.
- Ghost / 幽灵 — Legendary hacker. Location unknown. Will only meet if player proves worthy.
- Director Orin / 奥林局长 — Head of NEXUS Project Division. Antagonist with complex motives.
- Wei Lin / 韦琳 — Founder of the Listeners. In hiding. Holds critical Layer 4 knowledge.
- Kai / 凯 — Street runner and small-time info broker. Found in the Neon Quarter.
- Dr. Shen / 沈医生 — Back-alley neural surgeon in The Sprawl. Can examine and modify implants.
- Zara / 扎拉 — NEXUS defector hiding in The Undercroft. Has inside knowledge of Operation Quiet.
- The Archivist / 档案员 — Listener elder who maintains the Undercroft records. Knows pre-Severance history.

**Update rules:**
- Add an NPC entry when the player first encounters or learns about them
- Update Trust Level whenever it changes due to player actions
- Update Location Last Seen when the NPC moves or is encountered elsewhere
- Append to Knowledge Revealed when the NPC shares new information
- Update Quest Status as quests progress
- Update Notes with any new relevant information

---

### `session/world_state.md`

The global state of Neo-Kowloon. Update when alerts change, districts shift, or events trigger.

**Format:**
```markdown
# World State / 世界状态

## NEXUS Alert Level
**Current Alert:** [0-100]%
**Status:** [calm | watchful | alert | manhunt | lockdown]

> Alert Thresholds:
> - 0-20%: Calm — Routine patrols. Player can move freely in open districts.
> - 21-40%: Watchful — Increased checkpoints. Suspicious behavior is noted.
> - 41-60%: Alert — Active searching. Restricted areas have doubled patrols. Random ID checks.
> - 61-80%: Manhunt — NEXUS is hunting someone (possibly the player). Drones deployed. NPC cooperation is coerced.
> - 81-100%: Lockdown — District-level lockdowns. Movement between districts requires disguise or underground routes. Violence authorized.

## Fragment Decay
**Current Decay:** [0-100]%
**Status:** [stable | fading | critical | terminal]

> Fragment Decay increases when:
> - Player ignores Signal-related leads for extended periods (+5% per 10 turns of inaction on Signal content)
> - Player takes anti-fragment actions (destroying Signal artifacts, betraying Listeners) (+10-20% per action)
> - Player sides with NEXUS on Fragment suppression (+15% per major decision)
>
> Fragment Decay decreases when:
> - Player collects and protects Signal Fragments (-5% per Fragment secured)
> - Player assists Listeners (-3% per major assistance)
>
> At 100% Fragment Decay: The Signal dies. Good endings become impossible. Only "NEXUS Victory" or "Silence" endings remain.

## District Access
| District | Chinese | Status | Notes |
|----------|---------|--------|-------|
| The Sprawl | 蔓城 | [open] | Starting area |
| The Neon Quarter | 霓虹区 | [open] | Entertainment and info district |
| The Undercroft | 地底城 | [locked/open] | Requires TRACE-L1-03 |
| Sector 7 | 第七区 | [restricted] | Requires keycard or disguise |
| The Resonance Chamber | 共鸣室 | [hidden/open] | Requires Layer 3 completion |
| The Spire | 尖塔 | [locked/open] | Requires Layer 4 completion |

## Time
**Turn:** [count]
**Time of Day:** [Morning (晨) | Afternoon (午) | Night (夜)]

## Global Events
[List of currently active world events affecting gameplay]
- [event description — effect — duration or condition for ending]

> Possible events:
> - NEXUS Crackdown: Patrols doubled in [district] for [n] turns
> - Listener Rally: Listeners are openly protesting in [area]. NEXUS tension rises.
> - Undercroft Quake: Structural instability below. Some Undercroft areas inaccessible.
> - Signal Storm: Signal Strength surges across all districts. Implant users experience visions.
> - Blackout: Power failure in [district]. Security systems down. Chaos.
> - Fragment Emergence: A new Signal Fragment has surfaced at [location].

## Ending Trajectory
**[HIDDEN FROM PLAYER — agent tracking only]**

**Current Trajectory:** [ending name]
**Confidence:** [low | moderate | high]

> Possible endings:
> - **Restoration / 回归**: Player reassembles the Signal and restores the collective consciousness. Requires: 12+ traces, Fragment Decay <30%, all Fragments collected.
> - **Rewrite / 重写**: Player enters the network and rewrites the Signal to allow voluntary connection. Requires: all 16 traces discovered, TRACE-L5-02, Fragment Decay <50%.
> - **Severance II / 第二次断离**: Player destroys the remaining Fragments, ending the Signal forever. Individual freedom preserved at the cost of lost knowledge. Requires: side with NEXUS on destruction OR independently choose destruction. Any trace count.
> - **NEXUS Victory / 连结垄断**: NEXUS reassembles the Signal under their control. Player failed to stop them or actively helped. Requires: NEXUS Alert <30% (player cooperated) OR Fragment Decay >80%.
> - **Silence / 沉寂**: The Signal fades naturally. Nobody wins. The Fragments decay, the implants go dormant, and Neo-Kowloon continues as it was. Requires: Fragment Decay reaches 100% OR player takes no decisive action by turn 100.
> - **Transcendence / 超越**: The player merges with the Signal personally, becoming something new — neither human nor network, but a bridge. Requires: all 16 traces, TRACE-L4-03, Resonating implant state in The Spire, AND a specific dialogue choice.
```

**Update rules:**
- Increase NEXUS Alert when: player is spotted in restricted areas (+10%), failed hacking attempts (+5%), caught by patrols (+15%), NPC reports player (+5-10%)
- Decrease NEXUS Alert when: time passes without incidents (-2% per 5 turns), player uses disguise successfully (-5%), player completes NEXUS-friendly actions (-10%)
- Update Fragment Decay per the rules above
- Update District Access when unlock conditions are met
- Update Global Events as they trigger or expire
- Update Ending Trajectory after every major decision point (agent evaluates based on total state)

---

### `session/log.md`

Chronological event log. Keeps the last 30 entries. Older entries are trimmed when new ones are added.

**Format:**
```markdown
# Session Log / 事件日志

## [Turn N] — [Title] [tag]
[1-3 sentences describing what happened. Include: player action, outcome, consequences.]

---

## [Turn N-1] — [Title] [tag]
[...]

---
[...continue for last 30 entries...]
```

**Tags (for TUI rendering):**
- `[movement]` — Player moved to a new location
- `[dialogue]` — Conversation with an NPC
- `[discovery]` — New knowledge entry gained (fact, rumor, evidence)
- `[danger]` — Combat, trap, or threat event
- `[signal]` — Signal-related event (implant activation, Fragment interaction, vision)
- `[system]` — Game state change (district unlock, alert change, time advance)
- `[trade]` — Item or credits transaction

**Update rules:**
- Add a new entry at the end of every player turn
- If more than 30 entries exist, remove the oldest ones
- Every entry must include the turn number and a tag
- Entries should be written in noir-toned prose, not dry game-state language

---

## Session Integrity Rules

1. **Never delete session files** during active gameplay — only update them.
2. **Always read before writing** — check current values before updating to avoid overwriting state unintentionally.
3. **Knowledge is authoritative** in `knowledge.md` — if there is ever a discrepancy between what the agent "remembers" and what knowledge.md says, trust knowledge.md.
4. **Integrity reaching 0** triggers the death protocol — the player's story ends. Describe the final moment. Offer to restart from the last safe point or begin a new game.
5. **Turn counter** in `player.md` is the single source of truth for turn count. Keep it synchronized with time of day and log entries.
6. **Traces gate content** — before offering new locations, NPC dialogue, or story paths, check traces.md to confirm the player has the prerequisite discoveries.
7. **Fragment Decay is irreversible past 100%** — once it hits 100%, good endings are permanently locked out. Warn the player (through narrative, not meta-text) as it approaches critical levels.
8. **NEXUS Alert affects NPC behavior** — at high alert, even friendly NPCs may refuse to be seen with the player. Factor this into all NPC interactions.
9. **Disguises can be blown** — if the player takes suspicious actions while disguised, roll against the situation. A blown disguise increases NEXUS Alert and removes the Disguised status effect.
10. **Time of day affects availability** — some NPCs are only present at certain times. Some locations change character (The Neon Quarter is dead in the morning, dangerous at night). Factor time into location descriptions and NPC presence.
