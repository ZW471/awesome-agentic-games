# Agentic Game — TUI Viewer Template

This document specifies how to build a **Textual-based Terminal UI (TUI) viewer** for any agentic game that follows the structure defined in `game_template.md`. The TUI provides a persistent, tabbed dashboard that displays all session state at a glance and supports interactive features like dice rolling, instead of requiring the player to manually read individual `.md` files.

---

## When to Build a TUI

The TUI viewer is **optional**. The creating agent should ask the player during game setup whether they want one. Games work perfectly well without a TUI — the agent can present state inline during conversation. The TUI is most useful when:

- The game has complex, multi-file session state (5+ session files).
- The player wants a persistent overview while playing.
- The game includes stat bars, inventories, maps, or other data that benefits from visual formatting.

If the player declines, skip this entirely. The game still works.

---

## Architecture

```
<game_root>/
├── tui/
│   └── tui_viewer.py      # The TUI application (single file)
└── session/               # The TUI reads from here (same session/ the game engine writes to)
```

The TUI lives in its own `tui/` subfolder to keep the game root clean. It is a **read-only viewer** of the `session/` folder. It does not modify game state — that remains the agent's job. The TUI can also invoke tools from `tools/` (e.g., dice roller) for convenience.

The player launches the TUI from the game root using the venv Python:

```bash
# With integrated terminal (default) — split-screen: shell on left, game panels on right
.venv/bin/python tui/tui_viewer.py . --terminal true

# Without integrated terminal — full-width game panels only
.venv/bin/python tui/tui_viewer.py . --terminal false
```

### Reference Template

A complete, generic Python template is provided at **`tui_template.py`** in the repository root. When building a TUI for a new game, copy this file into the game's `tui/` folder and customize it. The template includes all standard components (session parser, panel widgets, terminal widget, tool runner) with `CUSTOMIZE` markers at every game-specific decision point.

### Core Components

The TUI has four layers:

1. **PTY Terminal Widget** (optional) — an embedded pseudo-terminal shell that lets the player interact with their AI agent (e.g., Claude Code) in one half of the screen while viewing game state in the other half. Controlled via the `--terminal` flag.
2. **Session Parser** — reads all `.md` and `.json` files from `session/`, `settings/`, and `game/` directories, extracting structured data via regex patterns.
3. **Widget Panels** — Rich-rendered `Static` widgets that display parsed data with color, bars, tables, and icons.
4. **App Shell** — A `TabbedContent` layout with keyboard shortcuts, a status bar, and an input widget for interactive tools.

---

## Integrated Terminal (`--terminal` Flag)

The TUI supports an **integrated PTY terminal** that embeds a live shell (e.g., bash, zsh) directly inside the TUI window. This is the primary way players interact with their AI agent while viewing game state.

### Launch Modes

```bash
# Default: terminal enabled — split-screen layout
.venv/bin/python tui/tui_viewer.py .

# Explicit: same as above
.venv/bin/python tui/tui_viewer.py . --terminal true

# Terminal disabled — full-width dashboard mode
.venv/bin/python tui/tui_viewer.py . --terminal false
```

| Mode | Layout | Use case |
|------|--------|----------|
| `--terminal true` (default) | Left 50%: live shell. Right 50%: tabbed game panels. | Player runs their AI agent in the terminal while viewing game state alongside. |
| `--terminal false` | Full width: tabbed game panels only. | Player uses a separate terminal window for the agent, or just wants a read-only dashboard. |

### How the Integrated Terminal Works

The terminal is implemented as a `PtyTerminal` widget (see `tui_template.py`) that:

