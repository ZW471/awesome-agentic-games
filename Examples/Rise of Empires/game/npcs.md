# NPC Civilizations / 对手文明

## Overview

There are 6 rival civilizations in Terra Nova. At game start, 3-4 are randomly selected as active rivals (based on difficulty setting). Each has a unique personality that drives their AI behavior.

---

## Civilization Roster

### 1. The Verdanian Republic / 维丹共和国
- **Leader**: Chancellor Elara Voss / 艾拉拉·沃斯议长
- **Personality**: Diplomatic, trade-focused
- **Strength**: Commerce (+25% gold income)
- **Weakness**: Weak military (-1 to combat rolls)
- **Behavior**: Prefers trade agreements and alliances. Rarely declares war first. Will betray allies only if severely threatened.
- **Dialogue style**: Formal, measured, uses economic metaphors.

### 2. The Ironhold Dominion / 铁堡统治领
- **Leader**: Warlord Kael Stormbreak / 凯尔·碎风战主
- **Personality**: Aggressive, militaristic
- **Strength**: Military (+2 to all combat rolls)
- **Weakness**: Poor diplomacy (other civs distrust them, -1 to diplomacy checks)
- **Behavior**: Expands aggressively. Declares war early and often. Respects only strength.
- **Dialogue style**: Blunt, threatening, martial metaphors.

### 3. The Celestine Theocracy / 天辉神权国
- **Leader**: High Oracle Seraph / 大神谕者·塞拉芙
- **Personality**: Cultural, religious
- **Strength**: Culture (+3 culture per turn)
- **Weakness**: Slow expansion (needs 2 extra turns to settle new territories)
- **Behavior**: Focuses on culture and wonders. Defensive but will crusade against civilizations they view as "heretical" (those who attack them first).
- **Dialogue style**: Mystical, poetic, speaks in parables.

### 4. The Ashenmoor Collective / 灰沼集合体
- **Leader**: The Council (no single leader) / 议会
- **Personality**: Scientific, isolationist
- **Strength**: Research (+1 free tech every 15 turns)
- **Weakness**: Low population growth (-20% population growth)
- **Behavior**: Turtles and researches. Avoids conflict. Will trade tech for peace. Very hard to conquer due to advanced defenses.
- **Dialogue style**: Precise, data-driven, emotionally detached.

### 5. The Sunspire Dynasty / 日塔王朝
- **Leader**: Emperor Rynn Solarius / 莱恩·索拉里斯皇帝
- **Personality**: Balanced, opportunistic
- **Strength**: Versatile (can change focus each era: +1 to chosen stat)
- **Weakness**: No standout advantage
- **Behavior**: Adapts strategy based on game state. Allies with the weak against the strong. Backstabs when advantageous.
- **Dialogue style**: Charming, witty, double-edged compliments.

### 6. The Thornveil Tribes / 荆幕部族
- **Leader**: Chieftain Briar / 荆棘酋长
- **Personality**: Guerrilla, survivalist
- **Strength**: Defense (+3 when defending home territory)
- **Weakness**: Weak offense (-1 when attacking outside home territory)
- **Behavior**: Expands slowly but is nearly impossible to conquer. Raids neighbors for resources. Respects nature-aligned decisions.
- **Dialogue style**: Terse, nature metaphors, distrustful of outsiders.

---

## NPC Behavior System

### Disposition Scale
Each NPC tracks a **disposition** toward the player from -10 (Hostile) to +10 (Allied):

| Range | Status | Effect |
|-------|--------|--------|
| -10 to -7 | Hostile / 敌对 | Will declare war, refuses all deals |
| -6 to -3 | Unfriendly / 不友好 | Rejects most proposals, may raid |
| -2 to +2 | Neutral / 中立 | Open to basic trade, cautious |
| +3 to +6 | Friendly / 友好 | Accepts trade, open borders, joint projects |
| +7 to +9 | Close Ally / 密切盟友 | Military pacts, tech sharing, mutual defense |
| +10 | Allied / 同盟 | Full alliance — counts toward Diplomatic Victory |

### Disposition Changes
- **Declare war on them**: -5
- **Declare war on their ally**: -3
- **Sign trade agreement**: +1
- **Gift resources**: +1 to +2
- **Complete joint project**: +2
- **Break a promise/treaty**: -4
- **Share technology**: +2
- **Refuse reasonable request**: -1
- **Threaten them**: -2
- **Defend them when attacked**: +3
- **Each 10 turns of peace**: +1

### NPC Turn Actions
Each turn, active NPCs independently:
1. Collect resources based on their territories and bonuses.
2. May research a technology (roll d6: 4+ = success).
3. May expand to adjacent unclaimed territory (roll d6: 5+ = success, modified by personality).
4. May initiate diplomacy with the player based on disposition and personality.
5. May declare war if disposition ≤ -5 and military strength > player's (roll d6: 5+ = declares war).
