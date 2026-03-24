# The Sundering of Aethermoor

*A dark fantasy RPG — play as a Riftwalker in a world being torn apart by the Void.*

## Background

The world of Aethermoor was once whole — a single continent bound by the Worldstone, a crystalline spire of pure creation magic. For ten thousand years, the Five Peoples thrived under its light. Then Malachar, a god-touched mage consumed by nihilistic philosophy, drove a shard of anti-creation into the Worldstone's heart. The explosion shattered the continent into five dying realms, each drifting apart, each slowly being consumed by the Void — the cold nothingness beyond all existence.

You are a **Riftwalker**, one of the rare few who can tear open passages between the fractured realms. The Void creeps closer with every passing day, erasing reality at the edges. Somewhere in the ruins of the old world lie the five Worldstone Shards — fragments of the original spire that, if reunited, might heal the Sundering. Or they might finish what Malachar started.

Choose your path. Gather companions. Face the Void. The world doesn't have long.

## How to Play

### With the TUI

The game includes an interactive terminal UI that lets you play directly in your terminal. The TUI provides a split-screen experience: an embedded terminal on one side for talking to the AI agent, and a tabbed dashboard on the other showing your character stats, inventory, location, quests, and more.

```bash
cd "Examples/The Sundering of Aethermoor/"
.venv/bin/python tui/tui_viewer.py . --terminal true
```

Press `r` to refresh the dashboard after each turn. Use the tabs to switch between panels (character, inventory, map, quests, log, etc.).

### With an AI Agent

You can also play entirely through conversation with any compatible AI coding agent:

1. Open this folder in your agent of choice ([Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://github.com/openai/codex), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [OpenCode](https://github.com/opencode-ai/opencode), or any agent that can read and write files).
2. Tell the agent: **"Read `NEW GAME.md` and follow the instructions."**
3. Play by describing your actions in natural language. There are no menus — say whatever you want to do, and the agent will interpret it, roll the dice, and tell you what happens.

## Game Lifecycle

| Command | Description |
|---------|-------------|
| `NEW GAME.md` | Start a fresh playthrough — create a character and begin your journey |
| `RESUME.md` | Resume the current in-progress session (quickest way back in) |
| `LOAD GAME.md` | Load a previously saved game from `saves/` |
| `SAVE GAME.md` | Save your current progress to `saves/` |

## Game Features

- **Three Riftwalker subclasses** — Voidblade (melee combat), Riftweaver (magic), or Shadowseer (stealth & divination)
- **D20-based combat and skill checks** — powered by a real dice roller, with crits, fumbles, and modifiers
- **Companion system** — recruit NPCs to fight alongside you, each with their own abilities and storylines
- **Void Corruption** — a global timer that rises every turn, warping the world and raising stakes as the game progresses
- **Five distinct realms** — Emberveil, Frosthollow, Thornveil, Skyreach, and the Shattered Core, each with unique environments and dangers
- **Malachar's Visions** — cryptic, unsettling visions that hint at the truth behind the Sundering
- **Open-ended gameplay** — no fixed dialogue trees or predetermined paths; your choices shape the story

## Settings

Customize your experience by editing `settings/custom.json`:

- **Difficulty** — Easy, Normal, Hard, or Nightmare (with permadeath)
- **Narrative style** — Terse, Normal, or Verbose prose
- **Tone** — Lighthearted, Balanced, or Dark Epic
- **Gameplay toggles** — Companion permadeath, auto-save frequency, inventory limits, and more

---

*The Void presses in. The Worldstone Shards call out. Will you answer?*
