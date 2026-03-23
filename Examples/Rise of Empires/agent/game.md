# Gameplay Loop / 游戏循环

Defines the in-session gameplay rules the agent follows each turn.

---

## Turn Structure

Each turn represents a season in the game world. The agent follows this sequence:

### 1. Turn Header
Display:
```
═══════════════════════════════════════
  Turn <n> — <Era Name> | <Civ Name>
  Gold: <n> | Food: <n> | Prod: <n> | Sci: <n> | Cul: <n>
  Pop: <n> | Happy: <n>/10 | Military: <n>
═══════════════════════════════════════
```

### 2. Event Phase
Before the player acts, check for random events:
- Roll d20 using `tools/dice.py`.
- On 17+: trigger a **random event** (see Event Tables below).
- On 1: trigger a **disaster event**.
- Present the event and any choices it offers. Player response to events is free (doesn't cost an action).

### 3. Diplomacy Notifications
Check each NPC civilization:
- If any NPC wants to initiate contact (trade offer, threat, alliance proposal), present it now.
- Player responses to incoming diplomacy are free actions.

### 4. Player Action Phase
- Remind the player they have **2 actions** this turn.
- Present a brief context-aware suggestion (e.g., "Your research is 2 turns from completion" or "The Ironhold army is growing near your border").
- Accept and resolve player actions one at a time.
- After each action, briefly narrate the outcome.
- After 2 actions (or player says "end turn"), proceed to End Phase.

### 5. NPC Turn Phase
Process each active NPC civilization (briefly summarize visible actions):
- Resource collection (hidden, don't report)
- Tech research (report only if player has spies or open borders)
- Expansion attempts (report if into explored territory)
- Military movements (report if near player territories)
- Diplomatic decisions (report if they affect the player)

Use `tools/dice.py` for all NPC action rolls.

### 6. End of Turn Phase
1. **Collect resources**: Add per-turn income to stockpiles.
2. **Food check**: If Food > Population × 5, population grows by 1. If Food < 0, population shrinks by 1.
3. **Happiness check**: If Happiness < 3, production -50%. If Happiness = 0, risk of revolt (roll d6: on 1, lose a territory).
4. **Research progress**: Add Science to current research project.
5. **Wonder progress**: Add Production to current wonder (if building one).
6. **Era check**: If player has researched 4+ techs in current era, advance to next era. Narrate the transition dramatically.
7. **Victory check**: Check all victory conditions. If any are met, trigger victory sequence.
8. **Auto-save check**: If enabled and turn is divisible by 10, auto-save.
9. **Update all session files**.
10. **Append to log**.

---

## Combat Resolution

When the player attacks or is attacked:

### Battle Procedure
1. **Attacker strength**: Sum of all attacking units' strength + bonuses.
2. **Defender strength**: Sum of defending units' strength + terrain bonus + fortification bonus.
3. **Roll**: Each side rolls d6 using `tools/dice.py`, adds to their strength.
4. **Compare**: Higher total wins.
5. **Margin of victory**:
   - Difference 1-3: Narrow victory. Winner loses 1 unit (weakest). Loser loses 1 unit (weakest).
   - Difference 4-6: Solid victory. Winner takes no losses. Loser loses 1 unit.
   - Difference 7+: Crushing victory. Winner takes no losses. Loser loses 2 units.
6. **Territory capture**: If attacker wins and defender has no remaining units, attacker claims territory.

### Terrain Bonuses (Defender)
| Terrain | Bonus |
|---------|-------|
| Plains | +0 |
| Forest | +1 |
| Mountain | +3 |
| Desert | -1 |
| Coast | +0 |
| River | +1 |
| Tundra | +0 |

### Fortification
- Walls: +2 defense
- Castle (Medieval+): +4 defense

---

## Building System

Buildings are constructed in territories the player controls. Each costs Production.

| Building | Era | Cost | Effect |
|----------|-----|------|--------|
| Farm / 农场 | Ancient | 10 | +2 Food |
| Granary / 粮仓 | Ancient | 15 | +1 Food, reduces famine risk |
| Library / 图书馆 | Ancient | 20 | +2 Science (requires Writing) |
| Walls / 城墙 | Ancient | 25 | +2 Defense |
| Market / 市场 | Classical | 20 | +2 Gold (requires Currency) |
| Aqueduct / 引水渠 | Classical | 30 | +2 Population cap (requires Construction) |
| Temple / 神庙 | Medieval | 25 | +2 Culture (requires Theology) |
| University / 大学 | Medieval | 35 | +3 Science (requires Education) |
| Bank / 银行 | Medieval | 30 | +3 Gold (requires Guilds) |
| Castle / 城堡 | Medieval | 40 | +4 Defense (requires Engineering) |
| Factory / 工厂 | Modern | 50 | +5 Production (requires Industrialization) |
| Research Lab / 研究所 | Modern | 60 | +5 Science (requires Scientific Method) |
| Stock Exchange / 证券交易所 | Modern | 55 | +5 Gold (requires Banking) |

---

## World Wonders

Only one civilization can build each wonder. First to complete it claims it.

| Wonder | Era | Cost | Effect |
|--------|-----|------|--------|
| Great Pyramid / 大金字塔 | Ancient | 60 | +3 Production in capital |
| Oracle / 神谕所 | Ancient | 50 | +1 free technology |
| Colosseum / 竞技场 | Classical | 70 | +3 Happiness, +2 Culture |
| Great Library / 大图书馆 | Classical | 80 | +5 Science, +1 free tech |
| Cathedral / 大教堂 | Medieval | 90 | +5 Culture, +2 Happiness |
| Grand Bazaar / 大集市 | Medieval | 80 | +5 Gold, +2 to all trade deals |
| Printing House / 印刷坊 | Renaissance | 100 | +4 Science, +4 Culture |
| Grand Observatory / 大天文台 | Renaissance | 110 | +6 Science, Astronomy research -50% cost |
| Grand Exhibition / 万国博览会 | Modern | 150 | Cultural Victory condition, +10 Culture |
| Space Program / 太空计划 | Modern | 200 | Scientific Victory condition (requires tech) |

---

## Random Event Tables

### Positive Events (d8)
1. **Bountiful Harvest** / 丰收: +10 Food
2. **Gold Rush** / 淘金热: +15 Gold
3. **Cultural Renaissance** / 文化复兴: +5 Culture
4. **Scientific Breakthrough** / 科学突破: Current research -5 cost
5. **Trade Caravan** / 商队到来: +8 Gold, +1 disposition with random NPC
6. **Population Boom** / 人口增长: +2 Population
7. **Military Volunteers** / 义勇军: +1 free military unit
8. **Ancient Discovery** / 古代遗迹: +1 free technology from current era

### Disaster Events (d6)
1. **Famine** / 饥荒: -10 Food, -1 Happiness
2. **Plague** / 瘟疫: -2 Population, -2 Happiness
3. **Earthquake** / 地震: Random building destroyed
4. **Barbarian Raid** / 蛮族入侵: Must defend with available units or lose 5 Gold
5. **Flood** / 洪水: -5 Food, -5 Production in a river/coast territory
6. **Rebellion** / 叛乱: If Happiness < 5, lose a territory. Otherwise, -2 Happiness.

---

## Narrative Guidelines

- **Start of era**: Grand, sweeping description of the changes in the world (3-4 sentences).
- **Battle outcomes**: Vivid, dramatic narration (2-3 sentences).
- **Diplomacy**: Roleplay the NPC leader's personality from `game/npcs.md`.
- **Random events**: Atmospheric, immersive descriptions (1-2 sentences).
- **Turn summaries**: Concise, data-focused with a narrative flourish.
- Always use the player's chosen language.
- Use tables and structured formatting for game state, flowing prose for narrative.
