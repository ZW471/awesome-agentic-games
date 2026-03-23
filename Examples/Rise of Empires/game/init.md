# Initialization Procedure / 初始化流程

**Called by the agent only** — never directly by the player.

---

## Step 1: Language Selection

If not already determined, ask the player:
> Choose your language / 选择你的语言: **English** or **中文**

Store the choice in `session/civilization.md` as `Language: en` or `Language: cn`.
All subsequent text must use the chosen language.

---

## Step 2: Civilization Creation

Present the player with a choice of 6 civilizations:

| # | Civilization | Bonus | Playstyle |
|---|-------------|-------|-----------|
| 1 | **The Aurelian Empire / 奥瑞利安帝国** | +2 Gold per turn, +1 to diplomacy | Balanced, diplomatic |
| 2 | **The Stormforge Clans / 风暴锻造氏族** | +2 Military Strength, +1 combat rolls | Aggressive, military |
| 3 | **The Jade Lotus Dominion / 翡翠莲花王朝** | +2 Culture per turn, start with Writing | Cultural, wonder-focused |
| 4 | **The Cogwright Federation / 齿轮联邦** | +2 Science per turn, +1 free tech | Scientific, tech-focused |
| 5 | **The Verdant Concord / 翠绿协约** | +3 Food per turn, +1 population growth | Expansionist, growth |
| 6 | **The Obsidian Pact / 黑曜之盟** | +2 Production per turn, cheaper buildings | Builder, infrastructure |

After the player chooses, ask them to **name their civilization** (or keep the default name).

---

## Step 3: Leader Name

Ask the player to name their leader, or generate a thematic default.

---

## Step 4: Generate the World Map

Use `tools/dice.py` to generate the 5x5 territory grid:

1. Assign the player's starting territory at a random position.
2. For each of the 25 territories, roll for terrain type:
   - d6: 1=Plains, 2=Forest, 3=Mountain, 4=Desert, 5=Coast, 6=River
3. For each territory, roll for bonus resource:
   - d6: 1-2=None, 3=Iron, 4=Horses, 5=Gems, 6=Fertile Soil
4. Place 3-4 NPC civilizations based on difficulty setting (see settings), each on a random unoccupied territory (not adjacent to player start).
5. Mark only the player's starting territory and adjacent territories as "Explored". All others are "Unexplored".

Write the result to `session/map.md`.

---

## Step 5: Select Rival Civilizations

Based on difficulty setting, randomly select 3-4 civilizations from `game/npcs.md`.
Roll `tools/dice.py` to choose which ones. Initialize their disposition to 0 (Neutral).

Write to `session/diplomacy.md`.

---

## Step 6: Initialize Technology Tree

All civilizations start with these technologies:
- **Agriculture / 农业** — Enables farms, +1 Food
- **Pottery / 制陶** — Enables granary building

Full tech tree (organized by era):

### Era I — Ancient / 远古时代
| Tech | Cost | Requires | Effect |
|------|------|----------|--------|
| Animal Husbandry / 畜牧 | 10 | Agriculture | +1 Food, enables Horses resource |
| Mining / 采矿 | 10 | — | +1 Production, enables Iron resource |
| Writing / 文字 | 15 | Pottery | +1 Science, enables Library |
| Bronze Working / 青铜冶炼 | 15 | Mining | Enables Warriors → Swordsmen upgrade |
| Sailing / 航海 | 15 | — | Enables coast exploration, +1 Gold from coast |
| Masonry / 石工 | 10 | Mining | Enables Walls, +1 Production |

### Era II — Classical / 古典时代
| Tech | Cost | Requires | Effect |
|------|------|----------|--------|
| Iron Working / 铁器 | 25 | Bronze Working | Enables Swordsmen (3 str) |
| Mathematics / 数学 | 25 | Writing | +2 Science, enables Siege Engines |
| Philosophy / 哲学 | 25 | Writing | +2 Culture, enables Cultural Victory path |
| Currency / 货币 | 20 | Writing | +2 Gold, enables Market |
| Construction / 建筑学 | 25 | Masonry | Enables Aqueduct (+2 population cap) |
| Horseback Riding / 骑术 | 20 | Animal Husbandry | Enables Cavalry (4 str) |

### Era III — Medieval / 中世纪
| Tech | Cost | Requires | Effect |
|------|------|----------|--------|
| Education / 教育 | 40 | Philosophy, Mathematics | +3 Science, enables University |
| Theology / 神学 | 35 | Philosophy | +3 Culture, enables Temple |
| Engineering / 工程学 | 40 | Construction, Mathematics | Enables advanced buildings, +2 Production |
| Guilds / 行会 | 35 | Currency | +3 Gold, enables Bank |
| Chivalry / 骑士精神 | 40 | Horseback Riding, Iron Working | Enables Knights (5 str) |
| Gunpowder / 火药 | 50 | Engineering | Enables Musketeers (6 str), Cannons |

### Era IV — Renaissance / 文艺复兴
| Tech | Cost | Requires | Effect |
|------|------|----------|--------|
| Printing Press / 印刷术 | 55 | Education | +4 Science, +2 Culture |
| Navigation / 导航术 | 50 | Sailing, Education | Enables deep ocean exploration |
| Banking / 银行业 | 50 | Guilds, Education | +4 Gold, enables Stock Exchange |
| Astronomy / 天文学 | 60 | Mathematics, Navigation | +3 Science, Scientific Victory prereq |
| Metallurgy / 冶金术 | 55 | Gunpowder | Enables Cannons (5+siege str) |
| Diplomatic Service / 外交 | 50 | Printing Press | +2 to all diplomacy rolls |

### Era V — Modern / 近现代
| Tech | Cost | Requires | Effect |
|------|------|----------|--------|
| Industrialization / 工业化 | 70 | Banking, Metallurgy | +5 Production, enables Factory |
| Scientific Method / 科学方法 | 70 | Astronomy | +5 Science, enables Research Lab |
| Ideology / 意识形态 | 65 | Printing Press | +4 Culture, enables ideological policies |
| Railroad / 铁路 | 60 | Industrialization | +3 Gold, +2 Production, fast unit movement |
| Advanced Ballistics / 先进弹道学 | 75 | Metallurgy, Scientific Method | Enables Artillery, Tanks |
| Space Program / 太空计划 | 100 | Scientific Method, Industrialization | Scientific Victory condition |

Write to `session/technology.md`.

---

## Step 7: Initialize Military

The player starts with:
- 1x Warriors (Strength 2, located at starting territory)
- 1x Archers (Strength 1+range, located at starting territory)

Write to `session/military.md`.

---

## Step 8: Initialize Resources

Starting resources based on civilization choice:
- **Base**: Gold 10, Food 10, Production 5, Science 3, Culture 2
- Apply civilization bonuses to per-turn income.
- Population: 3
- Happiness: 7/10

Write to `session/civilization.md`.

---

## Step 9: Create Game Log

Initialize `session/log.md` with:
```
# Game Log

## Turn 1 — Ancient Era
- A new civilization rises: <civilization_name>, led by <leader_name>.
- Capital established at <starting_territory>.
```

---

## Step 10: Present the Opening

Display to the player:

1. A narrative introduction (2-3 paragraphs, epic tone) describing the dawn of their civilization.
2. A summary dashboard showing:
   - Civilization name and leader
   - Starting territory and terrain
   - Resources and per-turn income
   - Known neighbors (if any are in explored range)
   - Available actions
3. Prompt for their first turn action.