1. **Spawns a real shell** via `pty.openpty()` + `subprocess.Popen`. The child process is a full interactive shell (`$SHELL` or `bash`) attached to a pseudo-terminal, not a fake prompt.
2. **Parses ANSI output** using [pyte](https://github.com/selectel/pyte), a Python terminal emulator library. pyte maintains a virtual screen buffer that tracks cursor position, colors, text attributes, and scrollback history.
3. **Renders to Textual** by converting pyte's screen buffer to Rich `Segment` objects line by line. Each character cell becomes a styled segment with the correct foreground/background color, bold, italic, underline, strikethrough, and reverse attributes.
4. **Forwards keyboard input** by translating Textual `Key` events into the correct byte sequences (ANSI escape codes for arrow keys, function keys, etc.) and writing them to the PTY master file descriptor.
5. **Polls for output** on a 20ms timer, reading up to 64KB per tick from the PTY master fd (set to non-blocking mode). Dirty lines trigger a widget refresh.

### Terminal Capabilities

The integrated terminal supports:

- **Full ANSI color** — 256-color mode via `TERM=xterm-256color`.
- **Alternate screen buffer** — Programs like `vim`, `less`, and `htop` that use modes 47/1047/1049 work correctly. The primary buffer is saved and restored when entering/leaving alternate mode.
- **Scrollback history** — `Shift+PageUp` / `Shift+PageDown` / mouse wheel to scroll through past output. Scrollback is disabled while in alternate screen mode.
- **Dynamic resize** — When the widget size changes (e.g., terminal window resize), the pyte screen is resized and a `TIOCSWINSZ` ioctl notifies the child process.
- **Cursor rendering** — The cursor position is shown as reverse video when the terminal is focused.
- **Wide characters** — CJK and other double-width characters are handled correctly.
- **Ctrl key combos** — `Ctrl+C`, `Ctrl+D`, `Ctrl+Z`, etc. are sent as the correct control codes.

### Terminal Focus Behavior

When the terminal is **focused** (click it or press `t`):
- ALL keyboard input goes to the shell — including keys that are normally TUI bindings (`q`, `r`, `d`, `1`-`8`). This is correct: the user is typing in the shell.
- The terminal border changes to the accent color to indicate focus.

When the terminal is **not focused** (click a tab, press `Escape` then another key):
- Keyboard shortcuts work normally (tab switching, refresh, quit).

### Platform Notes

- The PTY terminal requires **Unix** (`pty`, `fcntl`, `termios` modules). It does not work on native Windows.
- The `pyte` package must be installed: `uv pip install pyte` (in addition to `textual`).

### Implementation in `tui_template.py`

The terminal widget is fully implemented in `tui_template.py` as the `PtyTerminal` class with supporting `EnhancedScreen` class. The `GameTUI` app class conditionally includes the terminal panel based on the `--terminal` flag, using different CSS layouts:

- **With terminal**: `Horizontal` split — `#terminal-panel` (50% width) + `#main-content` (50% width).
- **Without terminal**: Single `#main-content` at full width.

The terminal is started in `on_ready()` and cleaned up in `on_unmount()`.

---

## Session Parser Design

The parser is a single class (`SessionParser`) that takes the game root directory as input and provides a `parse_*()` method for each session file type. Each method returns a `dict` (or `list[dict]`) of structured data extracted from the raw markdown.

### Parsing Strategy

Session files follow predictable markdown patterns. The parser uses regex to extract:

| Pattern | Example | Extraction |
|---------|---------|------------|
| `**Key:** Value` | `**HP:** 73 / 100` | Key-value pairs, optionally split on `/` |
| `\| col1 \| col2 \|` | Markdown tables | Row-by-row cell extraction |
| `- [x] Item` / `- [ ] Item` | Checklists | Boolean + label |
| `## Section` | Section headers | Section-level splitting |
| `---` | Horizontal rules | Record-level splitting (e.g., between NPC blocks) |
| `## [Turn N] — Title` | Log entries | Turn number + title + body text |

**Key principle:** The parser must be tolerant. If a file is missing or a field can't be found, return an empty dict or sensible default — never crash. Games may not populate all fields immediately, and different games will have different schemas.

### Recommended Parser Methods

The parser should provide one method per session file type. A typical RPG-style game might include:

```python
class SessionParser:
    def __init__(self, game_dir: str): ...

    def parse_player(self) -> dict:       # Player stats, class, HP/MP, abilities
    def parse_world_state(self) -> dict:   # Global state, threat meters, region statuses
    def parse_location(self) -> dict:      # Current location, exits, POI
    def parse_inventory(self) -> dict:     # Items, currency, slots
    def parse_companions(self) -> dict:    # Party members
    def parse_npcs(self) -> list[dict]:    # Encountered NPCs
    def parse_quests(self) -> dict:        # Active + completed quests
    def parse_log(self) -> list[dict]:     # Session log entries
    def parse_settings(self) -> dict:      # Game settings (from settings/ dir)
    def parse_all(self) -> dict:           # Calls all of the above
```

Adapt this to the game's actual `sessions.md` schema. A strategy game might replace `parse_player` with `parse_faction` and `parse_resources`. A mystery game might add `parse_clues` and `parse_suspects`. Not every game will have all of these — add, rename, or remove methods to match what the game tracks.

---

## Widget Panel Design

Each tab in the TUI corresponds to one panel widget. Panels inherit from `textual.widgets.Static` and override `render()` to return a `rich.console.Group` of styled `rich.text.Text` objects and `rich.table.Table` objects.

### Visual Conventions

Use these consistently across games. Adapt labels, icons, and colors to fit the game's theme.

#### Progress Bars

For any bounded numeric resource (health, mana, stamina, fuel, morale, etc.):

```
HP ██████████████████░░░░░░░ 73/100
MP ███████████████████░░░░░░ 38/50
```

- Use `█` for filled and `░` for empty.
- Color by threshold: green when > 50%, yellow when > 25%, red when <= 25%.
- Use distinct colors per resource type (e.g., green for health, blue for mana, purple for a special resource).

Helper function pattern:

```python
def bar(current: int, maximum: int, width: int = 20, fill_color: str = "green",
        empty_color: str = "grey37", label: str = "") -> Text:
    ratio = max(0, min(1, current / max(1, maximum)))
    filled = int(ratio * width)
    empty = width - filled
    t = Text()
    if label:
        t.append(f"{label} ", style="bold")
    t.append("█" * filled, style=fill_color)
    t.append("░" * empty, style=empty_color)
    t.append(f" {current}/{maximum}", style="bold white")
    return t
```

#### Global Threat / Progress Meters

For game-wide percentage trackers (corruption, instability, time pressure, invasion progress, etc.):

```
THREAT █████████░░░░░░░░░░░░░░░░░░░░░ 31%
```

- Color shifts with severity: green (0-25%) → yellow (26-50%) → orange (51-75%) → red (76-100%).
- For positive meters (e.g., reputation, completion), reverse the color scale.

#### Stat Blocks

For attribute scores with derived modifiers:

```
STR 14 (+2)    DEX 10 (+0)    WIS 8 (-1)
```

- Show the base value and any modifier inline.
- If the game uses a different stat system (percentile, dice pools, etc.), adapt the display format accordingly.

#### Collection Trackers

For tracking progress toward a set of items, objectives, or milestones:

```
✦ ○ ✦ ○ ○    2 / 5 collected
```

- Collected items show a themed icon or emoji; uncollected show `○` in dim style.
- Choose icons that fit the game's theme (keys, runes, stars, badges, etc.).

#### Disposition Colors

For NPC attitudes or relationship levels:

| Level | Color | Usage |
|-------|-------|-------|
| Hostile / Aggressive | red | Enemies, antagonistic NPCs |
| Wary / Suspicious | dark_orange | Distrustful, cautious NPCs |
| Neutral / Indifferent | yellow | Default, no strong opinion |
| Friendly / Allied | green | Helpful, cooperative NPCs |
| Devoted / Loyal | bright_magenta | Deep trust, bonded allies |
| Unknown | grey50 | Not yet encountered or assessed |

Rename these levels to match the game's disposition system (e.g., a sci-fi game might use "Cooperative" instead of "Friendly").

#### Status Severity Colors

For region states, threat levels, system statuses, or any multi-tier severity indicator:

| Level | Color | Example contexts |
|-------|-------|------------------|
| Safe / Stable / Intact | green | Secured regions, healthy systems |
| Caution / Damaged / Declining | yellow | Early warnings, partial damage |
| Danger / Critical / Failing | dark_orange or red | Urgent threats, heavy damage |
| Lost / Destroyed / Catastrophic | bright_red | Irrecoverable, game-over states |

### Choosing Tabs

The tab set should reflect the game's session file schema. Start from this baseline and adapt:

| Tab | Content | Key | When to include |
|-----|---------|-----|-----------------|
| Character | Name, class, resource bars, stats, abilities, status effects | `1` | Any game with a player character |
| World | Global threat/progress meter, region statuses, antagonist state | `2` | Games with a world map or global state tracker |
| Location | Current place (breadcrumb), description, exits, POI, NPCs present | `3` | Games with explorable locations |
| Inventory | Currency, slot usage, categorized item tables | `4` | Games with item systems |
| Quests | Active quests with progress, completed quests with outcomes | `5` | Games with quest/objective tracking |
| NPCs | All encountered NPCs with disposition, location, quest ties | `6` | Games with NPC interaction |
| Companions | Party members with resource bars, abilities, status | `7` | Games with recruitable party members |
| Log | Chronological session events, most recent first | `8` | Always — every game benefits from a turn log |
| Dice/Tools | Interactive tool runner (dice roller, calculator, etc.) | `d` | Games that use `tools/` scripts |
| Settings | Current game configuration display | — | Always — shows difficulty, preferences, etc. |

Add game-specific tabs as needed. Examples: a crafting game might add a Recipes tab; a political game might add Factions; a survival game might add a Base or Resources tab.

### Top Status Bar

Always include a persistent 1-line status bar above the tabs showing at-a-glance vitals:

```
⚔ <Name> (<Class>)   HP:<cur>/<max>  <Resource>:<cur>/<max>   THREAT:<pct>%   Turn:<n>
```

Choose whichever 4-6 fields are most critical for the game. The player should be able to see their most important numbers regardless of which tab is active.

---

## Interactive Features

### Tool Runner (Dice Roller, etc.)

If the game has scripts in `tools/`, the Tools tab should provide an `Input` widget that accepts expressions and displays results. Invoke tools via `subprocess.run()`:

```python
venv_python = Path(self.game_dir) / ".venv" / "bin" / "python"
tool_path = Path(self.game_dir) / "tools" / "dice.py"
args = [str(venv_python), str(tool_path)] + expr.split()
result = subprocess.run(args, capture_output=True, text=True, timeout=5)
```

For games with multiple tools, the tab can include a tool selector or accept a prefix (e.g., `dice d20+5`, `loot rare`, `map north`).

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit the TUI |
| `r` | Refresh all data from `session/` files |
| `t` | Focus the integrated terminal (when `--terminal true`) |
| `d` | Focus the tool runner input |
| `1`-`8` | Switch directly to tabs 1-8 |

**Note:** When the terminal is focused, all keys go to the shell. Click outside the terminal or press `Escape` first to use TUI shortcuts.

### Refresh

The `r` key re-reads all session files and re-renders all panels. This is essential since the agent modifies `session/` files during gameplay — the player presses `r` after each turn to see updated state.

**Implementation note:** Re-parsing the data is not enough — the new data must be propagated to every widget. Panel widgets store their own reference to the data dict (`self.data`). If `action_refresh` only reassigns `self.session_data` on the app, widgets still hold the old reference and won't update. The refresh handler must:

1. Re-parse all session data (`self.session_data = self.parser.parse_all()`).
2. Update each panel widget's `.data` attribute to point to the new data.
3. Call `.refresh()` on each widget to trigger a re-render.
4. Update the top status bar separately (via `.update()` on the Static widget).

```python
def action_refresh(self) -> None:
    self.session_data = self.parser.parse_all()
    for widget in self.query("CharacterPanel, WorldPanel, ..."):
        widget.data = self.session_data
        widget.refresh()
    # Also update the top status bar
    self.query_one("#top-bar", Static).update(self._make_top_bar(...))
    self.notify("Session data refreshed!")
```

---

## App Shell (CSS & Layout)

Use Textual's built-in `TabbedContent` for tab management. The CSS adapts based on whether the terminal is enabled.

**Base CSS (always applied):**

```css
Screen { background: $surface; }
#top-bar { height: 3; background: #1a1a2e; padding: 0 1; color: white; }
TabbedContent { height: 1fr; }
TabPane { padding: 1 2; }
#tool-input { margin: 1 2; width: 40; }
#tool-result { margin: 1 2; min-height: 5; }
VerticalScroll { height: 1fr; }
```

**Additional CSS when `--terminal true`:**

```css
#split-view { height: 1fr; }
#terminal-panel { width: 50%; height: 1fr; border-right: solid grey; }
#main-content { width: 50%; height: 1fr; }
```

**When `--terminal false`**, the `#split-view` and `#terminal-panel` elements are absent — `#main-content` takes full width.

Wrap each `TabPane`'s content in a `VerticalScroll` so panels with long content (log, inventory, NPCs) are scrollable.

The `tui_template.py` file generates the appropriate CSS dynamically via the `make_css(with_terminal)` function.

---

## Dependencies & Environment

The TUI requires a virtual environment with its dependencies installed. The creating agent must set this up using `uv` in the game root (shared with `tools/`):

```bash
cd <game_root>
uv venv                          # Creates .venv/ (skip if already exists for tools/)
uv pip install textual pyte      # textual = TUI framework (pulls in rich), pyte = terminal emulator
```

This provides:
- `textual` — the TUI framework.
- `rich` — text styling, tables, console rendering (transitive dependency of textual).
- `pyte` — Python terminal emulator library, used by the integrated PTY terminal widget.

If the player will always use `--terminal false`, `pyte` is not needed — but it's simpler to install both.

The TUI itself must be launched with the venv's Python:

```bash
# With integrated terminal (default)
.venv/bin/python tui/tui_viewer.py .

# Without integrated terminal
.venv/bin/python tui/tui_viewer.py . --terminal false
```

Inside `tui_viewer.py`, any `subprocess.run()` calls to `tools/` scripts must also use the venv Python (see the Tool Runner section above).

No other dependencies are needed for the TUI. The TUI is a single `.py` file with no build step. If a game's tools need additional packages (e.g., `numpy` for a procedural map generator), those are installed into the same venv with `uv pip install`.

---

## Adapting to Different Game Genres

The template above is flexible. Here are guidelines for common genres:

| Genre | Key adaptations |
|-------|-----------------|
| **RPG / Adventure** | All standard tabs apply. Focus on character stats, inventory, quest log, NPC relationships. |
| **Strategy / 4X** | Replace Character with Faction/Empire. Add Resources, Diplomacy, Army tabs. World tab shows territory map. |
| **Survival / Crafting** | Add Base, Crafting, Resources tabs. Status bar shows hunger/thirst/shelter. Inventory is central. |
| **Mystery / Investigation** | Add Clues, Suspects, Timeline tabs. Remove Inventory if not relevant. Log tab becomes critical. |
| **Political / Social** | Add Factions, Influence, Relationships tabs. Disposition colors become central. Remove combat-oriented tabs. |
| **Roguelike / Dungeon Crawl** | Keep Character, Inventory, Location, Log. Add Dungeon Map tab. Minimize NPC/Companion tabs. |
| **Sci-fi / Space** | Rename to fit theme: Ship instead of Character, Sectors instead of World, Crew instead of Companions. |

The visual conventions (bars, colors, severity scales) apply universally — just rename the labels and choose thematic icons.

---

## Implementation Checklist

When building a TUI for a new game:

1. **Copy `tui_template.py`** into the game's `tui/` folder and rename to `tui_viewer.py`.
2. **Set up the venv** — run `uv venv` in the game root (if not already created for `tools/`), then `uv pip install textual pyte`.
3. **Read `game/sessions.md`** to understand what files exist in `session/` and their schemas.
4. **Customize the `SessionParser`** — write `parse_*()` methods for each session file, matching the markdown patterns that game uses. Look for `CUSTOMIZE` markers in the template.
5. **Choose which tabs to include** based on what data the game tracks. Add/remove `TabPane` entries in `_compose_tab_panes()`.
6. **Customize panel widgets** — update each panel's `render()` method to display your game's data. Add new panel classes for game-specific tabs.
7. **Match the visual theme** to the game's tone. A horror game might use red/grey; a lighthearted game might use brighter colors. The color tables above are starting points, not requirements.
8. **Implement the top status bar** (`_make_top_bar()`) with the game's most critical at-a-glance values.
9. **Add interactive tool tabs** if the game has scripts in `tools/`. Use `.venv/bin/python` for subprocess calls.
10. **Test the parser** against actual session data — verify each method returns valid data and handles missing files gracefully.
11. **Test both terminal modes** — verify the TUI works with `--terminal true` (split-screen) and `--terminal false` (full-width).

---

## Reference Implementation

- **`tui_template.py`** (repository root) — the generic, game-agnostic template with all standard components. Copy this as your starting point and search for `CUSTOMIZE` markers.
- **`Examples/The Sundering of Aethermoor/tui/tui_viewer.py`** — a complete working implementation for a specific RPG game, demonstrating customized parser methods, themed panel widgets, and game-specific visual elements. Use it as a reference for how a real game adapts the template.
